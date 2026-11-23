from app.infra.seo import save_brand
from framework.extensions import db


def create_program(admin, **overrides):
    payload = {
        "title": "MI NW Selaparang",
        "level": "MI",
        "body": "<p>Lembaga pendidikan dasar</p>",
        **overrides,
    }
    return admin.post("/api/v1/program/programs", json=payload)


def test_list_programs_is_public_and_ordered(client, admin):
    create_program(
        admin, slug="second", title="SMA NW", level="SMA", order=2, status="published"
    )
    create_program(
        admin, slug="first", title="MI NW", level="MI", order=1, status="published"
    )

    body = client.get("/api/v1/program/programs").get_json()

    assert set(body) == {"items", "total", "page", "perPage"}
    assert [item["slug"] for item in body["items"]] == ["first", "second"]


def test_create_requires_admin(client, member, admin):
    payload = {"title": "T", "body": "B"}
    assert client.post("/api/v1/program/programs", json=payload).status_code == 401
    assert member.post("/api/v1/program/programs", json=payload).status_code == 403

    created = create_program(admin, slug="mi-nw")
    assert created.status_code == 201
    assert created.get_json()["level"] == "MI"
    assert created.get_json()["order"] == 0


def test_duplicate_slug_is_conflict(admin):
    create_program(admin, slug="dupe")
    response = create_program(admin, title="Other", slug="dupe")

    assert response.status_code == 409
    assert response.get_json() == {"message": "slug_taken"}


def test_draft_hidden_publicly_and_published_visible(admin, client):
    create_program(admin, slug="draft-program")

    assert client.get("/api/v1/program/programs").get_json()["total"] == 0
    assert client.get("/api/v1/program/programs/draft-program").status_code == 404
    assert admin.get("/api/v1/program/programs/draft-program").status_code == 200

    create_program(admin, slug="public-program", status="published")
    listing = client.get("/api/v1/program/programs").get_json()
    assert listing["total"] == 1
    assert listing["items"][0]["publishedOn"] is not None


def test_body_is_sanitized(admin):
    response = create_program(
        admin, body='<script>alert(1)</script><p>Aman</p>'
    )

    body = response.get_json()["body"]
    assert "<script" not in body
    assert "<p>Aman</p>" in body


def test_update_and_delete(admin):
    create_program(admin, slug="lifecycle")

    updated = admin.patch(
        "/api/v1/program/programs/lifecycle",
        json={"level": "MTs", "order": 5, "status": "published"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["level"] == "MTs"
    assert updated.get_json()["order"] == 5

    deleted = admin.delete("/api/v1/program/programs/lifecycle")
    assert deleted.status_code == 204
    assert deleted.data == b""


def test_program_in_sitemap_and_seo(app, client, admin):
    with app.app_context():
        save_brand(
            db.session,
            {"name": "Yayasan Islam Selaparang", "siteUrl": "https://selaparang.test"},
        )
        db.session.commit()

    create_program(admin, slug="program-seo", status="published")

    sitemap = client.get("/sitemap.xml").get_data(as_text=True)
    assert "/programs" in sitemap
    assert "/programs/program-seo" in sitemap

    head = client.get("/programs/program-seo").get_data(as_text=True)
    assert "program-seo" in head
