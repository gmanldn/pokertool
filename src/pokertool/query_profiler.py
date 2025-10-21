#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Query Profiler and Optimization
=========================================

Comprehensive query profiling using EXPLAIN ANALYZE for PostgreSQL and
EXPLAIN QUERY PLAN for SQLite. Integrates with existing performance monitoring
to achieve <50ms p95 query times.

Features:
- EXPLAIN ANALYZE profiling for PostgreSQL
- EXPLAIN QUERY PLAN profiling for SQLite
- Index recommendation based on slow queries
- Query performance tracking against <50ms p95 target
- Integration with DatabasePerformanceMonitor
- Automatic slow query detection and optimization suggestions

Module: pokertool.query_profiler
Version: 1.0.0
"""

import os
import re
import time
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None
    RealDictCursor = None

try:
    from .db_performance_monitor import performance_monitor, PerformanceConfig
    from .database_optimization import DatabaseOptimizationManager
except ImportError:
    from pokertool.db_performance_monitor import performance_monitor, PerformanceConfig
    from pokertool.database_optimization import DatabaseOptimizationManager

logger = logging.getLogger(__name__)

# Target: <50ms for 95th percentile queries
TARGET_P95_MS = 50.0
PROFILING_OUTPUT_DIR = Path.home() / ".pokertool" / "query_profiles"
PROFILING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class QueryProfile:
    """Detailed profile of a single query execution."""
    query: str
    execution_time_ms: float
    explain_plan: str
    db_type: str
    timestamp: datetime
    uses_index: bool = False
    scan_type: str = "unknown"  # seq_scan, index_scan, bitmap_scan, etc.
    rows_examined: Optional[int] = None
    rows_returned: Optional[int] = None
    cost_estimate: Optional[float] = None
    suggestions: List[str] = field(default_factory=list)

    @property
    def is_slow(self) -> bool:
        """Check if query exceeds p95 target."""
        return self.execution_time_ms > TARGET_P95_MS

    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score (0-100, higher is better)."""
        if self.rows_examined == 0 or self.rows_returned is None:
            return 0.0

        # Perfect efficiency: rows_returned == rows_examined
        # Poor efficiency: rows_returned << rows_examined
        if self.rows_examined > 0:
            ratio = self.rows_returned / self.rows_examined
            return min(100.0, ratio * 100.0)
        return 100.0


@dataclass
class IndexRecommendation:
    """Recommendation for adding a database index."""
    table: str
    columns: List[str]
    query_pattern: str
    reason: str
    impact_queries: int
    avg_time_reduction_estimate_ms: float

    def generate_sql(self, db_type: str = "postgresql") -> str:
        """Generate SQL to create the recommended index."""
        index_name = f"idx_{self.table}_{'_'.join(self.columns)}"
        if db_type == "postgresql":
            columns_str = ", ".join(self.columns)
            return f"CREATE INDEX {index_name} ON {self.table}({columns_str});"
        elif db_type == "sqlite":
            columns_str = ", ".join(self.columns)
            return f"CREATE INDEX IF NOT EXISTS {index_name} ON {self.table}({columns_str});"
        return ""


class QueryProfiler:
    """
    Advanced query profiler with EXPLAIN ANALYZE support.

    Usage:
        profiler = QueryProfiler(db_type="postgresql")

        # Profile a query
        profile = profiler.profile_query(connection, "SELECT * FROM users WHERE email = %s", ("user@example.com",))

        # Get optimization suggestions
        suggestions = profiler.get_optimization_suggestions()

        # Check if meeting p95 target
        report = profiler.get_performance_summary()
    """

    def __init__(self, db_type: str = "postgresql"):
        """
        Initialize query profiler.

        Args:
            db_type: Database type ('postgresql' or 'sqlite')
        """
        self.db_type = db_type
        self.profiles: List[QueryProfile] = []
        self.optimization_manager = DatabaseOptimizationManager()
        self._profile_count = 0

    def profile_query(
        self,
        connection: Any,
        query: str,
        parameters: Optional[Tuple] = None,
        normalize: bool = True
    ) -> QueryProfile:
        """
        Profile a query using EXPLAIN ANALYZE.

        Args:
            connection: Database connection
            query: SQL query to profile
            parameters: Query parameters
            normalize: Whether to normalize the query for pattern matching

        Returns:
            QueryProfile with detailed execution plan
        """
        if normalize:
            normalized_query = self._normalize_query(query)
        else:
            normalized_query = query

        # Execute EXPLAIN ANALYZE
        start_time = time.time()
        explain_plan = self._explain_analyze(connection, query, parameters)
        execution_time_ms = (time.time() - start_time) * 1000

        # Parse explain plan
        analysis = self._parse_explain_plan(explain_plan)

        # Create profile
        profile = QueryProfile(
            query=normalized_query,
            execution_time_ms=execution_time_ms,
            explain_plan=explain_plan,
            db_type=self.db_type,
            timestamp=datetime.now(),
            uses_index=analysis.get("uses_index", False),
            scan_type=analysis.get("scan_type", "unknown"),
            rows_examined=analysis.get("rows_examined"),
            rows_returned=analysis.get("rows_returned"),
            cost_estimate=analysis.get("cost_estimate"),
        )

        # Generate optimization suggestions
        profile.suggestions = self._generate_suggestions(profile, analysis)

        # Store profile
        self.profiles.append(profile)
        self._profile_count += 1

        # Limit profile history
        if len(self.profiles) > 1000:
            self.profiles.pop(0)

        # Log slow queries
        if profile.is_slow:
            logger.warning(
                f"Slow query detected ({execution_time_ms:.2f}ms > {TARGET_P95_MS}ms): {normalized_query[:100]}"
            )
            self._save_profile_to_disk(profile)

        return profile

    def _explain_analyze(
        self,
        connection: Any,
        query: str,
        parameters: Optional[Tuple] = None
    ) -> str:
        """Execute EXPLAIN ANALYZE and return the plan."""
        cursor = connection.cursor()

        try:
            if self.db_type == "postgresql" and POSTGRES_AVAILABLE:
                # PostgreSQL: EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {query}"
                cursor.execute(explain_query, parameters or ())
                plan_rows = cursor.fetchall()
                return "\n".join(row[0] for row in plan_rows)

            elif self.db_type == "sqlite":
                # SQLite: EXPLAIN QUERY PLAN
                explain_query = f"EXPLAIN QUERY PLAN {query}"
                if parameters:
                    cursor.execute(explain_query, parameters)
                else:
                    cursor.execute(explain_query)
                plan_rows = cursor.fetchall()
                return "\n".join(str(row) for row in plan_rows)

            else:
                return f"EXPLAIN not supported for {self.db_type}"

        except Exception as e:
            logger.error(f"Failed to EXPLAIN query: {e}")
            return f"Error: {e}"
        finally:
            cursor.close()

    def _parse_explain_plan(self, explain_plan: str) -> Dict[str, Any]:
        """Parse EXPLAIN output to extract key metrics."""
        analysis = {
            "uses_index": False,
            "scan_type": "unknown",
            "rows_examined": None,
            "rows_returned": None,
            "cost_estimate": None,
        }

        if self.db_type == "postgresql":
            # Look for index usage
            if "Index Scan" in explain_plan or "Index Only Scan" in explain_plan:
                analysis["uses_index"] = True
                analysis["scan_type"] = "index_scan"
            elif "Bitmap Index Scan" in explain_plan or "Bitmap Heap Scan" in explain_plan:
                analysis["uses_index"] = True
                analysis["scan_type"] = "bitmap_scan"
            elif "Seq Scan" in explain_plan:
                analysis["scan_type"] = "seq_scan"

            # Extract cost estimate (cost=0.00..1234.56)
            cost_match = re.search(r'cost=[\d.]+\.\.([\d.]+)', explain_plan)
            if cost_match:
                analysis["cost_estimate"] = float(cost_match.group(1))

            # Extract rows (rows=1234)
            rows_match = re.search(r'rows=(\d+)', explain_plan)
            if rows_match:
                analysis["rows_examined"] = int(rows_match.group(1))

            # Extract actual rows (actual.*rows=(\d+))
            actual_rows_match = re.search(r'actual.*rows=(\d+)', explain_plan)
            if actual_rows_match:
                analysis["rows_returned"] = int(actual_rows_match.group(1))

        elif self.db_type == "sqlite":
            # SQLite plan is simpler
            if "USING INDEX" in explain_plan.upper():
                analysis["uses_index"] = True
                analysis["scan_type"] = "index_scan"
            elif "SCAN TABLE" in explain_plan.upper():
                analysis["scan_type"] = "seq_scan"

        return analysis

    def _generate_suggestions(self, profile: QueryProfile, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on profile."""
        suggestions = []

        # Check for sequential scans
        if analysis.get("scan_type") == "seq_scan":
            suggestions.append("Query uses sequential scan - consider adding an index")

        # Check efficiency
        if profile.efficiency_score < 10.0 and profile.rows_examined and profile.rows_examined > 100:
            suggestions.append(
                f"Low efficiency ({profile.efficiency_score:.1f}%) - "
                f"examined {profile.rows_examined} rows but returned {profile.rows_returned}"
            )

        # Check execution time
        if profile.execution_time_ms > TARGET_P95_MS:
            suggestions.append(
                f"Exceeds p95 target ({profile.execution_time_ms:.2f}ms > {TARGET_P95_MS}ms)"
            )

        # Check for SELECT *
        if "SELECT *" in profile.query.upper():
            suggestions.append("Avoid SELECT * - specify only needed columns")

        # Check for missing WHERE clause
        if "WHERE" not in profile.query.upper() and "INSERT" not in profile.query.upper():
            suggestions.append("Query has no WHERE clause - may return unnecessary rows")

        return suggestions

    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching (remove parameters)."""
        # Replace quoted strings with placeholder
        normalized = re.sub(r"'[^']*'", "?", query)
        # Replace numbers with placeholder
        normalized = re.sub(r'\b\d+\b', "?", normalized)
        # Collapse whitespace
        normalized = " ".join(normalized.split())
        return normalized

    def _save_profile_to_disk(self, profile: QueryProfile):
        """Save slow query profile to disk for analysis."""
        timestamp = profile.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = PROFILING_OUTPUT_DIR / f"profile_{timestamp}_{self._profile_count}.txt"

        try:
            with open(filename, 'w') as f:
                f.write(f"Query Profile - {profile.timestamp.isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Query: {profile.query}\n\n")
                f.write(f"Execution Time: {profile.execution_time_ms:.2f}ms\n")
                f.write(f"Database Type: {profile.db_type}\n")
                f.write(f"Uses Index: {profile.uses_index}\n")
                f.write(f"Scan Type: {profile.scan_type}\n")
                f.write(f"Rows Examined: {profile.rows_examined}\n")
                f.write(f"Rows Returned: {profile.rows_returned}\n")
                f.write(f"Efficiency Score: {profile.efficiency_score:.1f}%\n\n")

                if profile.suggestions:
                    f.write("Suggestions:\n")
                    for i, suggestion in enumerate(profile.suggestions, 1):
                        f.write(f"  {i}. {suggestion}\n")
                    f.write("\n")

                f.write("Explain Plan:\n")
                f.write("-" * 80 + "\n")
                f.write(profile.explain_plan)
                f.write("\n")

        except Exception as e:
            logger.error(f"Failed to save profile to disk: {e}")

    def get_index_recommendations(self, min_occurrences: int = 3) -> List[IndexRecommendation]:
        """
        Generate index recommendations based on slow queries.

        Args:
            min_occurrences: Minimum number of times a pattern must appear

        Returns:
            List of index recommendations
        """
        recommendations = []

        # Find queries with sequential scans that occur frequently
        seq_scan_patterns: Dict[str, List[QueryProfile]] = {}
        for profile in self.profiles:
            if profile.scan_type == "seq_scan" and profile.is_slow:
                pattern = profile.query
                if pattern not in seq_scan_patterns:
                    seq_scan_patterns[pattern] = []
                seq_scan_patterns[pattern].append(profile)

        # Generate recommendations for frequent patterns
        for pattern, profiles in seq_scan_patterns.items():
            if len(profiles) >= min_occurrences:
                # Extract table and column from WHERE clause
                table, columns = self._extract_table_and_columns(pattern)
                if table and columns:
                    avg_time = statistics.mean(p.execution_time_ms for p in profiles)

                    recommendation = IndexRecommendation(
                        table=table,
                        columns=columns,
                        query_pattern=pattern,
                        reason=f"Sequential scan on {len(profiles)} queries",
                        impact_queries=len(profiles),
                        avg_time_reduction_estimate_ms=avg_time * 0.7,  # Estimate 70% reduction
                    )
                    recommendations.append(recommendation)

        return recommendations

    def _extract_table_and_columns(self, query: str) -> Tuple[Optional[str], List[str]]:
        """Extract table name and WHERE clause columns from query."""
        try:
            query_upper = query.upper()

            # Extract table name from FROM clause
            from_match = re.search(r'FROM\s+(\w+)', query_upper)
            if not from_match:
                return None, []
            table = from_match.group(1).lower()

            # Extract columns from WHERE clause
            where_match = re.search(r'WHERE\s+(.+?)(?:ORDER BY|GROUP BY|LIMIT|$)', query_upper)
            if not where_match:
                return table, []

            where_clause = where_match.group(1)

            # Extract column names (simple heuristic)
            columns = []
            # Look for patterns like "column_name =" or "column_name IN"
            column_matches = re.findall(r'(\w+)\s*(?:=|IN|<|>|LIKE)', where_clause)
            columns = [col.lower() for col in column_matches if col.upper() not in ('AND', 'OR', 'NOT')]

            return table, columns

        except Exception as e:
            logger.error(f"Failed to extract table and columns: {e}")
            return None, []

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary against p95 target.

        Returns:
            Dictionary with performance metrics
        """
        if not self.profiles:
            return {
                "total_queries": 0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "target_p95_ms": TARGET_P95_MS,
                "meeting_target": True,
                "slow_queries": 0,
                "index_usage_rate": 0.0,
            }

        execution_times = [p.execution_time_ms for p in self.profiles]
        execution_times_sorted = sorted(execution_times)
        n = len(execution_times_sorted)

        p50 = execution_times_sorted[int(n * 0.50)]
        p95 = execution_times_sorted[int(n * 0.95)]
        p99 = execution_times_sorted[int(n * 0.99)]

        slow_queries = sum(1 for p in self.profiles if p.is_slow)
        index_usage = sum(1 for p in self.profiles if p.uses_index)

        return {
            "total_queries": len(self.profiles),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "target_p95_ms": TARGET_P95_MS,
            "meeting_target": p95 <= TARGET_P95_MS,
            "slow_queries": slow_queries,
            "slow_query_rate": round(slow_queries / len(self.profiles), 3),
            "index_usage_rate": round(index_usage / len(self.profiles), 3),
            "avg_execution_ms": round(statistics.mean(execution_times), 2),
            "max_execution_ms": round(max(execution_times), 2),
        }

    @contextmanager
    def profile_context(self, connection: Any, query: str, parameters: Optional[Tuple] = None):
        """
        Context manager for profiling a query.

        Usage:
            with profiler.profile_context(conn, "SELECT * FROM users WHERE id = %s", (123,)) as profile:
                # Query is profiled automatically
                pass
        """
        profile = None
        try:
            profile = self.profile_query(connection, query, parameters)
            yield profile
        finally:
            if profile and profile.is_slow:
                logger.warning(f"Slow query in context: {query[:100]}")


# Global profiler instances
_postgresql_profiler: Optional[QueryProfiler] = None
_sqlite_profiler: Optional[QueryProfiler] = None


def get_profiler(db_type: str = "postgresql") -> QueryProfiler:
    """Get or create global profiler instance."""
    global _postgresql_profiler, _sqlite_profiler

    if db_type == "postgresql":
        if _postgresql_profiler is None:
            _postgresql_profiler = QueryProfiler(db_type="postgresql")
        return _postgresql_profiler
    elif db_type == "sqlite":
        if _sqlite_profiler is None:
            _sqlite_profiler = QueryProfiler(db_type="sqlite")
        return _sqlite_profiler
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


# Export public API
__all__ = [
    'QueryProfiler',
    'QueryProfile',
    'IndexRecommendation',
    'get_profiler',
    'TARGET_P95_MS',
]
