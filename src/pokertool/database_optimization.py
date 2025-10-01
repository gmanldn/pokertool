"""Database optimization utilities including caching, archiving, and monitoring."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

DEFAULT_DB_OPT_DIR = Path.home() / ".pokertool" / "db_optimization"
DEFAULT_DB_OPT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class CachedResult:
    """Represents a cached query result entry."""

    key: str
    value: Any
    expires_at: float
    hit_count: int = 0

    def is_valid(self) -> bool:
        return time.time() <= self.expires_at


@dataclass
class QueryRecord:
    """Captured information about executed queries."""

    name: str
    duration_ms: float
    rows: int
    success: bool
    sql: str
    parameters: Tuple[Any, ...]
    timestamp: float = field(default_factory=time.time)


class QueryCache:
    """In-memory query result cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, CachedResult] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if not entry:
            return None
        if not entry.is_valid():
            self._cache.pop(key, None)
            return None
        entry.hit_count += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._cache[key] = CachedResult(key=key, value=value, expires_at=time.time() + ttl_seconds)

    def purge(self) -> None:
        for key, entry in list(self._cache.items()):
            if not entry.is_valid():
                self._cache.pop(key, None)

    def stats(self) -> Dict[str, int]:
        return {
            "entries": len(self._cache),
            "valid_entries": sum(1 for entry in self._cache.values() if entry.is_valid()),
        }


class QueryMonitor:
    """Tracks query performance and identifies optimization candidates."""

    def __init__(self):
        self._records: List[QueryRecord] = []

    def record(self, name: str, sql: str, parameters: Tuple[Any, ...], duration_ms: float, rows: int, success: bool) -> None:
        self._records.append(QueryRecord(name=name, sql=sql, parameters=parameters, duration_ms=duration_ms, rows=rows, success=success))

    def slow_queries(self, threshold_ms: float = 200.0) -> List[QueryRecord]:
        return [record for record in self._records if record.duration_ms >= threshold_ms]

    def failure_rate(self) -> float:
        if not self._records:
            return 0.0
        failures = sum(1 for record in self._records if not record.success)
        return failures / len(self._records)

    def usage_statistics(self) -> Dict[str, Any]:
        total = len(self._records)
        if total == 0:
            return {"count": 0, "avg_duration": 0.0, "max_duration": 0.0}
        durations = [record.duration_ms for record in self._records]
        return {
            "count": total,
            "avg_duration": round(sum(durations) / total, 2),
            "max_duration": max(durations),
        }


class IndexAdvisor:
    """Heuristic index recommendation engine based on query patterns."""

    def __init__(self):
        self._column_usage: Dict[str, int] = {}

    def register_filter(self, table: str, column: str) -> None:
        key = f"{table}.{column}"
        self._column_usage[key] = self._column_usage.get(key, 0) + 1

    def recommendations(self, threshold: int = 2) -> List[str]:
        suggestions = []
        for key, count in sorted(self._column_usage.items(), key=lambda item: item[1], reverse=True):
            if count >= threshold:
                table, column = key.split(".", 1)
                suggestions.append(f"Consider adding index on {table}({column}) - seen in {count} filters")
        return suggestions


class ArchiveManager:
    """Handles data archiving for cold storage."""

    def __init__(self, storage_dir: Path = DEFAULT_DB_OPT_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def archive(self, table_name: str, rows: List[Dict[str, Any]]) -> Path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        archive_path = self.storage_dir / f"{table_name}_{timestamp}.json"
        archive_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
        return archive_path

    def archived_files(self) -> List[Path]:
        return sorted(self.storage_dir.glob("*.json"))


class DatabaseOptimizationManager:
    """Composite utility for applying database optimizations."""

    def __init__(self, storage_dir: Path = DEFAULT_DB_OPT_DIR):
        self.cache = QueryCache()
        self.monitor = QueryMonitor()
        self.index_advisor = IndexAdvisor()
        self.archiver = ArchiveManager(storage_dir)
        self._optimization_notes: List[str] = []

    def cached_query(self, key: str, loader: Callable[[], Any], ttl_seconds: int = 60) -> Any:
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        value = loader()
        self.cache.set(key, value, ttl_seconds)
        return value

    def optimize_query(self, sql: str) -> List[str]:
        sql_upper = sql.upper()
        hints: List[str] = []
        if "SELECT *" in sql_upper:
            hints.append("Avoid SELECT * to reduce payload size.")
        if "WHERE" not in sql_upper:
            hints.append("Add WHERE clauses or limits to improve efficiency.")
        if "JOIN" in sql_upper and " ON " not in sql_upper:
            hints.append("Ensure JOINs include explicit ON clauses.")
        if "ORDER BY" in sql_upper and "INDEX" not in sql_upper:
            hints.append("Verify supporting index for ORDER BY columns.")
        if not hints:
            hints.append("Query appears optimized; monitor for regressions.")
        self._optimization_notes.extend(hints)
        return hints

    def monitor_query(self, name: str, sql: str, parameters: Tuple[Any, ...], duration_ms: float, rows: int, success: bool) -> None:
        self.monitor.record(name, sql, parameters, duration_ms, rows, success)
        if success and duration_ms >= 150:
            # Register columns in WHERE clause for potential indexing.
            where_clause = sql.upper().split("WHERE")[-1] if "WHERE" in sql.upper() else ""
            for token in where_clause.split():
                if "." in token and token.isidentifier() is False:
                    table_column = token.strip('()=<>!,')
                    if "." in table_column:
                        table, column = table_column.split(".", 1)
                        self.index_advisor.register_filter(table.lower(), column.lower())

    def archive_table(self, table_name: str, rows: List[Dict[str, Any]]) -> Path:
        return self.archiver.archive(table_name, rows)

    def optimization_summary(self) -> Dict[str, Any]:
        return {
            "cache": self.cache.stats(),
            "queries": self.monitor.usage_statistics(),
            "slow_queries": len(self.monitor.slow_queries()),
            "failure_rate": round(self.monitor.failure_rate(), 3),
            "index_recommendations": self.index_advisor.recommendations(),
            "notes": list(self._optimization_notes[-10:]),
            "archives": [path.name for path in self.archiver.archived_files()],
        }


__all__ = [
    "ArchiveManager",
    "DatabaseOptimizationManager",
    "IndexAdvisor",
    "QueryCache",
    "QueryMonitor",
]
