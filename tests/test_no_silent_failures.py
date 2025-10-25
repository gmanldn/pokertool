#!/usr/bin/env python3
import pytest
from src.pokertool.no_silent_failures import NoSilentFailures

class TestNoSilentFailures:
    def test_initialization(self):
        obj = NoSilentFailures()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = NoSilentFailures()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = NoSilentFailures()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
