"""Centralized path resolution for the staker-agent project."""
from __future__ import annotations

import os

_ENV_KEY = "STAKER_AGENT_ETH_DOCKER_PATH"
_DEFAULT = "~/eth-docker"


def get_eth_docker_path() -> str:
    """Resolve eth-docker install path from env or default.

    Priority: STAKER_AGENT_ETH_DOCKER_PATH env var > ~/eth-docker.
    Always returns an expanded absolute path.
    """
    return os.path.abspath(os.path.expanduser(os.getenv(_ENV_KEY, _DEFAULT)))
