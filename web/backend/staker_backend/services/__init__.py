"""Service container bootstrap and helpers."""
from __future__ import annotations

import os
from queue import Queue

from flask import Flask, current_app

from .container import ServiceContainer
from .environment import EnvironmentService
from .configuration import ConfigurationService
from .deployment import DeploymentService
from .status import StatusService
from .fixes import FixService
from .jobs import JobService
from .remote import RemoteService
from ..repositories import RepositoryContainer
from ..jobs import JobManager


def init_services(app: Flask, repositories: RepositoryContainer) -> ServiceContainer:
    """Instantiate and attach services to the Flask app."""
    environment = EnvironmentService()
    eth_docker_path = app.config["ETH_DOCKER_PATH"]
    configuration = ConfigurationService(eth_docker_path, repositories.files)
    deployment = DeploymentService(eth_docker_path, repositories.files)
    status = StatusService(repositories.docker)
    fixes = FixService(environment)
    job_manager = app.extensions.get("jobs")
    if not isinstance(job_manager, JobManager):
        raise RuntimeError("Job manager not initialised")
    jobs = JobService(job_manager)

    ansible_dir = app.config.get(
        "ANSIBLE_DIR",
        os.path.abspath(os.path.join(app.root_path, "..", "ansible")),
    )
    artifacts_dir = app.config.get("REMOTE_ARTIFACTS_DIR")
    remote = RemoteService(ansible_dir, artifacts_dir)

    # Phase 2: Agent state + Monitor Loop
    from core.agent.state import AgentState
    from core.agent.tools import ToolContext
    from core.agent.monitor import MonitorLoop, MonitorConfig
    from core.node.status import StatusMonitor

    agent_state = AgentState()
    notif_queue: Queue = Queue()

    monitor_enabled = os.getenv("MONITOR_ENABLED", "true").lower() in ("1", "true", "yes")
    monitor_loop = None
    if monitor_enabled:
        status_monitor = StatusMonitor(eth_docker_path)
        ctx = ToolContext(
            eth_docker_path=eth_docker_path,
            state=agent_state,
            status_monitor=status_monitor,
        )
        config = MonitorConfig(
            check_interval=int(os.getenv("MONITOR_CHECK_INTERVAL", "60")),
            alert_cooldown=int(os.getenv("MONITOR_ALERT_COOLDOWN", "300")),
            max_auto_actions=int(os.getenv("MONITOR_MAX_AUTO_ACTIONS", "3")),
            thresholds={
                "el_max_sync_distance": int(os.getenv("MONITOR_EL_MAX_SYNC_DISTANCE", "50")),
                "cl_max_sync_distance": int(os.getenv("MONITOR_CL_MAX_SYNC_DISTANCE", "10")),
                "min_el_peers": int(os.getenv("MONITOR_MIN_EL_PEERS", "3")),
                "min_cl_peers": int(os.getenv("MONITOR_MIN_CL_PEERS", "3")),
            },
        )
        monitor_loop = MonitorLoop(ctx, notif_queue, config)

    container = ServiceContainer(
        environment=environment,
        configuration=configuration,
        deployment=deployment,
        status=status,
        fixes=fixes,
        jobs=jobs,
        remote=remote,
        agent_state=agent_state,
        monitor_loop=monitor_loop,
        notif_queue=notif_queue,
    )

    app.extensions["services"] = container
    return container


def get_services() -> ServiceContainer:
    """Fetch the service container for the current app context."""
    container = current_app.extensions.get("services")
    if not isinstance(container, ServiceContainer):
        raise RuntimeError("Service container not initialised")
    return container
