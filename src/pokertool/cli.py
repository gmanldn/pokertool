#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
PokerTool Cli Module
======================

This module provides functionality for cli operations
within the PokerTool application ecosystem.

Module: pokertool.cli
Version: 21.0.0
Last Modified: 2025-10-04
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v21.0.0 (2025-10-04): Enhanced GUI is now the ONLY GUI (removed fallback)
    - v20.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '21.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

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

    sub.add_parser('gui', help='Launch the Enhanced Tkinter GUI')
    sub.add_parser('scrape', help='Run the screen scraper (headless)')
    sub.add_parser('test', help='Run basic functionality tests')

    args = parser.parse_args(argv)

    if args.cmd in (None, 'gui'):
        # Check if tkinter is available before importing GUI
        try:
            import tkinter
            # Silent availability check without showing a demo window
            root = tkinter.Tk()
            try:
                root.withdraw()
                root.update_idletasks()
            finally:
                root.destroy()
        except Exception as e:
            logger.error(f'GUI not available: {e}')
            logger.info('Tkinter is not available on this system.')
            logger.info('On macOS, you may need to install tkinter with:')
            logger.info('  brew install python-tk')
            logger.info('Or use Anaconda/Miniconda which includes tkinter.')
            logger.info('Falling back to test mode...')
            return run_test_mode()
        
        # Import ONLY the enhanced GUI (no fallback)
        logger.info('🚀 Launching Enhanced PokerTool GUI...')
        try:
            from . import enhanced_gui
            
            # Run the enhanced GUI
            if hasattr(enhanced_gui, 'main'):
                return enhanced_gui.main()
            elif hasattr(enhanced_gui, 'run'):
                return enhanced_gui.run()
            else:
                # Create and run IntegratedPokerAssistant directly
                logger.info('Starting IntegratedPokerAssistant...')
                app = enhanced_gui.IntegratedPokerAssistant()
                app.mainloop()
                return 0
                
        except ImportError as e:
            logger.error(f'Enhanced GUI module not found: {e}')
            logger.error('The enhanced GUI is required. Please ensure all dependencies are installed.')
            logger.info('Run: python start.py --all')
            return 1
        except Exception as e:
            logger.error(f'Enhanced GUI startup failed: {e}')
            import traceback
            traceback.print_exc()
            return 1
    
    elif args.cmd == 'scrape':
        try:
            from . import scrape
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
        from . import core
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
        from .core import analyse_hand, parse_card, Position
        # Run a basic test
        hole_cards = [parse_card('As'), parse_card('Ah')]
        result = analyse_hand(hole_cards, position=Position.BTN, pot=100, to_call=10)
        logger.info(f'✅ Poker analysis working: {type(result).__name__}')
    except Exception as e:
        logger.error(f'❌ Poker analysis failed: {e}')
    
    logger.info('=' * 40)
    logger.info('Test mode completed. Use "pokertool gui" to launch Enhanced GUI (if tkinter is available).')
    logger.info('Use "pokertool scrape" for headless screen scraping functionality.')
    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
