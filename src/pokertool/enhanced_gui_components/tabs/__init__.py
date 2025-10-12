#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tab builders for the enhanced GUI.

Each module provides a mixin class for building a specific tab.
"""

from .analytics_tab import AnalyticsTabMixin
from .gamification_tab import GamificationTabMixin
from .community_tab import CommunityTabMixin
from .analysis_tab import AnalysisTabMixin
from .autopilot_tab import AutopilotTabMixin
from .hand_history_tab import HandHistoryTabMixin

__all__ = [
    "AnalyticsTabMixin",
    "GamificationTabMixin",
    "CommunityTabMixin",
    "AnalysisTabMixin",
    "AutopilotTabMixin",
    "HandHistoryTabMixin",
]
