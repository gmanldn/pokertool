"""Tests for the performance profiler utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.performance_profiler import AlertRule, PerformanceProfiler


def create_profiler(tmp_path: Path) -> PerformanceProfiler:
    storage = tmp_path / "profiler"
    return PerformanceProfiler(storage_dir=storage)


def test_snapshot_capture_and_alerts(tmp_path):
    profiler = create_profiler(tmp_path)
    profiler.add_alert_rule(AlertRule(metric="cpu_percent", threshold=80.0, comparison=">", message="CPU spike"))
    profiler.add_alert_rule(AlertRule(metric="latency_ms", threshold=200.0, comparison=">", message="Latency high"))

    profiler.capture_snapshot(cpu_percent=45.0, memory_mb=512.0, thread_count=12, latency_ms=80.0)
    profiler.capture_snapshot(cpu_percent=92.0, memory_mb=640.0, thread_count=14, latency_ms=150.0)
    profiler.capture_snapshot(cpu_percent=70.0, memory_mb=1500.0, thread_count=11, latency_ms=250.0)

    report = profiler.generate_report()
    assert report.snapshots == 3
    assert report.avg_cpu > 60
    assert any("CPU spike" in alert for alert in report.alerts_triggered)
    assert any(suggestion.category == "memory" for suggestion in report.suggestions)

    export_path = profiler.export_history()
    assert export_path.exists()


def test_clear_and_baseline_suggestion(tmp_path):
    profiler = create_profiler(tmp_path)
    profiler.capture_snapshot(cpu_percent=20.0, memory_mb=300.0, thread_count=8, latency_ms=50.0)
    profiler.capture_snapshot(cpu_percent=25.0, memory_mb=280.0, thread_count=9, latency_ms=60.0)
    report = profiler.generate_report()
    assert report.suggestions and report.suggestions[0].category == "baseline"

    profiler.clear()
    empty_report = profiler.generate_report()
    assert empty_report.snapshots == 0
