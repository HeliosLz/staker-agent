"""Node status and lifecycle services."""
from __future__ import annotations

from typing import Any, Dict

from core.node.status import StatusMonitor
from ..repositories.docker import DockerComposeRepository, CommandError


class StatusService:
    """Manage node status checks and lifecycle operations."""

    def __init__(self, docker: DockerComposeRepository, eth_docker_path: str) -> None:
        self._docker = docker
        self._eth_docker_path = eth_docker_path

    def get_status(self) -> Dict[str, Any]:
        monitor = StatusMonitor(self._eth_docker_path)
        return {
            "containers": monitor.get_container_status(),
            "sync": monitor.get_sync_status(),
        }

    def fetch_logs(self, service: str, lines: str) -> Dict[str, Any]:
        try:
            logs = self._docker.logs(service, lines)
            return {
                "service": service,
                "logs": logs,
            }
        except CommandError as exc:
            raise RuntimeError(exc.result.stderr.strip() or "Failed to fetch logs") from exc

    def start(self) -> None:
        self._docker.up()

    def stop(self) -> None:
        self._docker.down()

    def restart(self) -> None:
        self._docker.restart()
