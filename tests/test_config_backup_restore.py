#!/usr/bin/env python3
import pytest
from src.pokertool.config_backup_restore import ConfigBackupRestore

class TestConfigBackupRestore:
    def test_initialization(self):
        obj = ConfigBackupRestore()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ConfigBackupRestore()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ConfigBackupRestore()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
