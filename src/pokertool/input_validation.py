#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Input Validation and Sanitization Layer
========================================

Comprehensive input validation and sanitization to prevent errors
and improve reliability.

Features:
- Poker card validation
- Bet amount validation and sanitization
- Player data validation
- Table state validation
- Automatic type coercion
- Range checking
- Format normalization

Version: 69.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import re
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Validation Result
# ============================================================================

@dataclass
class ValidationResult:
    """Result of validation operation."""
    valid: bool
    value: Any = None
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# ============================================================================
# Card Validation
# ============================================================================

class CardValidator:
    """
    Validate and normalize poker cards.

    Examples:
        "As" -> "As" (Ace of spades)
        "10h" -> "Th" (Ten of hearts)
        "KD" -> "Kd" (King of diamonds, normalized to lowercase suit)
    """

    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    SUITS = ['c', 'd', 'h', 's']  # clubs, diamonds, hearts, spades

    @classmethod
    def validate(cls, card: str) -> ValidationResult:
        """
        Validate and normalize a poker card.

        Args:
            card: Card string (e.g., "As", "10h", "Kd")

        Returns:
            ValidationResult with normalized card or error
        """
        if not card or not isinstance(card, str):
            return ValidationResult(
                valid=False,
                error="Card must be a non-empty string"
            )

        card = card.strip()

        # Handle "10" as "T"
        card = card.replace("10", "T")

        if len(card) != 2:
            return ValidationResult(
                valid=False,
                error=f"Card must be 2 characters (got '{card}')"
            )

        rank = card[0].upper()
        suit = card[1].lower()

        if rank not in cls.RANKS:
            return ValidationResult(
                valid=False,
                error=f"Invalid rank '{rank}' (must be one of {cls.RANKS})"
            )

        if suit not in cls.SUITS:
            return ValidationResult(
                valid=False,
                error=f"Invalid suit '{suit}' (must be one of {cls.SUITS})"
            )

        normalized = f"{rank}{suit}"

        return ValidationResult(
            valid=True,
            value=normalized
        )

    @classmethod
    def validate_hand(cls, cards: List[str]) -> ValidationResult:
        """
        Validate a poker hand (2 or 5 cards).

        Args:
            cards: List of card strings

        Returns:
            ValidationResult with normalized cards or error
        """
        if not isinstance(cards, list):
            return ValidationResult(
                valid=False,
                error="Hand must be a list"
            )

        if len(cards) not in [0, 2, 5]:
            return ValidationResult(
                valid=False,
                error=f"Hand must have 0, 2, or 5 cards (got {len(cards)})"
            )

        normalized = []
        warnings = []
        seen = set()

        for card in cards:
            result = cls.validate(card)
            if not result.valid:
                return ValidationResult(
                    valid=False,
                    error=f"Invalid card: {result.error}"
                )

            # Check for duplicates
            if result.value in seen:
                warnings.append(f"Duplicate card: {result.value}")

            seen.add(result.value)
            normalized.append(result.value)

        return ValidationResult(
            valid=True,
            value=normalized,
            warnings=warnings
        )


# ============================================================================
# Bet Amount Validation
# ============================================================================

class BetValidator:
    """Validate and sanitize bet amounts."""

    MIN_BET = 0.0
    MAX_BET = 1_000_000.0  # $1M max

    @classmethod
    def validate(
        cls,
        amount: Union[int, float, str],
        min_bet: Optional[float] = None,
        max_bet: Optional[float] = None
    ) -> ValidationResult:
        """
        Validate and normalize a bet amount.

        Args:
            amount: Bet amount (can be string like "$100.50")
            min_bet: Minimum allowed bet
            max_bet: Maximum allowed bet

        Returns:
            ValidationResult with normalized float or error
        """
        min_bet = min_bet or cls.MIN_BET
        max_bet = max_bet or cls.MAX_BET

        # Convert string to number
        if isinstance(amount, str):
            amount_str = amount.strip()

            # Detect European format (comma as decimal separator)
            # If comma is followed by exactly 2 digits at end, it's decimal
            european_decimal_pattern = r',\d{2}(?:\D|$)'
            is_european = bool(re.search(european_decimal_pattern, amount_str))

            if is_european:
                # European format: remove thousand separators (periods), convert comma to period
                amount_str = re.sub(r'[£$€¢]', '', amount_str)
                amount_str = amount_str.replace('.', '')  # Remove thousand separators
                amount_str = amount_str.replace(',', '.')  # Convert decimal comma to period
            else:
                # US format: remove currency symbols and thousand separators (commas)
                amount_str = re.sub(r'[£$€¢,]', '', amount_str)

            try:
                amount = float(amount_str)
            except ValueError:
                return ValidationResult(
                    valid=False,
                    error=f"Cannot parse amount: '{amount}'"
                )

        # Convert to float
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return ValidationResult(
                valid=False,
                error=f"Invalid amount type: {type(amount)}"
            )

        # Check for invalid values
        if amount != amount:  # NaN check
            return ValidationResult(
                valid=False,
                error="Amount is NaN"
            )

        if amount < 0:
            return ValidationResult(
                valid=False,
                error=f"Amount cannot be negative: {amount}"
            )

        # Round to 2 decimal places
        amount = round(amount, 2)

        # Check range
        warnings = []
        if amount < min_bet:
            warnings.append(f"Amount {amount} is below minimum {min_bet}")
        if amount > max_bet:
            warnings.append(f"Amount {amount} exceeds maximum {max_bet}")

        return ValidationResult(
            valid=True,
            value=amount,
            warnings=warnings
        )


# ============================================================================
# Player Data Validation
# ============================================================================

class PlayerValidator:
    """Validate player data."""

    MAX_PLAYERS = 10
    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 50

    @classmethod
    def validate_name(cls, name: str) -> ValidationResult:
        """
        Validate player name.

        Args:
            name: Player name string

        Returns:
            ValidationResult with sanitized name or error
        """
        if not isinstance(name, str):
            return ValidationResult(
                valid=False,
                error="Name must be a string"
            )

        # Strip whitespace
        name = name.strip()

        if len(name) < cls.MIN_NAME_LENGTH:
            return ValidationResult(
                valid=False,
                error="Name is too short"
            )

        if len(name) > cls.MAX_NAME_LENGTH:
            return ValidationResult(
                valid=False,
                error=f"Name too long (max {cls.MAX_NAME_LENGTH} chars)"
            )

        # Remove control characters
        name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)

        # Check for suspicious patterns (SQL injection, XSS)
        warnings = []
        if any(keyword in name.lower() for keyword in ['select', 'drop', 'union', '<script', 'javascript:']):
            warnings.append("Name contains suspicious pattern")

        return ValidationResult(
            valid=True,
            value=name,
            warnings=warnings
        )

    @classmethod
    def validate_seat(cls, seat: Union[int, str]) -> ValidationResult:
        """
        Validate seat number.

        Args:
            seat: Seat number (1-10)

        Returns:
            ValidationResult with int seat or error
        """
        try:
            seat = int(seat)
        except (ValueError, TypeError):
            return ValidationResult(
                valid=False,
                error=f"Invalid seat type: {type(seat)}"
            )

        if seat < 1 or seat > cls.MAX_PLAYERS:
            return ValidationResult(
                valid=False,
                error=f"Seat must be 1-{cls.MAX_PLAYERS} (got {seat})"
            )

        return ValidationResult(
            valid=True,
            value=seat
        )

    @classmethod
    def validate_player_data(cls, player_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete player data dictionary.

        Args:
            player_data: Dict with player information

        Returns:
            ValidationResult with sanitized data or error
        """
        if not isinstance(player_data, dict):
            return ValidationResult(
                valid=False,
                error="Player data must be a dict"
            )

        sanitized = {}
        warnings = []

        # Validate name
        if 'name' in player_data:
            result = cls.validate_name(player_data['name'])
            if result.valid:
                sanitized['name'] = result.value
                warnings.extend(result.warnings)
            else:
                return ValidationResult(
                    valid=False,
                    error=f"Invalid name: {result.error}"
                )

        # Validate stack
        if 'stack' in player_data:
            result = BetValidator.validate(player_data['stack'])
            if result.valid:
                sanitized['stack'] = result.value
                warnings.extend(result.warnings)

        # Validate bet
        if 'bet' in player_data:
            result = BetValidator.validate(player_data['bet'])
            if result.valid:
                sanitized['bet'] = result.value

        # Copy other fields with type checking
        for key in ['vpip', 'af', 'pfr', 'wtsd']:
            if key in player_data:
                value = player_data[key]
                if value is not None:
                    try:
                        value = float(value)
                        if 0 <= value <= 100:  # Percentage
                            sanitized[key] = round(value, 1)
                    except (ValueError, TypeError):
                        warnings.append(f"Invalid {key}: {value}")

        # Boolean fields
        for key in ['is_active', 'is_dealer', 'is_turn']:
            if key in player_data:
                sanitized[key] = bool(player_data[key])

        # Status field
        if 'status' in player_data:
            status = str(player_data['status'])
            if status in ['Active', 'Sitting Out', 'Empty', 'Folded']:
                sanitized['status'] = status

        return ValidationResult(
            valid=True,
            value=sanitized,
            warnings=warnings
        )


# ============================================================================
# Table State Validation
# ============================================================================

class TableValidator:
    """Validate table state data."""

    VALID_STAGES = ['preflop', 'flop', 'turn', 'river', 'showdown', 'unknown']

    @classmethod
    def validate_stage(cls, stage: str) -> ValidationResult:
        """Validate game stage."""
        if not isinstance(stage, str):
            return ValidationResult(
                valid=False,
                error="Stage must be a string"
            )

        stage = stage.lower().strip()

        if stage not in cls.VALID_STAGES:
            return ValidationResult(
                valid=False,
                error=f"Invalid stage '{stage}' (must be one of {cls.VALID_STAGES})"
            )

        return ValidationResult(
            valid=True,
            value=stage
        )

    @classmethod
    def validate_table_data(cls, table_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete table data.

        Args:
            table_data: Dict with table information

        Returns:
            ValidationResult with sanitized data or error
        """
        if not isinstance(table_data, dict):
            return ValidationResult(
                valid=False,
                error="Table data must be a dict"
            )

        sanitized = {}
        warnings = []

        # Validate pot
        if 'pot' in table_data or 'pot_size' in table_data:
            pot = table_data.get('pot') or table_data.get('pot_size', 0)
            result = BetValidator.validate(pot)
            if result.valid:
                sanitized['pot'] = result.value

        # Validate blinds
        for blind_key in ['small_blind', 'big_blind', 'ante', 'sb', 'bb']:
            if blind_key in table_data:
                result = BetValidator.validate(table_data[blind_key])
                if result.valid:
                    sanitized[blind_key] = result.value

        # Validate board cards
        if 'board' in table_data or 'board_cards' in table_data:
            board = table_data.get('board') or table_data.get('board_cards', [])
            if board:
                result = CardValidator.validate_hand(board)
                if result.valid:
                    sanitized['board'] = result.value
                    warnings.extend(result.warnings)
                else:
                    warnings.append(f"Invalid board: {result.error}")
                    sanitized['board'] = []
            else:
                sanitized['board'] = []

        # Validate stage
        if 'stage' in table_data:
            result = cls.validate_stage(table_data['stage'])
            if result.valid:
                sanitized['stage'] = result.value
            else:
                sanitized['stage'] = 'unknown'
                warnings.append(result.error)

        # Validate players
        if 'players' in table_data:
            players = table_data['players']
            if isinstance(players, dict):
                sanitized_players = {}
                for seat, player_data in players.items():
                    # Validate seat
                    seat_result = PlayerValidator.validate_seat(seat)
                    if not seat_result.valid:
                        warnings.append(f"Invalid seat {seat}: {seat_result.error}")
                        continue

                    # Validate player data
                    player_result = PlayerValidator.validate_player_data(player_data)
                    if player_result.valid:
                        sanitized_players[seat_result.value] = player_result.value
                        warnings.extend(player_result.warnings)
                    else:
                        warnings.append(f"Invalid player at seat {seat}: {player_result.error}")

                sanitized['players'] = sanitized_players

        # Safe integer fields
        for key in ['dealer_seat', 'active_seat', 'hero_seat']:
            if key in table_data:
                try:
                    value = int(table_data[key]) if table_data[key] is not None else None
                    if value is not None and 1 <= value <= 10:
                        sanitized[key] = value
                except (ValueError, TypeError):
                    warnings.append(f"Invalid {key}: {table_data[key]}")

        return ValidationResult(
            valid=True,
            value=sanitized,
            warnings=warnings
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def validate_card(card: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Simple card validation helper.

    Args:
        card: Card string

    Returns:
        (valid, normalized_card, error_message)
    """
    result = CardValidator.validate(card)
    return (result.valid, result.value, result.error)


def validate_bet(amount: Union[int, float, str]) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Simple bet validation helper.

    Args:
        amount: Bet amount

    Returns:
        (valid, normalized_amount, error_message)
    """
    result = BetValidator.validate(amount)
    return (result.valid, result.value, result.error)


def sanitize_table_data(table_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize table data and return clean version.

    Args:
        table_data: Raw table data

    Returns:
        Sanitized table data
    """
    result = TableValidator.validate_table_data(table_data)

    if result.warnings:
        logger.warning(f"Table data validation warnings: {', '.join(result.warnings)}")

    return result.value if result.valid else {}


# ============================================================================
# Testing
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Input Validation System Test")
    print("=" * 60)

    # Test card validation
    print("\n1. Card Validation:")
    test_cards = ["As", "10h", "Kd", "XX", "5z", ""]
    for card in test_cards:
        result = CardValidator.validate(card)
        print(f"  '{card}' -> {result.valid}: {result.value or result.error}")

    # Test bet validation
    print("\n2. Bet Validation:")
    test_bets = [100, "$100.50", "£1,234.56", -50, "abc", 1_000_000]
    for bet in test_bets:
        result = BetValidator.validate(bet)
        print(f"  {bet} -> {result.valid}: {result.value or result.error}")

    # Test player validation
    print("\n3. Player Validation:")
    player = {
        'name': 'TestPlayer',
        'stack': '$100.50',
        'bet': 25,
        'vpip': 30.5,
        'is_active': True
    }
    result = PlayerValidator.validate_player_data(player)
    print(f"  Valid: {result.valid}")
    print(f"  Sanitized: {result.value}")

    # Test table validation
    print("\n4. Table Validation:")
    table = {
        'pot': '$150.00',
        'board': ['As', 'Kd', 'Qh'],
        'stage': 'flop',
        'players': {
            1: {'name': 'Player1', 'stack': 100},
            2: {'name': 'Player2', 'stack': 200}
        }
    }
    result = TableValidator.validate_table_data(table)
    print(f"  Valid: {result.valid}")
    print(f"  Warnings: {result.warnings}")
    print(f"  Sanitized pot: {result.value.get('pot')}")

    print("\n" + "=" * 60)
