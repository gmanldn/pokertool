#!/usr/bin/env python3
"""Extract and analyze frames from Betfair gameplay video."""

import cv2
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

video_path = "/Users/georgeridout/Desktop/Screen Recording 2025-10-14 at 20.51.26.mov"
output_dir = Path("video_frames")
output_dir.mkdir(exist_ok=True)

print("=" * 70)
print("VIDEO ANALYSIS - Betfair Poker Gameplay")
print("=" * 70)

# Open video
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"ERROR: Could not open video: {video_path}")
    sys.exit(1)

# Get video info
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = frame_count / fps if fps > 0 else 0
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"\nVideo Info:")
print(f"  Resolution: {width}x{height}")
print(f"  FPS: {fps:.2f}")
print(f"  Frames: {frame_count}")
print(f"  Duration: {duration:.1f} seconds")

# Extract frames at regular intervals
print(f"\nExtracting sample frames...")
num_samples = 10
interval = frame_count // num_samples if num_samples > 0 else 1

extracted = []
for i in range(num_samples):
    frame_num = i * interval
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()

    if ret:
        timestamp = frame_num / fps if fps > 0 else 0
        filename = f"frame_{i:02d}_t{timestamp:.1f}s.png"
        filepath = output_dir / filename
        cv2.imwrite(str(filepath), frame)
        extracted.append((i, timestamp, filepath))
        print(f"  ✓ {filename} (frame {frame_num}/{frame_count})")

cap.release()

print(f"\n✓ Extracted {len(extracted)} frames to {output_dir}/")

# Now analyze each frame with the scraper
print("\n" + "=" * 70)
print("ANALYZING FRAMES WITH BETFAIR SCRAPER")
print("=" * 70)

from pokertool.modules.poker_screen_scraper_betfair import PokerScreenScraper

scraper = PokerScreenScraper()

for idx, timestamp, filepath in extracted:
    print(f"\n📊 Frame {idx} @ {timestamp:.1f}s")
    print("-" * 70)

    # Load frame
    image = cv2.imread(str(filepath))
    if image is None:
        print("  ERROR: Could not load frame")
        continue

    # Detect table
    detected, confidence, details = scraper.detect_poker_table(image)
    print(f"  Table Detection: {detected} (confidence: {confidence:.1%})")

    if not detected:
        print("  ⚠ No poker table detected in this frame")
        continue

    # Analyze table
    try:
        state = scraper.analyze_table(image)

        # Show results
        print(f"  Pot: £{state.pot_size:.2f}")
        print(f"  Board Cards: {[f'{c.rank}{c.suit}' for c in state.board_cards]}")
        print(f"  Hero Cards: {[f'{c.rank}{c.suit}' for c in state.hero_cards]}")

        active_players = [s for s in state.seats if s.is_active]
        print(f"  Active Players: {len(active_players)}/{len(state.seats)}")

        for seat in active_players:
            hero_mark = " 🎯" if seat.is_hero else ""
            dealer_mark = " 🔘" if seat.is_dealer else ""
            print(f"    Seat {seat.seat_number}: {seat.player_name or '???'} - £{seat.stack_size:.2f}{hero_mark}{dealer_mark}")

    except Exception as e:
        print(f"  ⚠ Analysis error: {e}")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print(f"\nFrames saved to: {output_dir}/")
print("Review the extracted frames to see what the scraper detected.")
