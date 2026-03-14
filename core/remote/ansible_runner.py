"""
Ansible runner utility to drive playbooks programmatically.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class AnsibleResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class AnsibleExecutionError(RuntimeError):
    """Raised when ansible-playbook invocation fails."""

    def __init__(self, message: str, result: AnsibleResult) -> None:
        super().__init__(message)
        self.result = result


class AnsibleRunner:
    """
    Wrapper around `ansible-playbook` CLI.

    Assumes Ansible is installed on the orchestrating machine.
    """

    def __init__(self, *, working_dir: Optional[str] = None, binary: str = "ansible-playbook") -> None:
        self.working_dir = working_dir
        self.binary = binary

    def run(
        self,
        playbook_path: str,
        *,
        inventory: Optional[str] = None,
        extra_vars: Optional[Dict[str, object]] = None,
        tags: Optional[Iterable[str]] = None,
        check: bool = False,
        timeout: Optional[int] = None,
    ) -> AnsibleResult:
        command: List[str] = [self.binary, playbook_path]
        if not shutil.which(self.binary):
            raise FileNotFoundError(f"ansible binary '{self.binary}' not found in PATH")
        if inventory:
            command.extend(["-i", inventory])

        temp_vars_file: Optional[tempfile.NamedTemporaryFile] = None

        try:
            if extra_vars:
                temp_vars_file = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
                json.dump(extra_vars, temp_vars_file)
                temp_vars_file.flush()
                temp_vars_file.close()
                command.extend(["-e", f"@{temp_vars_file.name}"])

            if tags:
                command.extend(["--tags", ",".join(tags)])

            if check:
                command.append("--check")

            completed = subprocess.run(
                command,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            result = AnsibleResult(
                command=command,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )

            if not result.ok:
                raise AnsibleExecutionError(f"Ansible playbook failed: {playbook_path}", result)

            return result

        finally:
            if temp_vars_file:
                try:
                    Path(temp_vars_file.name).unlink(missing_ok=True)
                except Exception:
                    pass
