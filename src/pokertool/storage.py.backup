# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: poker_init.py
# version: '20'
# last_updated_utc: '2025-09-15T02:05:50.037678+00:00'
# applied_improvements: [Improvement1.py]
# summary: Database initialization and persistence layer
# ---
# POKERTOOL-HEADER-END
__version__ = "20"


# -*- coding: utf-8 -*-
import sqlite3, os, pathlib

__all__ = ["init_db", "initialise_db_if_needed"]

DEFAULT_DB = "poker_decisions.db"

def init_db(db_path: str = DEFAULT_DB) -> str:
    db_path = str(db_path or DEFAULT_DB)
    path = pathlib.Path(db_path)
    if db_path != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as _:
        pass
    return db_path

def initialise_db_if_needed(db_path: str = DEFAULT_DB) -> str:
    return init_db(db_path)

if __name__ == "__main__":
    if os.environ.get("POKER_AUTOCONFIRM","1") in {"1","true","True"}:
        init_db()
    else:
        ans = input("Initialize database now? (y/n): ").strip().lower()
        if ans.startswith("y"):
            init_db()
