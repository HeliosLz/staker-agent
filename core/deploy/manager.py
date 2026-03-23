"""
Deployment manager - Simple orchestration
Each function does ONE thing and does it well.
"""
import os
import subprocess
from typing import Callable, Optional

from core.system.checker import SystemChecker
from core.exceptions import PrerequisiteFailedError, DockerExecutionError


class DeployManager:
    """
    Orchestrates deployment.
    No complex logic, just simple steps.
    """

    def __init__(self, eth_docker_path=None):
        self.eth_docker_path = eth_docker_path or os.path.expanduser('~/eth-docker')

    def check_prerequisites(self):
        """Check if ready to deploy and raise error if not."""
        issues = self._find_issues()
        if issues:
            raise PrerequisiteFailedError(issues)

    def deploy(self, services: str = 'all', status_callback: Optional[Callable[[str, dict], None]] = None) -> bool:
        """
        Main deployment orchestration.
        Simple, linear, no nesting.

        Args:
            services: Services to deploy (default: 'all')
            status_callback: Optional callback for reporting progress back to the caller.
        """
        if status_callback:
            status_callback("step", {"step": "prerequisites", "message": "Checking prerequisites..."})
        
        self.check_prerequisites()

        if status_callback:
            status_callback("step", {"step": "pulling", "message": "Pulling Docker images..."})
        
        self._pull_images()

        if status_callback:
            status_callback("step", {"step": "starting", "message": "Starting services..."})
            
        self._start_services()

        if status_callback:
            status_callback("success", {"message": "Deployment completed successfully."})
            
        return True

    def _find_issues(self) -> list[str]:
        """Find what's missing. Simple list."""
        issues = []

        if not os.path.exists(self.eth_docker_path):
            issues.append("eth-docker not installed (run: python3 cli.py setup)")

        env_file = os.path.join(self.eth_docker_path, '.env')
        if not os.path.exists(env_file):
            issues.append("Configuration not found (run: python3 cli.py configure)")

        docker_result = SystemChecker.check_docker()
        if not docker_result.passed:
            issues.append(f"Docker: {docker_result.error}")

        return issues

    def get_deployment_info(self) -> dict:
        """Get deployment configuration for display."""
        network, client = self._get_config_info()
        return {
            "network": network,
            "client": client,
            "location": self.eth_docker_path
        }

    def _pull_images(self):
        """Pull Docker images"""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'pull'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True,
                shell=False
            )

            if result.returncode != 0:
                raise DockerExecutionError("docker compose pull", result.stderr)

        except Exception as e:
            if isinstance(e, DockerExecutionError):
                raise
            raise DockerExecutionError("docker compose pull", str(e))

    def _start_services(self):
        """Start Docker services, auto-cleaning orphans and stale networks."""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d', '--remove-orphans'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True,
                shell=False,
            )

            if result.returncode != 0:
                # Retry: network conflict or orphan containers — tear down first
                if 'network' in result.stderr.lower() or 'orphan' in result.stderr.lower():
                    subprocess.run(
                        ['docker', 'compose', 'down', '--remove-orphans'],
                        cwd=self.eth_docker_path,
                        capture_output=True, text=True, timeout=60,
                    )
                    result = subprocess.run(
                        ['docker', 'compose', 'up', '-d', '--remove-orphans'],
                        cwd=self.eth_docker_path,
                        capture_output=True, text=True,
                    )
                if result.returncode != 0:
                    raise DockerExecutionError("docker compose up -d", result.stderr)

        except Exception as e:
            if isinstance(e, DockerExecutionError):
                raise
            raise DockerExecutionError("docker compose up -d", str(e))

    def _get_config_info(self) -> tuple[str, str]:
        """Extract config from .env file"""
        env_file = os.path.join(self.eth_docker_path, '.env')
        network = 'unknown'
        client = 'unknown'

        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('NETWORK='):
                        network = line.split('=')[1].strip()
                    elif line.startswith('COMPOSE_FILE='):
                        compose_file = line.split('=')[1].strip()
                        client = self._parse_client_name(compose_file)
        except Exception:
            pass

        return network, client

    def _parse_client_name(self, compose_file: str) -> str:
        """Parse client name from compose file path"""
        client_map = {
            'lighthouse': 'Lighthouse + Geth',
            'prysm': 'Prysm + Geth',
            'teku': 'Teku + Geth',
            'nimbus': 'Nimbus + Geth'
        }

        for key, name in client_map.items():
            if key in compose_file:
                return name

        return 'unknown'

    def get_status(self):
        """Get deployment status"""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'ps'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True,
                shell=False
            )
            return result.stdout
        except Exception:
            return None

    def stop(self):
        """Stop all services"""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'down'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True,
                shell=False
            )

            if result.returncode != 0:
                raise DockerExecutionError("docker compose down", result.stderr)
            return True
        except Exception as e:
            if isinstance(e, DockerExecutionError):
                raise
            raise DockerExecutionError("docker compose down", str(e))

    def start(self):
        """Start all services"""
        self._start_services()
        return True
