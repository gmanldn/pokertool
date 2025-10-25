#!/usr/bin/env python3
import pytest
from src.pokertool.card_image_filters import CardImageFilters

class TestCardImageFilters:
    def test_initialization(self):
        obj = CardImageFilters()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = CardImageFilters()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = CardImageFilters()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
