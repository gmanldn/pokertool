#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Integration Tests
===========================

Comprehensive integration tests for database operations including:
- Hand analysis storage and retrieval
- Session management
- Data validation
- Migration compatibility
- Cross-database consistency (SQLite/PostgreSQL)

Test Suite: integration/database
"""

import pytest
import os
import tempfile
from typing import Generator

from pokertool.database import PokerDatabase, ProductionDatabase, DatabaseConfig, DatabaseType
from pokertool.data_validation import ValidationError


@pytest.fixture
def temp_db() -> Generator[PokerDatabase, None, None]:
    """Create temporary test database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db = PokerDatabase(db_path)
    yield db

    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def prod_db() -> Generator[ProductionDatabase, None, None]:
    """Create temporary production database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    config = DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        db_path=db_path
    )
    db = ProductionDatabase(config)
    yield db

    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestHandAnalysisIntegration:
    """Integration tests for hand analysis operations."""

    def test_save_and_retrieve_hand(self, temp_db):
        """Test saving and retrieving a hand analysis."""
        # Save hand
        hand_id = temp_db.save_hand_analysis(
            hand="Ah Kh",
            board="Qh Jh Th",
            result="Royal flush draw - very strong",
            confidence_score=0.95,
            bet_size_ratio=0.75,
            pot_size=100.0,
            player_position="BTN"
        )

        assert hand_id > 0

        # Retrieve hands
        hands = temp_db.get_recent_hands(limit=10)
        assert len(hands) == 1

        hand = hands[0]
        assert hand['hand_text'] == "Ah Kh"
        assert hand['board_text'] == "Qh Jh Th"
        assert hand['confidence_score'] == 0.95
        assert hand['bet_size_ratio'] == 0.75
        assert hand['pot_size'] == 100.0
        assert hand['player_position'] == "BTN"

    def test_save_multiple_hands_with_session(self, temp_db):
        """Test saving multiple hands in a session."""
        session_id = "test_session_123"

        # Save multiple hands
        hand_ids = []
        for i in range(5):
            hand_id = temp_db.save_hand_analysis(
                hand=f"A{i%4+1}h K{i%4+1}h",
                board="Qh Jh Th",
                result=f"Hand {i}",
                session_id=session_id,
                confidence_score=0.9 - (i * 0.05),
                player_position=["BTN", "SB", "BB", "UTG", "CO"][i]
            )
            hand_ids.append(hand_id)

        assert len(hand_ids) == 5
        assert len(set(hand_ids)) == 5  # All unique

        # Retrieve all hands
        hands = temp_db.get_recent_hands(limit=10)
        assert len(hands) == 5

        # Verify order (most recent first)
        assert hands[0]['id'] == hand_ids[-1]

    def test_validation_prevents_invalid_data(self, temp_db):
        """Test that validation prevents invalid data insertion."""
        # Invalid hand format
        with pytest.raises(ValueError, match="Invalid data for insertion"):
            temp_db.save_hand_analysis(
                hand="Invalid",
                board="Qh Jh Th",
                result="Test"
            )

        # Invalid confidence score
        with pytest.raises(ValueError, match="Confidence score must be between"):
            temp_db.save_hand_analysis(
                hand="Ah Kh",
                board="Qh Jh Th",
                result="Test",
                confidence_score=1.5
            )

        # Invalid player position
        with pytest.raises(ValueError, match="Invalid player position"):
            temp_db.save_hand_analysis(
                hand="Ah Kh",
                board="Qh Jh Th",
                result="Test",
                player_position="INVALID"
            )

    def test_confidence_score_tracking(self, temp_db):
        """Test confidence score tracking across multiple hands."""
        confidence_scores = [0.95, 0.88, 0.72, 0.91, 0.85]

        for i, conf in enumerate(confidence_scores):
            temp_db.save_hand_analysis(
                hand=f"A{i+1}h K{i+1}h",
                board="Qh Jh Th",
                result=f"Hand {i}",
                confidence_score=conf
            )

        hands = temp_db.get_recent_hands(limit=10)
        retrieved_scores = [h['confidence_score'] for h in hands]

        # Reverse because recent hands are first
        assert retrieved_scores[::-1] == confidence_scores

    def test_bet_sizing_tracking(self, temp_db):
        """Test bet sizing ratio and pot size tracking."""
        test_data = [
            (0.5, 100.0),   # Half pot
            (1.0, 150.0),   # Pot-sized
            (0.33, 200.0),  # 1/3 pot
            (2.0, 75.0),    # Over-bet
        ]

        for bet_ratio, pot in test_data:
            temp_db.save_hand_analysis(
                hand="Ah Kh",
                board="Qh Jh Th",
                result="Test",
                bet_size_ratio=bet_ratio,
                pot_size=pot
            )

        hands = temp_db.get_recent_hands(limit=10)

        for i, hand in enumerate(reversed(hands)):
            assert hand['bet_size_ratio'] == test_data[i][0]
            assert hand['pot_size'] == test_data[i][1]

    def test_position_based_analysis(self, temp_db):
        """Test position-based hand tracking."""
        positions = ["BTN", "SB", "BB", "UTG", "CO", "HJ", "MP"]

        for pos in positions:
            temp_db.save_hand_analysis(
                hand="Ah Kh",
                board="Qh Jh Th",
                result=f"From {pos}",
                player_position=pos
            )

        hands = temp_db.get_recent_hands(limit=20)
        retrieved_positions = [h['player_position'] for h in hands]

        assert set(retrieved_positions) == set(positions)


class TestProductionDatabaseIntegration:
    """Integration tests for ProductionDatabase."""

    def test_save_with_metadata(self, prod_db):
        """Test saving hands with metadata."""
        metadata = {
            'table_name': 'NL100',
            'opponent_count': 5,
            'vpip': 25.0,
            'pfr': 18.0
        }

        hand_id = prod_db.save_hand_analysis(
            hand="Ah Kh",
            board="Qh Jh Th",
            result="Test",
            metadata=metadata,
            confidence_score=0.92,
            bet_size_ratio=0.66,
            pot_size=125.0,
            player_position="BTN"
        )

        assert hand_id > 0

        hands = prod_db.get_recent_hands(limit=1)
        assert len(hands) == 1
        assert hands[0]['confidence_score'] == 0.92

    def test_database_stats(self, prod_db):
        """Test database statistics retrieval."""
        # Add some hands
        for i in range(10):
            prod_db.save_hand_analysis(
                hand=f"A{i%4+1}h K{i%4+1}h",
                board="Qh Jh Th",
                result=f"Hand {i}"
            )

        stats = prod_db.get_database_stats()

        assert 'database_type' in stats
        assert 'activity' in stats
        assert stats['activity']['total_hands'] == 10


class TestCrossComponentIntegration:
    """Integration tests across multiple components."""

    def test_validation_database_integration(self, temp_db):
        """Test that validation integrates properly with database."""
        # Valid data should save
        hand_id = temp_db.save_hand_analysis(
            hand="Ah Kh",
            board="Qh Jh Th",
            result="Good hand",
            confidence_score=0.95,
            bet_size_ratio=0.75,
            pot_size=100.0,
            player_position="BTN"
        )
        assert hand_id > 0

        # Invalid data should be rejected before hitting database
        with pytest.raises(ValueError):
            temp_db.save_hand_analysis(
                hand="Invalid hand format",
                board="Qh Jh Th",
                result="Bad"
            )

    def test_sanity_check_integration(self, temp_db):
        """Test sanity checks integrate with database operations."""
        # Negative pot size should be rejected
        with pytest.raises(ValueError):
            temp_db.save_hand_analysis(
                hand="Ah Kh",
                board="Qh Jh Th",
                result="Test",
                pot_size=-50.0
            )

        # Negative bet ratio should be rejected
        with pytest.raises(ValueError):
            temp_db.save_hand_analysis(
                hand="Ah Kh",
                board="Qh Jh Th",
                result="Test",
                bet_size_ratio=-0.5
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
