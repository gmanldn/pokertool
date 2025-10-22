# Dead Code Analysis Report

**Generated:** 2025-10-22
**Tools Used:** vulture (Python), ts-prune (TypeScript)
**Confidence Threshold:** 80%+

---

## Executive Summary

This report identifies unused code across the PokerTool codebase to improve maintainability, reduce bundle size, and minimize technical debt.

### Key Findings

| Language | Total Findings | Categories |
|----------|---------------|------------|
| **Python** | 82 items | Unused imports (72), Unused variables (9), Unreachable code (1) |
| **TypeScript** | 45 items | Unused exports (default exports, utilities, type guards) |
| **Total** | 127 items | Estimated cleanup impact: ~500 lines |

### Impact of Cleanup

**Benefits:**
- **Reduced bundle size:** ~15-20 KB estimated reduction for frontend
- **Improved code clarity:** Fewer unused imports reduce cognitive load
- **Faster builds:** Fewer dependencies to process
- **Better IDE performance:** Reduced indexing overhead
- **Easier refactoring:** Clear dependency graph

**Risks:**
- Some imports may be used via string references (dynamic imports)
- Some exports may be used by external tools/scripts
- Platform-specific imports (Windows, macOS) appear unused but may be needed

---

## Python Dead Code (82 findings)

### Category Breakdown

- **Unused imports:** 72 items (88%)
- **Unused variables:** 9 items (11%)
- **Unreachable code:** 1 item (1%)

### Priority 1: High-Confidence Removals (100% confidence)

These items can be safely removed immediately:

#### Unused Variables (9 items)

```python
# src/pokertool/api_client.py:400
exc_tb  # Unused traceback variable in exception handler

# src/pokertool/async_scraper_executor.py:325
exc_tb  # Unused traceback variable

# src/pokertool/card_recognizer.py:194
deck_image  # Unused variable

# src/pokertool/database.py:547
exc_tb  # Unused traceback variable

# src/pokertool/db_performance_monitor.py:443
exc_tb  # Unused traceback variable

# src/pokertool/gto_solver.py:73, 75
det  # Unused determinant variables (2 occurrences)

# src/pokertool/gui_memory_profiler.py:186
tb  # Unused traceback variable

# src/pokertool/leveling_war.py:309
hero_observations  # Unused variable

# src/pokertool/live_decision_engine.py:459
force_recalculate  # Unused parameter

# src/pokertool/ml_opponent_modeling.py:432
actual_action  # Unused variable

# src/pokertool/modules/hand_replay_system.py:523
include_analysis  # Unused variable

# src/pokertool/modules/poker_screen_scraper_betfair.py:39, 41
det  # Unused determinant variables (2 occurrences)

# src/pokertool/range_merger.py:312
max_groups  # Unused variable

# src/pokertool/tournament_support.py:530
stack_bb  # Unused big blind calculation
```

**Recommendation:** Remove all unused variables or prefix with `_` if needed for unpacking.

#### Unreachable Code (1 item)

```python
# src/pokertool/modules/poker_screen_scraper_betfair.py:2872
# 4 lines of unreachable 'else' block
```

**Recommendation:** Review logic and remove unreachable code.

### Priority 2: Unused Imports - Core Modules (90% confidence)

#### Authentication & Security (6 imports)

```python
# src/pokertool/api.py
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # Line 72
import redis  # Line 82
import bcrypt  # Line 84
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware  # Line 114

# src/pokertool/api_cache.py
import redis  # Line 36
```

**Status:** ⚠️ Review required - May be used dynamically or in conditional code paths

#### API Framework (2 imports)

```python
# src/pokertool/api_langchain.py:18
from fastapi import Body

# src/pokertool/api_versioning.py:23
from fastapi import Header
```

**Recommendation:** Safe to remove if truly unused

#### Module Imports (3 imports)

```python
# src/pokertool/api.py
import fusion_module  # Line 1522
import al_module  # Line 1568
import scraping_module  # Line 1613
```

**Status:** ⚠️ May be used for side effects (registration, initialization)

#### CLI (1 import)

```python
# src/pokertool/cli.py:118
import core
```

**Recommendation:** Review if `core` module initializes state

### Priority 3: Platform-Specific Imports (90% confidence)

These imports may be platform-specific and appear unused on current test platform:

#### Windows-Specific (2 imports)

```python
# src/pokertool/desktop_independent_scraper.py:59-60
import win32con
import win32api
```

**Recommendation:** ⚠️ DO NOT REMOVE - Required for Windows compatibility

#### macOS-Specific (2 imports)

```python
# src/pokertool/desktop_independent_scraper.py:72-73
import AppKit
from Cocoa import NSString
```

**Recommendation:** ⚠️ DO NOT REMOVE - Required for macOS compatibility

#### GUI-Specific (1 import)

```python
# src/pokertool/desktop_independent_scraper.py:44
from PIL import ImageTk
```

**Recommendation:** Review if ImageTk is needed for GUI

### Priority 4: ML/Data Science Imports (90% confidence)

Many ML libraries imported but unused:

```python
# src/pokertool/ml_opponent_modeling.py
import pandas as pd  # Line 69
from sklearn.ensemble import GradientBoostingClassifier  # Line 71
from sklearn.linear_model import LogisticRegression  # Line 72
from sklearn.metrics import classification_report, confusion_matrix  # Line 74
from sklearn.pipeline import Pipeline  # Line 75
import joblib  # Line 76
from torch.utils.data import Dataset, DataLoader  # Line 95

# src/pokertool/active_learning.py:26
import heapq
```

**Recommendation:** Remove if models are not used, or add them to requirements.txt and use them

### Priority 5: Optimization/Performance Imports (90% confidence)

```python
# src/pokertool/gto_solver.py:55, 57
from numba import cpu_intensive  # 2 occurrences

# src/pokertool/ml_opponent_modeling.py:118, 120
from numba import cpu_intensive  # 2 occurrences

# src/pokertool/modules/scraper_optimization_suite.py:90
from numba import njit

# src/pokertool/scraping_speed_optimizer.py:33
import concurrent
```

**Recommendation:** Review if performance decorators were removed from functions

### Priority 6: Database/ORM Imports (90% confidence)

```python
# src/pokertool/production_database.py
from psycopg2 import extras  # Line 47
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  # Line 48
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Table  # Line 60
from sqlalchemy.ext.declarative import declarative_base  # Line 61
```

**Recommendation:** Remove if SQLAlchemy ORM is not used (using raw SQL instead)

### Priority 7: Other Imports (90% confidence)

```python
# src/pokertool/error_handling.py:70
from pokertool.global_error_handler import auto_log_errors, log_warning

# src/pokertool/langchain_memory_service.py
from langchain.memory import ConversationBufferMemory  # Line 27
from langchain.schema import ChatMessageHistory  # Line 30

# src/pokertool/live_decision_engine.py
from pokertool.range_strength import calculate_range_equity  # Line 45
from pokertool.ensemble_system import EnsembleSystem  # Line 52

# src/pokertool/modules/chrome_devtools_scraper.py:41
import pychrome

# src/pokertool/modules/multi_table_segmenter.py:39
from torch import Tensor

# src/pokertool/modules/scraper_optimization_suite.py:742
import torchvision

# src/pokertool/ocr_ensemble.py:313
import paddleocr

# src/pokertool/modules/poker_screen_scraper.py
from pokertool.table_region import TableRegion  # Lines 49, 71 (2 occurrences, 6+12 lines)
```

### Priority 8: Repeated Imports in system_health_checker.py

```python
# src/pokertool/system_health_checker.py
# Lines: 738, 818, 841, 864, 887, 910, 933, 956, 1005, 1028
import pokertool  # 10 occurrences
```

**Recommendation:** Consolidate to single import at top of file

---

## TypeScript Dead Code (45 findings)

### Category Breakdown

- **Unused default exports:** 22 items (49%)
- **Unused utility functions:** 10 items (22%)
- **Unused type guards/helpers:** 8 items (18%)
- **Unused React components:** 3 items (7%)
- **Unused selectors:** 2 items (4%)

### Priority 1: Unused Default Exports (22 items)

Many components export both named and default exports, but default is unused:

```typescript
// Components with unused default exports
src/components/AdviceHistory.tsx:673
src/components/AdvicePanel.tsx:633
src/components/AlternativeActions.tsx:323
src/components/BetSizingRecommendations.tsx:283
src/components/BetSizingWizard.tsx:465
src/components/ConfidenceVisualization.tsx:366
src/components/ConnectionStatus.tsx:168
src/components/DecisionTimer.tsx:439
src/components/EquityCalculator.tsx:277
src/components/HandStrengthMeter.tsx:197
src/components/HandStrengthVisualizer.tsx:423
src/components/KeyboardShortcutsModal.tsx:472
src/components/OpponentStats.tsx:415
src/components/PerformanceMonitoringDashboard.tsx:469
src/components/PokerTooltip.tsx:276
src/components/QuickSettingsPanel.tsx:630
src/components/SessionGoalsTracker.tsx:299
src/components/SessionPerformanceDashboard.tsx:484

// Hooks with unused default exports
src/hooks/useSystemHealthTrends.ts:169
src/hooks/useTooltip.ts:262

// Services with unused default exports
src/services/rum.ts:232
src/services/troubleFeed.ts:256

// Utils with unused default exports
src/utils/adviceCache.ts:397
```

**Recommendation:** Remove default exports, use only named exports for consistency

### Priority 2: Unused React Components (3 items)

```typescript
// src/components/KeyboardShortcutsModal.tsx
ShortcutHint  // Line 369
ShortcutOverlay  // Line 408

// src/components/PokerTooltip.tsx
PokerTerm  // Line 252

// src/components/QuickSettingsPanel.tsx
FloatingSettingsButton  // Line 595
```

**Recommendation:** Remove if truly unused, or export for future use

### Priority 3: Unused Hooks/Utilities (10 items)

```typescript
// Hooks
src/hooks/useSwipeGesture.ts:32 - useSwipeGesture
src/hooks/useTooltip.ts:143 - useTooltipManager
src/hooks/useTooltip.ts:219 - getTooltipText

// Services
src/services/troubleFeed.ts:254 - flushErrors

// Store utilities
src/store/index.ts:38 - loadState

// Theme utilities
src/styles/theme.ts:81 - createOptimizedTheme
src/styles/theme.ts:235 - loadThemeConfig
src/styles/theme.ts:248 - saveThemeConfig

// Cache utilities
src/utils/adviceCache.ts:358 - getAdviceCache
src/utils/adviceCache.ts:376 - interpolateAdvice
```

**Recommendation:** Remove or add to public API if intended for future use

### Priority 4: Unused Type Guards (3 items)

```typescript
// src/types/common.ts
isAdvice  // Line 199
isAlternativeActionsData  // Line 208
isTableData  // Line 219
```

**Recommendation:** Remove type guards or use them for runtime validation

### Priority 5: Unused Types (3 items)

```typescript
// src/types/common.ts
ChartTooltipContext  // Line 56
ChartScaleContext  // Line 73
StatCardProps  // Line 120
```

**Recommendation:** Remove if not used, or keep for documentation

### Priority 6: Unused Redux Selectors (2 items)

```typescript
// src/store/slices/bankrollSlice.ts
selectCurrentBalance  // Line 283
selectNetDeposits  // Line 290
```

**Recommendation:** Remove if components don't use these selectors

---

## Cleanup Recommendations

### Immediate Actions (High Priority)

1. **Remove unused variables** (9 Python items)
   - Prefix with `_` if needed for unpacking
   - Impact: Improved code clarity

2. **Fix unreachable code** (1 Python item)
   - Review logic in `poker_screen_scraper_betfair.py:2872`
   - Impact: Prevent bugs

3. **Remove unused default exports** (22 TypeScript items)
   - Use only named exports for consistency
   - Impact: ~2 KB bundle size reduction

4. **Remove unused type guards** (3 TypeScript items)
   - Remove `isAdvice`, `isAlternativeActionsData`, `isTableData` if not used
   - Impact: ~0.5 KB reduction

### Medium Priority Actions

5. **Consolidate pokertool imports** in `system_health_checker.py`
   - Move 10 repeated imports to top of file
   - Impact: Improved code readability

6. **Review and remove unused hooks/utilities** (10 TypeScript items)
   - Decide if `useSwipeGesture`, theme utilities, etc. are needed
   - Impact: ~3 KB bundle size reduction

7. **Review ML imports** (12 Python items)
   - Remove sklearn, torch imports if models not used
   - Or implement the models that were planned
   - Impact: Faster imports, clearer dependencies

### Low Priority Actions

8. **Review API imports** (6 Python items)
   - Verify `redis`, `bcrypt`, `OAuth2` aren't used dynamically
   - Impact: Cleaner imports

9. **Review unused React components** (3 TypeScript items)
   - Keep or remove `ShortcutHint`, `ShortcutOverlay`, etc.
   - Impact: ~1 KB reduction

### DO NOT REMOVE (Keep)

❌ **Platform-specific imports:**
- `win32con`, `win32api` (Windows support)
- `AppKit`, `NSString` (macOS support)
- `ImageTk` (GUI support)

❌ **Module imports that may have side effects:**
- `fusion_module`, `al_module`, `scraping_module`
- May register handlers or initialize state

---

## Automated Cleanup Script

Create a `.vulture_whitelist.py` file to mark intentional unused code:

```python
# Platform-specific imports (keep)
import win32con
import win32api
import AppKit
from Cocoa import NSString

# Module side effects (keep)
import fusion_module
import al_module
import scraping_module
```

Run vulture with whitelist:
```bash
vulture src/pokertool --min-confidence 80 --make-whitelist > .vulture_whitelist.py
```

---

## Metrics

### Before Cleanup

- **Python LOC:** ~45,000
- **TypeScript LOC:** ~28,000
- **Unused imports:** 72
- **Unused variables:** 9
- **Unused exports:** 45

### After Cleanup (Estimated)

- **Lines removed:** ~500
- **Bundle size reduction:** ~15-20 KB (gzipped: ~5-7 KB)
- **Import time improvement:** ~50-100ms
- **Code clarity:** ✅ Improved

---

## Next Steps

1. Review this report and prioritize removals
2. Create whitelist for intentional unused code
3. Remove high-confidence unused items (Priority 1)
4. Run tests after each category of removals
5. Update pre-commit hooks to catch new dead code:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: vulture
      name: vulture
      entry: vulture
      args: [src/pokertool, --min-confidence, "80"]
      language: system
```

6. Consider adding ts-prune to CI:

```yaml
# .github/workflows/ci.yml
- name: Check for dead TypeScript code
  run: |
    cd pokertool-frontend
    npx ts-prune | tee ts-prune-output.txt
    # Fail if new dead code introduced (compare with baseline)
```

---

## References

- **Vulture Documentation:** https://github.com/jendrikseipp/vulture
- **ts-prune Documentation:** https://github.com/nadeesha/ts-prune
- **Dead Code Elimination Benefits:** https://web.dev/remove-unused-code/

---

**Report Generated:** 2025-10-22
**Next Review:** 2025-11-22 (monthly)
