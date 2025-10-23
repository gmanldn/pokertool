#!/usr/bin/env python3
"""
Detection Log Export Tool

Exports detection logs to CSV or JSON formats for external analysis, reporting,
and archival. Supports filtering by date range, event type, and confidence levels.

Usage:
    # Export all logs to JSON
    python scripts/export_detection_logs.py --output logs.json

    # Export to CSV with date filter
    python scripts/export_detection_logs.py --output logs.csv --start-date 2025-10-01 --end-date 2025-10-22

    # Export specific event types only
    python scripts/export_detection_logs.py --output pots.json --event-types pot_change,pot_detected

    # Export with confidence threshold
    python scripts/export_detection_logs.py --output high_confidence.csv --min-confidence 0.8

Author: PokerTool Team
Created: 2025-10-22
"""

import argparse
import csv
import json
import logging
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from pokertool.detection_logger import DetectionLogger, DetectionEvent
except ImportError:
    print("Warning: Could not import DetectionLogger")
    DetectionLogger = None
    DetectionEvent = None

logger = logging.getLogger(__name__)


class DetectionLogExporter:
    """
    Export detection logs to various formats
    """

    def __init__(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None
    ):
        """
        Initialize log exporter

        Args:
            start_date: Filter events after this date
            end_date: Filter events before this date
            event_types: List of event types to include (None = all)
            min_confidence: Minimum confidence threshold (0.0-1.0)
            max_confidence: Maximum confidence threshold (0.0-1.0)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.event_types = set(event_types) if event_types else None
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence

    def filter_event(self, event: Dict[str, Any]) -> bool:
        """
        Check if event passes filters

        Args:
            event: Event dictionary

        Returns:
            True if event passes all filters
        """
        # Date filter
        if self.start_date or self.end_date:
            timestamp_str = event.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if self.start_date and timestamp < self.start_date:
                        return False
                    if self.end_date and timestamp > self.end_date:
                        return False
                except (ValueError, TypeError):
                    pass

        # Event type filter
        if self.event_types:
            event_type = event.get('event_type')
            if event_type not in self.event_types:
                return False

        # Confidence filter
        confidence = event.get('confidence')
        if confidence is not None:
            if self.min_confidence is not None and confidence < self.min_confidence:
                return False
            if self.max_confidence is not None and confidence > self.max_confidence:
                return False

        return True

    def export_to_json(
        self,
        events: List[Dict[str, Any]],
        output_path: Path,
        pretty: bool = True
    ):
        """
        Export events to JSON

        Args:
            events: List of event dictionaries
            output_path: Output file path
            pretty: Pretty-print JSON with indentation
        """
        # Filter events
        filtered_events = [e for e in events if self.filter_event(e)]

        # Write JSON
        with open(output_path, 'w') as f:
            if pretty:
                json.dump(filtered_events, f, indent=2)
            else:
                json.dump(filtered_events, f)

        print(f"✓ Exported {len(filtered_events)} events to {output_path}")

    def export_to_csv(
        self,
        events: List[Dict[str, Any]],
        output_path: Path
    ):
        """
        Export events to CSV

        Args:
            events: List of event dictionaries
            output_path: Output file path
        """
        # Filter events
        filtered_events = [e for e in events if self.filter_event(e)]

        if not filtered_events:
            print("Warning: No events to export")
            return

        # Determine CSV columns from first event
        # Flatten nested 'data' dict into separate columns
        first_event = filtered_events[0]
        base_columns = ['timestamp', 'event_type', 'confidence', 'source']

        # Extract data keys from all events to get complete column set
        data_keys = set()
        for event in filtered_events:
            if 'data' in event and isinstance(event['data'], dict):
                data_keys.update(event['data'].keys())

        data_columns = sorted(data_keys)
        columns = base_columns + [f"data_{key}" for key in data_columns]

        # Write CSV
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for event in filtered_events:
                row = {
                    'timestamp': event.get('timestamp', ''),
                    'event_type': event.get('event_type', ''),
                    'confidence': event.get('confidence', ''),
                    'source': event.get('source', '')
                }

                # Flatten data dict
                if 'data' in event and isinstance(event['data'], dict):
                    for key in data_columns:
                        value = event['data'].get(key, '')
                        # Convert non-scalar values to JSON strings
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value)
                        row[f"data_{key}"] = value

                writer.writerow(row)

        print(f"✓ Exported {len(filtered_events)} events to {output_path}")

    def export_to_jsonl(
        self,
        events: List[Dict[str, Any]],
        output_path: Path
    ):
        """
        Export events to JSON Lines format (one JSON object per line)

        Useful for streaming large datasets

        Args:
            events: List of event dictionaries
            output_path: Output file path
        """
        # Filter events
        filtered_events = [e for e in events if self.filter_event(e)]

        # Write JSONL
        with open(output_path, 'w') as f:
            for event in filtered_events:
                f.write(json.dumps(event) + '\n')

        print(f"✓ Exported {len(filtered_events)} events to {output_path} (JSONL)")


def load_detection_logs_from_db() -> List[Dict[str, Any]]:
    """
    Load detection logs from database

    Returns:
        List of event dictionaries
    """
    # Mock implementation - in real usage, would query database
    # This would use production_database.py to fetch detection_events table

    print("Loading detection logs from database...")

    # Mock data for demonstration
    mock_events = [
        {
            'timestamp': '2025-10-22T10:00:00',
            'event_type': 'pot_change',
            'confidence': 0.95,
            'source': 'poker_screen_scraper_betfair',
            'data': {'pot_size': 150.0, 'previous_pot': 100.0}
        },
        {
            'timestamp': '2025-10-22T10:01:00',
            'event_type': 'card_detected',
            'confidence': 0.88,
            'source': 'card_recognizer',
            'data': {'cards': ['As', 'Kh'], 'position': 'player1'}
        },
        {
            'timestamp': '2025-10-22T10:02:00',
            'event_type': 'player_detected',
            'confidence': 0.92,
            'source': 'poker_screen_scraper_betfair',
            'data': {'player_name': 'Hero', 'position': 'BTN', 'stack': 1000.0}
        },
        {
            'timestamp': '2025-10-22T10:03:00',
            'event_type': 'pot_change',
            'confidence': 0.97,
            'source': 'poker_screen_scraper_betfair',
            'data': {'pot_size': 200.0, 'previous_pot': 150.0}
        },
        {
            'timestamp': '2025-10-22T10:04:00',
            'event_type': 'card_detected',
            'confidence': 0.65,  # Low confidence
            'source': 'card_recognizer',
            'data': {'cards': ['??', 'Qd'], 'position': 'player2'}
        }
    ]

    print(f"✓ Loaded {len(mock_events)} events")
    return mock_events


def load_detection_logs_from_file(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load detection logs from JSON file

    Args:
        input_path: Input file path

    Returns:
        List of event dictionaries
    """
    print(f"Loading detection logs from {input_path}...")

    with open(input_path, 'r') as f:
        events = json.load(f)

    print(f"✓ Loaded {len(events)} events")
    return events


def main():
    parser = argparse.ArgumentParser(
        description="Export detection logs to CSV or JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all logs to JSON
  %(prog)s --output logs.json

  # Export to CSV with date filter
  %(prog)s --output logs.csv --start-date 2025-10-01 --end-date 2025-10-22

  # Export specific event types
  %(prog)s --output pots.json --event-types pot_change,pot_detected

  # Export with confidence threshold
  %(prog)s --output high_confidence.csv --min-confidence 0.8

  # Export to JSON Lines (streaming)
  %(prog)s --output logs.jsonl --format jsonl

  # Load from existing JSON file and re-export with filters
  %(prog)s --input old_logs.json --output filtered.csv --event-types card_detected
        """
    )

    parser.add_argument(
        '--input',
        type=Path,
        help='Input JSON file (if not specified, loads from database)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output file path (.json, .csv, or .jsonl)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'jsonl'],
        help='Output format (auto-detected from file extension if not specified)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date filter (ISO format: 2025-10-01 or 2025-10-01T10:00:00)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date filter (ISO format: 2025-10-22 or 2025-10-22T23:59:59)'
    )
    parser.add_argument(
        '--event-types',
        type=str,
        help='Comma-separated list of event types to include (e.g., pot_change,card_detected)'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        help='Minimum confidence threshold (0.0-1.0)'
    )
    parser.add_argument(
        '--max-confidence',
        type=float,
        help='Maximum confidence threshold (0.0-1.0)'
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output (default: true for .json, false for .jsonl)',
        default=None
    )

    args = parser.parse_args()

    try:
        # Parse date filters
        start_date = None
        end_date = None
        if args.start_date:
            start_date = datetime.fromisoformat(args.start_date)
        if args.end_date:
            end_date = datetime.fromisoformat(args.end_date)

        # Parse event types
        event_types = None
        if args.event_types:
            event_types = [t.strip() for t in args.event_types.split(',')]

        # Create exporter
        exporter = DetectionLogExporter(
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            min_confidence=args.min_confidence,
            max_confidence=args.max_confidence
        )

        # Load events
        if args.input:
            events = load_detection_logs_from_file(args.input)
        else:
            events = load_detection_logs_from_db()

        # Determine output format
        output_format = args.format
        if not output_format:
            # Auto-detect from extension
            suffix = args.output.suffix.lower()
            if suffix == '.json':
                output_format = 'json'
            elif suffix == '.csv':
                output_format = 'csv'
            elif suffix == '.jsonl':
                output_format = 'jsonl'
            else:
                print(f"Error: Unknown file extension '{suffix}'. Use --format to specify.")
                return 1

        # Export
        print(f"\nExporting to {output_format.upper()} format...")

        if output_format == 'json':
            pretty = args.pretty if args.pretty is not None else True
            exporter.export_to_json(events, args.output, pretty=pretty)
        elif output_format == 'csv':
            exporter.export_to_csv(events, args.output)
        elif output_format == 'jsonl':
            exporter.export_to_jsonl(events, args.output)

        # Print summary
        print("\nExport Summary:")
        print(f"  Output: {args.output}")
        print(f"  Format: {output_format.upper()}")
        if start_date:
            print(f"  Start Date: {start_date}")
        if end_date:
            print(f"  End Date: {end_date}")
        if event_types:
            print(f"  Event Types: {', '.join(event_types)}")
        if args.min_confidence:
            print(f"  Min Confidence: {args.min_confidence}")
        if args.max_confidence:
            print(f"  Max Confidence: {args.max_confidence}")

        return 0

    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
