#!/usr/bin/env python3
import pytest
from src.pokertool.config_diff_tool import ConfigDiffTool

class TestConfigDiffTool:
    def test_initialization(self):
        obj = ConfigDiffTool()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ConfigDiffTool()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ConfigDiffTool()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
