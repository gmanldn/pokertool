"""Compact CFR++ implementation for normal-form poker abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


def _normalise(vector: Sequence[float]) -> List[float]:
    total = sum(vector)
    if total > 0:
        return [value / total for value in vector]
    if not vector:
        return []
    uniform = 1.0 / len(vector)
    return [uniform for _ in vector]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _matrix_vector_product(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> List[float]:
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]


def _transposed_matrix_vector_product(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> List[float]:
    columns = len(matrix[0])
    return [sum(matrix[i][j] * vector[i] for i in range(len(matrix))) for j in range(columns)]


@dataclass
class CFRPlusSolution:
    """Container for a solved normal-form game."""

    strategy_player_one: List[float]
    strategy_player_two: List[float]
    game_value: float
    exploitability: float
    iterations: int


class CFRPlusSolver:
    """CFR++ solver for two-player zero-sum normal-form games."""

    def __init__(
        self,
        payoff_matrix: Sequence[Sequence[float]],
        *,
        warm_start: Optional[Mapping[str, Sequence[float]]] = None,
    ) -> None:
        if not payoff_matrix or not payoff_matrix[0]:
            raise ValueError("payoff_matrix must contain at least one action per player")
        self.payoff_matrix = [[float(value) for value in row] for row in payoff_matrix]
        self.num_actions_p1 = len(self.payoff_matrix)
        self.num_actions_p2 = len(self.payoff_matrix[0])
        self.regret_sums_p1 = [0.0] * self.num_actions_p1
        self.regret_sums_p2 = [0.0] * self.num_actions_p2
        self.strategy_sums_p1 = [0.0] * self.num_actions_p1
        self.strategy_sums_p2 = [0.0] * self.num_actions_p2
        if warm_start:
            self._seed_from_warm_start(warm_start)

    def solve(self, iterations: int = 2000) -> CFRPlusSolution:
        iterations = max(1, int(iterations))
        for _ in range(iterations):
            strategy_p1 = self._current_strategy(self.regret_sums_p1)
            strategy_p2 = self._current_strategy(self.regret_sums_p2)

            self._accumulate(self.strategy_sums_p1, strategy_p1)
            self._accumulate(self.strategy_sums_p2, strategy_p2)

            util_p1 = _matrix_vector_product(self.payoff_matrix, strategy_p2)
            util_p2 = _transposed_matrix_vector_product(self.payoff_matrix, strategy_p1)
            util_p2 = [-value for value in util_p2]  # zero-sum transformation

            value_p1 = _dot(strategy_p1, util_p1)
            value_p2 = _dot(strategy_p2, util_p2)

            self._update_regrets(self.regret_sums_p1, util_p1, value_p1)
            self._update_regrets(self.regret_sums_p2, util_p2, value_p2)

        avg_strategy_p1 = _normalise(self.strategy_sums_p1)
        avg_strategy_p2 = _normalise(self.strategy_sums_p2)
        game_value = _dot(avg_strategy_p1, _matrix_vector_product(self.payoff_matrix, avg_strategy_p2))
        exploitability = self._compute_exploitability(avg_strategy_p1, avg_strategy_p2)
        return CFRPlusSolution(avg_strategy_p1, avg_strategy_p2, game_value, exploitability, iterations)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _seed_from_warm_start(self, warm_start: Mapping[str, Sequence[float]]) -> None:
        player_one = warm_start.get("player_1")
        player_two = warm_start.get("player_2")
        if player_one:
            normalised = _normalise(player_one)
            self.strategy_sums_p1 = [value * len(player_one) for value in normalised]
        if player_two:
            normalised = _normalise(player_two)
            self.strategy_sums_p2 = [value * len(player_two) for value in normalised]

    def _current_strategy(self, regrets: Sequence[float]) -> List[float]:
        positives = [max(0.0, regret) for regret in regrets]
        normalised = _normalise(positives)
        if not any(positives):
            return [1.0 / len(positives) for _ in positives]
        return normalised

    def _accumulate(self, accumulator: MutableMapping[int, float] | List[float], strategy: Sequence[float]) -> None:
        for index, value in enumerate(strategy):
            accumulator[index] += value

    def _update_regrets(self, regrets: List[float], util: Sequence[float], average_value: float) -> None:
        for index in range(len(regrets)):
            regrets[index] = max(0.0, regrets[index] + util[index] - average_value)

    def _compute_exploitability(
        self,
        strategy_p1: Sequence[float],
        strategy_p2: Sequence[float],
    ) -> float:
        best_response_p1 = max(_matrix_vector_product(self.payoff_matrix, strategy_p2))
        realised_p1 = _dot(strategy_p1, _matrix_vector_product(self.payoff_matrix, strategy_p2))
        best_response_p2 = max(
            -value for value in _transposed_matrix_vector_product(self.payoff_matrix, strategy_p1)
        )
        realised_p2 = _dot(strategy_p2, [-value for value in _transposed_matrix_vector_product(self.payoff_matrix, strategy_p1)])
        return max(0.0, best_response_p1 - realised_p1) + max(0.0, best_response_p2 - realised_p2)


__all__ = ["CFRPlusSolver", "CFRPlusSolution"]

