# Contributing to PokerTool

## Code Style & Naming Conventions

### Python

**Variable Naming:**
- `database` (full word) - preferred for database connections and instances
- `db` (abbreviation) - acceptable only for local variables in small scopes
- `config` (full word) - preferred for configuration objects
- Avoid: `cfg`, `conf` (use `config` instead)

**Examples:**
```python
# Good
database = get_production_db()
config = load_configuration()

# Acceptable (local scope only)
def save_hand(hand_id: str) -> bool:
    db = get_hand_history_db()
    return db.save(hand_id)

# Avoid
cfg = get_config()  # Use 'config' instead
```

**Function Naming:**
- Use descriptive names: `get_hand_history_db()`, not `get_db()`
- Private methods: prefix with `_` (e.g., `_format_hand_for_vectordb`)
- Avoid abbreviations unless universally understood (e.g., `id`, `url`, `api`)

**File Naming:**
- Snake_case for Python files: `hand_recorder.py`, `card_recognizer.py`
- Match the main class name when possible: `CardRecognitionEngine` → `card_recognizer.py`

### TypeScript/React

**Component Naming:**
- PascalCase for components: `Dashboard`, `TableView`, `SystemStatus`
- camelCase for hooks: `useWebSocket`, `useBackendLifecycle`
- camelCase for utilities: `buildApiUrl`, `formatDuration`

**File Naming:**
- PascalCase for component files: `Dashboard.tsx`, `Navigation.tsx`
- camelCase for hooks: `useWebSocket.ts`
- camelCase for utilities: `api.ts`, `common.ts`

**Props Naming:**
- Use descriptive names: `backendStatus`, not `status`
- Boolean props: prefix with `is`, `has`, `should`: `isLoading`, `hasError`

### General Guidelines

1. **Be Explicit**: `userAuthentication` over `auth`
2. **Be Consistent**: Pick one style per module and stick to it
3. **Context Matters**: Abbreviations acceptable in tight loops, full names in interfaces
4. **Document Deviations**: If you must use non-standard naming, add a comment explaining why

### Linting

- Python: `mypy`, `flake8`, `black` (configured in `.pre-commit-config.yaml`)
- TypeScript: ESLint with strict rules (see `pokertool-frontend/.eslintrc.json`)

Run linters before committing:
```bash
# Python
black src/pokertool/
mypy src/pokertool/

# TypeScript  
cd pokertool-frontend
npm run lint
```
