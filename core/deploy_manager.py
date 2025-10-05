"""
Deployment manager - Simple orchestration
Each function does ONE thing and does it well.
"""
import os
import subprocess
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from core.system_checker import SystemChecker

console = Console()


class DeployManager:
    """
    Orchestrates deployment.
    No complex logic, just simple steps.
    """

    def __init__(self, eth_docker_path=None):
        self.eth_docker_path = eth_docker_path or os.path.expanduser('~/eth-docker')

    def deploy(self, services='all', skip_confirm=False):
        """
        Main deployment orchestration.
        Simple, linear, no nesting.

        Args:
            services: Services to deploy (default: 'all')
            skip_confirm: Skip confirmation prompt (for API/non-interactive use)
        """
        console.print("\n[bold cyan]🛰️  Staker Agent - Deploy[/bold cyan]\n")

        # Each step is a separate function
        if not self._check_prerequisites():
            return False

        if not skip_confirm and not self._confirm_deployment():
            return False

        if not self._pull_images():
            return False

        if not self._start_services():
            return False

        self._show_success()
        return True

    def _check_prerequisites(self) -> bool:
        """Check if ready to deploy"""
        console.print("[cyan]Checking prerequisites...[/cyan]\n")

        issues = self._find_issues()

        if issues:
            console.print("[red]❌ Prerequisites not met:[/red]")
            for issue in issues:
                console.print(f"  • {issue}")
            console.print()
            return False

        console.print("[green]✅ All prerequisites met[/green]\n")
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

    def _confirm_deployment(self) -> bool:
        """Show info and get confirmation"""
        network, client = self._get_config_info()

        console.print("[cyan]Deployment Configuration:[/cyan]")
        console.print(f"  • Network: [yellow]{network}[/yellow]")
        console.print(f"  • Client: [yellow]{client}[/yellow]")
        console.print(f"  • Location: [yellow]{self.eth_docker_path}[/yellow]\n")

        self._show_services_list(network)

        if network == 'mainnet':
            self._show_mainnet_warning()

        return Confirm.ask("\n[bold]Start deployment?[/bold]", default=True)

    def _show_services_list(self, network: str):
        """Show what will be deployed"""
        console.print("[cyan]Services to deploy:[/cyan]")
        console.print("  • Execution Layer (Geth)")
        console.print("  • Consensus Layer (Beacon Node)")
        console.print("  • Validator Client")

        if network in ['mainnet', 'holesky']:
            console.print("  • Prometheus (Metrics)")
            console.print("  • Grafana (Dashboard)")

        console.print()

    def _show_mainnet_warning(self):
        """Warn about mainnet deployment"""
        console.print("[bold yellow]⚠️  MAINNET DEPLOYMENT[/bold yellow]")
        console.print("  • This will connect to Ethereum mainnet")
        console.print("  • Ensure you have deposited 32 ETH")
        console.print("  • Initial sync may take several days")
        console.print("  • Monitor your node regularly\n")

    def _pull_images(self) -> bool:
        """Pull Docker images"""
        console.print("\n[cyan]📥 Pulling Docker images...[/cyan]")
        console.print("[yellow]This may take several minutes on first run...[/yellow]\n")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Pulling images...", total=None)

                result = subprocess.run(
                    ['docker', 'compose', 'pull'],
                    cwd=self.eth_docker_path,
                    capture_output=True,
                    text=True,
                    shell=False
                )

                progress.remove_task(task)

                if result.returncode != 0:
                    console.print(f"[red]❌ Failed to pull images:[/red]")
                    console.print(result.stderr)
                    return False

            console.print("[green]✅ Images pulled successfully[/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False

    def _start_services(self) -> bool:
        """Start Docker services"""
        console.print("[cyan]🚀 Starting services...[/cyan]\n")

        try:
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True,
                shell=False
            )

            if result.returncode == 0:
                console.print("[green]✅ Services started successfully![/green]\n")
                return True
            else:
                console.print(f"[red]❌ Failed to start services:[/red]")
                console.print(result.stderr)
                console.print()
                return False

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False

    def _show_success(self):
        """Show post-deployment info"""
        network, _ = self._get_config_info()

        console.print("=" * 60)
        console.print("[bold green]🎉 Deployment Complete![/bold green]")
        console.print("=" * 60 + "\n")

        self._show_running_services()
        self._show_monitoring_commands()
        self._show_sync_times(network)
        self._show_next_steps()

        if network == 'mainnet':
            self._show_mainnet_reminders()

    def _show_running_services(self):
        """Show what's running"""
        console.print("[cyan]📊 What's running:[/cyan]")
        console.print("  • Execution Layer (Geth) - Syncing blockchain")
        console.print("  • Consensus Layer - Syncing beacon chain")
        console.print("  • Validator Client - Waiting for keys\n")

    def _show_monitoring_commands(self):
        """Show monitoring commands"""
        console.print("[cyan]🔍 Monitor your node:[/cyan]")
        console.print("  • Status: [yellow]python3 cli.py status[/yellow]")
        console.print("  • Logs: [yellow]python3 cli.py logs[/yellow]")
        console.print("  • Grafana: [yellow]http://localhost:3000[/yellow] (if enabled)\n")

    def _show_sync_times(self, network: str):
        """Show expected sync times"""
        console.print("[cyan]⏱️  Initial Sync Time:[/cyan]")

        if network == 'mainnet':
            console.print("  • Execution Layer: 1-3 days")
            console.print("  • Consensus Layer: 2-8 hours (with checkpoint sync)")
        else:
            console.print("  • Execution Layer: 2-6 hours")
            console.print("  • Consensus Layer: 30 minutes - 2 hours (with checkpoint sync)")

        console.print()

    def _show_next_steps(self):
        """Show next steps"""
        console.print("[cyan]📝 Next steps:[/cyan]")
        console.print("  1. Wait for sync to complete:")
        console.print("     [yellow]python3 cli.py status[/yellow]\n")
        console.print("  2. Import your validator keys:")
        console.print("     [yellow]cp ~/eth-docker/.eth/validator_keys/keystore-*.json ~/eth-docker/.eth/validators/[/yellow]\n")
        console.print("  3. Restart to load keys:")
        console.print("     [yellow]python3 cli.py stop && python3 cli.py start[/yellow]\n")
        console.print("  4. Monitor validator status:")
        console.print("     [yellow]python3 cli.py status --detailed[/yellow]\n")

    def _show_mainnet_reminders(self):
        """Show mainnet-specific reminders"""
        console.print("[bold yellow]⚠️  Important Reminders:[/bold yellow]")
        console.print("  • Keep your server online 24/7")
        console.print("  • Monitor for updates regularly")
        console.print("  • Backup your keys securely")
        console.print("  • Join EthStaker Discord for support\n")

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
        console.print("[yellow]Stopping validator node...[/yellow]\n")

        try:
            result = subprocess.run(
                ['docker', 'compose', 'down'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True,
                shell=False
            )

            if result.returncode == 0:
                console.print("[green]✅ Node stopped successfully[/green]\n")
                return True
            else:
                console.print(f"[red]❌ Error: {result.stderr}[/red]\n")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False

    def start(self):
        """Start all services"""
        console.print("[green]Starting validator node...[/green]\n")

        try:
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True,
                shell=False
            )

            if result.returncode == 0:
                console.print("[green]✅ Node started successfully[/green]\n")
                return True
            else:
                console.print(f"[red]❌ Error: {result.stderr}[/red]\n")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False
