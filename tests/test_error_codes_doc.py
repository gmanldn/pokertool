#!/usr/bin/env python3
import pytest
from src.pokertool.error_codes_doc import ErrorCodesDoc

class TestErrorCodesDoc:
    def test_initialization(self):
        obj = ErrorCodesDoc()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ErrorCodesDoc()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ErrorCodesDoc()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
