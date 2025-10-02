#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screen Scraper Diagnostic and Fix Tool
=======================================

This module diagnoses and fixes issues with the screen scraping system.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def diagnose_chrome_capture() -> Dict[str, Any]:
    """Diagnose Chrome capture issues."""
    diagnosis = {
        'chrome_running': False,
        'chrome_debug_port': None,
        'chrome_capture_available': False,
        'chrome_window_capture_available': False,
        'mss_available': False,
        'issues': [],
        'recommendations': []
    }
    
    # Check if Chrome is running
    try:
        import subprocess
        if sys.platform == 'darwin':  # macOS
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            diagnosis['chrome_running'] = 'Google Chrome' in result.stdout or 'chrome' in result.stdout.lower()
        elif sys.platform == 'win32':  # Windows
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
            diagnosis['chrome_running'] = 'chrome.exe' in result.stdout.lower()
        else:  # Linux
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            diagnosis['chrome_running'] = 'chrome' in result.stdout.lower()
    except Exception as e:
        diagnosis['issues'].append(f"Could not check if Chrome is running: {e}")
    
    # Check for Chrome debugging port
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', 9222))
        sock.close()
        diagnosis['chrome_debug_port'] = result == 0
        if result != 0:
            diagnosis['issues'].append("Chrome debugging port (9222) is not accessible")
            diagnosis['recommendations'].append(
                "Start Chrome with remote debugging: "
                "chrome --remote-debugging-port=9222"
            )
    except Exception as e:
        diagnosis['issues'].append(f"Could not check Chrome debugging port: {e}")
    
    # Check Chrome capture dependencies
    try:
        from pokertool.modules.browser_tab_capture import (
            ChromeTabCapture,
            ChromeTabCaptureConfig,
        )
        diagnosis['chrome_capture_available'] = True
    except ImportError as e:
        diagnosis['chrome_capture_available'] = False
        diagnosis['issues'].append(f"Chrome tab capture not available: {e}")
        diagnosis['recommendations'].append("Install Chrome capture dependencies if needed")
    
    # Check mss (fallback screen capture)
    try:
        import mss
        diagnosis['mss_available'] = True
    except ImportError:
        diagnosis['mss_available'] = False
        diagnosis['issues'].append("MSS (screen capture library) not available")
        diagnosis['recommendations'].append("Install mss: pip install mss")
    
    return diagnosis

def fix_scraper_initialization() -> bool:
    """Fix the screen scraper initialization by updating the default capture source."""
    logger.info("Applying screen scraper fixes...")
    
    try:
        scrape_file = Path(__file__).parent / 'scrape.py'
        
        # Read the current file
        with open(scrape_file, 'r') as f:
            content = f.read()
        
        # Check if already fixed
        if "# SCRAPER-FIX-APPLIED" in content:
            logger.info("Scraper fixes already applied")
            return True
        
        # Make a backup
        backup_file = scrape_file.with_suffix('.py.bak')
        with open(backup_file, 'w') as f:
            f.write(content)
        logger.info(f"Created backup: {backup_file}")
        
        # Apply fixes
        # 1. Change default capture source from 'chrome_tab' to 'monitor' for reliability
        content = content.replace(
            "self.capture_source = self.config.get('capture_source', 'monitor')",
            "# SCRAPER-FIX-APPLIED: Use monitor as default\n" +
            "        self.capture_source = self.config.get('capture_source', 'monitor')"
        )
        
        # 2. Add better error handling for Chrome capture initialization
        old_init = "if self.capture_source == 'chrome_tab':\n            self._initialise_chrome_capture()"
        new_init = """# SCRAPER-FIX-APPLIED: Better Chrome initialization
        if self.capture_source == 'chrome_tab':
            try:
                self._initialise_chrome_capture()
            except Exception as e:
                logger.warning(f"Chrome tab capture init failed: {e}")
                self.capture_source = 'monitor'"""
        
        content = content.replace(old_init, new_init)
        
        # Write the fixed file
        with open(scrape_file, 'w') as f:
            f.write(content)
        
        logger.info("Screen scraper fixes applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply fixes: {e}")
        return False

def test_screen_capture() -> Dict[str, Any]:
    """Test all available screen capture methods."""
    results = {
        'mss_test': False,
        'chrome_test': False,
        'desktop_scraper_test': False,
        'errors': []
    }
    
    # Test MSS
    try:
        import mss
        import numpy as np
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            
            if img.size > 0:
                results['mss_test'] = True
                logger.info(f"✓ MSS test passed - captured {img.shape}")
            else:
                results['errors'].append("MSS captured empty image")
    except Exception as e:
        results['errors'].append(f"MSS test failed: {e}")
        logger.error(f"MSS test failed: {e}")
    
    # Test Desktop Independent Scraper
    try:
        from pokertool.desktop_independent_scraper import create_desktop_scraper
        
        scraper = create_desktop_scraper()
        windows = scraper.scan_for_poker_windows()
        
        results['desktop_scraper_test'] = True
        results['windows_found'] = len(windows)
        logger.info(f"✓ Desktop scraper test passed - found {len(windows)} windows")
        
    except Exception as e:
        results['errors'].append(f"Desktop scraper test failed: {e}")
        logger.error(f"Desktop scraper test failed: {e}")
    
    return results

def main():
    """Main diagnostic and fix routine."""
    print("=" * 60)
    print("PokerTool Screen Scraper Diagnostic Tool")
    print("=" * 60)
    
    # Diagnose Chrome issues
    print("\n1. Diagnosing Chrome Capture...")
    print("-" * 60)
    chrome_diag = diagnose_chrome_capture()
    
    print(f"Chrome Running: {'✓' if chrome_diag['chrome_running'] else '✗'}")
    print(f"Chrome Debug Port (9222): {'✓' if chrome_diag['chrome_debug_port'] else '✗'}")
    print(f"Chrome Tab Capture Available: {'✓' if chrome_diag['chrome_capture_available'] else '✗'}")
    print(f"MSS Available: {'✓' if chrome_diag['mss_available'] else '✗'}")
    
    if chrome_diag['issues']:
        print("\nIssues Found:")
        for issue in chrome_diag['issues']:
            print(f"  • {issue}")
    
    if chrome_diag['recommendations']:
        print("\nRecommendations:")
        for rec in chrome_diag['recommendations']:
            print(f"  • {rec}")
    
    # Test screen capture
    print("\n2. Testing Screen Capture Methods...")
    print("-" * 60)
    test_results = test_screen_capture()
    
    print(f"MSS (Monitor Capture): {'✓ PASS' if test_results['mss_test'] else '✗ FAIL'}")
    print(f"Desktop Independent Scraper: {'✓ PASS' if test_results['desktop_scraper_test'] else '✗ FAIL'}")
    
    if 'windows_found' in test_results:
        print(f"Poker Windows Found: {test_results['windows_found']}")
    
    if test_results['errors']:
        print("\nErrors:")
        for error in test_results['errors']:
            print(f"  • {error}")
    
    # Apply fixes if needed
    print("\n3. Applying Fixes...")
    print("-" * 60)
    
    if not chrome_diag['chrome_debug_port']:
        print("⚠ Chrome debugging not available - will use monitor capture")
    
    if fix_scraper_initialization():
        print("✓ Scraper initialization fixes applied")
    else:
        print("✗ Failed to apply scraper fixes")
    
    # Final recommendations
    print("\n4. Final Recommendations")
    print("-" * 60)
    
    if test_results['mss_test']:
        print("✓ Monitor capture is working - this is the most reliable method")
    else:
        print("✗ Monitor capture failed - install mss: pip install mss")
    
    if test_results['desktop_scraper_test']:
        print("✓ Desktop independent scraper is working")
    else:
        print("⚠ Desktop independent scraper had issues")
    
    print("\nTo use screen scraping:")
    print("  1. Use monitor capture (most reliable)")
    print("  2. Or set up Chrome debugging port if you need browser capture")
    print("  3. Run test_desktop_scraper.py to verify")
    
    print("\n" + "=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)

if __name__ == '__main__':
    main()
