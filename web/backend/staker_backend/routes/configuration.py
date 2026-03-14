"""Configuration endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError as MarshmallowValidationError

from ..services import get_services
from ..services.configuration import ConfigurationError
from ..schemas.configuration import ConfigRequestSchema
from ..errors import ValidationError

bp = Blueprint("config", __name__)


@bp.route("/generate", methods=["POST"])
def generate_config() -> object:
    payload = request.get_json(silent=True) or {}
    try:
        data = ConfigRequestSchema().load(payload)
    except MarshmallowValidationError as exc:
        raise ValidationError("Invalid configuration request", details=exc.messages) from exc

    services = get_services()

    try:
        config_data = services.configuration.generate(
            network=data["network"],
            client=data["client"],
            fee_recipient=data.get("fee_recipient"),
            withdrawal_address=data.get("withdrawal_address"),
        )
        return jsonify(
            {
                "success": True,
                "data": config_data,
            }
        )
    except ValueError as exc:
        raise ValidationError(str(exc))
    except ConfigurationError as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/networks", methods=["GET"])
def get_networks() -> object:
    services = get_services()
    return jsonify({"success": True, "data": services.configuration.list_networks()})


@bp.route("/clients", methods=["GET"])
def get_clients() -> object:
    services = get_services()
    return jsonify({"success": True, "data": services.configuration.list_clients()})
