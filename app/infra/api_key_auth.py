"""API key authentication middleware - validates the X-API-Key header."""
from __future__ import annotations

from flask import request
from flask_login import login_user

from app.account.services import ApiKeyService
from framework.api import error


def init_api_key_auth(app) -> None:
    @app.before_request
    def _validate_api_key():
        raw_key = request.headers.get("X-API-Key")
        if not raw_key:
            return None

        key = ApiKeyService().verify(raw_key)
        if key is None or not key.user or not key.user.active:
            return error("invalid_api_key", 401)

        login_user(key.user, force=True)
        return None


__all__ = ["init_api_key_auth"]
