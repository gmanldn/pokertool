#!/usr/bin/env python3
"""Quick diagnostic test for BF_TEST.jpg detection issues."""

import cv2
import numpy as np
import pytesseract
from pathlib import Path

# Load the test image
img_path = Path(__file__).parent / "BF_TEST.jpg"
image = cv2.imread(str(img_path))

if image is None:
    print(f"Failed to load {img_path}")
    exit(1)

h, w = image.shape[:2]
print(f"Image size: {w}x{h}")

# Test player name detection at seat 5 (GmanLDN at bottom)
# Based on seat_positions {5: (0.5, 0.85)} from the code
print("\n=== Testing Player Name Detection (Seat 5: GmanLDN) ===")
cx = int(w * 0.5)
cy = int(h * 0.85)
roi_w = int(w * 0.22)
roi_h = int(h * 0.15)
x0 = max(cx - roi_w // 2, 0)
y0 = max(cy - roi_h // 2, 0)
x1 = min(cx + roi_w // 2, w)
y1 = min(cy + roi_h // 2, h)
roi = image[y0:y1, x0:x1]

print(f"ROI position: ({x0}, {y0}) to ({x1}, {y1})")
print(f"ROI size: {roi.shape}")

# Save ROI for inspection
cv2.imwrite("debug_seat5_roi.png", roi)
print("Saved: debug_seat5_roi.png")

# Try different OCR approaches
roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

# Approach 1: Simple threshold
_, thresh1 = cv2.threshold(roi_gray, 127, 255, cv2.THRESH_BINARY)
text1 = pytesseract.image_to_string(thresh1, config='--psm 6')
print(f"\nApproach 1 (simple): '{text1.strip()}'")
cv2.imwrite("debug_thresh1.png", thresh1)

# Approach 2: Inverted threshold (white text on dark background)
_, thresh2 = cv2.threshold(roi_gray, 127, 255, cv2.THRESH_BINARY_INV)
text2 = pytesseract.image_to_string(thresh2, config='--psm 6')
print(f"Approach 2 (inverted): '{text2.strip()}'")
cv2.imwrite("debug_thresh2.png", thresh2)

# Approach 3: Adaptive threshold
thresh3 = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
text3 = pytesseract.image_to_string(thresh3, config='--psm 6')
print(f"Approach 3 (adaptive): '{text3.strip()}'")
cv2.imwrite("debug_thresh3.png", thresh3)

# Approach 4: Upscale then threshold
roi_gray_big = cv2.resize(roi_gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
_, thresh4 = cv2.threshold(roi_gray_big, 127, 255, cv2.THRESH_BINARY_INV)
text4 = pytesseract.image_to_string(thresh4, config='--psm 6')
print(f"Approach 4 (upscale+inv): '{text4.strip()}'")
cv2.imwrite("debug_thresh4.png", thresh4)

# Test board card detection
print("\n=== Testing Board Card Detection ===")
# Cards should be in center region (y_start_ratio=0.25, y_end_ratio=0.60)
card_y0 = int(h * 0.25)
card_y1 = int(h * 0.60)
card_roi = image[card_y0:card_y1, :]
print(f"Card ROI: y={card_y0}-{card_y1}, size={card_roi.shape}")
cv2.imwrite("debug_board_cards_roi.png", card_roi)
print("Saved: debug_board_cards_roi.png")

# Test stack detection at seat 5 (should show £1.24)
print("\n=== Testing Stack Detection (Seat 5: £1.24) ===")
# Try to extract just numbers from the ROI
import re
nums = re.findall(r'[\d.]+', text2)
print(f"Numbers found in inverted thresh: {nums}")
nums = re.findall(r'[\d.]+', text4)
print(f"Numbers found in upscaled thresh: {nums}")

print("\nDiagnostic images saved. Check debug_*.png files.")
