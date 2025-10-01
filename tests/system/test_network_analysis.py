"""Tests for the network analysis utilities."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.network_analysis import Interaction, NetworkAnalysis


def build_sample_network() -> NetworkAnalysis:
    network = NetworkAnalysis()
    network.register_player("hero", sessions=120, vpip=0.28, aggression=2.5)
    network.register_player("villain1", sessions=85, vpip=0.32, aggression=1.8)
    network.register_player("villain2", sessions=60, vpip=0.22, aggression=1.6)

    now = time.time()
    for _ in range(6):
        network.add_interaction(
            "hero",
            "villain1",
            Interaction(table_id="alpha", timestamp=now, hands_played=40, shared_pots=8, shared_showdowns=5, ip_match=False, device_match=False),
        )
    for _ in range(3):
        network.add_interaction(
            "hero",
            "villain2",
            Interaction(table_id="beta", timestamp=now, hands_played=25, shared_pots=2, shared_showdowns=1),
        )
    for idx in range(5):
        network.add_interaction(
            "villain1",
            "villain2",
            Interaction(
                table_id=f"gamma_{idx}",
                timestamp=now,
                hands_played=60,
                shared_pots=15,
                shared_showdowns=4,
                ip_match=True,
                device_match=True,
            ),
        )
    return network


def test_collusion_detection_and_metrics():
    network = build_sample_network()
    warnings = network.collusion_warnings(threshold=0.4)
    assert warnings
    pair, metrics = warnings[0]
    assert set(pair) == {"villain1", "villain2"}
    assert "ip_match" in metrics.suspicious_flags
    assert metrics.collusion_score >= 0.6

    metrics_summary = network.network_metrics()
    assert metrics_summary["players"] == 3
    assert metrics_summary["relationships"] >= 2
    assert metrics_summary["density"] > 0


def test_visualization_payload_and_relationships():
    network = build_sample_network()
    payload = network.visualization_payload()
    assert len(payload["nodes"]) == 3
    assert any(edge["collusion_score"] >= 0.6 for edge in payload["edges"])

    relationships = network.build_relationships()
    assert "hero" in relationships
    hero_edges = relationships["hero"]
    assert any(edge.shared_tables >= 1 for edge in hero_edges)
