"""Read API — publishes user and role data over HTTP for clients outside this app.

Gated by ``INTERNAL_API_TOKEN`` or an admin session; see ``create_app.py``.
"""
from __future__ import annotations

import secrets

from flask import current_app, request
from flask_login import current_user

from app.account.presenters import RoleOut, UserAdminOut
from app.account.services import AccountService
from framework.api import BlueprintFactory, error, ok

bp = BlueprintFactory("app_api", __name__, url_prefix="/api/v1/app")


def _check_read_access():
    token = current_app.config.get("INTERNAL_API_TOKEN", "")
    header_token = request.headers.get("X-Internal-Token", "")

    if header_token:
        if token and secrets.compare_digest(header_token, token):
            return None
        return error("forbidden", 403)

    if not current_user.is_authenticated:
        return error("unauthorized", 401)

    if current_user.app_role == "admin":
        return None

    return error("forbidden", 403)


@bp.get("/ping")
def ping():
    return ok({"status": "ok", "service": "app"})


@bp.get("/users")
def list_users():
    if gate := _check_read_access():
        return gate

    users = AccountService().list_all_users()
    return ok({"items": [UserAdminOut.from_user(u).to_dict() for u in users]})


@bp.get("/roles")
def list_roles():
    if gate := _check_read_access():
        return gate

    roles = AccountService().list_roles()
    return ok({"items": [RoleOut.from_role(r).to_dict() for r in roles]})


__all__ = ["bp"]
