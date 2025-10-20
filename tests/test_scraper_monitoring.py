#!/usr/bin/env python3
"""Test script to monitor Betfair screen scraping functionality."""

import sys
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/scraper_test.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

# Add source to path
sys.path.insert(0, str(Path(__file__).parent))

def test_scraper():
    """Test the Betfair screen scraper."""
    try:
        logger.info("=" * 60)
        logger.info("Starting Betfair Screen Scraper Test")
        logger.info("=" * 60)
        
        # Import scraper modules
        from src.pokertool.modules.poker_screen_scraper_betfair import create_scraper
        logger.info("✓ Imported Betfair scraper module")
        
        # Create scraper instance
        scraper = create_scraper('BETFAIR')
        logger.info("✓ Created Betfair scraper instance")
        
        # Continuous monitoring loop
        logger.info("Starting continuous monitoring (press Ctrl+C to stop)...")
        logger.info("-" * 60)
        
        detection_count = 0
        loop_count = 0
        
        while True:
            loop_count += 1
            logger.debug(f"Loop iteration {loop_count}")
            
            try:
                # Capture screenshot
                img = scraper.capture_table()
                if img is not None:
                    logger.debug(f"Screenshot captured: {img.shape}")
                    
                    # Detect poker table
                    is_poker, confidence, details = scraper.detect_poker_table(img)
                    
                    if is_poker:
                        detection_count += 1
                        logger.info(f"🎯 TABLE DETECTED #{detection_count}")
                        logger.info(f"  • Confidence: {confidence:.1%}")
                        logger.info(f"  • Site: {details.get('site', 'unknown')}")
                        logger.info(f"  • Detector: {details.get('detector', 'unknown')}")
                        logger.info(f"  • Time: {details.get('time_ms', 0):.1f}ms")
                        
                        # Analyze table state
                        state = scraper.analyze_table(img)
                        if state:
                            logger.info("  📊 Table Analysis:")
                            
                            # Basic info
                            pot_size = getattr(state, 'pot_size', 0)
                            if pot_size > 0:
                                logger.info(f"    • Pot: ${pot_size}")
                            
                            active_players = getattr(state, 'active_players', 0)
                            if active_players > 0:
                                logger.info(f"    • Active players: {active_players}")
                            
                            stage = getattr(state, 'stage', 'unknown')
                            if stage != 'unknown':
                                logger.info(f"    • Stage: {stage}")
                            
                            # Hero cards
                            hero_cards = getattr(state, 'hero_cards', [])
                            if hero_cards:
                                cards_str = ', '.join([str(c) for c in hero_cards])
                                logger.info(f"    • Your cards: {cards_str}")
                            
                            # Board cards  
                            board_cards = getattr(state, 'board_cards', [])
                            if board_cards:
                                cards_str = ', '.join([str(c) for c in board_cards])
                                logger.info(f"    • Board: {cards_str}")
                            
                            # Player info
                            if hasattr(state, 'seats') and state.seats:
                                player_count = sum(1 for s in state.seats if s)
                                if player_count > 0:
                                    logger.info(f"    • Seated players: {player_count}")
                            
                            logger.info("-" * 60)
                        else:
                            logger.warning("Table detected but analysis failed")
                    else:
                        if loop_count % 10 == 0:  # Log every 10th loop when no table
                            logger.debug(f"No table detected (confidence: {confidence:.1%})")
                else:
                    if loop_count % 10 == 0:
                        logger.warning("Screenshot capture returned None")
            
            except Exception as e:
                logger.error(f"Error in detection loop: {e}", exc_info=True)
            
            # Wait before next iteration
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Test stopped by user")
        logger.info(f"Total detections: {detection_count}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Run scraper test (GUI removed in web-only architecture)
    test_scraper()
