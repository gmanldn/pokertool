#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Table Capture Diagnostic Tool
==============================

Test the Betfair poker scraper with static images or live captures.
This tool helps verify that all table elements are being captured correctly.
"""

import sys
import os
import cv2
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pokertool.modules.poker_screen_scraper_betfair import (
    create_scraper,
    TableState,
    PokerSite
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_table_state(state: TableState):
    """Pretty print the table state."""
    print("\n" + "="*80)
    print("TABLE STATE DIAGNOSTIC REPORT")
    print("="*80)

    # Detection info
    print(f"\n🎯 DETECTION:")
    print(f"   Method: {state.extraction_method.upper()}")
    print(f"   Confidence: {state.detection_confidence * 100:.1f}%")
    print(f"   Site: {state.site_detected.value if state.site_detected else 'Unknown'}")
    print(f"   Extraction Time: {state.extraction_time_ms:.1f}ms")

    # Game state
    print(f"\n🎮 GAME STATE:")
    print(f"   Stage: {state.stage.upper()}")
    print(f"   Pot: ${state.pot_size:.2f}")
    print(f"   Blinds: ${state.small_blind:.2f}/${state.big_blind:.2f}")
    if state.ante > 0:
        print(f"   Ante: ${state.ante:.2f}")

    # Board cards
    print(f"\n🃏 BOARD CARDS:")
    if state.board_cards:
        cards_str = ' '.join([str(c) for c in state.board_cards])
        print(f"   {cards_str}")
    else:
        print("   (No board cards)")

    # Hero cards
    print(f"\n🎴 HERO CARDS:")
    if state.hero_cards:
        cards_str = ' '.join([str(c) for c in state.hero_cards])
        print(f"   {cards_str}")
    else:
        print("   (No hero cards)")

    # Tournament info
    if state.tournament_name:
        print(f"\n🏆 TOURNAMENT:")
        print(f"   {state.tournament_name}")

    # Players
    print(f"\n👥 PLAYERS ({state.active_players} active):")
    if state.seats:
        for seat in sorted(state.seats, key=lambda s: s.seat_number):
            if not seat.is_active and not seat.player_name:
                continue

            indicators = []
            if seat.is_hero:
                indicators.append("⭐ HERO")
            if seat.is_dealer:
                indicators.append("🔘 BTN")
            if seat.is_active_turn:
                indicators.append("▶ TURN")
            if seat.position:
                indicators.append(seat.position)

            indicator_str = " ".join(indicators)

            stats_str = ""
            if seat.vpip is not None or seat.af is not None:
                vpip_str = f"VPIP:{seat.vpip}%" if seat.vpip is not None else ""
                af_str = f"AF:{seat.af:.1f}" if seat.af is not None else ""
                stats_parts = [s for s in [vpip_str, af_str] if s]
                if stats_parts:
                    stats_str = f" ({', '.join(stats_parts)})"

            time_bank_str = ""
            if seat.time_bank is not None:
                time_bank_str = f" ⏱ Time: {seat.time_bank}s"

            bet_str = ""
            if seat.current_bet > 0:
                bet_str = f" | Bet: ${seat.current_bet:.2f}"

            status_str = ""
            if seat.status_text and seat.status_text != "Active":
                status_str = f" [{seat.status_text}]"

            print(f"   Seat {seat.seat_number}: {seat.player_name or 'Empty'} - "
                  f"${seat.stack_size:.2f}{stats_str}{time_bank_str}{bet_str}{status_str}")

            if indicator_str:
                print(f"      {indicator_str}")

    else:
        print("   (No players detected)")

    # Positional info
    print(f"\n📍 POSITIONS:")
    if state.dealer_seat:
        print(f"   Dealer: Seat {state.dealer_seat}")
    if state.small_blind_seat:
        print(f"   Small Blind: Seat {state.small_blind_seat}")
    if state.big_blind_seat:
        print(f"   Big Blind: Seat {state.big_blind_seat}")
    if state.active_turn_seat:
        print(f"   Active Turn: Seat {state.active_turn_seat}")
    if state.hero_seat:
        print(f"   Hero: Seat {state.hero_seat}")

    print("\n" + "="*80 + "\n")


def test_with_image(image_path: str, use_cdp: bool = False):
    """Test scraper with a static image."""
    print(f"\n{'='*80}")
    print(f"TESTING WITH IMAGE: {image_path}")
    print(f"{'='*80}\n")

    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        return False

    # Load image
    print(f"📷 Loading image: {image_path}")
    image = cv2.imread(image_path)

    if image is None:
        print(f"❌ Error: Could not load image: {image_path}")
        return False

    print(f"✓ Image loaded: {image.shape[1]}x{image.shape[0]} pixels")

    # Create scraper (CDP won't work with static images, but we can still test the OCR path)
    print(f"\n🎯 Creating scraper (CDP: {use_cdp})...")
    scraper = create_scraper('BETFAIR')

    if use_cdp and scraper.cdp_scraper:
        print("⚠️  Note: CDP cannot work with static images. Using OCR fallback.")

    # Analyze table
    print(f"\n🔍 Analyzing table...")
    state = scraper.analyze_table(image)

    # Print results
    print_table_state(state)

    # Validation checks
    print("✅ VALIDATION CHECKS:")
    checks = {
        "Detection confidence > 0": state.detection_confidence > 0,
        "Pot size detected": state.pot_size > 0,
        "Board cards detected": len(state.board_cards) > 0,
        "Players detected": state.active_players > 0,
        "Dealer seat identified": state.dealer_seat is not None,
    }

    passed = 0
    total = len(checks)

    for check_name, check_result in checks.items():
        status = "✓" if check_result else "✗"
        print(f"   {status} {check_name}")
        if check_result:
            passed += 1

    print(f"\n📊 SCORE: {passed}/{total} checks passed ({passed/total*100:.0f}%)")

    return passed >= 3  # At least 3 checks should pass


def test_with_live_screen(use_cdp: bool = True):
    """Test scraper with live screen capture."""
    print(f"\n{'='*80}")
    print(f"TESTING WITH LIVE SCREEN CAPTURE")
    print(f"{'='*80}\n")

    print(f"🎯 Creating scraper (CDP: {use_cdp})...")
    scraper = create_scraper('BETFAIR')

    # Try to connect to Chrome if CDP is enabled
    if use_cdp and scraper.cdp_scraper:
        print("\n⚡ Attempting to connect to Chrome via DevTools Protocol...")
        if scraper.connect_to_chrome(tab_filter="betfair"):
            print("✓ Connected to Chrome! Using fast CDP extraction.")
        else:
            print("⚠️  Could not connect to Chrome. Using OCR fallback.")
            print("\nTo use CDP mode:")
            print("1. Launch Chrome with: chrome --remote-debugging-port=9222")
            print("2. Open Betfair poker in a tab")
            print("3. Run this script again")

    # Capture and analyze
    print(f"\n📸 Capturing screen...")
    state = scraper.analyze_table()

    # Print results
    print_table_state(state)

    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Betfair poker table scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with BF_TEST.jpg
  python test_table_capture_diagnostic.py BF_TEST.jpg

  # Test with live screen capture (OCR)
  python test_table_capture_diagnostic.py --live

  # Test with live screen capture (CDP - fast!)
  python test_table_capture_diagnostic.py --live --cdp

  # Test with live screen capture (OCR only)
  python test_table_capture_diagnostic.py --live --no-cdp
        """
    )

    parser.add_argument(
        'image',
        nargs='?',
        help='Path to test image (e.g., BF_TEST.jpg)'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Test with live screen capture instead of image'
    )
    parser.add_argument(
        '--cdp',
        action='store_true',
        default=True,
        help='Enable Chrome DevTools Protocol (default: True)'
    )
    parser.add_argument(
        '--no-cdp',
        action='store_true',
        help='Disable Chrome DevTools Protocol, use OCR only'
    )

    args = parser.parse_args()

    use_cdp = args.cdp and not args.no_cdp

    print("="*80)
    print("BETFAIR POKER TABLE CAPTURE DIAGNOSTIC TOOL")
    print("="*80)

    if args.live:
        success = test_with_live_screen(use_cdp=use_cdp)
    elif args.image:
        success = test_with_image(args.image, use_cdp=use_cdp)
    else:
        print("\n❌ Error: No test specified")
        print("\nUsage:")
        print("  python test_table_capture_diagnostic.py BF_TEST.jpg")
        print("  python test_table_capture_diagnostic.py --live")
        print("\nRun with --help for more options")
        sys.exit(1)

    if success:
        print("\n✅ TEST COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n⚠️  TEST COMPLETED WITH WARNINGS")
        print("Some checks failed. Review the output above.")
        sys.exit(0)


if __name__ == '__main__':
    main()
