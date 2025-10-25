#!/usr/bin/env python3
import pytest
from src.pokertool.config_validation import ConfigValidation

class TestConfigValidation:
    def test_initialization(self):
        obj = ConfigValidation()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ConfigValidation()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ConfigValidation()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
