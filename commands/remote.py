"""
Remote-specific CLI helpers.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

from rich.console import Console
from rich.table import Table

from core.remote import RemoteConnectionOptions, RemotePreflightChecker, SSHClient


console = Console()


@dataclass
class RemoteTarget:
    host: str
    user: Optional[str]


def parse_target(target: str, *, user: Optional[str]) -> RemoteTarget:
    if "@" in target:
        resolved_user, resolved_host = target.split("@", 1)
        return RemoteTarget(host=resolved_host, user=resolved_user or user)
    return RemoteTarget(host=target, user=user)


def run_remote_preflight(
    target: str,
    *,
    user: Optional[str] = None,
    port: int = 22,
    ssh_key: Optional[str] = None,
) -> dict[str, object]:
    resolved = parse_target(target, user=user)

    connection = RemoteConnectionOptions(
        host=resolved.host,
        user=resolved.user,
        port=port,
        ssh_key=ssh_key,
    )

    ssh = SSHClient(
        connection.host,
        user=connection.user,
        port=connection.port,
        key_path=connection.ssh_key,
    )

    checker = RemotePreflightChecker(ssh)
    result = checker.run()

    _render_preflight(result)
    return {
        "success": result.ok,
        "data": asdict(result),
    }


def _render_preflight(result) -> None:
    console.print(f"\n[bold cyan]Remote host:[/bold cyan] {result.host}")

    table = Table(title="System Overview", show_header=False)
    table.add_row("OS", result.os_info.get("kernel", ""))
    table.add_row("Kernel Release", result.os_info.get("kernel_release", ""))
    table.add_row("Architecture", result.os_info.get("architecture", ""))
    console.print(table)

    resources = Table(title="Resources", show_header=False)
    resources.add_row("CPU cores", str(result.resources.get("cpu_cores", "?")))
    resources.add_row("Memory (MB)", str(result.resources.get("memory_mb", "?")))
    console.print(resources)

    docker = result.docker
    if docker.get("installed"):
        console.print(f"[green]Docker installed[/green]: {docker.get('version', '').strip()}")
    else:
        console.print(f"[yellow]Docker missing[/yellow]: {docker.get('error', '').strip()}")

    disk = result.disk
    if disk:
        console.print(f"[cyan]Disk[/cyan]: total {disk.get('total')} / free {disk.get('free')}")

    if result.issues:
        console.print("\n[bold red]Issues detected:[/bold red]")
        for issue in result.issues:
            console.print(f"  • {issue}")
    else:
        console.print("\n[bold green]Preflight passed. Host meets baseline requirements.[/bold green]")
