"""
eth-docker management
"""
import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class EthDockerManager:
    def __init__(self, install_path=None):
        self.install_path = install_path or os.path.expanduser('~/eth-docker')

    def is_installed(self):
        """Check if eth-docker is already installed"""
        return os.path.exists(self.install_path) and os.path.exists(os.path.join(self.install_path, 'ethd'))

    def clone_repository(self):
        """Clone eth-docker repository"""
        console.print(f"\n[cyan]📥 Downloading eth-docker to {self.install_path}...[/cyan]\n")

        try:
            # Remove existing directory if it exists but is incomplete
            if os.path.exists(self.install_path) and not self.is_installed():
                import shutil
                shutil.rmtree(self.install_path)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Cloning eth-docker repository...", total=None)

                result = subprocess.run(
                    ['git', 'clone', 'https://github.com/eth-educators/eth-docker.git', self.install_path],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    console.print("[green]✅ eth-docker downloaded successfully![/green]\n")
                    return True
                else:
                    console.print(f"[red]❌ Clone failed: {result.stderr}[/red]\n")
                    return False

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]\n")
            return False

    def setup_permissions(self):
        """Set execute permissions for ethd script"""
        try:
            ethd_path = os.path.join(self.install_path, 'ethd')
            if os.path.exists(ethd_path):
                os.chmod(ethd_path, 0o755)
                console.print("[green]✅ Permissions set for ethd script[/green]\n")
                return True
            return False
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not set permissions: {str(e)}[/yellow]\n")
            return False

    def run_config(self, network='holesky', client='lighthouse'):
        """Run eth-docker configuration"""
        console.print(f"\n[cyan]⚙️  Configuring eth-docker for {network} with {client}...[/cyan]\n")

        try:
            ethd_path = os.path.join(self.install_path, 'ethd')

            # Run config command
            console.print("[yellow]Starting interactive configuration...[/yellow]\n")
            console.print("[yellow]Please follow the prompts:[/yellow]")
            console.print(f"  - Network: [cyan]{network}[/cyan]")
            console.print(f"  - Client: [cyan]{client}[/cyan]\n")

            result = subprocess.run(
                [ethd_path, 'config'],
                cwd=self.install_path
            )

            if result.returncode == 0:
                console.print("\n[green]✅ Configuration completed![/green]\n")
                return True
            else:
                console.print("\n[red]❌ Configuration failed[/red]\n")
                return False

        except Exception as e:
            console.print(f"\n[red]❌ Error: {str(e)}[/red]\n")
            return False

    def install(self):
        """Complete eth-docker installation"""
        if self.is_installed():
            console.print(f"[green]✅ eth-docker is already installed at {self.install_path}[/green]\n")
            return True

        # Clone repository
        if not self.clone_repository():
            return False

        # Set permissions
        self.setup_permissions()

        console.print("[green]✅ eth-docker setup complete![/green]\n")
        console.print("[cyan]Next steps:[/cyan]")
        console.print("  1. Run [yellow]python3 cli.py configure[/yellow] to configure your node")
        console.print("  2. Run [yellow]python3 cli.py keys generate[/yellow] to create validator keys\n")

        return True

    def get_status(self):
        """Get eth-docker status"""
        if not self.is_installed():
            return None

        try:
            result = subprocess.run(
                ['docker', 'compose', 'ps'],
                cwd=self.install_path,
                capture_output=True,
                text=True
            )

            return result.stdout
        except Exception:
            return None
