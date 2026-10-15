"""Auth input DTOs — request-body validation for auth endpoints."""
from __future__ import annotations

from pydantic import field_validator

from app.infra.validation import CredentialPolicy
from framework.base import DTOBase


class RegisterIn(DTOBase, CredentialPolicy):
    """Validate a registration payload."""

    email: str = DTOBase.field(..., max_length=255)
    username: str = DTOBase.field(..., min_length=3, max_length=150)
    password: str = DTOBase.field(..., min_length=8, max_length=255)
    full_name: str = DTOBase.field(..., alias="fullName", max_length=255)


class LoginIn(DTOBase):
    """Validate a login payload — ``identifier`` is email OR username.

    ``password`` is intentionally unbounded: the hash cost is independent of
    input length, and a bound here would lock out accounts that registered
    before the limit existed. Request size is capped at the transport layer.
    """

    identifier: str = DTOBase.field(..., min_length=1, max_length=255)
    password: str

    @field_validator("identifier", mode="before")
    @classmethod
    def clean_identifier(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else v


__all__ = ["LoginIn", "RegisterIn"]
