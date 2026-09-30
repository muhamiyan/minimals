"""Account domain — re-exports bp, AccountService, ApiKeyService, models, DTOs, and presenters."""
from __future__ import annotations

from app.account.api import bp
from app.account.dto import RoleCreateIn, RoleUpdateIn, UserUpdateIn
from app.account.models import ApiKey
from app.account.presenters import RoleOut, UserAdminOut
from app.account.services import AccountService, ApiKeyService
from app.auth.models import Role, User, user_roles

__all__ = [
    "AccountService",
    "ApiKey",
    "ApiKeyService",
    "Role",
    "RoleCreateIn",
    "RoleOut",
    "RoleUpdateIn",
    "User",
    "UserAdminOut",
    "UserUpdateIn",
    "bp",
    "user_roles",
]
