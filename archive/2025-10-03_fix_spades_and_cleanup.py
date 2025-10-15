#!/usr/bin/env python3
"""
Migration script to fix the Suit.SPADES issue and clean up old backup files in
the PokerTool repository.

This script installs or updates ``poker_modules.py`` with an improved
implementation that defines a proper :class:`Suit` enumeration and a flexible
``Card`` class.  It will also remove duplicate ``poker_modules.py`` files
elsewhere in the repository and archive the ``structure_backup`` directory
containing outdated backups.

Usage::

    python3 2025-10-03_fix_spades_and_cleanup.py

By default, the script operates on ``/Users/georgeridout/Documents/github/pokertool``.
If the ``POKERTOOL_DIR`` environment variable is set, that path will be used
instead.  Existing files are backed up with a timestamp suffix before being
modified or moved.
"""

import os
import shutil
import datetime
from typing import Any


# The new contents for poker_modules.py.  This module defines a proper Suit
# enumeration, exposes SUITS and RANKS constants, and provides a Card class
# that accepts multiple suit representations.  It retains placeholders for
# calculate_win_probability and plugin registration functions.
NEW_POKER_MODULES: str = """"""
Fixed poker_modules with Suit Enum, constants, and flexible Card class.

This module defines a ``Suit`` enumeration with familiar suits—Spades, Hearts,
Diamonds, and Clubs—and exposes ``SUITS`` and ``RANKS`` lists used by many UI
components.  A new ``Card`` class accepts either a ``Suit`` member or a
variety of string inputs (symbols, single‑letter abbreviations, or full
names).  It normalizes the suit internally and validates the rank against the
standard 2–A sequence.  The goal is to be completely backward‑compatible with
legacy code that may still refer to ``Suit.SPADES`` while gracefully
supporting more human‑friendly inputs.

If your code previously raised ``AttributeError: type object 'Suit' has no
attribute 'SPADES'``, it almost certainly imported a stale copy of this
module or defined ``Suit`` incorrectly.  Make sure that your PYTHONPATH
prefers this updated module.  You can verify which file is being imported by
running::

    import poker_modules
    print(poker_modules.__file__)

If the path points somewhere unexpected, delete or rename old copies.  When
correctly imported, you should see ``Suit.SPADES`` evaluate to ``'♠'`` and
``SUITS`` return ``['♠', '♥', '♦', '♣']``.

This file leaves room for additional functions (e.g. ``calculate_win_probability``)
from earlier versions.  If you have other functions or classes that need to
persist, copy them in below the ``Card`` class definition.
""""""

from enum import Enum
from typing import Tuple, Any, Dict


class Suit(Enum):
    """Standard playing card suits represented by their Unicode symbols."""

    SPADES = "♠"
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"

    def __str__(self) -> str:
        return self.value


# UI‑friendly lists of suits and ranks.  These constants should remain stable.
SUITS: list[str] = [s.value for s in Suit]
RANKS: list[str] = [
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "T",
    "J",
    "Q",
    "K",
    "A",
]


class Card:
    """Represents a standard playing card with a rank and suit.

    The constructor accepts either a :class:`Suit` member or a string/character
    describing the suit.  Supported inputs include:

    * A :class:`Suit` enumeration member (e.g., ``Suit.SPADES``).
    * One‑letter abbreviations ("S", "H", "D", "C"), case‑insensitive.
    * Full names ("spades", "hearts", "diamonds", "clubs"), case‑insensitive.
    * Unicode suit symbols ("♠", "♥", "♦", "♣").

    The rank may be one of the entries in the global ``RANKS`` list.  Both
    parameters are validated and normalized.  Invalid inputs raise
    :class:`ValueError`.
    """

    __slots__ = ("suit", "rank")

    _suit_aliases: Dict[str, Suit] = {
        # Spades
        "s": Suit.SPADES,
        "spade": Suit.SPADES,
        "spades": Suit.SPADES,
        "♠": Suit.SPADES,
        # Hearts
        "h": Suit.HEARTS,
        "heart": Suit.HEARTS,
        "hearts": Suit.HEARTS,
        "♥": Suit.HEARTS,
        # Diamonds
        "d": Suit.DIAMONDS,
        "diamond": Suit.DIAMONDS,
        "diamonds": Suit.DIAMONDS,
        "♦": Suit.DIAMONDS,
        # Clubs
        "c": Suit.CLUBS,
        "club": Suit.CLUBS,
        "clubs": Suit.CLUBS,
        "♣": Suit.CLUBS,
    }

    def __init__(self, suit: Any, rank: Any) -> None:
        # Normalize the suit
        if isinstance(suit, Suit):
            self.suit = suit
        else:
            key = str(suit).strip().lower()
            try:
                self.suit = self._suit_aliases[key]
            except KeyError as exc:
                raise ValueError(f"Unknown suit: {suit!r}") from exc

        # Normalize the rank
        r = str(rank).strip().upper()
        if r in RANKS:
            self.rank = r
        else:
            raise ValueError(f"Invalid rank: {rank!r}. Expected one of {RANKS}.")

    def __str__(self) -> str:
        return f"{self.rank}{self.suit.value}"

    def __repr__(self) -> str:
        return f"Card({self.suit!r}, {self.rank!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Card):
            return self.suit == other.suit and self.rank == other.rank
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    def as_tuple(self) -> Tuple[Suit, str]:
        """Return a tuple representation of the card: (suit, rank)."""
        return (self.suit, self.rank)


def calculate_win_probability(*args: Any, **kwargs: Any) -> float:
    """Placeholder function for win probability calculation.

    This dummy implementation returns 0.0.  Replace or extend this with your
    actual hand evaluation logic.
    """
    return 0.0


PLUGIN_REGISTRY: Dict[str, Any] = {}


def register_plugin(name: str, plugin: Any) -> None:
    """Register a plugin by name.

    This function adds the given plugin to the global ``PLUGIN_REGISTRY``.
    """
    PLUGIN_REGISTRY[name] = plugin

"""


def write_new_module(root_dir: str) -> None:
    """Install or update the main poker_modules.py file in ``root_dir``.

    If an existing file is found, it is backed up with a timestamp suffix
    before being overwritten.  The contents written are drawn from
    ``NEW_POKER_MODULES`` defined in this script.
    """
    target = os.path.join(root_dir, "poker_modules.py")
    # Ensure parent exists
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.exists(target):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = f"{target}.bak_{ts}"
        shutil.copy2(target, backup)
        print(f"Backed up existing poker_modules.py to {backup}")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(NEW_POKER_MODULES)
    print(f"Installed updated poker_modules.py to {target}")


def remove_duplicate_modules(root_dir: str) -> None:
    """Remove duplicate poker_modules.py files found in the tree below root_dir.

    Walks the directory tree and deletes any file named ``poker_modules.py``
    that is not the one located at the root of the repository.  This helps
    eliminate stale copies that might be picked up by Python's import system.
    """
    root_target = os.path.abspath(os.path.join(root_dir, "poker_modules.py"))
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname == "poker_modules.py":
                path = os.path.abspath(os.path.join(dirpath, fname))
                if path != root_target:
                    os.remove(path)
                    print(f"Removed duplicate poker_modules.py at {path}")


def archive_structure_backup(root_dir: str) -> None:
    """Archive the structure_backup directory if it exists.

    If a directory named ``structure_backup`` exists directly under ``root_dir``,
    it is renamed with a timestamp suffix to prevent accidental use.  This
    effectively removes old backup files from the active project tree while
    preserving them in an archive for reference.
    """
    backup_dir = os.path.join(root_dir, "structure_backup")
    if os.path.isdir(backup_dir):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dir = f"{backup_dir}_old_{ts}"
        shutil.move(backup_dir, archive_dir)
        print(f"Archived structure_backup to {archive_dir}")


def main() -> None:
    """Entry point for the script."""
    # Determine the project root directory.  Default to the user's repo location
    # but allow override via environment variable.
    root = os.getenv("POKERTOOL_DIR", "/Users/georgeridout/Documents/github/pokertool")
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        print(f"Error: specified root directory {root} does not exist.")
        return
    # Install the updated module
    write_new_module(root)
    # Remove duplicate modules
    remove_duplicate_modules(root)
    # Archive old backup directory
    archive_structure_backup(root)
    print("Migration complete.")


if __name__ == "__main__":
    main()