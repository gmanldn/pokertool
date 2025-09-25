# forwardscripts/update_gitignore_sep25.py
"""
Update script: Clean and fix .gitignore for PokerTool
- Removes irrelevant framework/tool entries (Django, Flask, Celery, Sage, etc.)
- Ensures SQLite DB files are ignored (poker.db, pokertool.db)
- Keeps standard Python ignores (__pycache__, *.pyc, venv, .env, etc.)
- Backs up existing .gitignore before writing new one
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
gitignore = ROOT / ".gitignore"
backup = ROOT / ".gitignore.backup"

CLEAN_GITIGNORE = """# Python bytecode
__pycache__/
*.py[cod]
*$py.class

# Distribution / build
build/
dist/
*.egg-info/
.eggs/
wheels/

# Virtual environments
.env
.venv/
env/
venv/
ENV/
env.bak/
venv.bak/

# Test / coverage
.pytest_cache/
.coverage
coverage.xml
htmlcov/
.tox/
.nox/

# OS files
.DS_Store
Thumbs.db

# IDE/editor
.vscode/
.idea/
*.swp

# Project-specific
poker.db
pokertool.db
"""

def run():
    if gitignore.exists():
        shutil.copy2(gitignore, backup)
        print(f"[info] Backed up {gitignore} -> {backup}")

    with open(gitignore, "w") as f:
        f.write(CLEAN_GITIGNORE.strip() + "\n")
    print(f"[info] Wrote cleaned .gitignore to {gitignore}")

if __name__ == "__main__":
    run()
