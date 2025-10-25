#!/usr/bin/env python3
import pytest
from src.pokertool.config_hot_reload import ConfigHotReload

class TestConfigHotReload:
    def test_initialization(self):
        obj = ConfigHotReload()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ConfigHotReload()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ConfigHotReload()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
