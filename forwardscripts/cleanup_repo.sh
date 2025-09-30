#!/bin/bash
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: cleanup_repo.sh
# version: v28.0.0
# last_commit: '2025-09-23T15:51:55+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END

# Git Repository Cleanup Script for PokerTool
echo "🧹 Starting Git repository cleanup for PokerTool..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository root. Please run from the repository root."
    exit 1
fi

# Create comprehensive .gitignore
echo "📝 Creating comprehensive .gitignore..."
cat > .gitignore << 'GITIGNORE_EOF'
# PokerTool - Comprehensive .gitignore

# POKERTOOL-SPECIFIC FILES
_backup_*/
build_reports/
.pokertool_state.json
poker_decisions.db.backup*
*.db.backup*
*.db-journal
htmlcov/
.coverage
coverage.xml
*.cover

# PYTHON
__pycache__/
*.py[cod]
*$py.class
*.so
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.tox/
.nox/
.cache
nosetests.xml
*.py,cover
.hypothesis/
.pytest_cache/
cover/
*.log
.pybuilder/
target/
.ipynb_checkpoints
profile_default/
ipython_config.py
.python-version

# ENVIRONMENTS
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDES AND EDITORS
.vscode/
*.code-workspace
.idea/
*.iml
*.ipr
*.iws
*.sublime-project
*.sublime-workspace
*.swp
*.swo
*~

# OPERATING SYSTEMS
.DS_Store
.AppleDouble
.LSOverride
Icon?
.Spotlight-V100
.Trashes
._*
Thumbs.db
ehthumbs.db
*.tmp
*.temp
Desktop.ini
$RECYCLE.BIN/
*.lnk

# TEMPORARY AND LOG FILES
*.log
logs/
log/
*.tmp
*.temp
.tmp/
temp/
tmp/
*.bak
*.backup
*.old

# SECURITY
.env.local
.env.development.local
.env.test.local
.env.production.local
secrets.json
private_key*
*.pem
*.key
*.crt
*.cer
*.p12
*.pfx
GITIGNORE_EOF

echo "🗑️  Untracking temporary/local files..."

# Remove from git tracking (keep local files)
git rm -r --cached _backup_* 2>/dev/null || true
git rm --cached .pokertool_state.json 2>/dev/null || true
git rm -r --cached build_reports/ 2>/dev/null || true
git rm -r --cached htmlcov/ 2>/dev/null || true
git rm -r --cached __pycache__/ 2>/dev/null || true
git rm -r --cached .pytest_cache/ 2>/dev/null || true
git rm --cached .coverage 2>/dev/null || true
git rm -r --cached .venv/ 2>/dev/null || true
git rm -r --cached venv/ 2>/dev/null || true
git rm -r --cached build/ 2>/dev/null || true
git rm -r --cached dist/ 2>/dev/null || true
git rm -r --cached .idea/ 2>/dev/null || true
git rm -r --cached .vscode/ 2>/dev/null || true
git rm -r --cached logs/ 2>/dev/null || true
git rm --cached .DS_Store 2>/dev/null || true
git rm --cached *.log 2>/dev/null || true
git rm --cached *.db.backup* 2>/dev/null || true

# Find and untrack backup directories
find . -name "_backup_*" -type d | while read dir; do
    if [ -d "$dir" ]; then
        git rm -r --cached "$dir" 2>/dev/null || true
        echo "   📁 Untracked: $dir"
    fi
done

# Find and untrack Python cache directories
find . -name "__pycache__" -type d | while read dir; do
    if [ -d "$dir" ]; then
        git rm -r --cached "$dir" 2>/dev/null || true
        echo "   📁 Untracked: $dir"
    fi
done

# Find and untrack .pyc files
find . -name "*.pyc" -type f | while read file; do
    if [ -f "$file" ]; then
        git rm --cached "$file" 2>/dev/null || true
        echo "   📄 Untracked: $file"
    fi
done

echo "📊 Checking repository size before cleanup..."
du -sh .git 2>/dev/null || echo "Could not determine .git size"

echo "🧹 Running git garbage collection..."
git gc --aggressive --prune=now

echo "📊 Repository size after cleanup:"
du -sh .git 2>/dev/null || echo "Could not determine .git size"

echo "✅ Cleanup complete!"
echo "📋 Current git status:"
git status --porcelain
