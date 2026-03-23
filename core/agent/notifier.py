"""Event formatting for notification sinks (Telegram, WebSocket)."""
from __future__ import annotations

import re
from typing import Any, Dict

_MD_V2_SPECIAL = re.compile(r"([_*\[\]()~`>#+\-=|{}.!\\])")


def escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2.

    Note: telegram_bot/formatting.py has an identical function. We duplicate
    here to keep core/ independent of the web layer. Both use the same regex.
    """
    return _MD_V2_SPECIAL.sub(r"\\\1", text)


def format_event(event: Dict[str, Any]) -> str:
    """Format a monitor event as a MarkdownV2 Telegram message."""
    etype = event.get("type", "")
    check = event.get("check", "")
    message = event.get("message", "")
    label = _CHECK_LABELS.get(check, check)

    if etype == "auto_fix":
        return (
            f"\u2699\ufe0f {escape_md(label)}\n\n"
            f"{escape_md(message)}\n"
            f"{escape_md('已自动重启，观察中...')}"
        )

    if etype == "recovery":
        downtime = event.get("downtime", 0)
        dt_str = _format_duration(downtime) if downtime else ""
        lines = [f"\u2705 *RECOVERED: {escape_md(label)}*", ""]
        if message:
            lines.append(escape_md(message))
        if dt_str:
            lines.append(f"{escape_md('停机时间: ' + dt_str)}")
        return "\n".join(lines)

    if etype == "escalation":
        action_count = event.get("action_count", 0)
        return (
            f"\U0001f6a8 *{escape_md(label)}*\n\n"
            f"{escape_md(message)}\n"
            f"{escape_md(f'已自动重启 {action_count} 次仍未恢复，需要人工介入')}"
        )

    # Default: alert
    level = event.get("level", "")
    icon = "\U0001f6a8" if level == "critical" else "\u26a0\ufe0f"
    severity = "ALERT" if level == "critical" else "WARNING"
    return (
        f"{icon} *{escape_md(severity)}: {escape_md(label)}*\n\n"
        f"{escape_md(message)}"
    )


def _format_duration(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m"


_CHECK_LABELS = {
    "container_liveness": "Container Status",
    "el_sync": "EL Sync",
    "cl_sync": "CL Sync",
    "el_peers": "EL Peers",
    "cl_peers": "CL Peers",
}
