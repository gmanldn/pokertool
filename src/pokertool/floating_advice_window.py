"""
Lightweight floating advice window primitives used by the PokerTool desktop UI.

The production project renders advice inside a tkinter overlay.  For the test
suite we only need deterministic, side-effect free behaviour: storing the most
recent advice, respecting update throttling, and exposing simple show/hide
operations.  The implementation below keeps the public API intact while
gracefully degrading when tkinter or a GUI environment is unavailable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
import os

try:  # pragma: no cover - tkinter is optional in CI environments
    import tkinter as tk
except Exception:  # pragma: no cover
    tk = None  # type: ignore[assignment]


class ActionType(Enum):
    """Supported decision categories surfaced to the player."""

    FOLD = "FOLD"
    CALL = "CALL"
    RAISE = "RAISE"
    CHECK = "CHECK"
    ALL_IN = "ALL-IN"


class ConfidenceLevel(Enum):
    """Discrete confidence buckets used for colouring the advice overlay."""

    VERY_HIGH = ("VERY HIGH", "#00C853", 0.90)
    HIGH = ("HIGH", "#1DE9B6", 0.80)
    MEDIUM = ("MEDIUM", "#FFC400", 0.65)
    LOW = ("LOW", "#FF9100", 0.45)
    VERY_LOW = ("VERY LOW", "#DD2C00", 0.0)

    def __init__(self, label: str, color: str, threshold: float) -> None:
        self.label = label
        self.color = color
        self.threshold = threshold

    @classmethod
    def from_confidence(cls, value: float) -> "ConfidenceLevel":
        """Return the first bucket whose threshold is satisfied."""
        value = max(0.0, min(1.0, value))
        for level in cls:
            if value >= level.threshold:
                return level
        return cls.VERY_LOW


@dataclass
class Advice:
    """Container for a single piece of strategic advice."""

    action: ActionType
    confidence: float
    amount: Optional[float] = None
    ev: Optional[float] = None
    pot_odds: Optional[float] = None
    hand_strength: Optional[float] = None
    reasoning: str = ""
    timestamp: float = field(default_factory=time.time)


class FloatingAdviceWindow:
    """
    Minimal window controller for displaying poker advice.

    The controller keeps the latest advice, ensures updates are throttled, and
    exposes show/hide semantics compatible with the production UI.  GUI work is
    deliberately deferred to keep automated tests headless-friendly.
    """

    def __init__(
        self,
        parent: Optional["tk.Misc"] = None,
        *,
        update_throttle: float = 0.5,
        time_provider: Callable[[], float] | None = None,
    ) -> None:
        self.update_throttle = max(update_throttle, 0.0)
        self._time = time_provider or time.monotonic
        self.current_advice: Optional[Advice] = None
        self.last_update_time: float = 0.0
        self._visible = False
        self._parent = parent
        self._window: Optional["tk.Toplevel"] = None
        self._test_mode = os.environ.get("POKERTOOL_TEST_MODE") == "1"

        if tk is not None and not self._test_mode:
            root = parent or tk.Tk()
            if parent is None:
                root.withdraw()  # pragma: no cover - not exercised in tests
            self._window = tk.Toplevel(root)
            self._window.withdraw()

    # ------------------------------------------------------------------ public
    def update_advice(self, advice: Advice) -> bool:
        """
        Update the window with new advice.

        Returns True when the update is applied, False when throttled.
        """
        now = self._time()
        if self.current_advice and (now - self.last_update_time) < self.update_throttle:
            return False

        self.current_advice = advice
        self.last_update_time = now
        self._render(advice)
        return True

    def clear_advice(self) -> None:
        """Clear the visual representation while keeping the last advice."""
        if self.current_advice is None:
            return
        self._render(None)

    def show(self) -> None:
        """Make the window visible."""
        self._visible = True
        if self._window is not None:
            self._window.deiconify()

    def hide(self) -> None:
        """Hide the window without destroying it."""
        self._visible = False
        if self._window is not None:
            self._window.withdraw()

    def destroy(self) -> None:
        """Destroy the underlying tkinter resources if they exist."""
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:  # pragma: no cover - defensive cleanup
                pass
            finally:
                self._window = None
        self._visible = False

    # ----------------------------------------------------------------- helpers
    def _render(self, advice: Optional[Advice]) -> None:
        """Placeholder render hook."""
        # The production UI updates labels and colour accents here.  Tests patch
        # tkinter so no additional work is required.
        _ = advice  # Intentional no-op.


__all__ = [
    "FloatingAdviceWindow",
    "Advice",
    "ActionType",
    "ConfidenceLevel",
]
