# PokerTool Enhanced GUI - Blade (Tab) System Documentation
> Issue Register: Use `python new_task.py` to append GUID-tagged entries to `docs/TODO.md`; manual edits are rejected and historical backlog lives in `docs/TODO_ARCHIVE.md`.

## Overview

The Enhanced GUI uses a blade-based architecture where each functional area is organized into distinct tabs (referred to as "blades" in UI terminology). This document covers the tab system's functionality, visibility requirements, and troubleshooting.

## Tab Architecture

### Core Components

#### 1. Notebook Tab Container (`ttk.Notebook`)

- Main container for all functional blades
- Configured with high-contrast styling for maximum visibility
- Supports dynamic tab addition/removal

#### 2. Tab Visibility Configuration

The tab visibility is controlled through TTK styling in `_setup_styles()`:

```python
# Explicitly configure Notebook tab styling to ensure visibility
style.configure('TNotebook', background=COLORS['bg_dark'])
style.configure(
    'TNotebook.Tab',
    background=COLORS['bg_medium'],     # Visible background
    foreground=COLORS['text_primary'],   # High-contrast text
    padding=[12, 6],                      # Adequate spacing
)
style.map(
    'TNotebook.Tab',
    background=[('selected', COLORS['bg_dark']), ('!selected', COLORS['bg_medium'])],
    foreground=[('selected', COLORS['accent_primary']), ('!selected', COLORS['text_primary'])],
)
```

#### 3. Color Scheme

**Unselected Tabs:**

- Background: `#2a3142` (medium gray-blue)
- Foreground: `#ffffff` (white text)

**Selected Tabs:**

- Background: `#1a1f2e` (dark background)
- Foreground: `#4a9eff` (bright blue accent)

**Padding:** 12px horizontal, 6px vertical for comfortable click targets

## Available Blades (Tabs)

### Required Blades (Always Visible)

1. **Autopilot** - Primary control center
   - Auto-start capabilities
   - Screen scraper integration
   - Table monitoring
   - Quick action buttons

2. **Manual Play** - Manual game interface
   - Card selection
   - Table visualization
   - Position controls
   - Analysis tools

3. **Analysis** - Hand analysis and statistics
   - Historical hand review
   - Statistical analysis
   - Performance metrics

4. **Settings** - Configuration and preferences
   - Localization settings
   - Theme customization
   - Advanced options

### Optional Blades (Conditionally Visible)

5. **Coaching** - Available when `CoachingSystem` is initialized
   - Real-time coaching advice
   - Training scenarios
   - Progress tracking

6. **Analytics** - Available when `AnalyticsDashboard` is initialized
   - Usage metrics
   - Session tracking
   - Performance analytics

7. **Gamification** - Available when `GamificationEngine` is initialized
   - Experience points
   - Achievement system
   - Leaderboards

8. **Community** - Available when `CommunityPlatform` is initialized
   - Forum posts
   - Challenges
   - Tournaments
   - Knowledge articles

## Auto-Start Features

### Background Services

The Enhanced GUI automatically starts critical background services on launch:

```python
# Auto-started after 100ms delay for thread-safety
self.after(100, self._start_background_services_safely)
```

#### Services Started Automatically:

1. **Enhanced Screen Scraper**
   - Continuous poker table monitoring
   - OCR-based card recognition
   - Real-time state updates
   - Automatic calibration

2. **Screen Update Loop**
   - Continuous display updates
   - Live scraper status
   - Recognition statistics
   - Table detection feedback

3. **Table Manager** (if available)
   - Multi-table tracking
   - Priority management
   - Focus automation

## Visibility Troubleshooting

### Problem: Tabs Not Visible

**Symptoms:**

- Blank notebook area
- Tabs present but invisible
- No text or clickable areas

**Root Cause:**

- Missing TTK style configuration
- Theme incompatibility
- Color contrast issues

**Solution Applied:**

- Explicit `style.configure()` calls with contrasting colors
- Platform-specific theme selection (aqua for macOS, clam for others)
- `style.map()` for selected/unselected states
- Increased padding for better visibility

### Problem: Scraper Not Auto-Starting

**Symptoms:**

- "Screen scraper not started" message
- Red scraper button indicator
- No table detection

**Root Causes:**

1. Missing dependencies (opencv-python, Pillow, pytesseract, mss)
2. Import failures for scraper modules
3. Thread-safety issues in startup sequence

**Solutions Applied:**

1. Auto-install missing dependencies via `_ensure_scraper_dependencies()`
2. Delayed background service start via `self.after(100, ...)`
3. Thread-safe widget updates using `self.after(0, lambda: ...)`
4. Comprehensive error logging and user feedback

## Testing

### Visual Test
Run the GUI and verify all tabs are visible:
```bash
python -m pokertool.enhanced_gui
```

**Expected Result:**

- All tabs clearly visible with distinct colors
- Selected tab highlighted in blue
- Clickable tab labels
- Smooth tab switching

### Style Configuration Test
```bash
pytest tests/gui/test_enhanced_gui_styles.py
```

**What It Tests:**

- TTK style configuration correctness
- Color application
- Padding values
- Style mapping for selection states

## Thread Safety

### GUI Update Guidelines

**DO:**

- Use `self.after(0, lambda: update_widget())` from background threads
- Schedule all widget modifications on the main thread
- Use daemon threads for background tasks

**DON'T:**

- Directly update widgets from worker threads
- Call Tk methods without `after()` from threads
- Block the main thread with long operations

### Example: Thread-Safe Update

```python
def _background_worker(self):
    while self.running:
        data = self.get_data()
        # Schedule update on main thread
        self.after(0, lambda d=data: self._update_display(d))
        time.sleep(1)
```

## Error Handling

### Fallback Tab Content

When a tab fails to load, the system automatically creates fallback content:

- Error description
- Diagnostic information
- Retry button
- System status display

### Diagnostic Window

Click "Show Diagnostics" on any failed tab to view:

- Module load status
- Available systems
- Python version
- Platform information
- Detailed error messages

## Performance Considerations

### Optimization Strategies

1. **Lazy Tab Building**
   - Tabs built only when notebook is created
   - Content constructed on-demand
   - Resources released on tab switch

2. **Async Background Services**
   - Screen scraper runs in separate thread
   - Non-blocking UI updates
   - Queued state processing

3. **Update Throttling**
   - Screen updates every 5 seconds (configurable)
   - Deduplication of identical states
   - Batched widget updates

## Configuration

### Customization Options

Users can customize blade behavior through Settings tab:

- **Auto-start Screen Scraper**: Enable/disable automatic scraper startup
- **Continuous Updates**: Control update frequency
- **Auto-detect Tables**: Automatic table detection on startup
- **Auto GTO Analysis**: Automatic analysis when tables detected

## Maintenance

### Adding New Blades

1. Create tab configuration in `tabs_config` list
2. Implement `_build_<name>_tab(self, parent)` method
3. Add conditional logic if tab is optional
4. Register translation keys
5. Add fallback error handling

### Modifying Tab Styles

Edit `_setup_styles()` method:

- Adjust colors in style.configure()
- Modify padding values
- Update style.map() for state changes

## Known Issues & Solutions

### Issue: Tabs Invisible on Some Platforms

**Fix:** Explicit style configuration (applied in v20.1.0)

### Issue: Scraper Won't Auto-Start

**Fix:** Thread-safe delayed startup (applied in v20.1.0)

### Issue: Widget Updates from Threads Crash

**Fix:** Use `self.after()` for all thread-initiated updates

## Version History

- **v20.1.0** (2025-10-08): Fixed tab visibility, guaranteed auto-start
- **v20.0.0** (2025-09-30): Auto-start scraper, continuous updates
- **v19.0.0** (2025-09-18): Enhanced error handling
- **v18.0.0** (2025-09-15): Initial blade architecture

## Related Files

- `src/pokertool/enhanced_gui.py` - Main GUI implementation
- `src/pokertool/enhanced_gui_components/style.py` - Color/font definitions
- `src/pokertool/enhanced_gui_components/autopilot_panel.py` - Autopilot blade
- `src/pokertool/enhanced_gui_components/manual_section.py` - Manual play blade
- `src/pokertool/enhanced_gui_components/settings_section.py` - Settings blade
- `src/pokertool/enhanced_gui_components/coaching_section.py` - Coaching blade
- `tests/gui/test_enhanced_gui_styles.py` - Style configuration tests

## Support

For issues with blade visibility or functionality:

1. Check console output for error messages
2. Run diagnostic tool: Click "Show Diagnostics" on failed tabs
3. Verify dependencies: `python -m pokertool.dependency_manager`
4. Run tests: `pytest tests/gui/test_enhanced_gui_styles.py`
5. Review startup log: `startup_log.txt`
