"""Environment-related application services."""
from __future__ import annotations

from typing import Any, Dict, Tuple

from core.system.checker import SystemChecker


class EnvironmentService:
    """Facade for environment and capability checks."""

    def run_checks(self) -> Tuple[Dict[str, Any], bool]:
        results = SystemChecker.run_all_checks()
        data = {
            "os": results["os"].to_dict(),
            "python": results["python"].to_dict(),
            "docker": results["docker"].to_dict(),
            "disk": results["disk_space"].to_dict(),
            "network": results["network"].to_dict(),
        }
        all_passed = all(
            [
                results["os"].passed,
                results["python"].passed,
                results["docker"].passed,
                results["network"].passed,
            ]
        )
        return data, all_passed

    def check_docker(self) -> Dict[str, Any]:
        result = SystemChecker.check_docker()
        return {
            "installed": result.passed,
            "version": result.value,
            "error": result.error,
        }
