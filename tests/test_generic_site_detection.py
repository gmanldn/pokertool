#!/usr/bin/env python3
import pytest
from src.pokertool.generic_site_detection import GenericSiteDetection

class TestGenericSiteDetection:
    def test_initialization(self):
        obj = GenericSiteDetection()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = GenericSiteDetection()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = GenericSiteDetection()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
