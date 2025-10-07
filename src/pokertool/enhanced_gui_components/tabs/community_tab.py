#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Community Tab for Enhanced PokerTool GUI
========================================

This module provides the community tab functionality for the enhanced GUI.

Module: pokertool.enhanced_gui_components.tabs.community_tab
Version: 1.0.0
Author: PokerTool Development Team
License: MIT
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)


class CommunityTabMixin:
    """Community tab mixin for the enhanced PokerTool GUI."""
    
    def setup_community_tab(self, parent):
        """Set up the community tab interface.
        
        Args:
            parent: Parent widget
        """
        # Create the community frame
        self.community_frame = ttk.Frame(parent)
        
        # Title
        title_label = ttk.Label(self.community_frame, text="Community & Social Features", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Leaderboards section
        leaderboard_frame = ttk.LabelFrame(self.community_frame, text="Weekly Leaderboard", padding=10)
        leaderboard_frame.pack(fill='x', pady=(0, 10))
        
        # Create leaderboard display
        self.community_leaderboard = [
            {"rank": 1, "player": "PokerPro123", "score": 25680, "badge": "👑"},
            {"rank": 2, "player": "CardShark", "score": 23450, "badge": "🥈"},
            {"rank": 3, "player": "BluffMaster", "score": 21200, "badge": "🥉"},
            {"rank": 4, "player": "You", "score": 8950, "badge": ""},
            {"rank": 5, "player": "ChipStack", "score": 7200, "badge": ""},
        ]
        
        for i, player in enumerate(self.community_leaderboard):
            player_frame = ttk.Frame(leaderboard_frame)
            player_frame.pack(fill='x', pady=2)
            
            # Rank and badge
            rank_text = f"{player['badge']} #{player['rank']}" if player['badge'] else f"#{player['rank']}"
            rank_label = ttk.Label(player_frame, text=rank_text, 
                                 font=('Arial', 10, 'bold'), width=8)
            rank_label.pack(side='left', padx=(0, 10))
            
            # Player name
            name_label = ttk.Label(player_frame, text=player["player"], 
                                 font=('Arial', 10))
            name_label.pack(side='left', fill='x', expand=True)
            
            # Score
            score_label = ttk.Label(player_frame, text=f"{player['score']:,} pts", 
                                  font=('Arial', 10, 'bold'))
            score_label.pack(side='right')
        
        # Social features section
        social_frame = ttk.LabelFrame(self.community_frame, text="Social Features", padding=10)
        social_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # Feature buttons
        buttons_frame = ttk.Frame(social_frame)
        buttons_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(buttons_frame, text="Share Achievement", 
                  command=self.share_achievement).pack(side='left', padx=(0, 10))
        ttk.Button(buttons_frame, text="Find Friends", 
                  command=self.find_friends).pack(side='left', padx=(0, 10))
        ttk.Button(buttons_frame, text="Join Tournament", 
                  command=self.join_tournament).pack(side='left')
        
        # Community feed
        feed_label = ttk.Label(social_frame, text="Community Feed:", 
                             font=('Arial', 10, 'bold'))
        feed_label.pack(anchor='w', pady=(10, 5))
        
        # Scrollable text area for community feed
        feed_frame = ttk.Frame(social_frame)
        feed_frame.pack(fill='both', expand=True)
        
        self.community_feed_text = tk.Text(feed_frame, height=8, wrap=tk.WORD, 
                                         state=tk.DISABLED, bg='white')
        scrollbar = ttk.Scrollbar(feed_frame, orient="vertical", command=self.community_feed_text.yview)
        self.community_feed_text.configure(yscrollcommand=scrollbar.set)
        
        self.community_feed_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Add some sample feed content
        self.add_feed_message("🎉 PokerPro123 just unlocked 'Century' achievement!")
        self.add_feed_message("🏆 Weekly tournament starts in 2 hours - Join now!")
        self.add_feed_message("💡 Tip of the day: Position is power in poker")
        self.add_feed_message("🔥 BluffMaster is on a 7-game win streak!")
        
        return self.community_frame
    
    def add_feed_message(self, message):
        """Add a message to the community feed.
        
        Args:
            message (str): Message to add to the feed
        """
        try:
            self.community_feed_text.config(state=tk.NORMAL)
            self.community_feed_text.insert(tk.END, f"• {message}\n")
            self.community_feed_text.config(state=tk.DISABLED)
            self.community_feed_text.see(tk.END)
        except Exception as e:
            logger.error(f"Error adding feed message: {e}")


class CommunityTab:
    """Community tab for the enhanced PokerTool GUI."""
    
    def __init__(self, parent):
        """Initialize the community tab.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.setup_community_tab()
    
    def setup_community_tab(self):
        """Set up the community tab interface."""
        # Create the community components
        mixin = CommunityTabMixin()
        self.frame = mixin.setup_community_tab(self.parent)
        self.community_leaderboard = mixin.community_leaderboard
        self.community_feed_text = mixin.community_feed_text
        self.add_feed_message = mixin.add_feed_message
    
    def share_achievement(self):
        """Share an achievement to the community."""
        try:
            # Placeholder for share functionality
            logger.info("Share achievement functionality not yet implemented")
            tk.messagebox.showinfo("Share", "Share achievement functionality will be available soon.")
        except Exception as e:
            logger.error(f"Share achievement error: {e}")
    
    def find_friends(self):
        """Find and add friends."""
        try:
            # Placeholder for find friends functionality
            logger.info("Find friends functionality not yet implemented")
            tk.messagebox.showinfo("Find Friends", "Find friends functionality will be available soon.")
        except Exception as e:
            logger.error(f"Find friends error: {e}")
    
    def join_tournament(self):
        """Join a community tournament."""
        try:
            # Placeholder for tournament functionality
            logger.info("Join tournament functionality not yet implemented")
            tk.messagebox.showinfo("Tournament", "Tournament functionality will be available soon.")
        except Exception as e:
            logger.error(f"Join tournament error: {e}")
    
    def update_leaderboard(self, leaderboard_data):
        """Update the leaderboard data.
        
        Args:
            leaderboard_data (list): List of player data dictionaries
        """
        try:
            self.community_leaderboard = leaderboard_data
            logger.info("Leaderboard updated")
        except Exception as e:
            logger.error(f"Error updating leaderboard: {e}")
    
    def get_frame(self):
        """Get the main frame for this tab.
        
        Returns:
            tkinter.Frame: The main frame
        """
        return self.frame


def create_community_tab(parent):
    """Create and return a community tab.
    
    Args:
        parent: Parent widget
        
    Returns:
        CommunityTab: The created community tab
    """
    return CommunityTab(parent)
