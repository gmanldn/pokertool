#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hand History Database for PokerTool
====================================

Captures and stores complete hand histories including:
- Players and positions
- Actions and betting
- Board cards and hole cards
- Results and winners
- Pot sizes and stack sizes

Version: 1.0.0
"""

from __future__ import annotations

import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class GameStage(Enum):
    """Stages of a poker hand."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class ActionType(Enum):
    """Types of player actions."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass
class PlayerInfo:
    """Information about a player in a hand."""
    seat_number: int
    player_name: str
    starting_stack: float
    ending_stack: float = 0.0
    position: str = ""
    is_hero: bool = False
    cards: List[str] = field(default_factory=list)  # ["As", "Kh"]
    won_amount: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerInfo":
        return cls(**data)


@dataclass
class PlayerAction:
    """A single action by a player."""
    player_name: str
    action_type: ActionType
    amount: float
    stage: GameStage
    timestamp: str  # ISO format

    def to_dict(self) -> Dict[str, Any]:
        return {
            'player_name': self.player_name,
            'action_type': self.action_type.value,
            'amount': self.amount,
            'stage': self.stage.value,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerAction":
        return cls(
            player_name=data['player_name'],
            action_type=ActionType(data['action_type']),
            amount=data['amount'],
            stage=GameStage(data['stage']),
            timestamp=data['timestamp']
        )


@dataclass
class HandHistory:
    """Complete history of a single poker hand."""
    hand_id: str  # Unique identifier
    timestamp: str  # ISO format
    table_name: str
    site: str
    small_blind: float
    big_blind: float

    # Players
    players: List[PlayerInfo] = field(default_factory=list)
    hero_name: Optional[str] = None

    # Cards
    hero_cards: List[str] = field(default_factory=list)  # ["As", "Kh"]
    board_cards: List[str] = field(default_factory=list)  # ["2h", "7d", "Qc", "3s", "9h"]

    # Actions
    actions: List[PlayerAction] = field(default_factory=list)

    # Results
    pot_size: float = 0.0
    winners: List[str] = field(default_factory=list)  # Player names
    hero_result: str = "unknown"  # "won", "lost", "pushed"
    hero_net: float = 0.0  # Net win/loss for hero

    # Metadata
    final_stage: GameStage = GameStage.PREFLOP
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'hand_id': self.hand_id,
            'timestamp': self.timestamp,
            'table_name': self.table_name,
            'site': self.site,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'players': [p.to_dict() for p in self.players],
            'hero_name': self.hero_name,
            'hero_cards': self.hero_cards,
            'board_cards': self.board_cards,
            'actions': [a.to_dict() for a in self.actions],
            'pot_size': self.pot_size,
            'winners': self.winners,
            'hero_result': self.hero_result,
            'hero_net': self.hero_net,
            'final_stage': self.final_stage.value,
            'duration_seconds': self.duration_seconds
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HandHistory":
        """Create from dictionary."""
        return cls(
            hand_id=data['hand_id'],
            timestamp=data['timestamp'],
            table_name=data['table_name'],
            site=data['site'],
            small_blind=data['small_blind'],
            big_blind=data['big_blind'],
            players=[PlayerInfo.from_dict(p) for p in data['players']],
            hero_name=data.get('hero_name'),
            hero_cards=data.get('hero_cards', []),
            board_cards=data.get('board_cards', []),
            actions=[PlayerAction.from_dict(a) for a in data.get('actions', [])],
            pot_size=data.get('pot_size', 0.0),
            winners=data.get('winners', []),
            hero_result=data.get('hero_result', 'unknown'),
            hero_net=data.get('hero_net', 0.0),
            final_stage=GameStage(data.get('final_stage', 'preflop')),
            duration_seconds=data.get('duration_seconds', 0.0)
        )


class HandHistoryDatabase:
    """SQLite database for storing hand histories."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize hand history database.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            root = Path(__file__).resolve().parents[2]
            db_path = root / "hand_history.db"

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hands (
                    hand_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    site TEXT NOT NULL,
                    small_blind REAL NOT NULL,
                    big_blind REAL NOT NULL,
                    pot_size REAL DEFAULT 0,
                    hero_name TEXT,
                    hero_result TEXT,
                    hero_net REAL DEFAULT 0,
                    final_stage TEXT,
                    duration_seconds REAL DEFAULT 0,
                    hand_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Index for faster queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON hands(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hero_name ON hands(hero_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_table_name ON hands(table_name)")

            conn.commit()
            logger.info(f"Hand history database initialized at {self.db_path}")

    def save_hand(self, hand: HandHistory) -> bool:
        """
        Save a hand history to the database.

        Args:
            hand: HandHistory object to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            hand_data = json.dumps(hand.to_dict())

            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO hands (
                        hand_id, timestamp, table_name, site, small_blind, big_blind,
                        pot_size, hero_name, hero_result, hero_net, final_stage,
                        duration_seconds, hand_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hand.hand_id, hand.timestamp, hand.table_name, hand.site,
                    hand.small_blind, hand.big_blind, hand.pot_size, hand.hero_name,
                    hand.hero_result, hand.hero_net, hand.final_stage.value,
                    hand.duration_seconds, hand_data
                ))
                conn.commit()

            logger.info(f"Saved hand {hand.hand_id} to database")
            return True

        except Exception as e:
            logger.error(f"Failed to save hand {hand.hand_id}: {e}")
            return False

    def get_hand(self, hand_id: str) -> Optional[HandHistory]:
        """
        Retrieve a hand by ID.

        Args:
            hand_id: Hand ID to retrieve

        Returns:
            HandHistory object or None if not found
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "SELECT hand_data FROM hands WHERE hand_id = ?",
                    (hand_id,)
                )
                row = cursor.fetchone()

                if row:
                    data = json.loads(row[0])
                    return HandHistory.from_dict(data)

        except Exception as e:
            logger.error(f"Failed to retrieve hand {hand_id}: {e}")

        return None

    def get_recent_hands(self, limit: int = 100, hero_name: Optional[str] = None) -> List[HandHistory]:
        """
        Get recent hands from the database.

        Args:
            limit: Maximum number of hands to return
            hero_name: Filter by hero name (optional)

        Returns:
            List of HandHistory objects
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                if hero_name:
                    cursor = conn.execute("""
                        SELECT hand_data FROM hands
                        WHERE hero_name = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (hero_name, limit))
                else:
                    cursor = conn.execute("""
                        SELECT hand_data FROM hands
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))

                hands = []
                for row in cursor.fetchall():
                    data = json.loads(row[0])
                    hands.append(HandHistory.from_dict(data))

                return hands

        except Exception as e:
            logger.error(f"Failed to retrieve recent hands: {e}")
            return []

    def get_statistics(self, hero_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about recorded hands.

        Args:
            hero_name: Filter by hero name (optional)

        Returns:
            Dictionary of statistics
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                if hero_name:
                    cursor = conn.execute("""
                        SELECT
                            COUNT(*) as total_hands,
                            SUM(CASE WHEN hero_result = 'won' THEN 1 ELSE 0 END) as hands_won,
                            SUM(CASE WHEN hero_result = 'lost' THEN 1 ELSE 0 END) as hands_lost,
                            SUM(hero_net) as total_net,
                            AVG(pot_size) as avg_pot_size,
                            MAX(pot_size) as max_pot_size
                        FROM hands
                        WHERE hero_name = ?
                    """, (hero_name,))
                else:
                    cursor = conn.execute("""
                        SELECT
                            COUNT(*) as total_hands,
                            AVG(pot_size) as avg_pot_size,
                            MAX(pot_size) as max_pot_size
                        FROM hands
                    """)

                row = cursor.fetchone()
                if row and hero_name:
                    return {
                        'total_hands': row[0] or 0,
                        'hands_won': row[1] or 0,
                        'hands_lost': row[2] or 0,
                        'total_net': row[3] or 0.0,
                        'avg_pot_size': row[4] or 0.0,
                        'max_pot_size': row[5] or 0.0,
                        'win_rate': (row[1] / row[0] * 100) if row[0] else 0.0
                    }
                elif row:
                    return {
                        'total_hands': row[0] or 0,
                        'avg_pot_size': row[1] or 0.0,
                        'max_pot_size': row[2] or 0.0
                    }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")

        return {}

    def delete_hand(self, hand_id: str) -> bool:
        """Delete a hand from the database."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM hands WHERE hand_id = ?", (hand_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete hand {hand_id}: {e}")
            return False

    def clear_all_hands(self) -> bool:
        """Clear all hands from the database (use with caution!)."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM hands")
                conn.commit()
            logger.warning("Cleared all hands from database")
            return True
        except Exception as e:
            logger.error(f"Failed to clear hands: {e}")
            return False


# Global database instance
_hand_db: Optional[HandHistoryDatabase] = None


def get_hand_history_db() -> HandHistoryDatabase:
    """Get the global hand history database instance."""
    global _hand_db
    if _hand_db is None:
        _hand_db = HandHistoryDatabase()
    return _hand_db


if __name__ == '__main__':
    # Test the hand history database
    print("Testing Hand History Database...")

    db = HandHistoryDatabase(Path("test_hand_history.db"))

    # Create a test hand
    test_hand = HandHistory(
        hand_id="test_hand_001",
        timestamp=datetime.now().isoformat(),
        table_name="Test Table 1",
        site="BETFAIR",
        small_blind=0.05,
        big_blind=0.10,
        players=[
            PlayerInfo(1, "HeroPlayer", 10.00, 12.00, "BTN", True, ["As", "Kh"], 2.50),
            PlayerInfo(2, "Villain1", 10.00, 9.50, "SB", False),
        ],
        hero_name="HeroPlayer",
        hero_cards=["As", "Kh"],
        board_cards=["2h", "7d", "Qc"],
        pot_size=2.50,
        winners=["HeroPlayer"],
        hero_result="won",
        hero_net=2.00,
        final_stage=GameStage.FLOP
    )

    # Save hand
    db.save_hand(test_hand)

    # Retrieve hand
    retrieved = db.get_hand("test_hand_001")
    assert retrieved is not None
    assert retrieved.hand_id == "test_hand_001"

    # Get statistics
    stats = db.get_statistics("HeroPlayer")
    print(f"Statistics: {stats}")

    # Cleanup
    Path("test_hand_history.db").unlink(missing_ok=True)

    print("✓ All tests passed")
