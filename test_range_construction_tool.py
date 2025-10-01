# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: test_range_construction_tool.py
# version: v28.1.0
# last_commit: '2025-09-30T13:00:00+01:00'
# fixes:
# - date: '2025-09-30'
#   summary: Unit tests for Range Construction Tool (RANGE-001)
# ---
# POKERTOOL-HEADER-END

"""
Unit tests for Range Construction Tool.

Tests all components including HandRange, RangeGrid, RangeComparator,
RangeTemplate, RangeImportExport, and RangeConstructionTool.
"""

from __future__ import annotations

import pytest
import json
import tempfile
import shutil
from pathlib import Path

from range_construction_tool import (
    RangeConstructionTool,
    HandRange,
    RangeGrid,
    RangeComparator,
    RangeTemplate,
    RangeImportExport,
    RANKS
)


class TestHandRange:
    """Test suite for HandRange class."""
    
    def test_create_range(self):
        """Test creating a hand range."""
        range_obj = HandRange(name="Test Range")
        assert range_obj.name == "Test Range"
        assert len(range_obj.hands) == 0
    
    def test_add_valid_hands(self):
        """Test adding valid hands."""
        range_obj = HandRange(name="Test")
        
        assert range_obj.add_hand("AA") is True
        assert range_obj.add_hand("AKs") is True
        assert range_obj.add_hand("AKo") is True
        assert range_obj.get_hand_count() == 3
    
    def test_add_invalid_hands(self):
        """Test that invalid hands are rejected."""
        range_obj = HandRange(name="Test")
        
        assert range_obj.add_hand("ZZ") is False
        assert range_obj.add_hand("AK") is False  # Missing s/o
        assert range_obj.add_hand("A") is False
        assert range_obj.get_hand_count() == 0
    
    def test_remove_hand(self):
        """Test removing hands."""
        range_obj = HandRange(name="Test")
        range_obj.add_hand("AA")
        range_obj.add_hand("KK")
        
        assert range_obj.remove_hand("AA") is True
        assert range_obj.get_hand_count() == 1
        assert range_obj.remove_hand("QQ") is False
    
    def test_range_string_parsing(self):
        """Test parsing range strings."""
        range_obj = HandRange(name="Test")
        range_obj.add_range_string("AA, KK, QQ, AKs")
        
        assert range_obj.get_hand_count() == 4
        assert range_obj.contains("AA")
        assert range_obj.contains("KK")
        assert range_obj.contains("AKs")
    
    def test_plus_notation_pairs(self):
        """Test plus notation for pairs."""
        range_obj = HandRange(name="Test")
        range_obj.add_range_string("88+")
        
        # Should include 88, 99, TT, JJ, QQ, KK, AA
        assert range_obj.contains("88")
        assert range_obj.contains("99")
        assert range_obj.contains("AA")
        assert not range_obj.contains("77")
        assert range_obj.get_hand_count() == 7
    
    def test_plus_notation_non_pairs(self):
        """Test plus notation for non-pairs."""
        range_obj = HandRange(name="Test")
        range_obj.add_range_string("AK+")
        
        # Should include AKs, AKo, AQs, AQo, AJs, AJo, ATs, ATo
        assert range_obj.contains("AKs")
        assert range_obj.contains("AKo")
        assert range_obj.contains("AQs")
        assert range_obj.contains("ATs")
        assert range_obj.get_hand_count() == 8
    
    def test_percentage_calculation(self):
        """Test percentage calculation."""
        range_obj = HandRange(name="Test")
        range_obj.add_range_string("AA")
        
        # 1 hand out of 169 total
        percentage = range_obj.get_percentage()
        assert 0 < percentage < 1
    
    def test_serialization(self):
        """Test range serialization."""
        range_obj = HandRange(name="Test", description="Test range")
        range_obj.add_range_string("AA, KK, AKs")
        
        # Serialize
        data = range_obj.to_dict()
        assert data['name'] == "Test"
        assert len(data['hands']) == 3
        
        # Deserialize
        restored = HandRange.from_dict(data)
        assert restored.name == range_obj.name
        assert restored.get_hand_count() == range_obj.get_hand_count()
    
    def test_clear(self):
        """Test clearing a range."""
        range_obj = HandRange(name="Test")
        range_obj.add_range_string("AA, KK, QQ")
        assert range_obj.get_hand_count() == 3
        
        range_obj.clear()
        assert range_obj.get_hand_count() == 0


class TestRangeGrid:
    """Test suite for RangeGrid class."""
    
    def test_create_grid(self):
        """Test creating a range grid."""
        grid = RangeGrid()
        assert len(grid.grid) == 169  # 13x13 grid
    
    def test_set_and_get_hand(self):
        """Test setting and getting hand states."""
        grid = RangeGrid()
        
        grid.set_hand('A', 'A', True)
        assert grid.get_hand('A', 'A') is True
        
        grid.set_hand('A', 'K', True)
        assert grid.get_hand('A', 'K') is True
    
    def test_load_from_range(self):
        """Test loading a HandRange into grid."""
        range_obj = HandRange(name="Test")
        range_obj.add_range_string("AA, KK, AKs")
        
        grid = RangeGrid()
        grid.load_from_range(range_obj)
        
        assert grid.get_hand('A', 'A') is True
        assert grid.get_hand('K', 'K') is True
        assert grid.get_selected_count() == 3
    
    def test_grid_to_range_conversion(self):
        """Test converting grid back to HandRange."""
        grid = RangeGrid()
        grid.set_hand('A', 'A', True)
        grid.set_hand('K', 'K', True)
        
        range_obj = grid.to_range("Grid Test")
        assert range_obj.name == "Grid Test"
        assert range_obj.get_hand_count() == 2
        assert range_obj.contains("AA")
        assert range_obj.contains("KK")
    
    def test_selected_count(self):
        """Test counting selected hands."""
        grid = RangeGrid()
        assert grid.get_selected_count() == 0
        
        grid.set_hand('A', 'A', True)
        grid.set_hand('K', 'K', True)
        assert grid.get_selected_count() == 2


class TestRangeComparator:
    """Test suite for RangeComparator class."""
    
    def test_overlap(self):
        """Test finding overlap between ranges."""
        range1 = HandRange(name="Range1")
        range1.add_range_string("AA, KK, QQ, AKs")
        
        range2 = HandRange(name="Range2")
        range2.add_range_string("KK, QQ, JJ, AKs")
        
        comparator = RangeComparator()
        overlap = comparator.get_overlap(range1, range2)
        
        assert overlap.get_hand_count() == 3  # KK, QQ, AKs
        assert overlap.contains("KK")
        assert overlap.contains("QQ")
        assert overlap.contains("AKs")
    
    def test_difference(self):
        """Test finding difference between ranges."""
        range1 = HandRange(name="Range1")
        range1.add_range_string("AA, KK, QQ")
        
        range2 = HandRange(name="Range2")
        range2.add_range_string("KK, QQ, JJ")
        
        comparator = RangeComparator()
        diff = comparator.get_difference(range1, range2)
        
        assert diff.get_hand_count() == 1  # AA
        assert diff.contains("AA")
        assert not diff.contains("KK")
    
    def test_union(self):
        """Test finding union of ranges."""
        range1 = HandRange(name="Range1")
        range1.add_range_string("AA, KK")
        
        range2 = HandRange(name="Range2")
        range2.add_range_string("QQ, JJ")
        
        comparator = RangeComparator()
        union = comparator.get_union(range1, range2)
        
        assert union.get_hand_count() == 4
        assert union.contains("AA")
        assert union.contains("JJ")
    
    def test_overlap_percentage(self):
        """Test calculating overlap percentage."""
        range1 = HandRange(name="Range1")
        range1.add_range_string("AA, KK, QQ, JJ")
        
        range2 = HandRange(name="Range2")
        range2.add_range_string("KK, QQ")
        
        comparator = RangeComparator()
        percentage = comparator.get_overlap_percentage(range1, range2)
        
        # 2 out of 4 hands = 50%
        assert percentage == 50.0
    
    def test_compare_multiple(self):
        """Test comparing multiple ranges."""
        range1 = HandRange(name="R1")
        range1.add_range_string("AA, KK, QQ")
        
        range2 = HandRange(name="R2")
        range2.add_range_string("KK, QQ, JJ")
        
        range3 = HandRange(name="R3")
        range3.add_range_string("QQ, JJ, TT")
        
        comparator = RangeComparator()
        result = comparator.compare_multiple([range1, range2, range3])
        
        assert result['range_count'] == 3
        assert result['common_count'] == 1  # Only QQ is common
        assert 'QQ' in result['common_hands']


class TestRangeTemplate:
    """Test suite for RangeTemplate class."""
    
    def test_get_template(self):
        """Test getting a predefined template."""
        utg_range = RangeTemplate.get_template("UTG")
        
        assert utg_range is not None
        assert utg_range.name == "UTG"
        assert utg_range.get_hand_count() > 0
    
    def test_invalid_template(self):
        """Test getting non-existent template."""
        result = RangeTemplate.get_template("NONEXISTENT")
        assert result is None
    
    def test_list_templates(self):
        """Test listing available templates."""
        templates = RangeTemplate.list_templates()
        
        assert len(templates) > 0
        assert "UTG" in templates
        assert "BTN" in templates
    
    def test_template_contents(self):
        """Test that templates contain expected hands."""
        tight_range = RangeTemplate.get_template("TIGHT")
        
        assert tight_range is not None
        assert tight_range.contains("AA")
        assert tight_range.contains("KK")
        assert tight_range.contains("AKs")


class TestRangeImportExport:
    """Test suite for RangeImportExport class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for exports."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_export_import_json(self, temp_dir):
        """Test JSON export and import."""
        ie_manager = RangeImportExport(export_dir=temp_dir)
        
        # Create a range
        range_obj = HandRange(name="Test", description="Test range")
        range_obj.add_range_string("AA, KK, QQ")
        
        # Export
        export_path = ie_manager.export_to_json(range_obj, "test_range")
        assert export_path.exists()
        
        # Import
        imported = ie_manager.import_from_json(export_path)
        assert imported.name == range_obj.name
        assert imported.get_hand_count() == range_obj.get_hand_count()
    
    def test_export_import_text(self, temp_dir):
        """Test text export and import."""
        ie_manager = RangeImportExport(export_dir=temp_dir)
        
        # Create a range
        range_obj = HandRange(name="Test")
        range_obj.add_range_string("AA, KK, AKs")
        
        # Export
        export_path = ie_manager.export_to_text(range_obj, "test_range")
        assert export_path.exists()
        
        # Verify file contents
        with open(export_path, 'r') as f:
            content = f.read()
        assert "AA" in content
        
        # Import
        imported = ie_manager.import_from_text(export_path, name="Imported")
        assert imported.get_hand_count() == range_obj.get_hand_count()


class TestRangeConstructionTool:
    """Test suite for RangeConstructionTool class."""
    
    def test_create_tool(self):
        """Test creating the tool."""
        tool = RangeConstructionTool()
        
        assert tool.grid is not None
        assert tool.comparator is not None
        assert tool.import_export is not None
    
    def test_create_range(self):
        """Test creating a new range."""
        tool = RangeConstructionTool()
        
        range_obj = tool.create_range("MyRange", "Custom range")
        assert range_obj.name == "MyRange"
        assert "MyRange" in tool.ranges
        assert tool.current_range == range_obj
    
    def test_load_template(self):
        """Test loading a template."""
        tool = RangeConstructionTool()
        
        range_obj = tool.load_template("UTG")
        assert range_obj is not None
        assert "UTG" in tool.ranges
        assert tool.current_range == range_obj
    
    def test_set_current_range(self):
        """Test setting current range."""
        tool = RangeConstructionTool()
        
        tool.create_range("Range1")
        tool.create_range("Range2")
        
        assert tool.set_current_range("Range1") is True
        assert tool.current_range.name == "Range1"
        
        assert tool.set_current_range("NonExistent") is False
    
    def test_add_hand_to_current(self):
        """Test adding hand to current range."""
        tool = RangeConstructionTool()
        tool.create_range("Test")
        
        assert tool.add_hand_to_current("AA") is True
        assert tool.current_range.contains("AA")
    
    def test_remove_hand_from_current(self):
        """Test removing hand from current range."""
        tool = RangeConstructionTool()
        tool.create_range("Test")
        tool.add_hand_to_current("AA")
        
        assert tool.remove_hand_from_current("AA") is True
        assert not tool.current_range.contains("AA")
    
    def test_compare_ranges(self):
        """Test comparing ranges."""
        tool = RangeConstructionTool()
        
        range1 = tool.create_range("R1")
        range1.add_range_string("AA, KK, QQ")
        
        range2 = tool.create_range("R2")
        range2.add_range_string("KK, QQ, JJ")
        
        result = tool.compare_ranges(["R1", "R2"])
        assert result is not None
        assert result['range_count'] == 2
    
    def test_export_range(self):
        """Test exporting a range."""
        tool = RangeConstructionTool()
        
        range_obj = tool.create_range("Export Test")
        range_obj.add_range_string("AA, KK")
        
        export_path = tool.export_range("Export Test", "export_test", format="json")
        assert export_path is not None
        assert export_path.exists()
    
    def test_import_range(self):
        """Test importing a range."""
        tool = RangeConstructionTool()
        
        # First export
        range_obj = tool.create_range("Original")
        range_obj.add_range_string("AA, KK, QQ")
        export_path = tool.export_range("Original", "import_test", format="json")
        
        # Clear and import
        tool.ranges.clear()
        imported = tool.import_range(export_path, format="json")
        
        assert imported is not None
        assert imported.get_hand_count() == 3
    
    def test_list_ranges(self):
        """Test listing ranges."""
        tool = RangeConstructionTool()
        
        tool.create_range("R1")
        tool.create_range("R2")
        
        ranges = tool.list_ranges()
        assert len(ranges) == 2
        assert "R1" in ranges
        assert "R2" in ranges
    
    def test_delete_range(self):
        """Test deleting a range."""
        tool = RangeConstructionTool()
        
        tool.create_range("ToDelete")
        assert "ToDelete" in tool.ranges
        
        assert tool.delete_range("ToDelete") is True
        assert "ToDelete" not in tool.ranges
        
        assert tool.delete_range("NonExistent") is False
    
    def test_get_range(self):
        """Test getting a range by name."""
        tool = RangeConstructionTool()
        
        created = tool.create_range("Test")
        retrieved = tool.get_range("Test")
        
        assert retrieved is not None
        assert retrieved.name == created.name


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_workflow(self):
        """Test a complete range construction workflow."""
        tool = RangeConstructionTool()
        
        # Create custom range
        custom = tool.create_range("Custom", "My opening range")
        custom.add_range_string("88+, AJs+, KQs, AQo+")
        
        # Load template
        utg = tool.load_template("UTG")
        
        # Compare
        comparison = tool.compare_ranges(["Custom", "UTG"])
        assert comparison is not None
        
        # Find overlap
        overlap = tool.comparator.get_overlap(custom, utg)
        assert overlap.get_hand_count() > 0
        
        # Export custom range
        export_path = tool.export_range("Custom", "my_range", format="json")
        assert export_path.exists()
        
        # Verify export structure
        with open(export_path, 'r') as f:
            data = json.load(f)
        assert data['name'] == "Custom"
    
    def test_grid_workflow(self):
        """Test workflow using grid."""
        tool = RangeConstructionTool()
        
        # Create range and load into grid
        range_obj = tool.create_range("Grid Test")
        range_obj.add_range_string("AA, KK, QQ")
        
        # Grid should be auto-updated
        assert tool.grid.get_hand('A', 'A') is True
        assert tool.grid.get_hand('K', 'K') is True
        
        # Convert grid back to range
        grid_range = tool.grid.to_range("From Grid")
        assert grid_range.get_hand_count() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
