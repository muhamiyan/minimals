"""Behavioural check: default limits cover API routes only.

Runs in a subprocess because flask-limiter's default limits are bound to the
app at creation time from config — the parent suite uses a deliberately huge
`RATE_LIMIT_DEFAULT`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SCRIPT = r"""
import json
import os
import tempfile

tmp = tempfile.mkdtemp(prefix="rlsub_")
out = os.path.join(os.environ["RL_OUT"], "result.json")
os.environ.update({
    "DATABASE_URL": "sqlite:///" + os.path.join(tmp, "sub.db").replace("\\", "/"),
    "CSRF_ENABLED": "true",
    "MIGRATE_ON_BOOT": "false",
    "RATE_LIMIT_DEFAULT": "2/hour",
    "RATE_LIMIT_AUTH": "10000/hour",
    "RATE_LIMIT_STORAGE_URL": "",
    "TALISMAN_ENABLED": "false",
    "FORCE_HTTPS": "false",
    "TRUSTED_PROXY": "false",
    "SECRET_KEY": "x" * 32,
    "LOG_FILE": os.path.join(tmp, "sub.log"),
})

from app.create_app import create_app
from app.auth.models import Role
from framework.extensions import db

app = create_app()
app.config["TESTING"] = True
with app.app_context():
    db.create_all()
    if db.session.scalar(db.select(Role).where(Role.name == "Member")) is None:
        db.session.add(Role(name="Member"))
        db.session.commit()

client = app.test_client()


def statuses(path, n=5):
    return [client.get(path).status_code for _ in range(n)]


result = {
    "spa_index": statuses("/"),
    "spa_route": statuses("/client/route"),
    "spa_asset": statuses("/static/frontend/does-not-exist.js"),
    "uploads": statuses("/uploads/missing.png"),
    "health": statuses("/health"),
    "ready": statuses("/ready"),
    "api": statuses("/api/v1/csrf"),
}
with open(out, "w", encoding="utf-8") as fh:
    fh.write(json.dumps(result))
"""


AUTH_SCRIPT = r"""
import json
import os
import tempfile

tmp = tempfile.mkdtemp(prefix="rlauth_")
out = os.path.join(os.environ["RL_OUT"], "auth.json")
os.environ.update({
    "DATABASE_URL": "sqlite:///" + os.path.join(tmp, "sub.db").replace("\\", "/"),
    "CSRF_ENABLED": "true",
    "MIGRATE_ON_BOOT": "false",
    "RATE_LIMIT_DEFAULT": "10000/hour",
    "RATE_LIMIT_AUTH": "2/hour",
    "RATE_LIMIT_STORAGE_URL": "",
    "TALISMAN_ENABLED": "false",
    "FORCE_HTTPS": "false",
    "TRUSTED_PROXY": "false",
    "SECRET_KEY": "x" * 32,
    "LOG_FILE": os.path.join(tmp, "sub.log"),
})

from app.create_app import create_app
from framework.extensions import db

app = create_app()
app.config["TESTING"] = True
with app.app_context():
    db.create_all()

client = app.test_client()
client.environ_base["HTTP_X_CSRFTOKEN"] = client.get("/api/v1/csrf").get_json()["csrfToken"]


def post_statuses(path, n=5):
    return [
        client.post(
            path, json={"identifier": "ghost", "password": "nope"}
        ).status_code
        for _ in range(n)
    ]


with open(out, "w", encoding="utf-8") as fh:
    fh.write(json.dumps({
        "login": post_statuses("/api/v1/auth/login"),
        "register": post_statuses("/api/v1/auth/register"),
    }))
"""


def test_default_limits_exempt_spa_health_and_uploads():
    out_dir = tempfile.mkdtemp(prefix="rlparent_")
    env = dict(os.environ, RL_OUT=out_dir)
    proc = subprocess.run(
        [sys.executable, "-c", SCRIPT],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]

    result = json.loads((Path(out_dir) / "result.json").read_text(encoding="utf-8"))

    assert result["spa_index"] == [200] * 5
    assert result["spa_route"] == [200] * 5
    assert result["spa_asset"] == [404] * 5
    assert result["uploads"] == [404] * 5
    assert result["health"] == [200] * 5
    assert result["ready"] == [200] * 5
    assert result["api"] == [200, 200, 429, 429, 429]


def test_auth_endpoints_honor_the_auth_rate_limit():
    out_dir = tempfile.mkdtemp(prefix="rlparent_")
    env = dict(os.environ, RL_OUT=out_dir)
    proc = subprocess.run(
        [sys.executable, "-c", AUTH_SCRIPT],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]

    result = json.loads((Path(out_dir) / "auth.json").read_text(encoding="utf-8"))

    assert result["login"] == [401, 401, 429, 429, 429]
    assert result["register"] == [400, 400, 429, 429, 429]
