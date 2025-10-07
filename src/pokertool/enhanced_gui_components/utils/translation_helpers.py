#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Translation and i18n helper utilities for enhanced GUI.

Provides a mixin class that handles widget translation registration and updates.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Dict, List, Optional, Tuple

try:
    from pokertool.i18n import translate, register_locale_listener, unregister_locale_listener
except ImportError:
    # Fallback if i18n module not available
    def translate(key: str, **kwargs) -> str:
        return key
    
    def register_locale_listener(callback) -> int:
        return 0
    
    def unregister_locale_listener(token: int) -> None:
        pass


class TranslationMixin:
    """
    Mixin class that provides translation capabilities to widgets.
    
    Usage:
        class MyWindow(tk.Tk, TranslationMixin):
            def __init__(self):
                super().__init__()
                self._init_translation()
                # ... rest of initialization
    """
    
    def _init_translation(self) -> None:
        """Initialize translation system. Call this in __init__."""
        self._translation_bindings: List[Tuple[Any, str, str, str, str, Dict[str, Any]]] = []
        self._tab_bindings: List[Tuple[Any, str]] = []
        self._window_title_key = 'app.title'
        self._locale_listener_token: Optional[int] = None
    
    def _register_widget_translation(
        self,
        widget: Any,
        key: str,
        attr: str = 'text',
        *,
        prefix: str = '',
        suffix: str = '',
        **kwargs: Any,
    ) -> None:
        """
        Register a widget for automatic translation updates.
        
        Args:
            widget: The widget to translate
            key: Translation key
            attr: Widget attribute to update (default: 'text')
            prefix: String to prepend to translation
            suffix: String to append to translation
            **kwargs: Additional arguments for translate function
        """
        self._translation_bindings.append((widget, key, attr, prefix, suffix, kwargs))
        self._apply_widget_translation(widget, key, attr, prefix, suffix, kwargs)

    def _update_widget_translation_key(
        self,
        widget: Any,
        key: str,
        attr: str = 'text',
        *,
        prefix: str = '',
        suffix: str = '',
        **kwargs: Any,
    ) -> None:
        """
        Update the translation key for an already-registered widget.
        
        Args:
            widget: The widget to update
            key: New translation key
            attr: Widget attribute (default: 'text')
            prefix: String to prepend to translation
            suffix: String to append to translation
            **kwargs: Additional arguments for translate function
        """
        for idx, (stored_widget, stored_key, stored_attr, stored_prefix, stored_suffix, stored_kwargs) in enumerate(self._translation_bindings):
            if stored_widget is widget and stored_attr == attr:
                self._translation_bindings[idx] = (widget, key, attr, prefix, suffix, kwargs)
                break
        else:
            self._translation_bindings.append((widget, key, attr, prefix, suffix, kwargs))
        self._apply_widget_translation(widget, key, attr, prefix, suffix, kwargs)

    def _register_tab_title(self, frame: Any, key: str) -> None:
        """
        Register a notebook tab for automatic translation updates.
        
        Args:
            frame: The tab frame
            key: Translation key for the tab title
        """
        self._tab_bindings.append((frame, key))
        if hasattr(self, 'notebook'):
            try:
                self.notebook.tab(frame, text=translate(key))
            except Exception:
                pass

    def _apply_widget_translation(
        self,
        widget: Any,
        key: str,
        attr: str,
        prefix: str,
        suffix: str,
        kwargs: Dict[str, Any],
    ) -> None:
        """Apply translation to a widget (internal method)."""
        try:
            translated = translate(key, **kwargs)
            widget.configure(**{attr: f"{prefix}{translated}{suffix}"})
        except tk.TclError:
            pass

    def _apply_translations(self, _locale_code: Optional[str] = None) -> None:
        """
        Apply all registered translations.
        
        This is called automatically when the locale changes.
        Override this method to add custom translation behavior.
        """
        # Update window title
        try:
            if hasattr(self, 'title'):
                self.title(translate(self._window_title_key))
        except (tk.TclError, AttributeError):
            pass

        # Update all registered widgets
        for widget, key, attr, prefix, suffix, kwargs in list(self._translation_bindings):
            self._apply_widget_translation(widget, key, attr, prefix, suffix, kwargs)

        # Update tab titles
        if hasattr(self, 'notebook'):
            for frame, key in list(self._tab_bindings):
                try:
                    self.notebook.tab(frame, text=translate(key))
                except Exception:
                    continue

    def _start_translation_listener(self) -> None:
        """Start listening for locale changes."""
        if self._locale_listener_token is None:
            self._locale_listener_token = register_locale_listener(self._apply_translations)

    def _stop_translation_listener(self) -> None:
        """Stop listening for locale changes."""
        if self._locale_listener_token is not None:
            unregister_locale_listener(self._locale_listener_token)
            self._locale_listener_token = None


__all__ = ["TranslationMixin"]
