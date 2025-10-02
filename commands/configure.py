"""
configure command - Configure eth-docker settings
"""
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from core.config_generator import ConfigGenerator
from core.env_checker import EnvChecker
import os

console = Console()

def run_configure(network, client, fee_recipient=None, withdrawal_address=None, interactive=False):
    """Configure eth-docker for a specific network and client"""

    console.print("\n[bold cyan]🛰️  Staker Agent - Configure[/bold cyan]\n")

    # Check if eth-docker is installed
    eth_docker_path = os.path.expanduser('~/eth-docker')
    if not os.path.exists(eth_docker_path):
        console.print("[red]❌ eth-docker is not installed.[/red]")
        console.print("[yellow]Run 'python3 cli.py setup' first.[/yellow]\n")
        return False

    # Interactive mode
    if interactive:
        console.print("[cyan]Let's configure your Ethereum node![/cyan]\n")

        # Select network
        networks = ['holesky', 'mainnet', 'hoodi', 'sepolia']
        console.print("[cyan]Available networks:[/cyan]")
        for i, net in enumerate(networks, 1):
            console.print(f"  {i}. {net}")

        network_choice = Prompt.ask("\nSelect network", choices=['1', '2', '3', '4'], default='1')
        network = networks[int(network_choice) - 1]

        # Select client
        clients = ['lighthouse', 'prysm', 'teku', 'nimbus']
        console.print("\n[cyan]Available consensus clients:[/cyan]")
        for i, cl in enumerate(clients, 1):
            console.print(f"  {i}. {cl}")

        client_choice = Prompt.ask("\nSelect client", choices=['1', '2', '3', '4'], default='1')
        client = clients[int(client_choice) - 1]

        # Fee recipient
        if Confirm.ask("\nDo you want to set a custom fee recipient address?", default=False):
            fee_recipient = Prompt.ask("Enter fee recipient address (0x...)")

        # Withdrawal address (for CSM)
        if network == 'hoodi':
            if Confirm.ask("\nDo you want to set a custom withdrawal address for Lido CSM?", default=False):
                withdrawal_address = Prompt.ask("Enter withdrawal address (0x...)")

    # Display configuration summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]Configuration Summary[/bold cyan]")
    console.print("="*60 + "\n")

    table = Table(show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Network", network)
    table.add_row("Consensus Client", client)
    table.add_row("Execution Client", "Geth (default)")

    if fee_recipient:
        table.add_row("Fee Recipient", fee_recipient)

    if withdrawal_address:
        table.add_row("Withdrawal Address", withdrawal_address)

    console.print(table)
    console.print()

    # Generate configuration
    console.print("[cyan]Generating configuration...[/cyan]\n")

    config_gen = ConfigGenerator(eth_docker_path)
    if not config_gen.generate_env(network, client, fee_recipient, withdrawal_address):
        console.print("[red]❌ Configuration failed[/red]\n")
        return False

    # Show next steps
    console.print("\n[green]✅ Configuration completed successfully![/green]\n")

    console.print("[cyan]📋 Configuration details:[/cyan]")
    console.print(f"  • Network: [yellow]{network}[/yellow]")
    console.print(f"  • Client: [yellow]{client} + Geth[/yellow]")
    console.print(f"  • Config file: [yellow]{eth_docker_path}/.env[/yellow]\n")

    # Show warnings for specific networks
    if network == 'mainnet':
        console.print("[bold yellow]⚠️  MAINNET WARNINGS:[/bold yellow]")
        console.print("  • Ensure you have 2TB+ of free storage")
        console.print("  • Initial sync may take several days")
        console.print("  • Test on Holesky first if you're new to staking\n")

    if network == 'hoodi':
        console.print("[bold cyan]ℹ️  Lido CSM (Hoodi Network):[/bold cyan]")
        console.print("  • This is Lido's Community Staking Module testnet")
        console.print("  • Fee recipient is set to Lido's rewards vault")
        console.print("  • You'll need to bond ETH through the CSM interface\n")

    console.print("[cyan]🎯 Next steps:[/cyan]")
    console.print("  1. Generate validator keys:")
    console.print(f"     [yellow]python3 cli.py keys generate --count 1 --network {network}[/yellow]\n")
    console.print("  2. Deploy your node:")
    console.print("     [yellow]python3 cli.py deploy[/yellow]\n")
    console.print("  3. Monitor status:")
    console.print("     [yellow]python3 cli.py status[/yellow]\n")

    return True
