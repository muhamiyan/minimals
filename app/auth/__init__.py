"""Auth domain — re-exports bp, AuthService, User, Role, and DTOs."""
from __future__ import annotations

from app.auth.api import bp
from app.auth.dto import LoginIn, RegisterIn, RegistrationModeIn
from app.auth.models import Role, User, user_roles
from app.auth.presenters import UserOut
from app.auth.services import AuthService

__all__ = [
    "AuthService",
    "LoginIn",
    "RegisterIn",
    "RegistrationModeIn",
    "Role",
    "User",
    "UserOut",
    "bp",
    "user_roles",
]
