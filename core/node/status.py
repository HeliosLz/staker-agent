"""
Status monitoring
"""
import json
import logging
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

logger = logging.getLogger(__name__)
console = Console()

class StatusMonitor:
    def __init__(self, eth_docker_path: str):
        self.eth_docker_path = eth_docker_path

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

    def get_sync_status(self):
        """Query sync progress from execution and consensus layer APIs."""
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_el = pool.submit(self._query_execution_sync)
            f_cl = pool.submit(self._query_consensus_sync)
        return {
            "execution": f_el.result(),
            "consensus": f_cl.result(),
        }

    def _docker_exec_wget(self, service, url, post_data=None):
        """Run wget inside a docker compose service container.

        Returns parsed JSON on success, None on failure.
        """
        cmd = ['docker', 'compose', 'exec', '-T', service, 'wget', '-qO-']
        if post_data:
            cmd += ['--header=Content-Type: application/json',
                    f'--post-data={post_data}']
        cmd.append(url)
        try:
            result = subprocess.run(
                cmd, cwd=self.eth_docker_path,
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
        except Exception as exc:
            logger.debug("docker exec wget failed for %s: %s", service, exc)
        return None

    def _query_execution_sync(self):
        """Query execution layer (Geth) sync status via JSON-RPC batch."""
        # Batch eth_syncing + eth_blockNumber in a single request
        data = self._docker_exec_wget(
            'execution', 'http://localhost:8545',
            post_data='[{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1},'
                      '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":2}]',
        )
        if data is None:
            return {"syncing": None, "error": "execution RPC not reachable"}

        # Parse batch response — array of results keyed by id
        if not isinstance(data, list):
            return {"syncing": None, "error": "unexpected response"}

        sync_result = None
        block_hex = None
        for item in data:
            rid = item.get("id")
            if rid == 1:
                sync_result = item.get("result")
            elif rid == 2:
                block_hex = item.get("result")

        if isinstance(sync_result, dict):
            current = int(sync_result.get("currentBlock", "0x0"), 16)
            highest = int(sync_result.get("highestBlock", "0x0"), 16)
            progress = (current / highest * 100) if highest > 0 else 0
            return {
                "syncing": True,
                "current_block": current,
                "highest_block": highest,
                "progress_pct": round(progress, 2),
            }

        if sync_result is False:
            block = int(block_hex, 16) if block_hex else None
            return {"syncing": False, "current_block": block}

        return {"syncing": None, "error": "unexpected response"}

    def _query_consensus_sync(self):
        """Query consensus layer sync status via Beacon API."""
        data = self._docker_exec_wget(
            'consensus', 'http://localhost:5052/eth/v1/node/syncing',
        )
        if data is None:
            return {"syncing": None, "error": "consensus API not reachable"}

        sync = data.get("data", {})
        head_slot = int(sync.get("head_slot", "0"))
        sync_distance = int(sync.get("sync_distance", "0"))
        is_syncing = sync.get("is_syncing", True)
        is_optimistic = sync.get("is_optimistic", False)

        if not is_syncing and sync_distance == 0:
            return {
                "syncing": False,
                "head_slot": head_slot,
                "is_optimistic": is_optimistic,
            }

        target_slot = head_slot + sync_distance
        progress = (head_slot / target_slot * 100) if target_slot > 0 else 0
        return {
            "syncing": True,
            "head_slot": head_slot,
            "sync_distance": sync_distance,
            "is_optimistic": is_optimistic,
            "progress_pct": round(progress, 2),
        }

    def _show_sync_status(self):
        """Show detailed sync status in CLI."""
        sync = self.get_sync_status()
        console.print("[cyan]Sync Status:[/cyan]")

        el = sync["execution"]
        if el.get("error"):
            console.print(f"  Execution: [yellow]unavailable ({el['error']})[/yellow]")
        elif el.get("syncing"):
            console.print(f"  Execution: [yellow]syncing {el['progress_pct']:.1f}% "
                          f"(block {el['current_block']}/{el['highest_block']})[/yellow]")
        elif el.get("syncing") is False:
            block = el.get("current_block", "?")
            console.print(f"  Execution: [green]synced (block {block})[/green]")

        cl = sync["consensus"]
        if cl.get("error"):
            console.print(f"  Consensus: [yellow]unavailable ({cl['error']})[/yellow]")
        elif cl.get("syncing"):
            console.print(f"  Consensus: [yellow]syncing {cl['progress_pct']:.1f}% "
                          f"(slot {cl['head_slot']}, {cl['sync_distance']} slots behind)[/yellow]")
        elif cl.get("syncing") is False:
            console.print(f"  Consensus: [green]synced (slot {cl['head_slot']})[/green]")

        console.print()

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
