#!/usr/bin/env python3
"""Tests for Showdown Tracker"""

import pytest
from src.pokertool.showdown_tracker import (
    ShowdownTracker,
    ShowdownResult,
    ShowdownEvent
)


class TestShowdownTracker:
    """Test suite for ShowdownTracker"""

    def test_initialization(self):
        """Test tracker initialization"""
        tracker = ShowdownTracker()
        assert len(tracker.showdown_events) == 0
        assert tracker.showdown_count == 0

    def test_record_showdown_won(self):
        """Test recording a won showdown"""
        tracker = ShowdownTracker()
        event = tracker.record_showdown(
            "Alice",
            ["Ah", "Kh"],
            ["Qh", "Jh", "Th", "5c", "2d"],
            "Royal Flush",
            ShowdownResult.WON,
            pot_won=100.0
        )

        assert event.player_name == "Alice"
        assert event.result == ShowdownResult.WON
        assert event.pot_won == 100.0
        assert event.showdown_id == 1

    def test_record_showdown_lost(self):
        """Test recording a lost showdown"""
        tracker = ShowdownTracker()
        event = tracker.record_showdown(
            "Bob",
            ["Ks", "Qd"],
            ["Jc", "Th", "9s", "2d", "3h"],
            "High Card",
            ShowdownResult.LOST
        )

        assert event.result == ShowdownResult.LOST
        assert event.pot_won == 0.0

    def test_record_showdown_split(self):
        """Test recording a split pot"""
        tracker = ShowdownTracker()
        event = tracker.record_showdown(
            "Charlie",
            ["Ah", "Kd"],
            ["Qc", "Js", "Th", "5d", "2h"],
            "Ace High Straight",
            ShowdownResult.SPLIT,
            pot_won=50.0
        )

        assert event.result == ShowdownResult.SPLIT
        assert event.pot_won == 50.0

    def test_get_player_showdowns(self):
        """Test getting showdowns for specific player"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Bob", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0)

        alice_showdowns = tracker.get_player_showdowns("Alice")
        assert len(alice_showdowns) == 2

    def test_showdown_win_rate_100_percent(self):
        """Test win rate calculation for all wins"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0)

        win_rate = tracker.get_showdown_win_rate("Alice")
        assert win_rate == 100.0

    def test_showdown_win_rate_50_percent(self):
        """Test win rate calculation for 50/50"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)

        win_rate = tracker.get_showdown_win_rate("Alice")
        assert win_rate == 50.0

    def test_showdown_win_rate_with_splits(self):
        """Test win rate calculation with splits"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["Ah", "Kd"], ["Qc", "Js", "Th", "5d", "2h"],
                              "Straight", ShowdownResult.SPLIT, 50.0)
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)

        # 1 win out of 3 = 33.33%
        win_rate = tracker.get_showdown_win_rate("Alice")
        assert win_rate == 33.33

    def test_total_showdowns(self):
        """Test total showdowns counting"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Bob", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)

        assert tracker.get_total_showdowns() == 2
        assert tracker.get_total_showdowns("Alice") == 1
        assert tracker.get_total_showdowns("Bob") == 1

    def test_showdown_wins_count(self):
        """Test counting showdown wins"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0)
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)

        assert tracker.get_showdown_wins("Alice") == 2

    def test_showdown_losses_count(self):
        """Test counting showdown losses"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)
        tracker.record_showdown("Alice", ["Js", "Td"], ["9c", "8h", "7s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)

        assert tracker.get_showdown_losses("Alice") == 2

    def test_showdown_splits_count(self):
        """Test counting showdown splits"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kd"], ["Qc", "Js", "Th", "5d", "2h"],
                              "Straight", ShowdownResult.SPLIT, 50.0)
        tracker.record_showdown("Alice", ["Ah", "Kd"], ["Qc", "Js", "Th", "5d", "2h"],
                              "Straight", ShowdownResult.SPLIT, 50.0)

        assert tracker.get_showdown_splits("Alice") == 2

    def test_total_won_at_showdown(self):
        """Test total amount won calculation"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0)
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST, 0.0)

        total = tracker.get_total_won_at_showdown("Alice")
        assert total == 250.0

    def test_avg_pot_won(self):
        """Test average pot won calculation"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 200.0)
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST, 0.0)

        avg = tracker.get_avg_pot_won("Alice")
        assert avg == 150.0  # (100 + 200) / 2

    def test_avg_pot_won_no_wins(self):
        """Test average pot won with no wins"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)

        avg = tracker.get_avg_pot_won("Alice")
        assert avg == 0.0

    def test_hand_types_shown(self):
        """Test hand types distribution"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["Ks", "Kh"], ["Kd", "7c", "2h", "5s", "9d"],
                              "Three of a Kind", ShowdownResult.WON, 75.0)
        tracker.record_showdown("Alice", ["Ks", "Kh"], ["Kd", "7c", "2h", "5s", "9d"],
                              "Three of a Kind", ShowdownResult.LOST)

        hand_types = tracker.get_hand_types_shown("Alice")
        assert hand_types["Royal Flush"] == 1
        assert hand_types["Three of a Kind"] == 2

    def test_most_common_showdown_hand(self):
        """Test most common hand shown"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ks", "Kh"], ["Kd", "7c", "2h", "5s", "9d"],
                              "Three of a Kind", ShowdownResult.WON, 75.0)
        tracker.record_showdown("Alice", ["Ks", "Kh"], ["Kd", "7c", "2h", "5s", "9d"],
                              "Three of a Kind", ShowdownResult.LOST)
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)

        most_common = tracker.get_most_common_showdown_hand("Alice")
        assert most_common == "Three of a Kind"

    def test_most_common_hand_no_showdowns(self):
        """Test most common hand with no showdowns"""
        tracker = ShowdownTracker()
        most_common = tracker.get_most_common_showdown_hand("Alice")

        assert most_common is None

    def test_multiway_showdowns(self):
        """Test multiway showdown counting"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0, opponents_shown=2)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0, opponents_shown=3)
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST, opponents_shown=1)

        multiway = tracker.get_multiway_showdowns("Alice")
        assert multiway == 2

    def test_heads_up_showdowns(self):
        """Test heads-up showdown counting"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0, opponents_shown=1)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0, opponents_shown=2)

        heads_up = tracker.get_heads_up_showdowns("Alice")
        assert heads_up == 1

    def test_player_statistics(self):
        """Test comprehensive player statistics"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0, opponents_shown=1)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0, opponents_shown=2)
        tracker.record_showdown("Alice", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST, 0.0, opponents_shown=1)

        stats = tracker.get_player_statistics("Alice")

        assert stats["player_name"] == "Alice"
        assert stats["total_showdowns"] == 3
        assert stats["wins"] == 2
        assert stats["losses"] == 1
        assert stats["splits"] == 0
        assert stats["win_rate"] == 66.67
        assert stats["total_won"] == 250.0
        assert stats["avg_pot_won"] == 125.0
        assert stats["heads_up_showdowns"] == 2
        assert stats["multiway_showdowns"] == 1

    def test_player_statistics_empty(self):
        """Test player statistics with no showdowns"""
        tracker = ShowdownTracker()
        stats = tracker.get_player_statistics("Alice")

        assert stats["total_showdowns"] == 0
        assert stats["wins"] == 0
        assert stats["win_rate"] == 0.0

    def test_recent_showdowns(self):
        """Test getting recent showdowns"""
        tracker = ShowdownTracker()

        for i in range(15):
            tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                                  "Royal Flush", ShowdownResult.WON, 100.0)

        recent = tracker.get_recent_showdowns(limit=5)
        assert len(recent) == 5
        assert recent[-1].showdown_id == 15

    def test_recent_showdowns_by_player(self):
        """Test getting recent showdowns for player"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Bob", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0)

        alice_recent = tracker.get_recent_showdowns(player_name="Alice")
        assert len(alice_recent) == 2
        assert all(e.player_name == "Alice" for e in alice_recent)

    def test_get_all_players(self):
        """Test getting all players"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Bob", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)
        tracker.record_showdown("Charlie", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0)

        players = tracker.get_all_players()
        assert players == ["Alice", "Bob", "Charlie"]

    def test_overall_statistics(self):
        """Test overall statistics"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Alice", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                              "Full House", ShowdownResult.WON, 150.0)
        tracker.record_showdown("Bob", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)

        stats = tracker.get_overall_statistics()

        assert stats["total_showdowns"] == 3
        assert stats["total_players"] == 2
        assert stats["overall_win_rate"] > 0
        assert stats["total_pot_won"] == 250.0
        assert stats["most_active_player"] == "Alice"

    def test_overall_statistics_empty(self):
        """Test overall statistics with no data"""
        tracker = ShowdownTracker()
        stats = tracker.get_overall_statistics()

        assert stats["total_showdowns"] == 0
        assert stats["total_players"] == 0
        assert stats["overall_win_rate"] == 0.0

    def test_showdown_id_increment(self):
        """Test showdown IDs increment correctly"""
        tracker = ShowdownTracker()
        e1 = tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                                    "Royal Flush", ShowdownResult.WON, 100.0)
        e2 = tracker.record_showdown("Bob", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                                    "High Card", ShowdownResult.LOST)
        e3 = tracker.record_showdown("Charlie", ["As", "Ad"], ["Ac", "Kh", "Kd", "5s", "2c"],
                                    "Full House", ShowdownResult.WON, 150.0)

        assert e1.showdown_id == 1
        assert e2.showdown_id == 2
        assert e3.showdown_id == 3

    def test_reset_functionality(self):
        """Test reset clears all data"""
        tracker = ShowdownTracker()
        tracker.record_showdown("Alice", ["Ah", "Kh"], ["Qh", "Jh", "Th", "5c", "2d"],
                              "Royal Flush", ShowdownResult.WON, 100.0)
        tracker.record_showdown("Bob", ["Ks", "Qd"], ["Jc", "Th", "9s", "2d", "3h"],
                              "High Card", ShowdownResult.LOST)

        assert len(tracker.showdown_events) == 2

        tracker.reset()

        assert len(tracker.showdown_events) == 0
        assert tracker.showdown_count == 0

    def test_cards_are_copied(self):
        """Test that card lists are copied, not referenced"""
        tracker = ShowdownTracker()
        hole_cards = ["Ah", "Kh"]
        board_cards = ["Qh", "Jh", "Th", "5c", "2d"]

        event = tracker.record_showdown("Alice", hole_cards, board_cards,
                                       "Royal Flush", ShowdownResult.WON, 100.0)

        # Modify original lists
        hole_cards.append("Qs")
        board_cards.append("6d")

        # Event should not be affected
        assert len(event.hole_cards) == 2
        assert len(event.board_cards) == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
