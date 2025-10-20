# What's New in PokerTool v37

## 🎯 Major Features

### 1. Purple Table Detection (v36.0.0)
**100% detection accuracy on Betfair purple tables!**

- Updated HSV color ranges to detect purple/violet Betfair poker tables
- Enhanced ellipse detection with morphological operations
- Supports both green AND purple tables simultaneously
- Calibrated against real Betfair table screenshots

**Test Results:**
```
✓ Felt ratio: 59.6%
✓ Table shape: ellipse(0.70)
✓ Detection confidence: 100%
✓ Pot size: $0.08 (accurate OCR)
✓ Active players: 2 detected
```

### 2. Poker Handle Configuration (NEW!)
**Accurate hero detection regardless of seat position**

Previously, the system always assumed seat #1 was the hero - completely inaccurate!

Now:

- **Prompts for your poker handle on first startup**
- **Uses OCR to match your username** at each seat
- **Accurately identifies your position** anywhere at the table
- **Handles OCR errors** with fuzzy matching

**Example Flow:**
```
POKER HANDLE SETUP
======================================================================

To accurately identify your position at the table, please enter
your poker username/handle exactly as it appears on the poker site.

Example: If you see 'JohnPoker123' at the table, enter: JohnPoker123

Enter your poker handle (or 'skip' to skip): JohnPoker123

✓ Poker handle saved: JohnPoker123
```

**During Gameplay:**
```
[INFO] ✓ Hero detected at seat 5: 'JohnPoker' matches handle 'JohnPoker123'
```

**Benefits:**

- ✅ Works at ANY seat (not just seat #1)
- ✅ Fuzzy matching handles OCR errors ("J0hnP0ker" matches "JohnPoker")
- ✅ One-time setup, remembers your handle
- ✅ Can skip to use seat #1 heuristic (old behavior)

### 3. Comprehensive Startup Validation (v36.0.0)
**Know exactly what's working before you start!**

```
🔍 POKERTOOL STARTUP DEPENDENCY CHECK
======================================================================

System Information:
----------------------------------------------------------------------
  ✓ Python: v3.12.12 - Version OK
  ℹ Platform: Darwin 24.4.0

Core Dependencies:
----------------------------------------------------------------------
  ✓ NumPy                v1.26.4 - Installed
  ✓ OpenCV               v4.9.0 - Installed
  ✓ Pillow               v11.3.0 - Installed
  ✓ pytesseract          v0.3.13 - Installed
  ✓ MSS                  v10.1.0 - Screen capture available

Optional Features:
----------------------------------------------------------------------
  ✓ PyTorch              v2.2.2 - ML features available
  ℹ GPU (CUDA)           - Not available (CPU mode)
  ✓ Tesseract OCR        v5.5.1 - Binary installed

SUMMARY
======================================================================
✓ ALL DEPENDENCIES SATISFIED
Application is ready to start!
```

**Validates:**

- Python version (3.10+)
- Core dependencies (NumPy, OpenCV, Pillow, pytesseract, MSS)
- Optional features (PyTorch, GPU/CUDA)
- Tesseract OCR binary
- System resources

**Prevents startup** if critical dependencies are missing!

## 📁 New Files

- `src/pokertool/user_config.py` - User configuration management
  - Stores poker handle in `.pokertool_config.json`
  - Functions: `get_poker_handle()`, `set_poker_handle()`, `prompt_for_poker_handle()`
  - Persistent across sessions

## 🔧 Updated Files

- `poker_screen_scraper_betfair.py` - Purple table detection + hero matching
- `multi_table_segmenter.py` - Multi-color table support
- `startup_validator.py` - Dependency checks + handle prompt
- `.gitignore` - Added `.pokertool_config.json`

## 🚀 How to Use

### First Time Setup
```bash
python start.py
```

1. Startup validation checks all dependencies
2. Prompts for your poker handle (e.g., "JohnPoker123")
3. Saves handle to `.pokertool_config.json`
4. Launches GUI

### Changing Your Handle

Edit `.pokertool_config.json`:
```json
{
  "poker_handle": "YourNewHandle",
  "poker_site": "BETFAIR",
  "show_startup_validation": true,
  "auto_detect_hero": true
}
```

Or delete the file to be prompted again on next startup.

## 🐛 Known Issues

### macOS OpenCV Loading Issue

If you see:
```
✗ OpenCV - Library not loaded: @loader_path/.dylibs/libavcodec...
```

**Solution 1**: Install opencv-python-headless
```bash
./.venv/bin/pip uninstall opencv-python
./.venv/bin/pip install opencv-python-headless
```

**Solution 2**: Install via Homebrew
```bash
brew install opencv
```

## 📊 Version History

- **v37.0.0** (upcoming) - Poker handle configuration
- **v36.0.0** - Purple table detection + startup validation
- **v35.0.0** - Confidence-aware decision API
- **v34.0.0** - Enhanced UX with hero position
- **v33.0.0** - Startup validation system

## 🎓 Configuration Options

`.pokertool_config.json`:
```json
{
  "poker_handle": "YourUsername",
  "poker_site": "BETFAIR",
  "show_startup_validation": true,
  "auto_detect_hero": true,
  "detection_confidence_threshold": 0.5,
  "enable_logging": true
}
```

## 🔒 Privacy

- `.pokertool_config.json` is **gitignored** by default
- Your poker handle is stored locally only
- Never transmitted or shared

## 📞 Support

Having issues? Check:

1. Is your poker handle spelled exactly as it appears on the site?
2. Is Tesseract OCR installed? (`brew install tesseract`)
3. Is OpenCV working? (See Known Issues above)

---

**Enjoy more accurate hero detection and purple table support!** 🎰
