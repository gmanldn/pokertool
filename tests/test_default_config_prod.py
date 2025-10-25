#!/usr/bin/env python3
import pytest
from src.pokertool.default_config_prod import DefaultConfigProd

class TestDefaultConfigProd:
    def test_initialization(self):
        obj = DefaultConfigProd()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = DefaultConfigProd()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = DefaultConfigProd()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
