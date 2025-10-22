# Test Database Seeding

This module provides database seeding utilities for creating consistent test data across different test scenarios.

## Quick Start

```python
from tests.fixtures.seeds import seed_database

# Seed with new user data (empty database)
db = seed_database(':memory:', scenario='new_user')

# Seed with veteran player data (10,000+ hands)
db = seed_database(':memory:', scenario='veteran_player')

# Seed with tournament player data
db = seed_database(':memory:', scenario='tournament_player')
```

## Available Scenarios

### `new_user`
Fresh user with no poker hands played yet.
- 0 hands
- No statistics
- Useful for testing first-time user experience

### `veteran_player`
Experienced player with 10,000+ hands and detailed statistics.
- 10,000 hands across multiple sites
- Various stake levels (NL10-NL100)
- Data spanning 6 months
- Realistic win rate (~0.05 BB/hand)
- Useful for testing analytics and reporting features

### `tournament_player`
Tournament specialist with MTT-specific data.
- 2,000 tournament hands
- 200 tournaments played
- Mix of MTT, SNG, Turbo, PKO
- ITM rate ~20%
- Various buy-in levels ($5-$100)
- Useful for testing tournament tracking features

### `cash_game_grinder` (TODO)
High-volume cash game player (100k+ hands).

### `mixed_player` (TODO)
Balanced player with both tournaments and cash games.

## Usage in Tests

### As a Fixture

```python
import pytest
from tests.fixtures.seeds import seed_database

@pytest.fixture
def seeded_db():
    """Provide a seeded database for tests."""
    return seed_database(':memory:', scenario='veteran_player')

def test_hand_analysis(seeded_db):
    """Test analyzing hands from seeded database."""
    assert seeded_db.get_total_hands() > 0
```

### Inline in Tests

```python
from tests.fixtures.seeds import seed_database

def test_new_user_onboarding():
    """Test onboarding flow for new users."""
    db = seed_database(':memory:', scenario='new_user')
    assert db.get_total_hands() == 0
    # Test onboarding...
```

### Multiple Scenarios

```python
import pytest
from tests.fixtures.seeds import seed_database

@pytest.mark.parametrize('scenario', ['new_user', 'veteran_player', 'tournament_player'])
def test_stats_calculation(scenario):
    """Test stats calculation for different player types."""
    db = seed_database(':memory:', scenario=scenario)
    # Run stats calculation...
```

## Clearing Data

```python
from tests.fixtures.seeds import clear_database

# Clear all data from database
clear_database(db)
```

## Implementation Notes

- Seeding uses SQLite for compatibility
- In-memory databases (`:memory:`) are recommended for tests
- Seeding gracefully handles schema mismatches
- Veteran player seeding generates realistic hand distributions
- Tournament seeding includes ITM rate and ROI calculations

## Adding New Scenarios

1. Create a new file in `tests/fixtures/seeds/` (e.g., `cash_game_grinder.py`)
2. Implement a `seed_<scenario>` function
3. Add the scenario to `base.py` in the `seed_database` function
4. Update `__init__.py` to export the new seeding function
5. Add tests in `tests/test_database_seeding.py`

## Testing

```bash
# Run seeding tests
pytest tests/test_database_seeding.py -v

# Run with coverage
pytest tests/test_database_seeding.py --cov=tests.fixtures.seeds
```

## Schema Flexibility

The seeding functions are designed to work with minimal schema requirements. They will:
- Create tables if needed
- Gracefully handle missing tables
- Not error if schema doesn't match expectations

This makes seeding robust across different database versions and configurations.
