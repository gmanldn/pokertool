#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Background services management for the integrated poker assistant.

Handles initialization and startup of background monitoring services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class BackgroundServicesMixin:
    """Mixin class providing background services management."""
    
    def _init_database(self) -> None:
        """Initialize database connection."""
        try:
            from pokertool.storage import get_secure_db
            GUI_MODULES_LOADED = True
        except ImportError:
            GUI_MODULES_LOADED = False
            
        try:
            if GUI_MODULES_LOADED:
                self.secure_db = get_secure_db()
                print("Database initialized")
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def _start_background_services(self) -> None:
        """Start background monitoring services."""
        try:
            started_services = []

            if self.multi_table_manager:
                # Check if start_monitoring method exists before calling
                if hasattr(self.multi_table_manager, 'start_monitoring'):
                    self.multi_table_manager.start_monitoring()
                    started_services.append('table monitoring')
                else:
                    print('TableManager initialized (start_monitoring method not available)')

            # AUTO-START screen scraper immediately (not waiting for autopilot)
            self._update_table_status("🚀 Auto-starting screen scraper...\n")
            if self._start_enhanced_screen_scraper():
                started_services.append('enhanced screen scraper')
                self._update_table_status("✅ Screen scraper active and monitoring\n")
            else:
                self._update_scraper_indicator(False)
                self._update_table_status("⚠️ Screen scraper not started (check dependencies)\n")

            if started_services:
                print(f'Background services started: {", ".join(started_services)}')
                self._update_table_status(f"📡 Services running: {', '.join(started_services)}\n")

        except Exception as e:
            print(f'Background services error: {e}')
            self._update_table_status(f"❌ Background services error: {e}\n")


__all__ = ["BackgroundServicesMixin"]
