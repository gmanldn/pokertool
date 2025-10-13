#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for Synthetic Scrape Data Generator
==========================================

DATA-030: Synthetic Scrape Data Generator Tests

Tests cover:
- Table theme configuration
- Player and table state generation
- Image rendering
- Ground truth label generation
- Batch generation
- Manifest creation
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from pokertool.synthetic_data_generator import (
    SyntheticDataGenerator,
    TableTheme,
    PlayerSeat,
    TableState,
    generate_synthetic_dataset,
    PIL_AVAILABLE
)

# Skip all tests if PIL not available
pytestmark = pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL/Pillow not available")


class TestTableTheme:
    """Test table theme configurations."""

    def test_standard_green(self):
        """Test standard green theme."""
        theme = TableTheme.standard_green()

        assert theme.name == "standard_green"
        assert isinstance(theme.felt_color, tuple)
        assert len(theme.felt_color) == 3
        assert all(0 <= c <= 255 for c in theme.felt_color)

    def test_betfair_purple(self):
        """Test Betfair purple theme."""
        theme = TableTheme.betfair_purple()

        assert theme.name == "betfair_purple"
        assert isinstance(theme.felt_color, tuple)

    def test_custom_theme(self):
        """Test creating custom theme."""
        theme = TableTheme("custom", (100, 150, 200), (50, 75, 100))

        assert theme.name == "custom"
        assert theme.felt_color == (100, 150, 200)
        assert theme.rail_color == (50, 75, 100)


class TestPlayerSeat:
    """Test player seat data structure."""

    def test_create_player_seat(self):
        """Test creating player seat."""
        player = PlayerSeat(
            seat_number=1,
            position=(500, 600),
            name="TestPlayer",
            stack=100.0,
            cards=['As', 'Kh'],
            bet=10.0,
            is_button=True,
            is_active=True
        )

        assert player.seat_number == 1
        assert player.position == (500, 600)
        assert player.name == "TestPlayer"
        assert player.stack == 100.0
        assert player.cards == ['As', 'Kh']
        assert player.bet == 10.0
        assert player.is_button is True
        assert player.is_active is True


class TestTableState:
    """Test table state data structure."""

    def test_create_table_state(self):
        """Test creating table state."""
        theme = TableTheme.standard_green()
        players = [
            PlayerSeat(1, (500, 600), "Alice", 100.0),
            PlayerSeat(2, (700, 400), "Bob", 150.0)
        ]

        state = TableState(
            pot_size=50.0,
            board_cards=['Qd', 'Jc', '9s'],
            players=players,
            button_position=1,
            blinds=(0.05, 0.10),
            theme=theme,
            stakes="NL10",
            resolution=(1920, 1080)
        )

        assert state.pot_size == 50.0
        assert len(state.board_cards) == 3
        assert len(state.players) == 2
        assert state.button_position == 1
        assert state.blinds == (0.05, 0.10)
        assert state.stakes == "NL10"


class TestDataGenerator:
    """Test synthetic data generator."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create generator instance."""
        return SyntheticDataGenerator(temp_dir)

    def test_init(self, temp_dir):
        """Test generator initialization."""
        generator = SyntheticDataGenerator(temp_dir)

        assert generator.output_dir == temp_dir
        assert temp_dir.exists()
        assert len(generator.ranks) == 13
        assert len(generator.suits) == 4

    def test_generate_deck(self, generator):
        """Test deck generation."""
        deck = generator.generate_deck()

        assert len(deck) == 52  # Full deck
        assert 'As' in deck
        assert 'Kh' in deck
        assert '2c' in deck

    def test_deal_cards(self, generator):
        """Test dealing cards."""
        cards = generator.deal_cards(5)

        assert len(cards) == 5
        assert len(set(cards)) == 5  # All unique

    def test_deal_cards_with_exclusions(self, generator):
        """Test dealing with excluded cards."""
        exclude = ['As', 'Kh']
        cards = generator.deal_cards(5, exclude=exclude)

        assert len(cards) == 5
        assert 'As' not in cards
        assert 'Kh' not in cards

    def test_generate_player_name(self, generator):
        """Test player name generation."""
        name = generator.generate_player_name()

        assert isinstance(name, str)
        assert len(name) > 0
        assert len(name) < 30

    def test_generate_table_state(self, generator):
        """Test table state generation."""
        theme = TableTheme.standard_green()
        state = generator.generate_table_state(theme, "NL10", num_players=6)

        assert len(state.players) == 6
        assert state.pot_size > 0
        assert state.blinds == (0.05, 0.10)  # NL10
        assert state.stakes == "NL10"
        assert 1 <= state.button_position <= 6

    def test_generate_table_state_random_players(self, generator):
        """Test table state with random player count."""
        theme = TableTheme.standard_green()
        state = generator.generate_table_state(theme, "NL25")

        assert 2 <= len(state.players) <= 9

    def test_generate_table_state_cards_unique(self, generator):
        """Test that dealt cards are unique."""
        theme = TableTheme.standard_green()
        state = generator.generate_table_state(theme, "NL10", num_players=9)

        all_cards = []
        for player in state.players:
            if player.cards:
                all_cards.extend(player.cards)
        all_cards.extend(state.board_cards)

        # All cards should be unique
        assert len(all_cards) == len(set(all_cards))

    def test_render_table(self, generator):
        """Test table rendering."""
        theme = TableTheme.standard_green()
        state = generator.generate_table_state(theme, "NL10", num_players=4)

        img = generator.render_table(state)

        assert img is not None
        assert img.size == (1920, 1080)
        assert img.mode == 'RGB'

    def test_render_table_with_variations(self, generator):
        """Test rendering with variations."""
        theme = TableTheme.standard_green()
        state = generator.generate_table_state(theme, "NL10", num_players=4)

        variations = {
            'brightness': 1.2,
            'contrast': 0.9,
            'blur': True,
            'blur_amount': 1.0
        }

        img = generator.render_table(state, variations)

        assert img is not None
        assert img.size == (1920, 1080)

    def test_generate_ground_truth(self, generator):
        """Test ground truth generation."""
        theme = TableTheme.standard_green()
        players = [
            PlayerSeat(1, (500, 600), "Alice", 100.0, cards=['As', 'Kh']),
            PlayerSeat(2, (700, 400), "Bob", 150.0, bet=10.0)
        ]

        state = TableState(
            pot_size=50.0,
            board_cards=['Qd', 'Jc', '9s'],
            players=players,
            button_position=1,
            blinds=(0.05, 0.10),
            theme=theme,
            stakes="NL10"
        )

        gt = generator.generate_ground_truth(state)

        assert gt['pot_size'] == 50.0
        assert gt['player_stacks'][1] == 100.0
        assert gt['player_stacks'][2] == 150.0
        assert gt['player_names'][1] == "Alice"
        assert gt['hole_cards'] == ['As', 'Kh']
        assert gt['board_cards'] == ['Qd', 'Jc', '9s']
        assert gt['button_position'] == 1
        assert gt['blinds'] == [0.05, 0.10]


class TestBatchGeneration:
    """Test batch generation."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create generator instance."""
        return SyntheticDataGenerator(temp_dir)

    def test_generate_batch_small(self, generator, temp_dir):
        """Test generating small batch."""
        results = generator.generate_batch(5, variations_enabled=False)

        assert len(results) == 5

        # Check files were created
        image_files = list(temp_dir.glob("*.png"))
        json_files = list(temp_dir.glob("*.json"))

        assert len(image_files) == 5
        assert len(json_files) == 5

    def test_generate_batch_with_variations(self, generator, temp_dir):
        """Test batch with variations enabled."""
        results = generator.generate_batch(3, variations_enabled=True)

        assert len(results) == 3

    def test_generate_batch_themes(self, generator, temp_dir):
        """Test batch with specific themes."""
        themes = [TableTheme.standard_green(), TableTheme.betfair_purple()]
        results = generator.generate_batch(4, themes=themes)

        assert len(results) == 4

        # Check that themes were used
        json_files = list(temp_dir.glob("*.json"))
        themes_used = set()

        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
                themes_used.add(data['theme'])

        assert themes_used.issubset({'standard_green', 'betfair_purple'})

    def test_generate_batch_stakes(self, generator, temp_dir):
        """Test batch with specific stakes."""
        stakes = ["NL10", "NL25"]
        results = generator.generate_batch(4, stakes_levels=stakes)

        assert len(results) == 4

        # Check that stakes were used
        json_files = list(temp_dir.glob("*.json"))
        stakes_used = set()

        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
                stakes_used.add(data['stakes'])

        assert stakes_used.issubset({'NL10', 'NL25'})

    def test_batch_filenames_sequential(self, generator, temp_dir):
        """Test that batch creates sequential filenames."""
        generator.generate_batch(3)

        assert (temp_dir / "synthetic_00000.png").exists()
        assert (temp_dir / "synthetic_00001.png").exists()
        assert (temp_dir / "synthetic_00002.png").exists()

    def test_batch_json_structure(self, generator, temp_dir):
        """Test JSON file structure."""
        generator.generate_batch(2)

        json_file = temp_dir / "synthetic_00000.json"
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Check required fields
        assert 'id' in data
        assert 'name' in data
        assert 'ground_truth' in data
        assert 'theme' in data
        assert 'stakes' in data
        assert 'resolution' in data
        assert 'metadata' in data

        # Check ground truth structure
        gt = data['ground_truth']
        assert 'pot_size' in gt
        assert 'player_stacks' in gt
        assert 'player_names' in gt


class TestManifestGeneration:
    """Test manifest generation."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def generator(self, temp_dir):
        """Create generator instance."""
        return SyntheticDataGenerator(temp_dir)

    def test_generate_manifest(self, generator, temp_dir):
        """Test manifest generation."""
        # Generate batch first
        results = generator.generate_batch(3)

        # Generate manifest
        manifest_path = generator.generate_manifest(results)

        assert manifest_path.exists()
        assert manifest_path.name == "manifest.json"

    def test_manifest_structure(self, generator, temp_dir):
        """Test manifest file structure."""
        results = generator.generate_batch(5)
        manifest_path = generator.generate_manifest(results)

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert 'version' in manifest
        assert 'generator' in manifest
        assert 'total_cases' in manifest
        assert 'test_cases' in manifest

        assert manifest['total_cases'] == 5
        assert len(manifest['test_cases']) == 5

    def test_manifest_test_cases(self, generator, temp_dir):
        """Test manifest test cases content."""
        results = generator.generate_batch(2)
        manifest_path = generator.generate_manifest(results)

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        # Check first test case
        tc = manifest['test_cases'][0]
        assert 'id' in tc
        assert 'ground_truth' in tc
        assert 'theme' in tc


class TestConvenienceFunction:
    """Test convenience function."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_generate_synthetic_dataset(self, temp_dir):
        """Test convenience function."""
        manifest_path = generate_synthetic_dataset(temp_dir, num_images=5, seed=42)

        assert manifest_path.exists()

        # Check files created
        image_files = list(temp_dir.glob("*.png"))
        json_files = list(temp_dir.glob("*.json"))

        assert len(image_files) == 5
        # 5 test case JSONs + 1 manifest
        assert len(json_files) == 6

    def test_generate_dataset_deterministic(self, temp_dir):
        """Test that same seed produces same results."""
        # Generate twice with same seed
        temp_dir1 = temp_dir / "run1"
        temp_dir2 = temp_dir / "run2"
        temp_dir1.mkdir()
        temp_dir2.mkdir()

        generate_synthetic_dataset(temp_dir1, num_images=3, seed=123)
        generate_synthetic_dataset(temp_dir2, num_images=3, seed=123)

        # Read manifests
        with open(temp_dir1 / "manifest.json", 'r') as f:
            manifest1 = json.load(f)

        with open(temp_dir2 / "manifest.json", 'r') as f:
            manifest2 = json.load(f)

        # Should have same player names (deterministic)
        names1 = [manifest1['test_cases'][0]['ground_truth']['player_names']['1']]
        names2 = [manifest2['test_cases'][0]['ground_truth']['player_names']['1']]

        # With same seed, first player name should match
        assert names1[0] == names2[0]


class TestIntegration:
    """Integration tests."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_full_pipeline(self, temp_dir):
        """Test complete generation pipeline."""
        # Generate dataset
        manifest_path = generate_synthetic_dataset(temp_dir, num_images=10, seed=42)

        # Verify all files
        image_files = list(temp_dir.glob("*.png"))
        assert len(image_files) == 10

        # Verify manifest
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert manifest['total_cases'] == 10

        # Verify each test case has matching image
        for tc in manifest['test_cases']:
            tc_id = tc['id']
            image_path = temp_dir / f"{tc_id}.png"
            assert image_path.exists()

    def test_qa_harness_compatibility(self, temp_dir):
        """Test that generated data is compatible with QA harness format."""
        # Generate dataset
        generate_synthetic_dataset(temp_dir, num_images=3)

        # Check QA harness can load it
        from pokertool.scrape_qa_harness import ScrapeQAHarness

        harness = ScrapeQAHarness(temp_dir)
        count = harness.load_test_suite()

        assert count == 3
        assert len(harness.test_cases) == 3

        # Check test case has required fields
        tc = harness.test_cases[0]
        assert tc.ground_truth.pot_size > 0
        assert len(tc.ground_truth.player_stacks) > 0


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '-s'])
