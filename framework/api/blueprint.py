"""Blueprint factory — standardized Flask Blueprint creation.

Reduces boilerplate in domain ``api.py`` modules by holding one consistent
blueprint construction, and forwarding every unknown attribute to the
underlying ``flask.Blueprint``.

Example::

    from framework.api import BlueprintFactory

    bp = BlueprintFactory("auth", __name__, url_prefix="/api/v1/auth")

    @bp.post("/register")
    def register():
        ...
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flask import Blueprint


class BlueprintFactory:
    """Factory for creating Flask Blueprints with consistent defaults.

    Acts as a drop-in wrapper around ``flask.Blueprint``. Supports all
    standard decorators (``@bp.get``, ``@bp.post``, etc.) and delegates
    unknown attribute access to the underlying ``Blueprint`` so it can be
    passed directly to ``app.register_blueprint()``.

    Usage::

        bp = BlueprintFactory("auth", __name__, url_prefix="/api/v1/auth")

        @bp.post("/register")
        def register():
            ...

        # Can be registered directly — no need for bp.blueprint
        app.register_blueprint(bp)
    """

    def __init__(
        self,
        name: str,
        import_name: str,
        *,
        url_prefix: str | None = None,
        **kwargs: Any,
    ):
        self._bp = Blueprint(name, import_name, url_prefix=url_prefix, **kwargs)

    # ------------------------------------------------------------------
    # Attribute delegation — any attribute not defined here falls
    # through to the underlying Blueprint. This includes:
    #   - ``register``, ``record``, ``before_request``, etc.
    #   - Anything Flask's ``app.register_blueprint()`` checks
    # ------------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        return getattr(self._bp, name)

    # Standard HTTP method decorators

    def get(self, rule: str, **options: Any) -> Callable:
        return self._bp.get(rule, **options)

    def post(self, rule: str, **options: Any) -> Callable:
        return self._bp.post(rule, **options)

    def put(self, rule: str, **options: Any) -> Callable:
        return self._bp.put(rule, **options)

    def patch(self, rule: str, **options: Any) -> Callable:
        return self._bp.patch(rule, **options)

    def delete(self, rule: str, **options: Any) -> Callable:
        return self._bp.delete(rule, **options)

    def route(self, rule: str, **options: Any) -> Callable:
        return self._bp.route(rule, **options)

    def add_url_rule(self, rule: str, endpoint: str | None = None, view_func: Callable | None = None, **options: Any) -> None:
        self._bp.add_url_rule(rule, endpoint=endpoint, view_func=view_func, **options)
