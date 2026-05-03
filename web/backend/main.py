"""Unified entrypoint: Flask API + Telegram Bot."""
import os
import sys
import threading
import time
import logging

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from staker_backend import create_app  # noqa: E402
from staker_backend.auth import DEFAULT_HOST  # noqa: E402
from staker_backend.extensions import socketio  # noqa: E402
from staker_backend.services.agent import init_from_env  # noqa: E402
from websocket import init_socketio  # noqa: E402
from telegram_bot import create_telegram_app  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> None:
    app = create_app()
    init_socketio(socketio)
    init_from_env()

    with app.app_context():
        services = app.extensions["services"]

    host = os.getenv("STAKER_AGENT_HOST", DEFAULT_HOST)
    port = int(os.getenv("STAKER_AGENT_PORT", "5001"))

    # Flask + Socket.IO in a daemon thread
    _flask_error: list[BaseException] = []

    def _run_flask():
        try:
            logger.info("Flask API starting on %s:%s", host, port)
            debug = bool(app.config.get("DEBUG", False))
            socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=debug)
        except Exception as exc:
            logger.critical("Flask thread crashed: %s", exc, exc_info=True)
            _flask_error.append(exc)

    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()
    time.sleep(1)
    if _flask_error:
        raise RuntimeError(f"Flask failed to start: {_flask_error[0]}") from _flask_error[0]

    # Start Monitor Loop (if enabled)
    if services.monitor_loop:
        # Wire Telegram alert sink
        tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        alert_chat_id = os.environ.get("TELEGRAM_ALERT_CHAT_ID")
        if tg_token and alert_chat_id:
            from telegram_bot.alerts import TelegramAlertSender
            sender = TelegramAlertSender(tg_token, int(alert_chat_id))
            services.monitor_loop.add_sink(sender.send)

        # Wire WebSocket sink
        def _ws_sink(message: str) -> None:
            with app.app_context():
                socketio.emit("health_alert", {"message": message}, room="health_updates")
        services.monitor_loop.add_sink(_ws_sink)
        services.monitor_loop.set_socketio(socketio, app)

        services.monitor_loop.start()
        logger.info("Monitor loop started")

    # Telegram Bot in the main thread
    logger.info("Starting Telegram bot polling...")
    tg_app = create_telegram_app(services)
    tg_app.run_polling()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    print("🚀 Starting Staker Agent (Flask + Telegram Bot)...")
    main()
