PAYLOAD = {
    "name": "Ahmad",
    "phone": "0878 6470 6565",
    "email": "ahmad@example.com",
    "message": "Mohon info pendaftaran.",
}


def test_public_can_send_message(client):
    response = client.post("/api/v1/contact/messages", json=PAYLOAD)

    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Ahmad"
    assert body["phone"] == "0878 6470 6565"
    assert body["email"] == "ahmad@example.com"
    assert body["message"] == "Mohon info pendaftaran."
    assert body["isRead"] is False
    assert body["createdOn"] is not None


def test_message_validation(client):
    bad_phone = client.post(
        "/api/v1/contact/messages", json={**PAYLOAD, "phone": "abc"}
    )
    assert bad_phone.status_code == 400
    assert bad_phone.get_json() == {"message": "phone_invalid_phone"}

    no_digit = client.post(
        "/api/v1/contact/messages", json={**PAYLOAD, "phone": "++++++"}
    )
    assert no_digit.status_code == 400
    assert no_digit.get_json() == {"message": "phone_invalid_phone"}

    empty_message = client.post(
        "/api/v1/contact/messages", json={**PAYLOAD, "message": "   "}
    )
    assert empty_message.status_code == 400

    bad_email = client.post(
        "/api/v1/contact/messages", json={**PAYLOAD, "email": "not-an-email"}
    )
    assert bad_email.status_code == 400


def test_admin_list_requires_admin(client, member, admin):
    assert client.get("/api/v1/contact/admin/messages").status_code == 401
    assert member.get("/api/v1/contact/admin/messages").status_code == 403

    response = admin.get("/api/v1/contact/admin/messages")
    assert response.status_code == 200
    assert set(response.get_json()) == {"items", "total", "page", "perPage"}


def test_admin_list_search(client, admin):
    client.post("/api/v1/contact/messages", json=PAYLOAD)

    found = admin.get("/api/v1/contact/admin/messages?search=pendaftaran")
    missing = admin.get("/api/v1/contact/admin/messages?search=nope-nope")

    assert found.get_json()["total"] == 1
    assert missing.get_json()["total"] == 0


def test_admin_can_mark_read_and_delete(client, admin):
    message_id = client.post("/api/v1/contact/messages", json=PAYLOAD).get_json()["id"]

    updated = admin.patch(
        f"/api/v1/contact/admin/messages/{message_id}", json={"isRead": True}
    )
    assert updated.status_code == 200
    assert updated.get_json()["isRead"] is True

    listed = admin.get("/api/v1/contact/admin/messages").get_json()
    assert listed["total"] == 1
    assert listed["items"][0]["isRead"] is True

    deleted = admin.delete(f"/api/v1/contact/admin/messages/{message_id}")
    assert deleted.status_code == 204
    assert deleted.data == b""
    assert admin.get("/api/v1/contact/admin/messages").get_json()["total"] == 0


def test_missing_message_is_404(admin):
    response = admin.delete("/api/v1/contact/admin/messages/does-not-exist")

    assert response.status_code == 404
    assert response.get_json() == {"message": "contact_message_not_found"}
