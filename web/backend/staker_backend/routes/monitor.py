"""Health monitor REST endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify

from ..services import get_services

bp = Blueprint("monitor", __name__)


@bp.route("/", methods=["GET"])
def get_health():
    """Return the latest cached health report."""
    services = get_services()
    report = services.agent_state.last_report if services.agent_state else None
    return jsonify({"success": True, "data": report})


@bp.route("/alerts", methods=["GET"])
def get_alerts():
    """Return active alert records."""
    services = get_services()
    if not services.agent_state:
        return jsonify({"success": True, "data": []})
    alerts = services.agent_state.get_active_alerts()
    return jsonify({"success": True, "data": alerts})


@bp.route("/events", methods=["GET"])
def get_events():
    """Return recent action/event log."""
    services = get_services()
    if not services.agent_state:
        return jsonify({"success": True, "data": []})
    events = services.agent_state.get_recent_events(limit=50)
    return jsonify({"success": True, "data": events})
