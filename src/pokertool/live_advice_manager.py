#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Live Advice Manager
===================

Manages real-time updates for compact live advice window.

Features:
- Real-time game state monitoring
- Throttled updates (max 2/sec)
- Background thread for calculations
- Debouncing for rapid state changes
- Performance optimizations with caching

Version: 61.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import logging
import time
import threading
from typing import Optional, Callable, Dict, Any
from queue import Queue, Empty
from dataclasses import dataclass
import hashlib

from .compact_live_advice_window import CompactLiveAdviceWindow, LiveAdviceData, ActionType
from .live_decision_engine import LiveDecisionEngine, GameState, get_live_decision_engine

logger = logging.getLogger(__name__)


# ============================================================================
# Update Manager
# ============================================================================

class LiveAdviceManager:
    """
    Manages real-time updates for live advice window.

    Handles:
    - Background computation thread
    - Update throttling (2/sec max)
    - State change debouncing (500ms)
    - Smart caching
    - Thread-safe queue
    """

    def __init__(
        self,
        window: CompactLiveAdviceWindow,
        decision_engine: Optional[LiveDecisionEngine] = None,
        update_frequency: float = 2.0,
        debounce_delay: float = 0.5
    ):
        """
        Initialize live advice manager.

        Args:
            window: Compact window to update
            decision_engine: Decision engine (creates default if None)
            update_frequency: Max updates per second (default 2.0)
            debounce_delay: Debounce delay in seconds (default 0.5)
        """
        self.window = window
        self.decision_engine = decision_engine or get_live_decision_engine()

        # Update control
        self.update_frequency = update_frequency
        self.update_interval = 1.0 / update_frequency
        self.debounce_delay = debounce_delay

        # State
        self.current_game_state: Optional[GameState] = None
        self.last_game_state_hash: Optional[str] = None
        self.last_update_time: float = 0.0
        self.last_state_change_time: float = 0.0

        # Threading
        self.state_queue = Queue(maxsize=10)
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
        self.paused = False

        # Performance tracking
        self.update_count = 0
        self.throttled_count = 0
        self.cache_hits = 0

        logger.info(f"LiveAdviceManager initialized (updates: {update_frequency}/sec, debounce: {debounce_delay}s)")

    def start(self):
        """Start the manager and background worker thread."""
        if self.running:
            logger.warning("Manager already running")
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        logger.info("LiveAdviceManager started")

    def stop(self):
        """Stop the manager and worker thread."""
        if not self.running:
            return

        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)

        logger.info("LiveAdviceManager stopped")

    def update_game_state(self, game_state: GameState):
        """
        Update game state (called from main thread).

        Args:
            game_state: New game state
        """
        if self.paused:
            return

        # Check if state actually changed
        state_hash = self._hash_game_state(game_state)
        if state_hash == self.last_game_state_hash:
            self.cache_hits += 1
            return

        # Record state change time
        self.last_state_change_time = time.time()
        self.last_game_state_hash = state_hash

        # Add to queue (non-blocking, drop if full)
        try:
            self.state_queue.put_nowait(game_state)
        except:
            logger.warning("State queue full, dropping update")

    def force_update(self):
        """Force immediate update (bypass throttle and cache)."""
        if self.current_game_state:
            self.last_game_state_hash = None
            self.last_update_time = 0.0
            self.update_game_state(self.current_game_state)

    def pause(self):
        """Pause updates."""
        self.paused = True
        logger.info("Manager paused")

    def resume(self):
        """Resume updates."""
        self.paused = False
        logger.info("Manager resumed")
        if self.current_game_state:
            self.force_update()

    def _worker_loop(self):
        """Background worker loop for processing game states."""
        logger.info("Worker thread started")

        while self.running:
            try:
                # Get next state from queue (with timeout)
                try:
                    game_state = self.state_queue.get(timeout=0.1)
                except Empty:
                    continue

                # Debounce: Wait for rapid changes to settle
                time_since_change = time.time() - self.last_state_change_time
                if time_since_change < self.debounce_delay:
                    # Put it back and wait
                    try:
                        self.state_queue.put_nowait(game_state)
                    except:
                        pass
                    time.sleep(0.1)
                    continue

                # Throttle: Check update interval
                time_since_update = time.time() - self.last_update_time
                if time_since_update < self.update_interval:
                    self.throttled_count += 1
                    # Put it back for later
                    try:
                        self.state_queue.put_nowait(game_state)
                    except:
                        pass
                    time.sleep(self.update_interval - time_since_update)
                    continue

                # Process update
                self._process_game_state(game_state)

                # Mark task done
                self.state_queue.task_done()

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                time.sleep(0.1)

        logger.info("Worker thread stopped")

    def _process_game_state(self, game_state: GameState):
        """
        Process game state and update window.

        Args:
            game_state: Game state to process
        """
        try:
            # Show calculating state
            self.window.root.after(0, lambda: self._update_window_calculating())

            # Get advice from decision engine (runs in background thread)
            advice = self.decision_engine.get_live_advice(game_state)

            # Update window (must use after() to run in main thread)
            self.window.root.after(0, lambda: self._update_window_advice(advice))

            # Update state
            self.current_game_state = game_state
            self.last_update_time = time.time()
            self.update_count += 1

            logger.debug(f"Processed update #{self.update_count}: {advice.action.value}")

        except Exception as e:
            logger.error(f"Error processing game state: {e}", exc_info=True)

    def _update_window_calculating(self):
        """Update window to show calculating state."""
        calculating_advice = LiveAdviceData(
            action=ActionType.UNKNOWN,
            has_data=True,
            is_calculating=True
        )
        self.window.update_advice(calculating_advice)

    def _update_window_advice(self, advice: LiveAdviceData):
        """Update window with new advice."""
        self.window.update_advice(advice)

    def _hash_game_state(self, game_state: GameState) -> str:
        """
        Generate hash of game state for change detection.

        Args:
            game_state: Game state to hash

        Returns:
            Hash string
        """
        # Include key fields that affect decision
        key_fields = [
            ''.join(sorted(game_state.hole_cards)),
            ''.join(sorted(game_state.community_cards)),
            f"{game_state.pot_size:.2f}",
            f"{game_state.call_amount:.2f}",
            f"{game_state.stack_size:.2f}",
            str(game_state.num_opponents),
            game_state.street
        ]

        hash_input = '|'.join(key_fields)
        return hashlib.md5(hash_input.encode()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get manager statistics.

        Returns:
            Dict with performance stats
        """
        return {
            'total_updates': self.update_count,
            'throttled_updates': self.throttled_count,
            'cache_hits': self.cache_hits,
            'queue_size': self.state_queue.qsize(),
            'is_running': self.running,
            'is_paused': self.paused,
            'avg_latency_ms': self.decision_engine.avg_latency_ms,
            'update_frequency': self.update_frequency,
            'debounce_delay': self.debounce_delay
        }


# ============================================================================
# Integrated Live Advice System
# ============================================================================

class IntegratedLiveAdviceSystem:
    """
    Complete integrated system combining window, decision engine, and manager.

    Provides simple API for launching and controlling live advice.
    """

    def __init__(
        self,
        parent=None,
        bankroll: float = 10000.0,
        update_frequency: float = 2.0,
        auto_start: bool = True
    ):
        """
        Initialize integrated system.

        Args:
            parent: Parent Tk window
            bankroll: Current bankroll
            update_frequency: Updates per second
            auto_start: Auto-start manager
        """
        # Create components
        self.window = CompactLiveAdviceWindow(parent=parent)
        self.decision_engine = get_live_decision_engine(bankroll=bankroll)
        self.manager = LiveAdviceManager(
            window=self.window,
            decision_engine=self.decision_engine,
            update_frequency=update_frequency
        )

        # Start if requested
        if auto_start:
            self.manager.start()

        logger.info("IntegratedLiveAdviceSystem initialized")

    def update_game_state(self, game_state: GameState):
        """Update game state."""
        self.manager.update_game_state(game_state)

    def show(self):
        """Show window."""
        self.window.show()

    def hide(self):
        """Hide window."""
        self.window.hide()

    def pause(self):
        """Pause updates."""
        self.manager.pause()
        self.window.toggle_pause()

    def resume(self):
        """Resume updates."""
        self.manager.resume()
        self.window.toggle_pause()

    def destroy(self):
        """Destroy system."""
        self.manager.stop()
        self.window.destroy()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive stats."""
        manager_stats = self.manager.get_stats()
        engine_stats = self.decision_engine.get_performance_stats()

        return {
            **manager_stats,
            **engine_stats
        }


# ============================================================================
# Demo / Testing
# ============================================================================

def demo():
    """Demo the integrated live advice system."""
    import tkinter as tk
    import random

    # Create main window
    root = tk.Tk()
    root.title("Live Advice System Demo")
    root.geometry("400x300")

    # Create system
    system = IntegratedLiveAdviceSystem(parent=root, auto_start=True)

    # Test data
    test_hands = [
        (['As', 'Kh'], ['Qh', 'Jd', '9s']),
        (['2c', '7d'], ['Ah', 'Kd', 'Qs']),
        (['Qd', 'Qc'], []),
        (['Jh', 'Ts'], ['Kh', 'Qd', '9s', '2c']),
        (['Ac', 'Ad'], ['Ks', 'Kh', '7d']),
    ]

    current_test = [0]

    def update_with_random_state():
        """Update with test game state."""
        # Rotate through test hands
        hole, board = test_hands[current_test[0] % len(test_hands)]
        current_test[0] += 1

        state = GameState(
            hole_cards=hole,
            community_cards=board,
            pot_size=random.uniform(50, 200),
            call_amount=random.uniform(10, 50),
            stack_size=random.uniform(200, 500),
            num_opponents=random.randint(1, 3),
            street='flop' if board else 'preflop'
        )

        system.update_game_state(state)

        # Show stats
        stats = system.get_stats()
        print(f"\n{'='*60}")
        print(f"Update #{stats['total_updates']}:")
        print(f"  Throttled: {stats['throttled_updates']}")
        print(f"  Cache hits: {stats['cache_hits']}")
        print(f"  Queue: {stats['queue_size']}")
        print(f"  Latency: {stats['avg_latency_ms']:.1f}ms")

        # Schedule next update
        root.after(3000, update_with_random_state)

    # Control panel
    control_frame = tk.Frame(root, padx=20, pady=20)
    control_frame.pack(expand=True)

    tk.Label(
        control_frame,
        text="Live Advice System Demo",
        font=("Arial", 16, "bold")
    ).pack(pady=10)

    tk.Button(
        control_frame,
        text="Update Now",
        command=update_with_random_state,
        width=20
    ).pack(pady=5)

    tk.Button(
        control_frame,
        text="Pause/Resume",
        command=lambda: system.resume() if system.manager.paused else system.pause(),
        width=20
    ).pack(pady=5)

    tk.Button(
        control_frame,
        text="Show Stats",
        command=lambda: print(f"\nStats: {system.get_stats()}"),
        width=20
    ).pack(pady=5)

    # Start first update after 1 second
    root.after(1000, update_with_random_state)

    # Run
    system.show()
    root.mainloop()

    # Cleanup
    system.destroy()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Starting Live Advice Manager Demo...")
    demo()
