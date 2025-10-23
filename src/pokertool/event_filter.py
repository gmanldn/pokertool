#!/usr/bin/env python3
"""Event filtering by type and severity."""

from typing import List, Dict, Any, Optional
from enum import Enum


class EventSeverity(Enum):
    """Event severity levels."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class EventFilter:
    """Filter events by type and severity."""

    def __init__(self, min_severity: EventSeverity = EventSeverity.INFO):
        """Initialize filter with minimum severity."""
        self.min_severity = min_severity
        self.allowed_types: Optional[set] = None  # None = all types

    def set_allowed_types(self, types: List[str]):
        """Set which event types to allow."""
        self.allowed_types = set(types) if types else None

    def filter_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter events by type and severity.

        Args:
            events: List of event dicts with 'type' and 'severity' keys

        Returns:
            Filtered event list
        """
        filtered = []
        for event in events:
            if not self._should_include(event):
                continue
            filtered.append(event)
        return filtered

    def _should_include(self, event: Dict[str, Any]) -> bool:
        """Check if event should be included."""
        # Check severity
        event_severity = event.get('severity', EventSeverity.INFO)
        if isinstance(event_severity, str):
            event_severity = EventSeverity[event_severity.upper()]
        if event_severity.value < self.min_severity.value:
            return False

        # Check type
        if self.allowed_types is not None:
            event_type = event.get('type', '')
            if event_type not in self.allowed_types:
                return False

        return True


_filter_instance: Optional[EventFilter] = None

def get_event_filter() -> EventFilter:
    """Get global event filter."""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = EventFilter()
    return _filter_instance
