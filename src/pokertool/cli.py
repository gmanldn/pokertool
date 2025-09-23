"""
cli.py — CLI entrypoint for pokertool.
"""
from __future__ import annotations

import argparse
import sys
import logging

# Set up basic logging for CLI
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def main(argv=None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(prog='pokertool', description='PokerTool CLI')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('gui', help='Launch the Tkinter GUI')
    sub.add_parser('scrape', help='Run the screen scraper (headless)')
    sub.add_parser('test', help='Run basic functionality tests')

    args = parser.parse_args(argv)

    if args.cmd in (None, 'gui'):
        # Check if tkinter is available before importing GUI
        try:
            import tkinter
            tkinter._test()  # Basic tkinter test
        except Exception as e:
            logger.error(f'GUI not available: {e}')
            logger.info('Tkinter is not available on this system.')
            logger.info('On macOS, you may need to install tkinter with:')
            logger.info('  brew install python-tk')
            logger.info('Or use Anaconda/Miniconda which includes tkinter.')
            logger.info('Falling back to test mode...')
            return run_test_mode()
        
        # Import GUI only after tkinter check passes
        try:
            from pokertool import gui
            return gui.main()
        except AttributeError:
            # Fallback if gui exposes a function named run() instead
            return getattr(gui, 'run')()
        except Exception as e:
            logger.error(f'GUI startup failed: {e}')
            return 1
    
    elif args.cmd == 'scrape':
        try:
            from pokertool import scrape
            result = scrape.run_screen_scraper()
            logger.info(result)
            return 0
        except Exception as e:
            logger.error(f'Scraper failed: {e}')
            return 1

    elif args.cmd == 'test':
        return run_test_mode()

    return 0

def run_test_mode():
    """Run basic functionality tests without GUI."""
    logger.info('🧪 PokerTool - Test Mode')
    logger.info('=' * 40)
    
    # Test basic imports
    logger.info('Testing core imports...')
    try:
        from pokertool import core
        logger.info('✅ Core module imported successfully')
    except Exception as e:
        logger.error(f'❌ Core module import failed: {e}')
    
    # Test database functionality
    logger.info('Testing database functionality...')
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE test (id INTEGER)')
        conn.close()
        logger.info('✅ Database functionality working')
    except Exception as e:
        logger.error(f'❌ Database test failed: {e}')
    
    # Test basic poker logic if available
    logger.info('Testing poker analysis...')
    try:
        from pokertool.core import analyse_hand, parse_card, Position
        # Run a basic test
        hole_cards = [parse_card('As'), parse_card('Ah')]
        result = analyse_hand(hole_cards, position=Position.BTN, pot=100, to_call=10)
        logger.info(f'✅ Poker analysis working: {type(result).__name__}')
    except Exception as e:
        logger.error(f'❌ Poker analysis failed: {e}')
    
    logger.info('=' * 40)
    logger.info('Test mode completed. Use "pokertool gui" to launch GUI (if tkinter is available).')
    logger.info('Use "pokertool scrape" for headless screen scraping functionality.')
    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
