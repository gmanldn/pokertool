# Development Workflow

Complete guide for contributing to PokerTool development.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Branch Strategy](#branch-strategy)
3. [Development Process](#development-process)
4. [Testing Workflow](#testing-workflow)
5. [Code Review](#code-review)
6. [Deployment](#deployment)
7. [Tools & Commands](#tools--commands)

## Getting Started

### Initial Setup

```bash
# Clone repository
git clone https://github.com/gmanldn/pokertool.git
cd pokertool

# Install dependencies
python start.py --setup-only

# Run tests to verify setup
python test.py
```

### IDE Configuration

**VS Code** (recommended):
- Install Python and ESLint extensions
- Settings included in `.vscode/settings.json`
- Use provided launch configurations

**PyCharm**:
- Configure Python interpreter to `.venv/bin/python`
- Enable pytest as test runner
- Configure Black as code formatter

## Branch Strategy

### Branch Types

```
main          - Production-ready code (protected)
develop       - Integration branch (default)
feature/*     - New features
bugfix/*      - Bug fixes
hotfix/*      - Urgent production fixes
release/*     - Release preparation
```

### Branch Naming

```bash
# Features
feature/add-tournament-support
feature/improve-ocr-accuracy

# Bug fixes
bugfix/fix-pot-calculation
bugfix/websocket-reconnect

# Hotfixes
hotfix/critical-security-patch
hotfix/crash-on-startup
```

### Creating a Feature Branch

```bash
# Update develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on your feature...

# Keep branch updated
git fetch origin
git rebase origin/develop
```

## Development Process

### 1. Pick a Task

- Check GitHub Issues or TODO.md
- Assign yourself to prevent duplication
- Understand requirements fully

### 2. Create Branch

```bash
git checkout develop
git pull
git checkout -b feature/task-name
```

### 3. Develop

#### Write Code

- Follow [Code Review Checklist](CODE_REVIEW_CHECKLIST.md)
- Add type hints (Python) and TypeScript types
- Write docstrings for all functions
- Keep commits small and focused

#### Run Locally

```bash
# Start app
python restart.py

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:5001/docs
```

#### Test Continuously

```bash
# Run affected tests
pytest tests/test_your_feature.py -v

# Run all tests
python test.py

# Check coverage
pytest --cov=src tests/
```

### 4. Commit Changes

#### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:

```bash
# Good
git commit -m "feat(scraper): Add multi-table detection support

Implements table segmentation using adaptive UI detection.
Supports up to 6 concurrent tables with automatic focus switching.

Closes #123"

# Bad
git commit -m "fixed stuff"
```

### 5. Push and Create PR

```bash
# Push branch
git push origin feature/your-feature-name

# Create PR via GitHub UI
# Template will auto-fill
```

## Testing Workflow

### Test-Driven Development (TDD)

```python
# 1. Write failing test
def test_calculate_pot_size():
    result = calculate_pot_size([10, 20, 30])
    assert result == 60

# 2. Run test (should fail)
pytest tests/test_poker.py::test_calculate_pot_size

# 3. Implement function
def calculate_pot_size(bets):
    return sum(bets)

# 4. Run test (should pass)
pytest tests/test_poker.py::test_calculate_pot_size

# 5. Refactor if needed
```

### Test Pyramid

```
         E2E Tests (few)
       /               \
    Integration Tests
   /                     \
 Unit Tests (many)
```

- **Unit Tests**: Test individual functions (90%)
- **Integration Tests**: Test component interactions (9%)
- **E2E Tests**: Test full user workflows (1%)

### Running Tests

```bash
# All tests
python test.py

# Specific file
pytest tests/test_api.py -v

# Specific test
pytest tests/test_api.py::test_health_endpoint -v

# By marker
pytest -m "not slow" -v

# With coverage
pytest --cov=src --cov-report=html tests/

# Watch mode (re-run on changes)
pytest-watch
```

### Test Coverage Requirements

- **New code**: Must have >90% coverage
- **Critical paths**: 100% coverage required
- **Edge cases**: All edge cases tested
- **Error paths**: All error scenarios tested

## Code Review

### Creating a Pull Request

1. **Update branch**:
   ```bash
   git fetch origin
   git rebase origin/develop
   ```

2. **Run checklist**:
   ```bash
   # Format code
   black src/ tests/
   isort src/ tests/
   
   # Lint
   pylint src/
   mypy src/
   
   # Test
   python test.py
   ```

3. **Create PR**:
   - Use GitHub UI
   - Fill out PR template completely
   - Link related issues
   - Add screenshots/videos if UI changes
   - Request reviewers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] No new warnings

## Screenshots
(if applicable)
```

### Review Response

- **Address all comments** - even minor ones
- **Explain decisions** - if you disagree, discuss
- **Update PR** - push new commits
- **Mark resolved** - when addressed
- **Re-request review** - when ready

## Deployment

### Pre-Deployment

```bash
# Ensure all tests pass
python test.py

# Build frontend
cd pokertool-frontend
npm run build

# Version bump (if release)
# Update VERSION file
echo "v1.2.3" > VERSION

# Update CHANGELOG.md
```

### Deployment Steps

#### To Development

```bash
# Merge to develop
git checkout develop
git merge feature/your-feature
git push origin develop

# Auto-deploys via GitHub Actions
```

#### To Production

```bash
# Create release branch
git checkout -b release/v1.2.3 develop

# Final testing
python test.py

# Merge to main
git checkout main
git merge release/v1.2.3
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge release/v1.2.3
git push origin develop
```

### Post-Deployment

- Monitor logs for errors
- Check health dashboard
- Verify key features working
- Update stakeholders

## Tools & Commands

### Daily Commands

```bash
# Start development server
python restart.py

# Run tests
python test.py --quick

# Format code
black src/ && isort src/

# Check types
mypy src/

# Update dependencies
pip install -r requirements.txt --upgrade
```

### Code Quality

```bash
# Run all linters
black --check src/
pylint src/
mypy src/
bandit -r src/

# Auto-fix issues
black src/
isort src/
autoflake --remove-all-unused-imports -i -r src/
```

### Git Workflows

```bash
# Sync with develop
git fetch origin
git rebase origin/develop

# Interactive rebase (clean commits)
git rebase -i HEAD~5

# Stash changes
git stash
git stash pop

# Cherry-pick commit
git cherry-pick <commit-hash>

# Undo last commit (keep changes)
git reset --soft HEAD~1
```

### Database

```bash
# Create migration
alembic revision -m "Add user table"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Reset database
rm data/pokertool.db
python -c "from pokertool.database import init_db; init_db()"
```

## Best Practices

### DO

✅ Write tests first (TDD)
✅ Keep commits small and focused
✅ Update documentation
✅ Add type hints
✅ Run tests before pushing
✅ Review your own code first
✅ Ask for help when stuck

### DON'T

❌ Commit directly to main/develop
❌ Push broken code
❌ Skip tests
❌ Ignore linter warnings
❌ Leave TODO comments without issues
❌ Mix refactoring with features
❌ Force push to shared branches

## Troubleshooting

### Common Issues

**"Tests fail locally but pass in CI"**
- Check Python version matches CI
- Clear pytest cache: `rm -rf .pytest_cache`
- Check environment variables

**"Import errors after updating"**
- Reinstall dependencies: `pip install -r requirements.txt`
- Restart app: `python restart.py`

**"Merge conflicts"**
- Fetch latest: `git fetch origin`
- Rebase: `git rebase origin/develop`
- Resolve conflicts manually
- Continue: `git rebase --continue`

**"Port already in use"**
- Kill processes: `python restart.py --kill-only`
- Or manually: `lsof -ti:5001 | xargs kill -9`

## Resources

- [Contributing Guide](../CONTRIBUTING.md)
- [Code Review Checklist](CODE_REVIEW_CHECKLIST.md)
- [Environment Variables](ENVIRONMENT_VARIABLES.md)
- [Testing Guide](TESTING.md)
- [Architecture Docs](README.md)

## Getting Help

- **GitHub Issues**: For bugs and features
- **Discussions**: For questions
- **Code Review**: Tag specific developers
- **Documentation**: Check docs/ folder first

## Quick Reference Card

```bash
# Daily workflow
git checkout develop && git pull
git checkout -b feature/my-feature
# ... make changes ...
black src/ && pytest tests/
git add -A && git commit -m "feat: my feature"
git push origin feature/my-feature
# Create PR on GitHub

# Testing
python test.py              # All tests
pytest tests/test_x.py -v   # Specific file
pytest -m "not slow"        # Skip slow tests

# Quality
black src/ && isort src/    # Format
pylint src/ && mypy src/    # Lint + type check

# Running app
python restart.py           # Clean restart
python start.py             # Fresh start