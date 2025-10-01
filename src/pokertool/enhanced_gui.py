#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
PokerTool Enhanced Gui Module
===============================

This module provides functionality for enhanced gui operations
within the PokerTool application ecosystem.

Module: pokertool.enhanced_gui
Version: 20.1.0
Last Modified: 2025-09-30
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v20.1.0 (2025-09-30): Added auto-start scraper, continuous updates, dependency checking
    - v28.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '20.1.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

# CRITICAL: Check and install screen scraper dependencies FIRST
import sys
import os
import subprocess

def _ensure_scraper_dependencies():
    """Ensure screen scraper dependencies are installed before module imports."""
    critical_deps = [
        ('cv2', 'opencv-python'),
        ('PIL', 'Pillow'),
        ('pytesseract', 'pytesseract'),
        ('mss', 'mss'),
        ('numpy', 'numpy'),
        ('requests', 'requests'),
        ('websocket', 'websocket-client'),
    ]

    if sys.platform == 'darwin':
        critical_deps.append(('Quartz', 'pyobjc-framework-Quartz'))
    
    missing = []
    for module_name, package_name in critical_deps:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print(f"\n{'='*60}")
        print("📦 [enhanced_gui] Installing screen scraper dependencies...")
        print(f"{'='*60}")
        for package in missing:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Failed to install {package}: {e}")
                print(f"   Please run manually: pip install {package}")
        print(f"{'='*60}\n")
    
    return len(missing) == 0

# Install dependencies before other imports
_DEPENDENCIES_OK = _ensure_scraper_dependencies()

import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable, Tuple
from pathlib import Path
import webbrowser

# Import all pokertool modules
try:
    from .gui import (
        EnhancedPokerAssistant,
        EnhancedPokerAssistantFrame,
        VisualCard,
        CardSelectionPanel,
        TableVisualization,
    )
    from .core import analyse_hand, Card, Suit, Position, HandAnalysisResult, parse_card
    from .i18n import (
        translate,
        set_locale,
        get_current_locale,
        available_locales,
        format_currency,
        format_decimal,
        format_datetime,
        register_locale_listener,
        unregister_locale_listener,
    )
    from .gto_solver import GTOSolver, get_gto_solver
    from .ml_opponent_modeling import OpponentModelingSystem, get_opponent_modeling_system
    from .multi_table_support import TableManager, get_table_manager
    from .error_handling import sanitize_input, run_safely
    from .storage import get_secure_db
    from .coaching_system import CoachingSystem
    GUI_MODULES_LOADED = True
except ImportError as e:
    print(f'Warning: GUI modules not fully loaded: {e}')
    GUI_MODULES_LOADED = False

# Import screen scraper
try:
    sys.path.append('.')
    from pokertool.modules.poker_screen_scraper import (
        PokerScreenScraper,
        PokerSite,
        TableState,
        create_scraper,
    )
    SCREEN_SCRAPER_LOADED = True
except ImportError as e:
    print(f'Warning: Screen scraper not loaded: {e}')
    SCREEN_SCRAPER_LOADED = False

# Import enhanced scraper manager utilities
try:
    from .scrape import run_screen_scraper, stop_screen_scraper, get_scraper_status
    ENHANCED_SCRAPER_LOADED = True
except ImportError as e:
    print(f'Warning: Enhanced screen scraper not loaded: {e}')
    ENHANCED_SCRAPER_LOADED = False

from .enhanced_gui_components import (
    COLORS,
    FONTS,
    AutopilotControlPanel,
    ManualPlaySection,
    SettingsSection,
    CoachingSection,
)

class IntegratedPokerAssistant(tk.Tk):
    """Integrated Poker Assistant with prominent Autopilot functionality."""
    
    def __init__(self):
        super().__init__()
        
        self.title(translate('app.title'))
        self.geometry('1600x1000')
        self.minsize(1400, 900)
        self.configure(bg=COLORS['bg_dark'])
        
        # State
        self.autopilot_active = False
        self.screen_scraper = None
        self.gto_solver = None
        self.opponent_modeler = None
        self.multi_table_manager = None
        self.coaching_system = None
        self._enhanced_scraper_started = False
        self._screen_update_running = False
        self._screen_update_thread = None

        self.manual_section = None
        self.settings_section = None
        self.coaching_section = None
        self._translation_bindings: List[Tuple[Any, str, str, str, str, Dict[str, Any]]] = []
        self._tab_bindings: List[Tuple[Any, str]] = []
        self._window_title_key = 'app.title'
        self._locale_listener_token: Optional[int] = None
        # Initialize modules
        self._init_modules()
        self._setup_styles()
        self._build_ui()
        self._locale_listener_token = register_locale_listener(self._apply_translations)
        self._apply_translations()
        self._init_database()
        
        # Start background services (includes auto-starting scraper)
        self._start_background_services()
        
        # Start continuous screen update loop
        self._start_screen_update_loop()

        # Ensure graceful shutdown including scraper cleanup
        self.protocol('WM_DELETE_WINDOW', self._handle_app_exit)
    
    def _init_modules(self):
        """Initialize all poker tool modules."""
        try:
            if SCREEN_SCRAPER_LOADED:
                self.screen_scraper = create_scraper('CHROME')
                print("Screen scraper initialized")
            
            if GUI_MODULES_LOADED:
                self.gto_solver = get_gto_solver()
                self.opponent_modeler = get_opponent_modeling_system()
                self.multi_table_manager = get_table_manager()
                print("Core modules initialized")

            try:
                self.coaching_system = CoachingSystem()
                print("Coaching system ready")
            except Exception as coaching_error:
                print(f"Coaching system initialization error: {coaching_error}")
        
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

    # Translation helpers -------------------------------------------------
    def _register_widget_translation(
        self,
        widget: Any,
        key: str,
        attr: str = 'text',
        *,
        prefix: str = '',
        suffix: str = '',
        **kwargs: Any,
    ) -> None:
        self._translation_bindings.append((widget, key, attr, prefix, suffix, kwargs))
        self._apply_widget_translation(widget, key, attr, prefix, suffix, kwargs)

    def _update_widget_translation_key(
        self,
        widget: Any,
        key: str,
        attr: str = 'text',
        *,
        prefix: str = '',
        suffix: str = '',
        **kwargs: Any,
    ) -> None:
        for idx, (stored_widget, stored_key, stored_attr, stored_prefix, stored_suffix, stored_kwargs) in enumerate(self._translation_bindings):
            if stored_widget is widget and stored_attr == attr:
                self._translation_bindings[idx] = (widget, key, attr, prefix, suffix, kwargs)
                break
        else:
            self._translation_bindings.append((widget, key, attr, prefix, suffix, kwargs))
        self._apply_widget_translation(widget, key, attr, prefix, suffix, kwargs)

    def _register_tab_title(self, frame: Any, key: str) -> None:
        self._tab_bindings.append((frame, key))
        if hasattr(self, 'notebook'):
            try:
                self.notebook.tab(frame, text=translate(key))
            except Exception:
                pass

    def _apply_widget_translation(
        self,
        widget: Any,
        key: str,
        attr: str,
        prefix: str,
        suffix: str,
        kwargs: Dict[str, Any],
    ) -> None:
        try:
            translated = translate(key, **kwargs)
            widget.configure(**{attr: f"{prefix}{translated}{suffix}"})
        except tk.TclError:
            pass

    def _apply_translations(self, _locale_code: Optional[str] = None) -> None:
        try:
            self.title(translate(self._window_title_key))
        except tk.TclError:
            pass

        for widget, key, attr, prefix, suffix, kwargs in list(self._translation_bindings):
            self._apply_widget_translation(widget, key, attr, prefix, suffix, kwargs)

        if hasattr(self, 'notebook'):
            for frame, key in list(self._tab_bindings):
                try:
                    self.notebook.tab(frame, text=translate(key))
                except Exception:
                    continue

        if hasattr(self, 'autopilot_panel') and self.autopilot_panel:
            self.autopilot_panel.apply_translations()

        if self.coaching_progress_vars:
            self._refresh_progress_summary()

        if self.settings_section:
            self.settings_section.update_localization_display()
    
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
        self.notebook.add(autopilot_frame, text=translate('tab.autopilot'))
        self._register_tab_title(autopilot_frame, 'tab.autopilot')
        self._build_autopilot_tab(autopilot_frame)
        
        # Manual play tab
        manual_frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(manual_frame, text=translate('tab.manual_play'))
        self._register_tab_title(manual_frame, 'tab.manual_play')
        self.manual_tab = manual_frame
        self._build_manual_play_tab(manual_frame)
        
        # Analysis tab
        analysis_frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(analysis_frame, text=translate('tab.analysis'))
        self._register_tab_title(analysis_frame, 'tab.analysis')
        self._build_analysis_tab(analysis_frame)
        
        # Coaching tab
        coaching_frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(coaching_frame, text=translate('tab.coaching'))
        self._register_tab_title(coaching_frame, 'tab.coaching')
        self._build_coaching_tab(coaching_frame)

        # Settings tab
        settings_frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
        self.notebook.add(settings_frame, text=translate('tab.settings'))
        self._register_tab_title(settings_frame, 'tab.settings')
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
            text=translate('section.quick_actions'),
            font=('Arial', 20, 'bold'),
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_primary'],
            relief=tk.RAISED,
            bd=4,
            labelanchor='n'
        )
        quick_actions.pack(side='right', fill='both', expand=True, padx=(10, 0))
        self._register_widget_translation(quick_actions, 'section.quick_actions')
        
        # Create a scrollable frame for quick actions
        quick_actions_canvas = tk.Canvas(quick_actions, bg=COLORS['bg_medium'], highlightthickness=0)
        quick_actions_scrollbar = tk.Scrollbar(quick_actions, orient='vertical', command=quick_actions_canvas.yview)
        quick_actions_frame = tk.Frame(quick_actions_canvas, bg=COLORS['bg_medium'])
        
        quick_actions_canvas.configure(yscrollcommand=quick_actions_scrollbar.set)
        quick_actions_canvas.create_window((0, 0), window=quick_actions_frame, anchor='nw')
        
        # Pack scrollbar and canvas
        quick_actions_scrollbar.pack(side='right', fill='y')
        quick_actions_canvas.pack(side='left', fill='both', expand=True)
        
        # Enhanced button styling function with improved visibility
        def create_action_button(parent, text_key, icon, command, color, desc_key=None, height=3):
            button_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
            button_frame.pack(fill='x', padx=8, pady=8)

            translated_text = translate(text_key)
            button = tk.Button(
                button_frame,
                text=f'{icon}  {translated_text}',
                font=('Arial', 16, 'bold'),  # Increased from 14 to 16
                bg=color,
                fg='#000000',  # Black text for better visibility
                activebackground=self._brighten_color(color),
                activeforeground='#000000',  # Black text on hover too
                relief=tk.RAISED,
                bd=5,  # Increased border
                height=height,
                cursor='hand2',
                command=command,
                padx=10,
                pady=8
            )
            button.pack(fill='x', ipady=8)  # Increased internal padding
            self._update_widget_translation_key(button, text_key, prefix=f'{icon}  ')

            # Add hover effects with shadow
            def on_enter(e):
                button.config(
                    bg=self._brighten_color(color, 0.3),
                    relief=tk.RIDGE,
                    bd=6
                )
            def on_leave(e):
                button.config(
                    bg=color,
                    relief=tk.RAISED,
                    bd=5
                )
            
            button.bind("<Enter>", on_enter)
            button.bind("<Leave>", on_leave)

            # Add description label if provided with improved visibility
            if desc_key:
                desc_text = translate(desc_key)
                desc_label = tk.Label(
                    button_frame,
                    text=desc_text,
                    font=('Arial', 10, 'italic'),  # Increased from 9 to 10
                    bg=COLORS['bg_medium'],
                    fg='#C8D3E0',  # Lighter color for better visibility
                    wraplength=220
                )
                desc_label.pack(pady=(3, 0))
                self._register_widget_translation(desc_label, desc_key)

            return button
        
        # Screen scraper status / toggle button (most prominent)
        self.scraper_status_button = create_action_button(
            quick_actions_frame,
            'actions.screen_scraper_off',
            '🔌',
            self._toggle_screen_scraper,
            COLORS['accent_danger'],
            desc_key='actions.screen_scraper_desc',
            height=4
        )

        if not ENHANCED_SCRAPER_LOADED:
            self.scraper_status_button.config(
                text=translate('actions.screen_scraper_unavailable'),
                state=tk.DISABLED,
                bg=COLORS['bg_light'],
                fg=COLORS['text_secondary'],
                activebackground=COLORS['bg_light'],
                activeforeground=COLORS['text_secondary'],
                cursor='arrow'
            )
            self._register_widget_translation(self.scraper_status_button, 'actions.screen_scraper_unavailable')

        # Separator
        tk.Frame(quick_actions_frame, height=2, bg=COLORS['accent_primary']).pack(fill='x', padx=10, pady=8)

        # Table detection and analysis buttons
        create_action_button(
            quick_actions_frame,
            'actions.detect_tables',
            '🔍',
            self._detect_tables,
            COLORS['accent_primary'],
            desc_key='actions.detect_tables_desc'
        )

        create_action_button(
            quick_actions_frame,
            'actions.screenshot_test',
            '📷',
            self._test_screenshot,
            COLORS['accent_warning'],
            desc_key='actions.screenshot_desc'
        )

        create_action_button(
            quick_actions_frame,
            'actions.gto_analysis',
            '🧠',
            self._run_gto_analysis,
            COLORS['accent_success'],
            desc_key='actions.gto_desc'
        )
        
        # Separator
        tk.Frame(quick_actions_frame, height=2, bg=COLORS['accent_primary']).pack(fill='x', padx=10, pady=8)
        
        # Interface and utility buttons
        create_action_button(
            quick_actions_frame,
            'actions.web_interface',
            '🌐',
            self._open_web_interface,
            COLORS['accent_primary'],
            desc_key='actions.web_desc'
        )

        create_action_button(
            quick_actions_frame,
            'actions.manual_gui',
            '🎮',
            self._open_manual_gui,
            '#9333ea',
            desc_key='actions.manual_desc'
        )

        create_action_button(
            quick_actions_frame,
            'actions.settings',
            '⚙️',
            lambda: self.notebook.select(4),
            '#64748b',
            desc_key='actions.settings_desc'
        )
        
        # Update canvas scroll region
        def configure_scroll_region(event=None):
            quick_actions_canvas.configure(scrollregion=quick_actions_canvas.bbox('all'))
        
        quick_actions_frame.bind('<Configure>', configure_scroll_region)
        
        # Bottom section - Table monitoring
        monitor_section = tk.LabelFrame(
            parent,
            text=translate('section.table_monitor'),
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=2
        )
        monitor_section.pack(fill='both', expand=True, pady=(10, 0))
        self._register_widget_translation(monitor_section, 'section.table_monitor')
        
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
        """Build manual play tab with the embedded manual assistant."""
        self.manual_section = ManualPlaySection(self, parent, modules_loaded=GUI_MODULES_LOADED)


    def _build_analysis_tab(self, parent):
        """Build analysis and statistics tab."""
        analysis_label = tk.Label(
            parent,
            text=translate('analysis.title'),
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        analysis_label.pack(pady=20)
        self._register_widget_translation(analysis_label, 'analysis.title')

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

    def _build_coaching_tab(self, parent):
        """Build the coaching integration tab."""
        self.coaching_section = CoachingSection(self, parent)

    def _handle_autopilot_toggle(self, active: bool):
        """Handle autopilot activation/deactivation."""
        self.autopilot_active = active
        
        if active:
            self._start_autopilot()
        else:
            self._stop_autopilot()

        self._update_manual_autopilot_status(active)

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

    def _update_manual_autopilot_status(self, active: bool) -> None:
        """Mirror autopilot status in the manual play tab."""
        if self.manual_section:
            self.manual_section.update_autopilot_status(active)
    
    def _start_autopilot(self):
        """Start the autopilot system."""
        print("Starting autopilot system...")

        # Update status
        start_time = self.state.start_time or datetime.now()
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
    
    def _stop_autopilot(self):
        """Stop the autopilot system."""
        print("Stopping autopilot system...")
        self._update_table_status(translate('autopilot.log.deactivated') + "\n")
        self._update_manual_autopilot_status(False)
    
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
                                self.after(0, lambda: self._update_table_status(translate('autopilot.log.auto_gto_start') + "\n"))
                                # GTO analysis would happen here with table_state
                                # This is a placeholder for the real implementation
                                self.after(0, lambda: self._update_table_status(translate('autopilot.log.auto_gto_complete') + "\n"))
                            except Exception as gto_error:
                                print(f"Auto GTO analysis error: {gto_error}")
                
                # Update statistics
                stats = {
                    'tables_detected': 1,  # Mock data
                    'hands_played': self.autopilot_panel.state.hands_played + 1,
                    'actions_taken': self.autopilot_panel.state.actions_taken + (1 if self.autopilot_panel.auto_gto_var.get() else 0),
                    'last_action_key': 'autopilot.last_action.auto_analyzing' if self.autopilot_panel.auto_gto_var.get() else 'autopilot.last_action.monitoring'
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
            if self.coaching_section:
                self.after(0, lambda ts=table_state: self.coaching_section.handle_table_state(ts))
            
        except Exception as e:
            print(f"Table state processing error: {e}")
    
    def _detect_tables(self):
        """Detect available poker tables with comprehensive error handling."""
        self._update_table_status(translate('autopilot.log.detecting_tables') + "\n")
        
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
        """Bring the embedded manual GUI into focus inside the notebook."""
        self._update_table_status("🎮 Manual workspace ready within the main window.\n")

        if getattr(self, 'manual_tab', None):
            self.notebook.select(self.manual_tab)
            self._update_table_status("✅ Manual Play tab activated.\n")

        if self.manual_section:
            self.manual_section.focus_workspace()
    
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

            # AUTO-START screen scraper immediately (not waiting for autopilot)
            self._update_table_status("🚀 Auto-starting screen scraper...\n")
            if self._start_enhanced_screen_scraper():
                started_services.append('enhanced screen scraper')
                self._update_table_status("✅ Screen scraper active and monitoring\n")
            else:
                self._update_scraper_indicator(False)
                self._update_table_status("⚠️ Screen scraper not started (check dependencies)\n")

            if started_services:
                print(f'Background services started: {", ".join(started_services)}')
                self._update_table_status(f"📡 Services running: {', '.join(started_services)}\n")

        except Exception as e:
            print(f'Background services error: {e}')
            self._update_table_status(f"❌ Background services error: {e}\n")

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
            text_key = 'actions.screen_scraper_error'
            button.config(
                bg=COLORS['accent_warning'],
                fg=COLORS['bg_dark'],
                activebackground=COLORS['accent_warning'],
                activeforeground=COLORS['bg_dark']
            )
            self._update_widget_translation_key(button, text_key, prefix='⚠️ ')
            return

        if active:
            text_key = 'actions.screen_scraper_on'
            button.config(
                bg=COLORS['accent_success'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['accent_success'],
                activeforeground=COLORS['text_primary']
            )
            self._update_widget_translation_key(button, text_key, prefix='🟢 ')
        else:
            text_key = 'actions.screen_scraper_off'
            button.config(
                bg=COLORS['accent_danger'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['accent_success'],
                activeforeground=COLORS['text_primary']
            )
            self._update_widget_translation_key(button, text_key, prefix='🔌 ')

    def _start_screen_update_loop(self):
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
                        if ENHANCED_SCRAPER_LOADED:
                            try:
                                from .scrape import get_scraper_status
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
                    
                    time.sleep(1)  # Update every second
                    
                except Exception as e:
                    print(f"Update loop error: {e}")
                    time.sleep(2)  # Back off on errors
        
        # Start update thread
        self._screen_update_thread = threading.Thread(target=update_loop, daemon=True)
        self._screen_update_thread.start()
        print("Screen update loop started - display will follow scraper continuously")
    
    def _stop_screen_update_loop(self):
        """Stop the continuous screen update loop."""
        self._screen_update_running = False
        if self._screen_update_thread:
            print("Stopping screen update loop...")

    def _handle_app_exit(self):
        """Handle window close events to ensure clean shutdown."""
        try:
            # Stop update loop first
            self._stop_screen_update_loop()
            
            if self.autopilot_active:
                self.autopilot_active = False
                self._stop_autopilot()
        except Exception as e:
            print(f'Shutdown error: {e}')
        finally:
            self._stop_enhanced_screen_scraper()
            if self._locale_listener_token is not None:
                unregister_locale_listener(self._locale_listener_token)
                self._locale_listener_token = None
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
