#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance Telemetry Analysis Tool
===================================

Standalone script to analyze performance telemetry data collected during
PokerTool startup and runtime operations.

Usage:
    python analyze_telemetry.py --last 5m
    python analyze_telemetry.py --slowest 20
    python analyze_telemetry.py --timeline startup
    python analyze_telemetry.py --thread-analysis
    python analyze_telemetry.py --memory-growth
    python analyze_telemetry.py --export report.json

Version: 1.0.0
"""

import sqlite3
import zlib
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# Telemetry database location
TELEMETRY_DB = Path.home() / ".pokertool" / "telemetry.db"


def decompress_details(blob: Optional[bytes]) -> Optional[Dict[str, Any]]:
    """Decompress JSON details from BLOB."""
    if not blob:
        return None
    try:
        json_str = zlib.decompress(blob).decode('utf-8')
        return json.loads(json_str)
    except:
        return None


def format_duration(ms: float) -> str:
    """Format duration in human-readable format."""
    if ms < 1:
        return f"{ms*1000:.1f}µs"
    elif ms < 1000:
        return f"{ms:.1f}ms"
    else:
        return f"{ms/1000:.2f}s"


def parse_time_filter(time_str: str) -> float:
    """Parse time filter string (e.g., '5m', '1h', '2d') into seconds."""
    if not time_str:
        return 0

    unit = time_str[-1].lower()
    try:
        value = int(time_str[:-1])
    except ValueError:
        raise ValueError(f"Invalid time format: {time_str}")

    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }

    if unit not in multipliers:
        raise ValueError(f"Invalid time unit: {unit}. Use s/m/h/d")

    return value * multipliers[unit]


def get_slowest_operations(conn: sqlite3.Connection, limit: int = 20, category: Optional[str] = None) -> List[Tuple]:
    """Get slowest operations."""
    query = """
        SELECT category, operation, duration_ms, timestamp, thread_id
        FROM telemetry
        WHERE event_type = 'end' AND duration_ms IS NOT NULL
    """

    params = []
    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY duration_ms DESC LIMIT ?"
    params.append(limit)

    return conn.execute(query, params).fetchall()


def get_timeline(conn: sqlite3.Connection, category: Optional[str] = None, time_filter: Optional[str] = None) -> List[Tuple]:
    """Get timeline of operations."""
    query = """
        SELECT timestamp, category, operation, event_type, duration_ms, thread_id, stack_depth
        FROM telemetry
    """

    params = []
    conditions = []

    if category:
        conditions.append("category = ?")
        params.append(category)

    if time_filter:
        cutoff = datetime.now().timestamp() - parse_time_filter(time_filter)
        conditions.append("timestamp >= ?")
        params.append(cutoff)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY timestamp ASC"

    return conn.execute(query, params).fetchall()


def get_thread_analysis(conn: sqlite3.Connection) -> Dict[int, Dict[str, Any]]:
    """Analyze operations by thread."""
    threads = defaultdict(lambda: {'operations': 0, 'total_time_ms': 0, 'categories': set()})

    rows = conn.execute("""
        SELECT thread_id, category, COUNT(*), SUM(duration_ms)
        FROM telemetry
        WHERE event_type = 'end' AND duration_ms IS NOT NULL
        GROUP BY thread_id, category
    """).fetchall()

    for thread_id, category, count, total_ms in rows:
        threads[thread_id]['operations'] += count
        threads[thread_id]['total_time_ms'] += total_ms or 0
        threads[thread_id]['categories'].add(category)

    return dict(threads)


def get_memory_growth(conn: sqlite3.Connection) -> List[Tuple]:
    """Get memory growth over time."""
    return conn.execute("""
        SELECT timestamp, memory_mb, category, operation
        FROM telemetry
        WHERE memory_mb IS NOT NULL
        ORDER BY timestamp ASC
    """).fetchall()


def print_slowest(conn: sqlite3.Connection, limit: int, category: Optional[str]):
    """Print slowest operations."""
    print(f"\n{'='*80}")
    print(f"SLOWEST {limit} OPERATIONS" + (f" (category: {category})" if category else ""))
    print(f"{'='*80}\n")

    rows = get_slowest_operations(conn, limit, category)

    if not rows:
        print("No data available.")
        return

    print(f"{'Duration':<15} {'Category':<20} {'Operation':<30} {'Thread':<10}")
    print(f"{'-'*80}")

    for category_val, operation, duration_ms, timestamp, thread_id in rows:
        duration_str = format_duration(duration_ms)
        print(f"{duration_str:<15} {category_val:<20} {operation:<30} {thread_id:<10}")


def print_timeline(conn: sqlite3.Connection, category: Optional[str], time_filter: Optional[str]):
    """Print timeline of operations."""
    print(f"\n{'='*80}")
    print(f"TIMELINE" + (f" (category: {category})" if category else "") + (f" (last {time_filter})" if time_filter else ""))
    print(f"{'='*80}\n")

    rows = get_timeline(conn, category, time_filter)

    if not rows:
        print("No data available.")
        return

    print(f"{'Time':<20} {'Event':<8} {'Category':<15} {'Operation':<25} {'Duration':<12} {'Depth':<5}")
    print(f"{'-'*80}")

    base_timestamp = None
    for timestamp, cat, operation, event_type, duration_ms, thread_id, stack_depth in rows:
        if base_timestamp is None:
            base_timestamp = timestamp

        relative_time = (timestamp - base_timestamp) * 1000  # ms since start
        time_str = f"+{format_duration(relative_time)}"

        duration_str = format_duration(duration_ms) if duration_ms else "-"

        # Indent by stack depth
        indent = "  " * stack_depth
        operation_display = indent + operation[:25-len(indent)]

        print(f"{time_str:<20} {event_type:<8} {cat:<15} {operation_display:<25} {duration_str:<12} {stack_depth:<5}")


def print_thread_analysis(conn: sqlite3.Connection):
    """Print thread analysis."""
    print(f"\n{'='*80}")
    print("THREAD ANALYSIS")
    print(f"{'='*80}\n")

    threads = get_thread_analysis(conn)

    if not threads:
        print("No data available.")
        return

    print(f"{'Thread ID':<15} {'Operations':<15} {'Total Time':<20} {'Categories'}")
    print(f"{'-'*80}")

    for thread_id, data in sorted(threads.items()):
        total_time_str = format_duration(data['total_time_ms'])
        categories_str = ", ".join(sorted(data['categories']))
        print(f"{thread_id:<15} {data['operations']:<15} {total_time_str:<20} {categories_str}")


def print_memory_growth(conn: sqlite3.Connection):
    """Print memory growth analysis."""
    print(f"\n{'='*80}")
    print("MEMORY GROWTH ANALYSIS")
    print(f"{'='*80}\n")

    rows = get_memory_growth(conn)

    if not rows:
        print("No data available.")
        return

    print(f"{'Time':<20} {'Memory':<15} {'Category':<15} {'Operation':<30}")
    print(f"{'-'*80}")

    base_timestamp = None
    for timestamp, memory_mb, category, operation in rows:
        if base_timestamp is None:
            base_timestamp = timestamp

        relative_time = (timestamp - base_timestamp) * 1000
        time_str = f"+{format_duration(relative_time)}"

        memory_str = f"{memory_mb:.1f} MB"

        print(f"{time_str:<20} {memory_str:<15} {category:<15} {operation:<30}")


def export_data(conn: sqlite3.Connection, output_file: str, time_filter: Optional[str]):
    """Export data to JSON."""
    print(f"\n{'='*80}")
    print(f"EXPORTING DATA TO: {output_file}")
    print(f"{'='*80}\n")

    query = "SELECT * FROM telemetry"
    params = []

    if time_filter:
        cutoff = datetime.now().timestamp() - parse_time_filter(time_filter)
        query += " WHERE timestamp >= ?"
        params.append(cutoff)

    query += " ORDER BY timestamp ASC"

    rows = conn.execute(query, params).fetchall()

    columns = [desc[0] for desc in conn.execute("SELECT * FROM telemetry LIMIT 1").description]

    data = []
    for row in rows:
        entry = dict(zip(columns, row))

        # Decompress details
        if entry['details']:
            entry['details'] = decompress_details(entry['details'])

        data.append(entry)

    output_path = Path(output_file)
    output_path.write_text(json.dumps(data, indent=2, default=str))

    print(f"✓ Exported {len(data)} entries to {output_file}")


def get_statistics(conn: sqlite3.Connection):
    """Print database statistics."""
    print(f"\n{'='*80}")
    print("DATABASE STATISTICS")
    print(f"{'='*80}\n")

    total = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
    db_size_mb = TELEMETRY_DB.stat().st_size / (1024 * 1024)

    oldest = conn.execute("SELECT MIN(timestamp) FROM telemetry").fetchone()[0]
    newest = conn.execute("SELECT MAX(timestamp) FROM telemetry").fetchone()[0]

    categories = conn.execute("""
        SELECT category, COUNT(*) FROM telemetry GROUP BY category ORDER BY COUNT(*) DESC
    """).fetchall()

    print(f"Total entries: {total:,}")
    print(f"Database size: {db_size_mb:.2f} MB")

    if oldest and newest:
        time_range = (newest - oldest) / 3600
        print(f"Time range: {time_range:.2f} hours")
        print(f"Oldest: {datetime.fromtimestamp(oldest).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Newest: {datetime.fromtimestamp(newest).strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\nCategories:")
    for category, count in categories:
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {category:<20} {count:>8,} ({percentage:>5.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze PokerTool performance telemetry',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_telemetry.py --slowest 20
  python analyze_telemetry.py --timeline startup --last 5m
  python analyze_telemetry.py --thread-analysis
  python analyze_telemetry.py --memory-growth
  python analyze_telemetry.py --export report.json --last 1h
  python analyze_telemetry.py --stats
        """
    )

    parser.add_argument('--slowest', type=int, metavar='N',
                        help='Show N slowest operations')
    parser.add_argument('--timeline', type=str, metavar='CATEGORY',
                        nargs='?', const='',
                        help='Show timeline of operations (optionally filtered by category)')
    parser.add_argument('--thread-analysis', action='store_true',
                        help='Show thread analysis')
    parser.add_argument('--memory-growth', action='store_true',
                        help='Show memory growth analysis')
    parser.add_argument('--last', type=str, metavar='TIME',
                        help='Filter by time (e.g., 5m, 1h, 2d)')
    parser.add_argument('--category', type=str,
                        help='Filter by category')
    parser.add_argument('--export', type=str, metavar='FILE',
                        help='Export data to JSON file')
    parser.add_argument('--stats', action='store_true',
                        help='Show database statistics')

    args = parser.parse_args()

    # Check database exists
    if not TELEMETRY_DB.exists():
        print(f"Error: Telemetry database not found at: {TELEMETRY_DB}")
        print("Run the application first to collect telemetry data.")
        sys.exit(1)

    # Connect to database
    conn = sqlite3.connect(str(TELEMETRY_DB))

    try:
        # Show statistics if requested or no other commands
        if args.stats or not any([args.slowest, args.timeline is not None, args.thread_analysis,
                                   args.memory_growth, args.export]):
            get_statistics(conn)

        # Execute requested analyses
        if args.slowest:
            print_slowest(conn, args.slowest, args.category)

        if args.timeline is not None:
            category = args.timeline if args.timeline else None
            print_timeline(conn, category, args.last)

        if args.thread_analysis:
            print_thread_analysis(conn)

        if args.memory_growth:
            print_memory_growth(conn)

        if args.export:
            export_data(conn, args.export, args.last)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
