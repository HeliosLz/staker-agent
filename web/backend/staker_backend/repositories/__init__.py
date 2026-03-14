"""Repository factory and helpers."""
from __future__ import annotations

from flask import Flask, current_app

from .docker import DockerComposeRepository
from .filesystem import FileRepository


class RepositoryContainer:
    """Collection of repositories shared across services."""

    def __init__(self, docker: DockerComposeRepository, files: FileRepository) -> None:
        self.docker = docker
        self.files = files


def init_repositories(app: Flask) -> RepositoryContainer:
    """Create repositories and attach them to the Flask app."""
    eth_docker_path: str = app.config["ETH_DOCKER_PATH"]

    container = RepositoryContainer(
        docker=DockerComposeRepository(eth_docker_path),
        files=FileRepository(),
    )

    app.extensions["repositories"] = container
    return container


def get_repositories() -> RepositoryContainer:
    container = current_app.extensions.get("repositories")
    if not isinstance(container, RepositoryContainer):
        raise RuntimeError("Repository container not initialised")
    return container
