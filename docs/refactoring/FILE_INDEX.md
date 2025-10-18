# Complete File Index - Enhanced GUI Refactoring
> Issue Register: Use `python new_task.py` to append GUID-tagged entries to `docs/TODO.md`; manual edits are rejected and historical backlog lives in `docs/TODO_ARCHIVE.md`.

## 📁 Documentation Files (In Project Root)

| File | Purpose | Status |
|------|---------|--------|
| `QUICK_START_CHECKLIST.md` | Step-by-step TODO list | ✅ Ready |
| `COMPLETING_REFACTORING.md` | Detailed guide with code examples | ✅ Ready |
| `REFACTORING_GUIDE.md` | Overview of refactoring | ✅ Ready |
| `ARCHITECTURE_DIAGRAM.md` | Visual architecture diagrams | ✅ Ready |
| `REFACTORING_SUMMARY_README.md` | Quick summary | ✅ Ready |

**Start here**: `QUICK_START_CHECKLIST.md`

## 📁 Source Files (enhanced_gui_components/)

### Main Files

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `__init__.py` | 80 | Package exports | ✅ Created |
| `app.py` | ~150 | Main application class | ⏳ To create |
| `style.py` | 60 | Colors & fonts | ✅ Existing |

### Components (Existing)

| File | Purpose | Status |
|------|---------|--------|
| `autopilot_panel.py` | Autopilot control panel | ✅ Keep as-is |
| `manual_section.py` | Manual play section | ✅ Keep as-is |
| `settings_section.py` | Settings tab | ✅ Keep as-is |
| `coaching_section.py` | Coaching tab | ✅ Keep as-is |

### Utils Directory

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `utils/__init__.py` | 10 | Utility exports | ✅ Created |
| `utils/translation_helpers.py` | 170 | TranslationMixin for i18n | ✅ Created |
| `utils/ui_helpers.py` | 50 | UI utilities (brighten_color) | ✅ Created |

### Handlers Directory

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `handlers/__init__.py` | 10 | Handler exports | ✅ Created |
| `handlers/action_handlers.py` | 340 | Quick action methods | ✅ Created |
| `handlers/autopilot_handlers.py` | 240 | Autopilot event handlers | ✅ Created |
| `handlers/scraper_handlers.py` | 140 | Screen scraper handlers | ✅ Created |

**Handlers total**: ~730 lines (was inline in original file)

### Services Directory

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `services/__init__.py` | 10 | Service exports | ✅ Created |
| `services/background_services.py` | 70 | Background service init | ✅ Created |
| `services/screen_update_loop.py` | 110 | Continuous updates | ✅ Created |

**Services total**: ~190 lines

### Tabs Directory

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `tabs/__init__.py` | 20 | Tab exports | ✅ Created |
| `tabs/TEMPLATE_tab.py` | 60 | Template for new tabs | ✅ Created |
| `tabs/analysis_tab.py` | 50 | Analysis tab | ✅ Created |
| `tabs/autopilot_tab.py` | ~180 | Autopilot tab with quick actions | ⏳ To create |
| `tabs/analytics_tab.py` | ~100 | Analytics dashboard tab | ⏳ To create |
| `tabs/gamification_tab.py` | ~120 | Gamification tab | ⏳ To create |
| `tabs/community_tab.py` | ~130 | Community features tab | ⏳ To create |

**Tabs when complete**: ~650 lines total

## 📁 Main Entry Point

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `enhanced_gui.py` | ~30 | Simplified entry point | ⏳ To update |

**Before**: 1000+ lines
**After**: 30 lines

## 📊 Code Statistics

### Before Refactoring
```
enhanced_gui.py: 1000+ lines (everything in one file)
```

### After Refactoring
```
Documentation:           5 files  (guides & references)
Source code:            22 files  (modular components)

Breakdown:

  - Utilities:           2 files  (~220 lines)
  - Handlers:            3 files  (~730 lines)
  - Services:            2 files  (~190 lines)
  - Tabs:                5 files  (~650 lines)
  - Components:          4 files  (existing, unchanged)
  - Main files:          3 files  (~290 lines)
  - __init__ files:      5 files  (~50 lines)

  ────────────────────────────────────────────
  ────────────────────────────────────────────
  Total source:         24 files  (~2130 lines organized)
```

## 🎯 File Purpose Quick Reference

**Need to...**

| Task | File to Edit |
|------|--------------|
| Add a quick action button | `handlers/action_handlers.py` |
| Modify autopilot logic | `handlers/autopilot_handlers.py` |
| Change screen scraper behavior | `handlers/scraper_handlers.py` |
| Update background services | `services/background_services.py` |
| Modify screen update loop | `services/screen_update_loop.py` |
| Change analytics tab UI | `tabs/analytics_tab.py` |
| Modify autopilot tab UI | `tabs/autopilot_tab.py` |
| Update colors/fonts | `style.py` |
| Change translations | `utils/translation_helpers.py` |
| Add UI helper function | `utils/ui_helpers.py` |

## 📝 Method Location Map

### Where Did Each Method Go?

**From original `enhanced_gui.py`:**

| Original Method | New Location |
|----------------|--------------|
| `_detect_tables()` | `handlers/action_handlers.py` |
| `_test_screenshot()` | `handlers/action_handlers.py` |
| `_run_gto_analysis()` | `handlers/action_handlers.py` |
| `_open_web_interface()` | `handlers/action_handlers.py` |
| `_open_manual_gui()` | `handlers/action_handlers.py` |
| `_handle_autopilot_toggle()` | `handlers/autopilot_handlers.py` |
| `_start_autopilot()` | `handlers/autopilot_handlers.py` |
| `_stop_autopilot()` | `handlers/autopilot_handlers.py` |
| `_autopilot_loop()` | `handlers/autopilot_handlers.py` |
| `_process_table_state()` | `handlers/autopilot_handlers.py` |
| `_toggle_screen_scraper()` | `handlers/scraper_handlers.py` |
| `_start_enhanced_screen_scraper()` | `handlers/scraper_handlers.py` |
| `_stop_enhanced_screen_scraper()` | `handlers/scraper_handlers.py` |
| `_update_scraper_indicator()` | `handlers/scraper_handlers.py` |
| `_init_database()` | `services/background_services.py` |
| `_start_background_services()` | `services/background_services.py` |
| `_start_screen_update_loop()` | `services/screen_update_loop.py` |
| `_stop_screen_update_loop()` | `services/screen_update_loop.py` |
| `_build_analysis_tab()` | `tabs/analysis_tab.py` |
| `_build_autopilot_tab()` | `tabs/autopilot_tab.py` (to create) |
| `_build_analytics_tab()` | `tabs/analytics_tab.py` (to create) |
| `_build_gamification_tab()` | `tabs/gamification_tab.py` (to create) |
| `_build_community_tab()` | `tabs/community_tab.py` (to create) |
| `_brighten_color()` | `utils/ui_helpers.py` |
| Translation methods | `utils/translation_helpers.py` |

## 🗂️ Import Map

**How to import from the new structure:**

```python
# Import style constants
from pokertool.enhanced_gui_components import COLORS, FONTS

# Import existing components
from pokertool.enhanced_gui_components import (
    AutopilotControlPanel,
    ManualPlaySection,
    SettingsSection,
    CoachingSection,
)

# Import utilities
from pokertool.enhanced_gui_components.utils import (
    TranslationMixin,
    brighten_color,
)

# Import handlers
from pokertool.enhanced_gui_components.handlers import (
    AutopilotHandlersMixin,
    ActionHandlersMixin,
    ScraperHandlersMixin,
)

# Import services
from pokertool.enhanced_gui_components.services import (
    BackgroundServicesMixin,
    ScreenUpdateLoopMixin,
)

# Import tabs
from pokertool.enhanced_gui_components.tabs import (
    AnalysisTabMixin,
    AutopilotTabMixin,
    AnalyticsTabMixin,
    GamificationTabMixin,
    CommunityTabMixin,
)

# Import main app (after creating app.py)
from pokertool.enhanced_gui_components.app import IntegratedPokerAssistant
```

## ✅ Completion Checklist

- [x] Created directory structure
- [x] Created utilities
- [x] Created handlers
- [x] Created services
- [x] Created analysis tab example
- [x] Created template
- [x] Updated __init__ files
- [x] Created documentation
- [ ] Create 4 remaining tab files
- [ ] Create app.py
- [ ] Update enhanced_gui.py
- [ ] Test application

## 📚 Reading Order

1. `QUICK_START_CHECKLIST.md` - Your TODO list
2. `tabs/analysis_tab.py` - See an example
3. `tabs/TEMPLATE_tab.py` - Use as template
4. `COMPLETING_REFACTORING.md` - Detailed guide
5. `ARCHITECTURE_DIAGRAM.md` - Understand structure

## 🎓 Learning Resources

**Want to understand a concept?**

- Mixins → `ARCHITECTURE_DIAGRAM.md` (Mixin Composition Pattern)
- File organization → `REFACTORING_GUIDE.md`
- How to create tabs → `tabs/TEMPLATE_tab.py`
- Translation system → `utils/translation_helpers.py`

Ready to start? Open `QUICK_START_CHECKLIST.md`! 🚀
