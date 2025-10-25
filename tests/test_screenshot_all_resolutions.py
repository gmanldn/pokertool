#!/usr/bin/env python3
import pytest
from src.pokertool.screenshot_all_resolutions import ScreenshotAllResolutions

class TestScreenshotAllResolutions:
    def test_initialization(self):
        obj = ScreenshotAllResolutions()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ScreenshotAllResolutions()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ScreenshotAllResolutions()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
