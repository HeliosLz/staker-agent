"""Configuration helpers for the backend service."""
from __future__ import annotations

import logging
import os
from typing import Dict, List

from core.paths import get_eth_docker_path

logger = logging.getLogger(__name__)

DEFAULT_CORS = ["http://localhost:5173", "http://localhost:3000"]


def load_config() -> Dict[str, object]:
    """Load configuration from environment variables."""
    origins = _parse_origins(os.getenv("STAKER_AGENT_CORS_ORIGINS"))
    secret_key = os.getenv("STAKER_AGENT_SECRET_KEY")
    if not secret_key:
        import secrets
        secret_key = secrets.token_hex(32)
        logger.warning("STAKER_AGENT_SECRET_KEY not set — using random key (sessions won't survive restarts)")
    debug = os.getenv("STAKER_AGENT_DEBUG", "false").lower() in {"1", "true", "yes"}

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    ansible_dir_default = os.path.join(project_root, "ansible")
    artifacts_default = os.path.expanduser(os.getenv("STAKER_AGENT_REMOTE_ARTIFACTS", "~/.staker-agent/artifacts"))

    return {
        "SECRET_KEY": secret_key,
        "CORS_ORIGINS": origins,
        "DEBUG": debug,
        "VERSION": os.getenv("STAKER_AGENT_VERSION", "0.1.0"),
        "ETH_DOCKER_PATH": get_eth_docker_path(),
        "ANSIBLE_DIR": os.getenv("STAKER_AGENT_ANSIBLE_DIR", ansible_dir_default),
        "REMOTE_ARTIFACTS_DIR": artifacts_default,
    }


def _parse_origins(value: str | None) -> List[str]:
    if not value:
        return DEFAULT_CORS
    return [origin.strip() for origin in value.split(",") if origin.strip()]
