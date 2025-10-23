# POKERTOOL POKER GAME DETECTION SYSTEM - COMPREHENSIVE ANALYSIS

**Date:** October 23, 2025  
**Analysis Scope:** Complete detection pipeline, entry points, and failure modes  
**Codebase:** pokertool (develop branch)

---

## 1. DETECTION SYSTEM OVERVIEW

The poker game detection system is a multi-layered architecture designed to:
- Detect and monitor poker applications across platforms
- Extract game state information from poker table screenshots
- Emit real-time detection events via WebSocket
- Handle failures gracefully with fallback mechanisms

**Architecture Pattern:** Event-driven with asynchronous broadcasting

---

## 2. CORE DETECTION COMPONENTS

### 2.1 Primary Detection Modules

#### A. **Smart Poker Detector** (`smart_poker_detector.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/smart_poker_detector.py`

**Responsibilities:**
- Window title classification and prioritization
- Differentiate real poker sites from development tools
- Assign priority scores to detected windows

**Key Features:**
- **High Priority (Score 100):** Actual betting site URLs (PokerStars, Betfair, GGPoker, 888poker, etc.)
- **Medium Priority (Score 50):** Poker application patterns and window titles
- **Low Priority (Score 10):** Generic poker keywords
- **Excluded (Score 0):** Development tools (VSCode, GitHub, IDEs)

**Detection Method:** Regex pattern matching against window titles

**Main Class:**
```python
class SmartPokerDetector:
    - classify_window(window_title: str) -> (priority_score, reason)
    - filter_and_prioritize(windows) -> (high, medium, excluded)
    - get_best_windows(windows, max_windows=5) -> best_windows
```

---

#### B. **Desktop Independent Scraper** (`desktop_independent_scraper.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/desktop_independent_scraper.py`

**Responsibilities:**
- Cross-platform window detection
- Screen region capture
- Poker table visual analysis
- Multi-monitor and multi-desktop support

**Platform Support:**
- **Windows:** win32gui, win32con API
- **macOS:** Quartz, AppKit frameworks
- **Linux:** subprocess-based detection

**Key Features:**
- `WindowInfo` dataclass for window metadata
- `PokerDetectionMode` enum (WINDOW_TITLE, PROCESS_NAME, COMBINED, FUZZY_MATCH)
- Color-based poker table detection (HSV and LAB color spaces)
- Continuous monitoring thread
- Screenshot debugging capabilities

**Main Detection Pipeline:**
```python
class DesktopIndependentScraper:
    - scan_for_poker_windows() -> List[WindowInfo]
    - start_monitoring() -> continuous monitoring
    - capture_window(window_info) -> screenshot
    - _detect_poker_table(image, hsv, lab) -> confidence_score
```

---

#### C. **Player Action Detector** (`player_action_detector.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/player_action_detector.py`

**Detects:**
- Fold, Check, Call, Bet, Raise, All-In actions
- Stack changes
- Visual action indicators

**Detection Methods:**
1. Stack change analysis (previous vs. current stack)
2. Visual indicators (dimmed areas, crossed cards)
3. OCR text recognition
4. Action button color detection

**Key Data Structure:**
```python
@dataclass
class ActionDetection:
    player_seat: int
    action: PlayerAction
    amount: float
    confidence: float
    timestamp: float
    detection_method: str  # "visual", "text", "button_state"
```

---

#### D. **Specialized Detectors**

| Module | Purpose | Detection Target |
|--------|---------|------------------|
| `side_pot_detector.py` | Main + side pot detection | Multiple pot amounts and positions |
| `blind_ante_detector.py` | Game stakes | Small blind, big blind, ante amounts (via regex) |
| `timeout_detector.py` | Action timeouts | Player timeout indicators |
| `suit_color_detector.py` | Card suit identification | Suit determination from card images |

---

### 2.2 Detection Event System

#### **Detection Events Module** (`detection_events.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_events.py`

**Purpose:** Centralized thread-safe event dispatch bridge

**Event Types:**
```python
class DetectionEventType(str, Enum):
    # Core detections
    POT = "pot"
    CARD = "card"
    PLAYER = "player"
    ACTION = "action"
    BOARD = "board"
    BUTTON = "button"
    BLIND = "blind"
    
    # State changes
    STATE_CHANGE = "state_change"
    HAND_START = "hand_start"
    HAND_END = "hand_end"
    STREET_CHANGE = "street_change"
    
    # System events
    SYSTEM = "system"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    
    # Performance events
    PERFORMANCE = "performance"
    FPS = "fps"
    LATENCY = "latency"
```

**Event Severity Levels:**
```python
class EventSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

**Core Functions:**
```python
emit_detection_event(event_type, severity, message, data, event_id, correlation_id)
emit_pot_event(pot_size, previous_pot_size, confidence, side_pots, correlation_id)
emit_card_event(cards, card_type, confidence, correlation_id)
emit_player_event(seat_number, player_name, stack_size, position, correlation_id)
emit_action_event(seat_number, action, amount, confidence, correlation_id)
emit_state_change_event(previous_state, new_state, reason, correlation_id)
emit_performance_event(fps, avg_frame_time_ms, memory_mb, cpu_percent, correlation_id)
```

**Event Queue:**
- Thread-safe deque (maxlen=256) for pending events
- Automatic buffering when event loop not registered
- Automatic flushing when loop becomes available

---

#### **Detection State Dispatcher** (`detection_state_dispatcher.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_state_dispatcher.py`

**Purpose:** Central dispatcher tracking table state and emitting events on changes

**State Tracking:**
```python
@dataclass
class TableState:
    pot_size: float
    side_pots: List[float]
    board_cards: List[Dict]
    hero_cards: List[Dict]
    player_stacks: Dict[int, float]
    player_names: Dict[int, str]
    player_positions: Dict[int, str]
    player_active: Dict[int, bool]
    current_street: str
    hand_id: Optional[str]
    button_position: Optional[int]
    last_fps: Optional[float]
    last_frame_time_ms: Optional[float]
```

**Core Methods:**
```python
class DetectionStateDispatcher:
    - begin_frame() -> correlation_id
    - update_pot(pot_size, side_pots, confidence) -> changed
    - update_board_cards(cards, confidence) -> changed
    - update_hero_cards(cards, confidence) -> changed
    - update_player(seat, stack_size, name, position, active, confidence) -> changed
    - emit_player_action(seat, action, amount, confidence)
    - update_performance(fps, frame_time_ms, memory_mb, cpu_percent) -> changed
    - reset_hand()
    - get_stats() -> stats_dict
```

**Change Detection:** Only emits events when state actually changes (with tolerance for floats)

---

### 2.3 Detection Configuration and Quality Control

#### **Detection Configuration** (`detection_config.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_config.py`

**Confidence Thresholds:**
```python
@dataclass
class ConfidenceThresholds:
    card_min_confidence: float = 0.7      # Minimum to report
    card_high_confidence: float = 0.9     # High confidence threshold
    pot_min_confidence: float = 0.6
    pot_high_confidence: float = 0.85
    player_min_confidence: float = 0.65
    player_high_confidence: float = 0.88
    button_min_confidence: float = 0.75
    button_high_confidence: float = 0.92
    action_min_confidence: float = 0.70
    action_high_confidence: float = 0.90
    board_min_confidence: float = 0.72
    board_high_confidence: float = 0.91
    min_confidence_to_emit: float = 0.6  # Overall minimum
```

**Environment Variables:** All thresholds configurable via `DETECTION_*` env vars

---

#### **Detection Fallback Manager** (`detection_fallback.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_fallback.py`

**Degradation Modes:**
```python
class DetectionMode(Enum):
    FULL = "full"           # All systems operational
    PARTIAL = "partial"     # Some systems working
    MINIMAL = "minimal"     # Critical detection only
    FALLBACK = "fallback"   # Using cached/estimated data
    OFFLINE = "offline"     # No detection available
```

**Fallback Strategy:**
1. Use cached state (marked with `_fallback` flag)
2. Use last known state
3. Return minimal safe state
4. Automatic recovery when successful detections resume

**Failure Tracking:**
- Failure count with threshold (default: 3)
- Recovery timeout (default: 60 seconds)
- Last error logging

---

### 2.4 Detection Monitoring and Metrics

#### **Detection Metrics Tracker** (`detection_metrics_tracker.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_metrics_tracker.py`

**Metrics Per Detection Type:**
```python
@dataclass
class DetectionMetrics:
    total_detections: int
    successful_detections: int
    failed_detections: int
    avg_confidence: float
    min/max_confidence: float
    avg_duration_ms: float
    min/max_duration_ms: float
    success_rate: float (calculated)
```

**Tracked Metrics:**
- FPS (frames per second)
- Frame processing time
- Error counts and types
- Recent error history

---

#### **Detection Accuracy Tracker** (`detection_accuracy_tracker.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_accuracy_tracker.py`

**Features:**
- Per-detection-type accuracy metrics
- Rolling window statistics (default window: 1000 detections)
- Alert thresholds:
  - Minimum success rate: 90%
  - Minimum average confidence: 70%
- Persistence to disk for historical analysis

---

#### **Detection Logger** (`detection_logger.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_logger.py`

**Features:**
- Dedicated logger with daily rotation
- Configurable retention (default: 30 days)
- Formats: timestamp, level, detection type, success, confidence, duration
- Separate log file from application logs

---

#### **Detection Cache** (`detection_cache.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_cache.py`

**Implementation:** LRU cache with TTL
- Max size: 100 items (configurable)
- TTL: 2.0 seconds (configurable)
- Uses image region hashing for keys

---

### 2.5 Detection Performance and FPS Tracking

#### **Detection FPS Counter** (`detection_fps_counter.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_fps_counter.py`

Tracks frames per second for detection pipeline

---

#### **Detection Event Batcher** (`detection_event_batcher.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_event_batcher.py`

**Purpose:** Batch events for efficient WebSocket transmission
- Batch interval: 0.1 seconds
- Max batch size: 50 events
- Reduces WebSocket overhead

---

---

## 3. DETECTION ENTRY POINTS

### 3.1 How Detection Is Triggered

#### **1. Main Scraping Pipeline** (`scrape.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/scrape.py`

**Detection Trigger:**
```
scrape.py -> Desktop Independent Scraper -> scan_for_poker_windows()
                                          -> start_monitoring()
```

**Flow:**
1. `RecognitionStats` tracks OCR quality
2. Desktop scraper scans for poker windows
3. Windows captured continuously
4. Screenshots analyzed for game state
5. Detection results cached

---

#### **2. WebSocket Detection Endpoint** (`api.py`)
**Location:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/api.py`

**WebSocket Route:** `/ws/detections`

**Features:**
- Real-time detection event streaming
- Connection-per-client WebSocket manager
- Automatic event broadcasting via `broadcast_detection_event()`
- Integration with event loop registration

**Event Flow:**
```
Detection System -> emit_detection_event() 
                 -> _enqueue_event() or _dispatch_event()
                 -> _schedule_broadcast()
                 -> broadcast_detection_event()
                 -> WebSocket clients
```

---

#### **3. Detection State Change Events**

**Triggered When:**
- Window is detected/classified
- Pot size changes (>0.01 tolerance)
- Board cards updated
- Hero cards updated
- Player stack changes
- Player action detected
- Game state transitions (hand start/end, street change)
- Performance metrics change significantly

---

### 3.2 Scheduled Detection

**FPS-based Detection:**
- Continuous monitoring thread in desktop scraper
- Frequency determined by detection_fps_counter
- Configurable capture interval

---

### 3.3 Manual Detection Triggers

**From Frontend:**
- DetectionLog component connects to `/ws/detections`
- Manual refresh endpoints (if available)
- Real-time message streaming

---

---

## 4. CURRENT IMPLEMENTATION STATUS

### 4.1 What's Currently Implemented

**FULLY IMPLEMENTED:**
- Smart window detection with prioritization
- Desktop-independent platform support (Windows, macOS, Linux)
- Event-driven architecture with WebSocket broadcasting
- Confidence threshold system with per-detection-type settings
- State change tracking and emission
- Fallback and graceful degradation
- Metrics tracking and accuracy monitoring
- Detection caching with TTL
- Specialized detectors for:
  - Player actions
  - Side pots
  - Blinds and antes
  - Card suits
  - Timeouts

**PARTIALLY IMPLEMENTED:**
- Pattern detection for behavioral analysis (timing, fatigue detection)
- OCR integration for text recognition
- Multi-table support (framework exists, feature TBD)

**NOT YET IMPLEMENTED:**
- Hand history parsing integration
- Real-time game state synthesis (combining multiple detections)
- Machine learning-based detection improvement
- Browser-based detection for web poker

---

### 4.2 Test Coverage

#### Test Files Located:

| Test File | Purpose | Location |
|-----------|---------|----------|
| `test_detection_suite.py` | Basic detection thresholds | `/tests/detection/test_detection_suite.py` |
| `test_detection_events.py` | Event emission and buffering | `/tests/test_detection_events.py` |
| `test_detection_state_dispatcher.py` | State change tracking | `/tests/test_detection_state_dispatcher.py` |
| `test_bf_detection.py` | Betfair-specific detection | `/tests/test_bf_detection.py` |
| `test_bf_test_image_detection.py` | Betfair image analysis | `/tests/test_bf_test_image_detection.py` |
| `test_adaptive_ui_detector.py` | Adaptive UI detection | `/tests/test_adaptive_ui_detector.py` |
| `DetectionLog.test.tsx` | Frontend detection log UI | `/pokertool-frontend/src/components/` |
| `DetectionLogAndTablesTabs.test.tsx` | Frontend tab visibility | `/pokertool-frontend/src/__tests__/` |

**Current Test Status:**
- Unit tests: Basic coverage for core components
- Integration tests: Event emission and state dispatch
- Frontend tests: UI component rendering and WebSocket connection

**Test Coverage Gaps:**
- No end-to-end detection pipeline tests
- Limited image-based detection tests
- No failure mode/recovery tests
- No performance/stress tests

---

### 4.3 Error Tracking

#### Error Logging:
**File:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/detection_error_logger.py`

```python
def log_detection_error(detection_type: str, error: Exception, context: Optional[Dict[str, Any]]):
    """Log with full context and traceback"""
```

**Logged Information:**
- Detection type
- Error type and message
- Context data
- Full traceback

---

---

## 5. DETECTION PIPELINE FLOW (DETAILED)

```
┌─────────────────────────────────────────────────────────────────┐
│ POKER GAME DETECTION PIPELINE                                   │
└─────────────────────────────────────────────────────────────────┘

STAGE 1: WINDOW DETECTION
┌──────────────────────────────────────┐
│ scan_for_poker_windows()             │
│ (DesktopIndependentScraper)          │
├──────────────────────────────────────┤
│ 1. Enumerate all windows             │
│ 2. Capture window metadata           │
│ 3. Classify with SmartPokerDetector  │
│ 4. Filter by priority score          │
└──────────────────────────────────────┘
           │
           ▼
STAGE 2: WINDOW PRIORITIZATION
┌──────────────────────────────────────┐
│ classify_window() & prioritize()     │
│ (SmartPokerDetector)                 │
├──────────────────────────────────────┤
│ Check patterns:                      │
│ - Exclusion rules (dev tools)       │
│ - Betting site URLs (HIGH)          │
│ - Poker app names (MEDIUM)          │
│ - Generic keywords (LOW)            │
└──────────────────────────────────────┘
           │
           ▼
STAGE 3: SCREENSHOT CAPTURE
┌──────────────────────────────────────┐
│ capture_window() & crop()            │
│ (DesktopIndependentScraper)          │
├──────────────────────────────────────┤
│ Platform-specific:                   │
│ - Windows: win32gui API              │
│ - macOS: Quartz API                  │
│ - Linux: subprocess                  │
└──────────────────────────────────────┘
           │
           ▼
STAGE 4: POKER TABLE DETECTION
┌──────────────────────────────────────┐
│ _detect_poker_table()                │
│ (DesktopIndependentScraper)          │
├──────────────────────────────────────┤
│ Color space analysis:                │
│ - HSV (Hue, Saturation, Value)      │
│ - LAB (Lightness, A*, B*)           │
│ - Green felt detection               │
│ - Table shape recognition            │
└──────────────────────────────────────┘
           │
           ▼
STAGE 5: ELEMENT DETECTION (Parallel)
┌─────────────────┬──────────────┬─────────────┐
│ Card Detection  │ Pot Detection│ Player Info │
├─────────────────┼──────────────┼─────────────┤
│ Card ranks      │ Amount OCR   │ Stack sizes │
│ Card suits      │ Side pots    │ Names       │
│ (SuitColorDet)  │ Confidence   │ Positions   │
│ Hero/board      │ Caching      │ Active flag │
└─────────────────┴──────────────┴─────────────┘
           │
           ▼
STAGE 6: ACTION & STATE DETECTION
┌──────────────────────────────────────┐
│ detect_player_action()               │
│ (PlayerActionDetector)               │
├──────────────────────────────────────┤
│ Methods:                             │
│ 1. Stack change analysis             │
│ 2. Visual indicators                 │
│ 3. OCR text recognition              │
│ 4. Action button color               │
└──────────────────────────────────────┘
           │
           ▼
STAGE 7: STATE CHANGE DETECTION
┌──────────────────────────────────────┐
│ Update TableState                    │
│ (DetectionStateDispatcher)           │
├──────────────────────────────────────┤
│ Track changes:                       │
│ - Pot size changes                   │
│ - Board card updates                 │
│ - Hero card updates                  │
│ - Player stack changes               │
│ - Street transitions                 │
│ - Hand start/end                     │
└──────────────────────────────────────┘
           │
           ▼
STAGE 8: CONFIDENCE & FILTERING
┌──────────────────────────────────────┐
│ Check thresholds                     │
│ (ConfidenceThresholds)               │
├──────────────────────────────────────┤
│ Per-detection-type:                  │
│ - Min confidence > threshold         │
│ - High confidence classification     │
│ - Emit event or suppress             │
└──────────────────────────────────────┘
           │
           ▼
STAGE 9: EVENT EMISSION
┌──────────────────────────────────────┐
│ emit_*_event()                       │
│ (detection_events.py)                │
├──────────────────────────────────────┤
│ Create DetectionEventSchema:         │
│ - Type (POT, CARD, PLAYER, etc)     │
│ - Severity (INFO, WARNING, etc)     │
│ - Message and data                   │
│ - Correlation ID                     │
│ - Timestamp                          │
└──────────────────────────────────────┘
           │
           ▼
STAGE 10: EVENT DISPATCH
┌──────────────────────────────────────┐
│ emit_detection_event()               │
│ (detection_events.py)                │
├──────────────────────────────────────┤
│ If loop running:                     │
│ → _dispatch_event() →                │
│ → _schedule_broadcast() →            │
│ → broadcast_detection_event() →      │
│ → WebSocket manager                  │
│                                      │
│ If no loop:                          │
│ → _enqueue_event() → buffer (max 256)│
└──────────────────────────────────────┘
           │
           ▼
STAGE 11: WEBSOCKET BROADCASTING
┌──────────────────────────────────────┐
│ broadcast_detection()                │
│ (DetectionWebSocketManager)          │
├──────────────────────────────────────┤
│ Send to all connected clients:       │
│ - Frontend detection log             │
│ - Real-time monitoring               │
│ - Analytics collection               │
└──────────────────────────────────────┘
           │
           ▼
STAGE 12: MONITORING & METRICS
┌──────────────────────────────────────┐
│ Track performance                    │
│ (Multiple trackers)                  │
├──────────────────────────────────────┤
│ - DetectionMetricsTracker            │
│ - DetectionAccuracyTracker           │
│ - DetectionLogger                    │
│ - DetectionFpsCounter                │
└──────────────────────────────────────┘
```

---

---

## 6. FAILURE MODES AND RECOVERY

### 6.1 Potential Failure Points

#### **Point 1: Window Detection Failure**
- **Cause:** No windows found, all windows excluded, poker site not in patterns
- **Detection:** `detected_windows` is empty
- **Impact:** No game data collection
- **Recovery:** Automatic pattern updates, manual window whitelisting

#### **Point 2: Screenshot Capture Failure**
- **Cause:** Permission denied, window minimized, display disconnected
- **Detection:** Exception in capture function
- **Impact:** Missing frame, no state update for this cycle
- **Recovery:** Retry on next cycle, fallback manager records error

#### **Point 3: OCR Failure**
- **Cause:** Text not readable, poor image quality, OCR not installed
- **Detection:** OCR confidence < threshold
- **Impact:** Missing pot/blind/stack data
- **Recovery:** Use cached values, use fallback mode

#### **Point 4: Confidence Below Threshold**
- **Cause:** Image quality poor, detection algorithm uncertainty
- **Detection:** Confidence score < min threshold
- **Impact:** Event not emitted (no false positives)
- **Recovery:** Retry on next frame, accumulate evidence

#### **Point 5: State Dispatch Failure**
- **Cause:** Event loop not initialized, asyncio error
- **Detection:** Exception in _dispatch_event or _schedule_broadcast
- **Impact:** Event buffered (up to 256 events)
- **Recovery:** Automatic flushing when loop available

#### **Point 6: WebSocket Connection Loss**
- **Cause:** Client disconnect, network issue, server restart
- **Detection:** WebSocket close frame
- **Impact:** Frontend not receiving real-time events
- **Recovery:** Client-side reconnect with exponential backoff

#### **Point 7: Metric Tracker Failure**
- **Cause:** Disk write error, corrupted metrics file
- **Detection:** Exception in metrics persistence
- **Impact:** Metrics not saved (in-memory only)
- **Recovery:** Continue operation, logs record error

---

### 6.2 Graceful Degradation Strategy

**Degradation Cascade:**
```
FULL MODE (all detection working)
    ↓ (3+ failures)
PARTIAL MODE (removed: actions, complex detections)
    ↓ (3+ failures)
MINIMAL MODE (only cards and pot)
    ↓ (3+ failures)
FALLBACK MODE (use cached data only)
    ↓ (3+ failures)
OFFLINE MODE (no detection)

Recovery (on success):
OFFLINE → FALLBACK → MINIMAL → PARTIAL → FULL
(each success allows one-level recovery)
```

**Available Features by Mode:**
- **FULL:** cards, pot, stacks, actions, players
- **PARTIAL:** cards, pot, stacks
- **MINIMAL:** cards, pot
- **FALLBACK:** (empty - use cache)
- **OFFLINE:** (empty - error response only)

---

### 6.3 Error Recovery Mechanisms

#### **Automatic Recovery:**
1. Successful detection resets failure count
2. 60-second recovery timeout
3. Cached state preserved for fallback
4. Alerts logged when mode changes

#### **Manual Recovery:**
- API endpoint to reset detection system
- Configuration reload capability
- Force rescan of poker windows
- Clear detection cache

---

---

## 7. DETECTION CONFIGURATION

### 7.1 Environment Variables

```bash
# Confidence thresholds
DETECTION_CARD_MIN_CONFIDENCE=0.7
DETECTION_CARD_HIGH_CONFIDENCE=0.9
DETECTION_POT_MIN_CONFIDENCE=0.6
DETECTION_POT_HIGH_CONFIDENCE=0.85
DETECTION_PLAYER_MIN_CONFIDENCE=0.65
DETECTION_PLAYER_HIGH_CONFIDENCE=0.88
DETECTION_BUTTON_MIN_CONFIDENCE=0.75
DETECTION_BUTTON_HIGH_CONFIDENCE=0.92
DETECTION_ACTION_MIN_CONFIDENCE=0.70
DETECTION_ACTION_HIGH_CONFIDENCE=0.90
DETECTION_BOARD_MIN_CONFIDENCE=0.72
DETECTION_BOARD_HIGH_CONFIDENCE=0.91
DETECTION_MIN_EMIT_CONFIDENCE=0.6

# Logger settings
DETECTION_LOG_RETENTION_DAYS=30

# Cache settings
DETECTION_CACHE_MAX_SIZE=100
DETECTION_CACHE_TTL_SECONDS=2.0

# Performance settings
DETECTION_MAX_WINDOWS=5
DETECTION_BATCH_INTERVAL=0.1
DETECTION_BATCH_MAX_SIZE=50
```

---

### 7.2 Configuration Loading

**Default:** `ConfidenceThresholds.from_env()`
**Reload:** `reload_detection_config()`
**Access:** `get_detection_config()`

---

---

## 8. FRONTEND DETECTION COMPONENTS

### 8.1 Detection Log Component
**File:** `/Users/georgeridout/Documents/github/pokertool/pokertool-frontend/src/components/DetectionLog.tsx`

**Features:**
- Real-time WebSocket connection to `/ws/detections`
- Log entry filtering by type and severity
- Auto-scroll to latest events
- Manual log clear and export
- Fallback endpoint for localhost/127.0.0.1 issues

**Log Entry Types:**
- player, card, pot, action, system, error

**Severity Levels:**
- info, success, warning, error

---

### 8.2 Detection State Indicator
**File:** `/Users/georgeridout/Documents/github/pokertool/pokertool-frontend/src/components/DetectionStateIndicator.tsx`

Displays current detection mode and status

---

### 8.3 Detection Loading State
**File:** `/Users/georgeridout/Documents/github/pokertool/pokertool-frontend/src/components/DetectionLoadingState.tsx`

Shows initialization and connection status

---

### 8.4 Detection Metrics Widget
**File:** `/Users/georgeridout/Documents/github/pokertool/pokertool-frontend/src/components/DetectionMetricsWidget.tsx`

Real-time performance metrics display

---

---

## 9. KEY STATISTICS & PERFORMANCE

### Current Thresholds
- **Card Detection:** 70-90% confidence range
- **Pot Detection:** 60-85% confidence range
- **Player Detection:** 65-88% confidence range
- **Action Detection:** 70-90% confidence range
- **Success Rate Target:** 90%+
- **Average Confidence Target:** 70%+

### Performance Targets
- **Detection Latency:** <50ms per frame
- **FPS:** 20+ FPS (configurable)
- **Memory Usage:** <500MB for detection system
- **Cache Hit Rate:** Target 80%+ for repeated detections

### Fallback Thresholds
- **Failure Threshold:** 3 consecutive failures
- **Recovery Timeout:** 60 seconds
- **Event Buffer Size:** 256 events max
- **Metrics Window:** 1000 detections rolling window

---

---

## 10. RELATED COMPONENTS

### 10.1 OCR Integration
**File:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/ocr_recognition.py`
- Text recognition from screenshots
- Pot amounts, player names, blind levels
- Confidence scoring for OCR results
- Card region detection

### 10.2 Screen Scraper Bridge
**File:** `/Users/georgeridout/Documents/github/pokertool/pokertool/modules/poker_screen_scraper.py`
- High-level scraping interface
- Multi-site support
- Table state synthesis

### 10.3 Pattern Analyzer
**File:** `/Users/georgeridout/Documents/github/pokertool/src/pokertool/pattern_detector.py`
- Behavioral pattern detection
- Timing analysis
- Fatigue detection
- Anomaly detection

---

---

## 11. COMPLETE FILE STRUCTURE MAP

### Core Detection Files
```
/src/pokertool/
├── smart_poker_detector.py              # Window classification
├── desktop_independent_scraper.py       # Cross-platform window/screen capture
├── detection_events.py                  # Event definitions & emission
├── detection_state_dispatcher.py        # State change tracking
├── detection_config.py                  # Confidence thresholds
├── detection_fallback.py                # Degradation & recovery
├── detection_logger.py                  # Event logging
├── detection_cache.py                   # LRU cache with TTL
├── detection_metrics_tracker.py         # Performance metrics
├── detection_accuracy_tracker.py        # Accuracy monitoring
├── detection_fps_counter.py             # FPS tracking
├── detection_event_batcher.py           # Event batching for WebSocket
├── detection_error_logger.py            # Error logging
├── detection_sanity_checks.py           # Validation
├── detection_state_persistence.py       # State persistence
│
├── player_action_detector.py            # Action detection (fold, bet, etc)
├── side_pot_detector.py                 # Pot detection
├── blind_ante_detector.py               # Blind/ante detection
├── suit_color_detector.py               # Card suit detection
├── timeout_detector.py                  # Action timeout detection
│
├── pattern_detector.py                  # Pattern & anomaly detection
├── player_detection_confidence.py       # Player detection confidence
│
├── scrape.py                            # Main scraping interface
├── ocr_recognition.py                   # OCR integration
│
├── api.py                               # WebSocket detection endpoint
└── ...
```

### Frontend Detection Files
```
/pokertool-frontend/src/
├── components/
│   ├── DetectionLog.tsx                 # Detection event log UI
│   ├── DetectionLog.test.tsx            # Unit tests
│   ├── DetectionStateIndicator.tsx      # Status indicator
│   ├── DetectionLoadingState.tsx        # Loading state UI
│   └── DetectionMetricsWidget.tsx       # Metrics display
│
├── __tests__/
│   └── DetectionLogAndTablesTabs.test.tsx  # Integration tests
│
└── types/
    └── common.ts                        # Detection event types
```

### Test Files
```
/tests/
├── detection/
│   └── test_detection_suite.py          # Detection accuracy tests
│
├── test_detection_events.py             # Event emission tests
├── test_detection_state_dispatcher.py   # State dispatch tests
├── test_bf_detection.py                 # Betfair detection
├── test_bf_test_image_detection.py      # Betfair image analysis
└── test_adaptive_ui_detector.py         # Adaptive UI detection
```

---

---

## 12. SUMMARY & RECOMMENDATIONS

### What's Working Well
1. ✅ Modular detection architecture with clear separation of concerns
2. ✅ Comprehensive event system with proper typing
3. ✅ Graceful degradation and fallback mechanisms
4. ✅ Detailed metrics and monitoring capabilities
5. ✅ Real-time WebSocket integration for frontend
6. ✅ Cross-platform support (Windows, macOS, Linux)
7. ✅ Confidence-based quality control
8. ✅ Thread-safe event queuing and dispatch

### Areas for Improvement
1. ⚠️ Limited test coverage for integration scenarios
2. ⚠️ No end-to-end detection pipeline tests with real images
3. ⚠️ Pattern detection needs more robust implementation
4. ⚠️ OCR integration could be more reliable
5. ⚠️ Multi-table support framework exists but incomplete
6. ⚠️ No machine learning feedback loop for improvement

### Critical Failure Paths to Monitor
1. **Window Detection Fails** → No data collection possible
2. **All OCR Fails** → Fallback to cache (stale data)
3. **WebSocket Disconnects** → Frontend has no visibility
4. **State Dispatch Timeout** → Events buffered indefinitely
5. **Metrics Tracker Crash** → Silent failure (no alerting)

---

**End of Analysis**
