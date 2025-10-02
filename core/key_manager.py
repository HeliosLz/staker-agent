"""
Validator key generation and management
"""
import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class KeyManager:
    def __init__(self, eth_docker_path=None):
        self.eth_docker_path = eth_docker_path or os.path.expanduser('~/eth-docker')
        self.keys_path = os.path.join(self.eth_docker_path, '.eth', 'validator_keys')

    def check_eth_docker(self):
        """Check if eth-docker is installed"""
        if not os.path.exists(self.eth_docker_path):
            console.print("[red]❌ eth-docker not found.[/red]")
            console.print("[yellow]Run 'python3 cli.py setup' first.[/yellow]\n")
            return False
        return True

    def generate_keys(self, count=1, network='holesky', withdrawal_address=None):
        """Generate validator keys using deposit-cli"""

        if not self.check_eth_docker():
            return False

        console.print(f"\n[cyan]🔑 Generating {count} validator key(s) for {network}...[/cyan]\n")

        # Check if Docker is available
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                console.print("[red]❌ Docker is not installed or not running.[/red]")
                console.print("[yellow]Please install Docker and try again.[/yellow]")
                console.print("[yellow]Or run: python3 cli.py setup[/yellow]\n")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            console.print("[red]❌ Docker is not installed or not running.[/red]")
            console.print("[yellow]Please install Docker and try again.[/yellow]")
            console.print("[yellow]Or run: python3 cli.py setup[/yellow]\n")
            return False

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

        # Prepare docker compose command
        try:
            # Create .eth directory if it doesn't exist
            eth_dir = os.path.join(self.eth_docker_path, '.eth')
            os.makedirs(eth_dir, exist_ok=True)

            console.print("\n[cyan]Starting key generation...[/cyan]\n")
            console.print("[yellow]Follow the prompts to:[/yellow]")
            console.print("  1. Choose your language")
            console.print("  2. Create a mnemonic phrase (write it down!)")
            console.print("  3. Set a keystore password (remember it!)")
            console.print("  4. Confirm your mnemonic\n")

            # Build the command
            cmd = [
                'docker', 'compose',
                'run', '--rm',
                'deposit-cli-new',
                '--num_validators', str(count),
                '--chain', network
            ]

            if withdrawal_address:
                cmd.extend(['--eth1_withdrawal_address', withdrawal_address])

            # Run the command interactively
            result = subprocess.run(
                cmd,
                cwd=self.eth_docker_path,
                env={**os.environ, 'NETWORK': network}
            )

            if result.returncode == 0:
                console.print("\n[green]✅ Keys generated successfully![/green]\n")
                self.show_generated_keys()
                return True
            else:
                console.print("\n[red]❌ Key generation failed.[/red]\n")
                return False

        except Exception as e:
            console.print(f"\n[red]❌ Error: {str(e)}[/red]\n")
            return False

    def show_generated_keys(self):
        """Display information about generated keys"""

        if not os.path.exists(self.keys_path):
            console.print("[yellow]⚠️  No keys found yet.[/yellow]")
            return

        # List generated files
        try:
            files = os.listdir(self.keys_path)

            if not files:
                console.print("[yellow]⚠️  No keys found.[/yellow]")
                return

            console.print("[cyan]📁 Generated files:[/cyan]")
            console.print(f"   Location: [yellow]{self.keys_path}[/yellow]\n")

            deposit_data_files = [f for f in files if 'deposit_data' in f]
            keystore_files = [f for f in files if 'keystore' in f]

            if deposit_data_files:
                console.print(f"   • deposit_data.json: [green]{len(deposit_data_files)} file(s)[/green]")
                console.print("     → Upload this to the Ethereum launchpad or Lido CSM\n")

            if keystore_files:
                console.print(f"   • keystore files: [green]{len(keystore_files)} file(s)[/green]")
                console.print("     → These contain your validator keys (encrypted)\n")

            console.print("[bold cyan]📋 Next steps:[/bold cyan]")
            console.print("  1. Backup your mnemonic phrase securely")
            console.print("  2. Copy keystore files to your validator:")
            console.print(f"     [yellow]cp {self.keys_path}/keystore-*.json ~/eth-docker/.eth/validators/[/yellow]\n")
            console.print("  3. Upload deposit_data.json:")

            # Check network and provide specific instructions
            env_file = os.path.join(self.eth_docker_path, '.env')
            network = 'unknown'
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('NETWORK='):
                            network = line.split('=')[1].strip()
                            break

            if network == 'hoodi':
                console.print("     [cyan]Lido CSM: https://csm.testnet.fi[/cyan]")
            elif network == 'holesky':
                console.print("     [cyan]Holesky Launchpad: https://holesky.launchpad.ethereum.org[/cyan]")
            elif network == 'mainnet':
                console.print("     [cyan]Ethereum Launchpad: https://launchpad.ethereum.org[/cyan]")
            else:
                console.print(f"     [cyan]Check launchpad for {network}[/cyan]")

            console.print("\n  4. Deploy your node:")
            console.print("     [yellow]python3 cli.py deploy[/yellow]\n")

        except Exception as e:
            console.print(f"[red]Error listing keys: {str(e)}[/red]")

    def list_keys(self):
        """List existing keys"""
        console.print("\n[cyan]🔑 Validator Keys[/cyan]\n")

        if not os.path.exists(self.keys_path):
            console.print("[yellow]⚠️  No keys directory found.[/yellow]")
            console.print("[yellow]Generate keys first: python3 cli.py keys generate[/yellow]\n")
            return

        try:
            files = os.listdir(self.keys_path)

            if not files:
                console.print("[yellow]⚠️  No keys found.[/yellow]")
                console.print("[yellow]Generate keys first: python3 cli.py keys generate[/yellow]\n")
                return

            console.print(f"[cyan]Location:[/cyan] {self.keys_path}\n")

            deposit_data_files = [f for f in files if 'deposit_data' in f]
            keystore_files = [f for f in files if 'keystore' in f]

            if deposit_data_files:
                console.print(f"[green]Deposit Data Files:[/green]")
                for f in deposit_data_files:
                    console.print(f"  • {f}")
                console.print()

            if keystore_files:
                console.print(f"[green]Keystore Files ({len(keystore_files)}):[/green]")
                for f in keystore_files[:5]:  # Show first 5
                    console.print(f"  • {f}")
                if len(keystore_files) > 5:
                    console.print(f"  ... and {len(keystore_files) - 5} more")
                console.print()

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]\n")

    def import_keys(self, keys_path):
        """Import existing keys"""
        console.print("\n[cyan]📥 Importing validator keys...[/cyan]\n")

        if not os.path.exists(keys_path):
            console.print(f"[red]❌ Path not found: {keys_path}[/red]\n")
            return False

        try:
            import shutil

            # Ensure destination directory exists
            os.makedirs(self.keys_path, exist_ok=True)

            # Copy files
            if os.path.isdir(keys_path):
                files = os.listdir(keys_path)
                for file in files:
                    src = os.path.join(keys_path, file)
                    dst = os.path.join(self.keys_path, file)
                    shutil.copy2(src, dst)
                    console.print(f"[green]✅ Copied: {file}[/green]")
            else:
                # Single file
                filename = os.path.basename(keys_path)
                dst = os.path.join(self.keys_path, filename)
                shutil.copy2(keys_path, dst)
                console.print(f"[green]✅ Copied: {filename}[/green]")

            console.print(f"\n[green]✅ Keys imported to {self.keys_path}[/green]\n")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False
