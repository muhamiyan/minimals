"""Rate limiting via flask-limiter."""
from __future__ import annotations

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def init_rate_limiter(app: Flask) -> None:
    app.config["RATELIMIT_DEFAULT"] = app.config["RATE_LIMIT_DEFAULT"]
    app.config.setdefault(
        "RATELIMIT_STORAGE_URI", app.config["RATE_LIMIT_STORAGE_URL"] or "memory://"
    )
    limiter.init_app(app)


__all__ = ["init_rate_limiter", "limiter"]
