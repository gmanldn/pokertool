"""Tests for v0.5.0: Initialize poker_hands table migration."""

import os
import tempfile
import pytest
import sqlite3

from src.pokertool.migrations.init_poker_hands_table import (
    migrate_sqlite,
    init_poker_hands_table,
)


class TestPokerHandsTableInitialization:
    """Test poker_hands table initialization."""

    def test_sqlite_table_creation(self):
        """Test creating poker_hands table in SQLite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            migrate_sqlite(db_path)

            # Verify table exists
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='poker_hands'"
            )
            assert cursor.fetchone() is not None
            conn.close()

    def test_sqlite_table_columns(self):
        """Test poker_hands table has correct columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            migrate_sqlite(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(poker_hands)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "id" in columns
            assert "hand_text" in columns
            assert "board_text" in columns
            assert "hole_cards" in columns
            assert "player_count" in columns
            assert "position" in columns
            assert "action" in columns
            assert "result" in columns
            assert "notes" in columns
            assert "timestamp" in columns
            conn.close()

    def test_sqlite_table_indexes(self):
        """Test poker_hands table has required indexes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            migrate_sqlite(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='poker_hands'"
            )
            indexes = {row[0] for row in cursor.fetchall()}

            assert "idx_hand_text" in indexes
            assert "idx_timestamp" in indexes
            assert "idx_position" in indexes
            conn.close()

    def test_sqlite_valid_hand_format_constraint(self):
        """Test hand format constraint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            migrate_sqlite(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Valid format: two cards
            cursor.execute(
                "INSERT INTO poker_hands (hand_text, hole_cards) VALUES (?, ?)",
                ("AsKh", "AsKh"),
            )
            conn.commit()

            # Verify insert worked
            cursor.execute("SELECT COUNT(*) FROM poker_hands")
            assert cursor.fetchone()[0] == 1

            conn.close()

    def test_sqlite_idempotent_migration(self):
        """Test running migration twice doesn't error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")

            # Run twice
            migrate_sqlite(db_path)
            migrate_sqlite(db_path)

            # Verify table still exists
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='poker_hands'"
            )
            assert cursor.fetchone()[0] == 1
            conn.close()

    def test_init_poker_hands_table_sqlite(self):
        """Test init function with SQLite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            init_poker_hands_table("sqlite", {"path": db_path})

            # Verify table exists
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='poker_hands'"
            )
            assert cursor.fetchone() is not None
            conn.close()

    def test_init_poker_hands_table_invalid_type(self):
        """Test init with invalid database type."""
        with pytest.raises(ValueError, match="Unsupported database type"):
            init_poker_hands_table("invalid_type", {})

    def test_sqlite_player_count_default(self):
        """Test player_count has default value of 2."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            migrate_sqlite(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO poker_hands (hand_text, hole_cards) VALUES (?, ?)",
                ("AsKh", "AsKh"),
            )
            conn.commit()

            cursor.execute("SELECT player_count FROM poker_hands WHERE id=1")
            assert cursor.fetchone()[0] == 2
            conn.close()

    def test_sqlite_timestamp_auto_set(self):
        """Test timestamp is automatically set on insert."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            migrate_sqlite(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO poker_hands (hand_text, hole_cards) VALUES (?, ?)",
                ("AsKh", "AsKh"),
            )
            conn.commit()

            cursor.execute("SELECT timestamp FROM poker_hands WHERE id=1")
            timestamp = cursor.fetchone()[0]
            assert timestamp is not None
            conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
