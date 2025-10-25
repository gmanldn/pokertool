#!/usr/bin/env python3
import pytest
from src.pokertool.table_detection_accuracy import TableDetectionAccuracy

class TestTableDetectionAccuracy:
    def test_initialization(self):
        obj = TableDetectionAccuracy()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = TableDetectionAccuracy()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = TableDetectionAccuracy()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
