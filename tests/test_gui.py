#!/usr/bin/env python3
"""
Minimal test GUI for PokerTool to verify basic functionality
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# Add src to Python path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

try:
    from pokertool.enhanced_gui_components.style import COLORS, FONTS
    print("✓ Successfully imported COLORS and FONTS")
except ImportError as e:
    print(f"Warning: Could not import style: {e}")
    # Fallback colors and fonts
    COLORS = {
        'bg_dark': '#1a1f2e',
        'bg_medium': '#2a3142', 
        'bg_light': '#3a4152',
        'text_primary': '#ffffff',
        'accent_primary': '#4a9eff'
    }
    FONTS = {
        'title': ('Arial', 20, 'bold'),
        'body': ('Arial', 12),
    }

class MinimalPokerGUI(tk.Tk):
    """Minimal PokerTool GUI for testing."""
    
    def __init__(self):
        super().__init__()
        
        self.title("PokerTool - Test GUI")
        self.geometry("800x600")
        self.configure(bg=COLORS['bg_dark'])
        
        # Create main frame
        main_frame = tk.Frame(self, bg=COLORS['bg_dark'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="PokerTool Test GUI",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        title_label.pack(pady=20)
        
        # Create notebook with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Test tabs
        self._create_test_tabs()
        
        print("✓ Minimal GUI initialized successfully")
    
    def _create_test_tabs(self):
        """Create test tabs."""
        tabs = [
            ("Autopilot", self._create_autopilot_tab),
            ("Manual", self._create_manual_tab),
            ("Analysis", self._create_analysis_tab),
            ("Settings", self._create_settings_tab)
        ]
        
        for tab_name, builder in tabs:
            try:
                frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
                builder(frame)
                self.notebook.add(frame, text=tab_name)
                print(f"✓ Created {tab_name} tab")
            except Exception as e:
                print(f"✗ Failed to create {tab_name} tab: {e}")
                # Create fallback tab
                frame = tk.Frame(self.notebook, bg=COLORS['bg_dark'])
                error_label = tk.Label(
                    frame,
                    text=f"{tab_name} Tab Error:\n{str(e)}",
                    font=FONTS['body'],
                    bg=COLORS['bg_dark'],
                    fg='red',
                    justify='left'
                )
                error_label.pack(expand=True)
                self.notebook.add(frame, text=f"{tab_name} (Error)")
    
    def _create_autopilot_tab(self, parent):
        """Create autopilot test tab."""
        tk.Label(
            parent,
            text="Autopilot Control Center",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(pady=20)
        
        # Control button
        control_button = tk.Button(
            parent,
            text="Start Autopilot",
            font=FONTS['body'],
            bg=COLORS['accent_primary'],
            fg='white',
            padx=20,
            pady=10
        )
        control_button.pack(pady=20)
        
        # Status display
        status_frame = tk.LabelFrame(
            parent,
            text="Status",
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        status_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(
            status_frame,
            text="Status: Ready",
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(pady=10)
    
    def _create_manual_tab(self, parent):
        """Create manual test tab."""
        tk.Label(
            parent,
            text="Manual Play Controls",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(pady=20)
        
        # Test controls
        controls_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        controls_frame.pack(expand=True)
        
        buttons = ["Fold", "Call", "Raise", "All-In"]
        for button_text in buttons:
            tk.Button(
                controls_frame,
                text=button_text,
                font=FONTS['body'],
                width=10
            ).pack(side='left', padx=5, pady=5)
    
    def _create_analysis_tab(self, parent):
        """Create analysis test tab."""
        tk.Label(
            parent,
            text="Hand Analysis",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(pady=20)
        
        # Analysis output
        text_widget = tk.Text(
            parent,
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            font=('Courier', 10),
            wrap='word'
        )
        text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        
        text_widget.insert('1.0', "Analysis results will appear here...\n")
        text_widget.config(state='disabled')
    
    def _create_settings_tab(self, parent):
        """Create settings test tab."""
        tk.Label(
            parent,
            text="PokerTool Settings",
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        ).pack(pady=20)
        
        # Settings form
        settings_frame = tk.LabelFrame(
            parent,
            text="Configuration",
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        settings_frame.pack(fill='x', padx=20, pady=20)
        
        # Sample settings
        tk.Checkbutton(
            settings_frame,
            text="Auto-detect tables",
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light']
        ).pack(anchor='w', padx=10, pady=5)
        
        tk.Checkbutton(
            settings_frame,
            text="Sound alerts",
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary'],
            selectcolor=COLORS['bg_light']
        ).pack(anchor='w', padx=10, pady=5)

def main():
    """Run the minimal test GUI."""
    print("🧪 Starting PokerTool Test GUI...")
    
    try:
        app = MinimalPokerGUI()
        print("✅ GUI created successfully, starting main loop...")
        app.mainloop()
        print("✅ GUI closed normally")
        return 0
    except Exception as e:
        print(f"❌ GUI error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
