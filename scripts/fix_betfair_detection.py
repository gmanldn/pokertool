#!/usr/bin/env python3
"""Fix for Betfair detection - recalibrate color ranges."""

import sys
from pathlib import Path

# Update the Betfair detector with corrected color ranges
fix_content = '''
# FIXED: Betfair color ranges - recalibrated for actual Betfair tables
# These ranges have been expanded to catch more variations of purple/violet
BETFAIR_FELT_RANGES: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = [
    # Primary purple range - wider saturation and value ranges
    ((110, 15, 50), (150, 255, 255)),  # Expanded from ((110, 30, 100), (150, 255, 255))
    # Darker purple/violet variations 
    ((100, 10, 40), (160, 255, 255)),  # Expanded from ((100, 20, 80), (160, 255, 255))
    # Blue-purple range for different lighting
    ((90, 10, 30), (140, 255, 255)),   # Expanded from ((90, 25, 90), (140, 255, 255))
    # Additional ranges for edge cases
    ((105, 5, 25), (155, 255, 255)),   # Very low saturation purple
    ((95, 15, 60), (145, 200, 255)),   # Medium saturation purple
]

# Adjusted weights for better detection
FELT_WEIGHT: float = 0.35  # Reduced from 0.40 since color ranges are wider
CARD_WEIGHT: float = 0.30
UI_WEIGHT: float = 0.20
TEXT_WEIGHT: float = 0.10
ELLIPSE_WEIGHT: float = 0.15  # Increased from 0.10 for better table shape detection

# Lower the detection threshold for more lenient detection
DETECTION_THRESHOLD: float = 0.40  # Reduced from 0.50
'''

def apply_fix():
    """Apply the fix to the Betfair scraper module."""
    scraper_file = Path("src/pokertool/modules/poker_screen_scraper_betfair.py")
    
    if not scraper_file.exists():
        print(f"Error: {scraper_file} not found")
        return False
    
    print(f"Reading {scraper_file}...")
    content = scraper_file.read_text()
    
    # Find and replace the color ranges
    import_idx = content.find("BETFAIR_FELT_RANGES")
    if import_idx == -1:
        print("Error: Could not find BETFAIR_FELT_RANGES in file")
        return False
    
    # Find the end of the current ranges definition
    end_idx = content.find("\nFELT_WEIGHT:", import_idx)
    if end_idx == -1:
        print("Error: Could not find FELT_WEIGHT in file")
        return False
    
    # Replace the ranges
    new_content = content[:import_idx] + fix_content.strip() + "\n\n" + content[end_idx + len("\nFELT_WEIGHT:"):]
    
    # Also update the detection threshold
    new_content = new_content.replace(
        "detected = total_confidence >= 0.50",
        "detected = total_confidence >= DETECTION_THRESHOLD"
    )
    
    # Add DETECTION_THRESHOLD if not present
    if "DETECTION_THRESHOLD" not in new_content:
        # Add it after ELLIPSE_WEIGHT
        idx = new_content.find("ELLIPSE_WEIGHT: float")
        if idx != -1:
            end_line = new_content.find("\n", idx)
            if end_line != -1:
                new_content = (new_content[:end_line] + 
                              "\nDETECTION_THRESHOLD: float = 0.40  # Lowered for better detection" +
                              new_content[end_line:])
    
    print(f"Writing fixed version to {scraper_file}...")
    scraper_file.write_text(new_content)
    print("✓ Fix applied successfully!")
    
    return True

def test_fix():
    """Quick test of the fix."""
    print("\nTesting the fix...")
    
    try:
        # Try importing the fixed module
        sys.path.insert(0, "src")
        from pokertool.modules.poker_screen_scraper_betfair import (
            BETFAIR_FELT_RANGES,
            BetfairPokerDetector
        )
        
        print("✓ Module imported successfully")
        print(f"✓ Number of color ranges: {len(BETFAIR_FELT_RANGES)}")
        
        # Check if BF_TEST.jpg exists for testing
        test_image = Path("BF_TEST.jpg")
        if test_image.exists():
            print(f"\nTesting with {test_image}...")
            import cv2
            import numpy as np
            
            img = cv2.imread(str(test_image))
            if img is not None:
                detector = BetfairPokerDetector()
                result = detector.detect(img)
                
                print(f"  Detection result: {result.detected}")
                print(f"  Confidence: {result.confidence:.1%}")
                
                if result.detected:
                    print("✓ SUCCESS: Betfair table detected in sample image!")
                else:
                    print("⚠ Table not detected. Checking color coverage...")
                    
                    # Analyze colors
                    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                    total_pixels = 0
                    for i, (lower, upper) in enumerate(BETFAIR_FELT_RANGES):
                        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                        pixels = np.count_nonzero(mask)
                        total_pixels += pixels
                        percentage = (pixels / mask.size) * 100
                        print(f"    Range {i+1}: {percentage:.2f}% coverage")
                    
                    total_percentage = (total_pixels / hsv.shape[0] / hsv.shape[1]) * 100
                    print(f"    Total purple coverage: {total_percentage:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"Error testing fix: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("BETFAIR DETECTION FIX")
    print("=" * 60)
    print("\nThis script will recalibrate the color detection ranges")
    print("for better Betfair table detection.")
    print()
    
    if apply_fix():
        print("\n" + "=" * 60)
        test_fix()
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("1. Open Betfair Poker with a table visible")
        print("2. Run: python test_scraper_monitoring.py")
        print("3. The scraper should now detect the purple Betfair tables")
        print("\nIf detection still fails, the table might be using")
        print("different colors than expected. In that case, run:")
        print("  python save_debug_screenshots_all_desktops()")
        print("to capture the actual table and analyze its colors.")
    else:
        print("\nFix failed. Please check the error messages above.")
