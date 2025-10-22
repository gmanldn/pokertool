"""
Unit Tests for Event Deduplicator

Tests event deduplication logic, metrics, and cleanup.

Author: PokerTool Team
Created: 2025-10-22
"""

import pytest
import time
from pokertool.event_deduplicator import EventDeduplicator, EventSignature


class TestEventDeduplicator:
    """Test suite for EventDeduplicator"""

    @pytest.fixture
    def dedup(self):
        """Create EventDeduplicator with short window for testing"""
        return EventDeduplicator(
            window_seconds=0.5,
            cleanup_interval_seconds=1.0,
            max_signatures_per_type=100
        )

    def test_first_event_passes(self, dedup):
        """First event of a type should always pass"""
        event_data = {"pot_size": 100, "players": 6}

        should_emit = dedup.should_emit("pot_change", event_data)

        assert should_emit is True
        assert dedup.unique_events_passed == 1
        assert dedup.duplicate_events_blocked == 0

    def test_duplicate_event_blocked(self, dedup):
        """Duplicate event within window should be blocked"""
        event_data = {"pot_size": 100, "players": 6}

        # First event
        assert dedup.should_emit("pot_change", event_data) is True

        # Duplicate immediately after
        assert dedup.should_emit("pot_change", event_data) is False

        # Metrics
        assert dedup.unique_events_passed == 1
        assert dedup.duplicate_events_blocked == 1

    def test_different_event_types_independent(self, dedup):
        """Different event types are tracked independently"""
        event_data = {"value": 123}

        # Same data, different types
        assert dedup.should_emit("pot_change", event_data) is True
        assert dedup.should_emit("card_detected", event_data) is True

        # Both should pass
        assert dedup.unique_events_passed == 2
        assert dedup.duplicate_events_blocked == 0

    def test_different_content_not_duplicate(self, dedup):
        """Events with different content are not duplicates"""
        event1 = {"pot_size": 100}
        event2 = {"pot_size": 200}

        assert dedup.should_emit("pot_change", event1) is True
        assert dedup.should_emit("pot_change", event2) is True

        # Both pass
        assert dedup.unique_events_passed == 2
        assert dedup.duplicate_events_blocked == 0

    def test_duplicate_after_window_passes(self, dedup):
        """Duplicate event after window expires should pass"""
        event_data = {"pot_size": 100}

        # First event
        assert dedup.should_emit("pot_change", event_data) is True

        # Wait for window to expire (0.5s)
        time.sleep(0.6)

        # Same event after window - should pass
        assert dedup.should_emit("pot_change", event_data) is True

        # Both passed, no duplicates
        assert dedup.unique_events_passed == 2
        assert dedup.duplicate_events_blocked == 0

    def test_force_bypasses_deduplication(self, dedup):
        """Force flag bypasses deduplication"""
        event_data = {"pot_size": 100}

        # First event
        assert dedup.should_emit("pot_change", event_data) is True

        # Force emit duplicate
        assert dedup.should_emit("pot_change", event_data, force=True) is True

        # Both passed
        assert dedup.unique_events_passed == 2
        assert dedup.duplicate_events_blocked == 0

    def test_content_hash_generation(self, dedup):
        """Content hashing is consistent and order-independent"""
        # Same data, different order
        event1 = {"a": 1, "b": 2, "c": 3}
        event2 = {"c": 3, "a": 1, "b": 2}

        hash1 = dedup._generate_content_hash(event1)
        hash2 = dedup._generate_content_hash(event2)

        assert hash1 == hash2, "Hashes should be same regardless of key order"

    def test_cleanup_removes_old_signatures(self, dedup):
        """Old signatures are cleaned up after cleanup interval"""
        event_data = {"value": 123}

        # Add signature
        dedup.should_emit("test_event", event_data)

        # Verify signature exists
        assert len(dedup.signatures["test_event"]) == 1

        # Wait for window + cleanup interval
        time.sleep(1.5)

        # Trigger cleanup by emitting new event
        dedup.should_emit("other_event", {})

        # Cleanup should have run
        assert dedup.cleanup_runs >= 1

    def test_max_signatures_enforced(self):
        """Max signatures per type is enforced"""
        dedup = EventDeduplicator(
            window_seconds=10.0,  # Long window
            max_signatures_per_type=5  # Small limit
        )

        # Add 10 different events
        for i in range(10):
            dedup.should_emit("test_event", {"value": i})

        # Should only keep 5 most recent
        assert len(dedup.signatures["test_event"]) <= 5

    def test_clear_specific_event_type(self, dedup):
        """Clear signatures for specific event type"""
        dedup.should_emit("type1", {"data": 1})
        dedup.should_emit("type2", {"data": 2})

        # Clear type1
        dedup.clear("type1")

        assert "type1" not in dedup.signatures
        assert "type2" in dedup.signatures

    def test_clear_all_event_types(self, dedup):
        """Clear all signatures"""
        dedup.should_emit("type1", {"data": 1})
        dedup.should_emit("type2", {"data": 2})

        # Clear all
        dedup.clear()

        assert len(dedup.signatures) == 0

    def test_metrics_tracking(self, dedup):
        """Metrics are tracked correctly"""
        event_data = {"value": 123}

        # 3 unique, 2 duplicates
        dedup.should_emit("event1", event_data)  # Unique
        dedup.should_emit("event1", event_data)  # Duplicate
        dedup.should_emit("event2", event_data)  # Unique
        dedup.should_emit("event2", event_data)  # Duplicate
        dedup.should_emit("event3", event_data)  # Unique

        metrics = dedup.get_metrics()

        assert metrics["total_events_seen"] == 5
        assert metrics["unique_events_passed"] == 3
        assert metrics["duplicate_events_blocked"] == 2
        assert metrics["deduplication_rate_pct"] == 40.0  # 2/5 = 40%
        assert metrics["event_types_tracked"] == 3

    def test_signature_counts(self, dedup):
        """Signature counts are tracked per event type"""
        dedup.should_emit("type1", {"a": 1})
        dedup.should_emit("type1", {"a": 2})
        dedup.should_emit("type2", {"b": 1})

        counts = dedup.get_signature_counts()

        assert counts["type1"] == 2
        assert counts["type2"] == 1

    def test_thread_safety(self, dedup):
        """Deduplicator is thread-safe"""
        import threading

        results = []

        def emit_events():
            for i in range(10):
                result = dedup.should_emit("test", {"value": i})
                results.append(result)

        # Run 3 threads concurrently
        threads = [threading.Thread(target=emit_events) for _ in range(3)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All events should be processed without errors
        assert len(results) == 30

    def test_event_signature_equality(self):
        """EventSignature equality and hashing work correctly"""
        sig1 = EventSignature("pot_change", "abc123", 1.0)
        sig2 = EventSignature("pot_change", "abc123", 2.0)  # Different timestamp
        sig3 = EventSignature("pot_change", "def456", 1.0)  # Different hash

        # Same type + hash = equal (timestamp doesn't matter)
        assert sig1 == sig2
        assert hash(sig1) == hash(sig2)

        # Different hash = not equal
        assert sig1 != sig3
        assert hash(sig1) != hash(sig3)

    def test_high_volume_deduplication(self, dedup):
        """Handles high volume of events efficiently"""
        # Emit 1000 events, half duplicates
        for i in range(500):
            dedup.should_emit("event", {"value": i})  # Unique
            dedup.should_emit("event", {"value": i})  # Duplicate

        metrics = dedup.get_metrics()

        assert metrics["unique_events_passed"] == 500
        assert metrics["duplicate_events_blocked"] == 500
        assert metrics["deduplication_rate_pct"] == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
