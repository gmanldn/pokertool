#!/usr/bin/env python3
import pytest
from src.pokertool.window_loss_recovery import WindowLossRecovery

class TestWindowLossRecovery:
    def test_initialization(self):
        obj = WindowLossRecovery()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = WindowLossRecovery()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = WindowLossRecovery()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
