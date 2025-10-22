"""Detection FPS Counter - Performance monitoring for detection system"""
import time
from collections import deque
from typing import Optional

class DetectionFPSCounter:
    """Track and calculate FPS for detection operations."""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.frame_times = deque(maxlen=window_size)
        self.last_frame_time = time.time()
        
    def tick(self):
        """Record a frame."""
        current_time = time.time()
        self.frame_times.append(current_time)
        self.last_frame_time = current_time
        
    def get_fps(self) -> float:
        """Calculate current FPS."""
        if len(self.frame_times) < 2:
            return 0.0
        time_span = self.frame_times[-1] - self.frame_times[0]
        if time_span == 0:
            return 0.0
        return (len(self.frame_times) - 1) / time_span
        
    def get_avg_frame_time_ms(self) -> float:
        """Get average frame time in milliseconds."""
        fps = self.get_fps()
        return (1000.0 / fps) if fps > 0 else 0.0

_global_fps_counter: Optional[DetectionFPSCounter] = None

def get_fps_counter() -> DetectionFPSCounter:
    global _global_fps_counter
    if _global_fps_counter is None:
        _global_fps_counter = DetectionFPSCounter()
    return _global_fps_counter
