"""Docker compose repository."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class CommandError(RuntimeError):
    """Raised when a command execution fails."""

    def __init__(self, message: str, result: CommandResult) -> None:
        super().__init__(message)
        self.result = result


class DockerComposeRepository:
    """Wrapper for docker compose command execution."""

    def __init__(self, workdir: str) -> None:
        self.workdir = workdir

    def logs(self, service: str, lines: str) -> str:
        result = self._run(["docker", "compose", "logs", "--tail", lines, service])
        return result.stdout

    def up(self) -> None:
        self._run(["docker", "compose", "up", "-d"])

    def down(self) -> None:
        self._run(["docker", "compose", "down"])

    def restart(self) -> None:
        self._run(["docker", "compose", "restart"])

    def _run(self, command: Sequence[str]) -> CommandResult:
        completed = subprocess.run(
            command,
            cwd=self.workdir,
            capture_output=True,
            text=True,
        )
        result = CommandResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )
        if not result.ok:
            message = result.stderr.strip() or f"Command failed: {' '.join(command)}"
            raise CommandError(message, result)
        return result
