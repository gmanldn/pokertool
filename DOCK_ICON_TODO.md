# macOS Dock Icon Implementation - 25 TODO Tasks

## Executive Summary

The dock icon currently doesn't reliably appear on macOS. **The guarantee must be:**
- **If app is running → dock icon MUST be visible**
- **If dock icon is NOT visible → app must NOT be running**
- **Clicking dock icon → shows diagnostic dashboard (health, tables, logs)**

This document outlines 25 critical TODO tasks with comprehensive unit tests to ensure reliable dock icon behavior and prevent regression.

---

## Phase 1: Dock Icon Visibility Guarantee (Tasks 1-7) - CRITICAL

### TODO 1: Ensure NSApplicationActivationPolicyRegular Set FIRST
**File:** `start.py`
**Lines:** 149-154
**Priority:** CRITICAL
**Issue:** Activation policy may not be set before other operations
**Fix:** Move `app.setActivationPolicy_(NSApplicationActivationPolicyRegular)` to line 150, immediately after `NSApplication.sharedApplication()`
**Test:** `tests/test_dock_icon_visibility.py::test_activation_policy_set_first`
**Expected:** No other NSApplication calls before activation policy
```python
# Current: Lines 149-154
app = NSApplication.sharedApplication()
# ... other code ...
app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

# After fix: Should be
app = NSApplication.sharedApplication()
app.setActivationPolicy_(NSApplicationActivationPolicyRegular)  # FIRST!
# ... other code ...
```

---

### TODO 2: Verify Activation Policy Actually Set
**File:** `start.py`
**Lines:** 157-159
**Priority:** CRITICAL
**Issue:** Current verification exists but doesn't fail if policy not set
**Fix:** If policy != Regular, raise exception and log error
**Test:** `tests/test_dock_icon_visibility.py::test_activation_policy_verification_fails`
**Expected:** Exception raised if policy verification fails
```python
# After fix:
current_policy = app.activationPolicy()
if current_policy != NSApplicationActivationPolicyRegular:
    raise RuntimeError(f"Failed to set activation policy. Got {current_policy}")
```

---

### TODO 3: Call activateIgnoringOtherApps AFTER Delegate Set
**File:** `start.py`
**Lines:** 162-179
**Priority:** CRITICAL
**Issue:** Activation might happen before delegate is installed
**Fix:** Ensure delegate is set before `app.activateIgnoringOtherApps_(True)` is called
**Test:** `tests/test_dock_icon_visibility.py::test_activate_after_delegate`
**Expected:** Delegate set before activation call
```python
# Correct order:
1. app.setActivationPolicy_(Regular)
2. delegate = AppDelegate.alloc().init()
3. app.setDelegate_(delegate)  # MUST be before activate
4. app.activateIgnoringOtherApps_(True)
```

---

### TODO 4: Force Window Visibility in StatusWindow
**File:** `src/pokertool/status_window.py`
**Lines:** 36-75
**Priority:** CRITICAL
**Issue:** StatusWindow might not be visible after toggle() call
**Fix:** Add explicit `self.root.deiconify()` and `self.root.lift()` calls
**Test:** `tests/test_dock_icon_visibility.py::test_status_window_forced_visible`
**Expected:** Window always visible after show() call, always on top
```python
# In show() method, add:
self.root.deiconify()  # Make visible
self.root.lift()        # Bring to front
self.root.focus()       # Focus window
self.root.attributes('-topmost', True)  # Keep on top
```

---

### TODO 5: Verify Custom Icon File Exists BEFORE Load
**File:** `start.py`
**Lines:** 166-175
**Priority:** HIGH
**Issue:** Icon loading silent fails if file doesn't exist
**Fix:** Check file exists, log clearly if missing
**Test:** `tests/test_dock_icon_visibility.py::test_icon_file_existence_checked`
**Expected:** Clear message if icon file missing, uses default
```python
# After fix:
icon_path = ROOT / "assets" / "pokertool-icon.png"
if not icon_path.exists():
    log(f"⚠️  Icon file not found at {icon_path}")
    log("   Using default Python icon")
else:
    # Load icon
```

---

### TODO 6: Ensure App Icon Set (Fallback to Default)
**File:** `start.py`
**Lines:** 168-170
**Priority:** HIGH
**Issue:** If NSImage fails to load, app has no icon
**Fix:** Verify icon was loaded and set, use sensible default if not
**Test:** `tests/test_dock_icon_visibility.py::test_app_icon_always_set`
**Expected:** App always has an icon, never None
```python
# After fix:
icon = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
if icon:
    app.setApplicationIconImage_(icon)
    log("✓ Custom icon loaded")
else:
    log("⚠️  Could not load custom icon, using system default")
    # Icon remains as system default (acceptable)
```

---

### TODO 7: Add Repeated Activation Calls (Safety Net)
**File:** `start.py`
**Lines:** 179
**Priority:** MEDIUM
**Issue:** Single activation call might not be enough
**Fix:** Call `activateIgnoringOtherApps_(True)` twice (with delay)
**Test:** `tests/test_dock_icon_visibility.py::test_repeated_activation`
**Expected:** Icon visible even if first activation fails
```python
# After fix:
app.activateIgnoringOtherApps_(True)
import time; time.sleep(0.1)
app.activateIgnoringOtherApps_(True)  # Safety net
```

---

## Phase 2: Dock Icon Process Management (Tasks 8-12) - HIGH

### TODO 8: Track All Spawned Processes
**File:** `start.py`
**New file:** Create `src/pokertool/process_tracker.py`
**Priority:** HIGH
**Issue:** Can't verify if all app processes running
**Fix:** Create ProcessTracker class to track backend, frontend, scraper processes
**Test:** `tests/test_dock_icon_process_management.py::test_process_tracker_tracks_all`
**Expected:** All 3 processes tracked and verifiable
```python
# New class:
class ProcessTracker:
    def __init__(self):
        self.backend_pid = None
        self.frontend_pid = None
        self.scraper_pid = None

    def set_backend(self, process): self.backend_pid = process.pid
    def set_frontend(self, process): self.frontend_pid = process.pid

    def all_running(self):
        return all(self._process_alive(pid) for pid in [
            self.backend_pid, self.frontend_pid, self.scraper_pid
        ])

    def _process_alive(self, pid):
        if not pid: return False
        try:
            os.kill(pid, 0)  # Check if process exists
            return True
        except: return False
```

---

### TODO 9: Verify All Processes Before Showing Dock Icon Success
**File:** `start.py`
**Lines:** 614-624 (application ready step)
**Priority:** HIGH
**Issue:** Dock icon success claimed before all processes running
**Fix:** Only mark as ready if backend + frontend + scraper all running
**Test:** `tests/test_dock_icon_process_management.py::test_dock_icon_only_ready_all_running`
**Expected:** "Application ready" message only if all processes verified
```python
# After fix:
if not process_tracker.all_running():
    raise RuntimeError("Not all processes started successfully")

startup_logger.complete_step(step7, success=True, ...)
```

---

### TODO 10: Implement Process Health Watchdog
**File:** Create `src/pokertool/process_watchdog.py`
**Priority:** HIGH
**Issue:** No monitoring if processes die after startup
**Fix:** Create watchdog thread that continuously monitors processes
**Test:** `tests/test_dock_icon_process_management.py::test_watchdog_detects_process_death`
**Expected:** Watchdog detects when processes die and alerts
```python
# New class:
class ProcessWatchdog:
    def __init__(self, process_tracker, callback):
        self.tracker = process_tracker
        self.callback = callback  # Called when process dies
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._watch_loop, daemon=True).start()

    def _watch_loop(self):
        while self.running:
            if not self.tracker.all_running():
                self.callback("Process died")
            time.sleep(5)
```

---

### TODO 11: Update Dock Icon Status Color Based on Process Health
**File:** `src/pokertool/status_window.py`
**Lines:** 190-245
**Priority:** MEDIUM
**Issue:** Dock icon doesn't reflect process health
**Fix:** Add visual indicator (window title bar color) based on health
**Test:** `tests/test_dock_icon_process_management.py::test_dock_icon_status_color`
**Expected:** Red title bar if process dead, green if healthy
```python
# In refresh_status():
if self.process_tracker.all_running():
    self.root.configure(bg='#2ecc71')  # Green
    status = "✅ ALL SYSTEMS OPERATIONAL"
else:
    self.root.configure(bg='#e74c3c')  # Red
    status = "❌ PROCESS FAILURE - Click to restart"
```

---

### TODO 12: Add "Restart" Button to Status Window
**File:** `src/pokertool/status_window.py`
**Lines:** 100-140
**Priority:** MEDIUM
**Issue:** User can't restart if process dies
**Fix:** Add "Restart Application" button that relaunches start.py
**Test:** `tests/test_dock_icon_process_management.py::test_restart_button_works`
**Expected:** Clicking restart launches new start.py process
```python
# Add to status window:
restart_button = tk.Button(
    self.root,
    text="🔄 Restart Application",
    command=self.restart_application,
    bg='#3498db', fg='white'
)
restart_button.pack()

def restart_application(self):
    subprocess.Popen([sys.executable, "start.py"])
    self.hide()
```

---

## Phase 3: Dock Icon Click Handler Reliability (Tasks 13-15) - HIGH

### TODO 13: Verify AppDelegate Properly Installed
**File:** `start.py`
**Lines:** 162-163
**Priority:** HIGH
**Issue:** AppDelegate might not be properly installed
**Fix:** Add verification that delegate was actually set
**Test:** `tests/test_dock_icon_click_handler.py::test_delegate_actually_installed`
**Expected:** Exception if delegate not properly set
```python
# After fix:
delegate = AppDelegate.alloc().init()
app.setDelegate_(delegate)

# Verify it was set:
current_delegate = app.delegate()
if current_delegate is None:
    raise RuntimeError("Failed to set application delegate")
```

---

### TODO 14: Make AppDelegate Robust to Null StatusWindow
**File:** `start.py`
**Lines:** 115-120
**Priority:** HIGH
**Issue:** Dock click fails if _status_window is None
**Fix:** Create StatusWindow on demand if it doesn't exist
**Test:** `tests/test_dock_icon_click_handler.py::test_delegate_handles_null_window`
**Expected:** Dock click works even if window not initialized
```python
# In AppDelegate.applicationShouldHandleReopen_hasVisibleWindows_:
def applicationShouldHandleReopen_hasVisibleWindows_(self, app, has_visible_windows):
    global _status_window
    if _status_window is None:
        _status_window = StatusWindow(api_url="http://localhost:5001")
    _status_window.toggle()
    return True
```

---

### TODO 15: Log All Dock Click Events
**File:** `start.py`
**Lines:** 115-120
**Priority:** MEDIUM
**Issue:** Can't debug dock click issues without logs
**Fix:** Log every dock click event with timestamp and action
**Test:** `tests/test_dock_icon_click_handler.py::test_dock_clicks_logged`
**Expected:** Each dock click creates log entry
```python
# In AppDelegate method:
def applicationShouldHandleReopen_hasVisibleWindows_(self, app, has_visible_windows):
    log(f"[DOCK CLICK] {datetime.now()} - Toggling status window visibility")
    global _status_window
    if _status_window:
        was_visible = _status_window.root.state() == 'normal'
        _status_window.toggle()
        log(f"[DOCK CLICK] Window was {'' if was_visible else 'not '}visible, now toggling")
    return True
```

---

## Phase 4: Status Window Diagnostic Dashboard (Tasks 16-18) - HIGH

### TODO 16: Display Complete Application Health in Status Window
**File:** `src/pokertool/status_window.py`
**Lines:** 140-180
**Priority:** HIGH
**Issue:** Status window missing critical health info
**Fix:** Add detailed health information display
**Test:** `tests/test_dock_icon_diagnostics.py::test_status_window_shows_all_health_info`
**Expected:** Window displays: backend health, frontend status, scraper state, process IDs, uptimes
```python
# Add to status window displays:
┌─ POKERTOOL STATUS DASHBOARD ─────────────────┐
│                                               │
│ APPLICATION STATUS                            │
│  Backend (PID 12345)      ✅ Running          │
│  Frontend (PID 12346)     ✅ Running          │
│  Scraper (PID 12347)      ✅ Running          │
│  Overall Uptime: 2h 34m 12s                  │
│                                               │
│ BACKEND HEALTH                                │
│  HTTP Status: 200 OK                          │
│  Response Time: 45ms                          │
│  Database: ✅ Connected                       │
│  API Health: ✅ 20/20 checks passing          │
│                                               │
│ DETECTED TABLES (Last 5 min)                  │
│  PokerStars (Texas Hold'em) - 2 players      │
│  BetFair (Cash 2/4) - 6 players               │
│                                               │
│ RECENT ACTIVITY LOG                           │
│  [14:32:15] Backend health check: PASS       │
│  [14:31:45] Table detected: PokerStars       │
│  [14:31:30] Frontend reconnected              │
│  [14:30:15] Scraper started                   │
│                                               │
│ [🔄 Refresh] [📋 Clear Log] [❌ Close]       │
└───────────────────────────────────────────────┘
```

---

### TODO 17: Make Status Window Resizable with Persistent Size
**File:** `src/pokertool/status_window.py`
**Lines:** 36-48
**Priority:** MEDIUM
**Issue:** Status window is fixed 500x600, can't expand for log viewing
**Fix:** Make resizable, remember user's preferred size
**Test:** `tests/test_dock_icon_diagnostics.py::test_status_window_resizable_and_persistent`
**Expected:** Window remembers size and position between launches
```python
# Modify window creation:
self.root.geometry("600x700")  # Larger default
self.root.resizable(True, True)  # Allow resizing

# Save/restore size in:
~/.pokertool/status_window_geometry.json
```

---

### TODO 18: Add Real-time Process Resource Usage Display
**File:** `src/pokertool/status_window.py`
**Priority:** MEDIUM
**Issue:** Can't see if processes consuming excessive resources
**Fix:** Display CPU and memory usage for each process
**Test:** `tests/test_dock_icon_diagnostics.py::test_process_resource_usage_displayed`
**Expected:** Window shows CPU% and RAM usage for backend, frontend, scraper
```python
# Add to status section:
│ Backend (PID 12345)       ✅ Running           │
│   CPU: 2.3%  |  RAM: 185 MB                   │
│ Frontend (PID 12346)      ✅ Running           │
│   CPU: 1.8%  |  RAM: 92 MB                    │
│ Scraper (PID 12347)       ✅ Running           │
│   CPU: 0.1%  |  RAM: 45 MB                    │
```

---

## Phase 5: Dock Icon Startup Integration (Tasks 19-21) - MEDIUM

### TODO 19: Test Dock Icon Setup Before Returning from launch_web_app()
**File:** `start.py`
**Lines:** 614-624
**Priority:** MEDIUM
**Issue:** Dock setup completes but might not be visible
**Fix:** Add verification that dock icon is actually visible
**Test:** `tests/test_dock_icon_startup.py::test_dock_icon_visible_before_app_ready`
**Expected:** App doesn't claim "ready" until dock icon verified visible
```python
# Before marking app as ready:
if IS_MACOS and HAS_APPKIT:
    # Verify dock icon is visible
    if not is_dock_icon_visible():
        raise RuntimeError("Dock icon setup failed - app not visible in dock")
```

---

### TODO 20: Add Dock Icon Availability Check to Startup Validation
**File:** `src/pokertool/startup_validation.py` (or add to start.py)
**Priority:** MEDIUM
**Issue:** No validation that startup completed successfully including dock
**Fix:** Verify dock icon visible as part of startup validation
**Test:** `tests/test_dock_icon_startup.py::test_startup_validation_includes_dock_check`
**Expected:** Startup validation includes dock icon visibility check
```python
# In startup validation:
def validate_startup():
    checks = {
        "Backend running": check_backend_running(),
        "Frontend running": check_frontend_running(),
        "Dock icon visible": check_dock_icon_visible() if IS_MACOS else True,
        "All processes healthy": check_all_processes_healthy(),
    }
    return all(checks.values()), checks
```

---

### TODO 21: Add Dock Icon Readiness to Startup Logger
**File:** `start.py`
**Lines:** 463-475
**Priority:** MEDIUM
**Issue:** Startup logger doesn't track dock icon setup as separate step
**Fix:** Add explicit dock icon readiness confirmation to startup flow
**Test:** `tests/test_dock_icon_startup.py::test_startup_logger_tracks_dock_icon`
**Expected:** Startup logger shows dock icon setup with clear success/failure
```python
# In startup flow, after starting frontend:
step_dock = startup_logger.start_step(
    "Dock Icon Ready",
    "Verifying application visible in dock"
)

if IS_MACOS and HAS_APPKIT:
    if is_dock_icon_visible():
        startup_logger.complete_step(step_dock, success=True)
    else:
        startup_logger.complete_step(step_dock, success=False,
            message="Dock icon not visible - check macOS settings")
else:
    startup_logger.complete_step(step_dock, success=True,
        message="Not macOS - dock icon not applicable")
```

---

## Phase 6: Comprehensive Test Coverage (Tasks 22-25) - CRITICAL

### TODO 22: Create Dock Icon Visibility Test Suite (50+ Tests)
**File:** Create `tests/test_dock_icon_visibility.py`
**Priority:** CRITICAL
**Tests:** 50 comprehensive visibility tests
**Test:** `tests/test_dock_icon_visibility.py::*`
**Expected:** 100% test pass rate
```python
# Test categories:
- Activation policy set correctly (5 tests)
- App icon loaded properly (5 tests)
- Delegate properly installed (5 tests)
- StatusWindow creation (5 tests)
- StatusWindow toggle logic (5 tests)
- Dock click handling (5 tests)
- Error recovery (5 tests)
- Multi-launch scenarios (5 tests)
```

---

### TODO 23: Create Dock Icon Process Management Test Suite (30+ Tests)
**File:** Create `tests/test_dock_icon_process_management.py`
**Priority:** CRITICAL
**Tests:** 30 comprehensive process management tests
**Test:** `tests/test_dock_icon_process_management.py::*`
**Expected:** 100% test pass rate
```python
# Test categories:
- Process tracker initialization (3 tests)
- Process tracking accuracy (3 tests)
- Process death detection (3 tests)
- Watchdog functionality (3 tests)
- Status window health display (3 tests)
- Restart functionality (3 tests)
- Resource usage calculation (3 tests)
- Error handling (3 tests)
```

---

### TODO 24: Create Dock Icon Click Handler Test Suite (20+ Tests)
**File:** Create `tests/test_dock_icon_click_handler.py`
**Priority:** CRITICAL
**Tests:** 20 comprehensive click handler tests
**Test:** `tests/test_dock_icon_click_handler.py::*`
**Expected:** 100% test pass rate
```python
# Test categories:
- AppDelegate creation (3 tests)
- Dock click event handling (3 tests)
- StatusWindow toggle on click (3 tests)
- Null StatusWindow handling (3 tests)
- Click logging (3 tests)
- Rapid click handling (3 tests)
```

---

### TODO 25: Create Comprehensive Integration Test Suite (50+ Tests)
**File:** Create `tests/test_dock_icon_comprehensive.py`
**Priority:** CRITICAL
**Tests:** 50 comprehensive integration tests
**Test:** `tests/test_dock_icon_comprehensive.py::*`
**Expected:** 100% test pass rate
```python
# Test categories (50+ tests total):
✅ Startup sequence: dock appears before "ready" (5 tests)
✅ Process lifecycle: all processes + dock icon (8 tests)
✅ Dock click → window appears (5 tests)
✅ Status dashboard displays correctly (8 tests)
✅ Restart functionality (5 tests)
✅ Multi-monitor support (3 tests)
✅ Different macOS versions (5 tests)
✅ Error recovery scenarios (5 tests)
✅ Resource management (5 tests)
```

---

## Test Coverage Summary

| Task | Tests | Coverage |
|------|-------|----------|
| TODO 1-7 (Visibility) | 50 | Phase 1 |
| TODO 8-12 (Process Mgmt) | 30 | Phase 2 |
| TODO 13-15 (Click Handler) | 20 | Phase 3 |
| TODO 16-18 (Diagnostics) | 25 | Phase 4 |
| TODO 19-21 (Startup) | 20 | Phase 5 |
| TODO 22-25 (Integration) | 150 | Phase 6 |
| **TOTAL** | **295 tests** | **Complete** |

---

## Success Criteria

✅ **Dock icon ALWAYS visible when app running**
✅ **Dock icon NOT visible when app NOT running**
✅ **Clicking dock icon shows diagnostic dashboard**
✅ **Dashboard shows:**
   - Application status (backend, frontend, scraper)
   - Process IDs and resource usage (CPU, RAM)
   - Uptime and last health check
   - Recent activity log
   - Detected poker tables
✅ **All 295 tests passing**
✅ **Zero regression in dock icon functionality**

---

## Implementation Schedule

**Phase 1 (Visibility):** Days 1-2
**Phase 2 (Process Management):** Days 2-3
**Phase 3 (Click Handler):** Day 3-4
**Phase 4 (Diagnostics):** Days 4-5
**Phase 5 (Startup Integration):** Day 5-6
**Phase 6 (Comprehensive Tests):** Days 6-7

---

## Notes

- All tests must mock AppKit (no actual macOS display required)
- Tests should run on all platforms (Linux, Windows, macOS)
- Dock icon only active on macOS; graceful degradation on other platforms
- StatusWindow uses Tkinter (cross-platform compatible)
- Process tracking uses psutil or os.kill for compatibility

