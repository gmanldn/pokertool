#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detection Sanity Checks Module
===============================

Validates detection results to ensure logical consistency and catch errors early.
Prevents propagation of invalid data through the system.

Module: pokertool.detection_sanity_checks
Version: 1.0.0
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SanityCheckSeverity(Enum):
    """Severity levels for sanity check violations."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SanityCheckResult:
    """Result of a sanity check."""
    passed: bool
    violations: List[Dict[str, Any]]

    def add_violation(self, field: str, message: str, severity: SanityCheckSeverity, value: Any = None):
        """Add a violation to the result."""
        self.violations.append({
            'field': field,
            'message': message,
            'severity': severity.value,
            'value': value
        })
        if severity in [SanityCheckSeverity.ERROR, SanityCheckSeverity.CRITICAL]:
            self.passed = False


class DetectionSanityChecker:
    """Validates detection results for logical consistency."""

    @staticmethod
    def check_pot_size(pot_size: Optional[float]) -> SanityCheckResult:
        """Validate pot size."""
        result = SanityCheckResult(passed=True, violations=[])

        if pot_size is None:
            return result  # Null is acceptable

        if not isinstance(pot_size, (int, float)):
            result.add_violation(
                'pot_size',
                f'Pot size must be numeric, got {type(pot_size)}',
                SanityCheckSeverity.ERROR,
                pot_size
            )
            return result

        if pot_size < 0:
            result.add_violation(
                'pot_size',
                'Pot size cannot be negative',
                SanityCheckSeverity.ERROR,
                pot_size
            )

        if pot_size > 1_000_000:
            result.add_violation(
                'pot_size',
                'Pot size suspiciously large (>1M)',
                SanityCheckSeverity.WARNING,
                pot_size
            )

        return result

    @staticmethod
    def check_stack_size(stack_size: Optional[float], player_name: str = "Unknown") -> SanityCheckResult:
        """Validate stack size."""
        result = SanityCheckResult(passed=True, violations=[])

        if stack_size is None:
            return result

        if not isinstance(stack_size, (int, float)):
            result.add_violation(
                'stack_size',
                f'Stack size must be numeric for {player_name}',
                SanityCheckSeverity.ERROR,
                stack_size
            )
            return result

        if stack_size < 0:
            result.add_violation(
                'stack_size',
                f'Stack size cannot be negative for {player_name}',
                SanityCheckSeverity.ERROR,
                stack_size
            )

        if stack_size > 10_000_000:
            result.add_violation(
                'stack_size',
                f'Stack size suspiciously large for {player_name} (>10M)',
                SanityCheckSeverity.WARNING,
                stack_size
            )

        return result

    @staticmethod
    def check_bet_amount(bet_amount: Optional[float], pot_size: Optional[float] = None) -> SanityCheckResult:
        """Validate bet amount."""
        result = SanityCheckResult(passed=True, violations=[])

        if bet_amount is None:
            return result

        if not isinstance(bet_amount, (int, float)):
            result.add_violation(
                'bet_amount',
                f'Bet amount must be numeric, got {type(bet_amount)}',
                SanityCheckSeverity.ERROR,
                bet_amount
            )
            return result

        if bet_amount < 0:
            result.add_violation(
                'bet_amount',
                'Bet amount cannot be negative',
                SanityCheckSeverity.ERROR,
                bet_amount
            )

        # Check if bet is reasonable relative to pot
        if pot_size and bet_amount > pot_size * 100:
            result.add_violation(
                'bet_amount',
                f'Bet amount ({bet_amount}) is >100x pot size ({pot_size})',
                SanityCheckSeverity.WARNING,
                bet_amount
            )

        return result

    @staticmethod
    def check_player_count(num_players: Optional[int]) -> SanityCheckResult:
        """Validate number of players."""
        result = SanityCheckResult(passed=True, violations=[])

        if num_players is None:
            return result

        if not isinstance(num_players, int):
            result.add_violation(
                'num_players',
                f'Player count must be integer, got {type(num_players)}',
                SanityCheckSeverity.ERROR,
                num_players
            )
            return result

        if num_players < 2:
            result.add_violation(
                'num_players',
                'Must have at least 2 players',
                SanityCheckSeverity.ERROR,
                num_players
            )

        if num_players > 10:
            result.add_violation(
                'num_players',
                'More than 10 players detected',
                SanityCheckSeverity.ERROR,
                num_players
            )

        return result

    @staticmethod
    def check_board_cards(board_cards: Optional[List[str]]) -> SanityCheckResult:
        """Validate board cards."""
        result = SanityCheckResult(passed=True, violations=[])

        if not board_cards:
            return result  # No board cards is valid (preflop)

        if not isinstance(board_cards, list):
            result.add_violation(
                'board_cards',
                f'Board cards must be list, got {type(board_cards)}',
                SanityCheckSeverity.ERROR,
                board_cards
            )
            return result

        # Valid board sizes: 3 (flop), 4 (turn), 5 (river)
        if len(board_cards) not in [0, 3, 4, 5]:
            result.add_violation(
                'board_cards',
                f'Invalid board card count: {len(board_cards)} (must be 0, 3, 4, or 5)',
                SanityCheckSeverity.ERROR,
                len(board_cards)
            )

        # Check for duplicates
        if len(board_cards) != len(set(board_cards)):
            result.add_violation(
                'board_cards',
                'Duplicate cards detected on board',
                SanityCheckSeverity.CRITICAL,
                board_cards
            )

        return result

    @staticmethod
    def check_hole_cards(hole_cards: Optional[List[str]]) -> SanityCheckResult:
        """Validate hole cards."""
        result = SanityCheckResult(passed=True, violations=[])

        if not hole_cards:
            return result  # No hole cards is valid (not visible yet)

        if not isinstance(hole_cards, list):
            result.add_violation(
                'hole_cards',
                f'Hole cards must be list, got {type(hole_cards)}',
                SanityCheckSeverity.ERROR,
                hole_cards
            )
            return result

        # Texas Hold'em: exactly 2 hole cards
        if len(hole_cards) != 2:
            result.add_violation(
                'hole_cards',
                f'Must have exactly 2 hole cards, got {len(hole_cards)}',
                SanityCheckSeverity.ERROR,
                len(hole_cards)
            )

        # Check for duplicates
        if len(hole_cards) != len(set(hole_cards)):
            result.add_violation(
                'hole_cards',
                'Duplicate hole cards detected',
                SanityCheckSeverity.CRITICAL,
                hole_cards
            )

        return result

    @staticmethod
    def check_player_action(action: Optional[str]) -> SanityCheckResult:
        """Validate player action."""
        result = SanityCheckResult(passed=True, violations=[])

        if not action:
            return result

        if not isinstance(action, str):
            result.add_violation(
                'player_action',
                f'Action must be string, got {type(action)}',
                SanityCheckSeverity.ERROR,
                action
            )
            return result

        valid_actions = ['fold', 'check', 'call', 'bet', 'raise', 'all-in']
        action_lower = action.lower()

        if action_lower not in valid_actions:
            result.add_violation(
                'player_action',
                f'Invalid action: {action} (must be one of {valid_actions})',
                SanityCheckSeverity.ERROR,
                action
            )

        return result

    @staticmethod
    def check_game_state_consistency(game_state: Dict[str, Any]) -> SanityCheckResult:
        """Comprehensive validation of entire game state."""
        result = SanityCheckResult(passed=True, violations=[])

        # Check pot size
        if 'pot_size' in game_state:
            pot_check = DetectionSanityChecker.check_pot_size(game_state['pot_size'])
            result.violations.extend(pot_check.violations)
            if not pot_check.passed:
                result.passed = False

        # Check player count
        if 'num_players' in game_state:
            player_check = DetectionSanityChecker.check_player_count(game_state['num_players'])
            result.violations.extend(player_check.violations)
            if not player_check.passed:
                result.passed = False

        # Check board cards
        if 'board_cards' in game_state:
            board_check = DetectionSanityChecker.check_board_cards(game_state['board_cards'])
            result.violations.extend(board_check.violations)
            if not board_check.passed:
                result.passed = False

        # Check hole cards
        if 'hole_cards' in game_state:
            hole_check = DetectionSanityChecker.check_hole_cards(game_state['hole_cards'])
            result.violations.extend(hole_check.violations)
            if not hole_check.passed:
                result.passed = False

        # Check bet amount vs pot size
        if 'bet_amount' in game_state:
            bet_check = DetectionSanityChecker.check_bet_amount(
                game_state.get('bet_amount'),
                game_state.get('pot_size')
            )
            result.violations.extend(bet_check.violations)
            if not bet_check.passed:
                result.passed = False

        # Check for card conflicts (hole cards vs board cards)
        if 'hole_cards' in game_state and 'board_cards' in game_state:
            hole_cards = game_state.get('hole_cards', [])
            board_cards = game_state.get('board_cards', [])
            if hole_cards and board_cards:
                conflicts = set(hole_cards) & set(board_cards)
                if conflicts:
                    result.add_violation(
                        'card_conflict',
                        f'Cards appear in both hole cards and board: {conflicts}',
                        SanityCheckSeverity.CRITICAL,
                        conflicts
                    )

        # Check stack sizes for all players
        if 'players' in game_state and isinstance(game_state['players'], list):
            for player in game_state['players']:
                if isinstance(player, dict) and 'stack' in player:
                    player_name = player.get('name', 'Unknown')
                    stack_check = DetectionSanityChecker.check_stack_size(
                        player['stack'],
                        player_name
                    )
                    result.violations.extend(stack_check.violations)
                    if not stack_check.passed:
                        result.passed = False

        # Check street progression logic
        if 'street' in game_state and 'board_cards' in game_state:
            street = game_state['street']
            board_cards = game_state.get('board_cards', [])
            expected_cards = {
                'preflop': 0,
                'flop': 3,
                'turn': 4,
                'river': 5
            }
            if street in expected_cards and len(board_cards) != expected_cards[street]:
                result.add_violation(
                    'street_consistency',
                    f'Street "{street}" should have {expected_cards[street]} board cards, got {len(board_cards)}',
                    SanityCheckSeverity.WARNING,
                    {'street': street, 'card_count': len(board_cards)}
                )

        return result

    @staticmethod
    def validate_and_log(game_state: Dict[str, Any], context: str = "") -> bool:
        """
        Validate game state and log violations.

        Args:
            game_state: Game state dictionary to validate
            context: Context string for logging

        Returns:
            True if passed, False otherwise
        """
        result = DetectionSanityChecker.check_game_state_consistency(game_state)

        if result.violations:
            context_str = f" [{context}]" if context else ""
            for violation in result.violations:
                severity = violation['severity']
                field = violation['field']
                message = violation['message']
                value = violation.get('value', 'N/A')

                if severity == 'critical':
                    logger.error(f"CRITICAL sanity check violation{context_str}: {field} - {message} (value: {value})")
                elif severity == 'error':
                    logger.error(f"Sanity check violation{context_str}: {field} - {message} (value: {value})")
                elif severity == 'warning':
                    logger.warning(f"Sanity check warning{context_str}: {field} - {message} (value: {value})")

        if not result.passed:
            logger.error(f"Game state failed sanity checks{context_str}. Total violations: {len(result.violations)}")

        return result.passed


# Convenience function
def validate_detection_result(detection_result: Dict[str, Any], context: str = "") -> bool:
    """
    Validate detection result before processing.

    Args:
        detection_result: Detection result dictionary
        context: Context for logging

    Returns:
        True if valid, False otherwise
    """
    return DetectionSanityChecker.validate_and_log(detection_result, context)
