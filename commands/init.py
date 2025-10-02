"""
init command - Environment initialization and checks
"""
from core.env_checker import EnvChecker
from rich.console import Console

console = Console()

def run_init():
    """Run environment initialization checks"""
    console.print("\n[bold cyan]🛰️  Staker Agent - Environment Check[/bold cyan]\n")

    checker = EnvChecker()
    all_passed = checker.run_all_checks()

    if all_passed:
        console.print("[bold green]Next steps:[/bold green]")
        console.print("  1. Run [cyan]python cli.py setup[/cyan] to install eth-docker")
        console.print("  2. Run [cyan]python cli.py configure[/cyan] to configure your node")
        console.print("  3. Run [cyan]python cli.py keys generate[/cyan] to create validator keys\n")
    else:
        console.print("[bold yellow]Please fix the issues above before proceeding.[/bold yellow]\n")

    return all_passed
