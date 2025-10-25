#!/usr/bin/env python3
import pytest
from src.pokertool.screenshot_no_slowdown import ScreenshotNoSlowdown

class TestScreenshotNoSlowdown:
    def test_initialization(self):
        obj = ScreenshotNoSlowdown()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ScreenshotNoSlowdown()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ScreenshotNoSlowdown()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
