#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Smart Poker Window Detector
===========================

Enhanced poker window detection that prioritizes actual betting sites
over development tools and documentation.

This module adds URL-based filtering and smart exclusions to improve
detection accuracy and reduce false positives.
"""

import re
import logging
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WindowPriority:
    """Priority levels for detected windows."""
    HIGH = 100      # Actual betting sites with URLs
    MEDIUM = 50     # Poker-like windows without URLs
    LOW = 10        # Development/documentation tools
    EXCLUDED = 0    # Should be ignored

class SmartPokerDetector:
    """
    Smart detector that prioritizes real poker sites over development tools.
    """
    
    def __init__(self):
        # Real betting/poker site URL patterns (HIGHEST PRIORITY)
        self.betting_url_patterns = [
            r'pokerstars\.(com|net|eu|uk|fr|es|it|de|se|dk)',
            r'888poker\.com',
            r'partypoker\.(com|net)',
            r'ggpoker\.(com|co\.uk)',
            r'bet365\.com',
            r'williamhill\.com',
            r'betfair\.(com|co\.uk|es|it|de|se|ro)',  # Enhanced Betfair
            r'poker\.betfair\.(com|co\.uk)',           # Betfair Poker subdomain
            r'betfair\.com.*poker',                    # Betfair with poker in URL
            r'unibet\.(com|co\.uk)',
            r'bwin\.com',
            r'pokernow\.club',
            r'replay\.poker',
            r'poker\.pokerstars',
            r'play\.pokerstars',
            r'secure\.pokerstars',
            r'global-poker\.com',
            r'ignitioncasino\.eu',
            r'bovada\.lv',
            r'americascardroom\.eu',
            r'blackchippoker\.eu',
            r'betonline\.ag',
            r'sportsbetting\.ag',
            r'tigergaming\.com',
            r'winamax\.(fr|es|it)',
            r'pokerstrategy\.com/poker',
            r'ladbrokes\.com',
            r'paddypower\.com',
        ]
        
        # Poker application window titles (MEDIUM PRIORITY)
        self.poker_app_patterns = [
            r'^PokerStars\s',
            r'^888poker\s',
            r'^PartyPoker\s',
            r'^GGPoker\s',
            r'^Betfair Poker',                 # Betfair Poker application
            r'Betfair.*Poker',                 # Betfair with Poker
            r'No Limit Hold.*em',
            r'Texas Hold.*em',
            r'Pot Limit Omaha',
            r'Table\s+\d+',
            r'Cash Game',
            r'Tournament',
        ]
        
        # Development/documentation to EXCLUDE
        self.exclusion_patterns = [
            r'Visual Studio Code',
            r'VS Code',
            r'VSCode',
            r'pokertool$',  # Our project name
            r'^pokertool\s',
            r'GitHub',
            r'GitKraken',
            r'Sublime Text',
            r'Atom Editor',
            r'IntelliJ',
            r'PyCharm',
            r'Chrome DevTools',
            r'Firefox Developer',
            r'Safari Developer',
            r'Documentation',
            r'README',
            r'Swagger',
            r'Postman',
            r'MongoDB Compass',
            r'pgAdmin',
            r'DBeaver',
        ]
    
    def classify_window(self, window_title: str) -> Tuple[int, str]:
        """
        Classify a window and assign priority.
        
        Args:
            window_title: The window title to classify
            
        Returns:
            Tuple of (priority_score, classification_reason)
        """
        title_lower = window_title.lower()
        
        # Check exclusions first
        for pattern in self.exclusion_patterns:
            if re.search(pattern, window_title, re.IGNORECASE):
                return (WindowPriority.EXCLUDED, f"Excluded: matches {pattern}")
        
        # Check for betting site URLs (HIGHEST PRIORITY)
        for pattern in self.betting_url_patterns:
            if re.search(pattern, title_lower):
                return (WindowPriority.HIGH, f"Betting site URL detected: {pattern}")
        
        # Check for poker application patterns (MEDIUM PRIORITY)
        for pattern in self.poker_app_patterns:
            if re.search(pattern, window_title, re.IGNORECASE):
                return (WindowPriority.MEDIUM, f"Poker application pattern: {pattern}")
        
        # Generic poker keyword (LOW PRIORITY)
        if 'poker' in title_lower or 'holdem' in title_lower or 'hold\'em' in title_lower:
            return (WindowPriority.LOW, "Generic poker keyword")
        
        return (WindowPriority.EXCLUDED, "No poker-related patterns found")
    
    def filter_and_prioritize(self, windows: List) -> Tuple[List, List, List]:
        """
        Filter windows and organize by priority.
        
        Args:
            windows: List of WindowInfo objects
            
        Returns:
            Tuple of (high_priority, medium_priority, excluded)
        """
        high_priority = []
        medium_priority = []
        excluded = []
        
        for window in windows:
            score, reason = self.classify_window(window.title)
            
            logger.debug(f"Window '{window.title}': score={score}, reason={reason}")
            
            if score == WindowPriority.HIGH:
                high_priority.append((window, score, reason))
            elif score == WindowPriority.MEDIUM:
                medium_priority.append((window, score, reason))
            elif score == WindowPriority.LOW:
                medium_priority.append((window, score, reason))
            else:  # EXCLUDED
                excluded.append((window, score, reason))
        
        # Sort by area within each priority group (larger windows first)
        high_priority.sort(key=lambda x: x[0].area, reverse=True)
        medium_priority.sort(key=lambda x: x[0].area, reverse=True)
        
        return (
            [w for w, _, _ in high_priority],
            [w for w, _, _ in medium_priority],
            [w for w, _, _ in excluded]
        )
    
    def get_best_windows(self, windows: List, max_windows: int = 5) -> List:
        """
        Get the best windows for poker detection.
        
        Args:
            windows: List of WindowInfo objects
            max_windows: Maximum number of windows to return
            
        Returns:
            List of best windows, prioritizing betting sites
        """
        high, medium, excluded = self.filter_and_prioritize(windows)
        
        logger.info(f"Window classification: {len(high)} high priority, "
                   f"{len(medium)} medium priority, {len(excluded)} excluded")
        
        # Prioritize high priority windows first
        best_windows = high[:max_windows]
        
        # Add medium priority if we have room
        if len(best_windows) < max_windows:
            remaining = max_windows - len(best_windows)
            best_windows.extend(medium[:remaining])
        
        return best_windows


def create_smart_detector() -> SmartPokerDetector:
    """Create a smart poker window detector."""
    return SmartPokerDetector()


if __name__ == '__main__':
    # Test the detector
    detector = SmartPokerDetector()
    
    test_windows = [
        "pokerstars.com - Table 5",
        "pokertool",
        "Visual Studio Code - pokertool",
        "888poker.com - No Limit Hold'em",
        "Poker - Documentation",
        "🎰 Poker Tool - Enhanced with Autopilot",
        "play.pokerstars.com - Cash Game",
    ]
    
    print("Testing Smart Poker Detector\n")
    for title in test_windows:
        score, reason = detector.classify_window(title)
        priority_name = {
            WindowPriority.HIGH: "HIGH",
            WindowPriority.MEDIUM: "MEDIUM",
            WindowPriority.LOW: "LOW",
            WindowPriority.EXCLUDED: "EXCLUDED"
        }.get(score, "UNKNOWN")
        
        print(f"{priority_name:10} | {title}")
        print(f"           | {reason}\n")
