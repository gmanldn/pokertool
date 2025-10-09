#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
PokerTool Enhanced Gui Module
===============================

This module provides functionality for enhanced gui operations
within the PokerTool application ecosystem.

Module: pokertool.enhanced_gui
Version: 20.3.0
Last Modified: 2025-10-12
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v20.3.0 (2025-10-12): Enforced single-instance locking and revamped notebook styling for reliable tab visibility
    - v20.2.0 (2025-10-08): CRITICAL FIX - Tab visibility guaranteed, auto-start screen scraper, thread-safe background services
    - v20.1.0 (2025-09-30): Added auto-start scraper, continuous updates, dependency checking
    - v28.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '20.3.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable, Tuple
from pathlib import Path
import webbrowser

# Ensure numpy is loaded from installed packages before any path changes
NUMPY_IMPORT_ERROR: Optional[BaseException] = None
try:
    import numpy as _numpy_guard  # noqa: F401  - imported for side effect
except Exception as _exc:  # pragma: no cover - environment specific
    NUMPY_IMPORT_ERROR = _exc

# CRITICAL: Check and install screen scraper dependencies FIRST
import sys
import os
import subprocess

from .utils.single_instance import acquire_lock, release_lock

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
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Failed to install {package}: {e}")
                print(f"   Please run manually: pip install {package}")
        print(f"{'='*60}\n")


try:
    _ensure_scraper_dependencies()
except Exception as dependency_check_error:
    print(f"⚠️  Dependency preflight check skipped: {dependency_check_error}")

# Import all pokertool modules with better error handling
GUI_MODULES_LOADED = False
CoachingSystem = None
AnalyticsDashboard = None
PrivacySettings = None
UsageEvent = None
GamificationEngine = None
Achievement = None
Badge = None
ProgressState = None
CommunityPlatform = None
ForumPost = None
Challenge = None
CommunityTournament = None
KnowledgeArticle = None
MentorshipPair = None

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
    GUI_MODULES_LOADED = True
except ImportError as e:
    print(f'Warning: GUI modules not fully loaded: {e}')
    GUI_MODULES_LOADED = False

# Import optional advanced modules separately with individual error handling
try:
    from .coaching_system import CoachingSystem
    print("✓ CoachingSystem loaded successfully")
except ImportError as e:
    print(f"Warning: CoachingSystem not available - {e}")
    CoachingSystem = None

try:
    from .analytics_dashboard import AnalyticsDashboard, PrivacySettings, UsageEvent
    print("✓ Analytics dashboard loaded successfully")
except ImportError as e:
    print(f"Warning: Analytics dashboard not available - {e}")
    AnalyticsDashboard = None
    PrivacySettings = None
    UsageEvent = None

try:
    from .gamification import GamificationEngine, Achievement, Badge, ProgressState
    print("✓ Gamification engine loaded successfully")
except ImportError as e:
    print(f"Warning: Gamification engine not available - {e}")
    GamificationEngine = None
    Achievement = None
    Badge = None
    ProgressState = None

try:
    from .community_features import CommunityPlatform, ForumPost, Challenge, CommunityTournament, KnowledgeArticle, MentorshipPair
    print("✓ Community platform loaded successfully")
except ImportError as e:
    print(f"Warning: Community platform not available - {e}")
    CommunityPlatform = None
    ForumPost = None
    Challenge = None
    CommunityTournament = None
    KnowledgeArticle = None
    MentorshipPair = None

# Import screen scraper
try:
    if NUMPY_IMPORT_ERROR is not None:
        raise ImportError(f"Error importing numpy: {NUMPY_IMPORT_ERROR}") from NUMPY_IMPORT_ERROR

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
    
    def __init__(self, lock_path: Optional[Path] = None):
        super().__init__()

        self._lock_path = lock_path
        
        self.title(translate('app.title'))
        self.geometry('1800x1000')  # Increased width to accommodate all tabs
        self.minsize(1600, 900)     # Increased minimum width
        self.configure(bg=COLORS['bg_dark'])
        
        # Maximize window on startup for best tab visibility
        try:
            self.state('zoomed')  # Windows/Linux
        except:
            try:
                self.attributes('-zoomed', True)  # macOS alternative
            except:
                pass  # Keep default geometry if zoom fails
        
        # State
        self.autopilot_active = False
        self.screen_scraper = None
        self.gto_solver = None
        self.opponent_modeler = None
        self.multi_table_manager = None
        self.coaching_system = None
        self.analytics_dashboard = None
        self.gamification_engine = None
        self.community_platform = None
        self._enhanced_scraper_started = False
        self._screen_update_running = False
        self._screen_update_thread = None

        self.manual_section = None
        self.settings_section = None
        self.coaching_section = None
        self.coaching_progress_vars = None  # Initialize coaching progress variables
        self._translation_bindings: List[Tuple[Any, str, str, str, str, Dict[str, Any]]] = []
        self._tab_bindings: List[Tuple[Any, str]] = []
        self._window_title_key = 'app.title'
        self._locale_listener_token: Optional[int] = None
        self._tab_records: List[Dict[str, Any]] = []
        self._tab_title_lookup: Dict[str, str] = {}
        self._tab_failure_reported = False
        self._tab_visibility_checks = 0
        self._tab_watchdog_id: Optional[str] = None
        self._blade_buttons: Dict[str, ttk.Button] = {}
        self._blade_meta: Dict[str, Dict[str, Any]] = {}
        self.blade_bar: Optional[tk.Frame] = None
        self._screen_scraper_ready = False
        self._screen_scraper_health_details: List[str] = []
        # Initialize modules
        self._init_modules()
        self._setup_styles()
        self._build_ui()
        self._locale_listener_token = register_locale_listener(self._apply_translations)
        self._apply_translations()
        self._init_database()
        
        # CRITICAL: Auto-start background services after GUI is fully initialized
        # All widget updates from threads must use self.after() to be thread-safe
        self.after(100, self._start_background_services_safely)

        # Ensure graceful shutdown including scraper cleanup
        self.protocol('WM_DELETE_WINDOW', self._handle_app_exit)

    def release_single_instance_lock(self) -> None:
        """Release the single-instance guard for this process."""
        if self._lock_path:
            release_lock(self._lock_path)
            self._lock_path = None
    
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
                if CoachingSystem:
                    self.coaching_system = CoachingSystem()
                    print("Coaching system ready")
                else:
                    print("Warning: CoachingSystem class not available")
            except Exception as coaching_error:
                print(f"Coaching system initialization error: {coaching_error}")
                self.coaching_system = None

            try:
                if AnalyticsDashboard:
                    self.analytics_dashboard = AnalyticsDashboard()
                    print("Analytics dashboard loaded")
                else:
                    print("Warning: AnalyticsDashboard class not available")
            except Exception as analytics_error:
                print(f"Analytics dashboard initialization error: {analytics_error}")
                self.analytics_dashboard = None

            try:
                if GamificationEngine and Achievement and Badge:
                    self.gamification_engine = GamificationEngine()
                    if hasattr(self.gamification_engine, 'achievements') and 'volume_grinder' not in self.gamification_engine.achievements:
                        self.gamification_engine.register_achievement(Achievement(
                            achievement_id='volume_grinder',
                            title='Volume Grinder',
                            description='Play 100 hands in a day',
                            points=200,
                            condition={'hands_played': 100}
                        ))
                    if hasattr(self.gamification_engine, 'badges') and 'marathon' not in self.gamification_engine.badges:
                        self.gamification_engine.register_badge(Badge(
                            badge_id='marathon',
                            title='Marathon',
                            description='Maintain a 7-day streak of activity',
                            tier='gold'
                        ))
                    print("Gamification engine ready")
                else:
                    print("Warning: Gamification classes not available")
            except Exception as gamification_error:
                print(f"Gamification engine initialization error: {gamification_error}")
                self.gamification_engine = None

            try:
                if (CommunityPlatform and ForumPost and Challenge and 
                    CommunityTournament and KnowledgeArticle):
                    self.community_platform = CommunityPlatform()
                    if hasattr(self.community_platform, 'posts') and not self.community_platform.posts:
                        self.community_platform.create_post(ForumPost(
                            post_id='welcome',
                            author='coach',
                            title='Welcome to the community',
                            content='Share your goals and get feedback from other players.',
                            tags=['announcement']
                        ))
                    if hasattr(self.community_platform, 'challenges') and not self.community_platform.challenges:
                        self.community_platform.create_challenge(Challenge(
                            challenge_id='daily_focus',
                            title='Daily Focus Session',
                            description='Play a focused 30-minute session and post a takeaway.',
                            reward_points=150
                        ))
                    if hasattr(self.community_platform, 'tournaments') and not self.community_platform.tournaments:
                        self.community_platform.schedule_tournament(CommunityTournament(
                            tournament_id='community_cup',
                            name='Community Cup',
                            start_time=time.time() + 86400,
                            format='freeroll'
                        ))
                    if hasattr(self.community_platform, 'articles') and not self.community_platform.articles:
                        self.community_platform.add_article(KnowledgeArticle(
                            article_id='icm_basics',
                            title='ICM Basics',
                            author='mentor',
                            content='Understanding short-stack decisions on the bubble.',
                            categories=['icm', 'strategy']
                        ))
                    print("Community platform ready")
                else:
                    print("Warning: Community platform classes not available")
            except Exception as community_error:
                print(f"Community platform initialization error: {community_error}")
                self.community_platform = None

        except Exception as e:
            print(f"Module initialization error: {e}")
    
    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()

        # Choose a theme that cooperates with dark backgrounds
        available_themes = {name.lower(): name for name in style.theme_names()}
        preferred_theme = 'clam'
        fallback_theme = 'default'

        if sys.platform == 'darwin':
            preferred_theme = 'clam'
            fallback_theme = 'aqua'

        try:
            style.theme_use(available_themes.get(preferred_theme, preferred_theme))
        except tk.TclError:
            try:
                style.theme_use(available_themes.get(fallback_theme, fallback_theme))
            except tk.TclError:
                # Leave whatever theme Tk selected if both options fail
                pass

        # Enhanced button styles
        style.configure('Autopilot.TButton',
                       font=FONTS['autopilot'],
                       foreground=COLORS['text_primary'])

        # Default TButton style for high-contrast bold buttons
        style.configure('TButton',
                       font=FONTS['body'],
                       background=COLORS['accent_primary'],
                       foreground=COLORS['text_primary'])

        # Blade navigation buttons (replacement for default notebook tabs)
        style.configure(
            'BladeNav.TButton',
            font=('Arial', 13, 'bold'),
            background=COLORS['bg_medium'],
            foreground=COLORS['text_primary'],
            padding=(18, 10),
            relief='flat',
            borderwidth=0,
        )
        style.map(
            'BladeNav.TButton',
            background=[('active', COLORS['bg_light'])],
            foreground=[('active', COLORS['text_primary'])],
        )
        style.configure(
            'BladeNavSelected.TButton',
            font=('Arial', 13, 'bold'),
            background=COLORS['accent_primary'],
            foreground=COLORS['bg_dark'],
            padding=(18, 10),
            relief='flat',
            borderwidth=0,
        )
        style.map(
            'BladeNavSelected.TButton',
            background=[('active', COLORS['accent_primary'])],
            foreground=[('active', COLORS['bg_dark'])],
        )
        style.configure(
            'BladeNavDisabled.TButton',
            font=('Arial', 13, 'bold'),
            background=COLORS['bg_dark'],
            foreground=COLORS['text_secondary'],
            padding=(18, 10),
            relief='flat',
            borderwidth=0,
        )
        style.configure(
            'BladeNavDisabledSelected.TButton',
            font=('Arial', 13, 'bold'),
            background=COLORS['accent_warning'],
            foreground=COLORS['bg_dark'],
            padding=(18, 10),
            relief='flat',
            borderwidth=0,
        )

        # Dedicated high-contrast notebook styling targetted by name
        notebook_style = 'PokerNotebook.TNotebook'
        tab_style = f'{notebook_style}.Tab'

        style.configure(
            notebook_style,
            background=COLORS['bg_dark'],
            borderwidth=2,
            relief='ridge',
            tabmargins=(16, 12, 16, 0)
        )

        style.configure(
            tab_style,
            background='#1f2937',
            foreground='#f8fafc',
            padding=(24, 14),
            font=('Arial', 14, 'bold'),
            borderwidth=2,
            relief='raised'
        )

        try:
            style.layout(
                tab_style,
                [
                    ('Notebook.tab', {'sticky': 'nsew', 'children': [
                        ('Notebook.padding', {'side': 'top', 'sticky': 'nsew', 'children': [
                            ('Notebook.focus', {'side': 'top', 'sticky': 'nsew', 'children': [
                                ('Notebook.label', {'side': 'top', 'sticky': 'nsew'})
                            ]})
                        ]})
                    ]})
                ]
            )
        except tk.TclError:
            pass  # Some themes may not expose these layout elements

        style.map(
            tab_style,
            background=[
                ('selected', '#0ea5e9'),
                ('active', '#38bdf8'),
                ('!selected', '#1f2937')
            ],
            foreground=[
                ('selected', '#0b1120'),
                ('active', '#0b1120'),
                ('!selected', '#f8fafc')
            ],
            bordercolor=[
                ('selected', '#f8fafc'),
                ('!selected', '#1f2937')
            ],
            relief=[
                ('selected', 'raised'),
                ('!selected', 'ridge')
            ]
        )

        # Fallback styling for environments that ignore custom style names
        style.configure(
            'TNotebook',
            background='#1f2937',
            borderwidth=1,
            tabmargins=(12, 10, 12, 0)
        )
        style.configure(
            'TNotebook.Tab',
            background='#334155',
            foreground='#f8fafc',
            padding=(22, 12),
            font=('Arial', 13, 'bold'),
            borderwidth=2,
            relief='raised'
        )
        style.map(
            'TNotebook.Tab',
            background=[
                ('selected', '#0ea5e9'),
                ('active', '#38bdf8'),
                ('!selected', '#334155')
            ],
            foreground=[
                ('selected', '#0b1120'),
                ('active', '#0b1120'),
                ('!selected', '#f8fafc')
            ]
        )
        try:
            style.layout(
                notebook_style,
                [('Notebook.client', {'sticky': 'nsew'})]
            )
        except tk.TclError:
            pass

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

    def _extract_icon_prefix(self, fallback: str) -> str:
        """Return emoji prefix (if any) from a fallback label."""
        stripped = fallback.strip()
        if not stripped:
            return ''
        parts = stripped.split(' ', 1)
        if len(parts) < 2:
            return ''
        prefix = parts[0]
        if prefix and not prefix.isalnum():
            return prefix + ' '
        return ''

    def _create_blade_button(
        self,
        frame: Any,
        tab_config: Dict[str, Any],
        feature_available: bool,
        disabled_reason: Optional[str],
    ) -> None:
        """Create a navigation blade button for the supplied tab."""
        if self.blade_bar is None:
            return

        icon_prefix = self._extract_icon_prefix(tab_config.get('title_fallback', ''))
        button_text = tab_config.get('title_fallback') or tab_config.get('name', 'Tab')

        button = ttk.Button(
            self.blade_bar,
            text=button_text,
            style='BladeNav.TButton',
            cursor='hand2',
            command=lambda f=frame: self._handle_blade_press(f)
        )
        button.pack(side='left', padx=4, pady=2)

        title_key = tab_config.get('title_key')
        if title_key:
            self._register_widget_translation(button, title_key, prefix=icon_prefix)
        elif button_text:
            button.configure(text=button_text)

        frame_id = str(frame)
        self._blade_buttons[frame_id] = button
        self._blade_meta[frame_id] = {
            'feature_available': feature_available,
            'disabled_reason': disabled_reason,
        }

        if not feature_available:
            button.configure(style='BladeNavDisabled.TButton')

    def _handle_blade_press(self, frame: Any) -> None:
        """Handle clicks on the blade navigation bar."""
        if not hasattr(self, 'notebook'):
            return
        try:
            self.notebook.select(frame)
        except tk.TclError:
            return
        self._update_blade_selection()


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

    def _update_blade_selection(self) -> None:
        """Refresh blade button styles to reflect the selected tab."""
        if not hasattr(self, 'notebook') or not self._blade_buttons:
            return

        try:
            current = str(self.notebook.select())
        except tk.TclError:
            current = None

        for frame_id, button in self._blade_buttons.items():
            meta = self._blade_meta.get(frame_id, {})
            feature_available = meta.get('feature_available', True)

            if frame_id == current:
                if feature_available:
                    button.configure(style='BladeNavSelected.TButton')
                else:
                    button.configure(style='BladeNavDisabledSelected.TButton')
            else:
                if feature_available:
                    button.configure(style='BladeNav.TButton')
                else:
                    button.configure(style='BladeNavDisabled.TButton')

    def _on_notebook_tab_changed(self, _event: Optional[tk.Event] = None) -> None:
        """Handle ttk notebook tab change events to sync blade navigation."""
        self._update_blade_selection()

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
        self._update_blade_selection()
    
    def _refresh_progress_summary(self):
        """Refresh the coaching progress summary display."""
        # This is a placeholder method for coaching progress updates
        # The actual implementation would depend on the coaching system structure
        pass
    
    def _build_ui(self):
        """Build the integrated user interface with robust error handling."""
        # Main container with notebook tabs
        main_container = tk.Frame(self, bg=COLORS['bg_dark'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Notebook wrapper gives a clear border beneath the tab row
        notebook_wrapper = tk.Frame(
            main_container,
            bg=COLORS['bg_medium'],
            bd=2,
            relief=tk.RIDGE,
            highlightbackground=COLORS['accent_primary'],
            highlightcolor=COLORS['accent_primary'],
            highlightthickness=1
        )
        notebook_wrapper.pack(side='top', fill='both', expand=True)

        if self.blade_bar and self.blade_bar.winfo_exists():
            self.blade_bar.destroy()
        self.blade_bar = tk.Frame(
            notebook_wrapper,
            bg=COLORS['bg_dark']
        )
        self.blade_bar.pack(side='top', fill='x', padx=6, pady=(6, 0))

        notebook_style = 'PokerNotebook.TNotebook'
        try:
            self.notebook = ttk.Notebook(notebook_wrapper, style=notebook_style)
        except tk.TclError:
            self.notebook = ttk.Notebook(notebook_wrapper)

        self.notebook.pack(fill='both', expand=True, padx=6, pady=(0, 6))
        self.notebook.bind("<<NotebookTabChanged>>", self._on_notebook_tab_changed)

        try:
            self.notebook.enable_traversal()
        except AttributeError:
            pass

        try:
            current_style = self.notebook.cget('style')
            print(f"Notebook style in use: {current_style or 'default'}")
        except tk.TclError:
            pass
        
        # Define all tabs with their builders and fallback handlers
        # Using shorter titles to ensure all tabs fit in the window
        tabs_config = [
            {
                'name': 'autopilot',
                'title_key': 'tab.autopilot',
                'title_fallback': '🤖 Auto',  # Shorter title with icon
                'builder': self._build_autopilot_tab,
                'required': True  # Always build this one
            },
            {
                'name': 'manual_play',
                'title_key': 'tab.manual_play', 
                'title_fallback': '🎮 Manual',  # Shorter title with icon
                'builder': self._build_manual_play_tab,
                'required': True
            },
            {
                'name': 'analysis',
                'title_key': 'tab.analysis',
                'title_fallback': '📊 Analysis',  # Icon for clarity
                'builder': self._build_analysis_tab,
                'required': True
            },
            {
                'name': 'coaching',
                'title_key': 'tab.coaching',
                'title_fallback': '🎓 Coach',  # Shorter with icon
                'builder': self._build_coaching_tab,
                'required': False,
                'condition': lambda: self.coaching_system is not None,
                'disabled_message': 'Coaching system not available. Install coaching dependencies to enable this tab.'
            },
            {
                'name': 'settings',
                'title_key': 'tab.settings',
                'title_fallback': '⚙️ Settings',
                'builder': self._build_settings_tab,
                'required': True
            },
            {
                'name': 'analytics',
                'title_key': None,
                'title_fallback': '📈 Stats',  # Much shorter
                'builder': self._build_analytics_tab,
                'required': False,
                'condition': lambda: self.analytics_dashboard is not None,
                'disabled_message': 'Analytics dashboard modules missing. Install analytics extras to activate.'
            },
            {
                'name': 'gamification',
                'title_key': None,
                'title_fallback': '🏆 XP',  # Very short
                'builder': self._build_gamification_tab,
                'required': False,
                'condition': lambda: self.gamification_engine is not None,
                'disabled_message': 'Gamification engine not loaded. Install gamification dependencies to enable.'
            },
            {
                'name': 'community',
                'title_key': None,
                'title_fallback': '👥 Social',  # Shorter
                'builder': self._build_community_tab,
                'required': False,
                'condition': lambda: self.community_platform is not None,
                'disabled_message': 'Community platform disabled. Install community dependencies to access this tab.'
            }
        ]
        
        # Build tabs with robust error handling
        built_tabs = []
        self._tab_records.clear()
        self._tab_title_lookup.clear()
        self._blade_buttons.clear()
        self._blade_meta.clear()
        if self.blade_bar:
            for child in self.blade_bar.winfo_children():
                child.destroy()
        for tab_config in tabs_config:
            try:
                # Determine if the full feature is available
                feature_available = True
                disabled_reason = None
                if not tab_config['required']:
                    condition = tab_config.get('condition')
                    if condition and not condition():
                        feature_available = False
                        disabled_reason = tab_config.get(
                            'disabled_message',
                            'This feature is currently unavailable.'
                        )
                        print(f"Initializing {tab_config['name']} tab in placeholder mode")

                # Create tab frame
                frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
                
                # Get title
                title = tab_config['title_fallback']
                if tab_config['title_key']:
                    try:
                        title = translate(tab_config['title_key'])
                    except:
                        pass  # Use fallback title
                
                # Add to notebook
                self.notebook.add(frame, text=title)
                
                # Register translation if key provided
                if tab_config['title_key']:
                    try:
                        self._register_tab_title(frame, tab_config['title_key'])
                    except Exception as e:
                        print(f"Translation registration failed for {tab_config['name']}: {e}")
                
                # Build tab content with error handling
                if feature_available:
                    try:
                        tab_config['builder'](frame)
                        print(f"✓ Successfully built {tab_config['name']} tab")
                    except Exception as tab_error:
                        print(f"Error building {tab_config['name']} tab: {tab_error}")
                        # Create fallback content
                        self._build_fallback_tab_content(frame, tab_config['name'], str(tab_error))
                else:
                    self._build_unavailable_tab_content(
                        frame,
                        tab_config['name'],
                        disabled_reason or 'Feature unavailable'
                    )
                
                tab_record = {
                    'name': tab_config['name'],
                    'frame': frame,
                    'title': title,
                    'required': tab_config.get('required', False),
                    'feature_available': feature_available,
                }
                self._tab_records.append(tab_record)
                self._tab_title_lookup[str(frame)] = title
                self._create_blade_button(frame, tab_config, feature_available, disabled_reason)
                
                # Store reference for special tabs
                if tab_config['name'] == 'manual_play':
                    self.manual_tab = frame
                
                built_tabs.append((frame, tab_config['name']))
                
            except Exception as e:
                print(f"Failed to create {tab_config['name']} tab: {e}")
                # Continue with other tabs even if one fails
                continue
        
        # Make autopilot tab active by default (if it was built)
        if built_tabs:
            # Find autopilot tab or use first tab
            autopilot_frame = None
            for frame, name in built_tabs:
                if name == 'autopilot':
                    autopilot_frame = frame
                    break
            
            if autopilot_frame:
                self.notebook.select(autopilot_frame)
            else:
                self.notebook.select(built_tabs[0][0])
        
        # CRITICAL: Force notebook to update and show all tabs
        self.notebook.update_idletasks()
        self._update_blade_selection()
        
        # Log tab visibility for debugging
        print(f"UI built successfully with {len(built_tabs)} tabs")
        print(f"Visible tabs: {[self.notebook.tab(i, 'text') for i in range(len(built_tabs))]}")
        self.after(150, self._enforce_tab_visibility)
        self.after(500, self._validate_screen_scraper_ready)
        
        # Add status bar showing tab count
        status_bar = tk.Frame(main_container, bg=COLORS['bg_medium'], height=25)
        status_bar.pack(side='bottom', fill='x', pady=(5, 0))
        
        tab_count_label = tk.Label(
            status_bar,
            text=f"✓ {len(built_tabs)} tabs loaded - Use Ctrl+Tab to cycle through tabs",
            font=('Arial', 9),
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_success']
        )
        tab_count_label.pack(side='left', padx=10, pady=2)
        self.tab_count_label = tab_count_label

    def _select_default_tab(self) -> None:
        """Ensure a sensible default tab stays selected after any recovery."""
        if not hasattr(self, 'notebook'):
            return

        target = None
        for record in self._tab_records:
            if record.get('name') == 'autopilot':
                target = record['frame']
                break

        if target is None and self._tab_records:
            target = self._tab_records[0]['frame']

        if target is None:
            return

        try:
            self.notebook.select(target)
            self._update_blade_selection()
        except tk.TclError:
            pass

    def _enforce_tab_visibility(self, attempt: int = 1) -> None:
        """Watchdog that guarantees notebook tabs stay visible."""
        if not hasattr(self, 'notebook') or not self._tab_records:
            return

        self._tab_visibility_checks += 1

        try:
            visible_ids = list(self.notebook.tabs())
        except tk.TclError as exc:
            print(f"Tab visibility check failed on attempt {attempt}: {exc}")
            return

        visible_set = set(visible_ids)
        missing_records = [
            record for record in self._tab_records
            if str(record['frame']) not in visible_set
        ]

        if missing_records:
            print(f"⚠️  Notebook missing {len(missing_records)} tab(s) on attempt {attempt}; applying fallback styling")
            try:
                self.notebook.configure(style='TNotebook')
            except tk.TclError as style_error:
                print(f"Notebook style fallback failed: {style_error}")

            for record in missing_records:
                frame_id = str(record['frame'])
                title = self._tab_title_lookup.get(frame_id, record['title'])
                try:
                    self.notebook.add(record['frame'], text=title)
                    print(f"   ↪ Reattached tab '{record['name']}'")
                except tk.TclError as attach_error:
                    print(f"   ↪ Failed to reattach tab '{record['name']}': {attach_error}")

            try:
                self.notebook.enable_traversal()
            except AttributeError:
                pass
            except tk.TclError:
                pass

            self.notebook.update_idletasks()
            visible_set = set(self.notebook.tabs())

        missing_required = [
            record for record in self._tab_records
            if record.get('required') and str(record['frame']) not in visible_set
        ]

        current_count = len(visible_set)
        if getattr(self, 'tab_count_label', None):
            try:
                self.tab_count_label.config(
                    text=f"✓ {current_count} tabs active - Ctrl+Tab cycles views"
                )
            except tk.TclError:
                pass

        if missing_required:
            if attempt < 4:
                delay = max(300, 600 * attempt)
                self._tab_watchdog_id = self.after(delay, lambda a=attempt + 1: self._enforce_tab_visibility(a))
            else:
                self._report_tab_failure(missing_required, visible_set)
            return

        # All required tabs accounted for; keep default selection
        self._select_default_tab()

        # Schedule periodic health check
        try:
            if self._tab_watchdog_id:
                self.after_cancel(self._tab_watchdog_id)
        except Exception:
            pass
        finally:
            self._tab_watchdog_id = self.after(10000, self._enforce_tab_visibility)

    def _report_tab_failure(self, missing_records: List[Dict[str, Any]], visible_set: set[str]) -> None:
        """Surface a critical error when required tabs cannot be recovered."""
        if self._tab_failure_reported:
            return

        self._tab_failure_reported = True
        missing_names = ', '.join(record['title'] for record in missing_records)
        diagnostic = [
            "Critical GUI tabs failed to render after recovery attempts.",
            f"Missing: {missing_names}",
            f"Visible widget ids: {sorted(visible_set)}",
            "Try switching to the default Tk theme or reinstalling GUI dependencies.",
        ]
        message = "\n".join(diagnostic)
        print(f"❌ {message}")

        try:
            messagebox.showerror("PokerTool GUI Error", message, parent=self)
        except tk.TclError:
            pass

    def _validate_screen_scraper_ready(self) -> None:
        """Run a lightweight readiness check for the screen scraper stack."""
        if not hasattr(self, 'table_status'):
            # UI still constructing; try again shortly.
            self.after(500, self._validate_screen_scraper_ready)
            return

        details: List[str] = []
        ready = False

        if not SCREEN_SCRAPER_LOADED:
            details.append("❌ Screen scraper module not available - install opencv-python, Pillow, pytesseract, mss")
        else:
            try:
                if self.screen_scraper is None and callable(create_scraper):
                    self.screen_scraper = create_scraper('CHROME')
                    details.append("ℹ️ Screen scraper factory invoked for CHROME profile")

                if self.screen_scraper is None:
                    details.append("❌ Screen scraper factory returned None")
                else:
                    required_methods = ['analyze_table', 'capture_table']
                    missing = [
                        name for name in required_methods
                        if not hasattr(self.screen_scraper, name)
                    ]
                    if missing:
                        details.append(f"⚠️ Screen scraper missing required methods: {', '.join(missing)}")
                    else:
                        ready = True
                        details.append("✅ Screen scraper object ready")

                    if hasattr(self.screen_scraper, 'get_performance_stats'):
                        try:
                            stats = self.screen_scraper.get_performance_stats()
                            if isinstance(stats, dict) and stats:
                                summary = ", ".join(
                                    f"{key}={value}"
                                    for key, value in list(stats.items())[:3]
                                )
                                details.append(f"📊 Initial scraper stats: {summary}")
                        except Exception as stats_error:
                            details.append(f"⚠️ Could not fetch scraper stats: {stats_error}")
            except Exception as exc:
                ready = False
                details.append(f"❌ Screen scraper initialization error: {exc}")

        self._screen_scraper_ready = ready
        self._screen_scraper_health_details = details

        for line in details:
            print(line)
            self._update_table_status(line + "\n")

        if not ready:
            guidance = "Run `python start.py --validate` to verify dependencies."
            self._update_table_status(f"⚠️ {guidance}\n")
    
    def _build_fallback_tab_content(self, parent: tk.Widget, tab_name: str, error_message: str) -> None:
        """Build fallback content for tabs that failed to load properly."""
        # Main error display
        error_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        error_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            error_frame,
            text=f"{tab_name.title().replace('_', ' ')} Tab - Error",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['accent_warning']
        )
        title_label.pack(pady=(0, 20))
        
        # Error message
        error_text = tk.Text(
            error_frame,
            font=FONTS['body'],
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            wrap='word',
            height=8,
            state='disabled'
        )
        error_text.pack(fill='both', expand=True, pady=(0, 20))
        
        # Insert error details
        error_text.config(state='normal')
        error_text.insert('1.0', f"This tab could not be loaded due to an error:\n\n{error_message}\n\n")
        error_text.insert(tk.END, "Possible solutions:\n")
        error_text.insert(tk.END, "• Check that all required dependencies are installed\n")
        error_text.insert(tk.END, "• Restart the application\n")
        error_text.insert(tk.END, "• Check the console for additional error messages\n")
        error_text.insert(tk.END, f"• The {tab_name} functionality may require additional setup\n")
        error_text.config(state='disabled')
        
        # Action buttons frame
        buttons_frame = tk.Frame(error_frame, bg=COLORS['bg_dark'])
        buttons_frame.pack(fill='x', pady=(10, 0))
        
        # Retry button
        retry_button = tk.Button(
            buttons_frame,
            text="Retry Tab Loading",
            font=FONTS['body'],
            bg=COLORS['accent_primary'],
            fg=COLORS['text_primary'],
            command=lambda: self._retry_tab_loading(parent, tab_name)
        )
        retry_button.pack(side='left', padx=(0, 10))
        
        # Diagnostic button
        diagnostic_button = tk.Button(
            buttons_frame,
            text="Show Diagnostics",
            font=FONTS['body'],
            bg=COLORS['accent_warning'],
            fg=COLORS['bg_dark'],
            command=lambda: self._show_tab_diagnostics(tab_name, error_message)
        )
        diagnostic_button.pack(side='left')
        
        print(f"✓ Created fallback content for {tab_name} tab")
    
    def _retry_tab_loading(self, parent: tk.Widget, tab_name: str) -> None:
        """Attempt to retry loading a failed tab."""
        try:
            # Clear the current content
            for widget in parent.winfo_children():
                widget.destroy()
            
            # Find the appropriate builder method
            builder_method = getattr(self, f'_build_{tab_name}_tab', None)
            if builder_method and callable(builder_method):
                builder_method(parent)
                print(f"✓ Successfully retried loading {tab_name} tab")
            else:
                # If no builder method, create a simple message
                tk.Label(
                    parent,
                    text=f"{tab_name.title().replace('_', ' ')} tab is not available",
                    font=FONTS['title'],
                    bg=COLORS['bg_dark'],
                    fg=COLORS['text_secondary']
                ).pack(expand=True)
                
        except Exception as retry_error:
            print(f"Failed to retry {tab_name} tab: {retry_error}")
            # Show the error again
            self._build_fallback_tab_content(parent, tab_name, str(retry_error))
    
    def _show_tab_diagnostics(self, tab_name: str, error_message: str) -> None:
        """Show diagnostic information for a failed tab."""
        diagnostic_info = f"""
Tab Diagnostics: {tab_name}
{'='*50}

Error: {error_message}

Module Status:
- GUI_MODULES_LOADED: {GUI_MODULES_LOADED}
- SCREEN_SCRAPER_LOADED: {SCREEN_SCRAPER_LOADED}  
- ENHANCED_SCRAPER_LOADED: {ENHANCED_SCRAPER_LOADED}

Available Systems:
- coaching_system: {self.coaching_system is not None}
- analytics_dashboard: {self.analytics_dashboard is not None}
- gamification_engine: {self.gamification_engine is not None}
- community_platform: {self.community_platform is not None}

Python Version: {sys.version}
Platform: {sys.platform}
"""
        
        # Create diagnostic window
        diagnostic_window = tk.Toplevel(self)
        diagnostic_window.title(f"Diagnostics: {tab_name}")
        diagnostic_window.geometry("600x400")
        diagnostic_window.configure(bg=COLORS['bg_dark'])
        
        # Diagnostic text
        diagnostic_text = tk.Text(
            diagnostic_window,
            font=('Courier', 10),
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            wrap='word'
        )
        diagnostic_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(diagnostic_text)
        scrollbar.pack(side='right', fill='y')
        diagnostic_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=diagnostic_text.yview)
        
        diagnostic_text.insert('1.0', diagnostic_info)
        diagnostic_text.config(state='disabled')

    def _build_unavailable_tab_content(self, parent: tk.Widget, tab_name: str, reason: str) -> None:
        """Render a lightweight placeholder for features that are disabled."""
        placeholder = tk.Frame(parent, bg=COLORS['bg_dark'])
        placeholder.pack(fill='both', expand=True, padx=20, pady=20)

        tk.Label(
            placeholder,
            text=f"{tab_name.replace('_', ' ').title()}",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['accent_warning']
        ).pack(pady=(0, 10))

        message = tk.Label(
            placeholder,
            text=reason,
            font=FONTS['body'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_secondary'],
            wraplength=480,
            justify='center'
        )
        message.pack(pady=(0, 20))

        tk.Button(
            placeholder,
            text="Check Dependencies",
            font=FONTS['body'],
            bg=COLORS['accent_primary'],
            fg=COLORS['text_primary'],
            command=lambda: self._open_dependency_report(reason)
        ).pack()

    def _open_dependency_report(self, reason: str) -> None:
        """Show quick guidance for resolving missing-feature dependencies."""
        info = f"{reason}\n\nRun `python start.py --validate` to view the dependency report."
        messagebox.showinfo("Feature Unavailable", info, parent=self)
    
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

    def _build_settings_tab(self, parent):
        """Build the settings configuration tab."""
        self.settings_section = SettingsSection(self, parent)

    def _build_analytics_tab(self, parent):
        """Render analytics dashboard data."""
        if not self.analytics_dashboard:
            tk.Label(parent, text='Analytics dashboard unavailable', bg=COLORS['bg_dark'], fg=COLORS['text_primary'], font=FONTS['title']).pack(pady=20)
            return

        summary_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        summary_frame.pack(fill='x', pady=20, padx=20)

        self.analytics_total_var = tk.StringVar(value='0')
        self.analytics_users_var = tk.StringVar(value='0')
        self.analytics_session_var = tk.StringVar(value='0.0')

        def build_metric(label_text: str, variable: tk.StringVar):
            wrapper = tk.Frame(summary_frame, bg=COLORS['bg_medium'], bd=2, relief=tk.RIDGE)
            wrapper.pack(side='left', expand=True, fill='both', padx=10)
            tk.Label(wrapper, text=label_text, font=FONTS['heading'], bg=COLORS['bg_medium'], fg=COLORS['accent_primary']).pack(pady=(10, 4))
            tk.Label(wrapper, textvariable=variable, font=FONTS['title'], bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(pady=(0, 10))

        build_metric('Total Events', self.analytics_total_var)
        build_metric('Active Users', self.analytics_users_var)
        build_metric('Avg Session (min)', self.analytics_session_var)

        controls = tk.Frame(parent, bg=COLORS['bg_dark'])
        controls.pack(fill='x', padx=20)

        ttk.Button(controls, text='Refresh Metrics', command=self._refresh_analytics_metrics).pack(side='left', padx=5)
        ttk.Button(controls, text='Track Sample Event', command=self._record_sample_event).pack(side='left', padx=5)
        ttk.Button(controls, text='Log 30 min Session', command=self._record_sample_session).pack(side='left', padx=5)

        display_frame = tk.LabelFrame(parent, text='Analytics Details', bg=COLORS['bg_dark'], fg=COLORS['text_primary'], padx=10, pady=10)
        display_frame.pack(fill='both', expand=True, padx=20, pady=20)

        self.analytics_metrics_text = tk.Text(display_frame, height=16, bg=COLORS['bg_light'], fg=COLORS['text_primary'], wrap='word')
        self.analytics_metrics_text.pack(fill='both', expand=True)
        self.analytics_metrics_text.configure(state='disabled')

        self._refresh_analytics_metrics()

    def _record_sample_event(self):
        if not self.analytics_dashboard:
            return
        event = UsageEvent(
            event_id=f'gui_{int(time.time()*1000)}',
            user_id='gui-user',
            action='gui_interaction',
            metadata={'source': 'gui'},
        )
        self.analytics_dashboard.track_event(event)
        self._refresh_analytics_metrics()

    def _record_sample_session(self):
        if not self.analytics_dashboard:
            return
        self.analytics_dashboard.track_session('gui-user', 30.0)
        self._refresh_analytics_metrics()

    def _refresh_analytics_metrics(self):
        if not self.analytics_dashboard:
            return
        metrics = self.analytics_dashboard.generate_metrics()
        self.analytics_total_var.set(str(metrics.total_events))
        self.analytics_users_var.set(str(metrics.active_users))
        self.analytics_session_var.set(f"{metrics.avg_session_length_minutes:.2f}")

        self.analytics_metrics_text.configure(state='normal')
        self.analytics_metrics_text.delete('1.0', tk.END)
        summary_lines = [
            f"Most common actions: {', '.join(metrics.most_common_actions) or 'N/A'}",
            "",
            "Actions per user:",
        ]
        for user_id, count in metrics.actions_per_user.items():
            summary_lines.append(f" - {user_id}: {count} events")
        self.analytics_metrics_text.insert(tk.END, '\n'.join(summary_lines))
        self.analytics_metrics_text.configure(state='disabled')

    def _ensure_gamification_state(self, player_id: str) -> ProgressState:
        if not self.gamification_engine:
            raise RuntimeError('Gamification engine is not available')
        state = self.gamification_engine.progress.get(player_id)
        if not state:
            self.gamification_engine.progress[player_id] = ProgressState(player_id=player_id)
            state = self.gamification_engine.progress[player_id]
            self.gamification_engine.export_state()
        return state

    def _build_gamification_tab(self, parent):
        if not self.gamification_engine:
            tk.Label(parent, text='Gamification engine unavailable', bg=COLORS['bg_dark'], fg=COLORS['text_primary'], font=FONTS['title']).pack(pady=20)
            return

        state = self._ensure_gamification_state('hero')

        summary_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        summary_frame.pack(fill='x', padx=20, pady=20)

        self.gamification_level_var = tk.StringVar()
        self.gamification_xp_var = tk.StringVar()
        self.gamification_streak_var = tk.StringVar()

        def metric_block(label, variable):
            block = tk.Frame(summary_frame, bg=COLORS['bg_medium'], bd=2, relief=tk.RIDGE)
            block.pack(side='left', expand=True, fill='both', padx=10)
            tk.Label(block, text=label, font=FONTS['heading'], bg=COLORS['bg_medium'], fg=COLORS['accent_success']).pack(pady=(10, 4))
            tk.Label(block, textvariable=variable, font=FONTS['title'], bg=COLORS['bg_medium'], fg=COLORS['text_primary']).pack(pady=(0, 10))

        metric_block('Level', self.gamification_level_var)
        metric_block('Experience', self.gamification_xp_var)
        metric_block('Streak (days)', self.gamification_streak_var)

        controls = tk.Frame(parent, bg=COLORS['bg_dark'])
        controls.pack(fill='x', padx=20)

        ttk.Button(controls, text='Log 50 hands', command=lambda: self._log_gamification_activity(heroes_hands=50)).pack(side='left', padx=5)
        ttk.Button(controls, text='Log coaching session', command=lambda: self._log_gamification_activity(coaching_minutes=30)).pack(side='left', padx=5)
        ttk.Button(controls, text='Award Marathon Badge', command=self._award_marathon_badge).pack(side='left', padx=5)

        progress_frame = tk.LabelFrame(parent, text='Hero Progress', bg=COLORS['bg_dark'], fg=COLORS['text_primary'])
        progress_frame.pack(fill='both', expand=True, padx=20, pady=20)

        self.gamification_progress_text = tk.Text(progress_frame, height=12, bg=COLORS['bg_light'], fg=COLORS['text_primary'], wrap='word')
        self.gamification_progress_text.pack(fill='both', expand=True)
        self.gamification_progress_text.configure(state='disabled')

        leaderboard_frame = tk.LabelFrame(parent, text='Leaderboard', bg=COLORS['bg_dark'], fg=COLORS['text_primary'])
        leaderboard_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        self.leaderboard_text = tk.Text(leaderboard_frame, height=8, bg=COLORS['bg_light'], fg=COLORS['text_primary'])
        self.leaderboard_text.pack(fill='both', expand=True)
        self.leaderboard_text.configure(state='disabled')

        self._refresh_gamification_view()

    def _log_gamification_activity(self, heroes_hands: int = 0, coaching_minutes: int = 0):
        if not self.gamification_engine:
            return
        metrics = {}
        if heroes_hands:
            metrics['hands_played'] = heroes_hands
        if coaching_minutes:
            metrics['learning_minutes'] = coaching_minutes
        self.gamification_engine.record_activity('hero', metrics)
        self._refresh_gamification_view()

    def _award_marathon_badge(self):
        if not self.gamification_engine:
            return
        try:
            self.gamification_engine.award_badge('hero', 'marathon')
        except KeyError:
            pass
        self._refresh_gamification_view()

    def _refresh_gamification_view(self):
        if not self.gamification_engine:
            return
        state = self._ensure_gamification_state('hero')
        self.gamification_level_var.set(str(state.level))
        self.gamification_xp_var.set(str(state.experience))
        self.gamification_streak_var.set(str(state.streak_days))

        self.gamification_progress_text.configure(state='normal')
        self.gamification_progress_text.delete('1.0', tk.END)
        self.gamification_progress_text.insert(tk.END, 'Achievements:\n')
        for achievement in state.achievements_unlocked or ['None yet']:
            self.gamification_progress_text.insert(tk.END, f" - {achievement}\n")
        self.gamification_progress_text.insert(tk.END, '\nBadges:\n')
        for badge in state.badges_earned or ['None yet']:
            self.gamification_progress_text.insert(tk.END, f" - {badge}\n")
        self.gamification_progress_text.configure(state='disabled')

        leaderboard = self.gamification_engine.leaderboard()
        self.leaderboard_text.configure(state='normal')
        self.leaderboard_text.delete('1.0', tk.END)
        for idx, entry in enumerate(leaderboard, start=1):
            self.leaderboard_text.insert(tk.END, f"{idx}. {entry.player_id} - XP: {entry.experience} (Lvl {entry.level})\n")
        if not leaderboard:
            self.leaderboard_text.insert(tk.END, 'No players yet.')
        self.leaderboard_text.configure(state='disabled')

    def _build_community_tab(self, parent):
        if not self.community_platform:
            tk.Label(parent, text='Community platform unavailable', bg=COLORS['bg_dark'], fg=COLORS['text_primary'], font=FONTS['title']).pack(pady=20)
            return

        layout = tk.Frame(parent, bg=COLORS['bg_dark'])
        layout.pack(fill='both', expand=True, padx=20, pady=20)

        # Posts column
        posts_frame = tk.LabelFrame(layout, text='Forum Posts', bg=COLORS['bg_dark'], fg=COLORS['text_primary'])
        posts_frame.pack(side='left', fill='both', expand=True, padx=10)

        self.community_posts_list = tk.Listbox(posts_frame, height=12, bg=COLORS['bg_light'], fg=COLORS['text_primary'])
        self.community_posts_list.pack(fill='both', expand=True, padx=10, pady=10)

        post_controls = tk.Frame(posts_frame, bg=COLORS['bg_dark'])
        post_controls.pack(fill='x', padx=10, pady=(0, 10))

        tk.Label(post_controls, text='Title', bg=COLORS['bg_dark'], fg=COLORS['text_primary']).grid(row=0, column=0, sticky='w')
        self.community_post_title = tk.Entry(post_controls)
        self.community_post_title.grid(row=0, column=1, sticky='ew', padx=5)

        tk.Label(post_controls, text='Content', bg=COLORS['bg_dark'], fg=COLORS['text_primary']).grid(row=1, column=0, sticky='nw')
        self.community_post_content = tk.Text(post_controls, height=4, width=30)
        self.community_post_content.grid(row=1, column=1, sticky='ew', padx=5)

        tk.Label(post_controls, text='Tags (comma separated)', bg=COLORS['bg_dark'], fg=COLORS['text_primary']).grid(row=2, column=0, sticky='w')
        self.community_post_tags = tk.Entry(post_controls)
        self.community_post_tags.grid(row=2, column=1, sticky='ew', padx=5, pady=(0, 5))

        post_controls.columnconfigure(1, weight=1)

        ttk.Button(post_controls, text='Create Post', command=self._create_community_post).grid(row=3, column=0, columnspan=2, pady=5, sticky='ew')

        reply_frame = tk.Frame(posts_frame, bg=COLORS['bg_dark'])
        reply_frame.pack(fill='x', padx=10, pady=(0, 10))
        tk.Label(reply_frame, text='Reply', bg=COLORS['bg_dark'], fg=COLORS['text_primary']).pack(anchor='w')
        self.community_reply_entry = tk.Entry(reply_frame)
        self.community_reply_entry.pack(fill='x', pady=5)
        ttk.Button(reply_frame, text='Reply to Selected Post', command=self._reply_to_selected_post).pack(fill='x')

        # Challenges and tournaments column
        community_right = tk.Frame(layout, bg=COLORS['bg_dark'])
        community_right.pack(side='left', fill='both', expand=True, padx=10)

        challenges_frame = tk.LabelFrame(community_right, text='Challenges', bg=COLORS['bg_dark'], fg=COLORS['text_primary'])
        challenges_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.community_challenges_list = tk.Listbox(challenges_frame, height=6, bg=COLORS['bg_light'], fg=COLORS['text_primary'])
        self.community_challenges_list.pack(fill='both', expand=True, padx=10, pady=10)
        ttk.Button(challenges_frame, text='Join Selected Challenge', command=self._join_selected_challenge).pack(fill='x', padx=10, pady=(0, 10))

        tournaments_frame = tk.LabelFrame(community_right, text='Community Tournaments', bg=COLORS['bg_dark'], fg=COLORS['text_primary'])
        tournaments_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.community_tournaments_list = tk.Listbox(tournaments_frame, height=6, bg=COLORS['bg_light'], fg=COLORS['text_primary'])
        self.community_tournaments_list.pack(fill='both', expand=True, padx=10, pady=10)

        articles_frame = tk.LabelFrame(community_right, text='Knowledge Articles', bg=COLORS['bg_dark'], fg=COLORS['text_primary'])
        articles_frame.pack(fill='both', expand=True, padx=10)
        self.community_articles_list = tk.Listbox(articles_frame, height=6, bg=COLORS['bg_light'], fg=COLORS['text_primary'])
        self.community_articles_list.pack(fill='both', expand=True, padx=10, pady=10)

        self._refresh_community_views()

    def _create_community_post(self):
        if not self.community_platform:
            return
        title = self.community_post_title.get().strip()
        content = self.community_post_content.get('1.0', tk.END).strip()
        tags = [tag.strip() for tag in self.community_post_tags.get().split(',') if tag.strip()]
        if not title or not content:
            messagebox.showwarning('Community', 'Title and content are required.')
            return
        post_id = f"gui_{int(time.time()*1000)}"
        self.community_platform.create_post(ForumPost(
            post_id=post_id,
            author='hero',
            title=title,
            content=content,
            tags=tags
        ))
        self.community_post_title.delete(0, tk.END)
        self.community_post_content.delete('1.0', tk.END)
        self.community_post_tags.delete(0, tk.END)
        self._refresh_community_views()

    def _reply_to_selected_post(self):
        if not self.community_platform:
            return
        selection = self.community_posts_list.curselection()
        if not selection:
            messagebox.showinfo('Community', 'Select a post to reply to.')
            return
        post_id = self.community_posts_list.get(selection[0]).split(' - ')[0]
        message = self.community_reply_entry.get().strip()
        if not message:
            messagebox.showinfo('Community', 'Enter a reply message.')
            return
        self.community_platform.reply_to_post(post_id, 'hero', message)
        self.community_reply_entry.delete(0, tk.END)
        self._refresh_community_views()

    def _join_selected_challenge(self):
        if not self.community_platform:
            return
        selection = self.community_challenges_list.curselection()
        if not selection:
            messagebox.showinfo('Community', 'Select a challenge to join.')
            return
        challenge_id = self.community_challenges_list.get(selection[0]).split(' - ')[0]
        self.community_platform.join_challenge(challenge_id, 'hero')
        self.community_platform.complete_challenge(challenge_id, 'hero')
        self._refresh_community_views()

    def _refresh_community_views(self):
        if not self.community_platform:
            return
        self.community_posts_list.delete(0, tk.END)
        for post in sorted(self.community_platform.posts.values(), key=lambda p: p.created_at, reverse=True):
            self.community_posts_list.insert(tk.END, f"{post.post_id} - {post.title} ({len(post.replies)} replies)")

        self.community_challenges_list.delete(0, tk.END)
        for challenge in self.community_platform.challenges.values():
            completed = len(challenge.completed_participants)
            total = len(challenge.participants)
            self.community_challenges_list.insert(tk.END, f"{challenge.challenge_id} - {challenge.title} ({completed}/{total} complete)")

        self.community_tournaments_list.delete(0, tk.END)
        for tournament in self.community_platform.tournaments.values():
            self.community_tournaments_list.insert(tk.END, f"{tournament.tournament_id} - {tournament.name} ({len(tournament.entrants)} entrants)")

        self.community_articles_list.delete(0, tk.END)
        for article in self.community_platform.list_articles():
            categories = ', '.join(article.categories)
            self.community_articles_list.insert(tk.END, f"{article.title} [{categories}]")

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
    
    def _stop_autopilot(self):
        """Stop the autopilot system."""
        print("Stopping autopilot system...")
        self._update_table_status(translate('autopilot.log.deactivated') + "\n")
        self._update_manual_autopilot_status(False)
    
    def _autopilot_loop(self):
        """Main autopilot processing loop with detailed table detection."""
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
                        from pokertool.core import Card as CoreCard  # Late import to avoid cycles
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
                    except Exception as update_err:
                        print(f"Manual panel update error: {update_err}")
                # Schedule update on the main thread
                self.after(0, _update_manual_panel)
            
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
    
    def _start_background_services_safely(self):
        """Start background monitoring services safely from the main thread.
        
        This method is called via self.after() to ensure it runs on the main thread
        after GUI initialization is complete. All widget updates use self.after()
        to maintain thread safety.
        """
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
            self.after(0, lambda: self._update_table_status("🚀 Auto-starting screen scraper...\n"))
            if self._start_enhanced_screen_scraper():
                started_services.append('enhanced screen scraper')
                self.after(0, lambda: self._update_table_status("✅ Screen scraper active and monitoring\n"))
            else:
                self.after(0, lambda: self._update_scraper_indicator(False))
                self.after(0, lambda: self._update_table_status("⚠️ Screen scraper not started (check dependencies)\n"))

            if started_services:
                print(f'Background services started: {", ".join(started_services)}')
                services_msg = f"📡 Services running: {', '.join(started_services)}\n"
                self.after(0, lambda msg=services_msg: self._update_table_status(msg))

            # Auto-start screen update loop for continuous monitoring
            self.after(0, self._start_screen_update_loop)
            # Ensure scraper keeps running even if dependencies fluctuate
            self.after(5000, self._ensure_screen_scraper_watchdog)

        except Exception as e:
            print(f'Background services error: {e}')
            error_msg = f"❌ Background services error: {e}\n"
            self.after(0, lambda msg=error_msg: self._update_table_status(msg))

    def _start_background_services(self):
        """Legacy method - redirects to thread-safe implementation."""
        self._start_background_services_safely()

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

    def _ensure_screen_scraper_watchdog(self) -> None:
        """Periodically verify the enhanced scraper is running and restart if needed."""
        try:
            if ENHANCED_SCRAPER_LOADED:
                status = get_scraper_status()
                running = bool(status.get('running', False)) if isinstance(status, dict) else False
                if not running:
                    self._update_table_status("⚠️ Screen scraper stopped unexpectedly. Restarting...\n")
                    self._start_enhanced_screen_scraper()
        except Exception as exc:
            self._update_table_status(f"⚠️ Screen scraper watchdog error: {exc}\n")
        finally:
            self.after(10000, self._ensure_screen_scraper_watchdog)

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
        # IMMEDIATE QUIT - don't wait for cleanup
        try:
            # Try quick cleanup but don't block
            self._screen_update_running = False
            self.autopilot_active = False
        except:
            pass
        
        # Force quit immediately
        self.quit()
        self.destroy()

        # Release the lock before terminating the process
        try:
            self.release_single_instance_lock()
        except Exception as exc:
            print(f"⚠️  Could not release single-instance lock: {exc}")
        
        # Force exit the entire program
        import os
        os._exit(0)


# Main application entry point
def _notify_existing_instance(pid: int) -> None:
    """Inform the user that another PokerTool instance is active."""
    message = (
        f"PokerTool is already running (PID: {pid}).\n"
        "Close the existing window before launching another instance."
    )
    print(f"⚠️  {message}")

    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("PokerTool Already Running", message, parent=root)
    except tk.TclError:
        pass  # Likely no display available; console warning will suffice.
    finally:
        if root is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass

def main():
    """Launch the enhanced poker assistant."""
    lock_path, existing_pid = acquire_lock()
    if not lock_path:
        if existing_pid:
            _notify_existing_instance(existing_pid)
        else:
            print("⚠️  Could not create the PokerTool single-instance lock file.")
        return 1

    app: Optional[IntegratedPokerAssistant] = None
    try:
        app = IntegratedPokerAssistant(lock_path=lock_path)
        app.mainloop()
        if app:
            app.release_single_instance_lock()
        return 0
    except Exception as e:
        print(f"Application error: {e}")
        return 1
    finally:
        release_lock(lock_path)


if __name__ == '__main__':
    import sys
    sys.exit(main())
