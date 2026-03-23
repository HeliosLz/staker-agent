"""Telegram Bot application factory."""
from __future__ import annotations

import logging
import os
from typing import FrozenSet, Optional

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from staker_backend.services.agent import cleanup_stale_sessions
from staker_backend.services.container import ServiceContainer
from .handlers import (
    start_command,
    reset_command,
    status_command,
    health_command,
    handle_message,
    handle_delete_mnemonic,
    handle_unauthorized,
)

logger = logging.getLogger(__name__)


def _parse_allowed_chat_ids() -> Optional[FrozenSet[int]]:
    """Parse TELEGRAM_ALLOWED_CHAT_IDS env var into a frozenset of ints.

    Returns None when the variable is unset (no restriction, backward-compatible).
    """
    raw = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        return None
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part:
            try:
                ids.add(int(part))
            except ValueError:
                logger.warning("Ignoring invalid chat ID in TELEGRAM_ALLOWED_CHAT_IDS: %r", part)
    if not ids:
        logger.error("TELEGRAM_ALLOWED_CHAT_IDS is set but contains no valid IDs — blocking all users")
    return frozenset(ids)


def create_telegram_app(services: ServiceContainer):
    """Build and configure the Telegram Bot Application."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

    app = ApplicationBuilder().token(token).build()
    app.bot_data["services"] = services

    # Access control filter
    allowed = _parse_allowed_chat_ids()
    if allowed is not None:
        acl = filters.Chat(chat_id=allowed)
        logger.info("Telegram ACL enabled — allowed chat IDs: %s", allowed)
    else:
        acl = filters.ALL
        logger.warning("TELEGRAM_ALLOWED_CHAT_IDS not set — all users can interact with the bot")

    # Commands
    app.add_handler(CommandHandler("start", start_command, filters=acl))
    app.add_handler(CommandHandler("status", status_command, filters=acl))
    app.add_handler(CommandHandler("health", health_command, filters=acl))
    app.add_handler(CommandHandler("reset", reset_command, filters=acl))

    # Text messages
    app.add_handler(MessageHandler(acl & filters.TEXT & ~filters.COMMAND, handle_message))

    # Inline button callbacks (always allowed — only owners see the button)
    app.add_handler(CallbackQueryHandler(handle_delete_mnemonic, pattern="^delete_mnemonic$"))

    # Catch-all for unauthorized users (only active when ACL is set)
    if allowed is not None:
        app.add_handler(MessageHandler(~acl, handle_unauthorized))

    # Periodic cleanup of stale sessions (every hour)
    app.job_queue.run_repeating(
        lambda ctx: cleanup_stale_sessions(),
        interval=3600,
        first=3600,
    )

    logger.info("Telegram bot configured")
    return app
