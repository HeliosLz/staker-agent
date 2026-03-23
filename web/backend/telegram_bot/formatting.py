"""Telegram MarkdownV2 formatting utilities."""
from __future__ import annotations

import re

from staker_backend.services.agent import (
    TOOL_CHECK_ENV,
    TOOL_INSTALL_ETH_DOCKER,
    TOOL_GENERATE_CONFIG,
    TOOL_GENERATE_KEYS,
    TOOL_DEPLOY_NODE,
    TOOL_CHECK_STATUS,
)

_MD_V2_SPECIAL = re.compile(r"([_*\[\]()~`>#+\-=|{}.!\\])")

TOOL_LABELS = {
    TOOL_CHECK_ENV: "环境检查",
    TOOL_INSTALL_ETH_DOCKER: "安装 eth-docker",
    TOOL_GENERATE_CONFIG: "生成配置",
    TOOL_GENERATE_KEYS: "生成密钥",
    TOOL_DEPLOY_NODE: "部署节点",
    TOOL_CHECK_STATUS: "节点状态检查",
    "check_health": "健康检查",
    "get_sync_progress": "同步进度",
    "get_peer_info": "Peer 信息",
    "restart_service": "重启服务",
    "load_skill": "加载知识",
    "todo": "更新任务",
}


def escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    return _MD_V2_SPECIAL.sub(r"\\\1", text)


def format_tool_start(name: str) -> str:
    label = TOOL_LABELS.get(name, name)
    return f"\U0001f527 正在执行: {escape_md(label)}\\.\\.\\."


def format_tool_done(name: str, success: bool) -> str:
    label = TOOL_LABELS.get(name, name)
    icon = "\u2705" if success else "\u274c"
    status = "完成" if success else "失败"
    return f"{icon} {escape_md(label)} {escape_md(status)}"


def format_mnemonic(mnemonic: str) -> str:
    escaped = escape_md(mnemonic)
    return (
        "\u26a0\ufe0f *助记词 \\(Mnemonic\\)* \u26a0\ufe0f\n\n"
        f"||{escaped}||\n\n"
        f"{escape_md('请立即备份！此消息将在你点击删除按钮后销毁。')}"
    )


def split_message(text: str, max_len: int = 4096) -> list[str]:
    """Split a long message into chunks that fit Telegram's limit."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Try to split at last newline within limit
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


def format_status_text(status: dict) -> str:
    """Format node status dict as plain text for /status command."""
    containers = status.get("containers", [])
    sync = status.get("sync", {})
    lines = ["Node Status:"]

    if not containers:
        lines.append("  No containers found.")
    else:
        for c in containers:
            service = c.get("Service", "?")
            state = c.get("State", "?")
            icon = "+" if state == "running" else "-"
            lines.append(f"  [{icon}] {service}: {state}")

    el = sync.get("execution", {})
    cl = sync.get("consensus", {})
    if el:
        if el.get("syncing") is False:
            lines.append(f"  EL: synced (block {el.get('current_block', '?')})")
        elif el.get("syncing"):
            lines.append(f"  EL: syncing {el.get('progress_pct', 0):.1f}%")
        elif el.get("error"):
            lines.append(f"  EL: {el['error']}")
    if cl:
        if cl.get("syncing") is False:
            lines.append(f"  CL: synced (slot {cl.get('head_slot', '?')})")
        elif cl.get("syncing"):
            lines.append(f"  CL: syncing {cl.get('progress_pct', 0):.1f}%")
        elif cl.get("error"):
            lines.append(f"  CL: {cl['error']}")

    return "\n".join(lines)


def format_health_text(report: dict) -> str:
    """Format health report dict as MarkdownV2 for /health command."""
    overall = report.get("overall", "unknown")
    checks = report.get("checks", [])

    icon = {"healthy": "\u2705", "degraded": "\u26a0\ufe0f", "critical": "\U0001f6a8"}.get(overall, "\u2753")
    lines = [f"{icon} *Health: {escape_md(overall.upper())}*", ""]

    for c in checks:
        level = c.get("level", "?")
        c_icon = {"healthy": "\u2705", "degraded": "\u26a0\ufe0f", "critical": "\U0001f6a8"}.get(level, "\u2753")
        lines.append(f"{c_icon} {escape_md(c.get('message', c.get('name', '?')))}")

    return "\n".join(lines)
