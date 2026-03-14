"""Logging configuration utilities."""
from __future__ import annotations

import logging
import logging.config
import os
from typing import Dict


def configure_logging(debug: bool) -> None:
    """Configure structured logging for the backend."""
    log_level = os.getenv("STAKER_AGENT_LOG_LEVEL", "DEBUG" if debug else "INFO").upper()

    has_json = _has_python_jsonlogger()

    config: Dict[str, object] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if has_json else "default",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    if has_json:
        config["formatters"]["json"] = {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }

    logging.config.dictConfig(config)


def _has_python_jsonlogger() -> bool:
    try:
        import pythonjsonlogger  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True
