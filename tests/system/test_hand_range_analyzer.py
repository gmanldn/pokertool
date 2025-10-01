"""Tests for the hand range analyzer utilities."""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.hand_range_analyzer import HandRangeAnalyzer, RangeParsingError


def create_analyzer() -> HandRangeAnalyzer:
    return HandRangeAnalyzer()


def test_parse_range_and_heatmap_generation():
    analyzer = create_analyzer()
    profile = analyzer.parse_range("AKS, AKO:0.5, 77")

    assert profile.total_combos == 4 + 12 + 6
    weights = analyzer.combination_weights(profile)
    assert weights["AKS"] == 4.0
    assert weights["AKO"] == 6.0
    assert weights["77"] == 6.0

    heatmap = analyzer.build_heatmap(profile)
    ranks = heatmap.ranks
    i_a = ranks.index("A")
    i_k = ranks.index("K")
    assert heatmap.matrix[min(i_a, i_k)][max(i_a, i_k)] >= 1.0  # suited allocation
    assert heatmap.matrix[max(i_a, i_k)][min(i_a, i_k)] >= 0.5  # offsuit weight


def test_equity_calculation_and_board_reduction():
    analyzer = create_analyzer()
    hero = analyzer.parse_range("QQ, AKS")
    villain = analyzer.parse_range("JJ, T9S")

    random.seed(42)
    result = analyzer.calculate_equity(hero, villain, board=["7h", "8h", "2c"], iterations=150)
    assert 0.0 < result.equity_one < 1.0
    assert 0.0 < result.equity_two < 1.0
    assert result.matchups_considered > 0

    adjusted = analyzer.reduce_with_board(villain, ["Jh", "Ts", "2c"])
    assert adjusted.total_combos < villain.total_combos
    assert any(entry.label == "JJ" for entry in adjusted.entries)


def test_frequency_filter_and_invalid_tokens():
    analyzer = create_analyzer()
    profile = analyzer.parse_range("AKS:1.0, QJS:0.25, 65O:0.75")
    filtered = analyzer.reduce_by_frequency(profile, 0.5)
    assert all(entry.frequency >= 0.5 for entry in filtered.entries)

    try:
        analyzer.parse_range("BadHand")
    except RangeParsingError as exc:
        assert "Invalid hand label" in str(exc)
    else:
        raise AssertionError("Expected RangeParsingError for invalid label")
