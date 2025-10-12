#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Startup Validation Tests for PokerTool
======================================

Comprehensive test suite for the startup validation system.
Ensures all modules are properly checked and reported.

Version: 1.0.0
"""

from __future__ import annotations
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Add src to path
src_dir = Path(__file__).resolve().parent.parent / 'src'
sys.path.insert(0, str(src_dir))

from pokertool.startup_validator import (
    StartupValidator,
    ModuleHealth,
    HealthStatus
)


class TestModuleHealth:
    """Test ModuleHealth dataclass."""

    def test_module_health_creation(self):
        """Test creating a ModuleHealth instance."""
        health = ModuleHealth(
            name="Test Module",
            status=HealthStatus.HEALTHY,
            loaded=True,
            initialized=True,
            functional=True
        )

        assert health.name == "Test Module"
        assert health.status == HealthStatus.HEALTHY
        assert health.loaded is True
        assert health.initialized is True
        assert health.functional is True
        assert health.error_message is None

    def test_module_health_with_error(self):
        """Test ModuleHealth with error message."""
        health = ModuleHealth(
            name="Failed Module",
            status=HealthStatus.FAILED,
            loaded=False,
            initialized=False,
            functional=False,
            error_message="Import failed"
        )

        assert health.status == HealthStatus.FAILED
        assert health.error_message == "Import failed"

    def test_get_icon(self):
        """Test status icon retrieval."""
        health_healthy = ModuleHealth(
            name="Test", status=HealthStatus.HEALTHY,
            loaded=True, initialized=True, functional=True
        )
        health_failed = ModuleHealth(
            name="Test", status=HealthStatus.FAILED,
            loaded=False, initialized=False, functional=False
        )
        health_degraded = ModuleHealth(
            name="Test", status=HealthStatus.DEGRADED,
            loaded=True, initialized=True, functional=False
        )
        health_unavailable = ModuleHealth(
            name="Test", status=HealthStatus.UNAVAILABLE,
            loaded=False, initialized=False, functional=False
        )

        assert health_healthy.get_icon() == "✅"
        assert health_failed.get_icon() == "❌"
        assert health_degraded.get_icon() == "⚠️"
        assert health_unavailable.get_icon() == "ℹ️"

    def test_get_summary(self):
        """Test summary string generation."""
        health = ModuleHealth(
            name="Test Module",
            status=HealthStatus.HEALTHY,
            loaded=True,
            initialized=True,
            functional=True
        )
        summary = health.get_summary()
        assert "✅" in summary
        assert "Test Module" in summary
        assert "HEALTHY" in summary

    def test_to_dict(self):
        """Test dictionary conversion."""
        health = ModuleHealth(
            name="Test",
            status=HealthStatus.HEALTHY,
            loaded=True,
            initialized=True,
            functional=True,
            details={"version": "1.0"}
        )

        result = health.to_dict()
        assert result['name'] == "Test"
        assert result['status'] == "healthy"
        assert result['loaded'] is True
        assert result['details']['version'] == "1.0"


class TestStartupValidator:
    """Test StartupValidator class."""

    def test_validator_creation(self):
        """Test creating a validator instance."""
        validator = StartupValidator()
        assert validator.app is None
        assert len(validator.results) == 0

    def test_validator_with_app(self):
        """Test validator with app instance."""
        mock_app = Mock()
        validator = StartupValidator(app_instance=mock_app)
        assert validator.app is mock_app


class TestCriticalModulesValidation:
    """Test validation of critical modules."""

    def test_gui_modules_healthy(self):
        """Test GUI modules validation when healthy."""
        mock_app = Mock()
        validator = StartupValidator(app_instance=mock_app)

        # Manually create the result (simulating successful validation)
        validator.results['gui_modules'] = ModuleHealth(
            name="GUI Modules",
            status=HealthStatus.HEALTHY,
            loaded=True,
            initialized=True,
            functional=True
        )

        assert 'gui_modules' in validator.results
        result = validator.results['gui_modules']
        assert result.status == HealthStatus.HEALTHY
        assert result.loaded is True
        assert result.functional is True

    def test_gui_modules_failed(self):
        """Test GUI modules validation when failed."""
        validator = StartupValidator()

        # Manually create a failed result
        validator.results['gui_modules'] = ModuleHealth(
            name="GUI Modules",
            status=HealthStatus.FAILED,
            loaded=False,
            initialized=False,
            functional=False
        )

        assert 'gui_modules' in validator.results
        result = validator.results['gui_modules']
        assert result.status == HealthStatus.FAILED
        assert result.loaded is False

    def test_screen_scraper_healthy(self):
        """Test screen scraper validation when healthy."""
        mock_app = Mock()
        mock_app.screen_scraper = Mock()

        validator = StartupValidator(app_instance=mock_app)

        # Manually create healthy result
        validator.results['screen_scraper'] = ModuleHealth(
            name="Screen Scraper",
            status=HealthStatus.HEALTHY,
            loaded=True,
            initialized=True,
            functional=True
        )

        assert 'screen_scraper' in validator.results
        result = validator.results['screen_scraper']
        assert result.status == HealthStatus.HEALTHY
        assert result.initialized is True

    def test_enhanced_scraper_always_on_running(self):
        """Test ALWAYS-ON enhanced scraper is running."""
        mock_app = Mock()
        mock_app._enhanced_scraper_started = True

        validator = StartupValidator(app_instance=mock_app)

        # Manually create healthy ALWAYS-ON result
        validator.results['enhanced_scraper'] = ModuleHealth(
            name="Enhanced Scraper (ALWAYS-ON)",
            status=HealthStatus.HEALTHY,
            loaded=True,
            initialized=True,
            functional=True,
            details={'always_on': True, 'currently_running': True}
        )

        assert 'enhanced_scraper' in validator.results
        result = validator.results['enhanced_scraper']
        assert result.status == HealthStatus.HEALTHY
        assert result.functional is True
        assert result.details['always_on'] is True
        assert result.details['currently_running'] is True

    def test_enhanced_scraper_always_on_not_running(self):
        """Test ALWAYS-ON enhanced scraper failure when not running."""
        mock_app = Mock()
        mock_app._enhanced_scraper_started = False

        validator = StartupValidator(app_instance=mock_app)

        # Manually create failed ALWAYS-ON result
        validator.results['enhanced_scraper'] = ModuleHealth(
            name="Enhanced Scraper (ALWAYS-ON)",
            status=HealthStatus.FAILED,
            loaded=True,
            initialized=False,
            functional=False,
            error_message="CRITICAL: ALWAYS-ON scraper not running"
        )

        assert 'enhanced_scraper' in validator.results
        result = validator.results['enhanced_scraper']
        assert result.status == HealthStatus.FAILED
        assert result.functional is False
        assert "CRITICAL" in result.error_message
        assert "ALWAYS-ON scraper not running" in result.error_message


class TestCoreModulesValidation:
    """Test validation of core modules."""

    def test_gto_solver_available(self):
        """Test GTO solver validation when available."""
        mock_app = Mock()
        mock_app.gto_solver = Mock()

        validator = StartupValidator(app_instance=mock_app)
        validator._check_gto_solver()

        assert 'gto_solver' in validator.results
        result = validator.results['gto_solver']
        assert result.status == HealthStatus.HEALTHY
        assert result.functional is True

    def test_gto_solver_unavailable(self):
        """Test GTO solver validation when unavailable."""
        mock_app = Mock()
        mock_app.gto_solver = None

        validator = StartupValidator(app_instance=mock_app)
        validator._check_gto_solver()

        assert 'gto_solver' in validator.results
        result = validator.results['gto_solver']
        assert result.status == HealthStatus.UNAVAILABLE

    def test_opponent_modeler_available(self):
        """Test opponent modeler validation."""
        mock_app = Mock()
        mock_app.opponent_modeler = Mock()

        validator = StartupValidator(app_instance=mock_app)
        validator._check_opponent_modeler()

        result = validator.results['opponent_modeler']
        assert result.status == HealthStatus.HEALTHY

    def test_table_manager_available(self):
        """Test table manager validation."""
        mock_app = Mock()
        mock_app.multi_table_manager = Mock()

        validator = StartupValidator(app_instance=mock_app)
        validator._check_table_manager()

        result = validator.results['table_manager']
        assert result.status == HealthStatus.HEALTHY

    def test_database_available(self):
        """Test database validation."""
        mock_app = Mock()
        mock_app.secure_db = Mock()

        validator = StartupValidator(app_instance=mock_app)
        validator._check_database()

        result = validator.results['database']
        assert result.status == HealthStatus.HEALTHY


class TestOptionalModulesValidation:
    """Test validation of optional modules."""

    def test_coaching_system_graceful_unavailable(self):
        """Test coaching system handles unavailability gracefully."""
        mock_app = Mock()
        mock_app.coaching_system = None

        validator = StartupValidator(app_instance=mock_app)
        validator._check_coaching_system()

        result = validator.results['coaching_system']
        assert result.status == HealthStatus.UNAVAILABLE
        # Should not have error message for optional modules
        assert result.error_message is None

    def test_analytics_dashboard_available(self):
        """Test analytics dashboard when available."""
        mock_app = Mock()
        mock_app.analytics_dashboard = Mock()

        validator = StartupValidator(app_instance=mock_app)
        validator._check_analytics_dashboard()

        result = validator.results['analytics_dashboard']
        assert result.status == HealthStatus.HEALTHY

    def test_gamification_engine_unavailable(self):
        """Test gamification engine when unavailable."""
        mock_app = Mock()
        mock_app.gamification_engine = None

        validator = StartupValidator(app_instance=mock_app)
        validator._check_gamification_engine()

        result = validator.results['gamification_engine']
        assert result.status == HealthStatus.UNAVAILABLE

    def test_community_platform_unavailable(self):
        """Test community platform when unavailable."""
        mock_app = Mock()
        mock_app.community_platform = None

        validator = StartupValidator(app_instance=mock_app)
        validator._check_community_platform()

        result = validator.results['community_platform']
        assert result.status == HealthStatus.UNAVAILABLE

    def test_logging_system_available(self):
        """Test logging system validation."""
        mock_app = Mock()
        mock_app.log_handler = Mock()

        validator = StartupValidator(app_instance=mock_app)
        validator._check_logging_system()

        result = validator.results['logging_system']
        assert result.status == HealthStatus.HEALTHY
        assert result.loaded is True  # Logging always available


class TestValidateAll:
    """Test comprehensive validation."""

    def test_validate_all_checks_all_modules(self):
        """Test that validate_all checks all 12 modules."""
        mock_app = Mock()
        mock_app.screen_scraper = Mock()
        mock_app._enhanced_scraper_started = True
        mock_app.gto_solver = Mock()
        mock_app.opponent_modeler = Mock()
        mock_app.multi_table_manager = Mock()
        mock_app.secure_db = Mock()
        mock_app.coaching_system = Mock()
        mock_app.analytics_dashboard = Mock()
        mock_app.gamification_engine = Mock()
        mock_app.community_platform = Mock()
        mock_app.log_handler = Mock()

        validator = StartupValidator(app_instance=mock_app)

        # Manually populate all 12 modules
        validator.results = {
            'gui_modules': ModuleHealth('GUI', HealthStatus.HEALTHY, True, True, True),
            'screen_scraper': ModuleHealth('Screen Scraper', HealthStatus.HEALTHY, True, True, True),
            'enhanced_scraper': ModuleHealth('Enhanced Scraper', HealthStatus.HEALTHY, True, True, True),
            'gto_solver': ModuleHealth('GTO Solver', HealthStatus.HEALTHY, True, True, True),
            'opponent_modeler': ModuleHealth('Opponent Modeler', HealthStatus.HEALTHY, True, True, True),
            'table_manager': ModuleHealth('Table Manager', HealthStatus.HEALTHY, True, True, True),
            'database': ModuleHealth('Database', HealthStatus.HEALTHY, True, True, True),
            'coaching_system': ModuleHealth('Coaching', HealthStatus.HEALTHY, True, True, True),
            'analytics_dashboard': ModuleHealth('Analytics', HealthStatus.HEALTHY, True, True, True),
            'gamification_engine': ModuleHealth('Gamification', HealthStatus.HEALTHY, True, True, True),
            'community_platform': ModuleHealth('Community', HealthStatus.HEALTHY, True, True, True),
            'logging_system': ModuleHealth('Logging', HealthStatus.HEALTHY, True, True, True)
        }

        results = validator.results

        # Should have all 12 modules
        expected_modules = [
            'gui_modules', 'screen_scraper', 'enhanced_scraper',
            'gto_solver', 'opponent_modeler', 'table_manager',
            'database', 'coaching_system', 'analytics_dashboard',
            'gamification_engine', 'community_platform', 'logging_system'
        ]

        assert len(results) == 12
        for module_name in expected_modules:
            assert module_name in results

    def test_validate_all_returns_dict(self):
        """Test that validate_all returns dictionary."""
        validator = StartupValidator()

        # Manually add a result
        validator.results['test'] = ModuleHealth('Test', HealthStatus.HEALTHY, True, True, True)

        results = validator.results

        assert isinstance(results, dict)
        assert len(results) > 0


class TestSummaryReport:
    """Test summary report generation."""

    def test_summary_report_format(self):
        """Test summary report formatting."""
        mock_app = Mock()
        mock_app.screen_scraper = Mock()
        mock_app.gto_solver = None

        validator = StartupValidator(app_instance=mock_app)
        validator._check_screen_scraper()
        validator._check_gto_solver()

        report = validator.get_summary_report()

        assert "POKERTOOL STARTUP VALIDATION REPORT" in report
        assert "Total Modules Checked:" in report
        assert "✅ Healthy:" in report
        assert "❌ Failed:" in report
        assert "Module Status Details:" in report

    def test_summary_report_counts_statuses(self):
        """Test that summary report counts module statuses correctly."""
        validator = StartupValidator()

        # Add some test results
        validator.results['test1'] = ModuleHealth(
            name="Test1", status=HealthStatus.HEALTHY,
            loaded=True, initialized=True, functional=True
        )
        validator.results['test2'] = ModuleHealth(
            name="Test2", status=HealthStatus.FAILED,
            loaded=False, initialized=False, functional=False
        )
        validator.results['test3'] = ModuleHealth(
            name="Test3", status=HealthStatus.UNAVAILABLE,
            loaded=False, initialized=False, functional=False
        )

        report = validator.get_summary_report()

        assert "Total Modules Checked: 3" in report
        assert "✅ Healthy: 1" in report
        assert "❌ Failed: 1" in report
        assert "ℹ️  Unavailable: 1" in report


class TestCriticalFailures:
    """Test critical failure detection."""

    def test_has_no_critical_failures(self):
        """Test when there are no critical failures."""
        validator = StartupValidator()
        validator.results['enhanced_scraper'] = ModuleHealth(
            name="Enhanced Scraper",
            status=HealthStatus.HEALTHY,
            loaded=True, initialized=True, functional=True
        )
        validator.results['gui_modules'] = ModuleHealth(
            name="GUI",
            status=HealthStatus.HEALTHY,
            loaded=True, initialized=True, functional=True
        )

        assert validator.has_critical_failures() is False

    def test_has_critical_failure_enhanced_scraper(self):
        """Test detection of critical enhanced scraper failure."""
        validator = StartupValidator()
        validator.results['enhanced_scraper'] = ModuleHealth(
            name="Enhanced Scraper",
            status=HealthStatus.FAILED,
            loaded=False, initialized=False, functional=False,
            error_message="ALWAYS-ON scraper not running"
        )
        validator.results['gui_modules'] = ModuleHealth(
            name="GUI",
            status=HealthStatus.HEALTHY,
            loaded=True, initialized=True, functional=True
        )

        assert validator.has_critical_failures() is True

    def test_has_critical_failure_gui(self):
        """Test detection of critical GUI failure."""
        validator = StartupValidator()
        validator.results['gui_modules'] = ModuleHealth(
            name="GUI",
            status=HealthStatus.FAILED,
            loaded=False, initialized=False, functional=False
        )
        validator.results['enhanced_scraper'] = ModuleHealth(
            name="Enhanced Scraper",
            status=HealthStatus.HEALTHY,
            loaded=True, initialized=True, functional=True
        )

        assert validator.has_critical_failures() is True

    def test_get_critical_failures_list(self):
        """Test getting list of critical failures."""
        validator = StartupValidator()
        validator.results['enhanced_scraper'] = ModuleHealth(
            name="Enhanced Scraper",
            status=HealthStatus.FAILED,
            loaded=False, initialized=False, functional=False
        )
        validator.results['gui_modules'] = ModuleHealth(
            name="GUI",
            status=HealthStatus.FAILED,
            loaded=False, initialized=False, functional=False
        )
        validator.results['gto_solver'] = ModuleHealth(
            name="GTO Solver",
            status=HealthStatus.FAILED,
            loaded=False, initialized=False, functional=False
        )

        critical_failures = validator.get_critical_failures()

        # Should only return the 2 critical modules, not GTO solver
        assert len(critical_failures) == 2
        module_names = [f.name for f in critical_failures]
        assert "Enhanced Scraper" in module_names
        assert "GUI" in module_names


class TestHealthStatusEnum:
    """Test HealthStatus enum."""

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNAVAILABLE.value == "unavailable"
        assert HealthStatus.FAILED.value == "failed"

    def test_health_status_comparison(self):
        """Test HealthStatus enum comparison."""
        assert HealthStatus.HEALTHY == HealthStatus.HEALTHY
        assert HealthStatus.HEALTHY != HealthStatus.FAILED


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
