"""Blueprint registration."""
from __future__ import annotations

from flask import Flask

from .environment import bp as env_bp
from .configuration import bp as config_bp
from .deployment import bp as deploy_bp
from .status import bp as status_bp
from .fixes import bp as fix_bp
from .jobs import bp as jobs_bp
from .remote import bp as remote_bp
from .agent import bp as agent_bp
from .auth import bp as auth_bp
from .monitor import bp as monitor_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(env_bp, url_prefix="/api/env")
    app.register_blueprint(config_bp, url_prefix="/api/config")
    app.register_blueprint(deploy_bp, url_prefix="/api/deploy")
    app.register_blueprint(status_bp, url_prefix="/api/status")
    app.register_blueprint(fix_bp, url_prefix="/api/fix")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(remote_bp, url_prefix="/api/remote")
    app.register_blueprint(agent_bp, url_prefix="/api/agent")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(monitor_bp, url_prefix="/api/monitor")
