#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Screen scraper handlers for the integrated poker assistant.

Contains methods for:
- Starting/stopping the screen scraper
- Toggling scraper
- Updating scraper status indicator
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class ScraperHandlersMixin:
    """Mixin class providing screen scraper handlers."""
    
    def _start_enhanced_screen_scraper(self) -> bool:
        """Start the enhanced screen scraper in continuous mode."""
        try:
            from pokertool.scrape import run_screen_scraper
            ENHANCED_SCRAPER_LOADED = True
        except ImportError:
            ENHANCED_SCRAPER_LOADED = False
        
        if not ENHANCED_SCRAPER_LOADED or self._enhanced_scraper_started:
            if self._enhanced_scraper_started:
                self._update_scraper_indicator(True)
            return False

        try:
            site = getattr(self.autopilot_panel.state, 'site', 'GENERIC')
            result = run_screen_scraper(
                site=site,
                continuous=True,
                interval=1.0,
                enable_ocr=True
            )

            if result.get('status') == 'success':
                self._enhanced_scraper_started = True
                status_line = '✅ Enhanced screen scraper running (continuous mode)'
                if result.get('ocr_enabled'):
                    status_line += ' with OCR'
                self._update_table_status(status_line + '\n')
                self._update_scraper_indicator(True)
                print(f'Enhanced screen scraper started automatically (site={site})')
                return True

            failure_message = result.get('message', 'unknown error')
            self._update_table_status(f"❌ Enhanced screen scraper failed to start: {failure_message}\n")
            self._update_scraper_indicator(False, error=True)
            print(f'Enhanced screen scraper failed to start: {failure_message}')
            return False

        except Exception as e:
            self._update_table_status(f"❌ Enhanced screen scraper error: {e}\n")
            self._update_scraper_indicator(False, error=True)
            print(f'Enhanced screen scraper error: {e}')
            return False

    def _stop_enhanced_screen_scraper(self) -> None:
        """Stop the enhanced screen scraper if it was started."""
        try:
            from pokertool.scrape import stop_screen_scraper
            ENHANCED_SCRAPER_LOADED = True
        except ImportError:
            ENHANCED_SCRAPER_LOADED = False
        
        if not (ENHANCED_SCRAPER_LOADED and self._enhanced_scraper_started):
            return

        try:
            stop_screen_scraper()
            print('Enhanced screen scraper stopped')
        except Exception as e:
            print(f'Enhanced screen scraper stop error: {e}')
        finally:
            self._enhanced_scraper_started = False
            self._update_scraper_indicator(False)

    def _toggle_screen_scraper(self) -> None:
        """Toggle the enhanced screen scraper on or off."""
        try:
            from pokertool.scrape import run_screen_scraper
            ENHANCED_SCRAPER_LOADED = True
        except ImportError:
            ENHANCED_SCRAPER_LOADED = False
        
        if not ENHANCED_SCRAPER_LOADED:
            self._update_table_status("❌ Screen scraper dependencies not available\n")
            return

        if self._enhanced_scraper_started:
            self._update_table_status("🛑 Stopping enhanced screen scraper...\n")
            self._stop_enhanced_screen_scraper()
            return

        self._update_table_status("🚀 Starting enhanced screen scraper...\n")
        if not self._start_enhanced_screen_scraper():
            self._update_table_status("❌ Screen scraper did not start\n")

    def _update_scraper_indicator(self, active: bool, *, error: bool = False) -> None:
        """Update the visual indicator for the screen scraper button."""
        from ..style import COLORS
        
        button = getattr(self, 'scraper_status_button', None)
        if not button:
            return

        if error:
            text_key = 'actions.screen_scraper_error'
            button.config(
                bg=COLORS['accent_warning'],
                fg=COLORS['bg_dark'],
                activebackground=COLORS['accent_warning'],
                activeforeground=COLORS['bg_dark']
            )
            self._update_widget_translation_key(button, text_key, prefix='⚠️ ')
            return

        if active:
            text_key = 'actions.screen_scraper_on'
            button.config(
                bg=COLORS['accent_success'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['accent_success'],
                activeforeground=COLORS['text_primary']
            )
            self._update_widget_translation_key(button, text_key, prefix='🟢 ')
        else:
            text_key = 'actions.screen_scraper_off'
            button.config(
                bg=COLORS['accent_danger'],
                fg=COLORS['text_primary'],
                activebackground=COLORS['accent_success'],
                activeforeground=COLORS['text_primary']
            )
            self._update_widget_translation_key(button, text_key, prefix='🔌 ')


__all__ = ["ScraperHandlersMixin"]
