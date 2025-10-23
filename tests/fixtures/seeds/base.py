"""
Base Database Seeding Utilities
================================

Core functions for seeding test databases with consistent data.
"""

import sys
from pathlib import Path
from typing import Optional, Literal

# Add src to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from pokertool.database import PokerDatabase

# Available seeding scenarios
SEED_SCENARIOS = Literal['new_user', 'veteran_player', 'tournament_player', 'cash_game_grinder', 'mixed_player']


def seed_database(db_path: str = ':memory:', scenario: str = 'new_user') -> PokerDatabase:
    """
    Seed a database with test data for a specific scenario.

    Args:
        db_path: Path to database file (':memory:' for in-memory database)
        scenario: Seeding scenario to use

    Returns:
        PokerDatabase instance with seeded data

    Examples:
        >>> db = seed_database(':memory:', scenario='new_user')
        >>> assert db.get_total_hands() == 0

        >>> db = seed_database(':memory:', scenario='veteran_player')
        >>> assert db.get_total_hands() >= 10000
    """
    # Create or open database
    db = PokerDatabase(db_path)

    # Clear existing data
    clear_database(db)

    # Seed based on scenario
    if scenario == 'new_user':
        from .new_user import seed_new_user
        seed_new_user(db)
    elif scenario == 'veteran_player':
        from .veteran_player import seed_veteran_player
        seed_veteran_player(db)
    elif scenario == 'tournament_player':
        from .tournament_player import seed_tournament_player
        seed_tournament_player(db)
    elif scenario == 'cash_game_grinder':
        # TODO: Implement cash game grinder seeding
        pass
    elif scenario == 'mixed_player':
        # TODO: Implement mixed player seeding
        pass
    else:
        raise ValueError(f"Unknown seeding scenario: {scenario}")

    return db


def clear_database(db: PokerDatabase) -> None:
    """
    Clear all data from a database.

    Args:
        db: PokerDatabase instance to clear

    Note:
        This does not drop tables, only clears data.
        Use with caution on non-test databases!
    """
    # Note: Actual implementation depends on PokerDatabase schema
    # This is a placeholder that demonstrates the concept

    if hasattr(db, 'conn') and db.conn:
        cursor = db.conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()

        # Clear each table
        for (table_name,) in tables:
            try:
                cursor.execute(f'DELETE FROM {table_name}')
            except Exception:
                # Table might not exist or have constraints
                pass

        db.conn.commit()


def get_scenario_description(scenario: str) -> str:
    """Get human-readable description of a seeding scenario."""
    descriptions = {
        'new_user': 'Fresh user with no poker hands played yet',
        'veteran_player': 'Experienced player with 10,000+ hands and detailed stats',
        'tournament_player': 'Tournament specialist with MTT-specific data',
        'cash_game_grinder': 'High-volume cash game player (100k+ hands)',
        'mixed_player': 'Balanced player with tournaments and cash games',
    }
    return descriptions.get(scenario, 'Unknown scenario')
