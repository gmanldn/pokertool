#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: poker_main.py
# version: '20'
# last_updated_utc: '2025-09-15T02:05:50.037678+00:00'
# applied_improvements: [Improvement1.py]
# summary: Application launcher
# ---
# POKERTOOL-HEADER-END
__version__ = "20"


"""
Tiny launcher that wires everything together.
FIXED VERSION - Resolves import issues
"""
import logging
import sys
import os

# GUI compatibility imports
try:
    from poker_gui import EnhancedPokerAssistant as PokerAssistant
except ImportError:
    from poker_gui import PokerAssistant


# Add current directory to path to ensure modules can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Ensure the database exists (side-effect is cheap / idempotent)
try:
    from poker_init import initialise_db_if_needed
    initialise_db_if_needed()
except ImportError as e:
    print(f"Warning: Could not import poker_init: {e}")
    print("Creating minimal database initialization...")
    
    # Minimal fallback database init
    import sqlite3
    from pathlib import Path
    
    DB_FILE = "poker_decisions.db"
    if not Path(DB_FILE).exists():
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                CREATE TABLE decisions (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    position TEXT,
                    hand_tier TEXT,
                    stack_bb INTEGER,
                    pot REAL,
                    to_call REAL,
                    board TEXT,
                    decision TEXT,
                    spr REAL,
                    board_texture TEXT,
                    hand TEXT
                );
            """)
            conn.commit()

# Import the GUI after the DB is ready
try:
    from poker_gui import PokerAssistantGUI
except ImportError as e:
    print(f"Error: Could not import poker_gui: {e}")
    print("Please ensure poker_gui.py exists and is properly configured.")
    sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        app = PokerAssistantGUI()
        app.mainloop()
    except Exception as e:
        print(f"Error launching application: {e}")
        import traceback
        traceback.print_exc()
