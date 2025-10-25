#!/usr/bin/env python3
import pytest
from src.pokertool.multi_monitor_support import MultiMonitorSupport

class TestMultiMonitorSupport:
    def test_initialization(self):
        obj = MultiMonitorSupport()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = MultiMonitorSupport()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = MultiMonitorSupport()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
