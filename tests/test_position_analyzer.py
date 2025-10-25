#!/usr/bin/env python3
"""Tests for Position Analyzer"""

import pytest
from src.pokertool.position_analyzer import PositionAnalyzer


class TestPositionAnalyzer:
    def test_get_position_index(self):
        assert PositionAnalyzer.get_position_index("BTN") == 5

    def test_is_early_position(self):
        assert PositionAnalyzer.is_early_position("UTG") is True
        assert PositionAnalyzer.is_early_position("BTN") is False

    def test_is_late_position(self):
        assert PositionAnalyzer.is_late_position("BTN") is True
        assert PositionAnalyzer.is_late_position("UTG") is False

    def test_is_blind(self):
        assert PositionAnalyzer.is_blind("BB") is True
        assert PositionAnalyzer.is_blind("BTN") is False

    def test_get_position_strength(self):
        assert PositionAnalyzer.get_position_strength("BTN") > 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
