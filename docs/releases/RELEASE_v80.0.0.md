# Release Notes - v80.0.0
> Issue Register: Use `python new_task.py` to append GUID-tagged entries to `docs/TODO.md`; manual edits are rejected and historical backlog lives in `docs/TODO_ARCHIVE.md`.

**Release Date:** 2025-10-15

## Overview

Version 80.0.0 integrates the Smart Advice Panel into the Table View and enhances the startup script to properly cleanup frontend instances before launching.

## Features

### 🎯 Smart Advice Integration (WEB-ADVICE-007)

**Component:** `table_view_advice`

Integrated the AdvicePanel component into the TableView for real-time poker advice:

- **Real-time WebSocket Integration**: Connected TableView to WebSocket for live advice updates
- **Prominent Placement**: Added AdvicePanel in dedicated grid column next to table display
- **Responsive Design**: Compact mode automatically activates on mobile devices
- **Seamless UX**: Advice panel updates in real-time without disrupting table view

**Files Modified:**
- `pokertool-frontend/src/components/TableView.tsx`

**Key Features:**
- Action recommendations (FOLD, CALL, RAISE, CHECK, ALL-IN)
- Confidence level visualization with progress bars
- Expected Value (EV) display with color coding
- Pot odds and hand strength metrics
- Reasoning explanations with expandable sections
- Low confidence warnings
- Smooth animations and throttled updates

### 🚀 Enhanced Frontend Cleanup (STARTUP-003)

**Component:** `frontend_cleanup`

Enhanced the startup script to properly terminate React dev servers:

- **Cross-Platform Support**: Handles both Windows and Unix-based systems
- **React Dev Server Detection**: Identifies and terminates `react-scripts` processes
- **Node.js Process Management**: Cleans up node.exe instances on Windows
- **Pattern-Based Cleanup**: Unix systems use process patterns to find React servers
- **Graceful Shutdown**: Ensures clean state before launching new instances

**Files Modified:**
- `scripts/start.py`

**Cleanup Patterns Added:**
- `node.*react-scripts`
- `react-scripts start`
- Windows: node.exe processes

## Technical Improvements

### Frontend Build
- **Build Size**: 244.21 kB (+4.79 kB from v79.0.0)
- **No Breaking Changes**: All existing features remain functional
- **TypeScript Compliance**: Full type safety maintained
- **Minimal Warnings**: Only non-critical unused variable warnings

### Process Management
- **SIGTERM First**: Attempts graceful shutdown before force kill
- **SIGKILL Fallback**: Ensures stuck processes are terminated
- **Timeout Protection**: All cleanup operations have timeouts
- **Error Resilience**: Continues startup even if cleanup partially fails

## Component Status

### New Components (v80.0.0)

| Component | Version | Status | Features |
|-----------|---------|--------|----------|
| table_view_advice | 1.0.0 | Active | WEB-ADVICE-007 |
| frontend_cleanup | 1.0.0 | Active | STARTUP-003 |

### Updated Statistics

- **Total Features**: 52 (+2 from v79.0.0)
- **Total Components**: 24 (+2 from v79.0.0)
- **Web Features**: 12 (+1 from v79.0.0)
- **Last Audit**: 2025-10-15

## Testing

### Build Validation
```bash
cd pokertool-frontend && npm run build
```
- ✅ Successful compilation
- ✅ No errors
- ✅ Optimized production build
- ⚠️ Minor eslint warnings (non-critical)

### Integration Testing
- ✅ AdvicePanel renders correctly in TableView
- ✅ WebSocket connection established
- ✅ Responsive layout adapts to mobile
- ✅ Cleanup script terminates old processes

## Migration Notes

### For Developers

No migration required. This is a backwards-compatible release.

### For Users

When restarting the application:
1. Old React dev servers will be automatically terminated
2. Fresh instances will launch with latest AdvicePanel integration
3. Navigate to Table View to see the new Smart Advice Panel

## Known Issues

None reported in this release.

## Dependencies

No new dependencies added. Uses existing packages:
- React 18.2.0
- Material-UI 5.14.18
- Redux Toolkit 1.9.7
- React Router 6.19.0

## Future Enhancements

Potential improvements for future releases:
- Advanced advice filtering and customization
- Historical advice tracking and analysis
- Multi-table advice aggregation
- Advice export and sharing features

## Contributors

- Enhanced by PokerTool Development Team

---

**Previous Version:** v79.0.0  
**Next Version:** TBD

For full feature documentation, see:
- [Web Improvements v76.0.0](./RELEASE_v76.0.0.md)
- [State Management v78.0.0](./RELEASE_v78.0.0.md)
- [Bet Sizing v79.0.0](./RELEASE_v79.0.0.md)
