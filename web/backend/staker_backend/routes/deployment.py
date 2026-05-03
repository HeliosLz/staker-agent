"""Deployment endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request, current_app
from marshmallow import ValidationError as MarshmallowValidationError

from core.remote import RemoteConnectionOptions, RemoteDeploymentConfig

from core.security import redact_secrets
from ..auth import require_auth
from ..extensions import socketio
from ..services import get_services
from ..services.pipeline import PipelineService
from ..schemas.deployment import KeyGenerationSchema, KeyImportSchema
from ..schemas.pipeline import FullDeploySchema
from ..schemas.remote import RemoteDeploySchema
from ..errors import ValidationError, NotFoundError

bp = Blueprint("deploy", __name__)


@bp.route("/full", methods=["POST"])
@require_auth
def full_deploy() -> object:
    """One-click full deployment pipeline."""
    payload = request.get_json(silent=True) or {}
    try:
        data = FullDeploySchema().load(payload)
    except MarshmallowValidationError as exc:
        raise ValidationError("Invalid pipeline request", details=exc.messages) from exc

    services = get_services()
    app = current_app._get_current_object()
    remote_opts = data.get("remote")
    is_remote = bool(remote_opts)

    # Socket.IO SID for directed mnemonic delivery — required when keys will be generated
    originating_sid = request.headers.get("X-Socket-ID") or payload.get("socket_id")
    will_generate_keys = not data.get("skip_keys", False) and not is_remote
    if will_generate_keys and not originating_sid:
        raise ValidationError("X-Socket-ID header required for key generation (mnemonic delivery channel)")

    # Mutable holder so the background thread can read the job_id set after submit().
    job_ref: dict = {}

    def make_progress():
        def _emit(step, total, name, status, message):
            socketio.emit("pipeline_progress", {
                "job_id": job_ref.get("id", "unknown"),
                "step": step,
                "total": total,
                "name": name,
                "status": status,
                "message": message,
            })
        return _emit

    def pipeline_task():
        with app.app_context():
            svc = get_services()
            p = PipelineService(svc)
            cb = make_progress()

            if is_remote:
                return p.run_remote(
                    network=data["network"],
                    client=data["client"],
                    fee_recipient=data.get("fee_recipient"),
                    withdrawal_address=data.get("withdrawal_address"),
                    host=remote_opts["host"],
                    user=remote_opts.get("user"),
                    port=remote_opts.get("port", 22),
                    ssh_key=remote_opts.get("ssh_key"),
                    progress=cb,
                )
            else:
                return p.run_local(
                    network=data["network"],
                    client=data["client"],
                    fee_recipient=data.get("fee_recipient"),
                    withdrawal_address=data.get("withdrawal_address"),
                    num_validators=data.get("num_validators", 1),
                    use_lido_csm=data.get("use_lido_csm", False),
                    skip_keys=data.get("skip_keys", False),
                    keystore_password=data.get("keystore_password"),
                    progress=cb,
                )

    def on_success(job, result):
        with app.app_context():
            # Extract mnemonic from keys result BEFORE any broadcast
            mnemonic = None
            if isinstance(result, dict):
                keys = result.get("keys")
                if isinstance(keys, dict):
                    mnemonic = keys.pop("mnemonic", None)

            # Broadcast completion WITHOUT mnemonic (redacted for safety)
            socketio.emit("pipeline_complete", {
                "job_id": job.id,
                "success": True,
                "result": redact_secrets(result) if isinstance(result, dict) else {},
            })

            # Deliver mnemonic ONLY to the originating client
            if mnemonic and originating_sid:
                socketio.emit("pipeline_mnemonic", {
                    "job_id": job.id,
                    "mnemonic": mnemonic,
                }, to=originating_sid)

    def on_failure(job, exc):
        with app.app_context():
            socketio.emit("pipeline_complete", {
                "job_id": job.id,
                "success": False,
                "error": redact_secrets(str(exc)),
            })

    job = services.jobs.submit(
        "full_pipeline",
        pipeline_task,
        on_success=on_success,
        on_failure=on_failure,
    )
    job_ref["id"] = job.id

    response = jsonify({
        "success": True,
        "data": {
            "job": job.to_dict(),
            "mode": "remote" if is_remote else "local",
            "links": {"self": f"/api/jobs/{job.id}"},
        },
    })
    response.status_code = 202
    response.headers["Location"] = f"/api/jobs/{job.id}"
    return response


@bp.route("/start", methods=["POST"])
@require_auth
def start_deployment() -> object:
    payload = request.get_json(silent=True) or {}
    services = get_services()
    app = current_app._get_current_object()

    remote_payload = payload.get("remote")

    if remote_payload:
        try:
            remote_data = RemoteDeploySchema().load(remote_payload)
        except MarshmallowValidationError as exc:
            raise ValidationError("Invalid remote deployment request", details=exc.messages) from exc

        connection_data = remote_data["connection"]
        deployment_data = remote_data["deployment"]

        connection = RemoteConnectionOptions(
            host=connection_data["host"],
            user=connection_data.get("user"),
            port=connection_data.get("port", 22),
            ssh_key=connection_data.get("ssh_key"),
        )
        deployment = RemoteDeploymentConfig(
            network=deployment_data.get("network"),
            client=deployment_data.get("client"),
            fee_recipient=deployment_data.get("fee_recipient"),
            withdrawal_address=deployment_data.get("withdrawal_address"),
        )

        def remote_task():
            with app.app_context():
                return get_services().remote.deploy(connection=connection, deployment=deployment)

        job = services.jobs.submit("remote_deployment", remote_task)
        mode = "remote"
    else:

        def task():
            with app.app_context():
                return get_services().deployment.start()

        job = services.jobs.submit("deployment", task)
        mode = "local"

    response = jsonify(
        {
            "success": True,
            "data": {
                "job": job.to_dict(),
                "mode": mode,
                "links": {
                    "self": f"/api/jobs/{job.id}",
                },
            },
        }
    )
    response.status_code = 202
    response.headers["Location"] = f"/api/jobs/{job.id}"
    return response


@bp.route("/keys/generate", methods=["POST"])
@require_auth
def generate_keys() -> object:
    payload = request.get_json(silent=True) or {}
    try:
        data = KeyGenerationSchema().load(payload)
    except MarshmallowValidationError as exc:
        raise ValidationError("Invalid key generation request", details=exc.messages) from exc

    services = get_services()

    try:
        result = services.deployment.generate_keys(
            network=data.get("network", "holesky"),
            num_validators=int(data.get("num_validators", 1)),
            withdrawal_address=data.get("withdrawal_address"),
            use_lido_csm=bool(data.get("use_lido_csm", False)),
        )
        # Deliver mnemonic via directed Socket.IO channel, redact from HTTP response
        mnemonic = result.pop("mnemonic", None) if isinstance(result, dict) else None
        socket_id = request.headers.get("X-Socket-ID")
        if mnemonic and socket_id:
            socketio.emit("pipeline_mnemonic", {"mnemonic": mnemonic}, to=socket_id)
        return jsonify({"success": result.get("status") == "success", "data": redact_secrets(result)})
    except ValueError as exc:
        raise ValidationError(redact_secrets(str(exc)))
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"success": False, "error": redact_secrets(str(exc))}), 500


@bp.route("/keys/import", methods=["POST"])
@require_auth
def import_keys() -> object:
    payload = request.get_json(silent=True) or {}
    try:
        data = KeyImportSchema().load(payload)
    except MarshmallowValidationError as exc:
        raise ValidationError("Invalid key import request", details=exc.messages) from exc

    services = get_services()
    try:
        result = services.deployment.import_keys(data["keys_path"])
        return jsonify(
            {"success": result, "data": {"message": "Keys imported successfully" if result else "Failed to import keys"}}
        )
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/keys/deposit-data", methods=["GET"])
def get_deposit_data() -> object:
    services = get_services()
    try:
        deposit_data = services.deployment.get_deposit_data()
        return jsonify({"success": True, "data": deposit_data})
    except FileNotFoundError as exc:
        raise NotFoundError(str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"success": False, "error": str(exc)}), 500


@bp.route("/lido-csm/info", methods=["GET"])
def get_lido_csm_info() -> object:
    network = request.args.get("network", "holesky")
    services = get_services()
    info = services.deployment.get_lido_csm_info(network)
    return jsonify({"success": True, "data": info})
