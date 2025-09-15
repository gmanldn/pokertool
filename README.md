<!-- POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: README.md
version: '20'
last_commit: '2025-09-15T03:10:40+01:00'
last_commit_hash: '0e8851bc52d28b82441342a4e20a8dc173cde109'
branch: 'main'
files_count: 39
modules_hash: '42a741bfaef60f9a785fa56c4b9e19d3309ac9318afe07278df25640b2e65829'
fixes: ['readme_sync','modules_doc_generated']
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

## File Headers (pokerheader.v1)

Every file in this repo carries a machine-readable header for logging and audit.

### Format
- YAML payload, fenced by markers `POKERTOOL-HEADER-START` and `POKERTOOL-HEADER-END`.
- For code and text files: YAML appears inside comments at the top of the file.
- For files that cannot hold comments (e.g., JSON, binaries): a sidecar file named `<filename>.pokerheader.yml`.

### Keys
- `schema`: always `pokerheader.v1`.
- `project`: `pokertool`.
- `file`: repository-relative path.
- `version`: semantic tag, starting at `v20.0.0`.
- `last_commit`: ISO-8601 timestamp of the last Git commit for that file, or file mtime if not under Git.
- `fixes`: list of `{date, summary}` entries documenting error fixes.

### Maintenance
Apply or update headers:

```bash
python3 tools/apply_headers.py --version v20.0.0 --fix "Initial v20 header applied"
# later examples:
python3 tools/apply_headers.py --version v20.1.0 --fix "Fix import mismatch in poker_modules"
python3 -m pytest -q tests/test_headers.py



## Improvements Log



<!-- IMPROVEMENTS-START -->
| When (UTC) | Improvement | Summary | Files touched |
|---|---|---|---|
| 2025-09-15T02:05:50.037678+00:00 | Improvement1.py | v20 header rollout, version vars, compile+AST audit | 51 |
| 2025-09-15T02:07:40.588679+00:00 | Improvement2.py | CHANGELOG added, module inventory refreshed, README log updated | 2 |
<!-- IMPROVEMENTS-END -->

<!-- AUTODOC:FILES-START -->
## Files Included

| File | Role | Last modified (UTC) |
|---|---|---|
| `Improvement1.py` | Utility/script | 2025-09-15T02:08:10.879427+00:00 |
| `Improvement2.py` | Utility/script | 2025-09-15T02:08:08.007432+00:00 |
| `Improvement3.py` | Utility/script | 2025-09-15T02:20:32.554947+00:00 |
| `apply_headers.py` | Utility/script | 2025-09-15T02:05:50.088115+00:00 |
| `apply_pokertool_fixes.py` | Utility/script | 2025-09-15T02:05:50.059505+00:00 |
| `autoconfirm.py` | Utility/script | 2025-09-15T02:05:50.054887+00:00 |
| `comprehensive_integration_tests.py` | Comprehensive integration tests | 2025-09-15T02:05:50.067867+00:00 |
| `enhanced_poker_test_main.py` | Enhanced test entry point | 2025-09-15T02:05:50.061325+00:00 |
| `final_test_validation.py` | Final validation tests | 2025-09-15T02:05:50.084124+00:00 |
| `gui_integration_tests.py` | GUI integration tests | 2025-09-15T02:05:50.078684+00:00 |
| `hotfix_pokertool.py` | Utility/script | 2025-09-15T02:05:50.080893+00:00 |
| `poker_go.py` | Setup/launcher with dependency checking | 2025-09-15T02:05:50.075587+00:00 |
| `poker_gui.py` | Main graphical user interface | 2025-09-15T02:05:50.066037+00:00 |
| `poker_gui_autopilot.py` | Automated GUI driver for testing | 2025-09-15T02:05:50.086890+00:00 |
| `poker_imports.py` | Shared imports, globals, and constants | 2025-09-15T02:05:50.074492+00:00 |
| `poker_init.py` | Database initialization and persistence layer | 2025-09-15T02:05:50.070282+00:00 |
| `poker_main.py` | Application launcher | 2025-09-15T02:05:50.071485+00:00 |
| `poker_modules.py` | Core poker logic: cards, enums, hand analysis | 2025-09-15T02:05:50.048915+00:00 |
| `poker_scraper_setup.py` | Scraper environment setup | 2025-09-15T02:05:50.063373+00:00 |
| `poker_screen_scraper.py` | Screen/table scraping utilities | 2025-09-15T02:05:50.073527+00:00 |
| `poker_tablediagram.py` | Table diagram helpers (ASCII/GUI) | 2025-09-15T02:05:50.053285+00:00 |
| `poker_test.py` | Unit tests | 2025-09-15T02:05:50.058080+00:00 |
| `saniitise_python_files.py` | Sanitise/fix Python files | 2025-09-15T02:05:50.050823+00:00 |
| `security_validation_tests.py` | Security sanity checks | 2025-09-15T02:05:50.072433+00:00 |
| `test_screen_scraper.py` | Utility/script | 2025-09-15T02:05:50.068932+00:00 |
| `requirements.txt` | Runtime dependencies | 2025-09-15T01:41:18.791101+00:00 |
| `requirements_scraper.txt` | Dependencies for scraper | 2025-09-15T01:41:18.866385+00:00 |
| `test_maintenance_guide.txt` | Asset | 2025-09-15T01:41:18.742166+00:00 |
| `testing_suite_summary.txt` | Asset | 2025-09-15T01:41:18.942483+00:00 |
| `CHANGELOG.md` | Asset | 2025-09-15T02:07:40.639425+00:00 |
| `README.md` | Project documentation | 2025-09-15T02:07:40.641407+00:00 |
| `poker_config.json` | Configuration file | 2025-09-14T23:35:15.340066+00:00 |
| `requirements.txt` | Runtime dependencies | 2025-09-15T01:41:18.791101+00:00 |
| `requirements_scraper.txt` | Dependencies for scraper | 2025-09-15T01:41:18.866385+00:00 |
| `tests/.DS_Store` | Asset | 2025-09-15T02:07:29.935583+00:00 |
| `tests/.DS_Store.pokerheader.yml` | Asset | 2025-09-15T01:44:35.451924+00:00 |
| `tests/__pycache__/test_poker.cpython-311.pyc` | Asset | 2025-09-15T00:43:36.556198+00:00 |
| `tests/__pycache__/test_poker.cpython-313.pyc` | Asset | 2025-09-15T02:05:50.232451+00:00 |
| `tests/test_poker.py` | Utility/script | 2025-09-15T02:05:50.090523+00:00 |
<!-- AUTODOC:FILES-END -->

<!-- AUTODOC:MODULES-START -->
## Machine-readable API for `poker_modules.py`

```json
{
  "schema": "pokermodules.v1",
  "module": "poker_modules.py",
  "generated_at": "2025-09-15T02:21:07.942084+00:00",
  "hash": "42a741bfaef60f9a785fa56c4b9e19d3309ac9318afe07278df25640b2e65829",
  "enums": [
    {
      "name": "Rank",
      "bases": [
        "Enum"
      ],
      "summary": null,
      "methods": [
        {
          "name": "sym",
          "summary": null,
          "returns": "str",
          "params": [
            {
              "name": "self",
              "annotation": null,
              "default": null,
              "kind": "pos"
            }
          ],
          "decorators": [
            "property"
          ],
          "lineno": 30
        },
        {
          "name": "val",
          "summary": null,
          "returns": "int",
          "params": [
            {
              "name": "self",
              "annotation": null,
              "default": null,
              "kind": "pos"
            }
          ],
          "decorators": [
            "property"
          ],
          "lineno": 37
        }
      ],
      "is_enum": true,
      "members": [
        "TWO",
        "THREE",
        "FOUR",
        "FIVE",
        "SIX",
        "SEVEN",
        "EIGHT",
        "NINE",
        "TEN",
        "JACK",
        "QUEEN",
        "KING",
        "ACE"
      ]
    },
    {
      "name": "Suit",
      "bases": [
        "Enum"
      ],
      "summary": null,
      "methods": [
        {
          "name": "glyph",
          "summary": null,
          "returns": "str",
          "params": [
            {
              "name": "self",
              "annotation": null,
              "default": null,
              "kind": "pos"
            }
          ],
          "decorators": [
            "property"
          ],
          "lineno": 43
        }
      ],
      "is_enum": true,
      "members": [
        "SPADES",
        "HEARTS",
        "DIAMONDS",
        "CLUBS"
      ]
    },
    {
      "name": "Position",
      "bases": [
        "Enum"
      ],
      "summary": null,
      "methods": [
        {
          "name": "category",
          "summary": null,
          "returns": "str",
          "params": [
            {
              "name": "self",
              "annotation": null,
              "default": null,
              "kind": "pos"
            }
          ],
          "decorators": [
            "property"
          ],
          "lineno": 49
        },
        {
          "name": "is_late",
          "summary": null,
          "returns": "bool",
          "params": [
            {
              "name": "self",
              "annotation": null,
              "default": null,
              "kind": "pos"
            }
          ],
          "decorators": [],
          "lineno": 56
        }
      ],
      "is_enum": true,
      "members": [
        "EARLY",
        "MIDDLE",
        "LATE",
        "BLINDS"
      ]
    }
  ],
  "classes": [
    {
      "name": "Card",
      "bases": [],
      "summary": null,
      "methods": [
        {
          "name": "__str__",
          "summary": null,
          "returns": "str",
          "params": [
            {
              "name": "self",
              "annotation": null,
              "default": null,
              "kind": "pos"
            }
          ],
          "decorators": [],
          "lineno": 63
        },
        {
          "name": "__repr__",
          "summary": null,
          "returns": "str",
          "params": [
            {
              "name": "self",
              "annotation": null,
              "default": null,
              "kind": "pos"
            }
          ],
          "decorators": [],
          "lineno": 64
        }
      ],
      "is_enum": false
    },
    {
      "name": "HandAnalysisResult",
      "bases": [],
      "summary": null,
      "methods": [],
      "is_enum": false
    }
  ],
  "functions": [
    {
      "name": "parse_card",
      "summary": null,
      "returns": "Card",
      "params": [
        {
          "name": "s",
          "annotation": "str",
          "default": null,
          "kind": "pos"
        }
      ],
      "decorators": [],
      "lineno": 66
    },
    {
      "name": "analyse_hand",
      "summary": null,
      "returns": "HandAnalysisResult",
      "params": [
        {
          "name": "hole_cards",
          "annotation": "Iterable[Card]",
          "default": null,
          "kind": "pos"
        },
        {
          "name": "board_cards",
          "annotation": "Optional[Iterable[Card]]",
          "default": "None",
          "kind": "pos"
        },
        {
          "name": "position",
          "annotation": "Optional[Position]",
          "default": "None",
          "kind": "pos"
        },
        {
          "name": "pot",
          "annotation": "Optional[float]",
          "default": "None",
          "kind": "pos"
        },
        {
          "name": "to_call",
          "annotation": "Optional[float]",
          "default": "None",
          "kind": "pos"
        }
      ],
      "decorators": [],
      "lineno": 84
    }
  ],
  "constants": [],
  "errors": null
}
```

_Regenerate with:_ `python3 Improvement3.py`
<!-- AUTODOC:MODULES-END -->
