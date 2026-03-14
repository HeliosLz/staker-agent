"""
System checker - Single source of truth for all system checks
No bullshit, no special cases, no repeated code.
"""
import os
import subprocess
import platform
from dataclasses import dataclass
from typing import Optional


@dataclass
class CheckResult:
    """Simple, clean data structure. No mixed responsibilities."""
    name: str
    passed: bool
    value: Optional[str] = None
    error: Optional[str] = None

    @property
    def status_emoji(self):
        """Display logic separated from data"""
        return '✅' if self.passed else '❌'

    def to_dict(self):
        """For API responses"""
        return {
            'name': self.name,
            'supported': self.passed,  # Keep API compatibility
            'status': self.status_emoji,
            'value': self.value,
            'error': self.error
        }


class SystemChecker:
    """
    Single source of truth for system checks.
    Each check is a static method - no state, no confusion.
    """

    @staticmethod
    def check_os() -> CheckResult:
        """Check OS compatibility"""
        os_type = platform.system()
        os_version = platform.release()
        supported = os_type in ['Darwin', 'Linux', 'Windows']

        return CheckResult(
            name='OS',
            passed=supported,
            value=f"{os_type} {os_version}",
            error=None if supported else f'Unsupported OS: {os_type}'
        )

    @staticmethod
    def check_python(min_version=(3, 10)) -> CheckResult:
        """Check Python version"""
        version = platform.python_version()
        parts = version.split('.')
        current = (int(parts[0]), int(parts[1]))
        passed = current >= min_version

        return CheckResult(
            name='Python',
            passed=passed,
            value=f"Python {version}",
            error=None if passed else f'Need Python {min_version[0]}.{min_version[1]}+'
        )

    @staticmethod
    def check_docker() -> CheckResult:
        """
        Check if Docker is installed and running.
        One function, one responsibility.
        """
        try:
            # First check if docker command exists
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=False  # NEVER use shell=True
            )

            if result.returncode == 0:
                version = result.stdout.strip()

                # Check if daemon is running
                ps_result = subprocess.run(
                    ['docker', 'ps'],
                    capture_output=True,
                    timeout=5,
                    shell=False
                )

                if ps_result.returncode == 0:
                    return CheckResult(
                        name='Docker',
                        passed=True,
                        value=version,
                        error=None
                    )
                else:
                    return CheckResult(
                        name='Docker',
                        passed=False,
                        value=version,
                        error='Docker daemon not running'
                    )

        except FileNotFoundError:
            return CheckResult(
                name='Docker',
                passed=False,
                value=None,
                error='Docker not installed'
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name='Docker',
                passed=False,
                value=None,
                error='Docker command timeout'
            )
        except Exception as e:
            return CheckResult(
                name='Docker',
                passed=False,
                value=None,
                error=str(e)
            )

        return CheckResult(
            name='Docker',
            passed=False,
            value=None,
            error='Unknown error'
        )

    @staticmethod
    def check_docker_compose() -> CheckResult:
        """Check Docker Compose availability"""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'version'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=False
            )

            if result.returncode == 0:
                return CheckResult(
                    name='Docker Compose',
                    passed=True,
                    value=result.stdout.strip(),
                    error=None
                )
        except Exception:
            pass

        return CheckResult(
            name='Docker Compose',
            passed=False,
            value=None,
            error='Not available'
        )

    @staticmethod
    def check_disk_space(required_gb: int = 100) -> CheckResult:
        """
        Check disk space using standard library.
        No special cases, works everywhere.
        """
        try:
            # shutil.disk_usage works on all platforms (Python 3.3+)
            import shutil
            target_path = os.path.expanduser('~/eth-docker')
            usage = shutil.disk_usage(target_path if os.path.exists(target_path) else '.')
            free_gb = usage.free / (1024 ** 3)
            passed = free_gb >= required_gb

            return CheckResult(
                name='Disk Space',
                passed=passed,
                value=f"{free_gb:.0f}GB available",
                error=None if passed else f'Need {required_gb}GB, have {free_gb:.0f}GB'
            )
        except Exception as e:
            return CheckResult(
                name='Disk Space',
                passed=False,
                value=None,
                error=f'Unable to check: {str(e)}'
            )

    @staticmethod
    def check_network(timeout: int = 5) -> CheckResult:
        """Check internet connectivity"""
        try:
            os_type = platform.system()
            cmd = ['ping', '-n' if os_type == 'Windows' else '-c', '1', '8.8.8.8']

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                shell=False
            )

            passed = result.returncode == 0

            return CheckResult(
                name='Network',
                passed=passed,
                value='Connected' if passed else None,
                error=None if passed else 'No internet connection'
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name='Network',
                passed=False,
                value=None,
                error='Connection timeout'
            )
        except Exception as e:
            return CheckResult(
                name='Network',
                passed=False,
                value=None,
                error=str(e)
            )

    @classmethod
    def run_all_checks(cls) -> dict[str, CheckResult]:
        """
        Run all checks and return results.
        Simple orchestration, no complexity.
        """
        return {
            'os': cls.check_os(),
            'python': cls.check_python(),
            'docker': cls.check_docker(),
            'docker_compose': cls.check_docker_compose(),
            'disk_space': cls.check_disk_space(),
            'network': cls.check_network()
        }
