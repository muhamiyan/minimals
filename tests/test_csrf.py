from conftest import register


def test_mutating_request_without_token_is_rejected(app):
    response = app.test_client().post(
        "/api/v1/auth/register",
        json={
            "email": "raw@example.com",
            "username": "raw",
            "password": "Str0ng!Pass",
            "fullName": "Raw User",
        },
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "csrf_token_invalid"}


def test_read_requests_do_not_need_a_token(app):
    assert app.test_client().get("/health").status_code == 200


def test_token_from_csrf_endpoint_allows_registration(client):
    response = register(client)
    assert response.status_code == 201
    assert response.get_json()["username"] == "alice"


def test_one_cached_token_survives_login_and_logout(app):
    client = app.test_client()
    token = client.get("/api/v1/csrf").get_json()["csrfToken"]
    client.environ_base["HTTP_X_CSRFTOKEN"] = token

    assert register(client).status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "alice", "password": "Str0ng!Pass"},
    )
    assert login.status_code == 200

    assert client.post("/api/v1/auth/logout").status_code == 200

    retry = client.post(
        "/api/v1/auth/login",
        json={"identifier": "alice", "password": "Str0ng!Pass"},
    )
    assert retry.status_code == 200


def test_stale_token_is_rejected(app):
    client = app.test_client()
    stale = client.get("/api/v1/csrf").get_json()["csrfToken"]
    fresh = client.get("/api/v1/csrf").get_json()["csrfToken"]
    assert stale == fresh

    other = app.test_client()
    response = other.post(
        "/api/v1/auth/login",
        json={"identifier": "ghost", "password": "Str0ng!Pass"},
        headers={"X-CSRFToken": stale},
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "csrf_token_invalid"}
