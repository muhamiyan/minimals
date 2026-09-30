def test_api_keys_require_authentication(client):
    assert client.get("/api/v1/account/api-keys").status_code == 401
    assert (
        client.post("/api/v1/account/api-keys", json={"name": "x"}).status_code == 401
    )


def test_create_api_key_returns_the_secret_once(member):
    response = member.post("/api/v1/account/api-keys", json={"name": "local"})
    assert response.status_code == 201

    body = response.get_json()
    assert body["key"].startswith("sk-")
    assert body["name"] == "lo****al"


def test_list_api_keys_is_camel_case(member):
    member.post("/api/v1/account/api-keys", json={"name": "local"})

    body = member.get("/api/v1/account/api-keys").get_json()
    assert set(body) == {"items"}
    assert set(body["items"][0]) == {
        "id",
        "name",
        "prefix",
        "isActive",
        "createdOn",
    }


def test_api_keys_are_scoped_to_the_owner(member, admin):
    member.post("/api/v1/account/api-keys", json={"name": "local"})

    assert len(member.get("/api/v1/account/api-keys").get_json()["items"]) == 1
    assert admin.get("/api/v1/account/api-keys").get_json()["items"] == []


def test_revoke_api_key(member):
    member.post("/api/v1/account/api-keys", json={"name": "local"})
    key_id = member.get("/api/v1/account/api-keys").get_json()["items"][0]["id"]

    response = member.delete(f"/api/v1/account/api-keys/{key_id}")
    assert response.status_code == 200
    assert response.get_json() == {"message": "revoked"}
    assert member.get("/api/v1/account/api-keys").get_json()["items"] == []


def test_revoke_foreign_api_key_is_404(member, admin):
    member.post("/api/v1/account/api-keys", json={"name": "local"})
    key_id = member.get("/api/v1/account/api-keys").get_json()["items"][0]["id"]

    response = admin.delete(f"/api/v1/account/api-keys/{key_id}")
    assert response.status_code == 404
    assert response.get_json() == {"message": "api_key_not_found"}


def test_revoke_unknown_api_key_is_404(member):
    response = member.delete("/api/v1/account/api-keys/no-such-key")
    assert response.status_code == 404
    assert response.get_json() == {"message": "api_key_not_found"}


def test_create_api_key_rejects_blank_name(member):
    response = member.post("/api/v1/account/api-keys", json={"name": "   "})
    assert response.status_code == 400
    assert set(response.get_json()) == {"message"}


def test_invalid_api_key_is_rejected_even_with_a_session(app, member):
    response = member.get(
        "/api/v1/auth/me", headers={"X-API-Key": "sk-not-a-real-key"}
    )
    assert response.status_code == 401
    assert response.get_json() == {"message": "invalid_api_key"}


def test_valid_api_key_authenticates_without_a_session(app, member):
    key = member.post("/api/v1/account/api-keys", json={"name": "ci"}).get_json()[
        "key"
    ]

    fresh = app.test_client()
    response = fresh.get("/api/v1/auth/me", headers={"X-API-Key": key})

    assert response.status_code == 200
    assert response.get_json()["email"] == "member@example.com"
