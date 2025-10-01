"""Tests for database optimization utilities."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.database_optimization import DatabaseOptimizationManager


def create_manager(tmp_path: Path) -> DatabaseOptimizationManager:
    storage = tmp_path / "db_opt"
    return DatabaseOptimizationManager(storage_dir=storage)


def test_query_cache_and_monitoring(tmp_path):
    manager = create_manager(tmp_path)

    calls = {"count": 0}

    def loader():
        calls["count"] += 1
        return {"rows": [1, 2, 3]}

    result_one = manager.cached_query("key", loader, ttl_seconds=2)
    assert result_one == {"rows": [1, 2, 3]}
    assert calls["count"] == 1

    result_two = manager.cached_query("key", loader, ttl_seconds=2)
    assert result_two == result_one
    assert calls["count"] == 1

    time.sleep(2.1)
    _ = manager.cached_query("key", loader, ttl_seconds=1)
    assert calls["count"] == 2

    manager.monitor_query(
        name="player_lookup",
        sql="SELECT * FROM players WHERE players.id = %s",
        parameters=(42,),
        duration_ms=220.0,
        rows=1,
        success=True,
    )

    assert manager.monitor.slow_queries()
    summary = manager.optimization_summary()
    assert summary["queries"]["count"] == 1


def test_archiving_and_recommendations(tmp_path):
    manager = create_manager(tmp_path)

    manager.monitor_query(
        name="hand_search",
        sql="SELECT hand_id FROM hands WHERE hands.player_id = %s AND hands.stage = %s",
        parameters=(10, "flop"),
        duration_ms=180.0,
        rows=25,
        success=True,
    )
    manager.monitor_query(
        name="hand_search",
        sql="SELECT hand_id FROM hands WHERE hands.player_id = %s AND hands.stage = %s",
        parameters=(10, "turn"),
        duration_ms=190.0,
        rows=20,
        success=True,
    )
    manager.monitor_query(
        name="session_lookup",
        sql="SELECT * FROM sessions WHERE sessions.date = %s",
        parameters=("2025-10-03",),
        duration_ms=210.0,
        rows=5,
        success=True,
    )

    archive_path = manager.archive_table("old_sessions", [{"id": 1, "profit": 120.0}])
    assert archive_path.exists()

    hints = manager.optimize_query("SELECT * FROM sessions")
    assert any("SELECT *" in hint for hint in hints)

    recommendations = manager.optimization_summary()["index_recommendations"]
    assert any("hands(player_id)" in rec for rec in recommendations)
