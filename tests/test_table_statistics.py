#!/usr/bin/env python3
"""Tests for Table Statistics"""

import pytest
from src.pokertool.table_statistics import TableStatistics


class TestTableStatistics:
    """Test suite for TableStatistics"""

    def test_initialization(self):
        """Test statistics initialization"""
        stats = TableStatistics()
        assert len(stats.snapshots) == 0
        assert stats.hands_played == 0
        assert stats.total_pots_won == 0.0

    def test_record_snapshot(self):
        """Test recording snapshot"""
        stats = TableStatistics()
        snapshot = stats.record_snapshot(6, 100.0, 15.0, 1.0)

        assert snapshot.num_players == 6
        assert snapshot.avg_stack == 100.0
        assert snapshot.total_pot == 15.0
        assert snapshot.snapshot_id == 1

    def test_record_hand_complete(self):
        """Test recording completed hand"""
        stats = TableStatistics()
        stats.record_hand_complete(25.0)

        assert stats.hands_played == 1
        assert stats.total_pots_won == 25.0

    def test_avg_players(self):
        """Test average players calculation"""
        stats = TableStatistics()
        stats.record_snapshot(6, 100.0)
        stats.record_snapshot(8, 100.0)
        stats.record_snapshot(7, 100.0)

        assert stats.get_avg_players() == 7.0

    def test_avg_pot_size(self):
        """Test average pot size calculation"""
        stats = TableStatistics()
        stats.record_hand_complete(10.0)
        stats.record_hand_complete(20.0)
        stats.record_hand_complete(30.0)

        assert stats.get_avg_pot_size() == 20.0

    def test_avg_stack_size(self):
        """Test average stack size calculation"""
        stats = TableStatistics()
        stats.record_snapshot(6, 100.0)
        stats.record_snapshot(6, 150.0)
        stats.record_snapshot(6, 200.0)

        assert stats.get_avg_stack_size() == 150.0

    def test_statistics_empty(self):
        """Test statistics with no data"""
        stats = TableStatistics()
        result = stats.get_statistics()

        assert result["hands_played"] == 0
        assert result["avg_players"] == 0.0

    def test_statistics_complete(self):
        """Test comprehensive statistics"""
        stats = TableStatistics()
        stats.record_snapshot(6, 100.0, 15.0)
        stats.record_hand_complete(15.0)
        stats.record_snapshot(6, 95.0, 20.0)
        stats.record_hand_complete(20.0)

        result = stats.get_statistics()

        assert result["hands_played"] == 2
        assert result["avg_players"] == 6.0
        assert result["avg_pot_size"] == 17.5
        assert result["total_pots"] == 35.0

    def test_reset(self):
        """Test reset clears all data"""
        stats = TableStatistics()
        stats.record_snapshot(6, 100.0)
        stats.record_hand_complete(15.0)

        stats.reset()

        assert len(stats.snapshots) == 0
        assert stats.hands_played == 0
        assert stats.total_pots_won == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
