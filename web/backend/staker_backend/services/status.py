"""Node status and lifecycle services."""
from __future__ import annotations

from typing import Any, Dict

from core.node.status import StatusMonitor
from ..repositories.docker import DockerComposeRepository, CommandError


class StatusService:
    """Manage node status checks and lifecycle operations."""

    def __init__(self, docker: DockerComposeRepository) -> None:
        self._docker = docker

    def get_status(self) -> Dict[str, Any]:
        monitor = StatusMonitor()
        return monitor.get_container_status()

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
