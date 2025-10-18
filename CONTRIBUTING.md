# Contributing to PokerTool

Thank you for your interest in contributing to PokerTool! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Security](#security)

## Issue Management

- Create and update backlog entries via `python new_task.py`; direct edits to `docs/TODO.md` are not accepted.
- Every task must include a GUID, typed classification, lifecycle status, duplicate-guard context, and rich paragraphs for both the problem summary and AI-oriented remediation plan.
- Legacy backlog items were archived to `docs/TODO_ARCHIVE.md`; reference them for historical context only.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.11+ (3.13 recommended)
- Node.js 18+ and npm
- Git
- A code editor with EditorConfig support (VSCode, IntelliJ, etc.)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pokertool.git
   cd pokertool
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/anthropics/pokertool.git
   ```

## Development Setup

### Backend Setup

```bash
# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Frontend Setup

```bash
cd pokertool-frontend
npm install
cd ..
```

### Verify Setup

```bash
# Run tests
pytest

# Check code quality
black --check src/
flake8 src/
mypy src/

# Frontend tests
cd pokertool-frontend && npm test
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements
- `chore/` - Maintenance tasks

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style and patterns
- Add/update tests as needed
- Update documentation if needed

### 3. Run Quality Checks

```bash
# Format code
black src/
isort src/

# Run linters
flake8 src/
mypy src/

# Run tests
pytest --cov=src/pokertool

# Security check
bandit -r src/

# Frontend checks
cd pokertool-frontend
npm run lint
npm test
```

### 4. Commit Your Changes

Follow our commit message conventions (see below).

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Standards

### Python Code Style

- **Line Length**: 100 characters maximum
- **Formatting**: Use Black formatter
- **Import Sorting**: Use isort with Black profile
- **Type Hints**: Add type hints to all function signatures
- **Docstrings**: Google-style docstrings for all public APIs
- **Complexity**: Keep cyclomatic complexity < 10

Example:
```python
from typing import List, Optional

def analyze_hand(cards: List[str], position: str) -> Optional[dict]:
    """
    Analyze a poker hand and return recommendations.

    Args:
        cards: List of card strings (e.g., ["Ah", "Kd"])
        position: Player position (e.g., "BB", "BTN")

    Returns:
        Analysis dictionary or None if invalid input

    Raises:
        ValueError: If cards are invalid
    """
    # Implementation
    pass
```

### JavaScript/TypeScript Code Style

- **Line Length**: 100 characters maximum
- **Formatting**: Use Prettier
- **Style**: ESLint with recommended rules
- **Components**: Functional components with hooks
- **TypeScript**: Strict mode, no `any` types

### General Principles

- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **Single Responsibility**: One class/function, one purpose
- **Meaningful Names**: Use descriptive variable/function names

## Testing Guidelines

### Test Coverage Requirements

- **Minimum**: 80% coverage for new code
- **Target**: 95% coverage overall
- **Critical Paths**: 100% coverage required

### Writing Tests

#### Python Unit Tests (pytest)

```python
def test_hand_analysis_basic():
    """Test basic hand analysis functionality."""
    cards = ["Ah", "Kd"]
    result = analyze_hand(cards, "BB")

    assert result is not None
    assert "action" in result
    assert result["action"] in ["fold", "call", "raise"]
```

#### JavaScript Tests (Jest)

```javascript
describe('HandAnalyzer', () => {
  it('should analyze basic hands correctly', () => {
    const cards = ['Ah', 'Kd'];
    const result = analyzeHand(cards, 'BB');

    expect(result).toBeDefined();
    expect(result.action).toBeOneOf(['fold', 'call', 'raise']);
  });
});
```

### Test Organization

- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/system/` - System/E2E tests
- `tests/fixtures/` - Test fixtures and data

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/).

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```
feat(ml): Add opponent modeling with neural networks

Implement deep learning-based opponent modeling to predict
player tendencies based on historical actions.

- Added OpponentModel class with LSTM architecture
- Integrated with existing GTO solver
- Added comprehensive unit tests
- Updated documentation

Closes #123
```

```
fix(scraper): Handle edge case in card recognition

Fixed issue where card recognition failed for certain
table backgrounds.

Fixes #456
```

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with develop

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Automated CI checks must pass
2. At least one reviewer approval required
3. All conversations resolved
4. No merge conflicts
5. Branch up to date with base branch

### After Approval

- Squash commits if requested
- Maintainer will merge using "Squash and Merge"

## Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead, email security@pokertool.com with:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Security Best Practices

- Never commit sensitive data (API keys, passwords, etc.)
- Use environment variables for configuration
- Sanitize all user inputs
- Follow OWASP security guidelines
- Run security scans before submitting PR

## Questions or Need Help?

- Open a Discussion on GitHub
- Join our Discord community
- Check existing Issues and Discussions
- Read the documentation in `/docs`

## License

By contributing to PokerTool, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to PokerTool! Your efforts help make poker analysis better for everyone.
