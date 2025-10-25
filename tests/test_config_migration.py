#!/usr/bin/env python3
import pytest
from src.pokertool.config_migration import ConfigMigration

class TestConfigMigration:
    def test_initialization(self):
        obj = ConfigMigration()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ConfigMigration()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ConfigMigration()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
