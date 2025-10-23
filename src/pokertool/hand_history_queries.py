#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hand History Query System
==========================

Provides comprehensive querying and filtering for hand history database.
Supports complex filters by:
- Position (BTN, SB, BB, etc.)
- Player action patterns
- Board texture (wet/dry, coordinated/rainbow, paired)
- Bet sizing (ratios, pot odds)
- Confidence scores
- Time ranges
- Session IDs

Features:
- Fluent query builder API
- Optimized SQL generation
- Type-safe filters
- Result aggregation
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class Position(str, Enum):
    """Poker table positions."""
    BTN = "BTN"
    SB = "SB"
    BB = "BB"
    UTG = "UTG"
    UTG_1 = "UTG+1"
    UTG_2 = "UTG+2"
    MP = "MP"
    MP_1 = "MP+1"
    MP_2 = "MP+2"
    HJ = "HJ"
    CO = "CO"


class BoardTexture(str, Enum):
    """Board texture classifications."""
    WET = "wet"              # Many draws possible
    DRY = "dry"              # Few draws possible
    COORDINATED = "coordinated"  # Cards work together
    RAINBOW = "rainbow"      # All different suits
    MONOTONE = "monotone"    # All same suit
    TWO_TONE = "two_tone"    # Two of same suit
    PAIRED = "paired"        # Contains a pair
    UNPAIRED = "unpaired"    # No pairs


@dataclass
class HandFilter:
    """
    Filter criteria for hand history queries.

    All filters are AND-ed together. Use None to skip a filter.
    """
    # Position filters
    positions: Optional[List[Position]] = None

    # Board texture filters
    board_textures: Optional[List[BoardTexture]] = None

    # Bet sizing filters
    min_bet_ratio: Optional[float] = None
    max_bet_ratio: Optional[float] = None
    min_pot_size: Optional[float] = None
    max_pot_size: Optional[float] = None

    # Confidence filters
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None

    # Time filters
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    last_n_days: Optional[int] = None

    # Session filter
    session_ids: Optional[List[str]] = None

    # Card filters
    hero_hand_contains: Optional[str] = None  # e.g., "AA", "AK"
    board_contains: Optional[str] = None      # e.g., "A", "flush"

    # Result limit
    limit: int = 100
    offset: int = 0


@dataclass
class HandQueryResult:
    """Result of a hand history query."""
    hands: List[Dict[str, Any]]
    total_count: int
    filters_applied: HandFilter


class HandHistoryQueryBuilder:
    """
    Fluent query builder for hand history.

    Example:
        results = (HandHistoryQueryBuilder(db)
                   .in_positions([Position.BTN, Position.CO])
                   .with_min_pot_size(100.0)
                   .with_min_confidence(0.9)
                   .last_n_days(7)
                   .limit(50)
                   .execute())
    """

    def __init__(self, database):
        """
        Initialize query builder.

        Args:
            database: PokerDatabase or ProductionDatabase instance.
        """
        self.database = database
        self.filter = HandFilter()

    # Position filters

    def in_positions(self, positions: List[Position]) -> HandHistoryQueryBuilder:
        """Filter by positions."""
        self.filter.positions = positions
        return self

    def in_position(self, position: Position) -> HandHistoryQueryBuilder:
        """Filter by single position."""
        self.filter.positions = [position]
        return self

    # Board texture filters

    def with_board_textures(self, textures: List[BoardTexture]) -> HandHistoryQueryBuilder:
        """Filter by board textures."""
        self.filter.board_textures = textures
        return self

    def with_board_texture(self, texture: BoardTexture) -> HandHistoryQueryBuilder:
        """Filter by single board texture."""
        self.filter.board_textures = [texture]
        return self

    # Bet sizing filters

    def with_bet_ratio_range(self, min_ratio: Optional[float] = None,
                            max_ratio: Optional[float] = None) -> HandHistoryQueryBuilder:
        """Filter by bet sizing ratio range."""
        self.filter.min_bet_ratio = min_ratio
        self.filter.max_bet_ratio = max_ratio
        return self

    def with_min_bet_ratio(self, ratio: float) -> HandHistoryQueryBuilder:
        """Filter by minimum bet ratio."""
        self.filter.min_bet_ratio = ratio
        return self

    def with_max_bet_ratio(self, ratio: float) -> HandHistoryQueryBuilder:
        """Filter by maximum bet ratio."""
        self.filter.max_bet_ratio = ratio
        return self

    def with_pot_size_range(self, min_pot: Optional[float] = None,
                           max_pot: Optional[float] = None) -> HandHistoryQueryBuilder:
        """Filter by pot size range."""
        self.filter.min_pot_size = min_pot
        self.filter.max_pot_size = max_pot
        return self

    def with_min_pot_size(self, size: float) -> HandHistoryQueryBuilder:
        """Filter by minimum pot size."""
        self.filter.min_pot_size = size
        return self

    def with_max_pot_size(self, size: float) -> HandHistoryQueryBuilder:
        """Filter by maximum pot size."""
        self.filter.max_pot_size = size
        return self

    # Confidence filters

    def with_confidence_range(self, min_conf: Optional[float] = None,
                             max_conf: Optional[float] = None) -> HandHistoryQueryBuilder:
        """Filter by confidence range."""
        self.filter.min_confidence = min_conf
        self.filter.max_confidence = max_conf
        return self

    def with_min_confidence(self, confidence: float) -> HandHistoryQueryBuilder:
        """Filter by minimum confidence."""
        self.filter.min_confidence = confidence
        return self

    def with_max_confidence(self, confidence: float) -> HandHistoryQueryBuilder:
        """Filter by maximum confidence."""
        self.filter.max_confidence = confidence
        return self

    # Time filters

    def in_time_range(self, start: datetime, end: datetime) -> HandHistoryQueryBuilder:
        """Filter by time range."""
        self.filter.start_time = start
        self.filter.end_time = end
        return self

    def since(self, start_time: datetime) -> HandHistoryQueryBuilder:
        """Filter since a specific time."""
        self.filter.start_time = start_time
        return self

    def until(self, end_time: datetime) -> HandHistoryQueryBuilder:
        """Filter until a specific time."""
        self.filter.end_time = end_time
        return self

    def last_n_days(self, days: int) -> HandHistoryQueryBuilder:
        """Filter to last N days."""
        self.filter.last_n_days = days
        return self

    # Session filters

    def in_sessions(self, session_ids: List[str]) -> HandHistoryQueryBuilder:
        """Filter by session IDs."""
        self.filter.session_ids = session_ids
        return self

    def in_session(self, session_id: str) -> HandHistoryQueryBuilder:
        """Filter by single session ID."""
        self.filter.session_ids = [session_id]
        return self

    # Card filters

    def with_hero_hand(self, cards: str) -> HandHistoryQueryBuilder:
        """Filter by hero hand containing specific cards (e.g., 'AA', 'AK')."""
        self.filter.hero_hand_contains = cards
        return self

    def with_board_card(self, card: str) -> HandHistoryQueryBuilder:
        """Filter by board containing specific card (e.g., 'A', 'K')."""
        self.filter.board_contains = card
        return self

    # Pagination

    def limit(self, limit: int) -> HandHistoryQueryBuilder:
        """Set result limit."""
        self.filter.limit = limit
        return self

    def offset(self, offset: int) -> HandHistoryQueryBuilder:
        """Set result offset."""
        self.filter.offset = offset
        return self

    def page(self, page_number: int, page_size: int = 50) -> HandHistoryQueryBuilder:
        """Set page number and size."""
        self.filter.offset = (page_number - 1) * page_size
        self.filter.limit = page_size
        return self

    # Execution

    def execute(self) -> HandQueryResult:
        """
        Execute the query and return results.

        Returns:
            HandQueryResult with filtered hands and metadata.
        """
        # Build SQL query
        query, params = self._build_query()

        # Execute query
        try:
            if hasattr(self.database, '_execute_query'):
                # Production database
                hands = self.database._execute_query(query, params)
            else:
                # Simple database - use connection directly
                cursor = self.database.conn.cursor()
                cursor.execute(query, params)

                columns = [desc[0] for desc in cursor.description]
                hands = [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to execute hand history query: {e}")
            hands = []

        # Get total count
        count_query, count_params = self._build_count_query()
        try:
            if hasattr(self.database, '_execute_query'):
                count_result = self.database._execute_query(count_query, count_params)
                total_count = count_result[0]['count'] if count_result else 0
            else:
                cursor = self.database.conn.cursor()
                cursor.execute(count_query, count_params)
                total_count = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get count: {e}")
            total_count = len(hands)

        return HandQueryResult(
            hands=hands,
            total_count=total_count,
            filters_applied=self.filter
        )

    def count(self) -> int:
        """
        Get count of matching hands without fetching full results.

        Returns:
            Number of matching hands.
        """
        result = self.execute()
        return result.total_count

    def _build_query(self) -> Tuple[str, List[Any]]:
        """Build SQL query from filter criteria."""
        # Base query
        query = """
            SELECT
                id,
                hand_text,
                board_text,
                analysis_result,
                timestamp,
                session_id,
                confidence_score,
                bet_size_ratio,
                pot_size,
                player_position
            FROM poker_hands
            WHERE 1=1
        """
        params = []

        # Position filter
        if self.filter.positions:
            placeholders = ','.join(['?' for _ in self.filter.positions])
            query += f" AND player_position IN ({placeholders})"
            params.extend([p.value for p in self.filter.positions])

        # Bet sizing filters
        if self.filter.min_bet_ratio is not None:
            query += " AND bet_size_ratio >= ?"
            params.append(self.filter.min_bet_ratio)

        if self.filter.max_bet_ratio is not None:
            query += " AND bet_size_ratio <= ?"
            params.append(self.filter.max_bet_ratio)

        if self.filter.min_pot_size is not None:
            query += " AND pot_size >= ?"
            params.append(self.filter.min_pot_size)

        if self.filter.max_pot_size is not None:
            query += " AND pot_size <= ?"
            params.append(self.filter.max_pot_size)

        # Confidence filters
        if self.filter.min_confidence is not None:
            query += " AND confidence_score >= ?"
            params.append(self.filter.min_confidence)

        if self.filter.max_confidence is not None:
            query += " AND confidence_score <= ?"
            params.append(self.filter.max_confidence)

        # Time filters
        if self.filter.last_n_days:
            query += " AND timestamp >= datetime('now', ?)"
            params.append(f'-{self.filter.last_n_days} days')
        elif self.filter.start_time:
            query += " AND timestamp >= ?"
            params.append(self.filter.start_time.isoformat())

        if self.filter.end_time:
            query += " AND timestamp <= ?"
            params.append(self.filter.end_time.isoformat())

        # Session filters
        if self.filter.session_ids:
            placeholders = ','.join(['?' for _ in self.filter.session_ids])
            query += f" AND session_id IN ({placeholders})"
            params.extend(self.filter.session_ids)

        # Card filters
        if self.filter.hero_hand_contains:
            query += " AND hand_text LIKE ?"
            params.append(f'%{self.filter.hero_hand_contains}%')

        if self.filter.board_contains:
            query += " AND board_text LIKE ?"
            params.append(f'%{self.filter.board_contains}%')

        # Order and pagination
        query += " ORDER BY timestamp DESC"
        query += f" LIMIT ? OFFSET ?"
        params.extend([self.filter.limit, self.filter.offset])

        return query, params

    def _build_count_query(self) -> Tuple[str, List[Any]]:
        """Build count query (same filters, just COUNT instead of SELECT *)."""
        query = "SELECT COUNT(*) as count FROM poker_hands WHERE 1=1"
        params = []

        # Apply same filters (excluding LIMIT/OFFSET)
        if self.filter.positions:
            placeholders = ','.join(['?' for _ in self.filter.positions])
            query += f" AND player_position IN ({placeholders})"
            params.extend([p.value for p in self.filter.positions])

        if self.filter.min_bet_ratio is not None:
            query += " AND bet_size_ratio >= ?"
            params.append(self.filter.min_bet_ratio)

        if self.filter.max_bet_ratio is not None:
            query += " AND bet_size_ratio <= ?"
            params.append(self.filter.max_bet_ratio)

        if self.filter.min_pot_size is not None:
            query += " AND pot_size >= ?"
            params.append(self.filter.min_pot_size)

        if self.filter.max_pot_size is not None:
            query += " AND pot_size <= ?"
            params.append(self.filter.max_pot_size)

        if self.filter.min_confidence is not None:
            query += " AND confidence_score >= ?"
            params.append(self.filter.min_confidence)

        if self.filter.max_confidence is not None:
            query += " AND confidence_score <= ?"
            params.append(self.filter.max_confidence)

        if self.filter.last_n_days:
            query += " AND timestamp >= datetime('now', ?)"
            params.append(f'-{self.filter.last_n_days} days')
        elif self.filter.start_time:
            query += " AND timestamp >= ?"
            params.append(self.filter.start_time.isoformat())

        if self.filter.end_time:
            query += " AND timestamp <= ?"
            params.append(self.filter.end_time.isoformat())

        if self.filter.session_ids:
            placeholders = ','.join(['?' for _ in self.filter.session_ids])
            query += f" AND session_id IN ({placeholders})"
            params.extend(self.filter.session_ids)

        if self.filter.hero_hand_contains:
            query += " AND hand_text LIKE ?"
            params.append(f'%{self.filter.hero_hand_contains}%')

        if self.filter.board_contains:
            query += " AND board_text LIKE ?"
            params.append(f'%{self.filter.board_contains}%')

        return query, params
