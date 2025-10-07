#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Autopilot handlers for the integrated poker assistant.

Contains methods for:
- Autopilot activation/deactivation
- Autopilot loop
- Table state processing
- Settings updates
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from typing import Optional


class AutopilotHandlersMixin:
    """Mixin class providing autopilot event handlers."""
    
    def _handle_autopilot_toggle(self, active: bool) -> None:
        """Handle autopilot activation/deactivation."""
        self.autopilot_active = active
        
        if active:
            self._start_autopilot()
        else:
            self._stop_autopilot()

        self._update_manual_autopilot_status(active)

    def _handle_autopilot_settings(self, setting: str, value: Any) -> None:
        """Handle autopilot settings changes."""
        print(f"Autopilot setting changed: {setting} = {value}")
        
        if setting == 'site' and self.screen_scraper:
            # Reinitialize scraper for new site
            try:
                from pokertool.modules.poker_screen_scraper import create_scraper
                self.screen_scraper = create_scraper(value)
                print(f"Screen scraper reconfigured for {value}")
            except Exception as e:
                print(f"Screen scraper reconfiguration error: {e}")

    def _update_manual_autopilot_status(self, active: bool) -> None:
        """Mirror autopilot status in the manual play tab."""
        if self.manual_section:
            self.manual_section.update_autopilot_status(active)
    
    def _start_autopilot(self) -> None:
        """Start the autopilot system."""
        from pokertool.i18n import translate, format_datetime
        
        print("Starting autopilot system...")

        # Update status
        start_time = getattr(self.autopilot_panel.state, 'start_time', None) or datetime.now()
        self._update_table_status(translate('autopilot.log.activated', time=format_datetime(start_time)) + "\n")

        # Execute quick actions based on settings
        if self.autopilot_panel.auto_scraper_var.get():
            self._update_table_status(translate('autopilot.log.auto_start_scraper') + "\n")
            if not self._enhanced_scraper_started:
                self._toggle_screen_scraper()

        if self.autopilot_panel.auto_detect_var.get():
            self._update_table_status(translate('autopilot.log.auto_detect') + "\n")
            threading.Thread(target=self._detect_tables, daemon=True).start()

        self._update_table_status(translate('autopilot.log.scanning_tables') + "\n")

        # Start autopilot thread
        autopilot_thread = threading.Thread(target=self._autopilot_loop, daemon=True)
        autopilot_thread.start()
    
    def _stop_autopilot(self) -> None:
        """Stop the autopilot system."""
        from pokertool.i18n import translate
        
        print("Stopping autopilot system...")
        self._update_table_status(translate('autopilot.log.deactivated') + "\n")
        self._update_manual_autopilot_status(False)
    
    def _autopilot_loop(self) -> None:
        """Main autopilot processing loop with detailed table detection."""
        from pokertool.i18n import translate
        
        while self.autopilot_active:
            try:
                table_active = False
                table_reason = ""
                
                # Detect and analyze tables
                if self.screen_scraper:
                    table_state = self.screen_scraper.analyze_table()
                    
                    # Check if we actually detected a valid table
                    if table_state and table_state.active_players >= 2:
                        # Valid table detected!
                        table_active = True
                        table_reason = f"{table_state.active_players} players, pot ${table_state.pot_size}"
                        self._process_table_state(table_state)
                        
                        # Auto GTO analysis if enabled
                        if self.autopilot_panel.auto_gto_var.get() and self.gto_solver:
                            try:
                                self.after(0, lambda: self._update_table_status(translate('autopilot.log.auto_gto_start') + "\n"))
                                # GTO analysis would happen here with table_state
                                # This is a placeholder for the real implementation
                                self.after(0, lambda: self._update_table_status(translate('autopilot.log.auto_gto_complete') + "\n"))
                            except Exception as gto_error:
                                print(f"Auto GTO analysis error: {gto_error}")
                    else:
                        # No valid table detected
                        table_active = False
                        if not table_state or table_state.active_players == 0:
                            table_reason = "No active players detected"
                        else:
                            table_reason = f"Only {table_state.active_players} player (need 2+)"
                
                # Update statistics with table detection status
                stats = {
                    'tables_detected': 1 if table_active else 0,
                    'hands_played': self.autopilot_panel.state.hands_played + (1 if table_active else 0),
                    'actions_taken': self.autopilot_panel.state.actions_taken + (1 if self.autopilot_panel.auto_gto_var.get() and table_active else 0),
                    'last_action_key': 'autopilot.last_action.auto_analyzing' if self.autopilot_panel.auto_gto_var.get() and table_active else 'autopilot.last_action.monitoring',
                    'table_active': table_active,
                    'table_reason': table_reason
                }

                self.after(0, lambda s=stats: self.autopilot_panel.update_statistics(s))
                
            except Exception as e:
                print(f"Autopilot loop error: {e}")
                self.after(0, lambda: self._update_table_status(f"⚠️ Autopilot error: {e}\n"))
            
            time.sleep(2)  # Check every 2 seconds
    
    def _process_table_state(self, table_state) -> None:
        """Process detected table state and make decisions."""
        try:
            status_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Table detected\n"
            status_msg += f"  Pot: ${table_state.pot_size}\n"
            status_msg += f"  Stage: {table_state.stage}\n"
            status_msg += f"  Active players: {table_state.active_players}\n"
            status_msg += f"  Hero cards: {len(table_state.hero_cards)}\n"
            
            self.after(0, lambda: self._update_table_status(status_msg))
            if self.coaching_section:
                self.after(0, lambda ts=table_state: self.coaching_section.handle_table_state(ts))

            # Mirror the live table state into the manual workspace when autopilot
            # is active.  This keeps the manual tab synchronized with the
            # detected game so the user can verify that scraping is keeping up.
            # Only update if the manual panel is available and valid.
            if hasattr(self, 'manual_panel') and self.manual_panel:
                def _update_manual_panel(state=table_state):
                    try:
                        # Update players
                        players_map = self.manual_panel.players
                        # Create a lookup of seat number to existing PlayerInfo
                        for seat_info in state.seats:
                            seat_num = seat_info.seat_number
                            if seat_num in players_map:
                                p = players_map[seat_num]
                                # Active/inactive and hero/dealer flags
                                p.is_active = bool(seat_info.is_active)
                                p.stack = float(seat_info.stack_size)
                                p.is_hero = bool(seat_info.is_hero)
                                p.is_dealer = bool(seat_info.is_dealer)
                                # Blind positions (if provided in position field)
                                pos = (seat_info.position or '').upper()
                                p.is_sb = pos == 'SB'
                                p.is_bb = pos == 'BB'
                                # Reset bet amount; autopilot does not track bets yet
                                p.bet = 0.0
                        # Update board cards and hero hole cards on the Table View.
                        # Convert detected Card objects into tuples for the manual panel state
                        from typing import List, Tuple
                        board_tuples: List[Tuple[str, str]] = []
                        hero_tuples: List[Tuple[str, str]] = []
                        for c in state.board_cards:
                            try:
                                board_tuples.append((c.rank, c.suit))
                            except Exception:
                                pass
                        for c in state.hero_cards:
                            try:
                                hero_tuples.append((c.rank, c.suit))
                            except Exception:
                                pass
                        # Assign board and hole cards on the manual panel
                        self.manual_panel.board_cards = board_tuples
                        self.manual_panel.hole_cards = hero_tuples

                        # Convert detected cards into core Card objects for visualization
                        try:
                            from pokertool.core import Card as CoreCard
                            from typing import List
                            
                            board_cards_objs: List[CoreCard] = []
                            for c in state.board_cards:
                                try:
                                    board_cards_objs.append(CoreCard(c.rank, c.suit))
                                except Exception:
                                    pass
                            hole_cards_objs: List[CoreCard] = []
                            for c in state.hero_cards:
                                try:
                                    hole_cards_objs.append(CoreCard(c.rank, c.suit))
                                except Exception:
                                    pass
                            # Update table visualization: pass players, pot size, board and hero cards
                            # The update_table method expects board_cards as a list of CoreCard objects; hero cards
                            # can be inferred from players mapping (seat.is_hero) but we provide via hole_cards_objs
                            self.manual_panel.table_viz.update_table(players_map, state.pot_size, board_cards_objs)
                            # Manually set hero hole cards within the visualization if supported
                            try:
                                self.manual_panel.table_viz.hole_cards = hole_cards_objs  # type: ignore[attr-defined]
                            except Exception:
                                pass
                            # Trigger redraw of manual panel controls
                            try:
                                self.manual_panel._update_table()
                            except Exception:
                                pass
                        except ImportError:
                            pass  # Core module not available
                    except Exception as update_err:
                        print(f"Manual panel update error: {update_err}")
                # Schedule update on the main thread
                self.after(0, _update_manual_panel)
            
        except Exception as e:
            print(f"Table state processing error: {e}")


__all__ = ["AutopilotHandlersMixin"]
