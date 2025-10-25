#!/usr/bin/env python3
import pytest
from src.pokertool.table_zoom_support import TableZoomSupport

class TestTableZoomSupport:
    def test_initialization(self):
        obj = TableZoomSupport()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = TableZoomSupport()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = TableZoomSupport()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
