"""
Lightweight SSH helper built on top of system ssh/scp commands.
Avoids third-party dependencies while supporting key-based auth.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class SSHResult:
    command: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class SSHCommandError(RuntimeError):
    """Raised when an SSH operation fails."""

    def __init__(self, message: str, result: SSHResult) -> None:
        super().__init__(message)
        self.result = result


class SSHClient:
    """
    Thin wrapper around the system ssh/scp binaries.

    Suitable for short, synchronous operations. For long-running commands,
    prefer the Ansible runner which streams output.
    """

    def __init__(
        self,
        host: str,
        *,
        user: Optional[str] = None,
        port: int = 22,
        key_path: Optional[str] = None,
        extra_opts: Optional[Iterable[str]] = None,
        known_hosts: Optional[str] = None,
    ) -> None:
        self.host = host
        self.user = user
        self.port = port
        self.key_path = key_path
        self.extra_opts = list(extra_opts or [])
        self.known_hosts = known_hosts

    def run(self, command: str, *, timeout: Optional[int] = None, check: bool = True) -> SSHResult:
        ssh_command = self._build_ssh_command(command)
        completed = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        result = SSHResult(
            command=" ".join(ssh_command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if check and not result.ok:
            raise SSHCommandError(f"SSH command failed: {command}", result)
        return result

    def upload(self, local_path: str, remote_path: str, *, recursive: bool = False, check: bool = True) -> SSHResult:
        scp_command = self._build_scp_command(local_path, remote_path, recursive=recursive)
        completed = subprocess.run(
            scp_command,
            capture_output=True,
            text=True,
            check=False,
        )
        result = SSHResult(
            command=" ".join(scp_command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if check and not result.ok:
            raise SSHCommandError(f"SCP upload failed: {local_path} -> {remote_path}", result)
        return result

    def _build_ssh_command(self, remote_command: str) -> List[str]:
        target = self._format_target()
        base = ["ssh", "-p", str(self.port)]

        if self.key_path:
            base.extend(["-i", os.path.expanduser(self.key_path)])

        if self.known_hosts:
            base.extend(["-o", f"UserKnownHostsFile={self.known_hosts}"])
        else:
            base.extend(["-o", "StrictHostKeyChecking=accept-new"])

        for opt in self.extra_opts:
            base.extend(["-o", opt])

        base.append(target)
        base.append(remote_command if remote_command else "true")
        return base

    def _build_scp_command(self, local_path: str, remote_path: str, *, recursive: bool) -> List[str]:
        target = self._format_target()
        base = ["scp", "-P", str(self.port)]
        if recursive:
            base.append("-r")
        if self.key_path:
            base.extend(["-i", os.path.expanduser(self.key_path)])
        if self.known_hosts:
            base.extend(["-o", f"UserKnownHostsFile={self.known_hosts}"])
        else:
            base.extend(["-o", "StrictHostKeyChecking=accept-new"])
        for opt in self.extra_opts:
            base.extend(["-o", opt])

        base.append(local_path)
        base.append(f"{target}:{remote_path}")
        return base

    def _format_target(self) -> str:
        if self.user:
            return f"{self.user}@{self.host}"
        return self.host
