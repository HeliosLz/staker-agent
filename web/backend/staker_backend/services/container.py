"""Service container for dependency injection."""
from __future__ import annotations

from dataclasses import dataclass

from .environment import EnvironmentService
from .configuration import ConfigurationService
from .deployment import DeploymentService
from .status import StatusService
from .fixes import FixService
from .jobs import JobService
from .remote import RemoteService


@dataclass
class ServiceContainer:
    """Collection of domain services used by the API layer."""

    environment: EnvironmentService
    configuration: ConfigurationService
    deployment: DeploymentService
    status: StatusService
    fixes: FixService
    jobs: JobService
    remote: RemoteService
