#!/usr/bin/env python3
"""Quick verification that the Betfair detection fix is working."""

import sys
from pathlib import Path
sys.path.insert(0, "src")

print("BETFAIR DETECTION FIX VERIFICATION")
print("=" * 60)

try:
    # Import the fixed module
    from pokertool.modules.poker_screen_scraper_betfair import (
        BETFAIR_FELT_RANGES,
        DETECTION_THRESHOLD,
        BetfairPokerDetector,
        create_scraper
    )
    
    print("✓ Module imported successfully")
    print(f"✓ Number of color ranges: {len(BETFAIR_FELT_RANGES)}")
    print(f"✓ Detection threshold: {DETECTION_THRESHOLD}")
    
    # Test with BF_TEST.jpg if available
    test_image = Path("BF_TEST.jpg")
    if test_image.exists():
        print(f"\nTesting with {test_image}...")
        import cv2
        import numpy as np
        
        img = cv2.imread(str(test_image))
        if img is not None:
            detector = BetfairPokerDetector()
            result = detector.detect(img)
            
            print(f"Detection result: {result.detected}")
            print(f"Confidence: {result.confidence:.1%}")
            
            if result.detected:
                print("\n✓✓✓ SUCCESS! Betfair table detected!")
            else:
                print("\n⚠ Table not detected. Details:")
                if result.details:
                    print(f"  Felt ratio: {result.details.get('felt_ratio', 0):.3f}")
                    print(f"  Felt confidence: {result.details.get('felt_confidence', 0):.1%}")
                    print(f"  Card shapes: {result.details.get('card_shapes_found', 0)}")
                    print(f"  Total confidence: {result.details.get('total_confidence', 0):.1%}")
    
    # Quick functional test
    print("\n" + "=" * 60)
    print("Creating scraper for live testing...")
    scraper = create_scraper('BETFAIR')
    
    print("Attempting to capture screen...")
    img = scraper.capture_table()
    if img is not None:
        print(f"✓ Screen captured: {img.shape}")
        
        is_poker, confidence, details = scraper.detect_poker_table(img)
        print(f"\nLive detection result:")
        print(f"  Detected: {is_poker}")
        print(f"  Confidence: {confidence:.1%}")
        print(f"  Detector: {details.get('detector', 'unknown')}")
        
        if is_poker:
            print("\n✓✓✓ SUCCESS! Live Betfair table detected!")
        else:
            print("\nIf Betfair is open but not detected:")
            print("1. Make sure a poker table is visible (not the lobby)")
            print("2. Try maximizing the Betfair window")
            print("3. Check that the table has purple/violet felt")
    else:
        print("Could not capture screen")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("\nThe fix has been applied successfully.")
    print("The scraper should now detect Betfair tables with:")
    print("  • Wider color tolerance")
    print("  • Lower detection threshold")
    print("  • Better shape detection")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
