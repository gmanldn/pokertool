from datetime import datetime

from fastapi.testclient import TestClient

from pokertool.api import APIServices, PokerToolAPI
from pokertool.rum_metrics import RUMMetricsStore


def test_rum_ingest_and_summary(tmp_path):
    services = APIServices()
    services._rum_metrics = RUMMetricsStore(storage_dir=tmp_path)
    class _DummyLimiter:
        enabled = False

        def limit(self, *_args, **_kwargs):
            def decorator(func):
                return func
            return decorator
    services._limiter = _DummyLimiter()

    api = PokerToolAPI(services=services)
    client = TestClient(api.app)

    payload = {
        "metric": "LCP",
        "value": 2350.0,
        "rating": "good",
        "session_id": "session-test",
        "page": "/dashboard",
        "client_timestamp": datetime.utcnow().isoformat(),
    }

    response = client.post("/api/rum/metrics", json=payload, headers={"User-Agent": "pytest"})
    assert response.status_code == 202

    summary_response = client.get(
        "/api/rum/summary",
        headers={"Authorization": "Bearer demo_token"},
    )
    assert summary_response.status_code == 200
    summary = summary_response.json()

    assert summary["total_samples"] == 1
    assert summary["pages"]["/dashboard"] == 1
    metric_info = next(item for item in summary["metrics"] if item["metric"] == "LCP")
    assert metric_info["samples"] == 1
    assert metric_info["ratings"]["good"] == 1
