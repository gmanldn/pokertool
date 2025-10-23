# PokerTool Program History Database

## Overview

The Program History Database is a comprehensive tracking system designed to prevent regressions, maintain complete version control, and ensure no features are accidentally removed without explicit approval and warnings.

## Architecture

### Core Components

1. **SQLite Database** - Persistent storage for all features, versions, and changes
2. **FeatureManager** - Manages feature lifecycle and test linking
3. **VersionManager** - Handles version creation and change tracking
4. **RegressionDetector** - Automatically detects potential issues
5. **CLI Tools** - Command-line interface for management tasks

### Database Tables

#### `versions`
Tracks all application releases with semantic versioning.

```sql
columns: id, version_string, major, minor, patch, release_type,
         release_date, description, is_current, breaking_changes,
         deprecated_features, new_features
```

#### `features`
Complete inventory of all features with status and protection level.

```sql
columns: id, name, description, category_id, status, risk_level,
         component_type, introduced_version, deprecated_version,
         removed_version, file_path, is_core_feature, is_gui_feature,
         dependencies, test_coverage_percent
```

#### `feature_tests`
Links tests to the features they protect.

```sql
columns: id, feature_id, test_file_path, test_name, test_count,
         coverage_type, is_critical, last_run_date, last_run_status
```

#### `regression_alerts`
Tracks potential regressions and issues.

```sql
columns: id, feature_id, alert_type, severity, message, resolution,
         is_resolved, created_at, resolved_at
```

#### `feature_removal_log`
Audit trail for all feature removal requests with warnings.

```sql
columns: id, feature_id, removal_requested_by, removal_requested_date,
         removal_warning_sent, warning_level, tests_protecting_feature,
         alternative_feature, migration_path, removal_approved_date,
         approved_by, actually_removed, removed_date
```

#### `version_changes`
Documents what changed in each version.

```sql
columns: id, version_id, feature_id, component_id, change_type,
         change_description, impact_level, requires_migration,
         migration_notes, git_commit
```

## Feature Categories

All features are categorized for proper protection levels:

- **Core Functionality** - Essential application features (CRITICAL)
- **User Interface** - Frontend components (HIGH)
- **API Endpoints** - REST API endpoints (CRITICAL)
- **Database** - Database schema operations (CRITICAL)
- **Authentication** - User auth systems (CRITICAL)
- **Performance** - Optimization features (MEDIUM)
- **Analytics** - Tracking features (LOW)
- **Testing Infrastructure** - Test framework (HIGH)
- **Poker Logic** - Core poker calculations (CRITICAL)
- **Backend Services** - Background services (HIGH)

## Feature Status Types

Features can have the following statuses:

- **active** - Currently in use and maintained
- **deprecated** - Marked for future removal
- **experimental** - Under development/testing
- **removed** - Completely removed from codebase
- **disabled** - Disabled but code still exists
- **in_development** - Currently being developed

## Component Types

Features are classified by implementation type:

- **frontend** - React components, UI
- **backend** - Python services, handlers
- **api** - REST/gRPC endpoints
- **database** - Database tables, schemas
- **utility** - Helper functions, utilities
- **service** - Services, managers, controllers

## Risk Levels

Each feature has an associated risk level:

- **low** - Minor features, low impact if broken
- **medium** - Standard features
- **high** - Important functionality
- **critical** - Core features that everything depends on

## CLI Commands

### Version Management

```bash
# Create a new major version
npm run program-history version:create major -d "Version description"

# Create a new minor version
npm run program-history version:create minor -d "Version description"

# Create a new patch version
npm run program-history version:create patch -d "Version description"
```

### Feature Management

```bash
# List all features
npm run program-history feature:list

# List only core features
npm run program-history feature:list --core

# List only GUI features
npm run program-history feature:list --gui

# Filter by status
npm run program-history feature:list --filter active

# Filter by component type
npm run program-history feature:list --type frontend
```

### Regression Detection

```bash
# Run regression detection
npm run program-history regression:detect

# Generate detailed regression report
npm run program-history regression:detect --detailed
```

### Test Coverage

```bash
# Generate test coverage report
npm run program-history coverage:report
```

### Feature Removal

```bash
# Request feature removal (with warning)
npm run program-history feature:remove-request "Feature Name"

# Request with critical warning
npm run program-history feature:remove-request "Feature Name" --warning critical

# Request with extreme warning (for core features)
npm run program-history feature:remove-request "Feature Name" --warning extreme
```

### Database Management

```bash
# Initialize the database
npm run program-history db:init

# Reset the database (WARNING: destructive)
npm run program-history db:reset --force
```

### Reports

```bash
# Generate comprehensive status report
npm run program-history report:full
```

## Regression Detection System

The system automatically detects:

1. **Removed Features** - Features marked as active but with removal versions
2. **Missing Tests** - Critical features without test coverage
3. **Orphaned Components** - Unused exported components
4. **Dependency Issues** - Circular dependencies or missing dependencies
5. **Coverage Drops** - Test coverage declining below thresholds
6. **File Removals** - Referenced files missing from disk

### Example Regression Detection Report

```
════════════════════════════════════════════════════════════════════════════════
REGRESSION DETECTION REPORT - 2025-10-23T21:00:00.000Z
════════════════════════════════════════════════════════════════════════════════

SUMMARY
────────────────────────────────────────────────────────────────────────────────
Total Issues Found: 5
🚨 Critical: 2
⚠️ High: 2
⚠️ Medium: 1
ℹ️ Low: 0

DETAILED FINDINGS
────────────────────────────────────────────────────────────────────────────────

CRITICAL SEVERITY ISSUES:
  • Critical feature 'Version History Tab' has no test coverage
    → Recommendation: Add comprehensive tests for frontend feature: Version History Tab
  • Feature 'Hand Evaluation' is marked as active but has a removed_version (v99.0.0)
    → This indicates a potential regression

HIGH SEVERITY ISSUES:
  • Test coverage for 'SmartHelper' dropped from 85% to 65%
  • Component 'LegacyAPI' may be unused (src/services/legacy/api.ts)

════════════════════════════════════════════════════════════════════════════════
```

## Test Coverage Tracking

### Linking Tests to Features

When you write tests, link them to features:

```typescript
// In your test file
import { featureManager } from './src/database/FeatureManager';

// Link test to feature
await featureManager.linkTestToFeature(
  featureId,
  'src/components/__tests__/VersionHistory.regression.test.tsx',
  'Version History Tab Present',
  true  // is_critical
);
```

### Coverage Report Example

```
📊 Test Coverage Report

🔴 ✓ Version History (4 tests)
🔴 ✓ Detection Log Tab (8 tests)
🔴 ✓ Tables Tab (6 tests)
⚪ ✓ SmartHelper (12 tests)
🔴 ✗ Autopilot (0 tests) ← Critical feature without tests
⚪ ✓ Analytics (3 tests)

────────────────────────────────────────────────────────────────────────────────
Total Features: 47
With Tests: 41
Without Tests: 6
Critical Features without Tests: 1 ⚠️
```

## Feature Removal Workflow

### When Removing a Feature

1. **Request Removal** with appropriate warning level:
   ```bash
   npm run program-history feature:remove-request "FeatureName" --warning extreme
   ```

2. **System automatically:**
   - Lists all tests protecting the feature
   - Assesses impact level
   - Creates removal request log
   - Issues appropriate warnings

3. **Removal warning output:**
   ```
   ⚠️ REMOVAL WARNING [EXTREME] for feature: Version History Tab
      Tests protecting this feature: VersionHistory.regression.test.tsx, VersionHistoryTab.visibility.test.tsx
      🚨 EXTREME: This is a core feature! Removal will break the application.
   ```

4. **Approval process:**
   - Document why removal is necessary
   - Update tests to reflect new state
   - Remove feature code
   - Record actual removal with timestamp

5. **Tests prevent accidental removal:**
   - If someone tries to remove feature without updating tests
   - Tests will FAIL immediately
   - Developers see which tests are protecting the feature

## Preventing Regressions

### Multi-Layer Protection

1. **Database constraints** - Features marked as core/critical
2. **Test requirements** - Critical features must have tests
3. **Removal warnings** - Explicit approval required for removal
4. **Automatic detection** - Regressions detected on test runs
5. **Change tracking** - Every change recorded with version

### Example Protection in Action

**Scenario:** Developer tries to remove Version History tab

```
1. Tests run: ✓ VersionHistory.regression.test.tsx
   - 13 regression tests including:
     - "Current Version tab MUST exist"
     - "Changelog tab MUST exist"
     - "Version History MUST remain visible after 5 navigation cycles"

2. Tests run: ✓ VersionHistoryTab.visibility.test.tsx
   - 27 critical integration tests

3. Tests run: ✓ CanonicalTabs.regression.test.tsx
   - "Version History Tab MUST always be present in navigation"
   - "All critical tabs (Tables, Detection Log, Version History) MUST be visible"

4. If feature is removed: 🚨 ALL TESTS FAIL

5. Developer sees:
   ✗ Version History present in navigation (FAILED)
   ✗ Version History route accessible (FAILED)
   ... (49 more failures)

6. Database alerts:
   🚨 CRITICAL: Regression detected in feature: "Version History"
      Removal without test updates is not allowed.
```

## Integration with Git

The system integrates with Git to track:

- Commit hashes for each change
- Author of each change
- Files modified for each feature
- Branch information
- Tag information for versions

## Generating Release Notes

```typescript
const versionManager = new VersionManager(db);
const releaseNotes = await versionManager.generateReleaseNotes('v100.3.1');
console.log(releaseNotes);
```

**Example output:**

```markdown
# Release Notes - v100.3.1

**Release Date:** 2025-10-23
**Type:** stable
**Description:** Version History Tab Protection & Comprehensive Test Coverage

## ✨ Added
- Version History Tab with 4 internal tabs
- 27 new critical visibility tests
- 5 new canonical tabs tests

## 🔧 Modified
- Enhanced VersionHistory component with better layout
- Updated Navigation to include Version History

## 📦 Deprecated
- Legacy hand history system (use new Version History)

## ⚠️ Breaking Changes
- None in this release
```

## Best Practices

### When Adding Features

1. Add feature to database first
2. Link tests to feature
3. Mark as core/critical if appropriate
4. Document dependencies
5. Record git commit

### When Modifying Features

1. Record modification in version_changes
2. Update feature status if needed
3. Ensure tests still pass
4. Link new tests if adding test coverage

### When Deprecating Features

1. Change status to "deprecated"
2. Record deprecation version
3. Suggest alternative
4. Keep tests for backward compatibility

### When Removing Features

1. Use `feature:remove-request` command
2. Get explicit approval
3. Wait for warning period
4. Remove feature code
5. Remove tests
6. Record removal with timestamp

## Troubleshooting

### Issue: "Critical feature without tests" warning

**Solution:**
```bash
# Add tests for the feature
npm run program-history coverage:report  # See which features need tests

# Then link your tests:
npm run program-history feature:tests-add "Feature Name" "path/to/test.tsx"
```

### Issue: "Circular dependency detected"

**Solution:**
Review the feature dependencies and refactor to eliminate circular references.

```bash
npm run program-history regression:detect --detailed  # Find the circular dependency
```

### Issue: "Feature file is missing"

**Solution:**
Either restore the file or update the database if intentionally removed:

```bash
# If feature was truly removed, request removal through proper workflow
npm run program-history feature:remove-request "Feature Name" --warning critical
```

## Maintenance

### Regular Tasks

- **Daily:** Run `regression:detect` to check for issues
- **Weekly:** Review `coverage:report` for uncovered features
- **Per Release:** Use `version:create` and record all changes
- **Per Feature:** Link tests when adding/modifying features

### Performance Optimization

The database is indexed on:
- Feature status
- Feature category
- Component type
- Core features flag
- GUI features flag
- Version changes
- Test coverage

## Future Enhancements

1. **Performance Metrics** - Track performance regression
2. **API Schema Tracking** - Track API endpoint changes
3. **Database Migration Tool** - Automated migration detection
4. **Slack Notifications** - Alert on critical regressions
5. **Dashboard UI** - Web interface for viewing features
6. **Git Hooks** - Automatic feature registration on commit

## Summary

The Program History Database provides:

✅ **Complete feature inventory** - Every feature tracked
✅ **Regression prevention** - Automatic detection of issues
✅ **Test requirement enforcement** - Critical features must have tests
✅ **Removal protection** - Features can't be removed without explicit approval
✅ **Change tracking** - Every change recorded with version
✅ **Version management** - Easy semantic versioning
✅ **Comprehensive reports** - Visibility into application state

This system eliminates the chance of accidental feature removal and makes it impossible to introduce regressions without immediate test failures alerting developers.
