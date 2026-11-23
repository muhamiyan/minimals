"""Billing service — invoice generation and lifecycle.

Invoices are generated lazily when billing is read (no scheduler exists):
every eligible organization whose plan carries a price — including the free
tier, whose price may be zero — gets an invoice for the current subscription
period. Plans without a price are billed manually. When a subscription enters
its renewal window (``invoice_lead_days`` before ``expires_on``), the next
period is invoiced early too. Period length comes from the plan (days or
months, anchored at the subscription start); amounts are the plan price at
generation time. Paying can record the amount actually received. Generation
is idempotent via the unique ``(organization_id, period_start)`` constraint
and never backfills past periods — the first call covers only the current
one. A self-service switch (``request_plan_switch``) creates an invoice
carrying ``plan_id`` instead: the subscription keeps its plan until that
invoice is paid, and ``mark_paid`` performs the actual switch — the old
plan is never observed as changed by an unpaid request.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.billing.dto import (
    BillingSettingsIn,
    InvoiceCreateIn,
    InvoicePayIn,
    PlanSwitchIn,
)
from app.billing.models import CURRENCY, Invoice
from app.billing.repositories import InvoiceRepository
from app.infra.audit import log as audit_log
from app.infra.billing_settings import (
    BillingSettings,
    load_billing_settings,
    save_billing_settings,
)
from app.plans.duration import period_bounds, period_index
from app.plans.repositories import PlanRepository
from app.tenancy.repositories import (
    MembershipRepository,
    OrganizationRepository,
    SubscriptionRepository,
)
from framework.base import ServiceBase
from framework.exceptions import (
    Conflict,
    Forbidden,
    InvalidOperation,
    NotFound,
    ValidationFailed,
)
from framework.extensions import db

if TYPE_CHECKING:
    from app.tenancy.models import Organization, Subscription

DUE_AFTER_DAYS = 14

# Concurrent readers can race the count-based invoice numbering; losing
# that race raises Conflict, and a fresh pass then sees the winner's rows.
GENERATION_ATTEMPTS = 3

# First-write race on the settings rows (same recovery as tenancy settings).
SETTINGS_ATTEMPTS = 3


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _renewal_due(
    expires_on: datetime | None, now: datetime, lead_days: int
) -> bool:
    if expires_on is None or lead_days <= 0:
        return False
    expires = _as_utc(expires_on)
    return expires - timedelta(days=lead_days) <= now < expires


class BillingService(ServiceBase[InvoiceRepository]):
    """Business logic layer for invoices."""

    repository_class = InvoiceRepository

    def __init__(
        self,
        repo: InvoiceRepository | None = None,
        orgs: OrganizationRepository | None = None,
        subs: SubscriptionRepository | None = None,
        members: MembershipRepository | None = None,
        plans: PlanRepository | None = None,
    ):
        super().__init__(repo)
        self._organizations = orgs or OrganizationRepository()
        self._subscriptions = subs or SubscriptionRepository()
        self._memberships = members or MembershipRepository()
        self._plans = plans or PlanRepository()

    # --- generation ----------------------------------------------------
    def _next_number(self, year: int) -> str:
        prefix = f"INV-{year}-"
        return f"{prefix}{self._repo.count_by_number_prefix(prefix) + 1:04d}"

    def _starts_for(
        self,
        existing: set[datetime],
        anchor: datetime,
        now: datetime,
        *,
        duration_value: int,
        duration_unit: str,
        renew: bool = False,
    ) -> list[tuple[datetime, datetime]]:
        """Period bounds that need an invoice for one subscription."""
        current = period_index(anchor, now, duration_value, duration_unit)
        if current < 0:  # subscription not started yet
            return []
        existing_indexes = {
            period_index(anchor, _as_utc(start), duration_value, duration_unit)
            for start in existing
        }
        # A restarted term re-anchors ``started_on``; invoices from the previous
        # anchor fall before index 0 and must not make the new term look backfilled.
        existing_indexes = {index for index in existing_indexes if index >= 0}
        last_index = max(
            (index for index in existing_indexes if index <= current), default=None
        )
        if last_index is None:
            indexes = [current]  # first read: current period only, no backfill
        else:
            indexes = list(range(last_index + 1, current + 1))
        if renew and current + 1 not in existing_indexes:
            indexes.append(current + 1)
        return [
            period_bounds(anchor, index, duration_value, duration_unit)
            for index in indexes
        ]

    def _build_invoice(
        self,
        *,
        organization_id: str,
        tier: str,
        amount: int,
        start: datetime,
        end: datetime,
        now: datetime,
    ) -> Invoice:
        return Invoice(
            organization_id=organization_id,
            number=self._next_number(start.year),
            tier=tier,
            amount=amount,
            currency=CURRENCY,
            status="issued",
            period_start=start,
            period_end=end,
            issued_on=now,
            due_on=start + timedelta(days=DUE_AFTER_DAYS),
        )

    def _ensure_org(
        self,
        sub: Subscription,
        now: datetime,
        existing: list[tuple[datetime, datetime]],
        *,
        renew: bool = False,
    ) -> list[Invoice]:
        """Create missing invoices for ``sub``'s organization (no commit)."""
        plan = sub.plan
        if plan is None or plan.price is None:
            return []

        periods = [(_as_utc(start), _as_utc(end)) for start, end in existing]
        created: list[Invoice] = []
        for start, end in self._starts_for(
            {start for start, _end in periods},
            _as_utc(sub.started_on),
            now,
            duration_value=plan.duration_value,
            duration_unit=plan.duration_unit,
            renew=renew,
        ):
            # A restarted term re-anchors the subscription, so its current
            # period can overlap one already invoiced under the previous anchor.
            if any(
                start < other_end and other_start < end
                for other_start, other_end in periods
            ):
                continue
            invoice = self._build_invoice(
                organization_id=sub.organization_id,
                tier=plan.tier,
                amount=plan.price,
                start=start,
                end=end,
                now=now,
            )
            self._repo.add(invoice)
            self._flush()
            created.append(invoice)
            audit_log(
                "invoice_generated",
                resource=f"billing/invoices/{invoice.id}",
                details={
                    "number": invoice.number,
                    "amount": invoice.amount,
                    "tier": invoice.tier,
                },
            )
        return created

    def _billable(self, now: datetime) -> list[Subscription]:
        """Subscriptions to invoice: active organizations on priced plans."""
        subs = self._subscriptions.list()
        if not subs:
            return []
        orgs: dict[str, Organization] = {
            o.id: o
            for o in self._organizations.find_by_ids([s.organization_id for s in subs])
        }
        eligible: list[Subscription] = []
        for sub in subs:
            org = orgs.get(sub.organization_id)
            if org is None or not org.active:
                continue
            if sub.status not in ("trial", "active"):
                continue
            if sub.expires_on is not None and _as_utc(sub.expires_on) <= now:
                continue
            if sub.plan is None or sub.plan.price is None:
                continue
            eligible.append(sub)
        return eligible

    def ensure_generated(self, org_ids: list[str] | None) -> int:
        """Generate invoices for the given orgs (all orgs when ``None``).

        Returns the number of invoices created; commits if any were. A
        concurrent writer (same period or same invoice number) surfaces as
        ``Conflict``; the retry then re-reads the committed state and the
        duplicate insert disappears, so a plain read never fails with 409.
        """
        now = datetime.now(UTC)
        lead_days = load_billing_settings().invoice_lead_days
        for _attempt in range(GENERATION_ATTEMPTS):
            try:
                eligible = self._billable(now)
                if org_ids is not None:
                    wanted = set(org_ids)
                    eligible = [s for s in eligible if s.organization_id in wanted]
                if not eligible:
                    return 0
                periods_by_org = self._repo.periods(
                    [s.organization_id for s in eligible]
                )
                created = sum(
                    len(
                        self._ensure_org(
                            sub,
                            now,
                            periods_by_org.get(sub.organization_id, []),
                            renew=_renewal_due(sub.expires_on, now, lead_days),
                        )
                    )
                    for sub in eligible
                )
                if created:
                    self._commit()
                return created
            except Conflict:
                continue
        raise Conflict("integrity_error")

    def create_invoice(
        self, dto: InvoiceCreateIn, *, actor_id: str
    ) -> Invoice:
        """Create one invoice by hand (superadmin), ahead of the schedule.

        ``period_start`` identifies a period and snaps to the plan's billing
        cadence, so a picked date can never shadow an auto-generated start.
        ``amount`` is required for plans without a price.
        """
        org = self._organizations.get(dto.organization_id)
        if org is None:
            raise NotFound("organization_not_found")
        if not org.active:
            raise InvalidOperation("organization_inactive")

        sub = self._subscriptions.find_by_org(org.id)
        if sub is None:
            raise NotFound("subscription_not_found")
        plan = sub.plan
        if plan is None:
            raise InvalidOperation("plan_missing")

        if dto.amount is not None:
            amount = dto.amount
        elif plan.price is not None:
            amount = plan.price
        else:
            raise ValidationFailed("amount_required")

        anchor = _as_utc(sub.started_on)
        requested = _as_utc(datetime.fromisoformat(dto.period_start))
        start, end = period_bounds(
            anchor,
            period_index(
                anchor, requested, plan.duration_value, plan.duration_unit
            ),
            plan.duration_value,
            plan.duration_unit,
        )
        if start < anchor:
            raise ValidationFailed("period_before_subscription")

        now = datetime.now(UTC)
        for _attempt in range(GENERATION_ATTEMPTS):
            if self._repo.find_by_org_and_period(org.id, start) is not None:
                raise Conflict("invoice_period_exists")
            invoice = self._build_invoice(
                organization_id=org.id,
                tier=plan.tier,
                amount=amount,
                start=start,
                end=end,
                now=now,
            )
            self._repo.add(invoice)
            try:
                self._flush()
                audit_log(
                    "invoice_created",
                    user_id=actor_id,
                    resource=f"billing/invoices/{invoice.id}",
                    details={
                        "number": invoice.number,
                        "amount": invoice.amount,
                        "tier": invoice.tier,
                        "organizationId": org.id,
                    },
                )
                self._commit()
            except Conflict:
                continue
            return invoice
        if self._repo.find_by_org_and_period(org.id, start) is not None:
            raise Conflict("invoice_period_exists")
        raise Conflict("integrity_error")

    # --- self-service plan switch --------------------------------------
    def request_plan_switch(self, org_id: str, dto: PlanSwitchIn, *, actor_id: str) -> Invoice:
        """Create the invoice a self-service switch is paid with.

        The subscription keeps the old plan until this invoice is paid;
        ``mark_paid`` performs the actual switch. Only one switch can be
        pending per organization; a superadmin voiding the invoice cancels
        the request. Manual plans (no price) cannot be self-served.
        """
        org = self._organizations.get(org_id)
        if org is None:
            raise NotFound("organization_not_found")
        if not org.active:
            raise InvalidOperation("organization_inactive")

        sub = self._subscriptions.find_by_org(org_id)
        if sub is None:
            raise NotFound("subscription_not_found")

        plan = self._plans.get(dto.plan_id)
        if plan is None:
            raise NotFound("plan_not_found")
        if not plan.is_active:
            raise InvalidOperation("plan_inactive")
        if plan.price is None:
            raise InvalidOperation("plan_not_self_serviceable")
        if sub.plan_id == plan.id:
            raise InvalidOperation("plan_already_current")
        if self._repo.find_pending_switch(org_id) is not None:
            raise InvalidOperation("plan_switch_pending")

        now = datetime.now(UTC)
        start, end = period_bounds(
            now, 0, plan.duration_value, plan.duration_unit
        )
        for _attempt in range(GENERATION_ATTEMPTS):
            if self._repo.find_by_org_and_period(org_id, start) is not None:
                raise Conflict("invoice_period_exists")
            invoice = self._build_invoice(
                organization_id=org_id,
                tier=plan.tier,
                amount=plan.price,
                start=start,
                end=end,
                now=now,
            )
            invoice.plan_id = plan.id
            self._repo.add(invoice)
            try:
                self._flush()
                audit_log(
                    "plan_switch_requested",
                    user_id=actor_id,
                    resource=f"billing/invoices/{invoice.id}",
                    details={
                        "number": invoice.number,
                        "amount": invoice.amount,
                        "planId": plan.id,
                        "tier": plan.tier,
                        "organizationId": org_id,
                    },
                )
                self._commit()
            except Conflict:
                continue
            return invoice
        if self._repo.find_by_org_and_period(org_id, start) is not None:
            raise Conflict("invoice_period_exists")
        raise Conflict("integrity_error")

    # --- reads ---------------------------------------------------------
    def list_invoices(
        self,
        *,
        caller_id: str,
        is_superadmin: bool,
        search: str | None = None,
        status: str | None = None,
        org_id: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Invoice], int]:
        """List invoices visible to the caller.

        ``is_superadmin`` scopes to every organization; otherwise the
        caller must be an owner somewhere, or the list is forbidden.
        ``org_id`` is an explicit filter applied inside the scope.
        """
        if is_superadmin:
            targets = [org_id] if org_id else None
        else:
            scope = self.owner_org_ids(caller_id)
            if not scope:
                raise Forbidden("forbidden")
            if org_id and org_id not in scope:
                return [], 0
            targets = [org_id] if org_id else list(scope)

        self.ensure_generated(targets)

        search_org_ids = None
        if search:
            search_org_ids = self._organizations.search_ids(search)
            if targets is not None:
                keep = set(targets)
                search_org_ids = [i for i in search_org_ids if i in keep]

        return self._repo.list_invoices(
            search=search,
            status=status,
            org_ids=targets,
            search_org_ids=search_org_ids,
            page=page,
            per_page=per_page,
        )

    def list_org_invoices(
        self,
        org_id: str,
        *,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
    ) -> tuple[list[Invoice], int]:
        self.ensure_generated([org_id])
        return self._repo.list_invoices(
            org_ids=[org_id], status=status, page=page, per_page=per_page
        )

    def get_invoice(self, invoice_id: str) -> Invoice:
        invoice = self._repo.get(invoice_id)
        if invoice is None:
            raise NotFound("invoice_not_found")
        return invoice

    def owner_org_ids(self, user_id: str) -> list[str]:
        """Organizations where ``user_id`` holds the owner role."""
        return [
            m.organization_id
            for m in self._memberships.list_for_user(user_id)
            if m.role == "owner"
        ]

    def organization_names(self, org_ids: list[str]) -> dict[str, str]:
        return {org.id: org.name for org in self._organizations.find_by_ids(org_ids)}

    # --- settings ------------------------------------------------------
    @staticmethod
    def get_settings() -> BillingSettings:
        return load_billing_settings()

    def save_settings(
        self, dto: BillingSettingsIn, *, actor_id: str
    ) -> BillingSettings:
        changes = dto.model_dump(exclude_none=True)
        for _ in range(SETTINGS_ATTEMPTS):
            save_billing_settings(changes)
            try:
                self._flush()
                settings = load_billing_settings()
                audit_log(
                    "settings_updated",
                    user_id=actor_id,
                    resource="billing/settings",
                    details={
                        "trialDays": settings.trial_days,
                        "invoiceLeadDays": settings.invoice_lead_days,
                    },
                )
                self._commit()
            except Conflict:
                continue
            return settings
        raise Conflict("settings_update_failed")

    # --- lifecycle -----------------------------------------------------
    def mark_paid(
        self, invoice_id: str, dto: InvoicePayIn, *, actor_id: str
    ) -> Invoice:
        invoice = self.get_invoice(invoice_id)
        if invoice.status == "paid":
            raise InvalidOperation("invoice_already_paid")
        if invoice.status != "issued":
            raise InvalidOperation("invoice_not_payable")

        if dto.paid_on:
            paid_on = _as_utc(datetime.fromisoformat(dto.paid_on))
            if paid_on > datetime.now(UTC) + timedelta(days=1):
                raise ValidationFailed("paid_on_in_future")
        else:
            paid_on = datetime.now(UTC)

        period_end = _as_utc(invoice.period_end)
        transitioned = self._repo.transition_status(
            invoice_id,
            from_status="issued",
            to_status="paid",
            paid_on=paid_on,
            amount=dto.amount,
        )
        # The conditional UPDATE bypasses the identity map.
        db.session.expire(invoice)
        if not transitioned:
            current = self._repo.get(invoice_id)
            if current is not None and current.status == "paid":
                raise InvalidOperation("invoice_already_paid")
            raise InvalidOperation("invoice_not_payable")

        sub = self._subscriptions.find_by_org(invoice.organization_id)
        if sub is not None and invoice.plan_id:
            # A switch invoice: the plan changes only now, anchored to the
            # paid period — the old plan (and its expiry tail) is replaced.
            plan = self._plans.get(invoice.plan_id)
            if plan is not None and plan.is_active:
                started = _as_utc(invoice.period_start)
                sub.plan_id = plan.id
                sub.started_on = started
                sub.expires_on = period_end
                if sub.status == "expired":
                    sub.status = "active"
                audit_log(
                    "subscription_plan_switch",
                    user_id=actor_id,
                    resource=f"organizations/{sub.organization_id}/subscription",
                    details={
                        "planId": plan.id,
                        "tier": plan.tier,
                        "invoiceNumber": invoice.number,
                    },
                )
            else:
                # The target plan disappeared or was deactivated before
                # payment; the invoice is still paid, the plan stays.
                audit_log(
                    "plan_switch_skipped",
                    user_id=actor_id,
                    resource=f"billing/invoices/{invoice.id}",
                    details={"planId": invoice.plan_id, "reason": "plan_unavailable"},
                )
        elif sub is not None and sub.expires_on is not None:
            expires = max(_as_utc(sub.expires_on), period_end)
            sub.expires_on = expires
            if sub.status == "expired" and expires > datetime.now(UTC):
                sub.status = "active"

        audit_log(
            "invoice_paid",
            user_id=actor_id,
            resource=f"billing/invoices/{invoice.id}",
            details={
                "number": invoice.number,
                "amount": invoice.amount,
                "paidOn": paid_on.isoformat(),
            },
        )
        self._commit()
        return invoice

    def void_invoice(self, invoice_id: str, *, actor_id: str) -> Invoice:
        invoice = self.get_invoice(invoice_id)
        if invoice.status != "issued":
            raise InvalidOperation("invoice_not_voidable")

        transitioned = self._repo.transition_status(
            invoice_id, from_status="issued", to_status="void"
        )
        db.session.expire(invoice)
        if not transitioned:
            raise InvalidOperation("invoice_not_voidable")

        audit_log(
            "invoice_voided",
            user_id=actor_id,
            resource=f"billing/invoices/{invoice.id}",
            details={"number": invoice.number},
        )
        self._commit()
        return invoice


__all__ = ["DUE_AFTER_DAYS", "BillingService"]
