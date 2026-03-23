"""Agent API Key management routes."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..services.agent import set_api_key, get_api_key_status

bp = Blueprint("agent", __name__)


@bp.route("/apikey", methods=["POST"])
def configure_api_key():
    """Validate and store an API key (OpenRouter)."""
    data = request.get_json(silent=True) or {}
    key = data.get("api_key", "").strip()
    if not key:
        return jsonify({"success": False, "error": "api_key is required"}), 400

    ok, error = set_api_key(key)
    if ok:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": error}), 400


@bp.route("/apikey/status", methods=["GET"])
def api_key_status():
    """Check whether an API key is configured."""
    return jsonify({"configured": get_api_key_status()})
