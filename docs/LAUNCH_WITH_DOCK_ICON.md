# Launching PokerTool API with Dock Icon

The PokerTool API can be launched with a visible macOS dock icon for easier management.

## Quick Start

```bash
.venv/bin/python scripts/launch_api_simple.py
```

This will:
- Start the API server on http://localhost:5001
- Display a dock icon with the PokerTool logo
- Show the app in the macOS dock so you can easily see it's running
- Allow you to quit the server from the dock (Cmd+Q) or with Ctrl+C

## Features

- **Visible Dock Presence**: The API server appears in the macOS dock with a custom icon
- **Easy to Quit**: Close from dock or press Ctrl+C in the terminal
- **Server Output**: All API logs are displayed in the terminal
- **Custom Icon**: Uses the PokerTool green poker chip icon (assets/pokertool-icon.png)

## Icon Creation

The dock icon was created using `scripts/create_app_icon.py`:

```bash
.venv/bin/python scripts/create_app_icon.py
```

This generates a 512x512 PNG icon at `assets/pokertool-icon.png` featuring:
- Green poker chip design
- "PT" text for PokerTool
- Professional appearance in the dock

## Files

- `scripts/launch_api_simple.py` - Main launcher script with dock icon support
- `scripts/create_app_icon.py` - Icon generation script
- `assets/pokertool-icon.png` - The application icon (512x512 PNG)

## Technical Details

The launcher uses PyObjC's NSApplication framework to:
1. Create an NSApplication instance
2. Set activation policy to `NSApplicationActivationPolicyRegular` (shows in dock)
3. Load and set the custom icon image
4. Spawn uvicorn as a subprocess
5. Handle cleanup on quit

## Alternative Launch Methods

If you don't need a dock icon, you can still use the standard method:

```bash
PYTHONPATH=src .venv/bin/python -m uvicorn pokertool.api:create_app --host 0.0.0.0 --port 5001 --factory
```

## Requirements

- PyObjC (included in requirements: `pyobjc-framework-Quartz`)
- macOS (dock icon feature is Mac-specific)
- Python 3.8+

## Troubleshooting

**Issue**: Dock icon doesn't appear
- Ensure you're running on macOS
- Verify PyObjC is installed: `.venv/bin/pip list | grep pyobjc`
- Check that Python is using Python.app framework

**Issue**: Icon looks wrong
- Regenerate the icon: `.venv/bin/python scripts/create_app_icon.py`
- Verify icon exists: `ls -lh assets/pokertool-icon.png`

**Issue**: Server won't start
- Check port 5001 isn't already in use: `lsof -i :5001`
- Kill existing processes: `pkill -f "uvicorn pokertool.api"`
