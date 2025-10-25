#!/usr/bin/env python3
import pytest
from src.pokertool.window_focus_detection import WindowFocusDetection

class TestWindowFocusDetection:
    def test_initialization(self):
        obj = WindowFocusDetection()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = WindowFocusDetection()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = WindowFocusDetection()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
