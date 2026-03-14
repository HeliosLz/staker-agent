"""Status endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services import get_services

bp = Blueprint("status", __name__)


@bp.route("/", methods=["GET"])
def get_status() -> object:
    services = get_services()
    try:
        status = services.status.get_status()
        return jsonify({"success": True, "data": status})
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/logs", methods=["GET"])
def get_logs() -> object:
    service_name = request.args.get("service", "consensus")
    lines = request.args.get("lines", "100")

    services = get_services()
    try:
        logs = services.status.fetch_logs(service_name, lines)
        return jsonify({"success": True, "data": logs})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/start", methods=["POST"])
def start_node() -> object:
    services = get_services()
    try:
        services.status.start()
        return jsonify({"success": True, "data": {"message": "Node started successfully"}})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/stop", methods=["POST"])
def stop_node() -> object:
    services = get_services()
    try:
        services.status.stop()
        return jsonify({"success": True, "data": {"message": "Node stopped successfully"}})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/restart", methods=["POST"])
def restart_node() -> object:
    services = get_services()
    try:
        services.status.restart()
        return jsonify({"success": True, "data": {"message": "Node restarted successfully"}})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
