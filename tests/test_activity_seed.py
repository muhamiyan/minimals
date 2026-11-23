from __future__ import annotations

import json

import pytest

from app.activity.models import Activity
from app.activity.seed import ACTIVITIES_FILE, seed_activities
from framework.extensions import db


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(
        "app.activity.seed._download_cover", lambda filename: "/uploads/cover.jpg"
    )


def test_seed_activities_creates_once_and_skips(app, admin):
    expected = len(json.loads(ACTIVITIES_FILE.read_text(encoding="utf-8")))

    with app.app_context():
        assert seed_activities() == (expected, 0)
        assert db.session.query(Activity).count() == expected

        assert seed_activities() == (0, expected)
        assert db.session.query(Activity).count() == expected


def test_seed_activity_preserves_publication_date(app, admin):
    with app.app_context():
        seed_activities()

        activity = db.session.scalar(
            db.select(Activity).where(Activity.slug == "olimpiade-madrasah-indonesia")
        )

        assert activity is not None
        assert activity.status == "published"
        assert activity.published_on is not None
        assert activity.published_on.date().isoformat() == "2026-09-25"


def test_seed_activities_requires_admin(app):
    with app.app_context(), pytest.raises(RuntimeError, match="no_admin_for_seed"):
        seed_activities()
