"""Compatibility shim for legacy `poker_gui_enhanced` module.

This module re-exports the current Tkinter assistant components from
`src.pokertool.gui` and provides lightweight stand-ins for helper classes that
older tests expect (e.g. `EnhancedCardEntry`, `StatusBar`).
"""

from __future__ import annotations

import queue
import sys

try:
    import tkinter as tk
except ImportError as exc:  # pragma: no cover - executed in headless envs
    raise ImportError(
        "Tkinter is required for pokertool.modules.poker_gui_enhanced; "
        "install python3-tk or use a Python build with Tk support."
    ) from exc
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional


try:
    from ..gui import (
        EnhancedPokerAssistant as _EnhancedPokerAssistant,
        EnhancedPokerAssistantFrame,
        VisualCard as _VisualCard,
        CardSelectionPanel as _CardSelectionPanel,
        TableVisualization as _TableVisualization,
        PlayerInfo,
    )
except Exception as exc:  # pragma: no cover - surface original error
    raise ImportError("Unable to import pokertool.gui components") from exc

try:
    from pokertool.core import Card, Suit, parse_card
except Exception:  # pragma: no cover - fallback shims for tests
    class Suit(Enum):
        SPADES = 'S'
        HEARTS = 'H'
        DIAMONDS = 'D'
        CLUBS = 'C'

    @dataclass
    class Card:
        rank: str
        suit: Suit

    def parse_card(code: str) -> Card:
        code = code.strip().upper()
        if len(code) != 2:
            raise ValueError(f'Invalid card code: {code!r}')
        rank = code[0]
        suit_map = {'S': Suit.SPADES, 'H': Suit.HEARTS,
                    'D': Suit.DIAMONDS, 'C': Suit.CLUBS}
        try:
            suit = suit_map[code[1]]
        except KeyError as err:
            raise ValueError(f'Invalid suit in card code: {code!r}') from err
        return Card(rank, suit)


class ValidationState(Enum):
    """Simple validation states for card entry widgets."""

    EMPTY = auto()
    PENDING = auto()
    VALID = auto()
    INVALID = auto()


@dataclass
class UITheme:
    """Minimal theme representation for legacy callers."""

    background: str = '#1a1f2e'
    foreground: str = '#ffffff'
    accent: str = '#4a9eff'
    warning: str = '#fbbf24'
    danger: str = '#ef4444'


@dataclass
class UIState:
    """Lightweight UI state container used by historic tests."""

    dark_mode: bool = True
    active_tab: str = 'manual'
    last_action: str = ''
    status: str = 'Ready'


class EnhancedCardEntry(tk.Entry):
    """Card entry widget with basic validation logic."""

    _VALID_RANKS = set('23456789TJQKA')
    _SUIT_MAP = {
        'S': 'S', 'H': 'H', 'D': 'D', 'C': 'C',
        '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C',
    }
    _SUIT_SYMBOL = {
        'S': '♠',
        'H': '♥',
        'D': '♦',
        'C': '♣',
    }

    def __init__(self, master: tk.Misc, callback: Optional[Callable[["EnhancedCardEntry"], None]] = None, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self.callback = callback
        self.validation_state = ValidationState.EMPTY
        self.bind('<KeyRelease>', self._validate_input)

    def _normalize(self, value: str) -> str:
        return value.strip().upper()

    def _validate_input(self, _event: Any = None) -> bool:
        value = self._normalize(self.get())

        if not value:
            self.validation_state = ValidationState.EMPTY
        elif len(value) == 1 and value[0] in self._VALID_RANKS:
            self.validation_state = ValidationState.PENDING
        elif len(value) == 2 and value[0] in self._VALID_RANKS and value[1] in self._SUIT_MAP:
            self.validation_state = ValidationState.VALID
            if self.callback:
                self.callback(self)
        else:
            self.validation_state = ValidationState.INVALID

        return True

    def get_card(self) -> Optional[Card]:
        if self.validation_state is not ValidationState.VALID:
            return None
        value = self._normalize(self.get())
        normalised = value[0] + self._SUIT_MAP[value[1]]
        try:
            return parse_card(normalised)
        except Exception:  # pragma: no cover - guard against parse errors
            return None

    def clear(self) -> None:
        self.delete(0, tk.END)
        self.validation_state = ValidationState.EMPTY

    def set_card(self, card: Card) -> None:
        rank = getattr(card, 'rank', '')
        suit_attr = getattr(card, 'suit', '')
        suit_value = getattr(suit_attr, 'value', suit_attr)
        if isinstance(suit_value, str):
            suit_value = suit_value.upper()
        suit_key = str(suit_value)[0]
        symbol = self._SUIT_SYMBOL.get(suit_key, suit_key)
        self.delete(0, tk.END)
        self.insert(0, f'{rank}{symbol}')
        self.validation_state = ValidationState.VALID


class StatusBar(tk.Frame):
    """Minimal status bar implementation for backwards compatibility."""

    def __init__(self, master: tk.Misc):
        super().__init__(master, bg='#1a1f2e')
        self.pack(fill='x')
        self.status_queue: queue.Queue[str] = queue.Queue()
        self.status_label = tk.Label(self, text='Ready', fg='#ffffff', bg='#1a1f2e')
        self.status_label.pack(side='left', padx=8)
        self.modules_frame = tk.Frame(self, bg='#1a1f2e')
        self.modules_frame.pack(side='right')
        self._pending_after: Optional[str] = None

    def set_status(self, message: str, timeout: float = 1.0) -> None:
        self.status_queue.put(message)
        self.status_label.config(text=message)

        if self._pending_after is not None:
            try:
                self.after_cancel(self._pending_after)
            except Exception:
                pass

        if timeout > 0:
            self._pending_after = self.after(int(timeout * 1000), lambda: self.status_label.config(text='Ready'))

    def set_permanent_status(self, message: str) -> None:
        self.status_queue.put(message)
        self.status_label.config(text=message)


def initialise_db_if_needed() -> None:  # pragma: no cover - legacy no-op
    """Legacy function kept for test patches."""


def open_db() -> None:  # pragma: no cover - legacy no-op
    """Legacy function kept for test patches."""


def _ensure_parent(parent: Any) -> tuple[tk.Misc, Optional[tk.Tk]]:
    """Provide a safe tkinter parent even when tests pass mocks."""
    if isinstance(parent, tk.Misc):
        return parent, None

    fallback_root = tk.Tk()
    fallback_root.withdraw()
    shim_parent = tk.Frame(fallback_root)
    shim_parent.pack_forget()
    return shim_parent, fallback_root


class VisualCard(_VisualCard):
    """Wrapper that tolerates mock parents during tests."""

    def __init__(self, parent: Any, *args: Any, **kwargs: Any) -> None:
        parent, helper_root = _ensure_parent(parent)
        self._helper_root = helper_root
        super().__init__(parent, *args, **kwargs)

    def destroy(self) -> None:  # pragma: no cover - defensive cleanup
        try:
            super().destroy()
        finally:
            if self._helper_root is not None:
                try:
                    self._helper_root.destroy()
                except Exception:
                    pass


class CardSelectionPanel(_CardSelectionPanel):
    """Wrapper panel that creates a hidden root when tests supply mocks."""

    def __init__(self, parent: Any, callback: Optional[Callable] = None) -> None:
        parent, helper_root = _ensure_parent(parent)
        self._helper_root = helper_root
        super().__init__(parent, callback)

    def destroy(self) -> None:  # pragma: no cover - defensive cleanup
        try:
            super().destroy()
        finally:
            if self._helper_root is not None:
                try:
                    self._helper_root.destroy()
                except Exception:
                    pass


class TableVisualization(_TableVisualization):
    """Wrapper canvas that tolerates mocked parents in legacy tests."""

    def __init__(self, parent: Any, *args: Any, **kwargs: Any) -> None:
        parent, helper_root = _ensure_parent(parent)
        self._helper_root = helper_root
        super().__init__(parent, *args, **kwargs)

    def destroy(self) -> None:  # pragma: no cover
        try:
            super().destroy()
        finally:
            if self._helper_root is not None:
                try:
                    self._helper_root.destroy()
                except Exception:
                    pass


class EnhancedPokerAssistant(_EnhancedPokerAssistant):
    """Alias exposing the modern assistant under the legacy module name."""


__all__ = [
    'EnhancedPokerAssistant',
    'EnhancedPokerAssistantFrame',
    'EnhancedCardEntry',
    'StatusBar',
    'UITheme',
    'UIState',
    'ValidationState',
    'VisualCard',
    'CardSelectionPanel',
    'TableVisualization',
    'PlayerInfo',
    'initialise_db_if_needed',
    'open_db',
]
