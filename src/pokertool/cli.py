"""
cli.py — CLI entrypoint for pokertool.
"""
from __future__ import annotations

import argparse
import sys

def main(argv = None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(prog = 'pokertool', description = 'PokerTool CLI',)
    sub = parser.add_subparsers(dest = 'cmd',)

    sub.add_parser('gui', help = 'Launch the Tkinter GUI',)
    sub.add_parser('scrape', help = 'Run the screen scraper (headless)',)

    args = parser.parse_args(argv,)

    if args.cmd in (None, 'gui'):
        # Defer tkinter import to runtime
        try:
            from pokertool import gui
        except Exception as e:
            print(f'[fatal] GUI import failed: {e}', file = sys.stderr,)
            return 1
            try:
                return gui.main(,)
            except AttributeError:
            # Fallback if gui exposes a function named run() instead
                return getattr(gui, 'run')(,)
            elif args.cmd == 'scrape':
                from pokertool import scrape
                result = scrape.run_screen_scraper(,)
                print(result,)
                return 0

                return 0

                if __name__ == '__main__':
                    raise SystemExit(main(),)
