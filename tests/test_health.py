def test_health_reports_ok(client):
    body = client.get("/health").get_json()
    assert body["status"] == "ok"
    assert {"metrics", "databasePool"} <= body.keys()


def test_health_metrics_are_camel_case(client):
    metrics = client.get("/health").get_json()["metrics"]
    assert {
        "totalRequests",
        "totalErrors",
        "errorRate",
        "avgResponseMs",
        "endpoints",
    } <= metrics.keys()
    assert not [key for key in metrics if key.startswith("total_")]
    assert "avg_ms" not in metrics


def test_health_pool_is_camel_case(client):
    pool = client.get("/health").get_json()["databasePool"]
    assert {"poolClass", "size", "checkedOut", "overflow"} <= pool.keys()


def test_ready_reports_healthy(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_metrics_track_requests(client):
    client.get("/health")
    endpoints = client.get("/health").get_json()["metrics"]["endpoints"]

    assert "GET /health" in endpoints
    assert endpoints["GET /health"]["count"] >= 2
    assert "avgMs" in endpoints["GET /health"]
    assert "avg_ms" not in endpoints["GET /health"]


class _UnavailableSession:
    def execute(self, *args, **kwargs):
        raise RuntimeError("database is unreachable")

    def remove(self):
        pass


def test_ready_reports_503_when_database_is_unavailable(app, monkeypatch):
    from framework.extensions import db

    monkeypatch.setattr(db, "session", _UnavailableSession())

    response = app.test_client().get("/ready")

    assert response.status_code == 503
    assert response.get_json() == {"message": "not_ready"}


def test_health_and_ready_survive_pools_without_stats(app, monkeypatch):
    from framework.extensions import db

    class _PoolWithoutStats:
        """A pool that can hand out connections but exposes no statistics."""

        def __init__(self, inner):
            self._inner = inner

        def __getattr__(self, name):
            if name in ("size", "checkedout", "overflow"):
                raise AttributeError(name)
            return getattr(self._inner, name)

    with app.app_context():
        engine = db.engine
    monkeypatch.setattr(engine, "pool", _PoolWithoutStats(engine.pool))

    client = app.test_client()
    health = client.get("/health")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert ready.status_code == 200
    assert "databasePool" not in health.get_json()
    assert "databasePool" not in ready.get_json()
