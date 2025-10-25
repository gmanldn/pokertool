#!/usr/bin/env python3
import pytest
from src.pokertool.virtual_desktop_support import VirtualDesktopSupport

class TestVirtualDesktopSupport:
    def test_initialization(self):
        obj = VirtualDesktopSupport()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = VirtualDesktopSupport()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = VirtualDesktopSupport()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
