#!/usr/bin/env python3
import pytest
from src.pokertool.scraper_autostart import ScraperAutostart

class TestScraperAutostart:
    def test_initialization(self):
        obj = ScraperAutostart()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = ScraperAutostart()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = ScraperAutostart()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics
        assert metrics["accuracy"] >= 90.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
