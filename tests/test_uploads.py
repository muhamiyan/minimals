from __future__ import annotations

import io
from uuid import uuid4

PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-image-bytes"


def _upload(client, filename="logo.png", content=PNG_BYTES):
    return client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(content), filename)},
        content_type="multipart/form-data",
    )


def test_admin_can_upload_image(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)

    response = _upload(admin)

    assert response.status_code == 201
    url = response.get_json()["url"]
    assert url.startswith("/uploads/")
    name = url.removeprefix("/uploads/")
    assert name.endswith(".png")
    assert (tmp_path / name).read_bytes() == PNG_BYTES


def test_member_cannot_upload(member):
    response = _upload(member)

    assert response.status_code == 403


def test_upload_rejects_bad_extension(admin):
    response = _upload(admin, filename="payload.svg")

    assert response.status_code == 400
    assert response.get_json() == {"message": "file_type_not_allowed"}


def test_upload_requires_file(admin):
    response = admin.post("/api/v1/uploads", data={})

    assert response.status_code == 400
    assert response.get_json() == {"message": "file_required"}


def test_upload_rejects_oversized_file(app, admin):
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    big = b"x" * (5 * 1024 * 1024 + 1)

    response = _upload(admin, content=big)

    assert response.status_code == 400
    assert response.get_json() == {"message": "file_too_large"}


def test_delete_rejects_invalid_name(admin):
    for name in ("evil.png", f"{uuid4()}.sh", "noext"):
        response = admin.delete(f"/api/v1/uploads/{name}")
        assert response.status_code == 400
        assert response.get_json() == {"message": "file_invalid_name"}


def test_delete_removes_file_and_is_idempotent(app, admin, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    name = f"{uuid4()}.png"
    (tmp_path / name).write_bytes(PNG_BYTES)

    first = admin.delete(f"/api/v1/uploads/{name}")
    second = admin.delete(f"/api/v1/uploads/{name}")

    assert first.status_code == 204
    assert second.status_code == 204
    assert not (tmp_path / name).exists()


def test_member_cannot_delete(member):
    name = f"{uuid4()}.png"

    response = member.delete(f"/api/v1/uploads/{name}")

    assert response.status_code == 403
