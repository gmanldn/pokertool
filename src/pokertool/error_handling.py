from __future__ import annotations

"""
error_handling.py — centralised error handling & logging (clean version).
"""
import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator
from functools import wraps

def _configure_logging() -> None:
    """Configure centralized logging for the application."""
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s %(levelname)s %(name)s :: %(message)s', 
        handlers=[logging.StreamHandler(sys.stderr)], 
        force=True, 
    )

_configure_logging()
log = logging.getLogger('pokertool')

def sanitize_input(input_str: str, max_length: int = 1000, allowed_chars: str = None) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        input_str: The input string to sanitize
        max_length: Maximum allowed length
        allowed_chars: String of allowed characters (None for basic alphanumeric + spaces)

    Returns:
        Sanitized string

    Raises:
        ValueError: If input is invalid or too long
    """
    if not isinstance(input_str, str):
        raise ValueError('Input must be a string')

    if len(input_str) > max_length:
        raise ValueError(f'Input too long: {len(input_str)} > {max_length}')

    if allowed_chars is None:
        # Allow alphanumeric, spaces, and common poker symbols
        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ♠♥♦♣AKQJT98765432-_"

    # Create set for faster lookup
    allowed_set = set(allowed_chars)
    sanitized = ''.join(c for c in input_str if c in allowed_set)

    if sanitized != input_str:
        log.warning('Input was sanitized, removed characters: %s', 
                   set(input_str) - set(sanitized))

    return sanitized

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function calls on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        log.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.2fs...",
                            attempt + 1, max_retries + 1,
                            func.__name__, e, current_delay
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        log.error('All %d attempts failed for %s',
                                max_retries + 1, func.__name__)
                        
            raise last_exception
        return wrapper
    return decorator

def run_safely(fn: Callable, *args, **kwargs) -> int:
    """
    Run a callable and catch all exceptions, logging a concise error.
    Return process exit code (0 on success, 1 on failure).
    """
    try:
        rv = fn(*args, **kwargs)
        return int(rv) if isinstance(rv, int) else 0
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 1
    except Exception as e:  # noqa: BLE001
        log.exception('Fatal error: %s', e)
        # Best-effort user-facing dialog if Tk is available
        try:
            import tkinter  # type: ignore
            import tkinter.messagebox  # type: ignore
            root = tkinter.Tk()
            root.withdraw()
            tkinter.messagebox.showerror('PokerTool error',
                                       f"A fatal error occurred: \n{e}")
            root.destroy()
        except Exception:  # noqa: BLE001
            pass
        return 1

@contextmanager
def db_guard(desc: str = 'DB operation') -> Iterator[None]:
    """
    Wrap short DB operations with error handling and logging.

    Example:
        with db_guard('saving decision'):
            storage.save_decision(...)
    """
    try:
        yield
    except Exception as e:  # noqa: BLE001
        log.exception('%s failed: %s', desc, e)
        raise

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for handling repeated failures.
    """
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        current_time = time.time()

        if self.state == 'OPEN':
            if current_time - self.last_failure_time >= self.timeout:
                self.state = 'HALF_OPEN'
                log.info('Circuit breaker moving to HALF_OPEN state')
            else:
                raise Exception('Circuit breaker is OPEN - too many recent failures')

        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.reset()
                log.info('Circuit breaker reset to CLOSED state')
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = current_time

            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                log.error('Circuit breaker opened due to %d failures',
                         self.failure_count)

            raise e

    def reset(self):
        """Reset the circuit breaker."""
        self.failure_count = 0
        self.state = 'CLOSED'
