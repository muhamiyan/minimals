"""Setup input DTOs — request-body validation for the first-run wizard."""
from __future__ import annotations

from pydantic import Field

from app.infra.validation import CredentialPolicy
from framework.base import DTOBase


class DbConfigIn(DTOBase):
    """Validate a database connection payload."""

    engine: str = Field(default="sqlite", max_length=32)  # sqlite | mariadb | postgresql
    host: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    database: str | None = Field(default=None, max_length=128)
    username: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, max_length=512)
    path: str | None = Field(default=None, max_length=4096)  # sqlite file path (optional)


class AdminCreateIn(DTOBase, CredentialPolicy):
    """Validate the initial administrator payload."""

    email: str = Field(..., max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=150)
    password: str = Field(..., min_length=8, max_length=255)
    full_name: str = Field(alias="fullName", min_length=1, max_length=255)


class SetupIn(DTOBase):
    """Validate a first-run setup payload."""

    db: DbConfigIn = Field(default_factory=DbConfigIn)
    admin: AdminCreateIn


__all__ = ["AdminCreateIn", "DbConfigIn", "SetupIn"]
