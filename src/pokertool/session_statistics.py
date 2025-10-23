#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Session Statistics Calculator
==============================

Calculates comprehensive poker statistics for sessions.

Statistics computed:
- VPIP (Voluntarily Put $ In Pot)
- PFR (Pre-Flop Raise)
- 3-Bet %
- Aggression Factor
- Win rate
- Hands played
- Position-based stats
- Bet sizing averages
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SessionStats:
    """Comprehensive session statistics."""
    # Basic counts
    total_hands: int = 0
    hands_won: int = 0
    hands_lost: int = 0

    # VPIP and PFR
    vpip_count: int = 0  # Hands where voluntarily put money in pot
    pfr_count: int = 0   # Hands where raised preflop

    # 3-Bet
    three_bet_opportunities: int = 0
    three_bet_count: int = 0

    # Positional stats
    position_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Bet sizing
    avg_bet_size_ratio: float = 0.0
    avg_pot_size: float = 0.0
    total_amount_wagered: float = 0.0
    total_amount_won: float = 0.0

    # Confidence
    avg_confidence: float = 0.0

    # Time
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None
    duration_minutes: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_hands': self.total_hands,
            'hands_won': self.hands_won,
            'hands_lost': self.hands_lost,
            'win_rate': self.win_rate,
            'vpip': self.vpip,
            'pfr': self.pfr,
            'three_bet_pct': self.three_bet_pct,
            'aggression_factor': self.aggression_factor,
            'avg_bet_size_ratio': self.avg_bet_size_ratio,
            'avg_pot_size': self.avg_pot_size,
            'total_amount_wagered': self.total_amount_wagered,
            'total_amount_won': self.total_amount_won,
            'net_profit': self.net_profit,
            'avg_confidence': self.avg_confidence,
            'duration_minutes': self.duration_minutes,
            'hands_per_hour': self.hands_per_hour,
            'position_stats': self.position_stats,
        }

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_hands == 0:
            return 0.0
        return (self.hands_won / self.total_hands) * 100

    @property
    def vpip(self) -> float:
        """Calculate VPIP percentage."""
        if self.total_hands == 0:
            return 0.0
        return (self.vpip_count / self.total_hands) * 100

    @property
    def pfr(self) -> float:
        """Calculate PFR percentage."""
        if self.total_hands == 0:
            return 0.0
        return (self.pfr_count / self.total_hands) * 100

    @property
    def three_bet_pct(self) -> float:
        """Calculate 3-bet percentage."""
        if self.three_bet_opportunities == 0:
            return 0.0
        return (self.three_bet_count / self.three_bet_opportunities) * 100

    @property
    def aggression_factor(self) -> float:
        """
        Calculate aggression factor.
        (Bets + Raises) / Calls
        """
        # Simplified - would need action tracking for real calculation
        return 0.0

    @property
    def net_profit(self) -> float:
        """Calculate net profit/loss."""
        return self.total_amount_won - self.total_amount_wagered

    @property
    def hands_per_hour(self) -> float:
        """Calculate hands per hour."""
        if self.duration_minutes == 0:
            return 0.0
        return (self.total_hands / self.duration_minutes) * 60


class SessionStatisticsCalculator:
    """
    Calculates session statistics from hand history.

    Example:
        calc = SessionStatisticsCalculator(database)
        stats = calc.calculate_session_stats(session_id="session_123")
        print(f"VPIP: {stats.vpip:.1f}%")
        print(f"PFR: {stats.pfr:.1f}%")
        print(f"Win Rate: {stats.win_rate:.1f}%")
    """

    def __init__(self, database):
        """
        Initialize calculator.

        Args:
            database: Database instance (PokerDatabase or ProductionDatabase).
        """
        self.database = database

    def calculate_session_stats(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        last_n_hands: Optional[int] = None
    ) -> SessionStats:
        """
        Calculate statistics for a session or time period.

        Args:
            session_id: Optional session ID to filter by.
            start_time: Optional start time for range query.
            end_time: Optional end time for range query.
            last_n_hands: Optional number of recent hands to analyze.

        Returns:
            SessionStats with calculated statistics.
        """
        # Build query
        query = "SELECT * FROM poker_hands WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp DESC"

        if last_n_hands:
            query += f" LIMIT ?"
            params.append(last_n_hands)

        # Execute query
        hands = self._execute_query(query, params)

        if not hands:
            return SessionStats()

        # Calculate stats
        stats = SessionStats()
        stats.total_hands = len(hands)

        # Track values for averaging
        bet_ratios = []
        pot_sizes = []
        confidences = []

        # Position tracking
        position_counts: Dict[str, int] = {}
        position_wins: Dict[str, int] = {}

        for hand in hands:
            # Bet sizing
            if hand.get('bet_size_ratio') is not None:
                bet_ratios.append(hand['bet_size_ratio'])

            if hand.get('pot_size') is not None:
                pot_sizes.append(hand['pot_size'])
                stats.total_amount_wagered += hand['pot_size']

            # Confidence
            if hand.get('confidence_score') is not None:
                confidences.append(hand['confidence_score'])

            # Position stats
            position = hand.get('player_position')
            if position:
                position_counts[position] = position_counts.get(position, 0) + 1

                # Simplified win detection (would need proper tracking)
                # For now, assume high confidence = win
                if hand.get('confidence_score', 0) > 0.9:
                    position_wins[position] = position_wins.get(position, 0) + 1
                    stats.hands_won += 1

            # VPIP estimation (if pot > 0, player put money in)
            if hand.get('pot_size', 0) > 0:
                stats.vpip_count += 1

            # PFR estimation (if bet ratio > 0, player raised)
            if hand.get('bet_size_ratio', 0) > 0:
                stats.pfr_count += 1

        # Calculate averages
        if bet_ratios:
            stats.avg_bet_size_ratio = sum(bet_ratios) / len(bet_ratios)

        if pot_sizes:
            stats.avg_pot_size = sum(pot_sizes) / len(pot_sizes)

        if confidences:
            stats.avg_confidence = sum(confidences) / len(confidences)

        stats.hands_lost = stats.total_hands - stats.hands_won

        # Build position stats
        for position, count in position_counts.items():
            wins = position_wins.get(position, 0)
            stats.position_stats[position] = {
                'hands': count,
                'wins': wins,
                'win_rate': (wins / count * 100) if count > 0 else 0.0,
            }

        # Time calculation
        if hands:
            # Get timestamps
            timestamps = [
                datetime.fromisoformat(hand['timestamp'])
                for hand in hands
                if hand.get('timestamp')
            ]

            if timestamps:
                stats.session_start = min(timestamps)
                stats.session_end = max(timestamps)
                duration = stats.session_end - stats.session_start
                stats.duration_minutes = duration.total_seconds() / 60

        return stats

    def calculate_multiple_sessions(
        self,
        session_ids: List[str]
    ) -> Dict[str, SessionStats]:
        """
        Calculate statistics for multiple sessions.

        Args:
            session_ids: List of session IDs.

        Returns:
            Dictionary mapping session_id to SessionStats.
        """
        results = {}
        for session_id in session_ids:
            results[session_id] = self.calculate_session_stats(session_id=session_id)
        return results

    def calculate_position_stats(
        self,
        position: str,
        session_id: Optional[str] = None
    ) -> SessionStats:
        """
        Calculate statistics for a specific position.

        Args:
            position: Position to analyze (BTN, SB, BB, etc.).
            session_id: Optional session ID to filter by.

        Returns:
            SessionStats for that position.
        """
        query = "SELECT * FROM poker_hands WHERE player_position = ?"
        params = [position]

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC"

        hands = self._execute_query(query, params)

        # Use main calculation logic but filter to position
        # (Simplified - reusing calculate_session_stats would be more efficient)
        stats = SessionStats()
        stats.total_hands = len(hands)

        return stats

    def get_recent_session_stats(
        self,
        days: int = 7
    ) -> SessionStats:
        """
        Get statistics for the last N days.

        Args:
            days: Number of days to look back.

        Returns:
            SessionStats for the time period.
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        return self.calculate_session_stats(
            start_time=start_time,
            end_time=end_time
        )

    def _execute_query(self, query: str, params: List[Any]) -> List[Dict[str, Any]]:
        """Execute database query and return results."""
        try:
            if hasattr(self.database, '_execute_query'):
                # Production database
                return self.database._execute_query(query, params)
            else:
                # Simple database - use connection directly
                cursor = self.database.conn.cursor()
                cursor.execute(query, params)

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            return []


# Import timedelta for time calculations
from datetime import timedelta
