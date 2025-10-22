"""Detection Result Cache with TTL"""
import time
import hashlib
from typing import Optional, Dict, Any
from collections import OrderedDict

class DetectionCache:
    """LRU cache for detection results with TTL."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: float = 2.0):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result if not expired."""
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                # Move to end (LRU)
                self.cache.move_to_end(key)
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Cache a result."""
        self.cache[key] = (value, time.time())
        self.cache.move_to_end(key)
        
        # Enforce size limit
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def hash_image_region(self, image_region) -> str:
        """Create hash key for image region."""
        return hashlib.md5(image_region.tobytes()).hexdigest()
    
    def clear(self):
        """Clear all cached results."""
        self.cache.clear()
