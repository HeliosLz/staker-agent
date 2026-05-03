"""
Validator for checking configuration and setup
"""
import os
from rich.console import Console
from rich.table import Table

console = Console()

class ConfigValidator:
    def __init__(self, eth_docker_path: str):
        self.eth_docker_path = eth_docker_path
        self.issues = []
        self.warnings = []

    def validate_all(self):
        """Run all validations"""
        console.print("\n[bold cyan]🔍 Validating Configuration[/bold cyan]\n")

        self._check_eth_docker_installed()
        self._check_configuration()
        self._check_compose_files()
        self._check_keys()

        return self._display_results()

    def _check_eth_docker_installed(self):
        """Check if eth-docker is installed"""
        if not os.path.exists(self.eth_docker_path):
            self.issues.append("eth-docker not installed")
            return False

        # Check if ethd script exists
        ethd_path = os.path.join(self.eth_docker_path, 'ethd')
        if not os.path.exists(ethd_path):
            self.warnings.append("ethd script not found")

        return True

    def _check_configuration(self):
        """Check if .env configuration exists and is valid"""
        env_file = os.path.join(self.eth_docker_path, '.env')

        if not os.path.exists(env_file):
            self.issues.append(".env configuration file not found")
            return False

        # Parse .env and check required fields
        required_fields = ['NETWORK', 'COMPOSE_FILE']
        found_fields = {}

        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            found_fields[key] = value

            for field in required_fields:
                if field not in found_fields:
                    self.issues.append(f"Missing required field in .env: {field}")
                elif not found_fields[field]:
                    self.warnings.append(f"Empty value for {field}")

        except Exception as e:
            self.issues.append(f"Error reading .env: {str(e)}")
            return False

        return True

    def _check_compose_files(self):
        """Check if referenced compose files exist"""
        env_file = os.path.join(self.eth_docker_path, '.env')

        if not os.path.exists(env_file):
            return False

        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('COMPOSE_FILE='):
                        compose_files = line.split('=')[1].strip()
                        # Parse colon-separated files
                        for file in compose_files.split(':'):
                            file = file.strip()
                            if file:
                                file_path = os.path.join(self.eth_docker_path, file)
                                if not os.path.exists(file_path):
                                    self.issues.append(f"Compose file not found: {file}")

        except Exception as e:
            self.warnings.append(f"Could not verify compose files: {str(e)}")

        return True

    def _check_keys(self):
        """Check if validator keys exist"""
        keys_path = os.path.join(self.eth_docker_path, '.eth', 'validator_keys')

        if not os.path.exists(keys_path):
            self.warnings.append("No validator keys directory found")
            return False

        try:
            files = os.listdir(keys_path)
            keystore_files = [f for f in files if 'keystore' in f]
            deposit_files = [f for f in files if 'deposit_data' in f]

            if not keystore_files:
                self.warnings.append("No keystore files found (run: python3 cli.py keys generate)")

            if not deposit_files:
                self.warnings.append("No deposit_data.json found")

        except Exception:
            pass

        return True

    def _display_results(self):
        """Display validation results"""

        if not self.issues and not self.warnings:
            console.print("[bold green]✅ All validations passed![/bold green]\n")
            console.print("[cyan]Your setup is ready to deploy.[/cyan]\n")
            return True

        if self.issues:
            console.print("[bold red]❌ Issues Found:[/bold red]")
            for issue in self.issues:
                console.print(f"  • {issue}")
            console.print()

        if self.warnings:
            console.print("[bold yellow]⚠️  Warnings:[/bold yellow]")
            for warning in self.warnings:
                console.print(f"  • {warning}")
            console.print()

        if self.issues:
            console.print("[yellow]Please fix the issues above before deploying.[/yellow]\n")
            return False
        else:
            console.print("[yellow]You can proceed, but address the warnings when possible.[/yellow]\n")
            return True
