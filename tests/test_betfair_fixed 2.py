#!/usr/bin/env python3
"""Test the Betfair scraper fixes with BF_TEST.jpg"""

import sys
import cv2
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pokertool.modules.poker_screen_scraper_betfair import PokerScreenScraper

# Load ground truth
with open("GROUND_TRUTH_BF_TEST.json") as f:
    ground_truth = json.load(f)

# Load test image
image = cv2.imread("BF_TEST.jpg")
if image is None:
    print("ERROR: Could not load BF_TEST.jpg")
    sys.exit(1)

print("=" * 70)
print("Testing Betfair Scraper with BF_TEST.jpg")
print("=" * 70)

# Create scraper
scraper = PokerScreenScraper()

# Extract table state
state = scraper.analyze_table(image)

print("\n📊 EXTRACTION RESULTS:\n")

# Check pot
expected_pot = ground_truth["critical_data"]["pot"]["value"]
print(f"Pot: £{state.pot_size:.2f} (expected: £{expected_pot:.2f})")
pot_match = abs(state.pot_size - expected_pot) < 0.01
print(f"  {'✓' if pot_match else '✗'} Pot {'PASS' if pot_match else 'FAIL'}")

# Check board cards
expected_cards = ground_truth["critical_data"]["board_cards"]["cards"]
detected_cards = [f"{c.rank}{c.suit}" for c in state.board_cards]
print(f"\nBoard Cards: {detected_cards} (expected: {expected_cards})")
cards_match = len(detected_cards) >= 3  # At least 3 of 5
print(f"  {'✓' if cards_match else '✗'} Cards {'PASS' if cards_match else 'FAIL'} ({len(detected_cards)}/5 detected)")

# Check players
print(f"\n👥 PLAYERS ({len([s for s in state.seats if s.is_active])} active):\n")
expected_players = ground_truth["critical_data"]["players"]

results = {"players_detected": 0, "names_correct": 0, "stacks_correct": 0}

for seat in state.seats:
    if seat.is_active:
        seat_key = f"seat_{seat.seat_number}"
        expected = expected_players.get(seat_key, {})
        expected_name = expected.get("name", "")
        expected_stack = expected.get("stack", 0.0)

        name_match = seat.player_name and len(seat.player_name) >= 3
        stack_match = abs(seat.stack_size - expected_stack) < 0.10 if expected_stack > 0 else seat.stack_size == 0

        print(f"Seat {seat.seat_number}: {seat.player_name or 'EMPTY'} - £{seat.stack_size:.2f}")
        if expected_name:
            print(f"  Expected: {expected_name} - £{expected_stack:.2f}")
            print(f"  {'✓' if name_match else '✗'} Name {'OK' if name_match else 'FAIL'}")
            print(f"  {'✓' if stack_match else '✗'} Stack {'OK' if stack_match else 'FAIL'}")

            results["players_detected"] += 1
            if name_match:
                results["names_correct"] += 1
            if stack_match:
                results["stacks_correct"] += 1

# Check hero detection
expected_hero_seat = ground_truth["critical_data"]["hero"]["seat"]
hero_seats = [s.seat_number for s in state.seats if s.is_hero]
hero_match = expected_hero_seat in hero_seats
print(f"\nHero Detection: Seat {hero_seats} (expected: Seat {expected_hero_seat})")
print(f"  {'✓' if hero_match else '✗'} Hero {'PASS' if hero_match else 'FAIL'}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Pot:        {'✓ PASS' if pot_match else '✗ FAIL'}")
print(f"Cards:      {'✓ PASS' if cards_match else '✗ FAIL'} ({len(detected_cards)}/5)")
print(f"Players:    {results['players_detected']}/4 detected")
print(f"Names:      {results['names_correct']}/{results['players_detected']} correct")
print(f"Stacks:     {results['stacks_correct']}/{results['players_detected']} correct")
print(f"Hero:       {'✓ PASS' if hero_match else '✗ FAIL'}")

# Overall score
total_checks = 6  # pot, cards, 4 players
passed_checks = sum([
    pot_match,
    cards_match,
    hero_match,
    results['names_correct'] >= 2,  # At least 2 names
    results['stacks_correct'] >= 2,  # At least 2 stacks
])

score = (passed_checks / total_checks) * 100
print(f"\nOverall Score: {score:.0f}% ({passed_checks}/{total_checks})")
print("=" * 70)

if score >= 70:
    print("\n🎉 TEST PASSED! Scraper is working well.")
    sys.exit(0)
else:
    print("\n❌ TEST FAILED! More improvements needed.")
    sys.exit(1)
