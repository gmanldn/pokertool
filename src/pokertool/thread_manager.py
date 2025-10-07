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
from typing import Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, Future
import logging

logger = logging.getLogger(__name__)

class ThreadManager:
    """Manages application threads and thread pools."""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_threads: Dict[str, threading.Thread] = {}
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
    
    def start_thread(self, name: str, target: Callable, *args, **kwargs) -> threading.Thread:
        """Start a named thread."""
        thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        thread.name = name
        self.active_threads[name] = thread
        thread.start()
        return thread
    
    def stop_thread(self, name: str) -> bool:
        """Stop a named thread."""
        if name in self.active_threads:
            thread = self.active_threads[name]
            if thread.is_alive():
                # Note: Python doesn't support forceful thread termination
                # The thread should check for stop conditions internally
                logger.warning(f"Cannot forcefully stop thread {name}. Thread should check stop conditions.")
                return False
            else:
                del self.active_threads[name]
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get thread pool statistics."""
        return self.thread_stats.copy()
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None):
        """Shutdown the thread pool."""
        self.executor.shutdown(wait=wait, timeout=timeout)

# Global thread manager instance
_global_thread_manager: Optional[ThreadManager] = None

def get_thread_manager() -> ThreadManager:
    """Get the global thread manager instance."""
    global _global_thread_manager
    if _global_thread_manager is None:
        _global_thread_manager = ThreadManager()
    return _global_thread_manager

def submit_task(func: Callable, *args, **kwargs) -> Future:
    """Submit a task to the global thread pool."""
    return get_thread_manager().submit_task(func, *args, **kwargs)

def start_thread(name: str, target: Callable, *args, **kwargs) -> threading.Thread:
    """Start a named thread using the global manager."""
    return get_thread_manager().start_thread(name, target, *args, **kwargs)
