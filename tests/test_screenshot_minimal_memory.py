#!/usr/bin/env python3
import pytest
from src.pokertool.screenshot_minimal_memory import ScreenshotMinimalMemory

class TestScreenshotMinimalMemory:
    def test_initialization(self):
        obj = ScreenshotMinimalMemory()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ScreenshotMinimalMemory()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ScreenshotMinimalMemory()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
