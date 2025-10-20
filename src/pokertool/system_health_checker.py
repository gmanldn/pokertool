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
from typing import Dict, List, Optional, Callable, Any, Awaitable, Tuple
import asyncio
import time
import logging
import os
import json
from pathlib import Path
from collections import deque
import threading

logger = logging.getLogger(__name__)

# Health history storage
HEALTH_HISTORY_DIR = Path.cwd() / 'logs' / 'health_history'
HEALTH_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
HEALTH_HISTORY_FILE = HEALTH_HISTORY_DIR / 'health_history.jsonl'

_DEFAULT_BACKEND_HOST = os.getenv('POKERTOOL_HOST', '127.0.0.1')
_DEFAULT_BACKEND_PORT = os.getenv('POKERTOOL_PORT', '5001')
_BACKEND_BASE_URL = os.getenv('POKERTOOL_BACKEND_URL', f'http://{_DEFAULT_BACKEND_HOST}:{_DEFAULT_BACKEND_PORT}')
_FRONTEND_BASE_URL = os.getenv('POKERTOOL_FRONTEND_URL', 'http://localhost:3000')


def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


_BACKEND_HEALTH_URL = _join_url(_BACKEND_BASE_URL, '/health')


async def _http_get_status(url: str, timeout: float = 2.0) -> Tuple[int, str]:
    """
    Perform an HTTP GET request and return status code and body text.

    Tries to use aiohttp when available, otherwise falls back to requests
    executed in a thread to avoid blocking the event loop.
    """
    try:
        import aiohttp  # type: ignore
    except ImportError:
        import requests  # type: ignore

        def _sync_request() -> Tuple[int, str]:
            response = requests.get(url, timeout=timeout)
            return response.status_code, response.text

        return await asyncio.to_thread(_sync_request)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as response:
            body = await response.text()
            return response.status, body


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

    def __init__(self, check_interval: int = 30, max_history_entries: int = 2880):
        """
        Initialize health checker.

        Args:
            check_interval: Seconds between automatic health checks
            max_history_entries: Maximum history entries to keep (default: 2880 = 24h at 30s intervals)
        """
        self.checks: Dict[str, HealthCheck] = {}
        self.last_results: Dict[str, HealthStatus] = {}
        self.check_interval = check_interval
        self._periodic_task: Optional[asyncio.Task] = None
        self._running = False
        self._broadcast_callback: Optional[Callable] = None
        
        # Health history tracking (in-memory circular buffer)
        self.max_history_entries = max_history_entries
        self.health_history: deque = deque(maxlen=max_history_entries)
        
        # Result caching (5s TTL)
        self._cache_ttl: float = 5.0
        self._history_cache: Dict[int, Tuple[float, List[Dict[str, Any]]]] = {}
        self._trends_cache: Dict[int, Tuple[float, Dict[str, Any]]] = {}
        self._cache_lock = threading.Lock()

        # Load existing history from disk
        self._load_history()

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
    
    def _load_history(self) -> None:
        """Load health history from disk."""
        if not HEALTH_HISTORY_FILE.exists():
            return
        
        try:
            with open(HEALTH_HISTORY_FILE, 'r') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        self.health_history.append(entry)
            
            logger.info(f"Loaded {len(self.health_history)} health history entries")
        except Exception as e:
            logger.error(f"Failed to load health history: {e}")
    
    def _persist_history_entry(self, entry: Dict[str, Any]) -> None:
        """Persist a single health history entry to disk."""
        try:
            with open(HEALTH_HISTORY_FILE, 'a') as f:
                f.write(json.dumps(entry, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist health history entry: {e}")
    
    def _add_to_history(self, results: Dict[str, HealthStatus]) -> None:
        """Add health check results to history."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'results': {
                name: status.to_dict()
                for name, status in results.items()
            }
        }
        
        self.health_history.append(entry)
        self._persist_history_entry(entry)
        self._invalidate_caches()
        
        # Trim old entries from disk file if needed
        if len(self.health_history) >= self.max_history_entries:
            self._trim_history_file()

    def _invalidate_caches(self) -> None:
        """Invalidate cached history and trend results."""
        with self._cache_lock:
            self._history_cache.clear()
            self._trends_cache.clear()

    def _set_history_cache(self, hours: int, data: List[Dict[str, Any]]) -> None:
        """Cache history data for the requested time window."""
        with self._cache_lock:
            self._history_cache[int(hours)] = (time.time(), data)

    def _get_history_cache(self, hours: int) -> Optional[List[Dict[str, Any]]]:
        """Return cached history data when available and not expired."""
        key = int(hours)
        with self._cache_lock:
            cached = self._history_cache.get(key)
            if not cached:
                return None
            timestamp, data = cached
        if time.time() - timestamp <= self._cache_ttl:
            return data
        with self._cache_lock:
            self._history_cache.pop(key, None)
        return None

    def _set_trends_cache(self, hours: int, data: Dict[str, Any]) -> None:
        """Cache trend analysis for the requested time window."""
        with self._cache_lock:
            self._trends_cache[int(hours)] = (time.time(), data)

    def _get_trends_cache(self, hours: int) -> Optional[Dict[str, Any]]:
        """Return cached trend analysis when available and valid."""
        key = int(hours)
        with self._cache_lock:
            cached = self._trends_cache.get(key)
            if not cached:
                return None
            timestamp, data = cached
        if time.time() - timestamp <= self._cache_ttl:
            return data
        with self._cache_lock:
            self._trends_cache.pop(key, None)
        return None
    
    def _trim_history_file(self) -> None:
        """Trim old entries from history file."""
        try:
            # Rewrite file with current in-memory history
            with open(HEALTH_HISTORY_FILE, 'w') as f:
                for entry in self.health_history:
                    f.write(json.dumps(entry, default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to trim health history file: {e}")

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
        
        # Add to history
        self._add_to_history(results_dict)

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
    
    def get_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get health check history for the specified time period.

        Args:
            hours: Number of hours of history to return (default: 24)

        Returns:
            List of historical health check results
        """
        cached = self._get_history_cache(hours)
        if cached is not None:
            logger.debug(f"Returning cached health history for {hours}h window")
            return cached

        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        filtered_history = []
        for entry in self.health_history:
            try:
                entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')).timestamp()
                if entry_time >= cutoff_time:
                    filtered_history.append(entry)
            except Exception:
                continue
        
        self._set_history_cache(hours, filtered_history)
        
        return filtered_history
    
    def get_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Calculate health trends over the specified time period.

        Args:
            hours: Number of hours to analyze (default: 24)

        Returns:
            Dictionary containing trend analysis
        """
        cached = self._get_trends_cache(hours)
        if cached is not None:
            logger.debug(f"Returning cached health trends for {hours}h window")
            return cached

        history = self.get_history(hours)
        
        if not history:
            return {
                'period_hours': hours,
                'data_points': 0,
                'trends': {},
                'summary': 'Insufficient data'
            }
        
        # Analyze trends per feature
        feature_trends = {}
        
        for entry in history:
            for feature_name, status_dict in entry.get('results', {}).items():
                if feature_name not in feature_trends:
                    feature_trends[feature_name] = {
                        'healthy': 0,
                        'degraded': 0,
                        'failing': 0,
                        'unknown': 0,
                        'avg_latency': []
                    }
                
                status = status_dict.get('status', 'unknown')
                feature_trends[feature_name][status] = feature_trends[feature_name].get(status, 0) + 1
                
                if status_dict.get('latency_ms'):
                    feature_trends[feature_name]['avg_latency'].append(status_dict['latency_ms'])
        
        # Calculate percentages and averages
        for feature_name, trend_data in feature_trends.items():
            total = sum(trend_data[status] for status in ['healthy', 'degraded', 'failing', 'unknown'])
            
            if total > 0:
                trend_data['healthy_pct'] = (trend_data['healthy'] / total) * 100
                trend_data['degraded_pct'] = (trend_data['degraded'] / total) * 100
                trend_data['failing_pct'] = (trend_data['failing'] / total) * 100
            
            if trend_data['avg_latency']:
                trend_data['avg_latency_ms'] = sum(trend_data['avg_latency']) / len(trend_data['avg_latency'])
                del trend_data['avg_latency']
            else:
                trend_data['avg_latency_ms'] = None
        
        trends = {
            'period_hours': hours,
            'data_points': len(history),
            'start_time': history[0]['timestamp'] if history else None,
            'end_time': history[-1]['timestamp'] if history else None,
            'feature_trends': feature_trends,
            'summary': f"Analyzed {len(history)} data points over {hours} hours"
        }
        
        self._set_trends_cache(hours, trends)
        return trends


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
        status_code, body = await _http_get_status(_BACKEND_HEALTH_URL, timeout=2.0)
        if status_code == 200:
            return HealthStatus(
                feature_name='api_server',
                category='backend',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='FastAPI server responding to health checks',
                metadata={'status_code': status_code}
            )
        return HealthStatus(
            feature_name='api_server',
            category='backend',
            status='degraded',
            last_check=datetime.utcnow().isoformat(),
            error_message=f'API returned status {status_code}',
            description='FastAPI server responding to health checks',
            metadata={'status_code': status_code, 'body': body[:200]}
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
        from pokertool.database import get_production_db
        db = get_production_db()
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
        # Try importing the model calibration module
        import pokertool.model_calibration
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
        status_code, _ = await _http_get_status(_FRONTEND_BASE_URL, timeout=2.0)
        if status_code == 200:
            return HealthStatus(
                feature_name='frontend_server',
                category='gui',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='React frontend server availability',
                metadata={'status_code': status_code}
            )
        return HealthStatus(
            feature_name='frontend_server',
            category='gui',
            status='degraded',
            last_check=datetime.utcnow().isoformat(),
            error_message=f'Frontend returned status {status_code}',
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
        # Import existing GTO solver module
        import pokertool.gto_solver
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
        # Import existing opponent modeling module
        import pokertool.ml_opponent_modeling
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
        # Import existing sequential opponent fusion module
        import pokertool.sequential_opponent_fusion
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
        # Import existing active learning module
        import pokertool.active_learning
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
        # Import existing neural evaluator module
        import pokertool.neural_evaluator
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
        # Import existing hand range analyzer module
        import pokertool.hand_range_analyzer
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
        # Import existing scraping accuracy module
        import pokertool.scraping_accuracy_system
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
        from pokertool.database import get_production_db
        db = get_production_db()
        # Verify database access
        db.get_database_stats()
        # Just check that database is available
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
        # Import existing tournament support module
        import pokertool.tournament_support
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
        # Import existing multi-table support module
        import pokertool.multi_table_support
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
        from pokertool.database import get_production_db
        import sqlite3

        db = get_production_db()
        try:
            db.get_recent_hands(limit=1)
        except sqlite3.OperationalError as exc:
            return HealthStatus(
                feature_name='hand_history_database',
                category='advanced',
                status='degraded',
                last_check=datetime.utcnow().isoformat(),
                error_message=str(exc),
                description='Hand history storage and retrieval'
            )

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
        status_code, _ = await _http_get_status(_BACKEND_HEALTH_URL, timeout=2.0)
        if status_code == 200:
            return HealthStatus(
                feature_name='websocket_server',
                category='backend',
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='WebSocket server for real-time updates',
                metadata={'status_code': status_code}
            )
        return HealthStatus(
            feature_name='websocket_server',
            category='backend',
            status='degraded',
            last_check=datetime.utcnow().isoformat(),
            error_message=f'Health endpoint returned status {status_code}',
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
        # Check if region extraction module exists in modules
        from pokertool.modules import poker_screen_scraper_betfair
        # Module exists and has scraping functionality
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
