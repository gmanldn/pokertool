#!/usr/bin/env python3
"""
Create a simple app icon for PokerTool API.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_icon(output_path: Path, size: int = 512):
    """Create a simple poker-themed icon."""
    # Create image with dark green background (poker table color)
    img = Image.new('RGB', (size, size), color='#1a5c1a')
    draw = ImageDraw.Draw(img)

    # Draw a circle for the chip
    margin = size // 8
    chip_bbox = [margin, margin, size - margin, size - margin]

    # Outer ring (white)
    draw.ellipse(chip_bbox, fill='#ffffff', outline='#ffffff')

    # Inner circle (dark green)
    inner_margin = margin + size // 20
    inner_bbox = [inner_margin, inner_margin, size - inner_margin, size - inner_margin]
    draw.ellipse(inner_bbox, fill='#2d8b2d', outline='#2d8b2d')

    # Draw poker suits in the center
    center_x = size // 2
    center_y = size // 2

    # Draw "PT" text for PokerTool
    try:
        # Try to use a nicer font
        font_size = size // 4
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default
        font = ImageFont.load_default()

    text = "PT"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Draw text in center
    text_x = center_x - text_width // 2
    text_y = center_y - text_height // 2
    draw.text((text_x, text_y), text, fill='#ffffff', font=font)

    # Save the image
    img.save(output_path, 'PNG')
    print(f"Icon created at: {output_path}")

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    assets_dir = project_root / "assets"
    assets_dir.mkdir(exist_ok=True)

    icon_path = assets_dir / "pokertool-icon.png"
    create_icon(icon_path)
