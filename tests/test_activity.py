from app.infra.seo import save_brand
from framework.extensions import db


def create_activity(admin, **overrides):
    payload = {
        "title": "Pengajian Bulanan",
        "body": "<p>Materi pengajian</p>",
        **overrides,
    }
    return admin.post("/api/v1/activity/activities", json=payload)


def test_list_activities_is_public_and_paginated(client):
    body = client.get("/api/v1/activity/activities").get_json()

    assert set(body) == {"items", "total", "page", "perPage"}
    assert body["items"] == []
    assert body["total"] == 0


def test_create_activity_requires_auth_and_admin(client, member):
    payload = {"title": "T", "body": "B"}
    assert client.post("/api/v1/activity/activities", json=payload).status_code == 401
    assert member.post("/api/v1/activity/activities", json=payload).status_code == 403


def test_create_activity_with_auto_and_explicit_slug(admin):
    created = create_activity(admin, title="Suling Subuh Keliling!")
    assert created.status_code == 201
    assert created.get_json()["slug"] == "suling-subuh-keliling"
    assert created.get_json()["status"] == "draft"

    explicit = create_activity(admin, slug="hultah-nw-91")
    assert explicit.status_code == 201
    assert explicit.get_json()["slug"] == "hultah-nw-91"


def test_duplicate_slug_is_conflict(admin):
    create_activity(admin, slug="dupe")
    response = create_activity(admin, title="Other", slug="dupe")

    assert response.status_code == 409
    assert response.get_json() == {"message": "slug_taken"}


def test_draft_is_hidden_publicly_but_visible_to_admin(admin, client):
    create_activity(admin, slug="secret-draft")

    assert client.get("/api/v1/activity/activities").get_json()["total"] == 0
    assert client.get("/api/v1/activity/activities/secret-draft").status_code == 404

    detail = admin.get("/api/v1/activity/activities/secret-draft")
    assert detail.status_code == 200
    assert detail.get_json()["status"] == "draft"


def test_published_activity_is_public(admin, client):
    create_activity(admin, slug="published-activity", status="published")

    listing = client.get("/api/v1/activity/activities").get_json()
    assert listing["total"] == 1
    assert listing["items"][0]["slug"] == "published-activity"
    assert listing["items"][0]["publishedOn"] is not None

    detail = client.get("/api/v1/activity/activities/published-activity")
    assert detail.status_code == 200
    assert detail.get_json()["body"] == "<p>Materi pengajian</p>"


def test_body_is_sanitized(admin):
    response = create_activity(
        admin,
        body='<script>alert(1)</script><p>Aman</p><a href="javascript:x">x</a>',
    )

    body = response.get_json()["body"]
    assert "<script" not in body
    assert "javascript:" not in body
    assert "<p>Aman</p>" in body


def test_publish_and_unpublish_toggle_publication_date(admin, client):
    create_activity(admin, slug="lifecycle")

    published = admin.patch(
        "/api/v1/activity/activities/lifecycle", json={"status": "published"}
    )
    assert published.status_code == 200
    assert published.get_json()["publishedOn"] is not None
    assert client.get("/api/v1/activity/activities").get_json()["total"] == 1

    draft = admin.patch(
        "/api/v1/activity/activities/lifecycle", json={"status": "draft"}
    )
    assert draft.status_code == 200
    assert "publishedOn" not in draft.get_json()
    assert client.get("/api/v1/activity/activities").get_json()["total"] == 0


def test_delete_activity(admin):
    create_activity(admin, slug="to-delete")

    response = admin.delete("/api/v1/activity/activities/to-delete")

    assert response.status_code == 204
    assert response.data == b""
    assert admin.get("/api/v1/activity/admin/activities").get_json()["total"] == 0


def test_activity_in_sitemap_and_seo(app, client, admin):
    with app.app_context():
        save_brand(
            db.session,
            {"name": "Yayasan Islam Selaparang", "siteUrl": "https://selaparang.test"},
        )
        db.session.commit()

    create_activity(admin, slug="kegiatan-seo", status="published")

    sitemap = client.get("/sitemap.xml").get_data(as_text=True)
    assert "/activities" in sitemap
    assert "/activities/kegiatan-seo" in sitemap

    head = client.get("/activities/kegiatan-seo").get_data(as_text=True)
    assert "kegiatan-seo" in head
