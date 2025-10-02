"""Advanced Nash equilibrium solver with game tree abstraction for PokerTool.

This module provides Nash equilibrium computation using CFR++ with support for:
- Heads-up zero-sum games
- Multi-way pot approximations
- Real-time strategy refinement
- Game tree abstraction for large games
- Information set bucketing

Module: nash_solver
Version: 2.0.0
Last Updated: 2025-10-05
Task: NASH-001
Dependencies: cfr_plus
Test Coverage: tests/system/test_nash_solver.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from .cfr_plus import CFRPlusSolution, CFRPlusSolver


@dataclass
class NashResult:
    """Represents the outcome of a Nash equilibrium computation."""

    strategies: Dict[str, List[float]]
    exploitability: float
    value: float
    iterations: int


class AdvancedNashSolver:
    """Facade combining CFR++ with helper routines for PokerTool."""

    def __init__(self, player_names: Tuple[str, str] = ("player_1", "player_2")) -> None:
        if len(player_names) != 2:
            raise ValueError("player_names must contain exactly two entries")
        self.player_one, self.player_two = player_names

    def solve_headsup(
        self,
        payoff_matrix: Sequence[Sequence[float]],
        *,
        iterations: int = 3000,
        warm_start: Optional[Mapping[str, Sequence[float]]] = None,
    ) -> NashResult:
        """Solve a two-player zero-sum normal-form game."""
        solver = CFRPlusSolver(payoff_matrix, warm_start=warm_start)
        solution = solver.solve(iterations)
        return self._build_result(solution)

    def solve_multiway(
        self,
        pairwise_game_map: Mapping[Tuple[str, str], Sequence[Sequence[float]]],
        *,
        iterations: int = 1500,
    ) -> Dict[str, object]:
        """Approximate strategies for a multi-way pot via pairwise CFR passes."""
        aggregated: Dict[str, List[List[float]]] = {}
        pair_solutions: Dict[Tuple[str, str], NashResult] = {}

        for (player_a, player_b), matrix in pairwise_game_map.items():
            local_solver = CFRPlusSolver(matrix)
            local_solution = local_solver.solve(iterations)
            mapped = self._map_result(local_solution, player_a, player_b)
            pair_solutions[(player_a, player_b)] = mapped

            aggregated.setdefault(player_a, []).append(mapped.strategies[player_a])
            aggregated.setdefault(player_b, []).append(mapped.strategies[player_b])

        aggregate_strategies = {
            player: self._average_vectors(vectors) for player, vectors in aggregated.items()
        }

        average_exploitability = sum(result.exploitability for result in pair_solutions.values()) / max(1, len(pair_solutions))

        return {
            "aggregate_strategies": aggregate_strategies,
            "pair_solutions": pair_solutions,
            "exploitability": average_exploitability,
        }

    def approximate_realtime_update(
        self,
        payoff_matrix: Sequence[Sequence[float]],
        previous_strategies: Mapping[str, Sequence[float]],
        *,
        iterations: int = 600,
    ) -> NashResult:
        """Quickly refine strategies using a CFR++ warm start."""
        warm_start = {
            "player_1": previous_strategies.get(self.player_one),
            "player_2": previous_strategies.get(self.player_two),
        }
        solver = CFRPlusSolver(payoff_matrix, warm_start=warm_start)
        solution = solver.solve(iterations)
        return self._build_result(solution)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_result(self, solution: CFRPlusSolution) -> NashResult:
        strategies = {
            self.player_one: list(solution.strategy_player_one),
            self.player_two: list(solution.strategy_player_two),
        }
        return NashResult(
            strategies=strategies,
            exploitability=solution.exploitability,
            value=solution.game_value,
            iterations=solution.iterations,
        )

    def _map_result(self, solution: CFRPlusSolution, player_a: str, player_b: str) -> NashResult:
        original_names = (self.player_one, self.player_two)
        self.player_one, self.player_two = player_a, player_b
        try:
            return self._build_result(solution)
        finally:
            self.player_one, self.player_two = original_names

    @staticmethod
    def _average_vectors(vectors: Iterable[Sequence[float]]) -> List[float]:
        cached = [list(vector) for vector in vectors]
        if not cached:
            return []
        length = len(cached[0])
        accumulator = [0.0] * length
        for vector in cached:
            for index, value in enumerate(vector):
                accumulator[index] += value
        count = len(cached)
        return [value / count for value in accumulator]


__all__ = ["AdvancedNashSolver", "NashResult"]


# ==============================================================================
# GAME TREE ABSTRACTION ALGORITHMS
# ==============================================================================


@dataclass
class InformationSet:
    """Represents an information set in the game tree.
    
    An information set groups together game states that are indistinguishable
    to the acting player based on available information.
    """
    
    set_id: str
    player: int  # 0 or 1
    available_actions: Tuple[str, ...]
    bucket_id: Optional[int] = None
    

@dataclass
class AbstractedNode:
    """A node in the abstracted game tree."""
    
    node_id: str
    parent_id: Optional[str]
    information_set: Optional[InformationSet]
    is_terminal: bool
    payoff: Optional[Tuple[float, float]] = None  # (player0_payoff, player1_payoff)
    children: List[str] = None
    
    def __post_init__(self) -> None:
        if self.children is None:
            self.children = []


class GameTreeAbstractor:
    """Abstracts large game trees into manageable sizes for CFR++.
    
    Uses bucketing and information set grouping to reduce the complexity
    of large poker games while preserving strategic structure.
    """
    
    def __init__(self, num_buckets: int = 1000):
        """Initialize the game tree abstractor.
        
        Args:
            num_buckets: Number of buckets for hand strength abstraction
        """
        self.num_buckets = num_buckets
        self.nodes: Dict[str, AbstractedNode] = {}
        self.information_sets: Dict[str, InformationSet] = {}
        self._bucket_assignments: Dict[str, int] = {}
        
    def create_node(self, 
                   node_id: str,
                   parent_id: Optional[str],
                   is_terminal: bool = False,
                   payoff: Optional[Tuple[float, float]] = None) -> AbstractedNode:
        """Create a new node in the abstracted game tree.
        
        Args:
            node_id: Unique identifier for this node
            parent_id: ID of parent node (None for root)
            is_terminal: Whether this is a terminal node
            payoff: Payoff at terminal nodes
            
        Returns:
            The created AbstractedNode
        """
        node = AbstractedNode(
            node_id=node_id,
            parent_id=parent_id,
            information_set=None,
            is_terminal=is_terminal,
            payoff=payoff
        )
        self.nodes[node_id] = node
        
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].children.append(node_id)
            
        return node
    
    def create_information_set(self,
                              set_id: str,
                              player: int,
                              actions: Sequence[str],
                              hand_strength: Optional[float] = None) -> InformationSet:
        """Create an information set and assign bucket.
        
        Args:
            set_id: Unique identifier for this information set
            player: Player who acts (0 or 1)
            actions: Available actions at this information set
            hand_strength: Optional hand strength for bucketing (0.0-1.0)
            
        Returns:
            The created InformationSet
        """
        bucket_id = None
        if hand_strength is not None:
            bucket_id = self._assign_bucket(hand_strength)
            
        info_set = InformationSet(
            set_id=set_id,
            player=player,
            available_actions=tuple(actions),
            bucket_id=bucket_id
        )
        self.information_sets[set_id] = info_set
        return info_set
    
    def _assign_bucket(self, hand_strength: float) -> int:
        """Assign a hand to a bucket based on its strength.
        
        Uses percentile-based bucketing to group similar hands.
        
        Args:
            hand_strength: Hand strength value between 0.0 and 1.0
            
        Returns:
            Bucket ID between 0 and num_buckets-1
        """
        clamped = max(0.0, min(1.0, hand_strength))
        bucket = int(clamped * self.num_buckets)
        return min(bucket, self.num_buckets - 1)
    
    def assign_information_set(self, node_id: str, info_set_id: str) -> None:
        """Assign an information set to a node.
        
        Args:
            node_id: Node to assign to
            info_set_id: Information set to assign
        """
        if node_id in self.nodes and info_set_id in self.information_sets:
            self.nodes[node_id].information_set = self.information_sets[info_set_id]
    
    def get_abstracted_strategy_space(self) -> Tuple[int, int]:
        """Calculate the size of the abstracted strategy space.
        
        Returns:
            Tuple of (num_information_sets, num_total_actions)
        """
        num_info_sets = len(self.information_sets)
        num_actions = sum(len(info_set.available_actions) 
                         for info_set in self.information_sets.values())
        return (num_info_sets, num_actions)
    
    def get_information_set_by_bucket(self, player: int, bucket_id: int) -> List[InformationSet]:
        """Get all information sets for a player in a specific bucket.
        
        Args:
            player: Player index (0 or 1)
            bucket_id: Bucket identifier
            
        Returns:
            List of information sets matching criteria
        """
        return [
            info_set for info_set in self.information_sets.values()
            if info_set.player == player and info_set.bucket_id == bucket_id
        ]


class HistogramAbstractor:
    """Creates card abstractions using hand strength histograms.
    
    This technique groups hands with similar equity distributions
    into buckets, dramatically reducing the game tree size.
    """
    
    def __init__(self, num_buckets: int = 200, num_histogram_bins: int = 50):
        """Initialize the histogram abstractor.
        
        Args:
            num_buckets: Number of buckets to create
            num_histogram_bins: Number of bins in each equity histogram
        """
        self.num_buckets = num_buckets
        self.num_histogram_bins = num_histogram_bins
        self._histograms: Dict[str, List[float]] = {}
        self._bucket_centers: List[List[float]] = []
        
    def create_histogram(self, hand_id: str, equity_samples: Sequence[float]) -> List[float]:
        """Create an equity histogram for a hand.
        
        Args:
            hand_id: Identifier for the hand
            equity_samples: Equity samples against random opponent hands
            
        Returns:
            Normalized histogram
        """
        histogram = [0.0] * self.num_histogram_bins
        
        for equity in equity_samples:
            bin_idx = int(equity * self.num_histogram_bins)
            bin_idx = min(bin_idx, self.num_histogram_bins - 1)
            histogram[bin_idx] += 1.0
            
        # Normalize
        total = sum(histogram)
        if total > 0:
            histogram = [count / total for count in histogram]
            
        self._histograms[hand_id] = histogram
        return histogram
    
    def compute_histogram_distance(self, hist1: Sequence[float], hist2: Sequence[float]) -> float:
        """Compute Earth Mover's Distance between two histograms.
        
        Args:
            hist1: First histogram
            hist2: Second histogram
            
        Returns:
            Distance metric (lower = more similar)
        """
        if len(hist1) != len(hist2):
            raise ValueError("Histograms must have same length")
            
        # Simplified Earth Mover's Distance
        cumsum1, cumsum2 = 0.0, 0.0
        distance = 0.0
        
        for i in range(len(hist1)):
            cumsum1 += hist1[i]
            cumsum2 += hist2[i]
            distance += abs(cumsum1 - cumsum2)
            
        return distance
    
    def cluster_hands(self, hand_ids: Sequence[str]) -> Dict[str, int]:
        """Cluster hands into buckets using k-means on histograms.
        
        Args:
            hand_ids: List of hand identifiers to cluster
            
        Returns:
            Mapping from hand_id to bucket_id
        """
        if not hand_ids:
            return {}
            
        # Initialize cluster centers randomly from existing hands
        import random
        random.seed(42)  # For reproducibility
        
        sample_size = min(self.num_buckets, len(hand_ids))
        center_hands = random.sample(list(hand_ids), sample_size)
        self._bucket_centers = [self._histograms[hand_id] for hand_id in center_hands]
        
        # K-means iterations
        assignments = {}
        for _ in range(10):  # 10 iterations
            # Assignment step
            for hand_id in hand_ids:
                if hand_id not in self._histograms:
                    continue
                    
                hist = self._histograms[hand_id]
                min_dist = float('inf')
                best_bucket = 0
                
                for bucket_id, center in enumerate(self._bucket_centers):
                    dist = self.compute_histogram_distance(hist, center)
                    if dist < min_dist:
                        min_dist = dist
                        best_bucket = bucket_id
                        
                assignments[hand_id] = best_bucket
            
            # Update step
            new_centers = []
            for bucket_id in range(len(self._bucket_centers)):
                bucket_hands = [hid for hid, bid in assignments.items() if bid == bucket_id]
                
                if bucket_hands:
                    # Average histograms in this bucket
                    avg_hist = [0.0] * self.num_histogram_bins
                    for hand_id in bucket_hands:
                        hist = self._histograms[hand_id]
                        for i in range(len(avg_hist)):
                            avg_hist[i] += hist[i]
                    
                    avg_hist = [val / len(bucket_hands) for val in avg_hist]
                    new_centers.append(avg_hist)
                else:
                    new_centers.append(self._bucket_centers[bucket_id])
                    
            self._bucket_centers = new_centers
            
        return assignments


__all__.extend([
    'InformationSet',
    'AbstractedNode',
    'GameTreeAbstractor',
    'HistogramAbstractor',
])

