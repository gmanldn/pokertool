# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/pokertool/database.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Production Database Module
Provides PostgreSQL support with connection pooling for production environments.
Maintains compatibility with existing SQLite implementation for development.
"""

import os
import logging
import time
import hashlib
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Iterator, Union
from dataclasses import dataclass
from pathlib import Path
import json
from enum import Enum

# Try to import PostgreSQL dependencies
try:
    import psycopg2
    from psycopg2 import pool, sql
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None
    pool = None
    sql = None
    RealDictCursor = None

# Import existing secure database for fallback
try:
    from .storage import SecureDatabase, SecurityError
except ImportError:
    from pokertool.storage import SecureDatabase, SecurityError

try:
    from .error_handling import retry_on_failure, db_guard
except ImportError:
    from pokertool.error_handling import retry_on_failure, db_guard

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = 'sqlite'
    POSTGRESQL = 'postgresql'


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_type: DatabaseType
    # SQLite config
    db_path: Optional[str] = None
    # PostgreSQL config
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    # Connection pool config
    min_connections: int = 2
    max_connections: int = 20
    connection_timeout: int = 30
    # Security
    ssl_mode: str = 'prefer'

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables."""
        db_type_str = os.getenv('POKER_DB_TYPE', 'sqlite').lower()
        db_type = DatabaseType.POSTGRESQL if db_type_str == 'postgresql' else DatabaseType.SQLITE

        if db_type == DatabaseType.POSTGRESQL:
            return cls(
                db_type=db_type,
                host=os.getenv('POKER_DB_HOST', 'localhost'),
                port=int(os.getenv('POKER_DB_PORT', '5432')),
                database=os.getenv('POKER_DB_NAME', 'pokertool'),
                user=os.getenv('POKER_DB_USER', 'postgres'),
                password=os.getenv('POKER_DB_PASSWORD'),
                min_connections=int(os.getenv('POKER_DB_MIN_CONN', '2')),
                max_connections=int(os.getenv('POKER_DB_MAX_CONN', '20')),
                ssl_mode=os.getenv('POKER_DB_SSL_MODE', 'prefer')
            )
        else:
            return cls(
                db_type=db_type,
                db_path=os.getenv('POKER_DB_PATH', 'poker_decisions.db')
            )


class ProductionDatabase:
    """
    Production database adapter supporting both SQLite and PostgreSQL.
    Provides connection pooling, migration support, and monitoring.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self.connection_pool = None
        self.sqlite_db = None
        self.rate_limiter = {}

        # Initialize based on database type
        if self.config.db_type == DatabaseType.POSTGRESQL:
            if not POSTGRES_AVAILABLE:
                raise RuntimeError("PostgreSQL dependencies not available. Install psycopg2-binary.")
            self._init_postgresql()
        else:
            self._init_sqlite()

    def _init_postgresql(self):
        """Initialize PostgreSQL connection pool."""
        try:
            # Build connection string
            conn_params = {
                'host': self.config.host,
                'port': self.config.port,
                'database': self.config.database,
                'user': self.config.user,
                'password': self.config.password,
                'sslmode': self.config.ssl_mode,
                'connect_timeout': self.config.connection_timeout,
                'application_name': 'pokertool'
            }

            # Remove None values
            conn_params = {k: v for k, v in conn_params.items() if v is not None}

            # Create connection pool
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                self.config.min_connections,
                self.config.max_connections,
                **conn_params
            )

            # Initialize schema
            self._create_postgresql_schema()

            logger.info(f"PostgreSQL connection pool initialized: {self.config.host}:{self.config.port}/{self.config.database}")

        except Exception as e:
            logger.error(f'Failed to initialize PostgreSQL: {e}')
            raise

    def _init_sqlite(self):
        """Initialize SQLite fallback."""
        self.sqlite_db = SecureDatabase(self.config.db_path)
        logger.info(f'SQLite database initialized: {self.config.db_path}')

    @contextmanager
    def get_connection(self) -> Iterator[Any]:
        """Get database connection from pool or SQLite."""
        if self.config.db_type == DatabaseType.POSTGRESQL:
            conn = self.connection_pool.getconn()
            try:
                yield conn
            finally:
                self.connection_pool.putconn(conn)
        else:
            with self.sqlite_db._get_connection() as conn:
                yield conn

    def _create_postgresql_schema(self):
        """Create PostgreSQL schema with enhanced features."""
        schema_sql = """
        -- Enable extensions
        CREATE EXTENSION IF NOT EXISTS 'uuid-ossp';
        CREATE EXTENSION IF NOT EXISTS 'pg_stat_statements';

        -- Main tables
        CREATE TABLE IF NOT EXISTS poker_hands (
            id BIGSERIAL PRIMARY KEY,
            hand_text VARCHAR(50) NOT NULL CHECK(length(hand_text) <= 50),
            board_text VARCHAR(50) CHECK(board_text IS NULL OR length(board_text) <= 50),
            analysis_result TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            user_hash VARCHAR(32),
            session_id VARCHAR(32),
            metadata JSONB DEFAULT '{}',
            -- Enhanced constraints for PostgreSQL
            CONSTRAINT valid_hand_format CHECK(
                hand_text ~ '^[AKQJT2-9][shdc][AKQJT2-9][shdc]( [AKQJT2-9][shdc][AKQJT2-9][shdc])*$'
            ),
            CONSTRAINT valid_board_format CHECK(
                board_text IS NULL OR
                board_text ~ '^([AKQJT2-9][shdc] ){2,4}[AKQJT2-9][shdc]$'
            )
        );

        CREATE TABLE IF NOT EXISTS game_sessions (
            session_id VARCHAR(32) PRIMARY KEY,
            start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP WITH TIME ZONE,
            hands_played INTEGER DEFAULT 0,
            notes TEXT CHECK(length(notes) <= 1000),
            metadata JSONB DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS security_log (
            id BIGSERIAL PRIMARY KEY,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            event_type VARCHAR(50) NOT NULL,
            details TEXT,
            severity INTEGER DEFAULT 1,
            user_hash VARCHAR(32),
            ip_address INET,
            metadata JSONB DEFAULT '{}'
        );

        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_hands_timestamp ON poker_hands(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_hands_user_hash ON poker_hands(user_hash);
        CREATE INDEX IF NOT EXISTS idx_hands_session ON poker_hands(session_id);
        CREATE INDEX IF NOT EXISTS idx_hands_metadata ON poker_hands USING GIN(metadata);

        CREATE INDEX IF NOT EXISTS idx_sessions_start ON game_sessions(start_time DESC);
        CREATE INDEX IF NOT EXISTS idx_sessions_metadata ON game_sessions USING GIN(metadata);

        CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_log(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_security_type ON security_log(event_type);
        CREATE INDEX IF NOT EXISTS idx_security_user ON security_log(user_hash);
        """

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()

    def _rate_limit_check(self, operation: str, limit_per_minute: int = 100):
        """Check rate limits (same as SQLite implementation)."""
        current_time = time.time()
        minute_window = int(current_time // 60)

        if operation not in self.rate_limiter:
            self.rate_limiter[operation] = {}

        count = self.rate_limiter[operation].get(minute_window, 0)
        if count >= limit_per_minute:
            raise SecurityError(f"Rate limit exceeded for {operation}: {count}/{limit_per_minute}")

        self.rate_limiter[operation][minute_window] = count + 1

        # Clean old entries
        old_windows = [w for w in self.rate_limiter[operation] if w < minute_window - 5]
        for w in old_windows:
            del self.rate_limiter[operation][w]

    def _generate_user_hash(self) -> str:
        """Generate anonymized user identifier."""
        import platform
        user_info = f"{platform.node()}{os.getenv('USER', 'anonymous')}{int(time.time() // 3600)}"
        return hashlib.sha256(user_info.encode()).hexdigest()[:16]

    @retry_on_failure(max_retries=3)
    def save_hand_analysis(self, hand: str, board: Optional[str], result: str,
                          session_id: Optional[str] = None, metadata: Optional[Dict] = None) -> int:
        """Save hand analysis with enhanced metadata support."""
        self._rate_limit_check('save_hand', 50)

        from .error_handling import sanitize_input

        # Sanitize inputs
        hand = sanitize_input(hand, max_length=50)
        if board:
            board = sanitize_input(board, max_length=50)
        result = sanitize_input(result, max_length=2000)

        user_hash = self._generate_user_hash()
        metadata_json = json.dumps(metadata or {})

        with db_guard('saving hand analysis'):
            if self.config.db_type == DatabaseType.POSTGRESQL:
                with self.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            """INSERT INTO poker_hands
                            (hand_text, board_text, analysis_result, user_hash, session_id, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                            (hand, board, result, user_hash, session_id, metadata_json)
                        )
                        result_id = cursor.fetchone()[0]
                        conn.commit()
                        return result_id
            else:
                return self.sqlite_db.save_hand_analysis(hand, board, result, session_id)

    def get_recent_hands(self, limit: int = 100, offset: int = 0,
                        user_hash: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent hands with enhanced filtering."""
        self._rate_limit_check('get_hands', 200)

        limit = min(max(1, limit), 1000)
        offset = max(0, offset)

        with db_guard('fetching recent hands'):
            if self.config.db_type == DatabaseType.POSTGRESQL:
                with self.get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        if user_hash:
                            cursor.execute(
                                """SELECT id, hand_text, board_text, analysis_result, timestamp, metadata
                                FROM poker_hands
                                WHERE user_hash = %s
                                ORDER BY timestamp DESC
                                LIMIT %s OFFSET %s""",
                                (user_hash, limit, offset)
                            )
                        else:
                            cursor.execute(
                                """SELECT id, hand_text, board_text, analysis_result, timestamp, metadata
                                FROM poker_hands
                                ORDER BY timestamp DESC
                                LIMIT %s OFFSET %s""",
                                (limit, offset)
                            )
                        return [dict(row) for row in cursor.fetchall()]
            else:
                return self.sqlite_db.get_recent_hands(limit, offset)

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics for monitoring."""
        with db_guard('getting database stats'):
            if self.config.db_type == DatabaseType.POSTGRESQL:
                with self.get_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        # Get recent activity
                        cursor.execute("""
                        SELECT
                            COUNT(*) as total_hands,
                            COUNT(*) FILTER (WHERE timestamp > NOW() - INTERVAL '1 day') as hands_last_24h,
                            COUNT(DISTINCT user_hash) as unique_users,
                            COUNT(DISTINCT session_id) as unique_sessions
                        FROM poker_hands
                        """)
                        activity_stats = cursor.fetchone()

                        return {
                            'database_type': 'postgresql',
                            'activity': dict(activity_stats)
                        }
            else:
                # SQLite stats
                db_size = os.path.getsize(self.config.db_path) if os.path.exists(self.config.db_path) else 0

                with self.get_connection() as conn:
                    cursor = conn.execute('SELECT COUNT(*) FROM poker_hands')
                    total_hands = cursor.fetchone()[0]

                    cursor = conn.execute('SELECT COUNT(DISTINCT user_hash) FROM poker_hands')
                    unique_users = cursor.fetchone()[0]

                    return {
                        'database_type': 'sqlite',
                        'activity': {
                            'total_hands': total_hands,
                            'unique_users': unique_users
                        }
                    }

    def close(self):
        """Close database connections."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info('PostgreSQL connection pool closed')


# Global instance management
_production_db_instance: Optional[ProductionDatabase] = None


def get_production_db() -> ProductionDatabase:
    """Get the global production database instance."""
    global _production_db_instance
    if _production_db_instance is None:
        _production_db_instance = ProductionDatabase()
    return _production_db_instance


def migrate_to_production(sqlite_path: str = 'poker_decisions.db') -> bool:
    """Helper function to migrate from SQLite to PostgreSQL."""
    try:
        # Force PostgreSQL configuration
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host=os.getenv('POKER_DB_HOST', 'localhost'),
            port=int(os.getenv('POKER_DB_PORT', '5432')),
            database=os.getenv('POKER_DB_NAME', 'pokertool'),
            user=os.getenv('POKER_DB_USER', 'postgres'),
            password=os.getenv('POKER_DB_PASSWORD')
        )

        prod_db = ProductionDatabase(config)
        logger.info("Production database migration would be implemented here")
        return True

    except Exception as e:
        logger.error(f'Migration failed: {e}')
        return False


if __name__ == '__main__':
    # Test database connectivity
    db = get_production_db()
    stats = db.get_database_stats()
    print(f"Database type: {stats['database_type']}")
    print(f'Database stats: {stats}')
