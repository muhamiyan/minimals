"""Auth HTTP endpoints — register, login, logout, me."""
from __future__ import annotations

from flask import current_app, request
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.dto import LoginIn, RegisterIn
from app.auth.presenters import UserOut
from app.auth.services import AuthService
from app.infra.csrf import clear_session_keep_csrf
from framework.api import BlueprintFactory, created, error, ok
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("auth", __name__, url_prefix="/api/v1/auth")

_auth_rate_limit = limiter.limit(
    lambda: current_app.config.get("RATE_LIMIT_AUTH", "10/minute")
    if current_app
    else "10/minute"
)


def _serialize_user(user) -> dict:
    return UserOut.from_user(user).to_dict()


@bp.post("/register")
@_auth_rate_limit
def register():
    dto = RegisterIn.validate(request.get_json(silent=True) or {})
    user = AuthService().register(dto)

    clear_session_keep_csrf()
    login_user(user, remember=True)
    return created(_serialize_user(user))


@bp.post("/login")
@_auth_rate_limit
def login():
    dto = LoginIn.validate(request.get_json(silent=True) or {})
    user = AuthService().authenticate(dto.identifier, dto.password)
    if user is None:
        return error("invalid_credentials", 401)

    clear_session_keep_csrf()
    login_user(user, remember=True)
    return ok(_serialize_user(user))


@bp.post("/logout")
@login_required
def logout():
    user_id = current_user.id
    logout_user()
    AuthService().record_logout(user_id)
    response, status = ok({"message": "logged_out"})
    response.delete_cookie("remember_token")
    return response, status


@bp.get("/me")
@login_required
def me():
    return ok(_serialize_user(current_user))
