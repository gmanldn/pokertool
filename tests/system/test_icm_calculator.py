"""System tests for the ICM calculator."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.icm_calculator import (
    ICMCalculator,
    ICMDecision,
    ICMResult,
    MalmuthHarvilleCalculator,
    TournamentState,
)


def test_tournament_state_creation() -> None:
    """Test creating a tournament state."""
    state = TournamentState(
        player_stacks={'player1': 5000, 'player2': 3000, 'player3': 2000},
        payout_structure=[500, 300, 200],
        blinds=100.0,
        ante=10.0
    )
    
    assert state.num_players == 3
    assert state.total_chips == 10000
    assert state.blinds == 100.0
    assert state.ante == 10.0


def test_tournament_state_stack_sizes() -> None:
    """Test getting sorted stack sizes."""
    state = TournamentState(
        player_stacks={'p1': 2000, 'p2': 5000, 'p3': 3000},
        payout_structure=[500, 300, 200],
        blinds=100.0
    )
    
    stacks = state.get_stack_sizes()
    assert stacks == [5000, 3000, 2000]  # Sorted descending


def test_malmuth_harville_first_place() -> None:
    """Test calculating first place probability."""
    calculator = MalmuthHarvilleCalculator()
    
    stack_sizes = [5000, 3000, 2000]  # 10000 total
    
    # Player with 5000 chips
    prob_first = calculator.calculate_finish_probability(stack_sizes, 0, 0)
    assert pytest.approx(prob_first, abs=0.01) == 0.5  # 5000/10000
    
    # Player with 3000 chips
    prob_first = calculator.calculate_finish_probability(stack_sizes, 1, 0)
    assert pytest.approx(prob_first, abs=0.01) == 0.3  # 3000/10000
    
    # Player with 2000 chips
    prob_first = calculator.calculate_finish_probability(stack_sizes, 2, 0)
    assert pytest.approx(prob_first, abs=0.01) == 0.2  # 2000/10000


def test_malmuth_harville_second_place() -> None:
    """Test calculating second place probability."""
    calculator = MalmuthHarvilleCalculator()
    
    stack_sizes = [6000, 4000]
    
    # Both players have some chance of 2nd
    prob_second_p1 = calculator.calculate_finish_probability(stack_sizes, 0, 1)
    prob_second_p2 = calculator.calculate_finish_probability(stack_sizes, 1, 1)
    
    # Chip leader less likely to finish 2nd
    assert prob_second_p2 > prob_second_p1


def test_malmuth_harville_probabilities_sum_to_one() -> None:
    """Test that finish probabilities sum to 1."""
    calculator = MalmuthHarvilleCalculator()
    
    stack_sizes = [5000, 3000, 2000]
    
    for player_idx in range(3):
        total_prob = sum(
            calculator.calculate_finish_probability(stack_sizes, player_idx, position)
            for position in range(3)
        )
        assert pytest.approx(total_prob, abs=0.01) == 1.0


def test_malmuth_harville_caching() -> None:
    """Test that memoization improves performance."""
    calculator = MalmuthHarvilleCalculator(memoize=True)
    
    stack_sizes = [5000, 3000, 2000]
    
    # First call
    prob1 = calculator.calculate_finish_probability(stack_sizes, 0, 1)
    cache_size_1 = len(calculator._cache)
    
    # Second call with same parameters
    prob2 = calculator.calculate_finish_probability(stack_sizes, 0, 1)
    cache_size_2 = len(calculator._cache)
    
    assert prob1 == prob2
    assert cache_size_2 == cache_size_1  # No new entries


def test_icm_calculator_basic() -> None:
    """Test basic ICM calculation."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000, 'p3': 2000},
        payout_structure=[600, 300, 100],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    result = calculator.calculate_icm(state)
    
    assert 'p1' in result.player_equity
    assert 'p2' in result.player_equity
    assert 'p3' in result.player_equity
    
    # Chip leader should have highest equity
    assert result.player_equity['p1'] > result.player_equity['p2']
    assert result.player_equity['p2'] > result.player_equity['p3']
    
    # Total equity should equal prize pool
    total_equity = sum(result.player_equity.values())
    prize_pool = sum(state.payout_structure)
    assert pytest.approx(total_equity, abs=1.0) == prize_pool


def test_icm_calculator_equal_stacks() -> None:
    """Test ICM with equal stacks."""
    state = TournamentState(
        player_stacks={'p1': 3333, 'p2': 3333, 'p3': 3334},
        payout_structure=[600, 300, 100],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    result = calculator.calculate_icm(state)
    
    # With equal stacks, equities should be nearly equal
    equities = list(result.player_equity.values())
    assert pytest.approx(equities[0], abs=5.0) == equities[1]
    assert pytest.approx(equities[1], abs=5.0) == equities[2]


def test_icm_result_equity_percentage() -> None:
    """Test getting equity as percentage."""
    result = ICMResult(
        player_equity={'p1': 500, 'p2': 300, 'p3': 200},
        finish_probabilities={},
        total_equity=1000
    )
    
    assert pytest.approx(result.get_equity_percentage('p1')) == 50.0
    assert pytest.approx(result.get_equity_percentage('p2')) == 30.0
    assert pytest.approx(result.get_equity_percentage('p3')) == 20.0


def test_bubble_factor_in_the_money() -> None:
    """Test bubble factor when already in the money."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000, 'p3': 2000},
        payout_structure=[600, 300, 100],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    bubble_factor = calculator.calculate_bubble_factor(state, 'p1')
    
    # Already ITM, bubble factor should be 1.0
    assert bubble_factor == 1.0


def test_bubble_factor_on_bubble() -> None:
    """Test bubble factor when on the money bubble."""
    state = TournamentState(
        player_stacks={'p1': 4000, 'p2': 3000, 'p3': 2000, 'p4': 1000},
        payout_structure=[600, 300, 100],  # Only 3 paid
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    bubble_factor = calculator.calculate_bubble_factor(state, 'p4')
    
    # Short stack on bubble should have bubble factor != 1.0
    assert bubble_factor != 1.0
    assert 0.5 <= bubble_factor <= 2.0


def test_risk_premium_calculation() -> None:
    """Test calculating risk premium."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000, 'p3': 2000},
        payout_structure=[600, 300, 100],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    
    # Risk 1000 chips
    risk_premium = calculator.calculate_risk_premium(state, 'p2', 1000)
    
    # Should return a float
    assert isinstance(risk_premium, float)


def test_decision_analysis_positive_ev() -> None:
    """Test analyzing a +EV decision."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000, 'p3': 2000},
        payout_structure=[600, 300, 100],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    
    # Analyze a decision with 70% win rate
    decision = calculator.analyze_decision(
        tournament_state=state,
        player_id='p2',
        action='call',
        chips_at_risk=500,
        win_probability=0.7
    )
    
    assert decision.action == 'call'
    assert isinstance(decision.cEV, float)
    assert isinstance(decision.dollar_EV, float)
    assert isinstance(decision.risk_premium, float)


def test_decision_analysis_negative_ev() -> None:
    """Test analyzing a -EV decision."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000, 'p3': 2000},
        payout_structure=[600, 300, 100],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    
    # Analyze a decision with 30% win rate
    decision = calculator.analyze_decision(
        tournament_state=state,
        player_id='p3',
        action='call',
        chips_at_risk=1000,
        win_probability=0.3
    )
    
    # Low win probability should not be recommended
    assert not decision.recommended
    assert decision.dollar_EV < 0


def test_payout_structure_optimization() -> None:
    """Test generating optimized payout structure."""
    calculator = ICMCalculator()
    
    payouts = calculator.optimize_payout_structure(
        total_prize_pool=1000,
        num_players=9,
        num_paid=3
    )
    
    assert len(payouts) == 3
    assert sum(payouts) == pytest.approx(1000, abs=0.01)
    
    # First place should get most
    assert payouts[0] > payouts[1]
    assert payouts[1] > payouts[2]
    
    # First place should get 30-45% of prize pool
    assert 300 <= payouts[0] <= 450


def test_payout_structure_single_winner() -> None:
    """Test payout structure for winner-take-all."""
    calculator = ICMCalculator()
    
    payouts = calculator.optimize_payout_structure(
        total_prize_pool=1000,
        num_players=10,
        num_paid=1
    )
    
    assert len(payouts) == 1
    assert payouts[0] == 1000


def test_future_game_simulation() -> None:
    """Test future game simulation."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000, 'p3': 2000},
        payout_structure=[600, 300, 100],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    
    # Run simulation
    simulated_equity = calculator.simulate_future_game(state, num_simulations=100)
    
    assert 'p1' in simulated_equity
    assert 'p2' in simulated_equity
    assert 'p3' in simulated_equity
    
    # Chip leader should have highest simulated equity
    assert simulated_equity['p1'] > simulated_equity['p2']
    assert simulated_equity['p2'] > simulated_equity['p3']


def test_modify_stack_increase() -> None:
    """Test modifying stack (increase)."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000},
        payout_structure=[600, 400],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    new_state = calculator._modify_stack(state, 'p2', 1000)
    
    assert new_state.player_stacks['p2'] == 4000
    assert new_state.player_stacks['p1'] == 5000


def test_modify_stack_decrease() -> None:
    """Test modifying stack (decrease)."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000},
        payout_structure=[600, 400],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    new_state = calculator._modify_stack(state, 'p2', -1000)
    
    assert new_state.player_stacks['p2'] == 2000
    assert new_state.player_stacks['p1'] == 5000


def test_modify_stack_elimination() -> None:
    """Test eliminating a player."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 1000},
        payout_structure=[600, 400],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    new_state = calculator._modify_stack(state, 'p2', -1000)
    
    # Player 2 should be eliminated
    assert 'p2' not in new_state.player_stacks
    assert new_state.num_players == 1


def test_heads_up_icm() -> None:
    """Test ICM calculation heads-up."""
    state = TournamentState(
        player_stacks={'p1': 7000, 'p2': 3000},
        payout_structure=[600, 400],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    result = calculator.calculate_icm(state)
    
    # With 70% of chips, p1 should have more than 70% equity
    # but less than maximum due to ICM
    p1_equity_pct = result.get_equity_percentage('p1')
    assert 65 < p1_equity_pct < 75


def test_finish_probabilities_included() -> None:
    """Test that finish probabilities are included in result."""
    state = TournamentState(
        player_stacks={'p1': 5000, 'p2': 3000, 'p3': 2000},
        payout_structure=[600, 300, 100],
        blinds=100.0
    )
    
    calculator = ICMCalculator()
    result = calculator.calculate_icm(state)
    
    assert len(result.finish_probabilities) == 3
    
    for player_id in ['p1', 'p2', 'p3']:
        assert player_id in result.finish_probabilities
        probs = result.finish_probabilities[player_id]
        assert len(probs) == 3
        # All probabilities should be between 0 and 1
        assert all(0 <= p <= 1 for p in probs)
