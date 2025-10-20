# BF_MOVIE.mp4 Training Data Analysis

## Video Information

- **Duration**: 137.7 seconds (~2.3 minutes)
- **Resolution**: 720x480 pixels
- **Frame Rate**: 29.85 fps
- **Total Frames**: 4,111 frames
- **Source**: Betfair Poker gameplay recording

## Training Data Extraction

### Frame Sampling Strategy
Extracted 10 sample frames at regular intervals throughout the video:

1. Frame 0 @ 0.0s
2. Frame 411 @ 13.8s
3. Frame 822 @ 27.5s
4. Frame 1233 @ 41.3s
5. Frame 1644 @ 55.1s
6. Frame 2055 @ 68.8s
7. Frame 2466 @ 82.6s
8. Frame 2877 @ 96.4s
9. Frame 3288 @ 110.1s
10. Frame 3699 @ 123.9s

### Training Value

This video provides valuable training data for:

1. **Table Detection**: Real Betfair poker table layouts and UI elements
2. **State Recognition**: Various game states throughout a poker hand
3. **Card Recognition**: Board cards and hole cards in actual gameplay conditions
4. **Player Information**: Stack sizes, player names, seat positions
5. **Pot Size Detection**: Pot amounts at different stages of play
6. **UI Element Detection**: Buttons, dealer button position, active player indicators
7. **Temporal Analysis**: How game states transition over time

### Analysis Approach

The `analyze_video.py` script:

1. Extracts representative frames from the video
2. Runs Betfair scraper detection on each frame
3. Records table detection confidence
4. Captures game state data:
   - Pot size
   - Board cards (rank and suit)
   - Hero cards (rank and suit)
   - Active players and their stacks
   - Dealer button position
   - Hero position

### Extracted Frames Location
All extracted frames saved to: `video_frames/`

### Usage for Training

This data can be used to:

- Validate scraper accuracy on real gameplay footage
- Identify edge cases where detection fails
- Calibrate confidence thresholds for table detection
- Improve OCR accuracy for stack sizes and pot amounts
- Train card recognition under actual lighting conditions
- Test sequential frame analysis for action detection

### Analysis Results

**Table Detection Performance:**

- ✅ All 10 frames successfully detected as Betfair poker tables
- Confidence levels: 76.5% → 93.9% (increasing trend)
- Average confidence: 86.5%

**Detection Confidence by Frame:**

1. Frame 0 (0.0s): 76.5%
2. Frame 1 (13.8s): 81.1%
3. Frame 2 (27.5s): 86.5%
4. Frame 3 (41.3s): 89.6%
5. Frame 4 (55.1s): 90.6%
6. Frame 5 (68.8s): 90.4%
7. Frame 6 (82.6s): 86.8%
8. Frame 7 (96.4s): 88.0%
9. Frame 8 (110.1s): 91.6%
10. Frame 9 (123.9s): 93.9%

**Limitations Identified:**

- OCR engines not available (Tesseract, PaddleOCR, EasyOCR)
- Unable to extract text-based information (pot size, stack sizes, player names)
- Card detection requires OCR for rank/suit identification

**Training Insights:**

1. **Table detection is robust**: 100% detection rate across all sampled frames
2. **Confidence increases over time**: Later frames have higher confidence, suggesting table becomes more stable/visible
3. **No false negatives**: All frames from real gameplay were correctly identified
4. **OCR dependency**: Text extraction capabilities are critical for full game state analysis

### Next Steps

1. ✅ Frames extracted and analyzed successfully
2. ⚠️ Install OCR engines (Tesseract/PaddleOCR/EasyOCR) for complete analysis
3. Rerun analysis with OCR to extract full game state data
4. Use extracted frames as ground truth test cases
5. Compare manual frame inspection with scraper output for validation
