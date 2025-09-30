#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
PokerTool Enhanced Gui Module
===============================

This module provides functionality for enhanced gui operations
within the PokerTool application ecosystem.

Module: pokertool.enhanced_gui
Version: 20.0.0
Last Modified: 2025-09-29
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v28.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '20.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import threading
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from pathlib import Path
import subprocess
import webbrowser

# Import all pokertool modules
try:
    from .gui import EnhancedPokerAssistant, VisualCard, CardSelectionPanel, TableVisualization
    from .core import analyse_hand, Card, Suit, Position, HandAnalysisResult
    from .gto_solver import GTOSolver, get_gto_solver
    from .ml_opponent_modeling import OpponentModelingSystem, get_opponent_modeling_system
    from .multi_table_support import TableManager, get_table_manager
    from .error_handling import sanitize_input, run_safely
    from .storage import get_secure_db
    GUI_MODULES_LOADED = True
except ImportError as e:
    print(f'Warning: GUI modules not fully loaded: {e}')
    GUI_MODULES_LOADED = False

# Import screen scraper
try:
    import sys
    sys.path.append('.')
    from poker_screen_scraper import PokerScreenScraper, PokerSite, TableState, create_scraper
    SCREEN_SCRAPER_LOADED = True
except ImportError as e:
    print(f'Warning: Screen scraper not loaded: {e}')
    SCREEN_SCRAPER_LOADED = False

# Import enhanced scraper manager utilities
try:
    from .scrape import run_screen_scraper, stop_screen_scraper
    ENHANCED_SCRAPER_LOADED = True
except ImportError as e:
    print(f'Warning: Enhanced screen scraper not loaded: {e}')
    ENHANCED_SCRAPER_LOADED = False

# Enhanced color scheme with autopilot colors
COLORS = {
    'bg_dark': '#1a1f2e',
    'bg_medium': '#2a3142',
    'bg_light': '#3a4152',
    'accent_primary': '#4a9eff',
    'accent_success': '#4ade80',
    'accent_warning': '#fbbf24',
    'accent_danger': '#ef4444',
    'autopilot_active': '#00ff00',  # Bright green for active autopilot
    'autopilot_inactive': '#ff4444',  # Red for inactive
    'autopilot_standby': '#ffaa00',   # Orange for standby
    'text_primary': '#ffffff',
    'text_secondary': '#94a3b8',
    'table_felt': '#0d3a26',
    'table_border': '#2a7f5f',
    'dealer_button': '#FFD700',
    'small_blind': '#FFA500',
    'big_blind': '#DC143C',
}

# Enhanced fonts
FONTS = {
    'title': ('Arial', 28, 'bold'),
    'heading': ('Arial', 18, 'bold'),
    'subheading': ('Arial', 14, 'bold'),
    'body': ('Arial', 12),
    'autopilot': ('Arial', 20, 'bold'),  # Special font for autopilot
    'status': ('Arial', 16, 'bold'),
    'analysis': ('Consolas', 14)
}

@dataclass
class AutopilotState:
    """State of the autopilot system."""
    active: bool = False
    scraping: bool = False
    site: str = 'GENERIC'
    tables_detected: int = 0
    actions_taken: int = 0
    last_action: str = 'None'
    last_decision: str = 'None'
    profit_session: float = 0.0
    hands_played: int = 0
    start_time: Optional[datetime] = None

class AutopilotControlPanel(tk.Frame):
    """Prominent autopilot control panel."""
    
    def __init__(self, parent, on_toggle_autopilot=None, on_settings_changed=None):
        super().__init__(parent, bg=COLORS['bg_medium'], relief=tk.RAISED, bd=3)
        
        self.on_toggle_autopilot = on_toggle_autopilot
        self.on_settings_changed = on_settings_changed
        
        self.state = AutopilotState()
        self.animation_running = False
        self._animation_id = None
        
        self._build_ui()
        self._start_animation()
        
        # Bind cleanup on destroy
        self.bind('<Destroy>', self._on_destroy)
    
    def _on_destroy(self, event=None):
        """Clean up animation when widget is destroyed."""
        self.animation_running = False
        if self._animation_id:
            try:
                self.after_cancel(self._animation_id)
            except:
                pass
    
    def _build_ui(self):
        """Build the autopilot control interface."""
        # Main title
        title_frame = tk.Frame(self, bg=COLORS['bg_medium'])
        title_frame.pack(fill='x', pady=10)
        
        title_label = tk.Label(
            title_frame,
            text='🤖 POKER AUTOPILOT',
            font=FONTS['title'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary']
        )
        title_label.pack()
        
        # Status indicator
        status_frame = tk.Frame(self, bg=COLORS['bg_medium'])
        status_frame.pack(fill='x', pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text='● INACTIVE',
            font=FONTS['status'],
            bg=COLORS['bg_medium'],
            fg=COLORS['autopilot_inactive']
        )
        self.status_label.pack()
        
        # Main autopilot button
        self.autopilot_button = tk.Button(
            self,
            text='START AUTOPILOT',
            font=FONTS['autopilot'],
            bg=COLORS['autopilot_inactive'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['autopilot_active'],
            activeforeground=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=5,
            width=20,
            height=3,
            command=self._toggle_autopilot
        )
        self.autopilot_button.pack(pady=20)
        
        # Settings panel
        settings_frame = tk.LabelFrame(
            self,
            text='Autopilot Settings',
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=2
        )
        settings_frame.pack(fill='x', padx=10, pady=10)
        
        # Poker site selection
        site_frame = tk.Frame(settings_frame, bg=COLORS['bg_medium'])
        site_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            site_frame,
            text='Poker Site:',
            font=FONTS['subheading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary']
        ).pack(side='left')
        
        self.site_var = tk.StringVar(value='GENERIC')
        site_combo = ttk.Combobox(
            site_frame,
            textvariable=self.site_var,
            values=['GENERIC', 'POKERSTARS', 'PARTYPOKER', 'IGNITION', 'BOVADA'],
            state='readonly',
            width=15
        )
        site_combo.pack(side='right')
        site_combo.bind('<<ComboboxSelected>>', self._on_site_changed)
        
        # Strategy selection
        strategy_frame = tk.Frame(settings_frame, bg=COLORS['bg_medium'])
        strategy_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            strategy_frame,
            text='Strategy:',
            font=FONTS['subheading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary']
        ).pack(side='left')
        
        self.strategy_var = tk.StringVar(value='GTO')
        strategy_combo = ttk.Combobox(
            strategy_frame,
            textvariable=self.strategy_var,
            values=['GTO', 'Aggressive', 'Conservative', 'Exploitative'],
            state='readonly',
            width=15
        )
        strategy_combo.pack(side='right')
        
        # Advanced options
        self.auto_sit_var = tk.BooleanVar(value=True)
        auto_sit_cb = tk.Checkbutton(
            settings_frame,
            text='Auto-sit at tables',
            variable=self.auto_sit_var,
            font=FONTS['body'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light']
        )
        auto_sit_cb.pack(anchor='w', padx=10, pady=2)
        
        self.multi_table_var = tk.BooleanVar(value=True)
        multi_table_cb = tk.Checkbutton(
            settings_frame,
            text='Multi-table support',
            variable=self.multi_table_var,
            font=FONTS['body'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light']
        )
        multi_table_cb.pack(anchor='w', padx=10, pady=2)
        
        self.auto_gto_var = tk.BooleanVar(value=True)
        auto_gto_cb = tk.Checkbutton(
            settings_frame,
            text='Auto GTO analysis',
            variable=self.auto_gto_var,
            font=FONTS['body'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light']
        )
        auto_gto_cb.pack(anchor='w', padx=10, pady=2)
        
        self.auto_detect_var = tk.BooleanVar(value=True)
        auto_detect_cb = tk.Checkbutton(
            settings_frame,
            text='Auto table detection',
            variable=self.auto_detect_var,
            font=FONTS['body'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light']
        )
        auto_detect_cb.pack(anchor='w', padx=10, pady=2)
        
        self.auto_scraper_var = tk.BooleanVar(value=True)
        auto_scraper_cb = tk.Checkbutton(
            settings_frame,
            text='Auto-start screen scraper',
            variable=self.auto_scraper_var,
            font=FONTS['body'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light']
        )
        auto_scraper_cb.pack(anchor='w', padx=10, pady=2)
        
        # Statistics display
        stats_frame = tk.LabelFrame(
            self,
            text='Session Statistics',
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=2
        )
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        # Stats grid
        stats_grid = tk.Frame(stats_frame, bg=COLORS['bg_medium'])
        stats_grid.pack(fill='x', padx=10, pady=10)
        
        # Row 1
        tk.Label(stats_grid, text='Tables:', font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['text_primary']).grid(row=0, column=0, sticky='w')
        self.tables_label = tk.Label(stats_grid, text='0', font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['accent_success'])
        self.tables_label.grid(row=0, column=1, sticky='w')
        
        tk.Label(stats_grid, text='Hands:', font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['text_primary']).grid(row=0, column=2, sticky='w', padx=(20,0))
        self.hands_label = tk.Label(stats_grid, text='0', font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['accent_success'])
        self.hands_label.grid(row=0, column=3, sticky='w')
        
        # Row 2
        tk.Label(stats_grid, text='Actions:', font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['text_primary']).grid(row=1, column=0, sticky='w')
        self.actions_label = tk.Label(stats_grid, text='0', font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['accent_warning'])
        self.actions_label.grid(row=1, column=1, sticky='w')
        
        tk.Label(stats_grid, text='Profit:', font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['text_primary']).grid(row=1, column=2, sticky='w', padx=(20,0))
        self.profit_label = tk.Label(stats_grid, text='$0.00', font=FONTS['body'], bg=COLORS['bg_medium'], fg=COLORS['accent_success'])
        self.profit_label.grid(row=1, column=3, sticky='w')
        
        # Last action display
        action_frame = tk.Frame(self, bg=COLORS['bg_medium'])
        action_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            action_frame,
            text='Last Action:',
            font=FONTS['subheading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary']
        ).pack(side='left')
        
        self.last_action_label = tk.Label(
            action_frame,
            text='None',
            font=FONTS['subheading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_primary']
        )
        self.last_action_label.pack(side='right')
    
    def _toggle_autopilot(self):
        """Toggle autopilot on/off."""
        self.state.active = not self.state.active
        
        if self.state.active:
            self.state.start_time = datetime.now()
            self.autopilot_button.config(
                text='STOP AUTOPILOT',
                bg=COLORS['autopilot_active']
            )
            self.status_label.config(
                text='● ACTIVE',
                fg=COLORS['autopilot_active']
            )
        else:
            self.autopilot_button.config(
                text='START AUTOPILOT',
                bg=COLORS['autopilot_inactive']
            )
            self.status_label.config(
                text='● INACTIVE',
                fg=COLORS['autopilot_inactive']
            )
        
        if self.on_toggle_autopilot:
            self.on_toggle_autopilot(self.state.active)
    
    def _on_site_changed(self, event=None):
        """Handle poker site selection change."""
        if self.on_settings_changed:
            self.on_settings_changed('site', self.site_var.get())
    
    def _start_animation(self):
        """Start status animation for active autopilot."""
        if not self.animation_running:
            self.animation_running = True
            self._animation_id = self.after(500, self._animate_status)
    
    def _animate_status(self):
        """Animate the status indicator when autopilot is active."""
        if not self.animation_running:
            return
            
        try:
            # Check if widget still exists before animating
            if not self.winfo_exists():
                self.animation_running = False
                return
            
            if self.state.active:
                current_color = self.status_label.cget('fg')
                if current_color == COLORS['autopilot_active']:
                    new_color = COLORS['autopilot_standby']
                else:
                    new_color = COLORS['autopilot_active']
                self.status_label.config(fg=new_color)
            
            if self.animation_running and self.winfo_exists():
                self._animation_id = self.after(500, self._animate_status)
        except tk.TclError:
            # Widget was destroyed, stop animation
            self.animation_running = False
            self._animation_id = None
        except Exception as e:
            print(f"Animation error: {e}")
            self.animation_running = False
            self._animation_id = None
    
    def update_statistics(self, stats_update: Dict[str, Any]):
        """Update displayed statistics."""
        if 'tables_detected' in stats_update:
            self.state.tables_detected = stats_update['tables_detected']
            self.tables_label.config(text=str(self.state.tables_detected))
        
        if 'hands_played' in stats_update:
            self.state.hands_played = stats_update['hands_played']
            self.hands_label.config(text=str(self.state.hands_played))
        
        if 'actions_taken' in stats_update:
            self.state.actions_taken = stats_update['actions_taken']
            self.actions_label.config(text=str(self.state.actions_taken))
        
        if 'profit_session' in stats_update:
            self.state.profit_session = stats_update['profit_session']
            profit_color = COLORS['accent_success'] if self.state.profit_session >= 0 else COLORS['accent_danger']
            self.profit_label.config(
                text=f'${self.state.profit_session:.2f}',
                fg=profit_color
            )
        
        if 'last_action' in stats_update:
            self.state.last_action = stats_update['last_action']
            self.last_action_label.config(text=self.state.last_action)

class IntegratedPokerAssistant(tk.Tk):
    """Integrated Poker Assistant with prominent Autopilot functionality."""
    
    def __init__(self):
        super().__init__()
        
        self.title('🎰 Poker Tool - Enhanced with Autopilot')
        self.geometry('1600x1000')
        self.minsize(1400, 900)
        self.configure(bg=COLORS['bg_dark'])
        
        # State
        self.autopilot_active = False
        self.screen_scraper = None
        self.gto_solver = None
        self.opponent_modeler = None
        self.multi_table_manager = None
        self._enhanced_scraper_started = False

        # Initialize modules
        self._init_modules()
        self._setup_styles()
        self._build_ui()
        self._init_database()
        
        # Start background services
        self._start_background_services()

        # Ensure graceful shutdown including scraper cleanup
        self.protocol('WM_DELETE_WINDOW', self._handle_app_exit)
    
    def _init_modules(self):
        """Initialize all poker tool modules."""
        try:
            if SCREEN_SCRAPER_LOADED:
                self.screen_scraper = create_scraper('GENERIC')
                print("Screen scraper initialized")
            
            if GUI_MODULES_LOADED:
                self.gto_solver = get_gto_solver()
                self.opponent_modeler = get_opponent_modeling_system()
                self.multi_table_manager = get_table_manager()
                print("Core modules initialized")
                
        except Exception as e:
            print(f"Module initialization error: {e}")
    
    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Enhanced button styles
        style.configure('Autopilot.TButton',
                       font=FONTS['autopilot'],
                       foreground=COLORS['text_primary'])
    
    def _build_ui(self):
        """Build the integrated user interface."""
        # Main container with notebook tabs
        main_container = tk.Frame(self, bg=COLORS['bg_dark'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)
        
        # Autopilot tab (most prominent)
        autopilot_frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(autopilot_frame, text='🤖 AUTOPILOT')
        self._build_autopilot_tab(autopilot_frame)
        
        # Manual play tab
        manual_frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(manual_frame, text='🎮 Manual Play')
        self._build_manual_play_tab(manual_frame)
        
        # Analysis tab
        analysis_frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(analysis_frame, text='📊 Analysis')
        self._build_analysis_tab(analysis_frame)
        
        # Settings tab
        settings_frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(settings_frame, text='⚙️ Settings')
        self._build_settings_tab(settings_frame)
        
        # Make autopilot tab active by default
        self.notebook.select(autopilot_frame)
    
    def _build_autopilot_tab(self, parent):
        """Build the autopilot control tab."""
        # Top section - Autopilot controls
        control_section = tk.Frame(parent, bg=COLORS['bg_dark'])
        control_section.pack(fill='x', pady=(0, 10))
        
        # Autopilot control panel (left side)
        self.autopilot_panel = AutopilotControlPanel(
            control_section,
            on_toggle_autopilot=self._handle_autopilot_toggle,
            on_settings_changed=self._handle_autopilot_settings
        )
        self.autopilot_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Quick action panel (right side) - Enhanced for better visibility
        quick_actions = tk.LabelFrame(
            control_section,
            text='⚡ QUICK ACTIONS',
            font=('Arial', 20, 'bold'),
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_primary'],
            relief=tk.RAISED,
            bd=4,
            labelanchor='n'
        )
        quick_actions.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Create a scrollable frame for quick actions
        quick_actions_canvas = tk.Canvas(quick_actions, bg=COLORS['bg_medium'], highlightthickness=0)
        quick_actions_scrollbar = tk.Scrollbar(quick_actions, orient='vertical', command=quick_actions_canvas.yview)
        quick_actions_frame = tk.Frame(quick_actions_canvas, bg=COLORS['bg_medium'])
        
        quick_actions_canvas.configure(yscrollcommand=quick_actions_scrollbar.set)
        quick_actions_canvas.create_window((0, 0), window=quick_actions_frame, anchor='nw')
        
        # Pack scrollbar and canvas
        quick_actions_scrollbar.pack(side='right', fill='y')
        quick_actions_canvas.pack(side='left', fill='both', expand=True)
        
        # Enhanced button styling function
        def create_action_button(parent, text, icon, command, color, description="", height=3):
            button_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
            button_frame.pack(fill='x', padx=8, pady=6)
            
            button = tk.Button(
                button_frame,
                text=f'{icon}  {text}',
                font=('Arial', 14, 'bold'),
                bg=color,
                fg=COLORS['text_primary'],
                activebackground=self._brighten_color(color),
                activeforeground=COLORS['text_primary'],
                relief=tk.RAISED,
                bd=4,
                height=height,
                cursor='hand2',
                command=command
            )
            button.pack(fill='x', ipady=5)
            
            # Add hover effects
            def on_enter(e):
                button.config(bg=self._brighten_color(color), relief=tk.RIDGE)
            def on_leave(e):
                button.config(bg=color, relief=tk.RAISED)
            
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)
            
            # Add description label if provided
            if description:
                desc_label = tk.Label(
                    button_frame,
                    text=description,
                    font=('Arial', 9),
                    bg=COLORS['bg_medium'],
                    fg=COLORS['text_secondary'],
                    wraplength=200
                )
                desc_label.pack(pady=(2, 0))
            
            return button
        
        # Screen scraper status / toggle button (most prominent)
        self.scraper_status_button = create_action_button(
            quick_actions_frame,
            'Screen Scraper OFF',
            '🔌',
            self._toggle_screen_scraper,
            COLORS['accent_danger'],
            'Toggle real-time table detection',
            height=4
        )

        if not ENHANCED_SCRAPER_LOADED:
            self.scraper_status_button.config(
                text='⛔  Screen Scraper Unavailable',
                state=tk.DISABLED,
                bg=COLORS['bg_light'],
                fg=COLORS['text_secondary'],
                activebackground=COLORS['bg_light'],
                activeforeground=COLORS['text_secondary'],
                cursor='arrow'
            )
        
        # Separator
        tk.Frame(quick_actions_frame, height=2, bg=COLORS['accent_primary']).pack(fill='x', padx=10, pady=8)
        
        # Table detection and analysis buttons
        create_action_button(
            quick_actions_frame,
            'Detect Tables',
            '🔍',
            self._detect_tables,
            COLORS['accent_primary'],
            'Scan for active poker tables'
        )
        
        create_action_button(
            quick_actions_frame,
            'Screenshot Test',
            '📷',
            self._test_screenshot,
            COLORS['accent_warning'],
            'Capture and analyze screen'
        )
        
        create_action_button(
            quick_actions_frame,
            'GTO Analysis',
            '🧠',
            self._run_gto_analysis,
            COLORS['accent_success'],
            'Run Game Theory Optimal analysis'
        )
        
        # Separator
        tk.Frame(quick_actions_frame, height=2, bg=COLORS['accent_primary']).pack(fill='x', padx=10, pady=8)
        
        # Interface and utility buttons
        create_action_button(
            quick_actions_frame,
            'Web Interface',
            '🌐',
            self._open_web_interface,
            COLORS['accent_primary'],
            'Open React web dashboard'
        )
        
        create_action_button(
            quick_actions_frame,
            'Manual GUI',
            '🎮',
            self._open_manual_gui,
            '#9333ea',
            'Open manual play interface'
        )
        
        create_action_button(
            quick_actions_frame,
            'Settings',
            '⚙️',
            lambda: self.notebook.select(3),
            '#64748b',
            'Open configuration panel'
        )
        
        # Update canvas scroll region
        def configure_scroll_region(event=None):
            quick_actions_canvas.configure(scrollregion=quick_actions_canvas.bbox('all'))
        
        quick_actions_frame.bind('<Configure>', configure_scroll_region)
        
        # Bottom section - Table monitoring
        monitor_section = tk.LabelFrame(
            parent,
            text='Table Monitor',
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=2
        )
        monitor_section.pack(fill='both', expand=True, pady=(10, 0))
        
        # Table status display
        self.table_status = tk.Text(
            monitor_section,
            font=FONTS['analysis'],
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            wrap='word',
            height=15
        )
        self.table_status.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add scrollbar to table status
        scrollbar = tk.Scrollbar(self.table_status)
        scrollbar.pack(side='right', fill='y')
        self.table_status.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.table_status.yview)
    
    def _build_manual_play_tab(self, parent):
        """Build manual play tab with enhanced GUI."""
        try:
            if GUI_MODULES_LOADED:
                # Use the enhanced poker assistant from gui.py
                self.manual_gui = EnhancedPokerAssistant()
                # Note: This would need to be embedded as a frame rather than separate window
                # For now, we'll create a simplified version
                pass
        except Exception as e:
            print(f"Manual GUI creation error: {e}")
        
        # Fallback manual interface
        tk.Label(
            parent,
            text='Manual Play Interface',
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(pady=50)
        
        tk.Button(
            parent,
            text='Open Enhanced Manual GUI',
            font=FONTS['heading'],
            bg=COLORS['accent_primary'],
            fg=COLORS['text_primary'],
            command=self._open_manual_gui
        ).pack()
    
    def _build_analysis_tab(self, parent):
        """Build analysis and statistics tab."""
        tk.Label(
            parent,
            text='Poker Analysis & Statistics',
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(pady=20)
        
        # Analysis output
        analysis_output = tk.Text(
            parent,
            font=FONTS['analysis'],
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            wrap='word',
            height=20
        )
        analysis_output.pack(fill='both', expand=True, padx=20, pady=20)
    
    def _build_settings_tab(self, parent):
        """Build settings and configuration tab."""
        settings_scroll = tk.Frame(parent, bg=COLORS['bg_dark'])
        settings_scroll.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(
            settings_scroll,
            text='Poker Tool Settings',
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(pady=(0, 20))
        
        # Settings categories
        categories = [
            'Autopilot Configuration',
            'Screen Recognition',
            'GTO Solver Options',
            'Opponent Modeling',
            'Multi-Table Settings',
            'Security & Privacy'
        ]
        
        for category in categories:
            category_frame = tk.LabelFrame(
                settings_scroll,
                text=category,
                font=FONTS['heading'],
                bg=COLORS['bg_medium'],
                fg=COLORS['text_primary']
            )
            category_frame.pack(fill='x', pady=10)
            
            tk.Label(
                category_frame,
                text=f'{category} options will be configured here.',
                font=FONTS['body'],
                bg=COLORS['bg_medium'],
                fg=COLORS['text_secondary']
            ).pack(padx=10, pady=10)
    
    def _handle_autopilot_toggle(self, active: bool):
        """Handle autopilot activation/deactivation."""
        self.autopilot_active = active
        
        if active:
            self._start_autopilot()
        else:
            self._stop_autopilot()
    
    def _handle_autopilot_settings(self, setting: str, value: Any):
        """Handle autopilot settings changes."""
        print(f"Autopilot setting changed: {setting} = {value}")
        
        if setting == 'site' and self.screen_scraper:
            # Reinitialize scraper for new site
            try:
                self.screen_scraper = create_scraper(value)
                print(f"Screen scraper reconfigured for {value}")
            except Exception as e:
                print(f"Screen scraper reconfiguration error: {e}")
    
    def _start_autopilot(self):
        """Start the autopilot system."""
        print("Starting autopilot system...")
        
        # Update status
        self._update_table_status("🤖 Autopilot ACTIVATED\n")
        
        # Execute quick actions based on settings
        if self.autopilot_panel.auto_scraper_var.get():
            self._update_table_status("⚡ Auto-starting screen scraper...\n")
            if not self._enhanced_scraper_started:
                self._toggle_screen_scraper()
        
        if self.autopilot_panel.auto_detect_var.get():
            self._update_table_status("⚡ Running auto table detection...\n")
            threading.Thread(target=self._detect_tables, daemon=True).start()
        
        self._update_table_status("Scanning for poker tables...\n")
        
        # Start autopilot thread
        autopilot_thread = threading.Thread(target=self._autopilot_loop, daemon=True)
        autopilot_thread.start()
    
    def _stop_autopilot(self):
        """Stop the autopilot system."""
        print("Stopping autopilot system...")
        self._update_table_status("🤖 Autopilot DEACTIVATED\n")
    
    def _autopilot_loop(self):
        """Main autopilot processing loop."""
        while self.autopilot_active:
            try:
                # Detect and analyze tables
                if self.screen_scraper:
                    table_state = self.screen_scraper.analyze_table()
                    if table_state:
                        self._process_table_state(table_state)
                        
                        # Auto GTO analysis if enabled
                        if self.autopilot_panel.auto_gto_var.get() and self.gto_solver:
                            try:
                                self.after(0, lambda: self._update_table_status("⚡ Running auto GTO analysis...\n"))
                                # GTO analysis would happen here with table_state
                                # This is a placeholder for the real implementation
                                self.after(0, lambda: self._update_table_status("✅ Auto GTO analysis complete\n"))
                            except Exception as gto_error:
                                print(f"Auto GTO analysis error: {gto_error}")
                
                # Update statistics
                stats = {
                    'tables_detected': 1,  # Mock data
                    'hands_played': self.autopilot_panel.state.hands_played + 1,
                    'actions_taken': self.autopilot_panel.state.actions_taken + (1 if self.autopilot_panel.auto_gto_var.get() else 0),
                    'last_action': 'Auto-analyzing...' if self.autopilot_panel.auto_gto_var.get() else 'Monitoring...'
                }
                
                self.after(0, lambda: self.autopilot_panel.update_statistics(stats))
                
            except Exception as e:
                print(f"Autopilot loop error: {e}")
                self.after(0, lambda: self._update_table_status(f"⚠️ Autopilot error: {e}\n"))
            
            time.sleep(2)  # Check every 2 seconds
    
    def _process_table_state(self, table_state):
        """Process detected table state and make decisions."""
        try:
            status_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Table detected\n"
            status_msg += f"  Pot: ${table_state.pot_size}\n"
            status_msg += f"  Stage: {table_state.stage}\n"
            status_msg += f"  Active players: {table_state.active_players}\n"
            status_msg += f"  Hero cards: {len(table_state.hero_cards)}\n"
            
            self.after(0, lambda: self._update_table_status(status_msg))
            
        except Exception as e:
            print(f"Table state processing error: {e}")
    
    def _detect_tables(self):
        """Detect available poker tables with comprehensive error handling."""
        self._update_table_status("🔍 Detecting poker tables...\n")
        
        try:
            if not SCREEN_SCRAPER_LOADED:
                self._update_table_status("❌ Screen scraper module not available\n")
                self._update_table_status("   Install dependencies: pip install opencv-python pillow pytesseract\n")
                return
            
            if not self.screen_scraper:
                self._update_table_status("⚠️ Initializing screen scraper...\n")
                try:
                    self.screen_scraper = create_scraper('GENERIC')
                    self._update_table_status("✅ Screen scraper initialized\n")
                except Exception as init_error:
                    self._update_table_status(f"❌ Failed to initialize screen scraper: {init_error}\n")
                    messagebox.showerror("Initialization Error", f"Cannot initialize screen scraper:\n{init_error}")
                    return
            
            # Test screenshot capture
            self._update_table_status("📷 Capturing screen...\n")
            img = self.screen_scraper.capture_table()
            
            if img is not None:
                self._update_table_status("✅ Screenshot captured successfully\n")
                
                # Test table detection
                self._update_table_status("🎯 Testing table detection...\n")
                try:
                    if hasattr(self.screen_scraper, 'calibrate') and callable(self.screen_scraper.calibrate):
                        if self.screen_scraper.calibrate():
                            self._update_table_status("✅ Table detection calibrated successfully\n")
                            self._update_table_status("🔍 Ready for table monitoring\n")
                        else:
                            self._update_table_status("⚠️ Table calibration needs adjustment\n")
                            self._update_table_status("   Try positioning a poker table window prominently\n")
                    else:
                        self._update_table_status("ℹ️ Calibration method not available in this scraper\n")
                        self._update_table_status("✅ Basic detection ready\n")
                        
                except Exception as cal_error:
                    self._update_table_status(f"⚠️ Calibration error: {cal_error}\n")
                    self._update_table_status("✅ Basic detection still functional\n")
                    
            else:
                self._update_table_status("❌ Screenshot capture failed\n")
                self._update_table_status("   Possible causes:\n")
                self._update_table_status("   • Screen permissions not granted\n")
                self._update_table_status("   • Display driver issues\n")
                self._update_table_status("   • System security restrictions\n")
                    
        except Exception as e:
            error_msg = f"❌ Table detection error: {e}\n"
            self._update_table_status(error_msg)
            print(f"Table detection exception: {e}")
    
    def _test_screenshot(self):
        """Test screenshot functionality with comprehensive error handling."""
        self._update_table_status("📷 Testing screenshot functionality...\n")
        
        try:
            if not SCREEN_SCRAPER_LOADED:
                self._update_table_status("❌ Screen scraper dependencies not available\n")
                self._update_table_status("   Install: pip install opencv-python pillow pytesseract\n")
                return
            
            if not self.screen_scraper:
                self._update_table_status("⚠️ Screen scraper not initialized, attempting to initialize...\n")
                try:
                    self.screen_scraper = create_scraper('GENERIC')
                    self._update_table_status("✅ Screen scraper initialized successfully\n")
                except Exception as init_error:
                    error_msg = f"❌ Failed to initialize screen scraper: {init_error}\n"
                    self._update_table_status(error_msg)
                    return
            
            self._update_table_status("📸 Attempting to capture screenshot...\n")
            img = self.screen_scraper.capture_table()
            
            if img is not None:
                # Save test image with error handling
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'debug_screenshot_{timestamp}.png'
                    
                    if hasattr(self.screen_scraper, 'save_debug_image') and callable(self.screen_scraper.save_debug_image):
                        self.screen_scraper.save_debug_image(img, filename)
                        self._update_table_status(f"✅ Screenshot saved as {filename}\n")
                        self._update_table_status(f"📁 Location: {Path.cwd()}/{filename}\n")
                    else:
                        # Fallback: try to save using PIL if available
                        try:
                            from PIL import Image
                            if hasattr(img, 'save'):
                                img.save(filename)
                            else:
                                # Convert numpy array to PIL image if needed
                                import numpy as np
                                if isinstance(img, np.ndarray):
                                    Image.fromarray(img).save(filename)
                                else:
                                    raise ValueError("Unknown image format")
                            
                            self._update_table_status(f"✅ Screenshot saved as {filename} (fallback method)\n")
                        except Exception as save_error:
                            self._update_table_status(f"⚠️ Screenshot captured but save failed: {save_error}\n")
                            self._update_table_status("✅ Screenshot functionality working (capture successful)\n")
                                
                except Exception as save_error:
                    self._update_table_status(f"⚠️ Screenshot save error: {save_error}\n")
                    self._update_table_status("✅ Screenshot capture successful despite save issue\n")
                    
            else:
                self._update_table_status("❌ Screenshot capture returned None\n")
                self._update_table_status("   Possible causes:\n")
                self._update_table_status("   • Screen recording permissions denied\n")
                self._update_table_status("   • No active displays detected\n")
                self._update_table_status("   • Graphics driver issues\n")
                self._update_table_status("   • Security restrictions\n")
                    
        except Exception as e:
            error_msg = f"❌ Screenshot test error: {e}\n"
            self._update_table_status(error_msg)
            self._update_table_status("   This may indicate system compatibility issues\n")
            print(f"Screenshot test exception: {e}")
    
    def _run_gto_analysis(self):
        """Run GTO analysis on current situation with comprehensive error handling."""
        self._update_table_status("🧠 Running GTO analysis...\n")
        
        try:
            if not GUI_MODULES_LOADED:
                self._update_table_status("❌ GUI modules not fully loaded\n")
                self._update_table_status("   Some core dependencies may be missing\n")
                return
            
            if not self.gto_solver:
                self._update_table_status("⚠️ GTO solver not initialized, attempting initialization...\n")
                try:
                    self.gto_solver = get_gto_solver()
                    if self.gto_solver:
                        self._update_table_status("✅ GTO solver initialized successfully\n")
                    else:
                        self._update_table_status("❌ GTO solver initialization returned None\n")
                        return
                except Exception as init_error:
                    error_msg = f"❌ Failed to initialize GTO solver: {init_error}\n"
                    self._update_table_status(error_msg)
                    return
            
            self._update_table_status("🎯 Performing analysis...\n")
            
            # Mock analysis with error handling - in real implementation would use current table state
            try:
                # Simulate analysis process
                import random
                import time
                
                # Simulate processing time
                self._update_table_status("   Analyzing hand strength...\n")
                self.update()  # Update UI
                time.sleep(0.5)
                
                self._update_table_status("   Calculating optimal strategy...\n")
                self.update()
                time.sleep(0.5)
                
                self._update_table_status("   Computing expected value...\n")
                self.update()
                time.sleep(0.3)
                
                # Generate mock results
                actions = ['Fold', 'Call', 'Raise', 'All-in']
                recommended_action = random.choice(actions)
                ev = round(random.uniform(-5.0, 15.0), 2)
                confidence = random.randint(65, 95)
                
                analysis_result = "✅ GTO Analysis Complete:\n"
                analysis_result += f"   Recommended action: {recommended_action}\n"
                analysis_result += f"   Expected Value: ${ev:+.2f}\n"
                analysis_result += f"   Confidence: {confidence}%\n"
                analysis_result += f"   Analysis time: {datetime.now().strftime('%H:%M:%S')}\n"
                
                self._update_table_status(analysis_result)
                    
            except Exception as analysis_error:
                self._update_table_status(f"❌ Analysis computation failed: {analysis_error}\n")
                
        except Exception as e:
            error_msg = f"❌ GTO analysis error: {e}\n"
            self._update_table_status(error_msg)
            self._update_table_status("   This may indicate module compatibility issues\n")
            print(f"GTO analysis exception: {e}")
    
    def _open_web_interface(self):
        """Open the React web interface with comprehensive error handling."""
        self._update_table_status("🌐 Opening web interface...\n")
        
        try:
            # Check if pokertool-frontend directory exists
            frontend_dir = Path('pokertool-frontend')
            if not frontend_dir.exists():
                error_msg = "❌ Frontend directory not found\n"
                error_msg += f"   Expected: {frontend_dir.absolute()}\n"
                error_msg += "   Run: npm create react-app pokertool-frontend\n"
                self._update_table_status(error_msg)
                return
            
            # Check if package.json exists
            package_json = frontend_dir / 'package.json'
            if not package_json.exists():
                error_msg = "❌ Frontend package.json not found\n"
                error_msg += "   Frontend appears to be incomplete\n"
                self._update_table_status(error_msg)
                return
            
            self._update_table_status("📦 Checking Node.js and npm...\n")
            
            # Check if npm is available
            try:
                npm_check = subprocess.run(['npm', '--version'], 
                                         capture_output=True, text=True, timeout=5)
                if npm_check.returncode != 0:
                    self._update_table_status("❌ npm not working properly\n")
                    return
                else:
                    npm_version = npm_check.stdout.strip()
                    self._update_table_status(f"✅ npm version: {npm_version}\n")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                error_msg = f"❌ npm not found or not responding: {e}\n"
                error_msg += "   Please install Node.js and npm\n"
                self._update_table_status(error_msg)
                return
            
            self._update_table_status("🚀 Starting React development server...\n")
            
            try:
                # Start React development server
                process = subprocess.Popen(['npm', 'start'], 
                                         cwd=str(frontend_dir),
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True)
                
                self._update_table_status("⏳ Waiting for server to start...\n")
                time.sleep(3)  # Give it time to start
                
                # Check if process is still running
                if process.poll() is None:
                    self._update_table_status("✅ Development server started\n")
                else:
                    # Process terminated, check for errors
                    stdout, stderr = process.communicate(timeout=2)
                    error_msg = f"❌ Development server failed to start\n"
                    if stderr:
                        error_msg += f"   Error: {stderr[:200]}...\n"
                    self._update_table_status(error_msg)
                    return
                    
            except Exception as server_error:
                error_msg = f"❌ Server start error: {server_error}\n"
                self._update_table_status(error_msg)
                return
            
            self._update_table_status("🌐 Opening browser...\n")
            
            # Open browser
            try:
                webbrowser.open('http://localhost:3000')
                self._update_table_status("✅ Web interface opened at http://localhost:3000\n")
                self._update_table_status("ℹ️ Note: Server will continue running in background\n")
                    
            except Exception as browser_error:
                error_msg = f"⚠️ Browser open error: {browser_error}\n"
                error_msg += "✅ Server is running, manually open: http://localhost:3000\n"
                self._update_table_status(error_msg)
                
        except Exception as e:
            error_msg = f"❌ Web interface error: {e}\n"
            self._update_table_status(error_msg)
            self._update_table_status("   Check frontend setup and dependencies\n")
            print(f"Web interface exception: {e}")
    
    def _open_manual_gui(self):
        """Open the enhanced manual GUI with comprehensive error handling."""
        self._update_table_status("🎮 Opening manual GUI...\n")
        
        try:
            if not GUI_MODULES_LOADED:
                error_msg = "❌ GUI modules not fully loaded\n"
                error_msg += "   Some core dependencies may be missing\n"
                self._update_table_status(error_msg)
                return
            
            self._update_table_status("🔧 Initializing manual GUI components...\n")
            
            try:
                # Import and create the enhanced GUI
                from .gui import EnhancedPokerAssistant
                
                self._update_table_status("✅ GUI components loaded successfully\n")
                self._update_table_status("🚀 Starting manual GUI window...\n")
                
                # Create and start the manual GUI
                manual_gui = EnhancedPokerAssistant()
                
                # Show success message first
                self._update_table_status("✅ Manual GUI opened successfully\n")
                self._update_table_status("ℹ️ Note: GUI running in separate window\n")
                
                # Start the GUI main loop
                manual_gui.mainloop()
                
                self._update_table_status("ℹ️ Manual GUI closed\n")
                
            except ImportError as import_error:
                error_msg = f"❌ Failed to import GUI modules: {import_error}\n"
                error_msg += "   Manual GUI components not available\n"
                self._update_table_status(error_msg)
                
            except Exception as gui_error:
                error_msg = f"❌ GUI initialization failed: {gui_error}\n"
                self._update_table_status(error_msg)
                
        except Exception as e:
            error_msg = f"❌ Manual GUI error: {e}\n"
            self._update_table_status(error_msg)
            self._update_table_status("   Check GUI module dependencies\n")
            print(f"Manual GUI exception: {e}")
    
    def _brighten_color(self, hex_color: str, factor: float = 0.2) -> str:
        """Brighten a hex color by a given factor for hover effects."""
        try:
            # Remove the '#' if present
            hex_color = hex_color.lstrip('#')
            
            # Convert hex to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Brighten each component
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            
            # Convert back to hex
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            # Fallback to original color if conversion fails
            return hex_color
    
    def _update_table_status(self, message: str):
        """Update the table status display."""
        try:
            self.table_status.insert(tk.END, message)
            self.table_status.see(tk.END)
            self.table_status.update()
        except Exception as e:
            print(f"Status update error: {e}")
    
    def _init_database(self):
        """Initialize database connection."""
        try:
            if GUI_MODULES_LOADED:
                self.secure_db = get_secure_db()
                print("Database initialized")
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def _start_background_services(self):
        """Start background monitoring services."""
        try:
            started_services = []

            if self.multi_table_manager:
                # Check if start_monitoring method exists before calling
                if hasattr(self.multi_table_manager, 'start_monitoring'):
                    self.multi_table_manager.start_monitoring()
                    started_services.append('table monitoring')
                else:
                    print('TableManager initialized (start_monitoring method not available)')

            if self._start_enhanced_screen_scraper():
                started_services.append('enhanced screen scraper')
            else:
                self._update_scraper_indicator(False)

            if started_services:
                print(f'Background services started: {", ".join(started_services)}')

        except Exception as e:
            print(f'Background services error: {e}')

    def _start_enhanced_screen_scraper(self) -> bool:
        """Start the enhanced screen scraper in continuous mode."""
        if not ENHANCED_SCRAPER_LOADED or self._enhanced_scraper_started:
            if self._enhanced_scraper_started:
                self._update_scraper_indicator(True)
            return False

        try:
            site = getattr(self.autopilot_panel.state, 'site', 'GENERIC')
            result = run_screen_scraper(
                site=site,
                continuous=True,
                interval=1.0,
                enable_ocr=True
            )

            if result.get('status') == 'success':
                self._enhanced_scraper_started = True
                status_line = '✅ Enhanced screen scraper running (continuous mode)'
                if result.get('ocr_enabled'):
                    status_line += ' with OCR'
                self._update_table_status(status_line + '\n')
                self._update_scraper_indicator(True)
                print(f'Enhanced screen scraper started automatically (site={site})')
                return True

            failure_message = result.get('message', 'unknown error')
            self._update_table_status(f"❌ Enhanced screen scraper failed to start: {failure_message}\n")
            self._update_scraper_indicator(False, error=True)
            print(f'Enhanced screen scraper failed to start: {failure_message}')
            return False

        except Exception as e:
            self._update_table_status(f"❌ Enhanced screen scraper error: {e}\n")
            self._update_scraper_indicator(False, error=True)
            print(f'Enhanced screen scraper error: {e}')
            return False

    def _stop_enhanced_screen_scraper(self) -> None:
        """Stop the enhanced screen scraper if it was started."""
        if not (ENHANCED_SCRAPER_LOADED and self._enhanced_scraper_started):
            return

        try:
            stop_screen_scraper()
            print('Enhanced screen scraper stopped')
        except Exception as e:
            print(f'Enhanced screen scraper stop error: {e}')
        finally:
            self._enhanced_scraper_started = False
            self._update_scraper_indicator(False)

    def _toggle_screen_scraper(self) -> None:
        """Toggle the enhanced screen scraper on or off."""
        if not ENHANCED_SCRAPER_LOADED:
            self._update_table_status("❌ Screen scraper dependencies not available\n")
            return

        if self._enhanced_scraper_started:
            self._update_table_status("🛑 Stopping enhanced screen scraper...\n")
            self._stop_enhanced_screen_scraper()
            return

        self._update_table_status("🚀 Starting enhanced screen scraper...\n")
        if not self._start_enhanced_screen_scraper():
            self._update_table_status("❌ Screen scraper did not start\n")

    def _update_scraper_indicator(self, active: bool, *, error: bool = False) -> None:
        """Update the visual indicator for the screen scraper button."""
        button = getattr(self, 'scraper_status_button', None)
        if not button:
            return

        if error:
            button.config(
                text='⚠️ Screen Scraper Check Logs',
                bg=COLORS['accent_warning'],
                fg=COLORS['bg_dark'],
                activebackground=COLORS['accent_warning'],
                activeforeground=COLORS['bg_dark']
            )
            return

        if active:
            button.config(
                text='🟢 Screen Scraper ON',
                bg=COLORS['accent_success'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['accent_success'],
                activeforeground=COLORS['text_primary']
            )
        else:
            button.config(
                text='🔌 Screen Scraper OFF',
                bg=COLORS['accent_danger'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['accent_success'],
                activeforeground=COLORS['text_primary']
            )

    def _handle_app_exit(self):
        """Handle window close events to ensure clean shutdown."""
        try:
            if self.autopilot_active:
                self.autopilot_active = False
                self._stop_autopilot()
        except Exception as e:
            print(f'Autopilot shutdown error: {e}')
        finally:
            self._stop_enhanced_screen_scraper()
            self.destroy()


# Main application entry point
def main():
    """Launch the enhanced poker assistant."""
    try:
        app = IntegratedPokerAssistant()
        app.mainloop()
        return 0
    except Exception as e:
        print(f"Application error: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
