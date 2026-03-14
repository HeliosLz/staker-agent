"""Remote orchestration service."""
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Optional

from core.remote import (
    RemoteConnectionOptions,
    RemoteDeploymentConfig,
    RemoteDeployManager,
    RemotePreflightChecker,
    SSHClient,
)


class RemoteService:
    """Backend-facing facade for remote operations."""

    def __init__(self, ansible_dir: str, artifacts_dir: str | None = None) -> None:
        self.ansible_dir = ansible_dir
        self.artifacts_dir = artifacts_dir

    def preflight(self, *, host: str, user: Optional[str], port: int, ssh_key: Optional[str]) -> Dict[str, object]:
        connection = RemoteConnectionOptions(host=host, user=user, port=port, ssh_key=ssh_key)
        ssh = SSHClient(host, user=user, port=port, key_path=ssh_key)
        checker = RemotePreflightChecker(ssh)
        result = checker.run()
        return {
            "success": result.ok,
            "data": asdict(result),
        }

    def deploy(
        self,
        *,
        connection: RemoteConnectionOptions,
        deployment: RemoteDeploymentConfig,
    ) -> Dict[str, object]:
        manager = RemoteDeployManager(
            connection,
            deployment,
            ansible_dir=self.ansible_dir,
            artifacts_dir=self.artifacts_dir,
        )
        return manager.deploy()
