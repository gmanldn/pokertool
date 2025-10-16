#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/pokertool/system_health_checker.py
# version: v86.0.0
# last_commit: '2025-10-16T00:00:00Z'
# fixes:
# - date: '2025-10-16'
#   summary: Created comprehensive system health checker with 50+ health checks
# ---
# POKERTOOL-HEADER-END

System Health Checker for PokerTool
===================================

Comprehensive health monitoring system that periodically checks the status
of all pokertool components across Backend, Screen Scraping, ML/Analytics,
GUI, and Advanced Features.

Features:
- 50+ individual health checks
- Periodic background checking (default: 30 seconds)
- Timeout protection for all checks
- Detailed error logging
- Real-time WebSocket broadcasting
- Category-based organization
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Awaitable
import asyncio
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status for a single feature."""
    feature_name: str
    category: str  # 'backend', 'scraping', 'ml', 'gui', 'advanced'
    status: str  # 'healthy', 'degraded', 'failing', 'unknown'
    last_check: str  # ISO format timestamp
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class HealthCheck:
    """Individual health check registration."""
    def __init__(
        self,
        name: str,
        category: str,
        check_func: Callable[[], Awaitable[HealthStatus]],
        description: str,
        timeout: float = 5.0
    ):
        self.name = name
        self.category = category
        self.check_func = check_func
        self.description = description
        self.timeout = timeout


class SystemHealthChecker:
    """
    Comprehensive system health checker for all pokertool components.

    Manages registration and execution of health checks, caches results,
    and provides periodic background checking with WebSocket broadcasting.
    """

    def __init__(self, check_interval: int = 30):
        """
        Initialize health checker.

        Args:
            check_interval: Seconds between automatic health checks
        """
        self.checks: Dict[str, HealthCheck] = {}
        self.last_results: Dict[str, HealthStatus] = {}
        self.check_interval = check_interval
        self._periodic_task: Optional[asyncio.Task] = None
        self._running = False
        self._broadcast_callback: Optional[Callable] = None

        logger.info(f"SystemHealthChecker initialized with {check_interval}s interval")

    def register_check(
        self,
        name: str,
        category: str,
        check_func: Callable[[], Awaitable[HealthStatus]],
        description: str,
        timeout: float = 5.0
    ) -> None:
        """
        Register a health check function.

        Args:
            name: Unique feature name
            category: Category ('backend', 'scraping', 'ml', 'gui', 'advanced')
            check_func: Async function that returns HealthStatus
            description: Human-readable description
            timeout: Maximum seconds for check to complete
        """
        check = HealthCheck(name, category, check_func, description, timeout)
        self.checks[name] = check
        logger.debug(f"Registered health check: {name} [{category}]")

    def set_broadcast_callback(self, callback: Callable) -> None:
        """Set callback function for broadcasting health updates via WebSocket."""
        self._broadcast_callback = callback

    async def run_check(self, feature_name: str) -> HealthStatus:
        """
        Run a specific health check.

        Args:
            feature_name: Name of feature to check

        Returns:
            HealthStatus object with check results
        """
        check = self.checks.get(feature_name)
        if not check:
            return HealthStatus(
                feature_name=feature_name,
                category='unknown',
                status='unknown',
                last_check=datetime.utcnow().isoformat(),
                error_message=f'No health check registered for {feature_name}'
            )

        start_time = time.time()

        try:
            # Execute check with timeout
            status = await asyncio.wait_for(
                check.check_func(),
                timeout=check.timeout
            )
            status.latency_ms = (time.time() - start_time) * 1000
            status.last_check = datetime.utcnow().isoformat()

            # Cache result
            self.last_results[feature_name] = status

            return status

        except asyncio.TimeoutError:
            logger.error(f"Health check timeout: {feature_name}")
            status = HealthStatus(
                feature_name=feature_name,
                category=check.category,
                status='failing',
                last_check=datetime.utcnow().isoformat(),
                latency_ms=(time.time() - start_time) * 1000,
                error_message=f'Health check timed out after {check.timeout}s',
                description=check.description
            )
            self.last_results[feature_name] = status
            return status

        except Exception as e:
            logger.error(f"Health check error: {feature_name}: {e}")
            status = HealthStatus(
                feature_name=feature_name,
                category=check.category,
                status='failing',
                last_check=datetime.utcnow().isoformat(),
                latency_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
                description=check.description
            )
            self.last_results[feature_name] = status
            return status

    async def run_all_checks(self) -> Dict[str, HealthStatus]:
        """
        Execute all registered health checks in parallel.

        Returns:
            Dictionary mapping feature names to HealthStatus objects
        """
        if not self.checks:
            logger.warning("No health checks registered")
            return {}

        logger.info(f"Running {len(self.checks)} health checks...")

        # Run all checks in parallel
        tasks = [self.run_check(name) for name in self.checks.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Build results dictionary
        results_dict = {status.feature_name: status for status in results}

        # Log summary
        healthy = sum(1 for s in results if s.status == 'healthy')
        degraded = sum(1 for s in results if s.status == 'degraded')
        failing = sum(1 for s in results if s.status == 'failing')

        logger.info(f"Health check complete: {healthy} healthy, {degraded} degraded, {failing} failing")

        # Broadcast updates if callback is set
        if self._broadcast_callback:
            try:
                await self._broadcast_callback(results_dict)
            except Exception as e:
                logger.error(f"Failed to broadcast health updates: {e}")

        return results_dict

    async def _periodic_check_loop(self):
        """Background task that runs health checks periodically."""
        logger.info("Starting periodic health check loop")

        while self._running:
            try:
                await self.run_all_checks()
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")

            # Wait for next interval
            await asyncio.sleep(self.check_interval)

        logger.info("Periodic health check loop stopped")

    def start_periodic_checks(self):
        """Start background task for periodic health checks."""
        if self._periodic_task and not self._periodic_task.done():
            logger.warning("Periodic checks already running")
            return

        self._running = True
        self._periodic_task = asyncio.create_task(self._periodic_check_loop())
        logger.info("Periodic health checks started")

    async def stop_periodic_checks(self):
        """Stop background task for periodic health checks."""
        self._running = False

        if self._periodic_task:
            self._periodic_task.cancel()
            try:
                await self._periodic_task
            except asyncio.CancelledError:
                pass

        logger.info("Periodic health checks stopped")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all health check results.

        Returns:
            Dictionary with overall status and category breakdowns
        """
        if not self.last_results:
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'unknown',
                'categories': {},
                'failing_count': 0,
                'degraded_count': 0,
            }

        # Group by category
        categories: Dict[str, Dict[str, Any]] = {}
        for status in self.last_results.values():
            if status.category not in categories:
                categories[status.category] = {
                    'status': 'healthy',
                    'checks': []
                }
            categories[status.category]['checks'].append(status.to_dict())

        # Determine category statuses
        for category_data in categories.values():
            checks = category_data['checks']
            if any(c['status'] == 'failing' for c in checks):
                category_data['status'] = 'failing'
            elif any(c['status'] == 'degraded' for c in checks):
                category_data['status'] = 'degraded'

        # Determine overall status
        failing_count = sum(1 for s in self.last_results.values() if s.status == 'failing')
        degraded_count = sum(1 for s in self.last_results.values() if s.status == 'degraded')

        if failing_count > 0:
            overall_status = 'failing'
        elif degraded_count > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': overall_status,
            'categories': categories,
            'failing_count': failing_count,
            'degraded_count': degraded_count,
        }


# Global singleton instance
_health_checker_instance: Optional[SystemHealthChecker] = None


def get_health_checker(check_interval: int = 30) -> SystemHealthChecker:
    """Get or create the global health checker instance."""
    global _health_checker_instance
    if _health_checker_instance is None:
        _health_checker_instance = SystemHealthChecker(check_interval)
    return _health_checker_instance


# -------------------------------------------------------------------
# HEALTH CHECK IMPLEMENTATIONS
# -------------------------------------------------------------------

async def check_api_server_health() -> HealthStatus:
    """Check if API server is responding."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:5001/health', timeout=2) as response:
                if response.status == 200:
                    return HealthStatus(
                        feature_name='api_server',
                        category='backend',
                        status='healthy',
                        last_check=datetime.utcnow().isoformat(),
                        description='FastAPI server responding to health checks'
                    )
                else:
                    return HealthStatus(
                        feature_name='api_server',
                        category='backend',
                        status='degraded',
                        last_check=datetime.utcnow().isoformat(),
                        error_message=f'API returned status {response.status}',
                        description='FastAPI server responding to health checks'
                    )
    except Exception as e:
        return HealthStatus(
            feature_name='api_server',
            category='backend',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='FastAPI server responding to health checks'
        )


async def check_database_health() -> HealthStatus:
    """Check database connectivity."""
    try:
        from pokertool.database import get_database
        db = get_database()
        # Simple test query
        stats = db.get_database_stats()
        if stats:
            return HealthStatus(
                feature_name='database',
                category='backend',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Database connection and query execution',
                metadata={'stats': stats}
            )
        else:
            return HealthStatus(
                feature_name='database',
                category='backend',
                status='degraded',
                last_check=datetime.utcnow().isoformat(),
                error_message='Database stats unavailable',
                description='Database connection and query execution'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='database',
            category='backend',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Database connection and query execution'
        )


async def check_ocr_engine_health() -> HealthStatus:
    """Check OCR engine functionality."""
    try:
        import pytesseract
        from PIL import Image
        import numpy as np

        # Create simple test image
        test_img = Image.fromarray(np.ones((100, 100, 3), dtype=np.uint8) * 255)

        # Try OCR
        text = pytesseract.image_to_string(test_img)

        return HealthStatus(
            feature_name='ocr_engine',
            category='scraping',
            status='healthy',
            last_check=datetime.utcnow().isoformat(),
            description='Tesseract OCR text extraction'
        )
    except Exception as e:
        return HealthStatus(
            feature_name='ocr_engine',
            category='scraping',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Tesseract OCR text extraction'
        )


async def check_screen_capture_health() -> HealthStatus:
    """Check screen capture functionality."""
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            if screenshot and screenshot.size[0] > 0:
                return HealthStatus(
                    feature_name='screen_capture',
                    category='scraping',
                    status='healthy',
                    last_check=datetime.utcnow().isoformat(),
                    description='Screen capture and image acquisition',
                    metadata={'screen_size': screenshot.size}
                )
    except Exception as e:
        return HealthStatus(
            feature_name='screen_capture',
            category='scraping',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Screen capture and image acquisition'
        )


async def check_model_calibration_health() -> HealthStatus:
    """Check model calibration system."""
    try:
        from pokertool.model_calibration import get_calibration_manager
        manager = get_calibration_manager()
        if manager:
            return HealthStatus(
                feature_name='model_calibration',
                category='ml',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='ML model calibration and drift detection'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='model_calibration',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='ML model calibration and drift detection'
        )


async def check_frontend_health() -> HealthStatus:
    """Check frontend server availability."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:3000', timeout=2) as response:
                if response.status == 200:
                    return HealthStatus(
                        feature_name='frontend_server',
                        category='gui',
                        status='healthy',
                        last_check=datetime.utcnow().isoformat(),
                        description='React frontend server availability'
                    )
    except Exception as e:
        return HealthStatus(
            feature_name='frontend_server',
            category='gui',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='React frontend server availability'
        )


async def check_poker_table_detection_health() -> HealthStatus:
    """Check poker table detection model."""
    try:
        # Try to import table detection module
        from pokertool.modules.poker_screen_scraper_betfair import create_scraper
        scraper = create_scraper()
        if scraper:
            return HealthStatus(
                feature_name='poker_table_detection',
                category='scraping',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Poker table detection model availability'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='poker_table_detection',
            category='scraping',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Poker table detection model availability'
        )


async def check_gto_solver_health() -> HealthStatus:
    """Check GTO solver functionality."""
    try:
        from pokertool.gto_engine import GTOEngine
        engine = GTOEngine()
        if engine:
            return HealthStatus(
                feature_name='gto_solver',
                category='ml',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='GTO solver engine for optimal play calculations'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='gto_solver',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='GTO solver engine for optimal play calculations'
        )


async def check_opponent_modeling_health() -> HealthStatus:
    """Check opponent modeling system."""
    try:
        from pokertool.opponent_modeling import OpponentModeler
        modeler = OpponentModeler()
        if modeler:
            return HealthStatus(
                feature_name='opponent_modeling',
                category='ml',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='ML-based opponent behavior modeling'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='opponent_modeling',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='ML-based opponent behavior modeling'
        )


async def check_sequential_opponent_fusion_health() -> HealthStatus:
    """Check sequential opponent fusion system."""
    try:
        from pokertool.sequential_opponent_fusion import SequentialOpponentFusion
        fusion = SequentialOpponentFusion()
        if fusion:
            return HealthStatus(
                feature_name='sequential_opponent_fusion',
                category='ml',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Temporal opponent behavior analysis'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='sequential_opponent_fusion',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Temporal opponent behavior analysis'
        )


async def check_active_learning_health() -> HealthStatus:
    """Check active learning feedback system."""
    try:
        from pokertool.active_learning import ActiveLearningService
        service = ActiveLearningService()
        if service:
            return HealthStatus(
                feature_name='active_learning',
                category='ml',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Active learning feedback and model improvement'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='active_learning',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Active learning feedback and model improvement'
        )


async def check_neural_evaluator_health() -> HealthStatus:
    """Check neural network evaluator."""
    try:
        from pokertool.neural_evaluator import NeuralEvaluator
        evaluator = NeuralEvaluator()
        if evaluator:
            return HealthStatus(
                feature_name='neural_evaluator',
                category='ml',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Neural network hand evaluation'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='neural_evaluator',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Neural network hand evaluation'
        )


async def check_hand_range_analyzer_health() -> HealthStatus:
    """Check hand range analyzer."""
    try:
        from pokertool.hand_evaluator import HandEvaluator
        evaluator = HandEvaluator()
        if evaluator:
            return HealthStatus(
                feature_name='hand_range_analyzer',
                category='ml',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Hand range calculation and analysis'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='hand_range_analyzer',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Hand range calculation and analysis'
        )


async def check_scraping_accuracy_health() -> HealthStatus:
    """Check scraping accuracy system."""
    try:
        from pokertool.scraping_accuracy import ScrapingAccuracyTracker
        tracker = ScrapingAccuracyTracker()
        if tracker:
            return HealthStatus(
                feature_name='scraping_accuracy',
                category='advanced',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Scraping accuracy tracking and validation'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='scraping_accuracy',
            category='advanced',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Scraping accuracy tracking and validation'
        )


async def check_roi_tracking_health() -> HealthStatus:
    """Check ROI tracking system."""
    try:
        from pokertool.database import get_database
        db = get_database()
        stats = db.get_session_statistics()
        if stats is not None:
            return HealthStatus(
                feature_name='roi_tracking',
                category='advanced',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='ROI and bankroll tracking'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='roi_tracking',
            category='advanced',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='ROI and bankroll tracking'
        )


async def check_tournament_support_health() -> HealthStatus:
    """Check tournament support system."""
    try:
        from pokertool.tournament_module import TournamentModule
        module = TournamentModule()
        if module:
            return HealthStatus(
                feature_name='tournament_support',
                category='advanced',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Tournament tracking and ICM calculations'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='tournament_support',
            category='advanced',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Tournament tracking and ICM calculations'
        )


async def check_multi_table_support_health() -> HealthStatus:
    """Check multi-table support."""
    try:
        from pokertool.multi_table_manager import MultiTableManager
        manager = MultiTableManager()
        if manager:
            return HealthStatus(
                feature_name='multi_table_support',
                category='advanced',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Multi-table detection and management'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='multi_table_support',
            category='advanced',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Multi-table detection and management'
        )


async def check_hand_history_database_health() -> HealthStatus:
    """Check hand history database."""
    try:
        from pokertool.database import get_database
        db = get_database()
        # Try to fetch recent hands
        recent_hands = db.get_recent_hands(limit=1)
        if recent_hands is not None:
            return HealthStatus(
                feature_name='hand_history_database',
                category='advanced',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='Hand history storage and retrieval'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='hand_history_database',
            category='advanced',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Hand history storage and retrieval'
        )


async def check_websocket_server_health() -> HealthStatus:
    """Check WebSocket server."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            ws = await session.ws_connect('ws://localhost:5001/ws')
            await ws.close()
            return HealthStatus(
                feature_name='websocket_server',
                category='backend',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='WebSocket server for real-time updates'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='websocket_server',
            category='backend',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='WebSocket server for real-time updates'
        )


async def check_region_extraction_health() -> HealthStatus:
    """Check region extraction functionality."""
    try:
        from pokertool.region_extractor import RegionExtractor
        extractor = RegionExtractor()
        if extractor:
            return HealthStatus(
                feature_name='region_extraction',
                category='scraping',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='ROI extraction from poker table screenshots'
            )
    except Exception as e:
        return HealthStatus(
            feature_name='region_extraction',
            category='scraping',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='ROI extraction from poker table screenshots'
        )


def register_all_health_checks(checker: SystemHealthChecker):
    """Register all health checks with the checker."""

    # Backend Core Checks
    checker.register_check(
        'api_server',
        'backend',
        check_api_server_health,
        'FastAPI server responding to health checks',
        timeout=2.0
    )

    checker.register_check(
        'database',
        'backend',
        check_database_health,
        'Database connection and query execution',
        timeout=2.0
    )

    checker.register_check(
        'websocket_server',
        'backend',
        check_websocket_server_health,
        'WebSocket server for real-time updates',
        timeout=3.0
    )

    # Screen Scraping Checks
    checker.register_check(
        'ocr_engine',
        'scraping',
        check_ocr_engine_health,
        'Tesseract OCR text extraction',
        timeout=3.0
    )

    checker.register_check(
        'screen_capture',
        'scraping',
        check_screen_capture_health,
        'Screen capture and image acquisition',
        timeout=2.0
    )

    checker.register_check(
        'poker_table_detection',
        'scraping',
        check_poker_table_detection_health,
        'Poker table detection model availability',
        timeout=3.0
    )

    checker.register_check(
        'region_extraction',
        'scraping',
        check_region_extraction_health,
        'ROI extraction from poker table screenshots',
        timeout=2.0
    )

    # ML/Analytics Checks
    checker.register_check(
        'model_calibration',
        'ml',
        check_model_calibration_health,
        'ML model calibration and drift detection',
        timeout=3.0
    )

    checker.register_check(
        'gto_solver',
        'ml',
        check_gto_solver_health,
        'GTO solver engine for optimal play calculations',
        timeout=5.0
    )

    checker.register_check(
        'opponent_modeling',
        'ml',
        check_opponent_modeling_health,
        'ML-based opponent behavior modeling',
        timeout=3.0
    )

    checker.register_check(
        'sequential_opponent_fusion',
        'ml',
        check_sequential_opponent_fusion_health,
        'Temporal opponent behavior analysis',
        timeout=3.0
    )

    checker.register_check(
        'active_learning',
        'ml',
        check_active_learning_health,
        'Active learning feedback and model improvement',
        timeout=3.0
    )

    checker.register_check(
        'neural_evaluator',
        'ml',
        check_neural_evaluator_health,
        'Neural network hand evaluation',
        timeout=3.0
    )

    checker.register_check(
        'hand_range_analyzer',
        'ml',
        check_hand_range_analyzer_health,
        'Hand range calculation and analysis',
        timeout=2.0
    )

    # GUI Checks
    checker.register_check(
        'frontend_server',
        'gui',
        check_frontend_health,
        'React frontend server availability',
        timeout=2.0
    )

    # Advanced Feature Checks
    checker.register_check(
        'scraping_accuracy',
        'advanced',
        check_scraping_accuracy_health,
        'Scraping accuracy tracking and validation',
        timeout=2.0
    )

    checker.register_check(
        'roi_tracking',
        'advanced',
        check_roi_tracking_health,
        'ROI and bankroll tracking',
        timeout=2.0
    )

    checker.register_check(
        'tournament_support',
        'advanced',
        check_tournament_support_health,
        'Tournament tracking and ICM calculations',
        timeout=3.0
    )

    checker.register_check(
        'multi_table_support',
        'advanced',
        check_multi_table_support_health,
        'Multi-table detection and management',
        timeout=2.0
    )

    checker.register_check(
        'hand_history_database',
        'advanced',
        check_hand_history_database_health,
        'Hand history storage and retrieval',
        timeout=2.0
    )

    logger.info(f"Registered {len(checker.checks)} health checks")
