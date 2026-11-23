from __future__ import annotations

from datetime import datetime, timedelta

from conftest import csrf_client, default_plan_id


def _create_org(client, name="Acme", slug="acme"):
    return client.post(
        "/api/v1/tenancy/organizations", json={"name": name, "slug": slug}
    )


class TestOrganizationCrud:
    def test_member_cannot_list(self, member):
        assert member.get("/api/v1/tenancy/organizations").status_code == 403

    def test_admin_cannot_list(self, admin):
        assert admin.get("/api/v1/tenancy/organizations").status_code == 403

    def test_superadmin_can_list(self, superadmin):
        assert superadmin.get("/api/v1/tenancy/organizations").status_code == 200

    def test_create_org(self, superadmin):
        response = _create_org(superadmin)
        assert response.status_code == 201, response.get_json()
        body = response.get_json()
        assert body["name"] == "Acme"
        assert body["slug"] == "acme"
        assert body["isActive"] is True
        assert body["subscription"]["tier"] == "community"
        assert body["subscription"]["status"] == "active"
        assert body["memberCount"] == 0

    def test_create_org_duplicate_slug(self, superadmin):
        _create_org(superadmin)
        response = _create_org(superadmin, name="Acme 2", slug="acme")
        assert response.status_code == 409
        assert response.get_json() == {"message": "slug_already_taken"}

    def test_create_org_invalid_slug(self, superadmin):
        response = _create_org(superadmin, name="Bad", slug="Bad Slug!")
        assert response.status_code == 400
        assert "slug" in response.get_json()["message"]

    def test_list_paginated(self, superadmin):
        _create_org(superadmin, name="One", slug="one")
        _create_org(superadmin, name="Two", slug="two")
        body = superadmin.get("/api/v1/tenancy/organizations").get_json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_list_search_matches_name_or_slug(self, superadmin):
        _create_org(superadmin, name="Zeta", slug="zz-top")
        _create_org(superadmin, name="Beta Corp", slug="beta-corp")

        by_name = superadmin.get(
            "/api/v1/tenancy/organizations?search=zeta"
        ).get_json()
        assert [item["slug"] for item in by_name["items"]] == ["zz-top"]

        by_slug = superadmin.get(
            "/api/v1/tenancy/organizations?search=beta-"
        ).get_json()
        assert [item["slug"] for item in by_slug["items"]] == ["beta-corp"]

    def test_get_org(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.get(f"/api/v1/tenancy/organizations/{org_id}")
        assert response.status_code == 200
        assert response.get_json()["slug"] == "acme"

    def test_get_org_not_found(self, superadmin):
        response = superadmin.get("/api/v1/tenancy/organizations/no-such")
        assert response.status_code == 404

    def test_update_org(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}",
            json={"name": "Acme Corp", "isActive": False},
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["name"] == "Acme Corp"
        assert body["isActive"] is False

    def test_update_org_slug_conflict(self, superadmin):
        _create_org(superadmin, name="One", slug="one")
        org_id = _create_org(superadmin, name="Two", slug="two").get_json()["id"]
        response = superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={"slug": "one"}
        )
        assert response.status_code == 409

    def test_update_org_empty_body(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={}
        )
        assert response.status_code == 400
        assert "no_fields_to_update" in response.get_json()["message"]

    def test_admin_cannot_update_org(self, admin):
        assert (
            admin.patch("/api/v1/tenancy/organizations/any", json={"name": "X"}).status_code
            == 403
        )

    def test_created_on_is_utc_annotated(self, superadmin):
        body = _create_org(superadmin).get_json()
        assert body["createdOn"].endswith("+00:00")
        assert body["subscription"]["startedOn"].endswith("+00:00")


class TestSubscription:
    def test_get_subscription(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}/subscription"
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["tier"] == "community"
        assert body["status"] == "active"

    def test_upsert_subscription(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
                "status": "trial",
                "featureFlags": {"custom_domain": True},
            },
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["tier"] == "professional"
        assert body["planId"] == default_plan_id(superadmin, "professional")
        assert body["planName"] == "Professional"
        assert body["status"] == "trial"
        assert body["featureFlags"] == {"custom_domain": True}

    def test_upsert_without_expiry_restarts_anchor(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        before = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}/subscription"
        ).get_json()["startedOn"]
        plan = superadmin.post(
            "/api/v1/plans",
            json={
                "name": "Thirty days",
                "tier": "professional",
                "price": 1000,
                "durationValue": 30,
                "durationUnit": "days",
            },
        ).get_json()

        body = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": plan["id"]},
        ).get_json()

        started = datetime.fromisoformat(body["startedOn"])
        expires = datetime.fromisoformat(body["expiresOn"])
        assert started > datetime.fromisoformat(before)
        assert expires - started == timedelta(days=30)

    def test_upsert_unknown_plan(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": "no-such-plan"},
        )
        assert response.status_code == 404
        assert response.get_json() == {"message": "plan_not_found"}

    def test_upsert_requires_a_plan(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription", json={}
        )
        assert response.status_code == 400
        assert "plan_id" in response.get_json()["message"]

    def test_upsert_invalid_status(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "community"),
                "status": "pending",
            },
        )
        assert response.status_code == 400
        assert "status" in response.get_json()["message"]

    def test_upsert_on_missing_org(self, superadmin):
        response = superadmin.put(
            "/api/v1/tenancy/organizations/no-such/subscription",
            json={"planId": default_plan_id(superadmin, "community")},
        )
        assert response.status_code == 404

    def test_upsert_invalid_expires_on(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "community"),
                "expiresOn": "not-a-date",
            },
        )
        assert response.status_code == 400
        assert "expires_on" in response.get_json()["message"]

    def test_upsert_naive_expiry_is_utc_annotated(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
                "expiresOn": "2027-06-30",
            },
        )
        assert response.status_code == 200
        assert response.get_json()["expiresOn"] == "2027-06-30T00:00:00+00:00"

    def test_admin_cannot_upsert_subscription(self, admin, superadmin):
        response = admin.put(
            "/api/v1/tenancy/organizations/any/subscription",
            json={"planId": default_plan_id(superadmin, "professional")},
        )
        assert response.status_code == 403


class TestFeatureFlags:
    def test_has_feature_tier_default(self, superadmin, app):
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": default_plan_id(superadmin, "professional")},
        )
        with app.app_context():
            svc = TenancyService()
            assert svc.has_feature(org_id, "priority_support") is True
            assert svc.has_feature(org_id, "todo") is False
            assert svc.has_feature(org_id, "nonexistent") is False

    def test_has_feature_explicit_override(self, superadmin, app):
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
                "featureFlags": {"priority_support": False},
            },
        )
        with app.app_context():
            assert TenancyService().has_feature(org_id, "priority_support") is False

    def test_resolve_features_tier_defaults(self, superadmin, app):
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": default_plan_id(superadmin, "professional")},
        )
        with app.app_context():
            features = TenancyService().resolve_features(org_id)
        assert features["priority_support"] is True
        assert features["advanced_reporting"] is True
        assert features["custom_domain"] is True
        assert features["todo"] is False

    def test_registry_keys_resolved_for_community(self, superadmin, app):
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        with app.app_context():
            features = TenancyService().resolve_features(org_id)
        assert features == {
            "advanced_reporting": False,
            "priority_support": False,
            "custom_domain": False,
            "todo": False,
        }

    def test_unknown_override_keys_are_not_resolved(self, superadmin, app):
        from app.plans.features import FEATURE_KEYS
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
                "featureFlags": {"teleportation": True},
            },
        )
        assert response.status_code == 400
        assert response.get_json() == {"message": "feature_flags_unknown_feature"}

        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
            },
        )
        with app.app_context():
            features = TenancyService().resolve_features(org_id)
        assert set(features) == set(FEATURE_KEYS)
        assert features["priority_support"] is True
        with app.app_context():
            features = TenancyService().resolve_features(org_id)
        assert set(features) == set(FEATURE_KEYS)
        assert features["priority_support"] is True

    def test_plan_features_drive_resolution(self, superadmin, app):
        from app.tenancy.services import TenancyService

        plan = superadmin.post(
            "/api/v1/plans",
            json={
                "name": "Reporting only",
                "tier": "professional",
                "durationValue": 1,
                "durationUnit": "months",
                "features": {"advanced_reporting": True},
            },
        ).get_json()
        org_id = _create_org(superadmin).get_json()["id"]
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": plan["id"]},
        )
        with app.app_context():
            assert TenancyService().resolve_features(org_id) == {
                "advanced_reporting": True,
                "priority_support": False,
                "custom_domain": False,
                "todo": False,
            }

        superadmin.put(
            f"/api/v1/plans/{plan['id']}",
            json={"features": {"priority_support": True}},
        )
        with app.app_context():
            features = TenancyService().resolve_features(org_id)
        assert features["priority_support"] is True
        assert features["advanced_reporting"] is False

    def test_resolve_features_empty_for_unknown_org(self, app):
        from app.tenancy.services import TenancyService

        with app.app_context():
            assert TenancyService().resolve_features("no-such") == {}

    def test_stale_expiry_synced_in_org_payload(self, superadmin, member, app):
        from datetime import UTC, datetime, timedelta

        from app.tenancy.repositories import SubscriptionRepository
        from framework.extensions import db

        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
                "expiresOn": "2099-01-01",
            },
        )
        with app.app_context():
            sub = SubscriptionRepository().find_by_org(org_id)
            sub.expires_on = datetime.now(UTC) - timedelta(days=1)
            db.session.commit()

        detail = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}"
        ).get_json()
        assert detail["subscription"]["status"] == "expired"

        listed = superadmin.get("/api/v1/tenancy/organizations").get_json()
        assert listed["items"][0]["subscription"]["status"] == "expired"

        mine = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert mine["items"][0]["subscription"]["status"] == "expired"

    def test_inactive_org_all_features_false(self, superadmin, app):
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
                "expiresOn": "2099-01-01",
            },
        )
        superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={"isActive": False}
        )
        with app.app_context():
            svc = TenancyService()
            assert svc.has_feature(org_id, "priority_support") is False
            features = svc.resolve_features(org_id)
        assert features != {}
        assert all(v is False for v in features.values())

    def test_inactive_org_features_endpoint_false(
        self, superadmin, member
    ):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
                "expiresOn": "2099-01-01",
            },
        )
        superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={"isActive": False}
        )
        body = member.get(
            f"/api/v1/tenancy/organizations/{org_id}/features"
        ).get_json()
        assert all(v is False for v in body["features"].values())


class TestReadQueries:
    def _count_queries(self, app, fn):
        from sqlalchemy import event

        statements: list[str] = []
        with app.app_context():
            from framework.extensions import db

            engine = db.engine

        def _record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(engine, "before_cursor_execute", _record)
        try:
            fn()
        finally:
            event.remove(engine, "before_cursor_execute", _record)
        return len(statements)

    def test_org_list_subscription_is_eager(self, superadmin, app):
        for i in range(5):
            _create_org(superadmin, name=f"Co {i}", slug=f"co-{i}")

        count = self._count_queries(
            app, lambda: superadmin.get("/api/v1/tenancy/organizations")
        )
        # auth + count + orgs + selectin subscriptions + audit/select ~= small
        # constant; N+1 would add ~1 per org.
        assert count <= 8, f"{count} queries for 5 orgs"

    def test_member_list_user_is_eager(self, superadmin, member, app):
        org_id = _create_org(superadmin).get_json()["id"]

        for i in range(4):
            c = csrf_client(app)
            c.post(
                "/api/v1/auth/register",
                json={
                    "email": f"u{i}@example.com",
                    "username": f"user{i}",
                    "password": "Str0ng!Pass",
                    "fullName": f"User {i}",
                },
            )
            uid = c.get("/api/v1/auth/me").get_json()["id"]
            superadmin.post(
                f"/api/v1/tenancy/organizations/{org_id}/members",
                json={"userId": uid},
            )

        count = self._count_queries(
            app,
            lambda: superadmin.get(
                f"/api/v1/tenancy/organizations/{org_id}/members"
            ),
        )
        assert count <= 8, f"{count} queries for 4 members"


class TestSubscriptionLifecycle:
    def _put(self, superadmin, org_id, **payload):
        return superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription", json=payload
        )

    def test_upsert_past_expiry_expires_immediately(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        body = self._put(
            superadmin,
            org_id,
            planId=default_plan_id(superadmin, "professional"),
            status="active",
            expiresOn="2020-01-01",
        ).get_json()
        assert body["status"] == "expired"

    def test_upsert_future_expiry_stays_active(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        body = self._put(
            superadmin,
            org_id,
            planId=default_plan_id(superadmin, "professional"),
            status="active",
            expiresOn="2099-01-01",
        ).get_json()
        assert body["status"] == "active"

    def test_get_subscription_lazily_expires_stale_row(self, superadmin, app):
        from datetime import UTC, datetime, timedelta

        from app.infra.audit import AuditLog
        from app.tenancy.repositories import SubscriptionRepository
        from framework.extensions import db

        org_id = _create_org(superadmin).get_json()["id"]
        with app.app_context():
            sub = SubscriptionRepository().find_by_org(org_id)
            sub.expires_on = datetime.now(UTC) - timedelta(days=1)
            db.session.commit()

        body = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}/subscription"
        ).get_json()
        assert body["status"] == "expired"
        assert body["expiresOn"].endswith("+00:00")

        with app.app_context():
            stored = SubscriptionRepository().find_by_org(org_id)
            assert stored.status == "expired"
            actions = [
                row.action
                for row in db.session.scalars(db.select(AuditLog)).all()
            ]
        assert "subscription_expired" in actions

    def test_cancelled_subscription_stays_cancelled(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        body = self._put(
            superadmin,
            org_id,
            planId=default_plan_id(superadmin, "professional"),
            status="cancelled",
        ).get_json()
        assert body["status"] == "cancelled"
        body = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}/subscription"
        ).get_json()
        assert body["status"] == "cancelled"

    def test_has_feature_false_when_expired(self, superadmin, app):
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        self._put(
            superadmin,
            org_id,
            planId=default_plan_id(superadmin, "professional"),
            status="active",
            expiresOn="2020-01-01",
        )
        with app.app_context():
            svc = TenancyService()
            assert svc.has_feature(org_id, "priority_support") is False
            assert all(v is False for v in svc.resolve_features(org_id).values())

    def test_has_feature_false_when_cancelled(self, superadmin, app):
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        self._put(
            superadmin,
            org_id,
            planId=default_plan_id(superadmin, "professional"),
            status="cancelled",
            featureFlags={"priority_support": True},
        )
        with app.app_context():
            assert (
                TenancyService().has_feature(org_id, "priority_support") is False
            )

    def test_trial_unexpired_still_has_features(self, superadmin, app):
        from app.tenancy.services import TenancyService

        org_id = _create_org(superadmin).get_json()["id"]
        self._put(
            superadmin,
            org_id,
            planId=default_plan_id(superadmin, "professional"),
            status="trial",
            expiresOn="2099-01-01",
        )
        with app.app_context():
            assert (
                TenancyService().has_feature(org_id, "priority_support") is True
            )


class TestFeaturesEndpoint:
    def test_superadmin_can_fetch(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}/features"
        )
        assert response.status_code == 200
        assert response.get_json()["features"]["priority_support"] is False

    def test_member_can_fetch(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        response = member.get(
            f"/api/v1/tenancy/organizations/{org_id}/features"
        )
        assert response.status_code == 200

    def test_non_member_forbidden(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        response = member.get(
            f"/api/v1/tenancy/organizations/{org_id}/features"
        )
        assert response.status_code == 403

    def test_unknown_org_returns_404(self, superadmin):
        response = superadmin.get(
            "/api/v1/tenancy/organizations/no-such/features"
        )
        assert response.status_code == 404

    def test_admin_forbidden(self, admin, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = admin.get(f"/api/v1/tenancy/organizations/{org_id}/features")
        assert response.status_code == 403

    def test_expired_org_all_features_false(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={
                "planId": default_plan_id(superadmin, "professional"),
                "status": "active",
                "expiresOn": "2020-01-01",
            },
        )
        body = member.get(
            f"/api/v1/tenancy/organizations/{org_id}/features"
        ).get_json()
        assert body["features"] != {}
        assert all(v is False for v in body["features"].values())

    def test_requires_login(self, client):
        assert (
            client.get("/api/v1/tenancy/organizations/x/features").status_code
            == 401
        )


class TestMembers:
    def _register_user(self, client, username="bob"):
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
        return response.get_json()["id"]

    def test_add_member(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        response = superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id, "role": "owner"},
        )
        assert response.status_code == 201
        body = response.get_json()
        assert body["userId"] == user_id
        assert body["role"] == "owner"

    def test_add_member_duplicate(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        response = superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        assert response.status_code == 409

    def test_add_member_invalid_role(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        response = superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id, "role": "boss"},
        )
        assert response.status_code == 400

    def test_add_member_unknown_user(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": "no-such-user"},
        )
        assert response.status_code == 404

    def test_list_members(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        body = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}/members"
        ).get_json()
        assert len(body["items"]) == 1
        assert body["items"][0]["username"] == "member"

    def test_remove_member(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        response = superadmin.delete(
            f"/api/v1/tenancy/organizations/{org_id}/members/{user_id}"
        )
        assert response.status_code == 204
        body = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}/members"
        ).get_json()
        assert body["items"] == []

    def test_remove_member_not_found(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.delete(
            f"/api/v1/tenancy/organizations/{org_id}/members/no-such"
        )
        assert response.status_code == 404

    def test_admin_cannot_add_member(self, admin, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        response = admin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        assert response.status_code == 403


class TestMyOrganizations:
    def test_returns_member_orgs(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert len(body["items"]) == 1
        assert body["items"][0]["id"] == org_id

    def test_empty_for_non_member(self, member):
        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["items"] == []

    def test_requires_login(self, client):
        assert client.get("/api/v1/tenancy/my-organizations").status_code == 401


class TestDefaultOrganization:
    def test_default_id_is_null_without_membership(self, member):
        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["defaultId"] is None

    def test_member_sets_own_default(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )

        response = member.put(
            "/api/v1/tenancy/my-organizations/default", json={"orgId": org_id}
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json() == {"defaultId": org_id}

        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["defaultId"] == org_id

    def test_unknown_org_is_not_found(self, member):
        response = member.put(
            "/api/v1/tenancy/my-organizations/default", json={"orgId": "x" * 36}
        )
        assert response.status_code == 404
        assert response.get_json() == {"message": "organization_not_found"}

    def test_non_member_is_rejected(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        response = member.put(
            "/api/v1/tenancy/my-organizations/default", json={"orgId": org_id}
        )
        assert response.status_code == 403
        assert response.get_json() == {"message": "not_a_member"}

    def test_superadmin_still_needs_membership(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        response = superadmin.put(
            "/api/v1/tenancy/my-organizations/default", json={"orgId": org_id}
        )
        assert response.status_code == 403

    def test_inactive_org_is_rejected(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={"isActive": False}
        )

        response = member.put(
            "/api/v1/tenancy/my-organizations/default", json={"orgId": org_id}
        )
        assert response.status_code == 422
        assert response.get_json() == {"message": "organization_inactive"}

    def test_default_of_org_left_is_reported_unset(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        member.put("/api/v1/tenancy/my-organizations/default", json={"orgId": org_id})
        superadmin.delete(f"/api/v1/tenancy/organizations/{org_id}/members/{user_id}")

        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["items"] == []
        assert body["defaultId"] is None

    def test_requires_login(self, client):
        response = client.put(
            "/api/v1/tenancy/my-organizations/default", json={"orgId": "x"}
        )
        assert response.status_code == 401

    def test_requires_org_id(self, member):
        response = member.put("/api/v1/tenancy/my-organizations/default", json={})
        assert response.status_code == 400
class TestDefaultOrgLifecycle:
    """`default_org_id` is seeded by the first membership, never overwritten."""

    def test_self_service_creation_seeds_the_default(self, member):
        org_id = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Seed Org", "slug": "seed-org"},
        ).get_json()["id"]

        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["defaultId"] == org_id

    def test_console_creation_does_not_seed_the_caller(self, app, superadmin):
        from app.auth.models import User
        from framework.extensions import db

        user_id = superadmin.get("/api/v1/auth/me").get_json()["id"]
        _create_org(superadmin)

        with app.app_context():
            assert db.session.get(User, user_id).default_org_id is None

    def test_add_member_seeds_a_missing_default(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )

        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["defaultId"] == org_id

    def test_add_member_keeps_an_existing_default(self, superadmin, member):
        own_id = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Mine", "slug": "mine"},
        ).get_json()["id"]
        other_id = _create_org(superadmin, name="Other", slug="other").get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{other_id}/members",
            json={"userId": user_id},
        )

        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["defaultId"] == own_id

    def test_redeem_seeds_a_missing_default(self, app, superadmin):
        org_id = _create_org(
            superadmin, name="Seed Join", slug="seed-join"
        ).get_json()["id"]
        owner, owner_id = _new_user(app, "seedjoinowner")
        _add_member(superadmin, org_id, owner_id, role="owner")
        code = owner.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes", json={}
        ).get_json()["code"]
        joiner, _ = _new_user(app, "seedjoiner")
        joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code})

        body = joiner.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["defaultId"] == org_id

    def test_removing_the_membership_clears_the_default(self, app, superadmin, member):
        from app.auth.models import User
        from framework.extensions import db

        org_id = _create_org(superadmin).get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": user_id},
        )
        superadmin.delete(
            f"/api/v1/tenancy/organizations/{org_id}/members/{user_id}"
        )

        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["defaultId"] is None
        with app.app_context():
            assert db.session.get(User, user_id).default_org_id is None

    def test_removing_another_org_keeps_the_default(self, superadmin, member):
        own_id = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Kept", "slug": "kept"},
        ).get_json()["id"]
        other_id = _create_org(superadmin, name="Dropped", slug="dropped").get_json()["id"]
        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        superadmin.post(
            f"/api/v1/tenancy/organizations/{other_id}/members",
            json={"userId": user_id},
        )
        superadmin.delete(
            f"/api/v1/tenancy/organizations/{other_id}/members/{user_id}"
        )

        body = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["defaultId"] == own_id

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


class TestOwnerMembership:
    """Member endpoints are owner-scoped; superadmin keeps its bypass."""

    def test_owner_can_list_and_manage_members(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "orgowner")
        _, member_id = _new_user(app, "orgmember")
        _add_member(superadmin, org_id, owner_id, role="owner")
        _add_member(superadmin, org_id, member_id, role="member")

        listed = owner.get(f"/api/v1/tenancy/organizations/{org_id}/members")
        assert listed.status_code == 200
        # Creating an org does not enroll the creator, so these two are all.
        assert len(listed.get_json()["items"]) == 2

        _, third_id = _new_user(app, "orgthird")
        added = owner.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": third_id},
        )
        assert added.status_code == 201

        removed = owner.delete(
            f"/api/v1/tenancy/organizations/{org_id}/members/{third_id}"
        )
        assert removed.status_code == 204

    def test_plain_member_cannot_manage_members(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        plain, plain_id = _new_user(app, "plainmember")
        _, other_id = _new_user(app, "plainother")
        _add_member(superadmin, org_id, plain_id, role="member")
        _add_member(superadmin, org_id, other_id, role="member")

        assert (
            plain.get(f"/api/v1/tenancy/organizations/{org_id}/members").status_code
            == 403
        )
        assert (
            plain.post(
                f"/api/v1/tenancy/organizations/{org_id}/members",
                json={"userId": other_id},
            ).status_code
            == 403
        )
        assert (
            plain.delete(
                f"/api/v1/tenancy/organizations/{org_id}/members/{other_id}"
            ).status_code
            == 403
        )

    def test_cannot_remove_the_only_owner(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "lonelyowner")
        _add_member(superadmin, org_id, owner_id, role="owner")

        response = owner.delete(
            f"/api/v1/tenancy/organizations/{org_id}/members/{owner_id}"
        )
        assert response.status_code == 422
        assert response.get_json() == {"message": "last_owner_cannot_be_removed"}

    def test_owner_blocked_even_when_other_members_remain(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "soleowner")
        _, member_id = _new_user(app, "leftbehind")
        _add_member(superadmin, org_id, owner_id, role="owner")
        _add_member(superadmin, org_id, member_id, role="member")

        response = owner.delete(
            f"/api/v1/tenancy/organizations/{org_id}/members/{owner_id}"
        )
        assert response.status_code == 422
        assert response.get_json() == {"message": "last_owner_cannot_be_removed"}

    def test_owner_removable_when_another_owner_remains(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        first, first_id = _new_user(app, "ownerone")
        _, second_id = _new_user(app, "ownertwo")
        _add_member(superadmin, org_id, first_id, role="owner")
        _add_member(superadmin, org_id, second_id, role="owner")

        response = first.delete(
            f"/api/v1/tenancy/organizations/{org_id}/members/{second_id}"
        )
        assert response.status_code == 204


class TestMemberOrganizationAccess:
    def test_member_can_fetch_their_organization(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        viewer, viewer_id = _new_user(app, "orgviewer")
        _add_member(superadmin, org_id, viewer_id, role="member")

        response = viewer.get(f"/api/v1/tenancy/organizations/{org_id}")
        assert response.status_code == 200
        assert response.get_json()["id"] == org_id

    def test_non_member_still_cannot_fetch_organization(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        outsider, _ = _new_user(app, "orgoutsider")
        assert (
            outsider.get(f"/api/v1/tenancy/organizations/{org_id}").status_code == 403
        )

    def test_my_organizations_reports_caller_role(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "roleowner")
        plain, plain_id = _new_user(app, "rolemember")
        _add_member(superadmin, org_id, owner_id, role="owner")
        _add_member(superadmin, org_id, plain_id, role="member")

        body = owner.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["items"][0]["myRole"] == "owner"

        body = plain.get("/api/v1/tenancy/my-organizations").get_json()
        assert body["items"][0]["myRole"] == "member"

    def test_superadmin_list_does_not_claim_a_role(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        body = superadmin.get("/api/v1/tenancy/organizations").get_json()
        assert body["items"][0]["id"] == org_id
        assert "myRole" not in body["items"][0]


class TestUserLookup:
    """The add-member form checks one identifier at a time — no listing."""

    def test_owner_with_plain_app_role_can_lookup_and_add(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "pickerowner")
        _, target_id = _new_user(app, "picktarget")
        _add_member(superadmin, org_id, owner_id, role="owner")

        # /account/users would 403 this caller (app_role "user"); the
        # org-scoped lookup must not.
        by_username = owner.get(
            f"/api/v1/tenancy/organizations/{org_id}/user-lookup"
            "?identifier=picktarget"
        )
        assert by_username.status_code == 200
        body = by_username.get_json()
        assert body["status"] == "ok"
        assert body["userId"] == target_id
        # Single object — never a directory listing.
        assert "items" not in body

        by_email = owner.get(
            f"/api/v1/tenancy/organizations/{org_id}/user-lookup"
            "?identifier=picktarget%40example.com"
        )
        assert by_email.status_code == 200
        assert by_email.get_json()["userId"] == target_id

        added = owner.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": target_id},
        )
        assert added.status_code == 201

    def test_unknown_identifier_is_not_found_not_error(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "lookupowner")
        _add_member(superadmin, org_id, owner_id, role="owner")

        response = owner.get(
            f"/api/v1/tenancy/organizations/{org_id}/user-lookup"
            "?identifier=ghost%40example.com"
        )
        assert response.status_code == 200
        # Presenters exclude None — null fields are simply absent.
        assert response.get_json() == {"status": "not_found"}

    def test_existing_member_reports_already_member(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "lookupholder")
        _, member_id = _new_user(app, "lookupinside")
        _add_member(superadmin, org_id, owner_id, role="owner")
        _add_member(superadmin, org_id, member_id, role="member")

        response = owner.get(
            f"/api/v1/tenancy/organizations/{org_id}/user-lookup"
            "?identifier=lookupinside"
        )
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "already_member"
        assert body["userId"] == member_id

    def test_missing_identifier_is_400(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        owner, owner_id = _new_user(app, "lookupblank")
        _add_member(superadmin, org_id, owner_id, role="owner")

        response = owner.get(f"/api/v1/tenancy/organizations/{org_id}/user-lookup")
        assert response.status_code == 400
        assert "identifier" in response.get_json()["message"]

    def test_plain_member_cannot_lookup(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        plain, plain_id = _new_user(app, "lookupplain")
        _add_member(superadmin, org_id, plain_id, role="member")

        response = plain.get(
            f"/api/v1/tenancy/organizations/{org_id}/user-lookup"
            "?identifier=anything"
        )
        assert response.status_code == 403

    def test_anonymous_401(self, client):
        response = client.get(
            "/api/v1/tenancy/organizations/any/user-lookup?identifier=x"
        )
        assert response.status_code == 401


class TestSelfServiceOrganization:
    """POST /my-organizations — the onboarding path (creator is enrolled)."""

    def test_creator_becomes_owner_member(self, member):
        response = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Solo Org", "slug": "solo-org"},
        )
        assert response.status_code == 201, response.get_json()
        body = response.get_json()
        assert body["slug"] == "solo-org"
        assert body["myRole"] == "owner"
        assert body["memberCount"] == 1
        assert body["subscription"]["tier"] == "community"

        mine = member.get("/api/v1/tenancy/my-organizations").get_json()
        assert [item["id"] for item in mine["items"]] == [body["id"]]
        assert mine["items"][0]["myRole"] == "owner"

    def test_creator_can_use_owner_endpoints_immediately(self, member):
        org_id = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Instant Org", "slug": "instant-org"},
        ).get_json()["id"]

        listed = member.get(f"/api/v1/tenancy/organizations/{org_id}/members")
        assert listed.status_code == 200
        items = listed.get_json()["items"]
        assert len(items) == 1
        assert items[0]["role"] == "owner"

    def test_console_path_still_does_not_enroll(self, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        body = superadmin.get(
            f"/api/v1/tenancy/organizations/{org_id}/members"
        ).get_json()
        assert body["items"] == []

    def test_duplicate_slug_conflicts(self, member):
        member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Dupe One", "slug": "dupe-org"},
        )
        response = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Dupe Two", "slug": "dupe-org"},
        )
        assert response.status_code == 409
        assert response.get_json() == {"message": "slug_already_taken"}

    def test_invalid_slug_rejected(self, member):
        response = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Bad", "slug": "Bad Slug!"},
        )
        assert response.status_code == 400
        assert "slug" in response.get_json()["message"]

    def test_requires_login(self, client):
        response = client.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Anon Org", "slug": "anon-org"},
        )
        assert response.status_code == 401

    def test_self_service_hits_the_per_user_quota(self, member):
        from app.tenancy.services import MAX_ORGS_PER_USER

        for i in range(MAX_ORGS_PER_USER):
            response = member.post(
                "/api/v1/tenancy/my-organizations",
                json={"name": f"Quota {i}", "slug": f"quota-{i}"},
            )
            assert response.status_code == 201, response.get_json()

        response = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "One Too Many", "slug": "one-too-many"},
        )
        assert response.status_code == 422
        assert response.get_json() == {"message": "too_many_organizations"}

    def test_console_path_ignores_the_quota(self, superadmin):
        from app.tenancy.services import MAX_ORGS_PER_USER

        for i in range(MAX_ORGS_PER_USER + 1):
            response = _create_org(superadmin, name=f"Console {i}", slug=f"console-{i}")
            assert response.status_code == 201, response.get_json()

    def test_created_by_is_recorded(self, app, member):
        from app.tenancy.models import Organization
        from framework.extensions import db

        user_id = member.get("/api/v1/auth/me").get_json()["id"]
        org_id = member.post(
            "/api/v1/tenancy/my-organizations",
            json={"name": "Traced Org", "slug": "traced-org"},
        ).get_json()["id"]

        with app.app_context():
            assert db.session.get(Organization, org_id).created_by == user_id


class TestInviteCodes:
    """Owner-generated codes — the self-service way into an organization."""

    @staticmethod
    def _owner_org(app, superadmin, username="codeowner"):
        org_id = _create_org(
            superadmin, name=username.title(), slug=username
        ).get_json()["id"]
        owner, owner_id = _new_user(app, username)
        _add_member(superadmin, org_id, owner_id, role="owner")
        return owner, org_id

    def test_owner_generates_lists_and_revokes(self, app, superadmin):
        owner, org_id = self._owner_org(app, superadmin)

        created = owner.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes",
            json={"role": "member"},
        )
        assert created.status_code == 201, created.get_json()
        body = created.get_json()
        assert len(body["code"]) == 8
        assert body["code"] == body["code"].upper()
        # Unambiguous alphabet — never I/L/O/0/1 to retype.
        assert not set(body["code"]) & set("ILO01")
        assert body["role"] == "member"
        assert body["createdOn"].endswith("+00:00")

        listed = owner.get(f"/api/v1/tenancy/organizations/{org_id}/invite-codes")
        assert listed.status_code == 200
        assert [item["code"] for item in listed.get_json()["items"]] == [body["code"]]

        revoked = owner.delete(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes/{body['id']}"
        )
        assert revoked.status_code == 204
        listed = owner.get(f"/api/v1/tenancy/organizations/{org_id}/invite-codes")
        assert listed.get_json()["items"] == []

    def test_revoked_code_no_longer_redeems(self, app, superadmin):
        owner, org_id = self._owner_org(app, superadmin, "revoker")
        code = owner.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes", json={}
        ).get_json()
        owner.delete(f"/api/v1/tenancy/organizations/{org_id}/invite-codes/{code['id']}")

        joiner, _ = _new_user(app, "revoketarget")
        response = joiner.post(
            "/api/v1/tenancy/invites/redeem", json={"code": code["code"]}
        )
        assert response.status_code == 404
        assert response.get_json() == {"message": "invite_not_found"}

    def test_plain_member_and_outsider_cannot_manage_codes(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        plain, plain_id = _new_user(app, "codeplain")
        outsider, _ = _new_user(app, "codeoutsider")
        _add_member(superadmin, org_id, plain_id, role="member")

        assert plain.get(f"/api/v1/tenancy/organizations/{org_id}/invite-codes").status_code == 403
        assert plain.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes", json={}
        ).status_code == 403
        assert outsider.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes", json={}
        ).status_code == 403
        assert outsider.delete(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes/any"
        ).status_code == 403

    def test_invalid_role_rejected(self, app, superadmin):
        owner, org_id = self._owner_org(app, superadmin, "rolecheck")
        response = owner.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes",
            json={"role": "admin"},
        )
        assert response.status_code == 400
        assert "invalid_role" in response.get_json()["message"]

    def test_code_of_another_org_is_not_found(self, app, superadmin):
        owner_a, org_a = self._owner_org(app, superadmin, "scopone")
        owner_b, org_b = self._owner_org(app, superadmin, "scopwo")
        code_b = owner_b.post(
            f"/api/v1/tenancy/organizations/{org_b}/invite-codes", json={}
        ).get_json()

        response = owner_a.delete(
            f"/api/v1/tenancy/organizations/{org_a}/invite-codes/{code_b['id']}"
        )
        assert response.status_code == 404
        assert response.get_json() == {"message": "invite_not_found"}
        # Untouched in its own organization.
        listed = owner_b.get(f"/api/v1/tenancy/organizations/{org_b}/invite-codes")
        assert listed.get_json()["items"]

    def test_anonymous_is_401(self, client):
        assert client.get("/api/v1/tenancy/organizations/any/invite-codes").status_code == 401
        assert client.post(
            "/api/v1/tenancy/invites/redeem", json={"code": "ABCDEFGH"}
        ).status_code == 401


class TestRedeemInvite:
    """Redeeming is idempotent and never escalates the caller's app_role."""

    @staticmethod
    def _code(app, superadmin, *, role="member", username="redeemowner"):
        org_id = _create_org(
            superadmin, name=username.title(), slug=username
        ).get_json()["id"]
        owner, owner_id = _new_user(app, username)
        _add_member(superadmin, org_id, owner_id, role="owner")
        created = owner.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes", json={"role": role}
        )
        assert created.status_code == 201, created.get_json()
        return org_id, created.get_json()["code"]

    def test_redeem_joins_with_the_codes_role(self, app, superadmin):
        org_id, code = self._code(app, superadmin, role="owner", username="joinowner")
        joiner, _ = _new_user(app, "joininvitee")

        response = joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code})
        assert response.status_code == 201, response.get_json()
        body = response.get_json()
        assert body["organizationId"] == org_id
        assert body["role"] == "owner"
        assert body["alreadyMember"] is False

        mine = joiner.get("/api/v1/tenancy/my-organizations").get_json()
        assert mine["items"][0]["id"] == org_id
        assert mine["items"][0]["myRole"] == "owner"

    def test_second_redeem_is_idempotent(self, app, superadmin):
        org_id, code = self._code(app, superadmin, username="twicejoin")
        joiner, _ = _new_user(app, "twiceinvitee")
        assert (
            joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code}).status_code
            == 201
        )

        again = joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code})
        assert again.status_code == 200
        assert again.get_json()["alreadyMember"] is True
        assert again.get_json()["organizationId"] == org_id

        mine = joiner.get("/api/v1/tenancy/my-organizations").get_json()
        assert len(mine["items"]) == 1

    def test_existing_member_reports_their_own_role(self, app, superadmin):
        org_id, code = self._code(app, superadmin, username="prememberorg")
        joiner, joiner_id = _new_user(app, "prememberuser")
        _add_member(superadmin, org_id, joiner_id, role="owner")

        response = joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code})
        assert response.status_code == 200
        body = response.get_json()
        assert body["alreadyMember"] is True
        assert body["role"] == "owner"

    def test_lowercase_code_is_normalized(self, app, superadmin):
        _, code = self._code(app, superadmin, username="lowerorg")
        joiner, _ = _new_user(app, "lowerjoiner")

        response = joiner.post(
            "/api/v1/tenancy/invites/redeem", json={"code": code.lower()}
        )
        assert response.status_code == 201

    def test_unknown_code_is_not_found(self, member):
        response = member.post(
            "/api/v1/tenancy/invites/redeem", json={"code": "ZZZZZZZZ"}
        )
        assert response.status_code == 404
        assert response.get_json() == {"message": "invite_not_found"}

    def test_missing_or_blank_code_is_400(self, member):
        assert member.post("/api/v1/tenancy/invites/redeem", json={}).status_code == 400
        response = member.post(
            "/api/v1/tenancy/invites/redeem", json={"code": "   "}
        )
        assert response.status_code == 400
        assert "code" in response.get_json()["message"]

    def test_code_of_a_deactivated_org_is_not_found(self, superadmin, member):
        org_id = _create_org(superadmin).get_json()["id"]
        code = superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes", json={}
        ).get_json()["code"]
        superadmin.patch(
            f"/api/v1/tenancy/organizations/{org_id}", json={"isActive": False}
        )

        response = member.post("/api/v1/tenancy/invites/redeem", json={"code": code})
        assert response.status_code == 404
        assert response.get_json() == {"message": "invite_not_found"}

    def test_redeem_never_touches_app_role(self, app, superadmin):
        from app.auth.models import User
        from framework.extensions import db

        org_id, code = self._code(app, superadmin, role="owner", username="keeproleorg")
        joiner, joiner_id = _new_user(app, "keeprolejoiner")
        assert (
            joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code}).status_code
            == 201
        )

        with app.app_context():
            assert db.session.get(User, joiner_id).app_role == "user"


class TestMembersQuota:
    """One app-wide member quota (superadmin setting, 0 = no limit).

    Enforced on both membership-creating paths: the add-member endpoint and
    invite redemption. Creating an organization itself is never blocked —
    it always enrolls exactly one owner and the minimum quota is 0=unlimited.
    """

    @staticmethod
    def _set_limit(superadmin, value):
        response = superadmin.put(
            "/api/v1/tenancy/settings", json={"membersLimit": value}
        )
        assert response.status_code == 200, response.get_json()
        return response.get_json()

    def test_settings_require_superadmin(self, client, member, admin, superadmin):
        assert client.get("/api/v1/tenancy/settings").status_code == 401
        assert member.get("/api/v1/tenancy/settings").status_code == 403
        assert admin.get("/api/v1/tenancy/settings").status_code == 403
        assert (
            member.put("/api/v1/tenancy/settings", json={"membersLimit": 1}).status_code
            == 403
        )

        # No row yet: the default is "no limit".
        assert superadmin.get("/api/v1/tenancy/settings").get_json() == {
            "membersLimit": 0
        }
        assert self._set_limit(superadmin, 5) == {"membersLimit": 5}
        assert superadmin.get("/api/v1/tenancy/settings").get_json() == {
            "membersLimit": 5
        }

    def test_settings_reject_invalid_values(self, superadmin):
        assert superadmin.put("/api/v1/tenancy/settings", json={}).status_code == 400
        negative = superadmin.put(
            "/api/v1/tenancy/settings", json={"membersLimit": -1}
        )
        assert negative.status_code == 400
        assert "members_limit" in negative.get_json()["message"]
        broken = superadmin.put(
            "/api/v1/tenancy/settings", json={"membersLimit": "many"}
        )
        assert broken.status_code == 400

    def test_default_limit_does_not_block_members(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        _, first = _new_user(app, "quota_unl_a")
        _, second = _new_user(app, "quota_unl_b")

        _add_member(superadmin, org_id, first)
        _add_member(superadmin, org_id, second)

        listed = superadmin.get(f"/api/v1/tenancy/organizations/{org_id}/members")
        assert len(listed.get_json()["items"]) == 2

    def test_add_member_blocked_at_limit(self, app, superadmin):
        org_id = _create_org(superadmin).get_json()["id"]
        _, first = _new_user(app, "quota_first")
        _, second = _new_user(app, "quota_second")
        self._set_limit(superadmin, 1)

        # Exactly at the limit — the last seat is still granted.
        _add_member(superadmin, org_id, first)
        denied = superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/members",
            json={"userId": second},
        )
        assert denied.status_code == 422
        assert denied.get_json() == {"message": "member_limit_reached"}

        # Raising the limit reopens the door without a restart.
        self._set_limit(superadmin, 2)
        assert (
            superadmin.post(
                f"/api/v1/tenancy/organizations/{org_id}/members",
                json={"userId": second},
            ).status_code
            == 201
        )

    def test_quota_is_per_organization(self, app, superadmin):
        self._set_limit(superadmin, 1)
        org_a = _create_org(superadmin, name="Quota A", slug="quota-a").get_json()["id"]
        org_b = _create_org(superadmin, name="Quota B", slug="quota-b").get_json()["id"]
        _, user_a = _new_user(app, "quota_per_a")
        _, user_b = _new_user(app, "quota_per_b")

        _add_member(superadmin, org_a, user_a)
        # Org A is full — org B still has its own empty seat.
        denied = superadmin.post(
            f"/api/v1/tenancy/organizations/{org_a}/members", json={"userId": user_b}
        )
        assert denied.status_code == 422
        assert (
            superadmin.post(
                f"/api/v1/tenancy/organizations/{org_b}/members",
                json={"userId": user_b},
            ).status_code
            == 201
        )

    def test_redeem_blocked_at_limit_then_recovered(self, app, superadmin):
        org_id = _create_org(superadmin, name="Quota Org", slug="quota-org").get_json()[
            "id"
        ]
        owner, owner_id = _new_user(app, "quota_owner")
        _add_member(superadmin, org_id, owner_id, role="owner")
        code = superadmin.post(
            f"/api/v1/tenancy/organizations/{org_id}/invite-codes",
            json={"role": "member"},
        ).get_json()["code"]

        self._set_limit(superadmin, 1)  # the owner already holds the only seat
        joiner, _ = _new_user(app, "quota_joiner")
        denied = joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code})
        assert denied.status_code == 422
        assert denied.get_json() == {"message": "member_limit_reached"}

        self._set_limit(superadmin, 2)
        joined = joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code})
        assert joined.status_code == 201
        assert joined.get_json()["alreadyMember"] is False

        # A repeat redemption stays idempotent even at a now-full quota.
        again = joiner.post("/api/v1/tenancy/invites/redeem", json={"code": code})
        assert again.status_code == 200
        assert again.get_json()["alreadyMember"] is True


class TestPlanCatalog:
    def test_catalog_requires_auth(self, client):
        assert client.get("/api/v1/plans/catalog").status_code == 401

    def test_catalog_returns_all_plans(self, superadmin, member):
        inactive = superadmin.post(
            "/api/v1/plans",
            json={
                "name": "Hidden",
                "tier": "professional",
                "price": 250000,
                "durationValue": 1,
                "durationUnit": "months",
                "isActive": False,
            },
        ).get_json()
        response = member.get("/api/v1/plans/catalog")
        assert response.status_code == 200
        names = [p["name"] for p in response.get_json()["items"]]
        assert "Community" in names
        assert "Professional" in names
        assert "Hidden" in names
        hidden = next(p for p in response.get_json()["items"] if p["name"] == "Hidden")
        assert hidden["isActive"] is False
        assert inactive["id"] == hidden["id"]


