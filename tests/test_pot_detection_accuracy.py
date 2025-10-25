#!/usr/bin/env python3
import pytest
from src.pokertool.pot_detection_accuracy import PotDetectionAccuracy

class TestPotDetectionAccuracy:
    def test_initialization(self):
        obj = PotDetectionAccuracy()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = PotDetectionAccuracy()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = PotDetectionAccuracy()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
