#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Query Performance Monitoring
======================================

Monitors and logs database query performance to identify slow queries,
optimize database operations, and track performance trends over time.

Features:
- Query execution time tracking
- Slow query detection and logging
- Query pattern analysis
- Performance metrics collection
- Automatic query optimization suggestions

Version: 86.5.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import time
import logging
import functools
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

class PerformanceConfig:
    """Configuration for database performance monitoring."""

    # Slow query thresholds (in seconds)
    SLOW_QUERY_THRESHOLD = 1.0  # Warn if query takes > 1s
    VERY_SLOW_QUERY_THRESHOLD = 5.0  # Critical if query takes > 5s

    # Monitoring settings
    ENABLE_MONITORING = True
    LOG_ALL_QUERIES = False  # Set to True for debugging
    LOG_SLOW_QUERIES = True
    COLLECT_STATS = True

    # Stats retention
    MAX_QUERY_HISTORY = 1000  # Keep last N queries in memory
    STATS_RETENTION_HOURS = 24  # Keep stats for 24 hours

    # Performance alerts
    ENABLE_ALERTS = True
    ALERT_ON_N_PLUS_ONE = True  # Detect N+1 query patterns


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_id: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE
    query_pattern: str  # Normalized query without parameters
    execution_time: float  # Seconds
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    rows_affected: Optional[int] = None
    db_type: str = "unknown"  # sqlite, postgresql
    stack_trace: Optional[str] = None

    @property
    def is_slow(self) -> bool:
        """Check if query is slow."""
        return self.execution_time > PerformanceConfig.SLOW_QUERY_THRESHOLD

    @property
    def is_very_slow(self) -> bool:
        """Check if query is very slow."""
        return self.execution_time > PerformanceConfig.VERY_SLOW_QUERY_THRESHOLD


@dataclass
class QueryStats:
    """Aggregated statistics for a query pattern."""
    query_pattern: str
    total_executions: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    median_time: float = 0.0
    p95_time: float = 0.0
    p99_time: float = 0.0
    slow_count: int = 0
    error_count: int = 0
    execution_times: List[float] = field(default_factory=list)
    last_executed: Optional[datetime] = None

    def update(self, metrics: QueryMetrics):
        """Update stats with new query metrics."""
        self.total_executions += 1
        self.total_time += metrics.execution_time
        self.min_time = min(self.min_time, metrics.execution_time)
        self.max_time = max(self.max_time, metrics.execution_time)
        self.last_executed = metrics.timestamp

        if metrics.is_slow:
            self.slow_count += 1

        if not metrics.success:
            self.error_count += 1

        # Keep execution times for percentile calculations
        self.execution_times.append(metrics.execution_time)

        # Limit history size
        if len(self.execution_times) > PerformanceConfig.MAX_QUERY_HISTORY:
            self.execution_times.pop(0)

        # Calculate statistics
        self._calculate_stats()

    def _calculate_stats(self):
        """Calculate average and percentile statistics."""
        if not self.execution_times:
            return

        self.avg_time = statistics.mean(self.execution_times)

        if len(self.execution_times) >= 2:
            self.median_time = statistics.median(self.execution_times)
            sorted_times = sorted(self.execution_times)
            n = len(sorted_times)
            self.p95_time = sorted_times[int(n * 0.95)]
            self.p99_time = sorted_times[int(n * 0.99)]


# ============================================================================
# Performance Monitor
# ============================================================================

class DatabasePerformanceMonitor:
    """
    Monitors database query performance and provides insights.

    Usage:
        monitor = DatabasePerformanceMonitor()

        # Decorate database methods
        @monitor.track_query("SELECT")
        def execute_query(query):
            ...

        # Or use context manager
        with monitor.track("SELECT", "get_user_by_id"):
            result = db.execute(query)

        # Get performance report
        report = monitor.get_performance_report()
    """

    def __init__(self):
        self._stats: Dict[str, QueryStats] = {}
        self._recent_queries: List[QueryMetrics] = []
        self._lock = threading.Lock()
        self._query_counter = 0
        self._start_time = datetime.now()

    def track_query(
        self,
        query_type: str = "UNKNOWN",
        db_type: str = "unknown"
    ) -> Callable:
        """
        Decorator to track query performance.

        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            db_type: Database type (sqlite, postgresql)

        Returns:
            Decorated function

        Example:
            @monitor.track_query("SELECT", "postgresql")
            def get_user(user_id):
                return db.execute("SELECT * FROM users WHERE id = ?", user_id)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                query_id = f"{func.__name__}_{self._get_next_id()}"
                query_pattern = func.__name__  # Simplified pattern

                start_time = time.time()
                success = True
                error = None
                rows_affected = None

                try:
                    result = func(*args, **kwargs)

                    # Try to extract rows affected
                    if hasattr(result, 'rowcount'):
                        rows_affected = result.rowcount

                    return result

                except Exception as e:
                    success = False
                    error = str(e)
                    raise

                finally:
                    execution_time = time.time() - start_time

                    # Create metrics
                    metrics = QueryMetrics(
                        query_id=query_id,
                        query_type=query_type,
                        query_pattern=query_pattern,
                        execution_time=execution_time,
                        timestamp=datetime.now(),
                        success=success,
                        error=error,
                        rows_affected=rows_affected,
                        db_type=db_type
                    )

                    # Record metrics
                    self._record_metrics(metrics)

            return wrapper
        return decorator

    def track(self, query_type: str, query_pattern: str, db_type: str = "unknown"):
        """
        Context manager for tracking query performance.

        Args:
            query_type: Type of query
            query_pattern: Pattern/name of query
            db_type: Database type

        Example:
            with monitor.track("SELECT", "get_all_users"):
                users = db.execute("SELECT * FROM users")
        """
        return _QueryTracker(self, query_type, query_pattern, db_type)

    def _get_next_id(self) -> int:
        """Get next query ID."""
        with self._lock:
            self._query_counter += 1
            return self._query_counter

    def _record_metrics(self, metrics: QueryMetrics):
        """Record query metrics."""
        if not PerformanceConfig.ENABLE_MONITORING:
            return

        with self._lock:
            # Add to recent queries
            self._recent_queries.append(metrics)

            # Limit recent queries size
            if len(self._recent_queries) > PerformanceConfig.MAX_QUERY_HISTORY:
                self._recent_queries.pop(0)

            # Update or create stats for this query pattern
            if metrics.query_pattern not in self._stats:
                self._stats[metrics.query_pattern] = QueryStats(
                    query_pattern=metrics.query_pattern
                )

            self._stats[metrics.query_pattern].update(metrics)

        # Log slow queries
        if PerformanceConfig.LOG_SLOW_QUERIES and metrics.is_slow:
            level = logging.CRITICAL if metrics.is_very_slow else logging.WARNING
            logger.log(
                level,
                f"Slow query detected: {metrics.query_pattern} took {metrics.execution_time:.3f}s"
            )

        # Log all queries (for debugging)
        if PerformanceConfig.LOG_ALL_QUERIES:
            logger.debug(
                f"Query: {metrics.query_pattern} ({metrics.query_type}) "
                f"took {metrics.execution_time:.3f}s"
            )

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report.

        Returns:
            Dictionary with performance statistics
        """
        with self._lock:
            total_queries = sum(stats.total_executions for stats in self._stats.values())
            total_time = sum(stats.total_time for stats in self._stats.values())
            slow_queries = sum(stats.slow_count for stats in self._stats.values())
            error_count = sum(stats.error_count for stats in self._stats.values())

            # Find slowest queries
            slowest_patterns = sorted(
                self._stats.items(),
                key=lambda x: x[1].max_time,
                reverse=True
            )[:10]

            # Find most frequent queries
            most_frequent = sorted(
                self._stats.items(),
                key=lambda x: x[1].total_executions,
                reverse=True
            )[:10]

            uptime = (datetime.now() - self._start_time).total_seconds()

            return {
                "uptime_seconds": uptime,
                "total_queries": total_queries,
                "total_time_seconds": total_time,
                "average_query_time": total_time / total_queries if total_queries > 0 else 0,
                "queries_per_second": total_queries / uptime if uptime > 0 else 0,
                "slow_queries_count": slow_queries,
                "error_count": error_count,
                "error_rate": error_count / total_queries if total_queries > 0 else 0,
                "unique_query_patterns": len(self._stats),
                "slowest_queries": [
                    {
                        "pattern": pattern,
                        "max_time": stats.max_time,
                        "avg_time": stats.avg_time,
                        "executions": stats.total_executions
                    }
                    for pattern, stats in slowest_patterns
                ],
                "most_frequent_queries": [
                    {
                        "pattern": pattern,
                        "executions": stats.total_executions,
                        "total_time": stats.total_time,
                        "avg_time": stats.avg_time
                    }
                    for pattern, stats in most_frequent
                ],
                "recent_slow_queries": [
                    {
                        "query_id": m.query_id,
                        "pattern": m.query_pattern,
                        "time": m.execution_time,
                        "timestamp": m.timestamp.isoformat()
                    }
                    for m in self._recent_queries[-20:]
                    if m.is_slow
                ]
            }

    def get_query_stats(self, query_pattern: str) -> Optional[QueryStats]:
        """Get statistics for a specific query pattern."""
        with self._lock:
            return self._stats.get(query_pattern)

    def get_all_stats(self) -> Dict[str, QueryStats]:
        """Get all query statistics."""
        with self._lock:
            return dict(self._stats)

    def reset_stats(self):
        """Reset all statistics."""
        with self._lock:
            self._stats.clear()
            self._recent_queries.clear()
            self._query_counter = 0
            self._start_time = datetime.now()
        logger.info("Performance statistics reset")

    def cleanup_old_stats(self, hours: int = None):
        """
        Remove old statistics.

        Args:
            hours: Remove stats older than this many hours (default from config)
        """
        if hours is None:
            hours = PerformanceConfig.STATS_RETENTION_HOURS

        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._lock:
            # Clean up recent queries
            self._recent_queries = [
                m for m in self._recent_queries
                if m.timestamp > cutoff_time
            ]

            # Clean up stats with no recent executions
            patterns_to_remove = [
                pattern for pattern, stats in self._stats.items()
                if stats.last_executed and stats.last_executed < cutoff_time
            ]

            for pattern in patterns_to_remove:
                del self._stats[pattern]

        logger.info(f"Cleaned up {len(patterns_to_remove)} old query patterns")


class _QueryTracker:
    """Context manager for tracking individual queries."""

    def __init__(
        self,
        monitor: DatabasePerformanceMonitor,
        query_type: str,
        query_pattern: str,
        db_type: str
    ):
        self.monitor = monitor
        self.query_type = query_type
        self.query_pattern = query_pattern
        self.db_type = db_type
        self.start_time = None
        self.query_id = None

    def __enter__(self):
        self.query_id = f"{self.query_pattern}_{self.monitor._get_next_id()}"
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        success = exc_type is None
        error = str(exc_val) if exc_val else None

        metrics = QueryMetrics(
            query_id=self.query_id,
            query_type=self.query_type,
            query_pattern=self.query_pattern,
            execution_time=execution_time,
            timestamp=datetime.now(),
            success=success,
            error=error,
            db_type=self.db_type
        )

        self.monitor._record_metrics(metrics)
        return False  # Don't suppress exceptions


# ============================================================================
# Global Monitor Instance
# ============================================================================

# Create a global monitor instance that can be imported
performance_monitor = DatabasePerformanceMonitor()


# ============================================================================
# Utility Functions
# ============================================================================

def get_performance_report() -> Dict[str, Any]:
    """Get performance report from global monitor."""
    return performance_monitor.get_performance_report()


def reset_performance_stats():
    """Reset global performance statistics."""
    performance_monitor.reset_stats()


def cleanup_old_performance_data(hours: int = None):
    """Clean up old performance data."""
    performance_monitor.cleanup_old_stats(hours)


# ============================================================================
# Testing
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Database Performance Monitor Test")
    print("=" * 60)

    monitor = DatabasePerformanceMonitor()

    # Test decorator
    @monitor.track_query("SELECT", "sqlite")
    def test_query_fast():
        time.sleep(0.1)
        return "result"

    @monitor.track_query("SELECT", "postgresql")
    def test_query_slow():
        time.sleep(1.5)
        return "result"

    # Run some queries
    print("\n1. Running test queries...")
    for i in range(5):
        test_query_fast()

    for i in range(2):
        test_query_slow()

    # Test context manager
    print("\n2. Testing context manager...")
    with monitor.track("INSERT", "insert_user", "sqlite"):
        time.sleep(0.05)

    # Get report
    print("\n3. Performance Report:")
    report = monitor.get_performance_report()
    print(f"Total queries: {report['total_queries']}")
    print(f"Slow queries: {report['slow_queries_count']}")
    print(f"Average query time: {report['average_query_time']:.3f}s")

    print("\nSlowest queries:")
    for q in report['slowest_queries']:
        print(f"  - {q['pattern']}: max={q['max_time']:.3f}s, avg={q['avg_time']:.3f}s")

    print("\n" + "=" * 60)
