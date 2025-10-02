"""Player network analysis with relationship mapping and collusion heuristics."""

from __future__ import annotations

import itertools
import math
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass
class Interaction:
    """Represents a player interaction at the table."""

    table_id: str
    timestamp: float
    hands_played: int
    shared_pots: int
    shared_showdowns: int
    ip_match: bool = False
    device_match: bool = False


@dataclass
class PlayerNode:
    """Node metadata for visualization."""

    player_id: str
    sessions: int
    vpip: float
    aggression: float


@dataclass
class EdgeMetrics:
    """Relationship metrics between two players."""

    weight: float
    collusion_score: float
    shared_tables: int
    suspicious_flags: List[str]


class NetworkAnalysis:
    """Builds a relationship graph and surfaces collusion warnings."""

    def __init__(self):
        self._interactions: Dict[Tuple[str, str], List[Interaction]] = defaultdict(list)
        self._player_nodes: Dict[str, PlayerNode] = {}

    # ------------------------------------------------------------------
    # Data ingestion
    # ------------------------------------------------------------------
    def register_player(self, player_id: str, sessions: int, vpip: float, aggression: float) -> None:
        self._player_nodes[player_id] = PlayerNode(player_id=player_id, sessions=sessions, vpip=vpip, aggression=aggression)

    def add_interaction(self, player_a: str, player_b: str, interaction: Interaction) -> None:
        if player_a == player_b:
            return
        key = self._normalize_key(player_a, player_b)
        self._interactions[key].append(interaction)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    def build_relationships(self) -> Dict[str, List[EdgeMetrics]]:
        graph: Dict[str, List[EdgeMetrics]] = defaultdict(list)
        for (player_a, player_b), events in self._interactions.items():
            metrics = self._calculate_edge(player_a, player_b, events)
            graph[player_a].append(metrics)
            graph[player_b].append(metrics)
        return graph

    def collusion_warnings(self, threshold: float = 0.6) -> List[Tuple[Tuple[str, str], EdgeMetrics]]:
        warnings = []
        for (player_a, player_b), events in self._interactions.items():
            metrics = self._calculate_edge(player_a, player_b, events)
            if metrics.collusion_score >= threshold:
                warnings.append(((player_a, player_b), metrics))
        warnings.sort(key=lambda entry: entry[1].collusion_score, reverse=True)
        return warnings

    def visualization_payload(self) -> Dict[str, List[Dict[str, object]]]:
        nodes = [node.__dict__ for node in self._player_nodes.values()]
        edges = []
        for (player_a, player_b), events in self._interactions.items():
            metrics = self._calculate_edge(player_a, player_b, events)
            edges.append({
                "source": player_a,
                "target": player_b,
                "weight": metrics.weight,
                "collusion_score": metrics.collusion_score,
            })
        return {"nodes": nodes, "edges": edges}

    def network_metrics(self) -> Dict[str, float]:
        degree_counts = {player: 0 for player in self._player_nodes}
        total_weight = 0.0
        for (player_a, player_b), events in self._interactions.items():
            metrics = self._calculate_edge(player_a, player_b, events)
            degree_counts[player_a] = degree_counts.get(player_a, 0) + 1
            degree_counts[player_b] = degree_counts.get(player_b, 0) + 1
            total_weight += metrics.weight
        degrees = list(degree_counts.values())
        avg_degree = statistics.fmean(degrees) if degrees else 0.0
        density = 0.0
        player_count = len(self._player_nodes)
        if player_count > 1:
            density = total_weight / (player_count * (player_count - 1) / 2)
        return {
            "players": player_count,
            "relationships": len(self._interactions),
            "average_degree": round(avg_degree, 2),
            "density": round(density, 3),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _calculate_edge(self, player_a: str, player_b: str, events: List[Interaction]) -> EdgeMetrics:
        shared_tables = len({event.table_id for event in events})
        total_hands = sum(event.hands_played for event in events)
        shared_showdowns = sum(event.shared_showdowns for event in events)
        weight = round(total_hands / max(shared_tables, 1), 2)
        suspicious_flags: List[str] = []
        collusion_score = 0.0

        if shared_tables >= 5 and total_hands >= 200:
            collusion_score += 0.25
            suspicious_flags.append("volume")
        if shared_showdowns >= 10:
            collusion_score += 0.2
            suspicious_flags.append("showdowns")
        ip_matches = sum(1 for event in events if event.ip_match)
        device_matches = sum(1 for event in events if event.device_match)
        if ip_matches:
            collusion_score += min(0.3, 0.1 * ip_matches)
            suspicious_flags.append("ip_match")
        if device_matches:
            collusion_score += min(0.2, 0.05 * device_matches)
            suspicious_flags.append("device_match")
        if total_hands > 0:
            coordination_ratio = sum(event.shared_pots for event in events) / total_hands
            if coordination_ratio >= 0.15:
                collusion_score += min(0.25, coordination_ratio)
                suspicious_flags.append("shared_pots")

        collusion_score = min(collusion_score, 1.0)
        return EdgeMetrics(weight=weight, collusion_score=round(collusion_score, 3), shared_tables=shared_tables, suspicious_flags=suspicious_flags)

    @staticmethod
    def _normalize_key(player_a: str, player_b: str) -> Tuple[str, str]:
        return tuple(sorted((player_a, player_b)))


__all__ = [
    "EdgeMetrics",
    "Interaction",
    "NetworkAnalysis",
    "PlayerNode",
]
