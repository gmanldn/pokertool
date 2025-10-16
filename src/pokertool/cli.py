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
import logging
import sys
from typing import Optional, Tuple

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

    sub.add_parser('web', help='Launch the web interface (default)')
    sub.add_parser('scrape', help='Run the screen scraper (headless)')
    sub.add_parser('test', help='Run basic functionality tests')

    args = parser.parse_args(argv)

    if args.cmd in (None, 'web'):
        logger.info('🚀 Launching PokerTool Web Interface...')
        try:
            # Try relative import first, then absolute import as fallback
            try:
                from . import api
            except ImportError:
                import pokertool.api as api
            
            # Run the web server
            if hasattr(api, 'main'):
                return api.main()
            elif hasattr(api, 'run'):
                return api.run()
            else:
                logger.error('Web API module does not have a main() or run() function')
                logger.info('The web interface needs to be properly configured.')
                return 1
                
        except ImportError as e:
            logger.error(f'Web API module not found: {e}')
            logger.error('Please ensure all dependencies are installed.')
            logger.info('Run: pip install -r requirements.txt')
            return 1
        except Exception as e:
            logger.error(f'Web server startup failed: {e}')
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
    logger.info('Test mode completed. Use "pokertool web" to launch the web interface.')
    logger.info('Use "pokertool scrape" for headless screen scraping functionality.')
    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
