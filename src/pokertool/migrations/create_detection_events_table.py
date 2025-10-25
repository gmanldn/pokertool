#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Migration: Create detection_events Table
==================================================

Creates detection_events table for tracking all detection system events
including card detection, pot size changes, player actions, board changes, etc.

Migration: 004_create_detection_events_table
Date: 2025-10-25
"""

import sqlite3
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import PostgreSQL dependencies
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None


def migrate_sqlite(db_path: str = 'poker_decisions.db') -> bool:
    """
    Create detection_events table in SQLite database.

    Args:
        db_path: Path to SQLite database file

    Returns:
        True if successful, False otherwise
    """
    try:
        if not Path(db_path).exists():
            logger.info(f"Database {db_path} does not exist yet - skipping migration")
            return True

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detection_events'")
        if cursor.fetchone():
            logger.info("Table 'detection_events' already exists in SQLite database")
            conn.close()
            return True

        # Create the table
        cursor.execute("""
            CREATE TABLE detection_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                detection_type TEXT NOT NULL,
                confidence REAL CHECK(confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
                value TEXT,
                previous_value TEXT,
                position TEXT,
                frame_number INTEGER,
                session_id TEXT,
                metadata TEXT DEFAULT '{}',
                processing_time_ms REAL,
                success INTEGER NOT NULL DEFAULT 1,
                error_message TEXT,
                CHECK(event_type IN ('card_detected', 'pot_change', 'board_change', 'player_action',
                                     'button_moved', 'stack_change', 'hand_complete', 'detection_error')),
                CHECK(detection_type IN ('card_rank', 'card_suit', 'pot_size', 'board_cards',
                                         'player_action', 'dealer_button', 'stack_size', 'player_name', 'hand_result'))
            )
        """)

        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_timestamp ON detection_events(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_type ON detection_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_session ON detection_events(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_success ON detection_events(success)")

        conn.commit()
        conn.close()

        logger.info(f"Successfully created detection_events table in SQLite database: {db_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to migrate SQLite database: {e}")
        return False


def migrate_postgresql(
    host: str = 'localhost',
    port: int = 5432,
    database: str = 'pokertool',
    user: str = 'postgres',
    password: str = None
) -> bool:
    """
    Create detection_events table in PostgreSQL database.

    Args:
        host: PostgreSQL host
        port: PostgreSQL port
        database: Database name
        user: Database user
        password: Database password

    Returns:
        True if successful, False otherwise
    """
    if not POSTGRES_AVAILABLE:
        logger.warning("PostgreSQL dependencies not available - skipping PostgreSQL migration")
        return True

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=10
        )

        cursor = conn.cursor()

        # Check if table already exists
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='detection_events'
        """)

        if cursor.fetchone():
            logger.info("Table 'detection_events' already exists in PostgreSQL database")
            conn.close()
            return True

        # Create the table
        cursor.execute("""
            CREATE TABLE detection_events (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                event_type VARCHAR(50) NOT NULL,
                detection_type VARCHAR(50) NOT NULL,
                confidence REAL CHECK(confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
                value TEXT,
                previous_value TEXT,
                position VARCHAR(10),
                frame_number BIGINT,
                session_id VARCHAR(32),
                metadata JSONB DEFAULT '{}',
                processing_time_ms REAL,
                success BOOLEAN NOT NULL DEFAULT TRUE,
                error_message TEXT,
                CHECK(event_type IN ('card_detected', 'pot_change', 'board_change', 'player_action',
                                     'button_moved', 'stack_change', 'hand_complete', 'detection_error')),
                CHECK(detection_type IN ('card_rank', 'card_suit', 'pot_size', 'board_cards',
                                         'player_action', 'dealer_button', 'stack_size', 'player_name', 'hand_result'))
            )
        """)

        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_timestamp ON detection_events(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_type ON detection_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_session ON detection_events(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_success ON detection_events(success)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_metadata ON detection_events USING GIN(metadata)")

        # Composite index for common query patterns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_events_session_time ON detection_events(session_id, timestamp DESC)")

        conn.commit()
        conn.close()

        logger.info(f"Successfully created detection_events table in PostgreSQL database: {database}")
        return True

    except Exception as e:
        logger.error(f"Failed to migrate PostgreSQL database: {e}")
        return False


def run_migration(db_type: str = 'auto') -> bool:
    """
    Run migration for the configured database type.

    Args:
        db_type: 'sqlite', 'postgresql', or 'auto' (detect from environment)

    Returns:
        True if successful, False otherwise
    """
    if db_type == 'auto':
        db_type = os.getenv('POKER_DB_TYPE', 'sqlite').lower()

    logger.info(f"Running detection_events table migration for {db_type}...")

    if db_type == 'postgresql':
        return migrate_postgresql(
            host=os.getenv('POKER_DB_HOST', 'localhost'),
            port=int(os.getenv('POKER_DB_PORT', '5432')),
            database=os.getenv('POKER_DB_NAME', 'pokertool'),
            user=os.getenv('POKER_DB_USER', 'postgres'),
            password=os.getenv('POKER_DB_PASSWORD')
        )
    else:
        return migrate_sqlite(
            db_path=os.getenv('POKER_DB_PATH', 'poker_decisions.db')
        )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("Database Migration: Create detection_events table")
    print("=" * 60)

    success = run_migration()

    if success:
        print("✓ Migration completed successfully")
    else:
        print("✗ Migration failed - check logs for details")
        exit(1)
