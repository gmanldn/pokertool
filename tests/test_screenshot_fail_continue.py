#!/usr/bin/env python3
import pytest
from src.pokertool.screenshot_fail_continue import ScreenshotFailContinue

class TestScreenshotFailContinue:
    def test_initialization(self):
        obj = ScreenshotFailContinue()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ScreenshotFailContinue()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ScreenshotFailContinue()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
