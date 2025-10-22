"""Detection Event Batcher - Batch events for efficient WebSocket transmission"""
import time
import threading
from typing import List, Dict, Any, Callable
from collections import deque

class DetectionEventBatcher:
    """Batch detection events to reduce WebSocket overhead."""
    
    def __init__(self, batch_interval: float = 0.1, max_batch_size: int = 50):
        self.batch_interval = batch_interval
        self.max_batch_size = max_batch_size
        self.event_queue = deque()
        self.lock = threading.Lock()
        self.running = False
        self.flush_callback: Callable[[List[Dict[str, Any]]], None] = lambda x: None
        
    def add_event(self, event: Dict[str, Any]):
        """Add event to batch."""
        with self.lock:
            self.event_queue.append(event)
            if len(self.event_queue) >= self.max_batch_size:
                self._flush()
                
    def _flush(self):
        """Flush current batch."""
        if not self.event_queue:
            return
        events = list(self.event_queue)
        self.event_queue.clear()
        self.flush_callback(events)
        
    def start(self, flush_callback: Callable[[List[Dict[str, Any]]], None]):
        """Start batching with callback."""
        self.flush_callback = flush_callback
        self.running = True
        
        def batch_worker():
            while self.running:
                time.sleep(self.batch_interval)
                with self.lock:
                    self._flush()
                    
        thread = threading.Thread(target=batch_worker, daemon=True)
        thread.start()
        
    def stop(self):
        """Stop batching and flush remaining events."""
        self.running = False
        with self.lock:
            self._flush()
