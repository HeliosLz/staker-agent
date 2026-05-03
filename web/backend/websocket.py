"""WebSocket events for real-time progress updates."""
from __future__ import annotations

from typing import Any, Dict

from flask import current_app
from flask_socketio import emit

from staker_backend.auth import authenticate_socketio
from staker_backend.services import get_services


DEPLOYMENT_EVENTS = {
    "progress": "deployment_progress",
    "complete": "deployment_complete",
}


def init_socketio(socketio):
    """Initialise WebSocket handlers."""

    @socketio.on("connect")
    def handle_connect(auth=None):
        """客户端连接"""
        if not authenticate_socketio(auth):
            return False
        current_app.logger.info("WebSocket client connected")
        emit("connected", {"message": "Connected to Staker Agent"})

    @socketio.on("disconnect")
    def handle_disconnect():
        """客户端断开"""
        current_app.logger.info("WebSocket client disconnected")

    @socketio.on("start_deployment")
    def handle_deployment(payload: Dict[str, Any] | None = None):
        """Handle deployment request and stream progress."""
        current_app.logger.info("Received deployment request via websocket", extra={"payload": payload or {}})

        app = current_app._get_current_object()

        def run_deployment():
            with app.app_context():
                services = get_services()

                def deployment_task():
                    with app.app_context():
                        return get_services().deployment.start()

                def handle_success(job, _result):
                    with app.app_context():
                        socketio.emit(
                            DEPLOYMENT_EVENTS["complete"],
                            {"success": True, "job_id": job.id, "message": "验证节点部署任务已完成。"},
                        )

                def handle_failure(job, exc):
                    with app.app_context():  # pragma: no cover - defensive
                        current_app.logger.exception("Deployment failed", exc_info=exc)
                        socketio.emit(
                            DEPLOYMENT_EVENTS["complete"],
                            {"success": False, "job_id": job.id, "error": str(exc)},
                        )

                job = services.jobs.submit(
                    "deployment",
                    deployment_task,
                    on_success=handle_success,
                    on_failure=handle_failure,
                )

                socketio.emit(
                    DEPLOYMENT_EVENTS["progress"],
                    {
                        "step": 1,
                        "name": "启动部署",
                        "message": "部署任务已排队",
                        "progress": 5,
                        "status": "running",
                        "job_id": job.id,
                    },
                )

        socketio.start_background_task(run_deployment)
        return {"status": "started"}

    @socketio.on("start_docker_install")
    def handle_docker_install(payload: Dict[str, Any] | None = None):
        """Return instructions for Docker installation rather than executing commands."""
        current_app.logger.info("Received docker install request via websocket", extra={"payload": payload or {}})

        app = current_app._get_current_object()

        def run_install():
            with app.app_context():
                services = get_services()
                instructions = services.fixes.docker_instructions()
                socketio.emit(
                    "docker_install_progress",
                    {
                        "message": "请按提示手动完成 Docker 安装。",
                        "progress": 100,
                        "status": "completed",
                        "instructions": instructions,
                    },
                )
                socketio.emit(
                    "docker_install_complete",
                    {
                        "success": True,
                        "message": "已推送 Docker 安装指引。",
                    },
                )

        socketio.start_background_task(run_install)
        return {"status": "started"}

    return socketio
