# Tkinter Removal & Web-Only Consolidation TODO
> Issue Register: Use `python new_task.py` to append GUID-tagged entries to `docs/TODO.md`; manual edits are rejected and historical backlog lives in `docs/TODO_ARCHIVE.md`.

**Project**: PokerTool Architecture Refactoring
**Version**: v81.0.0
**Priority**: CRITICAL
**Estimated Total Hours**: 120-160 hours (3-4 weeks)
**Status**: NOT STARTED

## Overview

This document outlines the comprehensive removal of all Tkinter/GUI components and consolidation to a single web-based application architecture. The current codebase has multiple interleaved versions (Tkinter GUI, simple GUI, enhanced GUI, web interface) that need to be unified.

---

## Phase 1: Remove Tkinter Python Files (30+ files)

**Priority**: CRITICAL
**Estimated Hours**: 24 hours
**Dependencies**: None

### Main GUI Applications (3 files)
- [ ] **Remove** `src/pokertool/gui.py` - Original Tkinter GUI with live advice integration
- [ ] **Remove** `src/pokertool/simple_gui.py` - Simplified Tkinter GUI
- [ ] **Remove** `src/pokertool/enhanced_gui.py` - Enhanced Tkinter GUI with advanced features

### Floating Windows & Overlays (4 files)
- [ ] **Remove** `src/pokertool/floating_advice_window.py` - Floating advice window (replaced by web interface)
- [ ] **Remove** `src/pokertool/compact_live_advice_window.py` - Compact live advice window
- [ ] **Remove** `src/pokertool/enhanced_floating_window.py` - Enhanced floating window
- [ ] **Remove** `src/pokertool/compact_advice_integration.py` - Compact advice integration

### HUD Components (3 files)
- [ ] **Remove** `src/pokertool/hud_overlay.py` - HUD overlay system
- [ ] **Remove** `src/pokertool/hud_designer.py` - HUD designer tool
- [ ] **Remove** `src/pokertool/hud_profiles.py` - HUD profile management

### GUI Components & Utilities (4 files)
- [ ] **Remove** `src/pokertool/gui_components.py` - Reusable GUI components
- [ ] **Remove** `src/pokertool/ui_enhancements.py` - UI enhancement utilities
- [ ] **Remove** `src/pokertool/ui_profiles_dashboard.py` - UI profiles dashboard
- [ ] **Remove** `src/pokertool/game_history_blade.py` - Game history blade component

### Enhanced GUI Components Directory (15+ files)
- [ ] **Remove** `src/pokertool/enhanced_gui_components/__init__.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/style.py` - Tkinter styling
- [ ] **Remove** `src/pokertool/enhanced_gui_components/autopilot_panel.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/coaching_section.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/live_table_section.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/manual_section.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/settings_section.py`

#### Handlers Subdirectory
- [ ] **Remove** `src/pokertool/enhanced_gui_components/handlers/__init__.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/handlers/action_handlers.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/handlers/autopilot_handlers.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/handlers/scraper_handlers.py`

#### Services Subdirectory
- [ ] **Remove** `src/pokertool/enhanced_gui_components/services/__init__.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/services/background_services.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/services/screen_update_loop.py`

#### Tabs Subdirectory
- [ ] **Remove** `src/pokertool/enhanced_gui_components/tabs/__init__.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/tabs/analysis_tab.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/tabs/analytics_tab.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/tabs/autopilot_tab.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/tabs/community_tab.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/tabs/gamification_tab.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/tabs/hand_history_tab.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/tabs/TEMPLATE_tab.py`

#### Utils Subdirectory
- [ ] **Remove** `src/pokertool/enhanced_gui_components/utils/__init__.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/utils/translation_helpers.py`
- [ ] **Remove** `src/pokertool/enhanced_gui_components/utils/ui_helpers.py`

### Modules with Tkinter Dependencies (2 files)
- [ ] **Remove** `src/pokertool/modules/poker_gui_enhanced.py` - Enhanced poker GUI module
- [ ] **Remove** `src/pokertool/modules/presentation_enhancer.py` - Presentation enhancer with Tkinter

### Learning & Stats Widgets (2 files)
- [ ] **Remove** `src/pokertool/learning_stats_widget.py` - Learning statistics widget
- [ ] **Remove** `src/pokertool/view_learning_stats.py` - View learning stats GUI

### Other GUI-Related Files (2 files)
- [ ] **Remove** `src/pokertool/live_advice_manager.py` - Contains Tkinter demo code
- [ ] **Remove** `src/pokertool/detailed_advice_explainer.py` - May have GUI dependencies (verify first)

---

## Phase 2: Update Files with Tkinter References

**Priority**: CRITICAL
**Estimated Hours**: 16 hours
**Dependencies**: Phase 1

### Core Files with Tkinter Imports
- [ ] **Update** `src/pokertool/cli.py` - Remove Tkinter availability check, update to web-only
- [ ] **Update** `src/pokertool/error_handling.py` - Remove Tkinter messagebox error dialogs, use logging only
- [ ] **Update** `src/pokertool/test_utils.py` - Remove Tkinter messagebox functions (showerror, showwarning, showinfo)
- [ ] **Update** `src/pokertool/dependency_manager.py` - Remove 'tkinter' from dependency list

### Archive Files (Consider removing entire archive directory)
- [ ] **Review** `archive/` directory - Many files reference GUI/Tkinter, consider complete removal
- [ ] **Decision**: Keep archive or remove? (Recommendation: Remove if covered by git history)

---

## Phase 3: Remove GUI Tests

**Priority**: HIGH
**Estimated Hours**: 12 hours
**Dependencies**: Phase 1, Phase 2

### Main GUI Test Files
- [ ] **Remove** `tests/test_gui.py` - Minimal test GUI
- [ ] **Remove** `tests/verify_enhanced_gui.py` - Enhanced GUI verification script
- [ ] **Remove** `tests/verify_enhanced_gui 2.py` - Duplicate verification script

### GUI Test Directory
- [ ] **Remove** `tests/gui/` directory (entire directory)
  - `tests/gui/__init__.py`
  - `tests/gui/test_suit_enum.py`
  - `tests/gui/test_enhanced_gui_styles.py`

### System Tests with GUI References
- [ ] **Update** `tests/system/enhanced_tests.py` - Remove GUI test classes (TestEnhancedCardEntry, TestStatusBar, TestEnhancedPokerAssistant)
- [ ] **Update** `tests/system/test_floating_advice_window.py` - Remove or rewrite for web
- [ ] **Update** `tests/system/test_syntax.py` - Remove GUI module checks

### Integration Tests with GUI
- [ ] **Update** `tests/test_comprehensive_system.py` - Remove HUD overlay tests
- [ ] **Update** `tests/test_everything.py` - Remove GUI test discovery
- [ ] **Update** `tests/final_integration_test.py` - Remove enhanced GUI import test
- [ ] **Update** `tests/final_integration_test 2.py` - Remove enhanced GUI import test

### Test Configuration
- [ ] **Update** `tests/conftest.py` - Ensure POKERTOOL_TEST_MODE suppresses all GUI, not just popups
- [ ] **Remove** GUI-related pytest fixtures if any

### Scraper Monitoring Tests
- [ ] **Update** `tests/test_scraper_monitoring.py` - Remove `test_enhanced_gui()` function
- [ ] **Update** `tests/test_scraper_monitoring 2.py` - Remove `test_enhanced_gui()` function

### Other Test Files
- [ ] **Update** `tests/test_startup_validation.py` - Remove `test_gui_modules_healthy`, `test_gui_modules_failed` tests
- [ ] **Update** `tests/test_master_logging.py` - Remove LogCategory.GUI references

---

## Phase 4: Clean Up Dependencies

**Priority**: HIGH
**Estimated Hours**: 4 hours
**Dependencies**: Phase 1, Phase 2, Phase 3

### Python Dependencies (requirements.txt)
- [ ] **Remove** line: `# GUI dependencies (to be removed)`
- [ ] **Remove** line: `tkinter  # Built-in Python module`
- [ ] **Remove** line: `customtkinter>=5.0.0`
- [ ] **Verify** no other GUI-related packages remain

### Verify Web Dependencies Present
- [ ] **Verify** `Flask>=2.3.0` - Present ✓
- [ ] **Verify** `flask-cors>=4.0.0` - Present ✓
- [ ] **Verify** `flask-socketio>=5.3.0` - Present ✓
- [ ] **Add** if missing: Any additional web framework dependencies

### Frontend Dependencies (pokertool-frontend/package.json)
- [ ] **Verify** React dependencies are complete
- [ ] **Verify** Material-UI dependencies are complete
- [ ] **Verify** WebSocket/Socket.io client dependencies
- [ ] **Verify** Chart.js for visualizations
- [ ] **Verify** Redux Toolkit for state management

---

## Phase 5: Enhance Web Interface Backend

**Priority**: CRITICAL
**Estimated Hours**: 40 hours
**Dependencies**: Phase 1, Phase 2, Phase 3, Phase 4

### API Enhancement (src/pokertool/api.py)
- [ ] **Audit** current API endpoints in `src/pokertool/api.py`
- [ ] **Implement** missing REST endpoints for all GUI functionality:
  - [ ] `/api/game-state` - Get current game state
  - [ ] `/api/advice` - Get poker advice
  - [ ] `/api/hand-history` - Hand history CRUD
  - [ ] `/api/session` - Session management
  - [ ] `/api/stats` - Player statistics
  - [ ] `/api/opponent-tracking` - Opponent data
  - [ ] `/api/settings` - User settings
  - [ ] `/api/health` - System health check

### WebSocket Implementation
- [ ] **Implement** WebSocket server with Flask-SocketIO
- [ ] **Add** real-time events:
  - [ ] `table_state_update` - Table state changes
  - [ ] `advice_update` - New advice available
  - [ ] `opponent_update` - Opponent stats update
  - [ ] `session_update` - Session stats update
- [ ] **Add** WebSocket authentication
- [ ] **Add** reconnection handling
- [ ] **Add** heartbeat/ping-pong

### Service Layer Creation
- [ ] **Create** `src/pokertool/web_service.py` - Main web service orchestrator
- [ ] **Create** `src/pokertool/websocket_manager.py` - WebSocket connection manager
- [ ] **Create** `src/pokertool/api_handlers.py` - Request handlers for API endpoints
- [ ] **Refactor** existing functionality to be API-callable (no GUI dependencies)

### Authentication & Security
- [ ] **Implement** basic authentication (if needed for multi-user)
- [ ] **Add** CORS configuration
- [ ] **Add** rate limiting
- [ ] **Add** input validation for all endpoints

---

## Phase 6: Frontend Integration

**Priority**: HIGH
**Estimated Hours**: 24 hours
**Dependencies**: Phase 5

### React Components (pokertool-frontend/src/)
- [ ] **Verify** all necessary components exist:
  - [ ] AdvicePanel component (✓ Implemented in TODO v80)
  - [ ] TableView component
  - [ ] HandHistory component
  - [ ] SessionDashboard component (✓ Implemented in TODO v80)
  - [ ] OpponentStats component (✓ Implemented in TODO v80)
  - [ ] SettingsPanel component (✓ Implemented in TODO v80)

### API Integration
- [ ] **Implement** API client service (`services/api.ts`)
- [ ] **Implement** WebSocket client service (`services/websocket.ts`)
- [ ] **Add** error handling and retry logic
- [ ] **Add** loading states for all API calls

### State Management (Redux - ✓ Implemented in TODO v80)
- [ ] **Verify** Redux store is properly configured
- [ ] **Verify** all slices are implemented (game, advice, session, settings)
- [ ] **Test** state persistence to localStorage

### Testing
- [ ] **Create** frontend unit tests (Jest)
- [ ] **Create** integration tests with mock API
- [ ] **Create** E2E tests (Cypress or Playwright)

---

## Phase 7: Update Documentation

**Priority**: MEDIUM
**Estimated Hours**: 8 hours
**Dependencies**: Phase 1-6

### User Documentation
- [ ] **Update** `README.md` - Remove GUI launch instructions, add web interface instructions
- [ ] **Update** `docs/QUICKSTART_TABLE_TAB.md` - Web-only quickstart
- [ ] **Update** `docs/FEATURES.md` - Remove GUI features, emphasize web features
- [ ] **Update** `docs/GUI_IMPROVEMENTS_v81.md` - Archive or remove (GUI-specific)
- [ ] **Update** `docs/GUI_REWORK_SUMMARY.md` - Archive or remove
- [ ] **Update** `docs/GUI_BLADE_FUNCTIONALITY.md` - Archive or remove
- [ ] **Update** `docs/COMPACT_LIVE_ADVICE.md` - Update for web interface

### Technical Documentation
- [ ] **Create** `docs/WEB_API_REFERENCE.md` - Complete API documentation
- [ ] **Create** `docs/WEBSOCKET_PROTOCOL.md` - WebSocket protocol documentation
- [ ] **Create** `docs/FRONTEND_ARCHITECTURE.md` - React app architecture
- [ ] **Update** `docs/API_DOCUMENTATION.md` - Ensure up-to-date

### Development Guides
- [ ] **Update** `docs/TESTING.md` - Remove GUI test instructions, add web test instructions
- [ ] **Update** `docs/CODE_OF_CONDUCT.md` - If GUI-specific references exist
- [ ] **Update** `docs/CODEBASE_STATUS_REPORT.md` - Reflect new web-only architecture

---

## Phase 8: Update Launch Scripts & Entry Points

**Priority**: HIGH
**Estimated Hours**: 6 hours
**Dependencies**: Phase 5

### Launch Scripts
- [ ] **Remove** Any GUI-specific launch scripts in root directory
- [ ] **Create** `start_web.sh` (macOS/Linux) - Start web server
- [ ] **Create** `start_web.ps1` (Windows) - Start web server
- [ ] **Create** `start_web.bat` (Windows alternative)
- [ ] **Update** `scripts/activate_pokertool.sh` - Web-only activation

### Entry Points
- [ ] **Update** `src/pokertool/__main__.py` - Launch web server instead of GUI
- [ ] **Update** `src/pokertool/cli.py` - Remove GUI launch option, add web server commands
- [ ] **Create** web server start command: `python -m pokertool --web`

### Package Configuration
- [ ] **Update** `pyproject.toml` - Update entry points to web-only
- [ ] **Update** `setup.py` (if exists) - Update entry points

---

## Phase 9: Bootstrap Scripts Update

**Priority**: MEDIUM
**Estimated Hours**: 4 hours
**Dependencies**: Phase 4, Phase 8

### Bootstrap Scripts
- [ ] **Update** `scripts/first_run_mac.sh` - Remove GUI setup, add web server info
- [ ] **Update** `scripts/first_run_linux.sh` - Remove GUI setup, add web server info
- [ ] **Update** `scripts/first_run_windows.ps1` - Remove GUI setup, add web server info
- [ ] **Update** `docs/FIRST_RUN_GUIDE.md` - Web-only instructions

### Verification
- [ ] **Test** bootstrap on clean macOS system
- [ ] **Test** bootstrap on clean Linux system
- [ ] **Test** bootstrap on clean Windows system

---

## Phase 10: Remove Archive Directory (Optional)

**Priority**: LOW
**Estimated Hours**: 2 hours
**Dependencies**: Phase 1-9 complete

### Archive Review
- [ ] **Review** `archive/` directory contents
- [ ] **Verify** all important code is in main codebase
- [ ] **Verify** git history preserves all archive content
- [ ] **Decision**: Remove archive directory entirely
- [ ] **Execute** removal if approved

### Files in Archive (48+ files)
- All files in `archive/` directory appear to be old versions/experiments
- Most reference GUI/Tkinter extensively
- Recommendation: **REMOVE** entire directory after verification

---

## Phase 11: Final Cleanup & Verification

**Priority**: HIGH
**Estimated Hours**: 8 hours
**Dependencies**: All previous phases

### Code Search & Cleanup
- [ ] **Search** entire codebase for remaining `tkinter` references
- [ ] **Search** for `import tk` patterns
- [ ] **Search** for `.Tk()`, `.mainloop()` patterns
- [ ] **Search** for GUI-specific terminology that needs updating
- [ ] **Clean up** any missed references

### Imports Cleanup
- [ ] **Run** `grep -r "import tkinter" src/` - Should return 0 results
- [ ] **Run** `grep -r "from tkinter" src/` - Should return 0 results
- [ ] **Run** `grep -r "customtkinter" src/` - Should return 0 results

### Testing Full Stack
- [ ] **Start** web server
- [ ] **Verify** all API endpoints work
- [ ] **Verify** WebSocket connections work
- [ ] **Verify** frontend connects to backend
- [ ] **Test** all major features through web interface:
  - [ ] Game state detection
  - [ ] Advice generation
  - [ ] Hand history tracking
  - [ ] Session statistics
  - [ ] Opponent tracking
  - [ ] Settings management

### Performance Testing
- [ ] **Test** API response times (should be <100ms)
- [ ] **Test** WebSocket latency (should be <50ms)
- [ ] **Test** frontend rendering performance
- [ ] **Profile** memory usage (should be stable)
- [ ] **Test** concurrent connections (if multi-user)

### Documentation Review
- [ ] **Verify** all documentation updated
- [ ] **Verify** no broken links
- [ ] **Verify** README is accurate
- [ ] **Create** migration guide for existing users

---

## Phase 12: Migration Path for Existing Users

**Priority**: MEDIUM
**Estimated Hours**: 4 hours
**Dependencies**: All previous phases

### Migration Documentation
- [ ] **Create** `docs/MIGRATION_GUIDE.md` - Guide for users upgrading from GUI version
- [ ] **Document** feature parity between GUI and web
- [ ] **Document** any features not yet available in web
- [ ] **Document** how to access web interface
- [ ] **Create** FAQ for common migration questions

### Backward Compatibility (Optional)
- [ ] **Decision**: Support GUI temporarily or remove immediately?
- [ ] If temporary support: **Add** feature flag to enable/disable GUI
- [ ] If immediate removal: **Communicate** clearly to users

### User Communication
- [ ] **Create** announcement of web-only architecture
- [ ] **Highlight** benefits (better UX, mobile support, etc.)
- [ ] **Provide** timeline for support

---

## Success Criteria

### Functional Requirements
- ✅ Zero Tkinter imports in codebase
- ✅ Zero GUI-specific files in src/pokertool/
- ✅ All functionality accessible via web interface
- ✅ WebSocket real-time updates working
- ✅ All tests passing (web-only tests)
- ✅ Documentation complete and accurate

### Performance Requirements
- ✅ API response time <100ms
- ✅ WebSocket latency <50ms
- ✅ Frontend load time <3s
- ✅ No memory leaks
- ✅ Stable under load

### Quality Requirements
- ✅ No broken imports
- ✅ No dead code
- ✅ All dependencies justified
- ✅ Clean git history
- ✅ Comprehensive tests

---

## Risk Assessment

### High Risk
1. **Feature Parity**: Ensuring all GUI features are available in web
   - Mitigation: Create feature comparison checklist
2. **User Adoption**: Users may resist change from GUI to web
   - Mitigation: Clear communication, migration guide, benefits explanation
3. **Testing Gaps**: May miss GUI-dependent code paths
   - Mitigation: Comprehensive code search, grep patterns

### Medium Risk
1. **Performance**: Web interface may be slower than native GUI
   - Mitigation: Performance testing, optimization
2. **Dependencies**: Web dependencies may introduce new issues
   - Mitigation: Thorough testing, gradual rollout

### Low Risk
1. **Documentation**: Docs may fall out of date
   - Mitigation: Update docs as part of each phase
2. **Rollback**: Hard to rollback after major changes
   - Mitigation: Git branches, feature flags

---

## Timeline Estimate

### Week 1 (40 hours)
- Phase 1: Remove Tkinter files (24h)
- Phase 2: Update references (16h)

### Week 2 (40 hours)
- Phase 3: Remove GUI tests (12h)
- Phase 4: Clean dependencies (4h)
- Phase 5: Enhance web backend (24h)

### Week 3 (40 hours)
- Phase 5: Enhance web backend (16h remaining)
- Phase 6: Frontend integration (24h)

### Week 4 (40 hours)
- Phase 6: Frontend integration (remaining)
- Phase 7: Documentation (8h)
- Phase 8: Launch scripts (6h)
- Phase 9: Bootstrap scripts (4h)
- Phase 10: Archive removal (2h)
- Phase 11: Final cleanup (8h)
- Phase 12: Migration guide (4h)
- Buffer for issues (8h)

**Total**: 160 hours (4 weeks at full-time pace)

---

## Next Steps

1. **Review this document** with team/stakeholders
2. **Get approval** for architecture change
3. **Create git branch** for refactoring work
4. **Start with Phase 1** (remove Tkinter files)
5. **Proceed incrementally** through phases
6. **Test thoroughly** at each phase
7. **Merge to main** when all phases complete

---

**Last Updated**: October 15, 2025, 10:17 PM
**Document Version**: 1.0
**Status**: READY FOR REVIEW
