"""
keys command - Manage validator keys
"""
from rich.console import Console
from core.key_manager import KeyManager

console = Console()

def run_keys(action, count=1, network='holesky', withdrawal_address=None, keys_path=None):
    """Manage validator keys"""

    key_mgr = KeyManager()

    if action == 'generate':
        console.print("\n[bold cyan]🛰️  Staker Agent - Key Generation[/bold cyan]")
        return key_mgr.generate_keys(count=count, network=network, withdrawal_address=withdrawal_address)

    elif action == 'list':
        key_mgr.list_keys()
        return True

    elif action == 'import':
        if not keys_path:
            console.print("[red]❌ Please specify --keys-path[/red]\n")
            return False
        return key_mgr.import_keys(keys_path)

    else:
        console.print(f"[red]❌ Unknown action: {action}[/red]\n")
        return False
