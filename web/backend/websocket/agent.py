"""WebSocket events for the Agent chat."""
from __future__ import annotations

import atexit
import os
from concurrent.futures import ThreadPoolExecutor

from flask import current_app
from flask_socketio import emit
from flask import request

from staker_backend.services.agent import run_agent_turn, reset_conversation, remove_session
from staker_backend.services import get_services

_MAX_WORKERS = int(os.getenv("AGENT_MAX_WORKERS", "8"))
_executor = ThreadPoolExecutor(max_workers=_MAX_WORKERS)
atexit.register(_executor.shutdown, wait=False)


def init_agent_socketio(socketio):
    """Register agent-related Socket.IO event handlers."""

    @socketio.on("agent_message")
    def handle_agent_message(data):
        """Handle an incoming user message and run the agent loop in a thread pool."""
        message = (data or {}).get("message", "").strip()
        if not message:
            emit("agent_error", {"error": "Empty message"})
            return

        sid = request.sid
        app = current_app._get_current_object()

        def _run():
            with app.app_context():
                try:
                    services = get_services()
                    run_agent_turn(message, services, socketio, sid)
                except Exception as exc:
                    socketio.emit("agent_error", {"error": str(exc)}, to=sid)

        _executor.submit(_run)

    @socketio.on("agent_reset")
    def handle_agent_reset(_data=None):
        """Reset the conversation history."""
        reset_conversation(request.sid)
        emit("agent_reset_done", {})

    @socketio.on("disconnect")
    def handle_agent_disconnect():
        """Clean up session state on disconnect."""
        remove_session(request.sid)
