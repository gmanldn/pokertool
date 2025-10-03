from enum import Enum
import logging


# --- Suit Enum ---
class Suit(Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"  # added to fix missing attribute


# --- Rank Enum ---
class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


# --- Card ---
class Card:
    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.rank.value} of {self.suit.value}"

    def __eq__(self, other):
        return isinstance(other, Card) and self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))


# --- Player Position ---
class Position(Enum):
    EARLY = "early"
    MIDDLE = "middle"
    LATE = "late"
    BLINDS = "blinds"

    def is_late(self):
        return self.value == "late"


# --- Example Poker Logic Helpers ---
def get_hand_strength(cards):
    """Stub for hand evaluation."""
    # TODO: integrate a real hand evaluation library
    logging.debug(f"Evaluating hand strength for: {cards}")
    return 0.5


def advise_action(position: Position, cards):
    """Simple example advice system."""
    strength = get_hand_strength(cards)
    logging.debug(f"Hand strength {strength} at position {position}")
    if strength > 0.7:
        return "Raise"
    elif strength > 0.4:
        return "Call"
    else:
        return "Fold"
