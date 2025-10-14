# Scraper Learning System Documentation

## Overview

The Pokertool scraper now includes an **Adaptive Learning System** that automatically improves OCR accuracy, detection reliability, and overall performance over time. The system learns from multiple sources and continuously optimizes itself for your specific environment and usage patterns.

## Key Features

### 1. **Environment Profiling**
- Automatically detects your screen resolution, brightness, and color profile
- Learns optimal detection parameters for each unique environment
- Adapts thresholds based on success rates in each environment
- Stores profiles persistently across sessions

### 2. **OCR Strategy Performance Tracking**
- Monitors success rates of different OCR strategies (OTSU, adaptive, CLAHE, bilateral filters)
- Automatically prioritizes best-performing strategies
- Tracks execution time vs accuracy trade-offs
- Adapts to different text rendering styles

### 3. **Adaptive Parameter Tuning**
- Automatically adjusts detection thresholds based on recent performance
- Tunes card detection parameters (area ranges, aspect ratios)
- Optimizes OCR scaling factors
- Balances speed vs accuracy based on your needs

### 4. **CDP-Based Ground Truth Learning**
- When Chrome DevTools Protocol (CDP) is available, uses it as 100% accurate ground truth
- Compares OCR extractions against CDP data
- Learns from discrepancies to improve OCR accuracy
- Tracks accuracy trends over time

### 5. **User Feedback Integration**
- Records user corrections from validation workflows
- Learns from manual fixes
- Improves strategy selection based on correction patterns
- Builds pattern library from validated data

### 6. **Pattern Learning**
- Learns common player name patterns
- Remembers typical stack sizes for different stake levels
- Identifies common pot size ranges
- Validates extractions against learned patterns

## How It Works

### Automatic Learning
The learning system operates transparently in the background:

1. **On Every Detection:**
   - Records success/failure and confidence
   - Updates environment profile
   - Tracks which strategies worked

2. **During Extraction:**
   - Tries multiple OCR strategies
   - Records which ones succeed
   - Builds performance statistics

3. **With CDP Connected:**
   - Compares OCR vs CDP data
   - Calculates accuracy metrics
   - Learns from differences

4. **From User Feedback:**
   - Records corrections
   - Updates strategy rankings
   - Improves validation confidence

### Persistent Learning
All learned data is saved automatically:
- **Location:** `~/.pokertool/learning/`
- **Files:**
  - `environment_profiles.json` - Environment-specific settings
  - `ocr_strategies.json` - OCR performance statistics
  - `adaptive_params.json` - Current tuned parameters
  - `learned_patterns.json` - Known patterns and values

## Usage

### Basic Usage (Automatic)
The learning system is **enabled by default** and requires no configuration:

```python
from pokertool.modules.poker_screen_scraper_betfair import create_scraper

# Learning is enabled automatically
scraper = create_scraper('BETFAIR')

# Use normally - learning happens in background
state = scraper.analyze_table()
```

### Viewing Learning Statistics

Use the built-in stats viewer to monitor learning progress:

```bash
# View learning statistics
cd src
python -m pokertool.view_learning_stats

# View detailed statistics
python -m pokertool.view_learning_stats --detailed

# Reset learning data (starts fresh)
python -m pokertool.view_learning_stats --reset
```

### Programmatic Access

```python
# Get learning report
report = scraper.get_learning_report()
print(f"Environment profiles: {report['environment_profiles']['total']}")
print(f"Recent success rate: {report['recent_performance']['success_rate']:.1%}")

# Print human-readable report
scraper.print_learning_report()

# Record user feedback
scraper.record_user_feedback(
    extraction_type='pot_size',
    extracted_value=12.50,
    corrected_value=12.75,
    strategy_used='otsu_threshold'
)

# Save learning data manually
scraper.save_learning_data()
```

### Disabling Learning

If you don't want the learning system (not recommended):

```python
scraper = PokerScreenScraper(
    site=PokerSite.BETFAIR,
    use_cdp=True,
    enable_learning=False  # Disable learning
)
```

## Learning Metrics

### Success Rate
- Percentage of successful detections/extractions
- Target: >90% for well-configured environments
- Improves over time as system learns

### Confidence Score
- Detection confidence (0.0 - 1.0)
- Higher is better
- Used for adaptive threshold tuning

### Execution Time
- Time taken for detection/extraction (milliseconds)
- System balances speed vs accuracy
- Optimizes based on your hardware

### Accuracy (with CDP)
- Percentage match between OCR and CDP ground truth
- Target: >95% for critical fields (pot size, stacks)
- Best metric for OCR quality

## Advanced Features

### CDP Ground Truth Learning

For maximum learning effectiveness, connect to Betfair Poker via Chrome with remote debugging:

```bash
# Launch Chrome with remote debugging
chrome --remote-debugging-port=9222 https://poker.betfair.com
```

Then connect in your code:

```python
scraper = create_scraper('BETFAIR')
scraper.connect_to_chrome(tab_filter='betfair')

# Now every extraction compares OCR vs CDP
# System learns from any discrepancies
state = scraper.analyze_table()
```

### Environment Profiling

The system automatically creates profiles for each unique environment:

**Environment Signature = (Resolution, Brightness, Color Profile)**

Example environments:
- `2560x1440_b128_c7f3a9b1` - Desktop monitor, normal brightness
- `1920x1080_b180_c4a2e6f8` - Laptop, high brightness
- `3840x2160_b95_c9e1d3c7` - 4K monitor, dim lighting

Each environment gets its own optimized parameters.

### Strategy Performance Tracking

The system tracks multiple OCR strategies:

1. **OTSU Threshold** - Good for high-contrast text
2. **Adaptive Threshold** - Handles varying lighting
3. **CLAHE Enhancement** - Improves low-contrast text
4. **Bilateral Filter** - Reduces noise while preserving edges
5. **Multiple PSM Modes** - Different text layout assumptions

Best performers are automatically prioritized.

### Adaptive Tuning Examples

**Detection Threshold:**
- Starts at 0.40 (default)
- Lowers to 0.35 if missing tables (high false negative rate)
- Raises to 0.50 if very high success rate (optimize for speed)

**Card Area Range:**
- Adjusts min/max area based on actual card sizes detected
- Adapts to high-resolution vs standard displays

**OCR Scale Factor:**
- Increases for small text (improves accuracy)
- Decreases for large text (improves speed)

## Troubleshooting

### Learning System Not Working?

Check these common issues:

1. **Storage permissions:**
   ```bash
   ls -la ~/.pokertool/learning/
   # Should show 4 JSON files
   ```

2. **Import errors:**
   ```python
   from pokertool.modules.scraper_learning_system import LEARNING_SYSTEM_AVAILABLE
   print(LEARNING_SYSTEM_AVAILABLE)  # Should be True
   ```

3. **No data accumulating:**
   - Make sure scraper is actually running
   - Check that `enable_learning=True` (default)
   - View stats: `python -m pokertool.view_learning_stats`

### Poor Learning Performance?

If the system isn't improving:

1. **Not enough data:** Need at least 50-100 detections for meaningful learning
2. **Inconsistent environment:** Changing lighting/resolution prevents profile building
3. **No CDP connection:** Connect to Chrome for best learning
4. **Old learned data:** Try resetting: `python -m pokertool.view_learning_stats --reset`

### Reset Learning Data

If you want to start fresh:

```bash
# Interactive reset (requires confirmation)
cd src
python -m pokertool.view_learning_stats --reset

# Manual reset
rm -rf ~/.pokertool/learning/*.json
```

## Performance Impact

The learning system is designed to be lightweight:

- **Memory:** ~5-10 MB for typical usage
- **Disk:** <1 MB for learned data
- **CPU:** <1ms overhead per detection
- **Storage writes:** Only every 20 detections (batched)

## Best Practices

### For Optimal Learning:

1. ✅ **Connect CDP when possible** - Provides ground truth data
2. ✅ **Use consistent environment** - Helps build reliable profiles
3. ✅ **Record user feedback** - Accelerates learning from corrections
4. ✅ **Monitor statistics** - Check progress weekly
5. ✅ **Let it run for 100+ detections** - Give it time to learn

### To Avoid:

1. ❌ **Don't reset data frequently** - Throws away learned optimizations
2. ❌ **Don't disable learning** - Loses adaptive benefits
3. ❌ **Don't mix wildly different environments** - Confuses profiling
4. ❌ **Don't ignore feedback opportunities** - Missed learning chances

## Example Learning Timeline

**Day 1-2 (0-50 detections):**
- System explores different strategies
- Environment profiles begin forming
- Success rate: ~70-80%

**Week 1 (50-200 detections):**
- Best strategies identified
- Parameters tuning to your environment
- Success rate: ~85-90%

**Week 2+ (200+ detections):**
- Highly optimized for your setup
- Rare false positives/negatives
- Success rate: ~92-97%

**With CDP (any time):**
- OCR accuracy improves rapidly
- Learns from every comparison
- Reaches >95% accuracy quickly

## Architecture

```
ScraperLearningSystem
├── Environment Profiling
│   ├── Signature Detection (Resolution, Brightness, Colors)
│   ├── Profile Management (Create, Update, Select)
│   └── Adaptive Thresholds (Auto-tune based on success)
│
├── OCR Strategy Tracking
│   ├── Strategy Registry (OTSU, Adaptive, CLAHE, etc.)
│   ├── Performance Stats (Success rate, Time, Attempts)
│   └── Auto-Prioritization (Best strategies first)
│
├── Adaptive Parameters
│   ├── Detection Threshold (0.25 - 0.60)
│   ├── Card Detection (Area, Aspect ratio)
│   └── OCR Settings (Scale, Config)
│
├── CDP Learning
│   ├── Ground Truth Collection
│   ├── OCR Comparison (Calculate accuracy)
│   └── Accuracy Trending
│
├── Feedback Integration
│   ├── User Corrections
│   ├── Validation Results
│   └── Pattern Building
│
└── Persistence
    ├── JSON Storage (~/.pokertool/learning/)
    ├── Auto-save (Every 20 updates)
    └── Load on startup
```

## API Reference

### `ScraperLearningSystem`

Main learning system class.

**Methods:**

- `get_environment_profile(image)` - Get profile for current environment
- `update_environment_profile(image, success, time_ms)` - Update after detection
- `record_ocr_attempt(type, strategy, result)` - Record OCR attempt
- `record_ocr_success(type, strategy, time_ms)` - Record success
- `record_ocr_failure(type, strategy)` - Record failure
- `get_best_ocr_strategies(type, top_k=3)` - Get best strategies
- `get_adaptive_parameters()` - Get current tuned parameters
- `record_detection_result(success, confidence, time_ms)` - Record detection
- `record_cdp_ground_truth(cdp_data)` - Record CDP data
- `compare_ocr_vs_cdp(ocr, cdp, types)` - Compare and learn
- `record_user_feedback(feedback)` - Record correction
- `get_learning_report()` - Get full report
- `print_learning_report()` - Print readable report
- `save()` - Save to disk
- `reset_learning_data()` - Clear all data

### `PokerScreenScraper` Learning Methods

**Methods:**

- `get_learning_report()` - Get learning system report
- `print_learning_report()` - Print learning report
- `record_user_feedback(type, extracted, corrected, strategy)` - Record feedback
- `save_learning_data()` - Manually save learning data

### Data Models

- `ExtractionType` - Enum of extraction types
- `EnvironmentSignature` - Environment fingerprint
- `OCRStrategyResult` - Result from OCR attempt
- `OCRStrategyStats` - Performance statistics
- `EnvironmentProfile` - Environment-specific settings
- `ExtractionFeedback` - User correction record
- `CDPGroundTruth` - Ground truth from CDP

## Future Enhancements

Potential improvements for future versions:

- **Neural network integration** - ML-based OCR improvement
- **Cross-device learning** - Share learned data across machines
- **Cloud sync** - Backup and sync learning data
- **Automated A/B testing** - Test new strategies automatically
- **Learning visualization** - Charts and graphs of improvement
- **Smart preprocessing** - Learn optimal image preprocessing per environment
- **Collaborative learning** - Learn from community data (opt-in)

## Contributing

To improve the learning system:

1. Test in your environment and report issues
2. Suggest new learning metrics
3. Contribute OCR strategies
4. Share anonymized learning data
5. Propose new adaptive parameters

## License

Same as Pokertool main project.

---

**Happy Learning! 🧠**

The more you use Pokertool, the better it gets at understanding your specific setup and poker site.
