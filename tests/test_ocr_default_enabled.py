#!/usr/bin/env python3
import pytest
from src.pokertool.ocr_default_enabled import OcrDefaultEnabled

class TestOcrDefaultEnabled:
    def test_initialization(self):
        obj = OcrDefaultEnabled()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = OcrDefaultEnabled()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = OcrDefaultEnabled()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
