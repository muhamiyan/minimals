from __future__ import annotations

from uuid import uuid4

import pytest

from app.infra.seo import get_brand

BRAND_URL = "/api/v1/brand/logo"
META_URL = "/api/v1/brand"
META = {
    "name": "Acme",
    "tagline": "Tagline",
    "description": "Description",
    "siteUrl": "https://acme.test",
}


def _url(name: str | None = None) -> str:
    return f"/uploads/{name or f'{uuid4()}.png'}"


def test_brand_meta_requires_authentication(client):
    response = client.put(META_URL, json=META)

    assert response.status_code == 401


def test_member_cannot_update_meta(member):
    response = member.put(META_URL, json=META)

    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_admin_updates_meta(app, admin):
    response = admin.put(META_URL, json=META)

    assert response.status_code == 200
    assert response.get_json() == META
    with app.app_context():
        brand = get_brand()
        assert brand["name"] == "Acme"
        assert brand["tagline"] == "Tagline"
        assert brand["description"] == "Description"
        assert brand["siteUrl"] == "https://acme.test"


def test_admin_meta_trims_and_defaults_blank_name(app, admin):
    response = admin.put(
        META_URL,
        json={**META, "name": "   ", "tagline": "  x  ", "siteUrl": "  https://acme.test  "},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "name": "Yayasan Islam Selaparang",
        "tagline": "x",
        "description": "Description",
        "siteUrl": "https://acme.test",
    }
    with app.app_context():
        assert get_brand()["name"] == "Yayasan Islam Selaparang"


@pytest.mark.parametrize(
    "site_url",
    ["not-a-url", "ftp://acme.test", "https://bad host", "https://"],
)
def test_admin_meta_rejects_invalid_site_url(app, admin, site_url):
    response = admin.put(META_URL, json={**META, "siteUrl": site_url})

    assert response.status_code == 400
    assert response.get_json() == {"message": "site_url_invalid"}
    with app.app_context():
        assert get_brand()["name"] == "Yayasan Islam Selaparang"


def test_admin_meta_requires_name(admin):
    response = admin.put(META_URL, json={"tagline": "Tagline"})

    assert response.status_code == 400
    assert response.get_json() == {"message": "name_required"}


def test_brand_logo_requires_authentication(client):
    response = client.put(BRAND_URL, json={"logoUrl": ""})

    assert response.status_code == 401


def test_member_cannot_update_logo(member):
    response = member.put(BRAND_URL, json={"logoUrl": _url()})

    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_admin_sets_and_clears_logo(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    url = _url()
    (tmp_path / url.removeprefix("/uploads/")).write_bytes(b"image")

    response = admin.put(BRAND_URL, json={"logoUrl": url})
    assert response.status_code == 200
    assert response.get_json() == {"logoUrl": url}
    with app.app_context():
        assert get_brand()["logoUrl"] == url

    response = admin.put(BRAND_URL, json={"logoUrl": ""})
    assert response.status_code == 200
    assert response.get_json() == {"logoUrl": ""}
    with app.app_context():
        assert get_brand()["logoUrl"] == ""


def test_admin_logo_trims_whitespace(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    url = _url()
    (tmp_path / url.removeprefix("/uploads/")).write_bytes(b"image")

    response = admin.put(BRAND_URL, json={"logoUrl": f"  {url}  "})

    assert response.status_code == 200
    assert response.get_json() == {"logoUrl": url}


def test_logo_rejects_missing_upload(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = admin.put(BRAND_URL, json={"logoUrl": _url()})

    assert response.status_code == 400
    assert response.get_json() == {"message": "logo_upload_missing"}
    with app.app_context():
        assert get_brand()["logoUrl"] == ""


def test_replacing_logo_deletes_previous_upload(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    old, new = _url(), _url()
    for url in (old, new):
        (tmp_path / url.removeprefix("/uploads/")).write_bytes(b"image")

    admin.put(BRAND_URL, json={"logoUrl": old})
    response = admin.put(BRAND_URL, json={"logoUrl": new})

    assert response.status_code == 200
    assert not (tmp_path / old.removeprefix("/uploads/")).exists()
    assert (tmp_path / new.removeprefix("/uploads/")).exists()


def test_clearing_logo_deletes_upload(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    url = _url()
    (tmp_path / url.removeprefix("/uploads/")).write_bytes(b"image")

    admin.put(BRAND_URL, json={"logoUrl": url})
    response = admin.put(BRAND_URL, json={"logoUrl": ""})

    assert response.status_code == 200
    assert not (tmp_path / url.removeprefix("/uploads/")).exists()


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.test/logo.png",
        "//evil.test/logo.png",
        "/uploads/../secret.png",
        "/uploads/logo.png",
        f"/uploads/{uuid4()}.svg",
        f"static/{uuid4()}.png",
    ],
)
def test_logo_rejects_non_upload_urls(admin, url):
    response = admin.put(BRAND_URL, json={"logoUrl": url})

    assert response.status_code == 400
    assert response.get_json() == {"message": "logo_url_invalid"}


def test_logo_requires_field(admin):
    response = admin.put(BRAND_URL, json={})

    assert response.status_code == 400
    assert response.get_json() == {"message": "logo_url_required"}
