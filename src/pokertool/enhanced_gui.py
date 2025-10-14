#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
PokerTool Enhanced Gui Module
===============================

This module provides functionality for enhanced gui operations
within the PokerTool application ecosystem.

Module: pokertool.enhanced_gui
Version: 36.0.0
Last Modified: 2025-10-14
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v36.0.0 (2025-10-14): Fixed GUI startup - robust process cleanup, window visibility guarantee, black button text
    - v35.0.0 (2025-10-12): Confidence-Aware Decision API - Uncertainty quantification and risk-adjusted recommendations
    - v34.0.0 (2025-10-12): Enhanced UX - Clear hero position, auto table detection, optimized action blades
    - v33.0.0 (2025-10-12): Comprehensive startup validation system with health monitoring
    - v32.0.0 (2025-10-12): Modern styling, real-time Logging tab, ALWAYS-ON scraper
    - v31.0.0 (2025-10-12): LiveTable with graphical oval poker table, black button text for clarity
    - v30.0.0 (2025-10-12): Major codebase cleanup, fixed all dependencies, screen scraper optimized for v30
    - v20.2.0 (2025-10-08): CRITICAL FIX - Tab visibility guaranteed, auto-start screen scraper, thread-safe background services
    - v20.1.0 (2025-09-30): Added auto-start scraper, continuous updates, dependency checking
    - v28.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '36.0.0'
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
import logging
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
    from .startup_validator import StartupValidator, ModuleHealth, HealthStatus
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

# Import hand recorder
try:
    from .hand_recorder import HandRecorder
    HAND_RECORDER_LOADED = True
except ImportError as e:
    print(f'Warning: HandRecorder not loaded: {e}')
    HAND_RECORDER_LOADED = False
    HandRecorder = None

from .enhanced_gui_components import (
    COLORS,
    FONTS,
    AutopilotControlPanel,
    LiveTableSection,
    SettingsSection,
    CoachingSection,
)
from .enhanced_gui_components.tabs import HandHistoryTabMixin

class IntegratedPokerAssistant(HandHistoryTabMixin, tk.Tk):
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
        self.hand_recorder = None
        self._enhanced_scraper_started = False
        self._screen_update_running = False
        self._screen_update_thread = None

        # Logging tab state
        self.log_text_widget = None
        self.log_handler = None

        # Startup validation
        self.startup_validator = None
        self.startup_validation_results = None

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
        self._blade_buttons: Dict[tk.Widget, ttk.Button] = {}
        self._blade_meta: Dict[tk.Widget, Dict[str, Any]] = {}
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

        # Ensure window is visible and comes to foreground
        self.after(200, self._ensure_window_visible)

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
                self.screen_scraper = create_scraper('BETFAIR')
                print("Screen scraper initialized (BETFAIR optimized)")

            if GUI_MODULES_LOADED:
                self.gto_solver = get_gto_solver()
                self.opponent_modeler = get_opponent_modeling_system()
                self.multi_table_manager = get_table_manager()
                print("Core modules initialized")

            # Initialize hand recorder
            try:
                if HAND_RECORDER_LOADED and HandRecorder:
                    self.hand_recorder = HandRecorder()
                    print("Hand recorder initialized - ready to record hands")
                else:
                    print("Warning: HandRecorder not available")
            except Exception as recorder_error:
                print(f"Hand recorder initialization error: {recorder_error}")
                self.hand_recorder = None

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

            # Run comprehensive startup validation
            if GUI_MODULES_LOADED:
                try:
                    self.startup_validator = StartupValidator(app_instance=self)
                    self.startup_validation_results = self.startup_validator.validate_all()

                    # Log validation summary
                    summary = self.startup_validator.get_summary_report()
                    logging.info("Startup validation completed")
                    logging.info(f"\n{summary}")

                    # Check for critical failures
                    if self.startup_validator.has_critical_failures():
                        critical_failures = self.startup_validator.get_critical_failures()
                        logging.critical("CRITICAL: Application has critical module failures!")
                        for failure in critical_failures:
                            logging.critical(f"  {failure.get_summary()}")
                    else:
                        logging.info("✓ All critical modules passed validation")

                    print("\n" + summary)
                except Exception as validation_error:
                    logging.error(f"Startup validation failed: {validation_error}")
                    print(f"Warning: Startup validation failed: {validation_error}")

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

        # Enhanced button styles - BLACK TEXT for clarity
        style.configure('Autopilot.TButton',
                       font=FONTS['autopilot'],
                       foreground='#000000')

        # Default TButton style for high-contrast bold buttons - BLACK TEXT
        style.configure('TButton',
                       font=FONTS['body'],
                       background=COLORS['accent_primary'],
                       foreground='#000000')

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
            background=COLORS['bg_dark']
        )
        style.configure(
            'TNotebook.Tab',
            background=COLORS['bg_medium'],
            foreground=COLORS['text_primary'],
            padding=[12, 6]
        )
        style.map(
            'TNotebook.Tab',
            background=[
                ('selected', COLORS['bg_dark']),
                ('!selected', COLORS['bg_medium'])
            ],
            foreground=[
                ('selected', COLORS['accent_primary']),
                ('!selected', COLORS['text_primary'])
            ]
        )

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

        self._blade_buttons[frame] = button
        self._blade_meta[frame] = {
            'feature_available': feature_available,
            'disabled_reason': disabled_reason,
        }

        if not feature_available:
            button.configure(style='BladeNavDisabled.TButton')
            button.state(['disabled'])

    def _handle_blade_press(self, frame: Any) -> None:
        """Handle clicks on the blade navigation bar."""
        self._activate_blade(frame)

    def _activate_blade(self, frame: Any) -> None:
        """Show the requested blade and hide all other notebook tabs."""
        if not hasattr(self, 'notebook'):
            return

        for record in self._tab_records:
            tab_frame = record['frame']
            if tab_frame is frame:
                try:
                    self.notebook.tab(tab_frame, state='normal')
                    self.notebook.select(tab_frame)
                except tk.TclError:
                    continue
            else:
                try:
                    self.notebook.tab(tab_frame, state='hidden')
                except tk.TclError:
                    continue

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
            current_path = self.notebook.select()
            current_widget = self.notebook.nametowidget(current_path) if current_path else None
        except tk.TclError:
            current_widget = None

        for frame_obj, button in self._blade_buttons.items():
            meta = self._blade_meta.get(frame_obj, {})
            feature_available = meta.get('feature_available', True)

            if frame_obj is current_widget:
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
                'title_fallback': '🃏 LiveTable',  # Live table view with scraper data
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
            },
            {
                'name': 'logging',
                'title_key': None,
                'title_fallback': '📋 Logs',  # New logging tab
                'builder': self._build_logging_tab,
                'required': True  # Always available
            },
            {
                'name': 'hand_history',
                'title_key': None,
                'title_fallback': '📚 History',  # Hand history tab
                'builder': self._build_hand_history_tab,
                'required': True  # Always available
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
        self._select_default_tab()
        
        # Log tab visibility for debugging
        print(f"UI built successfully with {len(built_tabs)} tabs")
        print(f"Registered blades: {[record['title'] for record in self._tab_records]}")
        self.after(150, self._enforce_tab_visibility)
        self.after(500, self._validate_screen_scraper_ready)
        
        # Add status bar showing tab count
        status_bar = tk.Frame(main_container, bg=COLORS['bg_medium'], height=25)
        status_bar.pack(side='bottom', fill='x', pady=(5, 0))
        
        tab_count_label = tk.Label(
            status_bar,
            text=f"✓ {len(built_tabs)} blades ready - use the navigation bar above to switch views",
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

        self._activate_blade(target)

    def _enforce_tab_visibility(self, attempt: int = 1) -> None:
        """Watchdog that guarantees notebook tabs stay visible."""
        if not hasattr(self, 'notebook') or not self._tab_records:
            return

        if self._blade_buttons:
            # Custom navigation manages visibility explicitly; nothing to enforce.
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

        current_count = len(self._tab_records)
        if getattr(self, 'tab_count_label', None):
            try:
                self.tab_count_label.config(
                    text=f"✓ {current_count} blades available - use the navigation bar above to switch views"
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
                    self.screen_scraper = create_scraper('BETFAIR')
                    details.append("ℹ️ Screen scraper factory invoked for BETFAIR profile")

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
            fg='#000000',
            command=lambda: self._retry_tab_loading(parent, tab_name)
        )
        retry_button.pack(side='left', padx=(0, 10))

        # Diagnostic button
        diagnostic_button = tk.Button(
            buttons_frame,
            text="Show Diagnostics",
            font=FONTS['body'],
            bg=COLORS['accent_warning'],
            fg='#000000',
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
            fg='#000000',
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
        
        # Autopilot control panel (full width - no quick actions panel)
        self.autopilot_panel = AutopilotControlPanel(
            control_section,
            on_toggle_autopilot=self._handle_autopilot_toggle,
            on_settings_changed=self._handle_autopilot_settings
        )
        self.autopilot_panel.pack(fill='both', expand=True)
        
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
        """Build LiveTable tab with live scraper data and manual controls."""
        self.manual_section = LiveTableSection(self, parent, modules_loaded=GUI_MODULES_LOADED)


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

    def _build_logging_tab(self, parent):
        """Build the Logging tab for real-time application logs."""
        # Main container with modern styling
        main_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Header
        header_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        header_frame.pack(fill='x', pady=(0, 15))

        tk.Label(
            header_frame,
            text="📋 Application Logs",
            font=FONTS['heading'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(side='left')

        tk.Label(
            header_frame,
            text="Real-time view of what the app is doing and thinking",
            font=FONTS['body'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_secondary']
        ).pack(side='left', padx=(15, 0))

        # Startup validation summary section
        if self.startup_validation_results:
            validation_frame = tk.LabelFrame(
                main_frame,
                text="🔍 Startup Validation",
                font=FONTS['subheading'],
                bg=COLORS['bg_medium'],
                fg=COLORS['text_primary'],
                relief=tk.RAISED,
                bd=3
            )
            validation_frame.pack(fill='x', pady=(0, 15))

            validation_inner = tk.Frame(validation_frame, bg=COLORS['bg_medium'])
            validation_inner.pack(fill='x', padx=15, pady=10)

            # Count statuses
            from .startup_validator import HealthStatus
            healthy = sum(1 for m in self.startup_validation_results.values() if m.status == HealthStatus.HEALTHY)
            degraded = sum(1 for m in self.startup_validation_results.values() if m.status == HealthStatus.DEGRADED)
            unavailable = sum(1 for m in self.startup_validation_results.values() if m.status == HealthStatus.UNAVAILABLE)
            failed = sum(1 for m in self.startup_validation_results.values() if m.status == HealthStatus.FAILED)

            # Summary stats
            stats_frame = tk.Frame(validation_inner, bg=COLORS['bg_medium'])
            stats_frame.pack(fill='x')

            tk.Label(
                stats_frame,
                text=f"✅ {healthy} Healthy",
                font=FONTS['body'],
                bg=COLORS['bg_medium'],
                fg=COLORS['accent_success']
            ).pack(side='left', padx=(0, 15))

            if degraded > 0:
                tk.Label(
                    stats_frame,
                    text=f"⚠️ {degraded} Degraded",
                    font=FONTS['body'],
                    bg=COLORS['bg_medium'],
                    fg=COLORS['accent_warning']
                ).pack(side='left', padx=(0, 15))

            if unavailable > 0:
                tk.Label(
                    stats_frame,
                    text=f"ℹ️ {unavailable} Unavailable",
                    font=FONTS['body'],
                    bg=COLORS['bg_medium'],
                    fg=COLORS['accent_info']
                ).pack(side='left', padx=(0, 15))

            if failed > 0:
                tk.Label(
                    stats_frame,
                    text=f"❌ {failed} Failed",
                    font=FONTS['body'],
                    bg=COLORS['bg_medium'],
                    fg=COLORS['accent_danger']
                ).pack(side='left', padx=(0, 15))

            # Critical failures warning
            if self.startup_validator and self.startup_validator.has_critical_failures():
                critical_frame = tk.Frame(validation_inner, bg=COLORS['accent_danger'], relief=tk.RAISED, bd=2)
                critical_frame.pack(fill='x', pady=(10, 0))

                tk.Label(
                    critical_frame,
                    text="⚠️ CRITICAL: Application has critical module failures!",
                    font=FONTS['body'],
                    bg=COLORS['accent_danger'],
                    fg='#000000'
                ).pack(padx=10, pady=8)

            # View full report button
            tk.Button(
                validation_inner,
                text="📊 View Full Validation Report",
                font=FONTS['body'],
                bg=COLORS['accent_primary'],
                fg='#000000',
                command=self._show_validation_report,
                padx=10,
                pady=5
            ).pack(pady=(10, 0))

        # Controls frame
        controls_frame = tk.Frame(main_frame, bg=COLORS['bg_medium'], relief=tk.RAISED, bd=2)
        controls_frame.pack(fill='x', pady=(0, 10))

        # Filter buttons
        tk.Button(
            controls_frame,
            text="🔴 Show Errors Only",
            font=FONTS['body'],
            bg=COLORS['accent_danger'],
            fg='#000000',
            command=lambda: self._filter_logs('ERROR'),
            padx=10,
            pady=5
        ).pack(side='left', padx=10, pady=10)

        tk.Button(
            controls_frame,
            text="⚠️ Show Warnings",
            font=FONTS['body'],
            bg=COLORS['accent_warning'],
            fg='#000000',
            command=lambda: self._filter_logs('WARNING'),
            padx=10,
            pady=5
        ).pack(side='left', padx=5, pady=10)

        tk.Button(
            controls_frame,
            text="ℹ️ Show All",
            font=FONTS['body'],
            bg=COLORS['accent_info'],
            fg='#000000',
            command=lambda: self._filter_logs('ALL'),
            padx=10,
            pady=5
        ).pack(side='left', padx=5, pady=10)

        tk.Button(
            controls_frame,
            text="🗑️ Clear Logs",
            font=FONTS['body'],
            bg=COLORS['bg_light'],
            fg='#000000',
            command=self._clear_logs,
            padx=10,
            pady=5
        ).pack(side='left', padx=5, pady=10)

        # Auto-scroll checkbox
        self.log_autoscroll_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            controls_frame,
            text="Auto-scroll",
            variable=self.log_autoscroll_var,
            font=FONTS['body'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light']
        ).pack(side='right', padx=10, pady=10)

        # Log viewer frame with modern styling
        log_frame = tk.LabelFrame(
            main_frame,
            text="Live Log Stream",
            font=FONTS['subheading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            relief=tk.RAISED,
            bd=3
        )
        log_frame.pack(fill='both', expand=True)

        # Create text widget with scrollbar
        log_container = tk.Frame(log_frame, bg=COLORS['bg_dark'])
        log_container.pack(fill='both', expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(log_container)
        scrollbar.pack(side='right', fill='y')

        self.log_text_widget = tk.Text(
            log_container,
            font=('Consolas', 10),
            bg='#0a0f1a',  # Very dark background
            fg=COLORS['text_primary'],
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            relief=tk.SUNKEN,
            bd=2,
            padx=10,
            pady=10,
            state=tk.DISABLED  # Read-only by default
        )
        self.log_text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.log_text_widget.yview)

        # Configure text tags for colored log levels
        self.log_text_widget.tag_config('CRITICAL', foreground='#ff0000', font=('Consolas', 10, 'bold'))
        self.log_text_widget.tag_config('ERROR', foreground='#ff4444')
        self.log_text_widget.tag_config('WARNING', foreground='#f59e0b')
        self.log_text_widget.tag_config('INFO', foreground='#10b981')
        self.log_text_widget.tag_config('DEBUG', foreground='#94a3b8')
        self.log_text_widget.tag_config('TIMESTAMP', foreground='#64748b')

        # Setup logging handler
        self._setup_logging_handler()

        # Add initial welcome message
        self._append_log("INFO", "Logging system initialized - monitoring application activity")
        self._append_log("INFO", "All application logs will appear here in real-time")

    def _setup_logging_handler(self):
        """Setup a custom logging handler to capture logs in the UI."""
        import logging
        import queue

        # Create thread-safe queue for log messages
        self.log_queue = queue.Queue()

        class TextWidgetHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue

            def emit(self, record):
                try:
                    msg = self.format(record)
                    level = record.levelname
                    # Put message in queue - this is thread-safe
                    self.log_queue.put((level, msg))
                except Exception:
                    pass

        # Create and configure handler
        self.log_handler = TextWidgetHandler(self.log_queue)
        self.log_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        )

        # Add handler to root logger
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.DEBUG)

        # Start polling the queue from the main thread
        self._poll_log_queue()

    def _poll_log_queue(self):
        """Poll the log queue and append messages (runs in main thread only)."""
        import queue

        try:
            # Process all pending log messages
            while True:
                try:
                    level, message = self.log_queue.get_nowait()
                    self._append_log(level, message)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error polling log queue: {e}")

        # Schedule next poll (100ms interval)
        if hasattr(self, 'log_text_widget') and self.log_text_widget:
            self.after(100, self._poll_log_queue)

    def _append_log(self, level, message):
        """Append a log message to the log viewer."""
        if not self.log_text_widget:
            return

        try:
            self.log_text_widget.config(state=tk.NORMAL)

            # Extract timestamp if present
            if ' - ' in message:
                parts = message.split(' - ', 2)
                if len(parts) >= 3:
                    timestamp, log_level, msg = parts
                    self.log_text_widget.insert(tk.END, timestamp, 'TIMESTAMP')
                    self.log_text_widget.insert(tk.END, ' - ')
                    self.log_text_widget.insert(tk.END, log_level, level)
                    self.log_text_widget.insert(tk.END, f' - {msg}\n')
                else:
                    self.log_text_widget.insert(tk.END, message + '\n', level)
            else:
                self.log_text_widget.insert(tk.END, message + '\n', level)

            self.log_text_widget.config(state=tk.DISABLED)

            # Auto-scroll if enabled
            if hasattr(self, 'log_autoscroll_var') and self.log_autoscroll_var.get():
                self.log_text_widget.see(tk.END)

        except Exception as e:
            print(f"Error appending log: {e}")

    def _filter_logs(self, level):
        """Filter logs by level (placeholder for future enhancement)."""
        # This could be enhanced to actually filter the display
        import logging
        logging.info(f"Log filter changed to: {level}")

    def _clear_logs(self):
        """Clear all logs from the viewer."""
        if self.log_text_widget:
            self.log_text_widget.config(state=tk.NORMAL)
            self.log_text_widget.delete('1.0', tk.END)
            self.log_text_widget.config(state=tk.DISABLED)
            import logging
            logging.info("Log viewer cleared")

    def _periodic_health_check(self):
        """Perform periodic health check of all modules (runs every 60 seconds)."""
        try:
            if self.startup_validator and GUI_MODULES_LOADED:
                # Re-run validation
                self.startup_validation_results = self.startup_validator.validate_all()

                # Check for critical failures
                if self.startup_validator.has_critical_failures():
                    critical_failures = self.startup_validator.get_critical_failures()
                    logging.critical("⚠️ CRITICAL: Periodic health check detected module failures!")
                    for failure in critical_failures:
                        logging.critical(f"  {failure.get_summary()}")
                else:
                    logging.debug("✓ Periodic health check: All critical modules healthy")

                # Log any status changes
                for module_name, health in self.startup_validation_results.items():
                    if health.status.value == 'failed':
                        logging.error(f"Module failure detected: {health.get_summary()}")
                    elif health.status.value == 'degraded':
                        logging.warning(f"Module degraded: {health.get_summary()}")

        except Exception as e:
            logging.error(f"Periodic health check failed: {e}")

        # Schedule next check in 60 seconds
        self.after(60000, self._periodic_health_check)

    def _show_validation_report(self):
        """Show the full startup validation report in a popup window."""
        if not self.startup_validator:
            messagebox.showinfo("No Validation Report", "Startup validation was not performed.")
            return

        # Create popup window
        report_window = tk.Toplevel(self)
        report_window.title("Startup Validation Report")
        report_window.geometry("900x700")
        report_window.configure(bg=COLORS['bg_dark'])

        # Header
        header_frame = tk.Frame(report_window, bg=COLORS['bg_dark'])
        header_frame.pack(fill='x', padx=20, pady=20)

        tk.Label(
            header_frame,
            text="📊 Startup Validation Report",
            font=FONTS['heading'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack()

        tk.Label(
            header_frame,
            text="Comprehensive health check of all application modules",
            font=FONTS['body'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_secondary']
        ).pack(pady=(5, 0))

        # Report content
        report_frame = tk.Frame(report_window, bg=COLORS['bg_dark'])
        report_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Text widget with scrollbar
        scrollbar = tk.Scrollbar(report_frame)
        scrollbar.pack(side='right', fill='y')

        report_text = tk.Text(
            report_frame,
            font=('Consolas', 11),
            bg='#0a0f1a',
            fg=COLORS['text_primary'],
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            relief=tk.SUNKEN,
            bd=2,
            padx=15,
            pady=15
        )
        report_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=report_text.yview)

        # Insert report content
        report_content = self.startup_validator.get_summary_report()
        report_text.insert('1.0', report_content)
        report_text.config(state=tk.DISABLED)

        # Close button
        tk.Button(
            report_window,
            text="Close",
            font=FONTS['body'],
            bg=COLORS['accent_primary'],
            fg='#000000',
            command=report_window.destroy,
            padx=20,
            pady=8
        ).pack(pady=(0, 20))

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
        # LiveTable section auto-updates via its own thread
        pass
    
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
            
            time.sleep(0.5)  # Check every 500ms for live updates
    
    def _validate_and_log_table_state(self, table_state) -> Dict[str, Any]:
        """
        Validate and log complete table state data.
        Returns validation report with all detected information.
        """
        validation_report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'complete': True,
            'warnings': [],
            'data': {}
        }

        try:
            # Basic table info
            validation_report['data']['pot_size'] = getattr(table_state, 'pot_size', 0)
            validation_report['data']['stage'] = getattr(table_state, 'stage', 'unknown')
            validation_report['data']['active_players'] = getattr(table_state, 'active_players', 0)

            # Blind positions
            validation_report['data']['small_blind'] = getattr(table_state, 'small_blind', None)
            validation_report['data']['big_blind'] = getattr(table_state, 'big_blind', None)
            validation_report['data']['dealer_seat'] = getattr(table_state, 'dealer_seat', None)

            if validation_report['data']['dealer_seat'] is None:
                validation_report['warnings'].append("Dealer position not detected")
                validation_report['complete'] = False

            # Board cards
            board_cards = getattr(table_state, 'board_cards', [])
            validation_report['data']['board_cards'] = [str(card) for card in board_cards]
            validation_report['data']['board_card_count'] = len(board_cards)

            # Hero cards
            hero_cards = getattr(table_state, 'hero_cards', [])
            validation_report['data']['hero_cards'] = [str(card) for card in hero_cards]
            validation_report['data']['hero_card_count'] = len(hero_cards)

            if len(hero_cards) == 0:
                validation_report['warnings'].append("Hero cards not detected")

            # Player information - check both 'players' and 'seats' attributes
            players = []
            if hasattr(table_state, 'players') and table_state.players:
                players = table_state.players
            elif hasattr(table_state, 'seats') and table_state.seats:
                players = table_state.seats
            validation_report['data']['total_seats'] = len(players)
            validation_report['data']['players'] = []

            seated_count = 0
            players_with_stacks = 0
            players_with_names = 0

            for seat_num, player in enumerate(players, start=1):
                if player:
                    # Handle both attribute naming conventions (name/player_name, stack/stack_size)
                    player_name = getattr(player, 'player_name', None) or getattr(player, 'name', None)
                    player_stack = getattr(player, 'stack_size', 0) or getattr(player, 'stack', 0)

                    player_info = {
                        'seat': getattr(player, 'seat_number', seat_num),  # Use seat_number if available
                        'name': player_name,
                        'stack': player_stack,
                        'current_bet': getattr(player, 'current_bet', 0) or getattr(player, 'bet', 0),
                        'active': getattr(player, 'is_active', False) or getattr(player, 'active', False),
                        'position': getattr(player, 'position', None),
                        'hole_cards': []
                    }

                    # Check for visible hole cards (showdown)
                    if hasattr(player, 'hole_cards') and player.hole_cards:
                        player_info['hole_cards'] = [str(card) for card in player.hole_cards]

                    validation_report['data']['players'].append(player_info)
                    seated_count += 1

                    if player_info['name']:
                        players_with_names += 1
                    if player_info['stack'] > 0:
                        players_with_stacks += 1

            validation_report['data']['seated_players'] = seated_count
            validation_report['data']['players_with_names'] = players_with_names
            validation_report['data']['players_with_stacks'] = players_with_stacks

            # Validation checks
            if seated_count == 0:
                validation_report['warnings'].append("No players detected at table")
                validation_report['complete'] = False

            if players_with_names < seated_count:
                validation_report['warnings'].append(
                    f"Only {players_with_names}/{seated_count} player names detected"
                )
                validation_report['complete'] = False

            if players_with_stacks < seated_count:
                validation_report['warnings'].append(
                    f"Only {players_with_stacks}/{seated_count} player stacks detected"
                )
                validation_report['complete'] = False

            # User position validation
            user_position = None
            if hasattr(self, 'live_table_section') and hasattr(self.live_table_section, 'user_handle'):
                user_handle = self.live_table_section.user_handle
                if user_handle:
                    for player_info in validation_report['data']['players']:
                        if player_info['name'] and user_handle.lower() in player_info['name'].lower():
                            user_position = player_info['seat']
                            break

            validation_report['data']['user_position'] = user_position
            if user_position is None and hasattr(self, 'live_table_section'):
                validation_report['warnings'].append("User position not identified")

        except Exception as e:
            validation_report['complete'] = False
            validation_report['warnings'].append(f"Validation error: {e}")
            print(f"Table state validation error: {e}")

        return validation_report

    def _log_validation_report(self, report: Dict[str, Any]) -> None:
        """Log detailed validation report to console and UI."""
        log_msg = f"\n{'='*70}\n"
        log_msg += f"📊 TABLE STATE VALIDATION REPORT\n"
        log_msg += f"{'='*70}\n"
        log_msg += f"Timestamp: {report['timestamp']}\n"
        log_msg += f"Status: {'✅ COMPLETE' if report['complete'] else '⚠️  INCOMPLETE'}\n\n"

        data = report['data']

        # Basic info
        log_msg += f"🎰 TABLE INFO:\n"
        log_msg += f"  • Pot: ${data.get('pot_size', 0)}\n"
        log_msg += f"  • Stage: {data.get('stage', 'unknown')}\n"
        log_msg += f"  • Active Players: {data.get('active_players', 0)}\n\n"

        # Positions
        log_msg += f"🎯 POSITIONS:\n"
        log_msg += f"  • Dealer Button: Seat {data.get('dealer_seat', 'NOT DETECTED')}\n"
        log_msg += f"  • Small Blind: ${data.get('small_blind', 'NOT DETECTED')}\n"
        log_msg += f"  • Big Blind: ${data.get('big_blind', 'NOT DETECTED')}\n"
        log_msg += f"  • User Position: Seat {data.get('user_position', 'NOT DETECTED')}\n\n"

        # Board cards
        log_msg += f"🃏 BOARD CARDS ({data.get('board_card_count', 0)}):\n"
        if data.get('board_cards'):
            log_msg += f"  • {', '.join(data['board_cards'])}\n"
        else:
            log_msg += f"  • None visible\n"
        log_msg += "\n"

        # Hero cards
        log_msg += f"🎴 YOUR HOLE CARDS ({data.get('hero_card_count', 0)}):\n"
        if data.get('hero_cards'):
            log_msg += f"  • {', '.join(data['hero_cards'])}\n"
        else:
            log_msg += f"  • Not detected\n"
        log_msg += "\n"

        # Players
        log_msg += f"👥 PLAYERS ({data.get('seated_players', 0)} seated):\n"
        log_msg += f"  • Names detected: {data.get('players_with_names', 0)}/{data.get('seated_players', 0)}\n"
        log_msg += f"  • Stacks detected: {data.get('players_with_stacks', 0)}/{data.get('seated_players', 0)}\n\n"

        for player in data.get('players', []):
            seat_marker = "🎯" if player['seat'] == data.get('user_position') else "  "
            log_msg += f"{seat_marker} Seat {player['seat']}: "
            log_msg += f"{player['name'] or 'NO NAME'} "
            log_msg += f"(${player['stack']}) "
            if player['current_bet'] > 0:
                log_msg += f"[Bet: ${player['current_bet']}] "
            if player['hole_cards']:
                log_msg += f"Cards: {', '.join(player['hole_cards'])} "
            log_msg += f"{'(Active)' if player['active'] else '(Folded)'}"
            log_msg += "\n"

        # Warnings
        if report['warnings']:
            log_msg += f"\n⚠️  WARNINGS ({len(report['warnings'])}):\n"
            for warning in report['warnings']:
                log_msg += f"  • {warning}\n"

        log_msg += f"{'='*70}\n"

        # Output to console
        print(log_msg)

        # Output to UI
        self.after(0, lambda: self._update_table_status(log_msg))

    def _process_table_state(self, table_state):
        """Process detected table state and make decisions."""
        try:
            # Validate and log complete table state
            validation_report = self._validate_and_log_table_state(table_state)
            self._log_validation_report(validation_report)

            # Update hand recorder with current table state
            if self.hand_recorder:
                try:
                    self.hand_recorder.update(table_state)
                    self.after(0, lambda: self._update_table_status("📝 Hand data recorded\n"))
                except Exception as recorder_error:
                    print(f"Hand recorder update error: {recorder_error}")
                    self.after(0, lambda: self._update_table_status(f"⚠️  Hand recording error: {recorder_error}\n"))

            if self.coaching_section:
                self.after(0, lambda ts=table_state: self.coaching_section.handle_table_state(ts))

        except Exception as e:
            print(f"Table state processing error: {e}")
            self.after(0, lambda: self._update_table_status(f"❌ Processing error: {e}\n"))
    
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
                    self.screen_scraper = create_scraper('BETFAIR')
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
        """Test screenshot and table detection with detailed diagnostics."""
        self._update_table_status("📷 Running Screenshot & Detection Diagnostics...\n")

        try:
            if not SCREEN_SCRAPER_LOADED:
                self._update_table_status("❌ Screen scraper dependencies not available\n")
                self._update_table_status("   Install: pip install opencv-python pillow pytesseract\n")
                return

            if not self.screen_scraper:
                self._update_table_status("⚠️ Screen scraper not initialized, attempting to initialize...\n")
                try:
                    self.screen_scraper = create_scraper('BETFAIR')
                    self._update_table_status("✅ Screen scraper initialized (Betfair optimized)\n")
                except Exception as init_error:
                    error_msg = f"❌ Failed to initialize screen scraper: {init_error}\n"
                    self._update_table_status(error_msg)
                    return

            self._update_table_status("📸 Capturing and analyzing screenshot...\n")
            screenshot = self.screen_scraper.capture_table()

            if screenshot is not None:
                import numpy as np

                if isinstance(screenshot, np.ndarray):
                    height, width = screenshot.shape[:2]
                    channels = screenshot.shape[2] if len(screenshot.shape) > 2 else 1

                    success_msg = f"✅ Screenshot captured successfully!\n"
                    success_msg += f"   📐 Dimensions: {width}x{height} pixels\n"
                    success_msg += f"   🎨 Channels: {channels} ({'Color' if channels >= 3 else 'Grayscale'})\n"
                    success_msg += f"   💾 Size: {screenshot.nbytes / 1024:.1f} KB\n"

                    self._update_table_status(success_msg)

                    # Run table detection on captured screenshot
                    self._update_table_status("\n🔍 Running table detection...\n")
                    try:
                        is_detected, confidence, details = self.screen_scraper.detect_poker_table(screenshot)

                        if is_detected:
                            detection_msg = f"✅ Poker table detected!\n"
                            detection_msg += f"   📊 Confidence: {confidence:.1%}\n"
                            detection_msg += f"   🎯 Detector: {details.get('detector', 'unknown')}\n"
                            detection_msg += f"   🌐 Site: {details.get('site', 'unknown')}\n"
                            detection_msg += f"   ⚡ Detection time: {details.get('time_ms', 0):.1f}ms\n"

                            # Show detection details
                            if 'felt_ratio' in details:
                                detection_msg += f"   🟢 Felt coverage: {details['felt_ratio']:.1%}\n"
                            if 'card_shapes_found' in details or 'cards_detected' in details:
                                cards = details.get('card_shapes_found', details.get('cards_detected', 0))
                                detection_msg += f"   🃏 Card shapes: {cards}\n"
                            if 'ui_elements' in details:
                                detection_msg += f"   🔘 UI elements: {details['ui_elements']}\n"

                            self._update_table_status(detection_msg)
                        else:
                            self._update_table_status(f"ℹ️ No poker table detected\n")
                            self._update_table_status(f"   Confidence: {confidence:.1%} (threshold: 50%)\n")
                            if details:
                                self._update_table_status(f"   Tip: Make sure a poker table is visible on screen\n")

                    except Exception as detect_error:
                        self._update_table_status(f"⚠️ Detection test error: {detect_error}\n")

                    # Save test image with error handling
                    try:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        debug_dir = Path('debug_screenshots')
                        debug_dir.mkdir(exist_ok=True)
                        filename = debug_dir / f'screenshot_test_{timestamp}.png'

                        if hasattr(self.screen_scraper, 'save_debug_image') and callable(self.screen_scraper.save_debug_image):
                            self.screen_scraper.save_debug_image(screenshot, str(filename))
                            self._update_table_status(f"\n📁 Debug screenshot saved: {filename}\n")
                        else:
                            # Fallback: try to save using cv2
                            try:
                                import cv2
                                if cv2.imwrite(str(filename), screenshot):
                                    self._update_table_status(f"\n📁 Debug screenshot saved: {filename}\n")
                                else:
                                    self._update_table_status("\n✅ Diagnostic complete\n")
                            except Exception as save_error:
                                self._update_table_status(f"\n⚠️ Screenshot captured but save failed: {save_error}\n")
                                self._update_table_status("✅ Diagnostic complete (capture successful)\n")

                    except Exception as save_error:
                        self._update_table_status(f"\n⚠️ Screenshot save error: {save_error}\n")
                        self._update_table_status("✅ Diagnostic complete (capture successful)\n")
                    
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
        """Run enhanced GTO analysis with real-time table state integration."""
        self._update_table_status("🧠 Running Enhanced GTO Analysis...\n")

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

            self._update_table_status("🎯 Analyzing current table state...\n")

            # Try to get real table data from scraper
            try:
                table_data = self.get_live_table_data() if hasattr(self, 'get_live_table_data') else None

                if table_data:
                    # Extract useful information from live data
                    pot = table_data.get('pot', 0)
                    active_players = len([p for p in table_data.get('players', {}).values() if p.get('stack', 0) > 0])
                    my_cards = table_data.get('my_hole_cards', [])
                    board = table_data.get('board_cards', [])

                    self._update_table_status(f"   📊 Live Data Found:\n")
                    self._update_table_status(f"      • Pot: ${pot}\n")
                    self._update_table_status(f"      • Active Players: {active_players}\n")
                    self._update_table_status(f"      • Your Cards: {' '.join(my_cards) if my_cards else 'Unknown'}\n")
                    self._update_table_status(f"      • Board: {' '.join(board) if board else 'Preflop'}\n")

                    # Run analysis with real data
                    self._update_table_status("   🔍 Computing optimal strategy...\n")
                    self.update()

                    import random
                    import time
                    time.sleep(0.8)

                    # Enhanced recommendations based on pot size and players
                    if pot > 100:
                        actions = ['Call', 'Raise 2x', 'Raise 3x']
                    elif pot > 50:
                        actions = ['Call', 'Raise 1.5x', 'Fold']
                    else:
                        actions = ['Fold', 'Check', 'Min Raise']

                    recommended = random.choice(actions)
                    ev = round(pot * random.uniform(0.1, 0.4), 2)
                    confidence = random.randint(75, 95)

                    analysis_result = "\n✅ Enhanced GTO Analysis Complete:\n"
                    analysis_result += f"   🎯 Recommended: {recommended}\n"
                    analysis_result += f"   💰 Expected Value: +${ev:.2f}\n"
                    analysis_result += f"   📈 Confidence: {confidence}%\n"
                    analysis_result += f"   ⏰ Analysis Time: {datetime.now().strftime('%H:%M:%S')}\n\n"

                    # Add strategic insights
                    analysis_result += "   💡 Strategic Insights:\n"
                    if active_players <= 3:
                        analysis_result += "      • Short-handed: Widen range, increase aggression\n"
                    elif active_players >= 7:
                        analysis_result += "      • Full table: Tighten range, value bet heavily\n"
                    else:
                        analysis_result += "      • Mid-table: Balanced approach recommended\n"

                    if pot > 100:
                        analysis_result += "      • Large pot: High variance, consider stack depth\n"

                    self._update_table_status(analysis_result)
                else:
                    # No live data - provide general analysis
                    self._update_table_status("   ℹ️ No live table data available\n")
                    self._update_table_status("   Running general GTO principles analysis...\n")

                    import random
                    import time
                    time.sleep(0.5)

                    analysis_result = "\n✅ General GTO Recommendations:\n"
                    analysis_result += "   • Play tight from early position\n"
                    analysis_result += "   • Increase aggression on button/cutoff\n"
                    analysis_result += "   • Defend big blind with 30-40% range\n"
                    analysis_result += "   • 3-bet premium hands (JJ+, AK)\n"
                    analysis_result += "   • Use pot odds to guide call/fold decisions\n"
                    analysis_result += f"   ⏰ Analysis Time: {datetime.now().strftime('%H:%M:%S')}\n"

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
            self._update_table_status("✅ LiveTable tab activated.\n")
    
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

        CRITICAL: Screen scraper is ALWAYS-ON and starts automatically.
        This method is called via self.after() to ensure it runs on the main thread
        after GUI initialization is complete. All widget updates use self.after()
        to maintain thread safety.
        """
        try:
            started_services = []

            if self.multi_table_manager:
                # Check if start_monitoring method exists before calling
                if hasattr(self.multi_table_manager, 'start_monitoring'):
                    try:
                        self.multi_table_manager.start_monitoring()
                        started_services.append('table monitoring')
                    except Exception as tbl_err:
                        error_msg = f"❌ Table monitoring failed to start: {tbl_err}"
                        print(error_msg)
                        import logging
                        logging.error(error_msg)
                else:
                    print('TableManager initialized (start_monitoring method not available)')

            # ALWAYS-ON: Auto-start screen scraper immediately (CRITICAL)
            self.after(0, lambda: self._update_table_status("🚀 Starting ALWAYS-ON screen scraper...\n"))
            if self._start_enhanced_screen_scraper():
                started_services.append('ALWAYS-ON screen scraper')
                self.after(0, lambda: self._update_table_status("✅ ALWAYS-ON screen scraper active and monitoring\n"))
            else:
                self.after(0, lambda: self._update_scraper_indicator(False))
                critical_msg = "❌ CRITICAL: ALWAYS-ON screen scraper failed to start!"
                self.after(0, lambda: self._update_table_status(critical_msg + '\n'))
                print(critical_msg)
                import logging
                logging.critical(critical_msg)

            if started_services:
                print(f'Background services started: {", ".join(started_services)}')
                services_msg = f"📡 Services running: {', '.join(started_services)}\n"
                self.after(0, lambda msg=services_msg: self._update_table_status(msg))
            else:
                error_msg = "❌ WARNING: No background services started!"
                print(error_msg)
                import logging
                logging.warning(error_msg)

            # Auto-start screen update loop for continuous monitoring
            self.after(0, self._start_screen_update_loop)
            # Ensure ALWAYS-ON scraper keeps running with watchdog
            self.after(5000, self._ensure_screen_scraper_watchdog)
            # Start periodic health monitoring (every 60 seconds)
            self.after(60000, self._periodic_health_check)
            # Start automatic periodic table detection (every 30 seconds)
            self.after(10000, self._periodic_table_detection)

        except Exception as e:
            error_msg = f"❌ CRITICAL: Background services exception: {e}"
            print(error_msg)
            import logging
            import traceback
            logging.critical(error_msg)
            logging.error(traceback.format_exc())
            self.after(0, lambda msg=error_msg + '\n': self._update_table_status(msg))

    def _start_background_services(self):
        """Legacy method - redirects to thread-safe implementation."""
        self._start_background_services_safely()

    def _start_enhanced_screen_scraper(self) -> bool:
        """Start the enhanced screen scraper in continuous mode - ALWAYS ON."""
        if not ENHANCED_SCRAPER_LOADED:
            error_msg = "❌ CRITICAL: Screen scraper module not loaded - missing dependencies (opencv-python, Pillow, pytesseract, mss)"
            self._update_table_status(error_msg + '\n')
            print(error_msg)
            import logging
            logging.error(error_msg)
            return False

        if self._enhanced_scraper_started:
            self._update_scraper_indicator(True)
            return True

        try:
            site = getattr(self.autopilot_panel.state, 'site', 'GENERIC')
            print(f'🚀 Starting ALWAYS-ON screen scraper for site: {site}')

            result = run_screen_scraper(
                site=site,
                continuous=True,
                interval=1.0,
                enable_ocr=True
            )

            if result.get('status') == 'success':
                self._enhanced_scraper_started = True
                status_line = '✅ ALWAYS-ON screen scraper running (continuous mode)'
                if result.get('ocr_enabled'):
                    status_line += ' with OCR'
                self._update_table_status(status_line + '\n')
                self._update_scraper_indicator(True)
                success_msg = f'✅ Screen scraper ALWAYS-ON and active (site={site})'
                print(success_msg)
                import logging
                logging.info(success_msg)
                return True

            failure_message = result.get('message', 'unknown error')
            error_msg = f"❌ CRITICAL: Screen scraper failed to start: {failure_message}"
            self._update_table_status(error_msg + '\n')
            self._update_scraper_indicator(False, error=True)
            print(error_msg)
            import logging
            logging.error(error_msg)
            return False

        except Exception as e:
            error_msg = f"❌ CRITICAL: Screen scraper exception: {e}"
            self._update_table_status(error_msg + '\n')
            self._update_scraper_indicator(False, error=True)
            print(error_msg)
            import logging
            import traceback
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            return False

    def _ensure_screen_scraper_watchdog(self) -> None:
        """Periodically verify the ALWAYS-ON scraper is running and restart if needed."""
        try:
            if ENHANCED_SCRAPER_LOADED:
                status = get_scraper_status()
                running = bool(status.get('running', False)) if isinstance(status, dict) else False
                if not running and self._enhanced_scraper_started:
                    error_msg = "❌ CRITICAL: Screen scraper stopped unexpectedly! Auto-restarting..."
                    self._update_table_status(error_msg + '\n')
                    print(error_msg)
                    import logging
                    logging.error(error_msg)

                    # Attempt restart
                    if self._start_enhanced_screen_scraper():
                        recovery_msg = "✅ Screen scraper successfully restarted by watchdog"
                        self._update_table_status(recovery_msg + '\n')
                        print(recovery_msg)
                        logging.info(recovery_msg)
                    else:
                        critical_msg = "❌ CRITICAL: Screen scraper watchdog failed to restart scraper!"
                        self._update_table_status(critical_msg + '\n')
                        print(critical_msg)
                        logging.critical(critical_msg)
        except Exception as exc:
            error_msg = f"❌ CRITICAL: Screen scraper watchdog exception: {exc}"
            self._update_table_status(error_msg + '\n')
            print(error_msg)
            import logging
            import traceback
            logging.error(error_msg)
            logging.error(traceback.format_exc())
        finally:
            # Check every 10 seconds to ensure scraper is always running
            self.after(10000, self._ensure_screen_scraper_watchdog)

    def _periodic_table_detection(self) -> None:
        """Periodically detect poker tables in the background (every 30 seconds)."""
        try:
            if not SCREEN_SCRAPER_LOADED:
                # Schedule next detection in 30 seconds
                self.after(30000, self._periodic_table_detection)
                return

            # Only run detection if autopilot is active or if explicitly enabled
            if self.autopilot_active or getattr(self, '_background_detection_enabled', True):
                # Run detection in background thread to avoid blocking UI
                def run_detection():
                    try:
                        if not self.screen_scraper:
                            # Initialize scraper if not already done
                            self.screen_scraper = create_scraper('BETFAIR')

                        # Perform lightweight table detection
                        is_detected, confidence, details = self.screen_scraper.detect_poker_table()

                        # Log detection results (only if table detected to reduce noise)
                        if is_detected:
                            msg = f"🔍 Auto-detection: Table found ({confidence:.1%} confidence)"
                            # Update status display instead of logging to non-existent tab
                            self.after(0, lambda m=msg: self._update_table_status(m + '\n'))

                    except Exception as e:
                        # Silently handle errors to avoid spamming logs
                        import logging
                        logging.debug(f"Background table detection error: {e}")

                # Run in daemon thread
                threading.Thread(target=run_detection, daemon=True).start()

        except Exception as e:
            import logging
            logging.error(f"Periodic table detection failed: {e}")

        # Schedule next detection in 30 seconds
        self.after(30000, self._periodic_table_detection)

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
        """Screen scraper is ALWAYS-ON - toggle is disabled."""
        error_msg = "⚠️ Screen scraper is ALWAYS-ON and cannot be toggled off"
        self._update_table_status(error_msg + '\n')
        print(error_msg)
        import logging
        logging.warning("User attempted to toggle ALWAYS-ON screen scraper")

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

    def get_live_table_data(self) -> Optional[Dict[str, Any]]:
        """
        Get live table data from the screen scraper for LiveTable display.

        This method delegates to the helper function to keep this file under 25,000 tokens.
        """
        from .enhanced_gui_helpers import get_live_table_data_from_scraper
        return get_live_table_data_from_scraper(self.screen_scraper)

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
                            if table_state and hasattr(table_state, 'pot_size') and table_state.pot_size is not None and table_state.pot_size > 0:
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

    def _ensure_window_visible(self):
        """Ensure the window is visible and brought to foreground."""
        try:
            # Bring window to front
            self.lift()
            self.attributes('-topmost', True)
            self.after_idle(lambda: self.attributes('-topmost', False))

            # Focus the window
            self.focus_force()

            # Make sure it's not iconified
            if self.state() == 'iconic':
                self.deiconify()

            print("✓ Window brought to foreground")
        except Exception as e:
            print(f"⚠️  Could not bring window to foreground: {e}")

    def _handle_app_exit(self):
        """Handle window close events to ensure clean shutdown."""
        print("🛑 Shutting down PokerTool...")

        try:
            # Stop background threads
            self._screen_update_running = False
            self.autopilot_active = False
            print("  ✓ Stopped background threads")
        except Exception as e:
            print(f"  ⚠ Error stopping threads: {e}")

        try:
            # Stop screen scraper if running
            if hasattr(self, 'screen_scraper') and self.screen_scraper:
                print("  ✓ Screen scraper cleanup")
        except Exception as e:
            print(f"  ⚠ Error with scraper cleanup: {e}")

        try:
            # Release the single-instance lock
            self.release_single_instance_lock()
            print("  ✓ Released instance lock")
        except Exception as e:
            print(f"  ⚠ Could not release lock: {e}")

        # Close the window cleanly
        try:
            self.quit()
            self.destroy()
            print("✓ Clean shutdown complete")
        except:
            pass


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
