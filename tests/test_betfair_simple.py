#!/usr/bin/env python3
"""Simple test to diagnose Betfair detection issues."""

import sys
import os
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_basic_capture():
    """Test basic screen capture."""
    print("=" * 60)
    print("BETFAIR SCRAPER DIAGNOSTIC")
    print("=" * 60)
    
    # Test 1: Check dependencies
    print("\n1. Testing dependencies...")
    try:
        import cv2
        print("  ✓ cv2 (OpenCV) available")
    except ImportError:
        print("  ✗ cv2 (OpenCV) NOT available - install with: pip install opencv-python")
        return
    
    try:
        import mss
        print("  ✓ mss available")
    except ImportError:
        print("  ✗ mss NOT available - install with: pip install mss")
        return
    
    try:
        import numpy as np
        print("  ✓ numpy available")
    except ImportError:
        print("  ✗ numpy NOT available - install with: pip install numpy")
        return
    
    # Test 2: Try to capture screen
    print("\n2. Testing screen capture...")
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            print(f"  Found {len(monitors) - 1} monitor(s)")
            for i, mon in enumerate(monitors[1:], 1):
                print(f"    Monitor {i}: {mon['width']}x{mon['height']}")
            
            # Capture primary monitor
            screenshot = sct.grab(monitors[1])
            img = np.array(screenshot)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            print(f"  ✓ Captured screen: {img_bgr.shape}")
            
            # Save it
            cv2.imwrite('test_capture.png', img_bgr)
            print("  ✓ Saved to test_capture.png")
    except Exception as e:
        print(f"  ✗ Screen capture failed: {e}")
        return img_bgr
    
    # Test 3: Try desktop-independent scraper
    print("\n3. Testing desktop-independent window detection...")
    try:
        from pokertool.desktop_independent_scraper import (
            create_desktop_scraper,
            PokerDetectionMode
        )
        
        scraper = create_desktop_scraper()
        print(f"  Platform: {scraper.platform}")
        
        # Scan for poker windows
        windows = scraper.scan_for_poker_windows(PokerDetectionMode.FUZZY_MATCH)
        print(f"  Found {len(windows)} poker windows:")
        
        for window in windows:
            print(f"    - {window.title}")
            print(f"      Position: {window.bounds}")
            print(f"      Visible: {window.is_visible}, Minimized: {window.is_minimized}")
            
            # Try to capture this window
            result = scraper.capture_window(window, include_screenshot=True)
            if result and result.get('screenshot') is not None:
                img = result['screenshot']
                filename = f"window_{window.title.replace(' ', '_')[:20]}.png"
                cv2.imwrite(filename, img)
                print(f"      ✓ Captured to {filename}")
                
                # Test Betfair detection on this window
                test_betfair_detection(img, window.title)
            
    except Exception as e:
        print(f"  Error with desktop scraper: {e}")
    
    return img_bgr

def test_betfair_detection(img, title="Unknown"):
    """Test Betfair detection on an image."""
    print(f"\n4. Testing Betfair detection on '{title}'...")
    
    try:
        from pokertool.modules.poker_screen_scraper_betfair import (
            BetfairPokerDetector,
            UniversalPokerDetector
        )
        
        # Test Betfair detector
        betfair = BetfairPokerDetector()
        result = betfair.detect(img)
        print(f"  Betfair detector:")
        print(f"    Detected: {result.detected}")
        print(f"    Confidence: {result.confidence:.1%}")
        if result.details:
            print(f"    Felt ratio: {result.details.get('felt_ratio', 0):.3f}")
            print(f"    Felt confidence: {result.details.get('felt_confidence', 0):.1%}")
            print(f"    Card shapes: {result.details.get('card_shapes_found', 0)}")
            print(f"    UI elements: {result.details.get('ui_elements', 0)}")
            print(f"    Text coverage: {result.details.get('text_coverage', 0):.3f}")
            print(f"    Table shape: {result.details.get('table_shape', 'none')}")
        
        # Test Universal detector  
        universal = UniversalPokerDetector()
        result2 = universal.detect(img)
        print(f"\n  Universal detector:")
        print(f"    Detected: {result2.detected}")
        print(f"    Confidence: {result2.confidence:.1%}")
        if result2.details:
            print(f"    Felt color: {result2.details.get('felt_color', 'none')}")
            print(f"    Felt ratio: {result2.details.get('felt_ratio', 0):.3f}")
        
    except Exception as e:
        print(f"  Detection error: {e}")

def analyze_colors(img):
    """Analyze the color distribution in an image."""
    import cv2
    import numpy as np
    
    print("\n5. Analyzing colors in the image...")
    
    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define color ranges to check
    color_ranges = {
        'Purple (Betfair)': ((110, 30, 100), (150, 255, 255)),
        'Purple (wider)': ((100, 20, 80), (160, 255, 255)),
        'Green (traditional)': ((40, 40, 40), (80, 255, 255)),
        'Blue': ((100, 50, 50), (130, 255, 255)),
        'Red': ((0, 50, 50), (20, 255, 255)),
    }
    
    for name, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        percentage = (np.count_nonzero(mask) / mask.size) * 100
        if percentage > 0.5:
            print(f"  {name:20}: {percentage:5.1f}%")
            # Save mask if significant
            if percentage > 2:
                filename = f"mask_{name.replace(' ', '_').replace('(', '').replace(')', '').lower()}.png"
                cv2.imwrite(filename, mask)
                print(f"    -> Saved mask to {filename}")

def main():
    """Run all tests."""
    # First test basic capture
    img = test_basic_capture()
    
    if img is not None:
        # Analyze colors
        analyze_colors(img)
        
        # Test detection on full screen
        test_betfair_detection(img, "Full Screen")
    
    # Test with sample image if available
    print("\n" + "=" * 60)
    print("Testing with BF_TEST.jpg sample...")
    print("=" * 60)
    
    sample_path = Path("BF_TEST.jpg")
    if sample_path.exists():
        import cv2
        sample_img = cv2.imread(str(sample_path))
        if sample_img is not None:
            print(f"Loaded sample image: {sample_img.shape}")
            analyze_colors(sample_img)
            test_betfair_detection(sample_img, "BF_TEST.jpg")
    else:
        print("BF_TEST.jpg not found")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check the captured screenshots to verify Betfair is visible")
    print("2. Check the color masks to see if purple is being detected")
    print("3. If Betfair is not detected in windows, make sure it's:")
    print("   - Running and visible (not minimized)")
    print("   - On the primary monitor (or adjust monitor selection)")
    print("   - The window title contains 'Betfair' or poker-related terms")

if __name__ == "__main__":
    main()
