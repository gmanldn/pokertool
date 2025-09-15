<!-- POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool/README.md
version: '20'
last_commit: '2025-09-14T23:35:42.847310+00:00'
fixes: []
---
POKERTOOL-HEADER-END -->
# Poker Assistant - Fixed Version

This directory contains the complete, fixed poker assistant application that resolves all regression bugs.

## Files Included

- **poker_modules.py** - Core poker logic, hand analysis, and card handling (FIXED)
- **poker_init.py** - Database initialization and persistence layer (FIXED)
- **poker_gui.py** - Main graphical user interface (FIXED)  
- **poker_main.py** - Application launcher (FIXED)
- **poker_go.py** - Setup script with dependency checking
- **poker_config.json** - Configuration file
- **README.md** - This file

## What Was Fixed

### Major Issues Resolved:
1. **Import Errors** - Fixed missing functions and classes that GUI was expecting
2. **API Mismatches** - Aligned function signatures between modules
3. **Missing Classes** - Added all required classes (GameState, HandAnalysisResult, etc.)
4. **Database Schema** - Fixed database compatibility issues
5. **Card Parsing** - Improved card input validation and parsing
6. **Error Handling** - Added proper fallback mechanisms

### Key Improvements:
- Enhanced card entry with validation
- Better error messages and debugging
- Fallback mode when modules fail to load
- Improved compatibility between components
- More robust database handling

## How to Run

### Option 1: Use the setup script (Recommended)
```bash
python3 poker_go.py
```

### Option 2: Run directly
```bash
python3 poker_main.py
```

### Option 3: Run GUI directly
```bash
python3 poker_gui.py
```

## Requirements

- Python 3.7 or higher
- tkinter (usually included with Python)
- No additional packages required

## Features

- **Hand Analysis**: Analyze poker hands with position and stack considerations
- **Card Input**: Enhanced card entry with validation and auto-completion hints
- **Database**: Automatic saving of analysis results
- **Position Awareness**: Recommendations based on table position
- **Board Texture Analysis**: Evaluates flop/turn/river dynamics
- **Quick Hands**: Buttons for common starting hands (AA, KK, AK)
- **Session Persistence**: Saves and loads your game state

## Usage

1. Enter your two hole cards (e.g., AS, KH)
2. Enter board cards if post-flop (e.g., QS, JD, TC)
3. Set your position and stack size
4. Enter pot size and amount to call
5. Click "Analyse Hand" for recommendations

## Card Input Format

Cards should be entered as two characters:
- Rank: 2, 3, 4, 5, 6, 7, 8, 9, T, J, Q, K, A
- Suit: S (Spades), H (Hearts), D (Diamonds), C (Clubs)

Examples: AS, KH, QD, JC, TC

## Troubleshooting

If you encounter issues:

1. **Import Errors**: Ensure all .py files are in the same directory
2. **GUI Won't Start**: Check that tkinter is installed (`python3 -m tkinter`)
3. **Database Issues**: Delete `poker_decisions.db` to reset
4. **Module Errors**: The app will run in limited mode if poker_modules.py has issues

## Technical Notes

- Uses SQLite for decision storage
- Implements Chen formula for starting hand rankings
- Supports both preflop and postflop analysis
- Includes SPR (Stack-to-Pot Ratio) calculations
- Board texture analysis (dry, wet, paired)

## Version History

- **v1.0** - Fixed all regression bugs from original implementation
- Resolved import mismatches between GUI and core modules
- Added proper error handling and fallback mechanisms
- Improved card input validation and user experience

## Support

If you encounter any issues, check that:
1. All files are in the same directory
2. You're using Python 3.7+
3. tkinter is available
4. Try running `poker_go.py` for automated setup
