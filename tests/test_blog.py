ITEM_KEYS = {
    "id",
    "title",
    "slug",
    "excerpt",
    "status",
    "createdOn",
    "authorName",
}

DRAFT_DETAIL_KEYS = ITEM_KEYS | {"body"}
PUBLISHED_SUMMARY_KEYS = ITEM_KEYS | {"publishedOn"}
PUBLISHED_DETAIL_KEYS = ITEM_KEYS | {"body", "publishedOn"}
COVER_DETAIL_KEYS = ITEM_KEYS | {"body", "coverImage"}


def create_post(admin, **overrides):
    payload = {
        "title": "Hello World",
        "body": "<p>First post content</p>",
        **overrides,
    }
    return admin.post("/api/v1/blog/posts", json=payload)


def test_list_posts_is_public_and_paginated(client):
    body = client.get("/api/v1/blog/posts").get_json()
    assert set(body) == {"items", "total", "page", "perPage"}
    assert body["items"] == []
    assert body["total"] == 0


def test_create_post_requires_authentication(client):
    response = client.post("/api/v1/blog/posts", json={"title": "T", "body": "B"})
    assert response.status_code == 401
    assert response.get_json() == {"message": "unauthorized"}


def test_create_post_requires_admin(member):
    response = member.post("/api/v1/blog/posts", json={"title": "T", "body": "B"})
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_create_post_returns_201_with_automatic_slug(admin):
    response = create_post(admin, title="Hello World!")
    assert response.status_code == 201

    body = response.get_json()
    assert set(body) == DRAFT_DETAIL_KEYS
    assert body["slug"] == "hello-world"
    assert body["status"] == "draft"
    assert body["authorName"] == "Admin User"
    assert "publishedOn" not in body
    assert "coverImage" not in body


def test_create_post_accepts_explicit_slug(admin):
    response = create_post(admin, slug="my-custom-slug")
    assert response.status_code == 201
    assert response.get_json()["slug"] == "my-custom-slug"


def test_create_duplicate_slug_is_409(admin):
    create_post(admin, slug="dupe")
    response = create_post(admin, title="Other", slug="dupe")
    assert response.status_code == 409
    assert response.get_json() == {"message": "slug_taken"}


def test_create_rejects_invalid_status(admin):
    response = create_post(admin, status="archived")
    assert response.status_code == 400
    assert response.get_json() == {"message": "status_invalid"}


def test_draft_is_hidden_from_public_list_and_detail(admin, client):
    create_post(admin, slug="secret-draft")

    body = client.get("/api/v1/blog/posts").get_json()
    assert body["total"] == 0

    detail = client.get("/api/v1/blog/posts/secret-draft")
    assert detail.status_code == 404
    assert detail.get_json() == {"message": "post_not_found"}


def test_draft_is_visible_to_admin(admin):
    create_post(admin, slug="secret-draft")
    detail = admin.get("/api/v1/blog/posts/secret-draft")
    assert detail.status_code == 200
    assert detail.get_json()["status"] == "draft"


def test_published_post_is_public(admin, client):
    create_post(admin, slug="published-post", status="published")

    body = client.get("/api/v1/blog/posts").get_json()
    assert body["total"] == 1
    assert set(body["items"][0]) == PUBLISHED_SUMMARY_KEYS
    assert body["items"][0]["slug"] == "published-post"
    assert body["items"][0]["publishedOn"] is not None

    detail = client.get("/api/v1/blog/posts/published-post")
    assert detail.status_code == 200
    assert set(detail.get_json()) == PUBLISHED_DETAIL_KEYS


def test_list_posts_search_filters_by_title(admin, client):
    create_post(admin, title="Flask Tips", status="published")
    create_post(admin, title="Vue Tricks", status="published")

    body = client.get("/api/v1/blog/posts", query_string={"search": "Flask"}).get_json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Flask Tips"


def test_list_posts_is_paginated(admin, client):
    for i in range(3):
        create_post(admin, title=f"Post {i}", status="published")

    body = client.get(
        "/api/v1/blog/posts", query_string={"page": 2, "per_page": 2}
    ).get_json()
    assert body["total"] == 3
    assert body["page"] == 2
    assert body["perPage"] == 2
    assert len(body["items"]) == 1


def test_update_post_requires_admin(member):
    response = member.patch("/api/v1/blog/posts/whatever", json={"title": "Nope"})
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_update_post_is_camel_case_and_persists(admin):
    create_post(admin, slug="editable")

    response = admin.patch(
        "/api/v1/blog/posts/editable",
        json={"title": "Updated Title", "coverImage": "/uploads/cover.png"},
    )
    assert response.status_code == 200

    body = response.get_json()
    assert set(body) == COVER_DETAIL_KEYS
    assert body["title"] == "Updated Title"
    assert body["coverImage"] == "/uploads/cover.png"
    assert admin.get("/api/v1/blog/posts/editable").get_json()["title"] == "Updated Title"


def test_publish_sets_published_on_and_unpublish_clears_it(admin):
    create_post(admin, slug="lifecycle")

    published = admin.patch("/api/v1/blog/posts/lifecycle", json={"status": "published"})
    assert published.status_code == 200
    assert published.get_json()["publishedOn"] is not None

    unpublished = admin.patch("/api/v1/blog/posts/lifecycle", json={"status": "draft"})
    assert unpublished.status_code == 200
    assert "publishedOn" not in unpublished.get_json()


def test_update_with_empty_body_is_400(admin):
    create_post(admin, slug="nochange")
    response = admin.patch("/api/v1/blog/posts/nochange", json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "value_no_fields_to_update"}


def test_update_unknown_post_is_404(admin):
    response = admin.patch("/api/v1/blog/posts/ghost", json={"title": "X"})
    assert response.status_code == 404
    assert response.get_json() == {"message": "post_not_found"}


def test_delete_post_is_204_and_removes_it(admin, client):
    create_post(admin, slug="doomed", status="published")

    response = admin.delete("/api/v1/blog/posts/doomed")
    assert response.status_code == 204
    assert response.data == b""

    assert admin.get("/api/v1/blog/posts/doomed").status_code == 404
    assert client.get("/api/v1/blog/posts").get_json()["total"] == 0


def test_delete_unknown_post_is_404(admin):
    response = admin.delete("/api/v1/blog/posts/ghost")
    assert response.status_code == 404
    assert response.get_json() == {"message": "post_not_found"}


def test_delete_post_requires_admin(member):
    response = member.delete("/api/v1/blog/posts/whatever")
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_admin_list_requires_authentication(client):
    response = client.get("/api/v1/blog/admin/posts")
    assert response.status_code == 401
    assert response.get_json() == {"message": "unauthorized"}


def test_admin_list_requires_admin(member):
    response = member.get("/api/v1/blog/admin/posts")
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_admin_list_includes_drafts(admin, client):
    create_post(admin, slug="draft-post")

    assert client.get("/api/v1/blog/posts").get_json()["total"] == 0

    body = admin.get("/api/v1/blog/admin/posts").get_json()
    assert set(body) == {"items", "total", "page", "perPage"}
    assert body["total"] == 1
    assert set(body["items"][0]) == ITEM_KEYS
    assert body["items"][0]["status"] == "draft"


def test_frappe_style_csrf_header_is_accepted(app, admin):
    client = app.test_client()
    token = client.get("/api/v1/csrf").get_json()["csrfToken"]
    client.environ_base["HTTP_X_FRAPPE_CSRF_TOKEN"] = token

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "admin@example.com", "password": "Str0ng!Pass"},
    )
    assert login.status_code == 200

    response = client.post(
        "/api/v1/blog/posts", json={"title": "Alias header", "body": "<p>x</p>"}
    )
    assert response.status_code == 201


def test_update_slug_is_ignored(admin):
    create_post(admin, slug="keep-slug")
    response = admin.patch(
        "/api/v1/blog/posts/keep-slug",
        json={"title": "Renamed", "slug": "hijacked"},
    )
    assert response.status_code == 200
    assert response.get_json()["slug"] == "keep-slug"


def test_draft_is_hidden_from_member(admin, member):
    create_post(admin, slug="member-draft")
    detail = member.get("/api/v1/blog/posts/member-draft")
    assert detail.status_code == 404
    assert detail.get_json() == {"message": "post_not_found"}


def test_create_rejects_invalid_slug(admin):
    response = create_post(admin, slug="Not A Slug!")
    assert response.status_code == 400
    assert response.get_json() == {"message": "slug_invalid"}


def test_body_html_is_sanitized(admin):
    response = create_post(
        admin,
        slug="xss-body",
        body=(
            '<p onclick="steal()">hi</p><script>alert(1)</script>'
            '<img src="/uploads/x.png" onerror="alert(2)">'
            '<a href="javascript:evil()">l</a>'
        ),
    )
    assert response.status_code == 201
    body = response.get_json()["body"]
    assert "<p" in body and "hi" in body
    assert "<script" not in body
    assert "onclick" not in body
    assert "onerror" not in body
    assert "javascript:" not in body

    patched = admin.patch(
        "/api/v1/blog/posts/xss-body", json={"body": "<script>bad()</script>ok"}
    )
    assert patched.status_code == 200
    assert "<script" not in patched.get_json()["body"]

    rejected = create_post(admin, slug="all-script", body="<script>alert(1)</script>")
    assert rejected.status_code == 400
    assert rejected.get_json() == {"message": "body_invalid"}


def test_create_title_without_slugable_chars_is_422(admin):
    response = create_post(admin, title="!!!")
    assert response.status_code == 422
    assert response.get_json() == {"message": "slug_required"}
