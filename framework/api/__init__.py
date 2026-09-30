"""API-layer utilities — response helpers, blueprint factory, error handlers, pagination."""
from __future__ import annotations

from framework.api.blueprint import BlueprintFactory
from framework.api.error_handler import register_domain_handlers
from framework.api.pagination import PageIn, PageOut, paginate
from framework.api.response import created, error, no_content, ok, paginated_response

__all__ = [
    "BlueprintFactory",
    "PageIn",
    "PageOut",
    "created",
    "error",
    "no_content",
    "ok",
    "paginate",
    "paginated_response",
    "register_domain_handlers",
]
