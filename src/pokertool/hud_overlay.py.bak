# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/pokertool/hud_overlay.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Real-time HUD Overlay System
Provides a transparent overlay window that displays poker statistics and advice in real-time.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from threading import Thread, Event
import time
import json
from pathlib import Path

# Try to import GUI dependencies
try:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.font as tkFont
    GUI_AVAILABLE = True
except ImportError:
    tk = None
    ttk = None
    tkFont = None
    GUI_AVAILABLE = False

from .core import analyse_hand, parse_card, Position
from .gto_solver import get_gto_solver, GameState, Range, create_standard_ranges
from .ml_opponent_modeling import get_opponent_modeling_system
from .storage import get_secure_db

logger = logging.getLogger(__name__)

@dataclass
class HUDConfig:
    """Configuration for HUD display."""
    position: Tuple[int, int] = (100, 100)
    size: Tuple[int, int] = (300, 200)
    opacity: float = 0.8
    always_on_top: bool = True
    show_hole_cards: bool = True
    show_board_cards: bool = True
    show_position: bool = True
    show_pot_odds: bool = True
    show_hand_strength: bool = True
    show_gto_advice: bool = True
    show_opponent_stats: bool = True
    update_interval: float = 0.5
    theme: str = 'dark'  # 'dark' or 'light'
    font_size: int = 10

@dataclass
class PlayerHUDStats:
    """HUD statistics for a player."""
    name: str
    vpip: float = 0.0  # Voluntarily Put $ In Pot
    pfr: float = 0.0   # Pre-flop Raise
    aggression: float = 0.0
    hands_played: int = 0
    position: str = "Unknown"
    notes: List[str] = field(default_factory=list)

class HUDOverlay:
    """
    Real-time HUD overlay window that displays poker statistics and advice.
    """
    
    def __init__(self, config: HUDConfig = None):
        if not GUI_AVAILABLE:
            raise RuntimeError("GUI dependencies not available. Install tkinter.")
        
        self.config = config or HUDConfig()
        self.root = None
        self.running = False
        self.update_thread = None
        self.stop_event = Event()
        
        # Data sources
        self.gto_solver = get_gto_solver()
        self.ml_system = get_opponent_modeling_system()
        self.db = get_secure_db()
        
        # Current game state
        self.current_state: Optional[Dict[str, Any]] = None
        self.player_stats: Dict[str, PlayerHUDStats] = {}
        
        # GUI elements
        self.widgets = {}
        self.style = None
        
        # Callbacks for table updates
        self.state_callbacks: List[Callable] = []
        
    def initialize(self) -> bool:
        """Initialize the HUD overlay window."""
        try:
            self.root = tk.Tk()
            self.root.title("Poker HUD")
            self.root.geometry(f"{self.config.size[0]}x{self.config.size[1]}+{self.config.position[0]}+{self.config.position[1]}")
            
            # Configure window properties
            self.root.attributes('-alpha', self.config.opacity)
            if self.config.always_on_top:
                self.root.attributes('-topmost', True)
            
            # Try to make window stay on top but not steal focus
            self.root.overrideredirect(False)  # Keep window decorations for now
            
            # Configure style
            self.style = ttk.Style()
            self._configure_theme()
            
            # Create widgets
            self._create_widgets()
            
            logger.info("HUD overlay initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize HUD overlay: {e}")
            return False
    
    def _configure_theme(self):
        """Configure the visual theme."""
        if self.config.theme == 'dark':
            # Dark theme colors
            bg_color = '#2b2b2b'
            fg_color = '#ffffff'
            accent_color = '#4a9eff'
            warning_color = '#ff6b6b'
            success_color = '#51cf66'
        else:
            # Light theme colors
            bg_color = '#ffffff'
            fg_color = '#000000'
            accent_color = '#007acc'
            warning_color = '#d63031'
            success_color = '#00b894'
        
        # Configure root window
        self.root.configure(bg=bg_color)
        
        # Store colors for later use
        self.colors = {
            'bg': bg_color,
            'fg': fg_color,
            'accent': accent_color,
            'warning': warning_color,
            'success': success_color
        }
    
    def _create_widgets(self):
        """Create the HUD interface widgets."""
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create font
        default_font = tkFont.Font(family="Consolas", size=self.config.font_size)
        small_font = tkFont.Font(family="Consolas", size=self.config.font_size-1)
        
        # Hero cards section
        if self.config.show_hole_cards:
            hero_frame = tk.LabelFrame(main_frame, text="Hero", bg=self.colors['bg'], 
                                     fg=self.colors['fg'], font=default_font)
            hero_frame.pack(fill='x', pady=2)
            
            self.widgets['hero_cards'] = tk.Label(hero_frame, text="-- --", 
                                                font=default_font, bg=self.colors['bg'], 
                                                fg=self.colors['accent'])
            self.widgets['hero_cards'].pack(side='left')
            
            self.widgets['position'] = tk.Label(hero_frame, text="Position: ?", 
                                               font=small_font, bg=self.colors['bg'], 
                                               fg=self.colors['fg'])
            self.widgets['position'].pack(side='right')
        
        # Board cards section
        if self.config.show_board_cards:
            board_frame = tk.LabelFrame(main_frame, text="Board", bg=self.colors['bg'], 
                                      fg=self.colors['fg'], font=default_font)
            board_frame.pack(fill='x', pady=2)
            
            self.widgets['board_cards'] = tk.Label(board_frame, text="-- -- -- -- --", 
                                                  font=default_font, bg=self.colors['bg'], 
                                                  fg=self.colors['accent'])
            self.widgets['board_cards'].pack()
        
        # Hand analysis section
        if self.config.show_hand_strength:
            analysis_frame = tk.LabelFrame(main_frame, text="Analysis", bg=self.colors['bg'], 
                                         fg=self.colors['fg'], font=default_font)
            analysis_frame.pack(fill='x', pady=2)
            
            self.widgets['hand_strength'] = tk.Label(analysis_frame, text="Strength: --", 
                                                   font=small_font, bg=self.colors['bg'], 
                                                   fg=self.colors['fg'])
            self.widgets['hand_strength'].pack()
            
            self.widgets['pot_odds'] = tk.Label(analysis_frame, text="Pot Odds: --", 
                                              font=small_font, bg=self.colors['bg'], 
                                              fg=self.colors['fg'])
            self.widgets['pot_odds'].pack()
        
        # GTO advice section
        if self.config.show_gto_advice:
            gto_frame = tk.LabelFrame(main_frame, text="GTO Advice", bg=self.colors['bg'], 
                                    fg=self.colors['fg'], font=default_font)
            gto_frame.pack(fill='x', pady=2)
            
            self.widgets['gto_advice'] = tk.Label(gto_frame, text="Calculating...", 
                                                font=small_font, bg=self.colors['bg'], 
                                                fg=self.colors['success'], wraplength=250)
            self.widgets['gto_advice'].pack()
        
        # Opponent stats section
        if self.config.show_opponent_stats:
            opponent_frame = tk.LabelFrame(main_frame, text="Opponents", bg=self.colors['bg'], 
                                         fg=self.colors['fg'], font=default_font)
            opponent_frame.pack(fill='both', expand=True, pady=2)
            
            # Scrollable text widget for opponent stats
            self.widgets['opponent_stats'] = tk.Text(opponent_frame, height=4, 
                                                   font=small_font, bg=self.colors['bg'], 
                                                   fg=self.colors['fg'], wrap='word')
            self.widgets['opponent_stats'].pack(fill='both', expand=True)
        
        # Status bar
        self.widgets['status'] = tk.Label(main_frame, text="Ready", 
                                        font=small_font, bg=self.colors['bg'], 
                                        fg=self.colors['fg'])
        self.widgets['status'].pack(side='bottom', fill='x')
    
    def start(self) -> bool:
        """Start the HUD overlay."""
        if not self.root:
            if not self.initialize():
                return False
        
        if self.running:
            logger.warning("HUD already running")
            return True
        
        try:
            self.running = True
            self.stop_event.clear()
            
            # Start update thread
            self.update_thread = Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            # Start GUI main loop in separate thread to avoid blocking
            gui_thread = Thread(target=self._run_gui, daemon=True)
            gui_thread.start()
            
            logger.info("HUD overlay started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start HUD overlay: {e}")
            self.running = False
            return False
    
    def _run_gui(self):
        """Run the GUI main loop."""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"GUI main loop error: {e}")
        finally:
            self.running = False
    
    def _update_loop(self):
        """Main update loop for HUD data."""
        while self.running and not self.stop_event.is_set():
            try:
                self._update_display()
                time.sleep(self.config.update_interval)
            except Exception as e:
                logger.error(f"HUD update error: {e}")
                time.sleep(1.0)  # Wait before retrying
    
    def _update_display(self):
        """Update the HUD display with current game state."""
        if not self.current_state:
            return
        
        try:
            # Update hero cards
            if 'hero_cards' in self.widgets:
                hole_cards = self.current_state.get('hole_cards_ocr', 
                                                   self.current_state.get('hole_cards', []))
                cards_text = ' '.join(hole_cards[:2]) if hole_cards else "-- --"
                self.widgets['hero_cards'].config(text=cards_text)
            
            # Update position
            if 'position' in self.widgets:
                position = self.current_state.get('position', 'Unknown')
                self.widgets['position'].config(text=f"Position: {position}")
            
            # Update board cards
            if 'board_cards' in self.widgets:
                board_cards = self.current_state.get('board_cards_ocr', 
                                                    self.current_state.get('board_cards', []))
                board_text = ' '.join(board_cards[:5]) if board_cards else "-- -- -- -- --"
                # Pad with empty slots
                board_parts = board_text.split()
                while len(board_parts) < 5:
                    board_parts.append("--")
                self.widgets['board_cards'].config(text=' '.join(board_parts))
            
            # Update hand analysis
            self._update_hand_analysis()
            
            # Update GTO advice
            self._update_gto_advice()
            
            # Update opponent stats
            self._update_opponent_stats()
            
            # Update status
            if 'status' in self.widgets:
                confidence = self.current_state.get('hole_confidence', 0.0)
                status = f"OCR Confidence: {confidence:.1%}" if confidence > 0 else "No OCR data"
                self.widgets['status'].config(text=status)
                
        except Exception as e:
            logger.error(f"Display update error: {e}")
    
    def _update_hand_analysis(self):
        """Update hand strength and pot odds analysis."""
        try:
            hole_cards = self.current_state.get('hole_cards_ocr', 
                                               self.current_state.get('hole_cards', []))
            board_cards = self.current_state.get('board_cards_ocr', 
                                                 self.current_state.get('board_cards', []))
            
            if len(hole_cards) >= 2:
                # Parse cards
                parsed_hole = [parse_card(card) for card in hole_cards[:2]]
                parsed_board = [parse_card(card) for card in board_cards[:5]] if board_cards else None
                
                # Analyze hand
                analysis = analyse_hand(
                    parsed_hole,
                    parsed_board,
                    position=self.current_state.get('position'),
                    pot=self.current_state.get('pot', 0),
                    to_call=self.current_state.get('to_call', 0)
                )
                
                # Update strength display
                if 'hand_strength' in self.widgets:
                    self.widgets['hand_strength'].config(
                        text=f"Strength: {analysis.strength:.2f}/10"
                    )
                
                # Calculate and display pot odds
                if 'pot_odds' in self.widgets:
                    pot = self.current_state.get('pot', 0)
                    to_call = self.current_state.get('to_call', 0)
                    
                    if pot > 0 and to_call > 0:
                        pot_odds = to_call / (pot + to_call)
                        self.widgets['pot_odds'].config(
                            text=f"Pot Odds: {pot_odds:.1%} (${to_call} to win ${pot})"
                        )
                    else:
                        self.widgets['pot_odds'].config(text="Pot Odds: Not available")
            
        except Exception as e:
            logger.debug(f"Hand analysis update failed: {e}")
            if 'hand_strength' in self.widgets:
                self.widgets['hand_strength'].config(text="Strength: Error")
    
    def _update_gto_advice(self):
        """Update GTO strategy advice."""
        try:
            hole_cards = self.current_state.get('hole_cards_ocr', 
                                               self.current_state.get('hole_cards', []))
            board_cards = self.current_state.get('board_cards_ocr', 
                                                 self.current_state.get('board_cards', []))
            
            if len(hole_cards) >= 2 and 'gto_advice' in self.widgets:
                # Create simplified game state
                pot = self.current_state.get('pot', 100)
                to_call = self.current_state.get('to_call', 20)
                
                game_state = GameState(
                    pot_size=pot,
                    bet_to_call=to_call,
                    effective_stack=1000,  # Assume deep stacks
                    position=self.current_state.get('position', 'MP'),
                    num_players=self.current_state.get('num_players', 6)
                )
                
                # Get standard ranges (simplified for HUD)
                ranges = create_standard_ranges()
                
                # Quick GTO analysis (simplified)
                advice = self._get_quick_gto_advice(hole_cards, board_cards, game_state)
                
                self.widgets['gto_advice'].config(text=advice)
            
        except Exception as e:
            logger.debug(f"GTO advice update failed: {e}")
            if 'gto_advice' in self.widgets:
                self.widgets['gto_advice'].config(text="GTO: Analysis error")
    
    def _get_quick_gto_advice(self, hole_cards: List[str], board_cards: List[str], 
                             game_state: GameState) -> str:
        """Get quick GTO advice without full solver computation."""
        try:
            # Simple heuristic-based advice for HUD display
            hand_str = ''.join(hole_cards[:2])
            
            # Basic preflop advice
            if not board_cards:
                if any(card[0] in 'AK' for card in hole_cards):
                    return "RAISE (Premium hand)"
                elif any(card[0] in 'QJT' for card in hole_cards):
                    return "RAISE/CALL (Good hand)"
                else:
                    return "FOLD/CALL (Marginal)"
            
            # Post-flop advice (simplified)
            pot_odds = game_state.bet_to_call / (game_state.pot_size + game_state.bet_to_call)
            
            if pot_odds > 0.33:
                return f"FOLD (Bad odds: {pot_odds:.1%})"
            elif pot_odds < 0.15:
                return f"CALL (Good odds: {pot_odds:.1%})"
            else:
                return f"MARGINAL (Odds: {pot_odds:.1%})"
                
        except Exception as e:
            logger.debug(f"Quick GTO advice failed: {e}")
            return "GTO: Error calculating"
    
    def _update_opponent_stats(self):
        """Update opponent statistics display."""
        try:
            if 'opponent_stats' in self.widgets:
                stats_text = ""
                
                # Get recent opponent data from ML system
                for seat in range(1, 10):  # Up to 9 seats
                    player_id = f"seat_{seat}"
                    profile = self.ml_system.get_player_profile(player_id)
                    
                    if profile and profile.get('hands_observed', 0) > 10:
                        name = profile.get('name', f'Player {seat}')
                        vpip = profile.get('vpip', 0.0) * 100
                        pfr = profile.get('pfr', 0.0) * 100
                        aggression = profile.get('aggression_factor', 0.0)
                        
                        stats_text += f"{name}: VPIP:{vpip:.0f}% PFR:{pfr:.0f}% AGG:{aggression:.1f}\n"
                
                if not stats_text:
                    stats_text = "No opponent data available yet.\nObserving table..."
                
                # Update text widget
                self.widgets['opponent_stats'].delete('1.0', 'end')
                self.widgets['opponent_stats'].insert('1.0', stats_text)
                
        except Exception as e:
            logger.debug(f"Opponent stats update failed: {e}")
    
    def update_game_state(self, state: Dict[str, Any]):
        """Update the current game state for HUD display."""
        self.current_state = state.copy()
        
        # Notify any registered callbacks
        for callback in self.state_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"State callback error: {e}")
    
    def register_state_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for state updates."""
        self.state_callbacks.append(callback)
    
    def stop(self):
        """Stop the HUD overlay."""
        self.running = False
        self.stop_event.set()
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)
        
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception as e:
                logger.error(f"Error stopping HUD GUI: {e}")
        
        logger.info("HUD overlay stopped")
    
    def save_config(self, filename: str = None):
        """Save HUD configuration to file."""
        if not filename:
            filename = Path.home() / ".pokertool" / "hud_config.json"
        
        try:
            Path(filename).parent.mkdir(exist_ok=True)
            
            config_dict = {
                'position': self.config.position,
                'size': self.config.size,
                'opacity': self.config.opacity,
                'always_on_top': self.config.always_on_top,
                'show_hole_cards': self.config.show_hole_cards,
                'show_board_cards': self.config.show_board_cards,
                'show_position': self.config.show_position,
                'show_pot_odds': self.config.show_pot_odds,
                'show_hand_strength': self.config.show_hand_strength,
                'show_gto_advice': self.config.show_gto_advice,
                'show_opponent_stats': self.config.show_opponent_stats,
                'update_interval': self.config.update_interval,
                'theme': self.config.theme,
                'font_size': self.config.font_size
            }
            
            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"HUD config saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save HUD config: {e}")
            return False
    
    @classmethod
    def load_config(cls, filename: str = None) -> 'HUDConfig':
        """Load HUD configuration from file."""
        if not filename:
            filename = Path.home() / ".pokertool" / "hud_config.json"
        
        try:
            with open(filename, 'r') as f:
                config_dict = json.load(f)
            
            return HUDConfig(**config_dict)
            
        except Exception as e:
            logger.warning(f"Failed to load HUD config: {e}, using defaults")
            return HUDConfig()

# Global HUD instance
_hud_overlay: Optional[HUDOverlay] = None

def get_hud_overlay() -> Optional[HUDOverlay]:
    """Get the global HUD overlay instance."""
    return _hud_overlay

def start_hud_overlay(config: HUDConfig = None) -> bool:
    """Start the HUD overlay system."""
    global _hud_overlay
    
    if not GUI_AVAILABLE:
        logger.error("GUI dependencies not available for HUD overlay")
        return False
    
    if _hud_overlay and _hud_overlay.running:
        logger.warning("HUD overlay already running")
        return True
    
    try:
        _hud_overlay = HUDOverlay(config)
        return _hud_overlay.start()
    except Exception as e:
        logger.error(f"Failed to start HUD overlay: {e}")
        return False

def stop_hud_overlay():
    """Stop the HUD overlay system."""
    global _hud_overlay
    
    if _hud_overlay:
        _hud_overlay.stop()
        _hud_overlay = None

def update_hud_state(state: Dict[str, Any]):
    """Update HUD with new game state."""
    global _hud_overlay
    
    if _hud_overlay and _hud_overlay.running:
        _hud_overlay.update_game_state(state)

def is_hud_running() -> bool:
    """Check if HUD overlay is currently running."""
    global _hud_overlay
    return _hud_overlay is not None and _hud_overlay.running

if __name__ == '__main__':
    # Test HUD functionality
    if GUI_AVAILABLE:
        print("Testing HUD overlay...")
        
        config = HUDConfig(position=(200, 200), size=(350, 250))
        
        if start_hud_overlay(config):
            print("HUD overlay started successfully")
            
            # Simulate some game state updates
            test_states = [
                {
                    'hole_cards': ['As', 'Kh'],
                    'board_cards': ['Js', '9d', '2c'],
                    'position': 'BTN',
                    'pot': 150,
                    'to_call': 30,
                    'hole_confidence': 0.95
                },
                {
                    'hole_cards': ['Qs', 'Jh'],
                    'board_cards': ['Ts', '9d', '8c', 'Ah'],
                    'position': 'MP',
                    'pot': 400,
                    'to_call': 75,
                    'hole_confidence': 0.88
                }
            ]
            
            import time
            for i, state in enumerate(test_states):
                time.sleep(3)
                update_hud_state(state)
                print(f"Updated HUD with test state {i+1}")
            
            # Keep running for demonstration
            time.sleep(10)
            stop_hud_overlay()
            print("HUD overlay stopped")
        else:
            print("Failed to start HUD overlay")
    else:
        print("GUI dependencies not available. Install tkinter.")
