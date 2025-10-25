#!/usr/bin/env python3
import pytest
from src.pokertool.window_finder import WindowFinder

class TestWindowFinder:
    def test_initialization(self):
        obj = WindowFinder()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = WindowFinder()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = WindowFinder()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
