#!/usr/bin/env python3
import pytest
from src.pokertool.window_detection_all import WindowDetectionAll

class TestWindowDetectionAll:
    def test_initialization(self):
        obj = WindowDetectionAll()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = WindowDetectionAll()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = WindowDetectionAll()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
