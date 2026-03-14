"""Environment endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify

from ..services import get_services

bp = Blueprint("env", __name__)


@bp.route("/check", methods=["GET"])
def check_environment() -> object:
    services = get_services()
    try:
        data, all_passed = services.environment.run_checks()
        return jsonify(
            {
                "success": True,
                "data": data,
                "all_passed": all_passed,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive
        return (
            jsonify(
                {
                    "success": False,
                    "error": "环境检查失败",
                    "details": str(exc),
                    "message": "无法完成环境检查，请确保所有必要的系统工具已安装",
                }
            ),
            500,
        )
