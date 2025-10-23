# VersionHistory Regression Tests

## Purpose

These regression tests are designed to **FAIL LOUDLY** if any features are removed, moved, or changed in the VersionHistory component. This ensures no regressions slip through during development.

## Test Files

### 1. `VersionHistory.test.tsx` (35 tests)
Standard functionality tests covering:
- Component rendering
- Tab navigation
- Content display
- Accessibility
- Visual elements

### 2. `VersionHistory.regression.test.tsx` (20 CRITICAL tests)
**Regression detection tests** that will fail with clear error messages if:
- Any tab is removed or renamed
- Any critical content section is missing
- Tab switching functionality breaks
- Component fails to render

## How to Run

```bash
# Run all VersionHistory tests
cd pokertool-frontend
npm test -- VersionHistory

# Run only regression tests
npm test -- VersionHistory.regression.test.tsx

# Run with coverage
npm test -- --coverage VersionHistory
```

## Expected Behavior

### ✅ All Tests Passing = No Regressions
When all tests pass, it means:
- All 4 tabs are present (Current Version, Changelog, Release Notes, What's New)
- All critical content sections exist
- Tab switching works correctly
- Component renders properly

### 🚨 Test Failure = REGRESSION DETECTED
If any test fails, you will see:
```
🚨 REGRESSION DETECTED: [specific issue]
```

**DO NOT modify the test to make it pass** without investigating:
1. Why did the feature get removed/moved?
2. Was this intentional?
3. Is there a replacement feature?
4. Should we update documentation?

## Critical Features Monitored

### Tabs (Must have exactly 4)
1. **Current Version** - Shows version info, release type, build number
2. **Changelog** - Lists recent changes across versions
3. **Release Notes** - Documents key features, improvements, issues
4. **What's New** - Highlights, explanations, getting started

### Current Version Tab Content
- Version Number card
- Release Type card
- Build Number card
- Version Components list

### Changelog Tab Content
- "Recent Changes" heading
- v100.3.1 (current) release
- v100.0.0 (major) release
- Previous versions

### Release Notes Tab Content
- Key Features section
- Technical Improvements section
- Known Issues section
- Breaking Changes section

### What's New Tab Content
- Highlights section
- "Why These Changes Matter" section
- Getting Started section

## Maintenance

### When to Update Tests

**Update regression tests when:**
- Intentionally adding new tabs (adjust count check)
- Intentionally renaming tabs (update name checks)
- Intentionally restructuring content (update content checks)

**Document the change in:**
- This file (REGRESSION_TESTS.md)
- Git commit message
- Changelog

### Adding New Regression Tests

When adding new features to VersionHistory:
1. Add corresponding regression test
2. Include clear error message with 🚨 emoji
3. Document what the test protects against

## Test Output Examples

### Successful Run
```
PASS src/components/__tests__/VersionHistory.regression.test.tsx
  VersionHistory - CRITICAL REGRESSION DETECTION
    🚨 TAB PRESENCE - All 4 Tabs MUST Exist
      ✓ REGRESSION CHECK: Must have exactly 4 tabs (48ms)
      ✓ REGRESSION CHECK: "Current Version" tab MUST exist (23ms)
      ✓ REGRESSION CHECK: "Changelog" tab MUST exist (21ms)
      ...
```

### Failure Example
```
FAIL src/components/__tests__/VersionHistory.regression.test.tsx
  ● REGRESSION CHECK: "Changelog" tab MUST exist

    🚨 REGRESSION DETECTED: "Changelog" tab is missing!
    Available tabs: Current Version, Release Notes, What's New

    This indicates the Changelog tab has been removed or renamed.
```

## Integration with CI/CD

These tests should be:
- ✅ Run on every commit
- ✅ Required to pass before merging to develop/master
- ✅ Monitored in CI/CD pipeline
- ✅ Reported in pull request checks

## Contact

If you encounter a regression test failure and need help:
1. Check git log to see what changed
2. Review the specific error message
3. Investigate whether the change was intentional
4. If needed, consult with the team before modifying tests
