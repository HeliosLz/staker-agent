"""Fix and remediation endpoints."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify

from ..services import get_services

bp = Blueprint("fix", __name__)


@bp.route("/docker/install-script", methods=["GET"])
def get_docker_install_script() -> object:
    services = get_services()
    script = services.fixes.docker_install_script()
    if not script:
        return jsonify(services.fixes.docker_instructions())
    return Response(script, mimetype="text/x-shellscript")


@bp.route("/docker/instructions", methods=["GET"])
def get_docker_instructions() -> object:
    services = get_services()
    return jsonify(services.fixes.docker_instructions())


@bp.route("/docker/check", methods=["GET"])
def check_docker_status() -> object:
    services = get_services()
    result = services.fixes.check_docker()
    return jsonify(
        {
            "success": True,
            "installed": result["installed"],
            "version": result["version"],
            "error": result["error"],
        }
    )
