#!/usr/bin/env python3
import pytest
from src.pokertool.table_region_extraction import TableRegionExtraction

class TestTableRegionExtraction:
    def test_initialization(self):
        obj = TableRegionExtraction()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = TableRegionExtraction()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = TableRegionExtraction()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
