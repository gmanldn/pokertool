"""Comprehensive Error Logging for Detection Events"""
import logging
from typing import Optional, Dict, Any
import traceback

logger = logging.getLogger('pokertool.detection.errors')

def log_detection_error(
    detection_type: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
):
    """Log detection error with full context."""
    context = context or {}
    logger.error(
        f"Detection error: {detection_type} | {type(error).__name__}: {str(error)} | "
        f"Context: {context}",
        exc_info=True,
        extra={'detection_type': detection_type, 'context': context}
    )
