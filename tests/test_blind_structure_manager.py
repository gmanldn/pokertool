#!/usr/bin/env python3
"""Tests for Blind Structure Manager"""

import pytest
from src.pokertool.blind_structure_manager import BlindStructureManager, BlindLevel, StructureType


class TestBlindStructureManager:
    def test_initialization(self):
        manager = BlindStructureManager()
        structures = manager.get_structure_names()
        assert 'turbo' in structures
        assert 'standard' in structures
        assert 'hyper' in structures

    def test_get_structure(self):
        manager = BlindStructureManager()
        turbo = manager.get_structure('turbo')
        assert turbo is not None
        assert len(turbo) > 0
        assert turbo[0].level == 1

    def test_get_structure_case_insensitive(self):
        manager = BlindStructureManager()
        turbo1 = manager.get_structure('TURBO')
        turbo2 = manager.get_structure('turbo')
        assert turbo1 == turbo2

    def test_add_custom_structure(self):
        manager = BlindStructureManager()
        custom = [
            BlindLevel(1, 10, 20, 0, 10),
            BlindLevel(2, 20, 40, 0, 10),
        ]
        manager.add_custom_structure('mycustom', custom)
        retrieved = manager.get_structure('mycustom')
        assert retrieved == custom

    def test_calculate_total_duration(self):
        manager = BlindStructureManager()
        duration = manager.calculate_total_duration('turbo')
        # 8 levels * 5 minutes, but level 6 is a break
        assert duration == 35  # 7 non-break levels * 5

    def test_get_level_at_time(self):
        manager = BlindStructureManager()
        # At 3 minutes into turbo (5-min levels), should be level 1
        level = manager.get_level_at_time('turbo', 3)
        assert level.level == 1

        # At 12 minutes, should be level 3
        level = manager.get_level_at_time('turbo', 12)
        assert level.level == 3

    def test_get_break_levels(self):
        manager = BlindStructureManager()
        breaks = manager.get_break_levels('turbo')
        assert 6 in breaks

    def test_scale_structure(self):
        manager = BlindStructureManager()
        scaled = manager.scale_structure('turbo', 2.0)
        original = manager.get_structure('turbo')
        assert scaled[0].big_blind == original[0].big_blind * 2
        assert scaled[0].small_blind == original[0].small_blind * 2

    def test_get_average_big_blind(self):
        manager = BlindStructureManager()
        avg = manager.get_average_big_blind('turbo')
        assert avg > 0

    def test_validate_structure_valid(self):
        manager = BlindStructureManager()
        valid = [
            BlindLevel(1, 25, 50, 0, 10),
            BlindLevel(2, 50, 100, 0, 10),
            BlindLevel(3, 100, 200, 0, 10),
        ]
        assert manager.validate_structure(valid) is True

    def test_validate_structure_invalid_decreasing(self):
        manager = BlindStructureManager()
        invalid = [
            BlindLevel(1, 50, 100, 0, 10),
            BlindLevel(2, 25, 50, 0, 10),  # Decreasing!
        ]
        assert manager.validate_structure(invalid) is False

    def test_validate_structure_invalid_zero_duration(self):
        manager = BlindStructureManager()
        invalid = [
            BlindLevel(1, 25, 50, 0, 0),  # Zero duration!
        ]
        assert manager.validate_structure(invalid) is False

    def test_validate_structure_empty(self):
        manager = BlindStructureManager()
        assert manager.validate_structure([]) is False

    def test_standard_structure_details(self):
        manager = BlindStructureManager()
        standard = manager.get_structure('standard')
        assert len(standard) == 10
        assert standard[0].small_blind == 25
        assert standard[0].big_blind == 50
        assert standard[0].duration_minutes == 15

    def test_hyper_structure_details(self):
        manager = BlindStructureManager()
        hyper = manager.get_structure('hyper')
        assert len(hyper) == 6
        assert hyper[0].duration_minutes == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
