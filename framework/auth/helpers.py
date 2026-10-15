"""RBAC helpers for API endpoints.

Designed to be used inside Flask view functions (or method views) so they
can return a standard ``(json_body, status)`` tuple immediately.

Imported by any domain's ``api.py`` — it is shared so the rule is the
same across every domain.
"""
from __future__ import annotations

from flask_login import current_user

from framework.api.response import error


def _deny(status: int, message: str):
    """Return a Flask ``Response`` tuple for denial cases."""
    return error(message, status)


def require_role(*roles: str):
    """Return a 401/403 response if the current user lacks one of ``roles``.

    Returns ``None`` when the user is authenticated **and** their
    ``app_role`` is in ``roles``.  Otherwise returns a Flask response
    tuple suitable for immediate return from the calling handler.

    Example::

        @bp.post("")
        def create_todo():
            if denied := require_role("admin"):
                return denied
            ...
    """
    if not current_user.is_authenticated:
        return _deny(401, "unauthorized")

    user_role = getattr(current_user, "app_role", None) or "user"
    if user_role not in roles:
        return _deny(403, "forbidden")
    return None


def require_owner_or_role(owner_id: str | None, *roles: str):
    """Return a 401/403 response unless the user owns the resource or has a privileged role.

    Returns ``None`` when:
    - The user is authenticated, **and**
    - Either ``current_user.id == owner_id`` or ``app_role in roles``.

    A resource with no owner (``owner_id is None``) is never owned by anyone;
    only ``roles`` can admit the caller.

    Otherwise returns a Flask response tuple.
    """
    if not current_user.is_authenticated:
        return _deny(401, "unauthorized")
    if owner_id is not None and current_user.id == owner_id:
        return None

    user_role = getattr(current_user, "app_role", None) or "user"
    if user_role in roles:
        return None
    return _deny(403, "forbidden")


__all__ = ["require_owner_or_role", "require_role"]
