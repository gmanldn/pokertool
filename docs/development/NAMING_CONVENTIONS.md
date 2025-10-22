# PokerTool Naming Conventions

**Version**: 1.0.0
**Last Updated**: 2025-10-22
**Status**: Active

## Table of Contents

1. [Python Conventions](#python-conventions)
2. [TypeScript/JavaScript Conventions](#typescriptjavascript-conventions)
3. [Database Conventions](#database-conventions)
4. [API Conventions](#api-conventions)
5. [File Naming](#file-naming)
6. [Enforcement](#enforcement)

---

## Python Conventions

### General Rules

Follow [PEP 8](https://pep8.org/) as the baseline standard.

### Variables

```python
# ✅ Good: snake_case for variables
user_count = 10
player_name = "Hero"
is_active = True
has_permission = False

# ❌ Bad: camelCase, PascalCase
userCount = 10  # Wrong
PlayerName = "Hero"  # Wrong
```

### Functions

```python
# ✅ Good: snake_case, descriptive verbs
def calculate_pot_odds(pot_size: float, bet_size: float) -> float:
    return bet_size / (pot_size + bet_size)

def get_player_position(player_id: int) -> str:
    pass

def is_valid_hand(hand: str) -> bool:
    pass

# ❌ Bad: camelCase, vague names
def calcPotOdds():  # Wrong casing
    pass

def get_data():  # Too vague
    pass
```

### Classes

```python
# ✅ Good: PascalCase, noun-based
class PokerHand:
    pass

class EquityCalculator:
    pass

class DatabaseConnection:
    pass

# ❌ Bad: snake_case, verb-based
class poker_hand:  # Wrong casing
    pass

class CalculateEquity:  # Verb-based (should be noun)
    pass
```

### Constants

```python
# ✅ Good: UPPER_SNAKE_CASE
MAX_PLAYERS = 9
DEFAULT_TIMEOUT_SECONDS = 30
API_BASE_URL = "https://api.example.com"

# ❌ Bad: other casing
maxPlayers = 9  # Wrong
default_timeout = 30  # Wrong (not uppercase)
```

### Private Members

```python
# ✅ Good: Leading underscore for internal use
class Player:
    def __init__(self):
        self._internal_state = {}  # Private
        self.public_name = "Hero"  # Public

    def _internal_helper(self):  # Private method
        pass

    def get_stats(self):  # Public method
        pass

# ❌ Bad: No distinction between public/private
class Player:
    def helper(self):  # Ambiguous visibility
        pass
```

### Type Hints

```python
# ✅ Good: Always use type hints
def calculate_equity(hand: str, board: List[str]) -> float:
    pass

def get_players(session_id: int) -> List[Player]:
    pass

# ❌ Bad: No type hints
def calculate_equity(hand, board):  # Missing types
    pass
```

---

## TypeScript/JavaScript Conventions

### Variables

```typescript
// ✅ Good: camelCase for variables
const userCount = 10;
const playerName = "Hero";
const isActive = true;
const hasPermission = false;

// ❌ Bad: snake_case, PascalCase
const user_count = 10;  // Wrong
const PlayerName = "Hero";  // Wrong
```

### Functions

```typescript
// ✅ Good: camelCase, descriptive verbs
function calculatePotOdds(potSize: number, betSize: number): number {
  return betSize / (potSize + betSize);
}

function getPlayerPosition(playerId: number): string {
  // ...
}

function isValidHand(hand: string): boolean {
  // ...
}

// ❌ Bad: PascalCase, vague names
function CalculatePotOdds() {  // Wrong casing
  // ...
}

function getData() {  // Too vague
  // ...
}
```

### Classes and Interfaces

```typescript
// ✅ Good: PascalCase for classes/interfaces
class PokerHand {
  // ...
}

interface PlayerStats {
  vpip: number;
  pfr: number;
}

type HandRange = string[];

// ❌ Bad: camelCase, snake_case
class pokerHand {  // Wrong
  // ...
}

interface player_stats {  // Wrong
  // ...
}
```

### React Components

```typescript
// ✅ Good: PascalCase for components
export const SystemStatus: React.FC = () => {
  return <div>Status</div>;
};

export function NavigationBar() {
  return <nav>Nav</nav>;
}

// ❌ Bad: camelCase
export const systemStatus = () => {  // Wrong
  return <div>Status</div>;
};
```

### Constants

```typescript
// ✅ Good: UPPER_SNAKE_CASE
const MAX_PLAYERS = 9;
const DEFAULT_TIMEOUT_MS = 30000;
const API_BASE_URL = "https://api.example.com";

// ❌ Bad: camelCase
const maxPlayers = 9;  // Wrong (not constant-case)
```

### Enums

```typescript
// ✅ Good: PascalCase for enum, UPPER_SNAKE_CASE for values
enum Street {
  PREFLOP = "PREFLOP",
  FLOP = "FLOP",
  TURN = "TURN",
  RIVER = "RIVER"
}

enum PlayerAction {
  FOLD = "fold",
  CHECK = "check",
  CALL = "call",
  BET = "bet",
  RAISE = "raise"
}

// ❌ Bad: inconsistent casing
enum street {  // Wrong (should be PascalCase)
  preflop = "preflop",  // Wrong (should be UPPER_SNAKE_CASE)
}
```

### Boolean Variables

```typescript
// ✅ Good: is/has/can/should prefix
const isConnected = true;
const hasPermission = false;
const canEdit = true;
const shouldRetry = false;

// ❌ Bad: no prefix, unclear meaning
const connected = true;  // Ambiguous
const permission = false;  // Unclear
```

---

## Database Conventions

### Table Names

```sql
-- ✅ Good: snake_case, plural nouns
CREATE TABLE players (
    id SERIAL PRIMARY KEY
);

CREATE TABLE detection_events (
    id SERIAL PRIMARY KEY
);

-- ❌ Bad: PascalCase, singular
CREATE TABLE Player (  -- Wrong casing
    id SERIAL PRIMARY KEY
);

CREATE TABLE Event (  -- Wrong (singular)
    id SERIAL PRIMARY KEY
);
```

### Column Names

```sql
-- ✅ Good: snake_case
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(255),
    created_at TIMESTAMP,
    is_active BOOLEAN
);

-- ❌ Bad: camelCase, PascalCase
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    userName VARCHAR(255),  -- Wrong
    CreatedAt TIMESTAMP  -- Wrong
);
```

### Foreign Keys

```sql
-- ✅ Good: {table}_id format
CREATE TABLE hands (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id),  -- Clear reference
    session_id INTEGER REFERENCES sessions(id)
);

-- ❌ Bad: unclear reference
CREATE TABLE hands (
    id SERIAL PRIMARY KEY,
    player INTEGER,  -- Ambiguous
    sid INTEGER  -- Unclear
);
```

---

## API Conventions

### Endpoints

```
✅ Good: RESTful, kebab-case for multi-word resources
GET    /api/players
GET    /api/players/{id}
POST   /api/players
PUT    /api/players/{id}
DELETE /api/players/{id}

GET    /api/detection-events
POST   /api/ai-analysis

❌ Bad: snake_case, camelCase
GET    /api/get_players  -- Wrong (verb in URL)
POST   /api/createPlayer  -- Wrong (camelCase)
GET    /api/detection_events  -- Wrong (snake_case)
```

### Request/Response Fields

```json
{
  "// ✅ Good: camelCase for JSON fields":  "",
  "userId": 123,
  "playerName": "Hero",
  "isActive": true,
  "createdAt": "2025-10-22T10:00:00Z"
}

{
  "// ❌ Bad: snake_case in JSON": "",
  "user_id": 123,
  "player_name": "Hero"
}
```

---

## File Naming

### Python Files

```
✅ Good: snake_case
equity_calculator.py
poker_screen_scraper.py
detection_logger.py
test_equity_calculator.py

❌ Bad: camelCase, PascalCase
equityCalculator.py
PokerScreenScraper.py
```

### TypeScript/JavaScript Files

```
✅ Good: camelCase for utilities, PascalCase for components
src/utils/apiClient.ts
src/utils/dateFormatter.ts
src/components/SystemStatus.tsx
src/components/NavigationBar.tsx
src/hooks/useWebSocket.ts

❌ Bad: inconsistent casing
src/utils/api_client.ts  -- Wrong (snake_case)
src/components/system-status.tsx  -- Wrong (kebab-case for components)
```

### Test Files

```
✅ Good: Match source file with test_ prefix (Python) or .test/.spec suffix (TS)
Python:
  tests/test_equity_calculator.py
  tests/test_gto_calculator.py

TypeScript:
  src/utils/__tests__/apiClient.test.ts
  tests/e2e/user-workflows.spec.ts

❌ Bad: unclear test files
tests/equity_tests.py
tests/test1.py
```

---

## Enforcement

### Python Linters

Use the following tools to enforce naming:

```bash
# Pylint - checks naming conventions
pylint src/pokertool/**/*.py

# Mypy - enforces type hints
mypy src/pokertool

# Black - auto-formats code
black src/pokertool

# isort - sorts imports
isort src/pokertool
```

### TypeScript Linters

```bash
# ESLint - checks naming via @typescript-eslint rules
npm run lint

# Prettier - auto-formats code
npm run format
```

### Pre-commit Hooks

Naming conventions are enforced via `.pre-commit-config.yaml`:

```yaml
- id: check-naming-python
  # Runs pylint with naming checks
- id: check-naming-typescript
  # Runs ESLint with naming rules
```

### ESLint Rules

Add to `pokertool-frontend/.eslintrc.json`:

```json
{
  "rules": {
    "@typescript-eslint/naming-convention": [
      "error",
      {
        "selector": "variable",
        "format": ["camelCase", "UPPER_CASE"]
      },
      {
        "selector": "function",
        "format": ["camelCase"]
      },
      {
        "selector": "class",
        "format": ["PascalCase"]
      },
      {
        "selector": "interface",
        "format": ["PascalCase"]
      }
    ]
  }
}
```

### Pylint Rules

Add to `.pylintrc`:

```ini
[BASIC]
# Variable naming
variable-rgx=[a-z_][a-z0-9_]{2,30}$
# Constant naming
const-rgx=(([A-Z_][A-Z0-9_]*)|(__.*__))$
# Function naming
function-rgx=[a-z_][a-z0-9_]{2,30}$
# Class naming
class-rgx=[A-Z_][a-zA-Z0-9]+$
```

---

## Common Mistakes

### 1. Mixing Conventions

```python
# ❌ Bad: Mixed snake_case and camelCase
def calculatePotOdds():  # camelCase function (wrong in Python)
    pot_size = 100  # snake_case variable (correct in Python)
    betSize = 50  # camelCase variable (wrong in Python)

# ✅ Good: Consistent snake_case
def calculate_pot_odds():
    pot_size = 100
    bet_size = 50
```

### 2. Vague Names

```python
# ❌ Bad: Unclear abbreviations
def get_p():  # What is 'p'?
    pass

def proc_data():  # 'proc' could mean process/procedure/procurement
    pass

# ✅ Good: Explicit names
def get_player():
    pass

def process_detection_data():
    pass
```

### 3. Inconsistent Boolean Prefixes

```typescript
// ❌ Bad: Inconsistent boolean naming
const active = true;  // Unclear
const enabled = false;  // Unclear
const validHand = true;  // Missing prefix

// ✅ Good: Consistent is/has/can prefixes
const isActive = true;
const isEnabled = false;
const isValidHand = true;
```

---

## Version History

- **v1.0.0** (2025-10-22): Initial naming conventions guide
