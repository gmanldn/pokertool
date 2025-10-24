"""Tests for seat change detection."""
import pytest
from pokertool.seat_change_detector import SeatChangeDetector

def test_seat_change_detection():
    detector = SeatChangeDetector()
    assert detector.detect_seat_change("player1", 1) is False
    assert detector.detect_seat_change("player1", 3) is True
