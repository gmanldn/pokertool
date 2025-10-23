#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Thread Cleanup Utilities
===================================

This module provides comprehensive thread cleanup and management utilities
to ensure clean startup and shutdown of the PokerTool application.

Module: pokertool.thread_cleanup
Version: 1.0.0
Last Modified: 2025-01-23
Author: PokerTool Development Team
License: MIT
"""

import threading
import logging
import atexit
import time
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ThreadInfo:
    """Information about a running thread."""
    name: str
    ident: Optional[int]
    daemon: bool
    is_alive: bool
    native_id: Optional[int] = None


class ThreadCleanupManager:
    """
    Centralized manager for thread cleanup and monitoring.

    This class provides utilities to track, monitor, and clean up threads
    throughout the application lifecycle.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._registered_threads: Set[str] = set()
        self._cleanup_handlers: List[callable] = []
        self._shutdown_in_progress = False

    def register_thread(self, thread_name: str) -> None:
        """Register a thread for tracking."""
        with self._lock:
            self._registered_threads.add(thread_name)
            logger.debug(f"Registered thread: {thread_name}")

    def unregister_thread(self, thread_name: str) -> None:
        """Unregister a thread."""
        with self._lock:
            self._registered_threads.discard(thread_name)
            logger.debug(f"Unregistered thread: {thread_name}")

    def register_cleanup_handler(self, handler: callable) -> None:
        """Register a cleanup handler to be called on shutdown."""
        with self._lock:
            self._cleanup_handlers.append(handler)
            logger.debug(f"Registered cleanup handler: {handler.__name__}")

    def get_all_threads(self) -> List[ThreadInfo]:
        """Get information about all running threads."""
        threads = []
        for thread in threading.enumerate():
            info = ThreadInfo(
                name=thread.name,
                ident=thread.ident,
                daemon=thread.daemon,
                is_alive=thread.is_alive(),
                native_id=getattr(thread, 'native_id', None)
            )
            threads.append(info)
        return threads

    def get_non_daemon_threads(self, exclude_main: bool = True) -> List[ThreadInfo]:
        """Get all non-daemon threads (optionally excluding main thread)."""
        main_thread = threading.main_thread()
        threads = []

        for thread in threading.enumerate():
            if thread.daemon:
                continue
            if exclude_main and thread == main_thread:
                continue

            info = ThreadInfo(
                name=thread.name,
                ident=thread.ident,
                daemon=thread.daemon,
                is_alive=thread.is_alive(),
                native_id=getattr(thread, 'native_id', None)
            )
            threads.append(info)

        return threads

    def get_pokertool_threads(self) -> List[ThreadInfo]:
        """Get all threads with 'PokerTool' in their name."""
        threads = []
        for thread in threading.enumerate():
            if 'PokerTool' in thread.name or 'pokertool' in thread.name.lower():
                info = ThreadInfo(
                    name=thread.name,
                    ident=thread.ident,
                    daemon=thread.daemon,
                    is_alive=thread.is_alive(),
                    native_id=getattr(thread, 'native_id', None)
                )
                threads.append(info)
        return threads

    def cleanup_dead_threads(self) -> int:
        """
        Clean up references to dead threads.

        Returns:
            Number of dead threads cleaned up
        """
        count = 0
        with self._lock:
            dead_threads = []
            for thread_name in self._registered_threads:
                # Check if thread still exists
                found = False
                for thread in threading.enumerate():
                    if thread.name == thread_name and thread.is_alive():
                        found = True
                        break

                if not found:
                    dead_threads.append(thread_name)

            for thread_name in dead_threads:
                self._registered_threads.discard(thread_name)
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} dead thread references")

        return count

    def shutdown_all(self, timeout: float = 5.0) -> Dict[str, any]:
        """
        Perform comprehensive shutdown of all managed resources.

        Args:
            timeout: Maximum time to wait for cleanup handlers

        Returns:
            Dictionary with shutdown statistics
        """
        with self._lock:
            if self._shutdown_in_progress:
                logger.warning("Shutdown already in progress")
                return {'status': 'already_in_progress'}

            self._shutdown_in_progress = True

        logger.info("Starting comprehensive thread cleanup")
        stats = {
            'cleanup_handlers_called': 0,
            'cleanup_handlers_failed': 0,
            'threads_found': 0,
            'non_daemon_threads': 0,
            'pokertool_threads': 0,
            'status': 'success'
        }

        # Call all registered cleanup handlers
        with self._lock:
            handlers = self._cleanup_handlers.copy()

        for handler in handlers:
            try:
                logger.debug(f"Calling cleanup handler: {handler.__name__}")
                handler()
                stats['cleanup_handlers_called'] += 1
            except Exception as e:
                logger.error(f"Cleanup handler {handler.__name__} failed: {e}")
                stats['cleanup_handlers_failed'] += 1

        # Get thread statistics
        all_threads = self.get_all_threads()
        non_daemon = self.get_non_daemon_threads()
        pokertool = self.get_pokertool_threads()

        stats['threads_found'] = len(all_threads)
        stats['non_daemon_threads'] = len(non_daemon)
        stats['pokertool_threads'] = len(pokertool)

        # Log thread information
        if non_daemon:
            logger.warning(f"Found {len(non_daemon)} non-daemon threads still running:")
            for thread_info in non_daemon:
                logger.warning(f"  - {thread_info.name} (alive: {thread_info.is_alive})")

        if pokertool:
            logger.info(f"Found {len(pokertool)} PokerTool threads:")
            for thread_info in pokertool:
                logger.info(f"  - {thread_info.name} (daemon: {thread_info.daemon}, alive: {thread_info.is_alive})")

        # Clean up dead thread references
        cleaned = self.cleanup_dead_threads()
        stats['dead_threads_cleaned'] = cleaned

        logger.info(f"Thread cleanup complete: {stats}")
        return stats

    def get_report(self) -> str:
        """Get a detailed report of current thread state."""
        all_threads = self.get_all_threads()
        non_daemon = self.get_non_daemon_threads()
        pokertool = self.get_pokertool_threads()

        report = []
        report.append("=" * 70)
        report.append("THREAD MANAGER REPORT")
        report.append("=" * 70)
        report.append(f"Total threads: {len(all_threads)}")
        report.append(f"Non-daemon threads: {len(non_daemon)}")
        report.append(f"PokerTool threads: {len(pokertool)}")
        report.append(f"Registered threads: {len(self._registered_threads)}")
        report.append(f"Cleanup handlers: {len(self._cleanup_handlers)}")
        report.append("")

        if non_daemon:
            report.append("Non-daemon threads:")
            for thread in non_daemon:
                report.append(f"  - {thread.name} (alive: {thread.is_alive})")
            report.append("")

        if pokertool:
            report.append("PokerTool threads:")
            for thread in pokertool:
                status = "daemon" if thread.daemon else "non-daemon"
                report.append(f"  - {thread.name} ({status}, alive: {thread.is_alive})")
            report.append("")

        report.append("=" * 70)
        return "\n".join(report)


# Global instance
_global_cleanup_manager: Optional[ThreadCleanupManager] = None
_manager_lock = threading.Lock()


def get_cleanup_manager() -> ThreadCleanupManager:
    """Get the global thread cleanup manager instance."""
    global _global_cleanup_manager

    if _global_cleanup_manager is None:
        with _manager_lock:
            if _global_cleanup_manager is None:
                _global_cleanup_manager = ThreadCleanupManager()
                logger.debug("Created global ThreadCleanupManager")

    return _global_cleanup_manager


def register_thread(thread_name: str) -> None:
    """Register a thread for tracking."""
    get_cleanup_manager().register_thread(thread_name)


def unregister_thread(thread_name: str) -> None:
    """Unregister a thread."""
    get_cleanup_manager().unregister_thread(thread_name)


def register_cleanup_handler(handler: callable) -> None:
    """Register a cleanup handler."""
    get_cleanup_manager().register_cleanup_handler(handler)


def cleanup_all_threads(timeout: float = 5.0) -> Dict[str, any]:
    """Perform comprehensive cleanup of all threads."""
    return get_cleanup_manager().shutdown_all(timeout)


def get_thread_report() -> str:
    """Get a detailed report of current thread state."""
    return get_cleanup_manager().get_report()


def get_all_threads() -> List[ThreadInfo]:
    """Get information about all running threads."""
    return get_cleanup_manager().get_all_threads()


def cleanup_on_startup() -> Dict[str, any]:
    """
    Clean up any orphaned resources on application startup.

    Returns:
        Dictionary with cleanup statistics
    """
    logger.info("Performing startup thread cleanup")

    manager = get_cleanup_manager()

    # Get initial state
    all_threads = manager.get_all_threads()
    non_daemon = manager.get_non_daemon_threads()
    pokertool = manager.get_pokertool_threads()

    stats = {
        'total_threads': len(all_threads),
        'non_daemon_threads': len(non_daemon),
        'pokertool_threads': len(pokertool),
        'dead_threads_cleaned': manager.cleanup_dead_threads()
    }

    if non_daemon:
        logger.warning(f"Found {len(non_daemon)} non-daemon threads at startup:")
        for thread in non_daemon:
            logger.warning(f"  - {thread.name}")

    if pokertool:
        logger.info(f"Found {len(pokertool)} PokerTool threads at startup:")
        for thread in pokertool:
            logger.info(f"  - {thread.name} (daemon: {thread.daemon})")

    logger.info(f"Startup cleanup complete: {stats}")
    return stats


# Register global cleanup handler
def _global_cleanup_handler():
    """Global cleanup handler for atexit."""
    logger.debug("Global cleanup handler triggered")
    try:
        cleanup_all_threads(timeout=3.0)
    except Exception as e:
        logger.error(f"Error in global cleanup handler: {e}")


atexit.register(_global_cleanup_handler)


# Export public API
__all__ = [
    'ThreadInfo',
    'ThreadCleanupManager',
    'get_cleanup_manager',
    'register_thread',
    'unregister_thread',
    'register_cleanup_handler',
    'cleanup_all_threads',
    'get_thread_report',
    'get_all_threads',
    'cleanup_on_startup',
]
