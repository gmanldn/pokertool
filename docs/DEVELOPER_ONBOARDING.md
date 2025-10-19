# Developer Onboarding Checklist

Welcome to PokerTool! This checklist will guide you through your first week.

## Day 1: Environment Setup

### Morning: Get Access

- [ ] GitHub account added to repository
- [ ] Slack/Discord workspace invited
- [ ] Development machine setup (Python 3.10-3.13)
- [ ] Git configured with SSH keys
- [ ] IDE installed (VS Code or PyCharm recommended)

### Afternoon: Clone and Run

```bash
# Clone repository
git clone git@github.com:gmanldn/pokertool.git
cd pokertool

# Run setup
python start.py --setup-only

# Verify installation
python test.py --quick

# Start app
python restart.py
```

**Verify**: App runs at http://localhost:3000

- [ ] Repository cloned successfully
- [ ] Dependencies installed without errors
- [ ] Tests pass (allow some failures on first run)
- [ ] App starts and loads frontend
- [ ] Backend health check passes: http://localhost:5001/health

## Day 2: Understand the Codebase

### Read Documentation

- [ ] [README.md](../README.md) - Project overview
- [ ] [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [ ] [FEATURES.md](../FEATURES.md) - Feature list
- [ ] [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) - Dev process
- [ ] [CODE_REVIEW_CHECKLIST.md](CODE_REVIEW_CHECKLIST.md) - Standards

### Explore Code Structure

```
pokertool/
├── src/pokertool/          # Backend Python code
│   ├── api.py             # FastAPI endpoints
│   ├── database.py        # Database layer
│   ├── gto_solver.py      # Game theory solver
│   └── modules/           # Screen scraping, ML
├── pokertool-frontend/    # React frontend
│   ├── src/components/    # UI components
│   └── src/store/         # Redux state
├── tests/                 # Test suites
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

- [ ] Understand directory structure
- [ ] Identify key modules for your team
- [ ] Read code in your focus area
- [ ] Review recent PRs to see coding style

### Run Your First Test

```bash
# Run a simple test
pytest tests/test_poker.py::test_hand_evaluation -v

# Run with coverage
pytest --cov=src/pokertool tests/test_poker.py
```

- [ ] Tests run successfully
- [ ] Understand test structure
- [ ] Can add a simple test

## Day 3: First Contribution

### Pick a Good First Issue

- Look for labels: `good-first-issue`, `documentation`, `easy`
- Examples:
  - Fix typo in documentation
  - Add missing type hints
  - Improve error messages
  - Add unit test

### Make Your First PR

```bash
# Create branch
git checkout -b fix/your-first-fix

# Make changes
# (edit files)

# Test
python test.py

# Commit
git add -A
git commit -m "docs: fix typo in README"

# Push and create PR
git push origin fix/your-first-fix
```

- [ ] Issue selected and assigned
- [ ] Branch created
- [ ] Changes made
- [ ] Tests pass
- [ ] PR created
- [ ] PR reviewed and merged

### Celebrate! 🎉

You've made your first contribution!

## Day 4-5: Deep Dive

### Choose Your Focus Area

**Backend**:
- API endpoints (`src/pokertool/api.py`)
- Database models (`src/pokertool/database.py`)
- GTO solver (`src/pokertool/gto_solver.py`)

**Frontend**:
- React components (`pokertool-frontend/src/components/`)
- State management (`pokertool-frontend/src/store/`)
- WebSocket integration

**ML/Scraping**:
- Screen scraper (`src/pokertool/modules/poker_screen_scraper_betfair.py`)
- Opponent modeling (`src/pokertool/ml_opponent_modeling.py`)
- Active learning (`src/pokertool/active_learning.py`)

- [ ] Focus area chosen
- [ ] Read all code in focus area
- [ ] Understand dependencies
- [ ] Identify improvement opportunities

### Pair Programming Session

- [ ] Schedule with senior developer
- [ ] Walk through complex code together
- [ ] Ask questions
- [ ] Learn debugging techniques

### Write a Test

```python
# Add test to tests/test_your_area.py
def test_new_functionality():
    """Test description."""
    # Arrange
    input_data = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

- [ ] Test written for your focus area
- [ ] Test passes
- [ ] PR created for test
- [ ] Understanding of testing improved

## Week 2: Regular Contributor

### Take on a Real Task

- Pick from current sprint
- Estimated effort: 2-5 days
- Has clear acceptance criteria
- Within your focus area

### Development Cycle

1. **Plan**: Break down task into subtasks
2. **Design**: Sketch solution approach
3. **Implement**: Write code with tests
4. **Review**: Self-review using checklist
5. **Submit**: Create PR
6. **Iterate**: Address review comments

- [ ] Task completed
- [ ] Code reviewed
- [ ] PR merged
- [ ] Feature deployed

### Shadow a Code Review

- [ ] Observe senior developer reviewing PR
- [ ] Learn what to look for
- [ ] Ask questions about decisions
- [ ] Practice on old PRs

## Month 1: Team Integration

### Knowledge Areas

- [ ] Can run app locally without help
- [ ] Understand architecture and data flow
- [ ] Know where to find documentation
- [ ] Familiar with test suite
- [ ] Comfortable with git workflow
- [ ] Can create PRs independently
- [ ] Understand code review process

### Technical Skills

- [ ] Written unit tests
- [ ] Written integration tests
- [ ] Debugged production issue
- [ ] Optimized slow query/function
- [ ] Reviewed someone else's PR
- [ ] Deployed code to production

### Team Skills

- [ ] Know who to ask for what
- [ ] Participated in standup
- [ ] Attended sprint planning
- [ ] Presented work in demo
- [ ] Contributed to retrospective

## Ongoing: Continuous Learning

### Stay Updated

- [ ] Subscribe to repository notifications
- [ ] Read weekly changelogs
- [ ] Review merged PRs in your area
- [ ] Follow poker AI research
- [ ] Learn from production incidents

### Share Knowledge

- [ ] Write documentation
- [ ] Answer questions in Slack/Discord
- [ ] Mentor new developers
- [ ] Present at team meetings
- [ ] Contribute to tooling

## Resources

### Essential Reading

1. **Python**:
   - [PEP 8 Style Guide](https://pep8.org/)
   - [Type Hints Guide](https://docs.python.org/3/library/typing.html)
   - [Pytest Documentation](https://docs.pytest.org/)

2. **React**:
   - [React Docs](https://react.dev/)
   - [TypeScript Handbook](https://www.typescriptlang.org/docs/)
   - [Redux Toolkit](https://redux-toolkit.js.org/)

3. **Poker**:
   - [Poker Math Guide](https://www.pokerstrategy.com/strategy/various-poker/basic-odds-and-outs/)
   - [GTO Concepts](https://upswingpoker.com/gto-poker-meaning/)

### Tools to Master

- [ ] Git (branch, rebase, cherry-pick)
- [ ] Pytest (fixtures, markers, coverage)
- [ ] FastAPI (endpoints, validation, WebSocket)
- [ ] React Hooks (useState, useEffect, custom hooks)
- [ ] Redux (actions, reducers, selectors)

### Commands to Memorize

```bash
# Daily
python restart.py           # Restart app
python test.py             # Run tests
black src/ && isort src/   # Format code

# Git
git checkout -b feature/x  # New branch
git rebase origin/develop  # Update branch
git push origin feature/x  # Push changes

# Testing
pytest tests/test_x.py -v  # Run specific test
pytest -k "test_name"      # Run by name
pytest --cov=src tests/    # With coverage

# Debug
python -m pdb script.py    # Python debugger
import ipdb; ipdb.set_trace()  # Breakpoint
```

## Getting Help

### When Stuck

1. **Check documentation** (docs/ folder)
2. **Search codebase** for similar examples
3. **Ask in Slack/Discord** with context
4. **Pair with teammate** if blocked >2 hours
5. **Create GitHub issue** for bugs

### Who to Ask

- **Architecture questions**: @senior-architect
- **Python/Backend**: @backend-lead
- **React/Frontend**: @frontend-lead
- **ML/Scraping**: @ml-engineer
- **DevOps/Deploy**: @devops-lead
- **Poker logic**: @poker-expert

## Checklist Summary

### Week 1
- [x] Environment setup
- [ ] First contribution merged
- [ ] Focus area chosen
- [ ] Test written

### Week 2
- [ ] Real task completed
- [ ] Code review shadowed
- [ ] PR reviewed

### Month 1
- [ ] 5+ PRs merged
- [ ] Reviewed 3+ PRs
- [ ] Deployed to production
- [ ] Team integration complete

## Welcome to the Team! 🎉

You're now ready to contribute effectively to PokerTool. Remember:

- **Ask questions** - No question is too small
- **Read code** - Best way to learn the codebase
- **Test everything** - Good tests prevent bugs
- **Document as you go** - Help future developers
- **Have fun** - Building cool poker tech!

If you have suggestions to improve this onboarding, please update this document!