#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Continuous screen update loop for the integrated poker assistant.

Manages the background thread that continuously fetches and displays
screen scraper updates.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class ScreenUpdateLoopMixin:
    """Mixin class providing screen update loop management."""
    
    def _start_screen_update_loop(self) -> None:
        """Start continuous screen update loop to follow scraper output."""
        if self._screen_update_running:
            return
        
        self._screen_update_running = True
        
        def update_loop():
            """Continuously fetch and display screen scraper updates."""
            update_count = 0
            while self._screen_update_running:
                try:
                    # Only update if scraper is active
                    if self._enhanced_scraper_started and self.autopilot_panel.continuous_update_var.get():
                        update_count += 1
                        
                        # Get scraper status and updates
                        try:
                            from pokertool.scrape import get_scraper_status
                            
                            status = get_scraper_status()
                            
                            if status and status.get('active'):
                                # Update display with latest info every 5 seconds
                                if update_count % 5 == 0:
                                    timestamp = datetime.now().strftime('%H:%M:%S')
                                    status_msg = f"[{timestamp}] 📊 Scraper Status:\n"
                                    status_msg += f"  • Active: Yes\n"
                                    status_msg += f"  • Updates: {update_count}\n"
                                    
                                    if 'last_capture_time' in status:
                                        status_msg += f"  • Last capture: {status['last_capture_time']}\n"
                                    
                                    if 'recognition_stats' in status:
                                        stats = status['recognition_stats']
                                        status_msg += f"  • Cards detected: {stats.get('cards_detected', 0)}\n"
                                        status_msg += f"  • Tables found: {stats.get('tables_found', 0)}\n"
                                    
                                    # Use after to safely update from thread
                                    self.after(0, lambda msg=status_msg: self._update_table_status(msg))
                            
                        except ImportError:
                            pass  # get_scraper_status not available
                        except Exception as e:
                            if update_count % 10 == 0:  # Log errors occasionally
                                print(f"Screen update error: {e}")
                    
                    # Check for basic scraper updates even without enhanced module
                    elif self.screen_scraper and update_count % 3 == 0:
                        try:
                            # Try to get basic table state
                            table_state = self.screen_scraper.analyze_table()
                            if table_state and table_state.pot_size > 0:
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                msg = f"[{timestamp}] 🎰 Table detected: Pot ${table_state.pot_size}\n"
                                self.after(0, lambda m=msg: self._update_table_status(m))
                        except Exception as e:
                            pass  # Silently continue on errors
                    
                    time.sleep(2)  # Update every 2 seconds (optimized for performance)
                    
                except Exception as e:
                    print(f"Update loop error: {e}")
                    time.sleep(2)  # Back off on errors
        
        # Start update thread
        self._screen_update_thread = threading.Thread(target=update_loop, daemon=True)
        self._screen_update_thread.start()
        print("Screen update loop started - display will follow scraper continuously")
    
    def _stop_screen_update_loop(self) -> None:
        """Stop the continuous screen update loop."""
        self._screen_update_running = False
        if self._screen_update_thread:
            print("Stopping screen update loop...")


__all__ = ["ScreenUpdateLoopMixin"]
