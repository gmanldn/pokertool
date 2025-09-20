"""
Enhanced Poker Assistant GUI with Autopilot
Integrates all modules with prominent screen scraping autopilot functionality.
"""

from __future__ import annotations

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
    from .gto_solver import GTOSolver
    from .ml_opponent_modeling import OpponentModeler
    from .multi_table_support import MultiTableManager
    from .error_handling import sanitize_input, log, run_safely
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
        
        self._build_ui()
        self._start_animation()
    
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
            self._animate_status()
    
    def _animate_status(self):
        """Animate the status indicator when autopilot is active."""
        if self.state.active:
            current_color = self.status_label.cget('fg')
            if current_color == COLORS['autopilot_active']:
                new_color = COLORS['autopilot_standby']
            else:
                new_color = COLORS['autopilot_active']
            self.status_label.config(fg=new_color)
        
        if self.animation_running:
            self.after(500, self._animate_status)
    
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
        
        # Initialize modules
        self._init_modules()
        self._setup_styles()
        self._build_ui()
        self._init_database()
        
        # Start background services
        self._start_background_services()
    
    def _init_modules(self):
        """Initialize all poker tool modules."""
        try:
            if SCREEN_SCRAPER_LOADED:
                self.screen_scraper = create_scraper('GENERIC')
                log("Screen scraper initialized")
            
            if GUI_MODULES_LOADED:
                self.gto_solver = GTOSolver()
                self.opponent_modeler = OpponentModeler()
                self.multi_table_manager = MultiTableManager()
                log("Core modules initialized")
                
        except Exception as e:
            log(f"Module initialization error: {e}")
    
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
        
        # Quick action panel (right side)
        quick_actions = tk.LabelFrame(
            control_section,
            text='Quick Actions',
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=2
        )
        quick_actions.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Quick action buttons
        tk.Button(
            quick_actions,
            text='🔍 Detect Tables',
            font=FONTS['subheading'],
            bg=COLORS['accent_primary'],
            fg=COLORS['text_primary'],
            command=self._detect_tables
        ).pack(fill='x', padx=10, pady=5)
        
        tk.Button(
            quick_actions,
            text='📷 Screenshot Test',
            font=FONTS['subheading'],
            bg=COLORS['accent_warning'],
            fg=COLORS['text_primary'],
            command=self._test_screenshot
        ).pack(fill='x', padx=10, pady=5)
        
        tk.Button(
            quick_actions,
            text='🧠 GTO Analysis',
            font=FONTS['subheading'],
            bg=COLORS['accent_success'],
            fg=COLORS['text_primary'],
            command=self._run_gto_analysis
        ).pack(fill='x', padx=10, pady=5)
        
        tk.Button(
            quick_actions,
            text='🌐 Open Web Interface',
            font=FONTS['subheading'],
            bg=COLORS['accent_primary'],
            fg=COLORS['text_primary'],
            command=self._open_web_interface
        ).pack(fill='x', padx=10, pady=5)
        
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
            log(f"Manual GUI creation error: {e}")
        
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
        log(f"Autopilot setting changed: {setting} = {value}")
        
        if setting == 'site' and self.screen_scraper:
            # Reinitialize scraper for new site
            try:
                self.screen_scraper = create_scraper(value)
                log(f"Screen scraper reconfigured for {value}")
            except Exception as e:
                log(f"Screen scraper reconfiguration error: {e}")
    
    def _start_autopilot(self):
        """Start the autopilot system."""
        log("Starting autopilot system...")
        
        # Update status
        self._update_table_status("🤖 Autopilot ACTIVATED\n")
        self._update_table_status("Scanning for poker tables...\n")
        
        # Start autopilot thread
        autopilot_thread = threading.Thread(target=self._autopilot_loop, daemon=True)
        autopilot_thread.start()
    
    def _stop_autopilot(self):
        """Stop the autopilot system."""
        log("Stopping autopilot system...")
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
                
                # Update statistics
                stats = {
                    'tables_detected': 1,  # Mock data
                    'hands_played': self.autopilot_panel.state.hands_played + 1,
                    'actions_taken': self.autopilot_panel.state.actions_taken,
                    'last_action': 'Analyzing...'
                }
                
                self.after(0, lambda: self.autopilot_panel.update_statistics(stats))
                
            except Exception as e:
                log(f"Autopilot loop error: {e}")
            
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
            log(f"Table state processing error: {e}")
    
    def _detect_tables(self):
        """Detect available poker tables."""
        self._update_table_status("🔍 Detecting poker tables...\n")
        
        if not SCREEN_SCRAPER_LOADED:
            self._update_table_status("❌ Screen scraper not available\n")
            return
        
        try:
            if self.screen_scraper:
                # Test screenshot
                img = self.screen_scraper.capture_table()
                if img is not None:
                    self._update_table_status("✅ Screenshot captured successfully\n")
                    
                    # Test calibration
                    if self.screen_scraper.calibrate():
                        self._update_table_status("✅ Table detection calibrated\n")
                    else:
                        self._update_table_status("⚠️ Table calibration needs adjustment\n")
                else:
                    self._update_table_status("❌ Screenshot capture failed\n")
                    
        except Exception as e:
            self._update_table_status(f"❌ Detection error: {e}\n")
    
    def _test_screenshot(self):
        """Test screenshot functionality."""
        self._update_table_status("📷 Testing screenshot...\n")
        
        if not SCREEN_SCRAPER_LOADED:
            self._update_table_status("❌ Screen scraper dependencies not available\n")
            return
        
        try:
            if self.screen_scraper:
                img = self.screen_scraper.capture_table()
                if img is not None:
                    # Save test image
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f'debug_screenshot_{timestamp}.png'
                    self.screen_scraper.save_debug_image(img, filename)
                    self._update_table_status(f"✅ Screenshot saved as {filename}\n")
                else:
                    self._update_table_status("❌ Screenshot capture failed\n")
            else:
                self._update_table_status("❌ Screen scraper not initialized\n")
        except Exception as e:
            self._update_table_status(f"❌ Screenshot error: {e}\n")
    
    def _run_gto_analysis(self):
        """Run GTO analysis on current situation."""
        self._update_table_status("🧠 Running GTO analysis...\n")
        
        try:
            if self.gto_solver and GUI_MODULES_LOADED:
                # Mock analysis - in real implementation would use current table state
                analysis_result = "GTO Analysis:\n"
                analysis_result += "  Recommended action: Call\n"
                analysis_result += "  EV: +$2.45\n"
                analysis_result += "  Confidence: 85%\n"
                self._update_table_status(analysis_result)
            else:
                self._update_table_status("❌ GTO solver not available\n")
        except Exception as e:
            self._update_table_status(f"❌ GTO analysis error: {e}\n")
    
    def _open_web_interface(self):
        """Open the React web interface."""
        self._update_table_status("🌐 Opening web interface...\n")
        
        try:
            # Start React development server if not running
            subprocess.Popen(['npm', 'start'], cwd='pokertool-frontend')
            time.sleep(3)  # Give it time to start
            
            # Open browser
            webbrowser.open('http://localhost:3000')
            self._update_table_status("✅ Web interface opened at http://localhost:3000\n")
        except Exception as e:
            self._update_table_status(f"❌ Web interface error: {e}\n")
    
    def _open_manual_gui(self):
        """Open the enhanced manual GUI."""
        try:
            if GUI_MODULES_LOADED:
                manual_gui = EnhancedPokerAssistant()
                manual_gui.mainloop()
            else:
                messagebox.showwarning("Manual GUI", "Enhanced GUI modules not loaded")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open manual GUI: {e}")
    
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
                log("Database initialized")
        except Exception as e:
            log(f"Database initialization error: {e}")
    
    def _start_background_services(self):
        """Start background monitoring services."""
        try:
            # Initialize table monitor
            if self.multi_table_manager:
                self.multi_table_manager.start_monitoring()
                log("Background services started")
        except Exception as e:
            log(f"Background services error: {e}")


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
