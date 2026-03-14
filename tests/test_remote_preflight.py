from types import SimpleNamespace

import pytest

from core.remote.preflight import RemotePreflightChecker


class FakeSSH:
    def __init__(self, responses, host="fake_host"):
        self.responses = responses
        self.host = host

    def run(self, command, check=True):
        if command not in self.responses:
            raise AssertionError(f"Unexpected command: {command}")
        result = self.responses[command]
        if isinstance(result, Exception):
            raise result
        if isinstance(result, str):
            stdout = result
            stderr = ""
            ok = True
        else:
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            ok = result.get("ok", True)
        return SimpleNamespace(stdout=stdout, stderr=stderr, ok=ok)


def test_preflight_passes_when_requirements_met():
    ssh = FakeSSH(
        {
            "uname -s && uname -r && uname -m": "Linux\n6.1\nx86_64\n",
            "cat /etc/os-release || true": "NAME=Debian\n",
            "nproc": "4\n",
            "free -m | awk '/Mem:/ {print $2}'": "16000\n",
            "docker --version": {"stdout": "Docker version 24.0", "ok": True},
            "df -h / | tail -1 | awk '{print $2\",\"$4}'": "200G,120G\n",
        }
    )

    checker = RemotePreflightChecker(ssh)  # type: ignore[arg-type]
    result = checker.run()

    assert result.ok
    assert result.resources["cpu_cores"] == 4
    assert result.resources["memory_mb"] == 16000
    assert result.docker["installed"] is True
    assert result.disk["free"] == "120G"


def test_preflight_flags_missing_docker_and_resources():
    ssh = FakeSSH(
        {
            "uname -s && uname -r && uname -m": "Linux\n6.1\nx86_64\n",
            "cat /etc/os-release || true": "NAME=Debian\n",
            "nproc": "1\n",
            "free -m | awk '/Mem:/ {print $2}'": "2000\n",
            "docker --version": {"stdout": "", "stderr": "not installed", "ok": False},
            "df -h / | tail -1 | awk '{print $2\",\"$4}'": "50G,10G\n",
        }
    )

    checker = RemotePreflightChecker(ssh)  # type: ignore[arg-type]
    result = checker.run()

    assert not result.ok
    assert any("CPU" in issue for issue in result.issues)
    assert any("Memory" in issue for issue in result.issues)
    assert any("Docker" in issue for issue in result.issues)
