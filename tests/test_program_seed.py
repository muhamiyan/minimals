from __future__ import annotations

import json

import pytest

from app.program.models import Program
from app.program.seed import PROGRAMS_FILE, seed_programs
from framework.extensions import db


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(
        "app.program.seed._download_cover", lambda filename: "/uploads/cover.jpg"
    )


def test_seed_programs_creates_once_and_skips(app, admin):
    expected = len(json.loads(PROGRAMS_FILE.read_text(encoding="utf-8")))

    with app.app_context():
        assert seed_programs() == (expected, 0)
        assert db.session.query(Program).count() == expected

        assert seed_programs() == (0, expected)
        assert db.session.query(Program).count() == expected


def test_seed_program_keeps_order_and_level(app, admin):
    with app.app_context():
        seed_programs()

        program = db.session.scalar(
            db.select(Program).where(Program.slug == "sma-nw-selaparang-kediri")
        )

        assert program is not None
        assert program.level == "SMA"
        assert program.order_index == 3
        assert program.status == "published"
        assert program.cover_image == "/uploads/cover.jpg"


def test_seed_programs_requires_admin(app):
    with app.app_context(), pytest.raises(RuntimeError, match="no_admin_for_seed"):
        seed_programs()
