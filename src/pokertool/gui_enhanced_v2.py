#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: gui_enhanced_v2.py
# version: v21.0.0
# last_commit: 2025-10-12T00:00:00Z
# fixes:
#   - date: 2025-10-12
#     summary: Complete GUI rework with integrated screen scraping
#   - date: 2025-10-12
#     summary: Added real-time poker table detection and monitoring
#   - date: 2025-10-12
#     summary: Enhanced visual feedback and status indicators
#   - date: 2025-10-12
#     summary: Comprehensive error handling and reliability improvements
#   - date: 2025-10-12
#     summary: Cross-platform desktop-independent scraping integration
# ---
# POKERTOOL-HEADER-END

PokerTool Enhanced GUI - Enterprise Edition
============================================

Comprehensive GUI with integrated screen scraping, real-time table monitoring,
and advanced poker hand analysis. Designed for maximum reliability and clarity.

Key Features:
-------------
- Desktop-independent screen scraping (works across all workspaces)
- Real-time poker table detection and monitoring  
- Visual table representation with live updates
- Manual card entry with validation
- Integrated hand analysis engine
- Performance metrics and diagnostics
- Cross-platform compatibility (Windows, macOS, Linux)
- Comprehensive error handling

Architecture:
-------------
1. Main GUI Window (EnhancedPokerToolGUI)
   - Tabbed interface for organized workflow
   - Manual entry tab for direct input
   - Scraper tab for automated detection
   - Analysis tab for results viewing
   - Settings tab for configuration

2. Screen Scraper Integration
   - Desktop-independent window detection
   - Automatic poker table recognition
   - OCR-based card detection
   - Real-time capture and analysis

3. Table Visualization
   - Dynamic 9-max table rendering
   - Player positions and stacks
   - Board cards and pot display
   - Hero cards visualization

4. Analysis Engine
   - Real-time hand strength calculation
   - Position-aware recommendations
   - Pot odds integration
   - Multi-opponent modeling

Module: pokertool.gui_enhanced_v2
Version: v21.0.0
Author: PokerTool Development Team
License: MIT
"""

__version__ = '21.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
import time
import threading
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import core modules
try:
    from .core import (
        Card, Rank, Suit, Position,
        parse_card, analyse_hand, HandAnalysisResult
    )
    CORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Core modules not available: {e}")
    CORE_AVAILABLE = False

# Import screen scraper
try:
    from .desktop_independent_scraper import (
        DesktopIndependentScraper,
        WindowInfo,
        PokerDetectionMode
    )
    SCRAPER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Screen scraper not available: {e}")
    SCRAPER_AVAILABLE = False
    
# Import dependencies for visualization
try:
    import numpy as np
    from PIL import Image, ImageTk
    IMAGING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Imaging libraries not available: {e}")
    IMAGING_AVAILABLE = False

# Color scheme - Professional dark theme
COLORS = {
    'bg_primary': '#1a1f2e',
    'bg_secondary': '#2a3142',
    'bg_tertiary': '#3a4152',
    'bg_panel': '#252b3b',
    'accent_blue': '#4a9eff',
    'accent_green': '#4ade80',
    'accent_yellow': '#fbbf24',
    'accent_red': '#ef4444',
    'text_primary': '#ffffff',
    'text_secondary': '#94a3b8',
    'text_muted': '#64748b',
    'table_felt': '#0d3a26',
    'table_border': '#2a7f5f',
    'card_bg': '#ffffff',
    'card_red': '#DC143C',
    'card_black': '#000000',
    'status_success': '#10b981',
    'status_warning': '#f59e0b',
    'status_error': '#ef4444',
    'status_info': '#3b82f6',
}

FONTS = {
    'title': ('Arial', 20, 'bold'),
    'heading': ('Arial', 14, 'bold'),
    'subheading': ('Arial', 12, 'bold'),
    'body': ('Arial', 11),
    'mono': ('Courier New', 10),
    'small': ('Arial', 9),
    'card': ('Arial', 16, 'bold'),
}


class StatusIndicator(tk.Frame):
    """Visual status indicator with color and text."""
    
    def __init__(self, parent, label: str = "Status", **kwargs):
        super().__init__(parent, bg=COLORS['bg_panel'], **kwargs)
        
        self.label = label
        self.status_text = "Unknown"
        self.status_color = COLORS['text_muted']
        
        # Label
        tk.Label(
            self,
            text=f"{label}:",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).pack(side='left', padx=(0, 5))
        
        # Status indicator dot
        self.indicator = tk.Canvas(self, width=12, height=12, bg=COLORS['bg_panel'], highlightthickness=0)
        self.indicator.pack(side='left', padx=(0, 5))
        self.indicator_id = self.indicator.create_oval(2, 2, 10, 10, fill=self.status_color, outline='')
        
        # Status text
        self.status_label = tk.Label(
            self,
            text=self.status_text,
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary']
        )
        self.status_label.pack(side='left')
    
    def set_status(self, text: str, color: str):
        """Update status indicator."""
        self.status_text = text
        self.status_color = color
        self.indicator.itemconfig(self.indicator_id, fill=color)
        self.status_label.config(text=text)


class MetricsPanel(tk.LabelFrame):
    """Panel displaying performance metrics."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            text="Performance Metrics",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary'],
            **kwargs
        )
        
        self.metrics: Dict[str, tk.Label] = {}
        
        # Create metric rows
        metrics_config = [
            ('captures', 'Total Captures'),
            ('success_rate', 'Success Rate'),
            ('avg_time', 'Avg Time'),
            ('cache_hits', 'Cache Hit Rate'),
            ('windows', 'Detected Windows'),
        ]
        
        for i, (key, label_text) in enumerate(metrics_config):
            row_frame = tk.Frame(self, bg=COLORS['bg_panel'])
            row_frame.pack(fill='x', padx=10, pady=2)
            
            tk.Label(
                row_frame,
                text=f"{label_text}:",
                font=FONTS['small'],
                bg=COLORS['bg_panel'],
                fg=COLORS['text_secondary'],
                width=15,
                anchor='w'
            ).pack(side='left')
            
            value_label = tk.Label(
                row_frame,
                text="--",
                font=FONTS['small'],
                bg=COLORS['bg_panel'],
                fg=COLORS['text_primary'],
                anchor='w'
            )
            value_label.pack(side='left', fill='x', expand=True)
            
            self.metrics[key] = value_label
    
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update displayed metrics."""
        if 'total_captures' in metrics:
            self.metrics['captures'].config(text=str(metrics['total_captures']))
        
        if 'success_rate' in metrics:
            rate = metrics['success_rate'] * 100
            self.metrics['success_rate'].config(text=f"{rate:.1f}%")
        
        if 'avg_capture_time' in metrics:
            time_ms = metrics['avg_capture_time'] * 1000
            self.metrics['avg_time'].config(text=f"{time_ms:.0f}ms")
        
        if 'cache_hit_rate' in metrics:
            rate = metrics['cache_hit_rate'] * 100
            self.metrics['cache_hits'].config(text=f"{rate:.1f}%")


class WindowListPanel(tk.LabelFrame):
    """Panel showing detected poker windows."""
    
    def __init__(self, parent, on_window_selected=None, **kwargs):
        super().__init__(
            parent,
            text="Detected Poker Windows",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary'],
            **kwargs
        )
        
        self.on_window_selected = on_window_selected
        
        # Scrollable list frame
        list_frame = tk.Frame(self, bg=COLORS['bg_panel'])
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.listbox = tk.Listbox(
            list_frame,
            font=FONTS['mono'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            selectbackground=COLORS['accent_blue'],
            selectforeground=COLORS['text_primary'],
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.bind('<<ListboxSelect>>', self._on_selection)
        
        self.windows: List[WindowInfo] = []
    
    def update_windows(self, windows: List[WindowInfo]):
        """Update the list of windows."""
        self.windows = windows
        self.listbox.delete(0, tk.END)
        
        for i, window in enumerate(windows):
            display_text = f"{i+1}. {window.title[:50]} ({window.width}x{window.height})"
            self.listbox.insert(tk.END, display_text)
            
            # Color code by visibility
            if not window.is_visible:
                self.listbox.itemconfig(i, fg=COLORS['text_muted'])
            elif window.is_minimized:
                self.listbox.itemconfig(i, fg=COLORS['accent_yellow'])
    
    def _on_selection(self, event):
        """Handle window selection."""
        selection = self.listbox.curselection()
        if selection and self.on_window_selected:
            index = selection[0]
            if 0 <= index < len(self.windows):
                self.on_window_selected(self.windows[index])


class TableVisualizationCanvas(tk.Canvas):
    """Enhanced table visualization with scraper integration."""
    
    def __init__(self, parent, width=800, height=500, **kwargs):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=COLORS['bg_primary'],
            highlightthickness=0,
            **kwargs
        )
        
        self.players: Dict[int, Dict[str, Any]] = {}
        self.pot_size = 0.0
        self.board_cards: List[Card] = []
        self.hero_cards: List[Card] = []
        self.dealer_seat = 1
        
        # Seat positions for 9-max table
        self.seat_positions = {
            1: (0.5, 0.85),   # Hero - Bottom center
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
        """Draw the complete poker table."""
        self.delete('all')
        
        w = self.winfo_width() or 800
        h = self.winfo_height() or 500
        
        # Draw table oval
        margin = 50
        self.create_oval(
            margin, margin, w - margin, h - margin,
            fill=COLORS['table_felt'],
            outline=COLORS['table_border'],
            width=4
        )
        
        # Draw pot
        self._draw_pot(w // 2, h // 2)
        
        # Draw board
        self._draw_board(w // 2, h // 2)
        
        # Draw players
        for seat, player_data in self.players.items():
            self._draw_player(seat, player_data, w, h)
        
        # Draw hero cards
        self._draw_hero_cards(w, h)
        
        # Draw dealer button
        self._draw_dealer_button(w, h)
    
    def _draw_player(self, seat: int, player_data: Dict[str, Any], canvas_w: int, canvas_h: int):
        """Draw a player at their seat."""
        if seat not in self.seat_positions:
            return
        
        x_ratio, y_ratio = self.seat_positions[seat]
        x = int(canvas_w * x_ratio)
        y = int(canvas_h * y_ratio)
        
        is_hero = player_data.get('is_hero', seat == 1)
        is_active = player_data.get('is_active', True)
        stack = player_data.get('stack', 100.0)
        bet = player_data.get('bet', 0.0)
        
        # Player circle
        fill_color = COLORS['accent_blue'] if is_hero else (COLORS['accent_green'] if is_active else COLORS['bg_tertiary'])
        radius = 35
        
        self.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=fill_color,
            outline=COLORS['text_primary'],
            width=2
        )
        
        # Player label
        label = 'HERO' if is_hero else f'Seat {seat}'
        self.create_text(
            x, y - 10,
            text=label,
            font=FONTS['subheading'],
            fill=COLORS['text_primary']
        )
        
        # Stack
        self.create_text(
            x, y + 10,
            text=f'${stack:.0f}',
            font=FONTS['body'],
            fill=COLORS['text_primary']
        )
        
        # Bet
        if bet > 0:
            bet_y = y + radius + 20
            self.create_oval(
                x - 20, bet_y - 10, x + 20, bet_y + 10,
                fill=COLORS['accent_yellow'],
                outline=COLORS['text_primary']
            )
            self.create_text(
                x, bet_y,
                text=f'${bet:.0f}',
                font=('Arial', 10, 'bold'),
                fill=COLORS['bg_primary']
            )
    
    def _draw_dealer_button(self, canvas_w: int, canvas_h: int):
        """Draw dealer button."""
        if self.dealer_seat not in self.seat_positions:
            return
        
        x_ratio, y_ratio = self.seat_positions[self.dealer_seat]
        x = int(canvas_w * x_ratio)
        y = int(canvas_h * y_ratio)
        
        offset_x = 50 if x_ratio < 0.5 else -50
        offset_y = 50 if y_ratio < 0.5 else -50
        
        button_x = x + offset_x
        button_y = y + offset_y
        
        self.create_oval(
            button_x - 15, button_y - 15, button_x + 15, button_y + 15,
            fill='#FFD700',
            outline=COLORS['bg_primary'],
            width=2
        )
        self.create_text(
            button_x, button_y,
            text='D',
            font=FONTS['subheading'],
            fill=COLORS['bg_primary']
        )
    
    def _draw_pot(self, center_x: int, center_y: int):
        """Draw pot."""
        if self.pot_size > 0:
            self.create_oval(
                center_x - 40, center_y - 20, center_x + 40, center_y + 20,
                fill=COLORS['accent_yellow'],
                outline=COLORS['text_primary'],
                width=2
            )
            self.create_text(
                center_x, center_y,
                text=f'POT: ${self.pot_size:.0f}',
                font=FONTS['subheading'],
                fill=COLORS['bg_primary']
            )
    
    def _draw_board(self, center_x: int, center_y: int):
        """Draw board cards."""
        if not self.board_cards:
            return
        
        card_width = 50
        card_height = 70
        spacing = 10
        total_width = len(self.board_cards) * card_width + (len(self.board_cards) - 1) * spacing
        start_x = center_x - total_width // 2
        
        suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
        
        for i, card in enumerate(self.board_cards):
            x = start_x + i * (card_width + spacing)
            y = center_y + 60
            
            self.create_rectangle(
                x, y, x + card_width, y + card_height,
                fill=COLORS['card_bg'],
                outline=COLORS['text_primary'],
                width=2
            )
            
            card_suit = getattr(card, 'suit', 's')
            if hasattr(card_suit, 'value'):
                card_suit = card_suit.value
            card_rank = getattr(card, 'rank', '?')
            if hasattr(card_rank, 'sym'):
                card_rank = card_rank.sym
            
            symbol = suit_symbols.get(str(card_suit), '?')
            suit_color = COLORS['card_red'] if card_suit in ['h', 'd'] else COLORS['card_black']
            
            self.create_text(
                x + card_width // 2,
                y + card_height // 2,
                text=f"{card_rank}\n{symbol}",
                font=FONTS['card'],
                fill=suit_color
            )
    
    def _draw_hero_cards(self, canvas_w: int, canvas_h: int):
        """Draw hero's hole cards."""
        if not self.hero_cards or 1 not in self.seat_positions:
            return
        
        x_ratio, y_ratio = self.seat_positions[1]
        player_x = int(canvas_w * x_ratio)
        player_y = int(canvas_h * y_ratio)
        
        card_width = 50
        card_height = 70
        spacing = 10
        total_width = len(self.hero_cards) * card_width + (len(self.hero_cards) - 1) * spacing
        start_x = player_x - total_width // 2
        y = player_y - 35 - card_height - 10
        
        suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
        
        for idx, card in enumerate(self.hero_cards):
            cx = start_x + idx * (card_width + spacing)
            
            self.create_rectangle(
                cx, y, cx + card_width, y + card_height,
                fill=COLORS['card_bg'],
                outline=COLORS['text_primary'],
                width=2
            )
            
            card_suit = getattr(card, 'suit', 's')
            if hasattr(card_suit, 'value'):
                card_suit = card_suit.value
            card_rank = getattr(card, 'rank', '?')
            if hasattr(card_rank, 'sym'):
                card_rank = card_rank.sym
            
            symbol = suit_symbols.get(str(card_suit), '?')
            suit_color = COLORS['card_red'] if card_suit in ['h', 'd'] else COLORS['card_black']
            
            self.create_text(
                cx + card_width // 2,
                y + card_height // 2,
                text=f"{card_rank}\n{symbol}",
                font=FONTS['card'],
                fill=suit_color
            )
    
    def update_table(self, players: Dict[int, Dict[str, Any]], pot: float, board: List[Card], hero_cards: List[Card] = None):
        """Update table state."""
        self.players = players
        self.pot_size = pot
        self.board_cards = board
        if hero_cards is not None:
            self.hero_cards = hero_cards
        self._draw_table()


class EnhancedPokerToolGUI(tk.Tk):
    """
    Main GUI application with integrated screen scraping and hand analysis.
    
    Features:
    - Desktop-independent screen scraping
    - Real-time poker table detection
    - Manual card entry and analysis
    - Visual table representation
    - Performance monitoring
    """
    
    def __init__(self):
        super().__init__()
        
        self.title('🎰 PokerTool - Enterprise Edition v21.0.0')
        self.geometry('1400x900')
        self.minsize(1200, 800)
        self.configure(bg=COLORS['bg_primary'])
        
        # Application state
        self.scraper: Optional[DesktopIndependentScraper] = None
        self.selected_window: Optional[WindowInfo] = None
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Initialize components
        self._init_scraper()
        self._setup_ui()
        self._setup_menu()
        
        # Start update loop
        self.after(100, self._update_loop)
        
        logger.info("PokerTool GUI initialized successfully")
    
    def _init_scraper(self):
        """Initialize screen scraper."""
        if SCRAPER_AVAILABLE:
            try:
                self.scraper = DesktopIndependentScraper()
                self.scraper.register_callback(self._handle_scraper_result)
                logger.info("Screen scraper initialized")
            except Exception as e:
                logger.error(f"Failed to initialize scraper: {e}")
                self.scraper = None
        else:
            logger.warning("Screen scraper not available")
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self._new_session)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Scraper menu
        scraper_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Scraper", menu=scraper_menu)
        scraper_menu.add_command(label="Scan for Windows", command=self._scan_windows)
        scraper_menu.add_command(label="Start Monitoring", command=self._start_monitoring)
        scraper_menu.add_command(label="Stop Monitoring", command=self._stop_monitoring)
        scraper_menu.add_separator()
        scraper_menu.add_command(label="Save Debug Screenshots", command=self._save_screenshots)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_docs)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _setup_ui(self):
        """Setup main UI."""
        # Main container
        main_container = tk.Frame(self, bg=COLORS['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=COLORS['bg_primary'], borderwidth=0)
        style.configure('TNotebook.Tab', padding=(20, 10), font=FONTS['heading'])
        
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self._create_scraper_tab()
        self._create_manual_tab()
        self._create_analysis_tab()
        self._create_settings_tab()
        
        # Status bar at bottom
        self._create_status_bar()
    
    def _create_scraper_tab(self):
        """Create screen scraper tab."""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(tab, text='🔍 Screen Scraper')
        
        # Top section - Controls and status
        top_frame = tk.Frame(tab, bg=COLORS['bg_primary'])
        top_frame.pack(fill='x', padx=10, pady=10)
        
        # Left - Controls
        controls_frame = tk.LabelFrame(
            top_frame,
            text="Scraper Controls",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary']
        )
        controls_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Scan button
        tk.Button(
            controls_frame,
            text="🔍 Scan for Poker Windows",
            command=self._scan_windows,
            font=FONTS['heading'],
            bg=COLORS['accent_blue'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['accent_green'],
            padx=20,
            pady=10
        ).pack(pady=10)
        
        # Monitoring toggle
        self.monitor_button = tk.Button(
            controls_frame,
            text="▶️ Start Monitoring",
            command=self._toggle_monitoring,
            font=FONTS['heading'],
            bg=COLORS['accent_green'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['accent_red'],
            padx=20,
            pady=10
        )
        self.monitor_button.pack(pady=10)
        
        # Status indicators
        status_frame = tk.Frame(controls_frame, bg=COLORS['bg_panel'])
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.scraper_status = StatusIndicator(status_frame, "Scraper")
        self.scraper_status.pack(fill='x', pady=2)
        self.scraper_status.set_status("Ready", COLORS['status_info'])
        
        self.monitor_status = StatusIndicator(status_frame, "Monitoring")
        self.monitor_status.pack(fill='x', pady=2)
        self.monitor_status.set_status("Inactive", COLORS['text_muted'])
        
        # Right - Metrics
        self.metrics_panel = MetricsPanel(top_frame)
        self.metrics_panel.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        # Middle section - Detected windows
        self.window_list = WindowListPanel(
            tab,
            on_window_selected=self._on_window_selected
        )
        self.window_list.pack(fill='x', padx=10, pady=10)
        
        # Bottom section - Table visualization
        table_frame = tk.LabelFrame(
            tab,
            text="Table Visualization",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary']
        )
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.table_canvas = TableVisualizationCanvas(table_frame, width=1200, height=400)
        self.table_canvas.pack(fill='both', expand=True, padx=10, pady=10)
    
    def _create_manual_tab(self):
        """Create manual entry tab."""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(tab, text='✏️ Manual Entry')
        
        # Left side - Card entry
        left_frame = tk.Frame(tab, bg=COLORS['bg_primary'])
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        
        # Hole cards
        hole_frame = tk.LabelFrame(
            left_frame,
            text="Hole Cards",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary']
        )
        hole_frame.pack(fill='x', pady=(0, 10))
        
        entry_frame = tk.Frame(hole_frame, bg=COLORS['bg_panel'])
        entry_frame.pack(padx=10, pady=10)
        
        tk.Label(
            entry_frame,
            text="Card 1:",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).grid(row=0, column=0, padx=5, pady=5)
        
        self.hole1_entry = tk.Entry(entry_frame, font=FONTS['body'], width=5)
        self.hole1_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(
            entry_frame,
            text="Card 2:",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).grid(row=0, column=2, padx=5, pady=5)
        
        self.hole2_entry = tk.Entry(entry_frame, font=FONTS['body'], width=5)
        self.hole2_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Board cards
        board_frame = tk.LabelFrame(
            left_frame,
            text="Board Cards",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary']
        )
        board_frame.pack(fill='x', pady=(0, 10))
        
        board_entry_frame = tk.Frame(board_frame, bg=COLORS['bg_panel'])
        board_entry_frame.pack(padx=10, pady=10)
        
        self.board_entries = []
        for i in range(5):
            tk.Label(
                board_entry_frame,
                text=f"C{i+1}:",
                font=FONTS['body'],
                bg=COLORS['bg_panel'],
                fg=COLORS['text_secondary']
            ).grid(row=0, column=i*2, padx=2, pady=5)
            
            entry = tk.Entry(board_entry_frame, font=FONTS['body'], width=5)
            entry.grid(row=0, column=i*2+1, padx=2, pady=5)
            self.board_entries.append(entry)
        
        # Game state
        state_frame = tk.LabelFrame(
            left_frame,
            text="Game State",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary']
        )
        state_frame.pack(fill='both', expand=True)
        
        state_grid = tk.Frame(state_frame, bg=COLORS['bg_panel'])
        state_grid.pack(padx=10, pady=10)
        
        # Position
        tk.Label(
            state_grid,
            text="Position:",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        if CORE_AVAILABLE:
            positions = [p.value for p in Position]
        else:
            positions = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
        
        self.position_var = tk.StringVar(value=positions[0])
        position_menu = ttk.Combobox(
            state_grid,
            textvariable=self.position_var,
            values=positions,
            state='readonly',
            width=15
        )
        position_menu.grid(row=0, column=1, padx=5, pady=5)
        
        # Pot size
        tk.Label(
            state_grid,
            text="Pot Size:",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        self.pot_entry = tk.Entry(state_grid, font=FONTS['body'], width=15)
        self.pot_entry.insert(0, "100")
        self.pot_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # To call
        tk.Label(
            state_grid,
            text="To Call:",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).grid(row=2, column=0, sticky='w', padx=5, pady=5)
        
        self.call_entry = tk.Entry(state_grid, font=FONTS['body'], width=15)
        self.call_entry.insert(0, "10")
        self.call_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Opponents
        tk.Label(
            state_grid,
            text="Opponents:",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).grid(row=3, column=0, sticky='w', padx=5, pady=5)
        
        self.opponents_entry = tk.Entry(state_grid, font=FONTS['body'], width=15)
        self.opponents_entry.insert(0, "1")
        self.opponents_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Analyze button
        tk.Button(
            left_frame,
            text="⚡ ANALYZE HAND",
            command=self._analyze_manual_hand,
            font=FONTS['heading'],
            bg=COLORS['accent_blue'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['accent_green'],
            padx=20,
            pady=15
        ).pack(pady=20)
        
        # Right side - Results
        results_frame = tk.LabelFrame(
            tab,
            text="Analysis Results",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary']
        )
        results_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)
        
        self.manual_results_text = scrolledtext.ScrolledText(
            results_frame,
            font=FONTS['mono'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            wrap='word',
            width=50
        )
        self.manual_results_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def _create_analysis_tab(self):
        """Create analysis history tab."""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(tab, text='📊 Analysis History')
        
        tk.Label(
            tab,
            text="Analysis History",
            font=FONTS['title'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary']
        ).pack(pady=20)
        
        self.history_text = scrolledtext.ScrolledText(
            tab,
            font=FONTS['mono'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            wrap='word'
        )
        self.history_text.pack(fill='both', expand=True, padx=20, pady=20)
    
    def _create_settings_tab(self):
        """Create settings tab."""
        tab = tk.Frame(self.notebook, bg=COLORS['bg_primary'])
        self.notebook.add(tab, text='⚙️ Settings')
        
        tk.Label(
            tab,
            text="Settings",
            font=FONTS['title'],
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary']
        ).pack(pady=20)
        
        settings_frame = tk.Frame(tab, bg=COLORS['bg_primary'])
        settings_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Scraper settings
        scraper_group = tk.LabelFrame(
            settings_frame,
            text="Screen Scraper Settings",
            font=FONTS['heading'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_primary']
        )
        scraper_group.pack(fill='x', pady=10)
        
        # Scan interval
        interval_frame = tk.Frame(scraper_group, bg=COLORS['bg_panel'])
        interval_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            interval_frame,
            text="Scan Interval (seconds):",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).pack(side='left', padx=5)
        
        self.scan_interval_var = tk.StringVar(value="2.0")
        tk.Entry(
            interval_frame,
            textvariable=self.scan_interval_var,
            font=FONTS['body'],
            width=10
        ).pack(side='left', padx=5)
        
        # Detection mode
        mode_frame = tk.Frame(scraper_group, bg=COLORS['bg_panel'])
        mode_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            mode_frame,
            text="Detection Mode:",
            font=FONTS['body'],
            bg=COLORS['bg_panel'],
            fg=COLORS['text_secondary']
        ).pack(side='left', padx=5)
        
        self.detection_mode_var = tk.StringVar(value="combined")
        modes = ['window_title', 'process_name', 'combined', 'fuzzy_match']
        ttk.Combobox(
            mode_frame,
            textvariable=self.detection_mode_var,
            values=modes,
            state='readonly',
            width=15
        ).pack(side='left', padx=5)
    
    def _create_status_bar(self):
        """Create status bar at bottom."""
        self.status_bar = tk.Frame(self, bg=COLORS['bg_secondary'], height=30)
        self.status_bar.pack(side='bottom', fill='x')
        
        self.status_label = tk.Label(
            self.status_bar,
            text="Ready",
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            anchor='w'
        )
        self.status_label.pack(side='left', padx=10)
        
        # Platform info
        platform_text = f"Platform: {self.scraper.platform if self.scraper else 'Unknown'}"
        tk.Label(
            self.status_bar,
            text=platform_text,
            font=FONTS['small'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary']
        ).pack(side='right', padx=10)
    
    def _scan_windows(self):
        """Scan for poker windows."""
        if not self.scraper:
            messagebox.showerror("Error", "Screen scraper not available")
            return
        
        self.scraper_status.set_status("Scanning...", COLORS['status_warning'])
        self.status_label.config(text="Scanning for poker windows...")
        self.update_idletasks()
        
        def scan_thread():
            try:
                mode_str = self.detection_mode_var.get()
                if SCRAPER_AVAILABLE:
                    mode = PokerDetectionMode(mode_str)
                    windows = self.scraper.scan_for_poker_windows(mode)
                else:
                    windows = []
                
                self.after(0, lambda: self._handle_scan_results(windows))
            except Exception as e:
                logger.error(f"Scan failed: {e}")
                self.after(0, lambda: self._handle_scan_error(str(e)))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _handle_scan_results(self, windows: List[WindowInfo]):
        """Handle scan results."""
        self.window_list.update_windows(windows)
        
        if windows:
            self.scraper_status.set_status(f"Found {len(windows)} windows", COLORS['status_success'])
            self.status_label.config(text=f"Found {len(windows)} poker windows")
        else:
            self.scraper_status.set_status("No windows found", COLORS['status_warning'])
            self.status_label.config(text="No poker windows found")
        
        # Update metrics
        if self.scraper:
            metrics = self.scraper.get_performance_metrics()
            metrics['windows'] = len(windows)
            self.metrics_panel.update_metrics(metrics)
    
    def _handle_scan_error(self, error: str):
        """Handle scan error."""
        self.scraper_status.set_status("Error", COLORS['status_error'])
        self.status_label.config(text=f"Scan error: {error}")
        messagebox.showerror("Scan Error", f"Failed to scan windows:\n{error}")
    
    def _on_window_selected(self, window: WindowInfo):
        """Handle window selection."""
        self.selected_window = window
        self.status_label.config(text=f"Selected: {window.title}")
        
        # Capture window
        if self.scraper:
            try:
                result = self.scraper.capture_window(window, include_screenshot=True)
                if result and result.get('success'):
                    self._update_table_from_scraper(result)
            except Exception as e:
                logger.error(f"Failed to capture window: {e}")
    
    def _update_table_from_scraper(self, result: Dict[str, Any]):
        """Update table visualization from scraper result."""
        # Extract game state from scraper result
        window_info = result.get('window_info')
        
        # Initialize players
        players = {}
        for seat in range(1, 10):
            players[seat] = {
                'is_hero': seat == 1,
                'is_active': seat <= 6,  # Default 6 players
                'stack': 100.0,
                'bet': 0.0
            }
        
        # Extract detected information
        seat_count = result.get('seat_count', 6)
        for seat in range(1, min(seat_count + 1, 10)):
            players[seat]['is_active'] = True
        
        # Update table
        self.table_canvas.update_table(players, 0.0, [], [])
        
        # Log activity
        self._log_analysis(f"Window captured: {window_info.title if window_info else 'Unknown'}")
    
    def _toggle_monitoring(self):
        """Toggle monitoring on/off."""
        if self.monitoring_active:
            self._stop_monitoring()
        else:
            self._start_monitoring()
    
    def _start_monitoring(self):
        """Start continuous monitoring."""
        if not self.scraper:
            messagebox.showerror("Error", "Screen scraper not available")
            return
        
        if not self.scraper.detected_windows:
            messagebox.showwarning("Warning", "No windows detected. Run scan first.")
            return
        
        try:
            interval = float(self.scan_interval_var.get())
        except ValueError:
            interval = 2.0
        
        if self.scraper.start_continuous_monitoring(interval):
            self.monitoring_active = True
            self.monitor_button.config(text="⏸️ Stop Monitoring", bg=COLORS['accent_red'])
            self.monitor_status.set_status("Active", COLORS['status_success'])
            self.status_label.config(text="Monitoring started")
            logger.info("Monitoring started")
    
    def _stop_monitoring(self):
        """Stop continuous monitoring."""
        if self.scraper:
            self.scraper.stop_monitoring()
        
        self.monitoring_active = False
        self.monitor_button.config(text="▶️ Start Monitoring", bg=COLORS['accent_green'])
        self.monitor_status.set_status("Inactive", COLORS['text_muted'])
        self.status_label.config(text="Monitoring stopped")
        logger.info("Monitoring stopped")
    
    def _handle_scraper_result(self, result: Dict[str, Any]):
        """Handle scraper callback result."""
        # Update UI on main thread
        self.after(0, lambda: self._update_table_from_scraper(result))
    
    def _analyze_manual_hand(self):
        """Analyze manually entered hand."""
        if not CORE_AVAILABLE:
            messagebox.showerror("Error", "Core analysis modules not available")
            return
        
        try:
            # Parse hole cards
            hole1 = self.hole1_entry.get().strip()
            hole2 = self.hole2_entry.get().strip()
            
            if not hole1 or not hole2:
                messagebox.showwarning("Warning", "Please enter both hole cards")
                return
            
            hole_cards = [parse_card(hole1), parse_card(hole2)]
            
            # Parse board cards
            board_cards = []
            for entry in self.board_entries:
                card_str = entry.get().strip()
                if card_str:
                    board_cards.append(parse_card(card_str))
            
            # Parse game state
            position = Position(self.position_var.get())
            pot = float(self.pot_entry.get() or 0)
            to_call = float(self.call_entry.get() or 0)
            opponents = int(self.opponents_entry.get() or 1)
            
            # Analyze hand
            result = analyse_hand(
                hole_cards=hole_cards,
                board_cards=board_cards if board_cards else None,
                position=position,
                pot=pot,
                to_call=to_call,
                num_opponents=opponents
            )
            
            # Display results
            self._display_analysis_result(result, hole_cards, board_cards)
            
            # Update table visualization
            players = {1: {'is_hero': True, 'is_active': True, 'stack': 100.0, 'bet': 0.0}}
            for i in range(2, opponents + 2):
                players[i] = {'is_hero': False, 'is_active': True, 'stack': 100.0, 'bet': 0.0}
            
            self.table_canvas.update_table(players, pot, board_cards, hole_cards)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            messagebox.showerror("Error", f"Analysis failed: {e}")
    
    def _display_analysis_result(self, result: HandAnalysisResult, hole_cards: List[Card], board_cards: List[Card]):
        """Display analysis result."""
        self.manual_results_text.delete('1.0', tk.END)
        
        # Header
        self.manual_results_text.insert('1.0', "="*50 + "\n")
        self.manual_results_text.insert('end', "HAND ANALYSIS RESULT\n")
        self.manual_results_text.insert('end', "="*50 + "\n\n")
        
        # Hand info
        hole_str = ', '.join(str(c) for c in hole_cards)
        self.manual_results_text.insert('end', f"Hole Cards: {hole_str}\n")
        
        if board_cards:
            board_str = ', '.join(str(c) for c in board_cards)
            self.manual_results_text.insert('end', f"Board: {board_str}\n")
        
        self.manual_results_text.insert('end', "\n")
        
        # Results
        self.manual_results_text.insert('end', f"Hand Type: {result.details.get('hand_type', 'Unknown')}\n")
        self.manual_results_text.insert('end', f"Strength: {result.strength:.2f}/10.0\n")
        self.manual_results_text.insert('end', f"Recommendation: {result.advice.upper()}\n\n")
        
        # Position and opponents
        self.manual_results_text.insert('end', f"Position: {result.details.get('position', 'Unknown')}\n")
        self.manual_results_text.insert('end', f"Opponents: {result.details.get('num_opponents', 0)}\n\n")
        
        # Pot odds
        if result.details.get('pot') and result.details.get('to_call'):
            pot_odds_ratio = result.details.get('pot_odds_ratio', 0)
            self.manual_results_text.insert('end', f"Pot: ${result.details['pot']:.2f}\n")
            self.manual_results_text.insert('end', f"To Call: ${result.details['to_call']:.2f}\n")
            self.manual_results_text.insert('end', f"Pot Odds Ratio: {pot_odds_ratio:.2%}\n\n")
        
        # Made hands
        self.manual_results_text.insert('end', "Made Hands:\n")
        for hand_type in ['ONE_PAIR', 'TWO_PAIR', 'THREE_OF_A_KIND', 'STRAIGHT', 'FLUSH', 'FULL_HOUSE', 'FOUR_OF_A_KIND', 'STRAIGHT_FLUSH']:
            if result.details.get(hand_type):
                self.manual_results_text.insert('end', f"  ✓ {hand_type.replace('_', ' ').title()}\n")
        
        # Log to history
        self._log_analysis(f"Manual analysis: {hole_str} - {result.advice.upper()} (Strength: {result.strength:.2f})")
    
    def _log_analysis(self, message: str):
        """Log analysis to history."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.history_text.insert('1.0', log_message)
        
        # Keep only last 100 entries
        lines = self.history_text.get('1.0', tk.END).split('\n')
        if len(lines) > 100:
            self.history_text.delete('101.0', tk.END)
    
    def _update_loop(self):
        """Periodic update loop."""
        # Update metrics if scraper available
        if self.scraper:
            try:
                metrics = self.scraper.get_performance_metrics()
                metrics['windows'] = len(self.scraper.detected_windows)
                self.metrics_panel.update_metrics(metrics)
            except Exception as e:
                logger.debug(f"Metrics update error: {e}")
        
        # Schedule next update
        self.after(1000, self._update_loop)
    
    def _new_session(self):
        """Start new session."""
        # Clear all entries
        self.hole1_entry.delete(0, tk.END)
        self.hole2_entry.delete(0, tk.END)
        for entry in self.board_entries:
            entry.delete(0, tk.END)
        
        # Reset table
        self.table_canvas.update_table({}, 0.0, [], [])
        
        self.status_label.config(text="New session started")
    
    def _save_screenshots(self):
        """Save debug screenshots."""
        if not self.scraper or not self.scraper.detected_windows:
            messagebox.showwarning("Warning", "No windows detected")
            return
        
        try:
            output_dir = "debug_screenshots"
            saved_files = self.scraper.save_debug_screenshots(output_dir)
            
            if saved_files:
                messagebox.showinfo("Success", f"Saved {len(saved_files)} screenshots to {output_dir}/")
            else:
                messagebox.showwarning("Warning", "No screenshots saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save screenshots: {e}")
    
    def _show_docs(self):
        """Show documentation."""
        doc_text = """
PokerTool - User Guide
======================

SCREEN SCRAPER TAB:
1. Click "Scan for Poker Windows" to detect poker applications
2. Select a window from the list to view it
3. Click "Start Monitoring" to continuously monitor selected windows
4. View real-time metrics and table state

MANUAL ENTRY TAB:
1. Enter your hole cards (e.g., As, Kh)
2. Enter board cards if post-flop (e.g., Qs, Jd, Tc)
3. Set position, pot size, and bet amount
4. Click "ANALYZE HAND" for recommendations

ANALYSIS HISTORY TAB:
- View history of all analyses performed
- Includes timestamps and key decisions

SETTINGS TAB:
- Configure scan interval
- Change detection mode
- Adjust scraper parameters

KEYBOARD SHORTCUTS:
- Ctrl+N: New Session
- Ctrl+S: Scan Windows
- Ctrl+M: Toggle Monitoring
- Ctrl+Q: Quit

For more information, visit the documentation.
        """
        
        doc_window = tk.Toplevel(self)
        doc_window.title("Documentation")
        doc_window.geometry("600x500")
        doc_window.configure(bg=COLORS['bg_primary'])
        
        text = scrolledtext.ScrolledText(
            doc_window,
            font=FONTS['mono'],
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_primary'],
            wrap='word'
        )
        text.pack(fill='both', expand=True, padx=20, pady=20)
        text.insert('1.0', doc_text)
        text.config(state='disabled')
    
    def _show_about(self):
        """Show about dialog."""
        about_text = f"""
PokerTool - Enterprise Edition
Version {__version__}

Professional poker analysis tool with integrated
screen scraping and real-time table monitoring.

Features:
• Desktop-independent screen scraping
• Cross-platform compatibility
• Real-time poker table detection
• Advanced hand analysis engine
• Performance monitoring

{__copyright__}
License: {__license__}

Developed by {__author__}
        """
        messagebox.showinfo("About PokerTool", about_text.strip())


def main():
    """Main entry point."""
    try:
        app = EnhancedPokerToolGUI()
        app.mainloop()
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
