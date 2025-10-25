#!/usr/bin/env python3
import pytest
from src.pokertool.exception_handling_stages import ExceptionHandlingStages

class TestExceptionHandlingStages:
    def test_initialization(self):
        obj = ExceptionHandlingStages()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ExceptionHandlingStages()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ExceptionHandlingStages()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
