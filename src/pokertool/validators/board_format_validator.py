"""Board Format Validator (v0.6.0)

Validates and parses poker board formats:
- Standard format: "Ks Qs Js" (space-separated)
- Compact format: "KsQsJs" (no spaces)

Supports flop (3 cards), turn (4 cards), and river (5 cards).
"""

import re
from typing import List


class BoardFormatError(Exception):
    """Exception raised for invalid board formats."""
    pass


# Valid poker card ranks and suits
VALID_RANKS = set('23456789TJQKA')
VALID_SUITS = set('shdc')  # spades, hearts, diamonds, clubs


def validate_board_format(board: str) -> bool:
    """Validate board format.

    Args:
        board: Board string (e.g., "Ks Qs Js" or "KsQsJs")

    Returns:
        True if valid, False otherwise
    """
    if not board or not board.strip():
        return False

    try:
        cards = parse_board(board)

        # Check card count (3, 4, or 5 cards)
        if len(cards) < 3 or len(cards) > 5:
            return False

        # Check for duplicates
        if len(cards) != len(set(cards)):
            return False

        # Validate each card
        for card in cards:
            if len(card) != 2:
                return False
            rank, suit = card[0].upper(), card[1].lower()
            if rank not in VALID_RANKS or suit not in VALID_SUITS:
                return False

        return True
    except BoardFormatError:
        return False


def parse_board(board: str) -> List[str]:
    """Parse board string into list of cards.

    Args:
        board: Board string (e.g., "Ks Qs Js" or "KsQsJs")

    Returns:
        List of card strings (e.g., ["Ks", "Qs", "Js"])

    Raises:
        BoardFormatError: If board format is invalid
    """
    board = board.strip()

    if not board:
        raise BoardFormatError("Empty board string")

    # Check if standard format (with spaces)
    if ' ' in board:
        cards = board.split()

        # Validate all cards are 2 characters
        for card in cards:
            if len(card) != 2:
                raise BoardFormatError(f"Invalid card length: {card}")

        return cards

    # Check if compact format (no spaces)
    if len(board) % 2 != 0:
        raise BoardFormatError(f"Compact format must have even length, got {len(board)}")

    # Split into 2-character chunks
    cards = [board[i:i+2] for i in range(0, len(board), 2)]

    return cards


def normalize_board_format(board: str) -> str:
    """Normalize board format to standard (space-separated).

    Args:
        board: Board string in any valid format

    Returns:
        Normalized board string (e.g., "Ks Qs Js")

    Raises:
        BoardFormatError: If board format is invalid
    """
    cards = parse_board(board)

    # Preserve original case but ensure spacing
    return ' '.join(cards)


class BoardFormatValidator:
    """Board format validator class."""

    def validate(self, board: str) -> bool:
        """Validate board format.

        Args:
            board: Board string

        Returns:
            True if valid, False otherwise
        """
        return validate_board_format(board)

    def parse(self, board: str) -> List[str]:
        """Parse board into list of cards.

        Args:
            board: Board string

        Returns:
            List of card strings

        Raises:
            BoardFormatError: If board format is invalid
        """
        return parse_board(board)

    def normalize(self, board: str) -> str:
        """Normalize board format to standard.

        Args:
            board: Board string

        Returns:
            Normalized board string

        Raises:
            BoardFormatError: If board format is invalid
        """
        return normalize_board_format(board)

    def get_card_count(self, board: str) -> int:
        """Get number of cards in board.

        Args:
            board: Board string

        Returns:
            Number of cards
        """
        try:
            cards = parse_board(board)
            return len(cards)
        except BoardFormatError:
            return 0

    def is_flop(self, board: str) -> bool:
        """Check if board is a flop (3 cards).

        Args:
            board: Board string

        Returns:
            True if flop, False otherwise
        """
        return self.get_card_count(board) == 3

    def is_turn(self, board: str) -> bool:
        """Check if board is a turn (4 cards).

        Args:
            board: Board string

        Returns:
            True if turn, False otherwise
        """
        return self.get_card_count(board) == 4

    def is_river(self, board: str) -> bool:
        """Check if board is a river (5 cards).

        Args:
            board: Board string

        Returns:
            True if river, False otherwise
        """
        return self.get_card_count(board) == 5
