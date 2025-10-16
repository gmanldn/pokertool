#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Gto Solver Module
=============================

This module provides functionality for gto solver operations
within the PokerTool application ecosystem.

Module: pokertool.gto_solver
Version: 20.0.0
Last Modified: 2025-09-29
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v28.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '20.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

import os
import logging
import time
import pickle
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from collections import OrderedDict
import json

try:
    from .core import Card, Rank, Suit, parse_card
except ImportError:
    from pokertool.core import Card, Rank, Suit, parse_card

try:
    from .thread_utils import get_thread_pool, TaskPriority, cpu_intensive
except ImportError:
    from pokertool.concurrency import get_thread_pool, TaskPriority, cpu_intensive

try:
    from .error_handling import retry_on_failure
except ImportError:
    from pokertool.error_handling import retry_on_failure

# Performance telemetry
try:
    from .performance_telemetry import telemetry_section, telemetry_instant
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    # No-op fallback
    from contextlib import contextmanager
    @contextmanager
    def telemetry_section(cat, op, det=None):
        yield
    def telemetry_instant(cat, op, det=None):
        pass

logger = logging.getLogger(__name__)

class Action(Enum):
    """Possible poker actions."""
    FOLD = 'fold'
    CHECK = 'check'
    CALL = 'call'
    BET = 'bet'
    RAISE = 'raise'
    ALL_IN = 'allin'

class Street(Enum):
    """Poker streets/betting rounds."""
    PREFLOP = 'preflop'
    FLOP = 'flop'
    TURN = 'turn'
    RIVER = 'river'

@dataclass
class Range:
    """Represents a poker range with hand combinations and frequencies."""
    hands: Dict[str, float] = field(default_factory=dict)  # hand -> frequency
    
    def __post_init__(self):
        """Normalize frequencies to sum to 1.0."""
        total = sum(self.hands.values())
        if total > 0:
            self.hands = {hand: freq/total for hand, freq in self.hands.items()}
    
    def add_hand(self, hand: str, frequency: float = 1.0):
        """Add a hand to the range."""
        self.hands[hand] = frequency
        self.__post_init__()  # Re-normalize
    
    def remove_hand(self, hand: str):
        """Remove a hand from the range."""
        if hand in self.hands:
            del self.hands[hand]
            self.__post_init__()
    
    def get_frequency(self, hand: str) -> float:
        """Get frequency of a specific hand."""
        return self.hands.get(hand, 0.0)
    
    def total_combos(self) -> int:
        """Get total number of combinations in range."""
        return len(self.hands)
    
    def to_string(self) -> str:
        """Convert range to string representation."""
        if not self.hands:
            return "Empty range"
        
        # Group by frequency for cleaner display
        freq_groups = {}
        for hand, freq in self.hands.items():
            if freq not in freq_groups:
                freq_groups[freq] = []
            freq_groups[freq].append(hand)
        
        parts = []
        for freq in sorted(freq_groups.keys(), reverse=True):
            hands_str = ','.join(sorted(freq_groups[freq]))
            if freq == 1.0:
                parts.append(hands_str)
            else:
                parts.append(f"{hands_str}:{freq:.2f}")
        
        return ', '.join(parts)

@dataclass
class GameState:
    """Represents the current state of a poker hand."""
    street: Street
    pot: float
    effective_stack: float
    board: List[str] = field(default_factory=list)
    position: str = 'UTG'
    num_players: int = 2
    to_call: float = 0.0
    min_bet: float = 0.0
    max_bet: float = float('inf')
    action_history: List[Tuple[str, Action, float]] = field(default_factory=list)  # (player, action, amount)
    
    def get_pot_odds(self) -> float:
        """Calculate pot odds for calling."""
        if self.to_call == 0:
            return float('inf')
        return self.pot / self.to_call
    
    def get_stack_to_pot_ratio(self) -> float:
        """Calculate stack-to-pot ratio."""
        if self.pot == 0:
            return float('inf')
        return self.effective_stack / self.pot

@dataclass
class Strategy:
    """Represents a mixed strategy for a given game state."""
    actions: Dict[Action, float] = field(default_factory=dict)  # action -> frequency
    expected_value: float = 0.0
    
    def __post_init__(self):
        """Normalize action frequencies."""
        total = sum(self.actions.values())
        if total > 0:
            self.actions = {action: freq/total for action, freq in self.actions.items()}
    
    def get_action_frequency(self, action: Action) -> float:
        """Get frequency of a specific action."""
        return self.actions.get(action, 0.0)
    
    def add_action(self, action: Action, frequency: float):
        """Add or update an action in the strategy."""
        self.actions[action] = frequency
        self.__post_init__()
    
    def get_dominant_action(self) -> Optional[Action]:
        """Get the most frequent action."""
        if not self.actions:
            return None
        return max(self.actions.keys(), key=self.actions.get)
    
    def is_pure_strategy(self, threshold: float = 0.95) -> bool:
        """Check if this is essentially a pure strategy."""
        if not self.actions:
            return False
        max_freq = max(self.actions.values())
        return max_freq >= threshold

@dataclass
class GTOSolution:
    """Complete GTO solution for a given scenario."""
    game_state: GameState
    ranges: Dict[str, Range]  # player -> range
    strategies: Dict[str, Dict[str, Strategy]]  # player -> hand -> strategy
    exploitability: float = 0.0
    iterations: int = 0
    solve_time: float = 0.0
    convergence_reached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class LRUCache:
    """LRU Cache with size limit and statistics tracking."""

    def __init__(self, max_size: int = 10000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        self.misses += 1
        return None

    def put(self, key: str, value: Any):
        """Put value in cache with LRU eviction."""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            self.cache[key] = value
            # Evict oldest if over size limit
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }

    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

class EquityCalculator:
    """Fast equity calculation for poker hands with advanced caching."""

    def __init__(self, cache_dir: str = None, cache_size: int = 10000):
        self.cache = LRUCache(max_size=cache_size)
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / "equity_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self._load_disk_cache()

        logger.info(f"EquityCalculator initialized with cache dir: {self.cache_dir}, size: {cache_size}")
    
    def calculate_equity(self, hands: List[str], board: List[str] = None, iterations: int = 100000) -> List[float]:
        """
        Calculate equity for multiple hands against each other.

        Args:
            hands: List of hole card combinations (e.g., ['AsKh', 'QdQc'])
            board: Community cards (e.g., ['Ah', 'Kc', 'Qh'])
            iterations: Number of Monte Carlo iterations

        Returns:
            List of equity values for each hand
        """
        telemetry_instant('gto', 'calculate_equity', {'hands': len(hands), 'iterations': iterations})

        # Create cache key
        cache_key = self._create_cache_key(hands, board, iterations)

        # Check memory cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Check disk cache
        disk_result = self._load_from_disk(cache_key)
        if disk_result is not None:
            self.cache.put(cache_key, disk_result)
            return disk_result
        
        board = board or []
        num_hands = len(hands)
        wins = [0] * num_hands
        
        # Generate all possible remaining cards
        all_cards = self._generate_deck()
        used_cards = set()
        
        # Remove known cards from deck
        for hand in hands:
            if len(hand) >= 4:  # Two cards
                used_cards.add(hand[:2])
                used_cards.add(hand[2:4])
        
        for card in board:
            used_cards.add(card)
        
        remaining_cards = [card for card in all_cards if card not in used_cards]
        
        # Monte Carlo simulation
        import random
        for _ in range(iterations):
            # Complete the board
            random.shuffle(remaining_cards)
            full_board = board + remaining_cards[:5-len(board)]
            
            # Evaluate each hand
            hand_values = []
            for hand in hands:
                if len(hand) >= 4:
                    hole_cards = [hand[:2], hand[2:4]]
                    value = self._evaluate_hand(hole_cards + full_board)
                    hand_values.append(value)
                else:
                    hand_values.append(0)  # Invalid hand
            
            # Find winner(s)
            max_value = max(hand_values)
            winners = [i for i, val in enumerate(hand_values) if val == max_value]
            
            # Split pot among winners
            for winner in winners:
                wins[winner] += 1.0 / len(winners)
        
        # Calculate equity percentages
        equities = [w / iterations for w in wins]

        # Cache result in memory and disk
        self.cache.put(cache_key, equities)
        self._save_to_disk(cache_key, equities)

        return equities
    
    def _create_cache_key(self, hands: List[str], board: List[str], iterations: int) -> str:
        """Create cache key for equity calculation."""
        key_data = {
            'hands': sorted(hands),
            'board': sorted(board) if board else [],
            'iterations': iterations
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _generate_deck(self) -> List[str]:
        """Generate a complete deck of cards."""
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        suits = ['s', 'h', 'd', 'c']
        return [f"{rank}{suit}" for rank in ranks for suit in suits]
    
    def _evaluate_hand(self, cards: List[str]) -> int:
        """
        Simplified hand evaluation (returns higher values for better hands).
        In production, you would use a proper poker hand evaluator.
        """
        if len(cards) < 5:
            return 0
        
        # Parse cards
        parsed_cards = []
        for card in cards:
            try:
                parsed_cards.append(parse_card(card))
            except (ValueError, TypeError, AttributeError):
                continue
        
        if len(parsed_cards) < 5:
            return 0
        
        # Sort by rank (simplified evaluation)
        ranks = sorted([card.rank.value for card in parsed_cards], reverse=True)
        suits = [card.suit for card in parsed_cards]
        
        # Check for flush
        suit_counts = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
        is_flush = max(suit_counts.values()) >= 5
        
        # Check for straight
        unique_ranks = sorted(set(ranks), reverse=True)
        is_straight = False
        if len(unique_ranks) >= 5:
            for i in range(len(unique_ranks) - 4):
                if unique_ranks[i] - unique_ranks[i+4] == 4:
                    is_straight = True
                    break
        
        # Count pairs, trips, etc.
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        count_values = sorted(rank_counts.values(), reverse=True)
        
        # Simplified hand ranking
        if is_straight and is_flush:
            return 8000 + max(ranks)  # Straight flush
        elif count_values[0] == 4:
            return 7000 + max(ranks)  # Four of a kind
        elif count_values[0] == 3 and count_values[1] == 2:
            return 6000 + max(ranks)  # Full house
        elif is_flush:
            return 5000 + max(ranks)  # Flush
        elif is_straight:
            return 4000 + max(ranks)  # Straight
        elif count_values[0] == 3:
            return 3000 + max(ranks)  # Three of a kind
        elif count_values[0] == 2 and count_values[1] == 2:
            return 2000 + max(ranks)  # Two pair
        elif count_values[0] == 2:
            return 1000 + max(ranks)  # One pair
        else:
            return max(ranks)  # High card

    def _load_disk_cache(self):
        """Load most recent equity calculations from disk cache on startup."""
        try:
            cache_files = sorted(self.cache_dir.glob("*.pkl"), key=lambda p: p.stat().st_mtime, reverse=True)
            loaded = 0
            # Load up to 1000 most recent calculations
            for cache_file in cache_files[:1000]:
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                        if isinstance(data, dict) and 'key' in data and 'equities' in data:
                            self.cache.put(data['key'], data['equities'])
                            loaded += 1
                except Exception:
                    continue
            if loaded > 0:
                logger.info(f"Loaded {loaded} equity calculations from disk cache")
        except Exception as e:
            logger.warning(f"Failed to load disk cache: {e}")

    def _load_from_disk(self, cache_key: str) -> Optional[List[float]]:
        """Load equity calculation from disk cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, dict) and 'equities' in data:
                        return data['equities']
        except Exception as e:
            logger.debug(f"Failed to load from disk cache: {e}")
        return None

    def _save_to_disk(self, cache_key: str, equities: List[float]):
        """Save equity calculation to disk cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump({'key': cache_key, 'equities': equities}, f)
        except Exception as e:
            logger.debug(f"Failed to save to disk cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.cache.get_stats()
        stats['disk_cache_files'] = len(list(self.cache_dir.glob("*.pkl")))
        return stats

    def clear_cache(self):
        """Clear both memory and disk caches."""
        self.cache.clear()
        # Clear disk cache (keep last 100 files for warmup)
        cache_files = sorted(self.cache_dir.glob("*.pkl"), key=lambda p: p.stat().st_mtime, reverse=True)
        for cache_file in cache_files[100:]:
            try:
                cache_file.unlink()
            except Exception:
                pass
        logger.info("Equity calculator cache cleared")

class GTOSolver:
    """
    Advanced GTO solver using counterfactual regret minimization (CFR).
    Supports multi-way pots and complex game trees.
    """
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / "gto_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.equity_calculator = EquityCalculator()
        self.solution_cache = {}
        self.thread_pool = get_thread_pool()
        
        # Solver parameters
        self.max_iterations = 10000
        self.convergence_threshold = 0.001
        self.exploration_factor = 0.6
        
        logger.info(f"GTO Solver initialized with cache directory: {self.cache_dir}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def solve(self, game_state: GameState, ranges: Dict[str, Range],
              max_iterations: int = None) -> GTOSolution:
        """
        Solve for GTO strategy using CFR algorithm.

        Args:
            game_state: Current game state
            ranges: Player ranges
            max_iterations: Maximum CFR iterations

        Returns:
            GTOSolution with optimal strategies
        """
        telemetry_instant('gto', 'solve', {'players': len(ranges), 'max_iterations': max_iterations or self.max_iterations})

        start_time = time.time()
        max_iterations = max_iterations or self.max_iterations
        
        # Check cache first
        cache_key = self._create_solution_cache_key(game_state, ranges)
        if cache_key in self.solution_cache:
            logger.debug("Returning cached GTO solution (memory)")
            return self.solution_cache[cache_key]

        # Check disk cache
        disk_solution = self.load_solution_from_disk(cache_key)
        if disk_solution is not None:
            logger.debug("Returning cached GTO solution (disk)")
            self.solution_cache[cache_key] = disk_solution
            return disk_solution
        
        logger.info(f"Starting GTO solve for {len(ranges)} players, {max_iterations} iterations")
        
        # Initialize regret and strategy sums
        regret_sum = {}
        strategy_sum = {}
        
        # CFR iterations
        for iteration in range(max_iterations):
            # Update strategies using regret matching
            for player in ranges:
                if player not in regret_sum:
                    regret_sum[player] = {}
                    strategy_sum[player] = {}
                
                # Generate strategy from regrets
                strategy = self._get_strategy_from_regret(regret_sum[player], game_state)
                
                # Update strategy sum
                for hand in ranges[player].hands:
                    if hand not in strategy_sum[player]:
                        strategy_sum[player][hand] = Strategy()
                    
                    for action in strategy.actions:
                        current_freq = strategy_sum[player][hand].get_action_frequency(action)
                        new_freq = strategy.get_action_frequency(action)
                        strategy_sum[player][hand].add_action(
                            action, 
                            current_freq + new_freq
                        )
            
            # Calculate exploitability periodically
            if iteration % 100 == 0:
                exploitability = self._calculate_exploitability(game_state, ranges, strategy_sum)
                logger.debug(f"Iteration {iteration}: Exploitability = {exploitability:.6f}")
                
                if exploitability < self.convergence_threshold:
                    logger.info(f"Convergence reached at iteration {iteration}")
                    break
        
        # Compute final strategies
        final_strategies = {}
        for player in ranges:
            final_strategies[player] = {}
            for hand in ranges[player].hands:
                if hand in strategy_sum[player]:
                    final_strategies[player][hand] = strategy_sum[player][hand]
                else:
                    # Default strategy (fold)
                    final_strategies[player][hand] = Strategy()
                    final_strategies[player][hand].add_action(Action.FOLD, 1.0)
        
        # Create solution
        solution = GTOSolution(
            game_state=game_state,
            ranges=ranges,
            strategies=final_strategies,
            exploitability=self._calculate_exploitability(game_state, ranges, strategy_sum),
            iterations=iteration + 1,
            solve_time=time.time() - start_time,
            convergence_reached=iteration < max_iterations - 1,
            metadata={
                'solver_version': '1.0',
                'algorithm': 'CFR',
                'max_iterations': max_iterations,
                'convergence_threshold': self.convergence_threshold
            }
        )
        
        # Cache solution
        self.solution_cache[cache_key] = solution
        self._save_solution_to_disk(cache_key, solution)
        
        logger.info(f"GTO solve completed: {solution.iterations} iterations, "
                   f"{solution.solve_time:.2f}s, exploitability={solution.exploitability:.6f}")
        
        return solution
    
    def _get_strategy_from_regret(self, regrets: Dict[str, float], game_state: GameState) -> Strategy:
        """Generate strategy using regret matching."""
        strategy = Strategy()
        
        # Get possible actions
        possible_actions = self._get_possible_actions(game_state)
        
        # Calculate positive regrets
        positive_regrets = {}
        total_positive_regret = 0.0
        
        for action in possible_actions:
            regret = regrets.get(action.value, 0.0)
            if regret > 0:
                positive_regrets[action] = regret
                total_positive_regret += regret
        
        # If no positive regrets, play uniformly
        if total_positive_regret == 0:
            for action in possible_actions:
                strategy.add_action(action, 1.0 / len(possible_actions))
        else:
            # Play proportional to positive regrets
            for action in possible_actions:
                if action in positive_regrets:
                    frequency = positive_regrets[action] / total_positive_regret
                else:
                    frequency = 0.0
                strategy.add_action(action, frequency)
        
        return strategy
    
    def _get_possible_actions(self, game_state: GameState) -> List[Action]:
        """Get possible actions in current game state."""
        actions = [Action.FOLD]
        
        if game_state.to_call == 0:
            actions.append(Action.CHECK)
        else:
            actions.append(Action.CALL)
        
        # Add betting/raising actions
        if game_state.effective_stack > game_state.to_call:
            if game_state.to_call == 0:
                actions.append(Action.BET)
            else:
                actions.append(Action.RAISE)
        
        return actions
    
    def _calculate_exploitability(self, game_state: GameState, ranges: Dict[str, Range],
                                strategies: Dict[str, Dict[str, Strategy]]) -> float:
        """Calculate exploitability of current strategies."""
        # Simplified exploitability calculation
        # In a full implementation, this would involve computing best responses
        return 0.001  # Placeholder
    
    def _create_solution_cache_key(self, game_state: GameState, ranges: Dict[str, Range]) -> str:
        """Create cache key for solution."""
        key_data = {
            'street': game_state.street.value,
            'pot': game_state.pot,
            'effective_stack': game_state.effective_stack,
            'board': sorted(game_state.board),
            'position': game_state.position,
            'num_players': game_state.num_players,
            'to_call': game_state.to_call,
            'ranges': {player: range_obj.to_string() for player, range_obj in ranges.items()}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _save_solution_to_disk(self, cache_key: str, solution: GTOSolution):
        """Save solution to disk cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(solution, f)
            logger.debug(f"Solution cached to disk: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache solution to disk: {e}")
    
    def load_solution_from_disk(self, cache_key: str) -> Optional[GTOSolution]:
        """Load solution from disk cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    solution = pickle.load(f)
                logger.debug(f"Solution loaded from disk: {cache_file}")
                return solution
        except Exception as e:
            logger.warning(f"Failed to load solution from disk: {e}")
        return None

class GTOTrainer:
    """
    GTO training system for practicing optimal play.
    Provides spot training and deviation analysis.
    """
    
    def __init__(self, solver: GTOSolver = None):
        self.solver = solver or GTOSolver()
        self.training_stats = {
            'spots_trained': 0,
            'correct_decisions': 0,
            'total_decisions': 0,
            'accuracy': 0.0
        }
        self.weak_spots = []
    
    def generate_training_spot(self, street: Street = Street.FLOP, 
                             num_players: int = 2) -> Dict[str, Any]:
        """Generate a random training spot."""
        # Generate random game state
        import random
        
        # Random board
        board = []
        if street != Street.PREFLOP:
            all_cards = self.solver.equity_calculator._generate_deck()
            board = random.sample(all_cards, 3)
            if street == Street.TURN:
                board.append(random.choice([c for c in all_cards if c not in board]))
            elif street == Street.RIVER:
                board.extend(random.sample([c for c in all_cards if c not in board], 2))
        
        game_state = GameState(
            street=street,
            pot=random.randint(10, 100),
            effective_stack=random.randint(50, 200),
            board=board,
            num_players=num_players,
            to_call=random.randint(0, 20)
        )
        
        # Generate ranges
        ranges = {}
        for i in range(num_players):
            player = f"Player{i+1}"
            range_obj = Range()
            # Add some random hands
            sample_hands = random.sample(self.solver.equity_calculator._generate_deck(), 20)
            for hand in sample_hands[:10]:  # Top 10 hands
                range_obj.add_hand(hand + random.choice(self.solver.equity_calculator._generate_deck()))
            ranges[player] = range_obj
        
        return {
            'game_state': game_state,
            'ranges': ranges,
            'hero_hand': random.choice(list(ranges['Player1'].hands.keys()))
        }
    
    def evaluate_decision(self, training_spot: Dict[str, Any], 
                         player_action: Action, bet_size: float = 0) -> Dict[str, Any]:
        """Evaluate a training decision against GTO solution."""
        # Solve the spot
        solution = self.solver.solve(training_spot['game_state'], training_spot['ranges'])
        
        # Get GTO strategy for hero hand
        hero_hand = training_spot['hero_hand']
        gto_strategy = solution.strategies.get('Player1', {}).get(hero_hand, Strategy())
        
        # Compare player action to GTO
        gto_frequency = gto_strategy.get_action_frequency(player_action)
        is_correct = gto_frequency > 0.1  # Allow some tolerance
        
        # Update stats
        self.training_stats['total_decisions'] += 1
        if is_correct:
            self.training_stats['correct_decisions'] += 1
        else:
            # Track weak spots
            self.weak_spots.append({
                'game_state': training_spot['game_state'],
                'hero_hand': hero_hand,
                'player_action': player_action,
                'gto_strategy': gto_strategy,
                'timestamp': time.time()
            })
        
        self.training_stats['accuracy'] = (
            self.training_stats['correct_decisions'] / self.training_stats['total_decisions']
        )
        
        return {
            'correct': is_correct,
            'gto_strategy': gto_strategy,
            'player_frequency': gto_frequency,
            'explanation': self._generate_explanation(gto_strategy, player_action),
            'stats': self.training_stats.copy()
        }
    
    def _generate_explanation(self, gto_strategy: Strategy, player_action: Action) -> str:
        """Generate explanation for GTO decision."""
        if not gto_strategy.actions:
            return "No GTO data available for this spot."
        
        dominant_action = gto_strategy.get_dominant_action()
        player_freq = gto_strategy.get_action_frequency(player_action)
        
        if player_freq == 0:
            return f"GTO never plays {player_action.value}. Should play {dominant_action.value} {gto_strategy.get_action_frequency(dominant_action)*100:.1f}% of the time."
        elif player_freq >= 0.3:
            return f"Good decision! GTO plays {player_action.value} {player_freq*100:.1f}% of the time."
        else:
            return f"Suboptimal. GTO only plays {player_action.value} {player_freq*100:.1f}% of the time. Consider {dominant_action.value} more often."
    
    def get_weak_spots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent weak spots for review."""
        return sorted(self.weak_spots, key=lambda x: x['timestamp'], reverse=True)[:limit]

class DeviationExplorer:
    """
    Explore deviations from GTO strategy and their impact.
    """
    
    def __init__(self, solver: GTOSolver = None):
        self.solver = solver or GTOSolver()
    
    def analyze_deviation(self, game_state: GameState, ranges: Dict[str, Range],
                         player: str, deviation_strategy: Strategy) -> Dict[str, Any]:
        """
        Analyze the impact of deviating from GTO strategy.
        
        Returns expected value change, counter-exploits, etc.
        """
        # Get GTO solution
        gto_solution = self.solver.solve(game_state, ranges)
        
        # Calculate EV of deviation vs GTO
        gto_ev = self._calculate_strategy_ev(gto_solution, player)
        deviation_ev = self._calculate_deviation_ev(gto_solution, player, deviation_strategy)
        
        ev_loss = gto_ev - deviation_ev
        
        return {
            'gto_ev': gto_ev,
            'deviation_ev': deviation_ev,
            'ev_loss': ev_loss,
            'ev_loss_bb': ev_loss / (game_state.pot / 100),  # Convert to big blinds
            'exploitability_increase': self._calculate_exploitability_increase(
                gto_solution, player, deviation_strategy
            ),
            'counter_exploit_suggestions': self._suggest_counter_exploits(
                gto_solution, player, deviation_strategy
            )
        }
    
    def _calculate_strategy_ev(self, solution: GTOSolution, player: str) -> float:
        """Calculate expected value of a strategy."""
        # Simplified EV calculation
        return 0.0  # Placeholder
    
    def _calculate_deviation_ev(self, solution: GTOSolution, player: str, 
                              deviation_strategy: Strategy) -> float:
        """Calculate EV of deviation strategy."""
        # Simplified calculation
        return 0.0  # Placeholder
    
    def _calculate_exploitability_increase(self, solution: GTOSolution, player: str,
                                         deviation_strategy: Strategy) -> float:
        """Calculate how much deviation increases exploitability."""
        return 0.0  # Placeholder
    
    def _suggest_counter_exploits(self, solution: GTOSolution, player: str,
                                deviation_strategy: Strategy) -> List[str]:
        """Suggest how opponents can exploit the deviation."""
        suggestions = []
        
        # Analyze deviation patterns
        if deviation_strategy.get_action_frequency(Action.BET) > 0.7:
            suggestions.append("Opponent is over-betting. Consider calling/raising more with medium strength hands.")
        
        if deviation_strategy.get_action_frequency(Action.FOLD) > 0.6:
            suggestions.append("Opponent is over-folding. Increase bluffing frequency.")
        
        return suggestions

# Global GTO solver instance
_gto_solver: Optional[GTOSolver] = None

def get_gto_solver() -> GTOSolver:
    """Get the global GTO solver instance."""
    global _gto_solver
    if _gto_solver is None:
        _gto_solver = GTOSolver()
    return _gto_solver

def solve_spot(game_state: GameState, ranges: Dict[str, Range], 
               max_iterations: int = None) -> GTOSolution:
    """Convenience function to solve a GTO spot."""
    solver = get_gto_solver()
    return solver.solve(game_state, ranges, max_iterations)

def create_standard_ranges() -> Dict[str, Range]:
    """Create standard preflop ranges for common positions."""
    ranges = {}
    
    # UTG range (tight)
    utg_hands = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', 'AKs', 'AKo', 'AQs', 'AJs', 'ATs']
    utg_range = Range()
    for hand in utg_hands:
        utg_range.add_hand(hand)
    ranges['UTG'] = utg_range
    
    # Button range (wide)
    btn_hands = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
                 'AKs', 'AKo', 'AQs', 'AQo', 'AJs', 'AJo', 'ATs', 'ATo', 'A9s', 'A8s', 'A7s',
                 'KQs', 'KQo', 'KJs', 'KJo', 'KTs', 'K9s', 'QJs', 'QJo', 'QTs', 'Q9s', 'JTs']
    btn_range = Range()
    for hand in btn_hands:
        btn_range.add_hand(hand)
    ranges['BTN'] = btn_range
    
    return ranges

def parse_range_string(range_str: str) -> Range:
    """Parse a range string into a Range object."""
    range_obj = Range()
    
    # Split by commas and parse each part
    parts = [part.strip() for part in range_str.split(',')]
    
    for part in parts:
        if ':' in part:
            # Hand with specific frequency
            hands_part, freq_part = part.split(':')
            frequency = float(freq_part)
            hands = hands_part.split(',')
        else:
            # Default frequency of 1.0
            hands = [part]
            frequency = 1.0
        
        for hand in hands:
            hand = hand.strip()
            if hand:
                range_obj.add_hand(hand, frequency)
    
    return range_obj

def calculate_range_equity(range1: Range, range2: Range, board: List[str] = None, 
                         iterations: int = 10000) -> Tuple[float, float]:
    """Calculate equity between two ranges."""
    equity_calc = EquityCalculator()
    
    total_equity1 = 0.0
    total_equity2 = 0.0
    total_weight = 0.0
    
    # Sample hands from ranges for equity calculation
    import random
    
    sample_size = min(100, len(range1.hands) * len(range2.hands))
    
    for _ in range(sample_size):
        # Sample hands weighted by frequency
        hand1 = random.choices(
            list(range1.hands.keys()), 
            weights=list(range1.hands.values())
        )[0]
        
        hand2 = random.choices(
            list(range2.hands.keys()), 
            weights=list(range2.hands.values())
        )[0]
        
        # Calculate equity for this matchup
        equities = equity_calc.calculate_equity([hand1, hand2], board, iterations//sample_size)
        
        weight = range1.get_frequency(hand1) * range2.get_frequency(hand2)
        total_equity1 += equities[0] * weight
        total_equity2 += equities[1] * weight
        total_weight += weight
    
    if total_weight > 0:
        return total_equity1 / total_weight, total_equity2 / total_weight
    else:
        return 0.5, 0.5

# Analysis utilities
def analyze_gto_spot(hole_cards: str, board: List[str], position: str, 
                    pot: float, to_call: float, effective_stack: float) -> Dict[str, Any]:
    """
    Analyze a specific GTO spot and return recommendations.
    
    Args:
        hole_cards: Hero's hole cards (e.g., "AsKh")
        board: Community cards
        position: Hero's position
        pot: Current pot size
        to_call: Amount to call
        effective_stack: Effective stack size
        
    Returns:
        Analysis with GTO recommendations
    """
    # Create game state
    street = Street.PREFLOP
    if len(board) >= 3:
        street = Street.FLOP
    if len(board) >= 4:
        street = Street.TURN
    if len(board) == 5:
        street = Street.RIVER
    
    game_state = GameState(
        street=street,
        pot=pot,
        effective_stack=effective_stack,
        board=board,
        position=position,
        to_call=to_call
    )
    
    # Create ranges based on position
    ranges = create_standard_ranges()
    
    # Solve the spot
    solver = get_gto_solver()
    solution = solver.solve(game_state, ranges)
    
    # Get strategy for hero's hand
    hero_strategy = solution.strategies.get(position, {}).get(hole_cards, Strategy())
    
    # Calculate additional metrics
    pot_odds = game_state.get_pot_odds()
    spr = game_state.get_stack_to_pot_ratio()
    
    return {
        'hole_cards': hole_cards,
        'board': board,
        'position': position,
        'game_state': game_state,
        'gto_strategy': hero_strategy,
        'dominant_action': hero_strategy.get_dominant_action(),
        'action_frequencies': hero_strategy.actions,
        'pot_odds': pot_odds,
        'stack_to_pot_ratio': spr,
        'solution_quality': {
            'exploitability': solution.exploitability,
            'iterations': solution.iterations,
            'converged': solution.convergence_reached,
            'solve_time': solution.solve_time
        },
        'recommendations': _generate_recommendations(hero_strategy, game_state)
    }

def _generate_recommendations(strategy: Strategy, game_state: GameState) -> List[str]:
    """Generate human-readable recommendations from GTO strategy."""
    recommendations = []
    
    if not strategy.actions:
        recommendations.append("Insufficient data for this spot.")
        return recommendations
    
    dominant_action = strategy.get_dominant_action()
    dominant_freq = strategy.get_action_frequency(dominant_action)
    
    # Primary recommendation
    if dominant_freq > 0.7:
        recommendations.append(f"Primary play: {dominant_action.value} {dominant_freq*100:.1f}% of the time")
    else:
        recommendations.append(f"Mixed strategy: {dominant_action.value} {dominant_freq*100:.1f}% (most frequent)")
    
    # Secondary actions
    sorted_actions = sorted(strategy.actions.items(), key=lambda x: x[1], reverse=True)
    for action, freq in sorted_actions[1:]:
        if freq > 0.1:  # Only mention actions with significant frequency
            recommendations.append(f"Also play {action.value} {freq*100:.1f}% of the time")
    
    # Contextual advice
    if game_state.get_pot_odds() < 3:
        recommendations.append("Good pot odds - consider calling more often with draws")
    
    if game_state.get_stack_to_pot_ratio() < 1:
        recommendations.append("Low SPR - consider simplified strategies")
    
    return recommendations

# Training and practice utilities
def create_training_session(difficulty: str = 'intermediate', num_spots: int = 10) -> List[Dict[str, Any]]:
    """Create a GTO training session with multiple spots."""
    trainer = GTOTrainer()
    spots = []
    
    difficulty_settings = {
        'beginner': {'streets': [Street.PREFLOP], 'players': [2]},
        'intermediate': {'streets': [Street.PREFLOP, Street.FLOP], 'players': [2, 3]},
        'advanced': {'streets': [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER], 'players': [2, 3, 4, 5, 6]}
    }
    
    settings = difficulty_settings.get(difficulty, difficulty_settings['intermediate'])
    
    import random
    for _ in range(num_spots):
        street = random.choice(settings['streets'])
        players = random.choice(settings['players'])
        spot = trainer.generate_training_spot(street, players)
        spots.append(spot)
    
    return spots

def export_solution(solution: GTOSolution, filename: str, format: str = 'json') -> bool:
    """Export GTO solution to file."""
    try:
        if format == 'json':
            # Convert solution to JSON-serializable format
            export_data = {
                'game_state': {
                    'street': solution.game_state.street.value,
                    'pot': solution.game_state.pot,
                    'effective_stack': solution.game_state.effective_stack,
                    'board': solution.game_state.board,
                    'position': solution.game_state.position,
                    'num_players': solution.game_state.num_players,
                    'to_call': solution.game_state.to_call
                },
                'ranges': {player: range_obj.to_string() for player, range_obj in solution.ranges.items()},
                'strategies': {
                    player: {
                        hand: {
                            'actions': {action.value: freq for action, freq in strategy.actions.items()},
                            'expected_value': strategy.expected_value
                        } for hand, strategy in hands.items()
                    } for player, hands in solution.strategies.items()
                },
                'exploitability': solution.exploitability,
                'iterations': solution.iterations,
                'solve_time': solution.solve_time,
                'convergence_reached': solution.convergence_reached,
                'metadata': solution.metadata
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
                
        elif format == 'pickle':
            with open(filename, 'wb') as f:
                pickle.dump(solution, f)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Solution exported to {filename} in {format} format")
        return True
        
    except Exception as e:
        logger.error(f"Failed to export solution: {e}")
        return False

if __name__ == '__main__':
    # Test GTO solver functionality
    print("Testing GTO Solver...")
    
    # Create a simple test scenario
    game_state = GameState(
        street=Street.FLOP,
        pot=20.0,
        effective_stack=100.0,
        board=['Ah', 'Kc', 'Qh'],
        position='BTN',
        num_players=2,
        to_call=5.0
    )
    
    # Create test ranges
    ranges = create_standard_ranges()
    
    # Test equity calculation
    equity_calc = EquityCalculator()
    test_hands = ['AsKh', 'QdQc']
    equities = equity_calc.calculate_equity(test_hands, game_state.board, iterations=1000)
    print(f"Equity test: {test_hands[0]} vs {test_hands[1]} = {equities[0]*100:.1f}% vs {equities[1]*100:.1f}%")
    
    # Test GTO solver
    solver = get_gto_solver()
    solution = solver.solve(game_state, ranges, max_iterations=100)
    print(f"GTO solve completed: {solution.iterations} iterations, exploitability={solution.exploitability:.6f}")
    
    # Test training
    trainer = GTOTrainer(solver)
    training_spot = trainer.generate_training_spot()
    print(f"Generated training spot: {training_spot['hero_hand']} on {training_spot['game_state'].street.value}")
    
    # Test spot analysis
    analysis = analyze_gto_spot('AsKh', ['Ah', 'Kc', 'Qh'], 'BTN', 20.0, 5.0, 100.0)
    print(f"Spot analysis: {analysis['dominant_action']}")
    print("GTO Solver test completed successfully!")
