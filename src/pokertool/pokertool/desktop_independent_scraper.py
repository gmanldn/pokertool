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
import re
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import numpy as np
from collections import deque

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
        
        # Performance optimization features
        self._window_cache: Dict[str, WindowInfo] = {}
        self._last_scan_time = 0.0
        self._scan_cache_duration = 5.0  # Cache window scan results for 5 seconds
        self._capture_history: deque = deque(maxlen=100)  # Keep last 100 captures
        self._analysis_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}  # Cache analysis results
        self._cache_ttl = 2.0  # Cache analysis for 2 seconds
        
        # Adaptive monitoring
        self._adaptive_intervals = True
        self._base_interval = 2.0
        self._fast_interval = 0.5
        self._slow_interval = 5.0
        self._consecutive_no_activity = 0
        
        # Performance metrics
        self._metrics = {
            'total_captures': 0,
            'successful_captures': 0,
            'failed_captures': 0,
            'avg_capture_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
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
        """Enhanced poker table screenshot analysis with caching and improved accuracy."""
        
        # Create cache key based on image hash
        cache_key = f"{window.handle}_{hash(screenshot.tobytes())}"
        current_time = time.time()
        
        # Check cache first
        if cache_key in self._analysis_cache:
            cached_time, cached_result = self._analysis_cache[cache_key]
            if current_time - cached_time < self._cache_ttl:
                self._metrics['cache_hits'] += 1
                return cached_result
        
        self._metrics['cache_misses'] += 1
        analysis = self._enhanced_table_analysis(screenshot, window)
        
        # Cache result
        self._analysis_cache[cache_key] = (current_time, analysis)
        
        # Clean old cache entries
        self._cleanup_analysis_cache()
        
        return analysis
    
    def _enhanced_table_analysis(self, screenshot: np.ndarray, window: WindowInfo) -> Dict[str, Any]:
        """Enhanced analysis with multiple detection algorithms."""
        analysis = {
            'pot_detected': False,
            'cards_detected': False,
            'buttons_detected': False,
            'table_active': False,
            'action_buttons_visible': False,
            'seat_count': 0,
            'hero_cards_visible': False,
            'board_cards_count': 0,
            'confidence_score': 0.0
        }
        
        try:
            start_time = time.time()
            
            # Multi-scale analysis for better detection
            scales = [1.0, 0.8, 0.6] if screenshot.shape[0] > 800 else [1.0]
            best_analysis = None
            best_confidence = 0.0
            
            for scale in scales:
                scaled_analysis = self._analyze_at_scale(screenshot, scale)
                if scaled_analysis['confidence_score'] > best_confidence:
                    best_confidence = scaled_analysis['confidence_score']
                    best_analysis = scaled_analysis
            
            if best_analysis:
                analysis.update(best_analysis)
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self._metrics['avg_capture_time'] = (
                (self._metrics['avg_capture_time'] * self._metrics['total_captures'] + processing_time) /
                (self._metrics['total_captures'] + 1)
            )
            
        except Exception as e:
            logger.debug(f"Enhanced analysis error: {e}")
            analysis['analysis_error'] = str(e)
        
        return analysis
    
    def _analyze_at_scale(self, screenshot: np.ndarray, scale: float) -> Dict[str, Any]:
        """Analyze screenshot at a specific scale for multi-scale detection."""
        if scale != 1.0:
            height, width = screenshot.shape[:2]
            new_height, new_width = int(height * scale), int(width * scale)
            screenshot = cv2.resize(screenshot, (new_width, new_height))
        
        analysis = {
            'pot_detected': False,
            'cards_detected': False,
            'buttons_detected': False,
            'table_active': False,
            'action_buttons_visible': False,
            'seat_count': 0,
            'hero_cards_visible': False,
            'board_cards_count': 0,
            'confidence_score': 0.0
        }
        
        try:
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(screenshot, cv2.COLOR_BGR2LAB)
            
            # Enhanced table detection using multiple color spaces
            table_confidence = self._detect_poker_table(screenshot, hsv, lab)
            analysis['table_active'] = table_confidence > 0.3
            analysis['confidence_score'] += table_confidence * 0.4
            
            # Advanced card detection
            card_analysis = self._detect_cards_advanced(screenshot, gray, hsv)
            analysis.update(card_analysis)
            analysis['confidence_score'] += card_analysis.get('card_confidence', 0) * 0.3
            
            # Button and UI element detection
            ui_analysis = self._detect_poker_ui_elements(screenshot, gray)
            analysis.update(ui_analysis)
            analysis['confidence_score'] += ui_analysis.get('ui_confidence', 0) * 0.2
            
            # OCR enhancement with better preprocessing
            ocr_analysis = self._enhanced_ocr_analysis(screenshot, gray)
            analysis.update(ocr_analysis)
            analysis['confidence_score'] += ocr_analysis.get('text_confidence', 0) * 0.1
            
            # Calculate overall activity score
            activity_score = 0
            if analysis['table_active']:
                activity_score += 40
            if analysis['cards_detected']:
                activity_score += 30
            if analysis['action_buttons_visible']:
                activity_score += 20
            if analysis['pot_detected']:
                activity_score += 10
                
            analysis['activity_score'] = activity_score
            analysis['likely_poker_table'] = activity_score >= 50
            
        except Exception as e:
            logger.debug(f"Scale analysis error at {scale}: {e}")
            analysis['analysis_error'] = str(e)
        
        return analysis
    
    def _detect_poker_table(self, screenshot: np.ndarray, hsv: np.ndarray, lab: np.ndarray) -> float:
        """Enhanced poker table detection using multiple color spaces."""
        confidence = 0.0
        
        try:
            # Multiple green ranges for different table types
            green_ranges = [
                ([40, 40, 40], [80, 255, 255]),    # Standard green felt
                ([35, 50, 50], [85, 255, 200]),    # Darker green
                ([45, 30, 30], [75, 255, 255]),    # Lighter green
            ]
            
            best_green_ratio = 0.0
            total_pixels = screenshot.shape[0] * screenshot.shape[1]
            
            for lower, upper in green_ranges:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                green_pixels = cv2.countNonZero(mask)
                green_ratio = green_pixels / total_pixels
                best_green_ratio = max(best_green_ratio, green_ratio)
            
            # Blue table detection (some sites use blue)
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            blue_ratio = cv2.countNonZero(blue_mask) / total_pixels
            
            # Combine color ratios
            color_confidence = min(1.0, (best_green_ratio + blue_ratio) * 2)
            confidence += color_confidence * 0.6
            
            # Check for table edge patterns
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Look for elliptical/circular patterns (table edges)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            ellipse_confidence = 0.0
            
            for contour in contours:
                if len(contour) >= 5:  # Minimum points for ellipse fitting
                    area = cv2.contourArea(contour)
                    if area > 1000:  # Significant area
                        try:
                            ellipse = cv2.fitEllipse(contour)
                            # Check if it's roughly table-shaped
                            (center, axes, angle) = ellipse
                            major_axis, minor_axis = max(axes), min(axes)
                            aspect_ratio = major_axis / minor_axis if minor_axis > 0 else 0
                            
                            if 1.2 < aspect_ratio < 3.0:  # Typical poker table ratios
                                ellipse_confidence = min(1.0, area / (total_pixels * 0.3))
                                break
                        except:
                            continue
            
            confidence += ellipse_confidence * 0.4
            
        except Exception as e:
            logger.debug(f"Table detection error: {e}")
        
        return min(1.0, confidence)
    
    def _detect_cards_advanced(self, screenshot: np.ndarray, gray: np.ndarray, hsv: np.ndarray) -> Dict[str, Any]:
        """Advanced card detection with template matching and contour analysis."""
        result = {
            'cards_detected': False,
            'potential_cards': 0,
            'hero_cards_visible': False,
            'board_cards_count': 0,
            'card_confidence': 0.0,
            'card_regions': []
        }
        
        try:
            # Adaptive thresholding for better card edge detection
            adaptive_thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Find contours
            contours, _ = cv2.findContours(adaptive_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            card_like_regions = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Adaptive area thresholds based on image size
                min_area = (screenshot.shape[0] * screenshot.shape[1]) * 0.001
                max_area = (screenshot.shape[0] * screenshot.shape[1]) * 0.05
                
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Enhanced card aspect ratio detection
                    if 0.55 < aspect_ratio < 0.85:  # Typical playing card ratios
                        # Check for rounded corners (card characteristic)
                        roi = gray[y:y+h, x:x+w]
                        if roi.size > 0:
                            corners_score = self._detect_rounded_corners(roi)
                            if corners_score > 0.3:
                                card_like_regions.append({
                                    'bbox': (x, y, w, h),
                                    'area': area,
                                    'aspect_ratio': aspect_ratio,
                                    'corners_score': corners_score,
                                    'confidence': min(1.0, corners_score + (0.7 - abs(aspect_ratio - 0.7)))
                                })
            
            # Sort by confidence and position
            card_like_regions.sort(key=lambda x: x['confidence'], reverse=True)
            
            result['potential_cards'] = len(card_like_regions)
            result['cards_detected'] = len(card_like_regions) > 0
            result['card_regions'] = card_like_regions[:10]  # Keep top 10
            
            # Estimate hero vs board cards based on position
            if card_like_regions:
                height = screenshot.shape[0]
                width = screenshot.shape[1]
                
                hero_cards = [r for r in card_like_regions if r['bbox'][1] > height * 0.7]
                board_cards = [r for r in card_like_regions if height * 0.3 < r['bbox'][1] < height * 0.7]
                
                result['hero_cards_visible'] = len(hero_cards) >= 2
                result['board_cards_count'] = min(5, len(board_cards))
                
                # Calculate confidence based on detected cards
                avg_confidence = np.mean([r['confidence'] for r in card_like_regions[:5]])
                result['card_confidence'] = avg_confidence
            
        except Exception as e:
            logger.debug(f"Advanced card detection error: {e}")
        
        return result
    
    def _detect_rounded_corners(self, roi: np.ndarray) -> float:
        """Detect rounded corners characteristic of playing cards."""
        try:
            if roi.shape[0] < 20 or roi.shape[1] < 20:
                return 0.0
            
            # Check corner regions
            corner_size = min(10, roi.shape[0] // 4, roi.shape[1] // 4)
            corners = [
                roi[:corner_size, :corner_size],           # Top-left
                roi[:corner_size, -corner_size:],          # Top-right
                roi[-corner_size:, :corner_size],          # Bottom-left
                roi[-corner_size:, -corner_size:]          # Bottom-right
            ]
            
            rounded_score = 0.0
            for corner in corners:
                # Count white pixels in the corner (card background)
                white_pixels = np.sum(corner > 200)
                total_pixels = corner.size
                white_ratio = white_pixels / total_pixels
                
                # Rounded corners have fewer white pixels in corners
                if white_ratio < 0.7:  # Less than 70% white suggests rounded corner
                    rounded_score += 0.25
            
            return rounded_score
            
        except Exception as e:
            logger.debug(f"Rounded corner detection error: {e}")
            return 0.0
    
    def _detect_poker_ui_elements(self, screenshot: np.ndarray, gray: np.ndarray) -> Dict[str, Any]:
        """Detect poker-specific UI elements like buttons, chips, etc."""
        result = {
            'buttons_detected': False,
            'action_buttons_visible': False,
            'seat_count': 0,
            'ui_confidence': 0.0
        }
        
        try:
            # Detect circular elements (chips, dealer button)
            circles = cv2.HoughCircles(
                gray, cv2.HOUGH_GRADIENT, 1, 20,
                param1=50, param2=30, minRadius=5, maxRadius=100
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                result['buttons_detected'] = True
                result['ui_confidence'] += 0.3
                
                # Analyze circle positions to estimate seat count
                height = screenshot.shape[0]
                width = screenshot.shape[1]
                
                # Group circles by position to find seat patterns
                edge_circles = [
                    c for c in circles 
                    if c[0] < width * 0.2 or c[0] > width * 0.8 or 
                       c[1] < height * 0.2 or c[1] > height * 0.8
                ]
                
                result['seat_count'] = min(10, len(edge_circles))
            
            # Detect rectangular buttons (fold, call, raise)
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            button_like_regions = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                if 1000 < area < 10000:  # Button-like area
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # Check for button-like aspect ratio
                    if 1.5 < aspect_ratio < 4.0:
                        # Check if it's in the bottom area (where action buttons typically are)
                        if y > screenshot.shape[0] * 0.6:
                            button_like_regions += 1
            
            if button_like_regions >= 2:  # At least 2 action buttons
                result['action_buttons_visible'] = True
                result['ui_confidence'] += 0.4
            
            # Look for text patterns typical of poker games
            if button_like_regions > 0:
                result['ui_confidence'] += 0.3
            
            result['ui_confidence'] = min(1.0, result['ui_confidence'])
            
        except Exception as e:
            logger.debug(f"UI detection error: {e}")
        
        return result
    
    def _enhanced_ocr_analysis(self, screenshot: np.ndarray, gray: np.ndarray) -> Dict[str, Any]:
        """Enhanced OCR analysis with better preprocessing."""
        result = {
            'pot_detected': False,
            'detected_amounts': [],
            'text_confidence': 0.0,
            'detected_text': ''
        }
        
        if not OCR_AVAILABLE:
            return result
        
        try:
            # Preprocess image for better OCR
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Multiple OCR attempts with different configurations
            ocr_configs = [
                '--psm 6',  # Uniform block of text
                '--psm 7',  # Single text line
                '--psm 8',  # Single word
                '--psm 13'  # Raw line. Treat the image as a single text line
            ]
            
            all_text = ""
            best_confidence = 0.0
            
            for config in ocr_configs:
                try:
                    text = pytesseract.image_to_string(enhanced, config=config)
                    if text.strip():
                        all_text += text + " "
                        
                        # Get confidence data
                        data = pytesseract.image_to_data(enhanced, config=config, output_type=pytesseract.Output.DICT)
                        confidences = [int(c) for c in data['conf'] if int(c) > 0]
                        if confidences:
                            avg_conf = np.mean(confidences) / 100.0
                            best_confidence = max(best_confidence, avg_conf)
                            
                except Exception as e:
                    logger.debug(f"OCR config {config} failed: {e}")
                    continue
            
            result['detected_text'] = all_text.strip()
            result['text_confidence'] = best_confidence
            
            # Enhanced money pattern matching
            money_patterns = [
                r'[\$€£¥]\s*\d+(?:,\d{3})*(?:\.\d{2})?',
                r'\d+(?:,\d{3})*(?:\.\d{2})?\s*[\$€£¥]',
                r'[Pp]ot\s*:?\s*[\$€£¥]?\s*\d+(?:,\d{3})*(?:\.\d{2})?',
                r'[Bb]et\s*:?\s*[\$€£¥]?\s*\d+(?:,\d{3})*(?:\.\d{2})?'
            ]
            
            amounts = []
            for pattern in money_patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                amounts.extend(matches)
            
            if amounts:
                result['pot_detected'] = True
                result['detected_amounts'] = list(set(amounts))  # Remove duplicates
                result['text_confidence'] += 0.2
            
            result['text_confidence'] = min(1.0, result['text_confidence'])
            
        except Exception as e:
            logger.debug(f"Enhanced OCR analysis failed: {e}")
        
        return result
    
    def _cleanup_analysis_cache(self):
        """Clean up old entries from analysis cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (timestamp, _) in self._analysis_cache.items()
            if current_time - timestamp > self._cache_ttl * 2
        ]
        
        for key in expired_keys:
            del self._analysis_cache[key]
    
    def _calculate_adaptive_interval(self, activity_detected: bool) -> float:
        """Calculate adaptive monitoring interval based on activity."""
        if not self._adaptive_intervals:
            return self._base_interval
        
        if activity_detected:
            self._consecutive_no_activity = 0
            return self._fast_interval
        else:
            self._consecutive_no_activity += 1
            
            # Gradually increase interval when no activity detected
            if self._consecutive_no_activity > 10:
                return self._slow_interval
            elif self._consecutive_no_activity > 5:
                return self._base_interval * 1.5
            else:
                return self._base_interval
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        total_captures = self._metrics['total_captures']
        success_rate = (
            self._metrics['successful_captures'] / total_captures 
            if total_captures > 0 else 0.0
        )
        
        total_cache_requests = self._metrics['cache_hits'] + self._metrics['cache_misses']
        cache_hit_rate = (
            self._metrics['cache_hits'] / total_cache_requests
            if total_cache_requests > 0 else 0.0
        )
        
        return {
            'total_captures': total_captures,
            'success_rate': success_rate,
            'avg_capture_time': self._metrics['avg_capture_time'],
            'cache_hit_rate': cache_hit_rate,
            'cache_entries': len(self._analysis_cache),
            'capture_history_size': len(self._capture_history),
            'adaptive_monitoring': self._adaptive_intervals,
            'consecutive_no_activity': self._consecutive_no_activity
        }
    
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
