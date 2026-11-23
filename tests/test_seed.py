from __future__ import annotations

import json

import pytest

from app.blog.models import BlogPost
from app.blog.seed import ARTICLES_FILE, seed_articles
from framework.extensions import db


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(
        "app.blog.seed._download_cover", lambda filename: "/uploads/cover.jpg"
    )


def test_seed_creates_all_articles_once(app, admin):
    expected = len(json.loads(ARTICLES_FILE.read_text(encoding="utf-8")))

    with app.app_context():
        assert seed_articles() == (expected, 0)
        assert db.session.query(BlogPost).count() == expected

        assert seed_articles() == (0, expected)
        assert db.session.query(BlogPost).count() == expected


def test_seed_preserves_publication_date(app, admin):
    with app.app_context():
        seed_articles()

        post = db.session.scalar(
            db.select(BlogPost).where(
                BlogPost.slug == "peringatan-hut-ri-ke-78-kamis-17-agustus-2023"
            )
        )

        assert post is not None
        assert post.status == "published"
        assert post.published_on is not None
        assert post.published_on.date().isoformat() == "2023-08-17"
        assert post.cover_image == "/uploads/cover.jpg"


def test_seed_requires_admin(app):
    with app.app_context(), pytest.raises(RuntimeError, match="no_admin_for_seed"):
        seed_articles()
