# PokerTool Troubleshooting Guide

Comprehensive guide for diagnosing and fixing common issues with PokerTool.

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Startup Problems](#startup-problems)
- [Screen Scraping Issues](#screen-scraping-issues)
- [GUI Problems](#gui-problems)
- [Database Issues](#database-issues)
- [Performance Problems](#performance-problems)
- [Chrome DevTools Issues](#chrome-devtools-issues)
- [Network & Connectivity](#network--connectivity)
- [Error Messages Reference](#error-messages-reference)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

### Run System Health Check

```bash
# Check all components via API
curl http://localhost:5001/api/system/health | python3 -m json.tool

# Check backend only
curl http://localhost:5001/health

# View health dashboard
# Open http://localhost:3000/system-status in browser
```

### View Logs

```bash
# Tail live logs
tail -f logs/pokertool.log

# View last 100 lines
tail -n 100 logs/pokertool.log

# Search for errors
grep -i error logs/pokertool.log

# Check startup logs
cat startup.log
```

### Verify Installation

```bash
# Check Python dependencies
.venv/bin/pip list

# Check Node dependencies
cd pokertool-frontend && npm list --depth=0

# Verify versions
python3 --version  # Should be 3.12+
node --version     # Should be 18+
npm --version
```

---

## Common Issues (Updated October 2025)

### Problem: Health check shows "API server failing"

**Symptoms**: `/api/system/health` shows API server status as "failing"

**Cause**: Health checker configured for wrong port (8000 instead of 5001)

**Solution**:
```bash
# Fixed in v88.5.1+
# If on older version, update system_health_checker.py:
# Change POKERTOOL_PORT from '8000' to '5001'

# Restart app to apply
python restart.py
```

### Problem: Dependency conflict with numpy and opencv-python

**Symptoms**:
```
opencv-python 4.12.0.88 requires numpy>=2, but you have numpy 1.26.4
```

**Solution**:
```bash
# Update numpy to 2.x (fixed in requirements.txt v88.5.1+)
.venv/bin/pip install "numpy>=2.0.0,<2.3.0"

# Or clean reinstall
python restart.py --kill-only
rm -rf .venv
python start.py --setup-only
python restart.py
```

### Problem: Port already in use after crash

**Symptoms**: `Address already in use` when starting app

**Solution**:
```bash
# Use restart script (automatic cleanup)
python restart.py

# Or manual cleanup
lsof -ti:5001 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Or kill all pokertool processes
python scripts/kill.py
```

---

## Installation Issues

### Problem: `pip install` fails

**Symptoms**: Error during `pip install -r requirements.txt`

**Solutions**:

1. **Update pip**:
   ```bash
   python3 -m pip install --upgrade pip
   ```

2. **Install system dependencies** (macOS):
   ```bash
   brew install python@3.13 tesseract opencv
   ```

3. **Install system dependencies** (Ubuntu/Debian):
   ```bash
   sudo apt-get install python3-dev tesseract-ocr libopencv-dev
   ```

4. **Use virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

### Problem: OpenCV import error

**Symptoms**: `ImportError: dlopen(...cv2.abi3.so...): Library not loaded: libavif`

**Solutions**:

1. **Reinstall opencv-python**:
   ```bash
   .venv/bin/pip uninstall opencv-python opencv-python-headless
   .venv/bin/pip install opencv-python-headless==4.8.1.78
   ```

2. **Install via Homebrew** (macOS):
   ```bash
   brew install opencv
   ```

3. **Run fix script**:
   ```bash
   chmod +x fix_opencv.sh
   ./fix_opencv.sh
   ```

### Problem: Tesseract not found

**Symptoms**: `TesseractNotFoundError`

**Solutions**:

1. **Install Tesseract** (macOS):
   ```bash
   brew install tesseract
   ```

2. **Install Tesseract** (Ubuntu):
   ```bash
   sudo apt-get install tesseract-ocr
   ```

3. **Set Tesseract path in `.env`**:
   ```bash
   TESSERACT_PATH=/usr/local/bin/tesseract
   ```

---

## Startup Problems

### Problem: `start.py` fails immediately

**Symptoms**: Application exits right after starting

**Diagnostic Steps**:

1. **Check logs**:
   ```bash
   python3 start.py 2>&1 | tee startup.log
   cat startup.log
   ```

2. **Verify ports are free**:
   ```bash
   # Check if port 5001 is in use
   lsof -i :5001

   # Check if port 3000 is in use
   lsof -i :3000
   ```

3. **Kill conflicting processes**:
   ```bash
   # Kill processes on port 5001
   kill $(lsof -t -i:5001)

   # Or use the cleanup script
   python3 src/pokertool/kill.py --force
   ```

4. **Check database connection**:
   ```bash
   # Test PostgreSQL connection
   psql -h localhost -U postgres -d pokertool
   ```

**Solutions**:

- Ensure `.env` file exists with required variables
- Verify database is running: `pg_ctl status`
- Check Python version: `python3 --version` (need 3.12+)

### Problem: Backend starts but frontend doesn't load

**Symptoms**: API responds but React app shows blank page

**Solutions**:

1. **Install frontend dependencies**:
   ```bash
   cd pokertool-frontend
   npm install
   cd ..
   ```

2. **Clear Node modules cache**:
   ```bash
   cd pokertool-frontend
   rm -rf node_modules package-lock.json
   npm install
   cd ..
   ```

3. **Check Node version**:
   ```bash
   node --version  # Should be 18.x or higher
   nvm use 18  # If using nvm
   ```

4. **Rebuild with clean cache**:
   ```bash
   cd pokertool-frontend
   npm run build --clean
   ```

---

## Screen Scraping Issues

### Problem: No tables detected

**Symptoms**: "No poker tables found" message

**Diagnostic Steps**:

1. **Verify table is visible**:
   - Ensure poker table window is not minimized
   - Check table is not covered by other windows
   - Verify table is on primary monitor

2. **Check screen permissions** (macOS):
   ```bash
   # Grant screen recording permission to Terminal/iTerm
   # System Preferences > Security & Privacy > Privacy > Screen Recording
   ```

3. **Test screen capture**:
   ```python
   import mss
   with mss.mss() as sct:
       screenshot = sct.grab(sct.monitors[0])
       print(f"Screenshot captured: {screenshot.size}")
   ```

**Solutions**:

- **Update ROI coordinates**: Test image may not match your screen resolution
- **Adjust detection threshold**: Lower confidence threshold in settings
- **Verify Betfair UI**: Ensure using standard Betfair poker client (not mobile app)

### Problem: Incorrect data extracted

**Symptoms**: Wrong player names, incorrect stacks, misread cards

**Solutions**:

1. **Improve image quality**:
   - Increase poker client window size
   - Ensure good lighting/contrast
   - Disable poker client animations

2. **Retrain OCR**:
   ```bash
   python3 scripts/calibrate_ocr.py --table-type betfair
   ```

3. **Update scraper module**:
   ```bash
   git pull origin develop
   pip install -r requirements.txt
   ```

4. **Enable debug mode**:
   ```bash
   # In .env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

   Check `logs/pokertool.log` for detailed OCR output.

### Problem: Scraper freezes or crashes

**Symptoms**: Application stops responding during scraping

**Solutions**:

1. **Reduce scraper workers**:
   ```bash
   # In .env
   SCRAPER_WORKERS=10  # Reduce from 20
   ```

2. **Increase timeout values**:
   ```bash
   # In .env
   OCR_TIMEOUT=10  # Increase from 5
   ```

3. **Clear image cache**:
   ```bash
   rm -rf ~/.pokertool/cache/images/*
   ```

4. **Monitor memory usage**:
   ```bash
   # While running
   ps aux | grep python | grep pokertool
   ```

---

## GUI Problems

### Problem: GUI window doesn't appear

**Symptoms**: Application runs but no GUI window shown

**Solutions**:

1. **Check tkinter installation**:
   ```python
   import tkinter
   tkinter._test()  # Should show a window
   ```

2. **Install tkinter** (Ubuntu):
   ```bash
   sudo apt-get install python3-tk
   ```

3. **Run GUI directly**:
   ```bash
   PYTHONPATH=src python3 src/pokertool/compact_live_advice_window.py
   ```

4. **Check display**:
   ```bash
   echo $DISPLAY  # Should show :0 or similar
   ```

### Problem: Status window click doesn't work (macOS)

**Symptoms**: Clicking dock icon doesn't show status window

**Solutions**:

1. **Install PyObjC**:
   ```bash
   .venv/bin/pip install pyobjc-framework-Cocoa
   ```

2. **Grant accessibility permissions**:
   - System Preferences > Security & Privacy > Privacy > Accessibility
   - Add Terminal/iTerm/Python

3. **Check process**:
   ```bash
   ps aux | grep "python.*start.py"
   ```

### Problem: GUI is laggy/unresponsive

**Symptoms**: Slow updates, freezing, high CPU usage

**Solutions**:

1. **Reduce GUI update frequency**:
   ```bash
   # In .env
   GUI_UPDATE_INTERVAL=1000  # Increase from 500ms
   ```

2. **Disable animations**:
   ```bash
   # In pokertool settings
   DISABLE_ANIMATIONS=true
   ```

3. **Close other applications**: Free up system resources

4. **Reduce OCR strategies**:
   ```bash
   # In .env
   OCR_MAX_STRATEGIES=2  # Reduce from 3
   ```

---

## Database Issues

### Problem: Database connection refused

**Symptoms**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:

1. **Start PostgreSQL**:
   ```bash
   # macOS (Homebrew)
   brew services start postgresql@14

   # Ubuntu
   sudo systemctl start postgresql

   # Check status
   pg_ctl status
   ```

2. **Verify connection string**:
   ```bash
   # In .env
   DATABASE_URL=postgresql://user:password@localhost:5432/pokertool
   ```

3. **Create database**:
   ```bash
   createdb pokertool
   # Or
   psql -c "CREATE DATABASE pokertool;"
   ```

4. **Check PostgreSQL logs**:
   ```bash
   # macOS
   tail -f /usr/local/var/log/postgres.log

   # Ubuntu
   tail -f /var/log/postgresql/postgresql-14-main.log
   ```

### Problem: Migration fails

**Symptoms**: `alembic upgrade head` fails

**Solutions**:

1. **Check current revision**:
   ```bash
   alembic current
   ```

2. **Rollback and retry**:
   ```bash
   alembic downgrade -1
   alembic upgrade head
   ```

3. **Reset database** (WARNING: loses data):
   ```bash
   dropdb pokertool
   createdb pokertool
   alembic upgrade head
   ```

4. **Check migration files**:
   ```bash
   ls -la alembic/versions/
   ```

### Problem: Slow database queries

**Symptoms**: Application slow, high database CPU

**Solutions**:

1. **Add missing indexes**:
   ```sql
   -- Check missing indexes
   SELECT schemaname, tablename, attname
   FROM pg_stats
   WHERE tablename = 'hands'
   AND n_distinct > 100
   ORDER BY n_distinct DESC;
   ```

2. **Analyze tables**:
   ```sql
   ANALYZE hands;
   ANALYZE players;
   ```

3. **Vacuum database**:
   ```bash
   vacuumdb --analyze --verbose pokertool
   ```

4. **Increase connection pool**:
   ```bash
   # In .env
   DB_POOL_SIZE=30  # Increase from 20
   ```

---

## Performance Problems

### Problem: High CPU usage

**Symptoms**: CPU at 100%, fan spinning loudly

**Solutions**:

1. **Reduce parallel workers**:
   ```bash
   # In .env
   SCRAPER_WORKERS=10
   ```

2. **Limit OCR strategies**:
   ```bash
   OCR_MAX_STRATEGIES=2
   ```

3. **Increase update intervals**:
   ```bash
   GUI_UPDATE_INTERVAL=1000
   STATE_UPDATE_INTERVAL=2000
   ```

4. **Profile performance**:
   ```bash
   python3 -m cProfile -o profile.stats start.py
   python3 -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
   ```

### Problem: High memory usage

**Symptoms**: Memory growing over time, eventual crash

**Solutions**:

1. **Clear image cache**:
   ```bash
   rm -rf ~/.pokertool/cache/*
   ```

2. **Reduce cache sizes**:
   ```bash
   # In .env
   IMAGE_HASH_CACHE_SIZE=500  # Reduce from 1000
   STATE_QUEUE_SIZE=3  # Reduce from 5
   ```

3. **Monitor memory**:
   ```bash
   # Real-time monitoring
   watch -n 1 'ps aux | grep python | grep pokertool'
   ```

4. **Restart periodically**: Set up automatic restart every 24 hours

---

## Chrome DevTools Issues

### Problem: Chrome connection timeout

**Symptoms**: `TimeoutError: Could not connect to Chrome DevTools`

**Solutions**:

1. **Launch Chrome manually**:
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --user-data-dir=~/.pokertool/chrome-debug-profile
   ```

2. **Check Chrome is running**:
   ```bash
   ps aux | grep Chrome | grep remote-debugging
   ```

3. **Verify port is open**:
   ```bash
   curl http://localhost:9222/json
   ```

4. **Change debug port**:
   ```bash
   # In .env
   CHROME_DEVTOOLS_PORT=9223  # Try different port
   ```

5. **Disable auto-launch**:
   ```bash
   # In .env
   CHROME_AUTO_LAUNCH=false
   ```
   Then launch Chrome manually before starting PokerTool.

### Problem: Chrome tabs not detected

**Symptoms**: "No poker tabs found"

**Solutions**:

1. **Open Betfair poker in Chrome**: Navigate to poker table

2. **Check tab URL**:
   ```bash
   curl http://localhost:9222/json | python3 -m json.tool
   ```

3. **Refresh Chrome connection**:
   - Close and reopen poker tab
   - Restart Chrome with debugging enabled

---

## Network & Connectivity

### Problem: CORS errors

**Symptoms**: `Access-Control-Allow-Origin` errors in browser console

**Solutions**:

1. **Update CORS origins**:
   ```bash
   # In .env
   CORS_ORIGINS=http://localhost:3000,http://localhost:5001
   ```

2. **Restart backend** after changing CORS settings

3. **Check frontend API URL**:
   ```bash
   # In .env
   REACT_APP_API_URL=http://localhost:5001
   ```

### Problem: WebSocket connection failed

**Symptoms**: Real-time updates not working

**Solutions**:

1. **Check WebSocket URL**:
   ```bash
   # In .env
   REACT_APP_WS_URL=ws://localhost:5001/ws
   ```

2. **Test WebSocket manually**:
   ```javascript
   // In browser console
   const ws = new WebSocket('ws://localhost:5001/ws');
   ws.onopen = () => console.log('Connected');
   ws.onerror = (e) => console.error('Error:', e);
   ```

3. **Check firewall**: Ensure ports 5001 and 3000 are not blocked

---

## Error Messages Reference

### `ModuleNotFoundError: No module named 'pokertool'`

**Fix**: Run from project root with `PYTHONPATH=src`:
```bash
PYTHONPATH=src python3 start.py
```

### `tkinter.TclError: no display name and no $DISPLAY environment variable`

**Fix**: Set DISPLAY or use headless mode:
```bash
export DISPLAY=:0
# Or
python3 start.py --headless
```

### `PermissionError: [Errno 13] Permission denied`

**Fix**: Check file permissions:
```bash
chmod +x start.py
chmod -R 755 src/
```

### `FileNotFoundError: [Errno 2] No such file or directory: '.env'`

**Fix**: Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your settings
```

---

## Getting Help

### Before Asking for Help

1. **Check logs**: `cat logs/pokertool.log`
2. **Run diagnostics**: `python3 scripts/health_check.py`
3. **Search issues**: https://github.com/gmanldn/pokertool/issues
4. **Review documentation**: All docs in `docs/` folder

### Reporting Bugs

Include the following in your bug report:

```bash
# 1. PokerTool version
git describe --tags

# 2. System information
uname -a
python3 --version
node --version

# 3. Last 50 log lines
tail -n 50 logs/pokertool.log

# 4. Health check output
python3 scripts/health_check.py

# 5. Steps to reproduce the issue

# 6. Expected vs actual behavior
```

### Community Support

- **GitHub Issues**: https://github.com/gmanldn/pokertool/issues
- **Discussions**: https://github.com/gmanldn/pokertool/discussions
- **Discord**: [Join our server](https://discord.gg/pokertool)

### Professional Support

For enterprise support, contact: support@pokertool.com

---

## Advanced Troubleshooting

### Enable Debug Logging

```python
# In start.py or any module
import logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

### Capture Network Traffic

```bash
# Using tcpdump
sudo tcpdump -i any -w pokertool_traffic.pcap port 5001 or port 3000

# Analyze with Wireshark
wireshark pokertool_traffic.pcap
```

### Profile Memory Usage

```bash
# Install memory_profiler
pip install memory_profiler

# Profile specific function
python3 -m memory_profiler start.py
```

### Trace System Calls

```bash
# macOS
sudo dtruss -p $(pgrep -f "python.*start.py")

# Linux
strace -p $(pgrep -f "python.*start.py")
```

---

**Last Updated**: 2025-10-17
**Version**: 1.0.0
