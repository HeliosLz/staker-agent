"""Bearer token authentication for destructive endpoints and Socket.IO."""
from __future__ import annotations

import hmac
import os
from functools import wraps

from flask import request

from .errors import ApiError

TOKEN_ENV = "STAKER_AGENT_API_TOKEN"
DEFAULT_HOST = "127.0.0.1"


class AuthenticationError(ApiError):
    status_code = 401
    error_code = "authentication_required"


class TokenNotConfiguredError(ApiError):
    status_code = 503
    error_code = "token_not_configured"

    def __init__(self):
        super().__init__(
            f"Server has no {TOKEN_ENV} configured. "
            "Set this environment variable and restart.",
            status_code=503,
            error_code="token_not_configured",
        )


def get_configured_token() -> str | None:
    return os.environ.get(TOKEN_ENV)


def _extract_bearer(header: str | None) -> str | None:
    if not header:
        return None
    parts = header.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def _token_matches(candidate: object, expected: str) -> bool:
    if not isinstance(candidate, str):
        return False
    return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))


def require_auth(f):
    """Decorator: reject requests without a valid Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_configured_token()
        if not token:
            raise TokenNotConfiguredError()

        bearer = _extract_bearer(request.headers.get("Authorization"))
        if not bearer:
            raise AuthenticationError("Missing Authorization header with Bearer token")
        if not _token_matches(bearer, token):
            raise AuthenticationError("Invalid Bearer token")

        return f(*args, **kwargs)
    return decorated


def authenticate_socketio(auth_data: dict | None) -> bool:
    """Validate Socket.IO connect auth. Returns True if allowed, False to reject.

    Accepts auth={"token": "<raw>"} or auth={"token": "Bearer <token>"}.
    """
    token = get_configured_token()
    if not token:
        return False

    if not auth_data or not isinstance(auth_data, dict):
        return False

    candidate = auth_data.get("token") or ""
    # Support "Bearer <token>" prefix in Socket.IO auth as well
    stripped = _extract_bearer(candidate)
    if stripped:
        candidate = stripped

    return _token_matches(candidate, token)
