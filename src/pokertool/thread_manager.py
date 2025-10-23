#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Threading Module
=========================

This module provides threading utilities for the PokerTool application.

Module: pokertool.thread_manager
Version: 1.0.0
Last Modified: 2025-01-07
Author: PokerTool Development Team
License: MIT
"""

import threading
import time
import atexit
import signal
import sys
from typing import Dict, Any, Callable, Optional, Set
from concurrent.futures import ThreadPoolExecutor, Future
import logging
import weakref

logger = logging.getLogger(__name__)

class ThreadManager:
    """Manages application threads and thread pools with comprehensive lifecycle management."""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PokerTool-Worker")
        self.active_threads: Dict[str, threading.Thread] = {}
        self._thread_stop_events: Dict[str, threading.Event] = {}
        self._lock = threading.RLock()
        self._shutdown_requested = False
        self.thread_stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'active_tasks': 0,
            'queue_size': 0,
            'avg_execution_time': 0.0,
            'worker_threads': 0,
            'max_workers': max_workers
        }
        
    def submit_task(self, func: Callable, *args, **kwargs) -> Future:
        """Submit a task to the thread pool."""
        self.thread_stats['submitted'] += 1
        return self.executor.submit(func, *args, **kwargs)
    
    def start_thread(self, name: str, target: Callable, stop_event: Optional[threading.Event] = None,
                     *args, **kwargs) -> threading.Thread:
        """
        Start a named thread with proper tracking and lifecycle management.

        Args:
            name: Unique name for the thread
            target: Callable to run in the thread
            stop_event: Optional Event for signaling thread to stop
            *args, **kwargs: Arguments to pass to target

        Returns:
            The started Thread object
        """
        with self._lock:
            if self._shutdown_requested:
                logger.warning(f"Refusing to start thread '{name}' - shutdown in progress")
                raise RuntimeError("ThreadManager is shutting down")

            # Clean up any old thread with same name
            if name in self.active_threads:
                old_thread = self.active_threads[name]
                if not old_thread.is_alive():
                    del self.active_threads[name]
                    if name in self._thread_stop_events:
                        del self._thread_stop_events[name]
                else:
                    logger.warning(f"Thread '{name}' already running - stopping old instance")
                    self.stop_thread(name, timeout=2.0)

            # Create stop event if not provided
            if stop_event is None:
                stop_event = threading.Event()

            thread = threading.Thread(
                target=target,
                args=args,
                kwargs=kwargs,
                daemon=True,
                name=f"PokerTool-{name}"
            )

            self.active_threads[name] = thread
            self._thread_stop_events[name] = stop_event
            thread.start()
            logger.debug(f"Started thread: {name}")
            return thread
    
    def stop_thread(self, name: str, timeout: float = 5.0) -> bool:
        """
        Stop a named thread by signaling its stop event and waiting for completion.

        Args:
            name: Name of the thread to stop
            timeout: Maximum time to wait for thread to stop (seconds)

        Returns:
            True if thread stopped successfully, False otherwise
        """
        with self._lock:
            if name not in self.active_threads:
                return True  # Thread doesn't exist, consider it stopped

            thread = self.active_threads[name]
            stop_event = self._thread_stop_events.get(name)

            if not thread.is_alive():
                # Thread already stopped, clean up
                del self.active_threads[name]
                if name in self._thread_stop_events:
                    del self._thread_stop_events[name]
                return True

            # Signal the thread to stop
            if stop_event:
                stop_event.set()
                logger.debug(f"Signaled stop event for thread: {name}")

        # Wait outside the lock to avoid deadlock
        thread.join(timeout=timeout)

        with self._lock:
            if thread.is_alive():
                logger.warning(
                    f"Thread '{name}' did not stop within {timeout}s. "
                    f"Thread should check stop conditions regularly."
                )
                return False
            else:
                # Clean up
                if name in self.active_threads:
                    del self.active_threads[name]
                if name in self._thread_stop_events:
                    del self._thread_stop_events[name]
                logger.debug(f"Successfully stopped thread: {name}")
                return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get thread pool statistics."""
        with self._lock:
            stats = self.thread_stats.copy()
            stats['active_threads_count'] = len(self.active_threads)
            stats['active_thread_names'] = list(self.active_threads.keys())
            return stats

    def get_active_threads(self) -> Dict[str, threading.Thread]:
        """Get a copy of currently active threads."""
        with self._lock:
            return self.active_threads.copy()

    def stop_all_threads(self, timeout: float = 5.0) -> int:
        """
        Stop all active threads gracefully.

        Args:
            timeout: Maximum time to wait for each thread (seconds)

        Returns:
            Number of threads that failed to stop
        """
        with self._lock:
            thread_names = list(self.active_threads.keys())

        failed_count = 0
        for name in thread_names:
            if not self.stop_thread(name, timeout=timeout):
                failed_count += 1

        return failed_count

    def cleanup_dead_threads(self) -> int:
        """
        Clean up threads that have stopped running.

        Returns:
            Number of dead threads cleaned up
        """
        with self._lock:
            dead_threads = [
                name for name, thread in self.active_threads.items()
                if not thread.is_alive()
            ]

            for name in dead_threads:
                del self.active_threads[name]
                if name in self._thread_stop_events:
                    del self._thread_stop_events[name]

            if dead_threads:
                logger.debug(f"Cleaned up {len(dead_threads)} dead threads")

            return len(dead_threads)

    def shutdown(self, wait: bool = True, timeout: Optional[float] = 5.0):
        """
        Shutdown the thread manager - stops all threads and executor.

        Args:
            wait: Block until all submitted tasks complete.
            timeout: Maximum time to wait for threads to stop (seconds)
        """
        with self._lock:
            if self._shutdown_requested:
                logger.debug("Shutdown already in progress")
                return
            self._shutdown_requested = True

        logger.info("ThreadManager shutdown initiated")

        # Stop all managed threads
        failed = self.stop_all_threads(timeout=timeout or 5.0)
        if failed > 0:
            logger.warning(f"{failed} threads did not stop cleanly")

        # Shutdown the executor
        try:
            self.executor.shutdown(wait=wait)
            logger.info("ThreadPoolExecutor shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down executor: {e}")

# Global thread manager instance
_global_thread_manager: Optional[ThreadManager] = None
_manager_lock = threading.Lock()
_shutdown_in_progress = False

def get_thread_manager() -> ThreadManager:
    """Get the global thread manager instance."""
    global _global_thread_manager
    if _global_thread_manager is None:
        with _manager_lock:
            if _global_thread_manager is None:
                _global_thread_manager = ThreadManager()
                logger.debug("Created global ThreadManager instance")
    return _global_thread_manager

def submit_task(func: Callable, *args, **kwargs) -> Future:
    """Submit a task to the global thread pool."""
    return get_thread_manager().submit_task(func, *args, **kwargs)

def start_thread(name: str, target: Callable, stop_event: Optional[threading.Event] = None,
                 *args, **kwargs) -> threading.Thread:
    """Start a named thread using the global manager."""
    return get_thread_manager().start_thread(name, target, stop_event, *args, **kwargs)

def stop_thread(name: str, timeout: float = 5.0) -> bool:
    """Stop a named thread using the global manager."""
    return get_thread_manager().stop_thread(name, timeout)

def get_active_threads() -> Dict[str, threading.Thread]:
    """Get all active threads from the global manager."""
    return get_thread_manager().get_active_threads()

def cleanup_dead_threads() -> int:
    """Clean up dead threads from the global manager."""
    return get_thread_manager().cleanup_dead_threads()

def shutdown_thread_manager(wait: bool = True, timeout: Optional[float] = 5.0) -> None:
    """Shutdown and clear the global thread manager if it has been initialised."""
    global _global_thread_manager, _shutdown_in_progress

    with _manager_lock:
        if _shutdown_in_progress:
            logger.debug("Shutdown already in progress")
            return

        if _global_thread_manager is None:
            return

        _shutdown_in_progress = True

    try:
        logger.info("Shutting down global ThreadManager")
        _global_thread_manager.shutdown(wait=wait, timeout=timeout)
    except Exception as exc:
        logger.warning("Failed to shutdown thread manager cleanly: %s", exc)
    finally:
        with _manager_lock:
            _global_thread_manager = None
            _shutdown_in_progress = False
        logger.info("Global ThreadManager shutdown complete")

# Register cleanup handlers
def _cleanup_on_exit():
    """Cleanup handler called on program exit."""
    logger.debug("atexit handler triggered - shutting down ThreadManager")
    shutdown_thread_manager(wait=True, timeout=3.0)

def _cleanup_on_signal(signum, frame):
    """Signal handler for graceful shutdown."""
    logger.info(f"Received signal {signum} - initiating graceful shutdown")
    shutdown_thread_manager(wait=True, timeout=3.0)
    sys.exit(0)

# Register handlers
atexit.register(_cleanup_on_exit)

# Register signal handlers (only on Unix-like systems)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, _cleanup_on_signal)
if hasattr(signal, 'SIGINT'):
    # Save original SIGINT handler for keyboard interrupt
    _original_sigint = signal.getsignal(signal.SIGINT)

    def _sigint_handler(signum, frame):
        logger.info("Received SIGINT - initiating graceful shutdown")
        shutdown_thread_manager(wait=True, timeout=2.0)
        # Call original handler if it exists
        if callable(_original_sigint):
            _original_sigint(signum, frame)
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint_handler)
