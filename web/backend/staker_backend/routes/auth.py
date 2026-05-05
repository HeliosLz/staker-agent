"""Auth check endpoint."""
from __future__ import annotations

from flask import Blueprint, jsonify

from ..auth import require_auth

bp = Blueprint("auth", __name__)


@bp.route("/check", methods=["GET"])
@require_auth
def check():
    return jsonify({"success": True})
