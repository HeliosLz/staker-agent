#!/usr/bin/env python3
"""
Staker Agent - Ethereum Validator Deployment Tool
"""
import click
from rich.console import Console

console = Console()

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """🛰️ Staker Agent - Deploy and manage Ethereum validators with ease."""
    pass

@cli.command()
def init():
    """Initialize and check environment"""
    from commands.init import run_init
    run_init()

@cli.command()
def validate():
    """Validate configuration and setup"""
    from core.validator import ConfigValidator
    validator = ConfigValidator()
    validator.validate_all()

@cli.command()
@click.option('--skip-docker', is_flag=True, help='Skip Docker installation')
def setup(skip_docker):
    """Install Docker and eth-docker"""
    from commands.setup import run_setup
    run_setup(skip_docker=skip_docker)

@cli.command()
@click.option('--network', type=click.Choice(['mainnet', 'holesky', 'hoodi', 'sepolia']),
              default='holesky', help='Ethereum network')
@click.option('--client', type=click.Choice(['lighthouse', 'prysm', 'teku', 'nimbus']),
              default='lighthouse', help='Consensus client')
@click.option('--fee-recipient', help='Fee recipient address (0x...)')
@click.option('--withdrawal-address', help='Withdrawal address for Lido CSM (0x...)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive configuration mode')
def configure(network, client, fee_recipient, withdrawal_address, interactive):
    """Configure network and client settings"""
    from commands.configure import run_configure
    run_configure(network, client, fee_recipient, withdrawal_address, interactive)

@cli.command()
@click.argument('action', type=click.Choice(['generate', 'import', 'list']))
@click.option('--count', default=1, help='Number of validators to generate')
@click.option('--network', default='holesky', help='Network name')
@click.option('--withdrawal-address', help='Withdrawal address (0x...)')
@click.option('--keys-path', help='Path to existing keys (for import)')
def keys(action, count, network, withdrawal_address, keys_path):
    """Manage validator keys"""
    from commands.keys import run_keys
    run_keys(action, count, network, withdrawal_address, keys_path)

@cli.command()
def deploy():
    """Deploy and start validator node"""
    from commands.deploy import run_deploy
    run_deploy()

@cli.command()
@click.option('--detailed', is_flag=True, help='Show detailed status')
def status(detailed):
    """Check validator node status"""
    from commands.status import run_status
    run_status(detailed)

@cli.command()
@click.option('--service', type=click.Choice(['all', 'execution', 'consensus', 'validator']),
              default='all', help='Which service logs to show')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
def logs(service, follow):
    """View node logs"""
    from commands.status import run_logs
    run_logs(service, follow)

@cli.command()
def stop():
    """Stop validator node"""
    from core.deploy_manager import DeployManager
    deploy_mgr = DeployManager()
    deploy_mgr.stop()

@cli.command()
def start():
    """Start validator node"""
    from core.deploy_manager import DeployManager
    deploy_mgr = DeployManager()
    deploy_mgr.start()

if __name__ == '__main__':
    cli()
