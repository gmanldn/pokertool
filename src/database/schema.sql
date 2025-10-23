-- POKERTOOL-HEADER-START
-- ---
-- schema: database.v1
-- project: pokertool
-- file: src/database/schema.sql
-- version: v100.3.1
-- last_commit: '2025-10-23T00:00:00+01:00'
-- fixes:
-- - date: '2025-10-23'
--   summary: Comprehensive ProgramHistory database schema for regression prevention
-- ---
-- POKERTOOL-HEADER-END

-- ============================================================================
-- POKERTOOL PROGRAM HISTORY DATABASE SCHEMA
-- ============================================================================
-- This database tracks every feature, every test, and every version change
-- to prevent regressions and maintain a complete audit trail.
-- ============================================================================

-- ============================================================================
-- 1. VERSIONS TABLE - Track all application releases
-- ============================================================================
CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_string TEXT NOT NULL UNIQUE,
    major INTEGER NOT NULL,
    minor INTEGER NOT NULL,
    patch INTEGER NOT NULL,
    release_type TEXT CHECK(release_type IN ('alpha', 'beta', 'rc', 'stable')) DEFAULT 'stable',
    release_date TEXT NOT NULL,
    description TEXT,
    is_current BOOLEAN DEFAULT 0,
    breaking_changes TEXT,
    deprecated_features TEXT,
    new_features TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. FEATURE CATEGORIES - Classify features by type
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    risk_level TEXT CHECK(risk_level IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
    protection_level TEXT CHECK(protection_level IN ('standard', 'enhanced', 'critical')) DEFAULT 'standard',
    requires_test BOOLEAN DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. FEATURE STATUS - Track feature state transitions
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_status_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL UNIQUE,
    description TEXT,
    allows_removal BOOLEAN DEFAULT 0,
    requires_warning BOOLEAN DEFAULT 1
);

-- ============================================================================
-- 4. FEATURES TABLE - Core feature inventory
-- ============================================================================
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    category_id INTEGER NOT NULL,
    status TEXT DEFAULT 'active',
    risk_level TEXT CHECK(risk_level IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
    component_type TEXT CHECK(component_type IN ('frontend', 'backend', 'api', 'database', 'utility', 'service')) NOT NULL,
    introduced_version TEXT,
    deprecated_version TEXT,
    removed_version TEXT,
    file_path TEXT,
    is_core_feature BOOLEAN DEFAULT 0,
    is_gui_feature BOOLEAN DEFAULT 0,
    dependencies TEXT,
    documentation_url TEXT,
    test_coverage_percent REAL DEFAULT 0,
    last_tested_version TEXT,
    removal_warning_required BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES feature_categories(id)
);

-- ============================================================================
-- 5. COMPONENTS TABLE - Track UI components and modules
-- ============================================================================
CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT CHECK(type IN ('component', 'service', 'utility', 'hook', 'module')) NOT NULL,
    file_path TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    introduced_version TEXT,
    is_core BOOLEAN DEFAULT 0,
    is_exported BOOLEAN DEFAULT 1,
    dependencies TEXT,
    dependents TEXT,
    test_file_path TEXT,
    line_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES feature_categories(id)
);

-- ============================================================================
-- 6. FEATURE TESTS - Link features to their test files
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL,
    test_file_path TEXT NOT NULL,
    test_name TEXT,
    test_count INTEGER DEFAULT 1,
    coverage_type TEXT CHECK(coverage_type IN ('unit', 'integration', 'e2e', 'regression')) DEFAULT 'unit',
    is_critical BOOLEAN DEFAULT 0,
    last_run_date TEXT,
    last_run_status TEXT CHECK(last_run_status IN ('pass', 'fail', 'skip')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feature_id) REFERENCES features(id)
);

-- ============================================================================
-- 7. REGRESSION ALERTS - Alert when features are at risk
-- ============================================================================
CREATE TABLE IF NOT EXISTS regression_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL,
    alert_type TEXT CHECK(alert_type IN ('missing_test', 'removed_feature', 'changed_api', 'dependency_issue', 'coverage_drop')) NOT NULL,
    severity TEXT CHECK(severity IN ('warning', 'critical')) DEFAULT 'warning',
    message TEXT NOT NULL,
    resolution TEXT,
    is_resolved BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,
    FOREIGN KEY (feature_id) REFERENCES features(id)
);

-- ============================================================================
-- 8. VERSION CHANGES - Track what changed between versions
-- ============================================================================
CREATE TABLE IF NOT EXISTS version_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    feature_id INTEGER,
    component_id INTEGER,
    change_type TEXT CHECK(change_type IN ('added', 'modified', 'removed', 'deprecated', 'restored')) NOT NULL,
    change_description TEXT NOT NULL,
    impact_level TEXT CHECK(impact_level IN ('low', 'medium', 'high', 'breaking')) DEFAULT 'medium',
    requires_migration BOOLEAN DEFAULT 0,
    migration_notes TEXT,
    git_commit TEXT,
    changed_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (version_id) REFERENCES versions(id),
    FOREIGN KEY (feature_id) REFERENCES features(id),
    FOREIGN KEY (component_id) REFERENCES components(id)
);

-- ============================================================================
-- 9. FEATURE DEPENDENCIES - Track feature relationships
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL,
    depends_on_feature_id INTEGER NOT NULL,
    dependency_type TEXT CHECK(dependency_type IN ('required', 'optional', 'conflicts')) DEFAULT 'required',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feature_id) REFERENCES features(id),
    FOREIGN KEY (depends_on_feature_id) REFERENCES features(id)
);

-- ============================================================================
-- 10. FEATURE REMOVAL LOG - Audit trail for feature removals
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_removal_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL,
    removal_requested_by TEXT NOT NULL,
    removal_requested_date TEXT NOT NULL,
    removal_warning_sent BOOLEAN DEFAULT 1,
    warning_level TEXT CHECK(warning_level IN ('warning', 'critical', 'extreme')) DEFAULT 'warning',
    affected_versions TEXT,
    tests_protecting_feature TEXT,
    alternative_feature TEXT,
    migration_path TEXT,
    removal_approved_date TEXT,
    approved_by TEXT,
    actually_removed BOOLEAN DEFAULT 0,
    removed_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 11. VERSION FEATURE MAPPING - Map features to versions
-- ============================================================================
CREATE TABLE IF NOT EXISTS version_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    feature_id INTEGER NOT NULL,
    was_added BOOLEAN DEFAULT 0,
    was_modified BOOLEAN DEFAULT 0,
    was_removed BOOLEAN DEFAULT 0,
    was_deprecated BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (version_id) REFERENCES versions(id),
    FOREIGN KEY (feature_id) REFERENCES features(id),
    UNIQUE(version_id, feature_id)
);

-- ============================================================================
-- 12. FEATURE HISTORY - Complete audit trail of every feature
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL,
    version_string TEXT NOT NULL,
    status_before TEXT,
    status_after TEXT,
    description TEXT,
    changed_by TEXT,
    change_reason TEXT,
    is_breaking_change BOOLEAN DEFAULT 0,
    requires_migration BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feature_id) REFERENCES features(id)
);

-- ============================================================================
-- 13. TEST COVERAGE METRICS - Track test coverage per feature
-- ============================================================================
CREATE TABLE IF NOT EXISTS test_coverage_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_id INTEGER NOT NULL,
    version_string TEXT NOT NULL,
    total_test_count INTEGER DEFAULT 0,
    passing_tests INTEGER DEFAULT 0,
    failing_tests INTEGER DEFAULT 0,
    skipped_tests INTEGER DEFAULT 0,
    coverage_percent REAL DEFAULT 0,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feature_id) REFERENCES features(id)
);

-- ============================================================================
-- 14. COMPONENT DEPENDENCIES - Track component relationships
-- ============================================================================
CREATE TABLE IF NOT EXISTS component_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL,
    depends_on_component_id INTEGER,
    depends_on_library TEXT,
    dependency_type TEXT CHECK(dependency_type IN ('internal', 'external', 'peer', 'dev')) DEFAULT 'internal',
    is_critical BOOLEAN DEFAULT 0,
    version_constraint TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (component_id) REFERENCES components(id),
    FOREIGN KEY (depends_on_component_id) REFERENCES components(id)
);

-- ============================================================================
-- 15. REGRESSION HISTORY - Track resolved and unresolved regressions
-- ============================================================================
CREATE TABLE IF NOT EXISTS regression_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regression_alert_id INTEGER,
    version_introduced TEXT NOT NULL,
    version_fixed TEXT,
    severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
    description TEXT NOT NULL,
    root_cause TEXT,
    prevention_notes TEXT,
    test_added_to_prevent BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    fixed_at TEXT,
    FOREIGN KEY (regression_alert_id) REFERENCES regression_alerts(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_features_status ON features(status);
CREATE INDEX IF NOT EXISTS idx_features_category ON features(category_id);
CREATE INDEX IF NOT EXISTS idx_features_component_type ON features(component_type);
CREATE INDEX IF NOT EXISTS idx_features_is_core ON features(is_core_feature);
CREATE INDEX IF NOT EXISTS idx_features_is_gui ON features(is_gui_feature);

CREATE INDEX IF NOT EXISTS idx_version_changes_version ON version_changes(version_id);
CREATE INDEX IF NOT EXISTS idx_version_changes_feature ON version_changes(feature_id);
CREATE INDEX IF NOT EXISTS idx_version_changes_type ON version_changes(change_type);

CREATE INDEX IF NOT EXISTS idx_feature_tests_feature ON feature_tests(feature_id);
CREATE INDEX IF NOT EXISTS idx_feature_tests_critical ON feature_tests(is_critical);

CREATE INDEX IF NOT EXISTS idx_regression_alerts_feature ON regression_alerts(feature_id);
CREATE INDEX IF NOT EXISTS idx_regression_alerts_severity ON regression_alerts(severity);

CREATE INDEX IF NOT EXISTS idx_components_type ON components(type);
CREATE INDEX IF NOT EXISTS idx_components_is_core ON components(is_core);

CREATE INDEX IF NOT EXISTS idx_feature_history_feature ON feature_history(feature_id);
CREATE INDEX IF NOT EXISTS idx_feature_history_version ON feature_history(version_string);

CREATE INDEX IF NOT EXISTS idx_regression_history_severity ON regression_history(severity);

-- ============================================================================
-- SEED DATA - Default Categories & Status Types
-- ============================================================================

-- Feature Categories
INSERT OR IGNORE INTO feature_categories (name, description, risk_level, protection_level) VALUES
('Core Functionality', 'Essential application features that everything depends on', 'critical', 'critical'),
('User Interface', 'Frontend components and UI elements', 'high', 'enhanced'),
('API Endpoints', 'REST API and data endpoints', 'critical', 'critical'),
('Database', 'Database schema and operations', 'critical', 'critical'),
('Authentication', 'User authentication and authorization', 'critical', 'critical'),
('Performance', 'Performance optimization features', 'medium', 'enhanced'),
('Analytics', 'Analytics and tracking features', 'low', 'standard'),
('Testing Infrastructure', 'Test framework and testing tools', 'high', 'critical'),
('Poker Logic', 'Core poker hand evaluation and logic', 'critical', 'critical'),
('Backend Services', 'Background services and workers', 'high', 'enhanced');

-- Status Types
INSERT OR IGNORE INTO feature_status_types (status, description, allows_removal, requires_warning) VALUES
('active', 'Feature is actively used and maintained', 0, 0),
('deprecated', 'Feature is marked for removal but still functional', 1, 1),
('experimental', 'Feature is under development and testing', 0, 0),
('removed', 'Feature has been completely removed', 1, 1),
('disabled', 'Feature is disabled but code still exists', 1, 1),
('in_development', 'Feature is currently being developed', 0, 0);
