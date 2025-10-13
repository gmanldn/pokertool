#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Synthetic Scrape Data Generator
================================

DATA-030: Synthetic Scrape Data Generator

Expands training coverage for rare layouts and exotic themes without requiring
manual screenshot collection.

Features:
- Programmatic poker table scene generation
- Configurable themes, layouts, stakes, lighting
- Randomized player names, stacks, cards, positions
- Automatic ground truth label generation
- Multiple rendering styles and variations
- Export in QA harness compatible format

Module: pokertool.synthetic_data_generator
Version: v47.0.0
Author: PokerTool Development Team
"""

__version__ = '47.0.0'
__author__ = 'PokerTool Development Team'

import random
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
import numpy as np
import json

logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None


class TableTheme:
    """Poker table theme configuration."""

    def __init__(self, name: str, felt_color: Tuple[int, int, int],
                 rail_color: Tuple[int, int, int],
                 text_color: Tuple[int, int, int] = (255, 255, 255)):
        self.name = name
        self.felt_color = felt_color  # RGB
        self.rail_color = rail_color
        self.text_color = text_color

    @staticmethod
    def standard_green():
        """Standard green felt theme."""
        return TableTheme("standard_green", (34, 139, 34), (101, 67, 33))

    @staticmethod
    def betfair_purple():
        """Betfair purple theme."""
        return TableTheme("betfair_purple", (147, 112, 219), (75, 56, 109))

    @staticmethod
    def pokerstars_blue():
        """PokerStars blue theme."""
        return TableTheme("pokerstars_blue", (25, 50, 75), (12, 25, 37))

    @staticmethod
    def red_table():
        """Red felt theme."""
        return TableTheme("red_table", (139, 34, 34), (67, 17, 17))

    @staticmethod
    def dark_mode():
        """Dark mode theme."""
        return TableTheme("dark_mode", (30, 30, 30), (15, 15, 15), (200, 200, 200))


@dataclass
class PlayerSeat:
    """A player seat configuration."""
    seat_number: int
    position: Tuple[int, int]  # (x, y) pixel position
    name: str
    stack: float
    cards: Optional[List[str]] = None  # Hole cards
    bet: Optional[float] = None
    is_button: bool = False
    is_active: bool = True


@dataclass
class TableState:
    """Complete poker table state."""
    pot_size: float
    board_cards: List[str]
    players: List[PlayerSeat]
    button_position: int
    blinds: Tuple[float, float]  # (SB, BB)
    theme: TableTheme
    stakes: str  # e.g., "NL10", "PLO25"
    resolution: Tuple[int, int] = (1920, 1080)


class SyntheticDataGenerator:
    """
    Generate synthetic poker table screenshots with ground truth labels.
    """

    def __init__(self, output_dir: Path):
        """
        Initialize generator.

        Args:
            output_dir: Directory to save generated images and labels
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow required. Install: pip install pillow")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Card ranks and suits
        self.ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        self.suits = ['s', 'h', 'd', 'c']

        # Player name pools
        self.first_names = [
            "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry",
            "Ivy", "Jack", "Karen", "Leo", "Mary", "Nick", "Olivia", "Peter",
            "Quinn", "Rachel", "Steve", "Tina", "Uma", "Victor", "Wendy", "Xavier",
            "Yara", "Zack"
        ]

        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
            "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
            "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
        ]

        # Seat positions for 9-player table (relative coordinates)
        self.seat_positions_9 = [
            (0.50, 0.85),  # Seat 1 (Hero, bottom)
            (0.30, 0.75),  # Seat 2
            (0.15, 0.60),  # Seat 3
            (0.10, 0.40),  # Seat 4
            (0.15, 0.20),  # Seat 5
            (0.50, 0.10),  # Seat 6 (top)
            (0.85, 0.20),  # Seat 7
            (0.90, 0.40),  # Seat 8
            (0.85, 0.60),  # Seat 9
            (0.70, 0.75),  # Seat 9 (if 10 seats)
        ]

        logger.info(f"Synthetic data generator initialized: {output_dir}")

    def generate_deck(self) -> List[str]:
        """Generate a full deck of cards."""
        return [f"{rank}{suit}" for rank in self.ranks for suit in self.suits]

    def deal_cards(self, num_cards: int, exclude: List[str] = None) -> List[str]:
        """Deal random cards from deck."""
        deck = self.generate_deck()

        if exclude:
            deck = [c for c in deck if c not in exclude]

        if num_cards > len(deck):
            num_cards = len(deck)

        return random.sample(deck, num_cards)

    def generate_player_name(self) -> str:
        """Generate random player name."""
        if random.random() < 0.3:
            # Username style
            return f"{random.choice(self.first_names)}{random.randint(10, 999)}"
        else:
            # First + Last
            first = random.choice(self.first_names)
            last = random.choice(self.last_names)
            return f"{first}{last[0]}"

    def generate_table_state(self, theme: TableTheme, stakes: str,
                             num_players: int = None) -> TableState:
        """
        Generate random table state.

        Args:
            theme: Table theme
            stakes: Stakes level (e.g., "NL10")
            num_players: Number of players (random if None)

        Returns:
            TableState
        """
        if num_players is None:
            num_players = random.randint(2, 9)

        # Parse stakes for blind levels
        import re
        stakes_match = re.match(r'([A-Z]+)(\d+)', stakes)
        if stakes_match:
            game_type = stakes_match.group(1)
            stakes_value = int(stakes_match.group(2))
            bb = stakes_value / 100.0  # NL10 = $0.10 BB
            sb = bb / 2.0
        else:
            bb = 0.10
            sb = 0.05

        blinds = (sb, bb)

        # Generate players
        players = []
        used_cards = []

        width, height = 1920, 1080

        for i in range(num_players):
            seat_num = i + 1

            # Position
            rel_x, rel_y = self.seat_positions_9[i]
            pos = (int(width * rel_x), int(height * rel_y))

            # Stack (random between 50BB and 200BB)
            stack = bb * random.uniform(50, 200)

            # Hole cards for hero (seat 1) and maybe others
            cards = None
            if i == 0 or random.random() < 0.3:  # 30% show cards
                cards = self.deal_cards(2, exclude=used_cards)
                used_cards.extend(cards)

            # Bet (30% chance)
            bet = None
            if random.random() < 0.3:
                bet = random.choice([bb * 2, bb * 3, bb * 5, bb * 10])

            player = PlayerSeat(
                seat_number=seat_num,
                position=pos,
                name=self.generate_player_name(),
                stack=stack,
                cards=cards,
                bet=bet,
                is_button=(seat_num == random.randint(1, num_players)),
                is_active=True
            )

            players.append(player)

        # Button position
        button_pos = next((p.seat_number for p in players if p.is_button), 1)

        # Board cards (random street)
        street = random.choice(['preflop', 'flop', 'turn', 'river'])
        if street == 'preflop':
            board_cards = []
        elif street == 'flop':
            board_cards = self.deal_cards(3, exclude=used_cards)
        elif street == 'turn':
            board_cards = self.deal_cards(4, exclude=used_cards)
        else:  # river
            board_cards = self.deal_cards(5, exclude=used_cards)

        # Pot size (sum of bets + some previous action)
        total_bets = sum(p.bet for p in players if p.bet)
        pot_size = total_bets + random.uniform(bb * 2, bb * 10)

        return TableState(
            pot_size=pot_size,
            board_cards=board_cards,
            players=players,
            button_position=button_pos,
            blinds=blinds,
            theme=theme,
            stakes=stakes,
            resolution=(width, height)
        )

    def render_table(self, state: TableState, variations: Dict[str, Any] = None) -> Image.Image:
        """
        Render poker table as image.

        Args:
            state: Table state
            variations: Rendering variations (lighting, noise, etc.)

        Returns:
            PIL Image
        """
        width, height = state.resolution
        img = Image.new('RGB', (width, height), state.theme.felt_color)
        draw = ImageDraw.Draw(img)

        # Try to load a font
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw table oval/ellipse
        table_rect = [
            (width * 0.1, height * 0.15),
            (width * 0.9, height * 0.85)
        ]
        draw.ellipse(table_rect, fill=state.theme.felt_color, outline=state.theme.rail_color, width=8)

        # Draw pot in center
        pot_text = f"Pot: ${state.pot_size:.2f}"
        pot_bbox = draw.textbbox((0, 0), pot_text, font=font_large)
        pot_w = pot_bbox[2] - pot_bbox[0]
        pot_h = pot_bbox[3] - pot_bbox[1]
        pot_pos = ((width - pot_w) // 2, int(height * 0.35))
        draw.text(pot_pos, pot_text, fill=state.theme.text_color, font=font_large)

        # Draw board cards
        if state.board_cards:
            board_text = " ".join(state.board_cards)
            board_bbox = draw.textbbox((0, 0), board_text, font=font_large)
            board_w = board_bbox[2] - board_bbox[0]
            board_pos = ((width - board_w) // 2, int(height * 0.45))
            draw.text(board_pos, board_text, fill=(255, 255, 255), font=font_large)

        # Draw players
        for player in state.players:
            x, y = player.position

            # Player name
            draw.text((x - 50, y - 60), player.name, fill=state.theme.text_color, font=font_medium)

            # Stack
            stack_text = f"${player.stack:.2f}"
            draw.text((x - 50, y - 40), stack_text, fill=state.theme.text_color, font=font_small)

            # Hole cards
            if player.cards:
                cards_text = " ".join(player.cards)
                draw.text((x - 50, y - 20), cards_text, fill=(255, 255, 255), font=font_medium)

            # Bet
            if player.bet:
                bet_text = f"Bet: ${player.bet:.2f}"
                draw.text((x - 50, y), bet_text, fill=(255, 255, 0), font=font_small)

            # Button
            if player.is_button:
                draw.ellipse([x + 40, y - 60, x + 60, y - 40], fill=(255, 215, 0), outline=(0, 0, 0))
                draw.text((x + 45, y - 58), "D", fill=(0, 0, 0), font=font_small)

        # Apply variations
        if variations:
            img = self._apply_variations(img, variations)

        return img

    def _apply_variations(self, img: Image.Image, variations: Dict[str, Any]) -> Image.Image:
        """Apply rendering variations (noise, blur, lighting)."""

        # Brightness/lighting
        if 'brightness' in variations:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(variations['brightness'])

        # Contrast
        if 'contrast' in variations:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(variations['contrast'])

        # Blur
        if variations.get('blur', False):
            blur_amount = variations.get('blur_amount', 1)
            img = img.filter(ImageFilter.GaussianBlur(blur_amount))

        # Noise
        if variations.get('noise', False) and CV2_AVAILABLE:
            # Convert to numpy
            img_array = np.array(img)

            # Add Gaussian noise
            noise_level = variations.get('noise_level', 10)
            noise = np.random.normal(0, noise_level, img_array.shape)
            noisy_img = np.clip(img_array + noise, 0, 255).astype(np.uint8)

            img = Image.fromarray(noisy_img)

        return img

    def generate_ground_truth(self, state: TableState) -> Dict[str, Any]:
        """Generate ground truth labels for a table state."""
        return {
            'pot_size': state.pot_size,
            'player_stacks': {p.seat_number: p.stack for p in state.players},
            'player_names': {p.seat_number: p.name for p in state.players},
            'bets': {p.seat_number: p.bet for p in state.players if p.bet},
            'hole_cards': next((p.cards for p in state.players if p.seat_number == 1 and p.cards), None),
            'board_cards': state.board_cards if state.board_cards else None,
            'button_position': state.button_position,
            'blinds': list(state.blinds)
        }

    def generate_batch(self, num_images: int, themes: List[TableTheme] = None,
                       stakes_levels: List[str] = None,
                       variations_enabled: bool = True) -> List[Tuple[Path, Dict]]:
        """
        Generate a batch of synthetic images with ground truth.

        Args:
            num_images: Number of images to generate
            themes: List of themes to use (random if None)
            stakes_levels: List of stakes to use (random if None)
            variations_enabled: Enable rendering variations

        Returns:
            List of (image_path, ground_truth) tuples
        """
        if themes is None:
            themes = [
                TableTheme.standard_green(),
                TableTheme.betfair_purple(),
                TableTheme.pokerstars_blue(),
                TableTheme.dark_mode()
            ]

        if stakes_levels is None:
            stakes_levels = ["NL10", "NL25", "NL50", "NL100", "NL200", "PLO25", "PLO50"]

        generated = []

        for i in range(num_images):
            # Random theme and stakes
            theme = random.choice(themes)
            stakes = random.choice(stakes_levels)

            # Generate state
            state = self.generate_table_state(theme, stakes)

            # Variations
            variations = {}
            if variations_enabled:
                variations = {
                    'brightness': random.uniform(0.8, 1.2),
                    'contrast': random.uniform(0.9, 1.1),
                    'blur': random.random() < 0.2,
                    'blur_amount': random.uniform(0.5, 1.5),
                    'noise': random.random() < 0.3,
                    'noise_level': random.uniform(5, 15)
                }

            # Render
            img = self.render_table(state, variations)

            # Save image
            image_filename = f"synthetic_{i:05d}.png"
            image_path = self.output_dir / image_filename
            img.save(image_path)

            # Ground truth
            gt = self.generate_ground_truth(state)

            # Save ground truth
            gt_data = {
                'id': f"synthetic_{i:05d}",
                'name': f"Synthetic {i+1}",
                'image_path': image_filename,  # Add for QA harness compatibility
                'ground_truth': gt,
                'theme': theme.name,
                'stakes': stakes,
                'resolution': list(state.resolution),
                'lighting': 'varied' if variations_enabled else 'normal',
                'metadata': {
                    'synthetic': True,
                    'variations': variations,
                    'num_players': len(state.players)
                }
            }

            json_path = self.output_dir / f"synthetic_{i:05d}.json"
            with open(json_path, 'w') as f:
                json.dump(gt_data, f, indent=2)

            generated.append((image_path, gt))

            if (i + 1) % 10 == 0:
                logger.info(f"Generated {i + 1}/{num_images} synthetic images")

        logger.info(f"Batch generation complete: {num_images} images")
        return generated

    def generate_manifest(self, batch_results: List[Tuple[Path, Dict]]) -> Path:
        """Generate manifest file for QA harness."""
        manifest = {
            'version': '1.0',
            'generator': 'synthetic_data_generator',
            'total_cases': len(batch_results),
            'test_cases': []
        }

        for img_path, gt in batch_results:
            # Load the JSON file to get full metadata
            json_path = img_path.with_suffix('.json')
            if json_path.exists():
                with open(json_path, 'r') as f:
                    test_case_data = json.load(f)
                    manifest['test_cases'].append(test_case_data)

        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Manifest generated: {manifest_path}")
        return manifest_path


def generate_synthetic_dataset(output_dir: Path, num_images: int = 100,
                                 seed: int = 42) -> Path:
    """
    Convenience function to generate a complete synthetic dataset.

    Args:
        output_dir: Output directory
        num_images: Number of images to generate
        seed: Random seed for reproducibility

    Returns:
        Path to manifest file
    """
    random.seed(seed)
    np.random.seed(seed)

    generator = SyntheticDataGenerator(output_dir)

    # Generate batch
    batch_results = generator.generate_batch(num_images, variations_enabled=True)

    # Generate manifest
    manifest_path = generator.generate_manifest(batch_results)

    return manifest_path


if __name__ == '__main__':
    # Demo usage
    print("=" * 70)
    print("Synthetic Scrape Data Generator")
    print("=" * 70)

    if not PIL_AVAILABLE:
        print("❌ PIL/Pillow not available. Install: pip install pillow")
        exit(1)

    # Generate small demo dataset
    output_dir = Path("synthetic_dataset_demo")
    output_dir.mkdir(exist_ok=True)

    print(f"\nGenerating 10 synthetic poker table images...")
    print(f"Output directory: {output_dir}")

    manifest_path = generate_synthetic_dataset(output_dir, num_images=10, seed=42)

    print(f"\n✅ Dataset generated successfully!")
    print(f"   Images: {output_dir}")
    print(f"   Manifest: {manifest_path}")

    # Show statistics
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print(f"\nDataset Statistics:")
    print(f"   Total images: {manifest['total_cases']}")

    # Count by theme
    themes = {}
    for tc in manifest['test_cases']:
        theme = tc['theme']
        themes[theme] = themes.get(theme, 0) + 1

    print(f"   By theme:")
    for theme, count in themes.items():
        print(f"      {theme}: {count}")

    print("\n" + "=" * 70)
