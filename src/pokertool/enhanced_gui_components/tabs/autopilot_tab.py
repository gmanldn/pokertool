#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Autopilot Tab for Enhanced PokerTool GUI
========================================

This module provides the autopilot tab functionality for the enhanced GUI.

Module: pokertool.enhanced_gui_components.tabs.autopilot_tab
Version: 1.0.0
Author: PokerTool Development Team
License: MIT
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class AutopilotTabMixin:
    """Autopilot tab mixin for the enhanced PokerTool GUI."""
    
    def setup_autopilot_tab(self, parent):
        """Set up the autopilot tab interface.
        
        Args:
            parent: Parent widget
        """
        # Create the autopilot frame
        self.autopilot_frame = ttk.Frame(parent)
        
        # Title
        title_label = ttk.Label(self.autopilot_frame, text="Automated Play Settings", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Status section
        status_frame = ttk.LabelFrame(self.autopilot_frame, text="Autopilot Status", padding=10)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # Status display
        self.autopilot_status_frame = ttk.Frame(status_frame)
        self.autopilot_status_frame.pack(fill='x')
        
        self.autopilot_enabled = tk.BooleanVar(value=False)
        self.autopilot_status_label = ttk.Label(self.autopilot_status_frame, text="Status: DISABLED", 
                                              font=('Arial', 12, 'bold'), foreground='red')
        self.autopilot_status_label.pack(side='left')
        
        # Control buttons
        control_frame = ttk.Frame(status_frame)
        control_frame.pack(fill='x', pady=(10, 0))
        
        self.autopilot_toggle_btn = ttk.Button(control_frame, text="Enable Autopilot", 
                                             command=self.toggle_autopilot)
        self.autopilot_toggle_btn.pack(side='left', padx=(0, 10))
        
        ttk.Button(control_frame, text="Emergency Stop", 
                  command=self.emergency_stop, state='disabled').pack(side='left')
        
        # Settings section
        settings_frame = ttk.LabelFrame(self.autopilot_frame, text="Autopilot Settings", padding=10)
        settings_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # Strategy selection
        strategy_frame = ttk.Frame(settings_frame)
        strategy_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(strategy_frame, text="Playing Strategy:").pack(side='left')
        self.autopilot_strategy = tk.StringVar(value="Conservative")
        strategy_combo = ttk.Combobox(strategy_frame, textvariable=self.autopilot_strategy, 
                                    values=["Conservative", "Balanced", "Aggressive", "Custom"],
                                    state='readonly', width=15)
        strategy_combo.pack(side='left', padx=(10, 0))
        
        # Betting limits
        limits_frame = ttk.LabelFrame(settings_frame, text="Betting Limits", padding=5)
        limits_frame.pack(fill='x', pady=(10, 0))
        
        # Max bet limit
        max_bet_frame = ttk.Frame(limits_frame)
        max_bet_frame.pack(fill='x', pady=2)
        
        ttk.Label(max_bet_frame, text="Max Bet:").pack(side='left', padx=(0, 10))
        self.autopilot_max_bet = tk.StringVar(value="50")
        max_bet_spin = tk.Spinbox(max_bet_frame, from_=1, to=1000, textvariable=self.autopilot_max_bet, 
                                width=10)
        max_bet_spin.pack(side='left')
        
        # Session limit
        session_limit_frame = ttk.Frame(limits_frame)
        session_limit_frame.pack(fill='x', pady=2)
        
        ttk.Label(session_limit_frame, text="Session Limit:").pack(side='left', padx=(0, 10))
        self.autopilot_session_limit = tk.StringVar(value="500")
        session_limit_spin = tk.Spinbox(session_limit_frame, from_=10, to=10000, 
                                      textvariable=self.autopilot_session_limit, width=10)
        session_limit_spin.pack(side='left')
        
        # Safety settings
        safety_frame = ttk.LabelFrame(settings_frame, text="Safety Settings", padding=5)
        safety_frame.pack(fill='x', pady=(10, 0))
        
        self.autopilot_stop_on_loss = tk.BooleanVar(value=True)
        ttk.Checkbutton(safety_frame, text="Stop on significant loss", 
                       variable=self.autopilot_stop_on_loss).pack(anchor='w')
        
        self.autopilot_human_takeover = tk.BooleanVar(value=True)
        ttk.Checkbutton(safety_frame, text="Allow human takeover", 
                       variable=self.autopilot_human_takeover).pack(anchor='w')
        
        # Performance metrics
        metrics_frame = ttk.LabelFrame(settings_frame, text="Current Session", padding=5)
        metrics_frame.pack(fill='x', pady=(10, 0))
        
        self.autopilot_metrics = {
            'hands_played': tk.StringVar(value="0"),
            'profit_loss': tk.StringVar(value="$0.00"),
            'win_rate': tk.StringVar(value="0.00%"),
            'time_active': tk.StringVar(value="00:00:00")
        }
        
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill='x')
        
        ttk.Label(metrics_grid, text="Hands:").grid(row=0, column=0, sticky='w')
        ttk.Label(metrics_grid, textvariable=self.autopilot_metrics['hands_played']).grid(row=0, column=1, sticky='w', padx=(10, 20))
        
        ttk.Label(metrics_grid, text="P/L:").grid(row=0, column=2, sticky='w')
        ttk.Label(metrics_grid, textvariable=self.autopilot_metrics['profit_loss']).grid(row=0, column=3, sticky='w', padx=(10, 0))
        
        ttk.Label(metrics_grid, text="Win Rate:").grid(row=1, column=0, sticky='w')
        ttk.Label(metrics_grid, textvariable=self.autopilot_metrics['win_rate']).grid(row=1, column=1, sticky='w', padx=(10, 20))
        
        ttk.Label(metrics_grid, text="Active:").grid(row=1, column=2, sticky='w')
        ttk.Label(metrics_grid, textvariable=self.autopilot_metrics['time_active']).grid(row=1, column=3, sticky='w', padx=(10, 0))
        
        return self.autopilot_frame
    
    def toggle_autopilot(self):
        """Toggle autopilot on/off."""
        try:
            current_state = self.autopilot_enabled.get()
            if not current_state:
                # Enable autopilot
                self.autopilot_enabled.set(True)
                self.autopilot_status_label.config(text="Status: ENABLED", foreground='green')
                self.autopilot_toggle_btn.config(text="Disable Autopilot")
                logger.info("Autopilot enabled")
            else:
                # Disable autopilot
                self.autopilot_enabled.set(False)
                self.autopilot_status_label.config(text="Status: DISABLED", foreground='red')
                self.autopilot_toggle_btn.config(text="Enable Autopilot")
                logger.info("Autopilot disabled")
        except Exception as e:
            logger.error(f"Error toggling autopilot: {e}")
    
    def emergency_stop(self):
        """Emergency stop for autopilot."""
        try:
            self.autopilot_enabled.set(False)
            self.autopilot_status_label.config(text="Status: EMERGENCY STOP", foreground='orange')
            self.autopilot_toggle_btn.config(text="Enable Autopilot")
            logger.warning("Autopilot emergency stop activated")
        except Exception as e:
            logger.error(f"Error in emergency stop: {e}")


class AutopilotTab:
    """Autopilot tab for the enhanced PokerTool GUI."""
    
    def __init__(self, parent):
        """Initialize the autopilot tab.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.setup_autopilot_tab()
    
    def setup_autopilot_tab(self):
        """Set up the autopilot tab interface."""
        # Create the autopilot components
        mixin = AutopilotTabMixin()
        self.frame = mixin.setup_autopilot_tab(self.parent)
        self.autopilot_enabled = mixin.autopilot_enabled
        self.autopilot_strategy = mixin.autopilot_strategy
        self.autopilot_max_bet = mixin.autopilot_max_bet
        self.autopilot_session_limit = mixin.autopilot_session_limit
        self.autopilot_stop_on_loss = mixin.autopilot_stop_on_loss
        self.autopilot_human_takeover = mixin.autopilot_human_takeover
        self.autopilot_metrics = mixin.autopilot_metrics
        self.toggle_autopilot = mixin.toggle_autopilot
        self.emergency_stop = mixin.emergency_stop
    
    def update_autopilot_metrics(self, metrics_data):
        """Update the autopilot performance metrics.
        
        Args:
            metrics_data (dict): Dictionary containing metrics data
        """
        try:
            for key, var in self.autopilot_metrics.items():
                if key in metrics_data:
                    var.set(str(metrics_data[key]))
        except Exception as e:
            logger.error(f"Error updating autopilot metrics: {e}")
    
    def is_autopilot_enabled(self):
        """Check if autopilot is enabled.
        
        Returns:
            bool: True if autopilot is enabled
        """
        return self.autopilot_enabled.get()
    
    def get_autopilot_settings(self):
        """Get current autopilot settings.
        
        Returns:
            dict: Dictionary of current settings
        """
        return {
            'strategy': self.autopilot_strategy.get(),
            'max_bet': int(self.autopilot_max_bet.get()),
            'session_limit': int(self.autopilot_session_limit.get()),
            'stop_on_loss': self.autopilot_stop_on_loss.get(),
            'human_takeover': self.autopilot_human_takeover.get()
        }
    
    def get_frame(self):
        """Get the main frame for this tab.
        
        Returns:
            tkinter.Frame: The main frame
        """
        return self.frame


def create_autopilot_tab(parent):
    """Create and return an autopilot tab.
    
    Args:
        parent: Parent widget
        
    Returns:
        AutopilotTab: The created autopilot tab
    """
    return AutopilotTab(parent)
