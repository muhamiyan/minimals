"""Dashboard stats endpoint — superadmin-only aggregates."""
from __future__ import annotations

from datetime import UTC, datetime

from conftest import csrf_client, default_plan_id


def _create_org(client, name="Acme", slug="acme", **overrides):
    response = client.post(
        "/api/v1/tenancy/organizations", json={"name": name, "slug": slug, **overrides}
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def _set_plan(client, org_id, tier="professional", **overrides):
    plan_id = default_plan_id(client, tier)
    payload = {"planId": plan_id, "status": "active", **overrides}
    response = client.put(
        f"/api/v1/tenancy/organizations/{org_id}/subscription", json=payload
    )
    assert response.status_code == 200, response.get_json()


def _create_user(app, username):
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


def _pay_invoice(superadmin, org_id, amount):
    period_start = datetime.now(UTC)
    response = superadmin.post(
        "/api/v1/billing/invoices",
        json={
            "organizationId": org_id,
            "periodStart": period_start.isoformat(),
            "amount": amount,
        },
    )
    assert response.status_code == 201, response.get_json()
    invoice_id = response.get_json()["id"]
    paid = superadmin.post(f"/api/v1/billing/invoices/{invoice_id}/pay", json={})
    assert paid.status_code == 200, paid.get_json()


def test_unauthenticated_is_401(client, app):
    assert client.get("/api/v1/dashboard/stats").status_code == 401


def test_member_is_403(member):
    assert member.get("/api/v1/dashboard/stats").status_code == 403


def test_admin_is_403(admin):
    assert admin.get("/api/v1/dashboard/stats").status_code == 403


def test_empty_payload_shape(superadmin):
    response = superadmin.get("/api/v1/dashboard/stats")
    assert response.status_code == 200, response.get_json()
    body = response.get_json()

    assert body["organizations"] == {"total": 0, "active": 0}
    assert body["users"]["total"] == 1  # the superadmin itself
    assert body["subscriptions"] == {
        "trial": 0,
        "active": 0,
        "expired": 0,
        "cancelled": 0,
    }
    assert body["invoices"] == {"issued": 0, "paid": 0, "void": 0}
    assert body["revenuePaid"] == 0

    orgs = body["organizationsPerMonth"]
    revenue = body["revenuePerMonth"]
    assert len(orgs) == 12
    assert len(revenue) == 12
    assert [row["month"] for row in orgs] == sorted(row["month"] for row in orgs)
    assert sum(row["count"] for row in orgs) == 0
    assert sum(row["amount"] for row in revenue) == 0
    assert orgs[-1]["month"] == datetime.now(UTC).strftime("%Y-%m")


def test_aggregates_with_data(app, superadmin):
    _create_user(app, "statmember")
    org_a = _create_org(superadmin, name="Acme", slug="acme")
    org_b = _create_org(superadmin, name="Bob Inc", slug="bob-inc")
    _set_plan(superadmin, org_a, status="active")
    _set_plan(superadmin, org_b, status="trial")
    _pay_invoice(superadmin, org_a, 250_000)

    body = superadmin.get("/api/v1/dashboard/stats").get_json()

    assert body["organizations"] == {"total": 2, "active": 2}
    assert body["users"]["total"] == 2
    assert body["subscriptions"]["active"] == 1
    assert body["subscriptions"]["trial"] == 1
    assert body["subscriptions"]["expired"] == 0
    assert body["invoices"]["paid"] == 1
    assert body["invoices"]["issued"] == 0
    assert body["revenuePaid"] == 250_000

    orgs = body["organizationsPerMonth"]
    revenue = body["revenuePerMonth"]
    current = datetime.now(UTC).strftime("%Y-%m")
    assert orgs[-1] == {"month": current, "count": 2}
    assert revenue[-1] == {"month": current, "amount": 250_000}
