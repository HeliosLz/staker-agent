"""Service container bootstrap and helpers."""
from __future__ import annotations

import os

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
    configuration = ConfigurationService(app.config["ETH_DOCKER_PATH"], repositories.files)
    deployment = DeploymentService(app.config["ETH_DOCKER_PATH"], repositories.files)
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

    container = ServiceContainer(
        environment=environment,
        configuration=configuration,
        deployment=deployment,
        status=status,
        fixes=fixes,
        jobs=jobs,
        remote=remote,
    )

    app.extensions["services"] = container
    return container


def get_services() -> ServiceContainer:
    """Fetch the service container for the current app context."""
    container = current_app.extensions.get("services")
    if not isinstance(container, ServiceContainer):
        raise RuntimeError("Service container not initialised")
    return container
