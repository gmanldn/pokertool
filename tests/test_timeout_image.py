#!/usr/bin/env python3
"""Tests for timeout detector and image preprocessor."""

import pytest
import numpy as np
import time
from src.pokertool.timeout_detector import TimeoutDetector
from src.pokertool.image_preprocessor import ImagePreprocessor, AnimationHandler


class TestTimeoutDetector:
    def test_start_timer(self):
        detector = TimeoutDetector()
        detector.start_action_timer(30.0)
        assert detector.get_time_remaining() > 29

    def test_warning_threshold(self):
        detector = TimeoutDetector(warning_threshold=5.0)
        detector.start_action_timer(4.0)
        time.sleep(0.1)
        assert detector.is_warning_threshold()


class TestImagePreprocessor:
    def test_remove_glare(self):
        preprocessor = ImagePreprocessor()
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = preprocessor.remove_glare(img)
        assert result.shape == img.shape

    def test_enhance_card(self):
        preprocessor = ImagePreprocessor()
        img = np.ones((50, 50, 3), dtype=np.uint8) * 128
        result = preprocessor.enhance_card(img)
        assert result.shape == img.shape


class TestAnimationHandler:
    def test_stability(self):
        handler = AnimationHandler(stability_threshold=2)
        img = np.zeros((10, 10, 3), dtype=np.uint8)

        assert not handler.is_stable(img)
        assert not handler.is_stable(img)
        assert handler.is_stable(img)  # Third time should be stable


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
