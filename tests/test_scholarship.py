

def create_scholarship(admin, **overrides):
    payload = {
        "title": "Beasiswa Selaparang",
        "level": "UM",
        "body": "<p>Lembaga pendidikan dasar</p>",
        **overrides,
    }
    return admin.post("/api/v1/scholarship/scholarships", json=payload)


def test_list_scholarships_is_public_and_ordered(client, admin):
    create_scholarship(
        admin, slug="second", title="SMA NW", level="S1", order=2, status="published"
    )
    create_scholarship(
        admin, slug="first", title="MI NW", level="UM", order=1, status="published"
    )

    body = client.get("/api/v1/scholarship/scholarships").get_json()

    assert set(body) == {"items", "total", "page", "perPage"}
    assert [item["slug"] for item in body["items"]] == ["first", "second"]


def test_create_requires_admin(client, member, admin):
    payload = {"title": "T", "body": "B"}
    assert client.post("/api/v1/scholarship/scholarships", json=payload).status_code == 401
    assert member.post("/api/v1/scholarship/scholarships", json=payload).status_code == 403

    created = create_scholarship(admin, slug="mi-nw")
    assert created.status_code == 201
    assert created.get_json()["level"] == "UM"
    assert created.get_json()["order"] == 0


def test_duplicate_slug_is_conflict(admin):
    create_scholarship(admin, slug="dupe")
    response = create_scholarship(admin, title="Other", slug="dupe")

    assert response.status_code == 409
    assert response.get_json() == {"message": "slug_taken"}


def test_draft_hidden_publicly_and_published_visible(admin, client):
    create_scholarship(admin, slug="draft-scholarship")

    assert client.get("/api/v1/scholarship/scholarships").get_json()["total"] == 0
    assert client.get("/api/v1/scholarship/scholarships/draft-scholarship").status_code == 404
    assert admin.get("/api/v1/scholarship/scholarships/draft-scholarship").status_code == 200

    create_scholarship(admin, slug="public-scholarship", status="published")
    listing = client.get("/api/v1/scholarship/scholarships").get_json()
    assert listing["total"] == 1
    assert listing["items"][0]["publishedOn"] is not None


def test_body_is_sanitized(admin):
    response = create_scholarship(
        admin, body='<script>alert(1)</script><p>Aman</p>'
    )

    body = response.get_json()["body"]
    assert "<script" not in body
    assert "<p>Aman</p>" in body


def test_update_and_delete(admin):
    create_scholarship(admin, slug="lifecycle")

    updated = admin.patch(
        "/api/v1/scholarship/scholarships/lifecycle",
        json={"level": "S2", "order": 5, "status": "published"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["level"] == "S2"
    assert updated.get_json()["order"] == 5

    deleted = admin.delete("/api/v1/scholarship/scholarships/lifecycle")
    assert deleted.status_code == 204
    assert deleted.data == b""
