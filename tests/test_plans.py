"""Tests for the plan catalog — superadmin CRUD and subscription wiring."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from conftest import default_plan_id

from app.plans.services import PlanService
from framework.exceptions import Conflict


def _create_org(client, name="Acme", slug="acme"):
    response = client.post(
        "/api/v1/tenancy/organizations", json={"name": name, "slug": slug}
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def _plans(client, **params):
    return client.get("/api/v1/plans", query_string=params).get_json()["items"]


def _create_plan(client, **overrides):
    payload = {
        "name": "Custom",
        "tier": "professional",
        "durationValue": 1,
        "durationUnit": "months",
        **overrides,
    }
    return client.post("/api/v1/plans", json=payload)


class TestSeededDefaults:
    def test_one_default_per_tier(self, superadmin):
        items = _plans(superadmin)
        by_tier = {plan["tier"]: plan for plan in items}
        assert set(by_tier) == {"community", "professional"}

        community = by_tier["community"]
        assert community["name"] == "Community"
        assert community["price"] == 0
        assert community["isDefault"] is True
        assert community["durationValue"] == 1
        assert community["durationUnit"] == "months"
        assert community["features"] == {}

        professional = by_tier["professional"]
        assert professional["name"] == "Professional"
        assert professional["price"] == 500_000
        assert professional["isDefault"] is True
        assert professional["features"] == {
            "advanced_reporting": True,
            "priority_support": True,
            "custom_domain": True,
        }
        assert "todos" not in professional["features"]

    def test_tier_filter(self, superadmin):
        items = _plans(superadmin, tier="professional")
        assert [plan["tier"] for plan in items] == ["professional"]

        assert superadmin.get("/api/v1/plans?tier=enterprise").status_code == 400

    def test_feature_registry_endpoint(self, superadmin):
        body = superadmin.get("/api/v1/plans/features").get_json()
        assert body == {
            "features": [
                "advanced_reporting",
                "priority_support",
                "custom_domain",
                "todos",
            ]
        }


class TestListing:
    def test_paged_envelope(self, superadmin):
        for name in ("Alpha", "Beta", "Gamma"):
            assert _create_plan(superadmin, name=name).status_code == 201

        first = superadmin.get(
            "/api/v1/plans", query_string={"page": 1, "per_page": 2}
        ).get_json()
        assert first["total"] == 5
        assert first["page"] == 1
        assert first["perPage"] == 2
        assert len(first["items"]) == 2

        last = superadmin.get(
            "/api/v1/plans", query_string={"page": 3, "per_page": 2}
        ).get_json()
        assert len(last["items"]) == 1

    def test_search_matches_name_case_insensitively(self, superadmin):
        _create_plan(superadmin, name="Enterprise Plus")
        _create_plan(superadmin, name="Starter")

        items = _plans(superadmin, search="enterprise")
        assert [plan["name"] for plan in items] == ["Enterprise Plus"]

    def test_search_combines_with_tier(self, superadmin):
        _create_plan(superadmin, name="Professional Lite", tier="community", price=0)
        _create_plan(superadmin, name="Professional Max")

        items = _plans(superadmin, search="professional", tier="professional")
        assert {plan["name"] for plan in items} == {"Professional", "Professional Max"}

    def test_invalid_page_rejected(self, superadmin):
        assert superadmin.get("/api/v1/plans?page=0").status_code == 400


class TestFeatures:
    def test_create_with_features(self, superadmin):
        response = _create_plan(
            superadmin,
            name="Reporting",
            features={"advanced_reporting": True, "custom_domain": False},
        )
        assert response.status_code == 201, response.get_json()
        assert response.get_json()["features"] == {
            "advanced_reporting": True,
            "custom_domain": False,
        }

    def test_unknown_feature_rejected(self, superadmin):
        response = _create_plan(
            superadmin, name="Bogus", features={"teleportation": True}
        )
        assert response.status_code == 400
        assert response.get_json() == {"message": "features_unknown_feature"}

    def test_null_features_rejected(self, superadmin):
        plan = _create_plan(superadmin, name="Nullish").get_json()
        response = superadmin.put(
            f"/api/v1/plans/{plan['id']}", json={"features": None}
        )
        assert response.status_code == 400
        assert response.get_json() == {"message": "features_must_be_an_object"}

    def test_update_replaces_features(self, superadmin):
        plan = _create_plan(
            superadmin, name="Toggle", features={"priority_support": True}
        ).get_json()
        response = superadmin.put(
            f"/api/v1/plans/{plan['id']}",
            json={"features": {"custom_domain": True}},
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json()["features"] == {"custom_domain": True}

    def test_member_cannot_read_registry(self, member):
        assert member.get("/api/v1/plans/features").status_code == 403


class TestGuards:
    def test_anonymous_401(self, client):
        assert client.get("/api/v1/plans").status_code == 401
        assert client.post("/api/v1/plans", json={}).status_code == 401

    def test_member_and_admin_forbidden(self, member, admin):
        for caller in (member, admin):
            assert caller.get("/api/v1/plans").status_code == 403
            assert caller.post(
                "/api/v1/plans",
                json={
                    "name": "Nope",
                    "tier": "professional",
                    "durationValue": 1,
                    "durationUnit": "months",
                },
            ).status_code == 403
            assert caller.put("/api/v1/plans/any", json={"price": 1}).status_code == 403
            assert caller.delete("/api/v1/plans/any").status_code == 403


class TestCreate:
    def test_professional_price_is_optional(self, superadmin):
        response = _create_plan(superadmin, name="Enterprise")
        assert response.status_code == 201, response.get_json()
        body = response.get_json()
        assert body["tier"] == "professional"
        assert "price" not in body
        assert body["isDefault"] is False
        assert body["isActive"] is True
        assert body["createdOn"].endswith("+00:00")

    def test_community_requires_a_price(self, superadmin):
        response = _create_plan(superadmin, name="Freebie", tier="community")
        assert response.status_code == 400
        assert response.get_json() == {"message": "community_requires_price"}

        free = _create_plan(superadmin, name="Freebie", tier="community", price=0)
        assert free.status_code == 201, free.get_json()
        assert free.get_json()["price"] == 0

    def test_duplicate_name_conflicts(self, superadmin):
        assert _create_plan(superadmin, name="Custom").status_code == 201
        duplicate = _create_plan(superadmin, name="Custom")
        assert duplicate.status_code == 409
        assert duplicate.get_json() == {"message": "plan_name_taken"}

    def test_new_default_replaces_the_old_one(self, superadmin):
        old_id = default_plan_id(superadmin, "professional")
        created = _create_plan(
            superadmin, name="Pro Annual", isDefault=True, durationValue=12
        )
        assert created.status_code == 201, created.get_json()
        new_id = created.get_json()["id"]

        items = {plan["id"]: plan for plan in _plans(superadmin, tier="professional")}
        assert items[new_id]["isDefault"] is True
        assert items[old_id]["isDefault"] is False
        assert default_plan_id(superadmin, "professional") == new_id

    def test_default_must_be_active(self, superadmin):
        response = _create_plan(superadmin, name="Zombie", isDefault=True, isActive=False)
        assert response.status_code == 400
        assert response.get_json() == {"message": "default_plan_must_be_active"}

    def test_invalid_tier_and_unit(self, superadmin):
        assert _create_plan(superadmin, name="A", tier="enterprise").status_code == 400
        assert _create_plan(superadmin, name="B", durationUnit="weeks").status_code == 400
        assert _create_plan(superadmin, name="C", durationValue=0).status_code == 400
        assert _create_plan(superadmin, name="D", durationValue=3651).status_code == 400
        assert _create_plan(superadmin, name="  ").status_code == 400

    def test_day_duration(self, superadmin):
        response = _create_plan(
            superadmin, name="Short Trial", durationValue=14, durationUnit="days"
        )
        assert response.status_code == 201, response.get_json()
        assert response.get_json()["durationValue"] == 14
        assert response.get_json()["durationUnit"] == "days"


class TestUpdate:
    def test_update_price_and_duration(self, superadmin):
        plan_id = default_plan_id(superadmin, "professional")
        response = superadmin.put(
            f"/api/v1/plans/{plan_id}",
            json={"price": 750_000, "durationValue": 3, "durationUnit": "months"},
        )
        assert response.status_code == 200, response.get_json()
        body = response.get_json()
        assert body["price"] == 750_000
        assert body["durationValue"] == 3
        assert body["durationUnit"] == "months"

    def test_professional_price_can_be_cleared(self, superadmin):
        plan_id = default_plan_id(superadmin, "professional")
        response = superadmin.put(f"/api/v1/plans/{plan_id}", json={"price": None})
        assert response.status_code == 200, response.get_json()
        assert "price" not in response.get_json()

    def test_community_price_cannot_be_cleared(self, superadmin):
        plan_id = default_plan_id(superadmin, "community")
        response = superadmin.put(f"/api/v1/plans/{plan_id}", json={"price": None})
        assert response.status_code == 400
        assert response.get_json() == {"message": "community_requires_price"}

    def test_default_cannot_be_deactivated(self, superadmin):
        plan_id = default_plan_id(superadmin, "professional")
        response = superadmin.put(f"/api/v1/plans/{plan_id}", json={"isActive": False})
        assert response.status_code == 400
        assert response.get_json() == {"message": "default_plan_must_be_active"}

    def test_default_cannot_be_unset(self, superadmin):
        plan_id = default_plan_id(superadmin, "professional")
        response = superadmin.put(f"/api/v1/plans/{plan_id}", json={"isDefault": False})
        assert response.status_code == 422
        assert response.get_json() == {"message": "default_plan_required"}

    def test_empty_update_is_rejected(self, superadmin):
        plan_id = default_plan_id(superadmin, "professional")
        response = superadmin.put(f"/api/v1/plans/{plan_id}", json={})
        assert response.status_code == 400
        assert "no_fields_to_update" in response.get_json()["message"]

    def test_rename_conflicts(self, superadmin):
        assert _create_plan(superadmin, name="Custom").status_code == 201
        plan_id = default_plan_id(superadmin, "professional")
        response = superadmin.put(
            f"/api/v1/plans/{plan_id}", json={"name": "Custom"}
        )
        assert response.status_code == 409
        assert response.get_json() == {"message": "plan_name_taken"}

    def test_tier_change_locked_when_referenced(self, superadmin):
        plan = _create_plan(superadmin, name="Referenced").get_json()
        org_id = _create_org(superadmin)
        assigned = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": plan["id"]},
        )
        assert assigned.status_code == 200, assigned.get_json()

        response = superadmin.put(
            f"/api/v1/plans/{plan['id']}", json={"tier": "community", "price": 0}
        )
        assert response.status_code == 422
        assert response.get_json() == {"message": "plan_tier_locked"}

    def test_tier_change_locked_for_default(self, superadmin):
        plan_id = default_plan_id(superadmin, "professional")
        response = superadmin.put(
            f"/api/v1/plans/{plan_id}", json={"tier": "community", "price": 0}
        )
        assert response.status_code == 422
        assert response.get_json() == {"message": "plan_tier_locked"}

    def test_unused_tier_change_is_allowed(self, superadmin):
        plan = _create_plan(
            superadmin, name="Movable", tier="community", price=0
        ).get_json()
        response = superadmin.put(
            f"/api/v1/plans/{plan['id']}", json={"tier": "professional"}
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json()["tier"] == "professional"

    def test_unknown_plan_404(self, superadmin):
        response = superadmin.put("/api/v1/plans/no-such", json={"price": 1})
        assert response.status_code == 404
        assert response.get_json() == {"message": "plan_not_found"}


class TestDelete:
    def test_default_cannot_be_deleted(self, superadmin):
        plan_id = default_plan_id(superadmin, "professional")
        response = superadmin.delete(f"/api/v1/plans/{plan_id}")
        assert response.status_code == 422
        assert response.get_json() == {"message": "default_plan_cannot_be_deleted"}

    def test_plan_in_use_cannot_be_deleted(self, superadmin):
        plan = _create_plan(superadmin, name="In Use").get_json()
        org_id = _create_org(superadmin)
        superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": plan["id"]},
        )

        response = superadmin.delete(f"/api/v1/plans/{plan['id']}")
        assert response.status_code == 422
        assert response.get_json() == {"message": "plan_in_use"}

    def test_delete_race_maps_to_in_use(self, superadmin, monkeypatch):
        plan = _create_plan(superadmin, name="Race").get_json()

        def fail(self):
            raise Conflict("integrity_error")

        monkeypatch.setattr(PlanService, "_commit", fail)
        response = superadmin.delete(f"/api/v1/plans/{plan['id']}")
        assert response.status_code == 422
        assert response.get_json() == {"message": "plan_in_use"}

    def test_unused_plan_is_deleted(self, superadmin):
        plan = _create_plan(superadmin, name="Disposable").get_json()
        response = superadmin.delete(f"/api/v1/plans/{plan['id']}")
        assert response.status_code == 204
        assert plan["id"] not in {item["id"] for item in _plans(superadmin)}

    def test_unknown_plan_404(self, superadmin):
        response = superadmin.delete("/api/v1/plans/no-such")
        assert response.status_code == 404
        assert response.get_json() == {"message": "plan_not_found"}


class TestSubscriptionWiring:
    @staticmethod
    def _subscription(client, org_id):
        body = client.get(
            f"/api/v1/tenancy/organizations/{org_id}"
        ).get_json()
        return body["subscription"]

    def test_new_org_reports_its_plan(self, superadmin):
        org_id = _create_org(superadmin)
        sub = self._subscription(superadmin, org_id)
        assert sub["planId"] == default_plan_id(superadmin, "community")
        assert sub["planName"] == "Community"
        assert sub["tier"] == "community"

    def test_assignment_uses_the_plan_duration(self, superadmin):
        plan = _create_plan(
            superadmin, name="Quarterly", durationValue=90, durationUnit="days"
        ).get_json()
        org_id = _create_org(superadmin)
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": plan["id"]},
        )
        assert response.status_code == 200, response.get_json()
        body = response.get_json()
        assert body["planId"] == plan["id"]
        assert body["planName"] == "Quarterly"
        delta = datetime.fromisoformat(body["expiresOn"]) - datetime.now(UTC)
        assert timedelta(days=89) < delta <= timedelta(days=90)

    def test_inactive_plan_cannot_be_assigned(self, superadmin):
        plan = _create_plan(superadmin, name="Retired", isActive=False).get_json()
        org_id = _create_org(superadmin)
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": plan["id"]},
        )
        assert response.status_code == 422
        assert response.get_json() == {"message": "plan_inactive"}

    def test_unknown_plan_cannot_be_assigned(self, superadmin):
        org_id = _create_org(superadmin)
        response = superadmin.put(
            f"/api/v1/tenancy/organizations/{org_id}/subscription",
            json={"planId": "no-such"},
        )
        assert response.status_code == 404
        assert response.get_json() == {"message": "plan_not_found"}
