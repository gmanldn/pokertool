"""
Enhanced Storage Module
Secure database wrapper with SQL injection prevention and access controls.
"""

__version__ = '21'

import sqlite3
import os
import pathlib
import hashlib
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Iterator
from .error_handling import db_guard, log, sanitize_input, retry_on_failure

__all__ = ['init_db', 'initialise_db_if_needed', 'SecureDatabase', 'get_secure_db']

DEFAULT_DB = 'poker_decisions.db'
MAX_DB_SIZE = 100 * 1024 * 1024  # 100MB limit
BACKUP_RETENTION_DAYS = 30


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


class SecureDatabase:
    """
    Secure database wrapper with SQL injection prevention and access controls.
    """

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = str(db_path or DEFAULT_DB)
        self.max_query_time = 30.0  # seconds
        self.rate_limiter = {}  # Simple rate limiting per operation
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Initialize database schema with proper security constraints."""
        schema = """
        CREATE TABLE IF NOT EXISTS poker_hands (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            hand_text TEXT NOT NULL CHECK(length(hand_text) <= 50), 
            board_text TEXT CHECK(board_text IS NULL OR length(board_text) <= 50), 
            analysis_result TEXT, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
            user_hash TEXT, 
            session_id TEXT, 
            CONSTRAINT valid_hand_format CHECK(hand_text GLOB '[AKQJT2-9][shdc][AKQJT2-9][shdc]' OR
                hand_text GLOB '[AKQJT2-9][shdc][AKQJT2-9][shdc] [AKQJT2-9][shdc][AKQJT2-9][shdc]')
        );

        CREATE TABLE IF NOT EXISTS game_sessions (
            session_id TEXT PRIMARY KEY, 
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP, 
            end_time DATETIME, 
            hands_played INTEGER DEFAULT 0, 
            notes TEXT CHECK(length(notes) <= 1000)
        );

        CREATE TABLE IF NOT EXISTS security_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
            event_type TEXT NOT NULL, 
            details TEXT, 
            severity INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_hands_timestamp ON poker_hands(timestamp);
        CREATE INDEX IF NOT EXISTS idx_sessions_start ON game_sessions(start_time);
        """

        with self._get_connection() as conn:
            conn.executescript(schema)

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Get a secure database connection with proper settings."""
        path = pathlib.Path(self.db_path)

        # Create parent directories securely
        if self.db_path != ':memory:':
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)

        # Check database size limit
            if path.exists() and path.stat().st_size > MAX_DB_SIZE:
                raise SecurityError(f"Database size exceeds limit: {path.stat().st_size} > {MAX_DB_SIZE}")

        conn = sqlite3.connect(
            self.db_path, 
            timeout=self.max_query_time, 
            check_same_thread=False
        )

        # Set security-focused pragmas
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA journal_mode = WAL')
        conn.execute('PRAGMA synchronous = FULL')
        conn.execute('PRAGMA temp_store = MEMORY')
        conn.execute('PRAGMA cache_size = -16384')  # 16MB cache

        try:
            yield conn
        finally:
            conn.close()

    def _rate_limit_check(self, operation: str, limit_per_minute: int = 100) -> None:
        """Check if operation is within rate limits."""
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

    def _log_security_event(self, event_type: str, details: str, severity: int = 1) -> None:
        """Log security events for auditing."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO security_log (event_type, details, severity) VALUES (?, ?, ?)", 
                    (event_type, details, severity)
                )
                conn.commit()
        except Exception as e:
            log.error('Failed to log security event: %s', e)

    @retry_on_failure(max_retries=3)
    def save_hand_analysis(self, hand: str, board: Optional[str], result: str, 
                          session_id: Optional[str] = None) -> int:
        """
        Securely save hand analysis with input validation.

        Returns:
            The ID of the inserted record
        """
        self._rate_limit_check('save_hand', 50)

        # Sanitize inputs
        hand = sanitize_input(hand, max_length=50)
        if board:
            board = sanitize_input(board, max_length=50)
        result = sanitize_input(result, max_length=2000)

        # Validate hand format
        if not self._validate_hand_format(hand):
            raise ValueError(f'Invalid hand format: {hand}')

        if board and not self._validate_board_format(board):
            raise ValueError(f'Invalid board format: {board}')

        user_hash = self._generate_user_hash()

        with db_guard('saving hand analysis'):
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO poker_hands
                    (hand_text, board_text, analysis_result, user_hash, session_id)
                    VALUES (?, ?, ?, ?, ?)""",
                    (hand, board, result, user_hash, session_id)
                )
                conn.commit()
                return cursor.lastrowid

    def get_recent_hands(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent hand analyses with pagination."""
        self._rate_limit_check('get_hands', 200)

        limit = min(max(1, limit), 1000)  # Clamp between 1-1000
        offset = max(0, offset)

        with db_guard('fetching recent hands'):
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """SELECT id, hand_text, board_text, analysis_result, timestamp
                    FROM poker_hands
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?""",
                    (limit, offset)
                )

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def create_session(self, notes: Optional[str] = None) -> str:
        """Create a new game session."""
        session_id = hashlib.sha256(f'{time.time()}{os.urandom(16)}'.encode()).hexdigest()[:16]

        if notes:
            notes = sanitize_input(notes, max_length=1000)

        with db_guard('creating session'):
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO game_sessions (session_id, notes) VALUES (?, ?)",
                    (session_id, notes)
                )
                conn.commit()

        return session_id

    def _validate_hand_format(self, hand: str) -> bool:
        """Validate poker hand format (e.g., 'AsKh' or 'AsKh QdJc')."""
        import re
        # Allow hole cards or hole cards + community cards
        pattern = r'^[AKQJT2-9][shdc][AKQJT2-9][shdc]( [AKQJT2-9][shdc][AKQJT2-9][shdc])*$'
        return bool(re.match(pattern, hand))

    def _validate_board_format(self, board: str) -> bool:
        """Validate board format (flop, turn, river)."""
        import re
        # Allow 3, 4, or 5 cards separated by spaces
        pattern = r'^([AKQJT2-9][shdc] ){2,4}[AKQJT2-9][shdc]$'
        return bool(re.match(pattern, board))

    def _generate_user_hash(self) -> str:
        """Generate anonymized user identifier."""
        # Use system info + time for basic user tracking without PII
        import platform
        user_info = f"{platform.node()}{os.getenv('USER', 'anonymous')}{int(time.time() // 3600)}"
        return hashlib.sha256(user_info.encode()).hexdigest()[:16]

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create a secure backup of the database."""
        if backup_path is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_path = f'{self.db_path}.backup_{timestamp}'

        with db_guard('backing up database'):
            with self._get_connection() as source:
                backup = sqlite3.connect(backup_path)
                source.backup(backup)
                backup.close()

        # Set restrictive permissions on backup file
        os.chmod(backup_path, 0o600)

        self._log_security_event('backup_created', f'Backup created: {backup_path}')
        return backup_path

    def cleanup_old_data(self, days_to_keep: int = BACKUP_RETENTION_DAYS) -> int:
        """Clean up old data beyond retention period."""
        # Calculate cutoff date in the same format as database timestamp
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        cutoff_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cutoff_time))

        with db_guard('cleaning up old data'):
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'DELETE FROM poker_hands WHERE timestamp < ?',
                    (cutoff_datetime,)
                )
                deleted_count = cursor.rowcount
                conn.commit()

                self._log_security_event('data_cleanup', f'Deleted {deleted_count} old records')
                return deleted_count


# Global instance for backward compatibility
_secure_db_instance: Optional[SecureDatabase] = None


def get_secure_db() -> SecureDatabase:
    """Get the global secure database instance."""
    global _secure_db_instance
    if _secure_db_instance is None:
        _secure_db_instance = SecureDatabase()
    return _secure_db_instance


def init_db(db_path: str = DEFAULT_DB) -> str:
    """
    Initialize database with security enhancements.

    Args:
        db_path: Path to the database file

    Returns:
        The normalized database path
    """
    db_path = str(db_path or DEFAULT_DB)
    path = pathlib.Path(db_path)

    if db_path != ':memory:':
        # Create parent directories with secure permissions
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o750)

    # Initialize secure database instance
    secure_db = SecureDatabase(db_path)

    # Test connection
    with secure_db._get_connection() as conn:
        conn.execute('SELECT 1').fetchone()

    log.info('Database initialized successfully: %s', db_path)
    return db_path


def initialise_db_if_needed(db_path: str = DEFAULT_DB) -> str:
    """
    Initialize database if needed (British spelling variant for compatibility).

    Args:
        db_path: Path to the database file

    Returns:
        The normalized database path
    """
    return init_db(db_path)


if __name__ == '__main__':
    if os.environ.get('POKER_AUTOCONFIRM', '1') in {'1', 'True', 'true'}:
        init_db()
    else:
        ans = input('Initialize database now? (y/n): ').strip().lower()
        if ans.startswith('y'):
            init_db()
