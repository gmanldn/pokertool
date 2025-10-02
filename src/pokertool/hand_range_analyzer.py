"""Advanced hand range analysis utilities."""

from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .gto_solver import EquityCalculator

RANKS = "AKQJT98765432"
SUITS = "shdc"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class RangeEntry:
    """Single entry in a parsed range."""

    label: str
    frequency: float
    combos: int
    category: str

    @property
    def weight(self) -> float:
        return self.frequency * self.combos


@dataclass
class RangeProfile:
    """Normalized representation of a poker range."""

    entries: List[RangeEntry]
    total_combos: int
    weighted_combos: float
    suited_combos: int
    offsuit_combos: int
    pair_combos: int
    specific_combos: int

    def as_dict(self) -> Dict[str, object]:
        return {
            "entries": [entry.__dict__ for entry in self.entries],
            "total_combos": self.total_combos,
            "weighted_combos": self.weighted_combos,
            "suited_combos": self.suited_combos,
            "offsuit_combos": self.offsuit_combos,
            "pair_combos": self.pair_combos,
            "specific_combos": self.specific_combos,
        }


@dataclass
class RangeEquityResult:
    """Return payload for equity computations."""

    equity_one: float
    equity_two: float
    iterations: int
    matchups_considered: int


@dataclass
class RangeHeatMap:
    """Matrix representation of range coverage."""

    ranks: Sequence[str]
    matrix: List[List[float]]


class RangeParsingError(ValueError):
    """Raised when range text cannot be parsed."""


class HandRangeAnalyzer:
    """Perform range parsing, equity evaluation, and visualisation support."""

    def __init__(self, equity_calculator: Optional[EquityCalculator] = None):
        self._equity_calculator = equity_calculator or EquityCalculator()

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    def parse_range(self, range_text: str) -> RangeProfile:
        if not range_text:
            raise RangeParsingError("Empty range text supplied")
        tokens = [token.strip() for token in range_text.replace(";", ",").split(",")]
        entries: List[RangeEntry] = []
        suited = offsuit = pair = specific = 0
        total_combos = 0
        weighted_combos = 0.0
        for token in tokens:
            if not token:
                continue
            label, frequency = self._parse_token(token)
            combos = self._combo_count(label)
            category = self._categorize(label)
            entries.append(RangeEntry(label=label, frequency=frequency, combos=combos, category=category))
            total_combos += combos
            weighted_combos += combos * frequency
            if category == "suited":
                suited += combos
            elif category == "offsuit":
                offsuit += combos
            elif category == "pair":
                pair += combos
            else:
                specific += combos
        if not entries:
            raise RangeParsingError("No valid range tokens parsed")
        return RangeProfile(
            entries=entries,
            total_combos=total_combos,
            weighted_combos=round(weighted_combos, 2),
            suited_combos=suited,
            offsuit_combos=offsuit,
            pair_combos=pair,
            specific_combos=specific,
        )

    # ------------------------------------------------------------------
    # Quantitative metrics
    # ------------------------------------------------------------------
    def build_heatmap(self, profile: RangeProfile) -> RangeHeatMap:
        matrix = [[0.0 for _ in RANKS] for _ in RANKS]
        for entry in profile.entries:
            r1, r2 = self._hand_ranks(entry.label)
            i = RANKS.index(r1)
            j = RANKS.index(r2)
            value = entry.frequency
            if entry.category == "pair":
                matrix[i][j] += value
            elif entry.category == "suited":
                matrix[min(i, j)][max(i, j)] += value
            elif entry.category == "offsuit":
                matrix[max(i, j)][min(i, j)] += value
            else:
                matrix[i][j] += value
        return RangeHeatMap(ranks=list(RANKS), matrix=matrix)

    def combination_weights(self, profile: RangeProfile) -> Dict[str, float]:
        return {entry.label: round(entry.weight, 2) for entry in profile.entries}

    # ------------------------------------------------------------------
    # Equity and reduction
    # ------------------------------------------------------------------
    def calculate_equity(
        self,
        range_one: RangeProfile,
        range_two: RangeProfile,
        board: Optional[Sequence[str]] = None,
        iterations: int = 400,
    ) -> RangeEquityResult:
        combos_one = self._expand_weighted_combos(range_one)
        combos_two = self._expand_weighted_combos(range_two)
        if not combos_one or not combos_two:
            return RangeEquityResult(0.0, 0.0, iterations, 0)
        equity_one = equity_two = 0.0
        total_weight = 0.0
        matchups = 0
        board_list = list(board) if board else []
        for hand_one, weight_one in combos_one:
            cards_one = {hand_one[:2], hand_one[2:]}
            for hand_two, weight_two in combos_two:
                cards_two = {hand_two[:2], hand_two[2:]}
                if cards_one & cards_two:
                    continue
                pair_weight = weight_one * weight_two
                if pair_weight == 0:
                    continue
                equities = self._equity_calculator.calculate_equity(
                    [hand_one, hand_two], board_list, iterations
                )
                equity_one += equities[0] * pair_weight
                equity_two += equities[1] * pair_weight
                total_weight += pair_weight
                matchups += 1
        if total_weight == 0:
            return RangeEquityResult(0.0, 0.0, iterations, matchups)
        return RangeEquityResult(
            equity_one=round(equity_one / total_weight, 4),
            equity_two=round(equity_two / total_weight, 4),
            iterations=iterations,
            matchups_considered=matchups,
        )

    def reduce_by_frequency(self, profile: RangeProfile, min_frequency: float) -> RangeProfile:
        filtered = [entry for entry in profile.entries if entry.frequency >= min_frequency]
        if not filtered:
            raise RangeParsingError("No range entries meet the minimum frequency threshold")
        return self.parse_range(", ".join(f"{entry.label}:{entry.frequency}" for entry in filtered))

    def reduce_with_board(self, profile: RangeProfile, board: Sequence[str]) -> RangeProfile:
        board_set = set(board)
        adjusted_entries: List[RangeEntry] = []
        for entry in profile.entries:
            combos = self._expand_entry(entry.label)
            valid = [combo for combo in combos if not self._combo_conflicts(combo, board_set)]
            if not valid:
                continue
            retention_ratio = len(valid) / len(combos)
            adjusted_entries.append(
                RangeEntry(
                    label=entry.label,
                    frequency=round(entry.frequency * retention_ratio, 3),
                    combos=len(valid),
                    category=entry.category,
                )
            )
        if not adjusted_entries:
            raise RangeParsingError("Board cards remove every combo from the range")
        return RangeProfile(
            entries=adjusted_entries,
            total_combos=sum(e.combos for e in adjusted_entries),
            weighted_combos=round(sum(e.weight for e in adjusted_entries), 2),
            suited_combos=sum(e.combos for e in adjusted_entries if e.category == "suited"),
            offsuit_combos=sum(e.combos for e in adjusted_entries if e.category == "offsuit"),
            pair_combos=sum(e.combos for e in adjusted_entries if e.category == "pair"),
            specific_combos=sum(e.combos for e in adjusted_entries if e.category == "specific"),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _parse_token(self, token: str) -> Tuple[str, float]:
        if ":" in token:
            label, value = token.split(":", 1)
        elif "@" in token:
            label, value = token.split("@", 1)
        else:
            label, value = token, "1"
        label = label.strip().upper()
        try:
            frequency = float(value.strip())
        except ValueError as exc:
            raise RangeParsingError(f"Invalid frequency value in token '{token}'") from exc
        if frequency <= 0:
            raise RangeParsingError(f"Frequency must be positive in token '{token}'")
        self._validate_label(label)
        return label, frequency

    def _categorize(self, label: str) -> str:
        if len(label) == 2 and label[0] == label[1]:
            return "pair"
        if label.endswith("S"):
            return "suited"
        if label.endswith("O"):
            return "offsuit"
        return "specific"

    def _combo_count(self, label: str) -> int:
        if len(label) == 4 and label[0] in RANKS and label[2] in RANKS and label[1] in SUITS and label[3] in SUITS:
            return 1
        if len(label) == 2:
            if label[0] == label[1]:
                return 6
            return 16
        if label.endswith("S"):
            return 4
        if label.endswith("O"):
            return 12
        if len(label) == 3:
            return 16
        raise RangeParsingError(f"Cannot determine combos for '{label}'")

    def _hand_ranks(self, label: str) -> Tuple[str, str]:
        if len(label) == 4 and label[0] in RANKS and label[2] in RANKS:
            return label[0], label[2]
        if len(label) >= 2:
            return label[0], label[1]
        raise RangeParsingError(f"Invalid label for rank extraction: '{label}'")

    def _validate_label(self, label: str) -> None:
        valid_ranks = set(RANKS)
        if len(label) >= 2 and label[0] in valid_ranks and label[1] in valid_ranks:
            return
        raise RangeParsingError(f"Invalid hand label '{label}'")

    def _expand_weighted_combos(self, profile: RangeProfile, max_combos: int = 40) -> List[Tuple[str, float]]:
        weighted: List[Tuple[str, float]] = []
        for entry in profile.entries:
            combos = self._expand_entry(entry.label)
            if not combos:
                continue
            weight_per_combo = entry.frequency / len(combos)
            for combo in combos:
                weighted.append((combo, weight_per_combo))
        if not weighted:
            return []
        if len(weighted) <= max_combos:
            return weighted
        weighted.sort(key=lambda item: item[1], reverse=True)
        return weighted[:max_combos]

    def _expand_entry(self, label: str) -> List[str]:
        label = label.upper()
        if len(label) == 4 and label[0] in RANKS and label[2] in RANKS:
            # Specific combo (e.g., AsKh)
            return [label]
        if len(label) == 2:
            if label[0] == label[1]:
                rank = label[0]
                combos = []
                for suit_one, suit_two in itertools.combinations(SUITS, 2):
                    combos.append(f"{rank}{suit_one}{rank}{suit_two}")
                return combos
            r1, r2 = label[0], label[1]
            combos = []
            for suit_one in SUITS:
                for suit_two in SUITS:
                    combos.append(f"{r1}{suit_one}{r2}{suit_two}")
            return combos
        if label.endswith("S"):
            r1, r2 = label[0], label[1]
            return [f"{r1}{suit}{r2}{suit}" for suit in SUITS]
        if label.endswith("O"):
            r1, r2 = label[0], label[1]
            combos = []
            for suit_one in SUITS:
                for suit_two in SUITS:
                    if suit_one == suit_two:
                        continue
                    combos.append(f"{r1}{suit_one}{r2}{suit_two}")
            return combos
        if len(label) == 3:
            r1, r2 = label[0], label[1]
            combos = []
            for suit_one in SUITS:
                for suit_two in SUITS:
                    if suit_one == suit_two and label.endswith("O"):
                        continue
                    combos.append(f"{r1}{suit_one}{r2}{suit_two}")
            return combos
        raise RangeParsingError(f"Unable to expand combos for '{label}'")

    def _combo_conflicts(self, combo: str, board: Sequence[str]) -> bool:
        cards = {combo[:2], combo[2:]}
        return any(card in board for card in cards)


__all__ = [
    "HandRangeAnalyzer",
    "RangeEntry",
    "RangeProfile",
    "RangeEquityResult",
    "RangeHeatMap",
    "RangeParsingError",
]
