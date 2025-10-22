"""Error Recovery System for AI Agents - Automatic retry with exponential backoff"""
import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator for automatic retry with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

class ErrorRecoveryManager:
    """Manages error recovery for AI agent operations"""
    def __init__(self, max_retries: int = 3, skip_after: int = 3):
        self.max_retries = max_retries
        self.skip_after = skip_after
        self.failure_counts = {}
    
    def should_skip_task(self, task_id: str) -> bool:
        """Check if task should be skipped due to repeated failures"""
        return self.failure_counts.get(task_id, 0) >= self.skip_after
    
    def record_failure(self, task_id: str):
        """Record task failure"""
        self.failure_counts[task_id] = self.failure_counts.get(task_id, 0) + 1
    
    def record_success(self, task_id: str):
        """Reset failure count on success"""
        self.failure_counts[task_id] = 0
    
    def get_failure_count(self, task_id: str) -> int:
        """Get current failure count for task"""
        return self.failure_counts.get(task_id, 0)
