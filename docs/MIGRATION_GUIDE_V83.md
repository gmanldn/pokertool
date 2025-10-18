# Migration Guide: v82 to v83 - Web-Only Architecture
> Issue Register: Use `python new_task.py` to append GUID-tagged entries to `docs/TODO.md`; manual edits are rejected and historical backlog lives in `docs/TODO_ARCHIVE.md`.

**Document Version:** 1.0  
**Last Updated:** October 15, 2025  
**Target Audience:** Existing PokerTool users upgrading from GUI versions

---

## Overview

PokerTool v83.0.0 represents a major architectural shift from a desktop GUI application to a modern web-based platform. This guide will help you transition smoothly to the new version.

---

## What Changed

### Removed Features
- ❌ **Tkinter Desktop GUI** - All desktop GUI components removed
- ❌ **GUI Launch Scripts** - Scripts like `launch_gui.py` no longer exist
- ❌ **GUI Test Files** - Desktop GUI tests removed
- ❌ **Tkinter Dependencies** - No longer requires tkinter or customtkinter

### Added Features
- ✅ **React Web Interface** - Modern, responsive web application
- ✅ **WebSocket Real-time Updates** - Instant synchronization vs polling
- ✅ **Mobile Support** - Works on phones and tablets
- ✅ **Remote Access** - Access from any device on your network
- ✅ **Redux State Management** - Better state handling and persistence
- ✅ **Progressive Web App** - Install as a native-like application

---

## Migration Steps

### Step 1: Update Your Installation

```bash
# Pull the latest changes
cd /path/to/pokertool
git pull origin develop

# Or checkout the release branch
git checkout release/v83.0.0

# Update Python dependencies
pip install -r requirements.txt

# Install/update frontend dependencies
cd pokertool-frontend
npm install
cd ..
```

### Step 2: Remove Old Launch Methods

**Before (v82 and earlier):**
```bash
python scripts/start.py --launch
python scripts/launch_gui.py
python tests/test_gui.py
```

**After (v83):**
```bash
python -m pokertool web
# or
pokertool web
```

### Step 3: Access the Web Interface

Once launched, open your browser to:
- **Local:** http://localhost:5000
- **Network:** http://your-ip:5000

The web interface will automatically open in your default browser when you run `pokertool web`.

---

## Feature Parity Matrix

All features from the desktop GUI are available in the web interface:

| Feature | Desktop GUI (v82) | Web Interface (v83) | Notes |
|---------|-------------------|---------------------|-------|
| Real-time Poker Advice | ✅ | ✅ | Now via WebSocket |
| Hand Analysis | ✅ | ✅ | Enhanced visualization |
| Session Tracking | ✅ | ✅ | Better charts |
| Opponent Modeling | ✅ | ✅ | Same functionality |
| Settings Management | ✅ | ✅ | Web-based UI |
| Screen Scraping | ✅ | ✅ | Desktop-independent |
| Multi-table Support | ✅ | ✅ | Improved management |
| Hand History | ✅ | ✅ | Better search/filter |
| **Mobile Access** | ❌ | ✅ | New! |
| **Remote Access** | ❌ | ✅ | New! |
| **Real-time Sync** | Polling | WebSocket | Improved! |

---

## Common Migration Issues

### Issue 1: "Module 'tkinter' not found" Errors

**Problem:** Old scripts or code trying to import tkinter.

**Solution:** 
- Update to v83.0.0 completely
- Remove any custom scripts that import GUI modules
- Use the new web interface instead

### Issue 2: Cannot Launch GUI

**Problem:** Old launch commands don't work.

**Solution:**
```bash
# Old command (won't work):
python scripts/launch_gui.py

# New command:
python -m pokertool web
```

### Issue 3: Screen Scraper Not Working

**Problem:** Screen scraper functionality seems missing.

**Solution:**
The screen scraper is still available and works the same way:

```bash
# Via web interface (recommended)
python -m pokertool web
# Then enable scraper in Settings

# Headless mode
python -m pokertool scrape
```

### Issue 4: Missing Configuration

**Problem:** Previous GUI settings not carried over.

**Solution:**
Configuration files are still used. Your existing `poker_config.json` will be loaded automatically. The web interface provides a Settings page to modify configuration.

---

## New Web Interface Features

### 1. Real-time WebSocket Updates

Instead of polling every second, the web interface receives instant updates via WebSocket:

- Table state changes appear immediately
- Advice updates in real-time
- No more 1-second lag

### 2. Mobile Responsive Design

Access PokerTool from your phone or tablet:

- Touch-optimized controls
- Responsive layout adapts to screen size
- Bottom navigation on mobile
- Swipe gestures supported

### 3. Remote Access

Run PokerTool on one computer, access from others:

```bash
# On your main computer
python -m pokertool web

# On your phone/tablet (same network)
# Open browser to: http://192.168.1.x:5000
```

### 4. Progressive Web App (PWA)

Install the web interface as a standalone app:

1. Open http://localhost:5000 in Chrome/Edge
2. Click the install icon in the address bar
3. Launch like a native app

### 5. Better State Management

- Redux-based state management
- Automatic persistence to localStorage
- Undo/redo capability (coming soon)
- Better error recovery

---

## API Changes for Developers

If you've built custom integrations:

### REST API Endpoints

The web interface communicates with the backend via REST API:

```python
# Game state
GET /api/game-state

# Get advice
POST /api/advice
{
  "hand": ["As", "Kh"],
  "board": ["Qd", "Jc", "Ts"],
  "position": "BTN",
  "pot": 100,
  "to_call": 10
}

# Session stats
GET /api/session

# Settings
GET /api/settings
PUT /api/settings
```

### WebSocket Events

Real-time updates via Socket.IO:

```javascript
// Client-side example
socket.on('table_state_update', (data) => {
  console.log('Table state changed:', data);
});

socket.on('advice_update', (advice) => {
  console.log('New advice:', advice);
});
```

---

## Performance Comparison

| Metric | Desktop GUI (v82) | Web Interface (v83) |
|--------|-------------------|---------------------|
| Startup Time | ~5 seconds | ~2 seconds |
| Update Latency | 1000ms (polling) | <50ms (WebSocket) |
| Memory Usage | 300-500MB | 200-400MB |
| Mobile Support | No | Yes |
| Remote Access | No | Yes |

---

## Troubleshooting

### Web Interface Won't Start

```bash
# Check if port 5000 is available
lsof -i :5000

# Try a different port
PORT=8080 python -m pokertool web

# Check dependencies
python src/pokertool/dependency_manager.py
```

### WebSocket Connection Failed

**Check firewall settings:**
- Ensure port 5000 (or your chosen port) is open
- Allow incoming connections for Python

**Check browser console:**
- Open Developer Tools (F12)
- Look for WebSocket connection errors
- Verify the URL matches your server

### Frontend Not Loading

```bash
# Rebuild frontend
cd pokertool-frontend
npm run build
cd ..

# Restart server
python -m pokertool web
```

---

## Rollback Instructions

If you need to temporarily revert to v82:

```bash
# Checkout previous version
git checkout v82.0.0

# Reinstall dependencies
pip install -r requirements.txt

# Launch old GUI
python scripts/launch_gui.py
```

**Note:** We recommend staying on v83+ for continued updates and support.

---

## Getting Help

### Documentation
- **README.md** - Updated for v83
- **docs/TKINTER_REMOVAL_TODO.md** - Complete technical details
- **docs/API_DOCUMENTATION.md** - API reference (if available)

### Reporting Issues

```bash
# Create an issue on GitHub
# Include:
# - Your OS and Python version
# - Error messages
# - Steps to reproduce
```

### Community Support

- GitHub Issues: https://github.com/gmanldn/pokertool/issues
- Check existing issues for similar problems
- Provide detailed information for faster resolution

---

## FAQ

### Q: Why was the GUI removed?

**A:** The web interface provides:
- Better cross-platform compatibility
- Mobile device support
- Remote access capability
- Easier maintenance and updates
- Modern UI/UX patterns

### Q: Can I still use PokerTool offline?

**A:** Yes! The web interface runs locally on your machine. You don't need an internet connection. Only the browser and local server are used.

### Q: Will my old data be preserved?

**A:** Yes! All your:
- Hand history
- Session data
- Configuration files
- Opponent models

...are preserved and will work with v83.

### Q: What about privacy?

**A:** The web interface runs locally on your machine. No data is sent to external servers unless you explicitly configure external integrations.

### Q: Can I customize the web interface?

**A:** Yes! The React frontend is fully customizable:

```bash
cd pokertool-frontend/src
# Edit components, styles, etc.
npm start  # Development server
npm run build  # Production build
```

### Q: Does this work on Linux/Windows?

**A:** Yes! The web interface works on all platforms:
- ✅ macOS 10.15+
- ✅ Linux (Ubuntu, Fedora, etc.)
- ✅ Windows 10/11
- ✅ Any device with a modern browser

---

## Next Steps

1. ✅ Install v83.0.0
2. ✅ Launch web interface: `python -m pokertool web`
3. ✅ Explore the new features
4. ✅ Configure settings via web UI
5. ✅ Try mobile access
6. ✅ Enjoy improved performance!

---

## Feedback

We value your feedback on the new web interface:

- **What you like:** Let us know what works well
- **What needs improvement:** Help us prioritize features
- **Bug reports:** Report any issues you encounter
- **Feature requests:** Suggest new capabilities

**Thank you for using PokerTool!** 🎉

---

**Document Version:** 1.0  
**Last Updated:** October 15, 2025  
**Applies to:** PokerTool v83.0.0 and later
