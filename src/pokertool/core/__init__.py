from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union
from collections import Counter

CardLike = Union["Card", str, Tuple[Union["Rank", str, int], Union["Suit", str]]]


class Rank(Enum):
    """Standard poker ranks with helper properties for legacy Callers."""

    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "T")
    JACK = (11, "J")
    QUEEN = (12, "Q")
    KING = (13, "K")
    ACE = (14, "A")

    def __new__(cls, value: int, symbol: str) -> "Rank":
        member = object.__new__(cls)
        member._value_ = value
        member._symbol = symbol
        return member

    @property
    def sym(self) -> str:
        """Short string symbol (e.g. 'A')."""
        return self._symbol  # type: ignore[attr-defined]

    @property
    def val(self) -> int:
        """Legacy alias for ``value``."""
        return self.value

    @classmethod
    def from_symbol(cls, symbol: Union[str, int, "Rank"]) -> "Rank":
        if isinstance(symbol, Rank):
            return symbol
        if isinstance(symbol, int):
            for rank in cls:
                if rank.value == symbol:
                    return rank
            raise ValueError(f"Unknown rank value: {symbol}")
        text = str(symbol).strip().upper()
        if text in {"10", "T"}:
            text = "T"
        for rank in cls:
            if rank.sym == text:
                return rank
        raise ValueError(f"Bad rank: {symbol!r}")


class Suit(Enum):
    """Standard suits with glyph helpers."""

    SPADES = ("s", "♠")
    HEARTS = ("h", "♥")
    DIAMONDS = ("d", "♦")
    CLUBS = ("c", "♣")

    def __new__(cls, code: str, glyph: str) -> "Suit":
        member = object.__new__(cls)
        member._value_ = code
        member._glyph = glyph
        return member

    @property
    def glyph(self) -> str:
        return self._glyph  # type: ignore[attr-defined]

    @property
    def letter(self) -> str:
        return self.value.upper()

    @classmethod
    def from_symbol(cls, symbol: Union[str, "Suit"]) -> "Suit":
        if isinstance(symbol, Suit):
            return symbol
        text = str(symbol).strip().lower()
        suit_map = {
            "s": cls.SPADES,
            "spade": cls.SPADES,
            "spades": cls.SPADES,
            "♠": cls.SPADES,
            "h": cls.HEARTS,
            "heart": cls.HEARTS,
            "hearts": cls.HEARTS,
            "♥": cls.HEARTS,
            "d": cls.DIAMONDS,
            "diamond": cls.DIAMONDS,
            "diamonds": cls.DIAMONDS,
            "♦": cls.DIAMONDS,
            "c": cls.CLUBS,
            "club": cls.CLUBS,
            "clubs": cls.CLUBS,
            "♣": cls.CLUBS,
        }
        try:
            return suit_map[text]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Bad suit: {symbol!r}") from exc


class Position(Enum):
    """Table positions with simple categorisation helpers."""

    UTG = "UTG"
    UTG1 = "UTG+1"
    UTG2 = "UTG+2"
    MP = "MP"
    MP1 = "MP+1"
    MP2 = "MP+2"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"
    EARLY = "EARLY"
    MIDDLE = "MIDDLE"
    LATE = "LATE"
    BLINDS = "BLINDS"

    def category(self) -> str:
        if self in {Position.CO, Position.BTN, Position.LATE}:
            return "Late"
        if self in {Position.SB, Position.BB, Position.BLINDS}:
            return "Blinds"
        if self in {Position.UTG, Position.UTG1, Position.UTG2, Position.EARLY}:
            return "Early"
        return "Middle"

    def is_late(self) -> bool:
        return self.category() == "Late"


@dataclass(frozen=True)
class Card:
    """Immutable representation of a playing card."""

    rank: Rank
    suit: Suit

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", Rank.from_symbol(self.rank))
        object.__setattr__(self, "suit", Suit.from_symbol(self.suit))

    def __str__(self) -> str:
        return f"{self.rank.sym}{self.suit.value}"


@dataclass(frozen=True)
class HandAnalysisResult:
    strength: float
    advice: str
    details: Dict[str, Any]


def parse_card(value: CardLike) -> Card:
    """Parse a string like ``'As'`` into a :class:`Card`."""

    if isinstance(value, Card):
        return value

    if isinstance(value, (tuple, list)):
        if len(value) != 2:
            raise ValueError(f"Bad card: {value!r}")
        rank, suit = value
        return Card(Rank.from_symbol(rank), Suit.from_symbol(suit))

    text = str(value).strip()
    if len(text) < 2:
        raise ValueError(f"Bad card: {value!r}")

    if text[:2] in {"10", "1 0"}:
        rank_code = "T"
        suit_code = text[2:]
    else:
        rank_code, suit_code = text[0], text[1:]

    if not suit_code:
        raise ValueError(f"Bad card: {value!r}")

    try:
        return Card(Rank.from_symbol(rank_code), Suit.from_symbol(suit_code))
    except ValueError as exc:
        raise ValueError(f"Bad card: {value!r}") from exc


def _normalise_cards(cards: Optional[Sequence[CardLike]]) -> List[Card]:
    return [parse_card(card) for card in (cards or [])]


_HAND_STRENGTH_BASE: Mapping[str, float] = {
    "HIGH_CARD": 4.0,
    "ONE_PAIR": 7.8,
    "TWO_PAIR": 8.5,
    "THREE_OF_A_KIND": 9.0,
    "STRAIGHT": 9.2,
    "FLUSH": 9.3,
    "FULL_HOUSE": 9.6,
    "FOUR_OF_A_KIND": 9.85,
    "STRAIGHT_FLUSH": 10.0,
}


def analyse_hand(
    hole_cards: Sequence[CardLike],
    board_cards: Optional[Sequence[CardLike]] = None,
    position: Position = Position.MP,
    pot: Optional[float] = None,
    to_call: Optional[float] = None,
    num_opponents: int = 1,
) -> HandAnalysisResult:
    """Lightweight strategic analysis returning a score on a 0-10 scale."""

    parsed_hole = _normalise_cards(hole_cards)
    if len(parsed_hole) < 2:
        details = {
            "error": "Need at least two hole cards",
            "hand_type": "UNKNOWN",
            "hole_cards": [str(c) for c in parsed_hole],
            "board_cards": [],
            "position": position.category(),
            "position_raw": position.value,
            "ONE_PAIR": False,
            "TWO_PAIR": False,
            "THREE_OF_A_KIND": False,
            "STRAIGHT": False,
            "FLUSH": False,
            "FULL_HOUSE": False,
            "FOUR_OF_A_KIND": False,
            "STRAIGHT_FLUSH": False,
            "num_opponents": num_opponents,
        }
        return HandAnalysisResult(0.0, "fold", details)

    parsed_board = _normalise_cards(board_cards)
    all_cards = parsed_hole + parsed_board
    rank_counter = Counter(card.rank for card in all_cards)
    suit_counter = Counter(card.suit for card in all_cards)

    unique_ranks = sorted({rank.value for rank in rank_counter}, reverse=True)

    def is_straight(ranks: Iterable[int]) -> bool:
        values = sorted(set(ranks))
        if len(values) < 5:
            return False
        for idx in range(len(values) - 4):
            window = values[idx : idx + 5]
            if window == list(range(window[0], window[0] + 5)):
                return True
        # Wheel straight (A-2-3-4-5)
        wheel = {Rank.ACE.value, Rank.FIVE.value, Rank.FOUR.value, Rank.THREE.value, Rank.TWO.value}
        return wheel.issubset(set(values))

    flush_suit = next((suit for suit, count in suit_counter.items() if count >= 5), None)
    straight_present = is_straight([card.rank.value for card in all_cards])
    straight_flush = False
    if flush_suit:
        suited_cards = [card for card in all_cards if card.suit == flush_suit]
        straight_flush = is_straight([card.rank.value for card in suited_cards])

    rank_multiplicities = sorted(rank_counter.values(), reverse=True)
    pair_count = sum(1 for count in rank_counter.values() if count >= 2)

    if straight_flush:
        hand_type = "STRAIGHT_FLUSH"
    elif 4 in rank_multiplicities:
        hand_type = "FOUR_OF_A_KIND"
    elif 3 in rank_multiplicities and 2 in rank_multiplicities:
        hand_type = "FULL_HOUSE"
    elif flush_suit:
        hand_type = "FLUSH"
    elif straight_present:
        hand_type = "STRAIGHT"
    elif 3 in rank_multiplicities:
        hand_type = "THREE_OF_A_KIND"
    elif pair_count >= 2:
        hand_type = "TWO_PAIR"
    elif 2 in rank_multiplicities:
        hand_type = "ONE_PAIR"
    else:
        hand_type = "HIGH_CARD"

    base_strength = _HAND_STRENGTH_BASE[hand_type]

    if hand_type == "HIGH_CARD":
        highest = unique_ranks[0]
        base_strength = 3.5 + (highest - Rank.TWO.value) * (2.0 / (Rank.ACE.value - Rank.TWO.value))
    elif hand_type == "ONE_PAIR":
        highest_pair = max(rank.value for rank, count in rank_counter.items() if count >= 2)
        base_strength = 7.0 + (highest_pair / Rank.ACE.value) * 2.5
    elif hand_type == "TWO_PAIR":
        pairs = sorted((rank.value for rank, count in rank_counter.items() if count >= 2), reverse=True)
        base_strength = 8.0 + (pairs[0] / Rank.ACE.value) * 1.5
    elif hand_type == "THREE_OF_A_KIND":
        trips = max(rank.value for rank, count in rank_counter.items() if count >= 3)
        base_strength = 8.8 + (trips / Rank.ACE.value) * 0.9

    position_adjustment = {
        "Early": -0.4,
        "Middle": 0.0,
        "Late": 0.4,
        "Blinds": -0.2,
    }[position.category()]

    opponent_pressure = max(num_opponents - 1, 0) * 0.15
    strength = max(0.0, min(10.0, base_strength + position_adjustment - opponent_pressure))

    ratio = None
    if pot and to_call and pot > 0:
        ratio = to_call / pot
        strength -= min(ratio * 2.0, 1.0)
        strength = max(0.0, strength)

    if strength >= 8.5:
        advice = "raise"
    elif strength >= 6.0:
        advice = "call"
    else:
        advice = "fold"

    details: Dict[str, Any] = {
        "hand_type": hand_type,
        "hole_cards": [str(c) for c in parsed_hole],
        "board_cards": [str(c) for c in parsed_board],
        "position": position.category(),
        "position_raw": position.value,
        "num_opponents": num_opponents,
        "pot": pot,
        "to_call": to_call,
        "pot_odds_ratio": ratio,
        "ONE_PAIR": hand_type in {"ONE_PAIR", "TWO_PAIR", "THREE_OF_A_KIND", "FULL_HOUSE", "FOUR_OF_A_KIND", "STRAIGHT_FLUSH"},
        "TWO_PAIR": hand_type in {"TWO_PAIR", "FULL_HOUSE", "STRAIGHT_FLUSH"},
        "THREE_OF_A_KIND": hand_type in {"THREE_OF_A_KIND", "FULL_HOUSE", "FOUR_OF_A_KIND", "STRAIGHT_FLUSH"},
        "STRAIGHT": hand_type in {"STRAIGHT", "STRAIGHT_FLUSH"},
        "FLUSH": hand_type in {"FLUSH", "STRAIGHT_FLUSH"},
        "FULL_HOUSE": hand_type == "FULL_HOUSE",
        "FOUR_OF_A_KIND": hand_type == "FOUR_OF_A_KIND",
        "STRAIGHT_FLUSH": hand_type == "STRAIGHT_FLUSH",
    }

    return HandAnalysisResult(round(strength, 2), advice, details)


__all__ = [
    "Rank",
    "Suit",
    "Position",
    "Card",
    "HandAnalysisResult",
    "parse_card",
    "analyse_hand",
]
