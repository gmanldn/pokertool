# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: note_taking_system.py
# version: v28.2.0
# last_commit: '2025-09-30T15:00:00+01:00'
# fixes:
# - date: '2025-09-30'
#   summary: Initial implementation of Note Taking System (NOTES-001)
# ---
# POKERTOOL-HEADER-END

"""
Note Taking System Module

This module provides comprehensive player note management for poker analysis.
Supports color coding, search functionality, auto-note generation, and templates.

Public API:
    - NoteTakingSystem: Main note management class
    - PlayerNote: Represents a single note
    - NoteDatabase: Database operations for notes
    - NoteSearch: Search and filter functionality
    - NoteTemplate: Pre-defined note templates
    - AutoNoteGenerator: Automatic note generation from hand history

Dependencies:
    - logger (for logging)
    - sqlite3, json, datetime (standard library)

Last Reviewed: 2025-09-30
"""

from __future__ import annotations

import sqlite3
import json
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Tuple
from enum import Enum
from pathlib import Path
from collections import Counter

try:
    from logger import logger, log_exceptions
except ImportError:
    class _FakeLogger:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass
    
    logger = _FakeLogger()
    
    def log_exceptions(func):
        return func


class NoteColor(Enum):
    """Enumeration of note color categories."""
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    GRAY = "gray"


class NoteCategory(Enum):
    """Enumeration of note categories."""
    GENERAL = "general"
    PREFLOP = "preflop"
    POSTFLOP = "postflop"
    BETTING = "betting"
    POSITION = "position"
    TELLS = "tells"
    TILT = "tilt"
    SESSION = "session"


@dataclass
class PlayerNote:
    """Represents a single player note."""
    note_id: Optional[int] = None
    player_name: str = ""
    player_id: Optional[str] = None
    text: str = ""
    color: NoteColor = NoteColor.YELLOW
    category: NoteCategory = NoteCategory.GENERAL
    tags: Set[str] = field(default_factory=set)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    is_important: bool = False
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert note to dictionary."""
        return {
            'note_id': self.note_id,
            'player_name': self.player_name,
            'player_id': self.player_id,
            'text': self.text,
            'color': self.color.value,
            'category': self.category.value,
            'tags': list(self.tags),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_important': self.is_important,
            'session_id': self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerNote':
        """Create note from dictionary."""
        data['color'] = NoteColor(data.get('color', 'yellow'))
        data['category'] = NoteCategory(data.get('category', 'general'))
        data['tags'] = set(data.get('tags', []))
        if data.get('created_at'):
            data['created_at'] = datetime.datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class NoteDatabase:
    """Database operations for player notes."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize note database."""
        self.db_path = db_path or Path("./notes.db")
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_database()
        logger.info(f"NoteDatabase initialized at {self.db_path}")
    
    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        self.connection = sqlite3.connect(str(self.db_path))
        cursor = self.connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                player_id TEXT,
                text TEXT NOT NULL,
                color TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_important INTEGER NOT NULL,
                session_id TEXT
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_name ON notes(player_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_color ON notes(color)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON notes(category)")
        
        self.connection.commit()
        logger.debug("Database tables initialized")
    
    @log_exceptions
    def add_note(self, note: PlayerNote) -> int:
        """Add a note to the database."""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO notes (
                player_name, player_id, text, color, category, tags,
                created_at, updated_at, is_important, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            note.player_name, note.player_id, note.text,
            note.color.value, note.category.value, json.dumps(list(note.tags)),
            note.created_at.isoformat(), note.updated_at.isoformat(),
            1 if note.is_important else 0, note.session_id
        ))
        
        self.connection.commit()
        note_id = cursor.lastrowid
        logger.info(f"Added note {note_id} for player {note.player_name}")
        return note_id
    
    @log_exceptions
    def update_note(self, note: PlayerNote) -> bool:
        """Update an existing note."""
        if note.note_id is None:
            return False
        
        note.updated_at = datetime.datetime.now()
        cursor = self.connection.cursor()
        
        cursor.execute("""
            UPDATE notes SET
                player_name=?, player_id=?, text=?, color=?, category=?,
                tags=?, updated_at=?, is_important=?, session_id=?
            WHERE note_id=?
        """, (
            note.player_name, note.player_id, note.text,
            note.color.value, note.category.value, json.dumps(list(note.tags)),
            note.updated_at.isoformat(), 1 if note.is_important else 0,
            note.session_id, note.note_id
        ))
        
        self.connection.commit()
        return cursor.rowcount > 0
    
    @log_exceptions
    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID."""
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM notes WHERE note_id=?", (note_id,))
        self.connection.commit()
        return cursor.rowcount > 0
    
    @log_exceptions
    def get_note(self, note_id: int) -> Optional[PlayerNote]:
        """Get a note by ID."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM notes WHERE note_id=?", (note_id,))
        row = cursor.fetchone()
        return self._row_to_note(row) if row else None
    
    @log_exceptions
    def get_notes_by_player(self, player_name: str) -> List[PlayerNote]:
        """Get all notes for a specific player."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT * FROM notes WHERE player_name=? ORDER BY updated_at DESC",
            (player_name,)
        )
        return [self._row_to_note(row) for row in cursor.fetchall()]
    
    @log_exceptions
    def get_all_notes(self, limit: Optional[int] = None) -> List[PlayerNote]:
        """Get all notes from database."""
        cursor = self.connection.cursor()
        if limit:
            cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
        return [self._row_to_note(row) for row in cursor.fetchall()]
    
    def _row_to_note(self, row: Tuple) -> PlayerNote:
        """Convert database row to PlayerNote object."""
        return PlayerNote(
            note_id=row[0], player_name=row[1], player_id=row[2], text=row[3],
            color=NoteColor(row[4]), category=NoteCategory(row[5]),
            tags=set(json.loads(row[6])) if row[6] else set(),
            created_at=datetime.datetime.fromisoformat(row[7]),
            updated_at=datetime.datetime.fromisoformat(row[8]),
            is_important=bool(row[9]), session_id=row[10]
        )
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()


class NoteSearch:
    """Search and filter functionality for notes."""
    
    def __init__(self, database: NoteDatabase):
        self.database = database
        logger.info("NoteSearch initialized")
    
    @log_exceptions
    def search_by_text(self, query: str, case_sensitive: bool = False) -> List[PlayerNote]:
        """Search notes by text content."""
        all_notes = self.database.get_all_notes()
        query = query if case_sensitive else query.lower()
        
        matching_notes = [
            note for note in all_notes
            if query in (note.text if case_sensitive else note.text.lower())
        ]
        
        logger.debug(f"Text search found {len(matching_notes)} matches")
        return matching_notes
    
    @log_exceptions
    def search_by_color(self, color: NoteColor) -> List[PlayerNote]:
        """Search notes by color."""
        cursor = self.database.connection.cursor()
        cursor.execute("SELECT * FROM notes WHERE color=?", (color.value,))
        return [self.database._row_to_note(row) for row in cursor.fetchall()]
    
    @log_exceptions
    def search_by_category(self, category: NoteCategory) -> List[PlayerNote]:
        """Search notes by category."""
        cursor = self.database.connection.cursor()
        cursor.execute("SELECT * FROM notes WHERE category=?", (category.value,))
        return [self.database._row_to_note(row) for row in cursor.fetchall()]
    
    @log_exceptions
    def search_by_tags(self, tags: Set[str], match_all: bool = False) -> List[PlayerNote]:
        """Search notes by tags."""
        all_notes = self.database.get_all_notes()
        
        if match_all:
            return [note for note in all_notes if tags.issubset(note.tags)]
        else:
            return [note for note in all_notes if tags & note.tags]
    
    @log_exceptions
    def search_important(self) -> List[PlayerNote]:
        """Get all important notes."""
        cursor = self.database.connection.cursor()
        cursor.execute("SELECT * FROM notes WHERE is_important=1")
        return [self.database._row_to_note(row) for row in cursor.fetchall()]
    
    @log_exceptions
    def advanced_search(
        self,
        text_query: Optional[str] = None,
        player_name: Optional[str] = None,
        color: Optional[NoteColor] = None,
        category: Optional[NoteCategory] = None,
        tags: Optional[Set[str]] = None,
        is_important: Optional[bool] = None
    ) -> List[PlayerNote]:
        """Advanced search with multiple criteria."""
        results = self.database.get_all_notes()
        
        if text_query:
            results = [n for n in results if text_query.lower() in n.text.lower()]
        if player_name:
            results = [n for n in results if n.player_name == player_name]
        if color:
            results = [n for n in results if n.color == color]
        if category:
            results = [n for n in results if n.category == category]
        if tags:
            results = [n for n in results if tags & n.tags]
        if is_important is not None:
            results = [n for n in results if n.is_important == is_important]
        
        return results


class NoteTemplate:
    """Pre-defined note templates."""
    
    TEMPLATES = {
        'fish': {
            'text': "Fish - calls too much, rarely folds",
            'color': NoteColor.RED,
            'category': NoteCategory.GENERAL,
            'tags': {'fish', 'loose', 'passive'}
        },
        'maniac': {
            'text': "Maniac - very aggressive, raises frequently",
            'color': NoteColor.ORANGE,
            'category': NoteCategory.BETTING,
            'tags': {'maniac', 'aggressive', 'loose'}
        },
        'rock': {
            'text': "Rock - very tight, only plays premium hands",
            'color': NoteColor.BLUE,
            'category': NoteCategory.PREFLOP,
            'tags': {'rock', 'tight', 'passive'}
        },
        'lag': {
            'text': "LAG - loose aggressive, difficult opponent",
            'color': NoteColor.GREEN,
            'category': NoteCategory.GENERAL,
            'tags': {'lag', 'loose', 'aggressive', 'good'}
        },
        'tag': {
            'text': "TAG - tight aggressive, solid player",
            'color': NoteColor.GREEN,
            'category': NoteCategory.GENERAL,
            'tags': {'tag', 'tight', 'aggressive', 'good'}
        },
        'tilting': {
            'text': "Currently on tilt - playing poorly",
            'color': NoteColor.RED,
            'category': NoteCategory.TILT,
            'tags': {'tilt', 'exploitable'}
        },
    }
    
    @classmethod
    def get_template(cls, template_name: str, player_name: str) -> Optional[PlayerNote]:
        """Get a pre-defined note template."""
        if template_name not in cls.TEMPLATES:
            return None
        
        template = cls.TEMPLATES[template_name]
        return PlayerNote(
            player_name=player_name,
            text=template['text'],
            color=template['color'],
            category=template['category'],
            tags=template['tags'].copy()
        )
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """Get list of available template names."""
        return list(cls.TEMPLATES.keys())


class AutoNoteGenerator:
    """Automatic note generation from hand history and statistics."""
    
    def __init__(self):
        logger.info("AutoNoteGenerator initialized")
    
    @log_exceptions
    def generate_from_stats(
        self,
        player_name: str,
        stats: Dict[str, float]
    ) -> List[PlayerNote]:
        """Generate notes based on player statistics."""
        notes = []
        
        vpip = stats.get('vpip', 0)
        if vpip > 35:
            notes.append(PlayerNote(
                player_name=player_name,
                text=f"Very loose preflop (VPIP: {vpip:.1f}%)",
                color=NoteColor.RED,
                category=NoteCategory.PREFLOP,
                tags={'loose', 'vpip', 'auto-generated'}
            ))
        elif vpip < 15:
            notes.append(PlayerNote(
                player_name=player_name,
                text=f"Very tight preflop (VPIP: {vpip:.1f}%)",
                color=NoteColor.BLUE,
                category=NoteCategory.PREFLOP,
                tags={'tight', 'vpip', 'auto-generated'}
            ))
        
        pfr = stats.get('pfr', 0)
        if pfr > 25:
            notes.append(PlayerNote(
                player_name=player_name,
                text=f"Very aggressive preflop (PFR: {pfr:.1f}%)",
                color=NoteColor.ORANGE,
                category=NoteCategory.PREFLOP,
                tags={'aggressive', 'pfr', 'auto-generated'}
            ))
        
        af = stats.get('af', 0)
        if af > 3.0:
            notes.append(PlayerNote(
                player_name=player_name,
                text=f"Highly aggressive postflop (AF: {af:.1f})",
                color=NoteColor.ORANGE,
                category=NoteCategory.POSTFLOP,
                tags={'aggressive', 'af', 'auto-generated'}
            ))
        
        return notes


class NoteTakingSystem:
    """Main note taking system."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the note taking system."""
        self.database = NoteDatabase(db_path)
        self.search = NoteSearch(self.database)
        self.auto_generator = AutoNoteGenerator()
        logger.info("NoteTakingSystem initialized")
    
    @log_exceptions
    def create_note(
        self,
        player_name: str,
        text: str,
        color: NoteColor = NoteColor.YELLOW,
        category: NoteCategory = NoteCategory.GENERAL,
        tags: Optional[Set[str]] = None,
        is_important: bool = False
    ) -> PlayerNote:
        """Create a new note."""
        note = PlayerNote(
            player_name=player_name, text=text, color=color,
            category=category, tags=tags or set(), is_important=is_important
        )
        
        note_id = self.database.add_note(note)
        note.note_id = note_id
        return note
    
    @log_exceptions
    def create_from_template(
        self,
        template_name: str,
        player_name: str
    ) -> Optional[PlayerNote]:
        """Create a note from a template."""
        note = NoteTemplate.get_template(template_name, player_name)
        if note:
            note_id = self.database.add_note(note)
            note.note_id = note_id
        return note
    
    @log_exceptions
    def update_note(self, note: PlayerNote) -> bool:
        """Update an existing note."""
        return self.database.update_note(note)
    
    @log_exceptions
    def delete_note(self, note_id: int) -> bool:
        """Delete a note."""
        return self.database.delete_note(note_id)
    
    @log_exceptions
    def get_player_notes(self, player_name: str) -> List[PlayerNote]:
        """Get all notes for a player."""
        return self.database.get_notes_by_player(player_name)
    
    @log_exceptions
    def get_player_summary(self, player_name: str) -> Dict[str, Any]:
        """Get a summary of notes for a player."""
        notes = self.get_player_notes(player_name)
        
        if not notes:
            return {
                'player_name': player_name,
                'note_count': 0,
                'primary_color': None,
                'categories': [],
                'all_tags': []
            }
        
        color_counts = Counter(note.color for note in notes)
        primary_color = color_counts.most_common(1)[0][0]
        
        categories = list(set(note.category for note in notes))
        all_tags = set()
        for note in notes:
            all_tags.update(note.tags)
        
        return {
            'player_name': player_name,
            'note_count': len(notes),
            'primary_color': primary_color.value,
            'categories': [cat.value for cat in categories],
            'all_tags': list(all_tags),
            'has_important': any(note.is_important for note in notes),
            'last_updated': max(note.updated_at for note in notes).isoformat()
        }
    
    @log_exceptions
    def generate_auto_notes(
        self,
        player_name: str,
        stats: Dict[str, float],
        save: bool = True
    ) -> List[PlayerNote]:
        """Generate and optionally save automatic notes."""
        notes = self.auto_generator.generate_from_stats(player_name, stats)
        
        if save:
            for note in notes:
                note_id = self.database.add_note(note)
                note.note_id = note_id
        
        return notes
    
    @log_exceptions
    def export_notes(self, output_path: Path, player_name: Optional[str] = None) -> None:
        """Export notes to JSON file."""
        if player_name:
            notes = self.get_player_notes(player_name)
        else:
            notes = self.database.get_all_notes()
        
        data = {
            'exported_at': datetime.datetime.now().isoformat(),
            'note_count': len(notes),
            'notes': [note.to_dict() for note in notes]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(notes)} notes to {output_path}")
    
    @log_exceptions
    def import_notes(self, input_path: Path) -> int:
        """Import notes from JSON file."""
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        count = 0
        for note_data in data['notes']:
            note = PlayerNote.from_dict(note_data)
            note.note_id = None  # Reset ID for new insert
            self.database.add_note(note)
            count += 1
        
        logger.info(f"Imported {count} notes from {input_path}")
        return count
    
    def close(self) -> None:
        """Close database connection."""
        self.database.close()


# Example usage
if __name__ == "__main__":
    system = NoteTakingSystem()
    
    # Create a manual note
    note = system.create_note(
        player_name="Villain1",
        text="Folds to 3-bets frequently",
        color=NoteColor.YELLOW,
        category=NoteCategory.PREFLOP,
        tags={'3bet', 'folds'},
        is_important=True
    )
    print(f"Created note {note.note_id}")
    
    # Create from template
    template_note = system.create_from_template("fish", "Player2")
    if template_note:
        print(f"Created template note {template_note.note_id}")
    
    # Generate auto-notes
    stats = {'vpip': 42.5, 'pfr': 28.3, 'af': 3.5}
    auto_notes = system.generate_auto_notes("Maniac1", stats, save=True)
    print(f"Generated {len(auto_notes)} auto-notes")
    
    # Search
    important_notes = system.search.search_important()
    print(f"Found {len(important_notes)} important notes")
    
    # Get player summary
    summary = system.get_player_summary("Maniac1")
    print(f"Player summary: {summary}")
    
    system.close()
