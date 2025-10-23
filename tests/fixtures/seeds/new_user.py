"""
New User Seeding
================

Seeds database with fresh user data (no hands played).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from pokertool.database import PokerDatabase


def seed_new_user(db: PokerDatabase) -> None:
    """
    Seed database with new user data.

    New user characteristics:
    - No hands played
    - No statistics
    - Default configuration
    - Fresh account

    Args:
        db: PokerDatabase instance to seed
    """
    # New user has no hands, so nothing to seed
    # This scenario is useful for testing first-time user experience

    # Verify database is empty
    total_hands = db.get_total_hands()
    assert total_hands == 0, f"Expected 0 hands for new user, found {total_hands}"

    # Could add default user preferences here if needed
    # For now, an empty database represents a new user
