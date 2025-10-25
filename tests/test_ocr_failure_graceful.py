#!/usr/bin/env python3
import pytest
from src.pokertool.ocr_failure_graceful import OcrFailureGraceful

class TestOcrFailureGraceful:
    def test_initialization(self):
        obj = OcrFailureGraceful()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = OcrFailureGraceful()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = OcrFailureGraceful()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
