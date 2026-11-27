"""Blog HTTP endpoints — public reading and admin management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.blog.dto import BlogCategoryCreateIn, BlogCreateIn, BlogUpdateIn
from app.blog.presenters import BlogCategoryOut, BlogPostOut, BlogPostSummaryOut
from app.blog.services import BlogCategoryService, BlogService
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    no_content,
    ok,
    paginate,
    paginated_response,
)
from framework.auth.helpers import require_role

bp = BlueprintFactory("blog", __name__, url_prefix="/api/v1/blog")


def _viewer_is_admin() -> bool:
    return bool(
        current_user.is_authenticated
        and getattr(current_user, "app_role", None) == "admin"
    )


def _actor_name() -> str:
    return current_user.full_name or current_user.username


@bp.get("/categories")
@login_required
def list_categories():
    if denied := require_role("admin"):
        return denied

    categories = BlogCategoryService().list_categories()
    return ok({"items": [BlogCategoryOut.from_model(c).to_dict() for c in categories]})


@bp.post("/categories")
@login_required
def create_category():
    if denied := require_role("admin"):
        return denied

    dto = BlogCategoryCreateIn.validate(request.get_json(silent=True) or {})
    category, was_created = BlogCategoryService().create(dto, actor_id=current_user.id)
    body = BlogCategoryOut.from_model(category).to_dict()
    return created(body) if was_created else ok(body)


@bp.get("/posts")
def list_posts():
    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    posts, total = BlogService().list_published(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [BlogPostSummaryOut.from_post(p).to_dict() for p in posts],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.get("/posts/<slug>")
def get_post(slug: str):
    post = BlogService().get_post(slug, include_drafts=_viewer_is_admin())
    return ok(BlogPostOut.from_post(post).to_dict())


@bp.get("/admin/posts")
@login_required
def list_all_posts():
    if denied := require_role("admin"):
        return denied

    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    posts, total = BlogService().list_all(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [BlogPostSummaryOut.from_post(p).to_dict() for p in posts],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.post("/posts")
@login_required
def create_post():
    if denied := require_role("admin"):
        return denied

    dto = BlogCreateIn.validate(request.get_json(silent=True) or {})
    post = BlogService().create(
        dto, actor_id=current_user.id, actor_name=_actor_name()
    )
    return created(BlogPostOut.from_post(post).to_dict())


@bp.patch("/posts/<slug>")
@login_required
def update_post(slug: str):
    if denied := require_role("admin"):
        return denied

    dto = BlogUpdateIn.validate(request.get_json(silent=True) or {})
    post = BlogService().update(
        slug, dto, actor_id=current_user.id, actor_name=_actor_name()
    )
    return ok(BlogPostOut.from_post(post).to_dict())


@bp.delete("/posts/<slug>")
@login_required
def delete_post(slug: str):
    if denied := require_role("admin"):
        return denied

    BlogService().delete(slug, actor_id=current_user.id)
    return no_content()
