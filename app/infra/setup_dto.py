"""Setup input DTOs — request-body validation for the first-run wizard."""
from __future__ import annotations

from pydantic import Field, field_validator

from framework.base import DTOBase


class DbConfigIn(DTOBase):
    """Validate a database connection payload."""

    engine: str = Field(default="sqlite")  # sqlite | mariadb | postgresql
    host: str | None = Field(default=None)
    port: int | None = Field(default=None)
    database: str | None = Field(default=None)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)
    path: str | None = Field(default=None)  # sqlite file path (optional)


class AdminCreateIn(DTOBase):
    """Validate the initial administrator payload."""

    email: str = Field(..., max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=150)
    password: str = Field(..., min_length=8, max_length=255)
    full_name: str = Field(alias="fullName", min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid_email")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not all(ch.isalnum() or ch in "_.-" for ch in v):
            raise ValueError("invalid_username")
        return v


class SetupIn(DTOBase):
    """Validate a first-run setup payload."""

    db: DbConfigIn = Field(default_factory=DbConfigIn)
    admin: AdminCreateIn


__all__ = ["AdminCreateIn", "DbConfigIn", "SetupIn"]
