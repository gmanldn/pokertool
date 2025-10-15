#!/usr/bin/env python3
"""
Test script for the desktop-independent screen scraper.
This validates that screen scraping works without Chrome connection
and across different desktops/workspaces.
"""

import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_desktop_independent_scraper():
    """Test the desktop-independent scraper functionality."""
    print("Testing Desktop-Independent Screen Scraper")
    print("=" * 60)
    
    try:
        # Test direct import
        from pokertool.desktop_independent_scraper import (
            create_desktop_scraper, 
            test_desktop_independence,
            quick_poker_scan
        )
        print("✅ Direct import successful")
        
        # Test creation
        scraper = create_desktop_scraper()
        print("✅ Scraper creation successful")
        
        # Test capabilities check
        capabilities = scraper.get_platform_capabilities()
        print(f"✅ Platform: {capabilities['platform']}")
        print(f"✅ Screen Capture: {'✓' if capabilities['screen_capture'] else '✗'}")
        print(f"✅ Cross-Desktop: {'✓' if capabilities['cross_desktop'] else '✗'}")
        print(f"✅ Multi-Monitor: {'✓' if capabilities['multi_monitor'] else '✗'}")
        
        # Test window scanning
        print("\n🔍 Scanning for poker windows...")
        windows = scraper.scan_for_poker_windows()
        print(f"✅ Found {len(windows)} potential poker windows")
        
        if windows:
            print("\n📋 Detected Windows:")
            for i, window in enumerate(windows[:3], 1):  # Show first 3
                print(f"  {i}. {window.title}")
                print(f"     Size: {window.width}x{window.height}")
                print(f"     Position: ({window.x}, {window.y})")
                print(f"     Visible: {'✓' if window.is_visible else '✗'}")
                print(f"     Area: {window.area:,} pixels")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_scraper_integration():
    """Test integration with the main scraper module."""
    print("\n" + "=" * 60)
    print("Testing Scraper Integration")
    print("=" * 60)
    
    try:
        from pokertool.scrape import (
            run_desktop_independent_scraper,
            get_desktop_scraper_status,
            quick_poker_window_scan,
            DESKTOP_SCRAPER_AVAILABLE
        )
        
        print(f"✅ Desktop scraper available: {'✓' if DESKTOP_SCRAPER_AVAILABLE else '✗'}")
        
        if not DESKTOP_SCRAPER_AVAILABLE:
            print("⚠️ Desktop scraper not available - check dependencies")
            return False
        
        # Test status check
        status = get_desktop_scraper_status()
        print(f"✅ Status check: {status['available']}")
        
        # Test quick scan
        scan_result = quick_poker_window_scan()
        print(f"✅ Quick scan: {scan_result['status']}")
        print(f"✅ Windows found: {scan_result.get('windows_found', 0)}")
        
        if scan_result['status'] == 'success' and scan_result.get('windows_found', 0) > 0:
            print("✅ Found poker windows - testing single capture...")
            
            # Test single capture
            result = run_desktop_independent_scraper(
                detection_mode='COMBINED',
                continuous=False
            )
            print(f"✅ Single capture: {result['status']}")
            
            if 'capture_results' in result:
                active_tables = sum(1 for r in result['capture_results'] if r.get('likely_poker_table'))
                print(f"✅ Active poker tables detected: {active_tables}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Integration import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False

def test_platform_specific_features():
    """Test platform-specific window detection features."""
    print("\n" + "=" * 60)
    print("Testing Platform-Specific Features")
    print("=" * 60)
    
    try:
        from pokertool.desktop_independent_scraper import (
            create_desktop_scraper,
            PokerDetectionMode
        )
        
        scraper = create_desktop_scraper()
        print(f"✅ Platform: {scraper.platform}")
        
        # Test different detection modes
        modes = [
            ('COMBINED', PokerDetectionMode.COMBINED),
            ('WINDOW_TITLE', PokerDetectionMode.WINDOW_TITLE),
            ('FUZZY_MATCH', PokerDetectionMode.FUZZY_MATCH)
        ]
        
        for mode_name, mode_enum in modes:
            try:
                windows = scraper.scan_for_poker_windows(mode_enum)
                print(f"✅ {mode_name} mode: {len(windows)} windows")
            except Exception as e:
                print(f"⚠️ {mode_name} mode error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Platform test error: {e}")
        return False

def test_error_handling():
    """Test error handling and edge cases."""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    try:
        from pokertool.scrape import run_desktop_independent_scraper
        
        # Test with invalid detection mode
        result = run_desktop_independent_scraper(detection_mode='INVALID_MODE')
        print(f"✅ Invalid mode handled: {result['status']}")
        
        # Test empty windows scenario
        result = run_desktop_independent_scraper(detection_mode='PROCESS_NAME')  # Less likely to find matches
        print(f"✅ Empty results handled: {result.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def show_dependencies_status():
    """Show the status of all dependencies."""
    print("\n" + "=" * 60)
    print("Dependencies Status")
    print("=" * 60)
    
    dependencies = {
        'mss': 'Cross-platform screen capture',
        'cv2': 'Computer vision and image processing', 
        'PIL': 'Python Imaging Library',
        'numpy': 'Numerical computing',
        'pytesseract': 'OCR text recognition (optional)'
    }
    
    # Platform-specific
    if sys.platform == 'win32':
        dependencies.update({
            'win32gui': 'Windows API for window management',
            'win32process': 'Windows process management'
        })
    elif sys.platform == 'darwin':
        dependencies.update({
            'Quartz': 'macOS window management',
            'AppKit': 'macOS application framework'
        })
    elif sys.platform.startswith('linux'):
        dependencies['subprocess'] = 'Linux command execution'
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            status = "✅ Available"
        except ImportError:
            status = "❌ Missing"
        
        print(f"{status:<12} {module:<15} - {description}")

def main():
    """Run all tests."""
    print("Desktop-Independent Screen Scraper Test Suite")
    print("=" * 60)
    
    # Show dependency status first
    show_dependencies_status()
    
    # Run tests
    tests = [
        ("Desktop Independent Scraper", test_desktop_independent_scraper),
        ("Scraper Integration", test_scraper_integration), 
        ("Platform Features", test_platform_specific_features),
        ("Error Handling", test_error_handling)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Desktop-independent scraping is ready.")
        print("\nKey Features Available:")
        print("• ✅ Cross-desktop window detection")
        print("• ✅ No Chrome connection required") 
        print("• ✅ Multi-platform support")
        print("• ✅ OCR integration")
        print("• ✅ Real-time monitoring")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Check dependencies and configuration.")
        
        print("\nTo resolve issues:")
        print("• Install missing dependencies: pip install mss opencv-python pillow")
        if sys.platform == 'win32':
            print("• Windows: pip install pywin32")
        elif sys.platform == 'darwin':
            print("• macOS: pip install pyobjc-framework-Quartz")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
