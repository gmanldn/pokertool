# Mutation Testing Guide

**Author:** PokerTool Team
**Created:** 2025-10-22
**Version:** 1.0.0

## Overview

Mutation testing is an advanced testing technique that evaluates the quality of test suites by introducing small changes (mutations) to the code and verifying that tests catch these changes. If tests fail after a mutation, the mutation is "killed" (good). If tests still pass, the mutation "survived" (bad - indicates weak test coverage).

PokerTool uses **mutmut** for Python mutation testing, targeting core modules with a goal of 80%+ mutation score.

## What is Mutation Testing?

### Example

**Original Code:**
```python
def calculate_pot_odds(bet_to_call, pot_size):
    if pot_size <= 0:
        return 0.0
    return bet_to_call / (pot_size + bet_to_call)
```

**Mutation #1:** Change `<=` to `<`
```python
if pot_size < 0:  # Bug introduced!
```
- **Expected:** Test should fail (pot_size=0 now returns wrong value)
- **If test passes:** Mutation survived - weak test coverage!

**Mutation #2:** Change `/` to `*`
```python
return bet_to_call * (pot_size + bet_to_call)  # Bug!
```
- **Expected:** Test should fail (obviously wrong calculation)
- **If test passes:** Critical gap in test coverage!

### Why Mutation Testing?

- **Identifies weak tests**: 100% code coverage doesn't mean tests are effective
- **Improves test quality**: Forces you to write assertions that actually verify correctness
- **Catches edge cases**: Reveals missing boundary tests
- **Validates critical paths**: Ensures important logic is properly tested

## Targeted Modules

Mutation testing focuses on critical core modules:

| Module | Path | Lines | Priority | Target Score |
|--------|------|-------|----------|--------------|
| **Core Engine** | `src/pokertool/core.py` | ~1000 | P0 | 85%+ |
| **Database** | `src/pokertool/database.py` | ~800 | P0 | 80%+ |
| **Equity Calculator** | `src/pokertool/equity_calculator.py` | ~400 | P1 | 85%+ |
| **GTO Calculator** | `src/pokertool/gto_calculator.py` | ~435 | P1 | 80%+ |
| **RBAC** | `src/pokertool/rbac.py` | ~300 | P1 | 85%+ |
| **Input Validator** | `src/pokertool/input_validator.py` | ~407 | P1 | 85%+ |

**Why these modules?**
- Security-critical (RBAC, Input Validator)
- Business logic (Core Engine, Calculators)
- Data integrity (Database)
- High test coverage already exists (good baseline)

## Installation

### Prerequisites

1. Install mutmut:
```bash
pip install mutmut>=2.4.0
```

Or from requirements.txt:
```bash
pip install -r requirements.txt
```

2. Ensure tests pass before running mutation tests:
```bash
pytest tests/
```

## Running Mutation Tests

### Quick Start

**Run all configured modules (10-30 minutes):**
```bash
make mutation-test
```

**Run core.py only (faster, 3-5 minutes):**
```bash
make mutation-test-core
```

**View results:**
```bash
mutmut results
mutmut show
```

### Command Reference

| Command | Description | Duration |
|---------|-------------|----------|
| `make mutation-test` | Run all modules | 10-30 min |
| `make mutation-test-core` | Run core.py only | 3-5 min |
| `make mutation-test-html` | Generate HTML report | 10 sec |
| `make mutation-test-reset` | Clear cache | Instant |

### Manual Usage

**Run mutmut directly:**
```bash
mutmut run --paths-to-mutate=src/pokertool/core.py
```

**Show summary:**
```bash
mutmut results
```

**Show all survived mutations:**
```bash
mutmut show
```

**Show specific mutation:**
```bash
mutmut show 1
```

**Apply a mutation (for debugging):**
```bash
mutmut apply 1
```

**Generate HTML report:**
```bash
mutmut html
open htmlcov/index.html
```

## Understanding Results

### Mutation Status

| Status | Meaning | Good/Bad |
|--------|---------|----------|
| **Killed** | Test failed after mutation | ✅ Good - test caught the bug |
| **Survived** | Test passed after mutation | ❌ Bad - test missed the bug |
| **Timeout** | Test took too long | ⚠️ Investigate |
| **Suspicious** | Coverage changed unexpectedly | ⚠️ Investigate |

### Example Output

```
mutmut run --paths-to-mutate=src/pokertool/core.py

- KILLED: 87
- SURVIVED: 12
- TIMEOUT: 1
- SUSPICIOUS: 0
- TOTAL: 100

Mutation score: 87.0%
```

**Interpretation:**
- **87 killed**: Good! Tests caught 87 out of 100 mutations
- **12 survived**: Need to add/improve 12 tests
- **1 timeout**: Likely infinite loop mutation, verify test setup
- **Score 87%**: Above 80% target, but can improve

### Survived Mutations

When mutations survive, you need to add tests. Example:

**Survived Mutation:**
```python
# Original
if player_count < 2:
    return False

# Mutated (survived)
if player_count < 1:  # Should fail, but didn't!
    return False
```

**Fix:** Add edge case test:
```python
def test_player_count_boundary():
    assert validate_game(player_count=1) == False  # Now catches the mutation!
    assert validate_game(player_count=2) == True
```

## Configuration

### .mutmut_config.py

```python
# Modules to mutate
paths_to_mutate = [
    'src/pokertool/core.py',
    'src/pokertool/database.py',
    # ...
]

# Modules to skip
paths_to_exclude = [
    'tests/',
    'scripts/',
]

# Test runner
runner = 'python -m pytest -x --tb=short'

# Custom mutation operators
dict_synonyms = {
    'True': 'False',
    '==': '!=',
    '<': '>=',
    # ...
}
```

## Mutation Types

mutmut introduces these mutations:

### 1. Operator Mutations
```python
# Comparison operators
< → >=
<= → >
> → <=
>= → <
== → !=
!= → ==

# Boolean operators
and → or
or → and
not x → x
```

### 2. Constant Mutations
```python
# Numbers
0 → 1
1 → 0
n → n + 1
n → n - 1

# Booleans
True → False
False → True

# Strings
"text" → "XXtextXX"
```

### 3. Function Call Mutations
```python
# Remove function calls
some_function() → None

# Change return values
return x → return None
```

## Best Practices

### 1. Start Small
Begin with one module, then expand:
```bash
# Step 1: Test core.py only
make mutation-test-core

# Step 2: Fix survived mutations

# Step 3: Add more modules
make mutation-test
```

### 2. Fix Survived Mutations Iteratively

**Workflow:**
1. Run mutation tests
2. Identify 5-10 survived mutations
3. Write tests to kill them
4. Re-run mutation tests
5. Repeat until score > 80%

### 3. Focus on Critical Paths

Prioritize mutation testing for:
- **Security**: Authentication, authorization, input validation
- **Money**: Pot calculations, chip transfers
- **Logic**: Hand evaluation, position calculation
- **Data**: Database operations, state management

### 4. Use Timeouts

Set reasonable timeouts to avoid infinite loops:
```python
# In pytest.ini
[pytest]
timeout = 10
```

### 5. Parallelize (Advanced)

For faster runs, use multiple workers:
```bash
mutmut run --paths-to-mutate=src/pokertool/core.py --use-coverage --runner="pytest -x" --workers=4
```

## Troubleshooting

### Problem: All mutations survive

**Cause:** Tests don't run or don't have assertions

**Solution:**
```bash
# Verify tests work
pytest tests/test_core.py -v

# Check test actually asserts
grep -r "assert" tests/test_core.py
```

### Problem: All mutations timeout

**Cause:** Infinite loop mutations

**Solution:**
1. Add pytest timeout plugin:
```bash
pip install pytest-timeout
```

2. Set timeout in pytest.ini:
```ini
[pytest]
timeout = 10
```

### Problem: Mutation score too low (<60%)

**Cause:** Missing tests

**Solution:**
1. Identify weakest areas:
```bash
mutmut show | grep "SURVIVED"
```

2. Add tests for survived mutations

3. Focus on edge cases:
   - Boundary values (0, 1, -1, None)
   - Empty collections
   - Invalid inputs

### Problem: Mutations in wrong files

**Cause:** Configuration issue

**Solution:**
Update `.mutmut_config.py`:
```python
paths_to_exclude = [
    'tests/',
    'scripts/',
    'src/pokertool/modules/',  # Exclude screen scraping
]
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/ci.yml`:

```yaml
- name: Install Dependencies
  run: pip install -r requirements.txt

- name: Run Unit Tests
  run: pytest tests/ --cov

- name: Run Mutation Tests (Core Module)
  run: |
    mutmut run --paths-to-mutate=src/pokertool/core.py --use-coverage
    MUTATION_SCORE=$(mutmut results | grep "Mutation score" | awk '{print $3}' | tr -d '%')
    if (( $(echo "$MUTATION_SCORE < 80" | bc -l) )); then
      echo "❌ Mutation score $MUTATION_SCORE% is below 80%"
      exit 1
    fi
    echo "✅ Mutation score $MUTATION_SCORE%"
  continue-on-error: true  # Don't fail CI initially, just warn
```

## Targets and Milestones

### Phase 1 (Current)
- ✅ Set up mutmut
- ✅ Configure core modules
- ✅ Add Makefile targets
- 🔄 Establish baseline scores

### Phase 2 (Next Month)
- 🎯 Achieve 80%+ on core.py
- 🎯 Achieve 80%+ on database.py
- 🎯 Achieve 85%+ on equity_calculator.py

### Phase 3 (2 Months)
- 🎯 Add CI/CD integration
- 🎯 Expand to all critical modules
- 🎯 Maintain 85%+ average score

## Metrics Dashboard

Track mutation scores over time:

| Module | Baseline | Target | Current | Status |
|--------|----------|--------|---------|--------|
| core.py | TBD | 85% | TBD | 🔄 In Progress |
| database.py | TBD | 80% | TBD | ⏳ Pending |
| equity_calculator.py | TBD | 85% | TBD | ⏳ Pending |
| gto_calculator.py | TBD | 80% | TBD | ⏳ Pending |
| rbac.py | TBD | 85% | TBD | ⏳ Pending |
| input_validator.py | TBD | 85% | TBD | ⏳ Pending |

## Resources

- [mutmut Documentation](https://mutmut.readthedocs.io/)
- [Mutation Testing Explained](https://en.wikipedia.org/wiki/Mutation_testing)
- [PIT (Java Mutation Testing)](https://pitest.org/)
- [Stryker (JavaScript Mutation Testing)](https://stryker-mutator.io/)

## FAQ

**Q: How long does mutation testing take?**
A: 3-5 minutes per 100 lines of code. Use `make mutation-test-core` for faster iteration.

**Q: Should I aim for 100% mutation score?**
A: No, 80-85% is excellent. Some mutations are impossible to kill (e.g., logging statements).

**Q: Can I skip certain mutations?**
A: Yes, use `.mutmut_config.py` to exclude files or add custom logic in `pre_mutation()`.

**Q: Does mutation testing replace unit tests?**
A: No, it complements them. Mutation testing validates that your tests are effective.

**Q: What if a mutation survives but test is correct?**
A: It's an "equivalent mutant" - the mutation doesn't change behavior. Mark it as skipped.

---

**Last Updated:** 2025-10-22
**Maintained By:** PokerTool Team
