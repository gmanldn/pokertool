# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/pokertool/scrape.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Screen scraping integration module.
Integrates the poker screen scraper with the main pokertool application.
Now includes OCR-powered card recognition and real-time HUD overlay support.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable, Tuple
from threading import Thread, Event
import time
from pathlib import Path
import numpy as np

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
    SCRAPER_AVAILABLE = True
except ImportError as e:
    logging.warning(f'Could not import screen scraper: {e}')
    PokerScreenScraper = None
    ScreenScraperBridge = None
    PokerSite = None
    TableState = None
    SCRAPER_AVAILABLE = False

# Import OCR system
try:
    from .ocr_recognition import (
        get_poker_ocr, 
        create_card_regions, 
        CardRegion, 
        RecognitionResult,
        RecognitionMethod,
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
        self.callbacks = []
        self.last_state = None
        self.card_regions = []
        self.thread_pool = get_thread_pool()
        self.recognition_stats = {
            'total_captures': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'avg_confidence': 0.0
        }

    def initialize(self, site: str = 'GENERIC', enable_ocr: bool = True) -> bool:
        """Initialize the enhanced screen scraper with OCR support."""
        if not SCRAPER_AVAILABLE:
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

            # Initialize OCR if available and enabled
            if enable_ocr and OCR_AVAILABLE:
                try:
                    self.ocr_engine = get_poker_ocr()
                    self.card_regions = create_card_regions('standard')
                    logger.info(f"OCR engine initialized with {len(self.card_regions)} regions")
                except Exception as e:
                    logger.warning(f"Failed to initialize OCR: {e}")
                    self.ocr_engine = None

            logger.info(f'Enhanced screen scraper initialized for {poker_site.value}')
            return True

        except Exception as e:
            logger.error(f'Failed to initialize screen scraper: {e}')
            return False

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for table state updates."""
        self.callbacks.append(callback)

    def _on_table_update(self, game_state: Dict[str, Any]):
        """Handle table state updates with OCR enhancement."""
        # Enhance game state with OCR if available
        if self.ocr_engine and 'table_image' in game_state:
            enhanced_state = self._enhance_with_ocr(game_state)
            if enhanced_state:
                game_state.update(enhanced_state)

        self.last_state = game_state

        # Update HUD overlay if running
        if HUD_AVAILABLE and is_hud_running():
            try:
                update_hud_state(game_state)
            except Exception as e:
                logger.error(f'HUD update error: {e}')

        # Save to database
        self._save_table_state(game_state)

        # Notify all callbacks
        for callback in self.callbacks:
            try:
                callback(game_state)
            except Exception as e:
                logger.error(f'Callback error: {e}')

    def _enhance_with_ocr(self, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhance game state with OCR-recognized information."""
        try:
            table_image = game_state.get('table_image')
            if table_image is None:
                return None

            # Convert to numpy array if needed
            if not isinstance(table_image, np.ndarray):
                import cv2
                table_image = cv2.imread(str(table_image)) if isinstance(table_image, str) else table_image

            enhanced_data = {}
            recognition_results = []

            # Recognize cards in parallel using thread pool
            def recognize_region(region: CardRegion) -> Tuple[str, RecognitionResult]:
                result = self.ocr_engine.recognize_cards(table_image, region)
                return region.card_type, result

            # Submit recognition tasks
            futures = []
            for region in self.card_regions:
                if region.card_type in ['hole', 'board']:  # Focus on important regions first
                    future = self.thread_pool.submit_thread_task(recognize_region, region)
                    futures.append((region.card_type, future))

            # Collect results
            for region_type, future in futures:
                try:
                    _, result = future.result(timeout=2.0)
                    recognition_results.append((region_type, result))
                    
                    if result.cards:
                        enhanced_data[f'{region_type}_cards_ocr'] = result.cards
                        enhanced_data[f'{region_type}_confidence'] = result.confidence
                        
                        # Update stats
                        self.recognition_stats['successful_recognitions'] += 1
                        self.recognition_stats['avg_confidence'] = (
                            (self.recognition_stats['avg_confidence'] * 
                             (self.recognition_stats['successful_recognitions'] - 1) + 
                             result.confidence) / self.recognition_stats['successful_recognitions']
                        )
                    else:
                        self.recognition_stats['failed_recognitions'] += 1
                        
                except Exception as e:
                    logger.debug(f'OCR recognition failed for {region_type}: {e}')
                    self.recognition_stats['failed_recognitions'] += 1

            self.recognition_stats['total_captures'] += 1

            # Recognize betting amounts
            if self.card_regions:
                betting_regions = [r for r in self.card_regions if r.card_type in ['pot', 'hero_bet']]
                amounts = self.ocr_engine.recognize_betting_amounts(table_image, betting_regions)
                enhanced_data.update(amounts)

            # Add OCR metadata
            enhanced_data['ocr_stats'] = self.recognition_stats.copy()
            enhanced_data['ocr_timestamp'] = time.time()

            return enhanced_data

        except Exception as e:
            logger.error(f'OCR enhancement failed: {e}')
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

            return game_state

        except Exception as e:
            logger.error(f'Single capture failed: {e}')
            return None

    def get_latest_state(self) -> Optional[Dict[str, Any]]:
        """Get the latest captured table state."""
        return self.last_state

    def get_recognition_stats(self) -> Dict[str, Any]:
        """Get OCR recognition statistics."""
        stats = self.recognition_stats.copy()
        if stats['total_captures'] > 0:
            stats['success_rate'] = stats['successful_recognitions'] / stats['total_captures']
        else:
            stats['success_rate'] = 0.0
        
        stats['ocr_enabled'] = self.ocr_engine is not None
        return stats

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

    if not _scraper_manager.scraper:
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
        'ocr_available': OCR_AVAILABLE,
        'ocr_enabled': _scraper_manager.ocr_engine is not None,
        'last_state': _scraper_manager.last_state,
        'recognition_stats': _scraper_manager.get_recognition_stats()
    }

def register_table_callback(callback: Callable[[Dict[str, Any]], None]) -> bool:
    """Register a callback for table state updates."""
    global _scraper_manager

    try:
        _scraper_manager.register_callback(callback)
        return True
    except Exception as e:
        logger.error(f'Failed to register callback: {e}')
        return False

def save_debug_capture(filename: str = 'debug_table.png') -> bool:
    """Save a debug image of the current table state with OCR regions."""
    global _scraper_manager

    return _scraper_manager.save_debug_image(filename)

def get_recognition_stats() -> Dict[str, Any]:
    """Get OCR recognition statistics."""
    global _scraper_manager
    
    return _scraper_manager.get_recognition_stats()

# Async support for API integration
async def run_screen_scraper_async(site: str = 'GENERIC', enable_ocr: bool = True) -> Dict[str, Any]:
    """Async version of screen scraper for API integration."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_screen_scraper, site, False, 1.0, enable_ocr)

# Anti-detection utilities
def implement_anti_detection() -> Dict[str, Any]:
    """Implement advanced anti-detection mechanisms for screen scraping."""
    try:
        import random
        import time
        
        mechanisms = {}
        
        # Random delays between captures
        def add_random_delay():
            delay = random.uniform(0.5, 2.0)  # 0.5 to 2 second delay
            time.sleep(delay)
            return delay
        
        # Simulate human-like mouse movements
        def simulate_mouse_movement():
            try:
                import pyautogui
                # Get current mouse position
                current_x, current_y = pyautogui.position()
                
                # Small random movement (simulating human jitter)
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                
                new_x = max(0, min(current_x + offset_x, pyautogui.size()[0] - 1))
                new_y = max(0, min(current_y + offset_y, pyautogui.size()[1] - 1))
                
                # Smooth movement
                pyautogui.moveTo(new_x, new_y, duration=random.uniform(0.1, 0.3))
                return True
            except ImportError:
                logger.warning("pyautogui not available for mouse simulation")
                return False
            except Exception as e:
                logger.debug(f"Mouse simulation failed: {e}")
                return False
        
        # Vary capture intervals
        def get_varied_interval(base_interval: float = 1.0) -> float:
            # Add 20% variance to interval
            variance = base_interval * 0.2
            return base_interval + random.uniform(-variance, variance)
        
        # Process priority simulation (lower CPU usage randomly)
        def simulate_process_priority():
            try:
                import psutil
                import os
                
                current_process = psutil.Process(os.getpid())
                # Randomly lower priority occasionally
                if random.random() < 0.1:  # 10% chance
                    current_process.nice(1)  # Lower priority
                    time.sleep(random.uniform(0.1, 0.5))
                    current_process.nice(0)  # Reset to normal
                return True
            except ImportError:
                return False
            except Exception as e:
                logger.debug(f"Process priority simulation failed: {e}")
                return False
        
        # Browser fingerprint randomization
        def randomize_user_agent():
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101'
            ]
            return random.choice(user_agents)
        
        # Network request timing simulation
        def add_network_delay():
            # Simulate network latency
            delay = random.expovariate(1/0.1)  # Exponential distribution with mean 0.1
            time.sleep(min(delay, 1.0))  # Cap at 1 second
            return delay
        
        # Test each mechanism
        mechanisms['random_delays'] = add_random_delay() > 0
        mechanisms['mouse_movements'] = simulate_mouse_movement()
        mechanisms['varied_intervals'] = True  # Always available
        mechanisms['process_priority'] = simulate_process_priority()
        mechanisms['user_agent_rotation'] = True  # Always available
        mechanisms['network_simulation'] = add_network_delay() > 0
        
        # Store functions for later use
        global _anti_detection_functions
        _anti_detection_functions = {
            'add_delay': add_random_delay,
            'move_mouse': simulate_mouse_movement,
            'vary_interval': get_varied_interval,
            'simulate_priority': simulate_process_priority,
            'get_user_agent': randomize_user_agent,
            'network_delay': add_network_delay
        }
        
        # Stealth mode configuration
        mechanisms['stealth_mode'] = all([
            mechanisms['random_delays'],
            mechanisms['varied_intervals'],
            mechanisms['network_simulation']
        ])
        
        success_count = sum(1 for enabled in mechanisms.values() if enabled)
        
        logger.info(f'Anti-detection mechanisms activated: {success_count}/{len(mechanisms)}')
        return {
            'status': 'success', 
            'mechanisms': mechanisms,
            'success_rate': success_count / len(mechanisms)
        }
        
    except Exception as e:
        logger.error(f'Failed to implement anti-detection: {e}')
        return {'status': 'error', 'message': str(e)}

def apply_anti_detection_delay():
    """Apply anti-detection delay before scraping operations."""
    try:
        global _anti_detection_functions
        if '_anti_detection_functions' in globals():
            # Random delay
            _anti_detection_functions['add_delay']()
            
            # Occasional mouse movement
            if random.random() < 0.3:  # 30% chance
                _anti_detection_functions['move_mouse']()
            
            # Network simulation
            if random.random() < 0.2:  # 20% chance
                _anti_detection_functions['network_delay']()
                
    except Exception as e:
        logger.debug(f"Anti-detection delay failed: {e}")

# Global storage for anti-detection functions
_anti_detection_functions = {}

if __name__ == '__main__':
    # Test enhanced scraper functionality
    print("Enhanced Screen Scraper with OCR Integration")
    print(f"Scraper available: {SCRAPER_AVAILABLE}")
    print(f"OCR available: {OCR_AVAILABLE}")
    
    if SCRAPER_AVAILABLE:
        result = run_screen_scraper('GENERIC', False, 1.0, True)
        print(f"Test result: {result}")
    else:
        print("Screen scraper dependencies not available")
