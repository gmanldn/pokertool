"""Detection State Persistence Across Sessions"""
import json
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class DetectionStatePersistence:
    def __init__(self, state_file: str = "logs/detection_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_state(self, state: Dict) -> None:
        """Save detection state to disk."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"Detection state saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save detection state: {e}")
    
    def load_state(self) -> Optional[Dict]:
        """Load detection state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load detection state: {e}")
        return None
