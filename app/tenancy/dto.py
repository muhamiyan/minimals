"""Tenancy input DTOs — request-body validation for tenancy endpoints."""
from __future__ import annotations

import re
from datetime import datetime

from pydantic import field_validator, model_validator

from app.plans.features import FEATURE_KEYS
from app.tenancy.models import MEMBER_ROLES, SUB_STATUSES
from framework.base import DTOBase

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OrganizationCreateIn(DTOBase):
    """Validate an organization creation payload."""

    name: str = DTOBase.field(..., min_length=1, max_length=255)
    slug: str = DTOBase.field(..., min_length=1, max_length=100)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not _SLUG.match(v):
            raise ValueError("slug_must_be_lowercase_alphanumeric_with_hyphens")
        return v


class OrganizationUpdateIn(DTOBase):
    """Validate an organization update payload."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    name: str | None = DTOBase.field(default=None, min_length=1, max_length=255)
    slug: str | None = DTOBase.field(default=None, min_length=1, max_length=100)
    active: bool | None = DTOBase.field(default=None, alias="isActive")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not _SLUG.match(v):
            raise ValueError("slug_must_be_lowercase_alphanumeric_with_hyphens")
        return v

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


class SubscriptionUpsertIn(DTOBase):
    """Validate a subscription upsert payload.

    The tier is not sent: it derives from the selected plan.
    """

    plan_id: str = DTOBase.field(..., alias="planId", max_length=36)
    status: str = DTOBase.field(default="active", max_length=20)
    feature_flags: dict[str, bool] | None = DTOBase.field(
        default=None, alias="featureFlags"
    )
    expires_on: str | None = DTOBase.field(default=None, alias="expiresOn")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in SUB_STATUSES:
            raise ValueError("invalid_status")
        return v

    @field_validator("feature_flags")
    @classmethod
    def validate_feature_flags(cls, v: dict[str, bool] | None) -> dict[str, bool] | None:
        if v is None:
            return v
        if set(v) - set(FEATURE_KEYS):
            raise ValueError("unknown_feature")
        return v

    @field_validator("expires_on")
    @classmethod
    def validate_expires_on(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("invalid_expiry_date") from None
        return v


class MemberAddIn(DTOBase):
    """Validate adding a member to an organization."""

    user_id: str = DTOBase.field(..., alias="userId", max_length=36)
    role: str = DTOBase.field(default="member", max_length=20)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in MEMBER_ROLES:
            raise ValueError("invalid_role")
        return v


class DefaultOrgIn(DTOBase):
    """Validate selecting the caller's default organization."""

    org_id: str = DTOBase.field(..., alias="orgId", max_length=36)


class UserLookupIn(DTOBase):
    """Validate an exact email/username lookup query (GET, no listing)."""

    identifier: str = DTOBase.field(..., min_length=1, max_length=255)

    @field_validator("identifier", mode="before")
    @classmethod
    def strip_identifier(cls, v):
        return v.strip() if isinstance(v, str) else v


class InviteCodeCreateIn(DTOBase):
    """Validate invite-code generation (the code itself is server-generated)."""

    role: str = DTOBase.field(default="member", max_length=20)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in MEMBER_ROLES:
            raise ValueError("invalid_role")
        return v


class InviteRedeemIn(DTOBase):
    """Validate an invite-code redemption payload."""

    code: str = DTOBase.field(..., min_length=1, max_length=12)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v):
        return v.strip().upper() if isinstance(v, str) else v


class SettingMembersLimitIn(DTOBase):
    """Validate the global member-per-organization quota update.

    ``0`` is the documented "no limit" value, hence the ``ge=0`` bound
    rather than a minimum of one.
    """

    members_limit: int = DTOBase.field(..., alias="membersLimit", ge=0, le=1_000_000)


# Domain mode: which operational stage a domain is in.
#   enabled     — fully available to its normal audience
#   maintenance — page 503-style maintenance message (tulis diblokir di backend)
#   dev         — work-in-progress badge (tulis tetap jalan; UI menandai)
DOMAIN_MODES = ("enabled", "maintenance", "dev")


class DomainModeUpdateIn(DTOBase):
    """Validate a partial domain-mode update (one domain per call)."""

    mode: str = DTOBase.field(..., max_length=20)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in DOMAIN_MODES:
            raise ValueError("invalid_mode")
        return v


__all__ = [
    "DefaultOrgIn",
    "DomainModeUpdateIn",
    "InviteCodeCreateIn",
    "InviteRedeemIn",
    "MemberAddIn",
    "OrganizationCreateIn",
    "OrganizationUpdateIn",
    "SettingMembersLimitIn",
    "SubscriptionUpsertIn",
    "UserLookupIn",
]
