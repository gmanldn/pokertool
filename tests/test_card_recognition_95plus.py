#!/usr/bin/env python3
import pytest
from src.pokertool.card_recognition_95plus import CardRecognition95Plus

class TestCardRecognition95Plus:
    def test_initialization(self):
        obj = CardRecognition95Plus()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = CardRecognition95Plus()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = CardRecognition95Plus()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
