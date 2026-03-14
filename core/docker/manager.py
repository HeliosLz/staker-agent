"""
Docker installation and management
"""
import platform
import subprocess
import shutil
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class DockerManager:
    def __init__(self):
        self.os_type = platform.system()

    def is_docker_installed(self):
        """Check if Docker is installed"""
        return shutil.which('docker') is not None

    def is_docker_running(self):
        """Check if Docker daemon is running"""
        try:
            result = subprocess.run(
                ['docker', 'ps'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def install_docker_mac(self):
        """Install Docker on macOS"""
        console.print("\n[cyan]📦 Installing Docker on macOS...[/cyan]\n")

        # Check if Homebrew is installed
        if not shutil.which('brew'):
            console.print("[red]❌ Homebrew is not installed.[/red]")
            console.print("\nPlease install Homebrew first:")
            console.print('[yellow]/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"[/yellow]\n')
            return False

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Installing Docker Desktop...", total=None)

                # Install Docker Desktop
                result = subprocess.run(
                    ['brew', 'install', '--cask', 'docker'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    console.print("[green]✅ Docker Desktop installed successfully![/green]\n")
                    console.print("[yellow]⚠️  Please start Docker Desktop from Applications folder.[/yellow]")
                    console.print("[yellow]   Wait for Docker to start, then run this command again.[/yellow]\n")
                    return True
                else:
                    console.print(f"[red]❌ Installation failed: {result.stderr}[/red]")
                    return False

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            return False

    def install_docker_linux(self):
        """Install Docker on Linux"""
        console.print("\n[cyan]📦 Installing Docker on Linux...[/cyan]\n")

        try:
            # Detect Linux distribution
            with open('/etc/os-release', 'r') as f:
                os_info = f.read().lower()

            if 'ubuntu' in os_info or 'debian' in os_info:
                commands = [
                    'sudo apt-get update',
                    'sudo apt-get install -y ca-certificates curl gnupg',
                    'sudo install -m 0755 -d /etc/apt/keyrings',
                    'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg',
                    'sudo chmod a+r /etc/apt/keyrings/docker.gpg',
                    'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null',
                    'sudo apt-get update',
                    'sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin'
                ]
            elif 'fedora' in os_info or 'rhel' in os_info:
                commands = [
                    'sudo dnf -y install dnf-plugins-core',
                    'sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo',
                    'sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin'
                ]
            else:
                console.print("[yellow]⚠️  Unsupported Linux distribution.[/yellow]")
                console.print("\nPlease install Docker manually:")
                console.print("[cyan]https://docs.docker.com/engine/install/[/cyan]\n")
                return False

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                for cmd in commands:
                    task = progress.add_task(f"Running: {cmd[:50]}...", total=None)
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    progress.remove_task(task)

                    if result.returncode != 0:
                        console.print(f"[red]❌ Command failed: {cmd}[/red]")
                        console.print(f"[red]{result.stderr}[/red]")
                        return False

            # Start Docker service
            subprocess.run(['sudo', 'systemctl', 'start', 'docker'])
            subprocess.run(['sudo', 'systemctl', 'enable', 'docker'])

            # Add current user to docker group
            subprocess.run(['sudo', 'usermod', '-aG', 'docker', subprocess.check_output(['whoami']).decode().strip()])

            console.print("[green]✅ Docker installed successfully![/green]\n")
            console.print("[yellow]⚠️  You may need to log out and back in for group changes to take effect.[/yellow]\n")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            return False

    def install_docker_windows(self):
        """Install Docker on Windows"""
        console.print("\n[yellow]⚠️  Windows detected[/yellow]\n")
        console.print("Please install Docker Desktop manually:")
        console.print("[cyan]https://docs.docker.com/desktop/install/windows-install/[/cyan]\n")
        console.print("Steps:")
        console.print("1. Download Docker Desktop for Windows")
        console.print("2. Run the installer")
        console.print("3. Restart your computer")
        console.print("4. Start Docker Desktop\n")
        return False

    def install_docker(self):
        """Install Docker based on OS"""
        if self.is_docker_installed():
            if self.is_docker_running():
                console.print("[green]✅ Docker is already installed and running![/green]\n")
                return True
            else:
                console.print("[yellow]⚠️  Docker is installed but not running.[/yellow]")
                console.print("[yellow]   Please start Docker and try again.[/yellow]\n")
                return False

        if self.os_type == 'Darwin':
            return self.install_docker_mac()
        elif self.os_type == 'Linux':
            return self.install_docker_linux()
        elif self.os_type == 'Windows':
            return self.install_docker_windows()
        else:
            console.print(f"[red]❌ Unsupported OS: {self.os_type}[/red]\n")
            return False

    def get_docker_info(self):
        """Get Docker version and info"""
        try:
            version_result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True
            )

            info_result = subprocess.run(
                ['docker', 'info', '--format', '{{json .}}'],
                capture_output=True,
                text=True
            )

            return {
                'version': version_result.stdout.strip(),
                'running': version_result.returncode == 0
            }
        except Exception:
            return {'version': 'Unknown', 'running': False}
