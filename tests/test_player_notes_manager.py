#!/usr/bin/env python3
"""Tests for Player Notes Manager"""

import pytest
from src.pokertool.player_notes_manager import PlayerNotesManager, NoteCategory, PlayerNote


class TestPlayerNotesManager:
    def test_initialization(self):
        manager = PlayerNotesManager()
        assert len(manager.notes) == 0
        assert len(manager.tags_index) == 0

    def test_add_note(self):
        manager = PlayerNotesManager()
        note = manager.add_note("Alice", "Plays tight", NoteCategory.PLAYING_STYLE)
        assert note.player_name == "Alice"
        assert note.note == "Plays tight"
        assert note.category == NoteCategory.PLAYING_STYLE

    def test_get_notes(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Note 1")
        manager.add_note("Alice", "Note 2")
        notes = manager.get_notes("Alice")
        assert len(notes) == 2

    def test_get_notes_by_category(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Aggressive", NoteCategory.TENDENCIES)
        manager.add_note("Alice", "History note", NoteCategory.HISTORY)
        tendency_notes = manager.get_notes_by_category("Alice", NoteCategory.TENDENCIES)
        assert len(tendency_notes) == 1
        assert tendency_notes[0].note == "Aggressive"

    def test_add_note_with_tags(self):
        manager = PlayerNotesManager()
        manager.add_note("Bob", "Bluffs often", NoteCategory.TENDENCIES, ["bluff", "aggressive"])
        notes = manager.get_notes("Bob")
        assert "bluff" in notes[0].tags
        assert "aggressive" in notes[0].tags

    def test_get_notes_by_tag(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Aggressive player", tags=["aggressive"])
        manager.add_note("Bob", "Also aggressive", tags=["aggressive"])
        aggressive_notes = manager.get_notes_by_tag("aggressive")
        assert len(aggressive_notes) == 2

    def test_search_notes(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Plays tight pre-flop")
        manager.add_note("Alice", "Aggressive on river")
        results = manager.search_notes("Alice", "aggressive")
        assert len(results) == 1
        assert "Aggressive" in results[0].note

    def test_get_recent_notes(self):
        manager = PlayerNotesManager()
        for i in range(10):
            manager.add_note("Alice", f"Note {i}")
        recent = manager.get_recent_notes("Alice", limit=3)
        assert len(recent) == 3
        assert "Note 9" in recent[0].note

    def test_delete_note(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Note 1")
        manager.add_note("Alice", "Note 2")
        assert manager.delete_note("Alice", 0) is True
        assert len(manager.get_notes("Alice")) == 1

    def test_delete_note_invalid_index(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Note 1")
        assert manager.delete_note("Alice", 10) is False

    def test_delete_note_invalid_player(self):
        manager = PlayerNotesManager()
        assert manager.delete_note("NonExistent", 0) is False

    def test_get_all_players(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Note")
        manager.add_note("Bob", "Note")
        players = manager.get_all_players()
        assert "Alice" in players
        assert "Bob" in players
        assert len(players) == 2

    def test_get_note_count(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Note 1")
        manager.add_note("Alice", "Note 2")
        assert manager.get_note_count("Alice") == 2

    def test_get_all_tags(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Note", tags=["tag1", "tag2"])
        manager.add_note("Bob", "Note", tags=["tag3"])
        tags = manager.get_all_tags()
        assert len(tags) == 3

    def test_merge_player_notes(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice_old", "Note 1")
        manager.add_note("Alice_old", "Note 2")
        manager.merge_player_notes("Alice_old", "Alice_new")
        assert len(manager.get_notes("Alice_new")) == 2
        assert len(manager.get_notes("Alice_old")) == 0

    def test_export_notes(self):
        manager = PlayerNotesManager()
        manager.add_note("Alice", "Plays tight", NoteCategory.PLAYING_STYLE, ["tight"])
        export = manager.export_notes("Alice")
        assert "Alice" in export
        assert "Plays tight" in export
        assert "tight" in export

    def test_export_notes_no_notes(self):
        manager = PlayerNotesManager()
        export = manager.export_notes("NonExistent")
        assert "No notes" in export


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
