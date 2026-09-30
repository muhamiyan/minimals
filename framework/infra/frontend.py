"""Serve a built Vue SPA — shared, service-agnostic helper."""
from __future__ import annotations

import os

from flask import (
    Flask,
    send_from_directory,
)
from flask_wtf.csrf import generate_csrf
from jinja2 import Environment, FileSystemLoader, select_autoescape

from framework.api.response import error
from framework.extensions.rate_limit import limiter

# One Jinja env per static_root — a process may mount SPAs from different
# directories, so we cannot use a single global.
_jinja_envs: dict[str, Environment] = {}


def _get_jinja_env(static_root: str) -> Environment:
    env = _jinja_envs.get(static_root)
    if env is None:
        env = Environment(
            loader=FileSystemLoader(static_root),
            autoescape=select_autoescape(["html", "xml"]),
            keep_trailing_newline=True,
        )
        _jinja_envs[static_root] = env
    return env


def has_frontend(static_root: str) -> bool:
    """``True`` when the SPA ``index.html`` exists under ``static_root``."""
    return os.path.isfile(os.path.join(static_root, "index.html"))


def _render_index_html(static_root: str) -> str:
    """Render ``<static_root>/index.html`` through Jinja, injecting CSRF.

    The Vite build embeds a ``{% for key in boot %} ... {% endfor %}`` block
    that needs server-side data. We inject the CSRF token there and the SPA
    reads it from ``window.csrfToken`` / ``window.boot`` at boot.
    """
    env = _get_jinja_env(static_root)
    template = env.get_template("index.html")
    return template.render(boot={"csrfToken": generate_csrf()})


def _serve_index(static_root: str):
    html = _render_index_html(static_root)
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


def _spa_not_built(url_prefix: str):
    return (
        {
            "message": "spa_not_built",
            "hint": (
                "Build the SPA (yarn build) so its output lands in the "
                f"service's static/frontend/ folder for prefix "
                f"'{url_prefix or '/'}'."
            ),
        },
        200,
    )


def register_spa(app: Flask, static_root: str, url_prefix: str = "") -> None:
    """Mount a built SPA on ``app`` at ``url_prefix``, served from ``static_root``.

    ``url_prefix`` is ``""`` for the root SPA (answers ``/``) or a path prefix
    for a sub-mounted SPA. Endpoints are namespaced by the prefix so several
    SPAs can coexist in one process.

    Registration order matters: mount SPAs LAST, after the API blueprints, so
    the catch-all never shadows them.
    """
    prefix = url_prefix.rstrip("/")  # "" for the root SPA, or a sub-path
    slug = prefix.strip("/").replace("/", "_") or "root"

    # 1) Built assets: <prefix>/static/frontend/<file>
    def _serve_asset(filename: str, _root: str = static_root):
        # Absolute directory so files resolve regardless of cwd / root_path.
        # Built assets use content-hashed filenames (cache-busted),
        # so a 1-hour cache is safe without stale-content risk.
        return send_from_directory(_root, filename, max_age=3600)

    app.add_url_rule(
        f"{prefix}/static/frontend/<path:filename>",
        endpoint=f"spa_asset_{slug}",
        view_func=_serve_asset,
    )
    limiter.exempt(_serve_asset)

    # 2) Client-side routes: <prefix> (bare) and <prefix>/<path:path>.
    def _spa_fallback(
        path: str | None = None,
        _root: str = static_root,
        _prefix: str = prefix,
    ):
        # Defensive: never serve the SPA for API paths.
        if path and path.startswith("api/"):
            return error("not_found", 404)

        if not has_frontend(_root):
            return _spa_not_built(_prefix)

        # Serve a real built file if the path maps to one; else index.html.
        if path and path != "index.html":
            requested = os.path.normpath(os.path.join(_root, path))
            root_abs = os.path.abspath(_root)
            requested_abs = os.path.abspath(requested)
            # Defense-in-depth: prevent path traversal outside static root.
            if not (
                requested_abs == root_abs
                or requested_abs.startswith(root_abs + os.sep)
            ):
                return error("not_found", 404)
            if os.path.isfile(requested):
                return _serve_asset(path, _root)

        return _serve_index(_root)

    # Bare prefix ("" or "/"). strict_slashes=False so both "/x" and "/x/"
    # work. For the root SPA this is "/".
    app.add_url_rule(
        prefix or "/",
        endpoint=f"spa_root_{slug}",
        view_func=_spa_fallback,
        defaults={"path": None},
        strict_slashes=False,
    )
    app.add_url_rule(
        f"{prefix}/<path:path>",
        endpoint=f"spa_path_{slug}",
        view_func=_spa_fallback,
        strict_slashes=False,
    )
    limiter.exempt(_spa_fallback)

    # 3) Uploads only for the root SPA (service-owned user files).
    if prefix == "":
        def _serve_upload(filename: str):
            upload_dir = os.path.join(app.static_folder or "static", "uploads")
            return send_from_directory(upload_dir, filename)

        app.add_url_rule(
            "/uploads/<path:filename>",
            endpoint="serve_upload",
            view_func=_serve_upload,
        )
        limiter.exempt(_serve_upload)


__all__ = ["has_frontend", "register_spa"]
