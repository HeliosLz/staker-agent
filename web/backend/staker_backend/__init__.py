"""
Staker Agent backend application factory.
Provides Flask app setup, extensions, and dependency wiring.
"""
from __future__ import annotations

from typing import Dict, List

from flask import Flask, jsonify

from .config import load_config
from .extensions import cors, socketio
from .repositories import init_repositories
from .services import init_services
from .routes import register_blueprints
from .jobs import init_jobs
from .logging import configure_logging
from .errors import register_error_handlers


def create_app(overrides: Dict[str, object] | None = None) -> Flask:
    """Application factory used by CLI and tests."""
    app = Flask(__name__)

    settings = load_config()
    if overrides:
        settings.update(overrides)
    app.config.update(settings)

    configure_logging(debug=bool(app.config.get("DEBUG", False)))
    _init_extensions(app)
    repositories = init_repositories(app)
    init_jobs(app)
    init_services(app, repositories)
    register_error_handlers(app)
    register_blueprints(app)
    _register_health_routes(app)

    return app


def _init_extensions(app: Flask) -> None:
    """Configure Flask extensions."""
    origins: List[str] = app.config["CORS_ORIGINS"]
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Socket-ID"],
            }
        },
    )
    socketio.init_app(app, cors_allowed_origins=origins)


def _register_health_routes(app: Flask) -> None:
    """Expose health and metadata endpoints."""

    @app.route("/api/health", methods=["GET"])
    def health() -> object:
        return jsonify(
            {
                "status": "healthy",
                "message": "Staker Agent API is running",
            }
        )

    @app.route("/", methods=["GET"])
    def index() -> object:
        return jsonify(
            {
                "name": "Staker Agent API",
                "version": app.config.get("VERSION", "0.1.0"),
                "endpoints": {
                    "health": "/api/health",
                    "env_check": "/api/env/check",
                    "config_generate": "/api/config/generate",
                    "deploy_start": "/api/deploy/start",
                    "status": "/api/status",
                    "jobs": "/api/jobs",
                },
            }
        )
