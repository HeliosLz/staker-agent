"""
keys command - Manage validator keys
"""
from rich.console import Console
from rich.prompt import Confirm
from core.keys.manager import KeyManager
from core.exceptions import KeyGenerationError

console = Console()

def run_keys(action, count=1, network='holesky', withdrawal_address=None, keys_path=None):
    """Manage validator keys"""

    key_mgr = KeyManager()

    if action == 'generate':
        console.print("\n[bold cyan]🛰️  Staker Agent - Key Generation[/bold cyan]")
        console.print(f"\n[cyan]🔑 Generating {count} validator key(s) for {network}...[/cyan]\n")

        # Show important information
        console.print("[bold yellow]⚠️  IMPORTANT SECURITY NOTES:[/bold yellow]")
        console.print("  • You will create a mnemonic phrase (24 words)")
        console.print("  • Write it down and keep it SAFE - it's your only recovery method")
        console.print("  • Never share your mnemonic with anyone")
        console.print("  • Store it offline in a secure location\n")

        if withdrawal_address:
            console.print(f"[cyan]Withdrawal address:[/cyan] {withdrawal_address}")
            console.print("[yellow]Note: Withdrawal address cannot be changed later![/yellow]\n")

        if not Confirm.ask("Do you want to continue?", default=True):
            console.print("[yellow]Cancelled.[/yellow]")
            return False

        console.print("\n[cyan]Starting key generation...[/cyan]\n")
        console.print("[yellow]Follow the prompts to:[/yellow]")
        console.print("  1. Choose your language")
        console.print("  2. Create a mnemonic phrase (write it down!)")
        console.print("  3. Set a keystore password (remember it!)")
        console.print("  4. Confirm your mnemonic\n")

        try:
            # We don't have use_lido_csm as a CLI argument right now, but we pass withdrawal_address if provided.
            result = key_mgr.generate_keys(network=network, num_validators=count, withdrawal_address=withdrawal_address)
            
            console.print("\n[green]✅ Keys generated successfully![/green]\n")
            
            # Use get_keys_info to show details
            info = key_mgr.get_keys_info()
            if info['exists']:
                show_keys_info(info, network)
                
            return True
            
        except KeyGenerationError as e:
            console.print(f"\n[red]❌ {str(e)}[/red]\n")
            return False

    elif action == 'list':
        console.print("\n[cyan]🔑 Validator Keys[/cyan]\n")
        try:
            info = key_mgr.get_keys_info()
            if not info['exists']:
                console.print("[yellow]⚠️  No keys directory found or no keys exist.[/yellow]")
                console.print("[yellow]Generate keys first: python3 cli.py keys generate[/yellow]\n")
                return True

            console.print(f"[cyan]Location:[/cyan] {info['keys_path']}\n")

            if info['deposit_data_files']:
                console.print(f"[green]Deposit Data Files:[/green]")
                for f in info['deposit_data_files']:
                    console.print(f"  • {f}")
                console.print()

            k_files = info['keystore_files']
            if k_files:
                console.print(f"[green]Keystore Files ({len(k_files)}):[/green]")
                for f in k_files[:5]:  # Show first 5
                    console.print(f"  • {f}")
                if len(k_files) > 5:
                    console.print(f"  ... and {len(k_files) - 5} more")
                console.print()
                
            return True
        except KeyGenerationError as e:
            console.print(f"[red]Error: {str(e)}[/red]\n")
            return False

    elif action == 'import':
        if not keys_path:
            console.print("[red]❌ Please specify --keys-path[/red]\n")
            return False
            
        console.print("\n[cyan]📥 Importing validator keys...[/cyan]\n")
        try:
            result = key_mgr.import_keys(keys_path)
            for f in result['copied_files']:
                console.print(f"[green]✅ Copied: {f}[/green]")
            console.print(f"\n[green]✅ Keys imported to {result['keys_path']}[/green]\n")
            return True
        except KeyGenerationError as e:
            console.print(f"[red]❌ {str(e)}[/red]\n")
            return False

    else:
        console.print(f"[red]❌ Unknown action: {action}[/red]\n")
        return False

def show_keys_info(info: dict, network: str):
    """Display information about generated keys"""
    console.print("[cyan]📁 Generated files:[/cyan]")
    console.print(f"   Location: [yellow]{info['keys_path']}[/yellow]\n")

    deposit_data_files = info['deposit_data_files']
    keystore_files = info['keystore_files']

    if deposit_data_files:
        console.print(f"   • deposit_data.json: [green]{len(deposit_data_files)} file(s)[/green]")
        console.print("     → Upload this to the Ethereum launchpad\n")

    if keystore_files:
        console.print(f"   • keystore files: [green]{len(keystore_files)} file(s)[/green]")
        console.print("     → These contain your validator keys (encrypted)\n")

    console.print("[bold cyan]📋 Next steps:[/bold cyan]")
    console.print("  1. Backup your mnemonic phrase securely")
    console.print("  2. Copy keystore files to your validator:")
    console.print(f"     [yellow]cp {info['keys_path']}/keystore-*.json ~/eth-docker/.eth/validators/[/yellow]\n")
    console.print("  3. Upload deposit_data.json:\n")

    if network == 'holesky':
        console.print("     [cyan]Holesky Launchpad: https://holesky.launchpad.ethereum.org[/cyan]")
    elif network == 'mainnet':
        console.print("     [cyan]Ethereum Launchpad: https://launchpad.ethereum.org[/cyan]")
        console.print("     [bold yellow]⚠️  Requires 32 ETH deposit per validator[/bold yellow]\n")
    elif network == 'sepolia':
        console.print("     [cyan]Sepolia Launchpad: https://sepolia.launchpad.ethereum.org[/cyan]")
    else:
        console.print(f"     [cyan]Check launchpad for {network}[/cyan]")
    console.print()

    console.print("  4. Wait for your node to sync:")
    console.print("     [yellow]python3 cli.py status[/yellow]\n")
    console.print("  5. Once synced, deploy your node:")
    console.print("     [yellow]python3 cli.py deploy[/yellow]\n")
