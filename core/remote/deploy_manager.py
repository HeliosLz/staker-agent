"""
Remote deployment manager orchestrating SSH preflight, artifact sync, and Ansible playbooks.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from core.config.generator import ConfigGenerator
from core.paths import get_eth_docker_path

from .ansible_runner import AnsibleRunner
from .preflight import RemotePreflightChecker, RemotePreflightResult
from .ssh_client import SSHClient, SSHCommandError

StatusCallback = Callable[[str, Dict[str, object]], None]


@dataclass
class RemoteConnectionOptions:
    host: str
    user: Optional[str] = None
    port: int = 22
    ssh_key: Optional[str] = None
    remote_base: str = "/opt/staker-agent"


@dataclass
class RemoteDeploymentConfig:
    network: Optional[str] = None
    client: Optional[str] = None
    fee_recipient: Optional[str] = None
    withdrawal_address: Optional[str] = None


class RemoteDeployManager:
    """High-level orchestration for remote validator deployment."""

    def __init__(
        self,
        connection: RemoteConnectionOptions,
        deployment: RemoteDeploymentConfig,
        *,
        ansible_dir: str | None = None,
        artifacts_dir: str | None = None,
        status_callback: Optional[StatusCallback] = None,
    ) -> None:
        self.connection = connection
        self.deployment = deployment
        self.ansible_dir = ansible_dir or os.path.join(Path.cwd(), "ansible")
        self.artifacts_dir = artifacts_dir or os.path.expanduser("~/.staker-agent/artifacts")
        self.status_callback = status_callback

    def deploy(self) -> Dict[str, object]:
        ssh = self._build_ssh_client()
        self._emit("preflight:start", {})
        preflight = RemotePreflightChecker(ssh).run()
        self._emit("preflight:complete", {"result": asdict(preflight)})

        if not preflight.ok:
            return {
                "success": False,
                "preflight": asdict(preflight),
                "message": "Remote host does not meet minimum requirements.",
            }

        self._emit("artifacts:start", {})
        archive_path, temp_dir = self._prepare_artifacts()
        try:
            remote_bundle = self._sync_artifacts(ssh, archive_path)
        finally:
            Path(archive_path).unlink(missing_ok=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
        self._emit("artifacts:complete", {"bundle": remote_bundle})

        ansible_inventory = self._write_inventory()

        setup_playbook = os.path.join(self.ansible_dir, "playbooks", "setup.yml")
        deploy_playbook = os.path.join(self.ansible_dir, "playbooks", "deploy.yml")
        runner = AnsibleRunner()

        extra_vars = {
            "staker_remote_base": self.connection.remote_base,
            "staker_bundle_path": remote_bundle,
        }

        if self.deployment.network:
            extra_vars["staker_network"] = self.deployment.network
        if self.deployment.client:
            extra_vars["staker_client"] = self.deployment.client

        if self.deployment.fee_recipient:
            extra_vars["staker_fee_recipient"] = self.deployment.fee_recipient
        if self.deployment.withdrawal_address:
            extra_vars["staker_withdrawal_address"] = self.deployment.withdrawal_address

        if os.path.exists(setup_playbook):
            self._emit("ansible:setup:start", {"playbook": setup_playbook})
            runner.run(setup_playbook, inventory=ansible_inventory, extra_vars=extra_vars)
            self._emit("ansible:setup:complete", {"playbook": setup_playbook})
        else:
            self._emit("ansible:setup:skipped", {"reason": "playbook_missing"})

        if os.path.exists(deploy_playbook):
            self._emit("ansible:deploy:start", {"playbook": deploy_playbook})
            runner.run(deploy_playbook, inventory=ansible_inventory, extra_vars=extra_vars)
            self._emit("ansible:deploy:complete", {"playbook": deploy_playbook})
        else:
            self._emit("ansible:deploy:skipped", {"reason": "playbook_missing"})

        verification = self._verify_remote(ssh)

        return {
            "success": True,
            "preflight": asdict(preflight),
            "verification": verification,
            "remote_bundle": remote_bundle,
        }

    def _build_ssh_client(self) -> SSHClient:
        return SSHClient(
            self.connection.host,
            user=self.connection.user,
            port=self.connection.port,
            key_path=self.connection.ssh_key,
        )

    def _prepare_artifacts(self) -> tuple[str, str]:
        generator = ConfigGenerator(get_eth_docker_path())
        if self.deployment.network and self.deployment.client:
            generator.generate_env(
                network=self.deployment.network,
                client=self.deployment.client,
                fee_recipient=self.deployment.fee_recipient,
                withdrawal_address=self.deployment.withdrawal_address,
            )
        source_dir = Path(generator.eth_docker_path)
        if not source_dir.exists():
            raise FileNotFoundError(f"eth-docker directory not found at {source_dir}")

        os.makedirs(self.artifacts_dir, exist_ok=True)
        tmp_dir = tempfile.mkdtemp(prefix="remote-deploy-", dir=self.artifacts_dir)
        archive_path = shutil.make_archive(
            base_name=os.path.join(tmp_dir, "eth-docker"),
            format="gztar",
            root_dir=source_dir,
        )
        return archive_path, tmp_dir

    def _sync_artifacts(self, ssh: SSHClient, archive_path: str) -> str:
        remote_dir = os.path.join(self.connection.remote_base, "bundles")
        remote_archive = os.path.join(remote_dir, os.path.basename(archive_path))
        ssh.run(f"mkdir -p {remote_dir}", check=True)
        ssh.upload(archive_path, remote_archive, recursive=False)
        ssh.run(f"mkdir -p {self.connection.remote_base}/eth-docker", check=True)
        ssh.run(
            f"tar -xzf {remote_archive} -C {self.connection.remote_base}/eth-docker --strip-components=1",
            check=True,
        )
        return remote_archive

    def _write_inventory(self) -> str:
        inventory_dir = Path(self.ansible_dir) / "inventory"
        inventory_dir.mkdir(parents=True, exist_ok=True)
        inventory_path = inventory_dir / "hosts.ini"
        ssh_user = self.connection.user or "root"
        inventory_content = "\n".join(
            [
                "[remote]",
                f"{self.connection.host} ansible_user={ssh_user} ansible_port={self.connection.port}"
                + (f" ansible_ssh_private_key_file={self.connection.ssh_key}" if self.connection.ssh_key else ""),
                "",
            ]
        )
        inventory_path.write_text(inventory_content, encoding="utf-8")
        return str(inventory_path)

    def _verify_remote(self, ssh: SSHClient) -> Dict[str, object]:
        verification = {
            "docker_ps": "",
            "services": [],
        }
        try:
            ps = ssh.run("cd {base}/eth-docker && docker compose ps".format(base=self.connection.remote_base), check=True)
            verification["docker_ps"] = ps.stdout
        except SSHCommandError as exc:
            verification["docker_ps"] = exc.result.stderr

        return verification

    def _emit(self, event: str, payload: Dict[str, object]) -> None:
        if self.status_callback:
            self.status_callback(event, payload)
