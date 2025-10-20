#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance Telemetry System for PokerTool
==========================================

High-performance telemetry system for capturing detailed timing data
with minimal overhead. Designed to identify performance bottlenecks
during GUI startup and runtime operations.

Features:
- Thread-safe SQLite database with compression
- Batch writes for minimal overhead (<10ms per operation)
- Automatic cleanup to maintain <1GB database
- Rich contextual data (CPU, memory, stack depth)
- Easy-to-use decorators and context managers

Usage:
    from pokertool.performance_telemetry import timed, telemetry_section

    @timed(category='module_init', operation='gto_solver')
    def init_solver(self):
        # Function is automatically timed
        pass

    with telemetry_section('ui_build', 'autopilot_tab'):
        # Section is automatically timed
        build_tab()

Version: 1.0.0
"""

from __future__ import annotations

import sqlite3
import zlib
import json
import time
import threading
import os
import atexit
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Optional dependency for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Global telemetry instance
_telemetry_instance: Optional['PerformanceTelemetry'] = None
_telemetry_lock = threading.Lock()

# Database configuration
TELEMETRY_DB_PATH = Path.home() / ".pokertool" / "telemetry.db"
TELEMETRY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Performance configuration
BATCH_SIZE = 100  # Flush after 100 entries
BATCH_TIMEOUT = 5.0  # Flush after 5 seconds
MAX_DB_SIZE_MB = 950  # Keep under 1GB
RETENTION_DAYS = 7  # Keep last 7 days


@dataclass
class TelemetryEntry:
    """Single telemetry entry."""
    timestamp: float
    category: str
    operation: str
    duration_ms: Optional[float]
    event_type: str  # 'start', 'end', 'instant'
    thread_id: int
    stack_depth: int
    cpu_percent: Optional[float]
    memory_mb: Optional[float]
    details: Optional[Dict[str, Any]]
    parent_id: Optional[int]

    def to_db_tuple(self) -> tuple:
        """Convert to database tuple with compressed JSON."""
        details_json = None
        if self.details:
            # Compress JSON details with zlib
            json_str = json.dumps(self.details, separators=(',', ':'))
            details_json = zlib.compress(json_str.encode('utf-8'), level=6)

        return (
            self.timestamp,
            self.category,
            self.operation,
            self.duration_ms,
            self.event_type,
            self.thread_id,
            self.stack_depth,
            self.cpu_percent,
            self.memory_mb,
            details_json,
            self.parent_id
        )


class PerformanceTelemetry:
    """
    High-performance telemetry system with batched writes and compression.

    Thread-safe, minimal overhead, automatic cleanup.
    """

    def __init__(self, db_path: Path = TELEMETRY_DB_PATH):
        """Initialize telemetry system."""
        self.db_path = db_path
        self.db_lock = threading.Lock()
        self.write_buffer: List[TelemetryEntry] = []
        self.buffer_lock = threading.Lock()
        self.last_flush = time.time()
        self.operation_stack: Dict[int, List[int]] = {}  # thread_id -> [entry_ids]
        self.next_id = 1
        self.id_lock = threading.Lock()

        # Initialize database
        self._init_database()

        # Start background flush thread
        self.running = True
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()

        # Register cleanup on exit
        atexit.register(self.shutdown)

        # Get process for metrics
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None

    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    category TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    duration_ms REAL,
                    event_type TEXT NOT NULL,
                    thread_id INTEGER NOT NULL,
                    stack_depth INTEGER NOT NULL,
                    cpu_percent REAL,
                    memory_mb REAL,
                    details BLOB,
                    parent_id INTEGER
                )
            """)

            # Indexes for fast queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON telemetry(timestamp DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category_operation ON telemetry(category, operation)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_thread_id ON telemetry(thread_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON telemetry(event_type)")

            conn.commit()

    def _get_next_id(self) -> int:
        """Get next entry ID (thread-safe)."""
        with self.id_lock:
            entry_id = self.next_id
            self.next_id += 1
            return entry_id

    def _get_system_metrics(self) -> tuple[Optional[float], Optional[float]]:
        """Get current CPU and memory usage."""
        if not self.process:
            return None, None

        try:
            cpu = self.process.cpu_percent(interval=0)
            memory = self.process.memory_info().rss / (1024 * 1024)  # MB
            return cpu, memory
        except:
            return None, None

    def _get_stack_depth(self) -> int:
        """Get current call stack depth."""
        thread_id = threading.get_ident()
        return len(self.operation_stack.get(thread_id, []))

    def record_start(self, category: str, operation: str, details: Optional[Dict[str, Any]] = None) -> int:
        """Record operation start."""
        entry_id = self._get_next_id()
        thread_id = threading.get_ident()
        cpu, memory = self._get_system_metrics()

        # Update operation stack
        if thread_id not in self.operation_stack:
            self.operation_stack[thread_id] = []

        parent_id = self.operation_stack[thread_id][-1] if self.operation_stack[thread_id] else None
        self.operation_stack[thread_id].append(entry_id)

        entry = TelemetryEntry(
            timestamp=time.time(),
            category=category,
            operation=operation,
            duration_ms=None,
            event_type='start',
            thread_id=thread_id,
            stack_depth=len(self.operation_stack[thread_id]) - 1,
            cpu_percent=cpu,
            memory_mb=memory,
            details=details,
            parent_id=parent_id
        )

        self._add_to_buffer(entry)
        return entry_id

    def record_end(self, category: str, operation: str, start_time: float, entry_id: int, details: Optional[Dict[str, Any]] = None):
        """Record operation end with duration."""
        thread_id = threading.get_ident()
        duration_ms = (time.time() - start_time) * 1000.0
        cpu, memory = self._get_system_metrics()

        # Pop from operation stack
        if thread_id in self.operation_stack and self.operation_stack[thread_id]:
            self.operation_stack[thread_id].pop()

        parent_id = self.operation_stack[thread_id][-1] if thread_id in self.operation_stack and self.operation_stack[thread_id] else None

        entry = TelemetryEntry(
            timestamp=time.time(),
            category=category,
            operation=operation,
            duration_ms=duration_ms,
            event_type='end',
            thread_id=thread_id,
            stack_depth=self._get_stack_depth(),
            cpu_percent=cpu,
            memory_mb=memory,
            details=details,
            parent_id=parent_id
        )

        self._add_to_buffer(entry)

    def record_instant(self, category: str, operation: str, details: Optional[Dict[str, Any]] = None):
        """Record instant event (no duration)."""
        thread_id = threading.get_ident()
        cpu, memory = self._get_system_metrics()

        parent_id = self.operation_stack[thread_id][-1] if thread_id in self.operation_stack and self.operation_stack[thread_id] else None

        entry = TelemetryEntry(
            timestamp=time.time(),
            category=category,
            operation=operation,
            duration_ms=None,
            event_type='instant',
            thread_id=thread_id,
            stack_depth=self._get_stack_depth(),
            cpu_percent=cpu,
            memory_mb=memory,
            details=details,
            parent_id=parent_id
        )

        self._add_to_buffer(entry)

    def _add_to_buffer(self, entry: TelemetryEntry):
        """Add entry to write buffer."""
        with self.buffer_lock:
            self.write_buffer.append(entry)

            # Flush if buffer is full
            if len(self.write_buffer) >= BATCH_SIZE:
                self._flush_buffer()

    def _flush_buffer(self):
        """Flush write buffer to database."""
        with self.buffer_lock:
            if not self.write_buffer:
                return

            entries = self.write_buffer.copy()
            self.write_buffer.clear()
            self.last_flush = time.time()

        # Write to database (outside lock for better concurrency)
        with self.db_lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.executemany("""
                        INSERT INTO telemetry (
                            timestamp, category, operation, duration_ms, event_type,
                            thread_id, stack_depth, cpu_percent, memory_mb, details, parent_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [entry.to_db_tuple() for entry in entries])
                    conn.commit()
            except Exception as e:
                print(f"Telemetry flush error: {e}")

    def _flush_loop(self):
        """Background thread to flush buffer periodically."""
        while self.running:
            time.sleep(1.0)

            # Check if timeout expired
            if time.time() - self.last_flush >= BATCH_TIMEOUT:
                self._flush_buffer()

    def cleanup_old_data(self):
        """Remove old entries and maintain database size."""
        with self.db_lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    # Delete entries older than retention period
                    cutoff = time.time() - (RETENTION_DAYS * 86400)
                    conn.execute("DELETE FROM telemetry WHERE timestamp < ?", (cutoff,))

                    # Check database size
                    db_size_mb = self.db_path.stat().st_size / (1024 * 1024)

                    # If still too large, delete oldest 20%
                    if db_size_mb > MAX_DB_SIZE_MB:
                        total = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
                        delete_count = int(total * 0.2)

                        conn.execute("""
                            DELETE FROM telemetry WHERE id IN (
                                SELECT id FROM telemetry ORDER BY timestamp ASC LIMIT ?
                            )
                        """, (delete_count,))

                    # Vacuum to reclaim space
                    conn.execute("VACUUM")
                    conn.commit()
            except Exception as e:
                print(f"Telemetry cleanup error: {e}")

    def shutdown(self):
        """Shutdown telemetry system."""
        self.running = False
        self._flush_buffer()

        # Wait for flush thread
        if self.flush_thread.is_alive():
            self.flush_thread.join(timeout=5.0)

        # Final cleanup
        self.cleanup_old_data()

    def get_statistics(self) -> Dict[str, Any]:
        """Get telemetry statistics."""
        with self.db_lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    total = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
                    db_size_mb = self.db_path.stat().st_size / (1024 * 1024)

                    oldest = conn.execute("SELECT MIN(timestamp) FROM telemetry").fetchone()[0]
                    newest = conn.execute("SELECT MAX(timestamp) FROM telemetry").fetchone()[0]

                    categories = conn.execute("""
                        SELECT category, COUNT(*) FROM telemetry GROUP BY category
                    """).fetchall()

                    return {
                        'total_entries': total,
                        'db_size_mb': round(db_size_mb, 2),
                        'oldest_timestamp': oldest,
                        'newest_timestamp': newest,
                        'time_range_hours': round((newest - oldest) / 3600, 2) if oldest and newest else 0,
                        'categories': {cat: count for cat, count in categories}
                    }
            except Exception as e:
                return {'error': str(e)}


# Decorator for automatic function timing
def timed(category: str, operation: Optional[str] = None, capture_args: bool = False):
    """
    Decorator to automatically time function execution.

    Args:
        category: Telemetry category (e.g., 'module_init', 'ui_build')
        operation: Operation name (defaults to function name)
        capture_args: If True, capture function arguments in details

    Usage:
        @timed(category='module_init', operation='gto_solver')
        def init_solver(self):
            # Automatically timed
            pass
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            telemetry = get_telemetry()
            if not telemetry:
                return func(*args, **kwargs)

            details = {}
            if capture_args:
                details['args'] = str(args)[:200]  # Limit size
                details['kwargs'] = str(kwargs)[:200]

            entry_id = telemetry.record_start(category, op_name, details)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                telemetry.record_end(category, op_name, start_time, entry_id)
                return result
            except Exception as e:
                telemetry.record_end(category, op_name, start_time, entry_id, {'error': str(e)})
                raise

        return wrapper
    return decorator


@contextmanager
def telemetry_section(category: str, operation: str, details: Optional[Dict[str, Any]] = None):
    """
    Context manager for timing code sections.

    Usage:
        with telemetry_section('ui_build', 'autopilot_tab'):
            build_autopilot_tab()
    """
    telemetry = get_telemetry()
    if not telemetry:
        yield
        return

    entry_id = telemetry.record_start(category, operation, details)
    start_time = time.time()

    try:
        yield
        telemetry.record_end(category, operation, start_time, entry_id)
    except Exception as e:
        telemetry.record_end(category, operation, start_time, entry_id, {'error': str(e)})
        raise


def telemetry_instant(category: str, operation: str, details: Optional[Dict[str, Any]] = None):
    """
    Record instant event (no duration).

    Usage:
        telemetry_instant('startup', 'splash_shown', {'version': '66.0.0'})
    """
    telemetry = get_telemetry()
    if telemetry:
        telemetry.record_instant(category, operation, details)


def init_telemetry(db_path: Path = TELEMETRY_DB_PATH) -> PerformanceTelemetry:
    """Initialize global telemetry instance."""
    global _telemetry_instance

    with _telemetry_lock:
        if _telemetry_instance is None:
            _telemetry_instance = PerformanceTelemetry(db_path)
            print(f"✓ Performance telemetry initialized: {db_path}")
        return _telemetry_instance


def get_telemetry() -> Optional[PerformanceTelemetry]:
    """Get global telemetry instance."""
    return _telemetry_instance


def shutdown_telemetry():
    """Shutdown global telemetry instance."""
    global _telemetry_instance

    with _telemetry_lock:
        if _telemetry_instance:
            _telemetry_instance.shutdown()
            _telemetry_instance = None


__all__ = [
    'PerformanceTelemetry',
    'TelemetryEntry',
    'timed',
    'telemetry_section',
    'telemetry_instant',
    'init_telemetry',
    'get_telemetry',
    'shutdown_telemetry',
]
