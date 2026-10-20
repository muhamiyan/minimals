"""Registration gate — open/closed flag stored in the settings table."""
from __future__ import annotations

from sqlalchemy import select

from app.infra.models import AppSetting
from framework.extensions import db

SETTING_KEY = "registrationMode"
MODES = ("open", "closed")
DEFAULT_MODE = "open"


def get_registration_mode() -> str:
    """Current registration mode; never raises (defaults to ``open``)."""
    try:
        value = db.session.scalars(
            select(AppSetting.value).where(AppSetting.key == SETTING_KEY)
        ).one_or_none()
    except Exception:
        db.session.rollback()
        return DEFAULT_MODE
    return value if value in MODES else DEFAULT_MODE


def save_registration_mode(mode: str) -> str:
    """Upsert the mode into the current session; the caller commits."""
    row = db.session.execute(
        select(AppSetting).where(AppSetting.key == SETTING_KEY)
    ).scalar_one_or_none()
    if row is None:
        db.session.add(AppSetting(key=SETTING_KEY, value=mode))
    else:
        row.value = mode
    db.session.flush()
    return mode


__all__ = [
    "DEFAULT_MODE",
    "MODES",
    "SETTING_KEY",
    "get_registration_mode",
    "save_registration_mode",
]
