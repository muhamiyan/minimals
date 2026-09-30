"""Audit trail — AuditLog model and log helper."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from flask import has_request_context, request
from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


# --- model --------------------------------------------------------------
class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)


# --- helper -------------------------------------------------------------
_log = logging.getLogger(__name__)


def _client_ip() -> str | None:
    if not has_request_context():
        return None
    addr = request.remote_addr
    return addr[:45] if addr else None


def _user_agent() -> str | None:
    if not has_request_context():
        return None
    ua = request.headers.get("User-Agent")
    return ua if ua else None


def log(
    action: str,
    *,
    user_id: str | None = None,
    resource: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    try:
        with db.session.begin_nested():
            db.session.add(
                AuditLog(
                    action=action,
                    user_id=user_id,
                    resource=resource,
                    details=details,
                    ip_address=_client_ip(),
                    user_agent=_user_agent(),
                )
            )
            db.session.flush()
    except Exception as exc:  # pragma: no cover - defensive
        _log.warning("audit log failed for action=%s: %s", action, exc)


__all__ = ["AuditLog", "log"]
