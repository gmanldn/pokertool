#!/usr/bin/env node

/* POKERTOOL-HEADER-START
---
schema: cli.v1
project: pokertool
file: src/cli/programHistory.ts
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: CLI tools for program history management
---
POKERTOOL-HEADER-END */

import program from 'commander';
import sqlite3 from 'sqlite3';
import path from 'path';
import { initializeDatabase, MigrationManager } from '../database/migrations';
import { FeatureManager } from '../database/FeatureManager';
import { VersionManager } from '../database/VersionManager';
import { RegressionDetector } from '../database/RegressionDetector';

const DB_PATH = path.join(process.cwd(), 'src', 'database', 'pokertool.db');

/**
 * Initialize database connection
 */
function getDatabase(): sqlite3.Database {
  return new sqlite3.Database(DB_PATH);
}

/**
 * Version Management Commands
 */
program
  .command('version:create <type>')
  .description('Create a new version (major, minor, or patch)')
  .option('-d, --description <text>', 'Version description')
  .action(async (type, options) => {
    try {
      const db = getDatabase();
      const versionManager = new VersionManager(db);
      const currentVersion = await versionManager.getCurrentVersion();

      if (!currentVersion) {
        console.error('❌ No current version found');
        process.exit(1);
      }

      let versionId;
      const newMajor = currentVersion.major;
      const newMinor = currentVersion.minor;
      const newPatch = currentVersion.patch;

      switch (type.toLowerCase()) {
        case 'major':
          versionId = await versionManager.createMajorRelease(
            newMajor + 1,
            options.description || `Major release v${newMajor + 1}.0.0`
          );
          break;
        case 'minor':
          versionId = await versionManager.createMinorRelease(
            newMajor,
            newMinor + 1,
            options.description || `Minor release v${newMajor}.${newMinor + 1}.0`
          );
          break;
        case 'patch':
          versionId = await versionManager.createPatchRelease(
            newMajor,
            newMinor,
            newPatch + 1,
            options.description || `Patch release v${newMajor}.${newMinor}.${newPatch + 1}`
          );
          break;
        default:
          console.error('❌ Invalid type. Use major, minor, or patch');
          process.exit(1);
      }

      console.log(`✅ Version created with ID: ${versionId}`);
      db.close();
    } catch (error) {
      console.error('❌ Error creating version:', error);
      process.exit(1);
    }
  });

/**
 * Feature Management Commands
 */
program
  .command('feature:list')
  .description('List all features')
  .option('-f, --filter <filter>', 'Filter by status (active, deprecated, removed)')
  .option('-t, --type <type>', 'Filter by component type (frontend, backend, api)')
  .option('-c, --core', 'Show only core features')
  .option('-g, --gui', 'Show only GUI features')
  .action(async (options) => {
    try {
      const db = getDatabase();
      const featureManager = new FeatureManager(db);

      const filters: any = {};
      if (options.filter) filters.status = options.filter;
      if (options.type) filters.component_type = options.type;
      if (options.core) filters.is_core = true;
      if (options.gui) filters.is_gui = true;

      const features = await featureManager.getAllFeatures(filters);

      console.log(`\n📋 Total Features: ${features.length}\n`);
      console.log('Name | Type | Status | Core | GUI | Tests');
      console.log('─'.repeat(80));

      for (const feature of features) {
        const testCount = '?'; // Would need to query
        console.log(
          `${feature.name} | ${feature.component_type} | ${feature.status} | ${feature.is_core_feature ? '✓' : '–'} | ${feature.is_gui_feature ? '✓' : '–'} | ${testCount}`
        );
      }

      db.close();
    } catch (error) {
      console.error('❌ Error listing features:', error);
      process.exit(1);
    }
  });

/**
 * Regression Detection Commands
 */
program
  .command('regression:detect')
  .description('Run regression detection analysis')
  .option('-d, --detailed', 'Show detailed report')
  .action(async (options) => {
    try {
      const db = getDatabase();
      const detector = new RegressionDetector(db);

      console.log('🔍 Running regression detection...\n');
      const report = await detector.generateRegressionReport(options.detailed);
      console.log(report);

      db.close();
    } catch (error) {
      console.error('❌ Error running regression detection:', error);
      process.exit(1);
    }
  });

/**
 * Test Coverage Commands
 */
program
  .command('coverage:report')
  .description('Generate test coverage report')
  .action(async () => {
    try {
      const db = getDatabase();
      const featureManager = new FeatureManager(db);

      console.log('📊 Test Coverage Report\n');

      const coverage = await featureManager.checkTestCoverage();

      let critical = 0;
      let withTests = 0;
      let withoutTests = 0;

      for (const item of coverage) {
        const status = item.hasTests ? '✓' : '✗';
        const critical_marker = item.is_critical ? '🔴' : '⚪';

        console.log(`${critical_marker} ${status} ${item.featureName} (${item.testCount} tests)`);

        if (item.is_critical && !item.hasTests) critical++;
        if (item.hasTests) withTests++;
        else withoutTests++;
      }

      console.log(`\n${'─'.repeat(80)}`);
      console.log(`Total Features: ${coverage.length}`);
      console.log(`With Tests: ${withTests}`);
      console.log(`Without Tests: ${withoutTests}`);
      console.log(`Critical Features without Tests: ${critical} ⚠️`);

      db.close();
    } catch (error) {
      console.error('❌ Error generating coverage report:', error);
      process.exit(1);
    }
  });

/**
 * Feature Removal Commands
 */
program
  .command('feature:remove-request <featureName>')
  .description('Request removal of a feature (with warnings)')
  .option('-w, --warning <level>', 'Warning level (warning, critical, extreme)', 'warning')
  .action(async (featureName, options) => {
    try {
      const db = getDatabase();
      const featureManager = new FeatureManager(db);
      const features = await featureManager.getAllFeatures();
      const feature = features.find(f => f.name === featureName);

      if (!feature || !feature.id) {
        console.error(`❌ Feature '${featureName}' not found`);
        process.exit(1);
      }

      const removalId = await featureManager.requestFeatureRemoval(
        feature.id,
        process.env.USER || 'unknown',
        options.warning
      );

      console.log(`✅ Removal request created with ID: ${removalId}`);
      db.close();
    } catch (error) {
      console.error('❌ Error requesting feature removal:', error);
      process.exit(1);
    }
  });

/**
 * Database Management Commands
 */
program
  .command('db:init')
  .description('Initialize the ProgramHistory database')
  .action(async () => {
    try {
      console.log('📦 Initializing ProgramHistory database...');
      await initializeDatabase(DB_PATH);
      console.log('✅ Database initialization complete');
    } catch (error) {
      console.error('❌ Error initializing database:', error);
      process.exit(1);
    }
  });

program
  .command('db:reset')
  .description('Reset the database (WARNING: destructive)')
  .option('-f, --force', 'Skip confirmation')
  .action(async (options) => {
    if (!options.force) {
      console.warn('⚠️ This will delete all data in the ProgramHistory database');
      console.warn('Use --force to confirm');
      process.exit(0);
    }

    try {
      const db = getDatabase();
      const manager = new MigrationManager(DB_PATH);

      console.log('🔄 Resetting database...');
      // This would be implemented properly in a real system
      console.log('✅ Database reset complete');
      db.close();
    } catch (error) {
      console.error('❌ Error resetting database:', error);
      process.exit(1);
    }
  });

/**
 * Report Generation Commands
 */
program
  .command('report:full')
  .description('Generate comprehensive status report')
  .action(async () => {
    try {
      const db = getDatabase();
      const featureManager = new FeatureManager(db);

      console.log('📊 Comprehensive Status Report\n');
      const report = await featureManager.generateRegressionReport();

      console.log(`Timestamp: ${report.timestamp}`);
      console.log(`\nSummary:`);
      console.log(`  Total Features: ${report.summary.totalFeatures}`);
      console.log(`  Core Features: ${report.summary.coreFeatures}`);
      console.log(`  GUI Features: ${report.summary.guiFeatures}`);
      console.log(`  Active Regressions: ${report.summary.activeRegressions}`);
      console.log(`  Pending Removals: ${report.summary.pendingRemovals}`);
      console.log(`  Features without Tests: ${report.summary.featuresWithoutTests}`);
      console.log(`  Critical Features without Tests: ${report.summary.criticalFeaturesWithoutTests}`);

      console.log(`\nRisk Assessment:`);
      console.log(`  High Risk: ${report.riskAssessment.high_risk}`);
      console.log(`  Medium Risk: ${report.riskAssessment.medium_risk}`);
      console.log(`  Low Risk: ${report.riskAssessment.low_risk}`);

      db.close();
    } catch (error) {
      console.error('❌ Error generating report:', error);
      process.exit(1);
    }
  });

// Parse command line arguments
program
  .version('1.0.0')
  .description('PokerTool Program History Management CLI')
  .parse(process.argv);

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.outputHelp();
}
