"""
Test Database Seeding Module
=============================

This module provides database seeding utilities for consistent test data across
different test scenarios.

Module: tests.fixtures.seeds
Version: 1.0.0
Last Modified: 2025-10-22

Available Seeds:
    - new_user: Fresh user with no hands played
    - veteran_player: Experienced player with 10,000+ hands
    - tournament_player: Tournament specialist with MTT data
    - cash_game_grinder: High-volume cash game player
    - mixed_player: Player with mix of tournaments and cash games

Usage:
    from tests.fixtures.seeds import seed_database, SEED_SCENARIOS

    # Seed with new user data
    db = seed_database(':memory:', scenario='new_user')

    # Or use decorator
    @pytest.fixture
    def seeded_db():
        return seed_database(':memory:', scenario='veteran_player')
"""

from .base import seed_database, clear_database, SEED_SCENARIOS
from .new_user import seed_new_user
from .veteran_player import seed_veteran_player
from .tournament_player import seed_tournament_player

__all__ = [
    'seed_database',
    'clear_database',
    'SEED_SCENARIOS',
    'seed_new_user',
    'seed_veteran_player',
    'seed_tournament_player',
]
