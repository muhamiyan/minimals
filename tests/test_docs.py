"""Keep the documented endpoint table in sync with the served routes."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
README = REPO / "README.md"

TABLE_ROW = re.compile(r"^\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*([/\w{}<>:.-]+)\s*\|")
PARAM = re.compile(r"<[^>]+>|:[A-Za-z_]\w*")
FRAMEWORK_ENDPOINTS = {"static", "serve_upload"}


def canonical(path: str) -> str:
    """Reduce a route to its shape: parameters become ``{}``."""
    return PARAM.sub("{}", path).rstrip("/") or "/"


def documented_endpoints(doc: Path) -> set[tuple[str, str]]:
    rows: set[tuple[str, str]] = set()
    for line in doc.read_text(encoding="utf-8").splitlines():
        match = TABLE_ROW.match(line)
        if match:
            rows.add((match.group(1), canonical(match.group(2))))
    return rows


def served_endpoints(app) -> set[tuple[str, str]]:
    """API routes served by the app, excluding framework-owned static/SPA routes."""
    rows: set[tuple[str, str]] = set()
    for rule in app.url_map.iter_rules():
        if rule.endpoint in FRAMEWORK_ENDPOINTS or rule.endpoint.startswith("spa_"):
            continue
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            rows.add((method, canonical(str(rule))))
    return rows


def test_readme_endpoint_table_matches_url_map(app):
    assert documented_endpoints(README) == served_endpoints(app)
