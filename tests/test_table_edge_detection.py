#!/usr/bin/env python3
import pytest
from src.pokertool.table_edge_detection import TableEdgeDetection

class TestTableEdgeDetection:
    def test_initialization(self):
        obj = TableEdgeDetection()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = TableEdgeDetection()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = TableEdgeDetection()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
