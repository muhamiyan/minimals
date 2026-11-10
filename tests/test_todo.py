"""Tests for organization-shared todo — CRUD, filters, and feature gating."""
from __future__ import annotations

from conftest import csrf_client


def _user_id(client) -> str:
    return client.get("/api/v1/auth/me").get_json()["id"]


def _create_org(client, name="Acme", slug="acme") -> str:
    response = client.post(
        "/api/v1/tenancy/organizations", json={"name": name, "slug": slug}
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def _todo_plan(client, name="ToDo Pro") -> str:
    response = client.post(
        "/api/v1/plans",
        json={
            "name": name,
            "tier": "professional",
            "durationValue": 1,
            "durationUnit": "months",
            "features": {"todo": True},
        },
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["id"]


def _assign_plan(client, org_id: str, plan_id: str) -> None:
    response = client.put(
        f"/api/v1/tenancy/organizations/{org_id}/subscription",
        json={"planId": plan_id},
    )
    assert response.status_code == 200, response.get_json()


def _org_with_todo(client, *, name="Acme", slug="acme", plan_name="ToDo Pro") -> str:
    org_id = _create_org(client, name=name, slug=slug)
    _assign_plan(client, org_id, _todo_plan(client, plan_name))
    return org_id


def _new_user(app, username: str):
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


def _add_member(superadmin, org_id: str, user_id: str, role="member") -> None:
    response = superadmin.post(
        f"/api/v1/tenancy/organizations/{org_id}/members",
        json={"userId": user_id, "role": role},
    )
    assert response.status_code == 201, response.get_json()


def _create_todo(client, org_id: str, **payload):
    return client.post(
        f"/api/v1/todo/organizations/{org_id}",
        json={"title": "Task", **payload},
    )


def _list(client, org_id: str, **params):
    return client.get(
        f"/api/v1/todo/organizations/{org_id}", query_string=params
    ).get_json()


class TestGuards:
    def test_anonymous_401(self, client):
        assert client.get("/api/v1/todo/organizations/x").status_code == 401
        assert client.post("/api/v1/todo/organizations/x", json={}).status_code == 401
        assert client.put("/api/v1/todo/organizations/x/y", json={}).status_code == 401
        assert client.delete("/api/v1/todo/organizations/x/y").status_code == 401

    def test_feature_off_for_community_org(self, superadmin, member, app):
        org_id = _create_org(superadmin)
        _add_member(superadmin, org_id, _user_id(member))

        for caller in (superadmin, member):
            response = caller.get(f"/api/v1/todo/organizations/{org_id}")
            assert response.status_code == 403
            assert response.get_json() == {"message": "feature_not_enabled"}

        created = _create_todo(member, org_id)
        assert created.status_code == 403
        assert created.get_json() == {"message": "feature_not_enabled"}

    def test_non_member_forbidden(self, superadmin, member):
        org_id = _org_with_todo(superadmin)
        response = member.get(f"/api/v1/todo/organizations/{org_id}")
        assert response.status_code == 403
        assert response.get_json() == {"message": "forbidden"}

    def test_unknown_org_404(self, superadmin):
        response = superadmin.get("/api/v1/todo/organizations/no-such")
        assert response.status_code == 404
        assert response.get_json() == {"message": "organization_not_found"}


class TestCrud:
    def test_create_returns_full_todo(self, superadmin):
        org_id = _org_with_todo(superadmin)
        response = _create_todo(
            superadmin,
            org_id,
            title="  Ship release  ",
            description="  Cut the tag  ",
            completed=True,
            dueDate="2026-12-31",
        )
        assert response.status_code == 201, response.get_json()
        body = response.get_json()
        assert body["title"] == "Ship release"
        assert body["description"] == "Cut the tag"
        assert body["completed"] is True
        assert body["dueDate"] == "2026-12-31"
        assert body["createdBy"] == _user_id(superadmin)
        assert body["createdOn"].endswith("+00:00")
        assert body["changedOn"].endswith("+00:00")

    def test_blank_description_is_omitted(self, superadmin):
        org_id = _org_with_todo(superadmin)
        body = _create_todo(superadmin, org_id, description="   ").get_json()
        assert "description" not in body
        assert body["completed"] is False
        assert "dueDate" not in body

    def test_update_is_partial(self, superadmin):
        org_id = _org_with_todo(superadmin)
        todo_id = _create_todo(superadmin, org_id, title="Draft").get_json()["id"]

        response = superadmin.put(
            f"/api/v1/todo/organizations/{org_id}/{todo_id}",
            json={"completed": True},
        )
        assert response.status_code == 200, response.get_json()
        body = response.get_json()
        assert body["completed"] is True
        assert body["title"] == "Draft"

    def test_update_clears_description_and_due_date(self, superadmin):
        org_id = _org_with_todo(superadmin)
        created = _create_todo(
            superadmin, org_id, description="Note", dueDate="2026-01-01"
        ).get_json()

        response = superadmin.put(
            f"/api/v1/todo/organizations/{org_id}/{created['id']}",
            json={"description": None, "dueDate": None},
        )
        assert response.status_code == 200, response.get_json()
        body = response.get_json()
        assert "description" not in body
        assert "dueDate" not in body

    def test_delete_removes_the_todo(self, superadmin):
        org_id = _org_with_todo(superadmin)
        todo_id = _create_todo(superadmin, org_id).get_json()["id"]

        response = superadmin.delete(f"/api/v1/todo/organizations/{org_id}/{todo_id}")
        assert response.status_code == 204
        assert _list(superadmin, org_id)["total"] == 0

        missing = superadmin.put(
            f"/api/v1/todo/organizations/{org_id}/{todo_id}",
            json={"completed": True},
        )
        assert missing.status_code == 404
        assert missing.get_json() == {"message": "todo_not_found"}

    def test_members_share_one_list(self, superadmin, app):
        org_id = _org_with_todo(superadmin)
        member, member_id = _new_user(app, "worker")
        _add_member(superadmin, org_id, member_id)

        created = _create_todo(member, org_id, title="From member")
        assert created.status_code == 201, created.get_json()
        assert created.get_json()["createdBy"] == member_id

        superadmin_created = _create_todo(superadmin, org_id, title="From admin")
        assert superadmin_created.status_code == 201

        titles = {item["title"] for item in _list(superadmin, org_id)["items"]}
        assert titles == {"From member", "From admin"}

        todo_id = created.get_json()["id"]
        updated = superadmin.put(
            f"/api/v1/todo/organizations/{org_id}/{todo_id}",
            json={"completed": True},
        )
        assert updated.status_code == 200
        assert updated.get_json()["completed"] is True

    def test_member_can_delete_another_members_todo(self, superadmin, app):
        org_id = _org_with_todo(superadmin)
        member, member_id = _new_user(app, "worker")
        _add_member(superadmin, org_id, member_id)
        todo_id = _create_todo(superadmin, org_id, title="Owned by superadmin").get_json()["id"]

        response = member.delete(f"/api/v1/todo/organizations/{org_id}/{todo_id}")
        assert response.status_code == 204
        assert _list(superadmin, org_id)["total"] == 0


class TestValidation:
    def test_title_is_required(self, superadmin):
        org_id = _org_with_todo(superadmin)

        missing = superadmin.post(f"/api/v1/todo/organizations/{org_id}", json={})
        assert missing.status_code == 400
        assert missing.get_json() == {"message": "title_required"}

        blank = _create_todo(superadmin, org_id, title="   ")
        assert blank.status_code == 400
        assert blank.get_json() == {"message": "title_required"}

    def test_update_rejects_null_title_and_completed(self, superadmin):
        org_id = _org_with_todo(superadmin)
        todo_id = _create_todo(superadmin, org_id).get_json()["id"]
        url = f"/api/v1/todo/organizations/{org_id}/{todo_id}"

        null_title = superadmin.put(url, json={"title": None})
        assert null_title.status_code == 400
        assert null_title.get_json() == {"message": "title_required"}

        null_completed = superadmin.put(url, json={"completed": None})
        assert null_completed.status_code == 400
        assert null_completed.get_json() == {"message": "completed_required"}

    def test_empty_update_rejected(self, superadmin):
        org_id = _org_with_todo(superadmin)
        todo_id = _create_todo(superadmin, org_id).get_json()["id"]
        url = f"/api/v1/todo/organizations/{org_id}/{todo_id}"

        empty = superadmin.put(url, json={})
        assert empty.status_code == 400
        assert empty.get_json() == {"message": "value_no_fields_to_update"}

        unknown_only = superadmin.put(url, json={"bogus": 1})
        assert unknown_only.status_code == 400
        assert unknown_only.get_json() == {"message": "value_no_fields_to_update"}

    def test_invalid_due_date_rejected(self, superadmin):
        org_id = _org_with_todo(superadmin)
        response = _create_todo(superadmin, org_id, dueDate="31-12-2026")
        assert response.status_code == 400
        assert response.get_json() == {"message": "due_date_invalid_date"}


class TestListing:
    def test_pagination_envelope(self, superadmin):
        org_id = _org_with_todo(superadmin)
        for index in range(3):
            assert _create_todo(superadmin, org_id, title=f"Task {index}").status_code == 201

        first = _list(superadmin, org_id, page=1, per_page=2)
        assert first["total"] == 3
        assert first["page"] == 1
        assert first["perPage"] == 2
        assert len(first["items"]) == 2

        last = _list(superadmin, org_id, page=2, per_page=2)
        assert len(last["items"]) == 1

    def test_search_matches_title(self, superadmin):
        org_id = _org_with_todo(superadmin)
        _create_todo(superadmin, org_id, title="Buy milk")
        _create_todo(superadmin, org_id, title="Write report")

        items = _list(superadmin, org_id, search="MILK")["items"]
        assert [item["title"] for item in items] == ["Buy milk"]

    def test_completed_filter(self, superadmin):
        org_id = _org_with_todo(superadmin)
        _create_todo(superadmin, org_id, title="Open task")
        _create_todo(superadmin, org_id, title="Done task", completed=True)

        done = _list(superadmin, org_id, completed="true")
        assert {item["title"] for item in done["items"]} == {"Done task"}

        open_items = _list(superadmin, org_id, completed="false")
        assert {item["title"] for item in open_items["items"]} == {"Open task"}

    def test_invalid_page_rejected(self, superadmin):
        org_id = _org_with_todo(superadmin)
        response = superadmin.get(f"/api/v1/todo/organizations/{org_id}?page=0")
        assert response.status_code == 400


class TestIsolation:
    def test_todo_is_scoped_to_its_org(self, superadmin):
        org_a = _org_with_todo(superadmin, name="Alpha", slug="alpha", plan_name="Pro A")
        org_b = _org_with_todo(superadmin, name="Beta", slug="beta", plan_name="Pro B")
        todo_id = _create_todo(superadmin, org_a, title="Alpha only").get_json()["id"]

        assert _list(superadmin, org_b)["total"] == 0

        update = superadmin.put(
            f"/api/v1/todo/organizations/{org_b}/{todo_id}",
            json={"completed": True},
        )
        assert update.status_code == 404
        assert update.get_json() == {"message": "todo_not_found"}

        delete = superadmin.delete(
            f"/api/v1/todo/organizations/{org_b}/{todo_id}"
        )
        assert delete.status_code == 404
        assert _list(superadmin, org_a)["total"] == 1
