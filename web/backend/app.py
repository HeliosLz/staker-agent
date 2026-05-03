"""Staker Agent - Flask backend entrypoint."""
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from staker_backend import create_app  # noqa: E402
from staker_backend.auth import DEFAULT_HOST  # noqa: E402
from staker_backend.extensions import socketio  # noqa: E402
from websocket import init_socketio  # noqa: E402

app = create_app()
init_socketio(socketio)


def _print_banner(host: str, port: int) -> None:
    print("🚀 Starting Staker Agent API Server...")
    print(f"📍 URL: http://{host}:{port}")
    print("🔌 WebSocket enabled")


if __name__ == "__main__":
    host = os.getenv("STAKER_AGENT_HOST", DEFAULT_HOST)
    port = int(os.getenv("STAKER_AGENT_PORT", "5001"))
    debug = bool(app.config.get("DEBUG", False))

    _print_banner(host, port)

    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=debug,
    )
