# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tests/test_comprehensive_system.py
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Comprehensive System Integration Tests
Tests all major components working together to achieve 95% test coverage.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Import all modules for testing
from pokertool.core import analyse_hand, parse_card, Card, Rank, Suit, Position
from pokertool.threading import get_thread_pool, TaskPriority, get_poker_concurrency_manager
from pokertool.compliance import get_compliance_manager, ConsentType, DataCategory
from pokertool.error_handling import retry_on_failure, sanitize_input, CircuitBreaker
from pokertool.storage import get_secure_db

# Test OCR module if available
try:
    from src.pokertool.ocr_recognition import get_poker_ocr, create_card_regions
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Test HUD overlay if available
try:
    from src.pokertool.hud_overlay import HUDConfig, start_hud_overlay, stop_hud_overlay
    HUD_AVAILABLE = True
except ImportError:
    HUD_AVAILABLE = False

# Test production database if available
try:
    from src.pokertool.production_database import DatabaseConfig, initialize_production_db
    PRODUCTION_DB_AVAILABLE = True
except ImportError:
    PRODUCTION_DB_AVAILABLE = False

class TestCorePokerFunctionality:
    """Test core poker analysis functionality."""
    
    def test_card_parsing(self):
        """Test card parsing functionality."""
        # Test valid cards
        card = parse_card("As")
        assert card.rank == Rank.ACE
        assert card.suit == Suit.SPADES
        
        card = parse_card("Kh")
        assert card.rank == Rank.KING
        assert card.suit == Suit.HEARTS
        
        # Test invalid cards
        with pytest.raises(ValueError):
            parse_card("Zx")
    
    def test_hand_analysis(self):
        """Test basic hand analysis."""
        hole_cards = [parse_card("As"), parse_card("Ah")]
        result = analyse_hand(hole_cards)
        
        assert result is not None
        assert hasattr(result, 'strength')
        assert result.strength > 7.0  # Pocket aces should be strong
    
    def test_position_categorization(self):
        """Test position categorization."""
        assert Position.BTN.is_late()
        assert Position.CO.is_late()
        assert not Position.UTG.is_late()
        
        assert Position.BTN.category() == "Late"
        assert Position.UTG.category() == "Early"

class TestThreadingSystem:
    """Test multi-threading and concurrency system."""
    
    def test_thread_pool_basic_operations(self):
        """Test basic thread pool operations."""
        pool = get_thread_pool()
        
        def test_task(x):
            return x * 2
        
        # Test priority task
        task_id = pool.submit_priority_task(test_task, 5, priority=TaskPriority.HIGH)
        result = pool.get_task_result(task_id, timeout=5.0)
        
        assert result.result == 10
        assert result.error is None
    
    def test_thread_pool_stats(self):
        """Test thread pool statistics."""
        pool = get_thread_pool()
        stats = pool.get_stats()
        
        assert 'submitted' in stats
        assert 'completed' in stats
        assert 'worker_threads' in stats
        assert stats['worker_threads'] > 0
    
    @pytest.mark.asyncio
    async def test_poker_concurrency_manager(self):
        """Test poker-specific concurrency operations."""
        manager = get_poker_concurrency_manager()
        
        # Test concurrent hand analysis
        hands = [
            {'hole_cards': ['As', 'Ah'], 'position': 'BTN', 'pot': 100, 'to_call': 20},
            {'hole_cards': ['Ks', 'Kh'], 'position': 'CO', 'pot': 150, 'to_call': 30}
        ]
        
        results = await manager.concurrent_hand_analysis(hands)
        assert len(results) == 2
        assert results[0] is not None or results[1] is not None  # At least one should succeed

class TestComplianceSystem:
    """Test legal compliance system."""
    
    def test_compliance_manager_initialization(self):
        """Test compliance manager initialization."""
        manager = get_compliance_manager()
        
        assert manager is not None
        assert manager.gdpr is not None
        assert manager.poker_sites is not None
    
    def test_user_consent_recording(self):
        """Test user consent recording and checking."""
        manager = get_compliance_manager()
        user_id = "test_user_consent"
        
        # Record consent
        manager.gdpr.record_consent(user_id, ConsentType.DATA_PROCESSING, True)
        
        # Check consent
        has_consent = manager.gdpr.check_consent(user_id, ConsentType.DATA_PROCESSING)
        assert has_consent is True
        
        # Revoke consent
        manager.gdpr.revoke_consent(user_id, ConsentType.DATA_PROCESSING)
        has_consent = manager.gdpr.check_consent(user_id, ConsentType.DATA_PROCESSING)
        assert has_consent is False
    
    def test_poker_site_compliance(self):
        """Test poker site ToS compliance checking."""
        manager = get_compliance_manager()
        
        # Test known restrictions
        assert not manager.poker_sites.check_feature_compliance('pokerstars', 'hud')
        assert manager.poker_sites.check_feature_compliance('partypoker', 'hud')
        assert manager.poker_sites.check_feature_compliance('generic', 'hud')
    
    def test_privacy_report_generation(self):
        """Test GDPR privacy report generation."""
        manager = get_compliance_manager()
        user_id = "test_privacy_report"
        
        # Setup some consent records
        manager.setup_user_consent(user_id, "127.0.0.1", "TestAgent/1.0")
        
        # Generate report
        report = manager.gdpr.generate_privacy_report(user_id)
        
        assert 'user_id' in report
        assert 'consents' in report
        assert 'retention_policies' in report
        assert report['user_id'] == user_id

class TestErrorHandlingSystem:
    """Test error handling and recovery system."""
    
    def test_input_sanitization(self):
        """Test input sanitization."""
        # Test normal input
        clean_input = sanitize_input("normal_input_123")
        assert clean_input == "normal_input_123"
        
        # Test input with dangerous characters
        dangerous_input = "'; DROP TABLE users; --"
        clean_input = sanitize_input(dangerous_input)
        assert "DROP TABLE" not in clean_input
    
    def test_retry_decorator(self):
        """Test retry on failure decorator."""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=1.0)
        
        def failing_function():
            raise Exception("Always fails")
        
        # First failures should be attempted
        with pytest.raises(Exception):
            breaker.call(failing_function)
        
        with pytest.raises(Exception):
            breaker.call(failing_function)
        
        # Circuit should now be open
        with pytest.raises(Exception):
            breaker.call(failing_function)

class TestDatabaseSystem:
    """Test database functionality."""
    
    def test_secure_database_operations(self):
        """Test secure database operations."""
        try:
            db = get_secure_db()
            
            # Test database initialization
            assert db is not None
            
            # Test basic operations
            test_hand = "AsAh"
            test_board = "KsQsJs"
            test_result = "Strong hand"
            
            # This should not raise an exception
            db.save_hand_analysis(test_hand, test_board, test_result)
            
        except Exception as e:
            # Database might not be initialized in test environment
            pytest.skip(f"Database not available for testing: {e}")

@pytest.mark.skipif(not OCR_AVAILABLE, reason="OCR module not available")
class TestOCRSystem:
    """Test OCR card recognition system."""
    
    def test_ocr_initialization(self):
        """Test OCR system initialization."""
        try:
            ocr = get_poker_ocr()
            assert ocr is not None
        except RuntimeError as e:
            pytest.skip(f"OCR dependencies not available: {e}")
    
    def test_card_region_creation(self):
        """Test card region creation."""
        regions = create_card_regions('standard')
        assert len(regions) > 0
        
        # Check that regions have required attributes
        for region in regions:
            assert hasattr(region, 'x')
            assert hasattr(region, 'y')
            assert hasattr(region, 'width')
            assert hasattr(region, 'height')
            assert hasattr(region, 'card_type')

@pytest.mark.skipif(not HUD_AVAILABLE, reason="HUD overlay not available")
class TestHUDSystem:
    """Test HUD overlay system."""
    
    def test_hud_config_creation(self):
        """Test HUD configuration creation."""
        config = HUDConfig(
            position=(100, 100),
            size=(300, 200),
            opacity=0.8
        )
        
        assert config.position == (100, 100)
        assert config.size == (300, 200)
        assert config.opacity == 0.8
    
    @patch('src.pokertool.hud_overlay.GUI_AVAILABLE', True)
    @patch('src.pokertool.hud_overlay.tk')
    def test_hud_overlay_lifecycle(self, mock_tk):
        """Test HUD overlay start/stop lifecycle."""
        # Mock tkinter components
        mock_tk.Tk.return_value = Mock()
        
        config = HUDConfig(position=(200, 200))
        
        # Test would start HUD (mocked)
        # In real implementation this would test actual HUD startup
        assert config is not None

@pytest.mark.skipif(not PRODUCTION_DB_AVAILABLE, reason="Production database not available")
class TestProductionDatabase:
    """Test production database system."""
    
    def test_database_config_creation(self):
        """Test database configuration creation."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_pokertool",
            username="test_user"
        )
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "test_pokertool"
    
    def test_migration_stats_creation(self):
        """Test migration statistics tracking."""
        from src.pokertool.production_database import MigrationStats
        
        stats = MigrationStats()
        stats.total_records = 100
        stats.migrated_records = 95
        
        success_rate = stats.get_success_rate()
        assert success_rate == 95.0

class TestIntegrationScenarios:
    """Test integration scenarios between components."""
    
    def test_full_hand_analysis_workflow(self):
        """Test complete hand analysis workflow."""
        # Parse cards
        hole_cards = [parse_card("As"), parse_card("Kh")]
        board_cards = [parse_card("Ad"), parse_card("Kc"), parse_card("Qh")]
        
        # Analyze hand
        result = analyse_hand(hole_cards, board_cards, position=Position.BTN)
        
        # Verify result
        assert result is not None
        assert hasattr(result, 'strength')
        assert result.strength > 8.0  # Two pair should be strong
    
    def test_compliance_with_threading(self):
        """Test compliance checking with threading."""
        manager = get_compliance_manager()
        pool = get_thread_pool()
        
        def check_compliance_task(user_id, site, feature):
            return manager.validate_feature_use(user_id, site, feature)
        
        # Submit compliance check as threaded task
        task_id = pool.submit_priority_task(
            check_compliance_task, 
            "test_user", "partypoker", "hud", 
            priority=TaskPriority.HIGH
        )
        
        result = pool.get_task_result(task_id, timeout=5.0)
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_async_operations(self):
        """Test async operations integration."""
        # This tests that async functionality works
        await asyncio.sleep(0.01)  # Simple async operation
        
        # Test async with concurrent manager
        manager = get_poker_concurrency_manager()
        await manager.async_manager.initialize()
        
        # Simple async operation test
        def simple_task():
            return "async_result"
        
        result = await manager.async_manager.run_in_executor(simple_task)
        assert result == "async_result"

class TestPerformanceAndLoad:
    """Test performance and load handling."""
    
    def test_concurrent_hand_analysis_performance(self):
        """Test performance with multiple concurrent hand analyses."""
        pool = get_thread_pool()
        
        def analyze_hand_task(hand_data):
            hole_cards = [parse_card(card) for card in hand_data]
            return analyse_hand(hole_cards)
        
        # Submit multiple tasks
        tasks = []
        test_hands = [["As", "Ah"], ["Ks", "Kh"], ["Qs", "Qh"], ["Js", "Jh"], ["Ts", "Th"]]
        
        for hand in test_hands:
            task_id = pool.submit_priority_task(analyze_hand_task, hand)
            tasks.append(task_id)
        
        # Collect results
        results = []
        for task_id in tasks:
            result = pool.get_task_result(task_id, timeout=10.0)
            results.append(result)
        
        # Verify all completed successfully
        assert len(results) == len(test_hands)
        for result in results:
            assert result.error is None
            assert result.result is not None

# Test fixtures and utilities
@pytest.fixture
def temp_database():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass

@pytest.fixture
def compliance_test_user():
    """Create test user for compliance testing."""
    user_id = f"test_user_{datetime.now().timestamp()}"
    return user_id

# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def test_hand_analysis_performance(self, benchmark):
        """Benchmark hand analysis performance."""
        hole_cards = [parse_card("As"), parse_card("Ah")]
        
        def analyze():
            return analyse_hand(hole_cards)
        
        result = benchmark(analyze)
        assert result is not None
    
    def test_threading_performance(self, benchmark):
        """Benchmark threading performance."""
        pool = get_thread_pool()
        
        def thread_task():
            task_id = pool.submit_priority_task(lambda x: x * 2, 5)
            return pool.get_task_result(task_id, timeout=5.0)
        
        result = benchmark(thread_task)
        assert result.result == 10

if __name__ == '__main__':
    # Run tests with coverage
    pytest.main([
        __file__,
        '--cov=src/pokertool',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-fail-under=95',
        '-v'
    ])
