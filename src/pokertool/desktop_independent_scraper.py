#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Desktop Independent Screen Scraper
==================================

Cross-platform screen scraping that works regardless of desktop/workspace separation.
Eliminates Chrome connection requirements and enables multi-desktop poker monitoring.

Features:
- Cross-desktop window detection and capture
- Platform-specific window management (macOS, Windows, Linux)
- OCR text recognition without browser dependencies
- Multi-monitor support
- Workspace-independent operation

Module: pokertool.desktop_independent_scraper
Version: 1.0.0
Author: PokerTool Development Team
License: MIT
"""

__version__ = '1.0.0'
__author__ = 'PokerTool Development Team'

import logging
import os
import sys
import time
import threading
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import numpy as np

# Cross-platform dependencies
try:
    import mss
    import cv2
    from PIL import Image, ImageTk
    MSS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Core screen capture dependencies not available: {e}")
    MSS_AVAILABLE = False

# Platform-specific window management
PLATFORM_WINDOWS = sys.platform == 'win32'
PLATFORM_MACOS = sys.platform == 'darwin'
PLATFORM_LINUX = sys.platform.startswith('linux')

# Windows-specific imports
if PLATFORM_WINDOWS:
    try:
        import win32gui
        import win32con
        import win32api
        import win32process
        WINDOWS_API_AVAILABLE = True
    except ImportError:
        WINDOWS_API_AVAILABLE = False
else:
    WINDOWS_API_AVAILABLE = False

# macOS-specific imports
if PLATFORM_MACOS:
    try:
        import Quartz
        import AppKit
        from Foundation import NSString
        MACOS_API_AVAILABLE = True
    except ImportError:
        MACOS_API_AVAILABLE = False
else:
    MACOS_API_AVAILABLE = False

# Linux-specific imports
if PLATFORM_LINUX:
    try:
        import subprocess
        LINUX_TOOLS_AVAILABLE = True
    except ImportError:
        LINUX_TOOLS_AVAILABLE = False
else:
    LINUX_TOOLS_AVAILABLE = False

# OCR dependencies
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class WindowInfo:
    """Information about a detected window."""
    handle: Any
    title: str
    pid: int
    x: int
    y: int
    width: int
    height: int
    is_visible: bool
    is_minimized: bool
    desktop_id: Optional[int] = None
    workspace_name: Optional[str] = None
    
    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Return window bounds as (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)
    
    @property
    def area(self) -> int:
        """Calculate window area."""
        return self.width * self.height if self.width > 0 and self.height > 0 else 0

@dataclass
class ScreenRegion:
    """Define a region on screen for capture."""
    x: int
    y: int
    width: int
    height: int
    name: str = ""
    
    def to_mss_monitor(self) -> Dict[str, int]:
        """Convert to mss monitor format."""
        return {
            'left': self.x,
            'top': self.y,
            'width': self.width,
            'height': self.height
        }

class PokerDetectionMode(Enum):
    """Different modes for detecting poker applications."""
    WINDOW_TITLE = "window_title"  # Match by window title patterns
    PROCESS_NAME = "process_name"  # Match by process/executable name
    COMBINED = "combined"          # Use both methods
    FUZZY_MATCH = "fuzzy_match"   # Fuzzy matching for similar titles

class DesktopIndependentScraper:
    """
    Desktop-independent screen scraper that can capture poker tables
    regardless of desktop/workspace separation.
    """
    
    def __init__(self):
        self.sct = None
        self.running = False
        self.detected_windows: List[WindowInfo] = []
        self.active_captures: Dict[str, Any] = {}
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Platform-specific initialization
        self.platform = self._detect_platform()
        self._init_platform_specific()
        
        # Poker application patterns
        self.poker_patterns = {
            'window_titles': [
                r'.*[Pp]oker[Ss]tars.*',
                r'.*[Pp]arty[Pp]oker.*',
                r'.*[Ii]gnition.*',
                r'.*[Bb]ovada.*',
                r'.*[Cc]asino.*',
                r'.*[Pp]oker.*',
                r'.*[Hh]old.*[Ee]m.*',
                r'.*[Tt]exas.*',
                r'.*NL.*Hold.*'
            ],
            'process_names': [
                'PokerStars.exe',
                'PartyPoker.exe', 
                'IgnitionCasino.exe',
                'BovadaPoker.exe',
                'poker.exe',
                'holdem.exe'
            ]
        }
        
        if MSS_AVAILABLE:
            self.sct = mss.mss()
            logger.info(f"Desktop-independent scraper initialized for {self.platform}")
        else:
            logger.error("MSS not available - screen capture disabled")
    
    def _detect_platform(self) -> str:
        """Detect current platform."""
        if PLATFORM_WINDOWS:
            return "Windows"
        elif PLATFORM_MACOS:
            return "macOS"
        elif PLATFORM_LINUX:
            return "Linux"
        else:
            return "Unknown"
    
    def _init_platform_specific(self):
        """Initialize platform-specific components."""
        if PLATFORM_WINDOWS and not WINDOWS_API_AVAILABLE:
            logger.warning("Windows API not available - install pywin32 for full functionality")
        
        if PLATFORM_MACOS and not MACOS_API_AVAILABLE:
            logger.warning("macOS API not available - install pyobjc for full functionality")
        
        if PLATFORM_LINUX and not LINUX_TOOLS_AVAILABLE:
            logger.warning("Linux tools not available - limited functionality")
    
    def scan_for_poker_windows(self, mode: PokerDetectionMode = PokerDetectionMode.COMBINED) -> List[WindowInfo]:
        """
        Scan all desktops/workspaces for poker application windows.
        
        Args:
            mode: Detection mode to use
            
        Returns:
            List of detected poker windows
        """
        self.detected_windows.clear()
        
        if PLATFORM_WINDOWS:
            self._scan_windows_windows(mode)
        elif PLATFORM_MACOS:
            self._scan_macos_windows(mode)
        elif PLATFORM_LINUX:
            self._scan_linux_windows(mode)
        else:
            logger.warning(f"Unsupported platform: {self.platform}")
        
        # Filter and sort results
        valid_windows = [w for w in self.detected_windows if w.area > 10000]  # Minimum size
        valid_windows.sort(key=lambda w: w.area, reverse=True)  # Largest first
        
        logger.info(f"Found {len(valid_windows)} poker windows across all desktops")
        return valid_windows
    
    def _scan_windows_windows(self, mode: PokerDetectionMode):
        """Scan for poker windows on Windows."""
        if not WINDOWS_API_AVAILABLE:
            logger.error("Windows API not available for window scanning")
            return
        
        def enum_windows_callback(hwnd, _):
            try:
                if not win32gui.IsWindow(hwnd):
                    return True
                
                title = win32gui.GetWindowText(hwnd)
                if not title:
                    return True
                
                # Get window rect
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, right, bottom = rect
                    width = right - x
                    height = bottom - y
                except:
                    return True
                
                # Get process info
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                except:
                    pid = 0
                
                # Check if window matches poker patterns
                if self._matches_poker_patterns(title, "", mode):
                    is_visible = win32gui.IsWindowVisible(hwnd)
                    is_minimized = win32gui.IsIconic(hwnd)
                    
                    window_info = WindowInfo(
                        handle=hwnd,
                        title=title,
                        pid=pid,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        is_visible=is_visible,
                        is_minimized=is_minimized
                    )
                    
                    self.detected_windows.append(window_info)
                
            except Exception as e:
                logger.debug(f"Error processing window {hwnd}: {e}")
            
            return True
        
        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            logger.error(f"Windows enumeration failed: {e}")
    
    def _scan_macos_windows(self, mode: PokerDetectionMode):
        """Scan for poker windows on macOS."""
        if not MACOS_API_AVAILABLE:
            logger.error("macOS API not available for window scanning")
            return
        
        try:
            # Get all windows across all spaces/desktops
            options = Quartz.kCGWindowListOptionAll
            window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
            
            for window in window_list:
                try:
                    window_dict = dict(window)
                    
                    # Extract window information
                    title = window_dict.get('kCGWindowName', '')
                    owner_name = window_dict.get('kCGWindowOwnerName', '')
                    pid = window_dict.get('kCGWindowOwnerPID', 0)
                    
                    bounds = window_dict.get('kCGWindowBounds', {})
                    x = int(bounds.get('X', 0))
                    y = int(bounds.get('Y', 0))
                    width = int(bounds.get('Width', 0))
                    height = int(bounds.get('Height', 0))
                    
                    # Check window layer (0 = normal windows)
                    layer = window_dict.get('kCGWindowLayer', -1)
                    is_on_screen = window_dict.get('kCGWindowIsOnscreen', False)
                    
                    # Check if this is a poker window
                    if self._matches_poker_patterns(title, owner_name, mode):
                        window_info = WindowInfo(
                            handle=window_dict.get('kCGWindowNumber', 0),
                            title=title or owner_name,
                            pid=pid,
                            x=x,
                            y=y,
                            width=width,
                            height=height,
                            is_visible=is_on_screen and layer == 0,
                            is_minimized=not is_on_screen
                        )
                        
                        self.detected_windows.append(window_info)
                        
                except Exception as e:
                    logger.debug(f"Error processing macOS window: {e}")
                    
        except Exception as e:
            logger.error(f"macOS window enumeration failed: {e}")
    
    def _scan_linux_windows(self, mode: PokerDetectionMode):
        """Scan for poker windows on Linux."""
        if not LINUX_TOOLS_AVAILABLE:
            logger.error("Linux tools not available for window scanning")
            return
        
        try:
            # Try xwininfo and wmctrl approaches
            methods = [
                self._scan_linux_wmctrl,
                self._scan_linux_xwininfo
            ]
            
            for method in methods:
                try:
                    method(mode)
                    if self.detected_windows:
                        break
                except Exception as e:
                    logger.debug(f"Linux scan method failed: {e}")
                    
        except Exception as e:
            logger.error(f"Linux window scanning failed: {e}")
    
    def _scan_linux_wmctrl(self, mode: PokerDetectionMode):
        """Scan using wmctrl on Linux."""
        try:
            result = subprocess.run(['wmctrl', '-lG'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split(None, 7)
                if len(parts) < 8:
                    continue
                
                window_id = parts[0]
                desktop = parts[1]
                x = int(parts[2])
                y = int(parts[3]) 
                width = int(parts[4])
                height = int(parts[5])
                title = parts[7] if len(parts) > 7 else ""
                
                if self._matches_poker_patterns(title, "", mode):
                    window_info = WindowInfo(
                        handle=window_id,
                        title=title,
                        pid=0,  # wmctrl doesn't provide PID
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        is_visible=desktop != "-1",
                        is_minimized=False,
                        desktop_id=int(desktop) if desktop.isdigit() else None
                    )
                    
                    self.detected_windows.append(window_info)
                    
        except subprocess.TimeoutExpired:
            logger.warning("wmctrl command timed out")
        except FileNotFoundError:
            logger.debug("wmctrl not found")
    
    def _scan_linux_xwininfo(self, mode: PokerDetectionMode):
        """Scan using xwininfo on Linux."""
        try:
            # Get root window info first
            result = subprocess.run(['xwininfo', '-root', '-tree'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return
            
            import re
            window_pattern = r'(0x[0-9a-f]+) "([^"]*)".*?(\d+)x(\d+)\+(\d+)\+(\d+)'
            
            for match in re.finditer(window_pattern, result.stdout):
                window_id = match.group(1)
                title = match.group(2)
                width = int(match.group(3))
                height = int(match.group(4))
                x = int(match.group(5))
                y = int(match.group(6))
                
                if self._matches_poker_patterns(title, "", mode):
                    window_info = WindowInfo(
                        handle=window_id,
                        title=title,
                        pid=0,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        is_visible=True,
                        is_minimized=False
                    )
                    
                    self.detected_windows.append(window_info)
                    
        except subprocess.TimeoutExpired:
            logger.warning("xwininfo command timed out")
        except FileNotFoundError:
            logger.debug("xwininfo not found")
    
    def _matches_poker_patterns(self, title: str, process_name: str, mode: PokerDetectionMode) -> bool:
        """Check if window matches poker application patterns."""
        import re
        
        title_match = False
        process_match = False
        
        # Check window title patterns
        if title and (mode in [PokerDetectionMode.WINDOW_TITLE, PokerDetectionMode.COMBINED]):
            for pattern in self.poker_patterns['window_titles']:
                if re.search(pattern, title, re.IGNORECASE):
                    title_match = True
                    break
        
        # Check process name patterns
        if process_name and (mode in [PokerDetectionMode.PROCESS_NAME, PokerDetectionMode.COMBINED]):
            for pattern in self.poker_patterns['process_names']:
                if pattern.lower() in process_name.lower():
                    process_match = True
                    break
        
        # Fuzzy matching
        if mode == PokerDetectionMode.FUZZY_MATCH:
            poker_keywords = ['poker', 'hold', 'texas', 'casino', 'bet', 'table']
            text = (title + " " + process_name).lower()
            fuzzy_match = any(keyword in text for keyword in poker_keywords)
            return fuzzy_match
        
        # Return based on mode
        if mode == PokerDetectionMode.WINDOW_TITLE:
            return title_match
        elif mode == PokerDetectionMode.PROCESS_NAME:
            return process_match
        elif mode == PokerDetectionMode.COMBINED:
            return title_match or process_match
        
        return False
    
    def capture_window(self, window: WindowInfo, include_screenshot: bool = True) -> Optional[Dict[str, Any]]:
        """
        Capture a specific poker window regardless of desktop/workspace.
        
        Args:
            window: Window to capture
            include_screenshot: Whether to include the actual screenshot
            
        Returns:
            Dict containing window capture data
        """
        if not self.sct:
            logger.error("Screen capture not available")
            return None
        
        try:
            # Create capture region
            monitor = {
                'left': window.x,
                'top': window.y,
                'width': window.width,
                'height': window.height
            }
            
            screenshot = None
            if include_screenshot:
                # Capture window screenshot
                sct_img = self.sct.grab(monitor)
                screenshot = np.array(sct_img)
                
                # Convert BGRA to BGR if needed
                if screenshot.shape[2] == 4:
                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            # Build capture result
            result = {
                'window_info': window,
                'timestamp': time.time(),
                'screenshot': screenshot,
                'capture_region': monitor,
                'success': True,
                'platform': self.platform
            }
            
            # Try to extract game state information
            if screenshot is not None:
                game_state = self._analyze_poker_screenshot(screenshot, window)
                result.update(game_state)
            
            return result
            
        except Exception as e:
            logger.error(f"Window capture failed for {window.title}: {e}")
            return {
                'window_info': window,
                'timestamp': time.time(),
                'screenshot': None,
                'success': False,
                'error': str(e),
                'platform': self.platform
            }
    
    def _analyze_poker_screenshot(self, screenshot: np.ndarray, window: WindowInfo) -> Dict[str, Any]:
        """Analyze poker table screenshot to extract game state."""
        analysis = {
            'pot_detected': False,
            'cards_detected': False,
            'buttons_detected': False,
            'table_active': False,
        }
        
        try:
            # Basic image analysis
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Detect if table is active (look for green felt color)
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            
            # Green range for poker table felt
            lower_green = np.array([40, 40, 40])
            upper_green = np.array([80, 255, 255])
            green_mask = cv2.inRange(hsv, lower_green, upper_green)
            green_pixels = cv2.countNonZero(green_mask)
            
            total_pixels = screenshot.shape[0] * screenshot.shape[1]
            green_ratio = green_pixels / total_pixels
            
            analysis['table_active'] = green_ratio > 0.1  # At least 10% green
            analysis['green_ratio'] = green_ratio
            
            # Look for cards (white rectangles with rounded corners)
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            card_like_contours = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if 500 < area < 5000:  # Card-like area
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    if 0.6 < aspect_ratio < 0.8:  # Card-like aspect ratio
                        card_like_contours.append((x, y, w, h))
            
            analysis['cards_detected'] = len(card_like_contours) > 0
            analysis['potential_cards'] = len(card_like_contours)
            
            # Look for circular buttons (chips, dealer button)
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                     param1=50, param2=30, minRadius=10, maxRadius=50)
            
            if circles is not None:
                analysis['buttons_detected'] = True
                analysis['button_count'] = len(circles[0])
            
            # OCR for pot size and betting amounts
            if OCR_AVAILABLE:
                try:
                    text = pytesseract.image_to_string(screenshot, config='--psm 6')
                    
                    # Look for currency symbols and numbers
                    import re
                    money_pattern = r'[\$€£¥]\s*\d+(?:,\d{3})*(?:\.\d{2})?'
                    amounts = re.findall(money_pattern, text)
                    
                    if amounts:
                        analysis['pot_detected'] = True
                        analysis['detected_amounts'] = amounts
                        
                except Exception as e:
                    logger.debug(f"OCR analysis failed: {e}")
            
            # Overall activity score
            activity_score = 0
            if analysis['table_active']:
                activity_score += 40
            if analysis['cards_detected']:
                activity_score += 30
            if analysis['buttons_detected']:
                activity_score += 20
            if analysis['pot_detected']:
                activity_score += 10
                
            analysis['activity_score'] = activity_score
            analysis['likely_poker_table'] = activity_score >= 50
            
        except Exception as e:
            logger.debug(f"Screenshot analysis error: {e}")
            analysis['analysis_error'] = str(e)
        
        return analysis
    
    def start_continuous_monitoring(self, interval: float = 2.0) -> bool:
        """
        Start continuous monitoring of all detected poker windows.
        
        Args:
            interval: Capture interval in seconds
            
        Returns:
            True if monitoring started successfully
        """
        if self.running:
            logger.warning("Monitoring already running")
            return True
        
        if not self.detected_windows:
            logger.warning("No poker windows detected - run scan_for_poker_windows() first")
            return False
        
        self.running = True
        
        def monitoring_loop():
            logger.info(f"Started monitoring {len(self.detected_windows)} poker windows")
            
            while self.running:
                try:
                    for window in self.detected_windows:
                        if not self.running:
                            break
                        
                        # Capture window
                        result = self.capture_window(window, include_screenshot=True)
                        
                        if result and result.get('success'):
                            # Notify callbacks
                            for callback in self.callbacks:
                                try:
                                    callback(result)
                                except Exception as e:
                                    logger.error(f"Callback error: {e}")
                    
                    # Wait before next round
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(interval)
            
            logger.info("Monitoring stopped")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        
        return True
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.running = False
        logger.info("Stopping continuous monitoring")
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for capture results."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregister callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def save_debug_screenshots(self, output_dir: str = "debug_screenshots") -> List[str]:
        """Save debug screenshots of all detected windows."""
        if not self.detected_windows:
            logger.warning("No windows to capture")
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        saved_files = []
        
        for i, window in enumerate(self.detected_windows):
            try:
                result = self.capture_window(window, include_screenshot=True)
                
                if result and result.get('success') and result.get('screenshot') is not None:
                    filename = f"poker_window_{i}_{window.title.replace(' ', '_')[:30]}.png"
                    filepath = output_path / filename
                    
                    # Save using OpenCV
                    cv2.imwrite(str(filepath), result['screenshot'])
                    saved_files.append(str(filepath))
                    
                    logger.info(f"Saved debug screenshot: {filepath}")
                
            except Exception as e:
                logger.error(f"Failed to save screenshot for window {window.title}: {e}")
        
        return saved_files
    
    def get_platform_capabilities(self) -> Dict[str, Any]:
        """Get platform-specific capabilities."""
        return {
            'platform': self.platform,
            'screen_capture': MSS_AVAILABLE,
            'window_management': {
                'windows': WINDOWS_API_AVAILABLE,
                'macos': MACOS_API_AVAILABLE, 
                'linux': LINUX_TOOLS_AVAILABLE
            },
            'ocr': OCR_AVAILABLE,
            'cross_desktop': True,  # This scraper supports cross-desktop capture
            'multi_monitor': MSS_AVAILABLE
        }

# Convenience functions
def create_desktop_scraper() -> DesktopIndependentScraper:
    """Create a desktop-independent scraper instance."""
    return DesktopIndependentScraper()

def quick_poker_scan() -> List[WindowInfo]:
    """Quick scan for poker windows across all desktops."""
    scraper = create_desktop_scraper()
    return scraper.scan_for_poker_windows()

def test_desktop_independence():
    """Test desktop-independent functionality."""
    print("Testing Desktop Independent Scraper")
    print("=" * 50)
    
    scraper = create_desktop_scraper()
    capabilities = scraper.get_platform_capabilities()
    
    print(f"Platform: {capabilities['platform']}")
    print(f"Screen Capture: {'✓' if capabilities['screen_capture'] else '✗'}")
    print(f"OCR Available: {'✓' if capabilities['ocr'] else '✗'}")
    print(f"Cross-Desktop: {'✓' if capabilities['cross_desktop'] else '✗'}")
    
    print("\nScanning for poker windows...")
    windows = scraper.scan_for_poker_windows()
    
    if windows:
        print(f"Found {len(windows)} poker windows:")
        for i, window in enumerate(windows):
            print(f"  {i+1}. {window.title} ({window.width}x{window.height})")
            print(f"      Position: ({window.x}, {window.y})")
            print(f"      Visible: {window.is_visible}, Minimized: {window.is_minimized}")
        
        # Test capture
        print("\nTesting window capture...")
        for window in windows[:2]:  # Test first 2 windows
            result = scraper.capture_window(window, include_screenshot=False)
            if result and result.get('success'):
                print(f"✓ Successfully captured {window.title}")
                if result.get('likely_poker_table'):
                    print(f"  ✓ Detected active poker table")
            else:
                print(f"✗ Failed to capture {window.title}")
    else:
        print("No poker windows found")
        print("Try opening a poker application and run the test again")
    
    return scraper

if __name__ == '__main__':
    test_desktop_independence()
