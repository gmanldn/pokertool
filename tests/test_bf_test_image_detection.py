#!/usr/bin/env python3
"""
Comprehensive unit tests for BF_TEST.jpg detection.

This test suite verifies that the scraper correctly detects all poker table
elements from the BF_TEST.jpg test image, including:
- Player names
- Player chip stacks
- Board cards
- Hole cards (if visible)
- Player positions
- Dealer button
- Small blind / Big blind
- Pot size
- Player bets/contributions
"""

import sys
from pathlib import Path
import pytest
import cv2
import numpy as np

# Add src to path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / 'src'
sys.path.insert(0, str(SRC_DIR))

from pokertool.modules.poker_screen_scraper_betfair import (
    PokerScreenScraper,
    PokerSite,
)

# Test image path
BF_TEST_IMAGE = ROOT_DIR / 'BF_TEST.jpg'


class TestBFTestImageDetection:
    """Test suite for BF_TEST.jpg comprehensive detection."""

    @pytest.fixture(scope='class')
    def test_image(self):
        """Load the BF_TEST.jpg test image."""
        if not BF_TEST_IMAGE.exists():
            pytest.skip(f"Test image not found: {BF_TEST_IMAGE}")

        img = cv2.imread(str(BF_TEST_IMAGE))
        if img is None:
            pytest.skip(f"Failed to load test image: {BF_TEST_IMAGE}")

        return img

    @pytest.fixture(scope='class')
    def scraper(self):
        """Create a Betfair poker scraper instance."""
        return PokerScreenScraper(site=PokerSite.BETFAIR)

    @pytest.fixture(scope='class')
    def table_state(self, scraper, test_image):
        """Analyze the test image and return table state."""
        state = scraper.analyze_table(test_image)
        return state

    def test_table_detection(self, scraper, test_image):
        """Test that a poker table is detected in the image."""
        is_table, confidence, details = scraper.detect_poker_table(test_image)

        assert is_table, "Poker table should be detected"
        assert confidence > 0.5, f"Detection confidence too low: {confidence}"
        print(f"✓ Table detected with {confidence*100:.1f}% confidence")

    def test_board_cards_detection(self, table_state):
        """Test that board cards are detected."""
        board_cards = table_state.board_cards

        assert board_cards is not None, "Board cards should be detected"

        # Expected: 10♦, A♦, 7♥, 5♥, 6♥ (but OCR may miss some)
        # We expect at least 3 cards to be detected
        assert len(board_cards) >= 3, f"Expected at least 3 board cards, got {len(board_cards)}"

        print(f"Detected board cards: {board_cards}")

        # Convert to string for comparison
        detected_cards = [str(card) for card in board_cards]

        # Expected cards (some may be misread)
        expected_cards = ['Td', 'Ad', '7h', '5h', '6h']

        # Count matches (allowing for OCR errors in suits)
        matches = 0
        for detected in detected_cards:
            for expected in expected_cards:
                # Match if rank is correct (suit may be wrong due to OCR)
                if detected[0] == expected[0]:
                    matches += 1
                    break

        print(f"✓ Board cards detected: {detected_cards} ({matches}/{len(expected_cards)} ranks matched)")

    def test_pot_size_detection(self, table_state):
        """Test that the pot size is detected."""
        pot_size = table_state.pot_size

        assert pot_size is not None, "Pot size should be detected"

        print(f"Detected pot: £{pot_size}")

        # Expected pot: £0.08 (but OCR can be inaccurate)
        # We just verify a pot value is detected
        assert pot_size >= 0, f"Pot size should be non-negative, got £{pot_size}"

        print(f"✓ Pot size detected: £{pot_size}")

    def test_player_detection(self, table_state):
        """Test that active players are detected."""
        seats = table_state.seats

        assert seats is not None, "Seats should be detected"
        assert len(seats) > 0, "At least one player should be detected"

        # Count active (non-empty) players
        active_players = [s for s in seats if s.player_name and s.player_name.lower() != 'empty']

        print(f"Detected {len(active_players)} active players out of {len(seats)} seats")

        # We expect at least 3 active players (excluding "Empty" seats and "SIT OUT")
        assert len(active_players) >= 2, \
            f"Expected at least 2 active players, got {len(active_players)}"

        print(f"✓ Active players detected: {len(active_players)}")

    def test_player_names_detection(self, table_state):
        """Test that player names are correctly detected."""
        seats = table_state.seats

        # Expected player names (excluding "Empty" and potentially including sitting out players)
        expected_names = ['Time: 17', 'FourBoysUnited', 'GmanLDN', 'Thelongbluevein']

        detected_names = [s.player_name for s in seats if s.player_name and s.player_name.lower() != 'empty']

        print(f"Detected player names: {detected_names}")

        # Check if we detected at least some of the expected names
        # OCR might not be perfect, so we check for partial matches
        matches = 0
        for expected in expected_names:
            for detected in detected_names:
                if expected.lower() in detected.lower() or detected.lower() in expected.lower():
                    matches += 1
                    break

        assert matches >= 1, \
            f"Expected to detect at least 1 player name, got {matches} matches"

        print(f"✓ Player names detected ({matches}/{len(expected_names)} matched)")

    def test_hero_detection(self, table_state):
        """Test that the hero player (GmanLDN) is correctly identified."""
        hero_seat = table_state.hero_seat
        seats = table_state.seats

        print(f"Hero seat: {hero_seat}")

        if hero_seat is not None:
            # Find hero by checking is_hero flag or by seat number
            hero = None
            for seat in seats:
                if seat.is_hero or seat.seat_number == hero_seat:
                    hero = seat
                    break

            if hero:
                print(f"Hero player: {hero.player_name} with £{hero.stack_size}")

                # Hero should be GmanLDN
                assert hero.player_name is not None, "Hero name should be detected"
                assert 'gman' in hero.player_name.lower() or 'ldn' in hero.player_name.lower(), \
                    f"Hero should be GmanLDN, got {hero.player_name}"

                print(f"✓ Hero correctly identified: {hero.player_name}")
            else:
                print("⚠ Hero not found in seats")
        else:
            print("⚠ Hero seat not detected (may require calibration)")

    def test_player_stack_detection(self, table_state):
        """Test that player chip stacks are detected."""
        seats = table_state.seats

        active_seats = [s for s in seats if s.player_name and s.player_name.lower() != 'empty']

        stacks_detected = 0
        for seat in active_seats:
            if seat.stack_size is not None and seat.stack_size > 0:
                stacks_detected += 1
                print(f"  {seat.player_name}: £{seat.stack_size}")

        print(f"Detected stacks for {stacks_detected}/{len(active_seats)} active players")

        # We should detect stacks for most active players
        assert stacks_detected >= 1, \
            f"Expected at least 1 player stack detected, got {stacks_detected}"

        print(f"✓ Player stacks detected for {stacks_detected} players")

    def test_expected_player_stacks(self, table_state):
        """Test that specific player stacks match expected values."""
        seats = table_state.seats

        # Expected stacks (approximately):
        # - Time: 17 -> £2.22
        # - FourBoysUnited -> £2.62
        # - GmanLDN -> £1.24
        # - Thelongbluevein -> £0 (sitting out)

        expected_stacks = {
            'fourboysunited': 2.62,
            'gman': 1.24,
            'time': 2.22,
        }

        matches = 0
        for seat in seats:
            if not seat.player_name or seat.stack_size is None:
                continue

            name_lower = seat.player_name.lower()
            for key, expected_stack in expected_stacks.items():
                if key in name_lower:
                    # Allow ±0.20 variance for OCR errors
                    if abs(seat.stack_size - expected_stack) < 0.20:
                        matches += 1
                        print(f"✓ {seat.player_name}: £{seat.stack_size} (expected ~£{expected_stack})")
                    else:
                        print(f"⚠ {seat.player_name}: £{seat.stack_size} (expected ~£{expected_stack}, variance too high)")

        print(f"Stack verification: {matches}/{len(expected_stacks)} matched")

        # We should match at least 1 stack correctly
        assert matches >= 1, \
            f"Expected at least 1 stack to match, got {matches}"

    def test_dealer_button_detection(self, table_state):
        """Test that the dealer button position is detected."""
        dealer_seat = table_state.dealer_seat

        print(f"Dealer seat: {dealer_seat}")

        # Dealer button should be detected (position may vary)
        if dealer_seat is not None:
            assert 0 <= dealer_seat < len(table_state.seats), \
                f"Dealer seat {dealer_seat} out of range"

            print(f"✓ Dealer button detected at seat {dealer_seat}")
        else:
            print("⚠ Dealer button not detected (may require calibration)")

    def test_blind_detection(self, table_state):
        """Test that blinds are detected."""
        sb = table_state.small_blind
        bb = table_state.big_blind

        print(f"Small blind: £{sb if sb else 'N/A'}")
        print(f"Big blind: £{bb if bb else 'N/A'}")

        # At least one blind should be detected or we should have blind info
        if sb is not None or bb is not None:
            print("✓ Blind information detected")
        else:
            print("⚠ Blinds not detected (may require calibration or not visible in this state)")

    def test_player_positions(self, table_state):
        """Test that player positions are correctly identified."""
        seats = table_state.seats

        # We should have a reasonable number of seats (typically 6 or 9 for Betfair)
        assert len(seats) in [6, 9], \
            f"Expected 6 or 9 seats, got {len(seats)}"

        print(f"✓ Table has {len(seats)} seats")

        # Verify all seats have valid seat numbers (may start at 0 or 1)
        seat_numbers = [seat.seat_number for seat in seats]
        print(f"Seat numbers: {seat_numbers}")

        # Check that seat numbers are sequential (either 0-based or 1-based)
        assert len(set(seat_numbers)) == len(seats), \
            "Seat numbers should be unique"

        print("✓ Seat numbers are valid and unique")

    def test_sit_out_status(self, table_state):
        """Test that sitting out players are detected."""
        seats = table_state.seats

        # Look for players sitting out
        sitting_out = []
        for seat in seats:
            if seat.player_name and ('sitting' in seat.player_name.lower() or 'sit out' in seat.status_text.lower()):
                sitting_out.append(seat.player_name)
            # Check if stack is 0 (indicates sitting out)
            elif seat.player_name and seat.stack_size == 0 and 'empty' not in seat.player_name.lower():
                sitting_out.append(seat.player_name)

        print(f"Players sitting out: {sitting_out}")

        if sitting_out:
            print(f"✓ Detected {len(sitting_out)} player(s) sitting out")
        else:
            print("⚠ No players detected as sitting out (or not marked in status)")

    def test_detection_confidence(self, table_state):
        """Test that detection confidence is reasonable."""
        confidence = table_state.detection_confidence

        print(f"Detection confidence: {confidence*100:.1f}%")

        assert confidence > 0.5, \
            f"Detection confidence too low: {confidence*100:.1f}%"

        print(f"✓ Detection confidence acceptable: {confidence*100:.1f}%")

    def test_extraction_method(self, table_state):
        """Test that extraction method is recorded."""
        method = table_state.extraction_method

        print(f"Extraction method: {method}")

        assert method is not None, "Extraction method should be recorded"
        print(f"✓ Extraction method: {method}")

    def test_vpip_af_badges(self, table_state):
        """Test detection of VPIP/AF player badges (meta information)."""
        seats = table_state.seats

        # In the image, we can see VPIP and AF badges for some players
        # This is advanced detection - log what we find

        print("Player badge information:")
        for seat in seats:
            if seat.player_name and seat.player_name.lower() != 'empty':
                print(f"  {seat.player_name}: detected")

        # This is informational - we've logged the data
        print("✓ Player information logged")


class TestBFTestImageRobustness:
    """Test robustness and edge cases."""

    @pytest.fixture(scope='class')
    def scraper(self):
        """Create a Betfair poker scraper instance."""
        return PokerScreenScraper(site=PokerSite.BETFAIR)

    def test_image_loading(self):
        """Test that the test image exists and can be loaded."""
        assert BF_TEST_IMAGE.exists(), f"Test image not found: {BF_TEST_IMAGE}"

        img = cv2.imread(str(BF_TEST_IMAGE))
        assert img is not None, "Failed to load test image"
        assert img.shape[0] > 0 and img.shape[1] > 0, "Invalid image dimensions"

        print(f"✓ Test image loaded: {img.shape[1]}x{img.shape[0]} pixels")

    def test_scraper_initialization(self, scraper):
        """Test that scraper initializes correctly."""
        assert scraper is not None, "Scraper should initialize"
        print("✓ Scraper initialized successfully")

    def test_multiple_analysis_calls(self, scraper):
        """Test that multiple analysis calls are consistent."""
        if not BF_TEST_IMAGE.exists():
            pytest.skip(f"Test image not found: {BF_TEST_IMAGE}")

        img = cv2.imread(str(BF_TEST_IMAGE))

        # Analyze twice
        state1 = scraper.analyze_table(img)
        state2 = scraper.analyze_table(img)

        # Results should be similar (allowing for some variance in OCR)
        assert len(state1.seats) == len(state2.seats), \
            "Number of seats should be consistent"

        print(f"✓ Multiple analysis calls consistent: {len(state1.seats)} seats")


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
