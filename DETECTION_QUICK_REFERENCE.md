# POKER DETECTION SYSTEM - QUICK REFERENCE

## Key Files at a Glance

### Entry Points
- **Main Scraper:** `/src/pokertool/scrape.py` → initiates detection
- **WebSocket:** `/src/pokertool/api.py` → `@websocket('/ws/detections')`
- **Window Detection:** `/src/pokertool/desktop_independent_scraper.py` → `scan_for_poker_windows()`

### Core Detection Pipeline
1. **Smart Poker Detector** - classifies windows by priority
2. **Desktop Scraper** - captures screenshots cross-platform
3. **Element Detectors** - cards, pots, players, actions
4. **State Dispatcher** - tracks changes and emits events
5. **Event System** - broadcasts to WebSocket clients

### Key Components
| Component | File | Purpose |
|-----------|------|---------|
| Window Classifier | `smart_poker_detector.py` | Prioritize poker windows (HIGH/MEDIUM/LOW/EXCLUDED) |
| Screen Capture | `desktop_independent_scraper.py` | Cross-platform window capture (Win/Mac/Linux) |
| Event Emission | `detection_events.py` | Thread-safe event queue and emission |
| State Tracking | `detection_state_dispatcher.py` | Track table state, emit on changes |
| Config | `detection_config.py` | Confidence thresholds (env-configurable) |
| Fallback | `detection_fallback.py` | Graceful degradation (FULL → PARTIAL → MINIMAL → FALLBACK → OFFLINE) |
| Metrics | `detection_metrics_tracker.py` | Performance metrics per detection type |
| Accuracy | `detection_accuracy_tracker.py` | Accuracy monitoring with alerts |
| Caching | `detection_cache.py` | LRU cache with TTL (2.0s default) |

### Specialized Detectors
- `player_action_detector.py` - Fold, Check, Call, Bet, Raise, All-In
- `side_pot_detector.py` - Main and side pot detection
- `blind_ante_detector.py` - Stakes detection (regex-based)
- `suit_color_detector.py` - Card suit identification
- `timeout_detector.py` - Action timeouts

---

## Detection Flow (12 Stages)

```
1. Window Enumeration
   ↓
2. Priority Classification (SmartPokerDetector)
   ↓
3. Screenshot Capture (Platform-specific)
   ↓
4. Poker Table Detection (HSV+LAB color analysis)
   ↓
5. Element Detection (Cards, Pot, Players - Parallel)
   ↓
6. Action Detection (PlayerActionDetector)
   ↓
7. State Change Tracking (DetectionStateDispatcher)
   ↓
8. Confidence Filtering (ConfidenceThresholds)
   ↓
9. Event Creation (DetectionEventSchema)
   ↓
10. Event Dispatch (Thread-safe queue)
    ↓
11. WebSocket Broadcasting (to connected clients)
    ↓
12. Metrics & Logging (Tracking performance)
```

---

## Detection Triggering

### Automatic Triggers
- **Continuous Loop:** FPS-based monitoring via `detection_fps_counter`
- **Platform:** Desktop scraper runs monitoring thread
- **Frontend:** WebSocket clients connect to `/ws/detections`

### Manual Triggers
- Force window rescan: `scan_for_poker_windows()`
- Reset state: `reset_dispatcher()`
- Clear cache: `detection_cache.clear()`

### State Change Triggers
- Pot size change (>0.01 tolerance)
- Board cards update
- Hero cards update
- Player stack change
- Player action detected
- Game state transition
- Performance metrics change (>5% FPS or >10ms frame time)

---

## Confidence Thresholds (Environment Variables)

```
DETECTION_CARD_MIN_CONFIDENCE=0.7       (default)
DETECTION_CARD_HIGH_CONFIDENCE=0.9      
DETECTION_POT_MIN_CONFIDENCE=0.6        
DETECTION_PLAYER_MIN_CONFIDENCE=0.65    
DETECTION_ACTION_MIN_CONFIDENCE=0.70    
DETECTION_BOARD_MIN_CONFIDENCE=0.72     
DETECTION_MIN_EMIT_CONFIDENCE=0.6       (overall minimum)
```

All thresholds have `_HIGH_CONFIDENCE` variants for quality classification.

---

## Event Types & Data

### Core Events
- **POT** - Pot size, change, side pots
- **CARD** - Card rank, suit, type (hero/board/opponent)
- **PLAYER** - Seat, name, stack, position, active status
- **ACTION** - Fold, Check, Call, Bet, Raise, All-In + amount
- **BOARD** - Board cards update
- **BUTTON** - Button position change
- **BLIND** - Blind amounts

### State Events
- **STATE_CHANGE** - Generic state transitions
- **HAND_START** - New hand detected
- **HAND_END** - Hand completion
- **STREET_CHANGE** - Preflop → Flop → Turn → River

### System Events
- **SYSTEM/INFO/WARNING/ERROR/CRITICAL** - System events
- **PERFORMANCE** - FPS, latency, memory, CPU
- **FPS** - Frame rate tracking
- **LATENCY** - Processing latency

---

## Failure Modes & Recovery

### Degradation Modes
1. **FULL** - All detection systems working
2. **PARTIAL** - Some systems disabled (no actions/complex)
3. **MINIMAL** - Only critical (cards, pot)
4. **FALLBACK** - Using cached data only
5. **OFFLINE** - No detection

### Recovery Strategy
- **Trigger:** 3 consecutive failures → degrade one level
- **Recovery:** Successful detection → restore one level
- **Timeout:** 60 seconds for recovery attempt
- **Cached Data:** Fallback uses last known state (marked with `_fallback` flag)

### Critical Failure Points
1. **Window Detection Fails** → No data collection
2. **All OCR Fails** → Use stale cache
3. **WebSocket Disconnects** → Frontend loses visibility
4. **Event Loop Missing** → Events buffered (max 256)
5. **Metrics Crash** → Silent failure (no alerting)

---

## Testing

### Test Files
- `tests/detection/test_detection_suite.py` - Basic accuracy tests
- `tests/test_detection_events.py` - Event emission/buffering
- `tests/test_detection_state_dispatcher.py` - State tracking
- `tests/test_bf_detection.py` - Betfair-specific
- `pokertool-frontend/src/__tests__/DetectionLogAndTablesTabs.test.tsx` - UI tests

### Test Gaps
- No end-to-end pipeline tests
- Limited image-based detection tests
- No failure/recovery scenario tests
- No performance/stress tests

---

## Performance Metrics

### Targets
- **Detection Latency:** <50ms/frame
- **FPS:** 20+
- **Success Rate:** 90%+
- **Avg Confidence:** 70%+
- **Cache Hit Rate:** 80%+
- **Memory:** <500MB

### Tracked Metrics
- FPS and frame time
- Per-type success rate and confidence
- Error counts and types
- Accuracy (rolling 1000-detection window)
- Duration per detection

---

## Configuration & Monitoring

### Confidence Thresholds
- **Get:** `get_detection_config()`
- **Reload:** `reload_detection_config()`
- **Method:** `should_emit_event(confidence, detection_type)`
- **Method:** `is_high_confidence(confidence, detection_type)`

### Fallback Manager
- **Get:** `get_fallback_manager()`
- **Status:** `get_status()` → mode, features, failure_count, last_error
- **Reset:** `reset()` → return to FULL mode

### Metrics Tracker
- **Get:** `DetectionMetricsTracker()`
- **Track:** `record_detection(type, success, confidence, duration_ms)`
- **Export:** `to_dict()` for each detection type

### Accuracy Tracker
- **Get:** `DetectionAccuracyTracker()`
- **Track:** `record_detection(type, success, confidence)`
- **Alert:** Triggers at <90% success or <70% confidence

### Logger
- **Get:** `get_detection_logger()`
- **Log:** `log_detection(type, success, confidence, details, duration_ms)`
- **Retention:** 30 days (configurable via env)

---

## Frontend Integration

### WebSocket Endpoint
**URL:** `wss://hostname/ws/detections` (auto-converts http to ws)

**Message Format:**
```json
{
  "type": "pot|card|player|action|system|error",
  "severity": "debug|info|success|warning|error|critical",
  "message": "Human-readable description",
  "data": { ... },
  "timestamp": 1234567890.123,
  "event_id": "optional-uuid",
  "correlation_id": "frame_abc123_1234567890"
}
```

### Frontend Components
- **DetectionLog** - Real-time event log with filtering
- **DetectionStateIndicator** - Current detection mode display
- **DetectionMetricsWidget** - Performance metrics visualization
- **DetectionLoadingState** - Initialization status

---

## Quick Debugging

### Check Window Detection
```python
from pokertool.desktop_independent_scraper import DesktopIndependentScraper
scraper = DesktopIndependentScraper()
windows = scraper.scan_for_poker_windows()
print(f"Found {len(windows)} windows")
for w in windows:
    print(f"  {w.title} - area={w.area}, visible={w.is_visible}")
```

### Check Smart Classification
```python
from pokertool.smart_poker_detector import SmartPokerDetector
detector = SmartPokerDetector()
score, reason = detector.classify_window("pokerstars.com - Table 5")
print(f"Score: {score}, Reason: {reason}")
```

### Check Thresholds
```python
from pokertool.detection_config import get_detection_config
config = get_detection_config()
should_emit = config.should_emit_event(0.75, 'card')
print(f"Should emit: {should_emit}")
```

### Check Fallback Status
```python
from pokertool.detection_fallback import get_fallback_manager
mgr = get_fallback_manager()
status = mgr.get_status()
print(f"Mode: {status['mode']}")
print(f"Available: {status['available_features']}")
```

---

**Complete Analysis File:** `/Users/georgeridout/Documents/github/pokertool/POKER_GAME_DETECTION_ANALYSIS.md` (1025 lines)
