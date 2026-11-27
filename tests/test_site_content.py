from __future__ import annotations

import json
from uuid import uuid4

from app.infra.models import AppSetting
from app.infra.seo import index_context
from app.infra.site_content_service import SITE_CONTENT_KEY
from framework.extensions import db

URL = "/api/v1/site/content"


def test_site_content_requires_authentication(client):
    assert client.get(URL).status_code == 401
    assert client.put(URL, json={}).status_code == 401
    assert client.patch(URL, json={}).status_code == 401


def test_member_cannot_read_or_write_site_content(member):
    assert member.get(URL).status_code == 403
    assert member.put(URL, json={}).status_code == 403
    assert member.patch(URL, json={}).status_code == 403


def test_admin_gets_full_shape(admin):
    data = admin.get(URL).get_json()

    assert set(data) >= {"hero", "highlights", "stats", "contact"}
    assert data["hero"]["title"] == ""
    assert data["configuredSections"] == []


def test_admin_saves_free_text_and_sanitizes_rich(admin):
    payload = {
        "configuredSections": ["support", "contact"],
        "support": {
            "body": "<p>Dukungan <b>baru</b></p><script>alert(1)</script>",
        },
        "contact": {"address": "Jl. Baru"},
    }

    response = admin.put(URL, json=payload)

    assert response.status_code == 200
    data = response.get_json()
    assert data["configuredSections"] == ["support", "contact"]
    assert data["support"]["body"].startswith("<p>Dukungan <b>baru</b></p>")
    assert "<script>" not in data["support"]["body"]
    assert data["contact"]["address"] == "Jl. Baru"
    assert data["hero"]["title"] == ""


def test_contact_map_and_ppdb_schedule_roundtrip(admin):
    response = admin.patch(URL, json={
        "configuredSections": ["contact", "ppdb"],
        "contact": {"mapsUrl": "https://www.google.com/maps?q=-8.6,116.1&output=embed"},
        "ppdb": {
            "period": "1 Mei - 30 Juni 2027",
            "hours": "08.00-16.00 WITA",
            "location": "Sekretariat YIS",
        },
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["contact"]["mapsUrl"].startswith("https://www.google.com/maps")
    assert data["ppdb"]["hours"] == "08.00-16.00 WITA"
    assert data["ppdb"]["location"] == "Sekretariat YIS"


def test_copy_accepts_arbitrary_text(admin):
    response = admin.put(URL, json={"hero": {"title": "Pondok pesantren tradisional"}})

    assert response.status_code == 200
    assert response.get_json()["hero"]["title"] == "Pondok pesantren tradisional"


def test_invalid_section_rejected(admin):
    response = admin.put(URL, json={"configuredSections": ["nope"]})

    assert response.status_code == 400


def test_invalid_url_rejected(admin):
    response = admin.put(URL, json={"ppdb": {"url": "javascript:alert(1)"}})

    assert response.status_code == 400


def test_site_content_injected_into_boot(app, admin):
    admin.put(URL, json={"hero": {"title": "Judul hero"}})

    with app.test_request_context("/"):
        context = index_context()

    assert context["siteContent"]["hero"]["title"] == "Judul hero"


def test_phase2_content_roundtrip(admin):
    slide = f"/uploads/{uuid4()}.jpg"
    photo = f"/uploads/{uuid4()}.jpg"

    response = admin.put(URL, json={
        "heroSlides": [slide],
        "pengurus": [{"name": "Amin", "role": "Ketua", "photo": photo}],
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["heroSlides"] == [slide]
    assert data["pengurus"][0]["role"] == "Ketua"


def test_hero_slide_must_be_stored_upload(admin):
    response = admin.put(URL, json={"heroSlides": ["https://cdn.example.test/a.jpg"]})

    assert response.status_code == 400


def test_patch_merges_one_section(app, admin):
    admin.put(URL, json={
        "hero": {"title": "Hero lama"},
        "contact": {"address": "Alamat lama"},
    })

    response = admin.patch(URL, json={
        "configuredSections": ["hero"],
        "hero": {"title": "Hero baru"},
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["hero"]["title"] == "Hero baru"
    assert data["contact"]["address"] == "Alamat lama"
    assert data["configuredSections"] == ["hero"]


def test_patch_hero_section_includes_slides(admin):
    slide = f"/uploads/{uuid4()}.jpg"

    response = admin.patch(URL, json={
        "configuredSections": ["hero"],
        "hero": {"title": "Hero", "period": "1 April - 10 Juli 2026"},
        "heroSlides": [slide],
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["hero"]["period"] == "1 April - 10 Juli 2026"
    assert data["heroSlides"] == [slide]
    assert data["configuredSections"] == ["hero"]


def test_corrupt_stored_value_keeps_other_content(app, admin):
    admin.put(URL, json={
        "hero": {"title": "Judul"},
        "contact": {"address": "Alamat baru"},
    })
    with app.app_context():
        row = AppSetting.query.filter_by(key=SITE_CONTENT_KEY).one()
        stored = json.loads(row.value)
        stored["contact"]["address"] = 42
        row.value = json.dumps(stored)
        db.session.commit()

    data = admin.get(URL).get_json()

    assert data["hero"]["title"] == "Judul"
    assert data["contact"]["address"] == ""


def test_too_many_slides_rejected(admin):
    response = admin.put(URL, json={
        "heroSlides": [f"/hero/hero-{i}.jpg" for i in range(11)]
    })

    assert response.status_code == 400


def test_invalid_pengurus_photo_rejected(admin):
    response = admin.put(URL, json={
        "pengurus": [{"name": "Amin", "photo": "https://cdn.example.test/a.jpg"}]
    })

    assert response.status_code == 400
