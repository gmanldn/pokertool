# PokerTool Quick Reference Guide

Fast command reference for common development tasks.

## 🚀 Getting Started

```bash
# First time setup
python start.py --setup-only

# Start application
python start.py
# or
python restart.py

# Access
http://localhost:3000      # Frontend
http://localhost:5001/docs # API docs
```

## 🔄 Application Control

```bash
# Restart (clean)
python restart.py

# Restart with GUI
python restart.py --gui

# Stop only (no restart)
python restart.py --kill-only

# Kill stuck processes
python scripts/kill.py
```

## 🧪 Testing

```bash
# All tests
python test.py

# Quick tests (skip slow)
python test.py --quick

# Specific test file
pytest tests/test_api.py -v

# Specific test function
pytest tests/test_api.py::test_health_endpoint -v

# Skip architecture graph rebuild
python test.py --no-graph

# With coverage report
python test.py --coverage
pytest --cov=src --cov-report=html tests/

# By marker
pytest -m "not slow" -v
pytest -m "not scraper" -v

# Watch mode (auto-rerun)
pytest-watch

# Parallel execution
pytest -n auto tests/
```

## 🎨 Code Quality

```bash
# Format code
black src/ tests/
black pokertool-frontend/src/

# Sort imports
isort src/ tests/

# Lint Python
pylint src/
flake8 src/

# Type check
mypy src/

# Security scan
bandit -r src/

# All quality checks
black --check src/ && isort --check src/ && pylint src/ && mypy src/
```

## 📦 Dependencies

```bash
# Install Python deps
pip install -r requirements.txt

# Install frontend deps
cd pokertool-frontend && npm install

# Update all deps
pip install -r requirements.txt --upgrade
cd pokertool-frontend && npm update

# Check for security issues
safety check
npm audit

# Fix npm issues
npm audit fix
```

## 🔍 Debugging

```bash
# Python debugger
python -m pdb start.py

# Add breakpoint in code:
import ipdb; ipdb.set_trace()

# View logs
tail -f logs/pokertool_master.log
tail -f logs/errors-and-warnings.log

# Error summary
./scripts/error-summary.sh

# Monitor errors in real-time
./scripts/monitor-errors.sh

# Check running processes
lsof -i :5001
lsof -i :3000
ps aux | grep python | grep pokertool
```

## 🗄️ Database

```bash
# Reset database
rm data/pokertool.db
python -c "from pokertool.database import init_db; init_db()"

# Check database stats
curl http://localhost:5001/api/database/stats

# Backup database
cp data/pokertool.db data/pokertool_backup_$(date +%Y%m%d).db

# Run migrations (if using Alembic)
alembic upgrade head
alembic downgrade -1
```

## 🌐 API Testing

```bash
# Health check
curl http://localhost:5001/health

# System health
curl http://localhost:5001/api/system/health | python -m json.tool

# Hand analysis
curl -X POST http://localhost:5001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"hole_cards": ["As", "Kh"], "board": [], "position": "BTN"}'

# Get database stats
curl http://localhost:5001/api/database/stats

# WebSocket test (requires wscat)
wscat -c ws://localhost:5001/ws
```

## 🔧 Frontend Development

```bash
# Start dev server
cd pokertool-frontend && npm start

# Build production
cd pokertool-frontend && npm run build

# Type check
cd pokertool-frontend && npm run type-check

# Lint
cd pokertool-frontend && npm run lint

# Fix lint issues
cd pokertool-frontend && npm run lint:fix

# Run tests
cd pokertool-frontend && npm test

# Update packages
cd pokertool-frontend && npm update
```

## 📊 Performance & Monitoring

```bash
# Profile Python code
python -m cProfile -o profile.stats start.py
# View with: python -m pstats profile.stats

# Memory profiling
python -m memory_profiler start.py

# System metrics
python scripts/analyze_telemetry.py

# Learning stats
python scripts/show_learning_stats.py
```

## 🎮 Screen Scraping

```bash
# Test scraper
python -m pokertool scrape

# Debug scraper
python scripts/diagnose_betfair_scraper.py

# Fix Betfair detection
python scripts/fix_betfair_detection.py

# Analyze video frames
python scripts/analyze_video.py --input video.mp4

# Extract frames
python scripts/extract_frames.py --input video.mp4 --output frames/
```

## 🔒 Security

```bash
# Security scan
bandit -r src/

# Check dependencies
safety check
pip-audit

# Frontend audit
cd pokertool-frontend && npm audit
```

## 📝 Git Workflows

```bash
# Create feature branch
git checkout develop
git pull
git checkout -b feature/my-feature

# Update branch with develop
git fetch origin
git rebase origin/develop

# Interactive rebase (clean commits)
git rebase -i HEAD~5

# Amend last commit
git add .
git commit --amend --no-edit

# Stash changes
git stash
git stash pop

# View diff
git diff
git diff --staged

# Commit
git add -A
git commit -m "feat: add feature"

# Push
git push origin feature/my-feature

# Delete branch after merge
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

## 🐛 Troubleshooting

```bash
# Port already in use
lsof -ti:5001 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Clean restart
python restart.py --kill-only
python restart.py

# Check syntax
./scripts/check_syntax.sh

# Validate structure
python tests/verify_structure.py

# Fix OpenCV issues (macOS)
./scripts/fix_opencv.sh
```

## 🚢 Deployment

```bash
# Build for production
cd pokertool-frontend && npm run build

# Create release
python scripts/create_release.py

# Generate changelog
python scripts/generate_changelog.py

# Publish (CI/CD)
git push origin main --tags
```

## 📚 Documentation

```bash
# Generate API docs
# (Automatic at http://localhost:5001/docs)

# Update architecture graph
python test.py  # Rebuilds graph automatically

# Check markdown
markdownlint docs/

# Spell check
codespell docs/ src/
```

## 🔢 Version Management

```bash
# Check current version
cat VERSION

# Bump version
echo "v1.2.3" > VERSION

# Tag release
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

## 🎯 Common Tasks Reference

### Fix Failing Tests

```bash
# 1. Identify failing test
pytest tests/ -v --tb=short

# 2. Run specific test with output
pytest tests/test_x.py::test_y -v -s

# 3. Debug with breakpoint
# Add: import ipdb; ipdb.set_trace()
pytest tests/test_x.py::test_y -v -s

# 4. Fix and verify
pytest tests/test_x.py::test_y -v
```

### Add New Feature

```bash
# 1. Create branch
git checkout -b feature/new-feature

# 2. Write test first (TDD)
# Edit: tests/test_new_feature.py

# 3. Implement feature
# Edit: src/pokertool/new_feature.py

# 4. Test
pytest tests/test_new_feature.py -v

# 5. Document
# Edit: docs/FEATURES.md

# 6. Commit and PR
git add -A
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### Fix Production Bug

```bash
# 1. Create hotfix branch
git checkout main
git checkout -b hotfix/bug-name

# 2. Reproduce bug
pytest tests/test_bug.py -v

# 3. Fix
# Edit source file

# 4. Verify fix
pytest tests/test_bug.py -v

# 5. Deploy
git commit -m "fix: resolve bug"
git checkout main
git merge hotfix/bug-name
git tag -a v1.2.4 -m "Hotfix v1.2.4"
git push origin main --tags
```

### Update Dependencies

```bash
# 1. Update requirements
# Edit: requirements.txt

# 2. Install
pip install -r requirements.txt

# 3. Test
python test.py

# 4. Check for conflicts
safety check
pip check

# 5. Commit
git commit -m "chore: update dependencies"
```

## 🌐 Environment-Specific

### macOS

```bash
# Install system dependencies
brew install python@3.12 tesseract node

# Fix permissions
sudo chown -R $(whoami) /usr/local

# Set Tesseract path
export TESSERACT_CMD=/opt/homebrew/bin/tesseract
```

### Linux

```bash
# Install system dependencies
sudo apt install python3-pip python3-venv tesseract-ocr nodejs npm

# Virtual display (headless)
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

### Windows

```powershell
# Install dependencies
choco install python nodejs tesseract

# Set Tesseract path
$env:TESSERACT_CMD="C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## ⚡ Performance Tips

```bash
# Use fast test markers
pytest -m "not slow" tests/

# Parallel test execution
pytest -n auto tests/

# Skip architecture rebuild
python test.py --no-graph

# Use caching
export SCRAPER_CACHE_SIZE=2000
export GTO_CACHE_SIZE=20000
```

## 🆘 Emergency Commands

```bash
# Everything broken - nuclear reset
python restart.py --kill-only
rm -rf .venv
rm -rf pokertool-frontend/node_modules
python start.py --setup-only
python restart.py

# Database corrupted
rm data/pokertool.db
python -c "from pokertool.database import init_db; init_db()"

# Tests won't run
rm -rf .pytest_cache
pip install -r requirements.txt --force-reinstall

# Git messed up
git fetch origin
git reset --hard origin/develop
```

## 📖 Documentation Links

- [Full Documentation](README.md)
- [Development Workflow](DEVELOPMENT_WORKFLOW.md)
- [Environment Variables](ENVIRONMENT_VARIABLES.md)
- [Testing Guide](TESTING.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Contributing](../CONTRIBUTING.md)

## 💡 Pro Tips

- Use `python restart.py` after pulling updates
- Run `python test.py --quick` before committing
- Check logs in `logs/` when debugging
- Use `--help` flag on any script for options
- Keep `develop` branch updated daily
- Tag teammates in PRs for faster review
- Document as you code (save time later)

## 🎓 Learning Resources

```bash
# Run smoke tests to learn system
python scripts/run_smoke_tests.py

# Explore with examples
python examples/api_client_example.py

# See learning system stats
python scripts/show_learning_stats.py