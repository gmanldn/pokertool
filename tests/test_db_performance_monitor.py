#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite for Database Performance Monitor
============================================

Comprehensive tests for database query performance monitoring.

Module: tests.test_db_performance_monitor
Version: 1.0.0
"""

import pytest
import time
from datetime import datetime, timedelta

from pokertool.db_performance_monitor import (
    PerformanceConfig,
    QueryMetrics,
    QueryStats,
    DatabasePerformanceMonitor,
    performance_monitor,
    get_performance_report,
    reset_performance_stats,
    cleanup_old_performance_data
)


class TestQueryMetrics:
    """Test QueryMetrics dataclass."""

    def test_query_metrics_creation(self):
        """Test creating query metrics."""
        metrics = QueryMetrics(
            query_id="test_001",
            query_type="SELECT",
            query_pattern="get_user_by_id",
            execution_time=0.5,
            timestamp=datetime.now(),
            success=True,
            error=None,
            rows_affected=1,
            db_type="postgresql"
        )

        assert metrics.query_id == "test_001"
        assert metrics.query_type == "SELECT"
        assert metrics.execution_time == 0.5
        assert metrics.success is True

    def test_is_slow_property(self):
        """Test is_slow property."""
        # Fast query
        fast_metrics = QueryMetrics(
            query_id="fast",
            query_type="SELECT",
            query_pattern="test",
            execution_time=0.1,
            timestamp=datetime.now(),
            success=True
        )
        assert fast_metrics.is_slow is False

        # Slow query
        slow_metrics = QueryMetrics(
            query_id="slow",
            query_type="SELECT",
            query_pattern="test",
            execution_time=1.5,
            timestamp=datetime.now(),
            success=True
        )
        assert slow_metrics.is_slow is True

    def test_is_very_slow_property(self):
        """Test is_very_slow property."""
        # Regular slow query
        slow_metrics = QueryMetrics(
            query_id="slow",
            query_type="SELECT",
            query_pattern="test",
            execution_time=2.0,
            timestamp=datetime.now(),
            success=True
        )
        assert slow_metrics.is_very_slow is False

        # Very slow query
        very_slow_metrics = QueryMetrics(
            query_id="very_slow",
            query_type="SELECT",
            query_pattern="test",
            execution_time=6.0,
            timestamp=datetime.now(),
            success=True
        )
        assert very_slow_metrics.is_very_slow is True


class TestQueryStats:
    """Test QueryStats aggregation."""

    def test_query_stats_initialization(self):
        """Test QueryStats initialization."""
        stats = QueryStats(query_pattern="get_all_users")

        assert stats.query_pattern == "get_all_users"
        assert stats.total_executions == 0
        assert stats.total_time == 0.0
        assert stats.min_time == float('inf')
        assert stats.max_time == 0.0

    def test_update_stats_with_metrics(self):
        """Test updating stats with new metrics."""
        stats = QueryStats(query_pattern="test_query")

        metrics1 = QueryMetrics(
            query_id="001",
            query_type="SELECT",
            query_pattern="test_query",
            execution_time=0.1,
            timestamp=datetime.now(),
            success=True
        )

        metrics2 = QueryMetrics(
            query_id="002",
            query_type="SELECT",
            query_pattern="test_query",
            execution_time=0.2,
            timestamp=datetime.now(),
            success=True
        )

        stats.update(metrics1)
        assert stats.total_executions == 1
        assert stats.total_time == 0.1
        assert stats.min_time == 0.1
        assert stats.max_time == 0.1

        stats.update(metrics2)
        assert stats.total_executions == 2
        assert stats.total_time == 0.3
        assert stats.min_time == 0.1
        assert stats.max_time == 0.2
        assert stats.avg_time == 0.15

    def test_slow_query_counting(self):
        """Test slow query counting."""
        stats = QueryStats(query_pattern="slow_query")

        # Add fast query
        fast_metrics = QueryMetrics(
            query_id="fast",
            query_type="SELECT",
            query_pattern="slow_query",
            execution_time=0.1,
            timestamp=datetime.now(),
            success=True
        )
        stats.update(fast_metrics)
        assert stats.slow_count == 0

        # Add slow query
        slow_metrics = QueryMetrics(
            query_id="slow",
            query_type="SELECT",
            query_pattern="slow_query",
            execution_time=1.5,
            timestamp=datetime.now(),
            success=True
        )
        stats.update(slow_metrics)
        assert stats.slow_count == 1

    def test_error_counting(self):
        """Test error counting."""
        stats = QueryStats(query_pattern="error_query")

        # Add successful query
        success_metrics = QueryMetrics(
            query_id="success",
            query_type="SELECT",
            query_pattern="error_query",
            execution_time=0.1,
            timestamp=datetime.now(),
            success=True
        )
        stats.update(success_metrics)
        assert stats.error_count == 0

        # Add failed query
        error_metrics = QueryMetrics(
            query_id="error",
            query_type="SELECT",
            query_pattern="error_query",
            execution_time=0.1,
            timestamp=datetime.now(),
            success=False,
            error="Database error"
        )
        stats.update(error_metrics)
        assert stats.error_count == 1

    def test_percentile_calculations(self):
        """Test percentile calculations."""
        stats = QueryStats(query_pattern="percentile_test")

        # Add multiple queries with varying execution times
        execution_times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        for i, exec_time in enumerate(execution_times):
            metrics = QueryMetrics(
                query_id=f"query_{i}",
                query_type="SELECT",
                query_pattern="percentile_test",
                execution_time=exec_time,
                timestamp=datetime.now(),
                success=True
            )
            stats.update(metrics)

        assert stats.total_executions == 10
        assert stats.median_time == 0.5
        assert stats.p95_time == 0.9
        assert stats.p99_time == 1.0


class TestDatabasePerformanceMonitor:
    """Test DatabasePerformanceMonitor class."""

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        monitor = DatabasePerformanceMonitor()

        assert monitor._query_counter == 0
        assert len(monitor._stats) == 0
        assert len(monitor._recent_queries) == 0

    def test_track_query_decorator(self):
        """Test track_query decorator."""
        monitor = DatabasePerformanceMonitor()

        @monitor.track_query("SELECT", "sqlite")
        def test_function():
            time.sleep(0.01)
            return "result"

        # Execute function
        result = test_function()

        assert result == "result"
        assert len(monitor._stats) == 1
        assert "test_function" in monitor._stats

    def test_track_query_decorator_with_exception(self):
        """Test track_query decorator with exception."""
        monitor = DatabasePerformanceMonitor()

        @monitor.track_query("SELECT")
        def failing_function():
            raise ValueError("Test error")

        # Execute function (should raise exception)
        with pytest.raises(ValueError):
            failing_function()

        # Metrics should still be recorded
        assert len(monitor._stats) == 1
        stats = monitor._stats["failing_function"]
        assert stats.error_count == 1

    def test_track_context_manager(self):
        """Test track context manager."""
        monitor = DatabasePerformanceMonitor()

        with monitor.track("INSERT", "create_user", "postgresql"):
            time.sleep(0.01)

        assert len(monitor._stats) == 1
        assert "create_user" in monitor._stats

    def test_track_context_manager_with_exception(self):
        """Test track context manager with exception."""
        monitor = DatabasePerformanceMonitor()

        with pytest.raises(RuntimeError):
            with monitor.track("UPDATE", "update_user"):
                raise RuntimeError("Update failed")

        # Metrics should still be recorded
        assert len(monitor._stats) == 1
        stats = monitor._stats["update_user"]
        assert stats.error_count == 1

    def test_get_performance_report(self):
        """Test getting performance report."""
        monitor = DatabasePerformanceMonitor()

        # Add some test queries
        @monitor.track_query("SELECT")
        def fast_query():
            time.sleep(0.01)

        @monitor.track_query("SELECT")
        def slow_query():
            time.sleep(0.1)

        fast_query()
        slow_query()

        report = monitor.get_performance_report()

        assert report["total_queries"] == 2
        assert report["unique_query_patterns"] == 2
        assert report["total_time_seconds"] > 0
        assert "slowest_queries" in report
        assert "most_frequent_queries" in report

    def test_slow_query_detection_in_report(self):
        """Test slow query detection in performance report."""
        monitor = DatabasePerformanceMonitor()

        # Create a slow query
        with monitor.track("SELECT", "very_slow_query"):
            time.sleep(1.1)  # Exceeds SLOW_QUERY_THRESHOLD

        report = monitor.get_performance_report()

        assert report["slow_queries_count"] > 0
        assert len(report["recent_slow_queries"]) > 0

    def test_get_query_stats(self):
        """Test getting stats for specific query pattern."""
        monitor = DatabasePerformanceMonitor()

        with monitor.track("SELECT", "specific_query"):
            time.sleep(0.01)

        stats = monitor.get_query_stats("specific_query")

        assert stats is not None
        assert stats.query_pattern == "specific_query"
        assert stats.total_executions == 1

    def test_get_query_stats_nonexistent(self):
        """Test getting stats for nonexistent query."""
        monitor = DatabasePerformanceMonitor()

        stats = monitor.get_query_stats("nonexistent")

        assert stats is None

    def test_get_all_stats(self):
        """Test getting all query statistics."""
        monitor = DatabasePerformanceMonitor()

        with monitor.track("SELECT", "query1"):
            pass

        with monitor.track("INSERT", "query2"):
            pass

        all_stats = monitor.get_all_stats()

        assert len(all_stats) == 2
        assert "query1" in all_stats
        assert "query2" in all_stats

    def test_reset_stats(self):
        """Test resetting statistics."""
        monitor = DatabasePerformanceMonitor()

        with monitor.track("SELECT", "test_query"):
            pass

        assert len(monitor._stats) == 1

        monitor.reset_stats()

        assert len(monitor._stats) == 0
        assert monitor._query_counter == 0

    def test_cleanup_old_stats(self):
        """Test cleaning up old statistics."""
        monitor = DatabasePerformanceMonitor()

        # Create metrics with old timestamp
        old_metrics = QueryMetrics(
            query_id="old_001",
            query_type="SELECT",
            query_pattern="old_query",
            execution_time=0.1,
            timestamp=datetime.now() - timedelta(hours=25),
            success=True
        )

        # Add to stats manually
        monitor._stats["old_query"] = QueryStats(query_pattern="old_query")
        monitor._stats["old_query"].update(old_metrics)
        monitor._recent_queries.append(old_metrics)

        # Create recent metrics
        with monitor.track("SELECT", "recent_query"):
            pass

        # Clean up old stats (default 24 hours)
        monitor.cleanup_old_stats()

        # Old query should be removed
        assert "old_query" not in monitor._stats
        # Recent query should remain
        assert "recent_query" in monitor._stats

    def test_concurrent_tracking(self):
        """Test concurrent query tracking (thread safety)."""
        import threading

        monitor = DatabasePerformanceMonitor()

        def run_queries():
            for i in range(10):
                with monitor.track("SELECT", f"thread_query"):
                    time.sleep(0.001)

        threads = [threading.Thread(target=run_queries) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        stats = monitor.get_query_stats("thread_query")
        assert stats.total_executions == 50  # 5 threads * 10 queries

    def test_query_history_limit(self):
        """Test that query history is limited."""
        monitor = DatabasePerformanceMonitor()
        original_limit = PerformanceConfig.MAX_QUERY_HISTORY

        # Set low limit for testing
        PerformanceConfig.MAX_QUERY_HISTORY = 10

        try:
            # Add more queries than the limit
            for i in range(20):
                with monitor.track("SELECT", f"query_{i}"):
                    pass

            # Should only keep last MAX_QUERY_HISTORY queries
            assert len(monitor._recent_queries) <= 10

        finally:
            # Restore original limit
            PerformanceConfig.MAX_QUERY_HISTORY = original_limit


class TestGlobalMonitor:
    """Test global monitor instance and utility functions."""

    def test_global_monitor_instance(self):
        """Test global monitor instance exists."""
        assert performance_monitor is not None
        assert isinstance(performance_monitor, DatabasePerformanceMonitor)

    def test_get_performance_report_function(self):
        """Test global get_performance_report function."""
        report = get_performance_report()

        assert isinstance(report, dict)
        assert "total_queries" in report

    def test_reset_performance_stats_function(self):
        """Test global reset function."""
        # Should not raise exception
        reset_performance_stats()

    def test_cleanup_old_performance_data_function(self):
        """Test global cleanup function."""
        # Should not raise exception
        cleanup_old_performance_data(hours=48)


class TestPerformanceConfig:
    """Test PerformanceConfig class."""

    def test_config_thresholds(self):
        """Test configuration thresholds."""
        assert PerformanceConfig.SLOW_QUERY_THRESHOLD == 1.0
        assert PerformanceConfig.VERY_SLOW_QUERY_THRESHOLD == 5.0

    def test_config_monitoring_flags(self):
        """Test monitoring configuration flags."""
        assert PerformanceConfig.ENABLE_MONITORING is True
        assert isinstance(PerformanceConfig.LOG_SLOW_QUERIES, bool)
        assert isinstance(PerformanceConfig.COLLECT_STATS, bool)


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_database_query_simulation(self):
        """Test simulating real database queries."""
        monitor = DatabasePerformanceMonitor()

        @monitor.track_query("SELECT", "postgresql")
        def get_users():
            time.sleep(0.05)
            return [{"id": 1, "name": "User1"}]

        @monitor.track_query("INSERT", "postgresql")
        def create_user():
            time.sleep(0.02)
            return {"id": 2}

        @monitor.track_query("UPDATE", "postgresql")
        def update_user():
            time.sleep(0.03)
            return True

        # Simulate workload
        for _ in range(10):
            get_users()

        for _ in range(5):
            create_user()

        for _ in range(3):
            update_user()

        report = monitor.get_performance_report()

        assert report["total_queries"] == 18
        assert report["unique_query_patterns"] == 3
        assert len(report["most_frequent_queries"]) > 0

        # get_users should be most frequent
        most_frequent = report["most_frequent_queries"][0]
        assert most_frequent["pattern"] == "get_users"
        assert most_frequent["executions"] == 10

    def test_error_handling_in_queries(self):
        """Test error handling and tracking."""
        monitor = DatabasePerformanceMonitor()

        @monitor.track_query("SELECT")
        def flaky_query(should_fail=False):
            if should_fail:
                raise ConnectionError("Database connection lost")
            return "success"

        # Successful queries
        for _ in range(5):
            flaky_query(should_fail=False)

        # Failed queries
        for _ in range(2):
            with pytest.raises(ConnectionError):
                flaky_query(should_fail=True)

        stats = monitor.get_query_stats("flaky_query")
        assert stats.total_executions == 7
        assert stats.error_count == 2

        report = monitor.get_performance_report()
        assert report["error_count"] == 2
        assert report["error_rate"] == pytest.approx(2/7, rel=0.01)

    def test_performance_degradation_detection(self):
        """Test detecting performance degradation."""
        monitor = DatabasePerformanceMonitor()

        # Simulate query getting slower over time
        @monitor.track_query("SELECT")
        def degrading_query(delay):
            time.sleep(delay)
            return "result"

        # Initially fast
        for _ in range(5):
            degrading_query(0.01)

        # Then slower
        for _ in range(5):
            degrading_query(0.1)

        stats = monitor.get_query_stats("degrading_query")

        # Should detect slow queries
        assert stats.slow_count == 0  # 0.1 is below SLOW_QUERY_THRESHOLD (1.0)
        assert stats.min_time < stats.max_time  # Performance variation detected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
