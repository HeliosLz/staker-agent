"""Telegram command and message handlers."""
from __future__ import annotations

import asyncio
import atexit
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from staker_backend.services.agent import (
    TransportCallbacks,
    run_agent_turn_cb,
    reset_conversation,
)
from .formatting import (
    format_tool_start,
    format_tool_done,
    format_mnemonic,
    split_message,
    format_status_text,
    format_health_text,
)

logger = logging.getLogger(__name__)

_MAX_WORKERS = int(os.getenv("AGENT_MAX_WORKERS", "8"))
_executor = ThreadPoolExecutor(max_workers=_MAX_WORKERS)
atexit.register(_executor.shutdown, wait=False)

WELCOME_TEXT = (
    "👋 你好！我是 *Staker Agent*，你的以太坊验证节点部署助手。\n\n"
    "直接发消息告诉我你想做什么，比如：\n"
    "• 帮我在 holesky 上部署一个验证者\n"
    "• 检查一下系统环境\n"
    "• 查看节点运行状态\n\n"
    "命令：\n"
    "/start \\- 显示此帮助\n"
    "/status \\- 即时节点状态\n"
    "/health \\- 即时健康报告\n"
    "/reset \\- 清空对话历史"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(WELCOME_TEXT, parse_mode="MarkdownV2")


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset command."""
    session_id = f"tg_{update.effective_chat.id}"
    reset_conversation(session_id)
    await update.message.reply_text("🔄 对话已重置。")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status — instant node status, no LLM."""
    services = context.bot_data["services"]
    try:
        status = services.status.get_status()
        text = format_status_text(status)
    except Exception as e:
        text = f"Status check failed: {e}"
    await update.message.reply_text(text)


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health — instant health report, no LLM."""
    services = context.bot_data["services"]
    report = getattr(services, 'agent_state', None)
    if report:
        report = report.last_report
    if not report:
        await update.message.reply_text("Monitor has not completed a health check yet.")
        return
    text = format_health_text(report)
    await update.message.reply_text(text, parse_mode="MarkdownV2")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages — run agent turn."""
    text = (update.message.text or "").strip()
    if not text:
        return

    chat_id = update.effective_chat.id
    session_id = f"tg_{chat_id}"
    services = context.bot_data["services"]
    loop = asyncio.get_running_loop()

    # Accumulated text deltas for final reply
    collected_text: list[str] = []
    # Track tool status message IDs for editing
    tool_messages: dict[str, int] = {}

    # --- Callback helpers (sync → async bridge) ---

    def _run_coro(coro):
        """Schedule a coroutine on the event loop from a worker thread."""
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout=60)
        except TimeoutError:
            logger.warning("_run_coro timed out after 60s for %s", coro)
            return None

    def on_text_delta(delta: str) -> None:
        collected_text.append(delta)

    def on_error(error: str) -> None:
        _run_coro(context.bot.send_message(chat_id=chat_id, text=f"❌ {error}"))

    def on_tool_start(name: str, inp: dict, tool_id: str) -> None:
        msg = _run_coro(
            context.bot.send_message(
                chat_id=chat_id,
                text=format_tool_start(name),
                parse_mode="MarkdownV2",
            )
        )
        if msg is not None:
            tool_messages[tool_id] = msg.message_id

    def on_tool_result(name: str, tool_id: str, result: dict, success: bool) -> None:
        msg_id = tool_messages.get(tool_id)
        if msg_id:
            try:
                _run_coro(
                    context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=format_tool_done(name, success),
                        parse_mode="MarkdownV2",
                    )
                )
            except TelegramError:
                logger.debug("Failed to edit tool message %s", tool_id)

    def on_mnemonic(mnemonic: str) -> None:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 删除此消息", callback_data="delete_mnemonic")]
        ])
        _run_coro(
            context.bot.send_message(
                chat_id=chat_id,
                text=format_mnemonic(mnemonic),
                parse_mode="MarkdownV2",
                reply_markup=keyboard,
            )
        )

    def on_turn_complete() -> None:
        full_text = "".join(collected_text).strip()
        if full_text:
            for chunk in split_message(full_text):
                _run_coro(context.bot.send_message(chat_id=chat_id, text=chunk))

    callbacks = TransportCallbacks(
        on_text_delta=on_text_delta,
        on_error=on_error,
        on_tool_start=on_tool_start,
        on_tool_result=on_tool_result,
        on_mnemonic=on_mnemonic,
        on_turn_complete=on_turn_complete,
    )

    # Run the blocking agent turn in a thread pool
    await loop.run_in_executor(
        _executor,
        run_agent_turn_cb,
        text,
        services,
        session_id,
        callbacks,
    )


async def handle_delete_mnemonic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback query to delete the mnemonic message."""
    query = update.callback_query
    await query.answer("消息已删除")
    await query.message.delete()


async def handle_unauthorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to users not in the allowed chat IDs list."""
    await update.message.reply_text("\u26d4 未授权访问")
