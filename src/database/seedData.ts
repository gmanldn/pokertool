/* POKERTOOL-HEADER-START
---
schema: seed_data.v1
project: pokertool
file: src/database/seedData.ts
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Seed data for PokerTool features in ProgramHistory database
---
POKERTOOL-HEADER-END */

import sqlite3 from 'sqlite3';
import { FeatureManager } from './FeatureManager';
import { VersionManager } from './VersionManager';

/**
 * Seed the database with PokerTool features
 */
export async function seedPokerToolFeatures(db: sqlite3.Database): Promise<void> {
  const featureManager = new FeatureManager(db);
  const versionManager = new VersionManager(db);

  console.log('🌱 Seeding PokerTool features...\n');

  // Seed current version
  const currentVersion = await versionManager.getCurrentVersion();
  if (!currentVersion) {
    await versionManager.createNewVersion(
      'v100.3.1',
      100,
      3,
      1,
      'stable',
      'Version History Tab and Comprehensive Test Coverage'
    );
  }

  // Define all PokerTool features
  const features = [
    // Core Functionality
    {
      name: 'Dashboard',
      description: 'Main application dashboard',
      category_id: 1, // Core Functionality
      status: 'active',
      risk_level: 'high',
      component_type: 'frontend',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool-frontend/src/components/Dashboard.tsx',
      is_core_feature: true,
      is_gui_feature: true
    },
    {
      name: 'SmartHelper',
      description: 'AI-powered poker strategy helper',
      category_id: 1,
      status: 'active',
      risk_level: 'critical',
      component_type: 'frontend',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool-frontend/src/components/SmartHelper.tsx',
      is_core_feature: true,
      is_gui_feature: true
    },
    {
      name: 'AI Chat',
      description: 'Chat interface with AI poker coach',
      category_id: 8, // Testing Infrastructure or could be Backend Services
      status: 'active',
      risk_level: 'medium',
      component_type: 'frontend',
      introduced_version: 'v100.1.0',
      file_path: 'pokertool-frontend/src/components/AIChat.tsx',
      is_core_feature: false,
      is_gui_feature: true
    },
    {
      name: 'Version History Tab',
      description: 'Tabbed interface showing version history, changelog, release notes, and what\'s new',
      category_id: 2, // User Interface
      status: 'active',
      risk_level: 'medium',
      component_type: 'frontend',
      introduced_version: 'v100.3.1',
      file_path: 'pokertool-frontend/src/components/VersionHistory.tsx',
      is_core_feature: false,
      is_gui_feature: true
    },
    {
      name: 'Tables Tab',
      description: 'Live table tracking and analysis',
      category_id: 2,
      status: 'active',
      risk_level: 'high',
      component_type: 'frontend',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool-frontend/src/components/TableView.tsx',
      is_core_feature: true,
      is_gui_feature: true
    },
    {
      name: 'Detection Log Tab',
      description: 'Displays detection events and analysis logs',
      category_id: 2,
      status: 'active',
      risk_level: 'high',
      component_type: 'frontend',
      introduced_version: 'v100.3.0',
      file_path: 'pokertool-frontend/src/components/DetectionLog.tsx',
      is_core_feature: true,
      is_gui_feature: true
    },
    {
      name: 'Backend Status Indicator',
      description: 'Real-time backend status and health monitoring',
      category_id: 2,
      status: 'active',
      risk_level: 'high',
      component_type: 'frontend',
      introduced_version: 'v100.3.0',
      file_path: 'pokertool-frontend/src/components/BackendStatus.tsx',
      is_core_feature: true,
      is_gui_feature: true
    },
    {
      name: 'Thread Management System',
      description: 'Comprehensive thread lifecycle management with graceful shutdown',
      category_id: 1,
      status: 'active',
      risk_level: 'critical',
      component_type: 'backend',
      introduced_version: 'v100.3.1',
      file_path: 'src/core/thread/ThreadManager.ts',
      is_core_feature: true,
      is_gui_feature: false
    },
    {
      name: 'Hand Evaluation Engine',
      description: 'Core poker hand evaluation and ranking logic',
      category_id: 9, // Poker Logic
      status: 'active',
      risk_level: 'critical',
      component_type: 'backend',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool/hand_evaluation.py',
      is_core_feature: true,
      is_gui_feature: false
    },
    {
      name: 'Database Connection Pool',
      description: 'SQLite database connection and query management',
      category_id: 4, // Database
      status: 'active',
      risk_level: 'critical',
      component_type: 'backend',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool/database.py',
      is_core_feature: true,
      is_gui_feature: false
    },
    {
      name: 'Program History Database',
      description: 'Feature tracking and regression prevention system',
      category_id: 1,
      status: 'active',
      risk_level: 'critical',
      component_type: 'database',
      introduced_version: 'v100.3.1',
      file_path: 'src/database/schema.sql',
      is_core_feature: false,
      is_gui_feature: false
    },
    {
      name: 'Navigation Component',
      description: 'Main navigation menu and drawer',
      category_id: 2,
      status: 'active',
      risk_level: 'high',
      component_type: 'frontend',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool-frontend/src/components/Navigation.tsx',
      is_core_feature: true,
      is_gui_feature: true
    },
    {
      name: 'Theme Management',
      description: 'Dark/light theme toggle and persistence',
      category_id: 2,
      status: 'active',
      risk_level: 'low',
      component_type: 'frontend',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool-frontend/src/context/ThemeContext.tsx',
      is_core_feature: false,
      is_gui_feature: true
    },
    {
      name: 'WebSocket Connection',
      description: 'Real-time data streaming with backend',
      category_id: 3, // API Endpoints
      status: 'active',
      risk_level: 'critical',
      component_type: 'frontend',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool-frontend/src/services/websocket.ts',
      is_core_feature: true,
      is_gui_feature: false
    },
    {
      name: 'Test Helper Utilities',
      description: 'Testing utilities and mock providers',
      category_id: 8, // Testing Infrastructure
      status: 'active',
      risk_level: 'high',
      component_type: 'utility',
      introduced_version: 'v100.0.0',
      file_path: 'pokertool-frontend/src/test-utils/testHelpers.ts',
      is_core_feature: false,
      is_gui_feature: false
    }
  ];

  // Create all features
  for (const feature of features) {
    try {
      const featureId = await featureManager.createFeature(feature as any);
      console.log(`✓ Created feature: ${feature.name}`);

      // Link tests to features
      const testLinks: { [key: string]: string[] } = {
        'Version History Tab': [
          'pokertool-frontend/src/components/__tests__/VersionHistory.regression.test.tsx',
          'pokertool-frontend/src/__tests__/VersionHistoryTab.visibility.test.tsx',
          'pokertool-frontend/src/__tests__/CanonicalTabs.regression.test.tsx'
        ],
        'Tables Tab': [
          'pokertool-frontend/src/__tests__/CriticalTabs.visibility.test.tsx',
          'pokertool-frontend/src/__tests__/CanonicalTabs.regression.test.tsx'
        ],
        'Detection Log Tab': [
          'pokertool-frontend/src/__tests__/CriticalTabs.visibility.test.tsx',
          'pokertool-frontend/src/__tests__/CanonicalTabs.regression.test.tsx'
        ],
        'Navigation Component': [
          'pokertool-frontend/src/components/__tests__/Navigation.comprehensive.test.tsx',
          'pokertool-frontend/src/components/__tests__/Navigation.dependencies.test.tsx'
        ],
        'Theme Management': [
          'pokertool-frontend/src/components/__tests__/ThemeContext.test.tsx'
        ],
        'Backend Status Indicator': [
          'pokertool-frontend/src/__tests__/BackendStatus.test.tsx'
        ]
      };

      if (testLinks[feature.name]) {
        for (const testPath of testLinks[feature.name]) {
          await featureManager.linkTestToFeature(
            featureId,
            testPath,
            undefined,
            ['Version History Tab', 'Tables Tab', 'Detection Log Tab'].includes(feature.name)
          );
        }
      }
    } catch (error) {
      console.error(`✗ Error creating feature ${feature.name}:`, error);
    }
  }

  console.log('\n✅ Feature seeding complete!');
}

/**
 * Seed database with current version and changes
 */
export async function seedCurrentVersion(db: sqlite3.Database): Promise<void> {
  const versionManager = new VersionManager(db);

  console.log('📝 Recording current version changes...\n');

  const currentVersion = await versionManager.getCurrentVersion();
  if (!currentVersion) {
    console.error('❌ No current version found');
    return;
  }

  // Record version changes for v100.3.1
  const changes = [
    {
      version_id: currentVersion.id,
      change_type: 'added',
      change_description: 'Version History Tab - comprehensive version tracking interface',
      impact_level: 'medium',
      requires_migration: false
    },
    {
      version_id: currentVersion.id,
      change_type: 'added',
      change_description: 'Program History Database - complete feature tracking system',
      impact_level: 'medium',
      requires_migration: false
    },
    {
      version_id: currentVersion.id,
      change_type: 'added',
      change_description: '49 new critical regression prevention tests',
      impact_level: 'high',
      requires_migration: false
    },
    {
      version_id: currentVersion.id,
      change_type: 'added',
      change_description: 'Thread Management System - graceful shutdown and cleanup',
      impact_level: 'high',
      requires_migration: false
    },
    {
      version_id: currentVersion.id,
      change_type: 'modified',
      change_description: 'Enhanced backend status indicator with real-time health checks',
      impact_level: 'medium',
      requires_migration: false
    },
    {
      version_id: currentVersion.id,
      change_type: 'modified',
      change_description: 'Improved navigation drawer with better organization',
      impact_level: 'low',
      requires_migration: false
    }
  ];

  for (const change of changes) {
    try {
      await versionManager.recordVersionChange(change as any);
      console.log(`✓ Recorded change: ${change.change_description}`);
    } catch (error) {
      console.error(`✗ Error recording change:`, error);
    }
  }

  console.log('\n✅ Version changes recorded!');
}

/**
 * Run all seeding
 */
export async function seedDatabase(db: sqlite3.Database): Promise<void> {
  try {
    await seedPokerToolFeatures(db);
    await seedCurrentVersion(db);
    console.log('\n🌟 Database seeding complete!\n');
  } catch (error) {
    console.error('❌ Database seeding failed:', error);
    throw error;
  }
}
