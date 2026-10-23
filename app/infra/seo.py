"""White-label brand + SEO — settings storage, per-path index payload, crawler files."""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

from flask import Blueprint, current_app, has_request_context, request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.models import AppSetting
from framework.exceptions import ValidationFailed
from framework.extensions import db
from framework.extensions.rate_limit import limiter

bp = Blueprint("seo", __name__)

limiter.exempt(bp)

DEFAULT_BRAND: dict[str, str] = {
    "name": "Minimals",
    "tagline": "",
    "description": "",
    "siteUrl": "",
}

BRAND_KEYS = tuple(DEFAULT_BRAND)

# First path segments of SPA routes that are never indexed (private app
# areas and auth forms). Mirrored as Disallow lines in robots.txt.
PRIVATE_SEGMENTS = frozenset({"admin", "dashboard", "login", "register", "setup"})

BLOG_LIST_TITLE = "Blog"


def get_brand() -> dict[str, str]:
    """Current brand settings; never raises.

    Before setup (no schema) or on any storage error the defaults are
    returned so serving ``index.html`` keeps working.
    """
    brand = dict(DEFAULT_BRAND)
    try:
        rows = db.session.scalars(
            select(AppSetting).where(AppSetting.key.in_(BRAND_KEYS))
        ).all()
    except Exception:
        db.session.rollback()
        return brand
    brand.update({row.key: row.value for row in rows})
    if not brand["name"].strip():
        brand["name"] = DEFAULT_BRAND["name"]
    return brand


def save_brand(session: Session, brand: dict[str, str]) -> None:
    """Upsert brand rows into the given (setup) session."""
    for key in BRAND_KEYS:
        value = (brand.get(key) or "").strip()
        if key == "name" and not value:
            value = DEFAULT_BRAND["name"]
        row = session.execute(
            select(AppSetting).where(AppSetting.key == key)
        ).scalar_one_or_none()
        if row is None:
            session.add(AppSetting(key=key, value=value))
        else:
            row.value = value


def validate_site_url(url: str | None) -> None:
    """Site URL must be an absolute http(s) URL with no whitespace."""
    if not url:
        return
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
    except ValueError:
        raise ValidationFailed("site_url_invalid") from None
    if (
        parts.scheme not in ("http", "https")
        or not hostname
        or any(ch.isspace() for ch in url)
    ):
        raise ValidationFailed("site_url_invalid")


def _canonical(brand: dict[str, str] | None = None) -> str:
    """Absolute site URL from brand ``siteUrl``; empty when not configured.

    Never derived from the request ``Host`` header — a spoofed host must
    not poison canonical/OG/sitemap URLs.
    """
    if brand is None:
        brand = get_brand()
    return brand.get("siteUrl", "").rstrip("/")


def _indexable() -> bool:
    return bool(current_app.config.get("SEO_INDEXABLE", True))


def _current_path() -> str:
    """Normalized request path; ``"/"`` outside a request context."""
    if not has_request_context():
        return "/"
    path = (request.path or "/").rstrip("/") or "/"
    # The built homepage is also reachable as /index.html — same page,
    # so it must get the root SEO head, not the unknown-path noindex.
    return "/" if path == "/index.html" else path


def _is_private(path: str) -> bool:
    return path.lstrip("/").partition("/")[0] in PRIVATE_SEGMENTS


def _published_post_by_slug(slug: str):
    """Published post for a slug — ``None`` on miss, bad slug or storage error."""
    from app.blog.models import BlogPost

    if not slug or "/" in slug:
        return None
    try:
        return db.session.scalar(
            select(BlogPost).where(
                BlogPost.slug == slug, BlogPost.status == "published"
            )
        )
    except Exception:
        db.session.rollback()
        return None


def _seo_for_path(brand: dict[str, str], path: str) -> dict:
    """SEO head payload for one SPA path.

    ``/`` keeps the classic brand-only head; ``/blog`` and ``/blog/<slug>``
    get page-specific titles/canonicals (article posts also get ``og:type``
    and ``og:image``). Private areas, unknown paths and missing/draft slugs
    come back ``noindex`` with no canonical so crawlers never index them.
    """
    site = _canonical(brand)
    name = brand["name"]
    lang = current_app.config.get("APP_LANG", "en")
    description = brand.get("description") or brand.get("tagline") or ""
    blog_title = f"{BLOG_LIST_TITLE} · {name}"

    def _base(title: str, robots: str, canonical: str) -> dict:
        payload = {
            "title": title,
            "lang": lang,
            "description": description,
            "robots": robots,
            "canonical": canonical,
            "site_name": name,
        }
        return payload

    if _is_private(path):
        return _base(name, "noindex, nofollow", "")
    if not _indexable():
        # Global noindex keeps master's shape: brand title + canonical site.
        return _base(name, "noindex, nofollow", site)

    if path == "/":
        return _base(name, "index, follow", site)
    if path == "/blog":
        return _base(blog_title, "index, follow", f"{site}/blog" if site else "")
    if path.startswith("/blog/"):
        post = _published_post_by_slug(path[len("/blog/") :])
        if post is None:
            return _base(blog_title, "noindex, nofollow", "")
        from app.blog.presenters import make_excerpt

        payload = _base(
            f"{post.title} · {name}",
            "index, follow",
            f"{site}/blog/{post.slug}" if site else "",
        )
        payload["description"] = make_excerpt(post.body)
        payload["og_type"] = "article"
        if site and post.cover_image:
            cover = post.cover_image
            payload["image"] = (
                cover
                if cover.startswith(("http://", "https://"))
                else f"{site}{cover}"
            )
        return payload
    # Unknown SPA path (404 inside the router) — never indexed.
    return _base(name, "noindex, nofollow", "")


def index_context() -> dict:
    """Boot payload for ``index.html``: brand for the SPA, ``seo`` for the head.

    ``seo`` is built for the current request path (per-page title/canonical,
    noindex for private areas) and is consumed server-side by
    ``_apply_seo`` — it never becomes a window global; everything else
    lands on ``window.brand``.
    """
    brand = get_brand()
    seo = _seo_for_path(brand, _current_path())
    return {"brand": brand, "seo": seo}


@bp.get("/robots.txt")
def robots_txt():
    if _indexable():
        body = (
            "User-Agent: *\n"
            "Allow: /\n"
            "Disallow: /api/\n"
            "Disallow: /dashboard\n"
            "Disallow: /admin\n"
            "Disallow: /setup\n"
            "Disallow: /login\n"
            "Disallow: /register\n"
        )
        if canonical := _canonical():
            body += f"Sitemap: {canonical}/sitemap.xml\n"
    else:
        body = "User-Agent: *\nDisallow: /\n"
    return body, 200, {"Content-Type": "text/plain; charset=utf-8"}


def _sitemap_entries() -> list[tuple[str, str | None]]:
    """``[(path, lastmod)]`` — root, blog index, published posts only.

    Never raises: on a storage error the root entry alone is returned so
    the crawler endpoint keeps serving what it can.
    """
    from app.blog.models import BlogPost

    entries: list[tuple[str, str | None]] = [("/", None), ("/blog", None)]
    try:
        rows = db.session.execute(
            select(BlogPost.slug, BlogPost.published_on, BlogPost.changed_on)
            .where(BlogPost.status == "published")
            .order_by(BlogPost.published_on.desc(), BlogPost.slug)
        ).all()
    except Exception:
        db.session.rollback()
        return entries[:1]
    for slug, published_on, changed_on in rows:
        last = published_on or changed_on
        entries.append((f"/blog/{slug}", last.date().isoformat() if last else None))
    return entries


@bp.get("/sitemap.xml")
def sitemap_xml():
    canonical = _canonical()
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    )
    if canonical:
        for path, lastmod in _sitemap_entries():
            loc = escape(f"{canonical}{path}")
            last = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
            xml += f"  <url><loc>{loc}</loc>{last}</url>\n"
    xml += "</urlset>\n"
    return xml, 200, {"Content-Type": "application/xml; charset=utf-8"}


__all__ = [
    "BRAND_KEYS",
    "DEFAULT_BRAND",
    "bp",
    "get_brand",
    "index_context",
    "save_brand",
    "validate_site_url",
]
