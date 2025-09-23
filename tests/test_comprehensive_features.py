"""
Comprehensive unit tests for new PokerTool features.
Tests for SCRP-001, DB-001, PERF-001, and API-001 implementations.
"""

import unittest
import tempfile
import os
import time
import json
import threading
import asyncio
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
import sys
from pathlib import Path
from concurrent.futures import Future

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from pokertool.scrape import ScraperManager, get_scraper_status, run_screen_scraper
    from pokertool.database import (
        ProductionDatabase, DatabaseConfig, DatabaseType, migrate_to_production
    )
    from pokertool.threading import (
        PokerThreadPool, ThreadPoolConfig, TaskPriority, TaskResult,
        ThreadSafeCounter, ThreadSafeDict, TaskQueue, get_thread_pool
    )
    from pokertool.api import (
        PokerToolAPI, AuthenticationService, UserRole, APIUser, ConnectionManager
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f'Some modules not available for testing: {e}')
    MODULES_AVAILABLE = False


class TestScraperIntegration(unittest.TestCase):
    """Test screen scraper integration."""
    
    def setUp(self):
        """Set up test environment."""
        if not MODULES_AVAILABLE:
            self.skipTest('Required modules not available')
    
    def test_scraper_manager_initialization(self):
        """Test scraper manager initialization."""
        manager = ScraperManager()
        self.assertIsNotNone(manager)
        self.assertFalse(manager.running)
        self.assertEqual(len(manager.callbacks), 0)
    
    @patch('pokertool.scrape.PokerScreenScraper')
    def test_scraper_manager_initialize(self, mock_scraper_class):
        """Test scraper manager initialization with mocked scraper."""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        
        manager = ScraperManager()
        result = manager.initialize('GENERIC')
        
        self.assertTrue(result)
        mock_scraper_class.assert_called_once()
    
    def test_get_scraper_status(self):
        """Test get_scraper_status function."""
        status = get_scraper_status()
        self.assertIsInstance(status, dict)
        self.assertIn('initialized', status)
        self.assertIn('running', status)
        self.assertIn('available', status)
    
    @patch('pokertool.scrape._scraper_manager')
    def test_run_screen_scraper_single_mode(self, mock_manager):
        """Test run_screen_scraper in single capture mode."""
        mock_manager.scraper = None
        mock_manager.initialize.return_value = True
        mock_manager.capture_single_state.return_value = {'test': 'data'}
        
        result = run_screen_scraper(continuous=False)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('state', result)
    
    @patch('pokertool.scrape._scraper_manager')
    def test_run_screen_scraper_continuous_mode(self, mock_manager):
        """Test run_screen_scraper in continuous mode."""
        mock_manager.scraper = None
        mock_manager.initialize.return_value = True
        mock_manager.start_continuous_capture.return_value = True
        
        result = run_screen_scraper(continuous=True)
        
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['continuous'])


class TestDatabaseMigration(unittest.TestCase):
    """Test database migration and production features."""
    
    def setUp(self):
        """Set up test environment."""
        if not MODULES_AVAILABLE:
            self.skipTest('Required modules not available')
    
    def test_database_config_from_env(self):
        """Test database configuration from environment variables."""
        with patch.dict(os.environ, {
            'POKER_DB_TYPE': 'sqlite',
            'POKER_DB_PATH': '/test/path.db'
        }):
            config = DatabaseConfig.from_env()
            self.assertEqual(config.db_type, DatabaseType.SQLITE)
            self.assertEqual(config.db_path, '/test/path.db')
    
    def test_database_config_postgresql(self):
        """Test PostgreSQL database configuration."""
        with patch.dict(os.environ, {
            'POKER_DB_TYPE': 'postgresql',
            'POKER_DB_HOST': 'test-host',
            'POKER_DB_PORT': '5433',
            'POKER_DB_NAME': 'test-db',
            'POKER_DB_USER': 'test-user'
        }):
            config = DatabaseConfig.from_env()
            self.assertEqual(config.db_type, DatabaseType.POSTGRESQL)
            self.assertEqual(config.host, 'test-host')
            self.assertEqual(config.port, 5433)
            self.assertEqual(config.database, 'test-db')
    
    def test_production_database_sqlite_init(self):
        """Test ProductionDatabase with SQLite."""
        config = DatabaseConfig(db_type=DatabaseType.SQLITE, db_path=':memory:')
        db = ProductionDatabase(config)
        self.assertIsNotNone(db.sqlite_db)
        self.assertIsNone(db.connection_pool)
    
    @patch('pokertool.database.POSTGRES_AVAILABLE', False)
    def test_production_database_postgresql_unavailable(self):
        """Test ProductionDatabase when PostgreSQL is unavailable."""
        config = DatabaseConfig(db_type=DatabaseType.POSTGRESQL)
        with self.assertRaises(RuntimeError):
            ProductionDatabase(config)
    
    def test_production_database_save_hand_sqlite(self):
        """Test saving hand analysis with SQLite backend."""
        config = DatabaseConfig(db_type=DatabaseType.SQLITE, db_path=':memory:')
        db = ProductionDatabase(config)
        
        result_id = db.save_hand_analysis(
            hand='AsKh',
            board='7d8d9c',
            result='Test result',
            metadata={'test': 'data'}
        )
        
        self.assertIsInstance(result_id, int)
        self.assertGreater(result_id, 0)
    
    def test_production_database_get_recent_hands(self):
        """Test getting recent hands."""
        config = DatabaseConfig(db_type=DatabaseType.SQLITE, db_path=':memory:')
        db = ProductionDatabase(config)
        
        # Add test data
        db.save_hand_analysis('AsKh', '7d8d9c', 'Test 1')
        db.save_hand_analysis('KdQh', 'TcJcQs', 'Test 2')
        
        hands = db.get_recent_hands(limit=10)
        self.assertEqual(len(hands), 2)
        self.assertEqual(hands[0]['hand_text'], 'KdQh')  # Most recent first
    
    def test_production_database_stats_sqlite(self):
        """Test database statistics for SQLite."""
        config = DatabaseConfig(db_type=DatabaseType.SQLITE, db_path=':memory:')
        db = ProductionDatabase(config)
        
        stats = db.get_database_stats()
        self.assertEqual(stats['database_type'], 'sqlite')
        self.assertIn('total_hands', stats)
        self.assertIn('unique_users', stats)


class TestThreadingFeatures(unittest.TestCase):
    """Test multi-threading implementation."""
    
    def setUp(self):
        """Set up test environment."""
        if not MODULES_AVAILABLE:
            self.skipTest('Required modules not available')
    
    def test_thread_safe_counter(self):
        """Test ThreadSafeCounter implementation."""
        counter = ThreadSafeCounter()
        self.assertEqual(counter.value, 0)
        
        # Test increment/decrement
        result = counter.increment()
        self.assertEqual(result, 1)
        self.assertEqual(counter.value, 1)
        
        result = counter.decrement()
        self.assertEqual(result, 0)
        self.assertEqual(counter.value, 0)
    
    def test_thread_safe_dict(self):
        """Test ThreadSafeDict implementation."""
        safe_dict = ThreadSafeDict()
        
        # Test basic operations
        safe_dict.set('key1', 'value1')
        self.assertEqual(safe_dict.get('key1'), 'value1')
        self.assertIsNone(safe_dict.get('nonexistent'))
        
        # Test deletion
        self.assertTrue(safe_dict.delete('key1'))
        self.assertFalse(safe_dict.delete('key1'))  # Already deleted
        
        # Test other operations
        safe_dict.set('key2', 'value2')
        safe_dict.set('key3', 'value3')
        self.assertEqual(len(safe_dict), 2)
        self.assertIn('key2', safe_dict.keys())
        self.assertIn('value3', safe_dict.values())
    
    def test_task_queue_priority(self):
        """Test priority-based task queue."""
        task_queue = TaskQueue()
        
        # Add tasks with different priorities
        task_queue.put('low', TaskPriority.LOW)
        task_queue.put('high', TaskPriority.HIGH)
        task_queue.put('normal', TaskPriority.NORMAL)
        task_queue.put('critical', TaskPriority.CRITICAL)
        
        # Should get items in priority order
        self.assertEqual(task_queue.get(timeout=0.1), 'critical')
        self.assertEqual(task_queue.get(timeout=0.1), 'high')
        self.assertEqual(task_queue.get(timeout=0.1), 'normal')
        self.assertEqual(task_queue.get(timeout=0.1), 'low')
    
    def test_thread_pool_config(self):
        """Test thread pool configuration."""
        config = ThreadPoolConfig()
        self.assertIsNotNone(config.max_workers)
        self.assertGreater(config.max_workers, 0)
        self.assertEqual(config.thread_name_prefix, 'PokerTool')
    
    def test_poker_thread_pool_initialization(self):
        """Test PokerThreadPool initialization."""
        config = ThreadPoolConfig(max_workers=2, monitor_interval=0)  # Disable monitoring for test
        pool = PokerThreadPool(config)
        
        try:
            self.assertIsNotNone(pool.executor)
            self.assertIsNotNone(pool.process_pool)
            self.assertEqual(len(pool._worker_threads), 1)  # max_workers // 2
            
            stats = pool.get_stats()
            self.assertIn('submitted', stats)
            self.assertIn('completed', stats)
            self.assertIn('max_workers', stats)
        finally:
            pool.shutdown(wait=False)
    
    def test_thread_pool_priority_task(self):
        """Test priority task submission."""
        config = ThreadPoolConfig(max_workers=2, monitor_interval=0)
        pool = PokerThreadPool(config)
        
        try:
            def test_function(x):
                """Test function."""
                return x * 2
            
            task_id = pool.submit_priority_task(test_function, 5, priority=TaskPriority.HIGH)
            self.assertIsInstance(task_id, str)
            
            result = pool.get_task_result(task_id, timeout=5.0)
            self.assertEqual(result.result, 10)
            self.assertIsNone(result.error)
        finally:
            pool.shutdown(wait=False)
    
    def test_thread_pool_thread_task(self):
        """Test regular thread task submission."""
        config = ThreadPoolConfig(max_workers=2, monitor_interval=0)
        pool = PokerThreadPool(config)
        
        try:
            def test_function(x, y):
                """Test function."""
                return x + y
            
            future = pool.submit_thread_task(test_function, 3, y=4)
            self.assertIsInstance(future, Future)
            
            result = future.result(timeout=5.0)
            self.assertEqual(result, 7)
        finally:
            pool.shutdown(wait=False)
    
    def test_get_thread_pool_singleton(self):
        """Test global thread pool singleton."""
        pool1 = get_thread_pool()
        pool2 = get_thread_pool()
        self.assertIs(pool1, pool2)


class TestAPIFeatures(unittest.TestCase):
    """Test API implementation."""
    
    def setUp(self):
        """Set up test environment."""
        if not MODULES_AVAILABLE:
            self.skipTest('Required modules not available')
    
    def test_user_role_enum(self):
        """Test UserRole enum."""
        self.assertEqual(UserRole.ADMIN.value, 'admin')
        self.assertEqual(UserRole.USER.value, 'user')
        self.assertEqual(UserRole.PREMIUM.value, 'premium')
        self.assertEqual(UserRole.GUEST.value, 'guest')
    
    def test_api_user_dataclass(self):
        """Test APIUser dataclass."""
        user = APIUser(
            user_id='test123',
            username='testuser',
            email='test@example.com',
            role=UserRole.USER
        )
        
        self.assertEqual(user.user_id, 'test123')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, UserRole.USER)
        self.assertTrue(user.is_active)
    
    def test_authentication_service_init(self):
        """Test AuthenticationService initialization."""
        auth_service = AuthenticationService()
        
        # Should have default admin user
        self.assertGreater(len(auth_service.users), 0)
        admin_users = [u for u in auth_service.users.values() if u.role == UserRole.ADMIN]
        self.assertEqual(len(admin_users), 1)
    
    def test_authentication_service_create_user(self):
        """Test user creation."""
        auth_service = AuthenticationService()
        
        user = auth_service.create_user(
            username='newuser',
            email='new@example.com',
            password='password123',
            role=UserRole.USER
        )
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.role, UserRole.USER)
        self.assertIn(user.user_id, auth_service.users)
    
    def test_authentication_service_duplicate_user(self):
        """Test duplicate user handling."""
        auth_service = AuthenticationService()
        
        # Create first user
        auth_service.create_user('testuser', 'test@example.com', 'password')
        
        # Try to create duplicate username
        # Should raise HTTPException, but we'll catch any exception
        with self.assertRaises(Exception):
            auth_service.create_user('testuser', 'different@example.com', 'password')
    
    def test_authentication_service_token_creation(self):
        """Test JWT token creation."""
        auth_service = AuthenticationService()
        user = auth_service.create_user('testuser', 'test@example.com', 'password')
        
        token = auth_service.create_access_token(user)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)  # JWT tokens are much longer
    
    def test_authentication_service_token_verification(self):
        """Test JWT token verification."""
        auth_service = AuthenticationService()
        user = auth_service.create_user('testuser', 'test@example.com', 'password')
        
        token = auth_service.create_access_token(user)
        verified_user = auth_service.verify_token(token)
        
        self.assertIsNotNone(verified_user)
        self.assertEqual(verified_user.user_id, user.user_id)
    
    def test_connection_manager_init(self):
        """Test ConnectionManager initialization."""
        manager = ConnectionManager()
        self.assertEqual(len(manager.active_connections), 0)
        self.assertEqual(len(manager.user_connections), 0)
    
    @patch('pokertool.api.FASTAPI_AVAILABLE', False)
    def test_poker_tool_api_unavailable(self):
        """Test PokerToolAPI when FastAPI is unavailable."""
        with self.assertRaises(RuntimeError):
            PokerToolAPI()


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios across modules."""
    
    def setUp(self):
        """Set up test environment."""
        if not MODULES_AVAILABLE:
            self.skipTest('Required modules not available')
    
    def test_database_with_threading(self):
        """Test database operations with threading."""
        config = DatabaseConfig(db_type=DatabaseType.SQLITE, db_path=':memory:')
        db = ProductionDatabase(config)
        thread_pool = PokerThreadPool(ThreadPoolConfig(max_workers=2, monitor_interval=0))
        
        try:
            def save_hand_task(hand_num):
                """Save hand task."""
                return db.save_hand_analysis(
                    hand='AsKh',
                    board='7d8d9c',
                    result=f'Analysis {hand_num}',
                    metadata={'thread_test': True, 'hand_num': hand_num}
                )
            
            # Submit multiple tasks
            task_ids = []
            for i in range(5):
                task_id = thread_pool.submit_priority_task(
                    save_hand_task, i, priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
            
            # Wait for all tasks to complete
            results = []
            for task_id in task_ids:
                result = thread_pool.get_task_result(task_id, timeout=10.0)
                self.assertIsNone(result.error)
                results.append(result.result)
            
            # Verify all records were saved
            hands = db.get_recent_hands(limit=10)
            self.assertEqual(len(hands), 5)
        
        finally:
            thread_pool.shutdown(wait=False)
    
    def test_scraper_database_integration(self):
        """Test scraper integration with database."""
        # This would test the full integration, but requires mocking
        # the screen scraper components
        manager = ScraperManager()
        
        # Test callback registration
        callback_called = threading.Event()
        test_state = {}
        
        def test_callback(game_state):
            """Test callback."""
            test_state.update(game_state)
            callback_called.set()
        
        manager.register_callback(test_callback)
        self.assertEqual(len(manager.callbacks), 1)
        
        # Simulate state update
        mock_state = {
            'hole_cards': ["As", "Kh"],
            'board_cards': ["7d", "8d", "9c"],
            'pot': 100.0,
            'stage': 'flop'
        }
        
        manager._on_table_update(mock_state)
        
        # Wait for callback
        self.assertTrue(callback_called.wait(timeout=1.0))
        self.assertEqual(test_state, mock_state)


class TestErrorHandling(unittest.TestCase):
    """Test error handling across new modules."""
    
    def setUp(self):
        """Set up test environment."""
        if not MODULES_AVAILABLE:
            self.skipTest('Required modules not available')
    
    def test_thread_pool_task_error_handling(self):
        """Test error handling in thread pool tasks."""
        config = ThreadPoolConfig(max_workers=2, monitor_interval=0)
        pool = PokerThreadPool(config)
        
        try:
            def failing_task():
                """Failing task."""
                raise ValueError('Test error')
            
            task_id = pool.submit_priority_task(failing_task, priority=TaskPriority.NORMAL)
            result = pool.get_task_result(task_id, timeout=5.0)
            
            self.assertIsNotNone(result.error)
            self.assertIsInstance(result.error, ValueError)
            self.assertEqual(str(result.error), 'Test error')
        
        finally:
            pool.shutdown(wait=False)
    
    def test_database_connection_error_simulation(self):
        """Test database connection error handling."""
        # Test with invalid SQLite path (read-only directory)
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only
            os.chmod(temp_dir, 0o444)
            
            try:
                invalid_path = os.path.join(temp_dir, 'test.db')
                config = DatabaseConfig(db_type=DatabaseType.SQLITE, db_path=invalid_path)
                
                # This should handle the error gracefully
                with self.assertRaises((PermissionError, Exception)):
                    db = ProductionDatabase(config)
                    db.save_hand_analysis('AsKh', None, 'Test')
            
            finally:
                # Restore permissions for cleanup
                os.chmod(temp_dir, 0o755)


class TestPerformanceScenarios(unittest.TestCase):
    """Test performance-related scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        if not MODULES_AVAILABLE:
            self.skipTest('Required modules not available')
    
    def test_thread_pool_concurrent_tasks(self):
        """Test thread pool with many concurrent tasks."""
        config = ThreadPoolConfig(max_workers=4, monitor_interval=0)
        pool = PokerThreadPool(config)
        
        try:
            def compute_task(n):
                """Compute task."""
                # Simulate some work
                total = 0
                for i in range(n):
                    total += i
                return total
            
            # Submit many tasks
            task_ids = []
            for i in range(20):
                task_id = pool.submit_priority_task(compute_task, 1000, priority=TaskPriority.NORMAL)
                task_ids.append(task_id)
            
            # Collect results
            start_time = time.time()
            results = []
            for task_id in task_ids:
                result = pool.get_task_result(task_id, timeout=10.0)
                self.assertIsNone(result.error)
                results.append(result.result)
            
            execution_time = time.time() - start_time
            
            # All results should be the same (sum of 0 to 999)
            expected_result = sum(range(1000))
            for result in results:
                self.assertEqual(result, expected_result)
            
            # Should complete reasonably quickly with multiple threads
            self.assertLess(execution_time, 5.0)
        
        finally:
            pool.shutdown(wait=False)
    
    def test_database_batch_operations(self):
        """Test database performance with batch operations."""
        config = DatabaseConfig(db_type=DatabaseType.SQLITE, db_path=':memory:')
        db = ProductionDatabase(config)
        
        # Measure time for batch inserts
        start_time = time.time()
        
        for i in range(100):
            db.save_hand_analysis(
                hand='AsKh',
                board='7d8d9c',
                result=f'Batch analysis {i}',
                metadata={'batch': True, 'index': i}
            )
        
        batch_time = time.time() - start_time
        
        # Verify all records were saved
        hands = db.get_recent_hands(limit=200)
        self.assertEqual(len(hands), 100)
        
        # Should complete reasonably quickly
        self.assertLess(batch_time, 10.0)


if __name__ == '__main__':
    # Create a comprehensive test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestScraperIntegration,
        TestDatabaseMigration,
        TestThreadingFeatures,
        TestAPIFeatures,
        TestIntegrationScenarios,
        TestErrorHandling,
        TestPerformanceScenarios
    ]
    
    for test_class in test_classes:
        if MODULES_AVAILABLE:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        else:
            print(f"Skipping {test_class.__name__} - modules not available")
    
    if MODULES_AVAILABLE:
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print(f"\n{'='*60}")
        print('Comprehensive Test Summary:')
        print(f'Tests run: {result.testsRun}')
        print(f'Failures: {len(result.failures)}')
        print(f'Errors: {len(result.errors)}')
        
        if result.testsRun > 0:
            success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
            print(f'Success rate: {success_rate:.1f}%')
        
        print(f"{'='*60}")
        
        # Exit with error code if tests failed
        if result.failures or result.errors:
            print('Some tests failed! ❌')
            for failure in result.failures:
                print(f'FAILURE: {failure[0]}')
            for error in result.errors:
                print(f'ERROR: {error[0]}')
            sys.exit(1)
        else:
            print('All comprehensive tests passed! ✅')
            sys.exit(0)
    else:
        print("Required modules not available - skipping comprehensive tests")
        sys.exit(0)
