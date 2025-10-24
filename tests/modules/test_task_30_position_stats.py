"""Tests for position-aware stats."""
import pytest
from pokertool.position_aware_stats import PositionAwareStats

def test_position_stats():
    stats = PositionAwareStats()
    stats.record_hand("BTN", True, True)
    result = stats.get_stats("BTN")
    assert result["vpip"] == 1.0
    assert result["pfr"] == 1.0
    assert result["hands"] == 1
