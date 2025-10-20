#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Trouble Feed - AI-Optimized Error and Warning Aggregator
==========================================================

Aggregates all errors and warnings from across the entire PokerTool application
into a single, AI-readable feed at /logs/trouble_feed.txt

This feed is designed to give AI maximum context for:
- Understanding what's broken
- Prioritizing fixes
- Making informed decisions about changes

Features:
- Human-readable but structured format
- Maximum detail including full stack traces
- Aggregates from all sources (backend, frontend, websocket, scraping, build)
- Automatic rotation to prevent file bloat
- Real-time appending for instant visibility
- Severity-based organization
- Context-rich entries

Module: pokertool.trouble_feed
Version: 94.0.0
"""

from __future__ import annotations

import os
import logging
import traceback
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
from collections import deque


# Configuration
TROUBLE_FEED_FILE = Path.cwd() / 'logs' / 'trouble_feed.txt'
MAX_FEED_SIZE_MB = 50  # Maximum file size before rotation
MAX_ENTRIES_IN_MEMORY = 1000  # Keep last N entries in memory for quick access
SEPARATOR = "=" * 100


class TroubleSeverity(Enum):
    """Severity levels for trouble feed entries"""
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TroubleSource(Enum):
    """Source of the trouble"""
    BACKEND = "Backend"
    FRONTEND = "Frontend"
    WEBSOCKET = "WebSocket"
    SCRAPER = "Scraper"
    DATABASE = "Database"
    API = "API"
    BUILD = "Build"
    SYSTEM = "System"
    UNKNOWN = "Unknown"


@dataclass
class TroubleEntry:
    """
    A single trouble feed entry with maximum detail for AI analysis
    """
    timestamp: str
    severity: TroubleSeverity
    source: TroubleSource
    module: str
    function: str
    line_number: int

    # The problem
    error_type: str
    error_message: str
    short_description: str

    # Full context
    stack_trace: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None

    # System state when error occurred
    system_state: Optional[Dict[str, Any]] = None

    # Additional metadata
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None

    # Analysis hints for AI
    suggested_fix: Optional[str] = None
    related_code_paths: Optional[List[str]] = None

    def to_readable_string(self) -> str:
        """
        Format as human and AI-readable text with maximum detail

        Example format:
        ================================================================================
        [2025-10-21 14:32:15 UTC] ERROR from Scraper
        --------------------------------------------------------------------------------
        Location: pokertool.scraper.detect_cards:142
        Error: ValueError - Invalid card format 'Xx' detected

        Description:
        Card detection failed during OCR processing of player hand at Table #3

        Stack Trace:
        Traceback (most recent call last):
          File "scraper.py", line 142, in detect_cards
            card = Card.from_string(text)
        ValueError: Invalid card format 'Xx'

        Context:
        - Table ID: table_3
        - OCR Text: "Xx 10h"
        - Confidence: 0.72
        - Attempt: 2/3

        System State:
        - Memory Usage: 245.3 MB
        - Active Tables: 3
        - Scraping FPS: 8.2

        AI Suggestion:
        1. Improve OCR preprocessing for edge detection
        2. Add validation for card text before parsing
        3. Implement retry with different OCR parameters

        Request ID: req_1729519935_abc123
        ================================================================================
        """
        lines = [SEPARATOR]

        # Header
        lines.append(f"[{self.timestamp}] {self.severity.value} from {self.source.value}")
        lines.append("-" * 100)

        # Location
        lines.append(f"Location: {self.module}::{self.function}:{self.line_number}")
        lines.append(f"Error: {self.error_type} - {self.error_message}")
        lines.append("")

        # Description
        if self.short_description:
            lines.append("Description:")
            lines.append(self.short_description)
            lines.append("")

        # Stack trace
        if self.stack_trace:
            lines.append("Stack Trace:")
            lines.append(self.stack_trace.strip())
            lines.append("")

        # Context
        if self.context_data:
            lines.append("Context:")
            for key, value in self.context_data.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        # System state
        if self.system_state:
            lines.append("System State:")
            for key, value in self.system_state.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        # AI suggestions
        if self.suggested_fix:
            lines.append("AI Suggestion:")
            for i, suggestion in enumerate(self.suggested_fix.split('\n'), 1):
                if suggestion.strip():
                    lines.append(f"{i}. {suggestion.strip()}")
            lines.append("")

        # Related code paths
        if self.related_code_paths:
            lines.append("Related Code Paths:")
            for path in self.related_code_paths:
                lines.append(f"- {path}")
            lines.append("")

        # IDs for correlation
        if self.request_id:
            lines.append(f"Request ID: {self.request_id}")
        if self.correlation_id:
            lines.append(f"Correlation ID: {self.correlation_id}")

        lines.append(SEPARATOR)
        lines.append("")  # Empty line between entries

        return "\n".join(lines)


class TroubleFeedHandler:
    """
    Centralized handler for the trouble feed that aggregates all errors/warnings
    from across the application into a single AI-optimized feed.
    """

    _instance: Optional['TroubleFeedHandler'] = None
    _lock = threading.Lock()

    def __init__(self):
        if TroubleFeedHandler._instance is not None:
            raise RuntimeError("Use TroubleFeedHandler.get_instance()")

        # Ensure logs directory exists
        TROUBLE_FEED_FILE.parent.mkdir(exist_ok=True)

        # In-memory cache of recent entries
        self.recent_entries: deque[TroubleEntry] = deque(maxlen=MAX_ENTRIES_IN_MEMORY)

        # Thread-safe file writing
        self._file_lock = threading.Lock()

        # Initialize the feed file with header
        self._initialize_feed_file()

        # Statistics
        self.stats = {
            'total_entries': 0,
            'warnings': 0,
            'errors': 0,
            'criticals': 0,
            'by_source': {},
        }

    @classmethod
    def get_instance(cls) -> 'TroubleFeedHandler':
        """Get or create the singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _initialize_feed_file(self):
        """Initialize the trouble feed file with a header"""
        if not TROUBLE_FEED_FILE.exists() or TROUBLE_FEED_FILE.stat().st_size == 0:
            header = f"""
{SEPARATOR}
POKERTOOL TROUBLE FEED
{SEPARATOR}

This file aggregates all errors and warnings from across the PokerTool application.
It is designed for AI analysis to understand problems and suggest fixes.

Format: Human-readable with maximum detail
Updated: Real-time as errors occur
Location: {TROUBLE_FEED_FILE}
Max Size: {MAX_FEED_SIZE_MB} MB (auto-rotates)

Last initialized: {datetime.now(timezone.utc).isoformat()}

{SEPARATOR}


"""
            with open(TROUBLE_FEED_FILE, 'w', encoding='utf-8') as f:
                f.write(header)

    def add_trouble(
        self,
        severity: TroubleSeverity,
        source: TroubleSource,
        module: str,
        function: str,
        line_number: int,
        error_type: str,
        error_message: str,
        short_description: str = "",
        stack_trace: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        system_state: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        related_code_paths: Optional[List[str]] = None,
    ):
        """
        Add a new trouble entry to the feed

        Args:
            severity: Severity level (WARNING, ERROR, CRITICAL)
            source: Source of the trouble (Backend, Frontend, etc.)
            module: Module/file where error occurred
            function: Function where error occurred
            line_number: Line number in source file
            error_type: Type of error (e.g., "ValueError", "NetworkError")
            error_message: The error message
            short_description: Brief human-readable description
            stack_trace: Full stack trace if available
            context_data: Additional context about what was happening
            system_state: System state when error occurred
            request_id: Request ID for correlation
            correlation_id: Correlation ID for distributed tracing
            user_id: User ID if applicable
            suggested_fix: AI-generated or predefined fix suggestion
            related_code_paths: List of related code files/functions
        """
        # Create entry
        entry = TroubleEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=severity,
            source=source,
            module=module,
            function=function,
            line_number=line_number,
            error_type=error_type,
            error_message=error_message,
            short_description=short_description,
            stack_trace=stack_trace,
            context_data=context_data or {},
            system_state=system_state or {},
            request_id=request_id,
            correlation_id=correlation_id,
            user_id=user_id,
            suggested_fix=suggested_fix,
            related_code_paths=related_code_paths or [],
        )

        # Add to in-memory cache
        self.recent_entries.append(entry)

        # Update statistics
        self.stats['total_entries'] += 1
        severity_key = severity.value.lower() + 's'
        self.stats[severity_key] = self.stats.get(severity_key, 0) + 1
        source_key = source.value
        self.stats['by_source'][source_key] = self.stats['by_source'].get(source_key, 0) + 1

        # Write to file (thread-safe)
        self._write_to_file(entry)

        # Check if rotation needed
        self._check_rotation()

    def _write_to_file(self, entry: TroubleEntry):
        """Write a trouble entry to the file"""
        with self._file_lock:
            try:
                with open(TROUBLE_FEED_FILE, 'a', encoding='utf-8') as f:
                    f.write(entry.to_readable_string())
                    f.flush()  # Ensure immediate write
            except Exception as e:
                # Fallback logging if we can't write to trouble feed
                logging.error(f"Failed to write to trouble feed: {e}")

    def _check_rotation(self):
        """Check if file needs rotation based on size"""
        try:
            file_size_mb = TROUBLE_FEED_FILE.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FEED_SIZE_MB:
                self._rotate_feed()
        except Exception as e:
            logging.error(f"Failed to check trouble feed rotation: {e}")

    def _rotate_feed(self):
        """Rotate the trouble feed file"""
        with self._file_lock:
            try:
                # Move current file to archive with timestamp
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                archive_name = TROUBLE_FEED_FILE.parent / f"trouble_feed_{timestamp}.txt"
                TROUBLE_FEED_FILE.rename(archive_name)

                # Reinitialize
                self._initialize_feed_file()

                # Add rotation notice
                with open(TROUBLE_FEED_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"[NOTICE] Previous feed archived to {archive_name}\n\n")

                logging.info(f"Trouble feed rotated to {archive_name}")
            except Exception as e:
                logging.error(f"Failed to rotate trouble feed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the trouble feed"""
        return self.stats.copy()

    def get_recent_entries(self, count: int = 50) -> List[TroubleEntry]:
        """Get the most recent trouble entries"""
        return list(self.recent_entries)[-count:]

    def clear_feed(self):
        """Clear the trouble feed (useful for testing)"""
        with self._file_lock:
            self._initialize_feed_file()
            self.recent_entries.clear()
            self.stats = {
                'total_entries': 0,
                'warnings': 0,
                'errors': 0,
                'criticals': 0,
                'by_source': {},
            }


# Global instance
def get_trouble_feed() -> TroubleFeedHandler:
    """Get the global trouble feed handler"""
    return TroubleFeedHandler.get_instance()


# Convenience functions for common use cases
def log_backend_error(
    error: Exception,
    module: str,
    function: str,
    line_number: int,
    description: str = "",
    context: Optional[Dict[str, Any]] = None,
    severity: TroubleSeverity = TroubleSeverity.ERROR
):
    """Log a backend Python error to the trouble feed"""
    handler = get_trouble_feed()
    handler.add_trouble(
        severity=severity,
        source=TroubleSource.BACKEND,
        module=module,
        function=function,
        line_number=line_number,
        error_type=type(error).__name__,
        error_message=str(error),
        short_description=description,
        stack_trace=traceback.format_exc(),
        context_data=context,
    )


def log_frontend_error(
    error_type: str,
    error_message: str,
    stack_trace: str,
    component: str,
    context: Optional[Dict[str, Any]] = None,
    severity: TroubleSeverity = TroubleSeverity.ERROR
):
    """Log a frontend JavaScript/React error to the trouble feed"""
    handler = get_trouble_feed()
    handler.add_trouble(
        severity=severity,
        source=TroubleSource.FRONTEND,
        module=component,
        function="",
        line_number=0,
        error_type=error_type,
        error_message=error_message,
        short_description=f"Frontend error in {component}",
        stack_trace=stack_trace,
        context_data=context or {},
    )


def log_scraper_warning(
    message: str,
    module: str,
    context: Optional[Dict[str, Any]] = None,
    suggested_fix: Optional[str] = None
):
    """Log a scraper warning to the trouble feed"""
    handler = get_trouble_feed()
    handler.add_trouble(
        severity=TroubleSeverity.WARNING,
        source=TroubleSource.SCRAPER,
        module=module,
        function="",
        line_number=0,
        error_type="ScraperWarning",
        error_message=message,
        short_description=message,
        context_data=context or {},
        suggested_fix=suggested_fix,
    )


def log_websocket_error(
    error: Exception,
    endpoint: str,
    context: Optional[Dict[str, Any]] = None
):
    """Log a WebSocket error to the trouble feed"""
    handler = get_trouble_feed()
    handler.add_trouble(
        severity=TroubleSeverity.ERROR,
        source=TroubleSource.WEBSOCKET,
        module=endpoint,
        function="",
        line_number=0,
        error_type=type(error).__name__,
        error_message=str(error),
        short_description=f"WebSocket error on {endpoint}",
        stack_trace=traceback.format_exc(),
        context_data=context or {},
    )


def log_build_error(
    error_message: str,
    file_path: str,
    line_number: int = 0,
    context: Optional[Dict[str, Any]] = None
):
    """Log a build error to the trouble feed"""
    handler = get_trouble_feed()
    handler.add_trouble(
        severity=TroubleSeverity.ERROR,
        source=TroubleSource.BUILD,
        module=file_path,
        function="build",
        line_number=line_number,
        error_type="BuildError",
        error_message=error_message,
        short_description=f"Build failed in {file_path}",
        context_data=context or {},
    )


# Integration with existing master_logging system
class TroubleFeedLogHandler(logging.Handler):
    """
    Custom logging handler that feeds warnings/errors into the trouble feed
    """

    def __init__(self):
        super().__init__()
        self.setLevel(logging.WARNING)  # Only capture warnings and above

    def emit(self, record: logging.LogRecord):
        """Process a log record and add to trouble feed if appropriate"""
        try:
            # Determine severity
            if record.levelno >= logging.CRITICAL:
                severity = TroubleSeverity.CRITICAL
            elif record.levelno >= logging.ERROR:
                severity = TroubleSeverity.ERROR
            else:
                severity = TroubleSeverity.WARNING

            # Determine source from logger name
            source = TroubleSource.UNKNOWN
            if 'scraper' in record.name or 'scrape' in record.name:
                source = TroubleSource.SCRAPER
            elif 'api' in record.name:
                source = TroubleSource.API
            elif 'websocket' in record.name or 'ws' in record.name:
                source = TroubleSource.WEBSOCKET
            elif 'database' in record.name or 'db' in record.name:
                source = TroubleSource.DATABASE
            else:
                source = TroubleSource.BACKEND

            # Extract context if available
            context = {}
            if hasattr(record, 'context'):
                context = getattr(record, 'context', {})

            # Get stack trace if exception
            stack_trace = None
            if record.exc_info:
                stack_trace = ''.join(traceback.format_exception(*record.exc_info))

            # Add to trouble feed
            handler = get_trouble_feed()
            handler.add_trouble(
                severity=severity,
                source=source,
                module=record.module,
                function=record.funcName,
                line_number=record.lineno,
                error_type=record.levelname,
                error_message=record.getMessage(),
                short_description=record.getMessage(),
                stack_trace=stack_trace,
                context_data=context,
            )
        except Exception:
            # Don't let trouble feed errors break logging
            pass


def setup_trouble_feed_integration():
    """
    Set up integration with existing logging systems
    Call this during application startup
    """
    # Add trouble feed handler to root logger
    root_logger = logging.getLogger()
    trouble_handler = TroubleFeedLogHandler()
    root_logger.addHandler(trouble_handler)

    # Initialize the trouble feed
    get_trouble_feed()

    logging.info("Trouble feed integration initialized")


if __name__ == '__main__':
    # Test the trouble feed
    print("Testing Trouble Feed...")

    handler = get_trouble_feed()

    # Test backend error
    try:
        raise ValueError("Invalid card format 'Xx'")
    except Exception as e:
        log_backend_error(
            error=e,
            module="pokertool.scraper",
            function="detect_cards",
            line_number=142,
            description="Card detection failed during OCR processing",
            context={
                "table_id": "table_3",
                "ocr_text": "Xx 10h",
                "confidence": 0.72,
                "attempt": "2/3"
            }
        )

    # Test frontend error
    log_frontend_error(
        error_type="TypeError",
        error_message="Cannot read property 'cards' of undefined",
        stack_trace="  at AdvicePanel.render (AdvicePanel.tsx:45)\n  at React.render",
        component="AdvicePanel",
        context={
            "props": "{ gameState: undefined }",
            "route": "/dashboard"
        }
    )

    # Test scraper warning
    log_scraper_warning(
        message="Low OCR confidence detected",
        module="pokertool.modules.ocr_engine",
        context={
            "confidence": 0.65,
            "threshold": 0.80,
            "text": "Ah Kc"
        },
        suggested_fix="Improve lighting conditions or adjust OCR preprocessing parameters"
    )

    print(f"\nTrouble feed created at: {TROUBLE_FEED_FILE}")
    print(f"Statistics: {handler.get_stats()}")
    print("\nCheck the file for formatted output!")
