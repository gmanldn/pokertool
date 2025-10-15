#!/usr/bin/env python3
"""Diagnostic script to troubleshoot Betfair scraper issues."""

import sys
import time
import logging
import cv2
import numpy as np
from pathlib import Path

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('betfair_diagnostic.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

# Add source to path
sys.path.insert(0, str(Path(__file__).parent))

def analyze_screenshot(img):
    """Analyze a screenshot for color distribution and poker-related features."""
    if img is None:
        logger.error("No image to analyze")
        return
    
    height, width = img.shape[:2]
    logger.info(f"Image dimensions: {width}x{height}")
    
    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Check different color ranges
    color_ranges = {
        'Purple/Violet (Betfair primary)': ((110, 30, 100), (150, 255, 255)),
        'Purple/Violet (darker)': ((100, 20, 80), (140, 255, 200)),
        'Purple/Violet (lighter)': ((120, 15, 120), (160, 200, 255)),
        'Green (traditional)': ((40, 40, 40), (80, 255, 255)),
        'Blue (some sites)': ((100, 50, 50), (130, 255, 255)),
    }
    
    logger.info("\n" + "="*60)
    logger.info("COLOR ANALYSIS:")
    logger.info("="*60)
    
    for name, (lower, upper) in color_ranges.items():
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        pixel_count = cv2.countNonZero(mask)
        percentage = (pixel_count / (width * height)) * 100
        logger.info(f"{name:30} : {percentage:6.2f}% coverage")
        
        # Save mask for visual inspection
        if percentage > 1:  # Only save if significant coverage
            filename = f"mask_{name.replace('/', '_').replace(' ', '_').lower()}.png"
            cv2.imwrite(filename, mask)
            logger.info(f"  -> Saved mask to {filename}")
    
    # Check for text regions (likely contains cards, pot info)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Look for white/bright text areas
    _, text_thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    text_pixels = cv2.countNonZero(text_thresh)
    text_percentage = (text_pixels / (width * height)) * 100
    logger.info(f"{'Bright/Text regions':30} : {text_percentage:6.2f}% coverage")
    
    # Look for circular shapes (chips, buttons)
    circles = cv2.HoughCircles(
        gray, 
        cv2.HOUGH_GRADIENT, 
        dp=1, 
        minDist=20,
        param1=50, 
        param2=30, 
        minRadius=10, 
        maxRadius=50
    )
    
    circle_count = 0 if circles is None else circles.shape[1]
    logger.info(f"{'Circular shapes detected':30} : {circle_count}")
    
    # Detect rectangular regions (cards, buttons)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rect_count = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if 100 < area < 10000:  # Filter by reasonable size
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            if len(approx) == 4:  # Rectangle has 4 vertices
                rect_count += 1
    
    logger.info(f"{'Rectangular regions':30} : {rect_count}")
    
    # Save annotated image
    annotated = img.copy()
    
    # Draw detected circles
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            cv2.circle(annotated, (circle[0], circle[1]), circle[2], (0, 255, 0), 2)
    
    # Draw rectangles
    for contour in contours:
        area = cv2.contourArea(contour)
        if 100 < area < 10000:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            if len(approx) == 4:
                cv2.drawContours(annotated, [approx], -1, (0, 0, 255), 2)
    
    cv2.imwrite('annotated_screenshot.png', annotated)
    logger.info(f"\n✓ Saved annotated image to annotated_screenshot.png")
    
    # Calculate dominant color
    logger.info("\n" + "="*60)
    logger.info("DOMINANT COLOR ANALYSIS:")
    logger.info("="*60)
    
    # Reshape image to be a list of pixels
    pixels = img.reshape((-1, 3))
    
    # Use k-means to find dominant colors
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    # Get the colors
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_
    
    # Count frequency of each color
    label_counts = np.bincount(labels)
    
    # Sort by frequency
    sorted_indices = np.argsort(label_counts)[::-1]
    
    for i, idx in enumerate(sorted_indices, 1):
        bgr = colors[idx]
        percentage = (label_counts[idx] / len(labels)) * 100
        
        # Convert to HSV for better understanding
        hsv_color = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        
        logger.info(f"Color {i}: BGR({bgr[0]:.0f}, {bgr[1]:.0f}, {bgr[2]:.0f}) "
                   f"HSV({hsv_color[0]}, {hsv_color[1]}, {hsv_color[2]}) "
                   f"- {percentage:.1f}%")
    
    return True

def test_betfair_detection():
    """Test Betfair table detection with diagnostics."""
    try:
        logger.info("="*60)
        logger.info("BETFAIR SCRAPER DIAGNOSTIC TEST")
        logger.info("="*60)
        
        # Try to import the scraper
        try:
            from src.pokertool.modules.poker_screen_scraper_betfair import (
                create_scraper, PokerSite, BetfairPokerDetector
            )
            logger.info("✓ Successfully imported Betfair scraper modules")
        except ImportError as e:
            logger.error(f"Failed to import Betfair scraper: {e}")
            return False
        
        # Create scraper
        scraper = create_scraper('BETFAIR')
        logger.info("✓ Created Betfair scraper instance")
        
        # Try to capture a screenshot
        logger.info("\nAttempting to capture screenshot...")
        img = scraper.capture_table()
        
        if img is None:
            logger.error("❌ Failed to capture screenshot - no window found")
            logger.info("\nTrying alternative capture methods...")
            
            # Try using mss for full screen capture
            try:
                import mss
                with mss.mss() as sct:
                    monitor = sct.monitors[1]  # Primary monitor
                    screenshot = sct.grab(monitor)
                    img = np.array(screenshot)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    logger.info(f"✓ Captured full screen: {img.shape}")
                    cv2.imwrite('fullscreen_capture.png', img)
                    logger.info("  -> Saved to fullscreen_capture.png")
            except Exception as e:
                logger.error(f"Full screen capture failed: {e}")
            
            # Try to find Betfair windows
            logger.info("\nSearching for Betfair windows...")
            try:
                from src.pokertool.desktop_independent_scraper import (
                    create_desktop_scraper, PokerDetectionMode
                )
                desktop_scraper = create_desktop_scraper()
                windows = desktop_scraper.scan_for_poker_windows(PokerDetectionMode.FUZZY_MATCH)
                
                logger.info(f"Found {len(windows)} potential poker windows:")
                for i, window in enumerate(windows, 1):
                    logger.info(f"  {i}. {window.title} (visible: {window.is_visible})")
                    
                    # Try to capture this window
                    result = desktop_scraper.capture_window(window, include_screenshot=True)
                    if result and result.get('screenshot') is not None:
                        img = result['screenshot']
                        filename = f"window_{i}_{window.title.replace(' ', '_')[:20]}.png"
                        cv2.imwrite(filename, img)
                        logger.info(f"     -> Saved screenshot to {filename}")
                        
                        # Analyze this window
                        logger.info(f"\n     Analyzing window {i}...")
                        analyze_screenshot(img)
                        
            except Exception as e:
                logger.error(f"Desktop scraper failed: {e}")
                
        else:
            logger.info(f"✓ Captured screenshot: {img.shape}")
            cv2.imwrite('betfair_screenshot.png', img)
            logger.info("  -> Saved to betfair_screenshot.png")
            
            # Analyze the screenshot
            logger.info("\nAnalyzing screenshot...")
            analyze_screenshot(img)
            
            # Test detection
            logger.info("\n" + "="*60)
            logger.info("TESTING DETECTION:")
            logger.info("="*60)
            
            is_poker, confidence, details = scraper.detect_poker_table(img)
            logger.info(f"Detected as poker table: {is_poker}")
            logger.info(f"Confidence: {confidence:.1%}")
            logger.info(f"Detection details: {details}")
            
            if not is_poker:
                logger.warning("\n⚠ Table not detected as poker table!")
                logger.info("This could be due to:")
                logger.info("  1. Color ranges not matching the actual table")
                logger.info("  2. Window not properly captured")
                logger.info("  3. Table layout different from expected")
        
        return True
        
    except Exception as e:
        logger.error(f"Diagnostic test failed: {e}", exc_info=True)
        return False

def test_with_sample_image():
    """Test with the BF_TEST.jpg sample image."""
    try:
        logger.info("\n" + "="*60)
        logger.info("TESTING WITH SAMPLE IMAGE (BF_TEST.jpg)")
        logger.info("="*60)
        
        # Load the sample image
        sample_path = Path("BF_TEST.jpg")
        if not sample_path.exists():
            logger.error(f"Sample image not found: {sample_path}")
            return False
        
        img = cv2.imread(str(sample_path))
        if img is None:
            logger.error("Failed to load sample image")
            return False
        
        logger.info(f"✓ Loaded sample image: {img.shape}")
        
        # Analyze it
        analyze_screenshot(img)
        
        # Test detection
        from src.pokertool.modules.poker_screen_scraper_betfair import BetfairPokerDetector
        detector = BetfairPokerDetector()
        
        result = detector.detect(img)
        logger.info(f"\nBetfair detector result:")
        logger.info(f"  Detected: {result.detected}")
        logger.info(f"  Confidence: {result.confidence:.1%}")
        logger.info(f"  Details: {result.details}")
        
        return True
        
    except Exception as e:
        logger.error(f"Sample image test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnose Betfair scraper issues")
    parser.add_argument('--sample', action='store_true', help='Test with BF_TEST.jpg sample')
    parser.add_argument('--live', action='store_true', help='Test with live Betfair window')
    
    args = parser.parse_args()
    
    # Install sklearn if needed for color analysis
    try:
        import sklearn
    except ImportError:
        logger.info("Installing scikit-learn for color analysis...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])
    
    if args.sample:
        test_with_sample_image()
    elif args.live:
        test_betfair_detection()
    else:
        # Run both tests
        logger.info("Running comprehensive diagnostic...")
        test_with_sample_image()
        test_betfair_detection()
