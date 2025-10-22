"""
Detection Accuracy Metrics Tracking
===================================

Track and measure accuracy of all detection operations over time.
Provides metrics for continuous improvement and quality monitoring.
"""

import time
import json
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from collections import deque
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class DetectionAccuracyMetrics:
    """Metrics for a single detection type."""
    total_detections: int = 0
    successful_detections: int = 0
    failed_detections: int = 0
    total_confidence: float = 0.0
    high_confidence_count: int = 0  # >= 0.8
    medium_confidence_count: int = 0  # 0.6-0.8
    low_confidence_count: int = 0  # < 0.6
    total_duration_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_detections == 0:
            return 0.0
        return self.successful_detections / self.total_detections
    
    @property
    def average_confidence(self) -> float:
        if self.successful_detections == 0:
            return 0.0
        return self.total_confidence / self.successful_detections
    
    @property
    def average_duration_ms(self) -> float:
        if self.total_detections == 0:
            return 0.0
        return self.total_duration_ms / self.total_detections

class DetectionAccuracyTracker:
    """
    Track detection accuracy metrics for continuous monitoring.
    
    Features:
    - Per-detection-type metrics
    - Rolling window statistics
    - Persistence to disk for historical analysis
    - Automatic alerts for accuracy drops
    """
    
    def __init__(self, window_size: int = 1000, metrics_dir: str = "logs/detection_metrics"):
        self.window_size = window_size
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics by detection type
        self.metrics: Dict[str, DetectionAccuracyMetrics] = {}
        
        # Recent detection history for rolling statistics
        self.recent_detections: Dict[str, deque] = {}
        
        # Alert thresholds
        self.min_success_rate = 0.9  # Alert if success rate drops below 90%
        self.min_avg_confidence = 0.7  # Alert if avg confidence drops below 70%
        
        logger.info(f"Detection accuracy tracker initialized - window size: {window_size}")
    
    def record_detection(
        self,
        detection_type: str,
        success: bool,
        confidence: float = 0.0,
        duration_ms: float = 0.0,
        metadata: Optional[Dict] = None
    ):
        """Record a detection attempt with result and confidence."""
        # Initialize metrics if needed
        if detection_type not in self.metrics:
            self.metrics[detection_type] = DetectionAccuracyMetrics()
            self.recent_detections[detection_type] = deque(maxlen=self.window_size)
        
        metrics = self.metrics[detection_type]
        metrics.total_detections += 1
        metrics.total_duration_ms += duration_ms
        
        if success:
            metrics.successful_detections += 1
            metrics.total_confidence += confidence
            
            # Categorize by confidence level
            if confidence >= 0.8:
                metrics.high_confidence_count += 1
            elif confidence >= 0.6:
                metrics.medium_confidence_count += 1
            else:
                metrics.low_confidence_count += 1
        else:
            metrics.failed_detections += 1
        
        # Add to recent detections for rolling statistics
        self.recent_detections[detection_type].append({
            'timestamp': time.time(),
            'success': success,
            'confidence': confidence,
            'duration_ms': duration_ms,
            'metadata': metadata or {}
        })
        
        # Check for alerts
        self._check_alerts(detection_type, metrics)
    
    def _check_alerts(self, detection_type: str, metrics: DetectionAccuracyMetrics):
        """Check if metrics have dropped below thresholds."""
        # Only alert after minimum number of detections
        if metrics.total_detections < 50:
            return
        
        if metrics.success_rate < self.min_success_rate:
            logger.warning(
                f"Detection accuracy alert: {detection_type} success rate dropped to "
                f"{metrics.success_rate:.2%} (threshold: {self.min_success_rate:.2%})"
            )
        
        if metrics.average_confidence < self.min_avg_confidence:
            logger.warning(
                f"Detection confidence alert: {detection_type} average confidence dropped to "
                f"{metrics.average_confidence:.2%} (threshold: {self.min_avg_confidence:.2%})"
            )
    
    def get_metrics(self, detection_type: Optional[str] = None) -> Dict:
        """Get current metrics for a specific type or all types."""
        if detection_type:
            if detection_type in self.metrics:
                return asdict(self.metrics[detection_type])
            return {}
        
        # Return all metrics
        return {
            dt: asdict(m) for dt, m in self.metrics.items()
        }
    
    def get_summary(self) -> Dict:
        """Get summary statistics across all detection types."""
        total_detections = sum(m.total_detections for m in self.metrics.values())
        total_successful = sum(m.successful_detections for m in self.metrics.values())
        total_confidence = sum(m.total_confidence for m in self.metrics.values())
        
        return {
            'total_detections': total_detections,
            'overall_success_rate': total_successful / total_detections if total_detections > 0 else 0,
            'overall_avg_confidence': total_confidence / total_successful if total_successful > 0 else 0,
            'detection_types': len(self.metrics),
            'by_type': {
                dt: {
                    'success_rate': m.success_rate,
                    'avg_confidence': m.average_confidence,
                    'avg_duration_ms': m.average_duration_ms,
                    'total_detections': m.total_detections
                }
                for dt, m in self.metrics.items()
            }
        }
    
    def save_metrics(self, filename: Optional[str] = None):
        """Save current metrics to disk."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'detection_metrics_{timestamp}.json'
        
        filepath = self.metrics_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': self.get_summary(),
                'metrics': self.get_metrics()
            }, f, indent=2)
        
        logger.info(f"Detection metrics saved to {filepath}")
    
    def reset(self, detection_type: Optional[str] = None):
        """Reset metrics for a specific type or all types."""
        if detection_type:
            if detection_type in self.metrics:
                self.metrics[detection_type] = DetectionAccuracyMetrics()
                self.recent_detections[detection_type].clear()
        else:
            self.metrics.clear()
            self.recent_detections.clear()

# Global tracker instance
_accuracy_tracker: Optional[DetectionAccuracyTracker] = None

def get_accuracy_tracker() -> DetectionAccuracyTracker:
    """Get or create the global accuracy tracker."""
    global _accuracy_tracker
    if _accuracy_tracker is None:
        _accuracy_tracker = DetectionAccuracyTracker()
    return _accuracy_tracker
