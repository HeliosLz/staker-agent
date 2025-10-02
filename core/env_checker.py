"""
Environment detection and validation
"""
import platform
import subprocess
import shutil
from rich.console import Console
from rich.table import Table

console = Console()

class EnvChecker:
    def __init__(self):
        self.os_type = platform.system()
        self.os_version = platform.version()
        self.architecture = platform.machine()
        self.checks = {}

    def check_os(self):
        """Check operating system compatibility"""
        supported = self.os_type in ['Darwin', 'Linux', 'Windows']
        self.checks['os'] = {
            'name': f"{self.os_type} {platform.release()}",
            'supported': supported,
            'status': '✅' if supported else '❌'
        }
        return supported

    def check_python(self):
        """Check Python version"""
        version = platform.python_version()
        major, minor = map(int, version.split('.')[:2])
        supported = major >= 3 and minor >= 10
        self.checks['python'] = {
            'name': f"Python {version}",
            'supported': supported,
            'status': '✅' if supported else '❌'
        }
        return supported

    def check_docker(self):
        """Check if Docker is installed and running"""
        docker_path = shutil.which('docker')
        if not docker_path:
            self.checks['docker'] = {
                'name': 'Docker',
                'supported': False,
                'status': '❌ Not installed'
            }
            return False

        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.checks['docker'] = {
                    'name': version,
                    'supported': True,
                    'status': '✅'
                }
                return True
        except Exception as e:
            self.checks['docker'] = {
                'name': 'Docker',
                'supported': False,
                'status': f'❌ {str(e)}'
            }
        return False

    def check_docker_running(self):
        """Check if Docker daemon is running"""
        try:
            result = subprocess.run(
                ['docker', 'ps'],
                capture_output=True,
                text=True,
                timeout=5
            )
            running = result.returncode == 0
            self.checks['docker_daemon'] = {
                'name': 'Docker Daemon',
                'supported': running,
                'status': '✅ Running' if running else '❌ Not running'
            }
            return running
        except Exception:
            self.checks['docker_daemon'] = {
                'name': 'Docker Daemon',
                'supported': False,
                'status': '❌ Not running'
            }
            return False

    def check_docker_compose(self):
        """Check if Docker Compose is available"""
        try:
            result = subprocess.run(
                ['docker', 'compose', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.checks['docker_compose'] = {
                    'name': version,
                    'supported': True,
                    'status': '✅'
                }
                return True
        except Exception:
            pass

        self.checks['docker_compose'] = {
            'name': 'Docker Compose',
            'supported': False,
            'status': '❌ Not available'
        }
        return False

    def check_disk_space(self, required_gb=100):
        """Check available disk space"""
        try:
            if self.os_type == 'Windows':
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p('/'),
                    None,
                    None,
                    ctypes.pointer(free_bytes)
                )
                free_gb = free_bytes.value / (1024**3)
            elif self.os_type == 'Darwin':  # macOS
                result = subprocess.run(
                    ['df', '-g', '.'],
                    capture_output=True,
                    text=True
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    # Available space is typically the 4th column (index 3)
                    free_gb = int(parts[3]) if len(parts) > 3 else 0
                else:
                    free_gb = 0
            else:  # Linux
                result = subprocess.run(
                    ['df', '-BG', '.'],
                    capture_output=True,
                    text=True
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    free_gb = int(parts[3].rstrip('G')) if len(parts) > 3 else 0
                else:
                    free_gb = 0

            sufficient = free_gb >= required_gb
            self.checks['disk_space'] = {
                'name': f"Disk Space ({free_gb:.0f}GB available)",
                'supported': sufficient,
                'status': '✅' if sufficient else f'⚠️  Need {required_gb}GB+'
            }
            return sufficient
        except Exception as e:
            self.checks['disk_space'] = {
                'name': 'Disk Space',
                'supported': False,
                'status': f'❌ Unable to check'
            }
            return False

    def check_network(self):
        """Check internet connectivity"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '8.8.8.8'] if self.os_type != 'Windows'
                else ['ping', '-n', '1', '8.8.8.8'],
                capture_output=True,
                timeout=5
            )
            connected = result.returncode == 0
            self.checks['network'] = {
                'name': 'Internet Connection',
                'supported': connected,
                'status': '✅' if connected else '❌'
            }
            return connected
        except Exception:
            self.checks['network'] = {
                'name': 'Internet Connection',
                'supported': False,
                'status': '❌'
            }
            return False

    def run_all_checks(self):
        """Run all environment checks"""
        console.print("\n[bold cyan]🔍 Running Environment Checks...[/bold cyan]\n")

        self.check_os()
        self.check_python()
        self.check_docker()
        self.check_docker_running()
        self.check_docker_compose()
        self.check_disk_space()
        self.check_network()

        return self.display_results()

    def display_results(self):
        """Display check results in a table"""
        table = Table(title="Environment Status")
        table.add_column("Component", style="cyan")
        table.add_column("Details", style="white")
        table.add_column("Status", style="white")

        all_passed = True
        for key, check in self.checks.items():
            table.add_row(
                key.replace('_', ' ').title(),
                check['name'],
                check['status']
            )
            if not check['supported'] and key not in ['disk_space']:
                all_passed = False

        console.print(table)
        console.print()

        if all_passed:
            console.print("[bold green]✅ All checks passed! Ready to proceed.[/bold green]\n")
        else:
            console.print("[bold yellow]⚠️  Some checks failed. Please fix the issues above.[/bold yellow]\n")
            if not self.checks.get('docker', {}).get('supported'):
                console.print("[yellow]💡 Docker is not installed. Run `staker-agent setup` to install it.[/yellow]\n")

        return all_passed
