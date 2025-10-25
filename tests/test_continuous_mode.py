#!/usr/bin/env python3
import pytest
from src.pokertool.continuous_mode import ContinuousMode

class TestContinuousMode:
    def test_initialization(self):
        obj = ContinuousMode()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ContinuousMode()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ContinuousMode()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
