#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PokerTool Simple GUI - Sidebar Navigation
==========================================

A clean, reliable GUI using sidebar navigation instead of tabs.
Works consistently across all platforms.
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Import core modules
try:
    from pokertool.enhanced_gui_components import COLORS, FONTS
    from pokertool.modules.poker_screen_scraper import create_scraper, SCREEN_SCRAPER_LOADED
    COMPONENTS_LOADED = True
except ImportError as e:
    print(f"Warning: Components not loaded: {e}")
    COMPONENTS_LOADED = False
    # Fallback colors
    COLORS = {
        'bg_dark': '#1a202c',
        'bg_medium': '#2d3748',
        'bg_light': '#4a5568',
        'text_primary': '#e2e8f0',
        'text_secondary': '#a0aec0',
        'accent_primary': '#3b82f6',
        'accent_success': '#10b981',
        'accent_warning': '#f59e0b',
        'accent_danger': '#ef4444',
    }
    FONTS = {
        'title': ('Arial', 24, 'bold'),
        'heading': ('Arial', 16, 'bold'),
        'body': ('Arial', 12),
        'small': ('Arial', 10),
    }


class SimplePokerGUI(tk.Tk):
    """Simple, reliable poker GUI with sidebar navigation."""
    
    def __init__(self):
        super().__init__()
        
        self.title("PokerTool - Simple GUI")
        self.geometry('1400x900')
        self.configure(bg=COLORS['bg_dark'])
        
        # State
        self.current_section = None
        self.sections = {}
        self.screen_scraper = None
        
        # Build UI
        self._build_ui()
        
        # Initialize scraper
        self._init_scraper()
        
        # Show first section
        self.show_section('autopilot')
        
        # Handle close
        self.protocol('WM_DELETE_WINDOW', self._on_close)
    
    def _build_ui(self):
        """Build the main UI layout."""
        # Main container
        main = tk.Frame(self, bg=COLORS['bg_dark'])
        main.pack(fill='both', expand=True)
        
        # Left sidebar
        sidebar = tk.Frame(main, bg=COLORS['bg_medium'], width=200)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # Title in sidebar
        title = tk.Label(
            sidebar,
            text="PokerTool",
            font=FONTS['title'],
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_primary'],
            pady=20
        )
        title.pack()
        
        # Navigation buttons
        nav_items = [
            ('🤖 Autopilot', 'autopilot'),
            ('🎮 Manual Play', 'manual'),
            ('📊 Analysis', 'analysis'),
            ('🎓 Coaching', 'coaching'),
            ('⚙️ Settings', 'settings'),
            ('📈 Analytics', 'analytics'),
            ('🏆 Rewards', 'rewards'),
            ('👥 Community', 'community'),
        ]
        
        self.nav_buttons = {}
        for label, section_id in nav_items:
            btn = tk.Button(
                sidebar,
                text=label,
                font=FONTS['heading'],
                bg=COLORS['bg_light'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['accent_primary'],
                activeforeground='white',
                relief='flat',
                bd=0,
                padx=20,
                pady=15,
                anchor='w',
                cursor='hand2',
                command=lambda s=section_id: self.show_section(s)
            )
            btn.pack(fill='x', padx=10, pady=5)
            self.nav_buttons[section_id] = btn
        
        # Status at bottom of sidebar
        status_frame = tk.Frame(sidebar, bg=COLORS['bg_medium'])
        status_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="● Ready",
            font=FONTS['small'],
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_success']
        )
        self.status_label.pack()
        
        # Right content area
        self.content_area = tk.Frame(main, bg=COLORS['bg_dark'])
        self.content_area.pack(side='right', fill='both', expand=True)
        
        # Build all sections
        self._build_sections()
    
    def _build_sections(self):
        """Build all content sections."""
        # Autopilot section
        self.sections['autopilot'] = self._build_autopilot_section()
        
        # Manual play section
        self.sections['manual'] = self._build_manual_section()
        
        # Analysis section
        self.sections['analysis'] = self._build_analysis_section()
        
        # Coaching section
        self.sections['coaching'] = self._build_placeholder_section('Coaching', '🎓')
        
        # Settings section
        self.sections['settings'] = self._build_placeholder_section('Settings', '⚙️')
        
        # Analytics section
        self.sections['analytics'] = self._build_placeholder_section('Analytics', '📈')
        
        # Rewards section
        self.sections['rewards'] = self._build_placeholder_section('Rewards', '🏆')
        
        # Community section
        self.sections['community'] = self._build_placeholder_section('Community', '👥')
    
    def _build_autopilot_section(self):
        """Build autopilot control section."""
        frame = tk.Frame(self.content_area, bg=COLORS['bg_dark'])
        
        # Header
        header = tk.Label(
            frame,
            text="🤖 Autopilot Control",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        header.pack(pady=20)
        
        # Control panel
        controls = tk.Frame(frame, bg=COLORS['bg_medium'], relief='ridge', bd=2)
        controls.pack(fill='x', padx=20, pady=10)
        
        # Start/Stop button
        self.autopilot_button = tk.Button(
            controls,
            text="▶ Start Autopilot",
            font=FONTS['heading'],
            bg=COLORS['accent_success'],
            fg='white',
            activebackground=COLORS['accent_primary'],
            pady=15,
            cursor='hand2',
            command=self._toggle_autopilot
        )
        self.autopilot_button.pack(fill='x', padx=20, pady=20)
        
        # Status display
        status_frame = tk.Frame(frame, bg=COLORS['bg_medium'], relief='ridge', bd=2)
        status_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(
            status_frame,
            text="📊 Autopilot Status",
            font=FONTS['heading'],
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_primary']
        ).pack(pady=10)
        
        self.autopilot_status = tk.Text(
            status_frame,
            font=FONTS['body'],
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            wrap='word',
            height=20
        )
        self.autopilot_status.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(self.autopilot_status)
        scrollbar.pack(side='right', fill='y')
        self.autopilot_status.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.autopilot_status.yview)
        
        self._log_autopilot("Autopilot ready. Click 'Start' to begin.")
        
        return frame
    
    def _build_manual_section(self):
        """Build manual play section."""
        frame = tk.Frame(self.content_area, bg=COLORS['bg_dark'])
        
        # Header
        header = tk.Label(
            frame,
            text="🎮 Manual Play",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        header.pack(pady=20)
        
        # Content
        info = tk.Label(
            frame,
            text="Manual play workspace\n\nUse this section to manually input hands\nand get real-time analysis.",
            font=FONTS['body'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_secondary'],
            justify='center'
        )
        info.pack(expand=True)
        
        return frame
    
    def _build_analysis_section(self):
        """Build analysis section."""
        frame = tk.Frame(self.content_area, bg=COLORS['bg_dark'])
        
        # Header
        header = tk.Label(
            frame,
            text="📊 Hand Analysis",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        header.pack(pady=20)
        
        # Analysis display
        analysis_frame = tk.Frame(frame, bg=COLORS['bg_medium'], relief='ridge', bd=2)
        analysis_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.analysis_output = tk.Text(
            analysis_frame,
            font=FONTS['body'],
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            wrap='word'
        )
        self.analysis_output.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.analysis_output.insert('1.0', "Analysis results will appear here...")
        
        return frame
    
    def _build_placeholder_section(self, title: str, icon: str):
        """Build a placeholder section."""
        frame = tk.Frame(self.content_area, bg=COLORS['bg_dark'])
        
        # Header
        header = tk.Label(
            frame,
            text=f"{icon} {title}",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        header.pack(pady=20)
        
        # Placeholder content
        info = tk.Label(
            frame,
            text=f"{title} section\n\nComing soon...",
            font=FONTS['body'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_secondary'],
            justify='center'
        )
        info.pack(expand=True)
        
        return frame
    
    def show_section(self, section_id: str):
        """Show a specific section."""
        # Hide current section
        if self.current_section and self.current_section in self.sections:
            self.sections[self.current_section].pack_forget()
        
        # Show new section
        if section_id in self.sections:
            self.sections[section_id].pack(fill='both', expand=True)
            self.current_section = section_id
            
            # Update navigation buttons
            for sid, btn in self.nav_buttons.items():
                if sid == section_id:
                    btn.config(
                        bg=COLORS['accent_primary'],
                        fg='white',
                        relief='sunken'
                    )
                else:
                    btn.config(
                        bg=COLORS['bg_light'],
                        fg=COLORS['text_primary'],
                        relief='flat'
                    )
    
    def _init_scraper(self):
        """Initialize screen scraper."""
        try:
            if COMPONENTS_LOADED:
                self.screen_scraper = create_scraper('BETFAIR')
                self._log_autopilot("✓ Screen scraper initialized")
        except Exception as e:
            self._log_autopilot(f"⚠ Screen scraper unavailable: {e}")
    
    def _toggle_autopilot(self):
        """Toggle autopilot on/off."""
        if self.autopilot_button.cget('text').startswith('▶'):
            # Start autopilot
            self.autopilot_button.config(
                text="⏸ Stop Autopilot",
                bg=COLORS['accent_danger']
            )
            self._log_autopilot("\n" + "="*60)
            self._log_autopilot("🚀 AUTOPILOT STARTED")
            self._log_autopilot("="*60 + "\n")
            self._start_autopilot()
        else:
            # Stop autopilot
            self.autopilot_button.config(
                text="▶ Start Autopilot",
                bg=COLORS['accent_success']
            )
            self._log_autopilot("\n" + "="*60)
            self._log_autopilot("⏹ AUTOPILOT STOPPED")
            self._log_autopilot("="*60 + "\n")
            self._stop_autopilot()
    
    def _start_autopilot(self):
        """Start autopilot monitoring."""
        self.autopilot_active = True
        threading.Thread(target=self._autopilot_loop, daemon=True).start()
    
    def _stop_autopilot(self):
        """Stop autopilot monitoring."""
        self.autopilot_active = False
    
    def _autopilot_loop(self):
        """Autopilot monitoring loop."""
        while self.autopilot_active:
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                self._log_autopilot(f"[{timestamp}] Monitoring for poker tables...")
                
                if self.screen_scraper:
                    # Try to detect table
                    try:
                        state = self.screen_scraper.analyze_table()
                        if state and state.active_players > 0:
                            self._log_autopilot(f"  ✓ Table detected: {state.active_players} players, pot ${state.pot_size}")
                        else:
                            self._log_autopilot("  ○ No active table detected")
                    except Exception as e:
                        self._log_autopilot(f"  ⚠ Detection error: {e}")
                
                time.sleep(3)
            except Exception as e:
                self._log_autopilot(f"⚠ Autopilot error: {e}")
                time.sleep(5)
    
    def _log_autopilot(self, message: str):
        """Add message to autopilot log."""
        def update():
            self.autopilot_status.insert('end', message + '\n')
            self.autopilot_status.see('end')
        
        self.after(0, update)
    
    def _on_close(self):
        """Handle window close."""
        self.autopilot_active = False
        self.quit()
        self.destroy()


def main():
    """Launch the simple GUI."""
    print("="*60)
    print("PokerTool - Simple GUI")
    print("="*60)
    print("\nLaunching...")
    
    app = SimplePokerGUI()
    app.mainloop()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
