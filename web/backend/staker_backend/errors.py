"""Centralised exception handling and response mapping."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Type

from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Base class for API-friendly exceptions."""

    status_code = 400
    error_code = "bad_request"

    def __init__(self, message: str, *, status_code: int | None = None, error_code: str | None = None, details: Dict[str, Any] | None = None) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.details = details or {}


class ValidationError(ApiError):
    status_code = 422
    error_code = "validation_error"


class NotFoundError(ApiError):
    status_code = 404
    error_code = "not_found"


@dataclass
class ErrorMapping:
    status_code: int
    error_code: str


def register_error_handlers(app: Flask) -> None:
    """Attach JSON error handlers for known exceptions."""

    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        logger.warning("Handled API error", extra={"error": exc.error_code, "details": exc.details})
        return _build_response(
            status=exc.status_code,
            error=exc.error_code,
            message=str(exc),
            details=exc.details,
        )

    @app.errorhandler(404)
    def handle_404(_exc):
        return _build_response(
            status=404,
            error="not_found",
            message=f"Endpoint {request.path} not found",
        )

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return _build_response(
            status=500,
            error="internal_server_error",
            message="An unexpected error occurred. Please try again later.",
        )


def _build_response(*, status: int, error: str, message: str, details: Dict[str, Any] | None = None):
    payload = {
        "success": False,
        "error": error,
        "message": message,
    }
    if details:
        payload["details"] = details
    return jsonify(payload), status
