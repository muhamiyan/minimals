"""Role seeding — ensures the Member role exists."""
from __future__ import annotations

from app.auth.models import MEMBER_ROLE, Role
from framework.extensions import db


def _roles_table_exists() -> bool:
    from sqlalchemy import inspect

    try:
        return "roles" in inspect(db.engine).get_table_names()
    except Exception:
        return False


def ensure_member_role() -> None:
    """Seed the Member role. Idempotent; runs after migrations on boot."""
    if not _roles_table_exists():
        return

    existing = {r.name for r in db.session.query(Role).all()}
    if MEMBER_ROLE not in existing:
        db.session.add(Role(name=MEMBER_ROLE))
        db.session.commit()


__all__ = [
    "MEMBER_ROLE",
    "Role",
    "ensure_member_role",
]
