"""deploy command - Deploy and start validator node."""
from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from commands.remote import parse_target
from core.deploy.manager import DeployManager
from core.exceptions import PrerequisiteFailedError, DockerExecutionError
from core.remote import (
    RemoteConnectionOptions,
    RemoteDeployManager,
    RemoteDeploymentConfig,
)

console = Console()

def show_success_info(network: str):
    """Show post-deployment info"""
    console.print("=" * 60)
    console.print("[bold green]🎉 Deployment Complete![/bold green]")
    console.print("=" * 60 + "\n")

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
    from core.paths import get_eth_docker_path
    _p = get_eth_docker_path()
    console.print(f"     [yellow]cp {_p}/.eth/validator_keys/keystore-*.json {_p}/.eth/validators/[/yellow]\n")
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

def run_deploy(
    services: str = "all",
    *,
    host: Optional[str] = None,
    user: Optional[str] = None,
    port: int = 22,
    ssh_key: Optional[str] = None,
    network: Optional[str] = None,
    client: Optional[str] = None,
    fee_recipient: Optional[str] = None,
    withdrawal_address: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, object]:
    """Deploy validator node locally or to a remote host."""
    if host:
        return _run_remote_deploy(
            host=host,
            user=user,
            port=port,
            ssh_key=ssh_key,
            network=network,
            client=client,
            fee_recipient=fee_recipient,
            withdrawal_address=withdrawal_address,
        )

    console.print("\n[bold cyan]🛰️  Staker Agent - Deploy[/bold cyan]\n")
    
    from core.paths import get_eth_docker_path
    deploy_mgr = DeployManager(get_eth_docker_path())

    # Pre-deployment checks and UI
    console.print("[cyan]Checking prerequisites...[/cyan]")
    try:
        deploy_mgr.check_prerequisites()
        console.print("[green]✅ All prerequisites met[/green]\n")
    except PrerequisiteFailedError as e:
        console.print("[red]❌ Prerequisites not met:[/red]")
        for issue in e.issues:
            console.print(f"  • {issue}")
        console.print()
        return {"success": False, "mode": "local", "error": "prerequisites_failed"}

    info = deploy_mgr.get_deployment_info()
    console.print("[cyan]Deployment Configuration:[/cyan]")
    console.print(f"  • Network: [yellow]{info['network']}[/yellow]")
    console.print(f"  • Client: [yellow]{info['client']}[/yellow]")
    console.print(f"  • Location: [yellow]{info['location']}[/yellow]\n")

    console.print("[cyan]Services to deploy:[/cyan]")
    console.print("  • Execution Layer (Geth)")
    console.print("  • Consensus Layer (Beacon Node)")
    console.print("  • Validator Client")

    if info['network'] in ['mainnet', 'holesky']:
        console.print("  • Prometheus (Metrics)")
        console.print("  • Grafana (Dashboard)")

    console.print()

    if info['network'] == 'mainnet':
        console.print("[bold yellow]⚠️  MAINNET DEPLOYMENT[/bold yellow]")
        console.print("  • This will connect to Ethereum mainnet")
        console.print("  • Ensure you have deposited 32 ETH")
        console.print("  • Initial sync may take several days")
        console.print("  • Monitor your node regularly\n")

    if not Confirm.ask("\n[bold]Start deployment?[/bold]", default=True):
        console.print("[yellow]Deployment cancelled.[/yellow]\n")
        return {"success": False, "mode": "local", "error": "cancelled"}

    if dry_run:
        console.print("\n[bold yellow]🧪 DRY RUN — no Docker commands will execute[/bold yellow]")
        console.print("[cyan]Would execute the following:[/cyan]\n")
        console.print(f"  [dim]cd {info['location']}[/dim]")
        console.print("  [yellow]docker compose pull[/yellow]")
        console.print("  [yellow]docker compose up -d --remove-orphans[/yellow]\n")
        console.print("[green]✅ Dry run complete. Re-run without --dry-run to actually deploy.[/green]\n")
        return {"success": True, "mode": "local", "dry_run": True}

    def _status(event: str, payload: dict[str, object]) -> None:
        if event == "step":
            if payload.get("step") == "pulling":
                console.print("\n[cyan]📥 Pulling Docker images...[/cyan]")
                console.print("[yellow]This may take several minutes on first run...[/yellow]")
            elif payload.get("step") == "starting":
                console.print("\n[cyan]🚀 Starting services...[/cyan]")
        elif event == "success":
            pass

    try:
        success = deploy_mgr.deploy(services=services, status_callback=_status)
        if success:
            show_success_info(info['network'])
        return {"success": bool(success), "mode": "local"}
    except DockerExecutionError as e:
        console.print(f"[red]❌ Failed during deployment:[/red]\n{e}")
        return {"success": False, "mode": "local", "error": "docker_error"}
    except Exception as e:
        console.print(f"[red]❌ Unexpected error:[/red] {e}")
        return {"success": False, "mode": "local", "error": str(e)}


def _run_remote_deploy(
    *,
    host: str,
    user: Optional[str],
    port: int,
    ssh_key: Optional[str],
    network: Optional[str],
    client: Optional[str],
    fee_recipient: Optional[str],
    withdrawal_address: Optional[str],
) -> dict[str, object]:
    target = parse_target(host, user=user)

    if (network is None or client is None):
        console.print(
            Panel(
                "Remote deployment requires --network and --client options to render configuration.",
                title="Missing configuration",
                style="red",
            )
        )
        return {"success": False, "error": "missing_configuration"}

    connection = RemoteConnectionOptions(
        host=target.host,
        user=target.user,
        port=port,
        ssh_key=ssh_key,
    )
    deployment = RemoteDeploymentConfig(
        network=network,
        client=client,
        fee_recipient=fee_recipient,
        withdrawal_address=withdrawal_address,
    )

    def _status(event: str, payload: dict[str, object]) -> None:
        console.print(f"[cyan]remote[{event}][/cyan] {payload}")

    manager = RemoteDeployManager(
        connection,
        deployment,
        status_callback=_status,
    )

    result = manager.deploy()
    if result.get("success"):
        console.print(Panel("Remote deployment completed", title="Success", style="green"))
    else:
        console.print(Panel("Remote deployment failed", title="Error", style="red"))
    return result
