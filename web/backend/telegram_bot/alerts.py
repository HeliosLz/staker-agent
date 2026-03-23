"""Telegram alert sender — direct HTTP, no async bridge needed."""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class TelegramAlertSender:
    """Synchronous Telegram message sender via Bot API.

    Called from the Monitor Loop's daemon thread. Uses httpx directly
    instead of python-telegram-bot's async API to avoid event loop issues.
    """

    def __init__(self, token: str, chat_id: int) -> None:
        self._url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._chat_id = chat_id
        self._client = httpx.Client(timeout=30)

    def send(self, message: str) -> None:
        """Send a MarkdownV2 message to the configured chat."""
        try:
            resp = self._client.post(self._url, json={
                "chat_id": self._chat_id,
                "text": message,
                "parse_mode": "MarkdownV2",
            })
            if resp.status_code != 200:
                logger.warning("Telegram alert failed (%d): %s", resp.status_code, resp.text[:200])
        except Exception:
            logger.warning("Failed to send Telegram alert", exc_info=True)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
