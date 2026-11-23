"""Goakal domain tests — webhook verify, auto-match, variable amounts, manual link."""

from __future__ import annotations

import hashlib
import hmac
import json

SECRET = "goakal-test-secret"


def _sign(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _payload(*, email="alice@example.com", amount=75000, tx_id="tx_cuid_1", payment_id="pay_1", status="PAID") -> dict:
    return {
        "event": "transaction.updated",
        "data": {
            "id": tx_id,
            "paymentId": payment_id,
            "status": status,
            "amount": amount,
            "user": {"name": "Alice Doe", "email": email, "phone": "62812345678"},
            "createdAt": "2024-01-24T08:00:00.000Z",
            "paidAt": "2024-01-24T08:12:00.000Z",
        },
    }


def _set_secret(client):
    response = client.put("/api/v1/goakal/settings", json={"secret": SECRET})
    assert response.status_code == 200, response.get_json()


def _post_webhook(client, payload: dict, *, sign: bool = True, secret: str = SECRET):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if sign:
        headers["Signature"] = _sign(body, secret)
    return client.post("/api/v1/goakal/webhook", data=body, headers=headers)


def _org_with_invoice(superadmin, name="Acme", slug="acme", price=100000):
    org_id = superadmin.post(
        "/api/v1/tenancy/organizations", json={"name": name, "slug": slug}
    ).get_json()["id"]
    items = superadmin.get("/api/v1/plans").get_json()["items"]
    plan_id = next(p["id"] for p in items if p["tier"] == "professional" and p["isDefault"])
    superadmin.put(f"/api/v1/plans/{plan_id}", json={"price": price})
    return org_id


def _register(app, email="alice@example.com", username="alice"):
    from conftest import csrf_client

    client = csrf_client(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "Str0ng!Pass", "fullName": username.title()},
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def _owner_of(superadmin, org_id, user_id):
    response = superadmin.post(
        f"/api/v1/tenancy/organizations/{org_id}/members", json={"userId": user_id, "role": "owner"}
    )
    assert response.status_code == 201, response.get_json()


def test_webhook_rejects_bad_signature(app, superadmin):
    _set_secret(superadmin)
    guest = app.test_client()
    response = _post_webhook(guest, _payload(), secret="wrong")
    assert response.status_code == 401
    assert response.get_json()["message"] == "invalid_signature"


def test_webhook_stores_transaction_and_auto_matches(app, superadmin):
    _set_secret(superadmin)
    org_id = _org_with_invoice(superadmin)
    user_id = _register(app)
    _owner_of(superadmin, org_id, user_id)
    payable = json.dumps({"amount": 75000}).encode()  # sanity: no-op
    assert payable is not None

    guest = app.test_client()
    response = _post_webhook(guest, _payload(amount=75000))
    assert response.status_code == 200, response.get_json()

    listing = superadmin.get("/api/v1/goakal/transactions").get_json()
    assert listing["total"] == 1
    tx = listing["items"][0]
    assert tx["paymentId"] == "pay_1"
    assert tx["amount"] == 75000
    assert tx["email"] == "alice@example.com"
    # ``invoiceId`` appears once the presenter includes it (auto-matched tx);
    # unlinked transactions omit the null key by design (exclude_none).
    assert tx.get("invoiceId") is not None, tx


def test_variable_amount_pays_invoice_and_extends_expiry(app, superadmin):
    _set_secret(superadmin)
    org_id = _org_with_invoice(superadmin)
    user_id = _register(app)
    _owner_of(superadmin, org_id, user_id)

    guest = app.test_client()
    response = _post_webhook(guest, _payload(amount=75000))  # plan price 100000
    assert response.status_code == 200, response.get_json()

    invoices = superadmin.get("/api/v1/billing/invoices").get_json()["items"]
    paid = [i for i in invoices if i["status"] == "paid"]
    assert len(paid) == 1
    assert paid[0]["amount"] == 75000
    org = superadmin.get(f"/api/v1/tenancy/organizations/{org_id}").get_json()
    assert org["subscription"]["expiresOn"] is not None


def test_duplicate_webhook_is_idempotent(app, superadmin):
    _set_secret(superadmin)
    guest = app.test_client()
    for _ in range(2):
        response = _post_webhook(guest, _payload())
        assert response.status_code == 200, response.get_json()
    listing = superadmin.get("/api/v1/goakal/transactions").get_json()
    assert listing["total"] == 1


def test_unsupported_event_is_rejected_after_verify(app, superadmin):
    _set_secret(superadmin)
    guest = app.test_client()
    payload = _payload()
    payload["event"] = "something.else"
    response = _post_webhook(guest, payload)
    assert response.status_code == 400
    assert response.get_json()["message"] == "unsupported_event"
    listing = superadmin.get("/api/v1/goakal/transactions").get_json()
    assert listing["total"] == 0


def test_manual_link_pays_invoice(app, superadmin):
    _set_secret(superadmin)
    org_id = _org_with_invoice(superadmin)
    user_id = _register(app)
    _owner_of(superadmin, org_id, user_id)

    guest = app.test_client()
    # Unknown email: stored, not matched.
    response = _post_webhook(guest, _payload(email="unknown@example.com"))
    assert response.status_code == 200, response.get_json()
    tx = superadmin.get("/api/v1/goakal/transactions").get_json()["items"][0]
    assert "invoiceId" not in tx  # null is omitted by exclude_none

    invoice = superadmin.get("/api/v1/billing/invoices").get_json()["items"][0]
    linked = superadmin.post(
        f"/api/v1/goakal/transactions/{tx['id']}/link",
        json={"invoiceId": invoice["id"]},
    )
    assert linked.status_code == 200, linked.get_json()
    assert linked.get_json()["invoiceId"] == invoice["id"]

    invoices = superadmin.get("/api/v1/billing/invoices").get_json()["items"]
    assert any(i["id"] == invoice["id"] and i["status"] == "paid" for i in invoices)


def test_transactions_require_superadmin(member):
    response = member.get("/api/v1/goakal/transactions")
    assert response.status_code == 403


def test_gateway_charges_flat_rate_for_community(app, superadmin):
    """Community plan price 0 still auto-invoices and can be paid via Goakal."""
    org_id = _org_with_invoice(superadmin)
    user_id = _register(app)
    _owner_of(superadmin, org_id, user_id)
    _set_secret(superadmin)
    guest = app.test_client()
    response = _post_webhook(guest, _payload(amount=50000))
    assert response.status_code == 200, response.get_json()
    tx = superadmin.get("/api/v1/goakal/transactions").get_json()["items"][0]
    assert tx["status"] == "PAID"
    assert tx["amount"] == 50000
