#!/usr/bin/env python3
import pytest
from src.pokertool.screenshot_speed_100ms import ScreenshotSpeed100Ms

class TestScreenshotSpeed100Ms:
    def test_initialization(self):
        obj = ScreenshotSpeed100Ms()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ScreenshotSpeed100Ms()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ScreenshotSpeed100Ms()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
