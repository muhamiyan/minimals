"""Global error handlers — JSON responses for 400-500 status codes."""
from __future__ import annotations

import logging

from flask import Flask
from flask_wtf.csrf import CSRFError

from framework.api.error_handler import register_domain_handlers
from framework.api.response import error

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    register_domain_handlers(app)

    @app.errorhandler(CSRFError)
    def handle_csrf(_e: CSRFError):
        return error("csrf_token_invalid", 400)

    @app.errorhandler(400)
    def bad_request(_e) -> tuple[dict, int]:
        return error("bad_request", 400)

    @app.errorhandler(401)
    def unauthorized(_e) -> tuple[dict, int]:
        return error("unauthorized", 401)

    @app.errorhandler(403)
    def forbidden(_e) -> tuple[dict, int]:
        return error("forbidden", 403)

    @app.errorhandler(404)
    def not_found(_e) -> tuple[dict, int]:
        return error("not_found", 404)

    @app.errorhandler(405)
    def method_not_allowed(_e) -> tuple[dict, int]:
        return error("method_not_allowed", 405)

    @app.errorhandler(422)
    def unprocessable_entity(_e) -> tuple[dict, int]:
        return error("unprocessable_entity", 422)

    @app.errorhandler(413)
    def payload_too_large(_e) -> tuple[dict, int]:
        logger.warning("payload too large: rejected request")
        return error("payload_too_large", 413)

    @app.errorhandler(429)
    def rate_limited(_e) -> tuple[dict, int]:
        return error("rate_limit_exceeded", 429)

    @app.errorhandler(500)
    def server_error(e) -> tuple[dict, int]:
        logger.error("unhandled exception: %s", e, exc_info=True)
        return error("internal_server_error", 500)


__all__ = ["register_error_handlers"]
