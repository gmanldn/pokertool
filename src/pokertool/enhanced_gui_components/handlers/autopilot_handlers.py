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

# Import master logger for comprehensive logging
try:
    from pokertool.master_logging import get_master_logger, LogCategory
    MASTER_LOGGER_AVAILABLE = True
except ImportError:
    MASTER_LOGGER_AVAILABLE = False
    print("Warning: Master logger not available")


class AutopilotHandlersMixin:
    """Mixin class providing autopilot event handlers."""

    def _is_valid_table(self, table_state) -> bool:
        """
        Strict validation to determine if detected table is actually active.

        Prevents false positives by checking multiple criteria:
        - Minimum 2 active players
        - Minimum confidence threshold (if available)
        - Valid blinds or pot size
        - Reasonable stack sizes
        """
        # Check basic player count
        if not table_state or table_state.active_players < 2:
            return False

        # Check confidence score if available
        confidence = getattr(table_state, 'confidence', 0)
        if confidence > 0 and confidence < 50:  # Less than 50% confidence
            return False

        # Check that we have valid blind structure OR non-zero pot
        has_valid_blinds = (
            getattr(table_state, 'small_blind', 0) > 0 and
            getattr(table_state, 'big_blind', 0) > 0
        )
        has_pot = table_state.pot_size > 0

        if not (has_valid_blinds or has_pot):
            return False

        # Check that at least one player has a reasonable stack
        if hasattr(table_state, 'seats'):
            total_stacks = sum(
                getattr(seat, 'stack_size', 0)
                for seat in table_state.seats
                if getattr(seat, 'is_active', False)
            )
            if total_stacks <= 0:
                return False

        # All validation passed
        return True

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

                    # STRICT validation criteria to prevent false positives
                    if table_state and self._is_valid_table(table_state):
                        # Valid table detected!
                        table_active = True
                        table_reason = f"{table_state.active_players} players, pot ${table_state.pot_size}, confidence {getattr(table_state, 'confidence', 0):.1f}%"

                        # Log detailed detection to GUI
                        detection_log = f"\n{'='*60}\n"
                        detection_log += f"🎯 TABLE DETECTED - {datetime.now().strftime('%H:%M:%S')}\n"
                        detection_log += f"{'='*60}\n"
                        detection_log += f"  Confidence: {getattr(table_state, 'confidence', 0):.1f}%\n"
                        detection_log += f"  Players: {table_state.active_players}\n"
                        detection_log += f"  Pot: ${table_state.pot_size:.2f}\n"
                        detection_log += f"  Stage: {table_state.stage}\n"
                        detection_log += f"  Hero Cards: {table_state.hero_cards if table_state.hero_cards else 'None'}\n"
                        detection_log += f"  Board: {table_state.board_cards if table_state.board_cards else 'None'}\n"
                        detection_log += f"{'='*60}\n"
                        self.after(0, lambda log=detection_log: self._update_table_status(log))

                        # Log to master logger (permanent record)
                        if MASTER_LOGGER_AVAILABLE:
                            logger = get_master_logger()
                            logger.info(
                                f"Table detected: {table_state.active_players} players, pot ${table_state.pot_size:.2f}",
                                category=LogCategory.SCRAPER,
                                confidence=getattr(table_state, 'confidence', 0),
                                active_players=table_state.active_players,
                                pot_size=table_state.pot_size,
                                stage=table_state.stage,
                                hero_cards=str(table_state.hero_cards) if table_state.hero_cards else None,
                                board_cards=str(table_state.board_cards) if table_state.board_cards else None
                            )

                        self._process_table_state(table_state)

                        # Auto GTO analysis (now always enabled)
                        if self.gto_solver:
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
                    'actions_taken': self.autopilot_panel.state.actions_taken + (1 if table_active else 0),
                    'last_action_key': 'autopilot.last_action.auto_analyzing' if table_active else 'autopilot.last_action.monitoring',
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
            # Build detailed hand information log
            status_msg = f"\n🃏 HAND DATA - {datetime.now().strftime('%H:%M:%S')}\n"
            status_msg += f"{'─'*60}\n"

            # Table info
            status_msg += f"💰 Pot: ${table_state.pot_size:.2f}\n"
            status_msg += f"📍 Stage: {table_state.stage.upper()}\n"
            status_msg += f"👥 Active Players: {table_state.active_players}\n"

            # Blinds
            sb = getattr(table_state, 'small_blind', 0)
            bb = getattr(table_state, 'big_blind', 0)
            if sb > 0 or bb > 0:
                status_msg += f"💵 Blinds: ${sb:.2f}/${bb:.2f}\n"

            # Hero cards (if visible)
            if table_state.hero_cards:
                cards_str = ', '.join(str(c) for c in table_state.hero_cards)
                status_msg += f"🎴 Hero Cards: {cards_str}\n"
            else:
                status_msg += f"🎴 Hero Cards: Not visible\n"

            # Board cards (if any)
            if table_state.board_cards:
                board_str = ', '.join(str(c) for c in table_state.board_cards)
                status_msg += f"🃏 Board: {board_str}\n"

            # Player details
            if hasattr(table_state, 'seats') and table_state.seats:
                status_msg += f"\n👥 PLAYERS:\n"
                for seat in table_state.seats:
                    if getattr(seat, 'is_active', False):
                        name = getattr(seat, 'name', 'Unknown')
                        stack = getattr(seat, 'stack_size', 0)
                        seat_num = getattr(seat, 'seat_number', '?')
                        position = getattr(seat, 'position', '')
                        is_hero = getattr(seat, 'is_hero', False)
                        is_dealer = getattr(seat, 'is_dealer', False)

                        hero_marker = ' 🎯 (YOU)' if is_hero else ''
                        dealer_marker = ' 🔘' if is_dealer else ''
                        pos_marker = f' [{position}]' if position else ''

                        status_msg += f"  Seat {seat_num}: {name} - ${stack:.2f}{pos_marker}{hero_marker}{dealer_marker}\n"

            status_msg += f"{'─'*60}\n"

            self.after(0, lambda msg=status_msg: self._update_table_status(msg))

            # Log comprehensive hand data to master logger (permanent record)
            if MASTER_LOGGER_AVAILABLE:
                logger = get_master_logger()

                # Build player data for logging
                player_data = {}
                if hasattr(table_state, 'seats') and table_state.seats:
                    for seat in table_state.seats:
                        if getattr(seat, 'is_active', False):
                            seat_num = getattr(seat, 'seat_number', 0)
                            player_data[f'seat_{seat_num}'] = {
                                'name': getattr(seat, 'name', 'Unknown'),
                                'stack': getattr(seat, 'stack_size', 0),
                                'position': getattr(seat, 'position', ''),
                                'is_hero': getattr(seat, 'is_hero', False),
                                'is_dealer': getattr(seat, 'is_dealer', False),
                            }

                logger.info(
                    f"Hand data: pot ${table_state.pot_size:.2f}, stage {table_state.stage}, {table_state.active_players} players",
                    category=LogCategory.ANALYSIS,
                    pot_size=table_state.pot_size,
                    stage=table_state.stage,
                    active_players=table_state.active_players,
                    small_blind=getattr(table_state, 'small_blind', 0),
                    big_blind=getattr(table_state, 'big_blind', 0),
                    hero_cards=str(table_state.hero_cards) if table_state.hero_cards else None,
                    board_cards=str(table_state.board_cards) if table_state.board_cards else None,
                    players=player_data
                )

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
