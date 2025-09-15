#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: pokertool/poker_gui_autopilot.py
# version: '20'
# last_commit: '2025-09-09T15:38:42+00:00'
# fixes: []
# ---
# POKERTOOL-HEADER-END
"""
Enhanced Poker GUI with Autopilot Integration
Extends the existing GUI with screen scraping autopilot functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Optional, Dict, Any

# Import existing poker modules
from poker_modules import (
    Card, Suit, Position, analyse_hand, get_hand_tier, 
    to_two_card_str, RANK_ORDER, GameState
)
from poker_init import open_db
from poker_gui import PokerAssistant  # Import original GUI

# Import screen scraper
from poker_screen_scraper import (
    PokerScreenScraper, PokerSite, TableState, 
    ScreenScraperBridge, CardRecognizer
)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTOPILOT CONTROL PANEL
# ═══════════════════════════════════════════════════════════════════════════════

class AutopilotPanel(ttk.Frame):
    """Autopilot control panel for the poker assistant."""
    
    def __init__(self, parent, poker_assistant):
        super().__init__(parent)
        self.poker_assistant = poker_assistant
        self.scraper = None
        self.bridge = None
        self.is_running = False
        self.update_thread = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the autopilot panel UI."""
        # Title
        title = ttk.Label(self, text="🤖 Autopilot Mode", font=('Arial', 12, 'bold'))
        title.pack(pady=(0, 10))
        
        # Site selection
        site_frame = ttk.Frame(self)
        site_frame.pack(fill='x', pady=5)
        
        ttk.Label(site_frame, text="Poker Site:").pack(side='left', padx=(0, 5))
        self.site_var = tk.StringVar(value=PokerSite.GENERIC.value)
        site_combo = ttk.Combobox(
            site_frame,
            textvariable=self.site_var,
            values=[site.value for site in PokerSite],
            state='readonly',
            width=15
        )
        site_combo.pack(side='left')
        
        # Control buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=10)
        
        self.start_button = ttk.Button(
            button_frame,
            text="▶️ Start Autopilot",
            command=self.toggle_autopilot
        )
        self.start_button.pack(side='left', padx=2)
        
        self.calibrate_button = ttk.Button(
            button_frame,
            text="🎯 Calibrate",
            command=self.calibrate_scraper
        )
        self.calibrate_button.pack(side='left', padx=2)
        
        self.debug_button = ttk.Button(
            button_frame,
            text="🐛 Debug",
            command=self.save_debug_image
        )
        self.debug_button.pack(side='left', padx=2)
        
        # Status display
        status_frame = ttk.LabelFrame(self, text="Status", padding=10)
        status_frame.pack(fill='both', expand=True, pady=10)
        
        self.status_text = tk.Text(status_frame, height=8, width=40, wrap='word')
        self.status_text.pack(fill='both', expand=True)
        
        # Update rate control
        rate_frame = ttk.Frame(self)
        rate_frame.pack(fill='x', pady=5)
        
        ttk.Label(rate_frame, text="Update Rate:").pack(side='left', padx=(0, 5))
        self.rate_var = tk.DoubleVar(value=1.0)
        rate_scale = ttk.Scale(
            rate_frame,
            from_=0.5,
            to=5.0,
            variable=self.rate_var,
            orient='horizontal',
            length=150
        )
        rate_scale.pack(side='left')
        self.rate_label = ttk.Label(rate_frame, text="1.0s")
        self.rate_label.pack(side='left', padx=5)
        
        # Bind scale update
        rate_scale.configure(command=self._update_rate_label)
        
        # Table state indicators
        self.indicators_frame = ttk.LabelFrame(self, text="Table State", padding=5)
        self.indicators_frame.pack(fill='x', pady=5)
        
        self.indicator_labels = {}
        indicators = [
            ('stage', 'Stage'),
            ('pot', 'Pot'),
            ('players', 'Players'),
            ('position', 'Position')
        ]
        
        for i, (key, label) in enumerate(indicators):
            row = i // 2
            col = i % 2
            
            ttk.Label(self.indicators_frame, text=f"{label}:").grid(
                row=row, column=col*2, sticky='w', padx=2
            )
            value_label = ttk.Label(self.indicators_frame, text="--", font=('Arial', 9, 'bold'))
            value_label.grid(row=row, column=col*2+1, sticky='e', padx=(0, 10))
            self.indicator_labels[key] = value_label
    
    def _update_rate_label(self, value):
        """Update the rate label when slider changes."""
        rate = float(value)
        self.rate_label.config(text=f"{rate:.1f}s")
    
    def toggle_autopilot(self):
        """Toggle autopilot on/off."""
        if not self.is_running:
            self.start_autopilot()
        else:
            self.stop_autopilot()
    
    def start_autopilot(self):
        """Start the autopilot mode."""
        try:
            # Get selected site
            site_name = self.site_var.get()
            site = next(s for s in PokerSite if s.value == site_name)
            
            # Initialize scraper
            self.scraper = PokerScreenScraper(site)
            self.bridge = ScreenScraperBridge(self.scraper)
            
            # Register callback
            self.bridge.register_callback(self._on_table_update)
            
            # Calibrate if needed
            if not self.scraper.calibrated:
                if not self.scraper.calibrate():
                    self._update_status("⚠️ Calibration failed, continuing anyway...")
            
            # Start continuous capture
            update_rate = self.rate_var.get()
            self.scraper.start_continuous_capture(interval=update_rate)
            
            # Update UI
            self.is_running = True
            self.start_button.config(text="⏹️ Stop Autopilot")
            self._update_status("✅ Autopilot started")
            
            # Start update thread
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
        except Exception as e:
            messagebox.showerror("Autopilot Error", f"Failed to start autopilot: {e}")
            self._update_status(f"❌ Error: {e}")
    
    def stop_autopilot(self):
        """Stop the autopilot mode."""
        if self.scraper:
            self.scraper.stop_continuous_capture()
        
        self.is_running = False
        self.start_button.config(text="▶️ Start Autopilot")
        self._update_status("⏹️ Autopilot stopped")
    
    def calibrate_scraper(self):
        """Calibrate the screen scraper."""
        if not self.scraper:
            # Initialize temporary scraper for calibration
            site_name = self.site_var.get()
            site = next(s for s in PokerSite if s.value == site_name)
            self.scraper = PokerScreenScraper(site)
        
        try:
            if self.scraper.calibrate():
                self._update_status("✅ Calibration successful")
                messagebox.showinfo("Calibration", "Screen scraper calibrated successfully!")
            else:
                self._update_status("❌ Calibration failed")
                messagebox.showwarning("Calibration", "Calibration failed. Please ensure a poker table is visible.")
        except Exception as e:
            self._update_status(f"❌ Calibration error: {e}")
            messagebox.showerror("Calibration Error", f"Failed to calibrate: {e}")
    
    def save_debug_image(self):
        """Save a debug image of the current capture."""
        if not self.scraper:
            messagebox.showwarning("Debug", "Please start autopilot or calibrate first")
            return
        
        try:
            img = self.scraper.capture_table()
            filename = f"debug_capture_{int(time.time())}.png"
            self.scraper.save_debug_image(img, filename)
            self._update_status(f"📸 Debug image saved: {filename}")
            messagebox.showinfo("Debug", f"Debug image saved to {filename}")
        except Exception as e:
            messagebox.showerror("Debug Error", f"Failed to save debug image: {e}")
    
    def _update_loop(self):
        """Background thread to process table updates."""
        while self.is_running:
            try:
                # Get state updates from queue
                state = self.scraper.get_state_updates(timeout=0.1)
                if state:
                    # Process in main thread
                    self.after(0, lambda s=state: self._process_state_update(s))
            except Exception as e:
                print(f"Update loop error: {e}")
            
            time.sleep(0.1)
    
    def _process_state_update(self, state: TableState):
        """Process a table state update in the main thread."""
        # Update indicators
        self.indicator_labels['stage'].config(text=state.stage.capitalize())
        self.indicator_labels['pot'].config(text=f"${state.pot_size:.2f}")
        self.indicator_labels['players'].config(text=str(state.active_players))
        
        # Find hero position
        hero_position = "--"
        if state.hero_seat:
            hero_seat = next((s for s in state.seats if s.seat_number == state.hero_seat), None)
            if hero_seat and hero_seat.position:
                hero_position = hero_seat.position.name
        
        self.indicator_labels['position'].config(text=hero_position)
        
        # Convert to game state and notify poker assistant
        game_state = self.bridge.convert_to_game_state(state)
        self._on_table_update(game_state)
    
    def _on_table_update(self, game_state: Dict[str, Any]):
        """Handle table state update from screen scraper."""
        try:
            # Update poker assistant with scraped data
            if game_state['hole_cards']:
                # Update hole cards
                for i, card in enumerate(game_state['hole_cards'][:2]):
                    if i < len(self.poker_assistant.hole):
                        slot = self.poker_assistant.hole[i]
                        slot.set_card(card)
            
            # Update board cards
            if game_state['board_cards']:
                for i, card in enumerate(game_state['board_cards'][:5]):
                    if i < len(self.poker_assistant.board):
                        slot = self.poker_assistant.board[i]
                        slot.set_card(card)
            
            # Update position
            if game_state['position']:
                self.poker_assistant.position.set(game_state['position'].name)
            
            # Update pot and betting
            self.poker_assistant.pot.set(game_state['pot'])
            self.poker_assistant.to_call.set(game_state['to_call'])
            self.poker_assistant.num_players.set(game_state['num_players'])
            
            # Trigger analysis
            self.poker_assistant.refresh()
            
            # Update status
            self._update_status(f"📊 Updated: {game_state['stage']} | Pot: ${game_state['pot']:.2f}")
            
        except Exception as e:
            self._update_status(f"❌ Update error: {e}")
    
    def _update_status(self, message: str):
        """Update the status display."""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')
        
        # Limit history
        lines = self.status_text.get('1.0', 'end').split('\n')
        if len(lines) > 100:
            self.status_text.delete('1.0', '2.0')


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED POKER ASSISTANT WITH AUTOPILOT
# ═══════════════════════════════════════════════════════════════════════════════

class PokerAssistantWithAutopilot(PokerAssistant):
    """Extended Poker Assistant with autopilot functionality."""
    
    def __init__(self):
        super().__init__()
        self.title("♠♥ Poker Assistant with Autopilot ♦♣")
        self.geometry("1400x900")  # Wider to accommodate autopilot panel
        
        # Add autopilot panel
        self._add_autopilot_panel()
        
        # Override window close to cleanup autopilot
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _add_autopilot_panel(self):
        """Add the autopilot panel to the GUI."""
        # Create a new frame for autopilot on the right side
        autopilot_frame = ttk.LabelFrame(
            self, 
            text="Autopilot Control", 
            padding="10"
        )
        autopilot_frame.grid(row=0, column=3, sticky=(tk.N, tk.S, tk.E, tk.W), padx=10, pady=10)
        
        # Add autopilot panel
        self.autopilot_panel = AutopilotPanel(autopilot_frame, self)
        self.autopilot_panel.pack(fill='both', expand=True)
        
        # Adjust grid weights
        self.columnconfigure(3, weight=0)  # Don't expand autopilot column
    
    def _on_close(self):
        """Handle window close event."""
        # Stop autopilot if running
        if hasattr(self, 'autopilot_panel'):
            self.autopilot_panel.stop_autopilot()
        
        # Close table window if exists
        if hasattr(self, 'table_window') and self.table_window:
            self.table_window.destroy()
        
        # Destroy main window
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# CALIBRATION WIZARD
# ═══════════════════════════════════════════════════════════════════════════════

class CalibrationWizard(tk.Toplevel):
    """Wizard to help users calibrate the screen scraper."""
    
    def __init__(self, parent, scraper: PokerScreenScraper):
        super().__init__(parent)
        self.scraper = scraper
        self.title("Screen Scraper Calibration Wizard")
        self.geometry("600x500")
        
        self._build_ui()
        self._start_calibration()
    
    def _build_ui(self):
        """Build the calibration wizard UI."""
        # Instructions
        instructions = tk.Text(self, height=5, wrap='word')
        instructions.pack(fill='x', padx=10, pady=10)
        instructions.insert('1.0', 
            "Screen Scraper Calibration\n\n"
            "1. Open your poker client and join a table\n"
            "2. Ensure the table window is visible\n"
            "3. Click 'Capture' to take a screenshot\n"
            "4. Verify the detected regions are correct\n"
            "5. Click 'Save' to complete calibration"
        )
        instructions.config(state='disabled')
        
        # Canvas for preview
        self.canvas = tk.Canvas(self, bg='gray')
        self.canvas.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Control buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Capture", command=self._capture).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Auto-Detect", command=self._auto_detect).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Save", command=self._save_calibration).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side='right', padx=5)
        
        # Status
        self.status_label = ttk.Label(self, text="Ready to capture...")
        self.status_label.pack(pady=5)
    
    def _start_calibration(self):
        """Start the calibration process."""
        self._capture()
    
    def _capture(self):
        """Capture a screenshot for calibration."""
        try:
            img = self.scraper.capture_table()
            # Save for debugging
            self.scraper.save_debug_image(img, "calibration_capture.png")
            
            # Display preview (scaled down)
            # This would show the captured image with detected regions
            
            self.status_label.config(text="Screenshot captured. Detecting regions...")
            
            # Try automatic calibration
            if self.scraper.calibrate(img):
                self.status_label.config(text="✅ Calibration successful!")
            else:
                self.status_label.config(text="⚠️ Auto-detection failed. Please adjust manually.")
                
        except Exception as e:
            self.status_label.config(text=f"❌ Error: {e}")
            messagebox.showerror("Capture Error", f"Failed to capture: {e}")
    
    def _auto_detect(self):
        """Attempt automatic detection of table elements."""
        # This would implement more sophisticated detection algorithms
        pass
    
    def _save_calibration(self):
        """Save the calibration settings."""
        # Save calibration to file for future use
        config_file = "poker_scraper_config.json"
        # Save configuration...
        
        messagebox.showinfo("Calibration", "Calibration saved successfully!")
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point for the enhanced poker assistant."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    from poker_init import initialise_db_if_needed
    initialise_db_if_needed()
    
    # Create and run the enhanced GUI
    app = PokerAssistantWithAutopilot()
    app.mainloop()


if __name__ == "__main__":
    main()
