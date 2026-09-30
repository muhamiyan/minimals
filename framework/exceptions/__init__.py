"""Framework exceptions — domain-driven exception hierarchy.

All domain exceptions carry an HTTP status code so the API layer can
map them to responses automatically via ``register_domain_handlers()``.

Hierarchy::

    DomainException (base)
    ├── NotFound
    ├── Conflict
    ├── Unauthorized
    ├── Forbidden
    ├── ValidationFailed
    └── InvalidOperation
"""
from __future__ import annotations


class DomainException(Exception):
    """Base for all domain-level exceptions.

    Attributes:
        message: Error key (snake_case i18n key).
        status_code: HTTP status code (default 400).
        details: Optional dict with extra context.
    """

    def __init__(
        self,
        message: str = "domain_error",
        *,
        status_code: int = 400,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFound(DomainException):
    """Resource not found (404)."""

    def __init__(self, message: str = "not_found", **kwargs):
        super().__init__(message, status_code=404, **kwargs)


class Conflict(DomainException):
    """Resource conflict / duplicate (409)."""

    def __init__(self, message: str = "conflict", **kwargs):
        super().__init__(message, status_code=409, **kwargs)


class Unauthorized(DomainException):
    """Authentication required (401)."""

    def __init__(self, message: str = "unauthorized", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class Forbidden(DomainException):
    """Permission denied (403)."""

    def __init__(self, message: str = "forbidden", **kwargs):
        super().__init__(message, status_code=403, **kwargs)


class ValidationFailed(DomainException):
    """Input validation failed (400)."""

    def __init__(self, message: str = "validation_error", **kwargs):
        super().__init__(message, status_code=400, **kwargs)


class InvalidOperation(DomainException):
    """Business rule violation (422)."""

    def __init__(self, message: str = "invalid_operation", **kwargs):
        super().__init__(message, status_code=422, **kwargs)


__all__ = [
    "Conflict",
    "DomainException",
    "Forbidden",
    "InvalidOperation",
    "NotFound",
    "Unauthorized",
    "ValidationFailed",
]
