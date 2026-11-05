"""Tenancy presenters — serialization for tenancy responses."""
from __future__ import annotations

from datetime import UTC, datetime

from app.tenancy.models import InviteCode, Membership, Organization, Subscription
from framework.base import PresenterBase


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


class SubscriptionOut(PresenterBase):
    """Subscription response. ``tier`` derives from the assigned plan."""

    id: str
    plan_id: str = PresenterBase.field(alias="planId")
    plan_name: str = PresenterBase.field("", alias="planName")
    plan_duration_value: int = PresenterBase.field(0, alias="planDurationValue")
    plan_duration_unit: str = PresenterBase.field("", alias="planDurationUnit")
    plan_price: int | None = PresenterBase.field(None, alias="planPrice")
    tier: str = ""
    status: str
    feature_flags: dict = PresenterBase.field(default_factory=dict, alias="featureFlags")
    started_on: str | None = PresenterBase.field(None, alias="startedOn")
    expires_on: str | None = PresenterBase.field(None, alias="expiresOn")

    @classmethod
    def from_subscription(cls, sub: Subscription) -> SubscriptionOut:
        plan = sub.plan
        return cls.from_model(
            sub,
            plan_id=sub.plan_id,
            plan_name=plan.name if plan else "",
            plan_duration_value=plan.duration_value if plan else 0,
            plan_duration_unit=plan.duration_unit if plan else "",
            plan_price=plan.price if plan else None,
            tier=plan.tier if plan else "",
            feature_flags=sub.feature_flags or {},
            started_on=_iso_utc(sub.started_on),
            expires_on=_iso_utc(sub.expires_on),
        )


class MemberOut(PresenterBase):
    """Membership response."""

    id: str
    user_id: str = PresenterBase.field(alias="userId")
    username: str = ""
    full_name: str = PresenterBase.field("", alias="fullName")
    role: str
    created_on: str | None = PresenterBase.field(None, alias="createdOn")

    @classmethod
    def from_membership(cls, m: Membership) -> MemberOut:
        return cls.from_model(
            m,
            username=m.user.username if m.user else "",
            full_name=m.user.full_name if m.user else "",
            created_on=_iso_utc(m.created_on),
        )


class OrganizationOut(PresenterBase):
    """Organization response."""

    id: str
    name: str
    slug: str
    is_active: bool = PresenterBase.field(True, alias="isActive")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")
    subscription: SubscriptionOut | None = None
    member_count: int = PresenterBase.field(0, alias="memberCount")

    @classmethod
    def from_organization(
        cls,
        org: Organization,
        *,
        subscription: Subscription | None = None,
        member_count: int = 0,
    ) -> OrganizationOut:
        sub = subscription if subscription is not None else org.subscription
        return cls.from_model(
            org,
            is_active=bool(org.active),
            created_on=_iso_utc(org.created_on),
            subscription=SubscriptionOut.from_subscription(sub) if sub else None,
            member_count=member_count,
        )


class MyOrganizationOut(OrganizationOut):
    """Organization response for one of its members — adds the caller's role.

    A separate presenter rather than a field on ``OrganizationOut``: that one
    also serves the superadmin list, where the caller has no membership role.
    """

    my_role: str | None = PresenterBase.field(None, alias="myRole")

    @classmethod
    def from_organization(
        cls,
        org: Organization,
        *,
        subscription: Subscription | None = None,
        member_count: int = 0,
        my_role: str | None = None,
    ) -> MyOrganizationOut:
        sub = subscription if subscription is not None else org.subscription
        return cls.from_model(
            org,
            is_active=bool(org.active),
            created_on=_iso_utc(org.created_on),
            subscription=SubscriptionOut.from_subscription(sub) if sub else None,
            member_count=member_count,
            my_role=my_role,
        )


class UserLookupOut(PresenterBase):
    """Result of an exact email/username check for the add-member form.

    One answer per call — never a directory listing. ``userId``/``username``
    are absent on ``not_found`` (presenters exclude None); no email echoed.
    """

    status: str
    user_id: str | None = PresenterBase.field(None, alias="userId")
    username: str | None = None
    full_name: str | None = PresenterBase.field(None, alias="fullName")

    @classmethod
    def build(cls, status: str, user=None) -> UserLookupOut:
        if user is None:
            return cls(status=status)
        return cls(
            status=status,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name or None,
        )


class InviteCodeOut(PresenterBase):
    """Invite code response — the raw code is shown once and revocable."""

    id: str
    code: str
    role: str
    created_on: str | None = PresenterBase.field(None, alias="createdOn")

    @classmethod
    def from_invite(cls, invite: InviteCode) -> InviteCodeOut:
        return cls.from_model(invite, created_on=_iso_utc(invite.created_on))


class InviteRedeemOut(PresenterBase):
    """Result of redeeming an invite code — which org the caller just joined."""

    organization_id: str = PresenterBase.field(alias="organizationId")
    name: str
    slug: str
    role: str
    already_member: bool = PresenterBase.field(False, alias="alreadyMember")

    @classmethod
    def build(
        cls, org: Organization, *, role: str, already_member: bool = False
    ) -> InviteRedeemOut:
        return cls(
            organization_id=org.id,
            name=org.name,
            slug=org.slug,
            role=role,
            already_member=already_member,
        )


class SettingsOut(PresenterBase):
    """Platform settings response — the superadmin console's quota form."""

    members_limit: int = PresenterBase.field(0, alias="membersLimit")

    @classmethod
    def build(cls, members_limit: int) -> SettingsOut:
        return cls(members_limit=members_limit)


__all__ = [
    "InviteCodeOut",
    "InviteRedeemOut",
    "MemberOut",
    "MyOrganizationOut",
    "OrganizationOut",
    "SettingsOut",
    "SubscriptionOut",
    "UserLookupOut",
]
