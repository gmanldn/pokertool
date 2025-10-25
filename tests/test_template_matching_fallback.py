#!/usr/bin/env python3
import pytest
from src.pokertool.template_matching_fallback import TemplateMatchingFallback

class TestTemplateMatchingFallback:
    def test_initialization(self):
        obj = TemplateMatchingFallback()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = TemplateMatchingFallback()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = TemplateMatchingFallback()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
