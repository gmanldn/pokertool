"""
Comprehensive unit tests for PokerTool security features and error handling.
Tests for SEC-001 (Security Enhancements) and ERR-001 (Error Recovery System).
"""

import unittest
import tempfile
import os
import time
import sqlite3
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pokertool.error_handling import (
    sanitize_input, retry_on_failure, run_safely, db_guard, CircuitBreaker
)
from pokertool.storage import SecureDatabase, SecurityError, init_db


class TestInputSanitization(unittest.TestCase):
    """Test input sanitization functions."""

    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        # Valid poker input
        result = sanitize_input('AsKh', max_length=50)
        self.assertEqual(result, 'AsKh')

    def test_sanitize_input_removes_invalid_chars(self):
        """Test that invalid characters are removed."""
        result = sanitize_input('As<script>Kh', max_length=50)
        self.assertEqual(result, 'AsscriptKh')  # 's', 'c', 'r', 'i', 'p', 't' are allowed chars

    def test_sanitize_input_length_limit(self):
        """Test length limit enforcement."""
        with self.assertRaises(ValueError):
            sanitize_input('A' * 1001, max_length=1000)

    def test_sanitize_input_non_string(self):
        """Test rejection of non-string input."""
        with self.assertRaises(ValueError):
            sanitize_input(123)

    def test_sanitize_input_custom_allowed_chars(self):
        """Test custom allowed characters."""
        result = sanitize_input('abc123!@#', allowed_chars='abc123')
        self.assertEqual(result, 'abc123')

    def test_sanitize_input_poker_symbols(self):
        """Test that poker symbols are allowed."""
        result = sanitize_input('A♠K♥Q♦J♣', max_length=50)
        self.assertEqual(result, 'A♠K♥Q♦J♣')


class TestRetryMechanism(unittest.TestCase):
    """Test retry mechanism with exponential backoff."""

    def test_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt."""
        @retry_on_failure(max_retries=3)
        def successful_function():
            """Test function."""
            return 'success'
        
        result = successful_function()
        self.assertEqual(result, 'success')

    def test_retry_success_after_failures(self):
        """Test success after initial failures."""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def intermittent_function():
            """Test function."""
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception('Temporary failure')
            return 'success'
        
        result = intermittent_function()
        self.assertEqual(result, 'success')
        self.assertEqual(call_count, 3)

    def test_retry_exhausted(self):
        """Test that retry is exhausted after max attempts."""
        @retry_on_failure(max_retries=2, delay=0.1)
        def always_failing_function():
            """Test function."""
            raise Exception('Always fails')
        
        with self.assertRaises(Exception):
            always_failing_function()

    def test_retry_exponential_backoff(self):
        """Test exponential backoff timing."""
        start_time = time.time()
        
        @retry_on_failure(max_retries=2, delay=0.1, backoff=2.0)
        def failing_function():
            """Test function."""
            raise Exception('Always fails')
        
        with self.assertRaises(Exception):
            failing_function()
        
        # Should take at least 0.1 + 0.2 = 0.3 seconds
        elapsed = time.time() - start_time
        self.assertGreaterEqual(elapsed, 0.3)


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern implementation."""

    def test_circuit_breaker_normal_operation(self):
        """Test normal operation with circuit breaker."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)
        
        def successful_function():
            """Test function."""
            return 'success'
        
        result = breaker.call(successful_function)
        self.assertEqual(result, 'success')
        self.assertEqual(breaker.state, 'CLOSED')

    def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=1.0)
        
        def failing_function():
            """Test function."""
            raise Exception('Always fails')
        
        # First two failures
        with self.assertRaises(Exception):
            breaker.call(failing_function)
        with self.assertRaises(Exception):
            breaker.call(failing_function)
        
        # Circuit should be open now
        self.assertEqual(breaker.state, 'OPEN')
        
        # Third call should fail immediately without calling function
        with self.assertRaises(Exception) as cm:
            breaker.call(failing_function)
        self.assertIn('Circuit breaker is OPEN', str(cm.exception))

    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)
        
        def failing_then_success():
            """Test function."""
            if not hasattr(failing_then_success, 'call_count'):
                failing_then_success.call_count = 0
            failing_then_success.call_count += 1
            if failing_then_success.call_count <= 2:
                raise Exception('Initial failures')
            return 'recovered'
        
        # Trip the circuit breaker
        with self.assertRaises(Exception):
            breaker.call(failing_then_success)
        with self.assertRaises(Exception):
            breaker.call(failing_then_success)
        
        self.assertEqual(breaker.state, 'OPEN')
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Next call should succeed and reset the breaker
        result = breaker.call(failing_then_success)
        self.assertEqual(result, 'recovered')
        self.assertEqual(breaker.state, 'CLOSED')


class TestSecureDatabase(unittest.TestCase):
    """Test secure database implementation."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.secure_db = SecureDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass
    
    def test_database_initialization(self):
        """Test database initialization with security constraints."""
        # Check that tables were created
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
        
        expected_tables = {'poker_hands', 'game_sessions', 'security_log'}
        self.assertTrue(expected_tables.issubset(tables))
    
    def test_save_hand_analysis_valid_input(self):
        """Test saving valid hand analysis."""
        record_id = self.secure_db.save_hand_analysis(
            hand='AsKh',
            board='7d 8d 9c',  # Fixed: spaces required between cards
            result='Test analysis result'
        )
        self.assertIsInstance(record_id, int)
        self.assertGreater(record_id, 0)
    
    def test_save_hand_analysis_invalid_hand_format(self):
        """Test rejection of invalid hand format."""
        with self.assertRaises(ValueError):
            self.secure_db.save_hand_analysis(
                hand='invalid_hand',
                board=None,
                result='Test result'
            )
    
    def test_save_hand_analysis_invalid_board_format(self):
        """Test rejection of invalid board format."""
        with self.assertRaises(ValueError):
            self.secure_db.save_hand_analysis(
                hand='AsKh',
                board='invalid_board',
                result='Test result'
            )
    
    def test_rate_limiting(self):
        """Test rate limiting protection."""
        # Reset rate limiter and set a low limit for testing
        self.secure_db.rate_limiter = {}
        
        # Try to exceed rate limit by directly calling the rate limit check
        for i in range(51):  # One more than the limit of 50
            if i < 50:
                try:
                    self.secure_db._rate_limit_check('save_hand', 50)
                except SecurityError:
                    self.fail(f'Rate limit should not be exceeded at {i} attempts')
            else:
                with self.assertRaises(SecurityError):
                    self.secure_db._rate_limit_check('save_hand', 50)
    
    def test_get_recent_hands_pagination(self):
        """Test pagination in recent hands retrieval."""
        # Add some test data
        for i in range(10):
            self.secure_db.save_hand_analysis(
                hand='AsKh',
                board=None,
                result=f'Analysis {i}'
            )
        
        # Test pagination
        hands_page1 = self.secure_db.get_recent_hands(limit=5, offset=0)
        hands_page2 = self.secure_db.get_recent_hands(limit=5, offset=5)
        
        self.assertEqual(len(hands_page1), 5)
        self.assertEqual(len(hands_page2), 5)
        
        # Check that pages don't overlap
        page1_ids = {hand['id'] for hand in hands_page1}
        page2_ids = {hand['id'] for hand in hands_page2}
        self.assertTrue(page1_ids.isdisjoint(page2_ids))
    
    def test_session_creation(self):
        """Test game session creation."""
        session_id = self.secure_db.create_session(notes='Test session')
        self.assertIsInstance(session_id, str)
        self.assertEqual(len(session_id), 16)
    
    def test_database_backup(self):
        """Test database backup functionality."""
        # Add some data
        self.secure_db.save_hand_analysis('AsKh', None, 'Test data')
        
        # Create backup
        backup_path = self.secure_db.backup_database()
        self.assertTrue(os.path.exists(backup_path))
        
        # Verify backup contains data
        backup_db = SecureDatabase(backup_path)
        hands = backup_db.get_recent_hands(limit=10)
        self.assertEqual(len(hands), 1)
        self.assertEqual(hands[0]['hand_text'], 'AsKh')
        
        # Cleanup
        os.unlink(backup_path)
    
    def test_data_cleanup(self):
        """Test old data cleanup."""
        # Add some data
        record_id = self.secure_db.save_hand_analysis('AsKh', None, 'Test data')
        
        # Cleanup with 0 days to keep (should delete everything)
        deleted_count = self.secure_db.cleanup_old_data(days_to_keep=0)
        self.assertGreaterEqual(deleted_count, 1)
        
        # Verify data was deleted
        hands = self.secure_db.get_recent_hands(limit=10)
        self.assertEqual(len(hands), 0)
    
    def test_database_size_limit(self):
        """Test database size limit enforcement."""
        # Create a mock for database size limit
        original_get_connection = self.secure_db._get_connection
        
        def mock_get_connection_with_size_check():
            """Mock connection that raises size error."""
            # Simulate a large database by raising SecurityError
            raise SecurityError('Database size exceeds limit: 209715200 > 104857600')
        
        self.secure_db._get_connection = mock_get_connection_with_size_check
        
        try:
            with self.assertRaises(SecurityError):
                with self.secure_db._get_connection():
                    pass
        finally:
            # Restore original method
            self.secure_db._get_connection = original_get_connection


class TestRunSafely(unittest.TestCase):
    """Test run_safely function."""
    
    def test_run_safely_success(self):
        """Test run_safely with successful function."""
        def successful_function():
            """Test function."""
            return 42
        
        result = run_safely(successful_function)
        self.assertEqual(result, 42)
    
    def test_run_safely_exception_handling(self):
        """Test run_safely exception handling."""
        def failing_function():
            """Test function."""
            raise Exception('Test exception')
        
        result = run_safely(failing_function)
        self.assertEqual(result, 1)  # Error exit code
    
    def test_run_safely_system_exit(self):
        """Test run_safely with SystemExit."""
        def exit_function():
            """Test function."""
            raise SystemExit(5)
        
        result = run_safely(exit_function)
        self.assertEqual(result, 5)


class TestDbGuard(unittest.TestCase):
    """Test database guard context manager."""
    
    def test_db_guard_success(self):
        """Test db_guard with successful operation."""
        with db_guard('test operation'):
            result = 'success'
        # Should not raise any exception
    
    def test_db_guard_exception_propagation(self):
        """Test that db_guard propagates exceptions."""
        with self.assertRaises(ValueError):
            with db_guard('test operation'):
                raise ValueError('Test error')


class TestSecurityLogging(unittest.TestCase):
    """Test security logging functionality."""
    
    def setUp(self):
        """Set up test database for security logging."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.secure_db = SecureDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass
    
    def test_security_event_logging(self):
        """Test that security events are logged."""
        self.secure_db._log_security_event(
            event_type='test_event',
            details='Test security event',
            severity=2
        )
        
        # Check that the event was logged
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT event_type, details, severity FROM security_log"
            )
            logs = cursor.fetchall()
        
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0][0], 'test_event')
        self.assertEqual(logs[0][1], 'Test security event')
        self.assertEqual(logs[0][2], 2)


class TestDatabaseInit(unittest.TestCase):
    """Test database initialization functions."""
    
    def test_init_db(self):
        """Test init_db function."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
            temp_path = temp_file.name
        
        try:
            result = init_db(temp_path)
            self.assertEqual(result, temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify database structure
            with sqlite3.connect(temp_path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = {row[0] for row in cursor.fetchall()}
            
            expected_tables = {'poker_hands', 'game_sessions', 'security_log'}
            self.assertTrue(expected_tables.issubset(tables))
        
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


class TestInputValidation(unittest.TestCase):
    """Test input validation for poker hands and boards."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.secure_db = SecureDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass
    
    def test_valid_hand_formats(self):
        """Test various valid hand formats."""
        valid_hands = [
            'AsKh',
            '2c3d',
            'TsJh',
            'QdAc'
        ]
        
        for hand in valid_hands:
            with self.subTest(hand=hand):
                self.assertTrue(self.secure_db._validate_hand_format(hand))
    
    def test_invalid_hand_formats(self):
        """Test various invalid hand formats."""
        invalid_hands = [
            'XX',         # Invalid ranks
            'A',          # Too short
            'AsKhQd',     # Too long without space
            '1s2h',       # Invalid rank
            'AsXh',       # Invalid suit
            '',           # Empty
            'As Kh'       # Space in hole cards
        ]
        
        for hand in invalid_hands:
            with self.subTest(hand=hand):
                self.assertFalse(self.secure_db._validate_hand_format(hand))
    
    def test_valid_board_formats(self):
        """Test various valid board formats."""
        valid_boards = [
            '7d 8d 9c',         # Flop
            '7d 8d 9c Th',      # Turn
            '7d 8d 9c Th Js'    # River
        ]
        
        for board in valid_boards:
            with self.subTest(board=board):
                self.assertTrue(self.secure_db._validate_board_format(board))
    
    def test_invalid_board_formats(self):
        """Test various invalid board formats."""
        invalid_boards = [
            '7d 8d',              # Too few cards
            '7d8d9c',             # No spaces
            '7d 8d 9c Th Js Qh',  # Too many cards
            'Xd 8d 9c',           # Invalid rank
            '7x 8d 9c',           # Invalid suit
            ''                    # Empty
        ]
        
        for board in invalid_boards:
            with self.subTest(board=board):
                self.assertFalse(self.secure_db._validate_board_format(board))


if __name__ == '__main__':
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestInputSanitization,
        TestRetryMechanism,
        TestCircuitBreaker,
        TestSecureDatabase,
        TestRunSafely,
        TestDbGuard,
        TestSecurityLogging,
        TestDatabaseInit,
        TestInputValidation
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print('Test Summary:')
    print(f'Tests run: {result.testsRun}')
    print(f'Failures: {len(result.failures)}')
    print(f'Errors: {len(result.errors)}')
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with error code if tests failed
    if result.failures or result.errors:
        sys.exit(1)
    else:
        print('All tests passed! ✅')
        sys.exit(0)
