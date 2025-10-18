# Screen Scraper Fix Documentation
> Issue Register: Use `python new_task.py` to append GUID-tagged entries to `docs/TODO.md`; manual edits are rejected and historical backlog lives in `docs/TODO_ARCHIVE.md`.

## Problem Identified

The screen scraper was failing due to Chrome capture initialization issues:

1. **Chrome Debugging Port Not Available** - Port 9222 not accessible
2. **Import Path Issues** - Module resolution problems
3. **Configuration Defaults** - Chrome site defaulting to failing capture method

## Current Status

- ✅ **MSS (Monitor Capture)** - WORKING and reliable
- ✅ **Desktop Independent Scraper** - Core functionality working
- ❌ **Chrome Tab Capture** - Requires Chrome with debugging enabled
- ❌ **Chrome Window Capture** - Platform-specific issues

## Solution

### Use Monitor Capture (Recommended)

The most reliable screen capture method is **monitor capture** using MSS library.

```python
from pokertool.modules.poker_screen_scraper import create_scraper, PokerSite

# Use GENERIC site for monitor capture (RECOMMENDED)
scraper = create_scraper('GENERIC')

# Or explicitly set monitor as capture source
from pokertool.scrape import run_screen_scraper
result = run_screen_scraper(site='GENERIC', continuous=False)
```

### Enable Chrome Capture (Optional)

If you need Chrome-specific capture:

1. Start Chrome with remote debugging:

   ```bash
   ```bash
   # macOS/Linux
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
   
   # Windows
   chrome.exe --remote-debugging-port=9222
   ```

2. Set environment variables (optional):

   ```bash
   ```bash
   export POKERTOOL_CHROME_HOST=127.0.0.1
   export POKERTOOL_CHROME_PORT=9222
   export POKERTOOL_CHROME_TITLE_FILTER="Poker"
   ```

3. Use Chrome site:

   ```python
   ```python
   scraper = create_scraper('CHROME')
   ```

## Testing

### Quick Test
```bash
cd /Users/georgeridout/Documents/github/pokertool
python test_desktop_scraper.py
```

### Diagnostic Tool
```bash
python src/pokertool/scrape_fix.py
```

## Files Modified

1. **src/pokertool/scrape_fix.py** - New diagnostic tool
2. **SCRAPER_FIX_README.md** - This documentation

## Recommendations

1. **Use `GENERIC` site for most reliable operation**
2. Only use `CHROME` if you specifically need browser capture and have debugging enabled
3. Use the desktop independent scraper for cross-desktop/workspace poker window detection
4. Monitor capture works immediately without any configuration

## Next Steps

1. Run the test suite to verify fixes:

   ```bash
   ```bash
   python test_desktop_scraper.py
   ```

2. Update any calling code to use `GENERIC` instead of `CHROME`:

   ```python
   ```python
   # OLD (may fail)
   run_screen_scraper(site='CHROME')
   
   # NEW (reliable)
   run_screen_scraper(site='GENERIC')
   ```

3. For poker window detection across desktops:

   ```python
   ```python
   from pokertool.scrape import run_desktop_independent_scraper
   
   result = run_desktop_independent_scraper(
       detection_mode='COMBINED',
       continuous=False
   )
   ```

## Verification

The diagnostic tool confirms:

- ✅ MSS working - Can capture full screen
- ✅ Desktop scraper functional - Can detect poker windows
- ⚠️  Chrome capture - Requires manual setup

## Support

If issues persist:

1. Check dependencies: `pip install mss opencv-python pillow numpy`
2. Run diagnostic: `python src/pokertool/scrape_fix.py`
3. Check logs in `logs/pokertool_errors.log`

---

**Date:** October 2, 2025
**Status:** RESOLVED - Use GENERIC site for monitor capture
