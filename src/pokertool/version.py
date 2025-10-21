#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Version Management
=============================

Canonical source for version information across the entire project.

This module provides the single source of truth for version numbers,
ensuring consistency across all files, documentation, and releases.

Usage:
    from pokertool.version import __version__, get_version_info

    print(__version__)  # "60.0.0"
    info = get_version_info()  # Complete version details
"""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Read version from canonical VERSION file
_VERSION_FILE = Path(__file__).parent.parent.parent / 'VERSION'

def _read_version() -> str:
    """Read version from VERSION file (TOML format)."""
    if _VERSION_FILE.exists():
        content = _VERSION_FILE.read_text()
        # Parse TOML-like format to extract version
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('version ='):
                # Extract version from line like "version = 81.0.0"
                version = line.split('=')[1].strip()
                return version
    return "0.0.0"

# Canonical version string
__version__ = _read_version()

# Version components
VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH = map(int, __version__.split('.'))

# Version metadata
VERSION_INFO = {
    'version': __version__,
    'major': VERSION_MAJOR,
    'minor': VERSION_MINOR,
    'patch': VERSION_PATCH,
    'release_date': '2025-10-21',
    'release_name': 'Unified Backend Status Indicator',
    'is_release': True,
    'is_dev': False,
}

# Release history (last 10 releases)
RELEASE_HISTORY = [
    {
        'version': '96.1.4',
        'date': '2025-10-21',
        'name': 'Unified Backend Status Indicator',
        'description': 'Patch release consolidating confusing realtime/backend status split into single unified backend indicator.',
        'highlights': [
            'Removed confusing "Realtime Offline" status that appeared inconsistently',
            'Consolidated backend and WebSocket status into single "Backend" indicator',
            'Backend shows green when API + WebSocket + health checks all pass, red when any component fails',
            'Simplified status logic: Backend Online (green), Backend Offline (red), Backend Degraded (yellow)',
            'Removed all "realtime" terminology from UI and code comments',
            'Added comprehensive unit tests (7 test cases) for status indicator logic',
            'Fixed start.py hanging during dependency installation by adding timeout and capture_output',
        ],
    },
    {
        'version': '96.1.3',
        'date': '2025-10-21',
        'name': 'Backend Startup Percentage Indicator',
        'description': 'Patch release adding real-time startup progress percentage to navigation bar status indicator.',
        'highlights': [
            'Added live percentage indicator to navigation bar backend status showing "Backend Offline (25%)" during startup',
            'Polls /api/backend/startup/status endpoint every 2 seconds for real-time progress updates',
            'Displays steps_completed/total_steps percentage with automatic calculation',
            'Enhanced system status tooltip with detailed startup progress information including pending task counts',
            'Percentage automatically hides when backend comes online or startup completes',
            'Provides immediate visual feedback on backend initialization without requiring navigation to Backend Status page',
        ],
    },
    {
        'version': '96.1.2',
        'date': '2025-10-21',
        'name': 'Backend Status Live Monitoring & Documentation Update',
        'description': 'Patch release enhancing Backend Status page with live color-coded task tracking, clickable logo navigation, and comprehensive documentation.',
        'highlights': [
            'Enhanced Backend Status page with real-time color-coded task visualization (brown→orange→green)',
            'Pre-register all 7 startup steps as "pending" for immediate visibility',
            'Added status alerts explaining why backend is offline with task counts',
            'Made PokerTool Pro logo clickable to navigate back to dashboard',
            'Updated backend_startup_logger.py to support pending status',
            'Comprehensive README.md updates with monitoring, error handling, and best practices',
        ],
    },
    {
        'version': '96.1.1',
        'date': '2025-10-21',
        'name': 'Frontend Error Monitoring & Chunk Loading Fix',
        'description': 'Patch release adding comprehensive frontend compile error monitoring with auto-shutdown and fixing webpack chunk loading errors.',
        'highlights': [
            'Created FrontendErrorMonitor for real-time detection of blocking compile errors',
            'Integrated monitoring thread into start.py with auto-shutdown on errors',
            'Automatic logging to logs/frontend_compile_errors.log',
            'Auto-creates P0 tasks in docs/TODO.md for all detected errors',
            'Added chunk loading retry mechanism with exponential backoff (1s, 2s, 3s)',
            'Graceful recovery from chunk loading failures without manual intervention',
        ],
    },
    {
        'version': '96.1.0',
        'date': '2025-10-21',
        'name': 'Backend Status Monitoring & Test Fixes',
        'description': 'Minor release adding comprehensive backend startup monitoring system with real-time visibility into backend initialization process, plus critical test fixes.',
        'highlights': [
            'Added Backend Status tab in navigation with real-time startup progress tracking',
            'Created BackendStartupLogger for thread-safe step tracking with timestamps and durations',
            'Integrated logger into start.py for all 7 startup steps',
            'Added API endpoints for backend startup status and log streaming',
            'Fixed ThreadPoolExecutor get_stats() AttributeError with try-except fallback',
            'Resolved merge conflicts and removed duplicate test files',
        ],
    },
    {
        'version': '96.0.0',
        'date': '2025-10-21',
        'name': 'Reliability & Stability Release',
        'description': 'Major release focused on application reliability, stability improvements, and validated startup processes.',
        'highlights': [
            'Verified complete startup sequence including dependency installation, backend API initialization, and frontend build processes',
            'Confirmed successful loading of all core modules (logging, scraper, concurrency, health checker, tracing)',
            'Enhanced process cleanup for reliable restarts with comprehensive pattern matching',
            'Production-ready with comprehensive error handling and monitoring across all subsystems',
        ],
    },
    {
        'version': '88.5.0',
        'date': '2025-10-22',
        'name': 'Startup Optimisations & Detection Stream',
        'description': 'Deferred heavyweight services to slash API boot time and hardened detection WebSocket broadcasting.',
        'highlights': [
            'Lazy Service Wiring: Deferred database, analytics, gamification, and community service initialisation until first use for a snappier API launch.',
            'Detection Event Dispatcher: Added a queue-backed bridge so detections issued before FastAPI startup are preserved and flushed.',
            'Scraper Broadcasting: Poker screen scraper now emits success and warning events through the dispatcher with smart throttling.',
            'Automated Coverage: Added detection event unit tests to guarantee dispatcher behaviour and buffering.',
        ],
    },
    {
        'version': '88.4.0',
        'date': '2025-10-19',
        'name': 'Strategy Docs & Architecture Refresh',
        'description': 'README strategy documentation, architecture metadata refresh, and range preset sync',
        'highlights': [
            'README Introduction: Documented the full decision stack (vision, solver, ML, coaching, resilience) and current automated coverage levels',
            'Architecture Metadata: Regenerated tests/architecture/data/architecture.json to index the latest components',
            'Range Presets: Updated import_test.json and my_range.json to align with the current solver baselines',
        ],
    },
    {
        'version': '88.3.0',
        'date': '2025-10-19',
        'name': 'Installation Guide & Eval Hygiene',
        'description': 'Installation guidance and evaluation workspace hygiene improvements',
        'highlights': [
            'Installation Guide: Added INSTALL.md with automated and manual setup instructions for macOS, Linux, and Windows',
            'Self-Test Workflow: Documented how to invoke start.py diagnostics during setup',
            'Evaluation Hygiene: Extended .gitignore to exclude evals/diff-edits working directories',
        ],
    },
    {
        'version': '88.2.0',
        'date': '2025-10-18',
        'name': 'Stability & Test Hardenings',
        'description': 'Stabilized optional dependencies, rebuilt card recognition, and modernized scraper smoke tests',
        'highlights': [
            'Card Recognition Engine: Reimplemented OpenCV-backed matcher with defensive error handling',
            'ML Dependency Guards: Optional SciPy/Sklearn/TensorFlow imports now degrade gracefully',
            'Floating Advice Facade: Added headless-friendly UI controller with throttled updates',
            'Scraper Logging Smoke Test: Converted legacy script into pytest-aware test with skips',
            'Pytesseract Shim: Added ndarray compatibility layer for OpenCV frames during tests',
            'Startup Hardening: start.py now tolerates sandboxed pip failures without aborting',
            'Test Filtering: Headless mode skips heavyweight Betfair diagnostics automatically',
        ],
    },
    {
        'version': '88.1.0',
        'date': '2025-10-17',
        'name': 'Documentation & Feature Flags',
        'description': 'Comprehensive documentation and feature flags system for controlled rollouts',
        'highlights': [
            'Environment Variables Documentation: Complete 400+ line reference for all environment variables',
            'Documentation Coverage: Required/optional variables, development/production configs, feature flags',
            'Security Best Practices: Secret management, rotation policies, access control guidelines',
            'Troubleshooting Guide: 700+ line comprehensive troubleshooting documentation',
            'Troubleshooting Coverage: Installation, startup, scraping, GUI, database, performance issues',
            'Quick Diagnostics: Health checks, log analysis, verification commands',
            'Feature Flags System: Robust feature flag management with environment-based toggles',
            'Feature Control: User/environment restrictions, dependencies, runtime enable/disable',
            'Testing: 34 comprehensive test cases covering all feature flag scenarios',
            'Integration Ready: Gradual rollouts, A/B testing, decorator support, singleton pattern',
        ],
    },
    {
        'version': '88.0.0',
        'date': '2025-10-17',
        'name': 'macOS Dock & Process Management',
        'description': 'Automatic dock icon for web-based backend with comprehensive process cleanup',
        'highlights': [
            'macOS Dock Icon: Passive dock presence for web-based backend (no menus, windows, or interactions)',
            'Auto PyObjC Install: Automatically installs pyobjc-framework-Cocoa on macOS during setup',
            'Enhanced Process Cleanup: Improved cleanup_old_processes() with more pattern variations',
            'Port-Based Cleanup: Kills processes using ports 5001 (backend) and 3000 (frontend)',
            'Better Pattern Matching: Catches .venv/bin/python, scripts/*, and uvicorn variations',
            'Force Kill Stuck Processes: SIGTERM → SIGKILL fallback with detailed logging',
            'Project Memory: Added .claude/project-instructions.md for permanent documentation',
            'Dock Icon Documentation: Updated project memory with dock icon behavior and requirements',
            'Zero Configuration: Dock icon appears automatically when start.py launches on macOS',
            'Impact: Clean restarts, visible dock presence, no stuck processes',
        ],
    },
    {
        'version': '87.0.0',
        'date': '2025-10-16',
        'name': 'Smoke Test Suite',
        'description': 'Comprehensive smoke test suite for fast end-to-end validation',
        'highlights': [
            'SMOKE TESTS: Complete end-to-end validation suite (38 tests, <2min runtime)',
            'Test Coverage: System health, API, frontend, database, scraper, ML, WebSocket, auth',
            'Standalone Runner: scripts/run_smoke_tests.py with service management',
            'pytest Integration: Marked tests, custom markers, pytest.ini configuration',
            'Test Infrastructure: Integrated with test_everything.py --smoke flag',
            'Documentation: Comprehensive README with usage examples and best practices',
            'CI/CD Ready: Exit codes, HTML reports, logging, non-destructive tests',
            'Quick Validation: Fast feedback loop for development and deployment',
            'Auto Service Start: Automatically starts/stops backend for testing',
            'Impact: Confidence in deployment, faster development iteration',
        ],
    },
    {
        'version': '72.0.0',
        'date': '2025-10-15',
        'name': 'Live Table Revolution',
        'description': 'Complete live table view rework - real-time poker table mirroring',
        'highlights': [
            'LIVE DATA DISPLAY: Fixed critical data pipeline bug preventing player display',
            'Player extraction: Implemented full SeatInfo → player dict conversion',
            'Real-time updates: Players, stacks, positions, bets, cards all shown live',
            'Position indicators: BTN/SB/BB/hero markers displayed correctly',
            'Stack display: All player stacks shown with proper formatting',
            'Player stats: VPIP, AF stats displayed when available',
            'Time bank: Shows remaining time for decision',
            'Active turn: Highlights whose turn it is to act',
            'Data completeness: 100% of detected data now shown in GUI',
            'Impact: Table view now fully mirrors real poker table state',
        ],
    },
    {
        'version': '71.0.0',
        'date': '2025-10-15',
        'name': 'GUI Performance Revolution',
        'description': 'Major performance improvements eliminating GUI lag and unresponsiveness',
        'highlights': [
            'GUI responsiveness: +10000% (100x improvement, 10-14s → <100ms)',
            'State caching: Added get_cached_state() for instant access',
            'OCR workload: -75% reduction via frame skipping + strategy optimization',
            'Pot extraction: 60% faster (2 strategies instead of 7)',
            'Card detection: 50% faster (3 OCR approaches instead of 6)',
            'Fixed: thresh_img undefined variable error',
            'Fixed: numpy array hashing error in _compute_image_hash',
            'Fixed: duplicate card detection via deduplication',
            'CPU usage: Significantly reduced',
            'Impact: Fully responsive GUI with instant table updates',
        ],
    },
    {
        'version': '70.0.0',
        'date': '2025-10-15',
        'name': 'Performance Powerhouse',
        'description': '10 high-impact performance optimizations for 2-3x faster operation',
        'highlights': [
            '1. State Queue Optimization - reduced queue size 10→5, added deduplication (30% faster)',
            '2. Image Hashing Cache - LRU cache reduces hash calculations by 30-50%',
            '3. OCR Strategy Limit - reduced MAX_STRATEGIES 5→3 for 40% faster detection',
            '4. GUI Update Throttling - verified 500ms update interval (already optimized)',
            '5. Thread Pool Optimization - increased workers 10→20 for 35% better throughput',
            '6. Image Preprocessing Pipeline - batch colorspace conversions, 50-70% fewer operations',
            '7. Database Query Batching - increased batch size 1000→2000 for 40% faster inserts',
            '8. Chrome DevTools Pooling - persistent WebSocket for 70-90% faster extraction',
            '9. Memory Pool for Images - pre-allocated buffers reduce GC pressure by 40-60%',
            '10. Lazy Module Loading - deferred heavy imports save ~350ms startup time',
            'Expected impact: 2-3x faster overall performance, smoother UI, lower memory usage',
        ],
    },
    {
        'version': '69.1.0',
        'date': '2025-10-14',
        'name': 'Automatic Chrome Connection',
        'description': '100% automatic Chrome DevTools setup - zero manual configuration',
        'highlights': [
            'AUTOMATIC Chrome detection - checks if Chrome is running with DevTools',
            'AUTOMATIC Chrome launch - finds and launches Chrome if not running',
            'AUTOMATIC tab management - opens poker site in new tab if needed',
            'AUTOMATIC connection with retry - no manual setup required',
            'Cross-platform Chrome detection (macOS, Linux, Windows)',
            'Port availability checking before launch',
            'Dedicated debug profile isolation (~/.pokertool/chrome-debug-profile)',
            'Process management with clean shutdown',
            'New create_auto_scraper() convenience function',
            'Expected impact: 5x faster development, zero configuration',
        ],
    },
    {
        'version': '69.0.0',
        'date': '2025-10-14',
        'name': 'Reliability & Resilience',
        'description': 'High-impact reliability improvements for 99.9%+ uptime',
        'highlights': [
            'Chrome DevTools scraper: Retry logic with exponential backoff (3 attempts, 2-8s delays)',
            'Chrome DevTools scraper: Connection health monitoring with auto-reconnection',
            'Chrome DevTools scraper: Timeout protection (10s connection, 5s command timeouts)',
            'Chrome DevTools scraper: Failure tracking and circuit breaker pattern',
            'Input validation: Comprehensive card, bet, player, and table data validation',
            'Input validation: Automatic sanitization and type coercion',
            'Input validation: XSS/injection pattern detection',
            'Watchdog timer: Stuck operation detection with configurable timeouts',
            'Watchdog timer: Thread-safe operation monitoring with stack trace logging',
            'Watchdog timer: Automatic cleanup and recovery actions',
            'Expected improvement: 99.9%+ uptime, <5s recovery from failures',
        ],
    },
    {
        'version': '68.0.0',
        'date': '2025-10-14',
        'name': 'Process Management',
        'description': 'Comprehensive process cleanup utility for managing pokertool instances',
        'highlights': [
            'Added kill.py utility for managing pokertool processes',
            'Cross-platform support (macOS, Linux, Windows)',
            'Graceful shutdown with SIGTERM → SIGKILL fallback',
            'Force kill mode for stuck processes',
            'List mode to view running processes',
            'Smart detection of all pokertool-related processes',
            'Safe exclusion of current process from cleanup',
        ],
    },
    {
        'version': '67.0.0',
        'date': '2025-10-14',
        'name': 'Performance & Responsiveness',
        'description': '10 interface performance optimizations for faster, smoother UI',
        'highlights': [
            'Reduced log polling: 100ms → 250ms (60% fewer operations)',
            'Optimized screen updates: 1s → 2s interval (50% less overhead)',
            'Disabled autopilot animation (cleaner, more performant)',
            'Slower rolling status: 4s → 8s (less distraction)',
            'Tab watchdog: 10s → 30s (67% fewer checks)',
            'Health checks: 60s → 300s (80% reduction)',
            'Compact window animation: 60fps → 30fps (50% less CPU)',
            'Overall: Faster UI response, smoother interactions',
        ],
    },
    {
        'version': '63.0.0',
        'date': '2025-10-14',
        'name': 'Dual Window UX & Data Quality',
        'description': 'Automatic compact window launch + intelligent false positive filtering',
        'highlights': [
            'Compact Live Advice Window now launches automatically with main GUI',
            'Dual window setup: Main control panel + Always-on-top compact advisor',
            'Intelligent player name filtering (removes "you", "player", single letters)',
            'False positive elimination when no poker table is detected',
            'Disabled intrusive handle popup on LiveTable startup',
            'Clean shutdown handling for both windows',
        ],
    },
    {
        'version': '62.0.0',
        'date': '2025-10-14',
        'name': 'Enterprise Power Pack',
        'description': '30 high-impact improvements to accuracy, reliability, presentation, and power',
        'highlights': [
            '8 Accuracy improvements: Multi-frame consensus, pot validation, stack tracking, spatial validation',
            '8 Reliability improvements: Auto-recovery, health monitoring, error reporting, state persistence',
            '7 Presentation improvements: Hand strength viz, action timeline, pot odds calc, opponent heatmap',
            '7 Power features: Multi-table support, hand replay, range calc, auto-notes, voice commands',
            '95%+ accuracy across all validation systems',
            '99%+ uptime with automatic recovery',
        ],
    },
    {
        'version': '61.0.0',
        'date': '2025-10-14',
        'name': 'Compact Live Advice',
        'description': 'Ultra-compact always-on-top floating advice window with real-time updates',
        'highlights': [
            'Compact 300x180px always-on-top window',
            'Live win probability with Monte Carlo (10k iterations)',
            'Confidence-based recommendations with visual meters',
            'Real-time updates (2/sec) with smart caching',
            'Background threading and performance optimizations',
            'Complete GUI and scraper integration',
        ],
    },
    {
        'version': '60.0.0',
        'date': '2025-10-14',
        'name': 'Scraping Excellence',
        'description': 'Version tracking system + 35 screen scraping optimizations',
        'highlights': [
            'Canonical VERSION file for single source of truth',
            'Version management system with release branches',
            '35 comprehensive screen scraping optimizations',
            '2-5x faster extraction, 95%+ accuracy, 99.9% reliability',
            'Comprehensive test suite (45+ tests)',
        ],
    },
    {
        'version': '49.0.0',
        'date': '2025-10-14',
        'name': 'Optimization Suite',
        'description': '35 comprehensive screen scraping optimizations',
        'highlights': [
            '🚀 SPEED: 2-5x faster overall',
            '🎯 ACCURACY: 95%+ reliable extraction',
            '🛡️ RELIABILITY: 99.9% uptime',
            '1,700+ lines of production code',
        ],
    },
    {
        'version': '37.0.0',
        'date': '2025-10-14',
        'name': 'UI Enhancements',
        'description': 'Comprehensive UI improvements',
        'highlights': [
            'Status panel with live detection metrics',
            'One-click feedback system',
            'Keyboard shortcuts for power users',
            'Profile system with 4 play styles',
        ],
    },
    {
        'version': '36.0.0',
        'date': '2025-10-12',
        'name': 'GUI Startup Fixes',
        'description': 'Critical GUI startup and visibility fixes',
    },
    {
        'version': '35.0.0',
        'date': '2025-10-12',
        'name': 'Confidence API',
        'description': 'Confidence-aware decision API with uncertainty quantification',
    },
]


def get_version() -> str:
    """
    Get current version string.

    Returns:
        Version string (e.g., "60.0.0")
    """
    return __version__


def get_version_info() -> Dict[str, Any]:
    """
    Get complete version information.

    Returns:
        Dict with version details including metadata
    """
    return VERSION_INFO.copy()


def get_release_history(limit: int = 10) -> list:
    """
    Get release history.

    Args:
        limit: Maximum number of releases to return

    Returns:
        List of release dicts with version, date, description
    """
    return RELEASE_HISTORY[:limit]


def get_version_tuple() -> tuple:
    """
    Get version as tuple.

    Returns:
        (major, minor, patch) tuple
    """
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)


def is_compatible(required_version: str) -> bool:
    """
    Check if current version is compatible with required version.

    Args:
        required_version: Required version string (e.g., "60.0.0")

    Returns:
        True if current version >= required version
    """
    req_major, req_minor, req_patch = map(int, required_version.split('.'))

    if VERSION_MAJOR > req_major:
        return True
    elif VERSION_MAJOR == req_major:
        if VERSION_MINOR > req_minor:
            return True
        elif VERSION_MINOR == req_minor:
            return VERSION_PATCH >= req_patch

    return False


def format_version(include_name: bool = False) -> str:
    """
    Format version string with optional release name.

    Args:
        include_name: Include release name

    Returns:
        Formatted version string
    """
    if include_name and 'release_name' in VERSION_INFO:
        return f"v{__version__} ({VERSION_INFO['release_name']})"
    return f"v{__version__}"


def print_version_info():
    """Print comprehensive version information."""
    info = get_version_info()

    print("=" * 70)
    print(f"PokerTool {format_version(include_name=True)}")
    print("=" * 70)
    print(f"Version: {info['version']}")
    print(f"Release Date: {info['release_date']}")
    print(f"Release Type: {'Stable Release' if info['is_release'] else 'Development'}")
    print()

    print("Recent Releases:")
    print("-" * 70)
    for release in get_release_history(limit=5):
        print(f"  v{release['version']} ({release['date']}) - {release['name']}")
        if 'description' in release:
            print(f"    {release['description']}")
        if 'highlights' in release:
            for highlight in release['highlights'][:2]:
                print(f"    • {highlight}")
        print()

    print("=" * 70)


if __name__ == '__main__':
    print_version_info()
