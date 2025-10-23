# Detection Logging Improvements

## Summary
Enhanced detection logging and event emissions throughout the poker screen scraper to provide better real-time visibility into the detection process via WebSocket events and log files.

## Changes Made

### 1. Added Detection Event Emissions (Option 2)

Added `emit_detection_event()` calls for the following detections:

#### **Error Events**
- **Betfair detection errors** (line 600-605)
  - Event type: `error`
  - Severity: `error`
  - Includes error details and exception type

- **Universal detection errors** (line 1239-1244)
  - Event type: `error`
  - Severity: `error`
  - Includes error details and exception type

#### **Pot Detection** (line 1833-1839)
- Event type: `pot`
- Severity: `info`
- Emitted when pot size > 0
- Includes pot_size in data payload

#### **Hero Cards Detection** (line 1841-1851)
- Event type: `card`
- Severity: `success`
- Emitted when hero cards are detected
- Includes card count and card details (rank, suit)

#### **Board Cards Detection** (line 1853-1863)
- Event type: `card`
- Severity: `info`
- Emitted when community cards are detected
- Includes card count and card details (rank, suit)

#### **Player Detection** (line 1900-1921)
- Event type: `player`
- Severity: `info`
- Emitted when active players > 0
- Includes:
  - Active player count
  - Player details for up to 5 players (seat, name, stack, position, hero/dealer status)

### 2. Changed Log Levels from DEBUG to INFO (Option 3)

Changed critical detection logs from `logger.debug()` to `logger.info()`:

#### **Line 1741: Low Confidence Detection**
```python
logger.info(f"[TABLE DETECTION] Low confidence detection ({confidence:.1%}), extracting partial data anyway")
```

#### **Line 546: Ellipse Detection Error**
```python
logger.info(f"Ellipse detection error: {e}")
```

#### **Line 2478: Configured Poker Handle**
```python
logger.info(f"Using configured poker handle for hero detection: {configured_handle}")
```

#### **Line 2480: Poker Handle Load Error**
```python
logger.info(f"Could not load poker handle: {e}")
```

## Impact

### Before
- Only 2 detection events were emitted (success/no-detection)
- Most detection information only visible at DEBUG log level
- Events heavily throttled (1 per second for success, 1 per 5 seconds for failures)
- Limited real-time visibility into detection process

### After
- **8 additional detection events** emitted for:
  - Errors (2 types)
  - Pot detection
  - Card detection (hero and board)
  - Player detection
- Critical detection information now visible at INFO log level
- Better real-time WebSocket updates to connected clients
- Improved debuggability and monitoring

## Event Types and Severities

| Event Type | Severity | Trigger |
|------------|----------|---------|
| `error` | `error` | Detection exceptions |
| `pot` | `info` | Pot detected |
| `card` | `success` | Hero cards detected |
| `card` | `info` | Board cards detected |
| `player` | `info` | Players detected |
| `system` | `success` | Table detected (existing) |
| `system` | `warning` | No table detected (existing) |

## Testing

To verify detection logs are working:

### 1. Check Log Level
Ensure console logging is set to INFO (default):
```python
# master_logging.py:256
console_handler.setLevel(logging.INFO)
```

### 2. Connect to WebSocket
```bash
# WebSocket endpoint for detection events
wscat -c ws://localhost:5001/ws/detection
```

### 3. Check Logs
```bash
tail -f logs/pokertool_master.log | grep -E "TABLE DETECTION|cards detected|players detected|Pot detected"
```

### 4. Check Health Status
```bash
curl http://localhost:5001/api/system/health | jq '.components[] | select(.name=="detection_websocket")'
```

## Notes

- Detection events are queued if WebSocket is not connected
- Event loop is automatically registered on API startup (api.py:955)
- Events include structured data payloads for programmatic consumption
- Player data is limited to 5 players per event to avoid large payloads

## Future Enhancements

Consider adding detection events for:
- Action detection (bet, raise, fold, check, call)
- Dealer button position
- Blind positions (SB, BB)
- Tournament information
- Hand strength calculations
- Timing tells

## Files Modified

- `src/pokertool/modules/poker_screen_scraper_betfair.py`
  - Added 6 new `emit_detection_event()` calls
  - Changed 4 `logger.debug()` calls to `logger.info()`
  - Lines modified: 546, 600-605, 1239-1244, 1741, 1833-1921, 2478, 2480

## Related Files

- `src/pokertool/detection_events.py` - Event emission infrastructure
- `src/pokertool/api.py` - WebSocket broadcasting (line 596-615)
- `src/pokertool/master_logging.py` - Logging configuration

---

**Date**: 2025-10-22
**Author**: Claude Code Assistant
**Status**: Complete ✅
