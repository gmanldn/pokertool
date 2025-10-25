#!/usr/bin/env python3
"""HUD Stats Calculator - Calculates common HUD statistics"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Action(Enum):
    """Player actions"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"


class Street(Enum):
    """Betting streets"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


@dataclass
class HandAction:
    """Single hand action record"""
    player_name: str
    street: Street
    action: Action
    amount: float
    was_facing_bet: bool


@dataclass
class HUDStats:
    """Calculated HUD statistics"""
    vpip: float  # Voluntarily put money in pot
    pfr: float   # Pre-flop raise
    af: float    # Aggression factor
    wtsd: float  # Went to showdown
    w_sd: float  # Won at showdown
    three_bet: float  # 3-bet percentage
    fold_to_3bet: float  # Fold to 3-bet percentage
    cbet: float  # Continuation bet


class HUDStatsCalculator:
    """Calculates HUD statistics from hand histories."""

    def __init__(self):
        """Initialize HUD stats calculator."""
        self.hands: List[List[HandAction]] = []
        self.showdowns: Dict[str, int] = {}
        self.showdown_wins: Dict[str, int] = {}

    def add_hand(self, actions: List[HandAction]):
        """Add a hand's actions."""
        self.hands.append(actions)
        logger.debug(f"Added hand with {len(actions)} actions")

    def record_showdown(self, player_name: str, won: bool):
        """Record showdown result."""
        if player_name not in self.showdowns:
            self.showdowns[player_name] = 0
            self.showdown_wins[player_name] = 0

        self.showdowns[player_name] += 1
        if won:
            self.showdown_wins[player_name] += 1

    def calculate_vpip(self, player_name: str) -> float:
        """Calculate VPIP (Voluntarily Put money In Pot) percentage."""
        total_hands = 0
        vpip_hands = 0

        for hand in self.hands:
            player_actions = [a for a in hand if a.player_name == player_name and a.street == Street.PREFLOP]
            if player_actions:
                total_hands += 1
                # VPIP if they called, bet, or raised (not just posting blinds)
                if any(a.action in [Action.CALL, Action.BET, Action.RAISE] for a in player_actions):
                    vpip_hands += 1

        return round((vpip_hands / total_hands * 100), 2) if total_hands > 0 else 0.0

    def calculate_pfr(self, player_name: str) -> float:
        """Calculate PFR (Pre-Flop Raise) percentage."""
        total_hands = 0
        pfr_hands = 0

        for hand in self.hands:
            player_actions = [a for a in hand if a.player_name == player_name and a.street == Street.PREFLOP]
            if player_actions:
                total_hands += 1
                if any(a.action == Action.RAISE for a in player_actions):
                    pfr_hands += 1

        return round((pfr_hands / total_hands * 100), 2) if total_hands > 0 else 0.0

    def calculate_aggression_factor(self, player_name: str) -> float:
        """Calculate Aggression Factor (bets+raises / calls)."""
        aggressive_actions = 0
        passive_actions = 0

        for hand in self.hands:
            player_actions = [a for a in hand if a.player_name == player_name]
            for action in player_actions:
                if action.action in [Action.BET, Action.RAISE]:
                    aggressive_actions += 1
                elif action.action == Action.CALL:
                    passive_actions += 1

        return round(aggressive_actions / passive_actions, 2) if passive_actions > 0 else float(aggressive_actions)

    def calculate_wtsd(self, player_name: str) -> float:
        """Calculate WTSD (Went To ShowDown) percentage."""
        total_hands = len([h for h in self.hands if any(a.player_name == player_name for a in h)])
        showdowns = self.showdowns.get(player_name, 0)

        return round((showdowns / total_hands * 100), 2) if total_hands > 0 else 0.0

    def calculate_w_sd(self, player_name: str) -> float:
        """Calculate W$SD (Won $ at ShowDown) percentage."""
        showdowns = self.showdowns.get(player_name, 0)
        wins = self.showdown_wins.get(player_name, 0)

        return round((wins / showdowns * 100), 2) if showdowns > 0 else 0.0

    def calculate_three_bet(self, player_name: str) -> float:
        """Calculate 3-bet percentage."""
        opportunities = 0
        three_bets = 0

        for hand in self.hands:
            preflop_actions = [a for a in hand if a.street == Street.PREFLOP]
            player_actions = [a for a in preflop_actions if a.player_name == player_name]

            # Check if there was a raise before player acted
            for player_action in player_actions:
                if player_action.was_facing_bet:
                    opportunities += 1
                    if player_action.action == Action.RAISE:
                        three_bets += 1

        return round((three_bets / opportunities * 100), 2) if opportunities > 0 else 0.0

    def calculate_fold_to_3bet(self, player_name: str) -> float:
        """Calculate fold to 3-bet percentage."""
        opportunities = 0
        folds = 0

        for hand in self.hands:
            preflop_actions = [a for a in hand if a.street == Street.PREFLOP]

            # Find if player raised, then faced a re-raise
            player_raised = False
            for i, action in enumerate(preflop_actions):
                if action.player_name == player_name and action.action == Action.RAISE:
                    player_raised = True
                elif player_raised and action.action == Action.RAISE:
                    # Someone 3-bet after player's raise
                    opportunities += 1
                    # Check if player folded
                    remaining = preflop_actions[i+1:]
                    if any(a.player_name == player_name and a.action == Action.FOLD for a in remaining):
                        folds += 1
                    break

        return round((folds / opportunities * 100), 2) if opportunities > 0 else 0.0

    def calculate_cbet(self, player_name: str) -> float:
        """Calculate C-bet (Continuation Bet) percentage."""
        opportunities = 0
        cbets = 0

        for hand in self.hands:
            # Check if player was preflop raiser
            preflop = [a for a in hand if a.street == Street.PREFLOP and a.player_name == player_name]
            if any(a.action == Action.RAISE for a in preflop):
                # Check if they bet on flop
                flop = [a for a in hand if a.street == Street.FLOP and a.player_name == player_name]
                if flop:
                    opportunities += 1
                    if any(a.action == Action.BET for a in flop):
                        cbets += 1

        return round((cbets / opportunities * 100), 2) if opportunities > 0 else 0.0

    def calculate_all_stats(self, player_name: str) -> HUDStats:
        """Calculate all HUD stats for a player."""
        return HUDStats(
            vpip=self.calculate_vpip(player_name),
            pfr=self.calculate_pfr(player_name),
            af=self.calculate_aggression_factor(player_name),
            wtsd=self.calculate_wtsd(player_name),
            w_sd=self.calculate_w_sd(player_name),
            three_bet=self.calculate_three_bet(player_name),
            fold_to_3bet=self.calculate_fold_to_3bet(player_name),
            cbet=self.calculate_cbet(player_name)
        )


if __name__ == '__main__':
    calc = HUDStatsCalculator()

    # Example hand
    hand1 = [
        HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False),
        HandAction("Bob", Street.PREFLOP, Action.CALL, 10, True),
        HandAction("Alice", Street.FLOP, Action.BET, 15, False),
    ]
    calc.add_hand(hand1)

    stats = calc.calculate_all_stats("Alice")
    print(f"Alice stats: VPIP={stats.vpip}%, PFR={stats.pfr}%, AF={stats.af}")
