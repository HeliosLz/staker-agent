"""
status command - Check validator node status
"""
from rich.console import Console
from core.status_monitor import StatusMonitor

console = Console()

def run_status(detailed=False):
    """Check node status"""
    monitor = StatusMonitor()
    return monitor.show_status(detailed=detailed)

def run_logs(service='all', follow=False):
    """View node logs"""
    monitor = StatusMonitor()
    return monitor.show_logs(service=service, follow=follow)
