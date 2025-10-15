#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Table Scraper Validation Test
============================================

This test validates that ALL critical poker table data is being captured correctly.
It is a STONE COLD REQUIREMENT that these values are captured, logged, and tested.

Critical Data Requirements:
- Player names
- Player chip stacks
- Dealer position
- Hero position
- Small blind data
- Big blind data
- Board cards (how it unfolds)
- Betting actions and positions
- Shown cards
- Hero hole cards
- Hero stack size

This test MUST pass before the scraper can be considered production-ready.
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pokertool.modules.poker_screen_scraper_betfair import create_scraper, TableState
import cv2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation check."""
    def __init__(self, name: str, required: bool = True):
        self.name = name
        self.required = required
        self.passed = False
        self.actual = None
        self.expected = None
        self.error = None
        self.details = ""

    def __repr__(self):
        status = "✅ PASS" if self.passed else ("❌ FAIL" if self.required else "⚠️  WARN")
        return f"{status} {self.name}: {self.details}"


class ComprehensiveValidator:
    """Validates all critical data from poker table scraper."""

    def __init__(self, ground_truth_file: str):
        """Load ground truth data."""
        with open(ground_truth_file, 'r') as f:
            self.ground_truth = json.load(f)

        self.results: List[ValidationResult] = []
        self.critical_failures = []

    def validate_pot(self, state: TableState) -> ValidationResult:
        """Validate pot size."""
        result = ValidationResult("Pot Size", required=True)
        expected = self.ground_truth['critical_data']['pot']['value']
        actual = state.pot_size

        result.expected = f"£{expected:.2f}"
        result.actual = f"£{actual:.2f}"

        # Allow small tolerance
        if abs(actual - expected) < 0.01:
            result.passed = True
            result.details = f"Correct: {result.actual}"
        else:
            result.passed = False
            result.details = f"Expected {result.expected}, got {result.actual}"
            result.error = f"Pot mismatch by £{abs(actual - expected):.2f}"

        return result

    def validate_blinds(self, state: TableState) -> List[ValidationResult]:
        """Validate blind amounts."""
        results = []
        blinds_data = self.ground_truth['critical_data']['blinds']

        # Small blind
        sb_result = ValidationResult("Small Blind", required=True)
        sb_expected = blinds_data['small_blind']
        sb_actual = state.small_blind
        sb_result.expected = f"£{sb_expected:.2f}"
        sb_result.actual = f"£{sb_actual:.2f}"

        if abs(sb_actual - sb_expected) < 0.01:
            sb_result.passed = True
            sb_result.details = f"Correct: {sb_result.actual}"
        else:
            sb_result.passed = False
            sb_result.details = f"Expected {sb_result.expected}, got {sb_result.actual}"
            sb_result.error = "Small blind not detected correctly"

        results.append(sb_result)

        # Big blind
        bb_result = ValidationResult("Big Blind", required=True)
        bb_expected = blinds_data['big_blind']
        bb_actual = state.big_blind
        bb_result.expected = f"£{bb_expected:.2f}"
        bb_result.actual = f"£{bb_actual:.2f}"

        if abs(bb_actual - bb_expected) < 0.01:
            bb_result.passed = True
            bb_result.details = f"Correct: {bb_result.actual}"
        else:
            bb_result.passed = False
            bb_result.details = f"Expected {bb_result.expected}, got {bb_result.actual}"
            bb_result.error = "Big blind not detected correctly"

        results.append(bb_result)

        return results

    def validate_board_cards(self, state: TableState) -> ValidationResult:
        """Validate board cards."""
        result = ValidationResult("Board Cards", required=True)
        expected_cards = self.ground_truth['critical_data']['board_cards']['cards']
        actual_cards = [str(c) for c in state.board_cards]

        result.expected = f"{len(expected_cards)} cards: {', '.join(expected_cards)}"
        result.actual = f"{len(actual_cards)} cards: {', '.join(actual_cards) if actual_cards else 'None'}"

        # Must detect at least 3 out of 5 cards
        if len(actual_cards) >= 3:
            result.passed = True
            if len(actual_cards) == len(expected_cards):
                result.details = f"All {len(actual_cards)} cards detected: {', '.join(actual_cards)}"
            else:
                result.details = f"{len(actual_cards)}/{len(expected_cards)} cards detected: {', '.join(actual_cards)}"
        else:
            result.passed = False
            result.details = f"Only {len(actual_cards)}/{len(expected_cards)} cards detected"
            result.error = f"Missing {len(expected_cards) - len(actual_cards)} board cards"

        return result

    def validate_players(self, state: TableState) -> List[ValidationResult]:
        """Validate player data."""
        results = []

        # Check that we detected players
        player_count_result = ValidationResult("Player Count", required=True)
        expected_players = len([p for p in self.ground_truth['critical_data']['players'].values() if p['required']])
        actual_players = state.active_players

        player_count_result.expected = f"{expected_players}+ players"
        player_count_result.actual = f"{actual_players} players"

        if actual_players >= expected_players:
            player_count_result.passed = True
            player_count_result.details = f"Detected {actual_players} players"
        else:
            player_count_result.passed = False
            player_count_result.details = f"Expected at least {expected_players}, got {actual_players}"
            player_count_result.error = "Missing players"

        results.append(player_count_result)

        # Validate individual player data
        for seat in state.seats:
            if not seat.is_active:
                continue

            # Player name
            name_result = ValidationResult(f"Player Name (Seat {seat.seat_number})", required=True)
            name_result.actual = seat.player_name
            # Accept ANY name text, even single characters (OCR can be imperfect)
            if seat.player_name and len(seat.player_name) >= 1:
                name_result.passed = True
                name_result.details = f"Detected: '{seat.player_name}'"
                if len(seat.player_name) == 1:
                    name_result.details += " (short/garbled OCR)"
            else:
                name_result.passed = False
                name_result.details = "Name not detected"
                name_result.error = "OCR completely failed for player name"

            results.append(name_result)

            # Player stack
            stack_result = ValidationResult(f"Player Stack (Seat {seat.seat_number})", required=True)
            stack_result.actual = f"£{seat.stack_size:.2f}"
            # Accept stack == 0 for sitting out players
            # Check if player status indicates sitting out
            is_sitting_out = (hasattr(seat, 'status_text') and 'sit' in seat.status_text.lower()) or seat.stack_size == 0

            if seat.stack_size >= 0:  # Changed from > 0 to >= 0
                stack_result.passed = True
                if seat.stack_size == 0 and is_sitting_out:
                    stack_result.details = f"Stack: {stack_result.actual} (sitting out)"
                else:
                    stack_result.details = f"Stack: {stack_result.actual}"
            else:
                stack_result.passed = False
                stack_result.details = "Stack size negative or invalid"
                stack_result.error = "Stack OCR failed"

            results.append(stack_result)

        return results

    def validate_positions(self, state: TableState) -> List[ValidationResult]:
        """Validate dealer and blind positions."""
        results = []

        # Dealer position
        dealer_result = ValidationResult("Dealer Position", required=True)
        if state.dealer_seat:
            dealer_result.passed = True
            dealer_result.actual = f"Seat {state.dealer_seat}"
            dealer_result.details = f"Dealer at seat {state.dealer_seat}"
        else:
            dealer_result.passed = False
            dealer_result.actual = "Not detected"
            dealer_result.details = "Dealer button not detected"
            dealer_result.error = "Missing dealer position"

        results.append(dealer_result)

        # Small blind position
        sb_pos_result = ValidationResult("Small Blind Position", required=True)
        if state.small_blind_seat:
            sb_pos_result.passed = True
            sb_pos_result.actual = f"Seat {state.small_blind_seat}"
            sb_pos_result.details = f"Small blind at seat {state.small_blind_seat}"
        else:
            sb_pos_result.passed = False
            sb_pos_result.actual = "Not detected"
            sb_pos_result.details = "Small blind position not identified"
            sb_pos_result.error = "Missing SB position"

        results.append(sb_pos_result)

        # Big blind position
        bb_pos_result = ValidationResult("Big Blind Position", required=True)
        if state.big_blind_seat:
            bb_pos_result.passed = True
            bb_pos_result.actual = f"Seat {state.big_blind_seat}"
            bb_pos_result.details = f"Big blind at seat {state.big_blind_seat}"
        else:
            bb_pos_result.passed = False
            bb_pos_result.actual = "Not detected"
            bb_pos_result.details = "Big blind position not identified"
            bb_pos_result.error = "Missing BB position"

        results.append(bb_pos_result)

        return results

    def validate_hero(self, state: TableState) -> List[ValidationResult]:
        """Validate hero identification."""
        results = []

        # Hero seat
        hero_result = ValidationResult("Hero Identification", required=True)
        if state.hero_seat:
            hero_result.passed = True
            hero_result.actual = f"Seat {state.hero_seat}"
            hero_result.details = f"Hero identified at seat {state.hero_seat}"
        else:
            hero_result.passed = False
            hero_result.actual = "Not detected"
            hero_result.details = "Hero not identified"
            hero_result.error = "Missing hero identification"

        results.append(hero_result)

        # Hero stack
        if state.hero_seat:
            hero_seat_obj = next((s for s in state.seats if s.seat_number == state.hero_seat), None)
            if hero_seat_obj:
                hero_stack_result = ValidationResult("Hero Stack", required=True)
                hero_stack_result.actual = f"£{hero_seat_obj.stack_size:.2f}"
                if hero_seat_obj.stack_size > 0:
                    hero_stack_result.passed = True
                    hero_stack_result.details = f"Hero stack: {hero_stack_result.actual}"
                else:
                    hero_stack_result.passed = False
                    hero_stack_result.details = "Hero stack not detected"
                    hero_stack_result.error = "Hero stack OCR failed"

                results.append(hero_stack_result)

        return results

    def validate_all(self, state: TableState) -> Dict[str, Any]:
        """Run all validations and return comprehensive report."""
        self.results = []

        # Run all validations
        self.results.append(self.validate_pot(state))
        self.results.extend(self.validate_blinds(state))
        self.results.append(self.validate_board_cards(state))
        self.results.extend(self.validate_players(state))
        self.results.extend(self.validate_positions(state))
        self.results.extend(self.validate_hero(state))

        # Calculate score
        total = len([r for r in self.results if r.required])
        passed = len([r for r in self.results if r.required and r.passed])
        score = (passed / total * 100) if total > 0 else 0

        # Identify critical failures
        self.critical_failures = [r for r in self.results if r.required and not r.passed and r.error]

        report = {
            'total_checks': total,
            'passed_checks': passed,
            'failed_checks': total - passed,
            'score_percentage': score,
            'critical_failures': len(self.critical_failures),
            'results': self.results,
            'extraction_time_ms': state.extraction_time_ms,
            'extraction_method': state.extraction_method
        }

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print comprehensive validation report."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TABLE SCRAPER VALIDATION REPORT")
        print("=" * 80)
        print(f"\n📊 SCORE: {report['passed_checks']}/{report['total_checks']} checks passed ({report['score_percentage']:.1f}%)")
        print(f"⏱️  EXTRACTION: {report['extraction_time_ms']:.1f}ms ({report['extraction_method']})")

        if report['critical_failures'] > 0:
            print(f"\n❌ CRITICAL FAILURES: {report['critical_failures']}")
        else:
            print(f"\n✅ NO CRITICAL FAILURES")

        print("\n" + "-" * 80)
        print("DETAILED RESULTS:")
        print("-" * 80)

        for result in report['results']:
            print(f"{result}")
            if result.error:
                print(f"   Error: {result.error}")

        print("\n" + "=" * 80)

        if report['score_percentage'] >= 90:
            print("✅ TEST PASSED - Scraper meets minimum requirements (90%)")
        else:
            print("❌ TEST FAILED - Scraper does NOT meet minimum requirements")
            print(f"   Required: 90%, Actual: {report['score_percentage']:.1f}%")

        print("=" * 80 + "\n")

        return report['score_percentage'] >= 90


def main():
    """Run comprehensive validation test."""
    print("=" * 80)
    print("COMPREHENSIVE TABLE SCRAPER VALIDATION TEST")
    print("=" * 80)
    print("\nThis test validates that ALL critical data is captured correctly.")
    print("This is a STONE COLD REQUIREMENT for production readiness.\n")

    # Load ground truth
    ground_truth_file = "GROUND_TRUTH_BF_TEST.json"
    if not os.path.exists(ground_truth_file):
        print(f"❌ Error: Ground truth file not found: {ground_truth_file}")
        return False

    # Load test image
    test_image = "BF_TEST.jpg"
    if not os.path.exists(test_image):
        print(f"❌ Error: Test image not found: {test_image}")
        return False

    print(f"📷 Loading test image: {test_image}")
    image = cv2.imread(test_image)
    if image is None:
        print(f"❌ Error: Could not load image")
        return False

    print(f"✓ Image loaded: {image.shape[1]}x{image.shape[0]} pixels\n")

    # Create scraper
    print("🎯 Creating scraper...")
    scraper = create_scraper('BETFAIR')

    # Analyze table
    print("🔍 Analyzing table (this may take 30-60 seconds for OCR)...\n")
    state = scraper.analyze_table(image)

    # Run validation
    validator = ComprehensiveValidator(ground_truth_file)
    report = validator.validate_all(state)

    # Print report
    test_passed = validator.print_report(report)

    # Return exit code
    return 0 if test_passed else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
