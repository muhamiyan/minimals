"""Tests for tenancy guards â€” require_org_access, require_feature, current_org."""
from __future__ import annotations

import pytest
from conftest import csrf_client, default_plan_id, register
from flask import Blueprint, jsonify


def _probe(app):
    """Register a throwaway blueprint exercising both guards."""
    from app.tenancy.guards import current_org, require_feature, require_org_access

    bp = Blueprint("guard_probe", __name__, url_prefix="/_probe")

    @bp.get("/org/<org_id>")
    def org_access(org_id):
        if denied := require_org_access(org_id):
            return denied
        return jsonify({"orgId": current_org().id})

    @bp.get("/feature/<org_id>/<flag>")
    def feature(org_id, flag):
        if denied := require_feature(org_id, flag):
            return denied
        return jsonify({"enabled": True})

    app.register_blueprint(bp)
    return app.test_client()


def _create_org(client, name="Probe Co", slug="probe-co"):
    response = client.post(
        "/api/v1/tenancy/organizations", json={"name": name, "slug": slug}
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


@pytest.fixture()
def probe(app):
    """Register the guard-probe blueprint before any request is made."""
    return _probe(app)


def _login(app, username, role=None):
    from app.auth.models import User
    from framework.extensions import db

    client = csrf_client(app)
    response = register(
        client,
        email=f"{username}@example.com",
        username=username,
        fullName=username.title(),
    )
    assert response.status_code == 201, response.get_json()
    if role:
        user_id = response.get_json()["id"]
        with app.app_context():
            db.session.get(User, user_id).app_role = role
            db.session.commit()
    return client


class TestRequireOrgAccess:
    def test_unauthenticated_401(self, app, probe):
        assert probe.get("/_probe/org/any").status_code == 401

    def test_non_member_403_and_superadmin_200(self, app, probe):
        sa = _login(app, "root", role="superadmin")
        org_id = _create_org(sa)

        stranger = _login(app, "stranger")
        assert stranger.get(f"/_probe/org/{org_id}").status_code == 403

        assert sa.get(f"/_probe/org/{org_id}").status_code == 200

    def test_member_200_and_current_org_set(self, app, probe):
        sa = _login(app, "root", role="superadmin")
        org_id = _create_org(sa)
        member = _login(app, "member")
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        sa.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )

        body = member.get(f"/_probe/org/{org_id}").get_json()
        assert body["orgId"] == org_id

    def test_unknown_org_404_for_member(self, app, probe):
        member = _login(app, "member")
        assert member.get("/_probe/org/no-such").status_code == 404


class TestRequireFeature:
    def test_tier_grant_allows(self, app, probe):
        sa = _login(app, "root", role="superadmin")
        org_id = _create_org(sa)
        member = _login(app, "member")
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        sa.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        sa.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(sa, "professional"),
                "expiresOn": "2099-01-01",
            },
        )

        response = member.get(f"/_probe/feature/{org_id}/priority_support")
        assert response.status_code == 200

    def test_tier_denies(self, app, probe):
        sa = _login(app, "root", role="superadmin")
        org_id = _create_org(sa)
        member = _login(app, "member")
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        sa.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )

        response = member.get(f"/_probe/feature/{org_id}/priority_support")
        assert response.status_code == 403
        assert response.get_json() == {"message": "feature_not_enabled"}

    def test_expired_subscription_denies_even_superadmin(self, app, probe):
        sa = _login(app, "root", role="superadmin")
        org_id = _create_org(sa)
        sa.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(sa, "professional"),
                "status": "active",
                "expiresOn": "2020-01-01",
            },
        )

        response = sa.get(f"/_probe/feature/{org_id}/priority_support")
        assert response.status_code == 403
        assert response.get_json() == {"message": "feature_not_enabled"}

    def test_inactive_org_denies(self, app, probe):
        sa = _login(app, "root", role="superadmin")
        org_id = _create_org(sa)
        sa.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(sa, "professional"),
                "expiresOn": "2099-01-01",
            },
        )
        sa.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={"isActive": False}
        )

        response = sa.get(f"/_probe/feature/{org_id}/priority_support")
        assert response.status_code == 403

    def test_membership_still_required_before_feature(self, app, probe):
        sa = _login(app, "root", role="superadmin")
        org_id = _create_org(sa)
        sa.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(sa, "professional"),
                "expiresOn": "2099-01-01",
            },
        )
        stranger = _login(app, "stranger")

        response = stranger.get(f"/_probe/feature/{org_id}/priority_support")
        assert response.status_code == 403
        assert response.get_json() == {"message": "forbidden"}

    def test_probe_needs_login(self, app, probe):
        assert probe.get("/_probe/feature/any/flag").status_code == 401

