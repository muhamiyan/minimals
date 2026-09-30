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
