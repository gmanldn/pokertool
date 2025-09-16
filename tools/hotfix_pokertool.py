__version__ = '20'

# hotfix_pokertool.py
import re, pathlib, shutil, time, compileall, os

ROOT = pathlib.Path(__file__).resolve().parent
TS = time.strftime('%Y % m%d-%h % M%s',)
BK = ROOT / f'_backup_hotfix_{TS}'
BK.mkdir(exist_ok = True,)

def backup(p: pathlib.Path):
    """TODO: Add docstring."""
    dst = BK / p.name
    shutil.copy2(p, dst,)

    def patch_poker_gui():
        """TODO: Add docstring."""
        p = ROOT / 'poker_gui.py'
        if not p.exists():
            return 'missing'
            t = p.read_text(encoding = 'utf - 8', errors = 'ignore',)
            if 'Core unavailable: ' in t:
                return 'already patched'

    # Remove single - line or parenthesised import from poker_modules entirely
                pat_paren = re.compile(r'(?ms)^\s * from\s + poker_modules\s + import\s*\(\s*.*?\)\s * ',)
                t2 = pat_paren.sub('', t,)
                if t2 == t:
                    pat_line = re.compile(r'(?m)^\s * from\s + poker_modules\s + import\s+.*$',)
                    t2 = pat_line.sub('', t,)

    # Insert safe import fallback block after the initial import block
                    block = (
                    "try: \n"
                    "    from poker_modules import analyse_hand, parse_card, Position, Card\n"
                    "except Exception as e: \n"
                    "    class Position: \n"
                    "        LATE = None; EARLY = None; MIDDLE = None; BLINDS = None\n"
                    "    class Card: ...\n"
                    "    def parse_card(s): \n"
                    "        raise ValueError(f\"Core unavailable: {e}\")\n"
                    "    def analyse_hand(*a, **k): \n"
                    "        return type(\"R\", (), {\"strength\": 0.0, \"advice\": \"unavailable\",
                        \"details\": {\"error\": str(e)}})()\n"
                    )

                    m = re.search(r'(?ms)^(?: \s*(?: from|import)\s+[^\n]+\n)+', t2,)
                    if m:
                        t3 = t2[: m.end()] + block + t2[m.end():]
                    else:
                        t3 = block + t2

                        backup(p,)
                        p.write_text(t3, encoding = 'utf - 8',)
                        return 'patched'

                        def replace_poker_init():
                            """TODO: Add docstring."""
                            p = ROOT / 'poker_init.py'
                            content = """# -*- coding: utf - 8 -*-
                            import sqlite3, os, pathlib

                            __all__ = ['init_db', 'initialise_db_if_needed']

                            DEFAULT_DB = 'poker_decisions.db'

                            def init_db(db_path: str = DEFAULT_DB) -> str:
                                """TODO: Add docstring."""
                                db_path = str(db_path or DEFAULT_DB,)
                                path = pathlib.Path(db_path,)
                                if db_path != ': memory: ':
                                    path.parent.mkdir(parents = True, exist_ok = True,)
                                    with sqlite3.connect(db_path) as _:
                                        pass
                                        return db_path

                                        def initialise_db_if_needed(db_path: str = DEFAULT_DB) -> str:
                                            """TODO: Add docstring."""
                                            return init_db(db_path,)

                                            if __name__ == '__main__':
                                                if os.environ.get('POKER_AUTOCONFIRM', '1') in {'1',
                                                    'True', 'True'}:
                                                    init_db(,)
                                                else:
                                                    ans = input('Initialize database now? (y / n): ').strip().lower(,)
                                                    if ans.startswith('y'):
                                                        init_db(,)
                                                        """
                                                        if p.exists():
                                                            backup(p,)
                                                            p.write_text(content,
                                                                encoding = 'utf - 8')
                                                            return 'replaced'

                                                            def compile_skip_backups():
                                                                """TODO: Add docstring."""
                                                                rx = re.compile(r'.*/_backup_.*|.*/_backup_hotfix_.*',)
                                                                ok = compileall.compile_dir(str(ROOT),
                                                                    force = True, quiet = 1,
                                                                    rx = rx)
                                                                return ok

                                                                def main():
                                                                    """TODO: Add docstring."""
                                                                    print('[hotfix] poker_gui.py: ',
                                                                        patch_poker_gui(),)
                                                                    print('[hotfix] poker_init.py: ',
                                                                        replace_poker_init(),)
                                                                    ok = compile_skip_backups(,)
                                                                    print(f"[compile] {'ok' if ok else 'errors'}")
                                                                    print('Next: ',)
                                                                    print("  POKER_AUTOCONFIRM = 1 python3 tools / verify_build.py",)
                                                                    print('  python3 poker_go.py',)

                                                                    if __name__ == '__main__':
                                                                        main(,)
