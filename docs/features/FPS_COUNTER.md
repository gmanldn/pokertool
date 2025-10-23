# Detection FPS Counter

## Overview

The Detection FPS Counter is a high-performance monitoring system for tracking frames-per-second (FPS) metrics across different detection types in PokerTool. It provides real-time FPS monitoring, historical metrics, and per-detection-type tracking.

## Features

- **Per-Detection-Type Tracking**: Track FPS separately for card detection, player detection, pot detection, etc.
- **Sliding Window Metrics**: Configurable window size for calculating averages
- **Thread-Safe**: Safe to use across multiple threads
- **Low Overhead**: Minimal performance impact using efficient data structures
- **Comprehensive Metrics**: Current FPS, average FPS, min/max FPS, frame count, uptime

## Installation

The FPS counter is included in the `performance_telemetry` module:

```python
from pokertool.performance_telemetry import (
    DetectionFPSCounter,
    get_fps_counter,
    reset_fps_counter
)
```

## Usage

### Basic Usage

```python
from pokertool.performance_telemetry import get_fps_counter

# Get the global FPS counter instance
fps_counter = get_fps_counter()

# Record a frame for card detection
fps_counter.record_frame('card_detection')

# Get metrics
metrics = fps_counter.get_metrics('card_detection')
print(f"Current FPS: {metrics['fps']}")
print(f"Average FPS: {metrics['avg_fps']}")
print(f"Min/Max FPS: {metrics['min_fps']} / {metrics['max_fps']}")
print(f"Frame count: {metrics['frame_count']}")
```

### In Detection Loops

```python
fps_counter = get_fps_counter()

while detection_running:
    # Perform detection
    detected_cards = detect_cards(screenshot)

    # Record frame
    fps_counter.record_frame('card_detection')

    # Optional: Log metrics every 100 frames
    metrics = fps_counter.get_metrics('card_detection')
    if metrics['frame_count'] % 100 == 0:
        fps_counter.log_metrics('card_detection')
```

### Multiple Detection Types

```python
fps_counter = get_fps_counter()

# Track different detection types
fps_counter.record_frame('card_detection')
fps_counter.record_frame('player_detection')
fps_counter.record_frame('pot_detection')

# Get all metrics
all_metrics = fps_counter.get_all_metrics()
for detection_type, metrics in all_metrics.items():
    print(f"{detection_type}: {metrics['avg_fps']:.1f} FPS")
```

### Custom Instance

```python
from pokertool.performance_telemetry import DetectionFPSCounter

# Create a custom instance with smaller window
counter = DetectionFPSCounter(window_size=50)
counter.record_frame('my_detection')
metrics = counter.get_metrics('my_detection')
```

## API Reference

### DetectionFPSCounter Class

#### Constructor

```python
DetectionFPSCounter(window_size: int = 100)
```

**Parameters:**
- `window_size`: Number of frames to track in sliding window (default: 100)

#### Methods

##### record_frame(detection_type: str = 'default')

Record a frame for the given detection type.

**Parameters:**
- `detection_type`: Type of detection (e.g., 'card_detection', 'player_detection')

**Example:**
```python
counter.record_frame('card_detection')
```

##### get_metrics(detection_type: str = 'default') -> Dict[str, Any]

Get FPS metrics for a specific detection type.

**Returns:**
```python
{
    'fps': 25.3,           # Current FPS
    'avg_fps': 24.8,       # Average FPS over window
    'min_fps': 20.1,       # Minimum FPS in window
    'max_fps': 29.5,       # Maximum FPS in window
    'frame_count': 100,    # Number of frames recorded
    'uptime_seconds': 42.5 # Time since counter started
}
```

##### get_all_metrics() -> Dict[str, Dict[str, Any]]

Get metrics for all detection types.

**Returns:**
```python
{
    'card_detection': {...},
    'player_detection': {...},
    'pot_detection': {...}
}
```

##### reset(detection_type: Optional[str] = None)

Reset counter for a specific type or all types.

**Parameters:**
- `detection_type`: Type to reset, or None to reset all

**Example:**
```python
counter.reset('card_detection')  # Reset specific type
counter.reset()                  # Reset all types
```

##### log_metrics(detection_type: Optional[str] = None, logger_instance: Optional[logging.Logger] = None)

Log FPS metrics to logger.

**Parameters:**
- `detection_type`: Specific type to log, or None for all types
- `logger_instance`: Logger to use, or None for module logger

**Example:**
```python
counter.log_metrics('card_detection')
counter.log_metrics()  # Log all types
```

### Global Functions

#### get_fps_counter() -> DetectionFPSCounter

Get or create the global FPS counter singleton.

**Returns:** Global DetectionFPSCounter instance

**Example:**
```python
from pokertool.performance_telemetry import get_fps_counter
counter = get_fps_counter()
```

#### reset_fps_counter(detection_type: Optional[str] = None)

Reset the global FPS counter.

**Parameters:**
- `detection_type`: Type to reset, or None to reset all

**Example:**
```python
from pokertool.performance_telemetry import reset_fps_counter
reset_fps_counter('card_detection')
```

## Integration Examples

### With Screen Scraper

```python
# In poker_screen_scraper_betfair.py
from pokertool.performance_telemetry import get_fps_counter

class PokerScreenScraper:
    def __init__(self):
        self.fps_counter = get_fps_counter()

    def detect_table_state(self, screenshot):
        # Detect cards
        cards = self.detect_cards(screenshot)
        self.fps_counter.record_frame('card_detection')

        # Detect players
        players = self.detect_players(screenshot)
        self.fps_counter.record_frame('player_detection')

        # Detect pot
        pot = self.detect_pot(screenshot)
        self.fps_counter.record_frame('pot_detection')

        # Log metrics every 5 seconds
        if time.time() - self.last_log > 5.0:
            self.fps_counter.log_metrics()
            self.last_log = time.time()
```

### With WebSocket API

```python
# In api.py - Add FPS metrics endpoint
from pokertool.performance_telemetry import get_fps_counter

@app.get("/api/performance/fps")
async def get_fps_metrics():
    """Get current FPS metrics for all detection types."""
    fps_counter = get_fps_counter()
    return fps_counter.get_all_metrics()
```

### With Frontend Dashboard

```typescript
// In PerformanceDashboard.tsx
const [fpsMetrics, setFpsMetrics] = useState({});

useEffect(() => {
  const interval = setInterval(async () => {
    const response = await fetch('/api/performance/fps');
    const metrics = await response.json();
    setFpsMetrics(metrics);
  }, 1000);  // Update every second

  return () => clearInterval(interval);
}, []);

return (
  <div>
    {Object.entries(fpsMetrics).map(([type, metrics]) => (
      <div key={type}>
        <h3>{type}</h3>
        <p>Current: {metrics.fps} FPS</p>
        <p>Average: {metrics.avg_fps} FPS</p>
      </div>
    ))}
  </div>
);
```

## Performance Considerations

### Overhead

The FPS counter is designed for minimal overhead:
- Recording a frame: ~1-2 μs
- Getting metrics: ~5-10 μs
- Memory usage: ~2KB per detection type (at default window size of 100)

### Best Practices

1. **Use appropriate window size**: Smaller windows (50) for real-time responsiveness, larger windows (200) for smoother averages
2. **Avoid excessive logging**: Log metrics every few seconds rather than every frame
3. **Use global instance**: For most cases, use `get_fps_counter()` to avoid multiple instances
4. **Clean up old data**: Call `reset()` when changing detection modes

## Troubleshooting

### FPS shows 0.0

**Cause:** Less than 2 frames recorded
**Solution:** Record at least 2 frames before checking metrics

### Metrics seem inaccurate

**Cause:** System timing variations or insufficient samples
**Solution:** Increase window size or check system load

### High memory usage

**Cause:** Very large window size
**Solution:** Reduce window size to 50-100 frames

## Testing

Run the comprehensive test suite:

```bash
pytest tests/test_fps_counter.py -v
```

Tests cover:
- Basic recording and metrics
- Multiple detection types
- Window size limits
- Thread safety
- Accuracy validation
- Global instance management

## Version History

### v1.0.0 (2025-10-23)
- Initial implementation
- Per-detection-type tracking
- Sliding window metrics
- Thread-safe operation
- Global singleton support
- Comprehensive test coverage

## See Also

- [Performance Telemetry System](../performance_telemetry.md)
- [Detection System Architecture](../detection_architecture.md)
- [Performance Optimization Guide](../optimization.md)
