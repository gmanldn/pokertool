"""System coverage for the advanced Nash equilibrium solver."""

from __future__ import annotations

import os
import sys

import pytest

from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.nash_solver import AdvancedNashSolver


MATCHING_PENNIES = (
    (1.0, -1.0),
    (-1.0, 1.0),
)


def test_matching_pennies_equilibrium() -> None:
    solver = AdvancedNashSolver(("hero", "villain"))
    result = solver.solve_headsup(MATCHING_PENNIES, iterations=5000)

    hero_strategy = result.strategies["hero"]
    villain_strategy = result.strategies["villain"]

    assert pytest.approx(hero_strategy[0], abs=0.05) == 0.5
    assert pytest.approx(villain_strategy[0], abs=0.05) == 0.5
    assert pytest.approx(result.value, abs=0.05) == 0.0
    assert result.exploitability < 0.15


def test_multiway_pairwise_aggregation() -> None:
    solver = AdvancedNashSolver(("player_a", "player_b"))
    pairwise_map = {
        ("player_a", "player_b"): MATCHING_PENNIES,
        ("player_a", "player_c"): MATCHING_PENNIES,
        ("player_b", "player_c"): MATCHING_PENNIES,
    }

    result = solver.solve_multiway(pairwise_map, iterations=2500)

    assert set(result["aggregate_strategies"].keys()) == {"player_a", "player_b", "player_c"}
    for strategy in result["aggregate_strategies"].values():
        assert len(strategy) == 2
        assert pytest.approx(strategy[0], abs=0.08) == 0.5
    assert result["exploitability"] < 0.2


def test_realtime_update_stays_close_to_previous_solution() -> None:
    solver = AdvancedNashSolver(("hero", "villain"))
    baseline = solver.solve_headsup(MATCHING_PENNIES, iterations=4000)
    new_matrix = (
        (1.1, -1.05),
        (-0.9, 0.95),
    )

    updated = solver.approximate_realtime_update(new_matrix, baseline.strategies, iterations=800)

    assert updated.iterations == 800
    assert updated.exploitability < 0.25
    assert len(updated.strategies["hero"]) == len(baseline.strategies["hero"])
    assert abs(updated.strategies["hero"][0] - baseline.strategies["hero"][0]) < 0.2


def test_game_tree_abstractor_creates_nodes() -> None:
    """Test creating nodes in the game tree abstractor."""
    from pokertool.nash_solver import GameTreeAbstractor
    
    abstractor = GameTreeAbstractor(num_buckets=100)
    
    # Create root node
    root = abstractor.create_node("root", None)
    assert root.node_id == "root"
    assert root.parent_id is None
    assert not root.is_terminal
    
    # Create child nodes
    child1 = abstractor.create_node("child1", "root")
    child2 = abstractor.create_node("child2", "root")
    
    assert "child1" in abstractor.nodes["root"].children
    assert "child2" in abstractor.nodes["root"].children
    
    # Create terminal node
    terminal = abstractor.create_node("term1", "child1", is_terminal=True, payoff=(1.0, -1.0))
    assert terminal.is_terminal
    assert terminal.payoff == (1.0, -1.0)


def test_game_tree_abstractor_information_sets() -> None:
    """Test creating and assigning information sets."""
    from pokertool.nash_solver import GameTreeAbstractor
    
    abstractor = GameTreeAbstractor(num_buckets=50)
    
    # Create information sets with different hand strengths
    info_set1 = abstractor.create_information_set(
        "is1", player=0, actions=["fold", "call", "raise"], hand_strength=0.8
    )
    info_set2 = abstractor.create_information_set(
        "is2", player=1, actions=["fold", "call"], hand_strength=0.3
    )
    
    assert info_set1.player == 0
    assert len(info_set1.available_actions) == 3
    assert info_set1.bucket_id is not None
    
    # High strength hand should be in higher bucket
    assert info_set1.bucket_id > info_set2.bucket_id
    
    # Assign to nodes
    node = abstractor.create_node("node1", None)
    abstractor.assign_information_set("node1", "is1")
    assert abstractor.nodes["node1"].information_set == info_set1


def test_game_tree_abstractor_bucket_assignment() -> None:
    """Test bucket assignment logic."""
    from pokertool.nash_solver import GameTreeAbstractor
    
    abstractor = GameTreeAbstractor(num_buckets=100)
    
    # Test boundary cases
    bucket_min = abstractor._assign_bucket(0.0)
    bucket_mid = abstractor._assign_bucket(0.5)
    bucket_max = abstractor._assign_bucket(1.0)
    
    assert bucket_min == 0
    assert bucket_mid == 50
    assert bucket_max == 99
    
    # Test clamping
    bucket_under = abstractor._assign_bucket(-0.5)
    bucket_over = abstractor._assign_bucket(1.5)
    assert bucket_under == 0
    assert bucket_over == 99


def test_game_tree_abstractor_strategy_space() -> None:
    """Test calculation of abstracted strategy space size."""
    from pokertool.nash_solver import GameTreeAbstractor
    
    abstractor = GameTreeAbstractor(num_buckets=100)
    
    # Create several information sets
    abstractor.create_information_set("is1", 0, ["fold", "call", "raise"])
    abstractor.create_information_set("is2", 1, ["fold", "call"])
    abstractor.create_information_set("is3", 0, ["check", "bet"])
    
    num_sets, num_actions = abstractor.get_abstracted_strategy_space()
    
    assert num_sets == 3
    assert num_actions == 7  # 3 + 2 + 2


def test_game_tree_abstractor_bucket_queries() -> None:
    """Test querying information sets by bucket."""
    from pokertool.nash_solver import GameTreeAbstractor
    
    abstractor = GameTreeAbstractor(num_buckets=10)
    
    # Create info sets in different buckets
    abstractor.create_information_set("is1", 0, ["fold", "call"], 0.85)  # bucket 8
    abstractor.create_information_set("is2", 0, ["fold", "raise"], 0.82)  # bucket 8
    abstractor.create_information_set("is3", 1, ["check", "bet"], 0.85)  # bucket 8
    abstractor.create_information_set("is4", 0, ["fold", "call"], 0.25)  # bucket 2
    
    # Query player 0, bucket 8
    results = abstractor.get_information_set_by_bucket(0, 8)
    assert len(results) == 2
    assert all(info_set.player == 0 for info_set in results)
    
    # Query player 1, bucket 8
    results = abstractor.get_information_set_by_bucket(1, 8)
    assert len(results) == 1


def test_histogram_abstractor_creation() -> None:
    """Test creating histograms from equity samples."""
    from pokertool.nash_solver import HistogramAbstractor
    
    abstractor = HistogramAbstractor(num_buckets=50, num_histogram_bins=20)
    
    # Create histogram from equity samples
    equity_samples = [0.55, 0.52, 0.58, 0.60, 0.54, 0.56, 0.53, 0.57]
    histogram = abstractor.create_histogram("AKs", equity_samples)
    
    assert len(histogram) == 20
    assert pytest.approx(sum(histogram), abs=1e-6) == 1.0  # Should be normalized
    
    # Most weight should be in bins around 0.55
    bin_idx = int(0.55 * 20)
    assert histogram[bin_idx] > 0.1


def test_histogram_abstractor_distance() -> None:
    """Test computing distance between histograms."""
    from pokertool.nash_solver import HistogramAbstractor
    
    abstractor = HistogramAbstractor()
    
    # Create two similar histograms
    hist1 = [0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.05]
    hist2 = [0.12, 0.18, 0.32, 0.19, 0.11, 0.04, 0.04]
    
    distance = abstractor.compute_histogram_distance(hist1, hist2)
    
    # Distance should be small for similar histograms
    assert distance < 0.5
    
    # Create very different histograms
    hist3 = [0.9, 0.05, 0.02, 0.01, 0.01, 0.01, 0.0]
    distance2 = abstractor.compute_histogram_distance(hist1, hist3)
    
    # Distance should be larger
    assert distance2 > distance


def test_histogram_abstractor_clustering() -> None:
    """Test clustering hands into buckets."""
    from pokertool.nash_solver import HistogramAbstractor
    
    abstractor = HistogramAbstractor(num_buckets=5, num_histogram_bins=10)
    
    # Create histograms for different hand types
    # Strong hands: high equity
    abstractor.create_histogram("AA", [0.85] * 10)
    abstractor.create_histogram("KK", [0.82] * 10)
    
    # Medium hands
    abstractor.create_histogram("AK", [0.55] * 10)
    abstractor.create_histogram("AQ", [0.52] * 10)
    
    # Weak hands
    abstractor.create_histogram("72o", [0.25] * 10)
    abstractor.create_histogram("83o", [0.28] * 10)
    
    hand_ids = ["AA", "KK", "AK", "AQ", "72o", "83o"]
    assignments = abstractor.cluster_hands(hand_ids)
    
    # Should have assignments for all hands
    assert len(assignments) == 6
    
    # Similar hands should be in same bucket
    assert assignments["AA"] == assignments["KK"]
    assert assignments["AK"] == assignments["AQ"]
    assert assignments["72o"] == assignments["83o"]
    
    # Different strength hands should be in different buckets
    assert assignments["AA"] != assignments["72o"]

