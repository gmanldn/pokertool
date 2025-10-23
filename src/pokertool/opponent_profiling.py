#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Opponent Profiling System
==========================

Tracks and analyzes opponent playing styles and tendencies.

Profiles include:
- VPIP by position
- PFR by position
- 3-bet percentage
- Aggression frequency
- Bet sizing patterns
- Fold to 3-bet %
- Continuation bet %
- Playing style classification (tight/loose, passive/aggressive)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class PlayerStyle(str, Enum):
    """Player style classifications."""
    TAG = "tight_aggressive"  # Tight-Aggressive (VPIP <25%, PFR high)
    LAG = "loose_aggressive"  # Loose-Aggressive (VPIP >30%, PFR high)
    TAP = "tight_passive"     # Tight-Passive (VPIP <25%, PFR low)
    LAP = "loose_passive"     # Loose-Passive (VPIP >30%, PFR low)
    ROCK = "rock"             # Very tight (VPIP <15%)
    MANIAC = "maniac"         # Very loose aggressive (VPIP >50%, PFR >40%)
    FISH = "fish"             # Loose passive calling station
    UNKNOWN = "unknown"       # Not enough data


@dataclass
class OpponentProfile:
    """
    Comprehensive opponent profile.

    Tracks tendencies across different positions and situations.
    """
    opponent_id: str  # Opponent identifier
    hands_observed: int = 0

    # Overall stats
    vpip: float = 0.0  # Voluntarily Put $ In Pot %
    pfr: float = 0.0   # Pre-Flop Raise %
    three_bet_pct: float = 0.0
    fold_to_three_bet_pct: float = 0.0
    cbet_pct: float = 0.0  # Continuation bet %

    # Aggression
    aggression_frequency: float = 0.0  # % of time betting/raising vs calling
    avg_bet_size_ratio: float = 0.0

    # Position-specific stats
    vpip_by_position: Dict[str, float] = field(default_factory=dict)
    pfr_by_position: Dict[str, float] = field(default_factory=dict)
    hands_by_position: Dict[str, int] = field(default_factory=dict)

    # Win rate
    win_rate: float = 0.0
    net_profit: float = 0.0

    # Style classification
    player_style: PlayerStyle = PlayerStyle.UNKNOWN

    # Tendencies
    is_tight: bool = False
    is_loose: bool = False
    is_aggressive: bool = False
    is_passive: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'opponent_id': self.opponent_id,
            'hands_observed': self.hands_observed,
            'vpip': self.vpip,
            'pfr': self.pfr,
            'three_bet_pct': self.three_bet_pct,
            'fold_to_three_bet_pct': self.fold_to_three_bet_pct,
            'cbet_pct': self.cbet_pct,
            'aggression_frequency': self.aggression_frequency,
            'avg_bet_size_ratio': self.avg_bet_size_ratio,
            'vpip_by_position': self.vpip_by_position,
            'pfr_by_position': self.pfr_by_position,
            'hands_by_position': self.hands_by_position,
            'win_rate': self.win_rate,
            'net_profit': self.net_profit,
            'player_style': self.player_style.value,
            'is_tight': self.is_tight,
            'is_loose': self.is_loose,
            'is_aggressive': self.is_aggressive,
            'is_passive': self.is_passive,
        }

    def classify_style(self):
        """Classify player style based on statistics."""
        if self.hands_observed < 50:
            self.player_style = PlayerStyle.UNKNOWN
            return

        # Determine tight/loose
        if self.vpip < 15:
            self.is_tight = True
            self.player_style = PlayerStyle.ROCK
        elif self.vpip < 25:
            self.is_tight = True
        elif self.vpip > 30:
            self.is_loose = True
        elif self.vpip > 50:
            self.is_loose = True

        # Determine aggressive/passive
        if self.pfr > 15:
            self.is_aggressive = True
        elif self.pfr < 8:
            self.is_passive = True

        # Classify combined style
        if self.vpip < 25 and self.pfr > 15:
            self.player_style = PlayerStyle.TAG
        elif self.vpip > 30 and self.pfr > 20:
            self.player_style = PlayerStyle.LAG
        elif self.vpip < 25 and self.pfr < 8:
            self.player_style = PlayerStyle.TAP
        elif self.vpip > 30 and self.pfr < 10:
            self.player_style = PlayerStyle.LAP
            if self.vpip > 45:
                self.player_style = PlayerStyle.FISH
        elif self.vpip > 50 and self.pfr > 40:
            self.player_style = PlayerStyle.MANIAC


class OpponentProfiler:
    """
    Builds and maintains opponent profiles.

    Example:
        profiler = OpponentProfiler(database)
        profile = profiler.get_opponent_profile("villain_123")
        print(f"Style: {profile.player_style}")
        print(f"VPIP: {profile.vpip:.1f}%")
        print(f"PFR: {profile.pfr:.1f}%")
    """

    def __init__(self, database):
        """
        Initialize profiler.

        Args:
            database: Database instance.
        """
        self.database = database

    def get_opponent_profile(
        self,
        opponent_id: str,
        min_hands: int = 20
    ) -> OpponentProfile:
        """
        Get profile for a specific opponent.

        Args:
            opponent_id: Opponent identifier.
            min_hands: Minimum hands to include in analysis.

        Returns:
            OpponentProfile with statistics.
        """
        profile = OpponentProfile(opponent_id=opponent_id)

        # Query opponent hands
        # Note: This assumes opponent tracking in metadata
        query = """
            SELECT * FROM poker_hands
            WHERE metadata LIKE ?
            ORDER BY timestamp DESC
        """
        params = [f'%{opponent_id}%']

        hands = self._execute_query(query, params)

        if not hands or len(hands) < min_hands:
            return profile

        profile.hands_observed = len(hands)

        # Track statistics
        vpip_count = 0
        pfr_count = 0
        three_bet_count = 0
        three_bet_opportunities = 0
        bet_ratios = []
        position_hands: Dict[str, int] = {}
        position_vpip: Dict[str, int] = {}
        position_pfr: Dict[str, int] = {}
        wins = 0
        total_wagered = 0.0
        total_won = 0.0

        for hand in hands:
            position = hand.get('player_position')
            if position:
                position_hands[position] = position_hands.get(position, 0) + 1

            # VPIP (pot > 0 means voluntarily put money in)
            if hand.get('pot_size', 0) > 0:
                vpip_count += 1
                if position:
                    position_vpip[position] = position_vpip.get(position, 0) + 1

            # PFR (bet ratio > 0 means raised)
            if hand.get('bet_size_ratio', 0) > 0:
                pfr_count += 1
                if position:
                    position_pfr[position] = position_pfr.get(position, 0) + 1

            # Bet sizing
            if hand.get('bet_size_ratio') is not None:
                bet_ratios.append(hand['bet_size_ratio'])

            # Win tracking (simplified - high confidence = win)
            if hand.get('confidence_score', 0) > 0.9:
                wins += 1

            # Profit tracking
            if hand.get('pot_size'):
                total_wagered += hand['pot_size']
                if hand.get('confidence_score', 0) > 0.9:
                    total_won += hand['pot_size']

        # Calculate percentages
        if profile.hands_observed > 0:
            profile.vpip = (vpip_count / profile.hands_observed) * 100
            profile.pfr = (pfr_count / profile.hands_observed) * 100
            profile.win_rate = (wins / profile.hands_observed) * 100

        if bet_ratios:
            profile.avg_bet_size_ratio = sum(bet_ratios) / len(bet_ratios)

        profile.net_profit = total_won - total_wagered

        # Calculate position-specific stats
        for position, count in position_hands.items():
            if count > 0:
                vpip_for_pos = position_vpip.get(position, 0)
                pfr_for_pos = position_pfr.get(position, 0)

                profile.hands_by_position[position] = count
                profile.vpip_by_position[position] = (vpip_for_pos / count) * 100
                profile.pfr_by_position[position] = (pfr_for_pos / count) * 100

        # Classify style
        profile.classify_style()

        return profile

    def get_all_opponent_profiles(
        self,
        min_hands: int = 20
    ) -> List[OpponentProfile]:
        """
        Get profiles for all observed opponents.

        Args:
            min_hands: Minimum hands required to include opponent.

        Returns:
            List of OpponentProfile objects.
        """
        # Get all unique opponent IDs from metadata
        # This is simplified - real implementation would need proper opponent tracking
        query = "SELECT DISTINCT metadata FROM poker_hands WHERE metadata IS NOT NULL"
        results = self._execute_query(query, [])

        # Extract opponent IDs (simplified)
        opponent_ids = set()
        for row in results:
            metadata = row.get('metadata', '')
            if metadata and 'opponent' in metadata.lower():
                # Extract opponent ID from metadata
                # This is simplified - real implementation needs proper parsing
                opponent_ids.add(metadata)

        # Build profiles
        profiles = []
        for opponent_id in opponent_ids:
            profile = self.get_opponent_profile(opponent_id, min_hands=min_hands)
            if profile.hands_observed >= min_hands:
                profiles.append(profile)

        # Sort by hands observed (most data first)
        profiles.sort(key=lambda p: p.hands_observed, reverse=True)

        return profiles

    def compare_opponents(
        self,
        opponent_ids: List[str]
    ) -> Dict[str, OpponentProfile]:
        """
        Compare multiple opponents side-by-side.

        Args:
            opponent_ids: List of opponent IDs to compare.

        Returns:
            Dictionary mapping opponent_id to OpponentProfile.
        """
        profiles = {}
        for opponent_id in opponent_ids:
            profiles[opponent_id] = self.get_opponent_profile(opponent_id)
        return profiles

    def get_opponents_by_style(
        self,
        style: PlayerStyle,
        min_hands: int = 50
    ) -> List[OpponentProfile]:
        """
        Find all opponents matching a specific style.

        Args:
            style: PlayerStyle to filter by.
            min_hands: Minimum hands required.

        Returns:
            List of matching OpponentProfile objects.
        """
        all_profiles = self.get_all_opponent_profiles(min_hands=min_hands)
        return [p for p in all_profiles if p.player_style == style]

    def get_toughest_opponents(
        self,
        limit: int = 10,
        min_hands: int = 50
    ) -> List[OpponentProfile]:
        """
        Get toughest opponents (highest win rate + TAG/LAG style).

        Args:
            limit: Maximum number to return.
            min_hands: Minimum hands required.

        Returns:
            List of toughest OpponentProfile objects.
        """
        all_profiles = self.get_all_opponent_profiles(min_hands=min_hands)

        # Filter for skilled styles
        skilled_profiles = [
            p for p in all_profiles
            if p.player_style in [PlayerStyle.TAG, PlayerStyle.LAG]
        ]

        # Sort by win rate
        skilled_profiles.sort(key=lambda p: p.win_rate, reverse=True)

        return skilled_profiles[:limit]

    def get_weakest_opponents(
        self,
        limit: int = 10,
        min_hands: int = 50
    ) -> List[OpponentProfile]:
        """
        Get weakest opponents (calling stations, fish).

        Args:
            limit: Maximum number to return.
            min_hands: Minimum hands required.

        Returns:
            List of weakest OpponentProfile objects.
        """
        all_profiles = self.get_all_opponent_profiles(min_hands=min_hands)

        # Filter for weak styles
        weak_profiles = [
            p for p in all_profiles
            if p.player_style in [PlayerStyle.FISH, PlayerStyle.LAP, PlayerStyle.TAP]
        ]

        # Sort by lowest win rate (easiest to exploit)
        weak_profiles.sort(key=lambda p: p.win_rate)

        return weak_profiles[:limit]

    def _execute_query(self, query: str, params: List[Any]) -> List[Dict[str, Any]]:
        """Execute database query and return results."""
        try:
            if hasattr(self.database, '_execute_query'):
                return self.database._execute_query(query, params)
            else:
                cursor = self.database.conn.cursor()
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            return []
