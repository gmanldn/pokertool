"""
Event Deduplication System

Prevents duplicate detection events from being emitted to reduce WebSocket overhead
and improve client performance. Uses content hashing and time-based windowing.

Author: PokerTool Team
Created: 2025-10-22
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class EventSignature:
    """
    Unique signature for an event based on content hash
    """
    event_type: str
    content_hash: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash((self.event_type, self.content_hash))

    def __eq__(self, other):
        if not isinstance(other, EventSignature):
            return False
        return self.event_type == other.event_type and self.content_hash == other.content_hash


class EventDeduplicator:
    """
    Deduplicates events using content hashing and time-based windowing

    Features:
    - Content-based hashing (SHA256)
    - Configurable deduplication window
    - Per-event-type tracking
    - Automatic cleanup of old signatures
    - Thread-safe operations
    - Metrics tracking
    """

    def __init__(
        self,
        window_seconds: float = 1.0,
        cleanup_interval_seconds: float = 10.0,
        max_signatures_per_type: int = 1000
    ):
        """
        Initialize event deduplicator

        Args:
            window_seconds: Time window for deduplication (seconds)
            cleanup_interval_seconds: How often to cleanup old signatures
            max_signatures_per_type: Max signatures to keep per event type
        """
        self.window_seconds = window_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.max_signatures_per_type = max_signatures_per_type

        # Event signatures by type
        self.signatures: Dict[str, Set[EventSignature]] = defaultdict(set)

        # Timestamps for cleanup
        self.last_cleanup_time = time.time()

        # Thread safety
        self.lock = Lock()

        # Metrics
        self.total_events_seen = 0
        self.duplicate_events_blocked = 0
        self.unique_events_passed = 0
        self.cleanup_runs = 0

        logger.info(f"EventDeduplicator initialized: window={window_seconds}s, "
                   f"cleanup_interval={cleanup_interval_seconds}s")

    def _generate_content_hash(self, event_data: Dict[str, Any]) -> str:
        """
        Generate SHA256 hash of event content

        Args:
            event_data: Event data dictionary

        Returns:
            Hex digest of SHA256 hash
        """
        # Sort keys for consistent hashing
        json_str = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]  # First 16 chars

    def should_emit(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        force: bool = False
    ) -> bool:
        """
        Check if event should be emitted or is a duplicate

        Args:
            event_type: Type of event (e.g., "pot_change", "card_detected")
            event_data: Event data dictionary
            force: If True, always emit (bypass deduplication)

        Returns:
            True if event should be emitted, False if duplicate
        """
        self.total_events_seen += 1

        # Force emit bypasses deduplication
        if force:
            self.unique_events_passed += 1
            return True

        with self.lock:
            # Periodic cleanup
            self._maybe_cleanup()

            # Generate signature
            content_hash = self._generate_content_hash(event_data)
            current_time = time.time()

            # Check for recent duplicate
            if event_type in self.signatures:
                for sig in self.signatures[event_type]:
                    # Same content within window = duplicate
                    if (sig.content_hash == content_hash and
                        current_time - sig.timestamp < self.window_seconds):
                        self.duplicate_events_blocked += 1
                        logger.debug(f"Duplicate event blocked: {event_type} "
                                   f"(hash: {content_hash[:8]}...)")
                        return False

            # Not a duplicate - add signature
            new_sig = EventSignature(
                event_type=event_type,
                content_hash=content_hash,
                timestamp=current_time
            )
            self.signatures[event_type].add(new_sig)

            # Enforce max signatures per type
            if len(self.signatures[event_type]) > self.max_signatures_per_type:
                self._trim_signatures(event_type)

            self.unique_events_passed += 1
            return True

    def _maybe_cleanup(self):
        """
        Cleanup old signatures if interval has elapsed
        """
        current_time = time.time()
        if current_time - self.last_cleanup_time >= self.cleanup_interval_seconds:
            self._cleanup_old_signatures()
            self.last_cleanup_time = current_time
            self.cleanup_runs += 1

    def _cleanup_old_signatures(self):
        """
        Remove signatures older than the deduplication window
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        total_removed = 0

        for event_type in list(self.signatures.keys()):
            old_sigs = {
                sig for sig in self.signatures[event_type]
                if sig.timestamp < cutoff_time
            }

            if old_sigs:
                self.signatures[event_type] -= old_sigs
                total_removed += len(old_sigs)

            # Remove empty sets
            if not self.signatures[event_type]:
                del self.signatures[event_type]

        if total_removed > 0:
            logger.debug(f"Cleaned up {total_removed} old event signatures")

    def _trim_signatures(self, event_type: str):
        """
        Trim signatures for a specific event type to max size

        Keeps most recent signatures

        Args:
            event_type: Event type to trim
        """
        sigs = self.signatures[event_type]

        if len(sigs) > self.max_signatures_per_type:
            # Sort by timestamp, keep most recent
            sorted_sigs = sorted(sigs, key=lambda s: s.timestamp, reverse=True)
            self.signatures[event_type] = set(sorted_sigs[:self.max_signatures_per_type])

            removed = len(sigs) - self.max_signatures_per_type
            logger.debug(f"Trimmed {removed} old signatures for {event_type}")

    def clear(self, event_type: Optional[str] = None):
        """
        Clear signatures (useful for testing or manual reset)

        Args:
            event_type: If provided, clear only this type. Otherwise clear all.
        """
        with self.lock:
            if event_type:
                if event_type in self.signatures:
                    del self.signatures[event_type]
                    logger.debug(f"Cleared signatures for {event_type}")
            else:
                self.signatures.clear()
                logger.debug("Cleared all event signatures")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get deduplication metrics

        Returns:
            Dictionary with metrics
        """
        with self.lock:
            total_signatures = sum(len(sigs) for sigs in self.signatures.values())

            dedup_rate = 0.0
            if self.total_events_seen > 0:
                dedup_rate = (self.duplicate_events_blocked / self.total_events_seen) * 100

            return {
                "total_events_seen": self.total_events_seen,
                "unique_events_passed": self.unique_events_passed,
                "duplicate_events_blocked": self.duplicate_events_blocked,
                "deduplication_rate_pct": round(dedup_rate, 2),
                "active_signatures": total_signatures,
                "event_types_tracked": len(self.signatures),
                "cleanup_runs": self.cleanup_runs,
                "window_seconds": self.window_seconds
            }

    def get_signature_counts(self) -> Dict[str, int]:
        """
        Get count of signatures per event type

        Returns:
            Dictionary mapping event type to signature count
        """
        with self.lock:
            return {
                event_type: len(sigs)
                for event_type, sigs in self.signatures.items()
            }


# Global deduplicator instance
_deduplicator: Optional[EventDeduplicator] = None


def get_deduplicator(
    window_seconds: float = 1.0,
    cleanup_interval_seconds: float = 10.0,
    max_signatures_per_type: int = 1000
) -> EventDeduplicator:
    """
    Get or create global event deduplicator

    Args:
        window_seconds: Deduplication window (seconds)
        cleanup_interval_seconds: Cleanup interval (seconds)
        max_signatures_per_type: Max signatures per event type

    Returns:
        Global EventDeduplicator instance
    """
    global _deduplicator

    if _deduplicator is None:
        _deduplicator = EventDeduplicator(
            window_seconds=window_seconds,
            cleanup_interval_seconds=cleanup_interval_seconds,
            max_signatures_per_type=max_signatures_per_type
        )

    return _deduplicator
