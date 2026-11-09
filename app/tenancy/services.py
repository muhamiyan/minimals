"""Tenancy service — business logic for organizations, subscriptions, and memberships."""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.auth.repositories import UserRepository
from app.infra.audit import log as audit_log
from app.infra.billing_settings import get_trial_days
from app.plans.duration import add_duration
from app.plans.features import FEATURE_KEYS
from app.plans.models import DEFAULT_TIER
from app.plans.repositories import PlanRepository
from app.tenancy.dto import (
    DefaultOrgIn,
    DomainModeUpdateIn,
    InviteCodeCreateIn,
    InviteRedeemIn,
    MemberAddIn,
    OrganizationCreateIn,
    OrganizationUpdateIn,
    SettingMembersLimitIn,
    SubscriptionUpsertIn,
)
from app.tenancy.models import (
    InviteCode,
    Membership,
    Organization,
    Subscription,
)
from app.tenancy.repositories import (
    InviteCodeRepository,
    MembershipRepository,
    OrganizationRepository,
    SettingRepository,
    SubscriptionRepository,
)
from framework.base import ServiceBase
from framework.exceptions import Conflict, Forbidden, InvalidOperation, NotFound

if TYPE_CHECKING:
    from app.auth.models import User

# Ambiguous-free alphabet (no I/L/O/0/1) — codes are read aloud and retyped.
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
GENERATE_ATTEMPTS = 3

# Abuse brake on the self-service path only: a plain user must not mint an
# unlimited number of organizations. The console is exempt (superadmin
# provisions on behalf of others) and invitations do not count against it.
MAX_ORGS_PER_USER = 10

# Global quota: max members in ANY organization. One app-wide setting row
# (superadmin-editable), not per-tier — 0 (the default) means "no limit".
MEMBERS_LIMIT_KEY = "members_limit"
DEFAULT_MEMBERS_LIMIT = 0
# Retries for the first-write race on the settings row (see set_members_limit).
SETTINGS_ATTEMPTS = 3

# Domain operational mode, stored per-domain as ``domain_mode_<name>`` rows.
# Values are validated against DOMAIN_MODES in dto.py.
DOMAIN_MODE_PREFIX = "domain_mode_"
DOMAIN_MODE_KEYS = ("todo", "billing", "plans", "tenancy", "infra")
DEFAULT_DOMAIN_MODE = "enabled"


def _new_invite_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(CODE_LENGTH))


class TenancyService(ServiceBase[OrganizationRepository]):
    """Business logic layer for tenancy management."""

    repository_class = OrganizationRepository

    def __init__(
        self,
        repo: OrganizationRepository | None = None,
        subs: SubscriptionRepository | None = None,
        members: MembershipRepository | None = None,
        users: UserRepository | None = None,
        invites: InviteCodeRepository | None = None,
        settings: SettingRepository | None = None,
        plans: PlanRepository | None = None,
    ):
        super().__init__(repo)
        self._subs = subs or SubscriptionRepository()
        self._members = members or MembershipRepository()
        self._users = users or UserRepository()
        self._invites = invites or InviteCodeRepository()
        self._settings = settings or SettingRepository()
        self._plans = plans or PlanRepository()

    # --- organizations ------------------------------------------------
    def create_organization(
        self,
        dto: OrganizationCreateIn,
        *,
        actor_id: str,
        enroll_creator: bool = False,
    ) -> Organization:
        """Create an organization (and its starter subscription).

        ``enroll_creator`` is only set by the self-service path
        (``POST /my-organizations``): the superadmin console deliberately
        creates orgs *without* enrolling anyone, since the console caller
        may be provisioning on behalf of someone else.
        """
        if self._repo.find_by_slug(dto.slug):
            raise Conflict("slug_already_taken")
        if enroll_creator and self._repo.count(created_by=actor_id) >= MAX_ORGS_PER_USER:
            raise InvalidOperation("too_many_organizations")

        plan = self._plans.find_default(DEFAULT_TIER)
        if plan is None or not plan.is_active:
            raise InvalidOperation("default_plan_missing")

        now = datetime.now(UTC)
        trial_days = get_trial_days()
        org = Organization(
            name=dto.name, slug=dto.slug, active=True, created_by=actor_id
        )
        self._repo.add(org)
        self._flush()

        sub = Subscription(
            organization_id=org.id,
            plan_id=plan.id,
            status="active",
            started_on=now,
            expires_on=now + timedelta(days=trial_days) if trial_days > 0 else None,
        )
        self._subs.add(sub)
        if enroll_creator:
            self._members.add(Membership(organization_id=org.id, user_id=actor_id, role="owner"))
            self._adopt_default_org(self._users.get(actor_id), org.id)
        self._flush()

        audit_log(
            "organization_created",
            user_id=actor_id,
            resource=f"organizations/{org.id}",
            details={
                "name": org.name,
                "slug": org.slug,
                "enrollCreator": enroll_creator,
                "planId": plan.id,
            },
        )
        self._commit()
        return org

    def update_organization(
        self, org_id: str, dto: OrganizationUpdateIn, *, actor_id: str
    ) -> Organization:
        org = self._repo.get(org_id)
        if org is None:
            raise NotFound("organization_not_found")

        data = dto.model_dump(exclude_unset=True, exclude_none=True)
        if "name" in data:
            org.name = data["name"]
        if "slug" in data:
            existing = self._repo.find_by_slug(data["slug"])
            if existing is not None and existing.id != org.id:
                raise Conflict("slug_already_taken")
            org.slug = data["slug"]
        if "active" in data:
            org.active = bool(data["active"])
        self._sync_expiry([org.subscription])

        audit_log(
            "organization_updated",
            user_id=actor_id,
            resource=f"organizations/{org.id}",
            details={"changed": sorted(data.keys())},
        )
        self._commit()
        return org

    def list_organizations(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Organization], int]:
        orgs, total = self._repo.list_organizations(
            search=search, page=page, per_page=per_page
        )
        if self._sync_expiry([org.subscription for org in orgs]):
            self._commit()
        return orgs, total

    def get_organization(self, org_id: str) -> Organization:
        org = self._repo.get(org_id)
        if org is None:
            raise NotFound("organization_not_found")
        if self._sync_expiry([org.subscription]):
            self._commit()
        return org

    def member_count(self, org_id: str) -> int:
        return self._members.count_for_org(org_id)

    def member_counts(self, org_ids: list[str]) -> dict[str, int]:
        return self._members.count_for_orgs(org_ids)

    # --- subscription -------------------------------------------------
    @staticmethod
    def _is_past_due(expires: datetime | None) -> bool:
        if expires is None:
            return False
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return expires <= datetime.now(UTC)

    def _effective_status(self, sub: Subscription) -> str:
        if sub.status in ("trial", "active") and self._is_past_due(sub.expires_on):
            return "expired"
        return sub.status

    def _expire_if_due(self, sub: Subscription) -> bool:
        if sub.status != self._effective_status(sub):
            sub.status = "expired"
            return True
        return False

    def _sync_expiry(self, subs: list[Subscription | None]) -> bool:
        """Flip due subscriptions to expired; audit each. Returns True if changed."""
        changed = False
        for sub in subs:
            if sub is not None and self._expire_if_due(sub):
                audit_log(
                    "subscription_expired",
                    resource=f"organizations/{sub.organization_id}/subscription",
                    details={
                        "planId": sub.plan_id,
                        "tier": sub.plan.tier if sub.plan else None,
                    },
                )
                changed = True
        return changed

    def get_subscription(self, org_id: str) -> Subscription:
        sub = self._subs.find_by_org(org_id)
        if sub is None:
            raise NotFound("subscription_not_found")
        if self._sync_expiry([sub]):
            self._commit()
        return sub

    def upsert_subscription(
        self, org_id: str, dto: SubscriptionUpsertIn, *, actor_id: str
    ) -> Subscription:
        org = self._repo.get(org_id)
        if org is None:
            raise NotFound("organization_not_found")

        plan = self._plans.get(dto.plan_id)
        if plan is None:
            raise NotFound("plan_not_found")
        if not plan.is_active:
            raise InvalidOperation("plan_inactive")

        now = datetime.now(UTC)
        sub = self._subs.find_by_org(org_id)
        if sub is None:
            sub = Subscription(organization_id=org_id, started_on=now)
            self._subs.add(sub)

        sub.plan_id = plan.id
        sub.status = dto.status
        if dto.feature_flags is not None:
            sub.feature_flags = dto.feature_flags
        if dto.expires_on is not None:
            expires = datetime.fromisoformat(dto.expires_on)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            sub.expires_on = expires
        else:
            # A plan-driven term restarts the billing anchor; otherwise the
            # period math would follow the old started_on while the expiry
            # followed now.
            sub.started_on = now
            sub.expires_on = add_duration(
                now, plan.duration_value, plan.duration_unit
            )
        self._sync_expiry([sub])

        audit_log(
            "subscription_updated",
            user_id=actor_id,
            resource=f"organizations/{org_id}/subscription",
            details={
                "planId": plan.id,
                "tier": plan.tier,
                "status": sub.status,
            },
        )
        self._flush()
        self._commit()
        return sub

    def has_feature(self, org_id: str, flag: str) -> bool:
        return self.resolve_features(org_id).get(flag, False)

    def resolve_features(self, org_id: str) -> dict[str, bool]:
        """Effective features, strictly limited to the registry.

        Per-org overrides win over the plan's grants, and an inactive org or
        lapsed subscription grants nothing. Keys no longer in ``FEATURE_KEYS``
        never surface, even if a plan or override still stores them.
        """
        sub = self._subs.find_by_org(org_id)
        if sub is None:
            return {}
        inactive = not sub.organization.active or self._effective_status(sub) not in (
            "trial",
            "active",
        )
        if inactive:
            return {flag: False for flag in FEATURE_KEYS}
        plan_flags = (sub.plan.features or {}) if sub.plan else {}
        flags = sub.feature_flags or {}
        return {
            flag: bool(flags[flag]) if flag in flags else bool(plan_flags.get(flag))
            for flag in FEATURE_KEYS
        }

    # --- platform settings --------------------------------------------
    def get_members_limit(self) -> int:
        """The app-wide member quota; ``0`` = no limit. Corrupt rows degrade
        to the default instead of 500ing every membership write."""
        raw = self._settings.get_value(MEMBERS_LIMIT_KEY)
        if raw is None:
            return DEFAULT_MEMBERS_LIMIT
        try:
            return max(0, int(raw))
        except ValueError:
            return DEFAULT_MEMBERS_LIMIT

    def set_members_limit(
        self, dto: SettingMembersLimitIn, *, actor_id: str
    ) -> int:
        # First-write race, same recovery as generate_invite_code: two
        # superadmins saving before the key exists both take the insert path;
        # the loser's commit rolls back (audit row included) and the retry
        # finds the winner's row — a plain update. Only the shared settings
        # store's unique `key` can raise IntegrityError here: audit_log never
        # fails the business operation.
        for _ in range(SETTINGS_ATTEMPTS):
            self._settings.set_value(MEMBERS_LIMIT_KEY, str(dto.members_limit))
            audit_log(
                "settings_updated",
                user_id=actor_id,
                resource="tenancy/settings",
                details={"membersLimit": dto.members_limit},
            )
            try:
                self._commit()
            except Conflict:
                continue
            return dto.members_limit
        raise Conflict("settings_update_failed")

    def get_domain_modes(self) -> dict[str, str]:
        """Operational mode per domain; corrupt/missing rows degrade to enabled."""
        from app.tenancy.dto import DOMAIN_MODES

        result: dict[str, str] = {}
        for name in DOMAIN_MODE_KEYS:
            raw = self._settings.get_value(DOMAIN_MODE_PREFIX + name)
            if raw in DOMAIN_MODES:
                result[name] = raw
            else:
                result[name] = DEFAULT_DOMAIN_MODE
        return result

    def set_domain_mode(
        self, domain: str, dto: DomainModeUpdateIn, *, actor_id: str
    ) -> dict[str, str]:
        """Set one domain's mode (superadmin). Validation happens in DTO."""
        key = DOMAIN_MODE_PREFIX + domain
        for _ in range(SETTINGS_ATTEMPTS):
            self._settings.set_value(key, dto.mode)
            audit_log(
                "domain_mode_updated",
                user_id=actor_id,
                resource=f"tenancy/settings/domain:{domain}",
                details={"mode": dto.mode},
            )
            try:
                self._commit()
            except Conflict:
                continue
            return self.get_domain_modes()
        raise Conflict("settings_update_failed")

    # --- members ------------------------------------------------------
    def _enforce_members_limit(self, org_id: str) -> None:
        """Block the next membership once the global quota is full.

        Checked on every membership-creating path (add-member and invite
        redemption). The count and the insert share one transaction, so the
        worst concurrent case is a brief overshoot on servers with read
        committed isolation — the same accepted trade-off as the other
        count-based checks here, not a correctness invariant.
        """
        limit = self.get_members_limit()
        if limit > 0 and self._members.count_for_org(org_id) >= limit:
            raise InvalidOperation("member_limit_reached")

    def add_member(
        self, org_id: str, dto: MemberAddIn, *, actor_id: str
    ) -> Membership:
        org = self._repo.get(org_id)
        if org is None:
            raise NotFound("organization_not_found")

        user = self._users.get(dto.user_id)
        if user is None:
            raise NotFound("user_not_found")

        if self._members.find_by_org_and_user(org_id, dto.user_id):
            raise Conflict("already_a_member")

        self._enforce_members_limit(org_id)

        membership = Membership(organization_id=org_id, user_id=dto.user_id, role=dto.role)
        self._members.add(membership)
        self._adopt_default_org(user, org_id)

        audit_log(
            "member_added",
            user_id=actor_id,
            resource=f"organizations/{org_id}/members",
            details={"userId": dto.user_id, "role": dto.role},
        )
        self._commit()
        return membership

    def remove_member(self, org_id: str, user_id: str, *, actor_id: str) -> None:
        membership = self._members.find_by_org_and_user(org_id, user_id)
        if membership is None:
            raise NotFound("member_not_found")

        # An organization must keep at least one owner, otherwise nobody left
        # in it can add members or manage the subscription path again.
        if membership.role == "owner" and self._members.count_owners_for_org(org_id) <= 1:
            raise InvalidOperation("last_owner_cannot_be_removed")

        self._members.delete(membership)
        # Cleared, not re-pointed: the preference is gone and the client falls
        # back to the first organization the user still belongs to.
        user = self._users.get(user_id)
        if user is not None and user.default_org_id == org_id:
            user.default_org_id = None

        audit_log(
            "member_removed",
            user_id=actor_id,
            resource=f"organizations/{org_id}/members",
            details={"userId": user_id},
        )
        self._commit()

    def list_members(self, org_id: str) -> list[Membership]:
        self.get_organization(org_id)
        return self._members.list_for_org(org_id)

    def lookup_user_candidate(
        self, org_id: str, *, identifier: str
    ) -> tuple[str, User | None]:
        """Exact email/username check for the add-member form.

        Returns ``(status, user)`` — status is ``ok``, ``already_member``,
        or ``not_found``. Deliberately single-match: org owners verify one
        identifier at a time and can never enumerate the user directory
        (``/account/users`` stays admin-only).
        """
        self.get_organization(org_id)
        user = self._users.find_by_identifier(identifier)
        if user is None:
            return "not_found", None
        if self._members.find_by_org_and_user(org_id, user.id):
            return "already_member", user
        return "ok", user

    # --- invite codes -------------------------------------------------
    def list_invite_codes(self, org_id: str) -> list[InviteCode]:
        self.get_organization(org_id)
        return self._invites.list_for_org(org_id)

    def generate_invite_code(
        self, org_id: str, dto: InviteCodeCreateIn, *, actor_id: str
    ) -> InviteCode:
        """Mint a fresh code for ``org_id``; retried on a (vanishing) collision."""
        self.get_organization(org_id)

        for _ in range(GENERATE_ATTEMPTS):
            invite = InviteCode(
                code=_new_invite_code(),
                organization_id=org_id,
                role=dto.role,
                created_by=actor_id,
            )
            self._invites.add(invite)
            # Audit before the commit (same transaction) — a savepoint opened
            # after commit would never be committed and the row would vanish.
            audit_log(
                "invite_code_generated",
                user_id=actor_id,
                resource=f"organizations/{org_id}/invite-codes",
                details={"role": invite.role},
            )
            try:
                self._commit()
            except Conflict:
                # Unique-code race only; the session (and this audit row) is
                # already rolled back, so the next attempt logs afresh.
                continue
            return invite
        raise Conflict("invite_code_generation_failed")

    def revoke_invite_code(self, org_id: str, code_id: str, *, actor_id: str) -> None:
        invite = self._invites.find_for_org(org_id, code_id)
        if invite is None:
            raise NotFound("invite_not_found")

        code = invite.code
        self._invites.delete(invite)
        audit_log(
            "invite_code_revoked",
            user_id=actor_id,
            resource=f"organizations/{org_id}/invite-codes",
            details={"code": code},
        )
        self._commit()

    def redeem_invite(
        self, dto: InviteRedeemIn, *, actor_id: str
    ) -> tuple[Organization, Membership, bool]:
        """Join the caller into the code's organization.

        Returns ``(org, membership, already_member)`` — the third element is
        what makes the endpoint idempotent: a second redemption of a valid
        code answers 200 with ``alreadyMember: true`` instead of an error,
        and a concurrent duplicate is recovered the same way.
        """
        invite = self._invites.find_by_code(dto.code)
        org = self._repo.get(invite.organization_id) if invite else None
        # A dead or deactivated organization never leaks through a code.
        if org is None or not org.active:
            raise NotFound("invite_not_found")

        membership = self._members.find_by_org_and_user(org.id, actor_id)
        if membership is not None:
            return org, membership, True

        self._enforce_members_limit(org.id)

        membership = Membership(organization_id=org.id, user_id=actor_id, role=invite.role)
        self._members.add(membership)
        self._adopt_default_org(self._users.get(actor_id), org.id)
        audit_log(
            "invite_redeemed",
            user_id=actor_id,
            resource=f"organizations/{org.id}",
            details={"role": invite.role},
        )
        try:
            self._commit()
        except Conflict:
            # Lost a race on uq_memberships_org_user — the join still happened,
            # and the winner's request already recorded the audit entry.
            existing = self._members.find_by_org_and_user(org.id, actor_id)
            if existing is None:
                raise
            return org, existing, True

        return org, membership, False

    # --- user's organizations -----------------------------------------
    def list_user_organizations(self, user_id: str) -> list[Organization]:
        memberships = self._members.list_for_user(user_id)
        orgs = self._repo.find_by_ids([m.organization_id for m in memberships])
        if self._sync_expiry([org.subscription for org in orgs]):
            self._commit()
        active = {org.id: org for org in orgs if org.active}
        return [
            org
            for m in memberships
            if (org := active.get(m.organization_id)) is not None
        ]

    def get_membership(self, org_id: str, user_id: str) -> Membership | None:
        return self._members.find_by_org_and_user(org_id, user_id)

    def membership_roles(self, user_id: str, org_ids: list[str]) -> dict[str, str]:
        """Caller's membership role per organization, for list responses."""
        return self._members.roles_for_user(user_id, org_ids)

    # --- default organization -----------------------------------------
    @staticmethod
    def _adopt_default_org(user: User | None, org_id: str) -> None:
        """Seed ``users.default_org_id`` for someone who has no preference yet.

        Called from the three paths that hand out a membership (self-service
        creation, add-member, invite redemption). It only fills an empty
        preference — an existing default is a deliberate choice, not a mirror
        of the newest membership. The caller commits.
        """
        if user is not None and user.default_org_id is None:
            user.default_org_id = org_id

    def set_default_org(
        self, user_id: str, dto: DefaultOrgIn, *, actor_id: str
    ) -> Organization:
        """Point ``user_id`` at an organization they are an active member of.

        Superadmin gets no bypass here: this is the caller's own preference,
        not an action on the organization.
        """
        org = self._repo.get(dto.org_id)
        if org is None:
            raise NotFound("organization_not_found")
        # Membership before the active check: an outsider must not be able to
        # tell an inactive organization apart from a normal one.
        if self._members.find_by_org_and_user(dto.org_id, user_id) is None:
            raise Forbidden("not_a_member")
        if not org.active:
            raise InvalidOperation("organization_inactive")

        user = self._users.get(user_id)
        if user is None:
            raise NotFound("user_not_found")
        user.default_org_id = org.id

        audit_log(
            "default_org_set",
            user_id=actor_id,
            resource=f"users/{user_id}",
            details={"organizationId": org.id},
        )
        self._commit()
        return org


__all__ = [
    "DEFAULT_MEMBERS_LIMIT",
    "MAX_ORGS_PER_USER",
    "MEMBERS_LIMIT_KEY",
    "TenancyService",
]
