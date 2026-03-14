"""
Status monitoring
"""
import os
import subprocess
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class StatusMonitor:
    def __init__(self, eth_docker_path=None):
        self.eth_docker_path = eth_docker_path or os.path.expanduser('~/eth-docker')

    def get_container_status(self):
        """Get Docker container status"""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'ps', '--format', 'json'],
                cwd=self.eth_docker_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                # Parse JSON output (one object per line)
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            containers.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
                return containers
            return []

        except Exception:
            return []

    def show_status(self, detailed=False):
        """Display node status"""

        console.print("\n[bold cyan]🛰️  Staker Agent - Status[/bold cyan]\n")

        # Check if eth-docker exists
        if not os.path.exists(self.eth_docker_path):
            console.print("[red]❌ eth-docker not found.[/red]")
            console.print("[yellow]Run 'python3 cli.py setup' first.[/yellow]\n")
            return False

        # Check if configured
        env_file = os.path.join(self.eth_docker_path, '.env')
        if not os.path.exists(env_file):
            console.print("[red]❌ Not configured.[/red]")
            console.print("[yellow]Run 'python3 cli.py configure' first.[/yellow]\n")
            return False

        # Get configuration info
        network, client = self._get_config_info(env_file)
        console.print(f"[cyan]Network:[/cyan] {network}")
        console.print(f"[cyan]Client:[/cyan] {client}\n")

        # Get container status
        containers = self.get_container_status()

        if not containers:
            console.print("[yellow]⚠️  No containers running.[/yellow]")
            console.print("[yellow]Run 'python3 cli.py deploy' to start your node.[/yellow]\n")
            return False

        # Display container status
        table = Table(title="Container Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("State", style="white")

        for container in containers:
            service = container.get('Service', 'unknown')
            status = container.get('Status', 'unknown')
            state = container.get('State', 'unknown')

            # Color code the state
            if state == 'running':
                state_colored = f"[green]{state}[/green]"
            elif state in ['restarting', 'paused']:
                state_colored = f"[yellow]{state}[/yellow]"
            else:
                state_colored = f"[red]{state}[/red]"

            table.add_row(service, status, state_colored)

        console.print(table)
        console.print()

        # Show sync status if detailed
        if detailed:
            self._show_sync_status()

        # Show next steps
        running_count = sum(1 for c in containers if c.get('State') == 'running')
        if running_count > 0:
            console.print("[green]✅ Node is running[/green]\n")
            console.print("[cyan]Useful commands:[/cyan]")
            console.print("  • View logs: [yellow]python3 cli.py logs[/yellow]")
            console.print("  • Stop node: [yellow]python3 cli.py stop[/yellow]")
            console.print("  • Grafana dashboard: [yellow]http://localhost:3000[/yellow] (if enabled)\n")
        else:
            console.print("[yellow]⚠️  Some services are not running properly.[/yellow]")
            console.print("[yellow]Check logs: python3 cli.py logs[/yellow]\n")

        return True

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

    def _show_sync_status(self):
        """Show detailed sync status"""
        console.print("[cyan]Sync Status:[/cyan]")
        console.print("[yellow]  Note: Sync status details require API access (coming soon)[/yellow]\n")

    def show_logs(self, service='all', follow=False):
        """Show container logs"""

        if not os.path.exists(self.eth_docker_path):
            console.print("[red]❌ eth-docker not found.[/red]\n")
            return False

        try:
            cmd = ['docker', 'compose', 'logs']

            if follow:
                cmd.append('-f')
            else:
                cmd.extend(['--tail', '50'])

            if service != 'all':
                # Map service names to container names
                service_map = {
                    'execution': 'geth',
                    'consensus': 'lighthouse',  # or prysm, teku, nimbus
                    'validator': 'validator'
                }
                service_name = service_map.get(service, service)
                cmd.append(service_name)

            result = subprocess.run(
                cmd,
                cwd=self.eth_docker_path
            )

            return result.returncode == 0

        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped following logs[/yellow]\n")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False
