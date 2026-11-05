"""Tenancy repositories — database access for organizations, subscriptions, memberships."""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import selectinload

from app.infra.models import AppSetting
from app.tenancy.models import (
    InviteCode,
    Membership,
    Organization,
    Subscription,
)
from framework.base import RepositoryBase
from framework.extensions import db


class OrganizationRepository(RepositoryBase[Organization]):
    """Database access layer for organizations."""

    model = Organization

    def find_by_slug(self, slug: str) -> Organization | None:
        return self.find_one(slug=slug)

    def find_by_ids(self, ids: list[str]) -> list[Organization]:
        if not ids:
            return []
        return (
            db.session.query(Organization)
            .filter(Organization.id.in_(ids))
            .all()
        )

    def search_ids(self, search: str) -> list[str]:
        """Organization ids whose name or slug matches ``search``."""
        like = f"%{search}%"
        rows = (
            db.session.query(Organization.id)
            .filter(db.or_(Organization.name.ilike(like), Organization.slug.ilike(like)))
            .all()
        )
        return [org_id for (org_id,) in rows]

    def list_organizations(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Organization], int]:
        q = db.session.query(Organization)
        if search:
            like = f"%{search}%"
            q = q.filter(db.or_(Organization.name.ilike(like), Organization.slug.ilike(like)))
        total = q.count()
        items = q.order_by(Organization.name).offset((page - 1) * per_page).limit(per_page).all()
        return items, total


class SubscriptionRepository(RepositoryBase[Subscription]):
    """Database access layer for subscriptions."""

    model = Subscription

    def find_by_org(self, org_id: str) -> Subscription | None:
        return self.find_one(organization_id=org_id)

    def count_by_plan(self, plan_id: str) -> int:
        return self.count(plan_id=plan_id)


class MembershipRepository(RepositoryBase[Membership]):
    """Database access layer for memberships."""

    model = Membership

    def find_by_org_and_user(self, org_id: str, user_id: str) -> Membership | None:
        return self.find_one(organization_id=org_id, user_id=user_id)

    def list_for_org(self, org_id: str) -> list[Membership]:
        return (
            db.session.query(Membership)
            .options(selectinload(Membership.user))
            .filter(Membership.organization_id == org_id)
            .order_by(Membership.created_on)
            .all()
        )

    def list_for_user(self, user_id: str) -> list[Membership]:
        return (
            db.session.query(Membership)
            .filter(Membership.user_id == user_id)
            .order_by(Membership.created_on)
            .all()
        )

    def count_for_org(self, org_id: str) -> int:
        return self.count(organization_id=org_id)

    def count_for_orgs(self, org_ids: list[str]) -> dict[str, int]:
        if not org_ids:
            return {}
        rows = (
            db.session.query(Membership.organization_id, func.count())
            .filter(Membership.organization_id.in_(org_ids))
            .group_by(Membership.organization_id)
            .all()
        )
        return {org_id: total for org_id, total in rows}

    def count_owners_for_org(self, org_id: str) -> int:
        return (
            db.session.query(func.count(Membership.id))
            .filter(
                Membership.organization_id == org_id, Membership.role == "owner"
            )
            .scalar()
            or 0
        )

    def roles_for_user(self, user_id: str, org_ids: list[str]) -> dict[str, str]:
        """Membership role per organization for one user."""
        if not org_ids:
            return {}
        rows = (
            db.session.query(Membership.organization_id, Membership.role)
            .filter(
                Membership.user_id == user_id,
                Membership.organization_id.in_(org_ids),
            )
            .all()
        )
        return {org_id: role for org_id, role in rows}


class InviteCodeRepository(RepositoryBase[InviteCode]):
    """Database access layer for invite codes."""

    model = InviteCode

    def find_by_code(self, code: str) -> InviteCode | None:
        return self.find_one(code=code)

    def find_for_org(self, org_id: str, code_id: str) -> InviteCode | None:
        """Org-scoped lookup — a code id from another org must 404, not 403."""
        return self.find_one(id=code_id, organization_id=org_id)

    def list_for_org(self, org_id: str) -> list[InviteCode]:
        return (
            db.session.query(InviteCode)
            .filter(InviteCode.organization_id == org_id)
            .order_by(InviteCode.created_on.desc())
            .all()
        )


class SettingRepository:
    """Access layer for the shared settings store (``AppSetting``).

    Deliberately not a ``RepositoryBase``: AppSetting's primary key is a uuid
    while lookups here go through the unique ``key`` column. No commit — the
    service owns the transaction.
    """

    def get_value(self, key: str) -> str | None:
        row = (
            db.session.query(AppSetting).filter(AppSetting.key == key).one_or_none()
        )
        return row.value if row else None

    def set_value(self, key: str, value: str) -> AppSetting:
        row = (
            db.session.query(AppSetting).filter(AppSetting.key == key).one_or_none()
        )
        if row is None:
            row = AppSetting(key=key, value=value)
            db.session.add(row)
        else:
            row.value = value
        return row


__all__ = [
    "InviteCodeRepository",
    "MembershipRepository",
    "OrganizationRepository",
    "SettingRepository",
    "SubscriptionRepository",
]
