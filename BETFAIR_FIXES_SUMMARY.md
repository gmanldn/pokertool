# Betfair Poker Screen Scraper Fixes

## Problem Summary
The Betfair poker table scraper was failing to detect:
1. **Player names** - Getting partial names like "An" instead of "GmanLDN"
2. **Stack amounts** - Showing $0.00 instead of actual values like £2.22, £2.62, £1.24
3. **Board cards** - OCR failures on card ranks

## Root Cause Analysis

### Discovery Process
1. Examined BF_TEST.jpg (Betfair poker table screenshot)
2. Created diagnostic script `test_bf_detection.py` to test OCR approaches
3. Identified that **Betfair uses WHITE text on DARK PURPLE background**

### Key Finding
The existing OCR preprocessing was NOT using inverted thresholding, causing text to be lost:
- **Wrong**: `THRESH_BINARY` on dark background with white text = text disappears
- **Right**: `THRESH_BINARY_INV` on dark background with white text = text becomes black on white (readable by Tesseract)

### Diagnostic Results
Testing different approaches on Seat 5 (GmanLDN, £1.24):
- ❌ Approach 1 (simple threshold): 'GmagloN' (OCR error)
- ❌ Approach 2 (inverted 2x): 'GmagloN' (OCR error)
- ❌ Approach 3 (adaptive): Garbage text
- ✅ **Approach 4 (upscale 3x + inverted): 'GmanLDN'** ← PERFECT!

## Fixes Applied

### File: `src/pokertool/modules/poker_screen_scraper_betfair.py`

#### Fix 1: Added Upscaled Inverted Threshold (Lines 2362-2367)
```python
# ENHANCED: Resize for better OCR (scale up 3x for Betfair's smaller text)
roi_gray_upscaled = cv2.resize(roi_gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)

# CRITICAL: Betfair uses WHITE text on DARK background - must use INVERTED threshold
# This is the most important preprocessing for Betfair
_, thresh_inverted = cv2.threshold(roi_gray_upscaled, 127, 255, cv2.THRESH_BINARY_INV)
```

#### Fix 2: Fixed Pass 2 OTSU Threshold (Line 2388)
```python
# Was: cv2.threshold(roi_gray_filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
# Now: cv2.threshold(roi_gray_filtered, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
```

#### Fix 3: Fixed Pass 4 Simple Threshold (Line 2403)
```python
# Was: cv2.threshold(roi_gray, 127, 255, cv2.THRESH_BINARY)
# Now: cv2.threshold(roi_gray, 127, 255, cv2.THRESH_BINARY_INV)
```

#### Fix 4: Prioritize Upscaled Inverted Threshold (Line 2415)
```python
# PRIORITIZE: Try upscaled inverted threshold first (best for Betfair)
for thresh in [thresh_inverted, thresh4, thresh1, thresh2, thresh3]:
```

#### Fix 5: Add £ (GBP) Currency Support (Lines 2430, 2435)
```python
# Find all numbers, including those with $, £, € prefix, commas, and decimals
nums = re.findall(r'[\$£€]?\s*([0-9][0-9,.]*\.?[0-9]*)', all_text)

# ...

cleaned = num_str.replace(',', '').replace('$', '').replace('£', '').replace('€', '').strip()
```

## Expected Improvements

### Player Name Detection
- **Before**: "An", "Eres", "Tabledetection", "Auto-detect"
- **After**: "GmanLDN", "FourBoysUnited", "ThelongblueVein", etc. (full names)

### Stack Amount Detection
- **Before**: $0.00 for most players
- **After**: £2.22, £2.62, £1.24, £0.00 (SIT OUT) - accurate values

### Board Card Detection
- **Before**: Garbage OCR text, ranks extracted but noisy
- **After**: Should remain functional (card detection uses different preprocessing)

## Testing

### Diagnostic Scripts Created
1. **`test_bf_detection.py`** - Diagnostic tool to test different OCR approaches
   - Saves debug images showing each preprocessing step
   - Tests player name/stack extraction at specific seats

2. **`test_betfair_fixed.py`** - Comprehensive test against BF_TEST.jpg
   - Compares against ground truth in GROUND_TRUTH_BF_TEST.json
   - Checks pot, cards, players, names, stacks, hero detection
   - Provides pass/fail score

### Ground Truth (BF_TEST.jpg)
- **Pot**: £0.08
- **Board Cards**: Td, Ad, 7h, 5h, 6h (river)
- **Players**:
  - Seat 1: Player with hat - £2.22
  - Seat 2: FourBoysUnited - £2.62 (DEALER)
  - Seat 5: GmanLDN - £1.24 (HERO)
  - Seat 6: ThelongblueVein - £0.00 (SIT OUT)

## Technical Notes

### Why 3x Upscaling?
Betfair's player names/stacks use relatively small text. 3x upscaling provides enough resolution for Tesseract to accurately recognize characters.

### Why Inverted Threshold is Critical
Tesseract OCR expects **black text on white background**. Betfair uses white text on dark purple background, so:
1. Grayscale conversion makes text light gray, background dark gray
2. `THRESH_BINARY_INV` inverts: text becomes black, background becomes white
3. Tesseract can now read the text correctly

### Performance Consideration
The fix adds one additional preprocessing pass (`thresh_inverted`) but prioritizes it first in the loop, so successful OCR happens faster for Betfair tables.

## Remaining Issues

### Cached Bytecode
- Old `.pyc` files in `__pycache__/` may contain the old buggy code
- **Solution**: Cleared all `__pycache__` directories
- **Prevention**: Restart Python processes after code changes

### Multiple OCR Passes
- Currently tries 5 thresholds × 4 configs = 20 OCR calls per seat
- **Optimization opportunity**: Could reduce to 2-3 best approaches for faster detection

## Files Modified
- `src/pokertool/modules/poker_screen_scraper_betfair.py` (lines 2362-2435)

## Files Created
- `test_bf_detection.py` - OCR diagnostic tool
- `test_betfair_fixed.py` - Comprehensive test suite
- `BETFAIR_FIXES_SUMMARY.md` - This document

## Next Steps
1. ✅ Clear Python cache
2. ✅ Fix player name OCR (inverted threshold + 3x upscale)
3. ✅ Fix stack amount OCR (£ currency support)
4. ⏳ Verify fixes work on live Betfair tables
5. ⏳ Optimize card detection if issues persist
