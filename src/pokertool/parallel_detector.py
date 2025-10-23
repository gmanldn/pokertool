"""Parallel Detection Executor"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Callable, Any
import logging

logger = logging.getLogger(__name__)

class ParallelDetectionExecutor:
    """Execute independent detections in parallel."""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def detect_parallel(self, tasks: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Run detection tasks in parallel.
        
        Args:
            tasks: Dict of {name: callable} detection tasks
            
        Returns:
            Dict of {name: result}
        """
        futures = {
            self.executor.submit(task): name 
            for name, task in tasks.items()
        }
        
        results = {}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Parallel detection failed for {name}: {e}")
                results[name] = None
        
        return results
    
    def shutdown(self):
        """Shutdown executor."""
        self.executor.shutdown(wait=True)
