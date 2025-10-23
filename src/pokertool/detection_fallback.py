#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detection Fallback and Graceful Degradation
============================================

Provides fallback mechanisms and graceful degradation when detection fails.
Ensures the system continues operating with reduced functionality rather than crashing.

Module: pokertool.detection_fallback
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class DetectionMode(Enum):
    """Detection quality modes."""
    FULL = "full"               # All detection systems working
    PARTIAL = "partial"         # Some detection systems working
    MINIMAL = "minimal"         # Only critical detection working
    FALLBACK = "fallback"       # Using cached/estimated data
    OFFLINE = "offline"         # No detection available


@dataclass
class DetectionStatus:
    """Status of detection systems."""
    mode: DetectionMode
    available_features: List[str]
    last_successful_detection: Optional[float]  # Timestamp
    failure_count: int
    last_error: Optional[str]

    def is_operational(self) -> bool:
        """Check if system is operational."""
        return self.mode not in [DetectionMode.OFFLINE]

    def can_detect(self, feature: str) -> bool:
        """Check if specific feature is available."""
        return feature in self.available_features


class DetectionFallbackManager:
    """Manages fallback strategies when detection fails."""

    def __init__(self):
        self.status = DetectionStatus(
            mode=DetectionMode.FULL,
            available_features=['cards', 'pot', 'stacks', 'actions', 'players'],
            last_successful_detection=time.time(),
            failure_count=0,
            last_error=None
        )
        self.cached_state: Optional[Dict[str, Any]] = None
        self.failure_threshold = 3
        self.recovery_timeout = 60.0  # seconds

    def handle_detection_failure(
        self,
        error: Exception,
        detection_type: str,
        last_known_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle detection failure gracefully.

        Args:
            error: The exception that occurred
            detection_type: Type of detection that failed
            last_known_state: Last known valid state

        Returns:
            Fallback state or degraded state
        """
        self.status.failure_count += 1
        self.status.last_error = str(error)

        logger.warning(
            f"Detection failure #{self.status.failure_count} for {detection_type}: {error}"
        )

        # Update cached state if provided
        if last_known_state:
            self.cached_state = last_known_state

        # Degrade mode based on failure count
        if self.status.failure_count >= self.failure_threshold:
            self._degrade_mode()

        # Attempt recovery strategies
        fallback_state = self._get_fallback_state(detection_type, last_known_state)

        # Log degradation
        if self.status.mode != DetectionMode.FULL:
            logger.info(
                f"Operating in {self.status.mode.value} mode. "
                f"Available features: {self.status.available_features}"
            )

        return fallback_state

    def _degrade_mode(self):
        """Degrade detection mode based on failures."""
        if self.status.mode == DetectionMode.FULL:
            self.status.mode = DetectionMode.PARTIAL
            self.status.available_features = ['cards', 'pot', 'stacks']
            logger.warning("Degraded to PARTIAL mode - some features disabled")

        elif self.status.mode == DetectionMode.PARTIAL:
            self.status.mode = DetectionMode.MINIMAL
            self.status.available_features = ['cards', 'pot']
            logger.warning("Degraded to MINIMAL mode - only critical features")

        elif self.status.mode == DetectionMode.MINIMAL:
            self.status.mode = DetectionMode.FALLBACK
            self.status.available_features = []
            logger.error("Degraded to FALLBACK mode - using cached data only")

        elif self.status.mode == DetectionMode.FALLBACK:
            self.status.mode = DetectionMode.OFFLINE
            self.status.available_features = []
            logger.error("System OFFLINE - detection completely failed")

    def _get_fallback_state(
        self,
        detection_type: str,
        last_known_state: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get fallback state based on available data."""

        # Strategy 1: Use cached state with warning flag
        if self.cached_state:
            logger.info(f"Using cached state for {detection_type}")
            fallback = self.cached_state.copy()
            fallback['_fallback'] = True
            fallback['_fallback_reason'] = f'{detection_type} detection failed'
            fallback['_fallback_age'] = time.time() - self.status.last_successful_detection
            return fallback

        # Strategy 2: Use last known state
        if last_known_state:
            logger.info(f"Using last known state for {detection_type}")
            fallback = last_known_state.copy()
            fallback['_fallback'] = True
            fallback['_fallback_reason'] = 'No cached state available'
            return fallback

        # Strategy 3: Return minimal safe state
        logger.warning(f"No fallback data available for {detection_type}, using minimal state")
        return {
            '_fallback': True,
            '_fallback_reason': 'No prior state available',
            '_mode': self.status.mode.value,
            'error': str(self.status.last_error),
            'detection_type': detection_type
        }

    def record_successful_detection(self, detection_type: str, state: Dict[str, Any]):
        """Record successful detection to enable recovery."""
        self.status.last_successful_detection = time.time()
        self.cached_state = state.copy()

        # Attempt recovery if we're degraded
        if self.status.mode != DetectionMode.FULL:
            self._attempt_recovery()

    def _attempt_recovery(self):
        """Attempt to recover to better mode."""
        time_since_last_success = time.time() - self.status.last_successful_detection

        # Only recover if we've had recent success
        if time_since_last_success < self.recovery_timeout:
            if self.status.mode == DetectionMode.OFFLINE:
                self.status.mode = DetectionMode.FALLBACK
                logger.info("Recovered to FALLBACK mode")

            elif self.status.mode == DetectionMode.FALLBACK:
                self.status.mode = DetectionMode.MINIMAL
                self.status.available_features = ['cards', 'pot']
                logger.info("Recovered to MINIMAL mode")

            elif self.status.mode == DetectionMode.MINIMAL:
                self.status.mode = DetectionMode.PARTIAL
                self.status.available_features = ['cards', 'pot', 'stacks']
                logger.info("Recovered to PARTIAL mode")

            elif self.status.mode == DetectionMode.PARTIAL:
                self.status.mode = DetectionMode.FULL
                self.status.available_features = ['cards', 'pot', 'stacks', 'actions', 'players']
                self.status.failure_count = 0
                logger.info("Recovered to FULL mode")

    def reset(self):
        """Reset to full detection mode."""
        self.status = DetectionStatus(
            mode=DetectionMode.FULL,
            available_features=['cards', 'pot', 'stacks', 'actions', 'players'],
            last_successful_detection=time.time(),
            failure_count=0,
            last_error=None
        )
        logger.info("Detection system reset to FULL mode")

    def get_status(self) -> Dict[str, Any]:
        """Get current status information."""
        return {
            'mode': self.status.mode.value,
            'available_features': self.status.available_features,
            'failure_count': self.status.failure_count,
            'last_error': self.status.last_error,
            'last_successful_detection': self.status.last_successful_detection,
            'is_operational': self.status.is_operational()
        }


def with_fallback(fallback_manager: DetectionFallbackManager):
    """
    Decorator to add fallback handling to detection functions.

    Usage:
        @with_fallback(manager)
        def detect_cards(image):
            # Detection code that might fail
            pass
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Record success
                if isinstance(result, dict):
                    fallback_manager.record_successful_detection(
                        func.__name__,
                        result
                    )
                return result
            except Exception as e:
                logger.error(f"Detection failed in {func.__name__}: {e}")
                # Get last known state from kwargs or args
                last_state = kwargs.get('last_known_state') or \
                            (args[1] if len(args) > 1 and isinstance(args[1], dict) else None)

                return fallback_manager.handle_detection_failure(
                    e,
                    func.__name__,
                    last_state
                )
        return wrapper
    return decorator


# Global fallback manager instance
_global_fallback_manager: Optional[DetectionFallbackManager] = None


def get_fallback_manager() -> DetectionFallbackManager:
    """Get or create global fallback manager."""
    global _global_fallback_manager
    if _global_fallback_manager is None:
        _global_fallback_manager = DetectionFallbackManager()
    return _global_fallback_manager


def handle_detection_error(
    error: Exception,
    detection_type: str,
    last_known_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to handle detection errors.

    Args:
        error: The exception
        detection_type: Type of detection
        last_known_state: Last valid state

    Returns:
        Fallback state
    """
    manager = get_fallback_manager()
    return manager.handle_detection_failure(error, detection_type, last_known_state)


def record_detection_success(detection_type: str, state: Dict[str, Any]):
    """
    Convenience function to record successful detection.

    Args:
        detection_type: Type of detection
        state: Detected state
    """
    manager = get_fallback_manager()
    manager.record_successful_detection(detection_type, state)
