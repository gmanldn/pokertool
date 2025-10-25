#!/usr/bin/env python3
import pytest
from src.pokertool.hidden_window_handling import HiddenWindowHandling

class TestHiddenWindowHandling:
    def test_initialization(self):
        obj = HiddenWindowHandling()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = HiddenWindowHandling()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = HiddenWindowHandling()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
