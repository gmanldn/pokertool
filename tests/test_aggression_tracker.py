#!/usr/bin/env python3
"""Tests for Aggression Tracker"""

import pytest
from src.pokertool.aggression_tracker import (
    AggressionTracker,
    ActionRecord
)


class TestAggressionTracker:
    """Test suite for AggressionTracker"""

    def test_initialization(self):
        """Test tracker initialization"""
        tracker = AggressionTracker()
        assert len(tracker.action_records) == 0
        assert tracker.action_count == 0

    def test_record_bet(self):
        """Test recording a bet"""
        tracker = AggressionTracker()
        record = tracker.record_action("Alice", "BET", 10.0, "flop")

        assert record.player_name == "Alice"
        assert record.action_type == "BET"
        assert record.amount == 10.0
        assert record.street == "flop"

    def test_record_call(self):
        """Test recording a call"""
        tracker = AggressionTracker()
        record = tracker.record_action("Bob", "CALL", 10.0, "preflop")

        assert record.action_type == "CALL"

    def test_get_player_actions(self):
        """Test getting actions for player"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Bob", "CALL", 10.0, "flop")
        tracker.record_action("Alice", "RAISE", 20.0, "turn")

        alice_actions = tracker.get_player_actions("Alice")
        assert len(alice_actions) == 2

    def test_aggressive_actions_count(self):
        """Test counting aggressive actions"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "RAISE", 20.0, "turn")
        tracker.record_action("Alice", "CALL", 10.0, "river")

        count = tracker.get_aggressive_actions("Alice")
        assert count == 2

    def test_passive_actions_count(self):
        """Test counting passive actions"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "CALL", 10.0, "flop")
        tracker.record_action("Alice", "CHECK", 0.0, "turn")
        tracker.record_action("Alice", "BET", 15.0, "river")

        count = tracker.get_passive_actions("Alice")
        assert count == 2

    def test_aggression_factor_calculation(self):
        """Test aggression factor calculation"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "RAISE", 20.0, "turn")
        tracker.record_action("Alice", "CALL", 10.0, "river")

        # 2 aggressive / 1 passive = 2.0
        af = tracker.get_aggression_factor("Alice")
        assert af == 2.0

    def test_aggression_factor_no_passive(self):
        """Test aggression factor with no passive actions"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "RAISE", 20.0, "turn")

        af = tracker.get_aggression_factor("Alice")
        assert af == 0.0

    def test_aggression_frequency_calculation(self):
        """Test aggression frequency calculation"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "CALL", 10.0, "turn")
        tracker.record_action("Alice", "RAISE", 20.0, "river")

        # 2 aggressive out of 3 = 66.67%
        freq = tracker.get_aggression_frequency("Alice")
        assert freq == 66.67

    def test_aggression_frequency_with_folds(self):
        """Test aggression frequency excludes folds"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "FOLD", 0.0, "turn")
        tracker.record_action("Alice", "CALL", 5.0, "river")

        # 1 aggressive out of 2 non-fold actions = 50%
        freq = tracker.get_aggression_frequency("Alice")
        assert freq == 50.0

    def test_three_bet_percentage(self):
        """Test 3-bet percentage calculation"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "3BET", 30.0, "preflop")
        tracker.record_action("Alice", "CALL", 10.0, "preflop")
        tracker.record_action("Alice", "FOLD", 0.0, "preflop")
        tracker.record_action("Alice", "3BET", 30.0, "preflop")

        # 2 3-bets out of 4 opportunities = 50%
        three_bet_pct = tracker.get_three_bet_percentage("Alice")
        assert three_bet_pct == 50.0

    def test_three_bet_percentage_no_opportunities(self):
        """Test 3-bet percentage with no opportunities"""
        tracker = AggressionTracker()
        three_bet_pct = tracker.get_three_bet_percentage("Alice")

        assert three_bet_pct == 0.0

    def test_continuation_bet_frequency(self):
        """Test c-bet frequency calculation"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 15.0, "flop")
        tracker.record_action("Alice", "BET", 20.0, "flop")
        tracker.record_action("Alice", "CHECK", 0.0, "flop")

        # 2 bets out of 3 flop actions = 66.67%
        cbet_freq = tracker.get_continuation_bet_frequency("Alice")
        assert cbet_freq == 66.67

    def test_continuation_bet_frequency_no_flop_actions(self):
        """Test c-bet frequency with no flop actions"""
        tracker = AggressionTracker()
        cbet_freq = tracker.get_continuation_bet_frequency("Alice")

        assert cbet_freq == 0.0

    def test_avg_bet_size(self):
        """Test average bet size calculation"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "RAISE", 20.0, "turn")
        tracker.record_action("Alice", "BET", 30.0, "river")

        # (10 + 20 + 30) / 3 = 20
        avg = tracker.get_avg_bet_size("Alice")
        assert avg == 20.0

    def test_avg_bet_size_excludes_calls(self):
        """Test average bet size excludes calls"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "CALL", 50.0, "turn")
        tracker.record_action("Alice", "RAISE", 30.0, "river")

        # (10 + 30) / 2 = 20 (call excluded)
        avg = tracker.get_avg_bet_size("Alice")
        assert avg == 20.0

    def test_total_bet_amount(self):
        """Test total bet amount calculation"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "RAISE", 20.0, "turn")
        tracker.record_action("Alice", "BET", 30.0, "river")

        total = tracker.get_total_bet_amount("Alice")
        assert total == 60.0

    def test_street_breakdown(self):
        """Test aggression breakdown by street"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "RAISE", 10.0, "preflop")
        tracker.record_action("Alice", "BET", 15.0, "flop")
        tracker.record_action("Alice", "CALL", 10.0, "flop")

        breakdown = tracker.get_street_breakdown("Alice")

        assert breakdown["preflop"]["aggressive_actions"] == 1
        assert breakdown["flop"]["aggressive_actions"] == 1
        assert breakdown["flop"]["passive_actions"] == 1

    def test_player_statistics(self):
        """Test comprehensive player statistics"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "RAISE", 20.0, "turn")
        tracker.record_action("Alice", "CALL", 5.0, "river")

        stats = tracker.get_player_statistics("Alice")

        assert stats["player_name"] == "Alice"
        assert stats["total_actions"] == 3
        assert stats["aggressive_actions"] == 2
        assert stats["passive_actions"] == 1
        assert stats["aggression_factor"] == 2.0
        assert stats["total_bet"] == 30.0

    def test_player_statistics_empty(self):
        """Test player statistics with no actions"""
        tracker = AggressionTracker()
        stats = tracker.get_player_statistics("Alice")

        assert stats["total_actions"] == 0
        assert stats["aggression_factor"] == 0.0

    def test_get_all_players(self):
        """Test getting all players"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Bob", "CALL", 10.0, "flop")
        tracker.record_action("Charlie", "RAISE", 20.0, "turn")

        players = tracker.get_all_players()
        assert players == ["Alice", "Bob", "Charlie"]

    def test_most_aggressive_player(self):
        """Test finding most aggressive player"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Alice", "CALL", 5.0, "turn")

        tracker.record_action("Bob", "RAISE", 20.0, "flop")
        tracker.record_action("Bob", "RAISE", 30.0, "turn")
        tracker.record_action("Bob", "CALL", 5.0, "river")

        # Bob has AF of 2.0, Alice has 1.0
        most_aggressive = tracker.get_most_aggressive_player()
        assert most_aggressive == "Bob"

    def test_most_aggressive_player_empty(self):
        """Test most aggressive with no players"""
        tracker = AggressionTracker()
        most_aggressive = tracker.get_most_aggressive_player()

        assert most_aggressive is None

    def test_action_id_increment(self):
        """Test action IDs increment"""
        tracker = AggressionTracker()
        r1 = tracker.record_action("Alice", "BET", 10.0, "flop")
        r2 = tracker.record_action("Bob", "CALL", 10.0, "flop")
        r3 = tracker.record_action("Charlie", "RAISE", 20.0, "turn")

        assert r1.action_id == 1
        assert r2.action_id == 2
        assert r3.action_id == 3

    def test_reset_functionality(self):
        """Test reset clears all data"""
        tracker = AggressionTracker()
        tracker.record_action("Alice", "BET", 10.0, "flop")
        tracker.record_action("Bob", "CALL", 10.0, "flop")

        assert len(tracker.action_records) == 2

        tracker.reset()

        assert len(tracker.action_records) == 0
        assert tracker.action_count == 0

    def test_action_type_case_insensitive(self):
        """Test action types are normalized to uppercase"""
        tracker = AggressionTracker()
        record = tracker.record_action("Alice", "bet", 10.0, "flop")

        assert record.action_type == "BET"

    def test_street_case_insensitive(self):
        """Test streets are normalized to lowercase"""
        tracker = AggressionTracker()
        record = tracker.record_action("Alice", "BET", 10.0, "FLOP")

        assert record.street == "flop"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
