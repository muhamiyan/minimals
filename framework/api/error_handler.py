"""Domain exception handlers — auto-map DomainException to HTTP responses.

Register on any Flask app or blueprint so that ``DomainException``
subclasses are caught automatically and returned as standard JSON error
responses.

Usage::

    from framework.api import register_domain_handlers

    # On the app (after all blueprints)
    register_domain_handlers(app)

    # Or on a specific blueprint
    register_domain_handlers(bp)
"""
from __future__ import annotations

from flask import Blueprint, Flask

from framework.api.response import error
from framework.exceptions import DomainException


def register_domain_handlers(app_or_bp: Flask | Blueprint) -> None:
    """Register error handlers that convert ``DomainException`` to JSON.

    Unhandled ``ValueError`` propagates to Flask's 500 handler — it signals
    a programming error, not a client error.
    """

    @app_or_bp.errorhandler(DomainException)
    def handle_domain_exception(exc: DomainException):
        return error(exc.message, exc.status_code)


__all__ = ["register_domain_handlers"]
