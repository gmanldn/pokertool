#!/usr/bin/env python3
import pytest
from src.pokertool.memory_cleanup_errors import MemoryCleanupErrors

class TestMemoryCleanupErrors:
    def test_initialization(self):
        obj = MemoryCleanupErrors()
        assert obj.enabled is True
    
    def test_validate(self):
        obj = MemoryCleanupErrors()
        assert obj.validate() is True
    
    def test_get_metrics(self):
        obj = MemoryCleanupErrors()
        metrics = obj.get_metrics()
        assert "accuracy" in metrics

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
