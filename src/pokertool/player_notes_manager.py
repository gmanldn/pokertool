#!/usr/bin/env python3
"""Player Notes Manager - Stores and retrieves player notes"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class NoteCategory(Enum):
    """Note categories"""
    GENERAL = "general"
    PLAYING_STYLE = "playing_style"
    TENDENCIES = "tendencies"
    TELLS = "tells"
    HISTORY = "history"


@dataclass
class PlayerNote:
    """Player note entry"""
    player_name: str
    note: str
    category: NoteCategory
    timestamp: datetime
    tags: List[str]


class PlayerNotesManager:
    """Manages player notes and observations."""

    def __init__(self):
        """Initialize notes manager."""
        self.notes: Dict[str, List[PlayerNote]] = {}
        self.tags_index: Dict[str, List[PlayerNote]] = {}

    def add_note(
        self,
        player_name: str,
        note: str,
        category: NoteCategory = NoteCategory.GENERAL,
        tags: Optional[List[str]] = None
    ) -> PlayerNote:
        """Add a note about a player."""
        if tags is None:
            tags = []

        player_note = PlayerNote(
            player_name=player_name,
            note=note,
            category=category,
            timestamp=datetime.now(),
            tags=tags
        )

        if player_name not in self.notes:
            self.notes[player_name] = []

        self.notes[player_name].append(player_note)

        # Index by tags
        for tag in tags:
            if tag not in self.tags_index:
                self.tags_index[tag] = []
            self.tags_index[tag].append(player_note)

        logger.info(f"Added note for {player_name}: {note[:50]}")
        return player_note

    def get_notes(self, player_name: str) -> List[PlayerNote]:
        """Get all notes for a player."""
        return self.notes.get(player_name, [])

    def get_notes_by_category(self, player_name: str, category: NoteCategory) -> List[PlayerNote]:
        """Get notes for a player by category."""
        all_notes = self.get_notes(player_name)
        return [note for note in all_notes if note.category == category]

    def get_notes_by_tag(self, tag: str) -> List[PlayerNote]:
        """Get all notes with a specific tag."""
        return self.tags_index.get(tag, [])

    def search_notes(self, player_name: str, keyword: str) -> List[PlayerNote]:
        """Search notes for a player by keyword."""
        all_notes = self.get_notes(player_name)
        return [note for note in all_notes if keyword.lower() in note.note.lower()]

    def get_recent_notes(self, player_name: str, limit: int = 5) -> List[PlayerNote]:
        """Get most recent notes for a player."""
        all_notes = self.get_notes(player_name)
        sorted_notes = sorted(all_notes, key=lambda n: n.timestamp, reverse=True)
        return sorted_notes[:limit]

    def delete_note(self, player_name: str, note_index: int) -> bool:
        """Delete a specific note."""
        if player_name not in self.notes:
            return False

        notes = self.notes[player_name]
        if note_index < 0 or note_index >= len(notes):
            return False

        deleted_note = notes.pop(note_index)

        # Remove from tags index
        for tag in deleted_note.tags:
            if tag in self.tags_index:
                self.tags_index[tag] = [n for n in self.tags_index[tag] if n != deleted_note]

        logger.info(f"Deleted note for {player_name}")
        return True

    def get_all_players(self) -> List[str]:
        """Get list of all players with notes."""
        return list(self.notes.keys())

    def get_note_count(self, player_name: str) -> int:
        """Get total number of notes for a player."""
        return len(self.notes.get(player_name, []))

    def get_all_tags(self) -> List[str]:
        """Get all unique tags."""
        return list(self.tags_index.keys())

    def merge_player_notes(self, old_name: str, new_name: str):
        """Merge notes from one player to another."""
        if old_name not in self.notes:
            return

        old_notes = self.notes.pop(old_name)

        # Update player names in notes
        for note in old_notes:
            note.player_name = new_name

        if new_name not in self.notes:
            self.notes[new_name] = []

        self.notes[new_name].extend(old_notes)
        logger.info(f"Merged {len(old_notes)} notes from {old_name} to {new_name}")

    def export_notes(self, player_name: str) -> str:
        """Export notes as formatted text."""
        notes = self.get_notes(player_name)
        if not notes:
            return f"No notes for {player_name}"

        lines = [f"=== Notes for {player_name} ===\n"]
        for i, note in enumerate(notes, 1):
            lines.append(f"{i}. [{note.category.value}] {note.note}")
            if note.tags:
                lines.append(f"   Tags: {', '.join(note.tags)}")
            lines.append(f"   {note.timestamp.strftime('%Y-%m-%d %H:%M')}\n")

        return "\n".join(lines)


if __name__ == '__main__':
    manager = PlayerNotesManager()
    manager.add_note("Alice", "Very aggressive pre-flop", NoteCategory.TENDENCIES, ["aggressive"])
    manager.add_note("Alice", "Tends to bluff on river", NoteCategory.TENDENCIES, ["bluff"])
    print(manager.export_notes("Alice"))
