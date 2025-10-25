#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automatic Migration Runner
===========================

Automatically runs pending database migrations on startup.
Tracks migration history in migrations_history table.

This ensures that existing databases are updated with new columns/indexes
without requiring manual migration execution.
"""

import logging
import importlib
import os
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import database dependencies
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None

import sqlite3


class MigrationRunner:
    """
    Manages and executes database migrations automatically.
    """

    def __init__(self, db_type: str = 'auto', **db_params):
        """
        Initialize migration runner.

        Args:
            db_type: 'sqlite', 'postgresql', or 'auto' (detect from environment)
            **db_params: Database connection parameters
        """
        if db_type == 'auto':
            db_type = os.getenv('POKER_DB_TYPE', 'sqlite').lower()

        self.db_type = db_type
        self.db_params = db_params

        # Set default params if not provided
        if db_type == 'sqlite':
            self.db_params.setdefault('db_path', os.getenv('POKER_DB_PATH', 'poker_decisions.db'))
        else:
            self.db_params.setdefault('host', os.getenv('POKER_DB_HOST', 'localhost'))
            self.db_params.setdefault('port', int(os.getenv('POKER_DB_PORT', '5432')))
            self.db_params.setdefault('database', os.getenv('POKER_DB_NAME', 'pokertool'))
            self.db_params.setdefault('user', os.getenv('POKER_DB_USER', 'postgres'))
            self.db_params.setdefault('password', os.getenv('POKER_DB_PASSWORD'))

    def _create_migrations_table(self, conn, cursor):
        """Create migrations_history table if it doesn't exist."""
        if self.db_type == 'postgresql':
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations_history (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL
                )
            """)
        else:  # SQLite
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name TEXT UNIQUE NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success INTEGER NOT NULL
                )
            """)
        conn.commit()

    def _get_applied_migrations(self, cursor) -> List[str]:
        """Get list of already applied migrations."""
        try:
            cursor.execute("SELECT migration_name FROM migrations_history WHERE success = ?", (True,) if self.db_type == 'sqlite' else (True,))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"Could not read migrations_history: {e}")
            return []

    def _record_migration(self, conn, cursor, migration_name: str, success: bool):
        """Record migration execution in history."""
        if self.db_type == 'postgresql':
            cursor.execute(
                "INSERT INTO migrations_history (migration_name, success) VALUES (%s, %s) ON CONFLICT (migration_name) DO UPDATE SET applied_at = CURRENT_TIMESTAMP, success = EXCLUDED.success",
                (migration_name, success)
            )
        else:  # SQLite
            cursor.execute(
                "INSERT OR REPLACE INTO migrations_history (migration_name, success) VALUES (?, ?)",
                (migration_name, success)
            )
        conn.commit()

    def _get_available_migrations(self) -> List[str]:
        """Get list of available migration files in order."""
        migrations_dir = Path(__file__).parent / 'migrations'
        if not migrations_dir.exists():
            return []

        # Find all migration Python files
        migration_files = sorted([
            f.stem for f in migrations_dir.glob('*.py')
            if f.stem != '__init__' and not f.stem.startswith('_')
        ])

        return migration_files

    def run_pending_migrations(self) -> Tuple[int, int]:
        """
        Run all pending migrations.

        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        try:
            # Connect to database
            if self.db_type == 'postgresql':
                if not POSTGRES_AVAILABLE:
                    logger.warning("PostgreSQL not available, skipping migrations")
                    return 0, 0

                conn = psycopg2.connect(**{k: v for k, v in self.db_params.items() if v is not None})
            else:
                db_path = self.db_params['db_path']
                if not Path(db_path).exists():
                    logger.info(f"Database {db_path} does not exist yet - skipping migrations")
                    return 0, 0
                conn = sqlite3.connect(db_path)

            cursor = conn.cursor()

            # Create migrations history table
            self._create_migrations_table(conn, cursor)

            # Get applied and available migrations
            applied = set(self._get_applied_migrations(cursor))
            available = self._get_available_migrations()

            logger.info(f"Found {len(available)} available migrations, {len(applied)} already applied")

            # Run pending migrations
            for migration_name in available:
                if migration_name in applied:
                    logger.debug(f"Skipping already applied migration: {migration_name}")
                    continue

                logger.info(f"Running migration: {migration_name}")

                try:
                    # Import and run migration
                    module = importlib.import_module(f'pokertool.migrations.{migration_name}')

                    if hasattr(module, 'run_migration'):
                        # Use the migration's run_migration function
                        success = module.run_migration(self.db_type)
                    elif hasattr(module, f'migrate_{self.db_type}'):
                        # Use database-specific function
                        migrate_func = getattr(module, f'migrate_{self.db_type}')
                        success = migrate_func(**self.db_params)
                    else:
                        logger.error(f"Migration {migration_name} has no run_migration or migrate_{self.db_type} function")
                        success = False

                    if success:
                        logger.info(f"✓ Migration {migration_name} completed successfully")
                        successful += 1
                    else:
                        logger.error(f"✗ Migration {migration_name} failed")
                        failed += 1

                    # Record result
                    self._record_migration(conn, cursor, migration_name, success)

                except Exception as e:
                    logger.error(f"✗ Migration {migration_name} raised exception: {e}")
                    self._record_migration(conn, cursor, migration_name, False)
                    failed += 1

            conn.close()

            if failed > 0:
                logger.warning(f"Migrations completed with {successful} successful, {failed} failed")
            elif successful > 0:
                logger.info(f"✓ All {successful} pending migrations completed successfully")
            else:
                logger.debug("No pending migrations to run")

            return successful, failed

        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return 0, 1


def run_migrations_on_startup(db_type: str = 'auto', **db_params) -> bool:
    """
    Convenience function to run migrations on application startup.

    Args:
        db_type: 'sqlite', 'postgresql', or 'auto'
        **db_params: Database connection parameters

    Returns:
        True if all migrations succeeded, False if any failed
    """
    runner = MigrationRunner(db_type, **db_params)
    successful, failed = runner.run_pending_migrations()
    return failed == 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("Database Migration Runner")
    print("=" * 60)

    success = run_migrations_on_startup()

    if success:
        print("✓ All migrations completed successfully")
    else:
        print("✗ Some migrations failed - check logs for details")
        exit(1)
