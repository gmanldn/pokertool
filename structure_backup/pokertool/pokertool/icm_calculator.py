"""Real-time Independent Chip Model (ICM) calculator for tournament poker.

This module implements ICM calculations for tournament optimal play, including:
- Malmuth-Harville algorithm for prize distribution
- Future game simulation
- Bubble factor calculations
- Risk premium adjustments
- Payout structure optimization

Module: icm_calculator
Version: 1.0.0
Last Updated: 2025-10-05
Task: ICM-001
Dependencies: None
Test Coverage: tests/system/test_icm_calculator.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass
class TournamentState:
    """Represents the current state of a poker tournament."""
    
    player_stacks: Dict[str, float]  # player_id -> stack size
    payout_structure: List[float]  # Prize amounts in order
    blinds: float
    ante: float = 0.0
    
    def __post_init__(self) -> None:
        self.blinds = float(self.blinds)
        self.ante = float(self.ante)
        
    @property
    def num_players(self) -> int:
        """Get number of remaining players."""
        return len(self.player_stacks)
    
    @property
    def total_chips(self) -> float:
        """Get total chips in play."""
        return sum(self.player_stacks.values())
    
    def get_stack_sizes(self) -> List[float]:
        """Get stack sizes as a sorted list."""
        return sorted(self.player_stacks.values(), reverse=True)


@dataclass
class ICMResult:
    """Result of an ICM calculation."""
    
    player_equity: Dict[str, float]  # player_id -> $ equity
    finish_probabilities: Dict[str, List[float]]  # player_id -> [1st%, 2nd%, ...]
    total_equity: float
    
    def get_equity_percentage(self, player_id: str) -> float:
        """Get player's equity as percentage of total prize pool."""
        if self.total_equity == 0:
            return 0.0
        return (self.player_equity.get(player_id, 0.0) / self.total_equity) * 100


@dataclass
class ICMDecision:
    """ICM-adjusted decision analysis."""
    
    action: str
    cEV: float  # Chip EV
    dollar_ev: float  # Dollar EV (ICM adjusted)
    risk_premium: float  # Difference between cEV and $EV
    recommended: bool


class MalmuthHarvilleCalculator:
    """Implements the Malmuth-Harville algorithm for ICM calculations.
    
    The Malmuth-Harville algorithm calculates the probability of each player
    finishing in each position based on their chip stacks.
    """
    
    def __init__(self, memoize: bool = True):
        """Initialize the calculator.
        
        Args:
            memoize: Whether to cache calculation results
        """
        self.memoize = memoize
        self._cache: Dict[str, float] = {}
    
    def calculate_finish_probability(
        self, 
        stack_sizes: Sequence[float], 
        player_index: int, 
        position: int
    ) -> float:
        """Calculate probability of a player finishing in a specific position.
        
        Args:
            stack_sizes: List of stack sizes (in chip order)
            player_index: Index of the player to calculate for
            position: Finish position (0 = 1st, 1 = 2nd, etc.)
            
        Returns:
            Probability (0.0 to 1.0)
        """
        if position < 0 or position >= len(stack_sizes):
            return 0.0
        
        if player_index < 0 or player_index >= len(stack_sizes):
            return 0.0
        
        # Check cache
        if self.memoize:
            cache_key = f"{tuple(stack_sizes)}:{player_index}:{position}"
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        # Base case: only one player left
        if len(stack_sizes) == 1:
            result = 1.0 if position == 0 else 0.0
        # Base case: calculating for first place
        elif position == 0:
            total_chips = sum(stack_sizes)
            if total_chips == 0:
                result = 0.0
            else:
                result = stack_sizes[player_index] / total_chips
        else:
            # Recursive case: probability of finishing in position
            # = sum over all other players of:
            #   (probability that other player finishes before) *
            #   (probability player finishes in position-1 among remaining)
            total_chips = sum(stack_sizes)
            if total_chips == 0:
                result = 0.0
            else:
                prob_sum = 0.0
                
                for other_idx in range(len(stack_sizes)):
                    if other_idx == player_index:
                        continue
                    
                    # Probability other player finishes before this player
                    prob_other_first = stack_sizes[other_idx] / total_chips
                    
                    # Create new stack list without other player
                    remaining_stacks = [
                        stack_sizes[i] for i in range(len(stack_sizes)) 
                        if i != other_idx
                    ]
                    
                    # Adjust player index for removed player
                    new_player_idx = player_index
                    if other_idx < player_index:
                        new_player_idx -= 1
                    
                    # Recursive probability for remaining positions
                    prob_player_next = self.calculate_finish_probability(
                        remaining_stacks, new_player_idx, position - 1
                    )
                    
                    prob_sum += prob_other_first * prob_player_next
                
                result = prob_sum
        
        # Cache result
        if self.memoize:
            cache_key = f"{tuple(stack_sizes)}:{player_index}:{position}"
            self._cache[cache_key] = result
        
        return result
    
    def clear_cache(self) -> None:
        """Clear the memoization cache."""
        self._cache.clear()


class ICMCalculator:
    """Real-time ICM calculator for tournament poker.
    
    Provides comprehensive ICM calculations including:
    - Player equity calculation
    - Finish probability distributions
    - Bubble factor analysis
    - Risk premium calculations
    """
    
    def __init__(self):
        """Initialize the ICM calculator."""
        self.mh_calculator = MalmuthHarvilleCalculator(memoize=True)
    
    def calculate_icm(self, tournament_state: TournamentState) -> ICMResult:
        """Calculate ICM equity for all players.
        
        Args:
            tournament_state: Current tournament state
            
        Returns:
            ICMResult with equities and probabilities
        """
        player_ids = list(tournament_state.player_stacks.keys())
        stack_sizes = [tournament_state.player_stacks[pid] for pid in player_ids]
        
        player_equity: Dict[str, float] = {}
        finish_probabilities: Dict[str, List[float]] = {}
        
        # Calculate for each player
        for idx, player_id in enumerate(player_ids):
            equity = 0.0
            probs = []
            
            # Calculate probability of each finish position
            num_paid = min(len(tournament_state.payout_structure), len(player_ids))
            
            for position in range(num_paid):
                prob = self.mh_calculator.calculate_finish_probability(
                    stack_sizes, idx, position
                )
                probs.append(prob)
                
                # Add equity for this finish
                if position < len(tournament_state.payout_structure):
                    equity += prob * tournament_state.payout_structure[position]
            
            player_equity[player_id] = equity
            finish_probabilities[player_id] = probs
        
        total_equity = sum(tournament_state.payout_structure)
        
        return ICMResult(
            player_equity=player_equity,
            finish_probabilities=finish_probabilities,
            total_equity=total_equity
        )
    
    def calculate_bubble_factor(
        self, 
        tournament_state: TournamentState,
        player_id: str
    ) -> float:
        """Calculate the bubble factor for a player.
        
        The bubble factor represents how much ICM pressure affects decisions,
        especially near the money bubble.
        
        Args:
            tournament_state: Current tournament state
            player_id: Player to calculate for
            
        Returns:
            Bubble factor (typically 0.5 to 2.0)
        """
        num_players = tournament_state.num_players
        num_paid = len(tournament_state.payout_structure)
        
        # Not on bubble if already in the money or far from it
        if num_players <= num_paid:
            return 1.0  # Already ITM
        
        if num_players > num_paid + 5:
            return 0.9  # Far from bubble
        
        # Calculate current ICM
        current_icm = self.calculate_icm(tournament_state)
        current_equity = current_icm.player_equity.get(player_id, 0.0)
        
        # Calculate chip EV (proportional equity)
        player_stack = tournament_state.player_stacks.get(player_id, 0.0)
        total_chips = tournament_state.total_chips
        chip_ev = (player_stack / total_chips) * current_icm.total_equity if total_chips > 0 else 0.0
        
        # Bubble factor is ratio of ICM equity to chip equity
        if chip_ev == 0:
            return 1.0
        
        bubble_factor = current_equity / chip_ev
        
        # Clamp to reasonable range
        return max(0.5, min(2.0, bubble_factor))
    
    def calculate_risk_premium(
        self,
        tournament_state: TournamentState,
        player_id: str,
        chips_at_risk: float
    ) -> float:
        """Calculate the risk premium for putting chips at risk.
        
        Args:
            tournament_state: Current tournament state
            player_id: Player making the decision
            chips_at_risk: Number of chips being risked
            
        Returns:
            Risk premium in dollars
        """
        # Current equity
        current_icm = self.calculate_icm(tournament_state)
        current_equity = current_icm.player_equity.get(player_id, 0.0)
        
        # Equity if we lose the chips
        lose_state = self._modify_stack(tournament_state, player_id, -chips_at_risk)
        lose_icm = self.calculate_icm(lose_state)
        lose_equity = lose_icm.player_equity.get(player_id, 0.0)
        
        # Equity if we win the chips
        win_state = self._modify_stack(tournament_state, player_id, chips_at_risk)
        win_icm = self.calculate_icm(win_state)
        win_equity = win_icm.player_equity.get(player_id, 0.0)
        
        # Risk premium is the difference between chip EV and ICM EV
        chip_ev = current_equity  # Baseline
        icm_ev = (lose_equity + win_equity) / 2  # Average of outcomes
        
        return chip_ev - icm_ev
    
    def analyze_decision(
        self,
        tournament_state: TournamentState,
        player_id: str,
        action: str,
        chips_at_risk: float,
        win_probability: float
    ) -> ICMDecision:
        """Analyze a decision using ICM.
        
        Args:
            tournament_state: Current tournament state
            player_id: Player making the decision
            action: Action being considered
            chips_at_risk: Chips being risked
            win_probability: Probability of winning the chips
            
        Returns:
            ICMDecision with analysis
        """
        # Calculate chip EV
        chip_ev = (win_probability * chips_at_risk) - ((1 - win_probability) * chips_at_risk)
        
        # Calculate ICM equity changes
        current_icm = self.calculate_icm(tournament_state)
        current_equity = current_icm.player_equity.get(player_id, 0.0)
        
        # Win scenario
        win_state = self._modify_stack(tournament_state, player_id, chips_at_risk)
        win_icm = self.calculate_icm(win_state)
        win_equity = win_icm.player_equity.get(player_id, 0.0)
        
        # Lose scenario
        lose_state = self._modify_stack(tournament_state, player_id, -chips_at_risk)
        lose_icm = self.calculate_icm(lose_state)
        lose_equity = lose_icm.player_equity.get(player_id, 0.0)
        
        # Calculate dollar EV
        dollar_ev = (win_probability * win_equity) + ((1 - win_probability) * lose_equity) - current_equity
        
        # Risk premium
        risk_premium = chip_ev - dollar_ev
        
        # Recommendation
        recommended = dollar_ev > 0
        
        return ICMDecision(
            action=action,
            cEV=chip_ev,
            dollar_ev=dollar_ev,
            risk_premium=risk_premium,
            recommended=recommended
        )
    
    def _modify_stack(
        self,
        tournament_state: TournamentState,
        player_id: str,
        chip_change: float
    ) -> TournamentState:
        """Create a new tournament state with modified stack.
        
        Args:
            tournament_state: Original state
            player_id: Player whose stack to modify
            chip_change: Chips to add (positive) or remove (negative)
            
        Returns:
            New TournamentState with modified stack
        """
        new_stacks = dict(tournament_state.player_stacks)
        current_stack = new_stacks.get(player_id, 0.0)
        new_stack = max(0.0, current_stack + chip_change)
        
        if new_stack > 0:
            new_stacks[player_id] = new_stack
        else:
            # Player is eliminated
            if player_id in new_stacks:
                del new_stacks[player_id]
        
        return TournamentState(
            player_stacks=new_stacks,
            payout_structure=tournament_state.payout_structure,
            blinds=tournament_state.blinds,
            ante=tournament_state.ante
        )
    
    def optimize_payout_structure(
        self,
        total_prize_pool: float,
        num_players: int,
        num_paid: int
    ) -> List[float]:
        """Generate an optimized payout structure.
        
        Creates a payout structure that balances:
        - Rewarding top finishers
        - Providing min-cash opportunities
        - ICM-friendly distribution
        
        Args:
            total_prize_pool: Total money to distribute
            num_players: Number of players in tournament
            num_paid: Number of places to pay
            
        Returns:
            List of prize amounts in order
        """
        if num_paid <= 0 or num_paid > num_players:
            return []
        
        if num_paid == 1:
            return [total_prize_pool]
        
        # Use exponential decay for prize distribution
        # First place gets ~35-40% of prize pool
        # Distribution becomes flatter as positions increase
        
        payouts = []
        remaining_pool = total_prize_pool
        
        for position in range(num_paid):
            if position == num_paid - 1:
                # Last place gets remaining amount
                payouts.append(remaining_pool)
            else:
                # Exponential decay factor
                position_factor = math.exp(-position * 0.5)
                total_factors = sum(math.exp(-i * 0.5) for i in range(num_paid))
                
                payout = (total_prize_pool * position_factor) / total_factors
                payouts.append(payout)
                remaining_pool -= payout
        
        return payouts
    
    def simulate_future_game(
        self,
        tournament_state: TournamentState,
        num_simulations: int = 1000
    ) -> Dict[str, float]:
        """Simulate future game outcomes to estimate final equity.
        
        Args:
            tournament_state: Current state
            num_simulations: Number of simulations to run
            
        Returns:
            Dictionary of player_id to average finish equity
        """
        # Simplified simulation using ICM as proxy
        # In production, would simulate actual hand outcomes
        
        icm_result = self.calculate_icm(tournament_state)
        
        # Add variance to ICM estimates based on stack sizes
        simulated_equity: Dict[str, List[float]] = {
            pid: [] for pid in tournament_state.player_stacks.keys()
        }
        
        for _ in range(num_simulations):
            # Use ICM as base, add random variance
            for player_id in tournament_state.player_stacks.keys():
                base_equity = icm_result.player_equity[player_id]
                
                # Add variance proportional to stack size
                stack_ratio = (tournament_state.player_stacks[player_id] / 
                             tournament_state.total_chips)
                variance = stack_ratio * 0.1 * icm_result.total_equity
                
                # Random outcome around base
                import random
                simulated_value = base_equity + random.gauss(0, variance)
                simulated_equity[player_id].append(max(0, simulated_value))
        
        # Average results
        return {
            player_id: sum(values) / len(values)
            for player_id, values in simulated_equity.items()
        }


__all__ = [
    'TournamentState',
    'ICMResult',
    'ICMDecision',
    'MalmuthHarvilleCalculator',
    'ICMCalculator',
]
