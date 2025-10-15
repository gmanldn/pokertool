#!/usr/bin/env python3
"""Extract key frames from video for analysis."""

import cv2
from pathlib import Path

video_path = "/Users/georgeridout/Desktop/Screen Recording 2025-10-14 at 20.51.26.mov"
output_dir = Path("video_frames")
output_dir.mkdir(exist_ok=True)

print("Extracting frames from video...")

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"ERROR: Could not open video")
    exit(1)

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
duration = frame_count / fps if fps > 0 else 0

print(f"Video: {frame_count} frames, {fps:.1f} fps, {duration:.1f}s duration")

# Extract 5 evenly spaced frames
num_samples = 5
for i in range(num_samples):
    frame_num = int((i / (num_samples - 1)) * (frame_count - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()

    if ret:
        timestamp = frame_num / fps if fps > 0 else 0
        filename = f"frame_{i}_t{timestamp:.1f}s.png"
        cv2.imwrite(str(output_dir / filename), frame)
        print(f"  ✓ {filename}")

cap.release()
print(f"\nExtracted {num_samples} frames to {output_dir}/")
