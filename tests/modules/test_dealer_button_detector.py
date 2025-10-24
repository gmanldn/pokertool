"""Tests for dealer button detection."""

import pytest
import numpy as np
import cv2
from pokertool.dealer_button_detector import DealerButtonDetector


class TestDealerButtonDetector:
    """Test dealer button detection functionality."""

    def test_detect_circle_button(self):
        """Test circle-based button detection."""
        detector = DealerButtonDetector()
        # Create image with white circle
        roi = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.circle(roi, (50, 50), 20, (255, 255, 255), -1)

        conf = detector._detect_circle_button(roi)
        assert conf >= 0.90

    def test_detect_color_button_white(self):
        """Test color-based detection for white button."""
        detector = DealerButtonDetector()
        roi = np.ones((100, 100, 3), dtype=np.uint8) * 255

        conf = detector._detect_color_button(roi)
        assert conf >= 0.85

    def test_button_movement_validation(self):
        """Test button movement validation."""
        detector = DealerButtonDetector()

        # Valid clockwise movement
        assert detector.track_button_movement(0, 1, 9) is True
        assert detector.track_button_movement(8, 0, 9) is True

        # Invalid movement
        assert detector.track_button_movement(0, 5, 9) is False

    def test_detect_button_from_seats(self):
        """Test button detection from seat positions."""
        detector = DealerButtonDetector()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)

        # Add button-like circle at seat 2
        cv2.circle(image, (400, 300), 20, (255, 255, 255), -1)

        seats = [
            (100, 100, 80, 80),
            (300, 100, 80, 80),
            (360, 260, 80, 80),  # Seat with button
        ]

        seat, conf = detector.detect_button(image, seats)
        assert seat == 2
        assert conf > 0.0

    def test_detect_no_button(self):
        """Test when no button is present."""
        detector = DealerButtonDetector()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        seats = [(100, 100, 80, 80)]

        seat, conf = detector.detect_button(image, seats)
        assert conf < 0.5

    def test_button_radius_range(self):
        """Test button detection within radius range."""
        detector = DealerButtonDetector()
        assert detector.button_radius_range == (10, 40)

    def test_button_colors_defined(self):
        """Test button colors are defined."""
        detector = DealerButtonDetector()
        assert len(detector.button_colors) >= 3

    def test_min_confidence_threshold(self):
        """Test minimum confidence threshold."""
        detector = DealerButtonDetector()
        assert detector.min_confidence == 0.98

    def test_track_button_wrap_around(self):
        """Test button movement wrap around at table."""
        detector = DealerButtonDetector()
        # Last seat to first seat
        assert detector.track_button_movement(8, 0, 9) is True

    def test_track_button_none_previous(self):
        """Test button tracking with no previous position."""
        detector = DealerButtonDetector()
        assert detector.track_button_movement(None, 3, 9) is True
