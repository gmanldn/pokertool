#!/usr/bin/env python3
import pytest
from src.pokertool.config_documentation import ConfigDocumentation

class TestConfigDocumentation:
    def test_initialization(self):
        obj = ConfigDocumentation()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ConfigDocumentation()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ConfigDocumentation()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
