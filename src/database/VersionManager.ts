/* POKERTOOL-HEADER-START
---
schema: version_manager.v1
project: pokertool
file: src/database/VersionManager.ts
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Version management service for tracking releases and changes
---
POKERTOOL-HEADER-END */

import sqlite3 from 'sqlite3';

/**
 * Version Record
 */
export interface VersionRecord {
  id?: number;
  version_string: string;
  major: number;
  minor: number;
  patch: number;
  release_type: 'alpha' | 'beta' | 'rc' | 'stable';
  release_date: string;
  description?: string;
  is_current: boolean;
  breaking_changes?: string;
  deprecated_features?: string;
  new_features?: string;
}

/**
 * Version Change
 */
export interface VersionChange {
  version_id: number;
  feature_id?: number;
  component_id?: number;
  change_type: 'added' | 'modified' | 'removed' | 'deprecated' | 'restored';
  change_description: string;
  impact_level: 'low' | 'medium' | 'high' | 'breaking';
  requires_migration: boolean;
  migration_notes?: string;
  git_commit?: string;
}

/**
 * Version Manager
 * Handles version creation, tracking, and management
 */
export class VersionManager {
  private db: sqlite3.Database;

  constructor(db: sqlite3.Database) {
    this.db = db;
  }

  /**
   * Get current version
   */
  async getCurrentVersion(): Promise<VersionRecord | null> {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM versions WHERE is_current = 1 LIMIT 1',
        (err, row: any) => {
          if (err) reject(err);
          else resolve(row || null);
        }
      );
    });
  }

  /**
   * Create a new version
   */
  async createNewVersion(
    versionString: string,
    major: number,
    minor: number,
    patch: number,
    releaseType: 'alpha' | 'beta' | 'rc' | 'stable',
    description: string
  ): Promise<number> {
    // Mark current version as not current
    await this.clearCurrentVersion();

    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO versions (
          version_string, major, minor, patch, release_type,
          release_date, description, is_current
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 1)`,
        [versionString, major, minor, patch, releaseType, description],
        function(err) {
          if (err) reject(err);
          else {
            console.log(`✓ Created new version: ${versionString}`);
            resolve(this.lastID);
          }
        }
      );
    });
  }

  /**
   * Clear current version marker
   */
  private clearCurrentVersion(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE versions SET is_current = 0',
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  /**
   * Record a version change
   */
  async recordVersionChange(change: VersionChange): Promise<number> {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO version_changes (
          version_id, feature_id, component_id, change_type,
          change_description, impact_level, requires_migration, migration_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          change.version_id,
          change.feature_id || null,
          change.component_id || null,
          change.change_type,
          change.change_description,
          change.impact_level,
          change.requires_migration ? 1 : 0,
          change.migration_notes || null
        ],
        function(err) {
          if (err) reject(err);
          else resolve(this.lastID);
        }
      );
    });
  }

  /**
   * Get changes for a version
   */
  async getVersionChanges(versionId: number): Promise<any[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT vc.*, f.name as feature_name, c.name as component_name
         FROM version_changes vc
         LEFT JOIN features f ON vc.feature_id = f.id
         LEFT JOIN components c ON vc.component_id = c.id
         WHERE vc.version_id = ?
         ORDER BY vc.change_type, vc.change_description`,
        [versionId],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  /**
   * Get version changelog
   */
  async getChangelog(versionString: string): Promise<any> {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM versions WHERE version_string = ?',
        [versionString],
        async (err, version: any) => {
          if (err) {
            reject(err);
          } else if (!version) {
            reject(new Error(`Version ${versionString} not found`));
          } else {
            const changes = await this.getVersionChanges(version.id);
            resolve({
              version: version,
              changes: changes
            });
          }
        }
      );
    });
  }

  /**
   * Compare two versions for regressions
   */
  async compareVersions(oldVersionString: string, newVersionString: string): Promise<{
    added: any[];
    modified: any[];
    removed: any[];
    deprecated: any[];
    potentialRegressions: any[];
  }> {
    return new Promise(async (resolve, reject) => {
      try {
        const oldChanges = await this.getVersionChanges(
          (await this.getVersionByString(oldVersionString))!.id
        );
        const newChanges = await this.getVersionChanges(
          (await this.getVersionByString(newVersionString))!.id
        );

        const categorized = {
          added: newChanges.filter(c => c.change_type === 'added'),
          modified: newChanges.filter(c => c.change_type === 'modified'),
          removed: newChanges.filter(c => c.change_type === 'removed'),
          deprecated: newChanges.filter(c => c.change_type === 'deprecated'),
          potentialRegressions: [] as any[]
        };

        // Check for potential regressions
        const removedFeatures = categorized.removed.filter(r => r.feature_id);
        for (const removed of removedFeatures) {
          if (removed.feature_name) {
            // Check if there are tests for this removed feature
            this.db.get(
              'SELECT COUNT(*) as testCount FROM feature_tests WHERE feature_id = ?',
              [removed.feature_id],
              (err, row: any) => {
                if (row?.testCount > 0) {
                  categorized.potentialRegressions.push({
                    type: 'removed_with_tests',
                    feature: removed.feature_name,
                    testsProtecting: row.testCount
                  });
                }
              }
            );
          }
        }

        resolve(categorized);
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Get version by string
   */
  private async getVersionByString(versionString: string): Promise<VersionRecord | null> {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM versions WHERE version_string = ?',
        [versionString],
        (err, row: any) => {
          if (err) reject(err);
          else resolve(row || null);
        }
      );
    });
  }

  /**
   * Create a new major release
   */
  async createMajorRelease(newMajor: number, description: string): Promise<number> {
    return this.createNewVersion(
      `v${newMajor}.0.0`,
      newMajor,
      0,
      0,
      'stable',
      description
    );
  }

  /**
   * Create a new minor release
   */
  async createMinorRelease(newMajor: number, newMinor: number, description: string): Promise<number> {
    return this.createNewVersion(
      `v${newMajor}.${newMinor}.0`,
      newMajor,
      newMinor,
      0,
      'stable',
      description
    );
  }

  /**
   * Create a new patch release
   */
  async createPatchRelease(newMajor: number, newMinor: number, newPatch: number, description: string): Promise<number> {
    return this.createNewVersion(
      `v${newMajor}.${newMinor}.${newPatch}`,
      newMajor,
      newMinor,
      newPatch,
      'stable',
      description
    );
  }

  /**
   * Get all versions
   */
  async getAllVersions(): Promise<VersionRecord[]> {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM versions ORDER BY major DESC, minor DESC, patch DESC',
        (err, rows) => {
          if (err) reject(err);
          else resolve((rows || []) as VersionRecord[]);
        }
      );
    });
  }

  /**
   * Generate release notes
   */
  async generateReleaseNotes(versionString: string): Promise<string> {
    const changelog = await this.getChangelog(versionString);
    const version = changelog.version;
    const changes = changelog.changes;

    let notes = `# Release Notes - ${version.version_string}\n\n`;
    notes += `**Release Date:** ${version.release_date}\n`;
    notes += `**Type:** ${version.release_type}\n`;
    notes += `**Description:** ${version.description || 'No description'}\n\n`;

    if (version.breaking_changes) {
      notes += `## ⚠️ Breaking Changes\n${version.breaking_changes}\n\n`;
    }

    const grouped = {
      added: changes.filter((c: any) => c.change_type === 'added'),
      modified: changes.filter((c: any) => c.change_type === 'modified'),
      removed: changes.filter((c: any) => c.change_type === 'removed'),
      deprecated: changes.filter((c: any) => c.change_type === 'deprecated'),
      restored: changes.filter((c: any) => c.change_type === 'restored')
    };

    if (grouped.added.length > 0) {
      notes += `## ✨ Added\n`;
      for (const change of grouped.added) {
        notes += `- ${change.change_description}\n`;
      }
      notes += '\n';
    }

    if (grouped.modified.length > 0) {
      notes += `## 🔧 Modified\n`;
      for (const change of grouped.modified) {
        notes += `- ${change.change_description}\n`;
      }
      notes += '\n';
    }

    if (grouped.deprecated.length > 0) {
      notes += `## 📦 Deprecated\n`;
      for (const change of grouped.deprecated) {
        notes += `- ${change.change_description}\n`;
      }
      notes += '\n';
    }

    if (grouped.removed.length > 0) {
      notes += `## ❌ Removed\n`;
      for (const change of grouped.removed) {
        notes += `- ${change.change_description}\n`;
      }
      notes += '\n';
    }

    if (grouped.restored.length > 0) {
      notes += `## ✅ Restored\n`;
      for (const change of grouped.restored) {
        notes += `- ${change.change_description}\n`;
      }
      notes += '\n';
    }

    return notes;
  }
}
