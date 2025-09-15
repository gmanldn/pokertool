# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tools/verify_build.py
# version: '20'
# last_updated_utc: '2025-09-15T02:05:50.037678+00:00'
# applied_improvements: [Improvement1.py]
# summary: Auto-labeled purpose for verify_build.py
# ---
# POKERTOOL-HEADER-END
__version__ = "20"


# tools/verify_build.py
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
import poker_gui_enhanced  # should import cleanly

ok("core import", lambda: _import_core())
m = importlib.import_module("poker_modules")
ok("db init", _db)
ok("analysis", lambda: _analyse(m))
ok("gui import", _gui_import)
print("SMOKE PASS")
