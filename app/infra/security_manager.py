"""Flask-Login SecurityManager — provides ``load_user`` callback."""
from __future__ import annotations

from framework.extensions import db


def load_user(user_id: str):
    from app.auth.models import User

    return db.session.get(User, user_id)


__all__ = ["load_user"]
