#!/usr/bin/env python3
"""Blind Structure Manager - Manages tournament blind schedules"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StructureType(Enum):
    """Tournament structure types"""
    TURBO = "turbo"
    STANDARD = "standard"
    DEEP_STACK = "deep_stack"
    HYPER = "hyper"
    CUSTOM = "custom"


@dataclass
class BlindLevel:
    """Blind level definition"""
    level: int
    small_blind: int
    big_blind: int
    ante: int
    duration_minutes: int
    is_break: bool = False


class BlindStructureManager:
    """Manages tournament blind structures."""

    def __init__(self):
        """Initialize blind structure manager."""
        self.structures: Dict[str, List[BlindLevel]] = {}
        self._load_standard_structures()

    def _load_standard_structures(self):
        """Load standard tournament structures."""
        # Turbo structure (5-min levels)
        self.structures['turbo'] = [
            BlindLevel(1, 25, 50, 0, 5),
            BlindLevel(2, 50, 100, 0, 5),
            BlindLevel(3, 75, 150, 25, 5),
            BlindLevel(4, 100, 200, 25, 5),
            BlindLevel(5, 150, 300, 50, 5),
            BlindLevel(6, 200, 400, 50, 5, is_break=True),
            BlindLevel(7, 300, 600, 75, 5),
            BlindLevel(8, 400, 800, 100, 5),
        ]

        # Standard structure (15-min levels)
        self.structures['standard'] = [
            BlindLevel(1, 25, 50, 0, 15),
            BlindLevel(2, 50, 100, 0, 15),
            BlindLevel(3, 75, 150, 25, 15),
            BlindLevel(4, 100, 200, 25, 15),
            BlindLevel(5, 150, 300, 50, 15),
            BlindLevel(6, 200, 400, 50, 15, is_break=True),
            BlindLevel(7, 300, 600, 75, 15),
            BlindLevel(8, 400, 800, 100, 15),
            BlindLevel(9, 500, 1000, 125, 15),
            BlindLevel(10, 600, 1200, 150, 15),
        ]

        # Hyper structure (3-min levels)
        self.structures['hyper'] = [
            BlindLevel(1, 25, 50, 0, 3),
            BlindLevel(2, 50, 100, 0, 3),
            BlindLevel(3, 75, 150, 25, 3),
            BlindLevel(4, 100, 200, 25, 3),
            BlindLevel(5, 150, 300, 50, 3),
            BlindLevel(6, 200, 400, 50, 3),
        ]

    def get_structure(self, name: str) -> Optional[List[BlindLevel]]:
        """Get a blind structure by name."""
        return self.structures.get(name.lower())

    def add_custom_structure(self, name: str, levels: List[BlindLevel]):
        """Add a custom blind structure."""
        self.structures[name.lower()] = levels
        logger.info(f"Added custom structure '{name}' with {len(levels)} levels")

    def get_structure_names(self) -> List[str]:
        """Get all available structure names."""
        return list(self.structures.keys())

    def calculate_total_duration(self, structure_name: str) -> int:
        """Calculate total duration in minutes (excluding breaks)."""
        structure = self.get_structure(structure_name)
        if not structure:
            return 0
        return sum(level.duration_minutes for level in structure if not level.is_break)

    def get_level_at_time(self, structure_name: str, minutes_elapsed: int) -> Optional[BlindLevel]:
        """Get the blind level at a specific time."""
        structure = self.get_structure(structure_name)
        if not structure:
            return None

        total_time = 0
        for level in structure:
            if level.is_break:
                continue
            total_time += level.duration_minutes
            if total_time > minutes_elapsed:
                return level

        return structure[-1] if structure else None

    def get_break_levels(self, structure_name: str) -> List[int]:
        """Get all break level numbers."""
        structure = self.get_structure(structure_name)
        if not structure:
            return []
        return [level.level for level in structure if level.is_break]

    def scale_structure(self, structure_name: str, multiplier: float) -> List[BlindLevel]:
        """Scale all blind amounts by a multiplier."""
        structure = self.get_structure(structure_name)
        if not structure:
            return []

        scaled = []
        for level in structure:
            scaled.append(BlindLevel(
                level=level.level,
                small_blind=int(level.small_blind * multiplier),
                big_blind=int(level.big_blind * multiplier),
                ante=int(level.ante * multiplier),
                duration_minutes=level.duration_minutes,
                is_break=level.is_break
            ))
        return scaled

    def get_average_big_blind(self, structure_name: str) -> float:
        """Get average big blind across all levels."""
        structure = self.get_structure(structure_name)
        if not structure:
            return 0.0
        non_break_levels = [l for l in structure if not l.is_break]
        if not non_break_levels:
            return 0.0
        return sum(l.big_blind for l in non_break_levels) / len(non_break_levels)

    def validate_structure(self, levels: List[BlindLevel]) -> bool:
        """Validate a blind structure."""
        if not levels:
            return False

        # Check that blinds are increasing
        for i in range(1, len(levels)):
            if levels[i].big_blind <= levels[i-1].big_blind and not levels[i].is_break:
                return False

        # Check that all levels have positive duration
        if any(level.duration_minutes <= 0 for level in levels):
            return False

        return True


if __name__ == '__main__':
    manager = BlindStructureManager()
    print(f"Available structures: {manager.get_structure_names()}")
    turbo = manager.get_structure('turbo')
    print(f"Turbo structure has {len(turbo)} levels")
    print(f"Total duration: {manager.calculate_total_duration('turbo')} minutes")
