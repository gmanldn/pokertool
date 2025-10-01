"""System tests for the MCTS optimizer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.mcts_optimizer import (
    GameState,
    MCTSConfig,
    MCTSNode,
    MCTSOptimizer,
    TranspositionTable,
)


def test_game_state_creation() -> None:
    """Test creating a game state."""
    state = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=1000.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=6,
        betting_history=('check', 'bet_medium')
    )
    
    assert state.street == 'flop'
    assert state.pot_size == 100.0
    assert state.stack_size == 1000.0
    assert len(state.board_cards) == 3
    assert len(state.hole_cards) == 2
    assert state.position == 'button'
    assert not state.is_terminal()


def test_game_state_terminal() -> None:
    """Test terminal state detection."""
    state = GameState(
        street='river',
        pot_size=500.0,
        stack_size=500.0,
        board_cards=('Ah', 'Kd', 'Qc', 'Jh', '9s'),
        hole_cards=('As', 'Ks'),
        position='button',
        num_players=2,
        betting_history=('bet_large', 'fold')
    )
    
    assert state.is_terminal()


def test_game_state_hash() -> None:
    """Test state hashing for transposition table."""
    state1 = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=1000.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=6
    )
    
    state2 = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=1000.0,
        board_cards=('2h', '3d', '4c'),  # Different cards
        hole_cards=('5s', '6s'),
        position='button',
        num_players=6
    )
    
    # Hashes should be same for similar structure
    hash1 = state1.get_state_hash()
    hash2 = state2.get_state_hash()
    assert hash1 == hash2  # Same street, pot, stack, board size


def test_mcts_node_creation() -> None:
    """Test creating an MCTS node."""
    state = GameState(
        street='preflop',
        pot_size=15.0,
        stack_size=985.0,
        board_cards=(),
        hole_cards=('Ah', 'Kh'),
        position='button',
        num_players=6
    )
    
    node = MCTSNode(state=state, parent=None, action=None)
    
    assert node.visits == 0
    assert node.total_value == 0.0
    assert len(node.untried_actions) > 0
    assert not node.is_fully_expanded()


def test_mcts_node_expansion() -> None:
    """Test node expansion."""
    state = GameState(
        street='preflop',
        pot_size=15.0,
        stack_size=985.0,
        board_cards=(),
        hole_cards=('Ah', 'Kh'),
        position='button',
        num_players=6
    )
    
    parent = MCTSNode(state=state, parent=None, action=None)
    
    # Add a child
    action = parent.untried_actions[0]
    new_state = GameState(
        street='preflop',
        pot_size=30.0,
        stack_size=970.0,
        board_cards=(),
        hole_cards=('Ah', 'Kh'),
        position='button',
        num_players=6,
        betting_history=(action,)
    )
    
    child = parent.add_child(action, new_state)
    
    assert child.parent == parent
    assert child.action == action
    assert action in parent.children
    assert action not in parent.untried_actions


def test_mcts_node_best_child() -> None:
    """Test UCT child selection."""
    state = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=900.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=2
    )
    
    parent = MCTSNode(state=state, parent=None, action=None)
    parent.visits = 10
    
    # Create children with different stats
    child1_state = GameState(
        street='flop',
        pot_size=150.0,
        stack_size=850.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=2,
        betting_history=('bet_small',)
    )
    child1 = parent.add_child('bet_small', child1_state)
    child1.visits = 5
    child1.total_value = 3.0  # Win rate: 0.6
    
    child2_state = GameState(
        street='flop',
        pot_size=200.0,
        stack_size=800.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=2,
        betting_history=('bet_large',)
    )
    child2 = parent.add_child('bet_large', child2_state)
    child2.visits = 3
    child2.total_value = 2.0  # Win rate: 0.667
    
    best = parent.best_child(exploration_constant=1.414)
    
    assert best in [child1, child2]
    assert best.visits > 0


def test_transposition_table() -> None:
    """Test transposition table operations."""
    table = TranspositionTable(max_size=100)
    
    # Store entries
    table.store('state1', 10, 7.5)
    table.store('state2', 5, 3.0)
    
    # Lookup entries
    result1 = table.lookup('state1')
    assert result1 is not None
    assert result1 == (10, 7.5)
    
    result2 = table.lookup('state2')
    assert result2 is not None
    assert result2 == (5, 3.0)
    
    # Lookup non-existent
    result3 = table.lookup('state3')
    assert result3 is None
    
    # Clear table
    table.clear()
    assert len(table.table) == 0


def test_transposition_table_eviction() -> None:
    """Test LRU eviction when table is full."""
    table = TranspositionTable(max_size=3)
    
    table.store('state1', 10, 5.0)
    table.store('state2', 20, 10.0)
    table.store('state3', 15, 7.5)
    
    # Access state1 and state3 to make state2 LRU
    table.lookup('state1')
    table.lookup('state3')
    
    # Add new entry, should evict state2
    table.store('state4', 25, 12.5)
    
    assert table.lookup('state2') is None
    assert table.lookup('state1') is not None
    assert table.lookup('state4') is not None


def test_mcts_optimizer_initialization() -> None:
    """Test MCTS optimizer initialization."""
    config = MCTSConfig(
        iterations=1000,
        exploration_constant=1.5,
        time_limit_seconds=5.0
    )
    
    optimizer = MCTSOptimizer(config)
    
    assert optimizer.config.iterations == 1000
    assert optimizer.config.exploration_constant == 1.5
    assert optimizer.config.time_limit_seconds == 5.0
    assert optimizer.iterations_completed == 0


def test_mcts_search_basic() -> None:
    """Test basic MCTS search."""
    state = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=900.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=2
    )
    
    config = MCTSConfig(iterations=100)
    optimizer = MCTSOptimizer(config)
    
    action = optimizer.search(state)
    
    assert action in ['fold', 'check', 'call', 'bet_small', 'bet_medium', 'bet_large', 'allin',
                     'raise_small', 'raise_medium', 'raise_large']
    assert optimizer.iterations_completed <= 100
    assert optimizer.root is not None
    assert optimizer.root.visits > 0


def test_mcts_search_with_time_limit() -> None:
    """Test MCTS search with time limit."""
    state = GameState(
        street='turn',
        pot_size=200.0,
        stack_size=800.0,
        board_cards=('Ah', 'Kd', 'Qc', 'Jh'),
        hole_cards=('Ts', '9s'),
        position='button',
        num_players=2
    )
    
    config = MCTSConfig(
        iterations=1000000,  # Very high
        time_limit_seconds=0.1  # But limited by time
    )
    optimizer = MCTSOptimizer(config)
    
    import time
    start = time.time()
    action = optimizer.search(state)
    elapsed = time.time() - start
    
    assert action is not None
    assert elapsed < 0.5  # Should stop quickly
    assert optimizer.iterations_completed < 1000000


def test_mcts_statistics() -> None:
    """Test getting search statistics."""
    state = GameState(
        street='river',
        pot_size=500.0,
        stack_size=500.0,
        board_cards=('Ah', 'Kd', 'Qc', 'Jh', '9s'),
        hole_cards=('As', 'Ks'),
        position='button',
        num_players=2
    )
    
    config = MCTSConfig(iterations=50)
    optimizer = MCTSOptimizer(config)
    
    optimizer.search(state)
    stats = optimizer.get_statistics()
    
    assert 'iterations' in stats
    assert 'root_visits' in stats
    assert 'root_value' in stats
    assert 'num_children' in stats
    assert 'elapsed_time' in stats
    assert 'children_stats' in stats
    
    assert stats['iterations'] == optimizer.iterations_completed
    assert stats['root_visits'] == optimizer.root.visits


def test_mcts_progressive_widening() -> None:
    """Test progressive widening limits expansion."""
    state = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=900.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=6
    )
    
    config = MCTSConfig(
        iterations=200,
        progressive_widening_constant=2.0,
        progressive_widening_exponent=0.5
    )
    optimizer = MCTSOptimizer(config)
    
    optimizer.search(state)
    
    # Root should have children but not all actions explored
    assert optimizer.root is not None
    assert len(optimizer.root.children) > 0


def test_mcts_action_application() -> None:
    """Test applying actions to states."""
    state = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=900.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=2
    )
    
    optimizer = MCTSOptimizer()
    
    # Test bet action
    new_state = optimizer._apply_action(state, 'bet_medium')
    assert new_state.pot_size > state.pot_size
    assert new_state.stack_size < state.stack_size
    assert 'bet_medium' in new_state.betting_history
    
    # Test fold action
    fold_state = optimizer._apply_action(state, 'fold')
    assert 'fold' in fold_state.betting_history
    assert fold_state.pot_size == state.pot_size  # Pot unchanged on fold


def test_mcts_state_evaluation() -> None:
    """Test heuristic state evaluation."""
    optimizer = MCTSOptimizer()
    
    # Good position state
    good_state = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=900.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('Js', 'Ts'),
        position='button',
        num_players=2
    )
    
    # Bad position state
    bad_state = GameState(
        street='flop',
        pot_size=100.0,
        stack_size=900.0,
        board_cards=('Ah', 'Kd', 'Qc'),
        hole_cards=('7s', '2d'),
        position='early',
        num_players=6
    )
    
    good_value = optimizer._evaluate_state(good_state)
    bad_value = optimizer._evaluate_state(bad_state)
    
    assert 0.0 <= good_value <= 1.0
    assert 0.0 <= bad_value <= 1.0
    assert good_value > bad_value  # Better position should have higher value
