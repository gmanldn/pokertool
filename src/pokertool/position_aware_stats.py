"""Position-aware statistics tracking."""
from collections import defaultdict

class PositionAwareStats:
    def __init__(self):
        self.stats = defaultdict(lambda: {"hands": 0, "vpip": 0, "pfr": 0})
    
    def record_hand(self, position: str, entered_pot: bool, raised_preflop: bool):
        """Record hand statistics by position."""
        self.stats[position]["hands"] += 1
        if entered_pot:
            self.stats[position]["vpip"] += 1
        if raised_preflop:
            self.stats[position]["pfr"] += 1
    
    def get_stats(self, position: str) -> dict:
        """Get statistics for a position."""
        s = self.stats[position]
        if s["hands"] == 0:
            return {"vpip": 0.0, "pfr": 0.0, "hands": 0}
        return {
            "vpip": s["vpip"] / s["hands"],
            "pfr": s["pfr"] / s["hands"],
            "hands": s["hands"]
        }
