#!/usr/bin/env python3
import pytest
from src.pokertool.card_detection_accuracy import CardDetectionAccuracy

class TestCardDetectionAccuracy:
    def test_initialization(self):
        obj = CardDetectionAccuracy()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = CardDetectionAccuracy()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = CardDetectionAccuracy()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
