"""Player seat change detection."""
import logging

class SeatChangeDetector:
    def __init__(self):
        self.player_seats = {}
    
    def detect_seat_change(self, player_id: str, new_seat: int) -> bool:
        """Detect if player changed seats."""
        old_seat = self.player_seats.get(player_id)
        if old_seat is None:
            self.player_seats[player_id] = new_seat
            return False
        
        if old_seat != new_seat:
            self.player_seats[player_id] = new_seat
            return True
        return False
