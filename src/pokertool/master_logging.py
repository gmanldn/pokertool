#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/pokertool/master_logging.py
# version: v28.1.0
# last_commit: '2025-01-10T17:10:00+00:00'
# fixes:
# - date: '2025-01-10'
#   summary: Master logging system with comprehensive error capture and data collection
# ---
# POKERTOOL-HEADER-END

"""
PokerTool Master Logging System
===============================

Centralized logging and error handling system that captures all errors
and routes them to a master log with comprehensive data collection.

Features:
- Unified logging across all components
- Structured error data collection
- Context-aware error capture
- Performance monitoring
- Security event logging
- Multiple output formats (JSON, text)
- Automatic log rotation
- Real-time error streaming
- Integration with existing systems

Module: pokertool.master_logging
Version: 28.1.0
Author: PokerTool Development Team
License: MIT
"""

from __future__ import annotations

import logging
import logging.handlers
import json
import sys
import os
import traceback
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from contextlib import contextmanager
from functools import wraps
import platform
import inspect
from dataclasses import dataclass, asdict
from enum import Enum

# Optional dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

__version__ = '28.1.0'
__author__ = 'PokerTool Development Team'

# Global configuration
MASTER_LOG_DIR = Path.cwd() / 'logs'
MASTER_LOG_FILE = MASTER_LOG_DIR / 'pokertool_master.log'  # 3-month rotation
ERROR_LOG_FILE = MASTER_LOG_DIR / 'pokertool_errors.log'    # Permanent (feedback system)
PERFORMANCE_LOG_FILE = MASTER_LOG_DIR / 'pokertool_performance.log'  # Permanent (feedback system)
SECURITY_LOG_FILE = MASTER_LOG_DIR / 'pokertool_security.log'  # Permanent (feedback system)

# Log Retention Policy:
# - MASTER_LOG: 3 months (90 days) - Daily rotation with automatic cleanup
# - ERROR_LOG: Permanent - Kept for feedback and analysis systems
# - PERFORMANCE_LOG: Permanent - Kept for feedback and analysis systems
# - SECURITY_LOG: Permanent - Kept for audit trail and security analysis

# Create logs directory
MASTER_LOG_DIR.mkdir(exist_ok=True)

class LogLevel(Enum):
    """Enhanced log levels with priorities."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    SECURITY = 60

class LogCategory(Enum):
    """Categories for different types of log entries."""
    GENERAL = "general"
    ERROR = "error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATABASE = "database"
    NETWORK = "network"
    GUI = "gui"
    ANALYSIS = "analysis"
    SOLVER = "solver"
    SCRAPER = "scraper"
    API = "api"

@dataclass
class LogContext:
    """Enhanced context information for log entries."""
    timestamp: str
    level: str
    category: str
    module: str
    function: str
    line_number: int
    thread_id: str
    process_id: int
    session_id: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # System information
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    disk_usage: float = 0.0
    
    # Application context
    table_count: int = 0
    active_sessions: int = 0
    current_hand: Optional[str] = None
    current_board: Optional[str] = None
    
    # Performance metrics
    execution_time: Optional[float] = None
    database_queries: int = 0
    api_calls: int = 0

@dataclass
class ErrorDetails:
    """Enhanced error information."""
    error_type: str
    error_message: str
    stack_trace: str
    error_hash: str  # For deduplication
    first_occurrence: str
    occurrence_count: int = 1
    
    # Context when error occurred
    input_data: Optional[Dict[str, Any]] = None
    system_state: Optional[Dict[str, Any]] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    
    # Impact assessment
    severity: str = "medium"
    affects_core_functionality: bool = False
    user_facing: bool = False

class MasterLogger:
    """
    Centralized master logging system for PokerTool.
    
    This class provides unified logging across all components with
    enhanced error capture, structured data collection, and multiple
    output formats.
    """
    
    _instance: Optional['MasterLogger'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        if MasterLogger._instance is not None:
            raise RuntimeError("Use MasterLogger.get_instance()")
        
        self.session_id = self._generate_session_id()
        self.error_cache: Dict[str, ErrorDetails] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        self.active_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Initialize loggers
        self._setup_loggers()
        
        # Start background monitoring
        self._start_monitoring()
        
        # Log system startup
        self.info("Master logging system initialized", category=LogCategory.GENERAL)
    
    @classmethod
    def get_instance(cls) -> 'MasterLogger':
        """Get or create the singleton master logger instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _setup_loggers(self):
        """Configure all logging handlers and formatters."""
        
        # Master logger (everything)
        self.master_logger = logging.getLogger('pokertool_master')
        self.master_logger.setLevel(logging.DEBUG)
        self.master_logger.handlers.clear()
        
        # Time-based rotating file handler for master log (keeps 3 months / 90 days)
        # Rotates daily and keeps 90 backup files = 90 days = ~3 months
        master_handler = logging.handlers.TimedRotatingFileHandler(
            MASTER_LOG_FILE,
            when='midnight',  # Rotate at midnight
            interval=1,       # Every 1 day
            backupCount=90,   # Keep 90 days = 3 months
            encoding='utf-8',
            delay=False,
            utc=False
        )
        master_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        master_handler.setFormatter(master_formatter)
        self.master_logger.addHandler(master_handler)

        # Add a note about log rotation to the log
        self.master_logger.info("Master log rotation configured: Daily rotation, 90 days retention (3 months)")
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        self.master_logger.addHandler(console_handler)
        
        # Error-specific logger
        self.error_logger = logging.getLogger('pokertool_errors')
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.handlers.clear()
        
        error_handler = logging.handlers.RotatingFileHandler(
            ERROR_LOG_FILE, maxBytes=20*1024*1024, backupCount=5
        )
        error_handler.setFormatter(self._get_json_formatter())
        self.error_logger.addHandler(error_handler)
        
        # Performance logger
        self.performance_logger = logging.getLogger('pokertool_performance')
        self.performance_logger.setLevel(logging.DEBUG)
        self.performance_logger.handlers.clear()
        
        perf_handler = logging.handlers.RotatingFileHandler(
            PERFORMANCE_LOG_FILE, maxBytes=10*1024*1024, backupCount=3
        )
        perf_handler.setFormatter(self._get_json_formatter())
        self.performance_logger.addHandler(perf_handler)
        
        # Security logger
        self.security_logger = logging.getLogger('pokertool_security')
        self.security_logger.setLevel(logging.WARNING)
        self.security_logger.handlers.clear()
        
        security_handler = logging.handlers.RotatingFileHandler(
            SECURITY_LOG_FILE, maxBytes=10*1024*1024, backupCount=5
        )
        security_handler.setFormatter(self._get_json_formatter())
        self.security_logger.addHandler(security_handler)
        
        # Redirect existing loggers to master system
        self._redirect_existing_loggers()
    
    def _get_json_formatter(self):
        """Create a JSON formatter for structured logging."""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_obj = {
                    'timestamp': self.formatTime(record),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'thread': record.thread,
                    'process': record.process,
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_obj['exception'] = self.formatException(record.exc_info)
                
                # Add extra context if available
                if hasattr(record, 'context'):
                    log_obj['context'] = record.context
                
                return json.dumps(log_obj, default=str)
        
        return JsonFormatter()
    
    def _redirect_existing_loggers(self):
        """Redirect existing loggers to use the master system."""
        # Get all existing loggers
        existing_loggers = [
            logging.getLogger('pokertool'),
            logging.getLogger('pokertool.error_handling'),
            logging.getLogger('pokertool.scrape'),
            logging.getLogger('pokertool.ocr_recognition'),
            logging.getLogger('pokertool.hud_overlay'),
            logging.getLogger('pokertool.api'),
            logging.getLogger('pokertool.concurrency'),
            logging.getLogger('pokertool.multi_table_support'),
            logging.getLogger('pokertool.production_database'),
            logging.getLogger('pokertool.game_selection'),
            logging.getLogger('pokertool.tournament_support'),
            logging.getLogger('pokertool.variance_calculator'),
        ]
        
        for logger in existing_loggers:
            # Clear existing handlers
            logger.handlers.clear()
            # Set parent to master logger
            logger.parent = self.master_logger
            logger.setLevel(logging.DEBUG)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"pokertool_{int(time.time())}_{os.getpid()}"
    
    def _get_context(self, category: LogCategory = LogCategory.GENERAL) -> LogContext:
        """Generate comprehensive context information."""
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the actual caller
            caller_frame = frame
            for _ in range(3):  # Adjust based on call stack depth
                caller_frame = caller_frame.f_back
                if caller_frame is None:
                    break
            
            if caller_frame:
                module_name = caller_frame.f_globals.get('__name__', 'unknown')
                function_name = caller_frame.f_code.co_name
                line_number = caller_frame.f_lineno
            else:
                module_name = 'unknown'
                function_name = 'unknown'
                line_number = 0
        finally:
            del frame
        
        # Get system metrics
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                cpu_usage = process.cpu_percent()
                disk_usage = psutil.disk_usage('/').percent
            except:
                memory_usage = cpu_usage = disk_usage = 0.0
        else:
            memory_usage = cpu_usage = disk_usage = 0.0
        
        return LogContext(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level="",  # Will be set by specific log methods
            category=category.value,
            module=module_name,
            function=function_name,
            line_number=line_number,
            thread_id=str(threading.current_thread().ident),
            process_id=os.getpid(),
            session_id=self.session_id,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            disk_usage=disk_usage,
            table_count=len(self.active_contexts),
            active_sessions=len([c for c in self.active_contexts.values() if c.get('active', False)]),
        )
    
    def _start_monitoring(self):
        """Start background system monitoring."""
        def monitor_loop():
            while True:
                try:
                    self._log_system_metrics()
                    time.sleep(60)  # Log metrics every minute
                except Exception as e:
                    self.error(f"System monitoring error: {e}", category=LogCategory.PERFORMANCE)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _log_system_metrics(self):
        """Log periodic system metrics."""
        try:
            metrics = {
                'active_threads': threading.active_count(),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            
            if PSUTIL_AVAILABLE:
                try:
                    metrics.update({
                        'memory_usage_mb': psutil.virtual_memory().used / 1024 / 1024,
                        'memory_percent': psutil.virtual_memory().percent,
                        'cpu_percent': psutil.cpu_percent(interval=1),
                        'disk_usage_percent': psutil.disk_usage('/').percent,
                        'open_file_descriptors': len(psutil.Process().open_files()),
                    })
                except Exception as psutil_error:
                    metrics['psutil_error'] = str(psutil_error)
            else:
                metrics['psutil_available'] = False
            
            self.performance_logger.info(
                json.dumps({
                    'event': 'system_metrics',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'metrics': metrics
                })
            )
        except Exception as e:
            self.error(f"Failed to log system metrics: {e}")
    
    def trace(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
        """Log trace level message."""
        self._log(LogLevel.TRACE, message, category, **kwargs)
    
    def debug(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
        """Log debug level message."""
        self._log(LogLevel.DEBUG, message, category, **kwargs)
    
    def info(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
        """Log info level message."""
        self._log(LogLevel.INFO, message, category, **kwargs)
    
    def warning(self, message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
        """Log warning level message."""
        self._log(LogLevel.WARNING, message, category, **kwargs)
    
    def error(self, message: str, category: LogCategory = LogCategory.ERROR, 
              exception: Optional[Exception] = None, **kwargs):
        """Log error level message with enhanced error tracking."""
        self._log(LogLevel.ERROR, message, category, exception=exception, **kwargs)
    
    def critical(self, message: str, category: LogCategory = LogCategory.ERROR, 
                 exception: Optional[Exception] = None, **kwargs):
        """Log critical level message."""
        self._log(LogLevel.CRITICAL, message, category, exception=exception, **kwargs)
    
    def security(self, message: str, **kwargs):
        """Log security-related events."""
        self._log(LogLevel.SECURITY, message, LogCategory.SECURITY, **kwargs)
    
    def _log(self, level: LogLevel, message: str, category: LogCategory, 
             exception: Optional[Exception] = None, **kwargs):
        """Internal logging method with full context capture."""
        
        context = self._get_context(category)
        context.level = level.name
        
        # Add any additional context from kwargs
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        # Create structured log entry
        log_entry = {
            'message': message,
            'context': asdict(context),
            'additional_data': {k: v for k, v in kwargs.items() if not hasattr(context, k)}
        }
        
        # Handle exceptions
        if exception:
            error_details = self._process_exception(exception, context, kwargs)
            log_entry['error_details'] = asdict(error_details)
        
        # Log to appropriate loggers
        log_record = logging.LogRecord(
            name=f"pokertool.{category.value}",
            level=level.value,
            pathname="",
            lineno=context.line_number,
            msg=message,
            args=(),
            exc_info=None
        )
        log_record.context = log_entry
        
        # Master logger gets everything
        self.master_logger.handle(log_record)
        
        # Route to specialized loggers
        if level.value >= LogLevel.ERROR.value:
            self.error_logger.handle(log_record)
        
        if category == LogCategory.PERFORMANCE:
            self.performance_logger.handle(log_record)
        
        if category == LogCategory.SECURITY or level == LogLevel.SECURITY:
            self.security_logger.handle(log_record)
    
    def _process_exception(self, exception: Exception, context: LogContext, 
                          additional_data: Dict[str, Any]) -> ErrorDetails:
        """Process and enhance exception information."""
        
        # Generate error hash for deduplication
        error_hash = hash(f"{type(exception).__name__}:{str(exception)}:{context.module}:{context.function}")
        error_hash_str = f"err_{abs(error_hash):x}"
        
        # Check if we've seen this error before
        if error_hash_str in self.error_cache:
            cached_error = self.error_cache[error_hash_str]
            cached_error.occurrence_count += 1
            return cached_error
        
        # Create new error details
        error_details = ErrorDetails(
            error_type=type(exception).__name__,
            error_message=str(exception),
            stack_trace=traceback.format_exc(),
            error_hash=error_hash_str,
            first_occurrence=context.timestamp,
            input_data=additional_data,
            system_state={
                'memory_usage': context.memory_usage,
                'cpu_usage': context.cpu_usage,
                'active_sessions': context.active_sessions,
                'current_hand': context.current_hand,
                'current_board': context.current_board,
            }
        )
        
        # Assess error severity
        error_details.severity = self._assess_error_severity(exception, context)
        error_details.affects_core_functionality = self._affects_core_functionality(exception, context)
        error_details.user_facing = self._is_user_facing_error(exception, context)
        
        # Cache the error
        self.error_cache[error_hash_str] = error_details
        
        return error_details
    
    def _assess_error_severity(self, exception: Exception, context: LogContext) -> str:
        """Assess the severity of an error based on type and context."""
        if isinstance(exception, (SystemExit, KeyboardInterrupt)):
            return "low"
        elif isinstance(exception, (MemoryError, OSError)):
            return "critical"
        elif isinstance(exception, (ValueError, TypeError, AttributeError)):
            return "medium"
        elif "database" in context.module.lower() or "storage" in context.module.lower():
            return "high"
        else:
            return "medium"
    
    def _affects_core_functionality(self, exception: Exception, context: LogContext) -> bool:
        """Determine if error affects core poker functionality."""
        core_modules = ['solver', 'analysis', 'gto', 'core', 'database', 'storage']
        return any(module in context.module.lower() for module in core_modules)
    
    def _is_user_facing_error(self, exception: Exception, context: LogContext) -> bool:
        """Determine if error is user-facing."""
        ui_modules = ['gui', 'api', 'hud', 'cli']
        return any(module in context.module.lower() for module in ui_modules)
    
    @contextmanager
    def operation_context(self, operation_name: str, **context_data):
        """Context manager for tracking operations with timing and error handling."""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        start_time = time.time()
        
        self.debug(f"Starting operation: {operation_name}", 
                  category=LogCategory.PERFORMANCE,
                  operation_id=operation_id,
                  **context_data)
        
        try:
            yield operation_id
            execution_time = time.time() - start_time
            self.info(f"Completed operation: {operation_name}",
                     category=LogCategory.PERFORMANCE,
                     operation_id=operation_id,
                     execution_time=execution_time,
                     **context_data)
        except Exception as e:
            execution_time = time.time() - start_time
            self.error(f"Failed operation: {operation_name}",
                      category=LogCategory.ERROR,
                      exception=e,
                      operation_id=operation_id,
                      execution_time=execution_time,
                      **context_data)
            raise
    
    def performance_timer(self, operation_name: str):
        """Decorator for timing function execution."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.operation_context(operation_name, function=func.__name__):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all captured errors."""
        return {
            'total_unique_errors': len(self.error_cache),
            'total_error_occurrences': sum(e.occurrence_count for e in self.error_cache.values()),
            'critical_errors': len([e for e in self.error_cache.values() if e.severity == 'critical']),
            'high_severity_errors': len([e for e in self.error_cache.values() if e.severity == 'high']),
            'core_functionality_errors': len([e for e in self.error_cache.values() if e.affects_core_functionality]),
            'user_facing_errors': len([e for e in self.error_cache.values() if e.user_facing]),
            'recent_errors': [
                {
                    'hash': e.error_hash,
                    'type': e.error_type,
                    'message': e.error_message[:100],
                    'count': e.occurrence_count,
                    'severity': e.severity
                }
                for e in sorted(self.error_cache.values(), 
                              key=lambda x: x.first_occurrence, reverse=True)[:10]
            ]
        }
    
    def flush_logs(self):
        """Force flush all log handlers."""
        for logger in [self.master_logger, self.error_logger, 
                      self.performance_logger, self.security_logger]:
            for handler in logger.handlers:
                handler.flush()

# Global instance
_master_logger = None

def get_master_logger() -> MasterLogger:
    """Get the global master logger instance."""
    global _master_logger
    if _master_logger is None:
        _master_logger = MasterLogger.get_instance()
    return _master_logger

# Convenience functions
def log_info(message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
    """Convenience function for info logging."""
    get_master_logger().info(message, category, **kwargs)

def log_error(message: str, exception: Optional[Exception] = None, 
              category: LogCategory = LogCategory.ERROR, **kwargs):
    """Convenience function for error logging."""
    get_master_logger().error(message, category, exception=exception, **kwargs)

def log_warning(message: str, category: LogCategory = LogCategory.GENERAL, **kwargs):
    """Convenience function for warning logging."""
    get_master_logger().warning(message, category, **kwargs)

def log_performance(operation: str, execution_time: float, **kwargs):
    """Convenience function for performance logging."""
    get_master_logger().info(f"Performance: {operation}",
                            category=LogCategory.PERFORMANCE,
                            execution_time=execution_time,
                            **kwargs)

def log_security_event(event: str, **kwargs):
    """Convenience function for security event logging."""
    get_master_logger().security(f"Security event: {event}", **kwargs)

# Decorator for automatic error logging
def auto_log_errors(category: LogCategory = LogCategory.GENERAL):
    """Decorator that automatically logs errors from functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(f"Error in {func.__name__}: {str(e)}", 
                         exception=e, category=category,
                         function_args=args, function_kwargs=kwargs)
                raise
        return wrapper
    return decorator

# Initialize the master logger when module is imported
try:
    get_master_logger()
except Exception as e:
    print(f"Warning: Failed to initialize master logger: {e}")
    # Fallback to basic logging
    logging.basicConfig(level=logging.INFO)
