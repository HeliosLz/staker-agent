"""
Core domain exceptions for Staker Agent.
"""

class StakerAgentError(Exception):
    """Base exception for all Staker Agent errors."""
    pass

class PrerequisiteFailedError(StakerAgentError):
    """Raised when prerequisite checks fail before an operation."""
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("Prerequisites not met:\n" + "\n".join(f"- {i}" for i in issues))

class DockerExecutionError(StakerAgentError):
    """Raised when a docker command fails."""
    def __init__(self, command: str, stderr: str):
        self.command = command
        self.stderr = stderr
        super().__init__(f"Docker command '{command}' failed:\n{stderr}")

class ConfigurationError(StakerAgentError):
    """Raised when there is an issue with the configuration."""
    pass

class KeyGenerationError(StakerAgentError):
    """Raised when key generation fails."""
    def __init__(self, message: str, details: str = ""):
        self.details = details
        super().__init__(f"{message} {details}".strip())

class UserCancelledError(StakerAgentError):
    """Raised when the user cancels an operation."""
    pass
