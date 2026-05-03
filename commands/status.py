"""
status command - Check validator node status
"""
from rich.console import Console
from core.node.status import StatusMonitor
from core.paths import get_eth_docker_path

console = Console()


def run_status(detailed=False):
    """Check node status"""
    monitor = StatusMonitor(get_eth_docker_path())
    return monitor.show_status(detailed=detailed)

def run_logs(service='all', follow=False):
    """View node logs"""
    monitor = StatusMonitor(get_eth_docker_path())
    return monitor.show_logs(service=service, follow=follow)
