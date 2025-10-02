"""
deploy command - Deploy and start validator node
"""
from rich.console import Console
from core.deploy_manager import DeployManager

console = Console()

def run_deploy(services='all'):
    """Deploy validator node"""
    deploy_mgr = DeployManager()
    return deploy_mgr.deploy(services=services)
