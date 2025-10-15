
from __future__ import annotations
"""Shared models, seed data, and a lightweight plugin registry for PokerTool.
This version is **backwards compatible** with code that expects a `Suit.SPADES` enum,
and **forwards compatible** with modules that use simple suit symbols like "♠".
"""

from typing import Callable, TypeVar, Dict, TYPE_CHECKING, List, Optional, Iterable, Union
from datetime import datetime
from enum import Enum

# SQLAlchemy minimal models used by the app menu/plugins
from sqlalchemy import Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, mapped_column, Mapped, Session

if TYPE_CHECKING:
    # Hinted controller type: must expose `session_context()` returning a context manager for Session
    from poker_main import PokerAssistant as GameController

Base = declarative_base()
T = TypeVar("T", bound=Callable)

# ---------------------------------------------------------------------------
# Suits & Ranks (robust and backwards compatible)
# ---------------------------------------------------------------------------

class Suit(Enum):
    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"

    @property
    def letter(self) -> str:
        return {
            Suit.SPADES: "S",
            Suit.HEARTS: "H",
            Suit.DIAMONDS: "D",
            Suit.CLUBS: "C",
        }[self]

    @property
    def name_title(self) -> str:
        return self.name.title()

    def __str__(self) -> str:
        # default string is the symbol, e.g. "♠"
        return self.value

# Public constants expected by the GUI layer
SUITS: List[str] = [s.value for s in Suit]  # ["♠","♥","♦","♣"]
RANKS: List[str] = ["2","3","4","5","6","7","8","9","T","J","Q","K","A"]
RANK_VALUES = {r:i for i,r in enumerate(RANKS, start=2)}

# Flexible parsing: accept symbols, letters, words, or Enum
_SUIT_ALIASES = {
    "♠": Suit.SPADES, "S": Suit.SPADES, "SPADE": Suit.SPADES, "SPADES": Suit.SPADES,
    "♣": Suit.CLUBS,  "C": Suit.CLUBS,  "CLUB": Suit.CLUBS,   "CLUBS": Suit.CLUBS,
    "♥": Suit.HEARTS, "H": Suit.HEARTS, "HEART": Suit.HEARTS, "HEARTS": Suit.HEARTS,
    "♦": Suit.DIAMONDS,"D": Suit.DIAMONDS,"DIAMOND": Suit.DIAMONDS,"DIAMONDS": Suit.DIAMONDS,
}
def to_suit(s: Union[Suit, str]) -> Suit:
    if isinstance(s, Suit):
        return s
    key = str(s).strip().upper()
    if key in _SUIT_ALIASES:
        return _SUIT_ALIASES[key]
    # Last resort: if passed the single unicode symbol already
    for su in Suit:
        if key == su.value:
            return su
    raise ValueError(f"Unknown suit: {s!r}")

# ---------------------------------------------------------------------------
# Card helpers
# ---------------------------------------------------------------------------

class Card:
    __slots__ = ("rank","suit","value")
    def __init__(self, rank: str, suit: Union[Suit, str]):
        if rank not in RANKS:
            raise ValueError(f"Invalid rank {rank!r}; expected one of {RANKS}")
        su = to_suit(suit)
        self.rank: str = rank
        self.suit: str = su.value          # store symbol for GUI friendliness
        self.value: int = RANK_VALUES[rank]

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return f"Card({self.rank!r}, {self.suit!r})"

def create_deck() -> List[Card]:
    return [Card(r, s) for s in SUITS for r in RANKS]

# ---------------------------------------------------------------------------
# Extremely light-weight odds heuristic (good enough for basic advice)
# ---------------------------------------------------------------------------

def calculate_win_probability(hole_cards: List[Card], community_cards: List[Card], 
                              num_opponents: int = 1) -> float:
    """Very rough and fast hand strength heuristic.
    Keeps the app responsive without heavy simulators. Returns 5%..95%.
    """
    if len(hole_cards) != 2:
        return 0.0

    is_pair   = hole_cards[0].rank == hole_cards[1].rank
    is_suited = hole_cards[0].suit == hole_cards[1].suit
    high_card = max(h.value for h in hole_cards)

    base = 0.12  # floor for two random cards

    if is_pair:
        base += 0.38
        if high_card >= RANK_VALUES["T"]:
            base += 0.10
    else:
        # broadway high-card boost
        if high_card >= RANK_VALUES["A"]:
            base += 0.20
        elif high_card >= RANK_VALUES["K"]:
            base += 0.16
        elif high_card >= RANK_VALUES["Q"]:
            base += 0.12
        elif high_card >= RANK_VALUES["J"]:
            base += 0.08

        # suited and gappers
        if is_suited:
            base += 0.06
        gap = abs(hole_cards[0].value - hole_cards[1].value)
        if gap == 0:
            pass  # already counted as pair
        elif gap == 1:
            base += 0.05
        elif gap == 2:
            base += 0.02

    # crude board interaction bonuses
    if community_cards:
        board_ranks = {c.rank for c in community_cards}
        board_suits = {c.suit for c in community_cards}
        if any(c.rank in board_ranks for c in hole_cards):
            base += 0.06
        if is_suited and hole_cards[0].suit in board_suits:
            base += 0.03

    # more players -> lower equity
    denom = 1 + (max(1, num_opponents) - 1) * 0.35
    prob = base / denom
    return max(0.05, min(0.95, prob))

# ---------------------------------------------------------------------------
# ORM models used by the History plugins/menu
# ---------------------------------------------------------------------------

class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Me")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class HandHistory(Base):
    __tablename__ = "hand_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    position: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    hole_cards: Mapped[str] = mapped_column(String(16), nullable=False)
    community_cards: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    predicted_win_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_result: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    chip_stack: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

# ---------------------------------------------------------------------------
# Plugin registry (used by PokerAssistant menu)
# ---------------------------------------------------------------------------

PLUGIN_REGISTRY: Dict[str, Callable[["GameController"], None]] = {}

def register_plugin(name: str) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        if name in PLUGIN_REGISTRY:
            raise ValueError(f"Duplicate plugin name: {name}")
        PLUGIN_REGISTRY[name] = func  # type: ignore[assignment]
        return func
    return decorator

# Built-in plugins -----------------------------------------------------------

@register_plugin("Show Hand History")
def _show_history_plugin(controller: "GameController") -> None:
    """Simple popup window listing the last 50 hands."""
    import tkinter as tk
    from tkinter import ttk, messagebox

    try:
        with controller.session_context() as session:  # type: ignore[attr-defined]
            rows = (session.query(HandHistory)
                    .order_by(HandHistory.created_at.desc())
                    .limit(50)
                    .all())
    except Exception as e:
        messagebox.showerror("DB Error", f"Failed to load hand history: {e}")
        return

    win = tk.Toplevel()
    win.title("Recent Hands (latest 50)")
    win.geometry("700x360")

    tree = ttk.Treeview(win, columns=("created","pos","hole","board","pred","result","stack"), show="headings")
    tree.heading("created", text="Time")
    tree.heading("pos",     text="Pos")
    tree.heading("hole",    text="Hole")
    tree.heading("board",   text="Board")
    tree.heading("pred",    text="Pred %")
    tree.heading("result",  text="Result")
    tree.heading("stack",   text="Stack")

    tree.pack(fill="both", expand=True)

    for h in rows:
        tree.insert("", "end", values=(
            h.created_at.strftime("%H:%M:%S"),
            h.position or "",
            h.hole_cards,
            h.community_cards or "",
            f"{(h.predicted_win_prob or 0.0)*100:.1f}",
            h.actual_result or "",
            h.chip_stack or 0,
        ))

@register_plugin("Clear History")
def _clear_history_plugin(controller: "GameController") -> None:
    import tkinter.messagebox as messagebox
    try:
        with controller.session_context() as session:  # type: ignore[attr-defined]
            count = session.query(HandHistory).delete()
            session.commit()
        messagebox.showinfo("History Cleared", f"Deleted {count} rows.")
    except Exception as e:
        messagebox.showerror("DB Error", f"Failed to clear history: {e}")
