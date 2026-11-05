"""Tenancy guards — membership and feature gates for API endpoints.

Pattern mirrors ``framework.auth.helpers.require_role``: return ``None``
when allowed, otherwise a response tuple to return immediately from the
view. Successful access resolution caches the org on ``g.current_org``
for the rest of the request (audit, sync, downstream services).
"""
from __future__ import annotations

from flask import g
from flask_login import current_user

from app.tenancy.models import Membership, Organization
from app.tenancy.services import TenancyService
from framework.api.response import error


def current_org() -> Organization | None:
    """Organization resolved by the last successful ``require_org_access``."""
    return getattr(g, "current_org", None)


def current_membership() -> Membership | None:
    """Membership resolved by ``require_org_access``. None for superadmins."""
    return getattr(g, "current_membership", None)


def require_org_access(org_id: str):
    """Deny unless the caller may act on ``org_id`` (superadmin or member).

    401 when unauthenticated, 404 when the org does not exist, 403 when
    the caller is neither a member nor a superadmin. On success sets
    ``g.current_org`` (and ``g.current_membership`` for non-superadmins)
    and returns ``None``.

    Note: resolving the org delegates to ``TenancyService``, which lazily
    flips a due subscription to ``expired`` (with audit) in the same call.
    That commit here is the one deliberate exception to "commit only in
    the view's service call" — without it a stale ``active`` would leak
    through feature checks on read paths.
    """
    if not current_user.is_authenticated:
        return error("unauthorized", 401)
    svc = TenancyService()
    org = svc.get_organization(org_id)
    if current_user.app_role != "superadmin":
        membership = svc.get_membership(org_id, current_user.id)
        if membership is None:
            return error("forbidden", 403)
        g.current_membership = membership
    g.current_org = org
    return None


def require_org_role(org_id: str, *roles: str):
    """Deny unless the caller is a superadmin or holds one of ``roles``.

    Builds on ``require_org_access``, so unauthenticated / missing-org /
    non-member outcomes are unchanged. Superadmin bypasses the role check —
    it is not a membership role.
    """
    if denied := require_org_access(org_id):
        return denied
    if current_user.app_role == "superadmin":
        return None
    membership = current_membership()
    if membership is None or membership.role not in roles:
        return error("forbidden", 403)
    return None


def require_feature(org_id: str, flag: str):
    """Deny unless the caller has access AND the org's subscription grants ``flag``.

    Superadmin bypasses membership, never the subscription itself — a
    disabled feature is off for everyone. Expiry/inactive evaluation
    happens inside ``TenancyService.has_feature``.
    """
    if denied := require_org_access(org_id):
        return denied
    if not TenancyService().has_feature(org_id, flag):
        return error("feature_not_enabled", 403)
    return None


__all__ = [
    "current_membership",
    "current_org",
    "require_feature",
    "require_org_access",
    "require_org_role",
]
