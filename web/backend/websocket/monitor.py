"""WebSocket events for health monitor subscriptions."""
from __future__ import annotations

from flask_socketio import emit, join_room, leave_room

from staker_backend.services import get_services


def init_monitor_socketio(socketio):
    """Register health monitor Socket.IO event handlers."""

    @socketio.on("subscribe_health")
    def handle_subscribe(_data=None):
        join_room("health_updates")
        # Push current cached report immediately
        try:
            services = get_services()
            if services.agent_state and services.agent_state.last_report:
                emit("health_update", services.agent_state.last_report)
        except Exception:
            pass

    @socketio.on("unsubscribe_health")
    def handle_unsubscribe(_data=None):
        leave_room("health_updates")
