"""Remote orchestration endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError as MarshmallowValidationError

from ..errors import ValidationError
from ..schemas.remote import RemotePreflightSchema
from ..services import get_services

bp = Blueprint("remote", __name__)


@bp.route("/preflight", methods=["POST"])
def remote_preflight() -> object:
    payload = request.get_json(silent=True) or {}
    try:
        data = RemotePreflightSchema().load(payload)
    except MarshmallowValidationError as exc:
        raise ValidationError("Invalid remote preflight request", details=exc.messages) from exc

    services = get_services()
    result = services.remote.preflight(
        host=data["host"],
        user=data.get("user"),
        port=data.get("port", 22),
        ssh_key=data.get("ssh_key"),
    )
    return jsonify(result)
