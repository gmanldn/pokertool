#!/usr/bin/env python3
"""Tests for blind_ante_detector module."""

import pytest
from src.pokertool.blind_ante_detector import BlindAnteDetector, get_blind_ante_detector


class TestBlindAnteDetector:
    """Test blind and ante detection."""

    def test_detect_blinds_format1(self):
        """Test 'Blinds: $1/$2' format."""
        detector = BlindAnteDetector()
        result = detector.detect_blinds("Blinds: $1/$2")
        assert result == (1.0, 2.0)

    def test_detect_blinds_format2(self):
        """Test separate SB/BB format."""
        detector = BlindAnteDetector()
        result = detector.detect_blinds("SB: $0.50 BB: $1.00")
        assert result == (0.50, 1.00)

    def test_detect_blinds_none(self):
        """Test no blinds in text."""
        detector = BlindAnteDetector()
        result = detector.detect_blinds("No blind info here")
        assert result is None

    def test_detect_ante(self):
        """Test ante detection."""
        detector = BlindAnteDetector()
        result = detector.detect_ante("Ante: $0.25")
        assert result == 0.25

    def test_detect_ante_none(self):
        """Test no ante in text."""
        detector = BlindAnteDetector()
        result = detector.detect_ante("No ante here")
        assert result is None

    def test_detect_all(self):
        """Test combined detection."""
        detector = BlindAnteDetector()
        result = detector.detect_all("Blinds: $5/$10 Ante: $1")
        assert result['small_blind'] == 5.0
        assert result['big_blind'] == 10.0
        assert result['ante'] == 1.0

    def test_get_stake_level(self):
        """Test stake level formatting."""
        detector = BlindAnteDetector()
        assert detector.get_stake_level(1.0, 2.0) == "$1/$2"
        assert detector.get_stake_level(0.50, 1.0) == "$0.50/$1"

    def test_global_detector(self):
        """Test global singleton."""
        d1 = get_blind_ante_detector()
        d2 = get_blind_ante_detector()
        assert d1 is d2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
