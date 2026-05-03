"""OpenRouter Agent service — Chat Loop (s01 pattern).

The LLM-driven agent loop. Uses the shared Tool Registry from core.agent.tools.
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import httpx
import openai

from .container import ServiceContainer
from core.agent.tools import (
    TOOL_DEFINITIONS,
    ToolContext,
    execute as execute_tool,
)
from core.security import redact_secrets

logger = logging.getLogger(__name__)

MAX_TURNS = 15
MAX_HISTORY = 80
MAX_RETRIES = 2
RETRY_BASE_DELAY = 3  # seconds; kept short to avoid blocking thread-pool workers
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ERROR_CONTEXT_OVERFLOW = "context_overflow"
ERROR_RATE_LIMIT = "rate_limit"
ERROR_TIMEOUT = "timeout"
ERROR_OTHER = "other"
TOOL_CONSECUTIVE_FAIL_LIMIT = 3
GRACE_TURNS_BEFORE_END = 2

# Re-export tool name constants for backward compatibility (used by formatting.py)
TOOL_CHECK_ENV = "check_environment"
TOOL_INSTALL_ETH_DOCKER = "install_eth_docker"
TOOL_GENERATE_CONFIG = "generate_config"
TOOL_GENERATE_KEYS = "generate_keys"
TOOL_DEPLOY_NODE = "deploy_node"
TOOL_CHECK_STATUS = "check_node_status"

SYSTEM_PROMPT = """\
你是 Staker Agent AI 助手，帮助用户部署和管理以太坊验证节点。

## 行为准则
- 默认使用中文回复，但跟随用户的语言偏好
- 从用户的自然语言描述中推断部署参数
- 合理默认值：network=holesky, client=lighthouse, num_validators=1, use_lido_csm=false
- keystore_password 必须明确询问用户，绝不使用默认值
- 如果用户要部署到 mainnet，必须明确二次确认
- 生成密钥后如果返回了助记词(mnemonic)，必须醒目地展示给用户并提醒备份

## 任务管理 (todo 工具)
执行多步操作前，先用 todo 工具创建任务列表，然后逐步执行并更新状态：
- pending: 待执行
- in_progress: 正在执行（同时只能有一个）
- completed: 已完成

示例：部署验证节点时，先创建 5 步计划，每完成一步后更新 todo。
这样即使对话很长，你也不会忘记进度。

## 部署流程
标准部署顺序：
1. check_environment - 检查系统环境
2. install_eth_docker - 安装 eth-docker
3. generate_config - 生成节点配置
4. generate_keys - 生成验证者密钥
5. deploy_node - 部署并启动节点

你可以根据用户需求灵活调用工具，不必严格按顺序。
开始部署前，用 todo 工具创建任务列表来追踪进度。

## 运维功能
- check_health - 综合健康检查和评分
- get_sync_progress - 详细同步进度
- get_peer_info - Peer 连接信息
- restart_service - 重启指定容器
- check_node_status - 节点运行状态

## 可用知识库 (用 load_skill 加载完整内容)
- staking: 以太坊质押机制、slashing 规则
- lido-csm: Lido CSM 操作流程
- troubleshooting: 常见节点问题排查

## Monitor 系统
后台 Monitor 持续监控节点健康。你的对话上下文中可能包含 <monitor-events> 标签，
这是 Monitor 最近检测到的事件，请参考这些信息回答用户问题。
如果 Monitor 已经自动重启了服务，向用户解释发生了什么，不要重复操作。

## 记忆功能
- remember: 保存重要信息（用户偏好、操作笔记）到持久化存储
- recall: 检索历史记忆

当用户告诉你偏好（如网络、客户端选择）时，主动用 remember 保存。
下次对话你会在 Memory 部分看到之前保存的信息。

## 错误处理
- 如果某步骤失败，直接重试该工具一次（系统会自动清理残留状态）
- 不要让用户手动执行 shell 命令来解决问题，你应该通过重新调用工具来自动修复
- 只有在重试仍失败时，才向用户解释问题并提供建议

## 注意事项
- withdrawal_address 和 fee_recipient 是可选的，用户没提供就传 null
- 部署前确保用户理解各参数的含义
- 回复简洁明了，避免冗长
"""


_SESSION_TTL = 24 * 3600  # 24 hours


@dataclass
class _Session:
    """Per-client session state."""
    history: List[Dict[str, Any]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    busy: bool = False
    last_active: float = field(default_factory=time.monotonic)
    todo: Any = field(default=None)  # TodoManager, lazily created


# Per-session state keyed by session id
_sessions: Dict[str, _Session] = {}
_sessions_lock = threading.Lock()

# Shared API key + cached client
_api_key: Optional[str] = None
_client: Optional[openai.OpenAI] = None


def _get_session(sid: str) -> _Session:
    with _sessions_lock:
        if sid not in _sessions:
            _sessions[sid] = _Session()
        session = _sessions[sid]
    session.last_active = time.monotonic()
    return session


def remove_session(sid: str) -> None:
    """Clean up session on disconnect."""
    with _sessions_lock:
        _sessions.pop(sid, None)


def cleanup_stale_sessions() -> int:
    """Remove sessions inactive for longer than _SESSION_TTL. Returns count removed."""
    cutoff = time.monotonic() - _SESSION_TTL
    removed = 0
    with _sessions_lock:
        stale = [sid for sid, s in _sessions.items() if s.last_active < cutoff and not s.busy]
        for sid in stale:
            del _sessions[sid]
            removed += 1
    if removed:
        logger.info("Cleaned up %d stale session(s)", removed)
    return removed


def set_api_key(key: str) -> tuple[bool, str]:
    """Store the API key. Validation happens on first use."""
    global _api_key, _client
    if not key:
        return False, "API Key 不能为空"
    _api_key = key
    _client = openai.OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=key,
        timeout=httpx.Timeout(connect=30, read=300, write=30, pool=30),
    )
    return True, ""


def get_api_key_status() -> bool:
    """Return whether an API key is configured."""
    return _api_key is not None


def reset_conversation(sid: str) -> None:
    """Clear conversation history for a session."""
    session = _get_session(sid)
    with session.lock:
        session.history.clear()


def init_from_env() -> None:
    """Initialize API key from environment variables.

    Checks OPENROUTER_API_KEY first, falls back to GEMINI_API_KEY for backward compat.
    """
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if key:
        set_api_key(key)
        logger.info("API key loaded from environment (model: %s)", MODEL)
    else:
        logger.warning("OPENROUTER_API_KEY not set in environment")


@dataclass
class TransportCallbacks:
    """Transport-agnostic callbacks for agent turn events."""
    on_text_delta: Callable[[str], None]
    on_error: Callable[[str], None]
    on_tool_start: Callable[[str, dict, str], None]       # name, input, id
    on_tool_result: Callable[[str, str, dict, bool], None] # name, id, result, success
    on_mnemonic: Callable[[str], None]
    on_turn_complete: Callable[[], None]


def _build_tool_context(services: ServiceContainer, session: _Session) -> ToolContext:
    """Build a ToolContext from the Flask ServiceContainer + session."""
    from core.agent.todo import TodoManager
    agent_state = getattr(services, 'agent_state', None)
    status_monitor = None
    if hasattr(services, 'monitor_loop') and services.monitor_loop:
        status_monitor = services.monitor_loop.ctx.status_monitor
    # Lazily create TodoManager per session (s03)
    if session.todo is None:
        session.todo = TodoManager()
    return ToolContext(
        eth_docker_path=services.deployment.eth_docker_path,
        services=services,
        state=agent_state,
        status_monitor=status_monitor,
        todo=session.todo,
        memory=services.memory_store,
    )


# ---------------------------------------------------------------------------
# s08: Notification drain — inject monitor events into LLM context
# ---------------------------------------------------------------------------

def _drain_notifications(services: ServiceContainer) -> list[dict]:
    """Drain all pending monitor events from the notification queue."""
    notif_queue = getattr(services, 'notif_queue', None)
    if not notif_queue:
        return []
    events = []
    while not notif_queue.empty():
        try:
            events.append(notif_queue.get_nowait())
        except Exception:
            break
    return events


# ---------------------------------------------------------------------------
# s06: Micro-compact — compress old tool results to save context
# ---------------------------------------------------------------------------

KEEP_RECENT_TOOL_RESULTS = 3
_COMPACT_KEEP_KEYS = (
    "status", "health_level", "network", "sync_progress",
    "container", "service", "step", "name",
)


def _summarize_tool_result(data: dict) -> str:
    """Compact a tool result dict, preserving key diagnostic fields."""
    tag = "OK" if data.get("success") else "FAIL"
    parts = [f"[Compacted: {tag}]"]
    if data.get("error"):
        err = str(data["error"])
        if len(err) > 80:
            err = err[:80] + "..."
        parts.append(f"error: {err}")
    for key in _COMPACT_KEEP_KEYS:
        val = data.get(key)
        if val is None:
            continue
        val_str = str(val)
        if len(val_str) > 40:
            val_str = val_str[:40] + "..."
        parts.append(f"{key}={val_str}")
    return " | ".join(parts)


def _micro_compact(history: list[dict]) -> None:
    """Replace old tool result contents with compact placeholders."""
    tool_indices = [i for i, msg in enumerate(history) if msg.get("role") == "tool"]
    if len(tool_indices) <= KEEP_RECENT_TOOL_RESULTS:
        return
    for idx in tool_indices[:-KEEP_RECENT_TOOL_RESULTS]:
        content = history[idx].get("content", "")
        if len(content) > 200:
            try:
                data = json.loads(content)
                history[idx]["content"] = _summarize_tool_result(data)
            except (json.JSONDecodeError, TypeError):
                history[idx]["content"] = "[Previous result compacted]"


def _error_text(error: BaseException) -> str:
    """Collect provider error details into one lowercase string for classification."""
    parts = [type(error).__name__, str(error)]
    for attr in ("body", "response"):
        value = getattr(error, attr, None)
        if value is None:
            continue
        parts.append(str(value))
        text = getattr(value, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).lower()


def classify_agent_error(error: BaseException) -> str:
    """Classify LLM/provider errors into recovery buckets."""
    if isinstance(error, openai.RateLimitError):
        return ERROR_RATE_LIMIT
    if isinstance(error, openai.APITimeoutError):
        return ERROR_TIMEOUT
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return ERROR_TIMEOUT

    text = _error_text(error)
    if any(marker in text for marker in (
        "context_length_exceeded",
        "maximum context length",
        "context length",
        "context window",
        "too many tokens",
        "token limit",
        "prompt is too long",
        "input is too long",
    )):
        return ERROR_CONTEXT_OVERFLOW
    if any(marker in text for marker in (
        "rate limit",
        "rate_limit",
        "too many requests",
        "quota exceeded",
        "status_code: 429",
        " 429",
    )):
        return ERROR_RATE_LIMIT
    if "timed out" in text or "timeout" in text:
        return ERROR_TIMEOUT
    return ERROR_OTHER


def _trim_history_to_safe_boundary(history: list[dict], max_messages: int) -> None:
    """Trim history in-place without starting on a tool-result fragment."""
    if len(history) <= max_messages:
        return

    cut = len(history) - max_messages
    original_cut = cut
    while cut < len(history):
        msg = history[cut]
        role = msg.get("role", "")
        if role in ("user", "system") or (role == "assistant" and "tool_calls" not in msg):
            break
        cut += 1
    if cut >= len(history):
        cut = original_cut
        while cut > 0:
            cut -= 1
            msg = history[cut]
            role = msg.get("role", "")
            if role in ("user", "system") or (role == "assistant" and "tool_calls" not in msg):
                break
    del history[:cut]


def _recover_context_overflow(history: list[dict]) -> None:
    """Aggressively shrink history once after a context-window failure."""
    _micro_compact(history)
    original_len = len(history)
    _trim_history_to_safe_boundary(history, max(12, MAX_HISTORY // 2))
    if len(history) < original_len:
        history.insert(0, {
            "role": "system",
            "content": "[Previous conversation omitted after context overflow recovery.]",
        })


def _strip_json_fence(text: str) -> Optional[str]:
    match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _extract_json_object(text: str) -> Optional[str]:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1].strip()
    return text[start:].strip()


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _close_json_delimiters(text: str) -> str:
    stack: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]":
            if stack and ((stack[-1] == "{" and char == "}") or (stack[-1] == "[" and char == "]")):
                stack.pop()
    suffix = "".join("}" if char == "{" else "]" for char in reversed(stack))
    return text + suffix


def _json_argument_candidates(raw: str) -> list[str]:
    candidates: list[str] = []

    def add(value: Optional[str]) -> None:
        if value is None:
            return
        value = value.strip()
        if value and value not in candidates:
            candidates.append(value)

    add(raw)
    stripped = raw.strip()
    add(stripped)
    add(_strip_json_fence(stripped))
    for candidate in list(candidates):
        add(_extract_json_object(candidate))
    for candidate in list(candidates):
        add(_remove_trailing_commas(candidate))
    for candidate in list(candidates):
        add(_close_json_delimiters(candidate))
        add(_remove_trailing_commas(_close_json_delimiters(candidate)))
    return candidates


def parse_tool_arguments(raw: str) -> tuple[dict, Optional[str]]:
    """Parse and repair streamed tool-call arguments.

    Returns (args, None) on success. On failure, returns ({}, error_message) so the
    agent can emit a structured tool error instead of silently executing with {}.
    """
    if not raw or not raw.strip():
        return {}, None

    last_error = ""
    for candidate in _json_argument_candidates(raw):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = f"{exc.msg} at char {exc.pos}"
            continue
        if isinstance(parsed, dict):
            return parsed, None
        return {}, f"tool arguments must be a JSON object, got {type(parsed).__name__}"
    return {}, f"invalid JSON tool arguments: {last_error or 'unparseable input'}"


def run_agent_turn_cb(
    user_message: str,
    services: ServiceContainer,
    session_id: str,
    callbacks: TransportCallbacks,
) -> None:
    """Run one full agent turn using transport-agnostic callbacks."""
    if not _client:
        callbacks.on_error("API Key 未配置")
        return

    session = _get_session(session_id)
    ctx = _build_tool_context(services, session)
    composer = services.message_composer

    with session.lock:
        if session.busy:
            callbacks.on_error("请等待上一条消息处理完成")
            return
        session.busy = True
        session.history.append({"role": "user", "content": user_message})
        _trim_history_to_safe_boundary(session.history, MAX_HISTORY)

    try:
        _tool_fail_streak: Dict[str, int] = {}

        for _turn in range(MAX_TURNS):
            # Grace call: warn LLM before the final turn
            is_grace_turn = _turn == MAX_TURNS - 1
            if _turn == MAX_TURNS - GRACE_TURNS_BEFORE_END and _turn > 0:
                with session.lock:
                    session.history.append({
                        "role": "user",
                        "content": (
                            "<system-notice>你即将达到本轮最大交互次数。"
                            "请总结已完成的操作和剩余待办事项。"
                            "如果有未完成的多步任务，请更新 todo 状态。</system-notice>"
                        ),
                    })

            # s08: drain monitor notifications into conversation context
            events = _drain_notifications(services)
            if events:
                summary = "\n".join(
                    f"[{e.get('type', '?')}] {e.get('check', '?')}: {e.get('message', '')}"
                    for e in events
                )
                with session.lock:
                    session.history.append({
                        "role": "user",
                        "content": f"<monitor-events>\n{summary}\n</monitor-events>",
                    })

            # s06: micro-compact old tool results
            with session.lock:
                _micro_compact(session.history)
                history_snapshot = list(session.history)

            def _compose(snapshot: list[dict]) -> list[dict]:
                if composer:
                    return composer.compose(snapshot)
                logger.warning("MessageComposer not available, memory injection skipped")
                return [{"role": "system", "content": SYSTEM_PROMPT}] + snapshot

            messages = _compose(history_snapshot)

            # Retry loop for stream creation only.
            # Consumption is NOT retried: text deltas already sent to the UI
            # cannot be rolled back, so retrying would produce duplicate text.
            stream = None
            recovered_context = False
            retry_attempt = 0
            create_kwargs: Dict[str, Any] = {
                "model": MODEL,
                "messages": messages,
                "stream": True,
            }
            if not is_grace_turn:
                create_kwargs["tools"] = TOOL_DEFINITIONS
            while True:
                try:
                    stream = _client.chat.completions.create(**create_kwargs)
                    break
                except Exception as e:
                    kind = classify_agent_error(e)
                    if kind == ERROR_CONTEXT_OVERFLOW and not recovered_context:
                        logger.warning("Context overflow from provider; compacting history and retrying once")
                        with session.lock:
                            _recover_context_overflow(session.history)
                            history_snapshot = list(session.history)
                        messages = _compose(history_snapshot)
                        create_kwargs["messages"] = messages
                        recovered_context = True
                        continue
                    if kind in (ERROR_RATE_LIMIT, ERROR_TIMEOUT) and retry_attempt < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (retry_attempt + 1)
                        logger.warning("%s provider error, retrying in %ds...", kind, delay)
                        retry_attempt += 1
                        time.sleep(delay)
                        continue
                    if kind == ERROR_CONTEXT_OVERFLOW:
                        callbacks.on_error(f"上下文过长，已尝试压缩后仍失败: {e}")
                    elif kind in (ERROR_RATE_LIMIT, ERROR_TIMEOUT):
                        callbacks.on_error(f"API 请求失败({kind})，已重试 {MAX_RETRIES} 次: {e}")
                    else:
                        callbacks.on_error(f"API 错误: {e}")
                    return

            if stream is None:
                return

            text_parts: list[str] = []
            tool_calls_acc: Dict[int, Dict[str, Any]] = {}

            try:
                for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue

                    if delta.content:
                        callbacks.on_text_delta(delta.content)
                        text_parts.append(delta.content)

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_acc:
                                tool_calls_acc[idx] = {
                                    "id": tc.id or "",
                                    "name": tc.function.name or "" if tc.function else "",
                                    "arguments": "",
                                }
                            entry = tool_calls_acc[idx]
                            if tc.id:
                                entry["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    entry["name"] = tc.function.name
                                if tc.function.arguments:
                                    entry["arguments"] += tc.function.arguments
            except Exception as e:
                logger.error("Streaming error: %s", e)
                callbacks.on_error(f"流式传输中断: {e}")
                return

            # Build function_calls list from accumulated fragments
            function_calls = []
            for idx in sorted(tool_calls_acc.keys()):
                entry = tool_calls_acc[idx]
                args, parse_error = parse_tool_arguments(entry["arguments"])
                function_calls.append({
                    "id": entry["id"],
                    "name": entry["name"],
                    "arguments": args,
                    "parse_error": parse_error,
                })

            collected_text = "".join(text_parts)

            if not collected_text and not function_calls:
                break

            # Append assistant message to history
            assistant_msg: Dict[str, Any] = {"role": "assistant"}
            if collected_text:
                assistant_msg["content"] = collected_text
            if function_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": fc["id"],
                        "type": "function",
                        "function": {
                            "name": fc["name"],
                            "arguments": json.dumps(redact_secrets(fc["arguments"])),
                        },
                    }
                    for fc in function_calls
                ]
            # OpenAI format requires content field even if null when tool_calls present
            if "content" not in assistant_msg:
                assistant_msg["content"] = None

            with session.lock:
                session.history.append(assistant_msg)

            if not function_calls:
                break

            # Execute tool calls and append results to history
            called_todo = False
            for fc in function_calls:
                tool_name = fc["name"]
                tool_input = fc["arguments"]
                tool_id = fc["id"] or uuid.uuid4().hex[:8]

                # Send redacted input to UI; execute with raw args
                callbacks.on_tool_start(tool_name, redact_secrets(tool_input), tool_id)

                if fc.get("parse_error"):
                    result = {
                        "success": False,
                        "error_type": "invalid_tool_arguments",
                        "error": "Tool arguments were not valid JSON",
                        "details": fc["parse_error"],
                    }
                elif _tool_fail_streak.get(tool_name, 0) >= TOOL_CONSECUTIVE_FAIL_LIMIT:
                    result = {
                        "success": False,
                        "error_type": "circuit_breaker",
                        "error": (
                            f"Tool '{tool_name}' has failed "
                            f"{TOOL_CONSECUTIVE_FAIL_LIMIT} consecutive times. "
                            "Try a different approach or ask the user for help."
                        ),
                    }
                else:
                    result = execute_tool(tool_name, tool_input, ctx)

                if result.get("success"):
                    _tool_fail_streak[tool_name] = 0
                else:
                    _tool_fail_streak[tool_name] = _tool_fail_streak.get(tool_name, 0) + 1

                if tool_name == "todo":
                    called_todo = True

                # Deliver mnemonic via directed channel, then redact everything
                if result.get("mnemonic"):
                    callbacks.on_mnemonic(result["mnemonic"])
                redacted_result = redact_secrets(result)

                callbacks.on_tool_result(
                    tool_name, tool_id, redacted_result, result.get("success", False)
                )

                with session.lock:
                    session.history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps(redacted_result, ensure_ascii=False),
                    })

            # s03: nag reminder — once per turn, as a separate user message
            if not called_todo and ctx.todo and ctx.todo.should_nag():
                with session.lock:
                    session.history.append({
                        "role": "user",
                        "content": "<reminder>Update your todos.</reminder>",
                    })

            # s03: tick turn counter
            if ctx.todo and not called_todo:
                ctx.todo.tick_turn()
    finally:
        with session.lock:
            session.busy = False
        callbacks.on_turn_complete()


def run_agent_turn(user_message: str, services: ServiceContainer, socketio: Any, sid: str) -> None:
    """Socket.IO wrapper around run_agent_turn_cb — preserves existing behaviour."""

    def _emit(event: str, data: Any) -> None:
        socketio.emit(event, data, to=sid)

    callbacks = TransportCallbacks(
        on_text_delta=lambda delta: _emit("agent_text_delta", {"delta": delta}),
        on_error=lambda error: _emit("agent_error", {"error": error}),
        on_tool_start=lambda name, inp, tid: _emit("agent_tool_start", {
            "tool_name": name, "tool_input": inp, "tool_id": tid,
        }),
        on_tool_result=lambda name, tid, result, success: _emit("agent_tool_result", {
            "tool_name": name, "tool_id": tid, "result": result, "success": success,
        }),
        on_mnemonic=lambda mnemonic: _emit("agent_mnemonic", {"mnemonic": mnemonic}),
        on_turn_complete=lambda: _emit("agent_turn_complete", {}),
    )

    run_agent_turn_cb(user_message, services, sid, callbacks)
