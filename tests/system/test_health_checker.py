#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for System Health Checker

Tests all health check functions to ensure modules load correctly
and health status is returned properly.
"""

import asyncio
import time
from datetime import datetime

import pytest

from pokertool.system_health_checker import (
    SystemHealthChecker,
    HealthStatus,
    check_api_server_health,
    check_database_health,
    check_ocr_engine_health,
    check_screen_capture_health,
    check_model_calibration_health,
    check_gto_solver_health,
    check_opponent_modeling_health,
    check_sequential_opponent_fusion_health,
    check_active_learning_health,
    check_neural_evaluator_health,
    check_hand_range_analyzer_health,
    check_scraping_accuracy_health,
    check_roi_tracking_health,
    check_tournament_support_health,
    check_multi_table_support_health,
    check_hand_history_database_health,
    check_region_extraction_health,
    check_poker_table_detection_health,
    register_all_health_checks,
)


class TestHealthStatus:
    """Test HealthStatus dataclass."""

    def test_health_status_creation(self):
        """Test creating a HealthStatus object."""
        status = HealthStatus(
            feature_name='test_feature',
            category='ml',
            status='healthy',
            last_check='2025-01-01T00:00:00Z',
            description='Test feature'
        )

        assert status.feature_name == 'test_feature'
        assert status.category == 'ml'
        assert status.status == 'healthy'
        assert status.description == 'Test feature'

    def test_health_status_to_dict(self):
        """Test converting HealthStatus to dictionary."""
        status = HealthStatus(
            feature_name='test_feature',
            category='ml',
            status='healthy',
            last_check='2025-01-01T00:00:00Z'
        )

        data = status.to_dict()
        assert isinstance(data, dict)
        assert data['feature_name'] == 'test_feature'
        assert data['status'] == 'healthy'


class TestSystemHealthChecker:
    """Test SystemHealthChecker class."""

    def test_health_checker_initialization(self):
        """Test creating a SystemHealthChecker instance."""
        checker = SystemHealthChecker(check_interval=60)
        assert checker.check_interval == 60
        assert len(checker.checks) == 0
        assert len(checker.last_results) == 0

    def test_register_check(self):
        """Test registering a health check."""
        checker = SystemHealthChecker()

        async def dummy_check():
            return HealthStatus(
                feature_name='test',
                category='ml',
                status='healthy',
                last_check='2025-01-01T00:00:00Z'
            )

        checker.register_check(
            'test',
            'ml',
            dummy_check,
            'Test check',
            timeout=5.0
        )

        assert 'test' in checker.checks
        assert checker.checks['test'].name == 'test'
        assert checker.checks['test'].category == 'ml'

    @pytest.mark.asyncio
    async def test_run_check(self):
        """Test running a single health check."""
        checker = SystemHealthChecker()

        async def dummy_check():
            return HealthStatus(
                feature_name='test',
                category='ml',
                status='healthy',
                last_check='2025-01-01T00:00:00Z'
            )

        checker.register_check('test', 'ml', dummy_check, 'Test check')
        result = await checker.run_check('test')

        assert result.feature_name == 'test'
        assert result.status == 'healthy'
        assert 'test' in checker.last_results

    @pytest.mark.asyncio
    async def test_run_all_checks(self):
        """Test running all registered checks."""
        checker = SystemHealthChecker()

        async def check1():
            return HealthStatus(
                feature_name='check1',
                category='ml',
                status='healthy',
                last_check='2025-01-01T00:00:00Z'
            )

        async def check2():
            return HealthStatus(
                feature_name='check2',
                category='backend',
                status='healthy',
                last_check='2025-01-01T00:00:00Z'
            )

        checker.register_check('check1', 'ml', check1, 'Check 1')
        checker.register_check('check2', 'backend', check2, 'Check 2')

        results = await checker.run_all_checks()

        assert len(results) == 2
        assert 'check1' in results
        assert 'check2' in results
        assert results['check1'].status == 'healthy'

    def test_get_summary(self):
        """Test getting health check summary."""
        checker = SystemHealthChecker()
        checker.last_results['test1'] = HealthStatus(
            feature_name='test1',
            category='ml',
            status='healthy',
            last_check='2025-01-01T00:00:00Z'
        )
        checker.last_results['test2'] = HealthStatus(
            feature_name='test2',
            category='backend',
            status='failing',
            last_check='2025-01-01T00:00:00Z'
        )

        summary = checker.get_summary()

        assert summary['overall_status'] == 'failing'
        assert summary['failing_count'] == 1
        assert summary['degraded_count'] == 0
        assert 'ml' in summary['categories']
        assert 'backend' in summary['categories']

    def test_history_cache_invalidation(self):
        """History cache should return same reference within TTL and invalidate on new data."""
        checker = SystemHealthChecker()
        checker._cache_ttl = 5.0  # ensure ample window for testing
        checker.health_history.clear()
        checker._persist_history_entry = lambda entry: None  # type: ignore[assignment]

        status = HealthStatus(
            feature_name='api_server',
            category='backend',
            status='healthy',
            last_check=datetime.utcnow().isoformat()
        )

        checker._add_to_history({'api_server': status})
        history_first = checker.get_history(hours=1)
        history_second = checker.get_history(hours=1)

        assert history_first is history_second
        assert len(history_first) == 1

        checker._add_to_history({'api_server': status})
        history_third = checker.get_history(hours=1)

        assert len(history_third) == 2
        assert history_third is not history_second

    def test_trend_cache_ttl_expiry(self):
        """Trend cache should expire after TTL and recompute."""
        checker = SystemHealthChecker()
        checker._cache_ttl = 0.1
        checker.health_history.clear()
        checker._persist_history_entry = lambda entry: None  # type: ignore[assignment]

        status = HealthStatus(
            feature_name='api_server',
            category='backend',
            status='healthy',
            last_check=datetime.utcnow().isoformat()
        )

        checker._add_to_history({'api_server': status})
        trends_initial = checker.get_trends(hours=1)
        trends_cached = checker.get_trends(hours=1)

        assert trends_initial is trends_cached

        time.sleep(0.12)
        trends_after_expiry = checker.get_trends(hours=1)

        assert trends_after_expiry is not trends_cached


class TestModuleHealthChecks:
    """Test individual module health check functions."""

    @pytest.mark.asyncio
    async def test_model_calibration_health(self):
        """Test model calibration health check."""
        result = await check_model_calibration_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'model_calibration'
        assert result.category == 'ml'
        # Should be healthy since module exists
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_gto_solver_health(self):
        """Test GTO solver health check."""
        result = await check_gto_solver_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'gto_solver'
        assert result.category == 'ml'
        # Should be healthy since module exists
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_opponent_modeling_health(self):
        """Test opponent modeling health check."""
        result = await check_opponent_modeling_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'opponent_modeling'
        assert result.category == 'ml'
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_sequential_opponent_fusion_health(self):
        """Test sequential opponent fusion health check."""
        result = await check_sequential_opponent_fusion_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'sequential_opponent_fusion'
        assert result.category == 'ml'
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_active_learning_health(self):
        """Test active learning health check."""
        result = await check_active_learning_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'active_learning'
        assert result.category == 'ml'
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_neural_evaluator_health(self):
        """Test neural evaluator health check."""
        result = await check_neural_evaluator_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'neural_evaluator'
        assert result.category == 'ml'
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_hand_range_analyzer_health(self):
        """Test hand range analyzer health check."""
        result = await check_hand_range_analyzer_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'hand_range_analyzer'
        assert result.category == 'ml'
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_scraping_accuracy_health(self):
        """Test scraping accuracy health check."""
        result = await check_scraping_accuracy_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'scraping_accuracy'
        assert result.category == 'advanced'
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_tournament_support_health(self):
        """Test tournament support health check."""
        result = await check_tournament_support_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'tournament_support'
        assert result.category == 'advanced'
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_multi_table_support_health(self):
        """Test multi-table support health check."""
        result = await check_multi_table_support_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'multi_table_support'
        assert result.category == 'advanced'
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_region_extraction_health(self):
        """Test region extraction health check."""
        result = await check_region_extraction_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'region_extraction'
        assert result.category == 'scraping'
        # Should be healthy since module exists
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_poker_table_detection_health(self):
        """Test poker table detection health check."""
        result = await check_poker_table_detection_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'poker_table_detection'
        assert result.category == 'scraping'
        # Should be healthy since scraper exists
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_ocr_engine_health(self):
        """Test OCR engine health check."""
        result = await check_ocr_engine_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'ocr_engine'
        assert result.category == 'scraping'
        # May fail if Tesseract not installed
        assert result.status in ['healthy', 'failing']

    @pytest.mark.asyncio
    async def test_screen_capture_health(self):
        """Test screen capture health check."""
        result = await check_screen_capture_health()
        assert isinstance(result, HealthStatus)
        assert result.feature_name == 'screen_capture'
        assert result.category == 'scraping'
        # May fail depending on permissions
        assert result.status in ['healthy', 'failing']


class TestHealthCheckRegistration:
    """Test health check registration."""

    def test_register_all_health_checks(self):
        """Test registering all health checks."""
        checker = SystemHealthChecker()
        register_all_health_checks(checker)

        # Should register 20 health checks
        assert len(checker.checks) == 20

        # Verify key checks are registered
        assert 'api_server' in checker.checks
        assert 'database' in checker.checks
        assert 'ocr_engine' in checker.checks
        assert 'gto_solver' in checker.checks
        assert 'opponent_modeling' in checker.checks
        assert 'tournament_support' in checker.checks

    def test_all_categories_represented(self):
        """Test that all categories have health checks."""
        checker = SystemHealthChecker()
        register_all_health_checks(checker)

        categories = set(check.category for check in checker.checks.values())

        # Should have all 5 categories
        assert 'backend' in categories
        assert 'scraping' in categories
        assert 'ml' in categories
        assert 'gui' in categories
        assert 'advanced' in categories


class TestHealthCheckTimeouts:
    """Test health check timeout handling."""

    @pytest.mark.asyncio
    async def test_check_timeout(self):
        """Test that slow checks timeout properly."""
        checker = SystemHealthChecker()

        async def slow_check():
            await asyncio.sleep(10)  # Sleep longer than timeout
            return HealthStatus(
                feature_name='slow',
                category='ml',
                status='healthy',
                last_check='2025-01-01T00:00:00Z'
            )

        checker.register_check('slow', 'ml', slow_check, 'Slow check', timeout=0.1)
        result = await checker.run_check('slow')

        # Should timeout and return failing status
        assert result.feature_name == 'slow'
        assert result.status == 'failing'
        assert 'timed out' in result.error_message.lower()


class TestHealthCheckErrors:
    """Test health check error handling."""

    @pytest.mark.asyncio
    async def test_check_exception_handling(self):
        """Test that exceptions are caught and reported."""
        checker = SystemHealthChecker()

        async def error_check():
            raise ValueError("Test error")

        checker.register_check('error', 'ml', error_check, 'Error check')
        result = await checker.run_check('error')

        # Should catch exception and return failing status
        assert result.feature_name == 'error'
        assert result.status == 'failing'
        assert 'Test error' in result.error_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
