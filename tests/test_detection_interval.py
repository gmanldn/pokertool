#!/usr/bin/env python3
import pytest
from src.pokertool.detection_interval import DetectionInterval

class TestDetectionInterval:
    def test_initialization(self):
        obj = DetectionInterval()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = DetectionInterval()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = DetectionInterval()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
