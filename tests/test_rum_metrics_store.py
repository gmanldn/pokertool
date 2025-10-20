from datetime import datetime, timedelta

from pokertool.rum_metrics import RUMMetricsStore


def test_record_and_summarise(tmp_path):
    store = RUMMetricsStore(storage_dir=tmp_path)
    now = datetime.utcnow().isoformat()

    store.record_metric({
        "metric": "LCP",
        "value": 2100,
        "rating": "good",
        "page": "/dashboard",
        "session_id": "session-a",
        "received_at": now,
    })
    store.record_metric({
        "metric": "LCP",
        "value": 3400,
        "rating": "needs-improvement",
        "page": "/dashboard",
        "session_id": "session-a",
        "received_at": now,
    })
    store.record_metric({
        "metric": "CLS",
        "value": 0.04,
        "rating": "good",
        "page": "/settings",
        "session_id": "session-b",
        "received_at": now,
    })

    summary = store.summarise(hours=1)

    assert summary["total_samples"] == 3
    assert summary["pages"]["/dashboard"] == 2
    assert summary["pages"]["/settings"] == 1

    lcp_summary = next(item for item in summary["metrics"] if item["metric"] == "LCP")
    assert lcp_summary["samples"] == 2
    assert lcp_summary["ratings"]["good"] == 1
    assert lcp_summary["ratings"]["needs-improvement"] == 1
    assert lcp_summary["p95"] >= 3400

    cls_summary = next(item for item in summary["metrics"] if item["metric"] == "CLS")
    assert cls_summary["samples"] == 1
    assert cls_summary["ratings"]["good"] == 1


def test_load_recent_filters_old_entries(tmp_path):
    store = RUMMetricsStore(storage_dir=tmp_path)
    old_time = (datetime.utcnow() - timedelta(hours=50)).isoformat()
    recent_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()

    store.record_metric({
        "metric": "TTFB",
        "value": 120,
        "rating": "good",
        "received_at": old_time,
    })
    store.record_metric({
        "metric": "TTFB",
        "value": 180,
        "rating": "good",
        "received_at": recent_time,
    })

    recent = store.load_recent(hours=24)
    assert len(recent) == 1
    assert recent[0]["value"] == 180
