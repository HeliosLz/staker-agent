"""
Remote preflight checks executed over SSH.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .ssh_client import SSHClient, SSHCommandError


@dataclass
class RemotePreflightResult:
    host: str
    os_info: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    docker: Dict[str, Any] = field(default_factory=dict)
    disk: Dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


class RemotePreflightChecker:
    """Collects remote host information needed prior to deployment."""

    def __init__(self, ssh_client: SSHClient) -> None:
        self.ssh = ssh_client

    def run(self) -> RemotePreflightResult:
        result = RemotePreflightResult(host=self.ssh.host)

        try:
            result.os_info = self._gather_os_info()
            result.resources = self._gather_resources()
            result.docker = self._check_docker()
            result.disk = self._check_disk()
        except SSHCommandError as exc:
            result.issues.append(str(exc))

        self._evaluate_requirements(result)
        return result

    def _gather_os_info(self) -> Dict[str, Any]:
        response = self.ssh.run(
            "uname -s && uname -r && uname -m",
            check=True,
        )
        parts = response.stdout.strip().splitlines()
        distro = self.ssh.run("cat /etc/os-release || true", check=False)
        return {
            "kernel": parts[0] if parts else "",
            "kernel_release": parts[1] if len(parts) > 1 else "",
            "architecture": parts[2] if len(parts) > 2 else "",
            "os_release": distro.stdout,
        }

    def _gather_resources(self) -> Dict[str, Any]:
        cpu = self.ssh.run("nproc", check=True).stdout.strip()
        mem = self.ssh.run("free -m | awk '/Mem:/ {print $2}'", check=True).stdout.strip()
        return {
            "cpu_cores": int(cpu) if cpu.isdigit() else cpu,
            "memory_mb": int(mem) if mem.isdigit() else mem,
        }

    def _check_docker(self) -> Dict[str, Any]:
        result = self.ssh.run("docker --version", check=False)
        return {
            "installed": result.ok,
            "version": result.stdout.strip(),
            "error": result.stderr.strip(),
        }

    def _check_disk(self) -> Dict[str, Any]:
        response = self.ssh.run("df -h / | tail -1 | awk '{print $2\",\"$4}'", check=True)
        parts = response.stdout.strip().split(",") if response.stdout else []
        total = parts[0] if parts else ""
        free = parts[1] if len(parts) > 1 else ""
        return {
            "total": total,
            "free": free,
        }

    def _evaluate_requirements(self, result: RemotePreflightResult) -> None:
        resources = result.resources
        if isinstance(resources.get("cpu_cores"), int) and resources["cpu_cores"] < 2:
            result.issues.append("CPU cores less than 2")
        if isinstance(resources.get("memory_mb"), int) and resources["memory_mb"] < 8000:
            result.issues.append("Memory below 8GB")

        if not result.docker.get("installed"):
            result.issues.append("Docker is not installed")
