"""
Migration: Initialize poker_hands table

Creates the poker_hands table if it doesn't exist.
Supports both SQLite and PostgreSQL.
"""

import sqlite3
from typing import Optional


def migrate_sqlite(db_path: str) -> None:
    """Initialize poker_hands table for SQLite."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='poker_hands'"
    )
    if cursor.fetchone():
        return  # Table already exists

    # Create table
    cursor.execute(
        """
        CREATE TABLE poker_hands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hand_text TEXT NOT NULL,
            board_text TEXT,
            hole_cards TEXT NOT NULL,
            player_count INTEGER NOT NULL DEFAULT 2,
            position TEXT,
            action TEXT,
            result TEXT,
            notes TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT valid_hand_format CHECK(
                hand_text GLOB '[AKQJT2-9][shdc][AKQJT2-9][shdc]' OR
                hand_text GLOB '[AKQJT2-9][shdc][AKQJT2-9][shdc] [AKQJT2-9][shdc][AKQJT2-9][shdc]'
            )
        )
        """
    )

    # Create indexes
    cursor.execute("CREATE INDEX idx_hand_text ON poker_hands(hand_text)")
    cursor.execute("CREATE INDEX idx_timestamp ON poker_hands(timestamp)")
    cursor.execute("CREATE INDEX idx_position ON poker_hands(position)")

    conn.commit()
    conn.close()


def migrate_postgresql(connection_string: str) -> None:
    """Initialize poker_hands table for PostgreSQL."""
    try:
        import psycopg2
    except ImportError:
        raise ImportError("psycopg2 required for PostgreSQL support")

    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name='poker_hands'
        )
        """
    )
    if cursor.fetchone()[0]:
        return  # Table already exists

    # Create table
    cursor.execute(
        """
        CREATE TABLE poker_hands (
            id SERIAL PRIMARY KEY,
            hand_text TEXT NOT NULL,
            board_text TEXT,
            hole_cards TEXT NOT NULL,
            player_count INTEGER NOT NULL DEFAULT 2,
            position TEXT,
            action TEXT,
            result TEXT,
            notes TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT valid_hand_format CHECK(
                hand_text ~ '^[AKQJT2-9][shdc][AKQJT2-9][shdc]$' OR
                hand_text ~ '^[AKQJT2-9][shdc][AKQJT2-9][shdc] [AKQJT2-9][shdc][AKQJT2-9][shdc]$'
            )
        )
        """
    )

    # Create indexes
    cursor.execute("CREATE INDEX idx_hand_text ON poker_hands(hand_text)")
    cursor.execute("CREATE INDEX idx_timestamp ON poker_hands(timestamp)")
    cursor.execute("CREATE INDEX idx_position ON poker_hands(position)")

    conn.commit()
    conn.close()


def init_poker_hands_table(db_type: str = "sqlite", db_config: Optional[dict] = None) -> None:
    """
    Initialize poker_hands table for the specified database type.

    Args:
        db_type: Type of database ('sqlite' or 'postgresql')
        db_config: Database configuration (path for sqlite, connection string for postgresql)
    """
    if db_config is None:
        db_config = {}

    if db_type == "sqlite":
        db_path = db_config.get("path", "pokertool.db")
        migrate_sqlite(db_path)
    elif db_type == "postgresql":
        connection_string = db_config.get("connection_string", "")
        migrate_postgresql(connection_string)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
