#!/usr/bin/env python3
import pytest
from src.pokertool.card_suit_rank_extract import CardSuitRankExtract

class TestCardSuitRankExtract:
    def test_initialization(self):
        obj = CardSuitRankExtract()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = CardSuitRankExtract()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = CardSuitRankExtract()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
