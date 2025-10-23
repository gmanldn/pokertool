/* POKERTOOL-HEADER-START
---
schema: feature_manager.v1
project: pokertool
file: src/database/FeatureManager.ts
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Feature management service for ProgramHistory database
---
POKERTOOL-HEADER-END */

import sqlite3 from 'sqlite3';

/**
 * Feature interface
 */
export interface Feature {
  id?: number;
  name: string;
  description: string;
  category_id: number;
  status: 'active' | 'deprecated' | 'experimental' | 'removed' | 'disabled' | 'in_development';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  component_type: 'frontend' | 'backend' | 'api' | 'database' | 'utility' | 'service';
  introduced_version: string;
  deprecated_version?: string;
  removed_version?: string;
  file_path?: string;
  is_core_feature: boolean;
  is_gui_feature: boolean;
  dependencies?: string[];
  test_coverage_percent?: number;
}

/**
 * Feature Manager
 * Handles all feature-related database operations
 */
export class FeatureManager {
  private db: sqlite3.Database;

  constructor(db: sqlite3.Database) {
    this.db = db;
  }

  /**
   * Create a new feature
   */
  async createFeature(feature: Feature): Promise<number> {
    return new Promise((resolve, reject) => {
      const sql = `
        INSERT INTO features (
          name, description, category_id, status, risk_level, component_type,
          introduced_version, file_path, is_core_feature, is_gui_feature, dependencies
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;

      this.db.run(
        sql,
        [
          feature.name,
          feature.description,
          feature.category_id,
          feature.status,
          feature.risk_level,
          feature.component_type,
          feature.introduced_version,
          feature.file_path,
          feature.is_core_feature ? 1 : 0,
          feature.is_gui_feature ? 1 : 0,
          feature.dependencies ? JSON.stringify(feature.dependencies) : null
        ],
        function(err) {
          if (err) reject(err);
          else resolve(this.lastID);
        }
      );
    });
  }

  /**
   * Get a feature by ID
   */
  async getFeature(id: number): Promise<Feature | null> {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM features WHERE id = ?',
        [id],
        (err, row: any) => {
          if (err) reject(err);
          else {
            if (row) {
              row.is_core_feature = row.is_core_feature === 1;
              row.is_gui_feature = row.is_gui_feature === 1;
              row.dependencies = row.dependencies ? JSON.parse(row.dependencies) : [];
            }
            resolve(row || null);
          }
        }
      );
    });
  }

  /**
   * Get all features
   */
  async getAllFeatures(filters?: {
    status?: string;
    category_id?: number;
    component_type?: string;
    is_core?: boolean;
    is_gui?: boolean;
  }): Promise<Feature[]> {
    return new Promise((resolve, reject) => {
      let sql = 'SELECT * FROM features WHERE 1=1';
      const params: any[] = [];

      if (filters?.status) {
        sql += ' AND status = ?';
        params.push(filters.status);
      }
      if (filters?.category_id) {
        sql += ' AND category_id = ?';
        params.push(filters.category_id);
      }
      if (filters?.component_type) {
        sql += ' AND component_type = ?';
        params.push(filters.component_type);
      }
      if (filters?.is_core !== undefined) {
        sql += ' AND is_core_feature = ?';
        params.push(filters.is_core ? 1 : 0);
      }
      if (filters?.is_gui !== undefined) {
        sql += ' AND is_gui_feature = ?';
        params.push(filters.is_gui ? 1 : 0);
      }

      sql += ' ORDER BY name';

      this.db.all(sql, params, (err, rows: any[]) => {
        if (err) {
          reject(err);
        } else {
          const features = (rows || []).map(row => {
            row.is_core_feature = row.is_core_feature === 1;
            row.is_gui_feature = row.is_gui_feature === 1;
            row.dependencies = row.dependencies ? JSON.parse(row.dependencies) : [];
            return row;
          });
          resolve(features);
        }
      });
    });
  }

  /**
   * Get all core features (features that everything depends on)
   */
  async getCoreFeatures(): Promise<Feature[]> {
    return this.getAllFeatures({ is_core: true });
  }

  /**
   * Get all GUI features
   */
  async getGUIFeatures(): Promise<Feature[]> {
    return this.getAllFeatures({ is_gui: true });
  }

  /**
   * Update feature status
   */
  async updateFeatureStatus(featureId: number, newStatus: string, reason?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.run(
        `UPDATE features SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?`,
        [newStatus, featureId],
        async (err) => {
          if (err) {
            reject(err);
          } else {
            // Log the change in feature history
            await this.logFeatureChange(featureId, newStatus, reason);
            resolve();
          }
        }
      );
    });
  }

  /**
   * Log feature change to history
   */
  private async logFeatureChange(featureId: number, newStatus: string, reason?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const feature = this.getFeature(featureId);
      this.db.run(
        `INSERT INTO feature_history (feature_id, version_string, status_after, change_reason, created_at)
         VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)`,
        [featureId, 'current', newStatus, reason || ''],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  /**
   * Link a test to a feature
   */
  async linkTestToFeature(featureId: number, testFilePath: string, testName?: string, isCritical: boolean = false): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO feature_tests (feature_id, test_file_path, test_name, is_critical)
         VALUES (?, ?, ?, ?)`,
        [featureId, testFilePath, testName || '', isCritical ? 1 : 0],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  /**
   * Get tests for a feature
   */
  async getFeatureTests(featureId: number): Promise<any[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM feature_tests WHERE feature_id = ? ORDER BY test_name',
        [featureId],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  /**
   * Request feature removal (with warnings)
   */
  async requestFeatureRemoval(
    featureId: number,
    requestedBy: string,
    warningLevel: 'warning' | 'critical' | 'extreme' = 'warning'
  ): Promise<number> {
    const feature = await this.getFeature(featureId);
    if (!feature) throw new Error(`Feature ${featureId} not found`);

    // Get tests protecting this feature
    const tests = await this.getFeatureTests(featureId);
    const testList = tests.map(t => t.test_file_path).join(', ');

    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO feature_removal_log (
          feature_id, removal_requested_by, removal_requested_date, warning_level,
          tests_protecting_feature, removal_warning_sent
        ) VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, 1)`,
        [featureId, requestedBy, warningLevel, testList || 'NONE'],
        function(err) {
          if (err) reject(err);
          else {
            console.warn(`⚠️ REMOVAL WARNING [${warningLevel.toUpperCase()}] for feature: ${feature.name}`);
            console.warn(`   Tests protecting this feature: ${testList || 'NONE'}`);
            if (warningLevel === 'extreme') {
              console.error(`   🚨 EXTREME: This is a core feature! Removal will break the application.`);
            }
            resolve(this.lastID);
          }
        }
      );
    });
  }

  /**
   * Get features marked for removal
   */
  async getRemovalRequests(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT f.*, frl.removal_requested_date, frl.warning_level
         FROM feature_removal_log frl
         JOIN features f ON frl.feature_id = f.id
         WHERE frl.actually_removed = 0
         ORDER BY frl.removal_requested_date DESC`,
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  /**
   * Create a regression alert
   */
  async createRegressionAlert(
    featureId: number,
    alertType: string,
    message: string,
    severity: 'warning' | 'critical' = 'warning'
  ): Promise<number> {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO regression_alerts (feature_id, alert_type, message, severity)
         VALUES (?, ?, ?, ?)`,
        [featureId, alertType, message, severity],
        function(err) {
          if (err) reject(err);
          else {
            if (severity === 'critical') {
              console.error(`🚨 CRITICAL REGRESSION: ${message}`);
            } else {
              console.warn(`⚠️ REGRESSION WARNING: ${message}`);
            }
            resolve(this.lastID);
          }
        }
      );
    });
  }

  /**
   * Get active regression alerts
   */
  async getActiveRegressionAlerts(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT ra.*, f.name FROM regression_alerts ra
         JOIN features f ON ra.feature_id = f.id
         WHERE ra.is_resolved = 0
         ORDER BY ra.severity DESC, ra.created_at DESC`,
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  /**
   * Check for missing tests on critical features
   */
  async checkTestCoverage(): Promise<{
    featureId: number;
    featureName: string;
    hasTests: boolean;
    testCount: number;
    is_critical: boolean;
  }[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT f.id as featureId, f.name as featureName, COUNT(ft.id) as testCount,
                f.is_core_feature as is_critical,
                CASE WHEN COUNT(ft.id) > 0 THEN 1 ELSE 0 END as hasTests
         FROM features f
         LEFT JOIN feature_tests ft ON f.id = ft.feature_id
         WHERE f.status = 'active'
         GROUP BY f.id
         ORDER BY f.is_core_feature DESC, f.risk_level DESC`,
        (err, rows: any[]) => {
          if (err) {
            reject(err);
          } else {
            const results = (rows || []).map(row => ({
              featureId: row.featureId,
              featureName: row.featureName,
              hasTests: row.hasTests === 1,
              testCount: row.testCount,
              is_critical: row.is_critical === 1
            }));
            resolve(results);
          }
        }
      );
    });
  }

  /**
   * Generate regression report
   */
  async generateRegressionReport(): Promise<any> {
    const activeAlerts = await this.getActiveRegressionAlerts();
    const testCoverage = await this.checkTestCoverage();
    const removalRequests = await this.getRemovalRequests();
    const coreFeatures = await this.getCoreFeatures();
    const guiFeatures = await this.getGUIFeatures();

    const missingTests = testCoverage.filter(t => !t.hasTests && t.is_critical);
    const uncoveredFeatures = testCoverage.filter(t => !t.hasTests);

    return {
      timestamp: new Date().toISOString(),
      summary: {
        totalFeatures: testCoverage.length,
        coreFeatures: coreFeatures.length,
        guiFeatures: guiFeatures.length,
        activeRegressions: activeAlerts.length,
        pendingRemovals: removalRequests.length,
        featuresWithoutTests: uncoveredFeatures.length,
        criticalFeaturesWithoutTests: missingTests.length
      },
      activeRegressionAlerts: activeAlerts,
      pendingFeatureRemovals: removalRequests,
      testCoverageByFeature: testCoverage,
      missingTestsOnCriticalFeatures: missingTests,
      riskAssessment: {
        high_risk: activeAlerts.filter(a => a.severity === 'critical').length,
        medium_risk: uncoveredFeatures.length,
        low_risk: testCoverage.filter(t => t.testCount >= 3).length
      }
    };
  }
}
