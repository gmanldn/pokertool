#!/usr/bin/env python3
import pytest
from src.pokertool.config_versioning import ConfigVersioning

class TestConfigVersioning:
    def test_initialization(self):
        obj = ConfigVersioning()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ConfigVersioning()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ConfigVersioning()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
