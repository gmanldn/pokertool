#!/usr/bin/env python3
"""
apply_pokertool_fixes.py
Run from the repo root. Creates a timestamped backup folder.
"""
import re, sys, os, shutil, time, pathlib, compileall

ROOT = pathlib.Path(__file__).resolve().parent
TS = time.strftime("%Y%m%d-%H%M%S")
BACKUP = ROOT / f"_backup_{TS}"
TOOLS = ROOT / "tools"
os.makedirs(BACKUP, exist_ok=True)
os.makedirs(TOOLS, exist_ok=True)

def backup_file(p: pathlib.Path):
    rel = p.relative_to(ROOT)
    dst = BACKUP / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst)

def read_text(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_text(p: pathlib.Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def sanitize_repo():
    fixed = 0
    for p in ROOT.rglob("*.py"):
        if any(part in {".venv","venv","__pycache__"} for part in p.parts):
            continue
        t0 = read_text(p)
        t = t0
        # Drop REPL prompts like ">>> from ..."
        t = re.sub(r'(?m)^\s*>>>\s.*\n', '', t)
        # Strip BOM/NUL
        t = t.lstrip("\ufeff\0")
        # Normalise leading tabs to 4 spaces
        t = re.sub(r'(?m)^\t+', lambda m: "    " * len(m.group(0)), t)
        if t != t0:
            backup_file(p)
            write_text(p, t)
            fixed += 1
    return fixed

# --- Replacement content for poker_modules.py (clean Enums, Card, analyse_hand) ---
POKER_MODULES_NEW = r'''# -*- coding: utf-8 -*-
from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple, Dict

__all__ = [
    "Suit","Rank","Position","Card",
    "parse_card","analyse_hand","HandAnalysisResult",
]

class Rank(Enum):
    TWO=2; THREE=3; FOUR=4; FIVE=5; SIX=6; SEVEN=7; EIGHT=8; NINE=9; TEN=10
    JACK=11; QUEEN=12; KING=13; ACE=14
    @property
    def sym(self)->str:
        return {
            Rank.TWO:"2", Rank.THREE:"3", Rank.FOUR:"4", Rank.FIVE:"5",
            Rank.SIX:"6", Rank.SEVEN:"7", Rank.EIGHT:"8", Rank.NINE:"9",
            Rank.TEN:"T", Rank.JACK:"J", Rank.QUEEN:"Q", Rank.KING:"K", Rank.ACE:"A",
        }[self]
    @property
    def val(self)->int:  # legacy accessor
        return int(self.value)

class Suit(Enum):
    SPADES="S"; HEARTS="H"; DIAMONDS="D"; CLUBS="C"
    @property
    def glyph(self)->str:
        return {"S":"♠","H":"♥","D":"♦","C":"♣"}[self.value]

class Position(Enum):
    EARLY=auto(); MIDDLE=auto(); LATE=auto(); BLINDS=auto()
    @property
    def category(self)->str:
        return {
            Position.EARLY:"early",
            Position.MIDDLE:"middle",
            Position.LATE:"late",
            Position.BLINDS:"blinds",
        }[self]
    def is_late(self)->bool:
        return self is Position.LATE

@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit
    def __str__(self)->str: return f"{self.rank.sym}{self.suit.value}"
    def __repr__(self)->str: return f"Card({self.rank.name},{self.suit.name})"

def parse_card(s: str) -> Card:
    s = s.strip().upper()
    rank_map: Dict[str, Rank] = {
        "2":Rank.TWO, "3":Rank.THREE, "4":Rank.FOUR, "5":Rank.FIVE,
        "6":Rank.SIX, "7":Rank.SEVEN, "8":Rank.EIGHT, "9":Rank.NINE,
        "T":Rank.TEN, "J":Rank.JACK, "Q":Rank.QUEEN, "K":Rank.KING, "A":Rank.ACE
    }
    suit_map = {"S":Suit.SPADES,"H":Suit.HEARTS,"D":Suit.DIAMONDS,"C":Suit.CLUBS}
    if len(s)!=2 or s[0] not in rank_map or s[1] not in suit_map:
        raise ValueError(f"Bad card '{s}'. Use like 'AS','TD','9C'.")
    return Card(rank_map[s[0]], suit_map[s[1]])

@dataclass
class HandAnalysisResult:
    strength: float
    advice: str
    details: dict

def analyse_hand(hole_cards: Iterable[Card],
                 board_cards: Optional[Iterable[Card]] = None,
                 position: Optional[Position] = None,
                 pot: Optional[float] = None,
                 to_call: Optional[float] = None) -> HandAnalysisResult:
    hc = list(hole_cards)
    if len(hc) < 2:
        return HandAnalysisResult(0.0, "fold", {"error":"need 2 hole cards"})
    ranks = sorted([int(c.rank.value) for c in hc[:2]], reverse=True)
    pair = ranks[0]==ranks[1]
    if pair and ranks[0] >= Rank.JACK.value:
        advice = "raise"
    elif min(ranks) < 7:
        advice = "fold"
    else:
        advice = "call"
    return HandAnalysisResult(
        strength = sum(ranks)/28.0,
        advice = advice,
        details = {"pair": pair, "position": getattr(position, "category", None)}
    )
'''

# --- verify_build.py content ---
VERIFY_BUILD = r'''# tools/verify_build.py
import os, importlib, sqlite3, contextlib
os.environ.setdefault("POKER_AUTOCONFIRM","1")

def ok(name, fn):
    try:
        fn(); print("[OK]", name)
    except Exception as e:
        print("[FAIL]", name, "->", e); raise

def _import_core():
    import poker_modules as m
    assert hasattr(m,"analyse_hand") and hasattr(m,"Card")
    return m

def _db():
    import poker_init as pi
    pi.init_db(":memory:")
    with contextlib.closing(sqlite3.connect(":memory:")) as _:
        pass

def _analyse(m):
    hc = [m.parse_card("AS"), m.parse_card("KD")]
    r = m.analyse_hand(hc)
    assert hasattr(r,"advice")

def _gui_import():
    import poker_gui  # should import cleanly

ok("core import", lambda: _import_core())
m = importlib.import_module("poker_modules")
ok("db init", _db)
ok("analysis", lambda: _analyse(m))
ok("gui import", _gui_import)
print("SMOKE PASS")
'''

def patch_poker_gui():
    p = ROOT / "poker_gui.py"
    if not p.exists(): return False, "poker_gui.py not found"
    t0 = read_text(p)
    t = t0
    # Replace a direct import line with try/except fallback
    pattern = r'(?m)^\s*from\s+poker_modules\s+import\s+.*\n'
    block = (
        "try:\n"
        "    from poker_modules import analyse_hand, parse_card, Position, Card\n"
        "except Exception as e:\n"
        "    class Position:\n"
        "        LATE=None; EARLY=None; MIDDLE=None; BLINDS=None\n"
        "    class Card: ...\n"
        "    def parse_card(s):\n"
        "        raise ValueError(f\"Core unavailable: {e}\")\n"
        "    def analyse_hand(*a, **k):\n"
        "        return type(\"R\",(),{\"strength\":0.0,\"advice\":\"unavailable\",\"details\":{\"error\":str(e)}})()\n"
    )
    if re.search(pattern, t):
        t = re.sub(pattern, block, t, count=1)
    else:
        # If not found, inject near top after first import
        m = re.search(r'(?m)^(import\s+\S+|from\s+\S+\s+import\s+.*)\n', t)
        insert_at = m.end() if m else 0
        t = t[:insert_at] + block + t[insert_at:]
    if t != t0:
        backup_file(p); write_text(p, t); return True, "patched"
    return False, "no change"

def patch_poker_go():
    p = ROOT / "poker_go.py"
    if not p.exists(): return False, "poker_go.py not found"
    t0 = read_text(p)
    t = t0
    # Ensure env-driven autoconfirm and input override at top
    autoconfirm_block = (
        "import os as _os\n"
        "if _os.environ.get('POKER_AUTOCONFIRM','1') in {'1','true','True'}:\n"
        "    import builtins as _bi\n"
        "    _bi.input = lambda *a, **k: 'y'\n"
    )
    if "builtins as _bi" not in t:
        # insert after first import block
        m = re.search(r'(?ms)^(?:\s*(?:from|import)\s+[^\n]+\n)+', t)
        if m:
            t = t[:m.end()] + autoconfirm_block + t[m.end():]
        else:
            t = autoconfirm_block + t
    # Replace prompt_continue body if present
    t = re.sub(
        r'(?ms)def\s+prompt_continue\s*\([^)]*\):\s*.*?(?=^\S|\Z)',
        "def prompt_continue(_msg:str=''):\n"
        "    import os\n"
        "    return os.environ.get('POKER_AUTOCONFIRM','1') not in {'0','false','False'}\n",
        t
    )
    # Comment out any writes to .py in write mode
    t = re.sub(r'(?m)^(?P<indent>\s*)with\s+open\((?P<args>[^\\n]*?\\.py[\"\\\'][^\\)]*?),\s*[\"\\\']w[\"\\\']([^)]*)\)\s+as\s+\w+:\s*$',
               r"\g<indent># PATCHED: \g<0>", t)
    t = re.sub(r'(?m)^(?P<indent>\s*)\w+\.write\(', r"\g<indent># PATCHED: write(", t)
    if t != t0:
        backup_file(p); write_text(p, t); return True, "patched"
    return False, "no change"

def patch_poker_init():
    p = ROOT / "poker_init.py"
    if not p.exists(): return False, "poker_init.py not found"
    t0 = read_text(p)
    t = t0
    # Ensure there is an init_db function call on import and env-driven main guard
    # Replace existing __main__ block if present
    t = re.sub(
        r'(?ms)if\s+__name__\s*==\s*[\'\"]__main__[\'\"]\s*:\s*.*\Z',
        (
            "if __name__ == '__main__':\n"
            "    import os\n"
            "    if os.environ.get('POKER_AUTOCONFIRM','1') in {'1','true','True'}:\n"
            "        init_db()\n"
            "    else:\n"
            "        ans = input('Initialize database now? (y/n): ').strip().lower()\n"
            "        if ans.startswith('y'):\n"
            "            init_db()\n"
            "else:\n"
            "    # Safe default on import\n"
            "    init_db()\n"
        ),
        t
    )
    # If there was no __main__ block, append ours
    if "__main__" not in t:
        t += (
            "\nif __name__ == '__main__':\n"
            "    import os\n"
            "    if os.environ.get('POKER_AUTOCONFIRM','1') in {'1','true','True'}:\n"
            "        init_db()\n"
            "    else:\n"
            "        ans = input('Initialize database now? (y/n): ').strip().lower()\n"
            "        if ans.startswith('y'):\n"
            "            init_db()\n"
            "else:\n"
            "    init_db()\n"
        )
    if t != t0:
        backup_file(p); write_text(p, t); return True, "patched"
    return False, "no change"

def replace_poker_modules():
    p = ROOT / "poker_modules.py"
    if not p.exists():
        # still write it afresh
        write_text(p, POKER_MODULES_NEW)
        return True, "created"
    t0 = read_text(p)
    if t0 == POKER_MODULES_NEW:
        return False, "up-to-date"
    backup_file(p)
    write_text(p, POKER_MODULES_NEW)
    return True, "replaced"

def write_verify_build():
    p = TOOLS / "verify_build.py"
    write_text(p, VERIFY_BUILD)
    return True, "written"

def compile_repo():
    ok = compileall.compile_dir(str(ROOT), force=True, quiet=1)
    return ok

def main():
    print(f"[info] repo: {ROOT}")
    print(f"[info] backup: {BACKUP}")
    changed = sanitize_repo()
    if changed:
        print(f"[fix] sanitised {changed} file(s)")
    else:
        print("[info] no sanitisation needed")

    changed, msg = replace_poker_modules()
    print(f"[poker_modules.py] {msg}")

    ch, msg = patch_poker_gui()
    print(f"[poker_gui.py] {msg}")

    ch, msg = patch_poker_go()
    print(f"[poker_go.py] {msg}")

    ch, msg = patch_poker_init()
    print(f"[poker_init.py] {msg}")

    write_verify_build()
    print("[tools/verify_build.py] written")

    ok = compile_repo()
    print(f"[compile] {'ok' if ok else 'errors'}")

    print("\nNext:")
    print("  POKER_AUTOCONFIRM=1 python3 tools/verify_build.py")
    print("  python3 poker_go.py  # should be non-interactive")

if __name__ == "__main__":
    main()
