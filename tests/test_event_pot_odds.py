#!/usr/bin/env python3
"""Tests for event filter and pot odds display."""

import pytest
from src.pokertool.event_filter import EventFilter, EventSeverity
from src.pokertool.pot_odds_display import PotOddsDisplay


class TestEventFilter:
    def test_filter_by_severity(self):
        filter = EventFilter(min_severity=EventSeverity.WARNING)
        events = [
            {'type': 'test', 'severity': EventSeverity.INFO},
            {'type': 'test', 'severity': EventSeverity.WARNING},
            {'type': 'test', 'severity': EventSeverity.ERROR}
        ]
        filtered = filter.filter_events(events)
        assert len(filtered) == 2

    def test_filter_by_type(self):
        filter = EventFilter()
        filter.set_allowed_types(['card_detection'])
        events = [
            {'type': 'card_detection', 'severity': EventSeverity.INFO},
            {'type': 'pot_detection', 'severity': EventSeverity.INFO}
        ]
        filtered = filter.filter_events(events)
        assert len(filtered) == 1


class TestPotOddsDisplay:
    def test_calculate_and_format(self):
        display = PotOddsDisplay()
        result = display.calculate_and_format(pot_size=100, bet_size=20)
        assert 'odds_ratio' in result
        assert 'odds_percent' in result
        assert result['odds_percent'] < 100

    def test_zero_bet(self):
        display = PotOddsDisplay()
        result = display.calculate_and_format(pot_size=100, bet_size=0)
        assert result['recommendation'] == 'Check'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
