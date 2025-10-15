#!/usr/bin/env python3
"""
Test script to verify comprehensive logging in Betfair scraper.

This script:
1. Initializes the scraper
2. Captures a screenshot
3. Runs detection and analysis
4. Verifies all logging is working
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure logging to show all INFO messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

print("=" * 80)
print("BETFAIR SCRAPER LOGGING TEST")
print("=" * 80)
print()

# Import the scraper
try:
    from pokertool.modules.poker_screen_scraper_betfair import create_scraper
    print("✓ Scraper module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import scraper: {e}")
    sys.exit(1)

# Create scraper
print("\n1. Creating Betfair-optimized scraper...")
scraper = create_scraper('BETFAIR')
print(f"   Scraper created: {type(scraper).__name__}")

# Capture screen
print("\n2. Capturing screen...")
image = scraper.capture_table()
if image is not None:
    print(f"   ✓ Captured {image.shape[1]}x{image.shape[0]} image")
else:
    print("   ❌ Failed to capture screen")
    sys.exit(1)

# Run detection
print("\n3. Running poker table detection...")
print("   (Watch for detailed detection logging above)")
is_poker, confidence, details = scraper.detect_poker_table(image)
print(f"\n   Result: {'DETECTED' if is_poker else 'NOT DETECTED'}")
print(f"   Confidence: {confidence:.1%}")
print(f"   Detector: {details.get('detector', 'unknown')}")

# Run full analysis if detected
if is_poker:
    print("\n4. Running full table analysis...")
    print("   (Watch for comprehensive data logging above)")
    table_state = scraper.analyze_table(image)

    print(f"\n   Analysis complete!")
    print(f"   - Active players: {table_state.active_players}")
    print(f"   - Pot size: ${table_state.pot_size}")
    print(f"   - Game stage: {table_state.stage}")
    print(f"   - Board cards: {len(table_state.board_cards)}")
    print(f"   - Hero cards: {len(table_state.hero_cards)}")
    print(f"   - Dealer seat: {table_state.dealer_seat}")
else:
    print("\n4. Skipping analysis (no table detected)")
    print("   TIP: Open a Betfair poker table and run this test again")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nIf you saw detailed logging above, the logging is working correctly!")
print("If no table was detected, open a Betfair poker table and try again.")
