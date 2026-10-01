"""Auth input DTOs — request-body validation for auth endpoints."""
from __future__ import annotations

from pydantic import field_validator

from framework.base import DTOBase


class RegisterIn(DTOBase):
    """Validate a registration payload."""

    email: str = DTOBase.field(..., max_length=255)
    username: str = DTOBase.field(..., min_length=3, max_length=150)
    password: str = DTOBase.field(..., min_length=8)
    full_name: str = DTOBase.field(..., alias="fullName", max_length=255)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("invalid_email")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not all(ch.isalnum() or ch in "_.-" for ch in v):
            raise ValueError("invalid_username")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("required")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("password_must_contain_uppercase")
        if not any(c.islower() for c in v):
            raise ValueError("password_must_contain_lowercase")
        if not any(c.isdigit() for c in v):
            raise ValueError("password_must_contain_digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("password_must_contain_special_character")
        return v


class LoginIn(DTOBase):
    """Validate a login payload — ``identifier`` is email OR username."""

    identifier: str = DTOBase.field(...)
    password: str

    @field_validator("identifier")
    @classmethod
    def clean_identifier(cls, v: str) -> str:
        return v.strip().lower()


__all__ = ["LoginIn", "RegisterIn"]
