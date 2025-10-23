# Migration Guide: v98.0.0

**Date**: 2025-10-23
**Previous Version**: v88.6.0
**Current Version**: v98.0.0

This guide helps you migrate your code and understand the changes introduced in version 98.0.0.

---

## Overview of Changes

Version 98.0.0 introduces several important changes focused on:
1. **Backward compatibility** for legacy database code
2. **Package reorganization** for better module structure
3. **Process management** improvements
4. **API endpoint fixes**

---

## 1. PokerDatabase Backward Compatibility Wrapper

### What Changed

A new `PokerDatabase` class was added to `src/pokertool/database.py` to maintain compatibility with legacy code that expects the old database interface.

### Why This Matters

If you have existing code using the old database interface, it will continue to work without modification. The wrapper provides a simple interface for SQLite operations while internally using the more robust `SecureDatabase` class.

### API Reference

#### Class: `PokerDatabase`

```python
from pokertool.database import PokerDatabase

# Initialize database
db = PokerDatabase(db_path='poker_decisions.db')

# Use as context manager
with PokerDatabase('poker_decisions.db') as db:
    # Your code here
    pass
```

#### Methods

##### `__init__(db_path: str = 'poker_decisions.db')`

Initialize database with given path.

**Parameters:**
- `db_path` (str): Path to SQLite database file. Default: 'poker_decisions.db'

**Example:**
```python
db = PokerDatabase('my_poker_data.db')
```

##### `save_hand_analysis(...)`

Save hand analysis to database with validation.

**Parameters:**
- `hand` (str): The hand to analyze (e.g., "AsKh")
- `board` (Optional[str]): The board cards (e.g., "Qh9c2d")
- `result` (str): The analysis result
- `session_id` (Optional[str]): Session identifier
- `confidence_score` (Optional[float]): Detection confidence (0.0-1.0)
- `bet_size_ratio` (Optional[float]): Bet size as ratio of pot
- `pot_size` (Optional[float]): Total pot size
- `player_position` (Optional[str]): Player position (BTN, SB, BB, UTG, etc.)

**Returns:** int - The ID of the inserted record

**Raises:** ValueError - If data validation fails

**Example:**
```python
record_id = db.save_hand_analysis(
    hand="AsKh",
    board="Qh9c2d",
    result="Fold",
    session_id="session_123",
    confidence_score=0.95,
    bet_size_ratio=0.75,
    pot_size=100.0,
    player_position="BTN"
)
```

##### `get_recent_hands(limit: int = 100, offset: int = 0)`

Get recent hands from database.

**Parameters:**
- `limit` (int): Maximum number of hands to return. Default: 100
- `offset` (int): Number of hands to skip. Default: 0

**Returns:** List[Dict[str, Any]] - List of hand records

**Example:**
```python
# Get last 50 hands
recent_hands = db.get_recent_hands(limit=50)

# Get hands 100-150 (pagination)
next_page = db.get_recent_hands(limit=50, offset=100)
```

##### `get_total_hands()`

Get total number of hands in database.

**Returns:** int - Total count of hands

**Example:**
```python
total = db.get_total_hands()
print(f"Database contains {total} hands")
```

##### `close()`

Close database connection.

**Example:**
```python
db.close()
```

### Migration Example

**Old Code (still works):**
```python
# This code continues to work as-is
from pokertool.database import PokerDatabase

db = PokerDatabase()
db.save_hand_analysis("AsKh", "Qh9c2d", "Fold")
hands = db.get_recent_hands(50)
db.close()
```

**New Code (recommended for new projects):**
```python
# Use SecureDatabase for new projects
from pokertool.storage import SecureDatabase

db = SecureDatabase('poker_decisions.db')
db.save_hand_analysis("AsKh", "Qh9c2d", "Fold")
hands = db.get_recent_hands(50)
db.close()
```

### When to Use Each

- **Use `PokerDatabase`**: When working with legacy code, maintaining compatibility, or need simple SQLite operations
- **Use `SecureDatabase`**: For new projects, when you need advanced features (encryption, PostgreSQL support, connection pooling)
- **Use `ProductionDatabase`**: For production deployments with PostgreSQL

---

## 2. ML Module Import Path Changes

### What Changed

ML modules have been reorganized into dedicated packages for better structure:
- New package: `pokertool.system` - Contains ML system modules
- New package: `pokertool.modules` - Contains poker modules like nash_solver

### Import Path Migration

#### Model Calibration

**Old Import:**
```python
from pokertool import model_calibration
```

**New Import (both work):**
```python
# Option 1: Original path (still works)
from pokertool import model_calibration

# Option 2: New system path
from pokertool.system import model_calibration
```

#### Sequential Opponent Fusion

**Old Import:**
```python
from pokertool import sequential_opponent_fusion
```

**New Import (both work):**
```python
# Option 1: Original path (still works)
from pokertool import sequential_opponent_fusion

# Option 2: New system path
from pokertool.system import sequential_opponent_fusion
```

#### Active Learning

**Old Import:**
```python
from pokertool import active_learning
```

**New Import (both work):**
```python
# Option 1: Original path (still works)
from pokertool import active_learning

# Option 2: New system path
from pokertool.system import active_learning
```

#### Nash Solver

**Old Import:**
```python
from pokertool import nash_solver
```

**New Import (both work):**
```python
# Option 1: Original path (still works)
from pokertool import nash_solver

# Option 2: New modules path
from pokertool.modules import nash_solver
```

### Why the Change?

The new package structure provides:
1. **Better organization**: Related modules grouped together
2. **Clearer intent**: `system` for ML, `modules` for poker components
3. **Easier maintenance**: Simpler to find and update related code
4. **Future-proof**: Easier to add new modules

### Do I Need to Change My Code?

**No!** Old import paths still work thanks to backward compatibility. The new paths are available for new code and refactoring.

### Recommended Migration Strategy

1. **For existing code**: No changes required, it continues to work
2. **For new code**: Use new import paths (`pokertool.system.*`, `pokertool.modules.*`)
3. **For refactoring**: Gradually migrate to new paths when updating files

### Example Migration

**Before (still works):**
```python
from pokertool import model_calibration
from pokertool import sequential_opponent_fusion
from pokertool import active_learning
from pokertool import nash_solver

# Use modules
calibration_result = model_calibration.calibrate(data)
fusion_result = sequential_opponent_fusion.fuse(opponents)
learning_result = active_learning.learn(session)
nash_result = nash_solver.solve(game_state)
```

**After (recommended for new code):**
```python
from pokertool.system import model_calibration
from pokertool.system import sequential_opponent_fusion
from pokertool.system import active_learning
from pokertool.modules import nash_solver

# Use modules (same API)
calibration_result = model_calibration.calibrate(data)
fusion_result = sequential_opponent_fusion.fuse(opponents)
learning_result = active_learning.learn(session)
nash_result = nash_solver.solve(game_state)
```

---

## 3. Process Cleanup on Startup

### What Changed

Added `cleanup_old_processes()` function to `scripts/start.py` that automatically terminates stale pokertool processes during startup.

### What It Does

When you start PokerTool, it now automatically:
1. **Detects** old pokertool processes (GUI, React dev servers, etc.)
2. **Terminates** stale processes that might be stuck
3. **Logs** what it cleaned up
4. **Starts fresh** with a clean slate

### Patterns Detected

The cleanup function searches for these process patterns:
- `python.*start\.py` - Old start.py processes
- `python.*enhanced_gui` - Enhanced GUI processes
- `python.*simple_gui` - Simple GUI processes
- `python.*launch.*gui` - Any GUI launcher
- `python.*run_gui` - GUI runners
- `pokertool.*gui` - General pokertool GUI processes
- `node.*react-scripts` - React development servers
- `react-scripts start` - React dev server start command

### Platform Support

- **macOS/Linux**: Uses `pgrep` and `kill` commands
- **Windows**: Uses `taskkill` command

### Safety Features

1. **Excludes current process**: Never kills itself
2. **Graceful shutdown first**: Sends SIGTERM before SIGKILL (Unix)
3. **Timeout protection**: Limited to 5 seconds
4. **Error handling**: Continues even if cleanup fails

### Impact on Users

**Positive:**
- No more "port already in use" errors
- No need to manually kill stuck processes
- Faster, cleaner startup
- Prevents resource leaks from zombie processes

**What to Watch:**
- If you run multiple instances intentionally, they will be killed on new startup
- Cleanup logs appear during startup

### Example Startup Log

```
Cleaning up previous pokertool/GUI instances...
  Found stuck processes: [12345, 12346]
  Terminating PID 12345... Done
  Terminating PID 12346... Done
  ✓ Cleaned up 2 old processes
```

### When Cleanup Happens

Cleanup runs automatically:
1. When you run `python3 start.py`
2. Before the main application starts
3. Only affects pokertool-related processes

### Manual Cleanup (if needed)

If automatic cleanup fails, you can manually clean up:

**macOS/Linux:**
```bash
# Find pokertool processes
ps aux | grep "pokertool\|start.py\|react-scripts"

# Kill specific process
kill -9 <PID>

# Or use pkill
pkill -f "start.py"
```

**Windows:**
```cmd
# Find processes
tasklist | findstr python

# Kill processes
taskkill /F /PID <PID>
```

---

## 4. Fixed API Endpoint Signatures

### What Changed

Fixed 422 validation errors by removing incorrect `request` parameter from GET handlers.

### Affected Endpoints

#### `/api/ml/opponent-fusion/stats` (GET)

**Before (caused 422 error):**
```python
@router.get("/api/ml/opponent-fusion/stats")
async def get_stats(request: Request):  # ❌ Wrong
    return stats
```

**After (fixed):**
```python
@router.get("/api/ml/opponent-fusion/stats")
async def get_stats():  # ✅ Correct
    return stats
```

#### `/api/ml/opponent-fusion/players` (GET)

**Before:**
```python
@router.get("/api/ml/opponent-fusion/players")
async def get_players(request: Request):  # ❌ Wrong
    return players
```

**After:**
```python
@router.get("/api/ml/opponent-fusion/players")
async def get_players():  # ✅ Correct
    return players
```

#### `/api/ml/active-learning/stats` (GET)

**Before:**
```python
@router.get("/api/ml/active-learning/stats")
async def get_learning_stats(request: Request):  # ❌ Wrong
    return stats
```

**After:**
```python
@router.get("/api/ml/active-learning/stats")
async def get_learning_stats():  # ✅ Correct
    return stats
```

#### `/api/scraping/accuracy/stats` (GET)

**Before:**
```python
@router.get("/api/scraping/accuracy/stats")
async def get_accuracy_stats(request: Request):  # ❌ Wrong
    return stats
```

**After:**
```python
@router.get("/api/scraping/accuracy/stats")
async def get_accuracy_stats():  # ✅ Correct
    return stats
```

### Impact

- **No API breaking changes**: Endpoints work the same from client perspective
- **Fixed validation errors**: No more 422 responses
- **Better FastAPI compliance**: Follows FastAPI best practices

### If You're Calling These APIs

**No changes required!** The endpoints work exactly the same:

```javascript
// These all work correctly now
fetch('/api/ml/opponent-fusion/stats')
fetch('/api/ml/opponent-fusion/players')
fetch('/api/ml/active-learning/stats')
fetch('/api/scraping/accuracy/stats')
```

---

## 5. Enhanced Smoke Test Coverage

### What Changed

Added comprehensive smoke tests to validate:
- Database operations
- ML module imports
- API endpoint responses
- Startup process cleanup

### Test Results

Version 98.0.0 achieved **100% smoke test pass rate** (38/38 tests).

### Running Smoke Tests

```bash
# Run all smoke tests
python3 -m pytest tests/smoke/ -v

# Run specific smoke test suite
python3 -m pytest tests/smoke/test_database.py -v
python3 -m pytest tests/smoke/test_ml_modules.py -v
python3 -m pytest tests/smoke/test_api_endpoints.py -v
python3 -m pytest tests/smoke/test_startup.py -v
```

---

## Quick Migration Checklist

Use this checklist to verify your code is ready for v98.0.0:

- [ ] **Database Code**
  - [ ] Verify legacy database code still works with `PokerDatabase`
  - [ ] Consider migrating new code to `SecureDatabase` or `ProductionDatabase`
  - [ ] Test `get_total_hands()` method if you use it

- [ ] **ML Module Imports**
  - [ ] Check if your code imports ML modules
  - [ ] Verify imports still work (they should!)
  - [ ] Optionally update to new import paths for clarity

- [ ] **Nash Solver Imports**
  - [ ] Check if you import nash_solver
  - [ ] Verify import still works
  - [ ] Optionally update to `pokertool.modules.nash_solver`

- [ ] **API Clients**
  - [ ] Test API calls to fixed endpoints
  - [ ] Verify no more 422 errors
  - [ ] Update error handling if you were catching 422s

- [ ] **Process Management**
  - [ ] Test startup with stuck processes
  - [ ] Verify cleanup logs appear
  - [ ] Check that startup is faster and cleaner

- [ ] **Testing**
  - [ ] Run smoke tests to verify everything works
  - [ ] Check your own test suite passes
  - [ ] Verify database migrations work

---

## Troubleshooting

### Problem: Import errors for ML modules

**Symptom:**
```python
ImportError: cannot import name 'model_calibration' from 'pokertool.system'
```

**Solution:**
Check if modules exist in your installation:
```bash
python3 -c "from pokertool import model_calibration; print('OK')"
```

If this fails, the module may not be installed. Try:
```bash
pip install -r requirements.txt --upgrade
```

### Problem: Database validation errors

**Symptom:**
```
ValueError: Invalid data for insertion: ...
```

**Solution:**
The new `PokerDatabase` wrapper includes validation. Ensure your data:
- Hand format is valid (e.g., "AsKh")
- Board format is valid (e.g., "Qh9c2d")
- Confidence score is between 0.0 and 1.0
- Position is valid poker position (BTN, SB, BB, UTG, etc.)

### Problem: Processes not cleaning up

**Symptom:**
```
Port 5001 already in use
```

**Solution:**
1. Check cleanup logs during startup
2. Manually kill processes if needed:
   ```bash
   lsof -ti:5001 | xargs kill -9
   lsof -ti:3000 | xargs kill -9
   ```
3. Report issue if cleanup consistently fails

### Problem: API 422 errors still occur

**Symptom:**
```
422 Unprocessable Entity
```

**Solution:**
1. Verify you're on v98.0.0 or later:
   ```bash
   cat VERSION
   ```
2. Check you're calling the correct endpoint
3. Verify request format matches API documentation

---

## Getting Help

If you encounter issues during migration:

1. **Check logs**: `logs/app.log`, `logs/update_manager.log`
2. **Run diagnostics**: `python3 -m pytest tests/smoke/ -v`
3. **Review this guide**: Check troubleshooting section
4. **GitHub Issues**: Report bugs at https://github.com/gmanldn/pokertool/issues
5. **Documentation**: See docs/ folder for detailed guides

---

## Summary

Version 98.0.0 focuses on **backward compatibility** and **stability**:

✅ **Database compatibility** - Legacy code continues to work
✅ **Module reorganization** - Better structure, maintained compatibility
✅ **Process cleanup** - Cleaner, more reliable startup
✅ **API fixes** - No more validation errors
✅ **100% smoke tests** - Comprehensive test coverage

**Migration effort**: Minimal to none for most users. Existing code continues to work.

---

**Last Updated:** 2025-10-23
**Next Review:** When version 102.0.0 is released
