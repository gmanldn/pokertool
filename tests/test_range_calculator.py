#!/usr/bin/env python3
"""Tests for Range Calculator"""

import pytest
from src.pokertool.range_calculator import RangeCalculator, RangeType, HandRange


class TestRangeCalculator:
    def test_initialization(self):
        calc = RangeCalculator()
        assert 'tight_open' in calc.ranges
        assert 'standard_open' in calc.ranges
        assert 'loose_open' in calc.ranges

    def test_get_range(self):
        calc = RangeCalculator()
        tight = calc.get_range('tight_open')
        assert tight is not None
        assert tight.name == 'tight_open'
        assert tight.range_type == RangeType.OPENING

    def test_add_range(self):
        calc = RangeCalculator()
        custom_hands = {'AA', 'KK', 'QQ'}
        custom = calc.add_range('custom', RangeType.THREE_BET, custom_hands)
        assert custom.name == 'custom'
        assert 'AA' in custom.hands

    def test_calculate_range_percentage_pairs(self):
        calc = RangeCalculator()
        hands = {'AA', 'KK'}  # 2 pairs = 12 combos
        percentage = calc.calculate_range_percentage(hands)
        assert percentage == round((12 / 1326) * 100, 2)

    def test_calculate_range_percentage_suited(self):
        calc = RangeCalculator()
        hands = {'AKs'}  # 4 combos
        percentage = calc.calculate_range_percentage(hands)
        assert percentage == round((4 / 1326) * 100, 2)

    def test_calculate_range_percentage_offsuit(self):
        calc = RangeCalculator()
        hands = {'AKo'}  # 12 combos
        percentage = calc.calculate_range_percentage(hands)
        assert percentage == round((12 / 1326) * 100, 2)

    def test_is_hand_in_range(self):
        calc = RangeCalculator()
        assert calc.is_hand_in_range('AA', 'tight_open') is True
        assert calc.is_hand_in_range('72o', 'tight_open') is False

    def test_combine_ranges(self):
        calc = RangeCalculator()
        calc.add_range('range1', RangeType.OPENING, {'AA', 'KK'})
        calc.add_range('range2', RangeType.OPENING, {'QQ', 'JJ'})
        combined = calc.combine_ranges('range1', 'range2', 'combined')
        assert combined is not None
        assert len(combined.hands) == 4

    def test_subtract_ranges(self):
        calc = RangeCalculator()
        calc.add_range('big', RangeType.OPENING, {'AA', 'KK', 'QQ'})
        calc.add_range('small', RangeType.OPENING, {'QQ'})
        result = calc.subtract_ranges('big', 'small', 'result')
        assert result is not None
        assert 'AA' in result.hands
        assert 'KK' in result.hands
        assert 'QQ' not in result.hands

    def test_get_range_strength(self):
        calc = RangeCalculator()
        tight = calc.get_range('tight_open')
        strength = calc.get_range_strength('tight_open')
        assert strength >= 0.0
        assert strength <= 100.0

    def test_polarize_range(self):
        calc = RangeCalculator()
        calc.add_range('test', RangeType.OPENING, {'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55'})
        polarized = calc.polarize_range('test', 20, 20)
        assert polarized is not None
        assert len(polarized.hands) == 4  # 20% of 10 = 2 top + 2 bottom

    def test_get_all_range_names(self):
        calc = RangeCalculator()
        names = calc.get_all_range_names()
        assert 'tight_open' in names
        assert 'standard_open' in names
        assert len(names) >= 3

    def test_export_range(self):
        calc = RangeCalculator()
        calc.add_range('test', RangeType.OPENING, {'AA', 'KK'})
        export = calc.export_range('test')
        assert 'test' in export
        assert 'AA' in export

    def test_parse_range_string(self):
        calc = RangeCalculator()
        hands = calc._parse_range_string("AA, KK, QQ")
        assert 'AA' in hands
        assert 'KK' in hands
        assert 'QQ' in hands
        assert len(hands) == 3

    def test_tight_range_percentage(self):
        calc = RangeCalculator()
        tight = calc.get_range('tight_open')
        assert tight.percentage > 10.0
        assert tight.percentage < 20.0

    def test_standard_range_wider_than_tight(self):
        calc = RangeCalculator()
        tight = calc.get_range('tight_open')
        standard = calc.get_range('standard_open')
        assert standard.percentage > tight.percentage

    def test_get_nonexistent_range(self):
        calc = RangeCalculator()
        result = calc.get_range('nonexistent')
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
