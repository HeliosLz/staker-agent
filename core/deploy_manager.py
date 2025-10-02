"""
Deployment manager for eth-docker
"""
import os
import subprocess
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class DeployManager:
    def __init__(self, eth_docker_path=None):
        self.eth_docker_path = eth_docker_path or os.path.expanduser('~/eth-docker')

    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        issues = []

        # Check if eth-docker exists
        if not os.path.exists(self.eth_docker_path):
            issues.append("eth-docker not installed (run: python3 cli.py setup)")

        # Check if .env exists
        env_file = os.path.join(self.eth_docker_path, '.env')
        if not os.path.exists(env_file):
            issues.append("Configuration not found (run: python3 cli.py configure)")

        # Check if Docker is running
        try:
            result = subprocess.run(
                ['docker', 'ps'],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                issues.append("Docker is not running")
        except Exception:
            issues.append("Docker is not installed or not running")

        return issues

    def deploy(self, services='all'):
        """Deploy the validator node"""

        console.print("\n[bold cyan]🛰️  Staker Agent - Deploy[/bold cyan]\n")

        # Check prerequisites
        console.print("[cyan]Checking prerequisites...[/cyan]\n")
        issues = self.check_prerequisites()

        if issues:
            console.print("[red]❌ Prerequisites not met:[/red]")
            for issue in issues:
                console.print(f"  • {issue}")
            console.print()
            return False

        console.print("[green]✅ All prerequisites met[/green]\n")

        # Show deployment info
        env_file = os.path.join(self.eth_docker_path, '.env')
        network, client = self._get_config_info(env_file)

        console.print("[cyan]Deployment Configuration:[/cyan]")
        console.print(f"  • Network: [yellow]{network}[/yellow]")
        console.print(f"  • Client: [yellow]{client}[/yellow]")
        console.print(f"  • Location: [yellow]{self.eth_docker_path}[/yellow]\n")

        # Show what will be deployed
        console.print("[cyan]Services to deploy:[/cyan]")
        console.print("  • Execution Layer (Geth)")
        console.print("  • Consensus Layer (Beacon Node)")
        console.print("  • Validator Client")
        if network in ['mainnet', 'holesky']:
            console.print("  • Prometheus (Metrics)")
            console.print("  • Grafana (Dashboard)")
        console.print()

        # Show warnings
        if network == 'mainnet':
            console.print("[bold yellow]⚠️  MAINNET DEPLOYMENT[/bold yellow]")
            console.print("  • This will connect to Ethereum mainnet")
            console.print("  • Ensure you have deposited 32 ETH")
            console.print("  • Initial sync may take several days")
            console.print("  • Monitor your node regularly\n")

        # Confirm deployment
        if not Confirm.ask("\n[bold]Start deployment?[/bold]", default=True):
            console.print("[yellow]Deployment cancelled.[/yellow]\n")
            return False

        # Pull Docker images
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
                    text=True
                )

                if result.returncode != 0:
                    progress.remove_task(task)
                    console.print(f"[red]❌ Failed to pull images:[/red]")
                    console.print(result.stderr)
                    return False

                progress.remove_task(task)

            console.print("[green]✅ Images pulled successfully[/green]\n")

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False

        # Start services
        console.print("[cyan]🚀 Starting services...[/cyan]\n")

        try:
            result = subprocess.run(
                ['docker', 'compose', 'up', '-d'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                console.print("[green]✅ Services started successfully![/green]\n")
                self._show_post_deployment_info(network)
                return True
            else:
                console.print(f"[red]❌ Failed to start services:[/red]")
                console.print(result.stderr)
                console.print()
                return False

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False

    def _get_config_info(self, env_file):
        """Extract network and client info from .env file"""
        network = 'unknown'
        client = 'unknown'

        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('NETWORK='):
                        network = line.split('=')[1].strip()
                    elif line.startswith('COMPOSE_FILE='):
                        compose_file = line.split('=')[1].strip()
                        if 'lighthouse' in compose_file:
                            client = 'Lighthouse + Geth'
                        elif 'prysm' in compose_file:
                            client = 'Prysm + Geth'
                        elif 'teku' in compose_file:
                            client = 'Teku + Geth'
                        elif 'nimbus' in compose_file:
                            client = 'Nimbus + Geth'
        except Exception:
            pass

        return network, client

    def _show_post_deployment_info(self, network):
        """Show information after successful deployment"""

        console.print("="*60)
        console.print("[bold green]🎉 Deployment Complete![/bold green]")
        console.print("="*60 + "\n")

        console.print("[cyan]📊 What's running:[/cyan]")
        console.print("  • Execution Layer (Geth) - Syncing blockchain")
        console.print("  • Consensus Layer - Syncing beacon chain")
        console.print("  • Validator Client - Waiting for keys\n")

        console.print("[cyan]🔍 Monitor your node:[/cyan]")
        console.print("  • Status: [yellow]python3 cli.py status[/yellow]")
        console.print("  • Logs: [yellow]python3 cli.py logs[/yellow]")
        console.print("  • Grafana: [yellow]http://localhost:3000[/yellow] (if enabled)\n")

        console.print("[cyan]⏱️  Initial Sync Time:[/cyan]")
        if network == 'mainnet':
            console.print("  • Execution Layer: 1-3 days")
            console.print("  • Consensus Layer: 2-8 hours (with checkpoint sync)")
        else:
            console.print("  • Execution Layer: 2-6 hours")
            console.print("  • Consensus Layer: 30 minutes - 2 hours (with checkpoint sync)")
        console.print()

        console.print("[cyan]📝 Next steps:[/cyan]")
        console.print("  1. Wait for sync to complete:")
        console.print("     [yellow]python3 cli.py status[/yellow]\n")
        console.print("  2. Import your validator keys:")
        console.print("     [yellow]cp ~/eth-docker/.eth/validator_keys/keystore-*.json ~/eth-docker/.eth/validators/[/yellow]\n")
        console.print("  3. Restart to load keys:")
        console.print("     [yellow]python3 cli.py stop && python3 cli.py start[/yellow]\n")
        console.print("  4. Monitor validator status:")
        console.print("     [yellow]python3 cli.py status --detailed[/yellow]\n")

        if network == 'mainnet':
            console.print("[bold yellow]⚠️  Important Reminders:[/bold yellow]")
            console.print("  • Keep your server online 24/7")
            console.print("  • Monitor for updates regularly")
            console.print("  • Backup your keys securely")
            console.print("  • Join EthStaker Discord for support\n")

    def get_status(self):
        """Get deployment status"""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'ps'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True
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
                text=True
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
                text=True
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
