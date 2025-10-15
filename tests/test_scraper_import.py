#!/usr/bin/env python3
"""Quick test to verify screen scraper imports work without numpy errors."""

import sys
from pathlib import Path

# Add src directory to path (like start.py does)
SRC_DIR = Path(__file__).parent / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("SRC_DIR added to path:", SRC_DIR)
print("\nTesting screen scraper imports...")

try:
    print("\n1. Testing numpy import...")
    import numpy as np
    print(f"   ✓ numpy {np.__version__} imported successfully")
except Exception as e:
    print(f"   ✗ numpy import failed: {e}")
    sys.exit(1)

try:
    print("\n2. Testing pokertool.modules.poker_screen_scraper import...")
    from pokertool.modules.poker_screen_scraper import (
        PokerScreenScraper,
        PokerSite,
        TableState,
        create_scraper,
    )
    print("   ✓ Screen scraper modules imported successfully")
except Exception as e:
    print(f"   ✗ Screen scraper import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Testing scraper creation...")
    scraper = create_scraper('BETFAIR')
    print(f"   ✓ Scraper created successfully: {type(scraper).__name__}")
except Exception as e:
    print(f"   ✗ Scraper creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✓✓✓ ALL TESTS PASSED - Screen scraper working correctly!")
print("="*60)
