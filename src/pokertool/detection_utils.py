"""Detection Utility Functions"""

from typing import List, Dict, Any, Optional
import time


def format_confidence_percent(confidence: float) -> str:
    """Format confidence as percentage string."""
    return f"{confidence * 100:.1f}%"


def classify_confidence(confidence: float) -> str:
    """Classify confidence level."""
    if confidence >= 0.9:
        return "VERY_HIGH"
    elif confidence >= 0.8:
        return "HIGH"
    elif confidence >= 0.6:
        return "MEDIUM"
    elif confidence >= 0.4:
        return "LOW"
    else:
        return "VERY_LOW"


def calculate_success_rate(successful: int, total: int) -> float:
    """Calculate success rate percentage."""
    if total == 0:
        return 0.0
    return (successful / total) * 100


def format_duration(duration_ms: float) -> str:
    """Format duration in human-readable form."""
    if duration_ms < 1:
        return f"{duration_ms * 1000:.0f}μs"
    elif duration_ms < 1000:
        return f"{duration_ms:.1f}ms"
    else:
        return f"{duration_ms / 1000:.2f}s"


def merge_detection_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple detection results using highest confidence."""
    if not results:
        return {}

    best_result = max(results, key=lambda r: r.get('confidence', 0))
    return best_result


def calculate_average_confidence(detections: List[Dict[str, Any]]) -> float:
    """Calculate average confidence from multiple detections."""
    if not detections:
        return 0.0

    total_confidence = sum(d.get('confidence', 0) for d in detections)
    return total_confidence / len(detections)


def timestamp_ms() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)
