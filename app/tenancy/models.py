"""Tenancy models — Organization, Subscription, Membership."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.plans.models import Plan
from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


SUB_STATUSES = ("trial", "active", "expired", "cancelled")
MEMBER_ROLES = ("owner", "member")


class Organization(db.Model):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    changed_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    # Creator of the record — the console actor, or the self-service user
    # (which is also what the per-user creation quota counts). Bare id, no
    # ForeignKey/relationship, same reasoning as users.default_org_id.
    # Declared last so `add_column` in 0002 (which appends) stays in parity
    # with the `create_all` column order.
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    subscription: Mapped[Subscription | None] = relationship(
        "Subscription", back_populates="organization", uselist=False,
        cascade="all, delete-orphan", lazy="selectin",
    )
    memberships: Mapped[list[Membership]] = relationship(
        "Membership", back_populates="organization", cascade="all, delete-orphan",
    )


class Subscription(db.Model):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_subscriptions_organization"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    feature_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_on: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    changed_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="subscription",
    )
    plan: Mapped[Plan] = relationship("Plan", lazy="joined")


class InviteCode(db.Model):
    """One redeemable code tying a user into an organization (owner-generated).

    Redeemed once by any authenticated user, then simply revoked — there is
    no per-assignee tracking and no expiry: the owner can rotate by revoking.
    ``created_by`` carries no FK on purpose, same as ``users.default_org_id``:
    a deleted actor must never cascade into (or block) tenancy rows.
    """

    __tablename__ = "invite_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(12), nullable=False, unique=True, index=True)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Membership(db.Model):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_memberships_org_user"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    organization: Mapped[Organization] = relationship(
        "Organization", back_populates="memberships",
    )
    user: Mapped[User] = relationship("User")  # noqa: F821


__all__ = [
    "MEMBER_ROLES",
    "SUB_STATUSES",
    "InviteCode",
    "Membership",
    "Organization",
    "Subscription",
]
