#!/usr/bin/env python3
import pytest
from src.pokertool.multi_platform_support import MultiPlatformSupport

class TestMultiPlatformSupport:
    def test_initialization(self):
        obj = MultiPlatformSupport()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = MultiPlatformSupport()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = MultiPlatformSupport()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
