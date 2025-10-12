#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Startup Validation System for PokerTool
========================================

Comprehensive health checks for all application features and modules.
Validates that every component is properly initialized and functional.

Version: 2.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
import sys
import platform
import subprocess
from pathlib import Path


class HealthStatus(Enum):
    """Health status for modules."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass
class ModuleHealth:
    """Health information for a single module."""
    name: str
    status: HealthStatus
    loaded: bool
    initialized: bool
    functional: bool
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'status': self.status.value,
            'loaded': self.loaded,
            'initialized': self.initialized,
            'functional': self.functional,
            'error_message': self.error_message,
            'details': self.details,
            'checked_at': self.checked_at
        }

    def get_icon(self) -> str:
        """Get status icon for console/GUI display."""
        icons = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNAVAILABLE: "ℹ️",
            HealthStatus.FAILED: "❌"
        }
        return icons.get(self.status, "❓")

    def get_summary(self) -> str:
        """Get one-line status summary."""
        icon = self.get_icon()
        status_text = self.status.value.upper()
        error_suffix = f" - {self.error_message}" if self.error_message else ""
        return f"{icon} {self.name}: {status_text}{error_suffix}"


class StartupValidator:
    """Validates all application modules on startup and during runtime."""

    def __init__(self, app_instance: Optional[Any] = None):
        """
        Initialize the startup validator.

        Args:
            app_instance: Reference to the main application (IntegratedPokerAssistant)
        """
        self.app = app_instance
        self.results: Dict[str, ModuleHealth] = {}
        self.logger = logging.getLogger(__name__)

    def validate_all(self) -> Dict[str, ModuleHealth]:
        """
        Run all validation checks.

        Returns:
            Dictionary of module names to ModuleHealth objects
        """
        self.logger.info("Starting comprehensive startup validation...")

        # Critical modules (must work)
        self._check_gui_modules()
        self._check_screen_scraper()
        self._check_enhanced_scraper()

        # Core modules (should work)
        self._check_gto_solver()
        self._check_opponent_modeler()
        self._check_table_manager()
        self._check_database()

        # Optional modules (nice to have)
        self._check_coaching_system()
        self._check_analytics_dashboard()
        self._check_gamification_engine()
        self._check_community_platform()
        self._check_logging_system()

        self.logger.info(f"Validation complete - checked {len(self.results)} modules")
        return self.results

    def _check_gui_modules(self) -> None:
        """Check if core GUI modules are loaded."""
        try:
            from pokertool import enhanced_gui
            loaded = getattr(enhanced_gui, 'GUI_MODULES_LOADED', False)

            if loaded and self.app:
                # Check if critical GUI components exist
                has_gui = hasattr(enhanced_gui, 'EnhancedPokerAssistant')
                has_frame = hasattr(enhanced_gui, 'EnhancedPokerAssistantFrame')

                self.results['gui_modules'] = ModuleHealth(
                    name="GUI Modules",
                    status=HealthStatus.HEALTHY if (has_gui and has_frame) else HealthStatus.DEGRADED,
                    loaded=loaded,
                    initialized=True,
                    functional=has_gui and has_frame,
                    details={'components': ['EnhancedPokerAssistant', 'EnhancedPokerAssistantFrame']}
                )
            else:
                self.results['gui_modules'] = ModuleHealth(
                    name="GUI Modules",
                    status=HealthStatus.FAILED,
                    loaded=loaded,
                    initialized=False,
                    functional=False,
                    error_message="GUI modules not loaded"
                )
        except Exception as e:
            self.results['gui_modules'] = ModuleHealth(
                name="GUI Modules",
                status=HealthStatus.FAILED,
                loaded=False,
                initialized=False,
                functional=False,
                error_message=str(e)
            )

    def _check_screen_scraper(self) -> None:
        """Check if screen scraper is loaded and initialized."""
        try:
            from pokertool import enhanced_gui
            loaded = getattr(enhanced_gui, 'SCREEN_SCRAPER_LOADED', False)

            if self.app and hasattr(self.app, 'screen_scraper'):
                scraper_exists = self.app.screen_scraper is not None

                self.results['screen_scraper'] = ModuleHealth(
                    name="Screen Scraper",
                    status=HealthStatus.HEALTHY if scraper_exists else HealthStatus.UNAVAILABLE,
                    loaded=loaded,
                    initialized=scraper_exists,
                    functional=scraper_exists,
                    details={'scraper_object': scraper_exists}
                )
            else:
                self.results['screen_scraper'] = ModuleHealth(
                    name="Screen Scraper",
                    status=HealthStatus.UNAVAILABLE,
                    loaded=loaded,
                    initialized=False,
                    functional=False
                )
        except Exception as e:
            self.results['screen_scraper'] = ModuleHealth(
                name="Screen Scraper",
                status=HealthStatus.FAILED,
                loaded=False,
                initialized=False,
                functional=False,
                error_message=str(e)
            )

    def _check_enhanced_scraper(self) -> None:
        """Check if enhanced scraper is loaded and ALWAYS-ON."""
        try:
            from pokertool import enhanced_gui
            loaded = getattr(enhanced_gui, 'ENHANCED_SCRAPER_LOADED', False)

            if self.app and hasattr(self.app, '_enhanced_scraper_started'):
                is_running = self.app._enhanced_scraper_started

                self.results['enhanced_scraper'] = ModuleHealth(
                    name="Enhanced Scraper (ALWAYS-ON)",
                    status=HealthStatus.HEALTHY if is_running else HealthStatus.FAILED,
                    loaded=loaded,
                    initialized=True,
                    functional=is_running,
                    details={'always_on': True, 'currently_running': is_running},
                    error_message=None if is_running else "CRITICAL: ALWAYS-ON scraper not running"
                )
            else:
                self.results['enhanced_scraper'] = ModuleHealth(
                    name="Enhanced Scraper (ALWAYS-ON)",
                    status=HealthStatus.FAILED,
                    loaded=loaded,
                    initialized=False,
                    functional=False,
                    error_message="CRITICAL: ALWAYS-ON scraper not initialized"
                )
        except Exception as e:
            self.results['enhanced_scraper'] = ModuleHealth(
                name="Enhanced Scraper (ALWAYS-ON)",
                status=HealthStatus.FAILED,
                loaded=False,
                initialized=False,
                functional=False,
                error_message=f"CRITICAL: {str(e)}"
            )

    def _check_gto_solver(self) -> None:
        """Check if GTO solver is available."""
        if self.app and hasattr(self.app, 'gto_solver'):
            solver_exists = self.app.gto_solver is not None

            self.results['gto_solver'] = ModuleHealth(
                name="GTO Solver",
                status=HealthStatus.HEALTHY if solver_exists else HealthStatus.UNAVAILABLE,
                loaded=solver_exists,
                initialized=solver_exists,
                functional=solver_exists
            )
        else:
            self.results['gto_solver'] = ModuleHealth(
                name="GTO Solver",
                status=HealthStatus.UNAVAILABLE,
                loaded=False,
                initialized=False,
                functional=False
            )

    def _check_opponent_modeler(self) -> None:
        """Check if opponent modeling system is available."""
        if self.app and hasattr(self.app, 'opponent_modeler'):
            modeler_exists = self.app.opponent_modeler is not None

            self.results['opponent_modeler'] = ModuleHealth(
                name="Opponent Modeler",
                status=HealthStatus.HEALTHY if modeler_exists else HealthStatus.UNAVAILABLE,
                loaded=modeler_exists,
                initialized=modeler_exists,
                functional=modeler_exists
            )
        else:
            self.results['opponent_modeler'] = ModuleHealth(
                name="Opponent Modeler",
                status=HealthStatus.UNAVAILABLE,
                loaded=False,
                initialized=False,
                functional=False
            )

    def _check_table_manager(self) -> None:
        """Check if table manager is available."""
        if self.app and hasattr(self.app, 'multi_table_manager'):
            manager_exists = self.app.multi_table_manager is not None

            self.results['table_manager'] = ModuleHealth(
                name="Table Manager",
                status=HealthStatus.HEALTHY if manager_exists else HealthStatus.UNAVAILABLE,
                loaded=manager_exists,
                initialized=manager_exists,
                functional=manager_exists
            )
        else:
            self.results['table_manager'] = ModuleHealth(
                name="Table Manager",
                status=HealthStatus.UNAVAILABLE,
                loaded=False,
                initialized=False,
                functional=False
            )

    def _check_database(self) -> None:
        """Check if database is connected."""
        if self.app and hasattr(self.app, 'secure_db'):
            db_exists = self.app.secure_db is not None

            self.results['database'] = ModuleHealth(
                name="Secure Database",
                status=HealthStatus.HEALTHY if db_exists else HealthStatus.UNAVAILABLE,
                loaded=db_exists,
                initialized=db_exists,
                functional=db_exists
            )
        else:
            self.results['database'] = ModuleHealth(
                name="Secure Database",
                status=HealthStatus.UNAVAILABLE,
                loaded=False,
                initialized=False,
                functional=False
            )

    def _check_coaching_system(self) -> None:
        """Check if coaching system is available."""
        if self.app and hasattr(self.app, 'coaching_system'):
            coaching_exists = self.app.coaching_system is not None

            self.results['coaching_system'] = ModuleHealth(
                name="Coaching System",
                status=HealthStatus.HEALTHY if coaching_exists else HealthStatus.UNAVAILABLE,
                loaded=coaching_exists,
                initialized=coaching_exists,
                functional=coaching_exists
            )
        else:
            self.results['coaching_system'] = ModuleHealth(
                name="Coaching System",
                status=HealthStatus.UNAVAILABLE,
                loaded=False,
                initialized=False,
                functional=False
            )

    def _check_analytics_dashboard(self) -> None:
        """Check if analytics dashboard is available."""
        if self.app and hasattr(self.app, 'analytics_dashboard'):
            analytics_exists = self.app.analytics_dashboard is not None

            self.results['analytics_dashboard'] = ModuleHealth(
                name="Analytics Dashboard",
                status=HealthStatus.HEALTHY if analytics_exists else HealthStatus.UNAVAILABLE,
                loaded=analytics_exists,
                initialized=analytics_exists,
                functional=analytics_exists
            )
        else:
            self.results['analytics_dashboard'] = ModuleHealth(
                name="Analytics Dashboard",
                status=HealthStatus.UNAVAILABLE,
                loaded=False,
                initialized=False,
                functional=False
            )

    def _check_gamification_engine(self) -> None:
        """Check if gamification engine is available."""
        if self.app and hasattr(self.app, 'gamification_engine'):
            gamification_exists = self.app.gamification_engine is not None

            self.results['gamification_engine'] = ModuleHealth(
                name="Gamification Engine",
                status=HealthStatus.HEALTHY if gamification_exists else HealthStatus.UNAVAILABLE,
                loaded=gamification_exists,
                initialized=gamification_exists,
                functional=gamification_exists
            )
        else:
            self.results['gamification_engine'] = ModuleHealth(
                name="Gamification Engine",
                status=HealthStatus.UNAVAILABLE,
                loaded=False,
                initialized=False,
                functional=False
            )

    def _check_community_platform(self) -> None:
        """Check if community platform is available."""
        if self.app and hasattr(self.app, 'community_platform'):
            community_exists = self.app.community_platform is not None

            self.results['community_platform'] = ModuleHealth(
                name="Community Platform",
                status=HealthStatus.HEALTHY if community_exists else HealthStatus.UNAVAILABLE,
                loaded=community_exists,
                initialized=community_exists,
                functional=community_exists
            )
        else:
            self.results['community_platform'] = ModuleHealth(
                name="Community Platform",
                status=HealthStatus.UNAVAILABLE,
                loaded=False,
                initialized=False,
                functional=False
            )

    def _check_logging_system(self) -> None:
        """Check if logging system is configured."""
        if self.app and hasattr(self.app, 'log_handler'):
            handler_exists = self.app.log_handler is not None

            self.results['logging_system'] = ModuleHealth(
                name="Logging System",
                status=HealthStatus.HEALTHY if handler_exists else HealthStatus.UNAVAILABLE,
                loaded=True,  # Logging is always available
                initialized=handler_exists,
                functional=handler_exists
            )
        else:
            self.results['logging_system'] = ModuleHealth(
                name="Logging System",
                status=HealthStatus.UNAVAILABLE,
                loaded=True,
                initialized=False,
                functional=False
            )

    def get_summary_report(self) -> str:
        """Generate a text summary report of all module health."""
        lines = [
            "="  * 70,
            "POKERTOOL STARTUP VALIDATION REPORT",
            "=" * 70,
            ""
        ]

        # Count statuses
        healthy = sum(1 for m in self.results.values() if m.status == HealthStatus.HEALTHY)
        degraded = sum(1 for m in self.results.values() if m.status == HealthStatus.DEGRADED)
        unavailable = sum(1 for m in self.results.values() if m.status == HealthStatus.UNAVAILABLE)
        failed = sum(1 for m in self.results.values() if m.status == HealthStatus.FAILED)

        lines.append(f"Total Modules Checked: {len(self.results)}")
        lines.append(f"  ✅ Healthy: {healthy}")
        lines.append(f"  ⚠️  Degraded: {degraded}")
        lines.append(f"  ℹ️  Unavailable: {unavailable}")
        lines.append(f"  ❌ Failed: {failed}")
        lines.append("")
        lines.append("Module Status Details:")
        lines.append("-" * 70)

        # Sort by status (failed first, then degraded, then unavailable, then healthy)
        status_order = {
            HealthStatus.FAILED: 0,
            HealthStatus.DEGRADED: 1,
            HealthStatus.UNAVAILABLE: 2,
            HealthStatus.HEALTHY: 3
        }
        sorted_results = sorted(
            self.results.values(),
            key=lambda m: (status_order[m.status], m.name)
        )

        for module in sorted_results:
            lines.append(module.get_summary())

        lines.append("=" * 70)

        return "\n".join(lines)

    def get_critical_failures(self) -> List[ModuleHealth]:
        """Get list of critical module failures."""
        critical_modules = ['enhanced_scraper', 'gui_modules']
        return [
            self.results[name]
            for name in critical_modules
            if name in self.results and self.results[name].status == HealthStatus.FAILED
        ]

    def has_critical_failures(self) -> bool:
        """Check if any critical modules have failed."""
        return len(self.get_critical_failures()) > 0


# ===========================================================================
# Pre-Startup Dependency Validation (runs before app initialization)
# ===========================================================================

@dataclass
class DependencyCheck:
    """Result of a dependency check."""
    name: str
    version: Optional[str]
    status: str  # "✓", "⚠", "✗"
    message: str
    critical: bool = False


def check_dependencies() -> Tuple[List[DependencyCheck], bool]:
    """
    Check all required dependencies before app startup.

    Returns:
        Tuple of (check_results, can_start)
        - check_results: List of dependency check results
        - can_start: True if app can start, False if critical deps missing
    """
    checks = []

    # ===== System Info =====
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(DependencyCheck(
        name="Python",
        version=py_version,
        status="✓" if sys.version_info >= (3, 10) else "✗",
        message="Version OK" if sys.version_info >= (3, 10) else "Version too old (need 3.10+)",
        critical=True
    ))

    checks.append(DependencyCheck(
        name="Platform",
        version=f"{platform.system()} {platform.release()}",
        status="ℹ",
        message="",
        critical=False
    ))

    # ===== Core Dependencies =====
    # NumPy
    try:
        import numpy as np
        checks.append(DependencyCheck(
            name="NumPy",
            version=np.__version__,
            status="✓",
            message="Installed",
            critical=True
        ))
    except ImportError:
        checks.append(DependencyCheck(
            name="NumPy",
            version=None,
            status="✗",
            message="NOT INSTALLED - pip install numpy",
            critical=True
        ))

    # OpenCV
    try:
        import cv2
        checks.append(DependencyCheck(
            name="OpenCV",
            version=cv2.__version__,
            status="✓",
            message="Installed",
            critical=True
        ))
    except ImportError:
        checks.append(DependencyCheck(
            name="OpenCV",
            version=None,
            status="✗",
            message="NOT INSTALLED - pip install opencv-python",
            critical=True
        ))

    # Pillow
    try:
        from PIL import Image
        import PIL
        checks.append(DependencyCheck(
            name="Pillow",
            version=PIL.__version__,
            status="✓",
            message="Installed",
            critical=True
        ))
    except ImportError:
        checks.append(DependencyCheck(
            name="Pillow",
            version=None,
            status="✗",
            message="NOT INSTALLED - pip install Pillow",
            critical=True
        ))

    # pytesseract
    try:
        import pytesseract
        version = getattr(pytesseract, '__version__', 'unknown')
        checks.append(DependencyCheck(
            name="pytesseract",
            version=version,
            status="✓",
            message="Installed",
            critical=True
        ))
    except ImportError:
        checks.append(DependencyCheck(
            name="pytesseract",
            version=None,
            status="✗",
            message="NOT INSTALLED - pip install pytesseract",
            critical=True
        ))

    # MSS (screen capture)
    try:
        import mss
        checks.append(DependencyCheck(
            name="MSS",
            version=mss.__version__,
            status="✓",
            message="Screen capture available",
            critical=True
        ))
    except ImportError:
        checks.append(DependencyCheck(
            name="MSS",
            version=None,
            status="✗",
            message="NOT INSTALLED - pip install mss",
            critical=True
        ))

    # ===== Optional Dependencies =====
    # PyTorch
    try:
        import torch
        checks.append(DependencyCheck(
            name="PyTorch",
            version=torch.__version__,
            status="✓",
            message="ML features available",
            critical=False
        ))

        # Check GPU
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            checks.append(DependencyCheck(
                name="GPU (CUDA)",
                version=torch.version.cuda,
                status="✓",
                message=f"{gpu_name}",
                critical=False
            ))
        else:
            checks.append(DependencyCheck(
                name="GPU (CUDA)",
                version=None,
                status="ℹ",
                message="Not available (CPU mode)",
                critical=False
            ))
    except ImportError:
        checks.append(DependencyCheck(
            name="PyTorch",
            version=None,
            status="⚠",
            message="Not installed (optional)",
            critical=False
        ))
        checks.append(DependencyCheck(
            name="GPU (CUDA)",
            version=None,
            status="ℹ",
            message="PyTorch not installed",
            critical=False
        ))

    # Tesseract binary
    try:
        result = subprocess.run(['tesseract', '--version'],
                               capture_output=True,
                               text=True,
                               timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            version = version_line.split()[1] if len(version_line.split()) > 1 else 'unknown'
            checks.append(DependencyCheck(
                name="Tesseract OCR",
                version=version,
                status="✓",
                message="Binary installed",
                critical=False
            ))
        else:
            checks.append(DependencyCheck(
                name="Tesseract OCR",
                version=None,
                status="⚠",
                message="Binary not working correctly",
                critical=False
            ))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        checks.append(DependencyCheck(
            name="Tesseract OCR",
            version=None,
            status="⚠",
            message="Binary not found (brew install tesseract)",
            critical=False
        ))

    # Check if any critical dependencies failed
    critical_failures = [c for c in checks if c.critical and c.status == "✗"]
    can_start = len(critical_failures) == 0

    return checks, can_start


def print_dependency_report(checks: List[DependencyCheck], verbose: bool = False):
    """Print a formatted dependency report."""
    print()
    print("=" * 70)
    print("🔍 POKERTOOL STARTUP DEPENDENCY CHECK")
    print("=" * 70)
    print()

    # Separate into categories
    system_checks = [c for c in checks if c.name in ["Python", "Platform"]]
    core_checks = [c for c in checks if c.name in ["NumPy", "OpenCV", "Pillow", "pytesseract", "MSS"]]
    optional_checks = [c for c in checks if c.name in ["PyTorch", "GPU (CUDA)", "Tesseract OCR"]]

    # Print system info
    print("System Information:")
    print("-" * 70)
    for check in system_checks:
        version_str = f" v{check.version}" if check.version else ""
        msg_str = f" - {check.message}" if check.message else ""
        print(f"  {check.status} {check.name}:{version_str}{msg_str}")
    print()

    # Print core dependencies
    print("Core Dependencies:")
    print("-" * 70)
    for check in core_checks:
        version_str = f" v{check.version}" if check.version else ""
        msg_str = f" - {check.message}" if check.message else ""
        print(f"  {check.status} {check.name:20s}{version_str}{msg_str}")
    print()

    # Print optional dependencies
    print("Optional Features:")
    print("-" * 70)
    for check in optional_checks:
        version_str = f" v{check.version}" if check.version else ""
        msg_str = f" - {check.message}" if check.message else ""
        print(f"  {check.status} {check.name:20s}{version_str}{msg_str}")
    print()

    # Summary
    passed = sum(1 for c in checks if c.status == "✓")
    warned = sum(1 for c in checks if c.status == "⚠")
    failed = sum(1 for c in checks if c.status == "✗")

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total checks:  {len(checks)}")
    print(f"  ✓ Passed:      {passed}")
    print(f"  ⚠ Warnings:    {warned}")
    print(f"  ✗ Failed:      {failed}")
    print()

    # Verdict
    critical_failures = [c for c in checks if c.critical and c.status == "✗"]
    if critical_failures:
        print("❌ CRITICAL DEPENDENCIES MISSING")
        print()
        print("The following critical dependencies are missing:")
        for check in critical_failures:
            print(f"  • {check.name}: {check.message}")
        print()
        print("Please install missing dependencies and try again.")
        print("=" * 70)
        return False
    elif warned > 0:
        print("⚠ WARNINGS DETECTED")
        print("Some optional features may not be available.")
        print("Application will start with reduced functionality.")
        print("=" * 70)
        return True
    else:
        print("✓ ALL DEPENDENCIES SATISFIED")
        print("Application is ready to start!")
        print("=" * 70)
        return True


def validate_startup_dependencies(verbose: bool = False) -> bool:
    """
    Quick dependency check before app startup.

    Returns:
        True if app can start, False if critical dependencies missing
    """
    checks, can_start = check_dependencies()
    print_dependency_report(checks, verbose=verbose)
    return can_start
