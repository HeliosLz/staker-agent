"""Unified Tool Registry (s02 pattern).

Both the Chat Loop (LLM-driven) and Monitor Loop (rules-driven) share this
dispatch map. Adding a tool = adding one handler + one definition.
"""
from __future__ import annotations

import logging
import subprocess
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent / "skills"

VALID_NETWORKS = ["mainnet", "hoodi", "holesky", "sepolia"]
VALID_CLIENTS = ["lighthouse", "prysm", "teku", "nimbus"]


@dataclass
class ToolContext:
    """Execution context passed to every tool handler.

    Carries references needed by handlers without coupling core/ to Flask.
    - ``services``: Flask ServiceContainer (for deployment handlers).
    - ``state``:    Shared AgentState (for ops/monitor handlers).
    - ``status_monitor``: StatusMonitor from core/node/status.py.
    """
    eth_docker_path: str
    services: Any = None       # ServiceContainer — set by web layer
    state: Any = None          # AgentState — set after Step 2
    status_monitor: Any = None # StatusMonitor — set after Step 2
    todo: Any = None           # TodoManager — set per-session (s03)


# ---------------------------------------------------------------------------
# Handler type: (tool_input: dict, ctx: ToolContext) -> dict
# ---------------------------------------------------------------------------
HandlerFn = Callable[[Dict[str, Any], ToolContext], Dict[str, Any]]


# ---------------------------------------------------------------------------
# Deployment tool handlers (migrated from services/agent.py)
# ---------------------------------------------------------------------------

def handle_check_env(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    data, all_passed = ctx.services.environment.run_checks()
    return {"success": True, "all_passed": all_passed, "checks": data}


def handle_install_eth_docker(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    result = ctx.services.deployment.install_eth_docker()
    return {"success": result, "message": "eth-docker 安装完成" if result else "安装失败"}


def handle_generate_config(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    result = ctx.services.configuration.generate(
        network=tool_input["network"],
        client=tool_input["client"],
        fee_recipient=tool_input.get("fee_recipient"),
        withdrawal_address=tool_input.get("withdrawal_address"),
    )
    return {
        "success": True,
        "network": result["network"],
        "client": result["client"],
        "config_path": result["config_path"],
    }


def handle_generate_keys(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    if not tool_input.get("keystore_password"):
        return {"success": False, "error": "keystore_password is required"}
    result = ctx.services.deployment.generate_keys(
        network=tool_input["network"],
        num_validators=tool_input.get("num_validators", 1),
        withdrawal_address=tool_input.get("withdrawal_address"),
        use_lido_csm=tool_input.get("use_lido_csm", False),
        keystore_password=tool_input["keystore_password"],
    )
    return {"success": True, **result}


def handle_deploy_node(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    result = ctx.services.deployment.start()
    return {"success": result, "message": "节点已启动" if result else "启动失败"}


def handle_check_status(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    status = ctx.services.status.get_status()
    return {"success": True, **status}


# ---------------------------------------------------------------------------
# Ops tool handlers (new — shared by Monitor Loop and Chat Loop)
# ---------------------------------------------------------------------------

def handle_check_health(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    """Return the latest health report from shared state, or run one now."""
    if ctx.state and ctx.state.last_report:
        return {"success": True, **ctx.state.last_report}
    # Fallback: run an immediate check
    from core.monitor.health import HealthMonitor
    sm = ctx.status_monitor
    if not sm:
        return {"success": False, "error": "StatusMonitor not available"}
    containers = sm.get_container_status()
    sync = sm.get_sync_status()
    report = HealthMonitor.full_report(
        containers, sync.get("execution", {}), sync.get("consensus", {}),
        ctx.eth_docker_path, {},
    )
    return {"success": True, **report.to_dict()}


def handle_get_sync(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    sm = ctx.status_monitor
    if not sm:
        return {"success": False, "error": "StatusMonitor not available"}
    return {"success": True, **sm.get_sync_status()}


def handle_get_peers(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    from core.monitor.health import _query_el_peer_count, _query_cl_peer_count
    el = _query_el_peer_count(ctx.eth_docker_path)
    cl = _query_cl_peer_count(ctx.eth_docker_path)
    return {
        "success": True,
        "execution": {"peers": el},
        "consensus": {"peers": cl},
    }


def handle_restart_service(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    service = tool_input.get("service", "")
    if service not in ("execution", "consensus", "validator"):
        return {"success": False, "error": f"Invalid service: {service}"}
    try:
        result = subprocess.run(
            ["docker", "compose", "restart", service],
            cwd=ctx.eth_docker_path,
            capture_output=True, text=True, timeout=120,
        )
        ok = result.returncode == 0
        return {"success": ok, "message": f"{service} {'restarted' if ok else 'restart failed'}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_load_skill(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    """s05: Load domain knowledge on demand."""
    name = tool_input.get("name", "")
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        available = [f.stem for f in SKILLS_DIR.glob("*.md")] if SKILLS_DIR.exists() else []
        return {"success": False, "error": f"Unknown skill: {name}", "available": available}
    content = path.read_text(encoding="utf-8")
    return {"success": True, "content": f"<skill name='{name}'>\n{content}\n</skill>"}


def handle_todo(tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    """s03: Update the structured task list."""
    items = tool_input.get("items", [])
    if not items:
        return {"success": False, "error": "items is required"}
    if not ctx.todo:
        return {"success": False, "error": "TodoManager not available"}
    result = ctx.todo.update(items)
    if result.startswith("Error:"):
        return {"success": False, "error": result}
    return {"success": True, "todos": result}


# ---------------------------------------------------------------------------
# Dispatch map — add a tool by adding one entry here
# ---------------------------------------------------------------------------

TOOL_HANDLERS: Dict[str, HandlerFn] = {
    # Deployment tools
    "check_environment":   handle_check_env,
    "install_eth_docker":  handle_install_eth_docker,
    "generate_config":     handle_generate_config,
    "generate_keys":       handle_generate_keys,
    "deploy_node":         handle_deploy_node,
    "check_node_status":   handle_check_status,
    # Ops tools
    "check_health":        handle_check_health,
    "get_sync_progress":   handle_get_sync,
    "get_peer_info":       handle_get_peers,
    "restart_service":     handle_restart_service,
    # Knowledge
    "load_skill":          handle_load_skill,
    # Planning (s03)
    "todo":                handle_todo,
}


# ---------------------------------------------------------------------------
# OpenAI-compatible tool definitions (sent to LLM)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_environment",
            "description": "检查系统环境是否满足运行以太坊节点的要求，包括 OS、Python、Docker、磁盘空间、网络连通性。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "install_eth_docker",
            "description": "安装 eth-docker（以太坊 Docker 部署工具）。如果已安装则跳过。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_config",
            "description": "生成 eth-docker 节点配置文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "enum": VALID_NETWORKS,
                        "description": "以太坊网络",
                    },
                    "client": {
                        "type": "string",
                        "enum": VALID_CLIENTS,
                        "description": "共识层客户端",
                    },
                    "fee_recipient": {
                        "type": "string",
                        "description": "手续费接收地址（可选）",
                    },
                    "withdrawal_address": {
                        "type": "string",
                        "description": "提款地址（可选）",
                    },
                },
                "required": ["network", "client"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_keys",
            "description": "生成验证者密钥。会返回助记词(mnemonic)，必须提醒用户妥善备份。",
            "parameters": {
                "type": "object",
                "properties": {
                    "network": {
                        "type": "string",
                        "enum": VALID_NETWORKS,
                        "description": "以太坊网络",
                    },
                    "num_validators": {
                        "type": "integer",
                        "description": "验证者数量",
                    },
                    "keystore_password": {
                        "type": "string",
                        "description": "密钥库密码（必须由用户提供）",
                    },
                    "withdrawal_address": {
                        "type": "string",
                        "description": "提款地址（可选）",
                    },
                    "use_lido_csm": {
                        "type": "boolean",
                        "description": "是否使用 Lido CSM",
                    },
                },
                "required": ["network", "num_validators", "keystore_password"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_node",
            "description": "部署并启动以太坊节点（执行 docker compose up）。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_node_status",
            "description": "检查当前节点运行状态，包括容器状态、网络、客户端信息。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # --- Ops tools ---
    {
        "type": "function",
        "function": {
            "name": "check_health",
            "description": "获取节点健康报告，包括容器状态、同步状态、Peer 连接数等综合健康评分。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sync_progress",
            "description": "获取详细的同步进度，包括执行层和共识层的当前区块/slot、同步距离和进度百分比。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_peer_info",
            "description": "获取执行层和共识层的 Peer 连接数量。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restart_service",
            "description": "重启指定的 Docker 容器服务。",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "enum": ["execution", "consensus", "validator"],
                        "description": "要重启的服务名称",
                    },
                },
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": "加载领域知识。可用: staking(质押机制), lido-csm(CSM操作), troubleshooting(排障)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "知识包名称",
                    },
                },
                "required": ["name"],
            },
        },
    },
    # --- Planning (s03) ---
    {
        "type": "function",
        "function": {
            "name": "todo",
            "description": "创建或更新任务列表。多步操作前先规划，每完成一步后更新状态。同一时间只能有一个 in_progress 任务。",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "完整的任务列表（每次调用传入全量列表）",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "任务 ID，如 '1', '2'"},
                                "text": {"type": "string", "description": "任务描述"},
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                    "description": "任务状态",
                                },
                            },
                            "required": ["id", "text", "status"],
                        },
                    },
                },
                "required": ["items"],
            },
        },
    },
]


def execute(name: str, tool_input: Dict[str, Any], ctx: ToolContext) -> Dict[str, Any]:
    """Execute a tool by name via the dispatch map."""
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"success": False, "error": f"Unknown tool: {name}"}
    try:
        return handler(tool_input, ctx)
    except Exception as e:
        logger.error("Tool %s failed: %s", name, traceback.format_exc())
        return {"success": False, "error": str(e)}
