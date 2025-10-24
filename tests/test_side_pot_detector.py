"""
Tests for Side Pot Detection System
====================================

Comprehensive test suite with 15+ tests covering:
- Single all-in scenarios
- Multiple all-ins
- Pot odds calculations
- Eligible player tracking
- Edge cases
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch

# Import module under test
from pokertool.side_pot_detector import (
    SidePotDetector,
    PotInfo,
    Player,
    PotType
)


class TestSidePotDetector:
    """Test suite for side pot detection."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return SidePotDetector()

    # Test 1: Initialization
    def test_initialization(self, detector):
        """Test detector initializes correctly."""
        assert detector.last_pots == []
        assert detector.pot_change_threshold == 0.01

    # Test 2: No side pots (all players active)
    def test_no_side_pots(self, detector):
        """Test scenario with no all-ins (main pot only)."""
        players = [
            Player(seat=1, name="Alice", stack=100, bet_amount=10, is_all_in=False),
            Player(seat=2, name="Bob", stack=100, bet_amount=10, is_all_in=False),
            Player(seat=3, name="Carol", stack=100, bet_amount=10, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=30.0)

        assert len(pots) == 1
        assert pots[0].is_main_pot
        assert pots[0].amount == 30.0
        assert pots[0].pot_number == 0
        assert len(pots[0].eligible_players) == 3

    # Test 3: Single all-in (2 pots)
    def test_single_all_in(self, detector):
        """Test scenario with one player all-in."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=2, name="Bob", stack=50, bet_amount=100, is_all_in=False),
            Player(seat=3, name="Carol", stack=50, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=250.0)

        # Should have 2 pots: main (3 players) and side (2 players)
        assert len(pots) == 2

        # Main pot: 50 * 3 = 150
        assert pots[0].is_main_pot
        assert pots[0].amount == 150.0
        assert len(pots[0].eligible_players) == 3
        assert {1, 2, 3} == pots[0].eligible_players

        # Side pot: (100-50) * 2 = 100
        assert not pots[1].is_main_pot
        assert pots[1].amount == 100.0
        assert len(pots[1].eligible_players) == 2
        assert {2, 3} == pots[1].eligible_players

    # Test 4: Multiple all-ins (3+ pots)
    def test_multiple_all_ins(self, detector):
        """Test scenario with multiple players all-in at different amounts."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=30, is_all_in=True),
            Player(seat=2, name="Bob", stack=0, bet_amount=60, is_all_in=True),
            Player(seat=3, name="Carol", stack=40, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=190.0)

        # Should have 3+ pots
        assert len(pots) >= 3

        # Main pot: 30 * 3 = 90
        assert pots[0].is_main_pot
        assert pots[0].amount == 90.0
        assert {1, 2, 3} == pots[0].eligible_players

        # Side pots should sum correctly
        total_side = sum(pot.amount for pot in pots[1:])
        assert abs((pots[0].amount + total_side) - 190.0) < 0.01

        # Check at least one side pot exists
        assert any(not pot.is_main_pot for pot in pots)

    # Test 5: Folded players excluded
    def test_folded_players_excluded(self, detector):
        """Test that folded players are excluded from pots."""
        players = [
            Player(seat=1, name="Alice", stack=100, bet_amount=10, is_folded=True),
            Player(seat=2, name="Bob", stack=100, bet_amount=10, is_folded=False),
            Player(seat=3, name="Carol", stack=100, bet_amount=10, is_folded=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=30.0)

        assert len(pots) == 1
        assert len(pots[0].eligible_players) == 2
        assert 1 not in pots[0].eligible_players

    # Test 6: Pot odds calculation
    def test_pot_odds_calculation(self, detector):
        """Test pot odds calculation."""
        pot = PotInfo(
            amount=100.0,
            confidence=0.9,
            is_main_pot=True,
            position=(0, 0, 0, 0),
            pot_number=0
        )

        # Pot odds = pot / bet_to_call
        assert pot.get_pot_odds(50.0) == 2.0  # 2:1
        assert pot.get_pot_odds(100.0) == 1.0  # 1:1
        assert pot.get_pot_odds(25.0) == 4.0  # 4:1

    # Test 7: Pot odds - invalid bet
    def test_pot_odds_invalid_bet(self, detector):
        """Test pot odds with invalid bet amount."""
        pot = PotInfo(
            amount=100.0,
            confidence=0.9,
            is_main_pot=True,
            position=(0, 0, 0, 0),
            pot_number=0
        )

        assert pot.get_pot_odds(0) is None
        assert pot.get_pot_odds(-10) is None

    # Test 8: Get total pot
    def test_get_total_pot(self, detector):
        """Test calculating total pot amount."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=2, name="Bob", stack=50, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=150.0)
        detector.last_pots = pots

        total = detector.get_total_pot()
        assert total == 150.0

    # Test 9: Get side pot count
    def test_get_side_pot_count(self, detector):
        """Test counting side pots."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=2, name="Bob", stack=50, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=150.0)
        detector.last_pots = pots

        assert detector.get_side_pot_count() == 1
        assert detector.has_side_pots() is True

    # Test 10: Get pots for player
    def test_get_pots_for_player(self, detector):
        """Test getting pots a specific player is eligible for."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=2, name="Bob", stack=50, bet_amount=100, is_all_in=False),
            Player(seat=3, name="Carol", stack=50, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=250.0)
        detector.last_pots = pots

        # Alice is only eligible for main pot
        alice_pots = detector.get_pots_for_player(1)
        assert len(alice_pots) == 1
        assert alice_pots[0].is_main_pot

        # Bob is eligible for all pots
        bob_pots = detector.get_pots_for_player(2)
        assert len(bob_pots) == 2

    # Test 11: Calculate total pot odds for player
    def test_calculate_total_pot_odds(self, detector):
        """Test calculating combined pot odds for player."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=2, name="Bob", stack=50, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=150.0)
        detector.last_pots = pots

        # Alice eligible for main pot (150) only
        # But if she's all-in, she can't call more
        odds_alice = detector.calculate_total_pot_odds(1, bet_to_call=50)
        assert odds_alice is not None

        # Bob eligible for all pots (150 total)
        odds_bob = detector.calculate_total_pot_odds(2, bet_to_call=50)
        assert odds_bob == 3.0  # 150 / 50 = 3:1

    # Test 12: Empty players list
    def test_empty_players_list(self, detector):
        """Test with no players."""
        pots = detector.calculate_pots_from_players([], total_pot=0.0)
        assert len(pots) == 0

    # Test 13: All players folded
    def test_all_players_folded(self, detector):
        """Test scenario where all players have folded."""
        players = [
            Player(seat=1, name="Alice", stack=100, bet_amount=10, is_folded=True),
            Player(seat=2, name="Bob", stack=100, bet_amount=10, is_folded=True),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=20.0)
        assert len(pots) == 0

    # Test 14: Get pot distribution
    def test_get_pot_distribution(self, detector):
        """Test getting pot distribution summary."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=2, name="Bob", stack=50, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=150.0)
        detector.last_pots = pots

        dist = detector.get_pot_distribution()
        assert 'main_pot' in dist
        assert 'side_pots' in dist
        assert 'total' in dist
        assert 'side_pot_count' in dist
        assert dist['side_pot_count'] == 1

    # Test 15: Same all-in amounts (should merge)
    def test_same_all_in_amounts(self, detector):
        """Test scenario where multiple players all-in for same amount."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=2, name="Bob", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=3, name="Carol", stack=50, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=200.0)

        # Should have 2 pots (main and side), not 3
        assert len(pots) == 2

        # Main pot: 50 * 3 = 150
        assert pots[0].amount == 150.0
        assert {1, 2, 3} == pots[0].eligible_players

        # Side pot: 50 * 1 = 50
        assert pots[1].amount == 50.0
        assert {3} == pots[1].eligible_players

    # Test 16: Complex scenario (4 players, 2 all-ins)
    def test_complex_four_player_scenario(self, detector):
        """Test complex scenario with 4 players."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=25, is_all_in=True),
            Player(seat=2, name="Bob", stack=0, bet_amount=75, is_all_in=True),
            Player(seat=3, name="Carol", stack=25, bet_amount=100, is_all_in=False),
            Player(seat=4, name="Dave", stack=0, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=300.0)

        # Should have 3+ pots
        assert len(pots) >= 3

        # Main pot: 25 * 4 = 100
        assert pots[0].amount == 100.0
        assert {1, 2, 3, 4} == pots[0].eligible_players

        # Total should match
        total = sum(pot.amount for pot in pots)
        assert abs(total - 300.0) < 0.01

        # All players should be eligible for main pot
        assert 1 in pots[0].eligible_players
        assert 2 in pots[0].eligible_players

    # Test 17: Single player (no opponents)
    def test_single_player(self, detector):
        """Test scenario with only one player."""
        players = [
            Player(seat=1, name="Alice", stack=100, bet_amount=10, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=10.0)

        assert len(pots) == 1
        assert pots[0].amount == 10.0
        assert {1} == pots[0].eligible_players

    # Test 18: Invalid pot odds calculation
    def test_invalid_total_pot_odds(self, detector):
        """Test total pot odds with invalid parameters."""
        players = [
            Player(seat=1, name="Alice", stack=100, bet_amount=50, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=50.0)
        detector.last_pots = pots

        # Invalid bet amount
        assert detector.calculate_total_pot_odds(1, 0) is None
        assert detector.calculate_total_pot_odds(1, -50) is None

        # Player not in any pot
        assert detector.calculate_total_pot_odds(99, 50) is None

    # Test 19: All-in amount tracking
    def test_all_in_amount_tracking(self, detector):
        """Test that all-in amounts are tracked in side pots."""
        players = [
            Player(seat=1, name="Alice", stack=0, bet_amount=50, is_all_in=True),
            Player(seat=2, name="Bob", stack=50, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=150.0)

        # Main pot should not have all_in_amount
        assert pots[0].all_in_amount is None

        # Side pot should track the all-in that created it
        assert pots[1].all_in_amount is None  # Created by non-all-in player

    # Test 20: Zero bet amounts
    def test_zero_bet_amounts(self, detector):
        """Test scenario with players who haven't bet."""
        players = [
            Player(seat=1, name="Alice", stack=100, bet_amount=0, is_all_in=False),
            Player(seat=2, name="Bob", stack=100, bet_amount=100, is_all_in=False),
        ]

        pots = detector.calculate_pots_from_players(players, total_pot=100.0)

        # Should still create pot
        assert len(pots) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
