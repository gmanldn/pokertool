#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Migration: Add bet_size_ratio and pot_size Columns
============================================================

Adds bet sizing tracking columns to poker_hands table for both SQLite and PostgreSQL.
These columns enable analysis of bet sizing patterns and pot odds calculations.

Migration: 002_add_bet_sizing_columns
Date: 2025-10-22
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
    Add bet_size_ratio and pot_size columns to SQLite database.

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

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(poker_hands)")
        columns = [row[1] for row in cursor.fetchall()]

        columns_to_add = []
        if 'bet_size_ratio' not in columns:
            columns_to_add.append('bet_size_ratio')
        if 'pot_size' not in columns:
            columns_to_add.append('pot_size')

        if not columns_to_add:
            logger.info("Columns 'bet_size_ratio' and 'pot_size' already exist in SQLite database")
            conn.close()
            return True

        # Add the columns
        for column in columns_to_add:
            cursor.execute(f"""
                ALTER TABLE poker_hands
                ADD COLUMN {column} REAL CHECK({column} IS NULL OR {column} >= 0.0)
            """)
            logger.info(f"Added column '{column}' to poker_hands table")

        conn.commit()
        conn.close()

        logger.info(f"Successfully added bet sizing columns to SQLite database: {db_path}")
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
    Add bet_size_ratio and pot_size columns to PostgreSQL database.

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

        # Check which columns already exist
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='poker_hands' AND column_name IN ('bet_size_ratio', 'pot_size')
        """)
        existing_columns = {row[0] for row in cursor.fetchall()}

        columns_to_add = []
        if 'bet_size_ratio' not in existing_columns:
            columns_to_add.append('bet_size_ratio')
        if 'pot_size' not in existing_columns:
            columns_to_add.append('pot_size')

        if not columns_to_add:
            logger.info("Columns 'bet_size_ratio' and 'pot_size' already exist in PostgreSQL database")
            conn.close()
            return True

        # Add the columns
        for column in columns_to_add:
            cursor.execute(f"""
                ALTER TABLE poker_hands
                ADD COLUMN {column} REAL CHECK({column} IS NULL OR {column} >= 0.0)
            """)
            logger.info(f"Added column '{column}' to poker_hands table")

        conn.commit()
        conn.close()

        logger.info(f"Successfully added bet sizing columns to PostgreSQL database: {database}")
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

    logger.info(f"Running bet sizing columns migration for {db_type}...")

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

    print("Database Migration: Add bet_size_ratio and pot_size columns")
    print("=" * 60)

    success = run_migration()

    if success:
        print("✓ Migration completed successfully")
    else:
        print("✗ Migration failed - check logs for details")
        exit(1)
