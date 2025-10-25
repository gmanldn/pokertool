#!/usr/bin/env python3
import pytest
from src.pokertool.card_position_tracking import CardPositionTracking

class TestCardPositionTracking:
    def test_initialization(self):
        obj = CardPositionTracking()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = CardPositionTracking()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = CardPositionTracking()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
