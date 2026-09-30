"""CSRF bootstrap endpoint — hands out tokens for same-origin axios requests."""
from __future__ import annotations

from flask import session
from flask_wtf.csrf import generate_csrf

from framework.api import BlueprintFactory, ok

bp = BlueprintFactory("csrf", __name__, url_prefix="/api/v1")

CSRF_SESSION_KEY = "csrf_token"


def clear_session_keep_csrf() -> None:
    token = session.get(CSRF_SESSION_KEY)
    session.clear()
    if token is not None:
        session[CSRF_SESSION_KEY] = token


@bp.get("/csrf")
def csrf_token():
    return ok({"csrfToken": generate_csrf()})
