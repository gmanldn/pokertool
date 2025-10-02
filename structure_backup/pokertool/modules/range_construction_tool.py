# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: range_construction_tool.py
# version: v28.1.0
# last_commit: '2025-09-30T13:00:00+01:00'
# fixes:
# - date: '2025-09-30'
#   summary: Initial implementation of Range Construction Tool (RANGE-001)
# ---
# POKERTOOL-HEADER-END

"""
Range Construction Tool Module

This module provides a visual interface for constructing and manipulating poker hand ranges.
Supports drag-and-drop, range comparison, import/export, and template management.

Public API:
    - RangeConstructionTool: Main range construction class
    - HandRange: Represents a poker hand range
    - RangeGrid: Visual grid representation of ranges
    - RangeComparator: Compare multiple ranges
    - RangeTemplate: Pre-defined range templates
    - RangeImportExport: Import/export functionality

Dependencies:
    - logger (for logging)
    - json, itertools (standard library)

Last Reviewed: 2025-09-30
"""

from __future__ import annotations

import json
import itertools
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple, Any
from enum import Enum
from pathlib import Path

try:
    from pokertool.modules.logger import logger, log_exceptions
except ImportError:
    # Fallback for standalone usage
    class _FakeLogger:
        """Fallback logger when main logger unavailable."""
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass
    
    logger = _FakeLogger()
    
    def log_exceptions(func):
        """Fallback decorator."""
        return func


class RangeFormat(Enum):
    """Enumeration of range format types."""
    STANDARD = "standard"
    PERCENTAGE = "percentage"
    GRID = "grid"
    CUSTOM = "custom"


class HandType(Enum):
    """Enumeration of hand types."""
    PAIR = "pair"
    SUITED = "suited"
    OFFSUIT = "offsuit"


# Card ranks in descending order
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']


@dataclass
class HandRange:
    """Represents a poker hand range."""
    name: str
    hands: Set[str] = field(default_factory=set)
    description: str = ""
    color: str = "#4CAF50"
    
    def __post_init__(self):
        """Validate hands after initialization."""
        self._validate_hands()
    
    def _validate_hands(self) -> None:
        """Validate that all hands are properly formatted."""
        valid_hands = set()
        for hand in self.hands:
            if self._is_valid_hand(hand):
                valid_hands.add(hand)
            else:
                logger.warning(f"Invalid hand removed from range: {hand}")
        self.hands = valid_hands
    
    def _is_valid_hand(self, hand: str) -> bool:
        """Check if a hand string is valid."""
        if len(hand) < 2 or len(hand) > 3:
            return False
        
        if hand[0] not in RANKS or hand[1] not in RANKS:
            return False
        
        if hand[0] != hand[1]:
            if len(hand) == 3 and hand[2] not in ['s', 'o']:
                return False
            elif len(hand) == 2:
                return False
        
        return True
    
    @log_exceptions
    def add_hand(self, hand: str) -> bool:
        """Add a hand to the range."""
        if self._is_valid_hand(hand):
            self.hands.add(hand)
            logger.debug(f"Added hand {hand} to range {self.name}")
            return True
        logger.warning(f"Attempted to add invalid hand: {hand}")
        return False
    
    @log_exceptions
    def remove_hand(self, hand: str) -> bool:
        """Remove a hand from the range."""
        if hand in self.hands:
            self.hands.remove(hand)
            logger.debug(f"Removed hand {hand} from range {self.name}")
            return True
        return False
    
    @log_exceptions
    def add_range_string(self, range_string: str) -> None:
        """Add multiple hands from a range string."""
        hands_to_add = self._parse_range_string(range_string)
        for hand in hands_to_add:
            self.add_hand(hand)
        logger.info(f"Added {len(hands_to_add)} hands to range {self.name}")
    
    def _parse_range_string(self, range_string: str) -> Set[str]:
        """Parse a range string into individual hands."""
        hands = set()
        parts = [p.strip() for p in range_string.split(',')]
        
        for part in parts:
            if not part:
                continue
            
            if part.endswith('+'):
                hands.update(self._expand_plus_notation(part[:-1]))
            else:
                if self._is_valid_hand(part):
                    hands.add(part)
        
        return hands
    
    def _expand_plus_notation(self, hand: str) -> Set[str]:
        """Expand plus notation into all included hands."""
        expanded = set()
        
        # Pair plus: include this pair and all higher pairs
        if len(hand) == 2 and hand[0] == hand[1]:
            rank_index = RANKS.index(hand[0])
            for i in range(rank_index + 1):
                rank = RANKS[i]
                expanded.add(f"{rank}{rank}")
        # Non-pair plus notation
        elif len(hand) in [2, 3]:
            rank1, rank2 = hand[0], hand[1]
            suffix = hand[2] if len(hand) == 3 else None
            
            rank1_index = RANKS.index(rank1)
            rank2_index = RANKS.index(rank2)
            
            if suffix in ('s', 'o'):
                # Suited or offsuit plus: include this and stronger second ranks
                for i in range(rank2_index, rank1_index, -1):
                    kicker = RANKS[i]
                    if kicker == rank1:
                        continue
                    expanded.add(f"{rank1}{kicker}{suffix}")
            else:
                # No suffix: include both suited and offsuit down to 'T'
                t_index = RANKS.index('T')
                for i in range(rank2_index, t_index + 1):
                    kicker = RANKS[i]
                    if kicker == rank1:
                        continue
                    expanded.add(f"{rank1}{kicker}s")
                    expanded.add(f"{rank1}{kicker}o")
        
        return expanded
    
    def get_hand_count(self) -> int:
        """Get the number of hands in this range."""
        return len(self.hands)
    
    def get_percentage(self) -> float:
        """Get the percentage of all possible hands this range represents."""
        return (len(self.hands) / 169.0) * 100.0
    
    def contains(self, hand: str) -> bool:
        """Check if a hand is in this range."""
        return hand in self.hands
    
    def clear(self) -> None:
        """Remove all hands from the range."""
        self.hands.clear()
        logger.info(f"Cleared all hands from range {self.name}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert range to dictionary for serialization."""
        return {
            'name': self.name,
            'hands': list(self.hands),
            'description': self.description,
            'color': self.color
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HandRange':
        """Create range from dictionary."""
        data['hands'] = set(data.get('hands', []))
        return cls(**data)
    
    def to_string(self) -> str:
        """Convert range to compact string representation."""
        return ', '.join(sorted(self.hands))


class RangeGrid:
    """Visual grid representation of a poker hand range."""
    
    def __init__(self):
        """Initialize empty range grid."""
        self.grid: Dict[Tuple[str, str], bool] = {}
        self._initialize_grid()
        logger.info("RangeGrid initialized")
    
    def _initialize_grid(self) -> None:
        """Initialize the 13x13 grid with all possible hands."""
        for rank1 in RANKS:
            for rank2 in RANKS:
                self.grid[(rank1, rank2)] = False
    
    @log_exceptions
    def set_hand(self, rank1: str, rank2: str, selected: bool) -> None:
        """Set a hand's selection state in the grid."""
        if (rank1, rank2) in self.grid:
            self.grid[(rank1, rank2)] = selected
        elif (rank2, rank1) in self.grid:
            self.grid[(rank2, rank1)] = selected
        else:
            logger.warning(f"Invalid grid position: {rank1}, {rank2}")
    
    def get_hand(self, rank1: str, rank2: str) -> bool:
        """Get a hand's selection state from the grid."""
        if (rank1, rank2) in self.grid:
            return self.grid[(rank1, rank2)]
        elif (rank2, rank1) in self.grid:
            return self.grid[(rank2, rank1)]
        return False
    
    def load_from_range(self, hand_range: HandRange) -> None:
        """Load a HandRange into the grid."""
        for key in self.grid:
            self.grid[key] = False
        
        for hand in hand_range.hands:
            if len(hand) == 2:
                self.set_hand(hand[0], hand[1], True)
            elif len(hand) == 3:
                rank1, rank2, suffix = hand[0], hand[1], hand[2]
                if suffix == 's':
                    self.set_hand(rank2, rank1, True)
                else:
                    self.set_hand(rank1, rank2, True)
        
        logger.debug(f"Loaded range {hand_range.name} into grid")
    
    def to_range(self, name: str = "Grid Range") -> HandRange:
        """Convert the grid to a HandRange."""
        hand_range = HandRange(name=name)
        
        for (rank1, rank2), selected in self.grid.items():
            if not selected:
                continue
            
            rank1_idx = RANKS.index(rank1)
            rank2_idx = RANKS.index(rank2)
            
            if rank1 == rank2:
                hand_range.add_hand(f"{rank1}{rank2}")
            elif rank1_idx < rank2_idx:
                hand_range.add_hand(f"{rank1}{rank2}o")
            else:
                hand_range.add_hand(f"{rank1}{rank2}s")
        
        return hand_range
    
    def get_selected_count(self) -> int:
        """Get the number of selected hands in the grid."""
        return sum(1 for selected in self.grid.values() if selected)


class RangeComparator:
    """Compare multiple poker hand ranges."""
    
    def __init__(self):
        """Initialize range comparator."""
        logger.info("RangeComparator initialized")
    
    @log_exceptions
    def get_overlap(self, range1: HandRange, range2: HandRange) -> HandRange:
        """Get hands that appear in both ranges."""
        overlap_hands = range1.hands & range2.hands
        overlap_range = HandRange(
            name=f"{range1.name} ∩ {range2.name}",
            hands=overlap_hands,
            description=f"Overlap between {range1.name} and {range2.name}"
        )
        logger.info(f"Found {len(overlap_hands)} overlapping hands")
        return overlap_range
    
    @log_exceptions
    def get_difference(self, range1: HandRange, range2: HandRange) -> HandRange:
        """Get hands in range1 that are not in range2."""
        diff_hands = range1.hands - range2.hands
        diff_range = HandRange(
            name=f"{range1.name} - {range2.name}",
            hands=diff_hands,
            description=f"Hands in {range1.name} but not in {range2.name}"
        )
        logger.info(f"Found {len(diff_hands)} hands in difference")
        return diff_range
    
    @log_exceptions
    def get_union(self, range1: HandRange, range2: HandRange) -> HandRange:
        """Get all hands from both ranges."""
        union_hands = range1.hands | range2.hands
        union_range = HandRange(
            name=f"{range1.name} ∪ {range2.name}",
            hands=union_hands,
            description=f"Union of {range1.name} and {range2.name}"
        )
        logger.info(f"Union contains {len(union_hands)} hands")
        return union_range
    
    @log_exceptions
    def get_overlap_percentage(self, range1: HandRange, range2: HandRange) -> float:
        """Calculate what percentage of range1 overlaps with range2."""
        if len(range1.hands) == 0:
            return 0.0
        
        overlap = len(range1.hands & range2.hands)
        percentage = (overlap / len(range1.hands)) * 100.0
        return percentage
    
    @log_exceptions
    def compare_multiple(self, ranges: List[HandRange]) -> Dict[str, Any]:
        """Compare multiple ranges and generate statistics."""
        if len(ranges) < 2:
            return {"error": "Need at least 2 ranges to compare"}
        
        common_hands = ranges[0].hands.copy()
        for r in ranges[1:]:
            common_hands &= r.hands
        
        unique_per_range = {}
        for i, r in enumerate(ranges):
            other_hands = set()
            for j, other in enumerate(ranges):
                if i != j:
                    other_hands |= other.hands
            unique_per_range[r.name] = r.hands - other_hands
        
        return {
            'range_count': len(ranges),
            'common_hands': list(common_hands),
            'common_count': len(common_hands),
            'unique_per_range': {k: list(v) for k, v in unique_per_range.items()},
            'total_unique_hands': len(set().union(*[r.hands for r in ranges]))
        }


class RangeTemplate:
    """Predefined poker hand range templates."""
    
    TEMPLATES = {
        'UTG': "99+, AJs+, KQs, AKo",
        'MP': "88+, ATs+, KQs, AQo+",
        'CO': "66+, A9s+, KJs+, QJs, AJo+, KQo",
        'BTN': "22+, A2s+, K9s+, Q9s+, J9s+, T8s+, 98s, 87s, 76s, 65s, A9o+, KJo+, QJo",
        'SB': "22+, A2s+, K2s+, Q8s+, J8s+, T7s+, 97s+, 87s, 76s, 65s, A2o+, K9o+, Q9o+, JTo",
        'TIGHT': "JJ+, AKs, AKo",
        'LOOSE': "22+, A2s+, K5s+, Q8s+, J8s+, T8s+, 97s+, 87s, 76s, A7o+, KTo+, QTo+, JTo",
    }
    
    @classmethod
    @log_exceptions
    def get_template(cls, template_name: str) -> Optional[HandRange]:
        """Get a predefined range template."""
        if template_name not in cls.TEMPLATES:
            logger.warning(f"Template {template_name} not found")
            return None
        
        range_string = cls.TEMPLATES[template_name]
        hand_range = HandRange(name=template_name, description=f"Standard {template_name} range")
        hand_range.add_range_string(range_string)
        
        logger.info(f"Created template range {template_name}")
        return hand_range
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """Get list of available template names."""
        return list(cls.TEMPLATES.keys())


class RangeImportExport:
    """Import and export poker hand ranges in various formats."""
    
    def __init__(self, export_dir: Optional[Path] = None):
        """Initialize import/export manager."""
        self.export_dir = export_dir or Path("./ranges")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"RangeImportExport initialized")
    
    @log_exceptions
    def export_to_json(self, hand_range: HandRange, filename: str) -> Path:
        """Export range to JSON format."""
        output_path = self.export_dir / f"{filename}.json"
        
        with open(output_path, 'w') as f:
            json.dump(hand_range.to_dict(), f, indent=2)
        
        logger.info(f"Exported range to {output_path}")
        return output_path
    
    @log_exceptions
    def import_from_json(self, filepath: Path) -> HandRange:
        """Import range from JSON format."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        hand_range = HandRange.from_dict(data)
        logger.info(f"Imported range from {filepath}")
        return hand_range
    
    @log_exceptions
    def export_to_text(self, hand_range: HandRange, filename: str) -> Path:
        """Export range to simple text format."""
        output_path = self.export_dir / f"{filename}.txt"
        
        with open(output_path, 'w') as f:
            f.write(f"# {hand_range.name}\n")
            f.write(f"# {hand_range.description}\n")
            f.write(f"# Hands: {hand_range.get_hand_count()} ({hand_range.get_percentage():.1f}%)\n\n")
            f.write(hand_range.to_string())
        
        logger.info(f"Exported range to {output_path}")
        return output_path
    
    @log_exceptions
    def import_from_text(self, filepath: Path, name: Optional[str] = None) -> HandRange:
        """Import range from text format."""
        with open(filepath, 'r') as f:
            content = f.read()
        
        lines = [line for line in content.split('\n') if not line.startswith('#')]
        range_string = ' '.join(lines).strip()
        
        range_name = name or filepath.stem
        hand_range = HandRange(name=range_name)
        hand_range.add_range_string(range_string)
        
        logger.info(f"Imported range from {filepath}")
        return hand_range


class RangeConstructionTool:
    """Main range construction tool."""
    
    def __init__(self):
        """Initialize the range construction tool."""
        self.ranges: Dict[str, HandRange] = {}
        self.current_range: Optional[HandRange] = None
        self.grid = RangeGrid()
        self.comparator = RangeComparator()
        self.import_export = RangeImportExport()
        logger.info("RangeConstructionTool initialized")
    
    @log_exceptions
    def create_range(self, name: str, description: str = "") -> HandRange:
        """Create a new empty range."""
        hand_range = HandRange(name=name, description=description)
        self.ranges[name] = hand_range
        self.current_range = hand_range
        logger.info(f"Created new range: {name}")
        # Ensure direct range string additions update the grid
        orig_add_range_string = hand_range.add_range_string
        def _wrapped_add_range_string(range_string: str):
            result = orig_add_range_string(range_string)
            self.grid.load_from_range(self.current_range)
            return result
        hand_range.add_range_string = _wrapped_add_range_string
        return hand_range
    
    @log_exceptions
    def load_template(self, template_name: str) -> Optional[HandRange]:
        """Load a predefined template range."""
        hand_range = RangeTemplate.get_template(template_name)
        if hand_range:
            self.ranges[hand_range.name] = hand_range
            self.current_range = hand_range
            logger.info(f"Loaded template: {template_name}")
        return hand_range
    
    @log_exceptions
    def set_current_range(self, name: str) -> bool:
        """Set the current active range."""
        if name in self.ranges:
            self.current_range = self.ranges[name]
            self.grid.load_from_range(self.current_range)
            logger.info(f"Set current range to: {name}")
            return True
        logger.warning(f"Range {name} not found")
        return False
    
    @log_exceptions
    def add_hand_to_current(self, hand: str) -> bool:
        """Add a hand to the current range."""
        if self.current_range is None:
            logger.warning("No current range selected")
            return False
        
        result = self.current_range.add_hand(hand)
        if result:
            self.grid.load_from_range(self.current_range)
        return result
    
    @log_exceptions
    def remove_hand_from_current(self, hand: str) -> bool:
        """Remove a hand from the current range."""
        if self.current_range is None:
            logger.warning("No current range selected")
            return False
        
        result = self.current_range.remove_hand(hand)
        if result:
            self.grid.load_from_range(self.current_range)
        return result
    
    @log_exceptions
    def compare_ranges(self, range_names: List[str]) -> Optional[Dict[str, Any]]:
        """Compare multiple ranges."""
        ranges = []
        for name in range_names:
            if name in self.ranges:
                ranges.append(self.ranges[name])
            else:
                logger.warning(f"Range {name} not found")
                return None
        
        return self.comparator.compare_multiple(ranges)
    
    @log_exceptions
    def export_range(self, range_name: str, filename: str, format: str = "json") -> Optional[Path]:
        """Export a range to file."""
        if range_name not in self.ranges:
            logger.warning(f"Range {range_name} not found")
            return None
        
        hand_range = self.ranges[range_name]
        
        if format == "json":
            return self.import_export.export_to_json(hand_range, filename)
        elif format == "text":
            return self.import_export.export_to_text(hand_range, filename)
        else:
            logger.warning(f"Unknown format: {format}")
            return None
    
    @log_exceptions
    def import_range(self, filepath: Path, format: str = "json") -> Optional[HandRange]:
        """Import a range from file."""
        try:
            if format == "json":
                hand_range = self.import_export.import_from_json(filepath)
            elif format == "text":
                hand_range = self.import_export.import_from_text(filepath)
            else:
                logger.warning(f"Unknown format: {format}")
                return None
            
            self.ranges[hand_range.name] = hand_range
            self.current_range = hand_range
            return hand_range
        except Exception as e:
            logger.error(f"Failed to import range: {e}")
            return None
    
    def get_range(self, name: str) -> Optional[HandRange]:
        """Get a range by name."""
        return self.ranges.get(name)
    
    def list_ranges(self) -> List[str]:
        """List all loaded ranges."""
        return list(self.ranges.keys())
    
    def delete_range(self, name: str) -> bool:
        """Delete a range."""
        if name in self.ranges:
            del self.ranges[name]
            if self.current_range and self.current_range.name == name:
                self.current_range = None
            logger.info(f"Deleted range: {name}")
            return True
        return False


# Example usage
if __name__ == "__main__":
    tool = RangeConstructionTool()
    
    # Create a custom range
    custom_range = tool.create_range("My Range", "Custom opening range")
    custom_range.add_range_string("AA, KK, QQ, AKs, AKo")
    print(f"Custom range: {custom_range.get_hand_count()} hands ({custom_range.get_percentage():.1f}%)")
    
    # Load a template
    utg_range = tool.load_template("UTG")
    if utg_range:
        print(f"UTG range: {utg_range.get_hand_count()} hands")
    
    # Compare ranges
    if utg_range and custom_range:
        overlap = tool.comparator.get_overlap(custom_range, utg_range)
        print(f"Overlap: {overlap.get_hand_count()} hands")
    
    # Export range
    export_path = tool.export_range("My Range", "my_custom_range", format="json")
    if export_path:
        print(f"Exported to: {export_path}")
