"""
cli.py — CLI entrypoint for pokertool.
"""
from __future__ import annotations

import argparse
import sys

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
            print(f'[error] GUI not available: {e}', file=sys.stderr)
            print('[info] Tkinter is not available on this system.', file=sys.stderr)
            print('[info] On macOS, you may need to install tkinter with:', file=sys.stderr)
            print('[info]   brew install python-tk', file=sys.stderr)
            print('[info] Or use Anaconda/Miniconda which includes tkinter.', file=sys.stderr)
            print('[info] Falling back to test mode...', file=sys.stderr)
            return run_test_mode()
        
        # Import GUI only after tkinter check passes
        try:
            from pokertool import gui
            return gui.main()
        except AttributeError:
            # Fallback if gui exposes a function named run() instead
            return getattr(gui, 'run')()
        except Exception as e:
            print(f'[error] GUI startup failed: {e}', file=sys.stderr)
            return 1
    
    elif args.cmd == 'scrape':
        try:
            from pokertool import scrape
            result = scrape.run_screen_scraper()
            print(result)
            return 0
        except Exception as e:
            print(f'[error] Scraper failed: {e}', file=sys.stderr)
            return 1

    elif args.cmd == 'test':
        return run_test_mode()

    return 0

def run_test_mode():
    """Run basic functionality tests without GUI."""
    print('🧪 PokerTool - Test Mode')
    print('=' * 40)
    
    # Test basic imports
    print('Testing core imports...')
    try:
        from pokertool import core
        print('✅ Core module imported successfully')
    except Exception as e:
        print(f'❌ Core module import failed: {e}')
    
    # Test database functionality
    print('Testing database functionality...')
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE test (id INTEGER)')
        conn.close()
        print('✅ Database functionality working')
    except Exception as e:
        print(f'❌ Database test failed: {e}')
    
    # Test basic poker logic if available
    print('Testing poker analysis...')
    try:
        from pokertool.core import analyse_hand, parse_card, Position
        # Run a basic test
        hole_cards = [parse_card('As'), parse_card('Ah')]
        result = analyse_hand(hole_cards, position=Position.BTN, pot=100, to_call=10)
        print(f'✅ Poker analysis working: {type(result).__name__}')
    except Exception as e:
        print(f'❌ Poker analysis failed: {e}')
    
    print('=' * 40)
    print('Test mode completed. Use "pokertool gui" to launch GUI (if tkinter is available).')
    print('Use "pokertool scrape" for headless screen scraping functionality.')
    
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
