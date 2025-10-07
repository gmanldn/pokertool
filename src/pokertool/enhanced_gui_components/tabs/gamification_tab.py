#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gamification Tab for Enhanced PokerTool GUI
==========================================

This module provides the gamification tab functionality for the enhanced GUI.

Module: pokertool.enhanced_gui_components.tabs.gamification_tab
Version: 1.0.0
Author: PokerTool Development Team
License: MIT
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class GamificationTabMixin:
    """Gamification tab mixin for the enhanced PokerTool GUI."""
    
    def setup_gamification_tab(self, parent):
        """Set up the gamification tab interface.
        
        Args:
            parent: Parent widget
        """
        # Create the gamification frame
        self.gamification_frame = ttk.Frame(parent)
        
        # Title
        title_label = ttk.Label(self.gamification_frame, text="Player Achievements & Progress", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Achievements section
        achievements_frame = ttk.LabelFrame(self.gamification_frame, text="Achievements", padding=10)
        achievements_frame.pack(fill='x', pady=(0, 10))
        
        # Create achievements display
        self.gamification_achievements = [
            {"name": "First Steps", "description": "Play your first hand", "unlocked": True},
            {"name": "Century", "description": "Play 100 hands", "unlocked": False},
            {"name": "Profit Hunter", "description": "Win 1000 chips", "unlocked": False},
            {"name": "Streak Master", "description": "Win 5 hands in a row", "unlocked": False},
        ]
        
        for i, achievement in enumerate(self.gamification_achievements):
            achievement_frame = ttk.Frame(achievements_frame)
            achievement_frame.pack(fill='x', pady=2)
            
            # Achievement icon/indicator
            status = "✓" if achievement["unlocked"] else "○"
            color = "green" if achievement["unlocked"] else "gray"
            
            status_label = ttk.Label(achievement_frame, text=status, 
                                   font=('Arial', 12, 'bold'), foreground=color)
            status_label.pack(side='left', padx=(0, 10))
            
            # Achievement info
            info_frame = ttk.Frame(achievement_frame)
            info_frame.pack(side='left', fill='x', expand=True)
            
            name_label = ttk.Label(info_frame, text=achievement["name"], 
                                 font=('Arial', 10, 'bold'))
            name_label.pack(anchor='w')
            
            desc_label = ttk.Label(info_frame, text=achievement["description"], 
                                 font=('Arial', 9), foreground='gray')
            desc_label.pack(anchor='w')
        
        # Progress section
        progress_frame = ttk.LabelFrame(self.gamification_frame, text="Session Progress", padding=10)
        progress_frame.pack(fill='x', pady=(10, 0))
        
        # Create progress bars
        self.gamification_progress_vars = {
            'hands_progress': tk.DoubleVar(value=0.0),
            'profit_progress': tk.DoubleVar(value=0.0),
            'experience_progress': tk.DoubleVar(value=0.0)
        }
        
        # Hands played progress
        ttk.Label(progress_frame, text="Hands Progress (0/100)").pack(anchor='w', pady=(0, 5))
        hands_progress = ttk.Progressbar(progress_frame, mode='determinate', 
                                       variable=self.gamification_progress_vars['hands_progress'])
        hands_progress.pack(fill='x', pady=(0, 10))
        
        # Profit progress
        ttk.Label(progress_frame, text="Profit Target (0/1000 chips)").pack(anchor='w', pady=(0, 5))
        profit_progress = ttk.Progressbar(progress_frame, mode='determinate', 
                                        variable=self.gamification_progress_vars['profit_progress'])
        profit_progress.pack(fill='x', pady=(0, 10))
        
        # Experience progress
        ttk.Label(progress_frame, text="Experience Level (Level 1)").pack(anchor='w', pady=(0, 5))
        exp_progress = ttk.Progressbar(progress_frame, mode='determinate', 
                                     variable=self.gamification_progress_vars['experience_progress'])
        exp_progress.pack(fill='x', pady=(0, 10))
        
        # Level and stats
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Label(stats_frame, text="Player Level: 1", 
                 font=('Arial', 10, 'bold')).pack(side='left')
        ttk.Label(stats_frame, text="Total XP: 0", 
                 font=('Arial', 10)).pack(side='right')
        
        return self.gamification_frame


class GamificationTab:
    """Gamification tab for the enhanced PokerTool GUI."""
    
    def __init__(self, parent):
        """Initialize the gamification tab.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.setup_gamification_tab()
    
    def setup_gamification_tab(self):
        """Set up the gamification tab interface."""
        # Create the gamification components
        mixin = GamificationTabMixin()
        self.frame = mixin.setup_gamification_tab(self.parent)
        self.gamification_progress_vars = mixin.gamification_progress_vars
        self.gamification_achievements = mixin.gamification_achievements
    
    def update_gamification_progress(self, progress_data):
        """Update the gamification progress.
        
        Args:
            progress_data (dict): Dictionary containing progress data
        """
        try:
            for key, var in self.gamification_progress_vars.items():
                if key in progress_data:
                    var.set(float(progress_data[key]))
        except Exception as e:
            logger.error(f"Error updating gamification progress: {e}")
    
    def unlock_achievement(self, achievement_name):
        """Unlock an achievement.
        
        Args:
            achievement_name (str): Name of the achievement to unlock
        """
        try:
            for achievement in self.gamification_achievements:
                if achievement["name"] == achievement_name:
                    achievement["unlocked"] = True
                    logger.info(f"Achievement unlocked: {achievement_name}")
                    break
        except Exception as e:
            logger.error(f"Error unlocking achievement: {e}")
    
    def get_frame(self):
        """Get the main frame for this tab.
        
        Returns:
            tkinter.Frame: The main frame
        """
        return self.frame


def create_gamification_tab(parent):
    """Create and return a gamification tab.
    
    Args:
        parent: Parent widget
        
    Returns:
        GamificationTab: The created gamification tab
    """
    return GamificationTab(parent)
