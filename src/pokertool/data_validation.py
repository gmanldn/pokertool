#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Validation Module
======================

Comprehensive validation for all database insertions to ensure data integrity,
prevent corruption, and catch errors early.

Module: pokertool.data_validation
Version: 1.0.0
Author: PokerTool Development Team
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


class ValidationSeverity(Enum):
    """Severity levels for validation errors."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)


class HandValidator:
    """Validates poker hand strings."""

    # Valid card ranks and suits
    RANKS = set('AKQJT98765432')
    SUITS = set('shdc')

    # Regex patterns
    CARD_PATTERN = re.compile(r'^[AKQJT98765432][shdc]$')
    HAND_PATTERN = re.compile(r'^[AKQJT98765432][shdc] [AKQJT98765432][shdc]$')
    BOARD_PATTERN = re.compile(r'^([AKQJT98765432][shdc] ){2,4}[AKQJT98765432][shdc]$')

    @classmethod
    def validate_card(cls, card: str) -> ValidationResult:
        """Validate a single card."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        if not card:
            result.add_error("Card is empty")
            return result

        if not isinstance(card, str):
            result.add_error(f"Card must be string, got {type(card)}")
            return result

        if len(card) != 2:
            result.add_error(f"Card must be 2 characters, got {len(card)}: '{card}'")
            return result

        rank, suit = card[0], card[1]

        if rank not in cls.RANKS:
            result.add_error(f"Invalid rank '{rank}' in card '{card}'")

        if suit not in cls.SUITS:
            result.add_error(f"Invalid suit '{suit}' in card '{card}'")

        return result

    @classmethod
    def validate_hand(cls, hand: str) -> ValidationResult:
        """Validate a poker hand (e.g., 'As Kd')."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        if not hand:
            result.add_error("Hand is empty")
            return result

        if not isinstance(hand, str):
            result.add_error(f"Hand must be string, got {type(hand)}")
            return result

        # Check length constraints
        if len(hand) > 50:
            result.add_error(f"Hand exceeds maximum length of 50 characters: {len(hand)}")
            return result

        # Check basic format
        if not cls.HAND_PATTERN.match(hand):
            result.add_error(f"Hand format invalid: '{hand}'. Expected format: 'As Kd'")
            return result

        # Parse and validate individual cards
        cards = hand.split()
        if len(cards) != 2:
            result.add_error(f"Hand must contain exactly 2 cards, got {len(cards)}")
            return result

        # Validate each card
        for card in cards:
            card_result = cls.validate_card(card)
            if not card_result.is_valid:
                result.errors.extend(card_result.errors)
                result.is_valid = False

        # Check for duplicates
        if len(cards) != len(set(cards)):
            result.add_error(f"Hand contains duplicate cards: '{hand}'")

        return result

    @classmethod
    def validate_board(cls, board: Optional[str]) -> ValidationResult:
        """Validate a poker board (e.g., 'As Kd Qh')."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Board can be None
        if board is None:
            return result

        if not isinstance(board, str):
            result.add_error(f"Board must be string or None, got {type(board)}")
            return result

        if not board.strip():
            result.add_warning("Board is empty string (should be None)")
            return result

        # Check length constraints
        if len(board) > 50:
            result.add_error(f"Board exceeds maximum length of 50 characters: {len(board)}")
            return result

        # Check basic format
        if not cls.BOARD_PATTERN.match(board):
            result.add_error(f"Board format invalid: '{board}'. Expected format: 'As Kd Qh' (3-5 cards)")
            return result

        # Parse and validate individual cards
        cards = board.split()
        if not (3 <= len(cards) <= 5):
            result.add_error(f"Board must contain 3-5 cards, got {len(cards)}")
            return result

        # Validate each card
        for card in cards:
            card_result = cls.validate_card(card)
            if not card_result.is_valid:
                result.errors.extend(card_result.errors)
                result.is_valid = False

        # Check for duplicates
        if len(cards) != len(set(cards)):
            result.add_error(f"Board contains duplicate cards: '{board}'")

        return result


class AnalysisValidator:
    """Validates analysis result strings."""

    @classmethod
    def validate_analysis(cls, analysis: str) -> ValidationResult:
        """Validate analysis result."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        if not analysis:
            result.add_warning("Analysis is empty")
            return result

        if not isinstance(analysis, str):
            result.add_error(f"Analysis must be string, got {type(analysis)}")
            return result

        # Check length constraints
        if len(analysis) > 10000:
            result.add_error(f"Analysis exceeds maximum length of 10000 characters: {len(analysis)}")

        # Check for suspicious patterns
        if analysis.count('\x00') > 0:
            result.add_error("Analysis contains null bytes")

        # Warn if analysis is very short
        if len(analysis) < 10:
            result.add_warning(f"Analysis seems too short ({len(analysis)} chars)")

        return result


class SessionValidator:
    """Validates session data."""

    SESSION_ID_PATTERN = re.compile(r'^[a-f0-9]{32}$')

    @classmethod
    def validate_session_id(cls, session_id: Optional[str]) -> ValidationResult:
        """Validate session ID."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        if session_id is None:
            return result

        if not isinstance(session_id, str):
            result.add_error(f"Session ID must be string or None, got {type(session_id)}")
            return result

        if not session_id.strip():
            result.add_warning("Session ID is empty string (should be None)")
            return result

        if not cls.SESSION_ID_PATTERN.match(session_id):
            result.add_error(f"Session ID format invalid: '{session_id}'. Expected 32 hex characters")

        return result


class MetadataValidator:
    """Validates metadata dictionaries."""

    MAX_METADATA_SIZE = 100000  # 100KB JSON
    MAX_NESTING_DEPTH = 5

    @classmethod
    def validate_metadata(cls, metadata: Optional[Dict[str, Any]]) -> ValidationResult:
        """Validate metadata dictionary."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        if metadata is None:
            return result

        if not isinstance(metadata, dict):
            result.add_error(f"Metadata must be dict or None, got {type(metadata)}")
            return result

        # Check size
        import json
        try:
            json_str = json.dumps(metadata)
            if len(json_str) > cls.MAX_METADATA_SIZE:
                result.add_error(f"Metadata JSON exceeds maximum size: {len(json_str)} bytes")
        except (TypeError, ValueError) as e:
            result.add_error(f"Metadata not JSON serializable: {e}")

        # Check nesting depth
        def check_depth(obj, current_depth=0):
            if current_depth > cls.MAX_NESTING_DEPTH:
                return False
            if isinstance(obj, dict):
                return all(check_depth(v, current_depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                return all(check_depth(item, current_depth + 1) for item in obj)
            return True

        if not check_depth(metadata):
            result.add_error(f"Metadata nesting exceeds maximum depth of {cls.MAX_NESTING_DEPTH}")

        # Check for suspicious keys
        suspicious_keys = ['__proto__', 'constructor', 'prototype']
        for key in metadata.keys():
            if key in suspicious_keys:
                result.add_warning(f"Metadata contains suspicious key: '{key}'")

        return result


class ComprehensiveValidator:
    """Validates complete database insertion data."""

    @classmethod
    def validate_hand_analysis(
        cls,
        hand: str,
        board: Optional[str],
        analysis: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate all data for hand analysis insertion.

        Args:
            hand: Hole cards (e.g., 'As Kd')
            board: Board cards (e.g., 'Ah Kh Qh')
            analysis: Analysis result text
            session_id: Optional session identifier
            metadata: Optional metadata dictionary

        Returns:
            ValidationResult with all errors and warnings
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Validate hand
        hand_result = HandValidator.validate_hand(hand)
        result.errors.extend(hand_result.errors)
        result.warnings.extend(hand_result.warnings)
        if not hand_result.is_valid:
            result.is_valid = False

        # Validate board
        board_result = HandValidator.validate_board(board)
        result.errors.extend(board_result.errors)
        result.warnings.extend(board_result.warnings)
        if not board_result.is_valid:
            result.is_valid = False

        # Check hand-board card conflicts
        if board and hand_result.is_valid and board_result.is_valid:
            hand_cards = set(hand.split())
            board_cards = set(board.split())
            conflicts = hand_cards & board_cards
            if conflicts:
                result.add_error(f"Cards appear in both hand and board: {conflicts}")

        # Validate analysis
        analysis_result = AnalysisValidator.validate_analysis(analysis)
        result.errors.extend(analysis_result.errors)
        result.warnings.extend(analysis_result.warnings)
        if not analysis_result.is_valid:
            result.is_valid = False

        # Validate session ID
        session_result = SessionValidator.validate_session_id(session_id)
        result.errors.extend(session_result.errors)
        result.warnings.extend(session_result.warnings)
        if not session_result.is_valid:
            result.is_valid = False

        # Validate metadata
        metadata_result = MetadataValidator.validate_metadata(metadata)
        result.errors.extend(metadata_result.errors)
        result.warnings.extend(metadata_result.warnings)
        if not metadata_result.is_valid:
            result.is_valid = False

        return result

    @classmethod
    def validate_and_raise(
        cls,
        hand: str,
        board: Optional[str],
        analysis: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Validate data and raise ValidationError if invalid.

        Raises:
            ValidationError: If validation fails
        """
        result = cls.validate_hand_analysis(hand, board, analysis, session_id, metadata)

        # Log warnings
        for warning in result.warnings:
            logger.warning(f"Data validation warning: {warning}")

        # Raise on errors
        if not result.is_valid:
            error_msg = "Data validation failed:\n" + "\n".join(f"  - {e}" for e in result.errors)
            logger.error(error_msg)
            raise ValidationError(error_msg)


# Convenience function
def validate_before_insert(
    hand: str,
    board: Optional[str],
    analysis: str,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Validate all data before database insertion.

    Raises:
        ValidationError: If validation fails
    """
    ComprehensiveValidator.validate_and_raise(hand, board, analysis, session_id, metadata)
