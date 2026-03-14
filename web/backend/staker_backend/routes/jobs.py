"""Job monitoring endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify

from ..services import get_services
from ..errors import NotFoundError

bp = Blueprint("jobs", __name__)


@bp.route("/", methods=["GET"])
def list_jobs() -> object:
    services = get_services()
    data = services.jobs.list()
    return jsonify({"success": True, "data": data})


@bp.route("/<job_id>", methods=["GET"])
def get_job(job_id: str) -> object:
    services = get_services()
    job = services.jobs.get(job_id)
    if not job:
        raise NotFoundError("Job not found")
    return jsonify({"success": True, "data": job})
