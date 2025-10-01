# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: test_note_taking_system.py
# version: v28.2.0
# last_commit: '2025-09-30T15:00:00+01:00'
# fixes:
# - date: '2025-09-30'
#   summary: Unit tests for Note Taking System (NOTES-001)
# ---
# POKERTOOL-HEADER-END

"""
Unit tests for Note Taking System.

Tests all components including PlayerNote, NoteDatabase, NoteSearch,
NoteTemplate, AutoNoteGenerator, and NoteTakingSystem.
"""

from __future__ import annotations

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from pokertool.modules.note_taking_system import (
    NoteTakingSystem,
    PlayerNote,
    NoteDatabase,
    NoteSearch,
    NoteTemplate,
    AutoNoteGenerator,
    NoteColor,
    NoteCategory
)


class TestPlayerNote:
    """Test suite for PlayerNote class."""
    
    def test_create_note(self):
        """Test creating a player note."""
        note = PlayerNote(
            player_name="TestPlayer",
            text="Aggressive player",
            color=NoteColor.ORANGE
        )
        
        assert note.player_name == "TestPlayer"
        assert note.text == "Aggressive player"
        assert note.color == NoteColor.ORANGE
        assert note.created_at is not None
    
    def test_note_with_tags(self):
        """Test note with tags."""
        note = PlayerNote(
            player_name="Player1",
            text="LAG player",
            tags={'loose', 'aggressive', 'good'}
        )
        
        assert len(note.tags) == 3
        assert 'loose' in note.tags
        assert 'aggressive' in note.tags
    
    def test_note_serialization(self):
        """Test note serialization and deserialization."""
        note = PlayerNote(
            player_name="Player1",
            text="Test note",
            color=NoteColor.GREEN,
            category=NoteCategory.PREFLOP,
            tags={'tag1', 'tag2'},
            is_important=True
        )
        
        # Serialize
        data = note.to_dict()
        assert data['player_name'] == "Player1"
        assert data['color'] == "green"
        assert set(data['tags']) == {'tag1', 'tag2'}
        
        # Deserialize
        restored = PlayerNote.from_dict(data)
        assert restored.player_name == note.player_name
        assert restored.color == note.color
        assert restored.tags == note.tags


class TestNoteDatabase:
    """Test suite for NoteDatabase class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_notes.db"
        db = NoteDatabase(db_path)
        yield db
        db.close()
        shutil.rmtree(temp_dir)
    
    def test_create_database(self, temp_db):
        """Test database creation."""
        assert temp_db.connection is not None
        assert temp_db.db_path.exists()
    
    def test_add_note(self, temp_db):
        """Test adding a note."""
        note = PlayerNote(
            player_name="Player1",
            text="Test note"
        )
        
        note_id = temp_db.add_note(note)
        assert note_id > 0
    
    def test_get_note(self, temp_db):
        """Test retrieving a note."""
        note = PlayerNote(
            player_name="Player1",
            text="Test note"
        )
        
        note_id = temp_db.add_note(note)
        retrieved = temp_db.get_note(note_id)
        
        assert retrieved is not None
        assert retrieved.player_name == "Player1"
        assert retrieved.text == "Test note"
    
    def test_update_note(self, temp_db):
        """Test updating a note."""
        note = PlayerNote(
            player_name="Player1",
            text="Original text"
        )
        
        note_id = temp_db.add_note(note)
        note.note_id = note_id
        note.text = "Updated text"
        
        success = temp_db.update_note(note)
        assert success is True
        
        retrieved = temp_db.get_note(note_id)
        assert retrieved.text == "Updated text"
    
    def test_delete_note(self, temp_db):
        """Test deleting a note."""
        note = PlayerNote(
            player_name="Player1",
            text="To be deleted"
        )
        
        note_id = temp_db.add_note(note)
        success = temp_db.delete_note(note_id)
        
        assert success is True
        assert temp_db.get_note(note_id) is None
    
    def test_get_notes_by_player(self, temp_db):
        """Test getting notes for specific player."""
        note1 = PlayerNote(player_name="Player1", text="Note 1")
        note2 = PlayerNote(player_name="Player1", text="Note 2")
        note3 = PlayerNote(player_name="Player2", text="Note 3")
        
        temp_db.add_note(note1)
        temp_db.add_note(note2)
        temp_db.add_note(note3)
        
        player1_notes = temp_db.get_notes_by_player("Player1")
        assert len(player1_notes) == 2
        
        player2_notes = temp_db.get_notes_by_player("Player2")
        assert len(player2_notes) == 1
    
    def test_get_all_notes(self, temp_db):
        """Test getting all notes."""
        for i in range(5):
            note = PlayerNote(
                player_name=f"Player{i}",
                text=f"Note {i}"
            )
            temp_db.add_note(note)
        
        all_notes = temp_db.get_all_notes()
        assert len(all_notes) == 5
    
    def test_get_all_notes_with_limit(self, temp_db):
        """Test getting limited number of notes."""
        for i in range(10):
            note = PlayerNote(player_name=f"Player{i}", text=f"Note {i}")
            temp_db.add_note(note)
        
        limited_notes = temp_db.get_all_notes(limit=5)
        assert len(limited_notes) == 5


class TestNoteSearch:
    """Test suite for NoteSearch class."""
    
    @pytest.fixture
    def search_db(self):
        """Create database with test data."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "search_test.db"
        db = NoteDatabase(db_path)
        
        # Add test notes
        notes = [
            PlayerNote(player_name="Fish1", text="Calls too much", 
                      color=NoteColor.RED, category=NoteCategory.GENERAL,
                      tags={'fish', 'loose'}),
            PlayerNote(player_name="Pro1", text="Very tight player",
                      color=NoteColor.GREEN, category=NoteCategory.PREFLOP,
                      tags={'tight', 'good'}, is_important=True),
            PlayerNote(player_name="Maniac1", text="Raises constantly",
                      color=NoteColor.ORANGE, category=NoteCategory.BETTING,
                      tags={'maniac', 'aggressive'}),
        ]
        
        for note in notes:
            db.add_note(note)
        
        search = NoteSearch(db)
        
        yield search, db
        
        db.close()
        shutil.rmtree(temp_dir)
    
    def test_search_by_text(self, search_db):
        """Test text search."""
        search, db = search_db
        
        results = search.search_by_text("tight")
        assert len(results) == 1
        assert results[0].player_name == "Pro1"
    
    def test_search_by_color(self, search_db):
        """Test search by color."""
        search, db = search_db
        
        red_notes = search.search_by_color(NoteColor.RED)
        assert len(red_notes) == 1
        assert red_notes[0].player_name == "Fish1"
    
    def test_search_by_category(self, search_db):
        """Test search by category."""
        search, db = search_db
        
        preflop_notes = search.search_by_category(NoteCategory.PREFLOP)
        assert len(preflop_notes) == 1
        assert preflop_notes[0].player_name == "Pro1"
    
    def test_search_by_tags(self, search_db):
        """Test search by tags."""
        search, db = search_db
        
        # Search for any matching tag
        results = search.search_by_tags({'loose', 'tight'}, match_all=False)
        assert len(results) >= 2
        
        # Search for all tags
        results = search.search_by_tags({'fish', 'loose'}, match_all=True)
        assert len(results) == 1
        assert results[0].player_name == "Fish1"
    
    def test_search_important(self, search_db):
        """Test searching for important notes."""
        search, db = search_db
        
        important = search.search_important()
        assert len(important) == 1
        assert important[0].player_name == "Pro1"
    
    def test_advanced_search(self, search_db):
        """Test advanced search with multiple criteria."""
        search, db = search_db
        
        results = search.advanced_search(
            color=NoteColor.RED,
            tags={'fish'}
        )
        
        assert len(results) == 1
        assert results[0].player_name == "Fish1"


class TestNoteTemplate:
    """Test suite for NoteTemplate class."""
    
    def test_get_template(self):
        """Test getting a template."""
        note = NoteTemplate.get_template("fish", "TestPlayer")
        
        assert note is not None
        assert note.player_name == "TestPlayer"
        assert note.color == NoteColor.RED
        assert 'fish' in note.tags
    
    def test_invalid_template(self):
        """Test getting non-existent template."""
        note = NoteTemplate.get_template("nonexistent", "Player1")
        assert note is None
    
    def test_list_templates(self):
        """Test listing available templates."""
        templates = NoteTemplate.list_templates()
        
        assert len(templates) > 0
        assert 'fish' in templates
        assert 'lag' in templates
        assert 'tag' in templates
    
    def test_all_templates(self):
        """Test that all templates can be created."""
        templates = NoteTemplate.list_templates()
        
        for template_name in templates:
            note = NoteTemplate.get_template(template_name, "TestPlayer")
            assert note is not None
            assert note.player_name == "TestPlayer"


class TestAutoNoteGenerator:
    """Test suite for AutoNoteGenerator class."""
    
    def test_generate_from_stats_loose(self):
        """Test generating notes for loose player."""
        generator = AutoNoteGenerator()
        
        stats = {'vpip': 45.0, 'pfr': 30.0}
        notes = generator.generate_from_stats("LoosePlayer", stats)
        
        assert len(notes) > 0
        # Should have note about high VPIP
        assert any('loose' in note.tags for note in notes)
    
    def test_generate_from_stats_tight(self):
        """Test generating notes for tight player."""
        generator = AutoNoteGenerator()
        
        stats = {'vpip': 12.0, 'pfr': 8.0}
        notes = generator.generate_from_stats("TightPlayer", stats)
        
        assert len(notes) > 0
        # Should have note about low VPIP
        assert any('tight' in note.tags for note in notes)
    
    def test_generate_from_stats_aggressive(self):
        """Test generating notes for aggressive player."""
        generator = AutoNoteGenerator()
        
        stats = {'vpip': 25.0, 'pfr': 28.0, 'af': 4.5}
        notes = generator.generate_from_stats("AggPlayer", stats)
        
        assert len(notes) > 0
        # Should have notes about aggression
        assert any('aggressive' in note.tags for note in notes)
    
    def test_generate_from_stats_passive(self):
        """Test generating notes for passive player."""
        generator = AutoNoteGenerator()
        
        stats = {'vpip': 25.0, 'pfr': 5.0, 'af': 0.5}
        notes = generator.generate_from_stats("PassivePlayer", stats)
        
        # May or may not generate notes depending on thresholds
        assert isinstance(notes, list)


class TestNoteTakingSystem:
    """Test suite for NoteTakingSystem class."""
    
    @pytest.fixture
    def note_system(self):
        """Create note taking system with temporary database."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "system_test.db"
        system = NoteTakingSystem(db_path)
        
        yield system
        
        system.close()
        shutil.rmtree(temp_dir)
    
    def test_create_note(self, note_system):
        """Test creating a note."""
        note = note_system.create_note(
            player_name="Player1",
            text="Test note",
            color=NoteColor.GREEN
        )
        
        assert note.note_id is not None
        assert note.player_name == "Player1"
    
    def test_create_from_template(self, note_system):
        """Test creating note from template."""
        note = note_system.create_from_template("fish", "FishPlayer")
        
        assert note is not None
        assert note.note_id is not None
        assert note.player_name == "FishPlayer"
        assert note.color == NoteColor.RED
    
    def test_update_note(self, note_system):
        """Test updating a note."""
        note = note_system.create_note(
            player_name="Player1",
            text="Original"
        )
        
        note.text = "Updated"
        success = note_system.update_note(note)
        
        assert success is True
        
        retrieved_notes = note_system.get_player_notes("Player1")
        assert retrieved_notes[0].text == "Updated"
    
    def test_delete_note(self, note_system):
        """Test deleting a note."""
        note = note_system.create_note(
            player_name="Player1",
            text="To delete"
        )
        
        success = note_system.delete_note(note.note_id)
        assert success is True
        
        notes = note_system.get_player_notes("Player1")
        assert len(notes) == 0
    
    def test_get_player_notes(self, note_system):
        """Test getting notes for a player."""
        note_system.create_note(player_name="Player1", text="Note 1")
        note_system.create_note(player_name="Player1", text="Note 2")
        note_system.create_note(player_name="Player2", text="Note 3")
        
        player1_notes = note_system.get_player_notes("Player1")
        assert len(player1_notes) == 2
    
    def test_get_player_summary(self, note_system):
        """Test getting player summary."""
        note_system.create_note(
            player_name="Player1",
            text="Note 1",
            color=NoteColor.RED,
            category=NoteCategory.PREFLOP,
            tags={'tag1', 'tag2'}
        )
        note_system.create_note(
            player_name="Player1",
            text="Note 2",
            color=NoteColor.RED,
            category=NoteCategory.POSTFLOP,
            tags={'tag2', 'tag3'},
            is_important=True
        )
        
        summary = note_system.get_player_summary("Player1")
        
        assert summary['player_name'] == "Player1"
        assert summary['note_count'] == 2
        assert summary['primary_color'] == 'red'
        assert summary['has_important'] is True
        assert 'tag1' in summary['all_tags']
    
    def test_get_player_summary_no_notes(self, note_system):
        """Test summary for player with no notes."""
        summary = note_system.get_player_summary("UnknownPlayer")
        
        assert summary['note_count'] == 0
        assert summary['primary_color'] is None
    
    def test_generate_auto_notes(self, note_system):
        """Test generating automatic notes."""
        stats = {'vpip': 45.0, 'pfr': 30.0, 'af': 4.0}
        notes = note_system.generate_auto_notes("AutoPlayer", stats, save=True)
        
        assert len(notes) > 0
        
        # Verify notes were saved
        saved_notes = note_system.get_player_notes("AutoPlayer")
        assert len(saved_notes) == len(notes)
    
    def test_export_notes(self, note_system):
        """Test exporting notes."""
        temp_dir = Path(tempfile.mkdtemp())
        export_path = temp_dir / "export.json"
        
        # Create some notes
        note_system.create_note(player_name="Player1", text="Note 1")
        note_system.create_note(player_name="Player2", text="Note 2")
        
        # Export
        note_system.export_notes(export_path)
        
        # Verify file exists and has content
        assert export_path.exists()
        
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        assert data['note_count'] == 2
        assert len(data['notes']) == 2
        
        shutil.rmtree(temp_dir)
    
    def test_import_notes(self, note_system):
        """Test importing notes."""
        temp_dir = Path(tempfile.mkdtemp())
        export_path = temp_dir / "import_test.json"
        
        # Create and export notes
        note_system.create_note(player_name="Player1", text="Note 1")
        note_system.export_notes(export_path)
        
        # Create new system and import
        import_db_path = temp_dir / "import.db"
        import_system = NoteTakingSystem(import_db_path)
        
        count = import_system.import_notes(export_path)
        assert count == 1
        
        notes = import_system.get_player_notes("Player1")
        assert len(notes) == 1
        
        import_system.close()
        shutil.rmtree(temp_dir)
    
    def test_export_player_specific(self, note_system):
        """Test exporting notes for specific player."""
        temp_dir = Path(tempfile.mkdtemp())
        export_path = temp_dir / "player_export.json"
        
        note_system.create_note(player_name="Player1", text="Note 1")
        note_system.create_note(player_name="Player2", text="Note 2")
        
        # Export only Player1 notes
        note_system.export_notes(export_path, player_name="Player1")
        
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        assert data['note_count'] == 1
        assert data['notes'][0]['player_name'] == "Player1"
        
        shutil.rmtree(temp_dir)


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_workflow(self):
        """Test a complete note-taking workflow."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "workflow.db"
        system = NoteTakingSystem(db_path)
        
        # Create manual note
        manual_note = system.create_note(
            player_name="Villain1",
            text="Folds to 3-bets",
            color=NoteColor.YELLOW,
            tags={'3bet', 'folds'}
        )
        assert manual_note.note_id is not None
        
        # Create template note
        template_note = system.create_from_template("fish", "Fish1")
        assert template_note is not None
        
        # Generate auto-notes
        stats = {'vpip': 42.0, 'pfr': 28.0}
        auto_notes = system.generate_auto_notes("Loose1", stats, save=True)
        assert len(auto_notes) > 0
        
        # Search
        red_notes = system.search.search_by_color(NoteColor.RED)
        assert len(red_notes) >= 1
        
        # Get summary
        summary = system.get_player_summary("Fish1")
        assert summary['note_count'] > 0
        
        # Export
        export_path = temp_dir / "export.json"
        system.export_notes(export_path)
        assert export_path.exists()
        
        system.close()
        shutil.rmtree(temp_dir)
    
    def test_tag_based_workflow(self):
        """Test workflow using tags."""
        temp_dir = Path(tempfile.mkdtemp())
        system = NoteTakingSystem(temp_dir / "tags.db")
        
        # Create notes with various tags
        system.create_note(
            player_name="Player1",
            text="LAG player",
            tags={'loose', 'aggressive', 'good'}
        )
        system.create_note(
            player_name="Player2",
            text="TAG player",
            tags={'tight', 'aggressive', 'good'}
        )
        system.create_note(
            player_name="Player3",
            text="Fish",
            tags={'loose', 'passive', 'bad'}
        )
        
        # Search for aggressive players
        aggressive = system.search.search_by_tags({'aggressive'})
        assert len(aggressive) == 2
        
        # Search for good aggressive players
        good_agg = system.search.search_by_tags(
            {'aggressive', 'good'},
            match_all=True
        )
        assert len(good_agg) == 2
        
        system.close()
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
