#!/usr/bin/env python3
import pytest
from src.pokertool.table_layout_variations import TableLayoutVariations

class TestTableLayoutVariations:
    def test_initialization(self):
        obj = TableLayoutVariations()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = TableLayoutVariations()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = TableLayoutVariations()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
