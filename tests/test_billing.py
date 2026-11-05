from __future__ import annotations

from datetime import UTC, datetime, timedelta

from conftest import csrf_client, default_plan_id


def _create_org(client, name="Acme", slug="acme"):
    return client.post(
        "/api/v1/tenancy/organizations", json={"name": name, "slug": slug}
    )


def _assign_plan(client, org_id, plan_id, **overrides):
    payload = {"planId": plan_id, "status": "active", **overrides}
    return client.put(
        f"/api/v1/tenancy/organizations/{org_id}/subscription", json=payload
    )


def _set_tier(client, org_id, tier="professional", **overrides):
    response = _assign_plan(
        client, org_id, default_plan_id(client, tier), **overrides
    )
    assert response.status_code == 200, response.get_json()
    return response


def _set_plan_price(client, tier, price):
    response = client.put(
        f"/api/v1/plans/{default_plan_id(client, tier)}", json={"price": price}
    )
    assert response.status_code == 200, response.get_json()
    return response


def _create_plan(
    client,
    name="Custom",
    *,
    tier="professional",
    price=None,
    duration_value=1,
    duration_unit="months",
    is_default=False,
    is_active=True,
):
    payload = {
        "name": name,
        "tier": tier,
        "durationValue": duration_value,
        "durationUnit": duration_unit,
        "isDefault": is_default,
        "isActive": is_active,
    }
    if price is not None:
        payload["price"] = price
    response = client.post("/api/v1/plans", json=payload)
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def _org_with_invoice(client, name="Acme", slug="acme"):
    org_id = _create_org(client, name=name, slug=slug).get_json()["id"]
    _set_tier(client, org_id)
    return org_id


def _new_user(app, username):
    client = csrf_client(app)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{username}@example.com",
            "username": username,
            "password": "Str0ng!Pass",
            "fullName": username.title(),
        },
    )
    assert response.status_code == 201, response.get_json()
    return client, response.get_json()["id"]


def _add_member(superadmin, org_id, user_id, role=None):
    payload = {"userId": user_id}
    if role:
        payload["role"] = role
    response = superadmin.post(
        f"/api/v1/tenancy/organizations/{org_id}/members", json=payload
    )
    assert response.status_code == 201, response.get_json()


def _first_invoice(client):
    body = client.get("/api/v1/billing/invoices").get_json()
    assert body["items"], "expected at least one invoice"
    return body["items"][0]


def _subscription(client, org_id):
    body = client.get(f"/api/v1/tenancy/organizations/{org_id}").get_json()
    return body["subscription"]


def _set_subscription(app, org_id, *, expires_on=None, status="active"):
    from app.tenancy.models import Subscription
    from framework.extensions import db

    with app.app_context():
        sub = db.session.scalar(
            db.select(Subscription).where(Subscription.organization_id == org_id)
        )
        assert sub is not None
        sub.expires_on = expires_on
        sub.status = status
        db.session.commit()


def _next_period_start(invoice):
    from app.plans.duration import add_months

    return add_months(datetime.fromisoformat(invoice["periodStart"]), 1)


class TestGeneration:
    """Invoices are auto-generated from active subscriptions, free tier included."""

    def test_community_org_invoiced_at_zero(self, superadmin):
        _create_org(superadmin)
        body = superadmin.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 1
        item = body["items"][0]
        assert item["tier"] == "community"
        assert item["amount"] == 0

    def test_professional_generates_current_period(self, superadmin):
        org_id = _org_with_invoice(superadmin)

        body = superadmin.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 1
        item = body["items"][0]
        year = datetime.now(UTC).year
        assert item["number"] == f"INV-{year}-0001"
        assert item["status"] == "issued"
        assert item["amount"] == 500_000
        assert item["currency"] == "IDR"
        assert item["tier"] == "professional"
        assert item["organizationId"] == org_id
        assert item["organizationName"] == "Acme"
        # Wire format omits None (PresenterBase.to_dict(exclude_none=True)).
        assert item.get("paidOn") is None

        start = datetime.fromisoformat(item["periodStart"])
        end = datetime.fromisoformat(item["periodEnd"])
        due = datetime.fromisoformat(item["dueOn"])
        assert end > start
        assert end.year * 12 + end.month == start.year * 12 + start.month + 1
        assert start < due <= start + timedelta(days=15)

    def test_configured_prices_drive_amounts(self, superadmin):
        _set_plan_price(superadmin, "community", 25_000)
        _set_plan_price(superadmin, "professional", 750_000)
        _create_org(superadmin, name="Free", slug="free")
        _org_with_invoice(superadmin)

        items = superadmin.get("/api/v1/billing/invoices").get_json()["items"]
        assert {item["tier"]: item["amount"] for item in items} == {
            "community": 25_000,
            "professional": 750_000,
        }

    def test_price_change_does_not_rewrite_existing_invoice(self, superadmin):
        _org_with_invoice(superadmin)
        assert _first_invoice(superadmin)["amount"] == 500_000

        _set_plan_price(superadmin, "professional", 900_000)
        assert _first_invoice(superadmin)["amount"] == 500_000

    def test_number_sequences_across_orgs(self, superadmin):
        _org_with_invoice(superadmin, name="Alpha", slug="alpha")
        _org_with_invoice(superadmin, name="Beta", slug="beta")
        items = superadmin.get("/api/v1/billing/invoices").get_json()["items"]
        assert sorted(i["number"].rsplit("-", 1)[1] for i in items) == ["0001", "0002"]

    def test_second_read_is_idempotent(self, superadmin):
        _org_with_invoice(superadmin)
        first = superadmin.get("/api/v1/billing/invoices").get_json()["total"]
        second = superadmin.get("/api/v1/billing/invoices").get_json()["total"]
        assert first == second == 1

    def test_restarted_term_skips_period_already_invoiced(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        assert _first_invoice(superadmin)["amount"] == 500_000

        # No expiresOn starts a fresh term from now, but the previous term's
        # invoice still covers the current period.
        _set_tier(superadmin, org_id)

        body = superadmin.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 1

    def test_no_backfill_on_first_read(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        with app.app_context():
            from app.tenancy.models import Subscription
            from framework.extensions import db

            sub = db.session.scalar(
                db.select(Subscription).where(Subscription.organization_id == org_id)
            )
            sub.started_on = datetime.now(UTC) - timedelta(days=183)
            db.session.commit()

        body = superadmin.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 1  # current period only, no six backfilled periods
        start = datetime.fromisoformat(body["items"][0]["periodStart"])
        assert datetime.now(UTC) - start <= timedelta(days=32)

    def test_expired_subscription_not_invoiced(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        _set_tier(
            superadmin, org_id, expiresOn="2020-01-01T00:00:00+00:00"
        )
        body = superadmin.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 0

    def test_trial_status_is_invoiced(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        _set_tier(superadmin, org_id, status="trial")

        body = superadmin.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 1
        assert body["items"][0]["status"] == "issued"

    def test_inactive_org_not_invoiced(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={"isActive": False}
        )
        body = superadmin.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 0

    def test_month_end_anchor_keeps_billing_day(self):
        from app.billing.services import BillingService

        svc = BillingService()
        anchor = datetime(2026, 1, 31, tzinfo=UTC)

        starts = svc._starts_for(
            set(),
            anchor,
            datetime(2026, 2, 28, tzinfo=UTC),
            duration_value=1,
            duration_unit="months",
        )
        assert starts == [
            (datetime(2026, 2, 28, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC))
        ]

        starts = svc._starts_for(
            {datetime(2026, 2, 28, tzinfo=UTC)},
            anchor,
            datetime(2026, 3, 31, tzinfo=UTC),
            duration_value=1,
            duration_unit="months",
        )
        assert starts == [
            (datetime(2026, 3, 31, tzinfo=UTC), datetime(2026, 4, 30, tzinfo=UTC))
        ]

    def test_day_duration_periods(self):
        from app.billing.services import BillingService

        svc = BillingService()
        anchor = datetime(2026, 1, 15, tzinfo=UTC)

        starts = svc._starts_for(
            set(),
            anchor,
            datetime(2026, 1, 24, tzinfo=UTC),
            duration_value=10,
            duration_unit="days",
        )
        assert starts == [
            (datetime(2026, 1, 15, tzinfo=UTC), datetime(2026, 1, 25, tzinfo=UTC))
        ]

        starts = svc._starts_for(
            {datetime(2026, 1, 15, tzinfo=UTC)},
            anchor,
            datetime(2026, 2, 10, tzinfo=UTC),
            duration_value=10,
            duration_unit="days",
        )
        assert starts == [
            (datetime(2026, 1, 25, tzinfo=UTC), datetime(2026, 2, 4, tzinfo=UTC)),
            (datetime(2026, 2, 4, tzinfo=UTC), datetime(2026, 2, 14, tzinfo=UTC)),
        ]

    def test_restarted_term_does_not_backfill_old_anchor(self):
        from app.billing.services import BillingService

        svc = BillingService()
        anchor = datetime(2026, 4, 20, tzinfo=UTC)
        existing = {
            datetime(2026, 1, 15, tzinfo=UTC),
            datetime(2026, 2, 15, tzinfo=UTC),
            datetime(2026, 3, 15, tzinfo=UTC),
        }

        starts = svc._starts_for(
            existing,
            anchor,
            anchor,
            duration_value=1,
            duration_unit="months",
        )
        assert starts == [(anchor, datetime(2026, 5, 20, tzinfo=UTC))]

    def test_future_invoice_does_not_skip_earlier_periods(self):
        from app.billing.services import BillingService

        svc = BillingService()
        anchor = datetime(2026, 1, 15, tzinfo=UTC)
        existing = {
            datetime(2026, 1, 15, tzinfo=UTC),
            datetime(2026, 4, 15, tzinfo=UTC),
        }

        starts = svc._starts_for(
            existing,
            anchor,
            datetime(2026, 3, 20, tzinfo=UTC),
            duration_value=1,
            duration_unit="months",
        )
        assert starts == [
            (datetime(2026, 2, 15, tzinfo=UTC), datetime(2026, 3, 15, tzinfo=UTC)),
            (datetime(2026, 3, 15, tzinfo=UTC), datetime(2026, 4, 15, tzinfo=UTC)),
        ]


class TestListAccess:
    """Global list: superadmin unrestricted, owners scoped, others denied."""

    def test_anonymous_gets_401(self, client):
        assert client.get("/api/v1/billing/invoices").status_code == 401

    def test_member_without_orgs_gets_403(self, member):
        assert member.get("/api/v1/billing/invoices").status_code == 403

    def test_admin_gets_403(self, admin):
        assert admin.get("/api/v1/billing/invoices").status_code == 403

    def test_owner_sees_only_owned_organizations(self, app, superadmin):
        org_a = _org_with_invoice(superadmin, name="Alpha", slug="alpha")
        _org_with_invoice(superadmin, name="Beta", slug="beta")
        owner, owner_id = _new_user(app, "orgowner")
        _add_member(superadmin, org_a, owner_id, role="owner")

        body = owner.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 1
        assert body["items"][0]["organizationId"] == org_a

    def test_plain_member_of_org_gets_403(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        outsider, outsider_id = _new_user(app, "orgmember")
        _add_member(superadmin, org_id, outsider_id, role="member")

        assert outsider.get("/api/v1/billing/invoices").status_code == 403


class TestListQueries:
    def test_paginated_shape(self, superadmin):
        _org_with_invoice(superadmin)
        body = superadmin.get("/api/v1/billing/invoices?page=1&per_page=5").get_json()
        assert set(body) == {"items", "total", "page", "perPage"}
        assert body["page"] == 1
        assert body["perPage"] == 5
        assert len(body["items"]) == 1

    def test_org_id_filter(self, superadmin):
        org_a = _org_with_invoice(superadmin, name="Alpha", slug="alpha")
        _org_with_invoice(superadmin, name="Beta", slug="beta")
        assert superadmin.get("/api/v1/billing/invoices").get_json()["total"] == 2

        body = superadmin.get(f"/api/v1/billing/invoices?orgId={org_a}").get_json()
        assert body["total"] == 1
        assert body["items"][0]["organizationId"] == org_a

    def test_status_filter(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        invoice_id = _first_invoice(superadmin)["id"]

        issued = superadmin.get("/api/v1/billing/invoices?status=issued").get_json()
        assert issued["total"] == 1

        superadmin.post(f"/api/v1/billing/invoices/{invoice_id}/pay")
        paid = superadmin.get("/api/v1/billing/invoices?status=paid").get_json()
        assert paid["total"] == 1
        assert paid["items"][0]["organizationId"] == org_id
        assert superadmin.get("/api/v1/billing/invoices?status=issued").get_json()[
            "total"
        ] == 0

    def test_invalid_status_filter(self, superadmin):
        response = superadmin.get("/api/v1/billing/invoices?status=bogus")
        assert response.status_code == 400
        assert response.get_json() == {"message": "invalid_status"}

    def test_search_by_org_name_and_number(self, superadmin):
        _org_with_invoice(superadmin, name="Zebra Corp", slug="zebra-corp")
        items = superadmin.get("/api/v1/billing/invoices?search=Zebra").get_json()[
            "items"
        ]
        assert len(items) == 1

        number = items[0]["number"]
        by_number = superadmin.get(
            f"/api/v1/billing/invoices?search={number}"
        ).get_json()
        assert by_number["total"] == 1


class TestInvoiceDetail:
    def test_owner_can_fetch_own_invoice(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        owner, owner_id = _new_user(app, "orgowner")
        _add_member(superadmin, org_id, owner_id, role="owner")
        invoice_id = _first_invoice(superadmin)["id"]

        response = owner.get(f"/api/v1/billing/invoices/{invoice_id}")
        assert response.status_code == 200
        assert response.get_json()["organizationId"] == org_id

    def test_non_member_gets_403(self, app, superadmin):
        _org_with_invoice(superadmin)
        invoice_id = _first_invoice(superadmin)["id"]
        outsider, _ = _new_user(app, "outsider")

        response = outsider.get(f"/api/v1/billing/invoices/{invoice_id}")
        assert response.status_code == 403

    def test_unknown_invoice_404(self, superadmin):
        response = superadmin.get("/api/v1/billing/invoices/no-such")
        assert response.status_code == 404
        assert response.get_json() == {"message": "invoice_not_found"}


class TestPayAndVoid:
    def test_owner_cannot_pay(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        owner, owner_id = _new_user(app, "orgowner")
        _add_member(superadmin, org_id, owner_id, role="owner")
        invoice_id = _first_invoice(superadmin)["id"]

        response = owner.post(f"/api/v1/billing/invoices/{invoice_id}/pay", json={})
        assert response.status_code == 403

    def test_pay_then_block_double_pay_and_void(self, superadmin):
        _org_with_invoice(superadmin)
        invoice_id = _first_invoice(superadmin)["id"]

        paid = superadmin.post(f"/api/v1/billing/invoices/{invoice_id}/pay", json={})
        assert paid.status_code == 200, paid.get_json()
        body = paid.get_json()
        assert body["status"] == "paid"
        assert body["paidOn"] is not None

        again = superadmin.post(f"/api/v1/billing/invoices/{invoice_id}/pay", json={})
        assert again.status_code == 422
        assert again.get_json() == {"message": "invoice_already_paid"}

        void_paid = superadmin.post(f"/api/v1/billing/invoices/{invoice_id}/void")
        assert void_paid.status_code == 422
        assert void_paid.get_json() == {"message": "invoice_not_voidable"}

    def test_void_blocks_repay_and_revoid(self, superadmin):
        _org_with_invoice(superadmin)
        invoice_id = _first_invoice(superadmin)["id"]

        voided = superadmin.post(f"/api/v1/billing/invoices/{invoice_id}/void")
        assert voided.status_code == 200
        assert voided.get_json()["status"] == "void"
        assert voided.get_json().get("paidOn") is None

        again = superadmin.post(f"/api/v1/billing/invoices/{invoice_id}/void")
        assert again.status_code == 422
        assert again.get_json() == {"message": "invoice_not_voidable"}

        pay = superadmin.post(f"/api/v1/billing/invoices/{invoice_id}/pay", json={})
        assert pay.status_code == 422
        assert pay.get_json() == {"message": "invoice_not_payable"}

    def test_pay_with_explicit_date(self, superadmin):
        _org_with_invoice(superadmin)
        invoice_id = _first_invoice(superadmin)["id"]
        paid_on = "2026-01-15T00:00:00+00:00"

        response = superadmin.post(
            f"/api/v1/billing/invoices/{invoice_id}/pay", json={"paidOn": paid_on}
        )
        assert response.status_code == 200
        assert response.get_json()["paidOn"] == paid_on

    def test_pay_invalid_date(self, superadmin):
        _org_with_invoice(superadmin)
        invoice_id = _first_invoice(superadmin)["id"]
        response = superadmin.post(
            f"/api/v1/billing/invoices/{invoice_id}/pay", json={"paidOn": "nope"}
        )
        assert response.status_code == 400
        assert "paid_on" in response.get_json()["message"]

    def test_pay_rejects_future_date(self, superadmin):
        _org_with_invoice(superadmin)
        invoice_id = _first_invoice(superadmin)["id"]
        response = superadmin.post(
            f"/api/v1/billing/invoices/{invoice_id}/pay",
            json={"paidOn": "2099-01-01T00:00:00+00:00"},
        )
        assert response.status_code == 400
        assert response.get_json() == {"message": "paid_on_in_future"}

    def test_pay_unknown_invoice_404(self, superadmin):
        response = superadmin.post("/api/v1/billing/invoices/no-such/pay", json={})
        assert response.status_code == 404

    def test_pay_records_received_amount(self, superadmin):
        _org_with_invoice(superadmin)
        invoice = _first_invoice(superadmin)
        assert invoice["amount"] == 500_000

        response = superadmin.post(
            f"/api/v1/billing/invoices/{invoice['id']}/pay", json={"amount": 650_000}
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json()["amount"] == 650_000
        assert _first_invoice(superadmin)["amount"] == 650_000

    def test_pay_without_amount_keeps_invoice_amount(self, superadmin):
        _org_with_invoice(superadmin)
        invoice = _first_invoice(superadmin)

        response = superadmin.post(
            f"/api/v1/billing/invoices/{invoice['id']}/pay", json={}
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json()["amount"] == invoice["amount"]

    def test_pay_amount_bounds(self, superadmin):
        _org_with_invoice(superadmin)
        invoice = _first_invoice(superadmin)
        for amount in (-1, 1_000_000_001):
            response = superadmin.post(
                f"/api/v1/billing/invoices/{invoice['id']}/pay",
                json={"amount": amount},
            )
            assert response.status_code == 400, amount
        assert _first_invoice(superadmin)["status"] == "issued"

    def test_member_cannot_void(self, member):
        assert member.post("/api/v1/billing/invoices/any/void").status_code == 403


class TestOrganizationInvoices:
    def test_owner_lists_own_org(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        owner, owner_id = _new_user(app, "orgowner")
        _add_member(superadmin, org_id, owner_id, role="owner")

        response = owner.get(f"/api/v1/billing/organizations/{org_id}/invoices")
        assert response.status_code == 200
        items = response.get_json()["items"]
        assert len(items) == 1
        assert items[0]["organizationId"] == org_id

    def test_plain_member_denied(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        outsider, outsider_id = _new_user(app, "orgmember")
        _add_member(superadmin, org_id, outsider_id, role="member")

        response = outsider.get(f"/api/v1/billing/organizations/{org_id}/invoices")
        assert response.status_code == 403

    def test_owner_sees_community_zero_invoice(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "orgowner")
        _add_member(superadmin, org_id, owner_id, role="owner")

        response = owner.get(f"/api/v1/billing/organizations/{org_id}/invoices")
        assert response.status_code == 200
        body = response.get_json()
        assert body["total"] == 1
        assert body["items"][0]["tier"] == "community"
        assert body["items"][0]["amount"] == 0

    def test_superadmin_can_list_any_org(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        response = superadmin.get(f"/api/v1/billing/organizations/{org_id}/invoices")
        assert response.status_code == 200
        assert len(response.get_json()["items"]) == 1

    def test_unknown_org_404(self, superadmin):
        response = superadmin.get("/api/v1/billing/organizations/no-such/invoices")
        assert response.status_code == 404

    def test_anonymous_401(self, client):
        assert client.get("/api/v1/billing/organizations/any/invoices").status_code == 401


class TestConcurrency:
    """Concurrent generation/pay/void never corrupts state or 409s a read."""

    def test_generation_retries_on_number_conflict(self, superadmin, monkeypatch):
        from app.billing.services import BillingService

        _org_with_invoice(superadmin)
        assert _first_invoice(superadmin)["number"].endswith("-0001")
        org_b = _create_org(superadmin, name="Beta", slug="beta").get_json()["id"]
        _set_tier(superadmin, org_b)

        real_next = BillingService._next_number
        state = {"calls": 0}

        def colliding(self, year):
            state["calls"] += 1
            if state["calls"] == 1:
                return f"INV-{year}-0001"  # stale count, duplicates Acme's
            return real_next(self, year)

        monkeypatch.setattr(BillingService, "_next_number", colliding)

        response = superadmin.get("/api/v1/billing/invoices")
        assert response.status_code == 200, response.get_json()
        numbers = [item["number"] for item in response.get_json()["items"]]
        assert len(numbers) == len(set(numbers)) == 2
        assert state["calls"] >= 2

    def test_transition_status_is_conditional(self, app, superadmin):
        from app.billing.repositories import InvoiceRepository

        _org_with_invoice(superadmin)
        invoice_id = _first_invoice(superadmin)["id"]

        with app.app_context():
            repo = InvoiceRepository()
            assert (
                repo.transition_status(
                    invoice_id,
                    from_status="issued",
                    to_status="paid",
                    paid_on=datetime.now(UTC),
                )
                is True
            )
            # A second transition from "issued" must miss the row.
            assert (
                repo.transition_status(
                    invoice_id, from_status="issued", to_status="void"
                )
                is False
            )


class TestBillingSettings:
    """Billing platform settings drive trial length and renewal lead time."""

    DEFAULTS = {
        "trialDays": 30,
        "invoiceLeadDays": 7,
    }

    def test_defaults(self, superadmin):
        response = superadmin.get("/api/v1/billing/settings")
        assert response.status_code == 200
        assert response.get_json() == self.DEFAULTS

    def test_update_persists(self, superadmin):
        updated = {"trialDays": 14, "invoiceLeadDays": 3}
        response = superadmin.put(
            "/api/v1/billing/settings",
            json={"trialDays": 14, "invoiceLeadDays": 3},
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json() == updated

        body = superadmin.get("/api/v1/billing/settings").get_json()
        assert body == updated

    def test_partial_update_keeps_other_fields(self, superadmin):
        superadmin.put("/api/v1/billing/settings", json={"trialDays": 14})

        response = superadmin.put(
            "/api/v1/billing/settings", json={"invoiceLeadDays": 3}
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json() == {
            "trialDays": 14,
            "invoiceLeadDays": 3,
        }

    def test_validation(self, superadmin):
        for payload in (
            {},
            {"trialDays": None},
            {"trialDays": -1, "invoiceLeadDays": 7},
            {"trialDays": 30, "invoiceLeadDays": -1},
            {"trialDays": "abc", "invoiceLeadDays": 7},
            {"trialDays": 30, "invoiceLeadDays": 366},
        ):
            response = superadmin.put("/api/v1/billing/settings", json=payload)
            assert response.status_code == 400, payload

    def test_guards(self, client, member, admin):
        assert client.get("/api/v1/billing/settings").status_code == 401
        assert member.get("/api/v1/billing/settings").status_code == 403
        assert admin.get("/api/v1/billing/settings").status_code == 403

        payload = {"trialDays": 10, "invoiceLeadDays": 5}
        assert admin.put("/api/v1/billing/settings", json=payload).status_code == 403


class TestTrialAndPlanExpiry:
    """New organizations inherit the trial length; assigning a plan expires
    at the plan's configured duration unless an explicit date is sent."""

    @staticmethod
    def _expires_on(client, org_id):
        body = client.get(f"/api/v1/tenancy/organizations/{org_id}").get_json()
        return body["subscription"].get("expiresOn")

    def test_default_trial_sets_expiry(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        expires = self._expires_on(superadmin, org_id)
        assert expires is not None
        delta = datetime.fromisoformat(expires) - datetime.now(UTC)
        assert timedelta(days=29) < delta <= timedelta(days=31)

    def test_custom_trial_days_applied(self, superadmin):
        superadmin.put(
            "/api/v1/billing/settings",
            json={"trialDays": 5, "invoiceLeadDays": 7},
        )
        org_id = _create_org(superadmin).get_json()["id"]
        expires = self._expires_on(superadmin, org_id)
        assert expires is not None
        delta = datetime.fromisoformat(expires) - datetime.now(UTC)
        assert timedelta(days=4) < delta <= timedelta(days=6)

    def test_zero_disables_expiry(self, superadmin):
        superadmin.put(
            "/api/v1/billing/settings",
            json={"trialDays": 0, "invoiceLeadDays": 7},
        )
        org_id = _create_org(superadmin).get_json()["id"]
        assert self._expires_on(superadmin, org_id) is None

    def test_plan_assignment_uses_plan_duration(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]

        body = _set_tier(superadmin, org_id).get_json()
        assert body["status"] == "active"
        delta = datetime.fromisoformat(body["expiresOn"]) - datetime.now(UTC)
        assert timedelta(days=27) < delta <= timedelta(days=31)

    def test_plan_assignment_replaces_live_expiry(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "community"),
                "expiresOn": "2099-01-01",
            },
        )

        body = _set_tier(superadmin, org_id).get_json()
        delta = datetime.fromisoformat(body["expiresOn"]) - datetime.now(UTC)
        assert delta < timedelta(days=40)


class TestRenewal:
    """The next period is invoiced inside the configured lead window."""

    def test_outside_window_no_renewal(self, superadmin):
        _org_with_invoice(superadmin)
        assert superadmin.get("/api/v1/billing/invoices").get_json()["total"] == 1
        assert superadmin.get("/api/v1/billing/invoices").get_json()["total"] == 1

    def test_inside_window_adds_next_period(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        current = _first_invoice(superadmin)
        _set_subscription(
            app, org_id, expires_on=datetime.now(UTC) + timedelta(days=3)
        )

        body = superadmin.get("/api/v1/billing/invoices").get_json()
        assert body["total"] == 2
        starts = sorted(
            datetime.fromisoformat(item["periodStart"]) for item in body["items"]
        )
        assert starts[1] == _next_period_start(current)

    def test_renewal_is_idempotent(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        _first_invoice(superadmin)
        _set_subscription(
            app, org_id, expires_on=datetime.now(UTC) + timedelta(days=3)
        )
        for _ in range(3):
            body = superadmin.get("/api/v1/billing/invoices").get_json()
            assert body["total"] == 2

    def test_zero_lead_disables_renewal(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        _first_invoice(superadmin)
        superadmin.put(
            "/api/v1/billing/settings",
            json={"trialDays": 30, "invoiceLeadDays": 0},
        )
        _set_subscription(
            app, org_id, expires_on=datetime.now(UTC) + timedelta(days=1)
        )
        assert superadmin.get("/api/v1/billing/invoices").get_json()["total"] == 1

    def test_no_expiry_has_no_renewal(self, app, superadmin):
        superadmin.put(
            "/api/v1/billing/settings",
            json={"trialDays": 0, "invoiceLeadDays": 7},
        )
        org_id = _org_with_invoice(superadmin)
        _first_invoice(superadmin)
        _set_subscription(app, org_id, expires_on=None)
        assert superadmin.get("/api/v1/billing/invoices").get_json()["total"] == 1


class TestManualInvoice:
    """Superadmin can issue one period's invoice ahead of the schedule."""

    def test_creates_next_period(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        start = _next_period_start(_first_invoice(superadmin))

        response = superadmin.post(
            "/api/v1/billing/invoices",
            json={"organizationId": org_id, "periodStart": start.isoformat()},
        )
        assert response.status_code == 201, response.get_json()
        body = response.get_json()
        assert body["organizationId"] == org_id
        assert body["organizationName"] == "Acme"
        assert datetime.fromisoformat(body["periodStart"]) == start
        assert datetime.fromisoformat(body["dueOn"]) == start + timedelta(days=14)
        assert body["amount"] == 500_000
        assert body["currency"] == "IDR"
        assert body["tier"] == "professional"
        assert body["status"] == "issued"

    def test_period_start_snaps_to_billing_day(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        start = _next_period_start(_first_invoice(superadmin))
        inside = start + timedelta(hours=12)
        payload = {"organizationId": org_id, "periodStart": inside.isoformat()}

        response = superadmin.post("/api/v1/billing/invoices", json=payload)
        assert response.status_code == 201, response.get_json()
        assert datetime.fromisoformat(response.get_json()["periodStart"]) == start

        duplicate = superadmin.post("/api/v1/billing/invoices", json=payload)
        assert duplicate.status_code == 409
        assert duplicate.get_json() == {"message": "invoice_period_exists"}

    def test_duplicate_period_conflicts(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        start = _next_period_start(_first_invoice(superadmin))
        payload = {"organizationId": org_id, "periodStart": start.isoformat()}

        assert (
            superadmin.post("/api/v1/billing/invoices", json=payload).status_code
            == 201
        )
        response = superadmin.post("/api/v1/billing/invoices", json=payload)
        assert response.status_code == 409
        assert response.get_json() == {"message": "invoice_period_exists"}

    def test_community_accepts_custom_amount(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.post(
            "/api/v1/billing/invoices",
            json={
                "organizationId": org_id,
                "periodStart": datetime.now(UTC).isoformat(),
                "amount": 50_000,
            },
        )
        assert response.status_code == 201, response.get_json()
        body = response.get_json()
        assert body["tier"] == "community"
        assert body["amount"] == 50_000

    def test_manual_default_uses_plan_price(self, superadmin):
        _set_plan_price(superadmin, "community", 20_000)
        org_id = _create_org(superadmin).get_json()["id"]

        response = superadmin.post(
            "/api/v1/billing/invoices",
            json={
                "organizationId": org_id,
                "periodStart": datetime.now(UTC).isoformat(),
            },
        )
        assert response.status_code == 201, response.get_json()
        assert response.get_json()["amount"] == 20_000

    def test_unpriced_plan_requires_an_amount(self, superadmin):
        plan = _create_plan(superadmin, "Enterprise Custom")
        org_id = _create_org(superadmin).get_json()["id"]
        _assign_plan(superadmin, org_id, plan["id"])

        missing = superadmin.post(
            "/api/v1/billing/invoices",
            json={
                "organizationId": org_id,
                "periodStart": datetime.now(UTC).isoformat(),
            },
        )
        assert missing.status_code == 400
        assert missing.get_json() == {"message": "amount_required"}

        issued = superadmin.post(
            "/api/v1/billing/invoices",
            json={
                "organizationId": org_id,
                "periodStart": datetime.now(UTC).isoformat(),
                "amount": 2_500_000,
            },
        )
        assert issued.status_code == 201, issued.get_json()
        body = issued.get_json()
        assert body["amount"] == 2_500_000
        assert body["tier"] == "professional"

    def test_amount_bounds(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        start = _next_period_start(_first_invoice(superadmin))
        for amount in (-1, 1_000_000_001):
            response = superadmin.post(
                "/api/v1/billing/invoices",
                json={
                    "organizationId": org_id,
                    "periodStart": start.isoformat(),
                    "amount": amount,
                },
            )
            assert response.status_code == 400, amount

    def test_inactive_organization_rejected(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        start = _next_period_start(_first_invoice(superadmin))
        superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={"isActive": False}
        )

        response = superadmin.post(
            "/api/v1/billing/invoices",
            json={"organizationId": org_id, "periodStart": start.isoformat()},
        )
        assert response.status_code == 422
        assert response.get_json() == {"message": "organization_inactive"}

    def test_period_before_subscription_rejected(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        response = superadmin.post(
            "/api/v1/billing/invoices",
            json={
                "organizationId": org_id,
                "periodStart": "2020-01-01T00:00:00+00:00",
            },
        )
        assert response.status_code == 400
        assert response.get_json() == {"message": "period_before_subscription"}

    def test_invalid_period_start(self, superadmin):
        org_id = _org_with_invoice(superadmin)
        response = superadmin.post(
            "/api/v1/billing/invoices",
            json={"organizationId": org_id, "periodStart": "nope"},
        )
        assert response.status_code == 400
        assert "period_start" in response.get_json()["message"]

    def test_unknown_organization(self, superadmin):
        response = superadmin.post(
            "/api/v1/billing/invoices",
            json={
                "organizationId": "no-such",
                "periodStart": datetime.now(UTC).isoformat(),
            },
        )
        assert response.status_code == 404
        assert response.get_json() == {"message": "organization_not_found"}

    def test_guards(self, client, member, admin):
        payload = {
            "organizationId": "any",
            "periodStart": datetime.now(UTC).isoformat(),
        }
        assert client.post("/api/v1/billing/invoices", json=payload).status_code == 401
        assert member.post("/api/v1/billing/invoices", json=payload).status_code == 403
        assert admin.post("/api/v1/billing/invoices", json=payload).status_code == 403


class TestPayExtendsExpiry:
    """Paying an invoice advances expiry and revives an expired subscription."""

    def test_pay_extends_to_period_end_and_reactivates(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        invoice = _first_invoice(superadmin)
        period_end = datetime.fromisoformat(invoice["periodEnd"])
        _set_subscription(
            app,
            org_id,
            expires_on=datetime.now(UTC) - timedelta(days=1),
            status="expired",
        )

        response = superadmin.post(
            f"/api/v1/billing/invoices/{invoice['id']}/pay", json={}
        )
        assert response.status_code == 200, response.get_json()
        sub = _subscription(superadmin, org_id)
        assert datetime.fromisoformat(sub["expiresOn"]) == period_end
        assert sub["status"] == "active"

    def test_pay_keeps_later_expiry(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        invoice = _first_invoice(superadmin)
        later = datetime.now(UTC) + timedelta(days=400)
        _set_subscription(app, org_id, expires_on=later)

        superadmin.post(f"/api/v1/billing/invoices/{invoice['id']}/pay", json={})
        sub = _subscription(superadmin, org_id)
        assert datetime.fromisoformat(sub["expiresOn"]) == later

    def test_pay_leaves_null_expiry(self, app, superadmin):
        org_id = _org_with_invoice(superadmin)
        invoice = _first_invoice(superadmin)
        _set_subscription(app, org_id, expires_on=None)

        superadmin.post(f"/api/v1/billing/invoices/{invoice['id']}/pay", json={})
        assert "expiresOn" not in _subscription(superadmin, org_id)
