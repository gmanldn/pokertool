"""
Screen scraping integration module.
Integrates the poker screen scraper with the main pokertool application.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable
from threading import Thread, Event
import time
from pathlib import Path

# Import the screen scraper
try:
    import sys
    import os
    # Add root directory to path to import poker_screen_scraper
    root_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_dir))
    
    from poker_screen_scraper import (
        PokerScreenScraper, 
        ScreenScraperBridge, 
        PokerSite, 
        TableState
    )
except ImportError as e:
    logging.warning(f"Could not import screen scraper: {e}")
    PokerScreenScraper = None
    ScreenScraperBridge = None
    PokerSite = None
    TableState = None

from .storage import get_secure_db
from .error_handling import retry_on_failure

logger = logging.getLogger(__name__)

class ScraperManager:
    """Manages the poker screen scraper integration."""
    
    def __init__(self):
        self.scraper = None
        self.bridge = None
        self.running = False
        self.callbacks = []
        self.last_state = None
        
    def initialize(self, site: str = 'GENERIC') -> bool:
        """Initialize the screen scraper."""
        if not PokerScreenScraper:
            logger.error("Screen scraper not available - missing dependencies")
            return False
            
        try:
            # Convert string to enum
            poker_site = PokerSite.GENERIC
            if site.upper() in [s.name for s in PokerSite]:
                poker_site = PokerSite[site.upper()]
                
            self.scraper = PokerScreenScraper(poker_site)
            self.bridge = ScreenScraperBridge(self.scraper)
            
            # Register our callback
            self.bridge.register_callback(self._on_table_update)
            
            logger.info(f"Screen scraper initialized for {poker_site.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize screen scraper: {e}")
            return False
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for table state updates."""
        self.callbacks.append(callback)
    
    def _on_table_update(self, game_state: Dict[str, Any]):
        """Handle table state updates."""
        self.last_state = game_state
        
        # Save to database
        self._save_table_state(game_state)
        
        # Notify all callbacks
        for callback in self.callbacks:
            try:
                callback(game_state)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _save_table_state(self, game_state: Dict[str, Any]):
        """Save table state to database."""
        try:
            db = get_secure_db()
            
            # Create a simplified representation for storage
            hand_str = ' '.join(str(card) for card in game_state.get('hole_cards', []))
            board_str = ' '.join(str(card) for card in game_state.get('board_cards', []))
            
            if hand_str and board_str:
                # Only save if we have both hole and board cards
                result = f"Pot: ${game_state.get('pot', 0):.2f}, Stage: {game_state.get('stage', 'unknown')}"
                
                db.save_hand_analysis(
                    hand=hand_str,
                    board=board_str if board_str.strip() else None,
                    result=result,
                    session_id=None,  # Could be enhanced to track sessions
                    metadata={
                        'source': 'screen_scraper',
                        'position': str(game_state.get('position', 'unknown')),
                        'num_players': game_state.get('num_players', 0),
                        'dealer_seat': game_state.get('dealer_seat'),
                        'hero_seat': game_state.get('hero_seat')
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to save table state: {e}")
            raise
    
    def start_continuous_capture(self, interval: float = 1.0) -> bool:
        """Start continuous table capture."""
        if not self.scraper:
            logger.error("Scraper not initialized")
            return False
            
        if self.running:
            logger.warning("Capture already running")
            return True
            
        try:
            # Calibrate first
            if not self.scraper.calibrate():
                logger.warning("Scraper calibration failed, starting anyway...")
            
            self.scraper.start_continuous_capture(interval)
            self.running = True
            
            # Start processing updates
            self._start_update_processor()
            
            logger.info("Continuous capture started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start continuous capture: {e}")
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
                    logger.debug(f"Update processing error: {e}")
        
        thread = Thread(target=process_updates, daemon=True)
        thread.start()
    
    def stop_continuous_capture(self):
        """Stop continuous capture."""
        if self.scraper and self.running:
            self.scraper.stop_continuous_capture()
            self.running = False
            logger.info("Continuous capture stopped")
    
    def capture_single_state(self) -> Optional[Dict[str, Any]]:
        """Capture a single table state."""
        if not self.scraper:
            logger.error("Scraper not initialized")
            return None
            
        try:
            table_state = self.scraper.analyze_table()
            return self.bridge.convert_to_game_state(table_state)
            
        except Exception as e:
            logger.error(f"Single capture failed: {e}")
            return None
    
    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get the latest captured table state."""
        return self.last_state
    
    def save_debug_image(self, filename: str = 'debug_table.png') -> bool:
        """Save a debug image of the current table."""
        if not self.scraper:
            return False
            
        try:
            img = self.scraper.capture_table()
            self.scraper.save_debug_image(img, filename)
            return True
        except Exception as e:
            logger.error(f"Failed to save debug image: {e}")
            return False

# Global scraper manager instance
_scraper_manager = ScraperManager()

def run_screen_scraper(site: str = 'GENERIC', continuous: bool = False, interval: float = 1.0) -> Dict[str, Any]:
    """
    Run the screen scraper to capture poker table state.
    
    Args:
        site: Poker site to scrape ('GENERIC', 'POKERSTARS', etc.)
        continuous: Whether to run continuously
        interval: Capture interval in seconds (for continuous mode)
    
    Returns:
        Dict containing scraper status and results
    """
    global _scraper_manager
    
    if not _scraper_manager.scraper:
        if not _scraper_manager.initialize(site):
            return {
                'status': 'error',
                'message': 'Failed to initialize screen scraper',
                'dependencies_missing': PokerScreenScraper is None
            }
    
    if continuous:
        success = _scraper_manager.start_continuous_capture(interval)
        return {
            'status': 'success' if success else 'error',
            'message': 'Continuous capture started' if success else 'Failed to start capture',
            'continuous': True
        }
    else:
        state = _scraper_manager.capture_single_state()
        return {
            'status': 'success' if state else 'error',
            'message': 'Single capture completed' if state else 'Capture failed',
            'state': state,
            'continuous': False
        }

def stop_screen_scraper() -> Dict[str, Any]:
    """Stop the continuous screen scraper."""
    global _scraper_manager
    
    _scraper_manager.stop_continuous_capture()
    return {
        'status': 'success',
        'message': 'Screen scraper stopped'
    }

def get_scraper_status() -> Dict[str, Any]:
    """Get current scraper status."""
    global _scraper_manager
    
    return {
        'initialized': _scraper_manager.scraper is not None,
        'running': _scraper_manager.running,
        'available': PokerScreenScraper is not None,
        'last_state': _scraper_manager.last_state
    }

def register_table_callback(callback: Callable[[Dict[str, Any]], None]) -> bool:
    """Register a callback for table state updates."""
    global _scraper_manager
    
    try:
        _scraper_manager.register_callback(callback)
        return True
    except Exception as e:
        logger.error(f"Failed to register callback: {e}")
        return False

def save_debug_capture(filename: str = 'debug_table.png') -> bool:
    """Save a debug image of the current table state."""
    global _scraper_manager
    
    return _scraper_manager.save_debug_image(filename)

# Async support for future API integration
async def run_screen_scraper_async(site: str = 'GENERIC') -> Dict[str, Any]:
    """Async version of screen scraper for API integration."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_screen_scraper, site, False, 1.0)
