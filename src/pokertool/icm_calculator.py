#!/usr/bin/env python3
"""ICM Calculator - Independent Chip Model calculations"""

import logging
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ICMResult:
    """ICM calculation result"""
    player_stacks: List[int]
    player_equities: List[float]
    prize_pool: List[float]
    player_evs: List[float]


class ICMCalculator:
    """Calculates Independent Chip Model equity."""

    def __init__(self):
        """Initialize ICM calculator."""
        pass

    def calculate_icm(
        self,
        stacks: List[int],
        payouts: List[float]
    ) -> ICMResult:
        """Calculate ICM equity for all players."""
        total_chips = sum(stacks)
        num_players = len(stacks)
        
        # Simple ICM approximation: equity proportional to stack
        equities = [round((stack / total_chips) * 100, 2) for stack in stacks]
        
        # Calculate EV for each player
        evs = []
        for i, stack in enumerate(stacks):
            ev = self._calculate_player_ev(stack, stacks, payouts)
            evs.append(ev)
        
        return ICMResult(
            player_stacks=stacks,
            player_equities=equities,
            prize_pool=payouts,
            player_evs=evs
        )

    def _calculate_player_ev(
        self,
        player_stack: int,
        all_stacks: List[int],
        payouts: List[float]
    ) -> float:
        """Calculate expected value for a player."""
        total_chips = sum(all_stacks)
        stack_percentage = player_stack / total_chips if total_chips > 0 else 0
        
        # Simplified EV calculation
        ev = 0.0
        for i, payout in enumerate(payouts):
            if i == 0:
                # First place weighted by stack percentage
                ev += payout * stack_percentage
            else:
                # Other places get reduced weight
                ev += payout * (stack_percentage / (i + 1))
        
        return round(ev, 2)

    def calculate_chip_ev(
        self,
        current_stack: int,
        all_stacks: List[int],
        payouts: List[float],
        chips_to_risk: int
    ) -> Dict[str, float]:
        """Calculate EV of risking chips."""
        # Current EV
        current_ev = self._calculate_player_ev(current_stack, all_stacks, payouts)
        
        # EV if we win chips
        win_stacks = all_stacks.copy()
        player_idx = all_stacks.index(current_stack)
        win_stacks[player_idx] += chips_to_risk
        win_ev = self._calculate_player_ev(win_stacks[player_idx], win_stacks, payouts)
        
        # EV if we lose chips
        lose_stacks = all_stacks.copy()
        lose_stacks[player_idx] -= chips_to_risk
        if lose_stacks[player_idx] < 0:
            lose_stacks[player_idx] = 0
        lose_ev = self._calculate_player_ev(lose_stacks[player_idx], lose_stacks, payouts)
        
        return {
            'current_ev': current_ev,
            'win_ev': win_ev,
            'lose_ev': lose_ev,
            'risk_premium': round(win_ev - current_ev, 2),
            'risk_penalty': round(current_ev - lose_ev, 2)
        }

    def find_push_fold_threshold(
        self,
        stack: int,
        blinds: int,
        players: int
    ) -> float:
        """Find push/fold threshold in big blinds."""
        bb_stack = stack / blinds
        
        # Simplified threshold based on stack size
        if bb_stack < 10:
            return 20.0  # Push with top 20%
        elif bb_stack < 15:
            return 15.0  # Push with top 15%
        elif bb_stack < 20:
            return 10.0  # Push with top 10%
        else:
            return 5.0   # Push with premium hands only

    def calculate_bubble_factor(
        self,
        stacks: List[int],
        positions_paid: int
    ) -> float:
        """Calculate bubble factor."""
        num_players = len(stacks)
        positions_from_money = num_players - positions_paid
        
        if positions_from_money <= 0:
            return 1.0  # In the money
        elif positions_from_money == 1:
            return 2.5  # On the bubble
        elif positions_from_money == 2:
            return 1.5  # Near bubble
        else:
            return 1.0  # Far from bubble


if __name__ == '__main__':
    calc = ICMCalculator()
    stacks = [5000, 3000, 2000]
    payouts = [500.0, 300.0, 200.0]
    result = calc.calculate_icm(stacks, payouts)
    print(f"Player equities: {result.player_equities}")
    print(f"Player EVs: {result.player_evs}")
