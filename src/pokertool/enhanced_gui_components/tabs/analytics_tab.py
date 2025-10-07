#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analytics Tab for Enhanced PokerTool GUI
========================================

This module provides the analytics tab functionality for the enhanced GUI.

Module: pokertool.enhanced_gui_components.tabs.analytics_tab
Version: 1.0.0
Author: PokerTool Development Team
License: MIT
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class AnalyticsTabMixin:
    """Analytics tab mixin for the enhanced PokerTool GUI."""
    
    def setup_analytics_tab(self, parent):
        """Set up the analytics tab interface.
        
        Args:
            parent: Parent widget
        """
        # Create the analytics frame
        self.analytics_frame = ttk.Frame(parent)
        
        # Title
        title_label = ttk.Label(self.analytics_frame, text="Session Analytics", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Statistics section
        stats_frame = ttk.LabelFrame(self.analytics_frame, text="Session Statistics", padding=10)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        # Create statistics display
        self.analytics_stats_vars = {
            'hands_played': tk.StringVar(value="0"),
            'win_rate': tk.StringVar(value="0.00%"),
            'bb_per_100': tk.StringVar(value="0.00"),
            'vpip': tk.StringVar(value="0.00%"),
            'pfr': tk.StringVar(value="0.00%")
        }
        
        stats_labels = {
            'hands_played': "Hands Played:",
            'win_rate': "Win Rate:",
            'bb_per_100': "BB/100:",
            'vpip': "VPIP:",
            'pfr': "PFR:"
        }
        
        for i, (key, label_text) in enumerate(stats_labels.items()):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_frame, text=label_text).grid(
                row=row, column=col, sticky='w', padx=(0, 10), pady=2
            )
            ttk.Label(stats_frame, textvariable=self.analytics_stats_vars[key], 
                     font=('Arial', 10, 'bold')).grid(
                row=row, column=col+1, sticky='w', padx=(0, 20), pady=2
            )
        
        # Charts section
        charts_frame = ttk.LabelFrame(self.analytics_frame, text="Performance Charts", padding=10)
        charts_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # Placeholder for charts
        chart_placeholder = ttk.Label(charts_frame, 
                                     text="Chart functionality will be available soon.\n"
                                          "This will show profit/loss over time, position statistics,\n"
                                          "and other analytical data.",
                                     font=('Arial', 10),
                                     foreground='gray')
        chart_placeholder.pack(expand=True)
        
        # Control buttons
        button_frame = ttk.Frame(charts_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Export Data", 
                  command=self.export_analytics_data).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Reset Session", 
                  command=self.reset_analytics_session).pack(side='left')
        
        return self.analytics_frame


class AnalyticsTab:
    """Analytics tab for the enhanced PokerTool GUI."""
    
    def __init__(self, parent):
        """Initialize the analytics tab.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.setup_analytics_tab()
    
    def setup_analytics_tab(self):
        """Set up the analytics tab interface."""
        # Create the analytics components
        mixin = AnalyticsTabMixin()
        self.frame = mixin.setup_analytics_tab(self.parent)
        self.analytics_stats_vars = mixin.analytics_stats_vars
    
    
    def update_analytics_statistics(self, stats_data):
        """Update the displayed analytics statistics.
        
        Args:
            stats_data (dict): Dictionary containing statistics data
        """
        try:
            for key, var in self.analytics_stats_vars.items():
                if key in stats_data:
                    var.set(str(stats_data[key]))
        except Exception as e:
            logger.error(f"Error updating analytics statistics: {e}")
    
    def export_analytics_data(self):
        """Export analytics data to file."""
        try:
            # Placeholder for export functionality
            logger.info("Analytics export functionality not yet implemented")
            tk.messagebox.showinfo("Export", "Analytics export functionality will be available soon.")
        except Exception as e:
            logger.error(f"Analytics export error: {e}")
    
    def reset_analytics_session(self):
        """Reset analytics session statistics."""
        try:
            # Reset all statistics
            self.analytics_stats_vars['hands_played'].set("0")
            self.analytics_stats_vars['win_rate'].set("0.00%")
            self.analytics_stats_vars['bb_per_100'].set("0.00")
            self.analytics_stats_vars['vpip'].set("0.00%")
            self.analytics_stats_vars['pfr'].set("0.00%")
            
            logger.info("Analytics session statistics reset")
        except Exception as e:
            logger.error(f"Analytics reset error: {e}")
    
    def update_statistics(self, stats_data):
        """Update the displayed statistics (alias for compatibility)."""
        return self.update_analytics_statistics(stats_data)
    
    def export_data(self):
        """Export data (alias for compatibility)."""
        return self.export_analytics_data()
    
    def reset_session(self):
        """Reset session (alias for compatibility)."""
        return self.reset_analytics_session()
    
    def get_frame(self):
        """Get the main frame for this tab.
        
        Returns:
            tkinter.Frame: The main frame
        """
        return self.frame


def create_analytics_tab(parent):
    """Create and return an analytics tab.
    
    Args:
        parent: Parent widget
        
    Returns:
        AnalyticsTab: The created analytics tab
    """
    return AnalyticsTab(parent)
