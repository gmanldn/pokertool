"""
Enhanced Poker Assistant GUI
Enterprise-grade poker application with visual card selection, 
clear table visualization, and optimized for live game entry.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading

# Import error handling functions from the existing module
try:
    from .error_handling import sanitize_input, log, run_safely, retry_on_failure, CircuitBreaker
    from .storage import get_secure_db, SecurityError
except ImportError:
    # Fallback if modules not available
    def sanitize_input(x): return x
    def log(x): print(x)
    def run_safely(func): return func()
    def get_secure_db(): return None
    class SecurityError(Exception): pass
    class CircuitBreaker: pass

# Try to import poker modules
try:
    from .core import analyse_hand, Card, Suit, Position, HandAnalysisResult
    MODULES_LOADED = True
except ImportError as e:
    print(f'Warning: Some modules not loaded: {e}')
    MODULES_LOADED = False

    # Fallback definitions
    from enum import Enum

    class Suit(Enum):
        """Suit enumeration."""
        spades = 's'
        hearts = 'h'
        diamonds = 'd'
        clubs = 'c'

    class Position(Enum):
        """Position enumeration."""
        UNDER_THE_GUN = 'UTG'
        UNDER_THE_GUN_PLUS_1 = 'UTG+1'
        MIDDLE_POSITION = 'MP'
        CUTOFF = 'CO'
        BUTTON = 'BTN'
        SMALL_BLIND = 'SB'
        BIG_BLIND = 'BB'

    class Card:
        """Card class."""
        def __init__(self, rank: str, suit: Suit):
            self.rank = rank
            self.suit = suit.value if hasattr(suit, 'value') else suit

        def __str__(self):
            return f'{self.rank}{self.suit}'

# Color scheme
COLORS = {
    'bg_dark': '#1a1f2e',
    'bg_medium': '#2a3142',
    'bg_light': '#3a4152',
    'accent_primary': '#4a9eff',
    'accent_success': '#4ade80',
    'accent_warning': '#fbbf24',
    'accent_danger': '#ef4444',
    'text_primary': '#ffffff',
    'text_secondary': '#94a3b8',
    'table_felt': '#0d3a26',
    'table_border': '#2a7f5f',
    'dealer_button': '#FFD700',
    'small_blind': '#FFA500',
    'big_blind': '#DC143C',
    'card_red': '#DC143C',
    'card_black': '#000000',
    'card_bg': '#ffffff',
    'card_selected': '#4a9eff',
    'card_hover': '#e0e7ff'
}

# Font sizes
FONTS = {
    'title': ('Arial', 24, 'bold'),
    'heading': ('Arial', 18, 'bold'),
    'subheading': ('Arial', 14, 'bold'),
    'body': ('Arial', 12),
    'card': ('Arial', 20, 'bold'),
    'button': ('Arial', 14, 'bold'),
    'analysis': ('Consolas', 14)
}

class VisualCard(tk.Frame):
    """A visual representation of a playing card that can be clicked."""

    def __init__(self, parent, rank: str, suit: Suit, callback=None):
        super().__init__(parent, bg=COLORS['card_bg'], relief=tk.RAISED, bd=2)

        self.rank = rank
        self.suit = suit
        self.callback = callback
        self.selected = False

        # Determine card color
        suit_color = COLORS['card_red'] if suit in [Suit.HEARTS, Suit.DIAMONDS] else COLORS['card_black']

        # Suit symbols
        suit_symbols = {
            Suit.SPADES: '♠',
            Suit.HEARTS: '♥',
            Suit.DIAMONDS: '♦',
            Suit.CLUBS: '♣'
        }

        # Create card display
        self.label = tk.Label(
            self,
            text=f"{rank}\n{suit_symbols[suit]}",
            font=FONTS['card'],
            fg=suit_color,
            bg=COLORS['card_bg'],
            width=4,
            height=3
        )
        self.label.pack(expand=True, fill='both')

        # Bind events
        self.bind('<Button-1>', self._on_click)
        self.label.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.label.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.label.bind('<Leave>', self._on_leave)

    def _on_click(self, event):
        """Handle card click."""
        if self.callback:
            self.callback(self)

    def _on_enter(self, event):
        """Handle mouse enter."""
        if not self.selected:
            self.configure(bg=COLORS['card_hover'])
            self.label.configure(bg=COLORS['card_hover'])

    def _on_leave(self, event):
        """Handle mouse leave."""
        if not self.selected:
            self.configure(bg=COLORS['card_bg'])
            self.label.configure(bg=COLORS['card_bg'])

    def set_selected(self, selected: bool):
        """Set card selection state."""
        self.selected = selected
        if selected:
            self.configure(bg=COLORS['card_selected'], relief=tk.SUNKEN)
            self.label.configure(bg=COLORS['card_selected'], fg=COLORS['text_primary'])
        else:
            suit_color = COLORS['card_red'] if self.suit in [Suit.HEARTS, Suit.DIAMONDS] else COLORS['card_black']
            self.configure(bg=COLORS['card_bg'], relief=tk.RAISED)
            self.label.configure(bg=COLORS['card_bg'], fg=suit_color)

    def set_disabled(self, disabled: bool):
        """Set card disabled state."""
        if disabled:
            self.configure(bg=COLORS['bg_light'])
            self.label.configure(bg=COLORS['bg_light'], fg=COLORS['text_secondary'])
        else:
            self.set_selected(self.selected)

class CardSelectionPanel(tk.Frame):
    """Panel for visual card selection."""

    def __init__(self, parent, on_card_selected=None):
        super().__init__(parent, bg=COLORS['bg_medium'])

        self.on_card_selected = on_card_selected
        self.cards: Dict[str, VisualCard] = {}
        self.selected_cards: List[VisualCard] = []

        self._build_ui()

    def _build_ui(self):
        """Build the card selection grid."""
        # Title
        title = tk.Label(
            self,
            text='Select Cards',
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary']
        )
        title.pack(pady=10)

        # Card grid frame
        grid_frame = tk.Frame(self, bg=COLORS['bg_medium'])
        grid_frame.pack(padx=10, pady=10)

        # Create cards in rank order
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        suits = [Suit.SPADES, Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]

        for row, rank in enumerate(ranks):
            for col, suit in enumerate(suits):
                card = VisualCard(grid_frame, rank, suit, self._on_card_click)
                card.grid(row=row, column=col, padx=2, pady=2)
                card_key = f'{rank}{suit.value}'
                self.cards[card_key] = card

    def _on_card_click(self, card: VisualCard):
        """Handle card selection."""
        if card.selected:
            # Deselect
            card.set_selected(False)
            self.selected_cards.remove(card)
        else:
            # Select (max 7 cards)
            if len(self.selected_cards) < 7:
                card.set_selected(True)
                self.selected_cards.append(card)

                if self.on_card_selected:
                    self.on_card_selected(card)
            else:
                messagebox.showwarning('Card Limit', 'Maximum 7 cards can be selected (2 hole + 5 board)')

    def get_selected_cards(self) -> List[Tuple[str, Suit]]:
        """Get list of selected cards."""
        return [(card.rank, card.suit) for card in self.selected_cards]

    def clear_selection(self):
        """Clear all selected cards."""
        for card in self.selected_cards:
            card.set_selected(False)
        self.selected_cards.clear()

    def set_cards_disabled(self, card_strs: List[str], disabled: bool):
        """Disable/enable specific cards."""
        for card_str in card_strs:
            if card_str in self.cards:
                self.cards[card_str].set_disabled(disabled)

@dataclass
class PlayerInfo:
    """Information about a player at the table."""
    seat: int
    is_active: bool
    stack: float
    bet: float
    cards: Optional[List[Card]] = None
    is_hero: bool = False
    is_dealer: bool = False
    is_sb: bool = False
    is_bb: bool = False
    has_acted: bool = False

class TableVisualization(tk.Canvas):
    """Enhanced poker table visualization."""

    def __init__(self, parent, width=800, height=500):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=COLORS['bg_dark'],
            highlightthickness=0
        )

        self.players: Dict[int, PlayerInfo] = {}
        self.pot_size = 0.0
        self.board_cards: List[Card] = []

        # Seat positions for 9-max table (normalized 0-1)
        self.seat_positions = {
            1: (0.5, 0.85),   # Bottom center (usually hero)
            2: (0.25, 0.82),  # Bottom left
            3: (0.08, 0.65),  # Left
            4: (0.08, 0.35),  # Left top
            5: (0.25, 0.18),  # Top left
            6: (0.5, 0.15),   # Top center
            7: (0.75, 0.18),  # Top right
            8: (0.92, 0.35),  # Right top
            9: (0.92, 0.65),  # Right
        }

        self.bind('<Configure>', self._on_resize)
        self._draw_table()

    def _on_resize(self, event):
        """Handle canvas resize."""
        self._draw_table()

    def _draw_table(self):
        """Draw the complete table."""
        self.delete('all')

        w = self.winfo_width()
        h = self.winfo_height()

        if w <= 1 or h <= 1:
            self.after(100, self._draw_table)
            return

        # Draw table oval
        margin = 60
        self.create_oval(
            margin, margin, w - margin, h - margin,
            fill=COLORS['table_felt'],
            outline=COLORS['table_border'],
            width=4
        )

        # Draw pot area
        self._draw_pot(w // 2, h // 2)

        # Draw board cards
        self._draw_board(w // 2, h // 2)

        # Draw players
        for seat, player in self.players.items():
            self._draw_player(seat, player, w, h)

        # Draw dealer button
        self._draw_dealer_button(w, h)

    def _draw_player(self, seat: int, player: PlayerInfo, canvas_w: int, canvas_h: int):
        """Draw a player at their seat."""
        if seat not in self.seat_positions:
            return

        x_ratio, y_ratio = self.seat_positions[seat]
        x = int(canvas_w * x_ratio)
        y = int(canvas_h * y_ratio)

        # Player circle color
        if player.is_hero:
            fill_color = COLORS['accent_primary']
        elif player.is_active:
            fill_color = COLORS['accent_success']
        else:
            fill_color = COLORS['bg_light']

        # Draw player circle
        radius = 35
        self.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=fill_color,
            outline=COLORS['text_primary'],
            width=2
        )

        # Player label
        label = f'Seat {seat}'
        if player.is_hero:
            label = 'HERO'

        self.create_text(
            x, y - 10,
            text=label,
            font=FONTS['subheading'],
            fill=COLORS['text_primary']
        )

        # Stack size
        self.create_text(
            x, y + 10,
            text=f'${player.stack:.0f}',
            font=FONTS['body'],
            fill=COLORS['text_primary']
        )

        # Current bet
        if player.bet > 0:
            bet_y = y + radius + 20
            self.create_oval(
                x - 20, bet_y - 10, x + 20, bet_y + 10,
                fill=COLORS['accent_warning'],
                outline=COLORS['text_primary']
            )
            self.create_text(
                x, bet_y,
                text=f'${player.bet:.0f}',
                font=('Arial', 10, 'bold'),
                fill=COLORS['bg_dark']
            )

    def _draw_dealer_button(self, canvas_w: int, canvas_h: int):
        """Draw the dealer button."""
        dealer_seat = None
        for seat, player in self.players.items():
            if player.is_dealer:
                dealer_seat = seat
                break

        if dealer_seat and dealer_seat in self.seat_positions:
            x_ratio, y_ratio = self.seat_positions[dealer_seat]
            x = int(canvas_w * x_ratio)
            y = int(canvas_h * y_ratio)

            # Position button offset from player
            offset_x = 50 if x_ratio < 0.5 else -50
            offset_y = 50 if y_ratio < 0.5 else -50

            button_x = x + offset_x
            button_y = y + offset_y

            # Draw button
            self.create_oval(
                button_x - 15, button_y - 15, button_x + 15, button_y + 15,
                fill=COLORS['dealer_button'],
                outline=COLORS['bg_dark'],
                width=2
            )
            self.create_text(
                button_x, button_y,
                text='D',
                font=FONTS['subheading'],
                fill=COLORS['bg_dark']
            )

    def _draw_pot(self, center_x: int, center_y: int):
        """Draw the pot in the center."""
        if self.pot_size > 0:
            self.create_oval(
                center_x - 40, center_y - 20, center_x + 40, center_y + 20,
                fill=COLORS['accent_warning'],
                outline=COLORS['text_primary'],
                width=2
            )
            self.create_text(
                center_x, center_y,
                text=f'POT: ${self.pot_size:.0f}',
                font=FONTS['subheading'],
                fill=COLORS['bg_dark']
            )

    def _draw_board(self, center_x: int, center_y: int):
        """Draw the board cards."""
        if not self.board_cards:
            return

        card_width = 50
        card_height = 70
        spacing = 10
        total_width = len(self.board_cards) * card_width + (len(self.board_cards) - 1) * spacing
        start_x = center_x - total_width // 2

        for i, card in enumerate(self.board_cards):
            x = start_x + i * (card_width + spacing)
            y = center_y + 60

            # Draw card
            self.create_rectangle(
                x, y, x + card_width, y + card_height,
                fill=COLORS['card_bg'],
                outline=COLORS['text_primary'],
                width=2
            )

            # Card text
            suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
            suit_color = COLORS['card_red'] if card.suit in ['h', 'd'] else COLORS['card_black']

            self.create_text(
                x + card_width // 2,
                y + card_height // 2,
                text=f"{card.rank}\n{suit_symbols.get(card.suit, '?')}",
                font=FONTS['card'],
                fill=suit_color
            )

    def update_table(self, players: Dict[int, PlayerInfo], pot: float, board: List[Card]):
        """Update table state and redraw."""
        self.players = players
        self.pot_size = pot
        self.board_cards = board
        self._draw_table()

class EnhancedPokerAssistant(tk.Tk):
    """Enhanced Poker Assistant with visual card selection and clear table view."""

    def __init__(self):
        super().__init__()

        self.title('🎰 Poker Assistant - Enhanced Edition')
        self.geometry('1400x900')
        self.minsize(1200, 800)
        self.configure(bg=COLORS['bg_dark'])

        # State
        self.hole_cards: List[Card] = []
        self.board_cards: List[Card] = []
        self.selected_cards: List[Tuple[str, Suit]] = []
        self.players: Dict[int, PlayerInfo] = self._init_players()
        self.secure_db = None

        # Setup
        self._setup_styles()
        self._build_ui()
        self._init_database()

    def _init_players(self) -> Dict[int, PlayerInfo]:
        """Initialize default player configuration."""
        players = {}
        for seat in range(1, 10):
            players[seat] = PlayerInfo(
                seat=seat,
                is_active=(seat <= 6),  # Default 6 players
                stack=100.0,
                bet=0.0,
                is_hero=(seat == 1),
                is_dealer=(seat == 3)
            )
        return players

    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure styles for different elements
        style.configure('Title.TLabel',
                       font=FONTS['title'],
                       background=COLORS['bg_dark'],
                       foreground=COLORS['text_primary'])

    def _build_ui(self):
        """Build the main UI."""
        # Main container
        main_container = tk.Frame(self, bg=COLORS['bg_dark'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Top section - Table visualization
        table_frame = tk.Frame(main_container, bg=COLORS['bg_dark'])
        table_frame.pack(fill='both', expand=True)

        self.table_viz = TableVisualization(table_frame, width=1200, height=400)
        self.table_viz.pack(fill='both', expand=True)

        # Bottom section - Controls
        controls_frame = tk.Frame(main_container, bg=COLORS['bg_dark'])
        controls_frame.pack(fill='both', expand=True, pady=(10, 0))

        # Left - Card selection
        card_frame = tk.Frame(controls_frame, bg=COLORS['bg_medium'], relief=tk.RAISED, bd=2)
        card_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        self.card_selector = CardSelectionPanel(card_frame, self._on_card_selected)
        self.card_selector.pack(fill='both', expand=True)

        # Right - Game controls and analysis
        right_frame = tk.Frame(controls_frame, bg=COLORS['bg_dark'])
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Game controls
        self._build_game_controls(right_frame)

        # Analysis output
        self._build_analysis_panel(right_frame)

    def _build_game_controls(self, parent):
        """Build game control panel."""
        control_frame = tk.LabelFrame(
            parent,
            text='Game Controls',
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=2
        )
        control_frame.pack(fill='x', pady=(0, 10))

        # Player controls
        player_frame = tk.Frame(control_frame, bg=COLORS['bg_medium'])
        player_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(
            player_frame,
            text='Active Players:',
            font=FONTS['subheading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary']
        ).pack(side='left', padx=(0, 10))

        # Player toggles
        for seat in range(1, 10):
            var = tk.BooleanVar(value=seat <= 6)
            cb = tk.Checkbutton(
                player_frame,
                text=f'{seat}',
                variable=var,
                font=FONTS['body'],
                bg=COLORS['bg_medium'],
                fg=COLORS['text_primary'],
                selectcolor=COLORS['bg_light'],
                command=lambda s=seat, v=var: self._toggle_player(s, v.get())
            )
            cb.pack(side='left', padx=2)

        # Dealer position
        dealer_frame = tk.Frame(control_frame, bg=COLORS['bg_medium'])
        dealer_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(
            dealer_frame,
            text='Dealer Position:',
            font=FONTS['subheading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary']
        ).pack(side='left', padx=(0, 10))

        self.dealer_var = tk.IntVar(value=3)
        dealer_spin = tk.Spinbox(
            dealer_frame,
            from_=1,
            to=9,
            textvariable=self.dealer_var,
            width=5,
            font=FONTS['body'],
            command=self._update_dealer
        )
        dealer_spin.pack(side='left')

        # Action buttons
        action_frame = tk.Frame(control_frame, bg=COLORS['bg_medium'])
        action_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(
            action_frame,
            text='ANALYZE HAND',
            command=self._analyze_hand
        ).pack(side='left', padx=5)

        ttk.Button(
            action_frame,
            text='CLEAR CARDS',
            command=self._clear_cards
        ).pack(side='left', padx=5)

        ttk.Button(
            action_frame,
            text='UPDATE TABLE',
            command=self._update_table
        ).pack(side='left', padx=5)

    def _build_analysis_panel(self, parent):
        """Build analysis output panel."""
        analysis_frame = tk.LabelFrame(
            parent,
            text='Analysis',
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=2
        )
        analysis_frame.pack(fill='both', expand=True)

        # Analysis text
        self.analysis_text = tk.Text(
            analysis_frame,
            font=FONTS['analysis'],
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            wrap='word',
            height=10
        )
        self.analysis_text.pack(fill='both', expand=True, padx=10, pady=10)

    def _on_card_selected(self, card: VisualCard):
        """Handle card selection from visual selector."""
        self.selected_cards = self.card_selector.get_selected_cards()
        self._update_card_assignment()

    def _update_card_assignment(self):
        """Update hole and board card assignments."""
        if len(self.selected_cards) >= 2:
            # First 2 cards are hole cards
            self.hole_cards = self.selected_cards[:2]
            # Remaining are board cards
            self.board_cards = self.selected_cards[2:7]
        elif len(self.selected_cards) == 1:
            self.hole_cards = self.selected_cards[:1]
            self.board_cards = []
        else:
            self.hole_cards = []
            self.board_cards = []

        # Update display
        self._update_table()

    def _toggle_player(self, seat: int, active: bool):
        """Toggle player active status."""
        if seat in self.players:
            self.players[seat].is_active = active
            self._update_table()

    def _update_dealer(self):
        """Update dealer position."""
        dealer_seat = self.dealer_var.get()
        for player in self.players.values():
            player.is_dealer = (player.seat == dealer_seat)

        # Update blinds
        self._update_blinds()
        self._update_table()

    def _update_blinds(self):
        """Update small and big blind positions."""
        # Clear existing blinds
        for player in self.players.values():
            player.is_sb = False
            player.is_bb = False

        # Get active seats
        active_seats = sorted([s for s, p in self.players.items() if p.is_active])
        if len(active_seats) < 2:
            return

        dealer_seat = self.dealer_var.get()

        # Find dealer index
        if dealer_seat in active_seats:
            dealer_idx = active_seats.index(dealer_seat)
        else:
            # Find next active seat after dealer
            dealer_idx = 0
            for i, seat in enumerate(active_seats):
                if seat > dealer_seat:
                    dealer_idx = i
                    break

        # Set blinds
        sb_idx = (dealer_idx + 1) % len(active_seats)
        bb_idx = (dealer_idx + 2) % len(active_seats)

        self.players[active_seats[sb_idx]].is_sb = True
        self.players[active_seats[bb_idx]].is_bb = True

    def _update_table(self):
        """Update table visualization."""
        # Convert selected cards to Card objects if modules are loaded
        board_cards = []
        if MODULES_LOADED and self.board_cards:
            for rank, suit in self.board_cards:
                try:
                    card = Card(rank, suit)
                    board_cards.append(card)
                except Exception:
                    pass

        # Update pot and bets
        try:
            pot = float(getattr(self, 'pot_var', tk.StringVar()).get() or 0)
        except Exception:
            pot = 0.0

        try:
            to_call = float(getattr(self, 'call_var', tk.StringVar()).get() or 0)
        except Exception:
            to_call = 0.0

        # Update player bets
        for player in self.players.values():
            if player.is_bb:
                player.bet = to_call if to_call > 0 else 2.0
            elif player.is_sb:
                player.bet = to_call / 2 if to_call > 0 else 1.0
            else:
                player.bet = 0.0

        self.table_viz.update_table(self.players, pot, board_cards)

    def _analyze_hand(self):
        """Analyze the current hand."""
        if hasattr(self, 'analysis_text'):
            self.analysis_text.delete('1.0', tk.END)
            self.analysis_text.insert('1.0', "Analysis functionality placeholder - modules not fully loaded\n")

    def _clear_cards(self):
        """Clear all selected cards."""
        self.card_selector.clear_selection()
        self.hole_cards = []
        self.board_cards = []
        self._update_table()
        if hasattr(self, 'analysis_text'):
            self.analysis_text.delete('1.0', tk.END)

    def _init_database(self):
        """Initialize database connection."""
        try:
            self.secure_db = get_secure_db()
        except Exception as e:
            print(f'Database initialization failed: {e}')
            self.secure_db = None

# Alias the new GUI class for compatibility
SecureGUI = EnhancedPokerAssistant

def main() -> int:
    """Main GUI entry point."""
    def create_and_run_gui():
        """Create and run the GUI."""
        gui = EnhancedPokerAssistant()
        gui.mainloop()
        return 0

    return run_safely(create_and_run_gui)

# Legacy function names for backward compatibility
def run() -> int:
    """Legacy entry point."""
    return main()

if __name__ == '__main__':
    raise SystemExit(main())
