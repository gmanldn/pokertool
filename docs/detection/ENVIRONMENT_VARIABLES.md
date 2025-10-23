# Detection System Environment Variables

Complete reference for all detection-related environment variables.

## Confidence Thresholds

### Card Detection
```bash
# Minimum confidence to accept card detection (default: 0.7)
DETECTION_CARD_MIN_CONFIDENCE=0.7

# High confidence threshold for cards (default: 0.9)
DETECTION_CARD_HIGH_CONFIDENCE=0.9
```

### Pot Detection
```bash
# Minimum confidence to accept pot detection (default: 0.6)
DETECTION_CARD_MIN_CONFIDENCE=0.7

# High confidence threshold for cards (default: 0.9)
DETECTION_CARD_HIGH_CONFIDENCE=0.9
```

### Pot Detection
```bash
# Minimum confidence to accept pot detection (default: 0.6)
DETECTION_POT_MIN_CONFIDENCE=0.6

# High confidence threshold for pot (default: 0.85)
DETECTION_POT_HIGH_CONFIDENCE=0.85
```

### Player Detection
```bash
# Minimum confidence to accept player detection (default: 0.65)
DETECTION_PLAYER_MIN_CONFIDENCE=0.65

# High confidence threshold for players (default: 0.88)
DETECTION_PLAYER_HIGH_CONFIDENCE=0.88
```

### Button/Position Detection
```bash
# Minimum confidence to accept button detection (default: 0.75)
DETECTION_BUTTON_MIN_CONFIDENCE=0.75

# High confidence threshold for button (default: 0.92)
DETECTION_BUTTON_HIGH_CONFIDENCE=0.92
```

### Action Detection
```bash
# Minimum confidence to accept action detection (default: 0.70)
DETECTION_ACTION_MIN_CONFIDENCE=0.70

# High confidence threshold for actions (default: 0.90)
DETECTION_ACTION_HIGH_CONFIDENCE=0.90
```

### Board Detection
```bash
# Minimum confidence to accept board card detection (default: 0.72)
DETECTION_BOARD_MIN_CONFIDENCE=0.72

# High confidence threshold for board (default: 0.91)
DETECTION_BOARD_HIGH_CONFIDENCE=0.91
```

### General Settings
```bash
# Minimum confidence to emit any event (default: 0.6)
DETECTION_MIN_EMIT_CONFIDENCE=0.6
```

## Logging Configuration

```bash
# Number of days to retain detection logs (default: 30)
DETECTION_LOG_RETENTION_DAYS=30

# Log level for detection system (default: INFO)
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
DETECTION_LOG_LEVEL=INFO

# Enable detailed detection logging (default: false)
DETECTION_ENABLE_VERBOSE_LOGGING=true
```

## Cache Configuration

```bash
# Time-to-live for cache entries in seconds (default: 2.0)
DETECTION_CACHE_TTL=2.0

# Maximum number of cache entries (default: 100)
DETECTION_CACHE_MAX_SIZE=100

# Enable detection cache (default: true)
DETECTION_ENABLE_CACHE=true
```

## Performance Configuration

```bash
# Target FPS for detection (default: 20)
DETECTION_TARGET_FPS=20

# Enable parallel detection (default: false)
DETECTION_ENABLE_PARALLEL=true

# Number of worker threads for parallel detection (default: 3)
DETECTION_WORKER_THREADS=3

# Enable GPU acceleration if available (default: false)
DETECTION_ENABLE_GPU=true
```

## Event System Configuration

```bash
# Event batching interval in seconds (default: 0.1)
DETECTION_EVENT_BATCH_INTERVAL=0.1

# Maximum events per batch (default: 50)
DETECTION_EVENT_MAX_BATCH_SIZE=50

# Enable event deduplication (default: true)
DETECTION_ENABLE_EVENT_DEDUP=true

# Event deduplication window in seconds (default: 1.0)
DETECTION_EVENT_DEDUP_WINDOW=1.0
```

## State Persistence

```bash
# Path to detection state file (default: logs/detection_state.json)
DETECTION_STATE_FILE=logs/detection_state.json

# Enable automatic state saving (default: true)
DETECTION_ENABLE_STATE_PERSISTENCE=true

# State save interval in seconds (default: 60)
DETECTION_STATE_SAVE_INTERVAL=60
```

## Metrics & Monitoring

```bash
# Enable metrics tracking (default: true)
DETECTION_ENABLE_METRICS=true

# Metrics aggregation window in seconds (default: 60)
DETECTION_METRICS_WINDOW=60

# Enable performance telemetry (default: true)
DETECTION_ENABLE_TELEMETRY=true
```

## Example Configuration File

Create `.env` in project root:

```bash
# .env - Detection System Configuration

# === Confidence Thresholds ===
DETECTION_CARD_MIN_CONFIDENCE=0.75
DETECTION_POT_MIN_CONFIDENCE=0.65
DETECTION_PLAYER_MIN_CONFIDENCE=0.70
DETECTION_MIN_EMIT_CONFIDENCE=0.65

# === Performance ===
DETECTION_TARGET_FPS=25
DETECTION_ENABLE_CACHE=true
DETECTION_CACHE_MAX_SIZE=150
DETECTION_ENABLE_PARALLEL=true

# === Logging ===
DETECTION_LOG_RETENTION_DAYS=30
DETECTION_LOG_LEVEL=INFO

# === Event System ===
DETECTION_EVENT_BATCH_INTERVAL=0.1
DETECTION_EVENT_MAX_BATCH_SIZE=50
DETECTION_ENABLE_EVENT_DEDUP=true

# === State Persistence ===
DETECTION_ENABLE_STATE_PERSISTENCE=true
DETECTION_STATE_SAVE_INTERVAL=60
```

## Production vs Development

### Development Settings
```bash
# Lower thresholds for more detections
DETECTION_MIN_EMIT_CONFIDENCE=0.5
DETECTION_LOG_LEVEL=DEBUG
DETECTION_ENABLE_VERBOSE_LOGGING=true
DETECTION_ENABLE_METRICS=true
```

### Production Settings
```bash
# Higher thresholds for quality
DETECTION_MIN_EMIT_CONFIDENCE=0.7
DETECTION_LOG_LEVEL=INFO
DETECTION_ENABLE_VERBOSE_LOGGING=false
DETECTION_ENABLE_CACHE=true
DETECTION_ENABLE_PARALLEL=true
```

## Loading Environment Variables

Detection modules automatically load from environment variables via `os.getenv()`.

**Python:**
```python
from src.pokertool.detection_config import get_detection_config

# Automatically loads from environment
config = get_detection_config()
```

**Shell:**
```bash
# Set for current session
export DETECTION_CARD_MIN_CONFIDENCE=0.8

# Or use .env file with python-dotenv
pip install python-dotenv
```

## Validation

To validate your configuration:

```python
from src.pokertool.detection_config import get_detection_config

config = get_detection_config()
print(f"Card min confidence: {config.card_min_confidence}")
print(f"Should emit event with 0.85: {config.should_emit_event(0.85, 'card')}")
```

## Troubleshooting

### Variables Not Loading
- Ensure variables are exported before starting application
- Check variable names match exactly (case-sensitive)
- Verify `.env` file is in correct location
- Confirm python-dotenv is installed if using .env file

### Invalid Values
- All confidence values must be between 0.0 and 1.0
- Numeric values must be valid floats/integers
- Boolean values should be 'true' or 'false' (lowercase)

### Permission Issues
- Ensure write permissions for log directory
- Check state file path is writable
- Verify cache directory exists
