"""
setup command - Install Docker and eth-docker
"""
from rich.console import Console
from core.docker.manager import DockerManager
from core.docker.eth_docker import EthDockerManager
from core.paths import get_eth_docker_path
from core.system.env_checker import EnvChecker

console = Console()

def run_setup(skip_docker=False):
    """Run complete setup: Docker + eth-docker"""
    console.print("\n[bold cyan]🛰️  Staker Agent - Setup[/bold cyan]\n")

    # Step 1: Check environment first
    console.print("[cyan]Step 1: Checking environment...[/cyan]")
    checker = EnvChecker()
    checker.check_os()
    checker.check_python()

    # Step 2: Install/check Docker
    if not skip_docker:
        console.print("\n[cyan]Step 2: Setting up Docker...[/cyan]")
        docker_mgr = DockerManager()

        if not docker_mgr.is_docker_installed():
            console.print("[yellow]Docker not found. Installing...[/yellow]\n")
            if not docker_mgr.install_docker():
                console.print("\n[red]❌ Docker installation failed. Please install manually and try again.[/red]\n")
                return False
        else:
            if docker_mgr.is_docker_running():
                console.print("[green]✅ Docker is already installed and running![/green]\n")
            else:
                console.print("[yellow]⚠️  Docker is installed but not running.[/yellow]")
                console.print("[yellow]   Please start Docker Desktop and try again.[/yellow]\n")
                return False
    else:
        console.print("\n[yellow]⏭️  Skipping Docker installation...[/yellow]\n")
        docker_mgr = DockerManager()

    # Step 3: Install eth-docker
    console.print("\n[cyan]Step 3: Setting up eth-docker...[/cyan]")
    eth_docker_mgr = EthDockerManager(install_path=get_eth_docker_path())

    if not eth_docker_mgr.install():
        console.print("\n[red]❌ eth-docker installation failed.[/red]\n")
        return False

    # Summary
    console.print("\n" + "="*60)
    console.print("[bold green]✅ Setup completed successfully![/bold green]")
    console.print("="*60 + "\n")

    console.print("[cyan]📋 What's installed:[/cyan]")
    if not skip_docker:
        docker_info = docker_mgr.get_docker_info()
        console.print(f"  • {docker_info['version']}")
    console.print(f"  • eth-docker at {eth_docker_mgr.install_path}\n")

    console.print("[cyan]🎯 Next steps:[/cyan]")
    console.print("  1. Configure your node:")
    console.print("     [yellow]python3 cli.py configure --network holesky --client lighthouse[/yellow]\n")
    console.print("  2. Generate validator keys:")
    console.print("     [yellow]python3 cli.py keys generate --count 1 --network holesky[/yellow]\n")
    console.print("  3. Deploy your node:")
    console.print("     [yellow]python3 cli.py deploy[/yellow]\n")

    return True
