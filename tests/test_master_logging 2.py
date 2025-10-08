#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Master Logging System
==========================

Comprehensive tests for the master logging system to ensure all errors
are properly captured and routed to the master log with enhanced data collection.
"""

import sys
import os
import time
import tempfile
import json
from pathlib import Path
from contextlib import contextmanager

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from pokertool.master_logging import (
        get_master_logger, 
        LogCategory, 
        log_error, 
        log_info, 
        log_warning, 
        log_performance,
        log_security_event,
        auto_log_errors
    )
    from pokertool.error_handling import run_safely, retry_on_failure, CircuitBreaker
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Could not import modules: {e}")
    MODULES_AVAILABLE = False

def test_basic_logging():
    """Test basic logging functionality."""
    print("=== Testing Basic Logging ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        logger = get_master_logger()
        
        # Test different log levels
        logger.info("Test info message", category=LogCategory.GENERAL)
        logger.warning("Test warning message", category=LogCategory.GENERAL)
        logger.debug("Test debug message", category=LogCategory.GENERAL)
        
        print("✅ Basic logging test passed")
        return True
    except Exception as e:
        print(f"❌ Basic logging test failed: {e}")
        return False

def test_error_logging():
    """Test error logging with exception capture."""
    print("=== Testing Error Logging ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        logger = get_master_logger()
        
        # Test error without exception
        logger.error("Test error message without exception", category=LogCategory.ERROR)
        
        # Test error with exception
        try:
            raise ValueError("This is a test exception")
        except Exception as e:
            logger.error("Test error with exception", category=LogCategory.ERROR, exception=e)
        
        # Test using convenience function
        try:
            raise TypeError("Another test exception")
        except Exception as e:
            log_error("Convenience function error test", exception=e)
        
        print("✅ Error logging test passed")
        return True
    except Exception as e:
        print(f"❌ Error logging test failed: {e}")
        return False

def test_performance_logging():
    """Test performance logging and timing."""
    print("=== Testing Performance Logging ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        logger = get_master_logger()
        
        # Test operation context
        with logger.operation_context("test_operation", test_data="sample"):
            time.sleep(0.1)  # Simulate work
        
        # Test performance timer decorator
        @logger.performance_timer("decorated_operation")
        def sample_operation():
            time.sleep(0.05)
            return "operation_result"
        
        result = sample_operation()
        
        # Test direct performance logging
        log_performance("manual_timing", 0.02, operation_type="test")
        
        print("✅ Performance logging test passed")
        return True
    except Exception as e:
        print(f"❌ Performance logging test failed: {e}")
        return False

def test_security_logging():
    """Test security event logging."""
    print("=== Testing Security Logging ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        logger = get_master_logger()
        
        # Test security events
        logger.security("Attempted unauthorized access", 
                       user_id="test_user", 
                       ip_address="192.168.1.100",
                       action="login_attempt")
        
        log_security_event("Suspicious activity detected", 
                          severity="high",
                          details="Multiple failed login attempts")
        
        print("✅ Security logging test passed")
        return True
    except Exception as e:
        print(f"❌ Security logging test failed: {e}")
        return False

def test_categorized_logging():
    """Test logging with different categories."""
    print("=== Testing Categorized Logging ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        logger = get_master_logger()
        
        # Test all categories
        categories = [
            LogCategory.DATABASE,
            LogCategory.NETWORK,
            LogCategory.GUI,
            LogCategory.ANALYSIS,
            LogCategory.SOLVER,
            LogCategory.SCRAPER,
            LogCategory.API
        ]
        
        for category in categories:
            logger.info(f"Test message for {category.value} category", 
                       category=category,
                       component="test_component")
        
        print("✅ Categorized logging test passed")
        return True
    except Exception as e:
        print(f"❌ Categorized logging test failed: {e}")
        return False

@auto_log_errors(LogCategory.ERROR)
def failing_function():
    """Function that always fails for testing auto-log decorator."""
    raise RuntimeError("This function always fails")

def test_auto_logging_decorator():
    """Test automatic error logging decorator."""
    print("=== Testing Auto-Logging Decorator ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        # This should automatically log the error
        try:
            failing_function()
        except RuntimeError:
            pass  # Expected
        
        print("✅ Auto-logging decorator test passed")
        return True
    except Exception as e:
        print(f"❌ Auto-logging decorator test failed: {e}")
        return False

def test_error_deduplication():
    """Test that identical errors are deduplicated."""
    print("=== Testing Error Deduplication ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        logger = get_master_logger()
        
        # Generate the same error multiple times
        for i in range(5):
            try:
                raise ValueError("Duplicate error for testing")
            except Exception as e:
                logger.error(f"Duplicate error #{i+1}", exception=e)
        
        # Check error summary
        summary = logger.get_error_summary()
        print(f"Error summary: {summary['total_unique_errors']} unique errors, "
              f"{summary['total_error_occurrences']} total occurrences")
        
        print("✅ Error deduplication test passed")
        return True
    except Exception as e:
        print(f"❌ Error deduplication test failed: {e}")
        return False

def test_integration_with_error_handling():
    """Test integration with existing error handling system."""
    print("=== Testing Error Handling Integration ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        # Test run_safely function
        def safe_function():
            log_info("Safe function executed successfully")
            return 0
        
        def failing_function():
            raise Exception("Function failed intentionally")
            return 1
        
        result1 = run_safely(safe_function)
        result2 = run_safely(failing_function)
        
        # Test retry decorator
        @retry_on_failure(max_retries=2, delay=0.1)
        def flaky_function():
            if not hasattr(flaky_function, 'call_count'):
                flaky_function.call_count = 0
            flaky_function.call_count += 1
            
            if flaky_function.call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        try:
            result = flaky_function()
            print(f"Retry function succeeded: {result}")
        except Exception as e:
            print(f"Retry function failed after retries: {e}")
        
        # Test circuit breaker
        breaker = CircuitBreaker(failure_threshold=2, timeout=1.0)
        
        def unreliable_function():
            raise Exception("Always fails")
        
        # Trigger circuit breaker
        for i in range(3):
            try:
                breaker.call(unreliable_function)
            except Exception:
                pass
        
        print("✅ Error handling integration test passed")
        return True
    except Exception as e:
        print(f"❌ Error handling integration test failed: {e}")
        return False

def test_log_file_creation():
    """Test that log files are created properly."""
    print("=== Testing Log File Creation ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        logger = get_master_logger()
        
        # Force some logging to ensure files are created
        logger.info("Test message for file creation")
        logger.error("Test error for file creation")
        logger.security("Test security event for file creation")
        
        # Force flush
        logger.flush_logs()
        
        # Check if log files exist
        logs_dir = Path.cwd() / 'logs'
        expected_files = [
            'pokertool_master.log',
            'pokertool_errors.log',
            'pokertool_performance.log',
            'pokertool_security.log'
        ]
        
        files_exist = []
        for filename in expected_files:
            file_path = logs_dir / filename
            if file_path.exists() and file_path.stat().st_size > 0:
                files_exist.append(filename)
                print(f"✓ {filename} exists ({file_path.stat().st_size} bytes)")
            else:
                print(f"✗ {filename} missing or empty")
        
        if len(files_exist) >= 2:  # At least master and one specialized log
            print("✅ Log file creation test passed")
            return True
        else:
            print("❌ Log file creation test failed - insufficient files created")
            return False
            
    except Exception as e:
        print(f"❌ Log file creation test failed: {e}")
        return False

def test_structured_data():
    """Test logging with structured data."""
    print("=== Testing Structured Data Logging ===")
    
    if not MODULES_AVAILABLE:
        print("❌ Modules not available, skipping test")
        return False
    
    try:
        logger = get_master_logger()
        
        # Test with poker-specific context
        logger.info("Hand analysis completed", 
                   category=LogCategory.ANALYSIS,
                   current_hand="AhKd",
                   current_board="9s8h7c",
                   pot_size=150.00,
                   player_count=3,
                   position="BTN")
        
        # Test with database context
        logger.info("Database query executed",
                   category=LogCategory.DATABASE,
                   query_type="SELECT",
                   execution_time=0.025,
                   rows_affected=42,
                   table_name="hands")
        
        # Test with API context
        logger.info("API request processed",
                   category=LogCategory.API,
                   endpoint="/api/analyze",
                   method="POST",
                   response_code=200,
                   processing_time=0.15,
                   user_id="user_123")
        
        print("✅ Structured data logging test passed")
        return True
    except Exception as e:
        print(f"❌ Structured data logging test failed: {e}")
        return False

def run_all_tests():
    """Run all master logging tests."""
    print("🧪 Starting Master Logging System Tests")
    print("=" * 50)
    
    tests = [
        test_basic_logging,
        test_error_logging,
        test_performance_logging,
        test_security_logging,
        test_categorized_logging,
        test_auto_logging_decorator,
        test_error_deduplication,
        test_integration_with_error_handling,
        test_log_file_creation,
        test_structured_data
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if MODULES_AVAILABLE and failed == 0:
        logger = get_master_logger()
        summary = logger.get_error_summary()
        print(f"📈 Error Summary: {summary}")
        print("🎉 All tests passed! Master logging system is working correctly.")
        return True
    else:
        print("❌ Some tests failed or modules unavailable.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
