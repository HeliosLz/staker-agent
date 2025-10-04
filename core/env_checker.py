"""
Environment checker - Clean wrapper around SystemChecker
Display logic only, no business logic duplication.
"""
from rich.console import Console
from rich.table import Table
from core.system_checker import SystemChecker

console = Console()


class EnvChecker:
    """
    Thin wrapper for CLI display.
    All checking logic lives in SystemChecker.
    This is just presentation.
    """

    def __init__(self):
        self.checks = {}

    def check_os(self):
        """Check OS - delegates to SystemChecker"""
        result = SystemChecker.check_os()
        self.checks['os'] = result.to_dict()
        return result.passed

    def check_python(self):
        """Check Python - delegates to SystemChecker"""
        result = SystemChecker.check_python()
        self.checks['python'] = result.to_dict()
        return result.passed

    def check_docker(self):
        """Check Docker - delegates to SystemChecker"""
        result = SystemChecker.check_docker()
        self.checks['docker'] = result.to_dict()
        return result.passed

    def check_docker_running(self):
        """
        Deprecated: Now handled by check_docker()
        Kept for backward compatibility.
        """
        return self.check_docker()

    def check_docker_compose(self):
        """Check Docker Compose - delegates to SystemChecker"""
        result = SystemChecker.check_docker_compose()
        self.checks['docker_compose'] = result.to_dict()
        return result.passed

    def check_disk_space(self, required_gb=100):
        """Check disk space - delegates to SystemChecker"""
        result = SystemChecker.check_disk_space(required_gb)
        self.checks['disk_space'] = result.to_dict()
        return result.passed

    def check_network(self):
        """Check network - delegates to SystemChecker"""
        result = SystemChecker.check_network()
        self.checks['network'] = result.to_dict()
        return result.passed

    def run_all_checks(self):
        """Run all checks and display results"""
        console.print("\n[bold cyan]🔍 Running Environment Checks...[/bold cyan]\n")

        # Run all checks
        self.check_os()
        self.check_python()
        self.check_docker()
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
            # Build details string
            details = check.get('value', check['name'])

            # Add error if exists
            if check.get('error'):
                details += f" - {check['error']}"

            table.add_row(
                key.replace('_', ' ').title(),
                details,
                check['status']
            )

            # Check if critical requirement failed
            if not check['supported'] and key not in ['disk_space', 'docker_compose']:
                all_passed = False

        console.print(table)
        console.print()

        if all_passed:
            console.print("[bold green]✅ All checks passed! Ready to proceed.[/bold green]\n")
        else:
            console.print("[bold yellow]⚠️  Some checks failed. Please fix the issues above.[/bold yellow]\n")

            # Give specific guidance
            if not self.checks.get('docker', {}).get('supported'):
                console.print("[yellow]💡 To install Docker:[/yellow]")
                console.print("[yellow]   Visit: http://localhost:5001/api/fix/docker/instructions[/yellow]\n")

        return all_passed
