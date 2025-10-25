#!/usr/bin/env python3
import pytest
from src.pokertool.screenshot_quality import ScreenshotQuality

class TestScreenshotQuality:
    def test_initialization(self):
        obj = ScreenshotQuality()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ScreenshotQuality()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ScreenshotQuality()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
