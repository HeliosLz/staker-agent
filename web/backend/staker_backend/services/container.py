"""Service container for dependency injection."""
from __future__ import annotations

from dataclasses import dataclass, field
from queue import Queue
from typing import Any, Optional

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
    # Phase 2: Agent ops
    agent_state: Any = None             # core.agent.state.AgentState
    monitor_loop: Any = None            # core.agent.monitor.MonitorLoop | None
    notif_queue: Queue = field(default_factory=Queue)
