/* POKERTOOL-HEADER-START
---
schema: regression_detector.v1
project: pokertool
file: src/database/RegressionDetector.ts
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Regression detection engine for automatic issue identification
---
POKERTOOL-HEADER-END */

import sqlite3 from 'sqlite3';
import fs from 'fs';
import path from 'path';

/**
 * Regression Detection Result
 */
export interface RegressionResult {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  affectedFeature?: string;
  affectedComponent?: string;
  testRecommendation?: string;
}

/**
 * Regression Detector
 * Automatically detects potential regressions in the codebase
 */
export class RegressionDetector {
  private db: sqlite3.Database;
  private projectRoot: string;

  constructor(db: sqlite3.Database, projectRoot: string = process.cwd()) {
    this.db = db;
    this.projectRoot = projectRoot;
  }

  /**
   * Run comprehensive regression detection
   */
  async detectRegressions(): Promise<RegressionResult[]> {
    const results: RegressionResult[] = [];

    // Run all detection checks
    results.push(...await this.detectRemovedFeatures());
    results.push(...await this.detectMissingTests());
    results.push(...await this.detectOrphanedComponents());
    results.push(...await this.detectDependencyIssues());
    results.push(...await this.detectTestCoverageDrops());
    results.push(...await this.detectFileRemovals());

    return results;
  }

  /**
   * Detect features marked as active but with missing implementation
   */
  private async detectRemovedFeatures(): Promise<RegressionResult[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT f.* FROM features f
         WHERE f.status = 'active' AND f.removed_version IS NOT NULL`,
        (err, features: any[]) => {
          if (err) {
            reject(err);
          } else {
            const results = (features || []).map(feature => ({
              type: 'removed_active_feature',
              severity: 'critical' as const,
              message: `Feature '${feature.name}' is marked as active but has a removed_version (${feature.removed_version})`,
              affectedFeature: feature.name
            }));
            resolve(results);
          }
        }
      );
    });
  }

  /**
   * Detect core/critical features without tests
   */
  private async detectMissingTests(): Promise<RegressionResult[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT f.* FROM features f
         WHERE f.status = 'active'
         AND (f.is_core_feature = 1 OR f.risk_level = 'critical')
         AND NOT EXISTS (
           SELECT 1 FROM feature_tests WHERE feature_id = f.id
         )`,
        (err, features: any[]) => {
          if (err) {
            reject(err);
          } else {
            const results = (features || []).map(feature => ({
              type: 'missing_critical_tests',
              severity: 'critical' as const,
              message: `Critical feature '${feature.name}' has no test coverage`,
              affectedFeature: feature.name,
              testRecommendation: `Add comprehensive tests for ${feature.component_type} feature: ${feature.name}`
            }));
            resolve(results);
          }
        }
      );
    });
  }

  /**
   * Detect components that are no longer used
   */
  private async detectOrphanedComponents(): Promise<RegressionResult[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT c.* FROM components c
         WHERE c.is_exported = 1
         AND NOT EXISTS (
           SELECT 1 FROM component_dependencies WHERE depends_on_component_id = c.id
         )
         AND NOT EXISTS (
           SELECT 1 FROM features WHERE file_path LIKE '%' || c.name || '%'
         )`,
        (err, components: any[]) => {
          if (err) {
            reject(err);
          } else {
            const results = (components || []).map(component => ({
              type: 'orphaned_component',
              severity: component.is_core ? 'high' as const : 'medium' as const,
              message: `Component '${component.name}' may be unused (${component.file_path})`,
              affectedComponent: component.name
            }));
            resolve(results);
          }
        }
      );
    });
  }

  /**
   * Detect dependency conflicts
   */
  private async detectDependencyIssues(): Promise<RegressionResult[]> {
    return new Promise((resolve, reject) => {
      // Check for circular dependencies
      this.db.all(
        `SELECT DISTINCT fd1.feature_id
         FROM feature_dependencies fd1
         WHERE EXISTS (
           SELECT 1 FROM feature_dependencies fd2
           WHERE fd2.feature_id = fd1.depends_on_feature_id
           AND fd2.depends_on_feature_id = fd1.feature_id
         )`,
        (err, circularFeatures: any[]) => {
          if (err) {
            reject(err);
          } else {
            const featureResults = (circularFeatures || []).map(item => ({
              type: 'circular_dependency',
              severity: 'high' as const,
              message: `Circular dependency detected in feature dependencies (feature_id: ${item.feature_id})`
            }));

            // Check for missing dependencies
            this.db.all(
              `SELECT f.name, f.dependencies
               FROM features f
               WHERE f.status = 'active'
               AND f.dependencies IS NOT NULL
               AND LENGTH(f.dependencies) > 2`,
              (err2, featuresWithDeps: any[]) => {
                if (err2) {
                  reject(err2);
                } else {
                  const depResults: RegressionResult[] = [];
                  for (const feature of (featuresWithDeps || [])) {
                    try {
                      const deps = JSON.parse(feature.dependencies);
                      for (const dep of deps) {
                        // Check if dependency exists
                        this.db.get(
                          'SELECT id FROM features WHERE name = ?',
                          [dep],
                          (err3, found) => {
                            if (!found) {
                              depResults.push({
                                type: 'missing_dependency',
                                severity: 'high' as const,
                                message: `Feature '${feature.name}' depends on '${dep}' which doesn't exist`,
                                affectedFeature: feature.name
                              });
                            }
                          }
                        );
                      }
                    } catch (e) {
                      // JSON parse error
                    }
                  }
                  resolve([...featureResults, ...depResults]);
                }
              }
            );
          }
        }
      );
    });
  }

  /**
   * Detect test coverage drops
   */
  private async detectTestCoverageDrops(): Promise<RegressionResult[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT f.name, f.test_coverage_percent, tcm.coverage_percent
         FROM features f
         LEFT JOIN test_coverage_metrics tcm ON f.id = tcm.feature_id
         WHERE f.status = 'active'
         AND (f.is_core_feature = 1 OR f.is_gui_feature = 1)
         AND f.test_coverage_percent > 0
         AND tcm.coverage_percent < f.test_coverage_percent * 0.8`,
        (err, features: any[]) => {
          if (err) {
            reject(err);
          } else {
            const results = (features || []).map(feature => ({
              type: 'coverage_drop',
              severity: feature.is_core_feature ? 'critical' as const : 'high' as const,
              message: `Test coverage for '${feature.name}' dropped from ${feature.test_coverage_percent}% to ${feature.coverage_percent}%`,
              affectedFeature: feature.name
            }));
            resolve(results);
          }
        }
      );
    });
  }

  /**
   * Detect files that have been removed from disk
   */
  private async detectFileRemovals(): Promise<RegressionResult[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT f.name, f.file_path FROM features f WHERE f.file_path IS NOT NULL',
        (err, features: any[]) => {
          if (err) {
            reject(err);
            return;
          }

          const results: RegressionResult[] = [];

          for (const feature of (features || [])) {
            if (feature.file_path) {
              const fullPath = path.join(this.projectRoot, feature.file_path);
              if (!fs.existsSync(fullPath) && feature.status === 'active') {
                results.push({
                  type: 'file_removed',
                  severity: feature.is_core_feature ? 'critical' as const : 'high' as const,
                  message: `Feature '${feature.name}' file is missing: ${feature.file_path}`,
                  affectedFeature: feature.name
                });
              }
            }
          }

          // Also check components
          this.db.all(
            'SELECT c.name, c.file_path FROM components c WHERE c.file_path IS NOT NULL',
            (err2, components: any[]) => {
              if (err2) {
                reject(err2);
              } else {
                for (const component of (components || [])) {
                  if (component.file_path) {
                    const fullPath = path.join(this.projectRoot, component.file_path);
                    if (!fs.existsSync(fullPath)) {
                      results.push({
                        type: 'component_file_removed',
                        severity: component.is_core ? 'critical' as const : 'high' as const,
                        message: `Component '${component.name}' file is missing: ${component.file_path}`,
                        affectedComponent: component.name
                      });
                    }
                  }
                }
                resolve(results);
              }
            }
          );
        }
      );
    });
  }

  /**
   * Generate regression report
   */
  async generateRegressionReport(detailed: boolean = false): Promise<string> {
    const results = await this.detectRegressions();

    let report = `\n${'='.repeat(80)}\n`;
    report += `REGRESSION DETECTION REPORT - ${new Date().toISOString()}\n`;
    report += `${'='.repeat(80)}\n\n`;

    // Summary
    const bySeverity = {
      critical: results.filter(r => r.severity === 'critical').length,
      high: results.filter(r => r.severity === 'high').length,
      medium: results.filter(r => r.severity === 'medium').length,
      low: results.filter(r => r.severity === 'low').length
    };

    report += `SUMMARY\n`;
    report += `${'─'.repeat(80)}\n`;
    report += `Total Issues Found: ${results.length}\n`;
    report += `🚨 Critical: ${bySeverity.critical}\n`;
    report += `⚠️ High: ${bySeverity.high}\n`;
    report += `⚠️ Medium: ${bySeverity.medium}\n`;
    report += `ℹ️ Low: ${bySeverity.low}\n\n`;

    if (detailed) {
      report += `DETAILED FINDINGS\n`;
      report += `${'─'.repeat(80)}\n`;

      const bySeverityMap = {
        critical: results.filter(r => r.severity === 'critical'),
        high: results.filter(r => r.severity === 'high'),
        medium: results.filter(r => r.severity === 'medium'),
        low: results.filter(r => r.severity === 'low')
      };

      for (const [severity, issues] of Object.entries(bySeverityMap)) {
        if (issues.length > 0) {
          report += `\n${severity.toUpperCase()} SEVERITY ISSUES:\n`;
          for (const issue of issues) {
            report += `  • ${issue.message}\n`;
            if (issue.testRecommendation) {
              report += `    → Recommendation: ${issue.testRecommendation}\n`;
            }
          }
        }
      }
    }

    report += `\n${'='.repeat(80)}\n`;
    return report;
  }
}
