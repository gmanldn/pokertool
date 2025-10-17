#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Status Window
=======================

Simple status window for macOS dock icon that shows:
- App loading status
- Current activity
- Detected tables
- Real-time updates from backend

Module: pokertool.status_window
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from typing import Optional
import threading
import requests
import json


class StatusWindow:
    """Status window for displaying app status and detected tables."""

    def __init__(self, api_url: str = "http://localhost:5001"):
        self.api_url = api_url
        self.window: Optional[tk.Tk] = None
        self.is_visible = False
        self.update_thread: Optional[threading.Thread] = None
        self.should_update = False

    def create_window(self):
        """Create the status window."""
        if self.window is not None:
            return

        self.window = tk.Tk()
        self.window.title("PokerTool Status")
        self.window.geometry("500x600")

        # Make it stay on top
        self.window.attributes('-topmost', True)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Title
        title = ttk.Label(main_frame, text="🎰 PokerTool Status",
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)

        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Application Status",
                                     padding="5")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        status_frame.columnconfigure(1, weight=1)

        # Backend status
        ttk.Label(status_frame, text="Backend API:").grid(row=0, column=0,
                                                          sticky=tk.W, padx=5)
        self.backend_status = ttk.Label(status_frame, text="Checking...",
                                       foreground="gray")
        self.backend_status.grid(row=0, column=1, sticky=tk.W, padx=5)

        # Frontend status
        ttk.Label(status_frame, text="Frontend:").grid(row=1, column=0,
                                                       sticky=tk.W, padx=5)
        self.frontend_status = ttk.Label(status_frame, text="Checking...",
                                        foreground="gray")
        self.frontend_status.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Scraper status
        ttk.Label(status_frame, text="Screen Scraper:").grid(row=2, column=0,
                                                             sticky=tk.W, padx=5)
        self.scraper_status = ttk.Label(status_frame, text="Checking...",
                                       foreground="gray")
        self.scraper_status.grid(row=2, column=1, sticky=tk.W, padx=5)

        # Detection Section
        detection_frame = ttk.LabelFrame(main_frame, text="Table Detection",
                                        padding="5")
        detection_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        detection_frame.columnconfigure(1, weight=1)

        # Last detection
        ttk.Label(detection_frame, text="Last Detection:").grid(row=0, column=0,
                                                               sticky=tk.W, padx=5)
        self.last_detection = ttk.Label(detection_frame, text="None",
                                       foreground="gray")
        self.last_detection.grid(row=0, column=1, sticky=tk.W, padx=5)

        # Detected table
        ttk.Label(detection_frame, text="Table Name:").grid(row=1, column=0,
                                                           sticky=tk.W, padx=5)
        self.table_name = ttk.Label(detection_frame, text="N/A",
                                    foreground="gray")
        self.table_name.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Activity Log
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="5")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # Scrolled text for log
        self.activity_log = scrolledtext.ScrolledText(log_frame,
                                                      height=15,
                                                      width=50,
                                                      wrap=tk.WORD,
                                                      font=('Courier', 10))
        self.activity_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        ttk.Button(button_frame, text="Refresh",
                  command=self.refresh_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Log",
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close",
                  command=self.hide).pack(side=tk.RIGHT, padx=5)

        # Initial log message
        self.log("Status window initialized")
        self.log(f"Backend API: {self.api_url}")

    def show(self):
        """Show the status window."""
        if self.window is None:
            self.create_window()

        self.window.deiconify()
        self.window.lift()
        self.is_visible = True

        # Start update thread
        if not self.should_update:
            self.should_update = True
            self.update_thread = threading.Thread(target=self._update_loop,
                                                  daemon=True)
            self.update_thread.start()

        # Initial refresh
        self.refresh_status()

    def hide(self):
        """Hide the status window."""
        if self.window:
            self.window.withdraw()
            self.is_visible = False

    def toggle(self):
        """Toggle status window visibility."""
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def log(self, message: str):
        """Add a message to the activity log."""
        if not self.window:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        self.activity_log.insert(tk.END, log_message)
        self.activity_log.see(tk.END)

    def clear_log(self):
        """Clear the activity log."""
        if self.activity_log:
            self.activity_log.delete(1.0, tk.END)

    def refresh_status(self):
        """Refresh all status information."""
        self.log("Refreshing status...")

        # Check backend API
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            if response.status_code == 200:
                self.backend_status.config(text="✓ Running", foreground="green")
                self.log("Backend API: Running")
            else:
                self.backend_status.config(text="✗ Error", foreground="red")
                self.log(f"Backend API: Error {response.status_code}")
        except Exception as e:
            self.backend_status.config(text="✗ Offline", foreground="red")
            self.log(f"Backend API: Offline ({str(e)[:50]})")

        # Check frontend
        try:
            response = requests.get("http://localhost:3000", timeout=2)
            if response.status_code in [200, 304]:
                self.frontend_status.config(text="✓ Running", foreground="green")
                self.log("Frontend: Running")
            else:
                self.frontend_status.config(text="? Unknown", foreground="orange")
        except Exception:
            self.frontend_status.config(text="✗ Offline", foreground="red")
            self.log("Frontend: Offline")

        # Check for recent detections
        try:
            response = requests.get(f"{self.api_url}/api/status", timeout=2)
            if response.status_code == 200:
                data = response.json()

                # Update scraper status
                scraper_active = data.get('scraper_active', False)
                if scraper_active:
                    self.scraper_status.config(text="✓ Active", foreground="green")
                else:
                    self.scraper_status.config(text="○ Idle", foreground="gray")

                # Update detection info
                last_detection = data.get('last_detection')
                if last_detection:
                    self.last_detection.config(text=last_detection,
                                              foreground="black")
                    self.log(f"Last detection: {last_detection}")

                table_name = data.get('table_name', 'N/A')
                if table_name != 'N/A':
                    self.table_name.config(text=table_name, foreground="black")
                    self.log(f"Detected table: {table_name}")

        except Exception as e:
            self.log(f"Could not fetch status: {str(e)[:50]}")

    def _update_loop(self):
        """Background thread to periodically update status."""
        import time

        while self.should_update:
            if self.is_visible:
                try:
                    self.window.after(0, self.refresh_status)
                except:
                    pass
            time.sleep(5)  # Update every 5 seconds

    def run(self):
        """Run the status window (blocking)."""
        if self.window is None:
            self.create_window()
        self.show()
        self.window.mainloop()

    def stop(self):
        """Stop the status window and cleanup."""
        self.should_update = False
        if self.window:
            self.window.destroy()
            self.window = None


def main():
    """Test the status window."""
    window = StatusWindow()
    window.run()


if __name__ == "__main__":
    main()
