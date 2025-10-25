#!/usr/bin/env python3
import pytest
from src.pokertool.config_file_format import ConfigFileFormat

class TestConfigFileFormat:
    def test_initialization(self):
        obj = ConfigFileFormat()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ConfigFileFormat()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ConfigFileFormat()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
