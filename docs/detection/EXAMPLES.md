# Detection System Usage Examples

Practical examples for using the PokerTool detection system.

## Basic Detection Setup

```python
from src.pokertool.detection_logger import get_detection_logger
from src.pokertool.detection_config import get_detection_config
from src.pokertool.detection_cache import DetectionCache
from src.pokertool.detection_fps_counter import get_fps_counter

# Initialize detection components
logger = get_detection_logger()
config = get_detection_config()
cache = DetectionCache()
fps_counter = get_fps_counter()

def detect_table_state(screenshot):
    """Main detection loop."""
    fps_counter.tick()

    # Check cache first
    cache_key = cache.hash_image_region(screenshot)
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.log_detection('cache_hit', True, 1.0, duration_ms=0.1)
        return cached_result

    # Perform detection
    start_time = time.time()
    result = perform_actual_detection(screenshot)
    duration_ms = (time.time() - start_time) * 1000

    # Log result
    logger.log_detection(
        'full_scan',
        success=True,
        confidence=result.confidence,
        duration_ms=duration_ms
    )

    # Cache if high confidence
    if config.is_high_confidence(result.confidence, 'general'):
        cache.set(cache_key, result)

    # Log FPS periodically
    if fps_counter.get_fps() > 0:
        logger.log_fps(fps_counter.get_fps())

    return result
```

## Card Detection with Confidence Filtering

```python
from src.pokertool.detection_config import get_detection_config
from src.pokertool.detection_events import emit_card_event

config = get_detection_config()

def detect_cards(card_region):
    """Detect cards with confidence filtering."""
    cards = ocr_detect_cards(card_region)

    for card in cards:
        # Check if confidence meets threshold
        if config.should_emit_event(card.confidence, 'card'):
            emit_card_event(
                cards=[{'rank': card.rank, 'suit': card.suit}],
                card_type='hero' if card.is_hero else 'board',
                confidence=card.confidence,
                detection_method='OCR+Template',
                duration_ms=card.detection_time_ms
            )

            # Log confidence level
            level = config.get_confidence_level(card.confidence, 'card')
            print(f"Card {card.rank}{card.suit}: {level} confidence")
        else:
            print(f"Card detection below threshold: {card.confidence}")
```

## Board Texture Analysis

```python
from src.pokertool.board_texture_analyzer import analyze_flop, analyze_turn

# Analyze flop
flop = analyze_flop('Kh', 'Qh', 'Jh')
print(f"Wetness: {flop.wetness.value}")  # "wet"
print(f"Coordination: {flop.coordination.value}")  # "monotone"
print(f"Has flush draw: {flop.has_flush_draw}")  # True
print(f"Description: {flop.description}")
# Output: "Very wet monotone with flush draw and straight draw"

# Analyze turn
turn = analyze_turn('7d', '7h', '2c', 'Ah')
print(f"Wetness: {turn.wetness.value}")  # "dry"
print(f"Has pair: {turn.has_pair}")  # True
print(f"Connectivity: {turn.connectivity_score}")  # 0.23 (low)
```

## Event Batching for WebSocket

```python
from src.pokertool.detection_event_batcher import DetectionEventBatcher
import asyncio

# Initialize batcher
batcher = DetectionEventBatcher(batch_interval=0.1, max_batch_size=50)

async def send_batch_to_websocket(events):
    """Send batched events via WebSocket."""
    await websocket.send_json({
        'type': 'batch',
        'events': events,
        'count': len(events)
    })

# Start batching
batcher.start(lambda events: asyncio.create_task(send_batch_to_websocket(events)))

# Add events as they occur
batcher.add_event({'type': 'pot', 'size': 150})
batcher.add_event({'type': 'card', 'rank': 'A', 'suit': 'h'})

# Events are automatically batched and sent every 100ms
```

## Metrics Tracking and Reporting

```python
from src.pokertool.detection_metrics_tracker import DetectionMetricsTracker

tracker = DetectionMetricsTracker()

# Record detections
tracker.record_detection('card', success=True, confidence=0.92, duration_ms=45.2)
tracker.record_detection('pot', success=True, confidence=0.88, duration_ms=38.1)
tracker.record_detection('card', success=False, confidence=0.42, duration_ms=52.3)

# Get metrics for specific type
card_metrics = tracker.get_metrics('card')
print(f"Total card detections: {card_metrics.total_detections}")
print(f"Success rate: {card_metrics.successful_detections / card_metrics.total_detections * 100:.1f}%")
print(f"Average confidence: {card_metrics.avg_confidence:.2f}")
print(f"Average duration: {card_metrics.avg_duration_ms:.1f}ms")

# Get all metrics
all_metrics = tracker.get_all_metrics()
for det_type, metrics in all_metrics.items():
    print(f"{det_type}: {metrics.total_detections} detections")
```

## State Persistence and Recovery

```python
from src.pokertool.detection_state_persistence import DetectionStatePersistence

persistence = DetectionStatePersistence(state_file='logs/detection_state.json')

# Save current state
current_state = {
    'pot': 125.50,
    'board_cards': ['Ah', 'Kd', 'Qc'],
    'hero_cards': ['Js', 'Jh'],
    'players': [
        {'seat': 1, 'name': 'Player1', 'stack': 1000},
        {'seat': 2, 'name': 'Player2', 'stack': 850}
    ],
    'button_position': 1
}

persistence.save_state(current_state)

# Load state after crash
recovered_state = persistence.load_state()
if recovered_state:
    print(f"Recovered pot: {recovered_state['pot']}")
    print(f"Recovered board: {recovered_state['board_cards']}")
```

## Sanity Checks and Validation

```python
from src.pokertool.detection_sanity_checks import validate_pot_size, validate_player_stack

# Validate pot size
pot = 150.0
previous_pot = 100.0
bet_amount = 50.0

is_valid = validate_pot_size(pot, previous_pot, bet_amount)
if not is_valid:
    print("Warning: Pot size doesn't match expected value!")

# Validate player stack
current_stack = 850.0
previous_stack = 900.0
action_amount = 50.0

is_valid = validate_player_stack(current_stack, previous_stack, action_amount)
if not is_valid:
    print("Error: Stack size inconsistent with action!")
```

## Error Handling and Logging

```python
from src.pokertool.detection_error_logger import log_detection_error
from src.pokertool.detection_fallback import DetectionFallbackManager

fallback_manager = DetectionFallbackManager()

def detect_with_fallback(image_region):
    """Detection with automatic fallback."""
    try:
        result = perform_detection(image_region)
        fallback_manager.record_success()
        return result
    except Exception as e:
        # Log error with context
        log_detection_error(
            detection_type='card',
            error=e,
            context={'region_size': image_region.shape}
        )

        # Handle failure and get fallback
        fallback_result = fallback_manager.handle_detection_failure(
            error=e,
            detection_type='card',
            last_known_state={'cards': ['Ah', 'Kd']}
        )

        return fallback_result
```

## Complete Detection Pipeline

```python
from src.pokertool.detection_state_dispatcher import get_dispatcher
from src.pokertool.detection_events import emit_pot_event, emit_card_event

dispatcher = get_dispatcher()

def run_detection_pipeline(screenshot):
    """Complete detection pipeline."""
    # Begin frame for correlation
    frame_id = dispatcher.begin_frame()

    try:
        # Detect pot
        pot_size = detect_pot(screenshot)
        dispatcher.update_pot(pot_size)

        # Detect board cards
        board_cards = detect_board(screenshot)
        dispatcher.update_board_cards(board_cards)

        # Detect hero cards
        hero_cards = detect_hero_cards(screenshot)
        dispatcher.update_hero_cards(hero_cards)

        # Detect players
        for seat in range(1, 10):
            player = detect_player(screenshot, seat)
            if player:
                dispatcher.update_player(
                    seat=seat,
                    name=player.name,
                    stack=player.stack,
                    is_active=player.is_active
                )

        # Update performance metrics
        fps = fps_counter.get_fps()
        frame_time = get_frame_time_ms()
        dispatcher.update_performance(fps, frame_time)

    finally:
        # End frame
        dispatcher.end_frame()
```

## Configuration Examples

### Development Configuration
```python
import os

# Set environment for development
os.environ['DETECTION_CARD_MIN_CONFIDENCE'] = '0.6'
os.environ['DETECTION_MIN_EMIT_CONFIDENCE'] = '0.5'
os.environ['DETECTION_LOG_LEVEL'] = 'DEBUG'
os.environ['DETECTION_ENABLE_VERBOSE_LOGGING'] = 'true'

from src.pokertool.detection_config import reload_detection_config

config = reload_detection_config()
print(f"Development config loaded: card_min={config.card_min_confidence}")
```

### Production Configuration
```python
import os

# Set environment for production
os.environ['DETECTION_CARD_MIN_CONFIDENCE'] = '0.8'
os.environ['DETECTION_MIN_EMIT_CONFIDENCE'] = '0.7'
os.environ['DETECTION_ENABLE_CACHE'] = 'true'
os.environ['DETECTION_ENABLE_PARALLEL'] = 'true'

config = reload_detection_config()
```

## Testing Detection Components

```python
import pytest
from src.pokertool.board_texture_analyzer import analyze_flop

def test_wet_board():
    """Test wet board classification."""
    texture = analyze_flop('Kh', 'Qh', 'Jh')
    assert texture.wetness.value == 'wet'
    assert texture.has_flush_draw == True
    assert texture.coordination.value == 'monotone'

def test_dry_board():
    """Test dry board classification."""
    texture = analyze_flop('7d', '7h', '2c')
    assert texture.wetness.value == 'dry'
    assert texture.has_pair == True
    assert texture.coordination.value == 'rainbow'
```
