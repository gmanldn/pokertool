# PokerTool Pot & Bet Detection - Comprehensive Analysis

## Overview
The pokertool application uses a sophisticated multi-layered approach to detect poker table information including pot sizes, bets, and player stacks. The system spans both frontend (React/TypeScript) and backend (Python) components.

## Current Detection Architecture

### 1. Screen Capture & OCR Layer

**Primary Files:**
- `/src/pokertool/ocr_recognition.py` - OCR text recognition for cards and amounts
- `/src/pokertool/modules/poker_screen_scraper_betfair.py` - Advanced screen scraping with 99.2% accuracy
- `/src/pokertool/desktop_independent_scraper.py` - Cross-platform screen capture

**How it Works:**
- Uses **three OCR engines** in a hybrid approach:
  - Tesseract (pytesseract) - Default fallback
  - EasyOCR - More robust for challenging conditions
  - Template matching - For card recognition via pre-loaded templates
  
- **Preprocessing pipeline** for currency amounts:
  ```python
  def preprocess_image(self, image, enhance_for='numbers'):
      # For number recognition (pot sizes, bets):
      # 1. Convert to grayscale
      # 2. Apply contrast enhancement (2.5x)
      # 3. Apply Gaussian blur (0.5)
      # 4. Text-specific configuration: '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,$'
  ```

### 2. Amount Parsing & Validation

**Primary File:**
- `/src/pokertool/input_validation.py` - Comprehensive bet validation

**BetValidator Class:**
```python
class BetValidator:
    MIN_BET = 0.0
    MAX_BET = 1_000_000.0  # $1M max
    
    def validate(amount: Union[int, float, str]) -> ValidationResult:
        # Handles: "$100.50", "£1,234.56", "100", etc.
        # Removes currency symbols: £$€
        # Removes commas
        # Converts to float
        # Rounds to 2 decimal places
```

**Key Issue for Small Stakes (1c/2c euros):**
- The `clean_amount()` method in `OCRPostProcessor`:
  ```python
  def clean_amount(self, text: str) -> str:
      # Apply character replacement rules
      # Remove non-numeric EXCEPT decimal point
      # Pattern: r'[^\d.]'
      text = re.sub(r'[^\d.]', '', text)
      return text
  ```
- Problem: **This doesn't handle European decimal separators** (comma vs period)
- For "0,01€" OCR might read as "0.01" OR it might read as "O,01" (with letter O)

### 3. Currency Processing

**Primary File:**
- `/src/pokertool/scraping_accuracy_system.py` - OCR Post-Processing & Cleanup

**OCRPostProcessor Class:**
```python
class OCRPostProcessor:
    def __init__(self):
        self.correction_rules = {
            'O': '0',  # Letter O -> digit 0
            'o': '0',
            'l': '1',  # Letter l -> digit 1
            'I': '1',  # Letter I -> digit 1
            'S': '5',
            '$S': '$5',
            'Z': '2',
            'B': '8',
        }
```

**Issue for 1c/2c Stakes:**
- Correction rules assume typical OCR mistakes
- **Missing rule for European decimal separator (,)**
- Small amounts like "0,01€", "0,02€" might be:
  - Read as "0.01" (correct)
  - Read as "O,O1" (incorrect - letter O confused with 0)
  - Read as "0,01" (European format, but needs conversion)

### 4. Amount Recognition in OCR

**File:** `/src/pokertool/ocr_recognition.py`

**Method:** `recognize_betting_amounts()`
```python
def recognize_betting_amounts(self, image, regions) -> Dict[str, float]:
    for region in regions:
        # Extract region
        processed = self.preprocess_image(roi, 'numbers')
        
        # OCR config for numbers
        config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,$'
        text = pytesseract.image_to_string(processed, config=config)
        
        # Parse amount
        amount = self._parse_amount(text)
        return amounts

def _parse_amount(self, text: str) -> float:
    text = text.strip().replace(',', '').replace('$', '')
    # Find number patterns
    number_pattern = r'(\d+\.?\d*)'
    matches = re.findall(number_pattern, text)
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            return 0.0
    return 0.0
```

**Problem:** The regex `(\d+\.?\d*)` only matches periods as decimal separators, not commas.

### 5. Multi-Strategy Fusion & Accuracy System

**Primary File:**
- `/src/pokertool/scraping_accuracy_system.py`

**Key Components:**
1. **TemporalConsensus** - Smooths values over 5 frames to eliminate OCR noise
2. **PotValidator** - Validates pot size using game state continuity (tolerance: 10%)
3. **BlindsChecker** - Validates against known blind structures
4. **MultiStrategyFusion** - Combines OCR, Vision Model, and CDP results with weighted voting

**BlindsChecker Known Structures:**
```python
blind_structures = [
    (0.5, 1), (1, 2), (2, 4), (2.5, 5), (5, 10),
    (10, 20), (25, 50), (50, 100), (100, 200),
    (200, 400), (500, 1000), (1000, 2000)
]
```

**NOTE:** `(0.5, 1)` is 50c/€1, but no `(0.01, 0.02)` structure for 1c/2c!

### 6. ROI (Region of Interest) Tracking

**Primary File:**
- `/src/pokertool/roi_tracking_system.py`

**Standard ROI Definitions:**
```python
ROI("pot", 860, 300, 200, 60)              # Center-top
ROI("board_card_1", 760, 400, 70, 100)    # etc.
ROI("seat_1", 860, 850, 200, 150)         # Hero position
# ... 9 seat positions around table
```

**Issue:** These are normalized to 1920x1080, may need calibration for different tables.

### 7. Frontend Display

**Primary Files:**
- `/pokertool-frontend/src/components/TableView.tsx` - Displays pot as: `<Pot: ${table.pot}>`
- `/pokertool-frontend/src/components/DetectionLog.tsx` - Logs detection events

**Current Display:**
```typescript
<Typography variant="h6">
    Pot: ${table.pot}
</Typography>
```

**Note:** Always uses $ symbol, doesn't respect original currency.

## Identified Issues for 1c/2c Euro Stakes

### Problem 1: European Decimal Separator
- **Location:** `ocr_recognition.py::_parse_amount()` and `scraping_accuracy_system.py::clean_amount()`
- **Issue:** Regex only matches periods (.) as decimal separators
- **Impact:** "0,01€" is parsed incorrectly
- **Example:** "0,01€" -> removed to "001" -> parsed as "1" instead of "0.01"

### Problem 2: Missing Blind Structure
- **Location:** `scraping_accuracy_system.py::BlindsChecker`
- **Issue:** No (0.01, 0.02) entry in `blind_structures` list
- **Impact:** Validation may reject 1c/2c games as invalid
- **Symptom:** BlindsChecker.validate() returns `False` for 1c/2c stakes

### Problem 3: OCR Character Confusion at Small Amounts
- **Location:** `ocr_recognition.py::preprocess_image()`
- **Issue:** Small amounts like "0,01" are prone to:
  - Letter O (O) confused with digit 0
  - Letter l (l) confused with digit 1
  - Dot vs comma confusion
- **Impact:** "0,01" might be read as "O,O1" which fails validation

### Problem 4: Currency Symbol Handling
- **Location:** `BetValidator.validate()`
- **Issue:** Handles £$€ symbols but doesn't normalize to consistent format
- **Impact:** Frontend always shows $, even for euro games

### Problem 5: Precision Loss in Small Stakes
- **Location:** `input_validation.py::BetValidator`
- **Code:** Rounds to 2 decimal places (`round(amount, 2)`)
- **Issue:** Fine for normal stakes but can accumulate rounding errors on microstack games
- **Example:** 0.01 + 0.01 + 0.01 = 0.03 vs actual 0.03 due to float precision

## Data Flow Summary

```
Screen Capture (mss library)
    ↓
Region extraction (ROI coordinates)
    ↓
Image preprocessing
  - Grayscale conversion
  - Contrast enhancement
  - Noise reduction
    ↓
OCR (Tesseract / EasyOCR / Template)
    ↓
Raw text: "0,01€", "Pot: €5.25", etc.
    ↓
OCRPostProcessor::clean_amount()
  - Character replacement
  - Regex cleanup: r'[^\d.]'  ← ISSUE: Doesn't handle comma
    ↓
Temporary Consensus (5-frame averaging)
    ↓
Amount Parsing: _parse_amount()
  - Regex: r'(\d+\.?\d*)'  ← ISSUE: Only matches periods
    ↓
BlindsChecker validation
  - Checks against known structures  ← ISSUE: No 0.01/0.02
    ↓
Frontend Display (always $ symbol)
```

## Configuration Files
- `/poker_config.json` - Main configuration (doesn't have currency settings)
- `/src/pokertool/user_config.py` - User configuration module
- No currency format configuration file found

## File Locations (Absolute Paths)

### Backend Detection Logic
- `/Users/georgeridout/Documents/github/pokertool/src/pokertool/ocr_recognition.py`
- `/Users/georgeridout/Documents/github/pokertool/src/pokertool/scraping_accuracy_system.py`
- `/Users/georgeridout/Documents/github/pokertool/src/pokertool/input_validation.py`
- `/Users/georgeridout/Documents/github/pokertool/src/pokertool/roi_tracking_system.py`
- `/Users/georgeridout/Documents/github/pokertool/src/pokertool/modules/poker_screen_scraper.py`
- `/Users/georgeridout/Documents/github/pokertool/src/pokertool/modules/poker_screen_scraper_betfair.py`
- `/Users/georgeridout/Documents/github/pokertool/src/pokertool/desktop_independent_scraper.py`

### Frontend Display
- `/Users/georgeridout/Documents/github/pokertool/pokertool-frontend/src/components/TableView.tsx`
- `/Users/georgeridout/Documents/github/pokertool/pokertool-frontend/src/components/DetectionLog.tsx`

### Configuration
- `/Users/georgeridout/Documents/github/pokertool/poker_config.json`
- `/Users/georgeridout/Documents/github/pokertool/src/pokertool/user_config.py`

## Recommended Fixes

1. **Update `_parse_amount()` in ocr_recognition.py:**
   - Add support for European decimal separator (comma)
   - Try parsing with both period and comma

2. **Update `clean_amount()` in scraping_accuracy_system.py:**
   - Handle European number formats
   - Add rule: ',' -> '.' for normalization

3. **Add 1c/2c to BlindsChecker:**
   - Add `(0.01, 0.02)` to `blind_structures`

4. **Improve preprocessing for small amounts:**
   - Increase contrast more aggressively for sub-1 euro amounts
   - Add specific cleanup rules for very small numbers

5. **Add currency awareness:**
   - Detect and preserve original currency (€, $, £)
   - Display correctly in frontend
