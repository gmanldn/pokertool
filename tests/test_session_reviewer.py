#!/usr/bin/env python3
"""Tests for session reviewer."""

import pytest
from src.pokertool.session_reviewer import SessionReviewer


class TestSessionReviewer:
    def test_generate_summary(self):
        reviewer = SessionReviewer()
        hands = [
            {'hole_cards': 'AA', 'pot': 100, 'profit': 50, 'result': 'win'},
            {'hole_cards': '72o', 'pot': 200, 'profit': -100, 'result': 'loss'},
        ]
        summary = reviewer.generate_summary(hands)

        assert 'key_hands' in summary
        assert 'mistakes' in summary
        assert 'wins' in summary
        assert 'improvements' in summary
        assert summary['stats']['total_hands'] == 2

    def test_empty_hands(self):
        reviewer = SessionReviewer()
        summary = reviewer.generate_summary([])
        assert summary['stats'] == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
