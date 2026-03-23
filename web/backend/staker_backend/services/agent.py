"""OpenRouter Agent service — Chat Loop (s01 pattern).

The LLM-driven agent loop. Uses the shared Tool Registry from core.agent.tools.
"""
from __future__ import annotations

import json
import logging
import os
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

logger = logging.getLogger(__name__)

MAX_TURNS = 15
MAX_HISTORY = 80
MAX_RETRIES = 2
RETRY_BASE_DELAY = 3  # seconds; kept short to avoid blocking thread-pool workers
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

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
                tag = "OK" if data.get("success") else "FAIL"
                history[idx]["content"] = f"[Previous result: {tag}]"
            except (json.JSONDecodeError, TypeError):
                history[idx]["content"] = "[Previous result compacted]"


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
        if len(session.history) > MAX_HISTORY:
            # Truncate but avoid splitting tool-call/tool-result pairs.
            # Walk forward from the cut point to find a safe boundary
            # (a "user" or "assistant" without tool_calls).
            cut = len(session.history) - MAX_HISTORY
            original_cut = cut
            while cut < len(session.history):
                msg = session.history[cut]
                role = msg.get("role", "")
                if role in ("user", "system") or (role == "assistant" and "tool_calls" not in msg):
                    break
                cut += 1
            # If no safe boundary found forward, scan backward
            if cut >= len(session.history):
                cut = original_cut
                while cut > 0:
                    cut -= 1
                    msg = session.history[cut]
                    role = msg.get("role", "")
                    if role in ("user", "system") or (role == "assistant" and "tool_calls" not in msg):
                        break
            session.history = session.history[cut:]

    try:
        for _turn in range(MAX_TURNS):
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

            if composer:
                messages = composer.compose(history_snapshot)
            else:
                logger.warning("MessageComposer not available, memory injection skipped")
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history_snapshot

            # Retry loop for stream creation only.
            # Consumption is NOT retried: text deltas already sent to the UI
            # cannot be rolled back, so retrying would produce duplicate text.
            stream = None
            for _attempt in range(MAX_RETRIES + 1):
                try:
                    stream = _client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        tools=TOOL_DEFINITIONS,
                        stream=True,
                    )
                    break
                except (openai.RateLimitError, openai.APITimeoutError) as e:
                    if _attempt < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (_attempt + 1)
                        logger.warning("Retryable error (%s), retrying in %ds...", type(e).__name__, delay)
                        time.sleep(delay)
                        continue
                    callbacks.on_error(f"API 请求失败，已重试 {MAX_RETRIES} 次: {e}")
                    return
                except Exception as e:
                    err_str = str(e).lower()
                    if ('timed out' in err_str or 'timeout' in err_str) and _attempt < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (_attempt + 1)
                        logger.warning("Provider timeout, retrying in %ds...", delay)
                        time.sleep(delay)
                        continue
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
                try:
                    args = json.loads(entry["arguments"]) if entry["arguments"] else {}
                except json.JSONDecodeError:
                    args = {}
                function_calls.append({
                    "id": entry["id"],
                    "name": entry["name"],
                    "arguments": args,
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
                            "arguments": json.dumps(fc["arguments"]),
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

                callbacks.on_tool_start(tool_name, tool_input, tool_id)

                result = execute_tool(tool_name, tool_input, ctx)

                if tool_name == "todo":
                    called_todo = True

                if result.get("mnemonic"):
                    callbacks.on_mnemonic(result["mnemonic"])
                    result["mnemonic"] = "[REDACTED - delivered separately]"

                callbacks.on_tool_result(
                    tool_name, tool_id, result, result.get("success", False)
                )

                with session.lock:
                    session.history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps(result, ensure_ascii=False),
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
