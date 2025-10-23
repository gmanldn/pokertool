#!/usr/bin/env python3
"""Quick tests for new detector modules."""

import pytest
import numpy as np
from src.pokertool.suit_color_detector import SuitColorDetector
from src.pokertool.card_history_tracker import CardHistoryTracker
from src.pokertool.position_validator import PositionValidator


class TestSuitColorDetector:
    def test_red_suit(self):
        detector = SuitColorDetector()
        red_img = np.array([[[200, 50, 50]]])
        result = detector.detect_suit_by_color(red_img)
        assert result == 'h'

    def test_black_suit(self):
        detector = SuitColorDetector()
        black_img = np.array([[[50, 50, 50]]])
        result = detector.detect_suit_by_color(black_img)
        assert result == 's'


class TestCardHistoryTracker:
    def test_add_card(self):
        tracker = CardHistoryTracker()
        tracker.start_new_hand()
        assert tracker.add_card('As') == True
        assert tracker.add_card('Kh') == True

    def test_duplicate_detection(self):
        tracker = CardHistoryTracker()
        tracker.start_new_hand()
        tracker.add_card('As')
        assert tracker.add_card('As') == False
        assert len(tracker.get_anomalies()) > 0


class TestPositionValidator:
    def test_validate_positions(self):
        validator = PositionValidator()
        positions = {0: 'BTN', 1: 'SB', 2: 'BB'}
        assert validator.validate_positions(0, positions) == True

    def test_calculate_position(self):
        validator = PositionValidator()
        assert validator.calculate_position(0, 0, 6) == 'BTN'
        assert validator.calculate_position(1, 0, 6) == 'SB'
        assert validator.calculate_position(2, 0, 6) == 'BB'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
