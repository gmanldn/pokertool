#!/usr/bin/env python3
import pytest
from src.pokertool.card_all_styles import CardAllStyles

class TestCardAllStyles:
    def test_initialization(self):
        obj = CardAllStyles()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = CardAllStyles()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = CardAllStyles()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
