# Detection System Documentation

## Overview

The PokerTool detection system provides comprehensive poker table monitoring with high accuracy and low latency. This document covers all detection modules and their usage.

## Core Modules

### 1. Detection Logger (`detection_logger.py`)
- Daily log rotation with 30-day retention
- Automatic severity levels based on confidence
- FPS and performance logging
- Global singleton pattern

**Usage:**
```python
from src.pokertool.detection_logger import get_detection_logger

logger = get_detection_logger()
logger.log_detection('card', success=True, confidence=0.95, duration_ms=45.2)
logger.log_fps(fps=22.5)
```

### 2. Detection Cache (`detection_cache.py`)
- LRU cache with 2-second TTL
- MD5 image region hashing
- Automatic expiration
- Max 100 entries

**Usage:**
```python
from src.pokertool.detection_cache import DetectionCache

cache = DetectionCache(max_size=100, ttl_seconds=2.0)
key = cache.hash_image_region(image_region)
result = cache.get(key)
if result is None:
    result = perform_detection(image_region)
    cache.set(key, result)
```

### 3. Detection Configuration (`detection_config.py`)
- Type-specific confidence thresholds
- Environment variable support
- Confidence level helpers

**Usage:**
```python
from src.pokertool.detection_config import get_detection_config

config = get_detection_config()
if config.should_emit_event(0.85, 'card'):
    emit_event(...)
level = config.get_confidence_level(0.92, 'pot')  # Returns 'HIGH'
```

### 4. Event System (`detection_events.py`)
- 16 event types with enums
- Structured event payloads
- Automatic confidence level calculation

**Usage:**
```python
from src.pokertool.detection_events import emit_pot_event, DetectionEventType

emit_pot_event(
    pot_size=125.50,
    confidence=0.88,
    detection_method='OCR',
    duration_ms=42.1
)
```

### 5. FPS Counter (`detection_fps_counter.py`)
- 60-frame rolling window
- Accurate FPS calculation

**Usage:**
```python
from src.pokertool.detection_fps_counter import get_fps_counter

fps_counter = get_fps_counter()
fps_counter.tick()  # Call each frame
current_fps = fps_counter.get_fps()
```

### 6. Event Batching (`detection_event_batcher.py`)
- 100ms batching interval
- Max 50 events per batch
- Thread-safe

**Usage:**
```python
from src.pokertool.detection_event_batcher import DetectionEventBatcher

batcher = DetectionEventBatcher(batch_interval=0.1)
batcher.start(lambda events: send_to_websocket(events))
batcher.add_event({'type': 'pot', 'value': 100})
```

### 7. Metrics Tracking (`detection_metrics_tracker.py`)
- Per-type metrics aggregation
- Confidence and duration statistics
- Thread-safe operations

**Usage:**
```python
from src.pokertool.detection_metrics_tracker import DetectionMetricsTracker

tracker = DetectionMetricsTracker()
tracker.record_detection('card', success=True, confidence=0.91, duration_ms=38.5)
metrics = tracker.get_metrics('card')
```

### 8. Sanity Checks (`detection_sanity_checks.py`)
- Logical consistency validation
- Automatic rejection of impossible states
- Severity levels (WARNING/ERROR/CRITICAL)

**Usage:**
```python
from src.pokertool.detection_sanity_checks import validate_detection_result

is_valid, errors = validate_detection_result(detection_data)
if not is_valid:
    log_validation_errors(errors)
```

### 9. State Persistence (`detection_state_persistence.py`)
- JSON-based state saving
- Crash recovery support

**Usage:**
```python
from src.pokertool.detection_state_persistence import DetectionStatePersistence

persistence = DetectionStatePersistence()
persistence.save_state({'pot': 150, 'cards': ['Ah', 'Kd']})
state = persistence.load_state()
```

### 10. Board Texture Analysis (`board_texture_analyzer.py`)
- Wet/dry/semi-wet classification
- Connectivity scoring
- Flush/straight possibility detection

**Usage:**
```python
from src.pokertool.board_texture_analyzer import analyze_flop

texture = analyze_flop('Kh', 'Qh', 'Jh')
print(texture.wetness)  # BoardWetness.WET
print(texture.has_flush_draw)  # True
print(texture.description)  # "Very wet monotone with flush draw and straight draw"
```

## Configuration

All detection modules support environment variable configuration:

```bash
# Confidence thresholds
export DETECTION_CARD_MIN_CONFIDENCE=0.7
export DETECTION_POT_MIN_CONFIDENCE=0.6
export DETECTION_MIN_EMIT_CONFIDENCE=0.6

# Logging
export DETECTION_LOG_RETENTION_DAYS=30

# Cache
export DETECTION_CACHE_TTL=2.0
export DETECTION_CACHE_MAX_SIZE=100
```

## Best Practices

1. **Always use confidence thresholds** to filter low-quality detections
2. **Enable caching** for repeated image regions to improve performance
3. **Monitor FPS** to ensure detection keeps up with real-time requirements
4. **Use event batching** to reduce WebSocket overhead
5. **Review sanity check violations** to catch bugs early
6. **Enable state persistence** for crash recovery

## Performance

- Target: 20+ FPS detection rate
- Typical latency: 40-80ms per frame
- Cache hit rate: 60-80% in stable conditions
- Event throughput: 100+ events/second

## Troubleshooting

### Low FPS
- Check CPU usage
- Enable detection cache
- Reduce image resolution
- Use GPU acceleration if available

### Low Confidence
- Improve lighting conditions
- Increase OCR threshold
- Add more training data
- Check for screen glare

### High Latency
- Profile detection hot paths
- Enable parallel detection
- Optimize image preprocessing
- Use adaptive ROI sizing

## Related Documentation

- [Environment Variables Guide](./ENVIRONMENT_VARIABLES.md)
- [Detection Examples](./EXAMPLES.md)
- [Performance Tuning](./PERFORMANCE.md)
