#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Screen Scraping Module
=================================

Advanced screen scraping and OCR capabilities for monitoring online
poker tables and extracting game state information in real-time.

Module: pokertool.scrape
Version: 20.0.0
Last Modified: 2025-09-29
Author: PokerTool Development Team
License: MIT

Dependencies:
    - requests >= 2.32.0: HTTP client
    - beautifulsoup4 >= 4.12.0: HTML parsing
    - Pillow: Image processing
    - pytesseract: OCR capabilities (optional)

Scraping Features:
    - Multi-platform screen capture
    - OCR text recognition
    - Table layout detection
    - Real-time tracking
    - Anti-detection measures
    - Error recovery
    - Multiple site support

Supported Sites:
    - Generic table layout
    - Custom profiles per site
    - Configurable detection

IMPORTANT:
    This module is for educational purposes only.
    Users must comply with all applicable terms of service
    and local regulations when using screen scraping features.

Change Log:
    - v28.0.0 (2025-09-29): Enhanced documentation, improved OCR
    - v19.0.0 (2025-09-18): Multi-site support
    - v18.0.0 (2025-09-15): Initial scraping implementation
"""

__version__ = '20.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Beta'

import logging
import time
from concurrent.futures import Future
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, Optional, Sequence

import numpy as np

# Import the screen scraper
try:
    import sys
    import os
    # Add root directory to path to import poker_screen_scraper
    root_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_dir))

    from pokertool.modules.poker_screen_scraper import (
        PokerScreenScraper, 
        ScreenScraperBridge, 
        PokerSite, 
        TableState
    )
    SCRAPER_AVAILABLE = True
except ImportError as e:
    logging.warning(f'Could not import screen scraper: {e}')
    PokerScreenScraper = None
    ScreenScraperBridge = None
    PokerSite = None
    TableState = None
    SCRAPER_AVAILABLE = False

# Import desktop-independent scraper
try:
    from .desktop_independent_scraper import (
        DesktopIndependentScraper,
        create_desktop_scraper,
        WindowInfo,
        PokerDetectionMode
    )
    DESKTOP_SCRAPER_AVAILABLE = True
except ImportError as e:
    logging.warning(f'Could not import desktop-independent scraper: {e}')
    DesktopIndependentScraper = None
    create_desktop_scraper = None
    WindowInfo = None
    PokerDetectionMode = None
    DESKTOP_SCRAPER_AVAILABLE = False

# Import OCR system
try:
    from .ocr_recognition import (
        get_poker_ocr, 
        create_card_regions, 
        CardRegion,
        OCR_AVAILABLE
    )
except ImportError as e:
    logging.warning(f'Could not import OCR system: {e}')
    OCR_AVAILABLE = False

from .storage import get_secure_db
from .error_handling import retry_on_failure
from .core import analyse_hand, parse_card
from .threading import get_thread_pool, TaskPriority

logger = logging.getLogger(__name__)

# Recognition bookkeeping ----------------------------------------------------


@dataclass
class RecognitionStats:
    """Lightweight statistics tracker for OCR recognition quality."""

    total_captures: int = 0
    successful_recognitions: int = 0
    failed_recognitions: int = 0
    avg_confidence: float = 0.0

    def record_capture(self) -> None:
        self.total_captures += 1

    def record_success(self, confidence: float) -> None:
        self.successful_recognitions += 1
        if self.successful_recognitions == 1:
            self.avg_confidence = confidence
        else:
            delta = confidence - self.avg_confidence
            self.avg_confidence += delta / self.successful_recognitions

    def record_failure(self) -> None:
        self.failed_recognitions += 1

    def snapshot(self, ocr_enabled: bool) -> Dict[str, Any]:
        success_rate = (
            self.successful_recognitions / self.total_captures
            if self.total_captures
            else 0.0
        )
        return {
            'total_captures': self.total_captures,
            'successful_recognitions': self.successful_recognitions,
            'failed_recognitions': self.failed_recognitions,
            'avg_confidence': self.avg_confidence,
            'success_rate': success_rate,
            'ocr_enabled': ocr_enabled,
        }


class _FallbackScraperBridge:
    """Minimal bridge used when the native bridge is unavailable (e.g. tests)."""

    def __init__(self, _scraper: Any):
        self._callbacks: list[Callable[[Dict[str, Any]], None]] = []

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def process_update(self, state: Dict[str, Any]) -> None:
        payload = dict(state) if isinstance(state, dict) else {'raw_state': state}
        for callback in list(self._callbacks):
            try:
                callback(payload)
            except Exception as exc:
                logger.error('Fallback bridge callback error: %s', exc)

    @staticmethod
    def convert_to_game_state(table_state: Any) -> Dict[str, Any]:
        if isinstance(table_state, dict):
            return dict(table_state)
        if hasattr(table_state, 'to_dict'):
            try:
                return dict(table_state.to_dict())  # type: ignore[arg-type]
            except Exception:
                pass
        return {'raw_state': table_state}

# Import HUD overlay system
try:
    from .hud_overlay import update_hud_state, is_hud_running
    HUD_AVAILABLE = True
except ImportError as e:
    logger.warning(f'Could not import HUD overlay system: {e}')
    HUD_AVAILABLE = False

class EnhancedScraperManager:
    """
    Enhanced scraper manager with OCR integration and real-time analysis.
    Supports multiple poker sites with anti-detection mechanisms.
    """

    def __init__(self):
        self.scraper = None
        self.bridge = None
        self.ocr_engine = None
        self.running = False
        self.callbacks: list[Callable[[Dict[str, Any]], None]] = []
        self.last_state: Optional[Dict[str, Any]] = None
        self.card_regions: Sequence['CardRegion'] = ()
        self.thread_pool = get_thread_pool()
        self._recognition_stats = RecognitionStats()
        self._hole_regions: Sequence['CardRegion'] = ()
        self._board_regions: Sequence['CardRegion'] = ()
        self._primary_regions: Sequence['CardRegion'] = ()
        self._betting_regions: Sequence['CardRegion'] = ()
        self._pending_save: Optional[Future] = None
        self._current_site: Optional[str] = None
        self._ocr_requested = False
        self._last_signature: Optional[tuple] = None

    def initialize(self, site: str = 'GENERIC', enable_ocr: bool = True) -> bool:
        """Initialize the enhanced screen scraper with OCR support."""
        if not SCRAPER_AVAILABLE and PokerScreenScraper is None:
            logger.error('Screen scraper not available - missing dependencies')
            return False

        normalized_site = site.upper()
        requested_ocr = bool(enable_ocr and OCR_AVAILABLE)

        # If the scraper is already configured for this site, only refresh OCR when needed
        if self.scraper and self._current_site == normalized_site:
            if requested_ocr != self._ocr_requested:
                self._configure_ocr(enable_ocr)
                self._ocr_requested = requested_ocr
                self._recognition_stats = RecognitionStats()
                self._last_signature = None
            return True

        # Reinitialise underlying scraper state
        self.stop_continuous_capture()
        self.scraper = None
        self.bridge = None
        self._pending_save = None

        poker_site = None
        if PokerSite is not None:
            try:
                poker_site = PokerSite[normalized_site]
            except Exception:
                logger.debug('Unknown poker site "%s", falling back to generic profile', site)
                poker_site = PokerSite.GENERIC
        site_label = poker_site.value if poker_site is not None else normalized_site

        try:
            scraper_target = poker_site if poker_site is not None else normalized_site
            self.scraper = PokerScreenScraper(scraper_target)
            bridge_cls = ScreenScraperBridge or _FallbackScraperBridge
            self.bridge = bridge_cls(self.scraper)
            self.bridge.register_callback(self._on_table_update)

            self._configure_ocr(enable_ocr)
            self._recognition_stats = RecognitionStats()
            self._current_site = normalized_site
            self._ocr_requested = requested_ocr
            self._last_signature = None
            logger.info('Enhanced screen scraper initialized for %s', site_label)
            return True

        except Exception as exc:
            logger.error('Failed to initialize screen scraper: %s', exc)
            self.scraper = None
            self.bridge = None
            return False

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for table state updates."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def _configure_ocr(self, enable_ocr: bool) -> None:
        """Initialise or disable OCR resources and pre-compute region groups."""
        self.ocr_engine = None
        self.card_regions = ()
        self._hole_regions = ()
        self._board_regions = ()
        self._primary_regions = ()
        self._betting_regions = ()

        if not (enable_ocr and OCR_AVAILABLE):
            return

        try:
            engine = get_poker_ocr()
            regions = tuple(create_card_regions('standard'))

            hole_regions = []
            board_regions = []
            betting_regions = []
            for region in regions:
                if region.card_type == 'hole':
                    hole_regions.append(region)
                elif region.card_type == 'board':
                    board_regions.append(region)
                elif region.card_type in {'pot', 'hero_bet'}:
                    betting_regions.append(region)

            self.ocr_engine = engine
            self.card_regions = regions
            self._hole_regions = tuple(hole_regions)
            self._board_regions = tuple(board_regions)
            self._primary_regions = self._hole_regions + self._board_regions
            self._betting_regions = tuple(betting_regions)

            logger.info('OCR engine initialized with %d regions', len(regions))

        except Exception as exc:
            logger.warning('Failed to initialize OCR: %s', exc)
            self.ocr_engine = None

    def _strip_table_image(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Return a shallow copy of *state* without the raw table image payload."""
        if 'table_image' not in state:
            return dict(state)
        trimmed = dict(state)
        trimmed.pop('table_image', None)
        return trimmed

    def _should_process_update(self, state: Dict[str, Any]) -> bool:
        """Deduplicate updates by comparing key strategic fields."""
        signature = (
            tuple(state.get('hole_cards_ocr') or state.get('hole_cards') or ()),
            tuple(state.get('board_cards_ocr') or state.get('board_cards') or ()),
            state.get('stage'),
            state.get('pot'),
            state.get('to_call'),
        )
        if signature == self._last_signature:
            return False
        self._last_signature = signature
        return True

    def _schedule_state_persistence(self, state: Dict[str, Any]) -> None:
        """Persist the captured state asynchronously, avoiding duplicate tasks."""
        if not self.thread_pool:
            return

        if self._pending_save and not self._pending_save.done():
            return

        persistable = dict(state)
        future = self.thread_pool.submit_thread_task(self._save_table_state, persistable)
        self._pending_save = future

        def _clear(_future: Future) -> None:
            self._pending_save = None

        future.add_done_callback(_clear)

    @staticmethod
    def _prepare_image(raw_image: Any) -> Optional[np.ndarray]:
        """Normalise *raw_image* into an ``np.ndarray`` if possible."""
        if raw_image is None:
            return None

        if isinstance(raw_image, np.ndarray):
            return raw_image

        cv2 = None
        try:  # pragma: no cover - optional dependency
            import cv2  # type: ignore
        except Exception:
            pass

        if isinstance(raw_image, (str, Path)) and cv2 is not None:
            return cv2.imread(str(raw_image))

        if hasattr(raw_image, 'read') and cv2 is not None:
            try:
                data = raw_image.read()
            except Exception:
                data = None
            if data:
                buffer = np.frombuffer(data, dtype=np.uint8)
                return cv2.imdecode(buffer, 1)

        try:
            return np.asarray(raw_image)
        except Exception:
            return None

    def _on_table_update(self, game_state: Dict[str, Any]):
        """Handle table state updates with OCR enhancement."""
        # Enhance game state with OCR if available
        if self.ocr_engine and 'table_image' in game_state:
            enhanced_state = self._enhance_with_ocr(game_state)
            if enhanced_state:
                game_state.update(enhanced_state)

        normalized_state = self._strip_table_image(game_state)
        if not self._should_process_update(normalized_state):
            self.last_state = normalized_state
            return

        self.last_state = normalized_state

        # Update HUD overlay if running
        if HUD_AVAILABLE and is_hud_running():
            try:
                update_hud_state(normalized_state)
            except Exception as e:
                logger.error(f'HUD update error: {e}')

        # Persist asynchronously to avoid blocking the scraper thread
        self._schedule_state_persistence(normalized_state)

        # Notify all callbacks
        for callback in self.callbacks:
            try:
                callback(dict(normalized_state))
            except Exception as e:
                logger.error(f'Callback error: {e}')

    def _enhance_with_ocr(self, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance game state with OCR-recognized information."""
        try:
            if not self.ocr_engine:
                return None

            table_image = self._prepare_image(game_state.get('table_image'))
            if table_image is None:
                return None

            enhanced_data: Dict[str, Any] = {}

            for region in self._primary_regions:
                try:
                    result = self.ocr_engine.recognize_cards(table_image, region)
                except Exception as exc:
                    logger.debug('OCR recognition failed for %s: %s', region.card_type, exc)
                    self._recognition_stats.record_failure()
                    continue

                cards = getattr(result, 'cards', None)
                confidence = float(getattr(result, 'confidence', 0.0) or 0.0)

                if cards:
                    key_cards = f'{region.card_type}_cards_ocr'
                    key_conf = f'{region.card_type}_confidence'
                    existing = enhanced_data.get(key_cards)
                    if existing:
                        if isinstance(existing, list):
                            if isinstance(cards, list):
                                existing.extend(cards)
                            else:
                                existing.append(cards)
                            enhanced_data[key_cards] = existing
                        else:
                            merged = list(existing if isinstance(existing, list) else [existing])
                            if isinstance(cards, list):
                                merged.extend(cards)
                            else:
                                merged.append(cards)
                            enhanced_data[key_cards] = merged
                    else:
                        enhanced_data[key_cards] = cards

                    enhanced_data[key_conf] = confidence
                    self._recognition_stats.record_success(confidence)
                else:
                    self._recognition_stats.record_failure()

            if self._betting_regions and hasattr(self.ocr_engine, 'recognize_betting_amounts'):
                try:
                    amounts = self.ocr_engine.recognize_betting_amounts(table_image, list(self._betting_regions))
                except Exception as exc:
                    logger.debug('Betting amount recognition failed: %s', exc)
                else:
                    if amounts:
                        enhanced_data.update(amounts)

            self._recognition_stats.record_capture()
            enhanced_data['ocr_stats'] = self._recognition_stats.snapshot(self.ocr_engine is not None)
            enhanced_data['ocr_timestamp'] = time.time()

            return enhanced_data

        except Exception as e:
            logger.error('OCR enhancement failed: %s', e)
            return None

    @retry_on_failure(max_retries=3, delay=1.0)
    def _save_table_state(self, game_state: Dict[str, Any]):
        """Save enhanced table state to database."""
        try:
            db = get_secure_db()

            # Use OCR cards if available, fallback to original detection
            hole_cards = game_state.get('hole_cards_ocr', game_state.get('hole_cards', []))
            board_cards = game_state.get('board_cards_ocr', game_state.get('board_cards', []))

            hand_str = ' '.join(str(card) for card in hole_cards)
            board_str = ' '.join(str(card) for card in board_cards)

            if hand_str:  # Save even without board cards
                # Perform hand analysis if we have hole cards
                analysis_result = "No analysis"
                if len(hole_cards) >= 2:
                    try:
                        parsed_cards = [parse_card(str(card)) for card in hole_cards[:2]]
                        board_parsed = [parse_card(str(card)) for card in board_cards[:5]] if board_cards else None
                        
                        analysis = analyse_hand(
                            parsed_cards,
                            board_parsed,
                            position=game_state.get('position'),
                            pot=game_state.get('pot', 0),
                            to_call=game_state.get('to_call', 0)
                        )
                        
                        analysis_result = f"Strength: {analysis.strength:.2f}, Advice: {analysis.advice}"
                        
                    except Exception as e:
                        logger.debug(f'Hand analysis failed: {e}')
                        analysis_result = f"Analysis error: {str(e)}"

                # Enhanced metadata with OCR information
                metadata = {
                    'source': 'enhanced_screen_scraper',
                    'position': str(game_state.get('position', 'unknown')),
                    'num_players': game_state.get('num_players', 0),
                    'dealer_seat': game_state.get('dealer_seat'),
                    'hero_seat': game_state.get('hero_seat'),
                    'pot_size': game_state.get('pot', 0),
                    'stage': game_state.get('stage', 'unknown'),
                    'ocr_enabled': self.ocr_engine is not None,
                    'hole_confidence': game_state.get('hole_confidence', 0.0),
                    'board_confidence': game_state.get('board_confidence', 0.0),
                    'recognition_method': game_state.get('recognition_method', 'legacy'),
                    'ocr_stats': game_state.get('ocr_stats', {})
                }

                db.save_hand_analysis(
                    hand=hand_str,
                    board=board_str if board_str.strip() else None,
                    result=analysis_result,
                    session_id=game_state.get('session_id'),
                    metadata=metadata
                )

        except Exception as e:
            logger.error(f'Failed to save enhanced table state: {e}')
            raise

    def start_continuous_capture(self, interval: float = 1.0) -> bool:
        """Start continuous table capture with OCR enhancement."""
        if not self.scraper:
            logger.error('Scraper not initialized')
            return False

        if self.running:
            logger.warning('Capture already running')
            return True

        try:
            # Calibrate first
            if not self.scraper.calibrate():
                logger.warning('Scraper calibration failed, starting anyway...')

            self.scraper.start_continuous_capture(interval)
            self.running = True

            # Start processing updates
            self._start_update_processor()

            logger.info(f'Continuous capture started (OCR: {self.ocr_engine is not None})')
            return True

        except Exception as e:
            logger.error(f'Failed to start continuous capture: {e}')
            return False

    def _start_update_processor(self):
        """Start background thread to process scraper updates."""
        def process_updates():
            while self.running:
                try:
                    state = self.scraper.get_state_updates(timeout=0.5)
                    if state:
                        self.bridge.process_update(state)
                except Exception as e:
                    logger.debug(f'Update processing error: {e}')

        thread = Thread(target=process_updates, daemon=True)
        thread.start()

    def stop_continuous_capture(self):
        """Stop continuous capture."""
        if self.scraper and self.running:
            self.scraper.stop_continuous_capture()
            self.running = False
            logger.info('Continuous capture stopped')

    def capture_single_state(self) -> Optional[Dict[str, Any]]:
        """Capture a single table state with OCR enhancement."""
        if not self.scraper:
            logger.error('Scraper not initialized')
            return None

        try:
            table_state = self.scraper.analyze_table()
            game_state = self.bridge.convert_to_game_state(table_state)
            
            # Enhance with OCR if available
            if self.ocr_engine and 'table_image' in game_state:
                enhanced_data = self._enhance_with_ocr(game_state)
                if enhanced_data:
                    game_state.update(enhanced_data)

            normalized_state = self._strip_table_image(game_state)
            self.last_state = normalized_state
            self._schedule_state_persistence(normalized_state)
            return normalized_state

        except Exception as e:
            logger.error(f'Single capture failed: {e}')
            return None

    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get the latest captured table state."""
        return self.last_state

    def get_recognition_stats(self) -> Dict[str, Any]:
        """Get OCR recognition statistics."""
        return self._recognition_stats.snapshot(self.ocr_engine is not None)

    def save_debug_image(self, filename: str = 'debug_table.png') -> bool:
        """Save a debug image of the current table."""
        if not self.scraper:
            return False

        try:
            img = self.scraper.capture_table()
            self.scraper.save_debug_image(img, filename)
            
            # Also save OCR regions if available
            if self.ocr_engine and img is not None:
                debug_filename = filename.replace('.png', '_ocr_regions.png')
                self._save_debug_regions(img, debug_filename)
            
            return True
        except Exception as e:
            logger.error(f'Failed to save debug image: {e}')
            return False

    def _save_debug_regions(self, image: np.ndarray, filename: str):
        """Save debug image with OCR regions marked."""
        try:
            import cv2
            debug_img = image.copy()
            
            # Draw rectangles around card regions
            colors = {
                'hole': (0, 255, 0),     # Green for hero cards
                'board': (255, 0, 0),    # Blue for board
                'opponent': (0, 0, 255), # Red for opponents
                'pot': (255, 255, 0),    # Cyan for pot
                'hero_bet': (255, 0, 255) # Magenta for hero bet
            }
            
            for region in self.card_regions:
                color = colors.get(region.card_type, (255, 255, 255))
                cv2.rectangle(debug_img, 
                            (region.x, region.y), 
                            (region.x + region.width, region.y + region.height),
                            color, 2)
                
                # Add label
                cv2.putText(debug_img, region.card_type, 
                          (region.x, region.y - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            cv2.imwrite(filename, debug_img)
            logger.info(f'OCR debug image saved: {filename}')
            
        except Exception as e:
            logger.error(f'Failed to save OCR debug image: {e}')

# Global enhanced scraper manager instance
_scraper_manager = EnhancedScraperManager()

# Backwards compatibility -----------------------------------------------------

# Earlier versions exposed a ``ScraperManager`` symbol; keep an alias so
# existing integrations and historical tests continue to import it without
# modification.
ScraperManager = EnhancedScraperManager

def run_screen_scraper(site: str = 'GENERIC', continuous: bool = False, interval: float = 1.0, enable_ocr: bool = True) -> Dict[str, Any]:
    """
    Run the enhanced screen scraper with OCR support.

    Args:
        site: Poker site to scrape ('GENERIC', 'POKERSTARS', etc.)
        continuous: Whether to run continuously
        interval: Capture interval in seconds (for continuous mode)
        enable_ocr: Whether to enable OCR card recognition

    Returns:
        Dict containing scraper status and results
    """
    global _scraper_manager

    if not _scraper_manager.initialize(site, enable_ocr):
        return {
            'status': 'error',
            'message': 'Failed to initialize enhanced screen scraper',
            'dependencies_missing': {
                'scraper': not SCRAPER_AVAILABLE,
                'ocr': not OCR_AVAILABLE
            }
        }

    if continuous:
        success = _scraper_manager.start_continuous_capture(interval)
        return {
            'status': 'success' if success else 'error',
            'message': 'Continuous capture started' if success else 'Failed to start capture',
            'continuous': True,
            'ocr_enabled': _scraper_manager.ocr_engine is not None,
            'recognition_stats': _scraper_manager.get_recognition_stats()
        }
    else:
        state = _scraper_manager.capture_single_state()
        return {
            'status': 'success' if state else 'error',
            'message': 'Single capture completed' if state else 'Capture failed',
            'state': state,
            'continuous': False,
            'ocr_enabled': _scraper_manager.ocr_engine is not None
        }

def stop_screen_scraper() -> Dict[str, Any]:
    """Stop the continuous screen scraper."""
    global _scraper_manager

    _scraper_manager.stop_continuous_capture()
    return {
        'status': 'success',
        'message': 'Enhanced screen scraper stopped',
        'final_stats': _scraper_manager.get_recognition_stats()
    }

def get_scraper_status() -> Dict[str, Any]:
    """Get current scraper status with OCR information."""
    global _scraper_manager

    return {
        'initialized': _scraper_manager.scraper is not None,
        'running': _scraper_manager.running,
        'available': SCRAPER_AVAILABLE,
        'desktop_scraper_available': DESKTOP_SCRAPER_AVAILABLE,
        'ocr_available': OCR_AVAILABLE,
        'ocr_enabled': _scraper_manager.ocr_engine is not None,
        'last_state': _scraper_manager.last_state,
        'recognition_stats': _scraper_manager.get_recognition_stats()
    }

# Desktop-Independent Scraper Functions ----------------------------------

_desktop_scraper = None

def run_desktop_independent_scraper(detection_mode: str = 'COMBINED', continuous: bool = False, interval: float = 2.0) -> Dict[str, Any]:
    """
    Run the desktop-independent screen scraper that works across all desktops/workspaces.
    
    Args:
        detection_mode: Poker detection mode ('WINDOW_TITLE', 'PROCESS_NAME', 'COMBINED', 'FUZZY_MATCH')
        continuous: Whether to run continuously
        interval: Capture interval in seconds (for continuous mode)
        
    Returns:
        Dict containing scraper status and results
    """
    global _desktop_scraper
    
    if not DESKTOP_SCRAPER_AVAILABLE:
        return {
            'status': 'error',
            'message': 'Desktop-independent scraper not available',
            'dependencies_missing': {
                'desktop_scraper': True,
                'mss': False,  # Will be checked by the scraper itself
                'cv2': False,
                'platform_apis': False
            }
        }
    
    try:
        # Initialize desktop scraper
        if not _desktop_scraper:
            _desktop_scraper = create_desktop_scraper()
        
        # Convert string to enum
        mode_map = {
            'WINDOW_TITLE': PokerDetectionMode.WINDOW_TITLE,
            'PROCESS_NAME': PokerDetectionMode.PROCESS_NAME,
            'COMBINED': PokerDetectionMode.COMBINED,
            'FUZZY_MATCH': PokerDetectionMode.FUZZY_MATCH
        }
        
        mode = mode_map.get(detection_mode.upper(), PokerDetectionMode.COMBINED)
        
        # Scan for poker windows
        windows = _desktop_scraper.scan_for_poker_windows(mode)
        
        if not windows:
            return {
                'status': 'warning',
                'message': 'No poker windows found across all desktops',
                'windows_found': 0,
                'capabilities': _desktop_scraper.get_platform_capabilities(),
                'detection_mode': detection_mode
            }
        
        if continuous:
            # Register callback to forward updates to the main scraper manager
            def forward_update(capture_result: Dict[str, Any]):
                if capture_result.get('success') and capture_result.get('likely_poker_table'):
                    # Convert desktop scraper result to standard format
                    window_info = capture_result.get('window_info')
                    game_state = {
                        'source': 'desktop_independent_scraper',
                        'window_title': window_info.title if window_info else 'Unknown',
                        'platform': capture_result.get('platform'),
                        'timestamp': capture_result.get('timestamp'),
                        'table_active': capture_result.get('table_active', False),
                        'cards_detected': capture_result.get('cards_detected', False),
                        'pot_detected': capture_result.get('pot_detected', False),
                        'buttons_detected': capture_result.get('buttons_detected', False),
                        'activity_score': capture_result.get('activity_score', 0),
                        'detected_amounts': capture_result.get('detected_amounts', []),
                        'potential_cards': capture_result.get('potential_cards', 0),
                        'button_count': capture_result.get('button_count', 0),
                        'green_ratio': capture_result.get('green_ratio', 0.0),
                        'table_image': capture_result.get('screenshot')  # Include screenshot for OCR
                    }
                    
                    # Forward to main scraper callbacks
                    for callback in _scraper_manager.callbacks:
                        try:
                            callback(game_state)
                        except Exception as e:
                            logger.error(f'Desktop scraper callback error: {e}')
            
            _desktop_scraper.register_callback(forward_update)
            
            success = _desktop_scraper.start_continuous_monitoring(interval)
            
            return {
                'status': 'success' if success else 'error',
                'message': f'Continuous monitoring started for {len(windows)} windows' if success else 'Failed to start monitoring',
                'continuous': True,
                'windows_found': len(windows),
                'windows': [{'title': w.title, 'bounds': w.bounds, 'visible': w.is_visible} for w in windows],
                'detection_mode': detection_mode,
                'platform': _desktop_scraper.platform,
                'capabilities': _desktop_scraper.get_platform_capabilities()
            }
        else:
            # Single capture of all detected windows
            results = []
            for window in windows[:5]:  # Limit to first 5 windows
                capture_result = _desktop_scraper.capture_window(window, include_screenshot=False)
                if capture_result:
                    results.append({
                        'window_title': window.title,
                        'success': capture_result.get('success', False),
                        'likely_poker_table': capture_result.get('likely_poker_table', False),
                        'activity_score': capture_result.get('activity_score', 0),
                        'table_active': capture_result.get('table_active', False),
                        'cards_detected': capture_result.get('cards_detected', False),
                        'pot_detected': capture_result.get('pot_detected', False)
                    })
            
            return {
                'status': 'success',
                'message': f'Single capture completed for {len(windows)} windows',
                'continuous': False,
                'windows_found': len(windows),
                'capture_results': results,
                'detection_mode': detection_mode,
                'platform': _desktop_scraper.platform,
                'capabilities': _desktop_scraper.get_platform_capabilities()
            }
            
    except Exception as e:
        logger.error(f'Desktop-independent scraper error: {e}')
        return {
            'status': 'error',
            'message': f'Desktop scraper failed: {str(e)}',
            'error_details': str(e)
        }

def stop_desktop_scraper() -> Dict[str, Any]:
    """Stop the desktop-independent scraper."""
    global _desktop_scraper
    
    if _desktop_scraper:
        _desktop_scraper.stop_monitoring()
        return {
            'status': 'success',
            'message': 'Desktop-independent scraper stopped'
        }
    else:
        return {
            'status': 'warning',
            'message': 'Desktop scraper was not running'
        }

def get_desktop_scraper_status() -> Dict[str, Any]:
    """Get desktop scraper status and capabilities."""
    if not DESKTOP_SCRAPER_AVAILABLE:
        return {
            'available': False,
            'message': 'Desktop-independent scraper not available'
        }
    
    if not _desktop_scraper:
        capabilities = {}
        try:
            temp_scraper = create_desktop_scraper()
            capabilities = temp_scraper.get_platform_capabilities()
        except Exception as e:
            capabilities = {'error': str(e)}
        
        return {
            'available': True,
            'initialized': False,
            'running': False,
            'capabilities': capabilities
        }
    
    return {
        'available': True,
        'initialized': True,
        'running': _desktop_scraper.running,
        'platform': _desktop_scraper.platform,
        'detected_windows_count': len(_desktop_scraper.detected_windows),
        'detected_windows': [
            {
                'title': w.title,
                'bounds': w.bounds,
                'visible': w.is_visible,
                'minimized': w.is_minimized,
                'area': w.area
            } for w in _desktop_scraper.detected_windows
        ],
        'capabilities': _desktop_scraper.get_platform_capabilities()
    }

def save_debug_screenshots_all_desktops(output_dir: str = "debug_screenshots") -> Dict[str, Any]:
    """
    Save debug screenshots of all poker windows found across all desktops.
    
    Args:
        output_dir: Directory to save screenshots
        
    Returns:
        Dict with results
    """
    global _desktop_scraper
    
    if not DESKTOP_SCRAPER_AVAILABLE:
        return {
            'status': 'error',
            'message': 'Desktop-independent scraper not available'
        }
    
    try:
        if not _desktop_scraper:
            _desktop_scraper = create_desktop_scraper()
        
        # Scan for windows if not already done
        if not _desktop_scraper.detected_windows:
            _desktop_scraper.scan_for_poker_windows()
        
        saved_files = _desktop_scraper.save_debug_screenshots(output_dir)
        
        return {
            'status': 'success',
            'message': f'Saved {len(saved_files)} debug screenshots',
            'saved_files': saved_files,
            'output_directory': output_dir,
            'windows_captured': len(saved_files)
        }
        
    except Exception as e:
        logger.error(f'Debug screenshot error: {e}')
        return {
            'status': 'error',
            'message': f'Failed to save debug screenshots: {str(e)}',
            'error_details': str(e)
        }

def quick_poker_window_scan() -> Dict[str, Any]:
    """
    Quick scan for poker windows across all desktops without starting monitoring.
    
    Returns:
        Dict with scan results
    """
    if not DESKTOP_SCRAPER_AVAILABLE:
        return {
            'status': 'error',
            'message': 'Desktop-independent scraper not available',
            'windows': []
        }
    
    try:
        scraper = create_desktop_scraper()
        windows = scraper.scan_for_poker_windows()
        
        return {
            'status': 'success',
            'message': f'Found {len(windows)} poker windows',
            'windows_found': len(windows),
            'platform': scraper.platform,
            'capabilities': scraper.get_platform_capabilities(),
            'windows': [
                {
                    'title': w.title,
                    'bounds': w.bounds,
                    'area': w.area,
                    'visible': w.is_visible,
                    'minimized': w.is_minimized,
                    'desktop_id': w.desktop_id,
                    'workspace_name': w.workspace_name
                } for w in windows
            ]
        }
        
    except Exception as e:
        logger.error(f'Quick scan error: {e}')
        return {
            'status': 'error',
            'message': f'Scan failed: {str(e)}',
            'windows': [],
            'error_details': str(e)
        }

if __name__ == '__main__':
    # Test enhanced scraper functionality
    print("Enhanced Screen Scraper with OCR Integration")
    print(f"Scraper available: {SCRAPER_AVAILABLE}")
    print(f"OCR available: {OCR_AVAILABLE}")
    
    if SCRAPER_AVAILABLE:
        result = run_screen_scraper('CHROME', False, 1.0, True)
        print(f"Test result: {result}")
    else:
        print("Screen scraper dependencies not available")
