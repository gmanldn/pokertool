# Detection System Quick Reference

## Import Statements

```python
# Core
from src.pokertool.detection_logger import get_detection_logger
from src.pokertool.detection_config import get_detection_config
from src.pokertool.detection_cache import DetectionCache
from src.pokertool.detection_fps_counter import get_fps_counter

# Events
from src.pokertool.detection_events import (
    emit_pot_event, emit_card_event, emit_player_event
)

# Analysis
from src.pokertool.board_texture_analyzer import analyze_flop

# Metrics
from src.pokertool.detection_metrics_tracker import DetectionMetricsTracker
```

## Common Patterns

### Initialize Detection System
```python
logger = get_detection_logger()
config = get_detection_config()
cache = DetectionCache()
fps_counter = get_fps_counter()
```

### Log Detection
```python
logger.log_detection('card', success=True, confidence=0.92, duration_ms=45.2)
```

### Check Confidence
```python
if config.should_emit_event(0.85, 'card'):
    emit_card_event(...)
```

### Cache Result
```python
key = cache.hash_image_region(image)
result = cache.get(key) or perform_detection(image)
cache.set(key, result)
```

### Track FPS
```python
fps_counter.tick()
print(f"FPS: {fps_counter.get_fps():.1f}")
```

### Analyze Board
```python
texture = analyze_flop('Kh', 'Qh', 'Jh')
print(texture.wetness.value)  # 'wet'
```

## Environment Variables

```bash
# Essential
DETECTION_MIN_EMIT_CONFIDENCE=0.7
DETECTION_ENABLE_CACHE=true
DETECTION_LOG_LEVEL=INFO

# Performance
DETECTION_CACHE_MAX_SIZE=150
DETECTION_EVENT_BATCH_INTERVAL=0.1
```

## File Locations

- Logs: `logs/detection.log`
- State: `logs/detection_state.json`
- Config: Environment variables
- Docs: `docs/detection/`
