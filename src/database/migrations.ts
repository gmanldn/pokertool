/* POKERTOOL-HEADER-START
---
schema: migrations.v1
project: pokertool
file: src/database/migrations.ts
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Database migration system for ProgramHistory database
---
POKERTOOL-HEADER-END */

import sqlite3 from 'sqlite3';
import path from 'path';
import fs from 'fs';

/**
 * Migration Record - tracks which migrations have been applied
 */
interface MigrationRecord {
  id: number;
  name: string;
  applied_at: string;
}

/**
 * Migration Definition
 */
interface Migration {
  name: string;
  up: (db: sqlite3.Database) => Promise<void>;
  down: (db: sqlite3.Database) => Promise<void>;
}

/**
 * Database Migration Manager
 * Handles schema migrations and data consistency
 */
export class MigrationManager {
  private db: sqlite3.Database;
  private dbPath: string;

  constructor(dbPath: string) {
    this.dbPath = dbPath;
    this.db = new sqlite3.Database(dbPath);
  }

  /**
   * Run all pending migrations
   */
  async runMigrations(): Promise<void> {
    // Create migrations table if it doesn't exist
    await this.createMigrationsTable();

    // Get list of applied migrations
    const appliedMigrations = await this.getAppliedMigrations();
    const appliedNames = new Set(appliedMigrations.map(m => m.name));

    // Define all migrations
    const migrations = this.defineMigrations();

    // Run pending migrations
    for (const migration of migrations) {
      if (!appliedNames.has(migration.name)) {
        console.log(`Running migration: ${migration.name}`);
        await migration.up(this.db);
        await this.recordMigration(migration.name);
        console.log(`✓ Completed migration: ${migration.name}`);
      }
    }
  }

  /**
   * Create migrations tracking table
   */
  private createMigrationsTable(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.run(
        `CREATE TABLE IF NOT EXISTS migrations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE,
          applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        )`,
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  /**
   * Get list of applied migrations
   */
  private getAppliedMigrations(): Promise<MigrationRecord[]> {
    return new Promise((resolve, reject) => {
      this.db.all('SELECT * FROM migrations ORDER BY applied_at', (err, rows) => {
        if (err) reject(err);
        else resolve((rows || []) as MigrationRecord[]);
      });
    });
  }

  /**
   * Record a migration as applied
   */
  private recordMigration(name: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO migrations (name, applied_at) VALUES (?, CURRENT_TIMESTAMP)',
        [name],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  /**
   * Define all migrations
   */
  private defineMigrations(): Migration[] {
    return [
      {
        name: '001_create_core_schema',
        up: async (db) => {
          return this.runSqlFile(db, path.join(__dirname, 'schema.sql'));
        },
        down: async (db) => {
          // Drop all tables in reverse order
          const tables = [
            'regression_history',
            'component_dependencies',
            'test_coverage_metrics',
            'feature_history',
            'version_feature_mapping',
            'feature_removal_log',
            'feature_dependencies',
            'version_changes',
            'regression_alerts',
            'feature_tests',
            'components',
            'features',
            'feature_status_types',
            'feature_categories',
            'versions',
            'migrations'
          ];

          for (const table of tables) {
            await this.dropTable(db, table);
          }
        }
      },
      {
        name: '002_add_feature_metadata',
        up: async (db) => {
          return this.runQuery(db,
            `ALTER TABLE features ADD COLUMN test_effectiveness_score REAL DEFAULT 0;`
          );
        },
        down: async (db) => {
          return this.dropColumnIfExists(db, 'features', 'test_effectiveness_score');
        }
      },
      {
        name: '003_add_performance_tracking',
        up: async (db) => {
          return this.runQuery(db,
            `CREATE TABLE IF NOT EXISTS performance_metrics (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              component_id INTEGER NOT NULL,
              metric_name TEXT NOT NULL,
              metric_value REAL NOT NULL,
              version_string TEXT NOT NULL,
              measured_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (component_id) REFERENCES components(id)
            );
            CREATE INDEX IF NOT EXISTS idx_performance_component ON performance_metrics(component_id);
            CREATE INDEX IF NOT EXISTS idx_performance_version ON performance_metrics(version_string);`
          );
        },
        down: async (db) => {
          return this.dropTable(db, 'performance_metrics');
        }
      },
      {
        name: '004_add_api_endpoints_tracking',
        up: async (db) => {
          return this.runQuery(db,
            `CREATE TABLE IF NOT EXISTS api_endpoints (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              path TEXT NOT NULL UNIQUE,
              method TEXT NOT NULL,
              description TEXT,
              feature_id INTEGER,
              introduced_version TEXT,
              deprecated_version TEXT,
              removed_version TEXT,
              requires_auth BOOLEAN DEFAULT 0,
              is_deprecated BOOLEAN DEFAULT 0,
              replacement_endpoint TEXT,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (feature_id) REFERENCES features(id)
            );
            CREATE INDEX IF NOT EXISTS idx_api_endpoints_feature ON api_endpoints(feature_id);
            CREATE INDEX IF NOT EXISTS idx_api_endpoints_deprecated ON api_endpoints(is_deprecated);`
          );
        },
        down: async (db) => {
          return this.dropTable(db, 'api_endpoints');
        }
      },
      {
        name: '005_add_database_schema_tracking',
        up: async (db) => {
          return this.runQuery(db,
            `CREATE TABLE IF NOT EXISTS database_schema_changes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              table_name TEXT NOT NULL,
              change_type TEXT NOT NULL,
              column_name TEXT,
              old_definition TEXT,
              new_definition TEXT,
              version_introduced TEXT NOT NULL,
              is_breaking_change BOOLEAN DEFAULT 0,
              migration_required BOOLEAN DEFAULT 0,
              created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_db_schema_table ON database_schema_changes(table_name);
            CREATE INDEX IF NOT EXISTS idx_db_schema_version ON database_schema_changes(version_introduced);`
          );
        },
        down: async (db) => {
          return this.dropTable(db, 'database_schema_changes');
        }
      }
    ];
  }

  /**
   * Run a SQL file
   */
  private runSqlFile(db: sqlite3.Database, filePath: string): Promise<void> {
    return new Promise((resolve, reject) => {
      fs.readFile(filePath, 'utf8', (err, sql) => {
        if (err) {
          reject(err);
          return;
        }

        db.exec(sql, (err) => {
          if (err) reject(err);
          else resolve();
        });
      });
    });
  }

  /**
   * Run a query
   */
  private runQuery(db: sqlite3.Database, sql: string): Promise<void> {
    return new Promise((resolve, reject) => {
      db.exec(sql, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  /**
   * Drop a table
   */
  private dropTable(db: sqlite3.Database, tableName: string): Promise<void> {
    return new Promise((resolve, reject) => {
      db.run(`DROP TABLE IF EXISTS ${tableName}`, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  /**
   * Drop a column if it exists
   */
  private dropColumnIfExists(db: sqlite3.Database, tableName: string, columnName: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
      // This is a simplified version - in production, you'd need a more robust approach
      resolve();
    });
  }

  /**
   * Close database connection
   */
  close(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.close((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }
}

/**
 * Initialize the database
 */
export async function initializeDatabase(dbPath: string): Promise<void> {
  const manager = new MigrationManager(dbPath);
  try {
    await manager.runMigrations();
    await manager.close();
    console.log('✓ Database initialization complete');
  } catch (error) {
    console.error('✗ Database initialization failed:', error);
    throw error;
  }
}
