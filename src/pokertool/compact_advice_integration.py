#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compact Live Advice - GUI Integration
======================================

Integration module for compact live advice window with PokerTool GUI.

Provides simple API to:
- Launch compact advice window from any GUI
- Connect to table scraper for real-time updates
- Manage window lifecycle

Version: 61.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
import threading
import time

from .compact_live_advice_window import CompactLiveAdviceWindow
from .live_decision_engine import LiveDecisionEngine, GameState, get_live_decision_engine
from .live_advice_manager import LiveAdviceManager, IntegratedLiveAdviceSystem

logger = logging.getLogger(__name__)


# ============================================================================
# Scraper Bridge
# ============================================================================

class ScraperBridge:
    """
    Bridge between poker screen scraper and live advice system.

    Converts scraper table state to GameState for decision engine.
    """

    @staticmethod
    def table_state_to_game_state(table_state: Dict[str, Any]) -> Optional[GameState]:
        """
        Convert scraper table state to GameState.

        Args:
            table_state: Table state dict from scraper

        Returns:
            GameState or None if invalid
        """
        try:
            # Extract player info (assuming player at seat 0 for now)
            player_seat = table_state.get('hero_seat', 0)
            seats = table_state.get('seats', [])

            if not seats or player_seat >= len(seats):
                return None

            player_data = seats[player_seat]

            # Hole cards
            hole_cards = player_data.get('cards', [])
            if not hole_cards or len(hole_cards) < 2:
                return None

            # Community cards
            community_cards = table_state.get('community_cards', [])

            # Pot and betting
            pot_size = table_state.get('pot', 0.0)
            current_bet = table_state.get('current_bet', 0.0)
            player_bet = player_data.get('bet', 0.0)
            call_amount = max(0.0, current_bet - player_bet)

            # Stack
            stack_size = player_data.get('stack', 0.0)

            # Opponents
            active_seats = [s for s in seats if s.get('active', False) and s != player_data]
            num_opponents = len(active_seats)

            # Street
            street_map = {
                0: 'preflop',
                3: 'flop',
                4: 'turn',
                5: 'river'
            }
            num_community = len(community_cards) if community_cards else 0
            street = street_map.get(num_community, 'preflop')

            # Position (simplified)
            position = player_data.get('position', 'unknown')

            # Blinds
            small_blind = table_state.get('small_blind', 1.0)
            big_blind = table_state.get('big_blind', 2.0)

            return GameState(
                hole_cards=hole_cards,
                community_cards=community_cards,
                pot_size=pot_size,
                call_amount=call_amount,
                min_raise=big_blind,
                max_raise=stack_size,
                stack_size=stack_size,
                position=position,
                num_opponents=num_opponents,
                street=street,
                blinds=(small_blind, big_blind)
            )

        except Exception as e:
            logger.error(f"Error converting table state: {e}")
            return None

    @staticmethod
    def validate_table_state(table_state: Dict[str, Any]) -> bool:
        """
        Validate that table state has minimum required data.

        Args:
            table_state: Table state dict

        Returns:
            True if valid
        """
        if not table_state:
            return False

        # Must have seats
        if 'seats' not in table_state or not table_state['seats']:
            return False

        # Must have pot
        if 'pot' not in table_state:
            return False

        return True


# ============================================================================
# GUI Integration
# ============================================================================

class CompactAdviceGUIIntegration:
    """
    Integration class for adding compact live advice to any PokerTool GUI.

    Usage:
        # In your GUI __init__:
        self.live_advice = CompactAdviceGUIIntegration(
            parent=self.root,
            scraper=self.scraper
        )
        self.live_advice.start()
    """

    def __init__(
        self,
        parent=None,
        scraper=None,
        bankroll: float = 10000.0,
        auto_launch: bool = False,
        update_frequency: float = 2.0
    ):
        """
        Initialize GUI integration.

        Args:
            parent: Parent Tk window
            scraper: Poker screen scraper instance
            bankroll: Current bankroll
            auto_launch: Auto-launch window on start
            update_frequency: Updates per second
        """
        self.parent = parent
        self.scraper = scraper
        self.bankroll = bankroll
        self.auto_launch = auto_launch

        # Create integrated system
        self.system = IntegratedLiveAdviceSystem(
            parent=parent,
            bankroll=bankroll,
            update_frequency=update_frequency,
            auto_start=False  # We'll start it manually
        )

        # Scraper polling
        self.scraper_poll_interval = 1000  # 1 second
        self.scraper_poll_job = None
        self.is_running = False

        # Show window if auto-launch
        if self.auto_launch:
            self.system.show()

        logger.info("CompactAdviceGUIIntegration initialized")

    def start(self):
        """Start the integration (begin scraper polling and updates)."""
        if self.is_running:
            return

        self.is_running = True
        self.system.manager.start()

        if self.scraper and self.parent:
            self._schedule_scraper_poll()

        logger.info("Compact advice integration started")

    def stop(self):
        """Stop the integration."""
        if not self.is_running:
            return

        self.is_running = False

        if self.scraper_poll_job and self.parent:
            self.parent.after_cancel(self.scraper_poll_job)
            self.scraper_poll_job = None

        self.system.manager.stop()

        logger.info("Compact advice integration stopped")

    def _schedule_scraper_poll(self):
        """Schedule next scraper poll."""
        if not self.is_running or not self.parent:
            return

        self.scraper_poll_job = self.parent.after(
            self.scraper_poll_interval,
            self._poll_scraper
        )

    def _poll_scraper(self):
        """Poll scraper for table state and update advice."""
        try:
            if not self.scraper:
                self._schedule_scraper_poll()
                return

            # Get current table state from scraper
            table_state = self._get_table_state_from_scraper()

            if table_state and ScraperBridge.validate_table_state(table_state):
                # Convert to GameState
                game_state = ScraperBridge.table_state_to_game_state(table_state)

                if game_state:
                    # Update advice
                    self.system.update_game_state(game_state)
                    logger.debug("Updated advice from scraper data")

        except Exception as e:
            logger.error(f"Error polling scraper: {e}")

        # Schedule next poll
        self._schedule_scraper_poll()

    def _get_table_state_from_scraper(self) -> Optional[Dict[str, Any]]:
        """
        Get table state from scraper.

        Returns:
            Table state dict or None
        """
        try:
            # Try to get table state from scraper
            if hasattr(self.scraper, 'get_table_state'):
                return self.scraper.get_table_state()
            elif hasattr(self.scraper, 'last_table_state'):
                return self.scraper.last_table_state
            elif hasattr(self.scraper, 'analyze_table'):
                # Call analyze_table and return result
                return self.scraper.analyze_table()
            else:
                logger.warning("Scraper has no recognized state accessor")
                return None

        except Exception as e:
            logger.error(f"Error getting table state: {e}")
            return None

    def show(self):
        """Show the compact advice window."""
        self.system.show()

    def hide(self):
        """Hide the compact advice window."""
        self.system.hide()

    def toggle(self):
        """Toggle window visibility."""
        self.system.window.toggle_visibility()

    def pause(self):
        """Pause updates."""
        self.system.pause()

    def resume(self):
        """Resume updates."""
        self.system.resume()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive stats."""
        return self.system.get_stats()

    def destroy(self):
        """Destroy the integration."""
        self.stop()
        self.system.destroy()


# ============================================================================
# Convenience Functions
# ============================================================================

def launch_compact_advice_standalone(
    scraper=None,
    bankroll: float = 10000.0
):
    """
    Launch compact live advice window in standalone mode.

    Args:
        scraper: Optional poker screen scraper
        bankroll: Current bankroll

    Returns:
        CompactAdviceGUIIntegration instance
    """
    integration = CompactAdviceGUIIntegration(
        parent=None,
        scraper=scraper,
        bankroll=bankroll,
        auto_launch=True
    )
    integration.start()

    logger.info("Launched compact advice in standalone mode")

    return integration


def add_to_existing_gui(
    gui_instance,
    scraper=None,
    menu_name: str = "View",
    auto_launch: bool = False
) -> CompactAdviceGUIIntegration:
    """
    Add compact advice to existing GUI with menu integration.

    Args:
        gui_instance: Existing GUI instance (must have self.root)
        scraper: Optional poker screen scraper
        menu_name: Menu name to add item to
        auto_launch: Auto-launch on start

    Returns:
        CompactAdviceGUIIntegration instance
    """
    # Get parent window
    if hasattr(gui_instance, 'root'):
        parent = gui_instance.root
    elif hasattr(gui_instance, 'window'):
        parent = gui_instance.window
    else:
        raise ValueError("GUI instance must have 'root' or 'window' attribute")

    # Create integration
    integration = CompactAdviceGUIIntegration(
        parent=parent,
        scraper=scraper,
        auto_launch=auto_launch
    )

    # Try to add menu item
    try:
        if hasattr(gui_instance, 'menubar') or hasattr(gui_instance, 'menu'):
            menubar = getattr(gui_instance, 'menubar', getattr(gui_instance, 'menu', None))

            if menubar:
                # Find or create View menu
                view_menu = None
                for i in range(menubar.index('end') + 1):
                    try:
                        label = menubar.entrycget(i, 'label')
                        if label == menu_name:
                            view_menu = menubar.nametowidget(menubar.entrycget(i, 'menu'))
                            break
                    except:
                        pass

                if view_menu:
                    # Add toggle menu item
                    view_menu.add_separator()
                    view_menu.add_command(
                        label="Compact Live Advice",
                        command=integration.toggle,
                        accelerator="Ctrl+L"
                    )
                    logger.info("Added menu item for compact advice")
    except Exception as e:
        logger.warning(f"Could not add menu item: {e}")

    # Start integration
    integration.start()

    logger.info("Added compact advice to existing GUI")

    return integration


# ============================================================================
# Demo / Testing
# ============================================================================

def demo():
    """Demo the GUI integration."""
    import tkinter as tk

    # Create simple GUI
    root = tk.Tk()
    root.title("Poker GUI with Compact Advice")
    root.geometry("600x400")

    # Create mock scraper
    class MockScraper:
        def __init__(self):
            self.call_count = 0

        def get_table_state(self):
            """Return mock table state."""
            import random
            self.call_count += 1

            return {
                'hero_seat': 0,
                'seats': [
                    {
                        'active': True,
                        'cards': ['As', 'Kh'],
                        'stack': random.uniform(300, 600),
                        'bet': 0.0,
                        'position': 'button'
                    },
                    {
                        'active': True,
                        'cards': [],
                        'stack': 500.0,
                        'bet': 25.0
                    }
                ],
                'community_cards': ['Qh', 'Jd', '9s'] if self.call_count % 3 == 0 else [],
                'pot': random.uniform(50, 200),
                'current_bet': 25.0,
                'small_blind': 1.0,
                'big_blind': 2.0
            }

    scraper = MockScraper()

    # Add integration
    integration = CompactAdviceGUIIntegration(
        parent=root,
        scraper=scraper,
        auto_launch=True
    )
    integration.start()

    # Control panel
    control_frame = tk.Frame(root, padx=20, pady=20)
    control_frame.pack(expand=True)

    tk.Label(
        control_frame,
        text="Compact Live Advice Integration Demo",
        font=("Arial", 16, "bold")
    ).pack(pady=20)

    tk.Button(
        control_frame,
        text="Toggle Window",
        command=integration.toggle,
        width=20
    ).pack(pady=5)

    tk.Button(
        control_frame,
        text="Pause/Resume",
        command=lambda: integration.resume() if integration.system.manager.paused else integration.pause(),
        width=20
    ).pack(pady=5)

    tk.Button(
        control_frame,
        text="Show Stats",
        command=lambda: print(f"\nStats:\n{integration.get_stats()}"),
        width=20
    ).pack(pady=5)

    # Run
    root.mainloop()

    # Cleanup
    integration.destroy()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Starting Compact Advice Integration Demo...")
    demo()
