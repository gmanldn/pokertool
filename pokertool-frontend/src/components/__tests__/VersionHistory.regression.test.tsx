/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/__tests__/VersionHistory.regression.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Critical regression detection tests - will fail if ANY tabs are removed or moved
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { VersionHistory } from '../VersionHistory';
import { renderWithProviders } from '../../test-utils/testHelpers';
import '@testing-library/jest-dom';
import { RELEASE_VERSION } from '../../config/releaseVersion';

/**
 * CRITICAL REGRESSION TESTS
 *
 * These tests are designed to FAIL LOUDLY if any features are removed or moved.
 * If any of these tests fail, it indicates a REGRESSION that must be investigated.
 *
 * DO NOT modify these tests to make them pass without explicit approval.
 * If a test fails, it means functionality has been removed or changed.
 */

describe('VersionHistory - CRITICAL REGRESSION DETECTION', () => {
  describe('🚨 TAB PRESENCE - All 4 Tabs MUST Exist', () => {
    it('REGRESSION CHECK: Must have exactly 4 tabs (no more, no less)', () => {
      renderWithProviders(<VersionHistory />);

      const tabs = screen.getAllByRole('tab');

      // CRITICAL: If this fails, tabs have been added or removed
      expect(tabs).toHaveLength(4);

      if (tabs.length !== 4) {
        throw new Error(
          `🚨 REGRESSION DETECTED: Expected 4 tabs but found ${tabs.length}. ` +
          `This indicates tabs have been added or removed. ` +
          `Current tabs: ${tabs.map(t => t.textContent).join(', ')}`
        );
      }
    });

    it('REGRESSION CHECK: "Current Version" tab MUST exist', () => {
      renderWithProviders(<VersionHistory />);

      const currentVersionTab = screen.queryByRole('tab', { name: /current version/i });

      // CRITICAL: If this fails, the Current Version tab has been removed or renamed
      expect(currentVersionTab).toBeInTheDocument();

      if (!currentVersionTab) {
        const allTabs = screen.getAllByRole('tab').map(t => t.textContent).join(', ');
        throw new Error(
          `🚨 REGRESSION DETECTED: "Current Version" tab is missing! ` +
          `Available tabs: ${allTabs}`
        );
      }
    });

    it('REGRESSION CHECK: "Changelog" tab MUST exist', () => {
      renderWithProviders(<VersionHistory />);

      const changelogTab = screen.queryByRole('tab', { name: /changelog/i });

      // CRITICAL: If this fails, the Changelog tab has been removed or renamed
      expect(changelogTab).toBeInTheDocument();

      if (!changelogTab) {
        const allTabs = screen.getAllByRole('tab').map(t => t.textContent).join(', ');
        throw new Error(
          `🚨 REGRESSION DETECTED: "Changelog" tab is missing! ` +
          `Available tabs: ${allTabs}`
        );
      }
    });

    it('REGRESSION CHECK: "Release Notes" tab MUST exist', () => {
      renderWithProviders(<VersionHistory />);

      const releaseNotesTab = screen.queryByRole('tab', { name: /release notes/i });

      // CRITICAL: If this fails, the Release Notes tab has been removed or renamed
      expect(releaseNotesTab).toBeInTheDocument();

      if (!releaseNotesTab) {
        const allTabs = screen.getAllByRole('tab').map(t => t.textContent).join(', ');
        throw new Error(
          `🚨 REGRESSION DETECTED: "Release Notes" tab is missing! ` +
          `Available tabs: ${allTabs}`
        );
      }
    });

    it('REGRESSION CHECK: "What\'s New" tab MUST exist', () => {
      renderWithProviders(<VersionHistory />);

      const whatsNewTab = screen.queryByRole('tab', { name: /what's new/i });

      // CRITICAL: If this fails, the What's New tab has been removed or renamed
      expect(whatsNewTab).toBeInTheDocument();

      if (!whatsNewTab) {
        const allTabs = screen.getAllByRole('tab').map(t => t.textContent).join(', ');
        throw new Error(
          `🚨 REGRESSION DETECTED: "What's New" tab is missing! ` +
          `Available tabs: ${allTabs}`
        );
      }
    });
  });

  describe('🚨 TAB CONTENT - Critical Content MUST Be Present', () => {
    it('REGRESSION CHECK: Current Version tab MUST show version number', () => {
      renderWithProviders(<VersionHistory />);

      // Should be on Current Version tab by default
      const versionText = screen.queryAllByText(RELEASE_VERSION);

      expect(versionText.length).toBeGreaterThan(0);

      if (versionText.length === 0) {
        throw new Error(
          `🚨 REGRESSION DETECTED: Version number "${RELEASE_VERSION}" not displayed in Current Version tab!`
        );
      }
    });

    it('REGRESSION CHECK: Current Version tab MUST show Release Type card', () => {
      renderWithProviders(<VersionHistory />);

      const releaseType = screen.queryByText('Release Type');

      expect(releaseType).toBeInTheDocument();

      if (!releaseType) {
        throw new Error(
          `🚨 REGRESSION DETECTED: "Release Type" card is missing from Current Version tab!`
        );
      }
    });

    it('REGRESSION CHECK: Current Version tab MUST show Build Number card', () => {
      renderWithProviders(<VersionHistory />);

      const buildNumber = screen.queryByText('Build Number');

      expect(buildNumber).toBeInTheDocument();

      if (!buildNumber) {
        throw new Error(
          `🚨 REGRESSION DETECTED: "Build Number" card is missing from Current Version tab!`
        );
      }
    });

    it('REGRESSION CHECK: Changelog tab MUST show "Recent Changes"', () => {
      renderWithProviders(<VersionHistory />);

      const changelogTab = screen.getByRole('tab', { name: /changelog/i });
      fireEvent.click(changelogTab);

      const recentChanges = screen.queryByText('Recent Changes');

      expect(recentChanges).toBeInTheDocument();

      if (!recentChanges) {
        throw new Error(
          `🚨 REGRESSION DETECTED: "Recent Changes" heading is missing from Changelog tab!`
        );
      }
    });

    it('REGRESSION CHECK: Changelog tab MUST show v100.3.1 release', () => {
      renderWithProviders(<VersionHistory />);

      const changelogTab = screen.getByRole('tab', { name: /changelog/i });
      fireEvent.click(changelogTab);

      const currentVersion = screen.queryAllByText('v100.3.1');

      expect(currentVersion.length).toBeGreaterThan(0);

      if (currentVersion.length === 0) {
        throw new Error(
          `🚨 REGRESSION DETECTED: Current version "v100.3.1" is missing from Changelog!`
        );
      }
    });

    it('REGRESSION CHECK: Changelog tab MUST show v100.0.0 major release', () => {
      renderWithProviders(<VersionHistory />);

      const changelogTab = screen.getByRole('tab', { name: /changelog/i });
      fireEvent.click(changelogTab);

      const majorRelease = screen.queryAllByText('v100.0.0');

      expect(majorRelease.length).toBeGreaterThan(0);

      if (majorRelease.length === 0) {
        throw new Error(
          `🚨 REGRESSION DETECTED: Major release "v100.0.0" is missing from Changelog!`
        );
      }
    });

    it('REGRESSION CHECK: Release Notes tab MUST show "Key Features"', () => {
      renderWithProviders(<VersionHistory />);

      const releaseNotesTab = screen.getByRole('tab', { name: /release notes/i });
      fireEvent.click(releaseNotesTab);

      const keyFeatures = screen.queryByText(/key features/i);

      expect(keyFeatures).toBeInTheDocument();

      if (!keyFeatures) {
        throw new Error(
          `🚨 REGRESSION DETECTED: "Key Features" section is missing from Release Notes tab!`
        );
      }
    });

    it('REGRESSION CHECK: Release Notes tab MUST show "Technical Improvements"', () => {
      renderWithProviders(<VersionHistory />);

      const releaseNotesTab = screen.getByRole('tab', { name: /release notes/i });
      fireEvent.click(releaseNotesTab);

      const techImprovements = screen.queryByText(/technical improvements/i);

      expect(techImprovements).toBeInTheDocument();

      if (!techImprovements) {
        throw new Error(
          `🚨 REGRESSION DETECTED: "Technical Improvements" section is missing from Release Notes tab!`
        );
      }
    });

    it('REGRESSION CHECK: What\'s New tab MUST show "Highlights"', () => {
      renderWithProviders(<VersionHistory />);

      const whatsNewTab = screen.getByRole('tab', { name: /what's new/i });
      fireEvent.click(whatsNewTab);

      const highlights = screen.queryByText('Highlights');

      expect(highlights).toBeInTheDocument();

      if (!highlights) {
        throw new Error(
          `🚨 REGRESSION DETECTED: "Highlights" section is missing from What's New tab!`
        );
      }
    });
  });

  describe('🚨 TAB FUNCTIONALITY - All Tabs MUST Be Switchable', () => {
    it('REGRESSION CHECK: Can switch to Changelog tab', () => {
      renderWithProviders(<VersionHistory />);

      const changelogTab = screen.getByRole('tab', { name: /changelog/i });
      fireEvent.click(changelogTab);

      expect(changelogTab).toHaveAttribute('aria-selected', 'true');

      if (changelogTab.getAttribute('aria-selected') !== 'true') {
        throw new Error(
          `🚨 REGRESSION DETECTED: Cannot switch to Changelog tab! Tab switching is broken.`
        );
      }
    });

    it('REGRESSION CHECK: Can switch to Release Notes tab', () => {
      renderWithProviders(<VersionHistory />);

      const releaseNotesTab = screen.getByRole('tab', { name: /release notes/i });
      fireEvent.click(releaseNotesTab);

      expect(releaseNotesTab).toHaveAttribute('aria-selected', 'true');

      if (releaseNotesTab.getAttribute('aria-selected') !== 'true') {
        throw new Error(
          `🚨 REGRESSION DETECTED: Cannot switch to Release Notes tab! Tab switching is broken.`
        );
      }
    });

    it('REGRESSION CHECK: Can switch to What\'s New tab', () => {
      renderWithProviders(<VersionHistory />);

      const whatsNewTab = screen.getByRole('tab', { name: /what's new/i });
      fireEvent.click(whatsNewTab);

      expect(whatsNewTab).toHaveAttribute('aria-selected', 'true');

      if (whatsNewTab.getAttribute('aria-selected') !== 'true') {
        throw new Error(
          `🚨 REGRESSION DETECTED: Cannot switch to What's New tab! Tab switching is broken.`
        );
      }
    });

    it('REGRESSION CHECK: Can switch back to Current Version tab', () => {
      renderWithProviders(<VersionHistory />);

      // Switch to another tab first
      const changelogTab = screen.getByRole('tab', { name: /changelog/i });
      fireEvent.click(changelogTab);

      // Switch back to Current Version
      const currentVersionTab = screen.getByRole('tab', { name: /current version/i });
      fireEvent.click(currentVersionTab);

      expect(currentVersionTab).toHaveAttribute('aria-selected', 'true');

      if (currentVersionTab.getAttribute('aria-selected') !== 'true') {
        throw new Error(
          `🚨 REGRESSION DETECTED: Cannot switch back to Current Version tab! Tab switching is broken.`
        );
      }
    });
  });

  describe('🚨 NAVIGATION INTEGRATION - Component MUST Be Accessible', () => {
    it('REGRESSION CHECK: Component renders without crashing', () => {
      const { container } = renderWithProviders(<VersionHistory />);

      expect(container).toBeTruthy();
      expect(container.querySelector('[role="tabpanel"]')).toBeInTheDocument();

      if (!container.querySelector('[role="tabpanel"]')) {
        throw new Error(
          `🚨 REGRESSION DETECTED: VersionHistory component is not rendering properly!`
        );
      }
    });

    it('REGRESSION CHECK: Page title "Version History" MUST be visible', () => {
      renderWithProviders(<VersionHistory />);

      const title = screen.queryByText('Version History');

      expect(title).toBeInTheDocument();

      if (!title) {
        throw new Error(
          `🚨 REGRESSION DETECTED: Page title "Version History" is missing!`
        );
      }
    });
  });

  describe('🚨 FEATURE SNAPSHOT - Complete Feature List', () => {
    it('REGRESSION CHECK: Complete snapshot of all expected features', () => {
      renderWithProviders(<VersionHistory />);

      const expectedFeatures = {
        tabs: [
          'Current Version',
          'Changelog',
          'Release Notes',
          "What's New"
        ],
        currentVersionContent: [
          'Version Number',
          'Release Type',
          'Build Number',
          'Version Components'
        ],
        changelogContent: [
          'Recent Changes',
          'v100.3.1',
          'v100.0.0'
        ],
        releaseNotesContent: [
          'Key Features',
          'Technical Improvements',
          'Known Issues',
          'Breaking Changes'
        ],
        whatsNewContent: [
          'Highlights',
          'Why These Changes Matter',
          'Getting Started'
        ]
      };

      // Check all tabs exist
      const tabs = screen.getAllByRole('tab');
      const tabTexts = tabs.map(t => t.textContent || '');

      const missingTabs = expectedFeatures.tabs.filter(
        expectedTab => !tabTexts.some(actualTab => actualTab.includes(expectedTab))
      );

      if (missingTabs.length > 0) {
        throw new Error(
          `🚨 REGRESSION DETECTED: Missing tabs: ${missingTabs.join(', ')}\n` +
          `Expected: ${expectedFeatures.tabs.join(', ')}\n` +
          `Found: ${tabTexts.join(', ')}`
        );
      }

      // Check Current Version content
      expectedFeatures.currentVersionContent.forEach(feature => {
        const element = screen.queryByText(feature);
        if (!element) {
          throw new Error(
            `🚨 REGRESSION DETECTED: Current Version tab is missing "${feature}"`
          );
        }
      });

      // Switch to Changelog and check content
      fireEvent.click(screen.getByRole('tab', { name: /changelog/i }));
      expectedFeatures.changelogContent.forEach(feature => {
        const element = screen.queryAllByText(feature);
        if (element.length === 0) {
          throw new Error(
            `🚨 REGRESSION DETECTED: Changelog tab is missing "${feature}"`
          );
        }
      });

      // Switch to Release Notes and check content
      fireEvent.click(screen.getByRole('tab', { name: /release notes/i }));
      expectedFeatures.releaseNotesContent.forEach(feature => {
        const element = screen.queryAllByText(new RegExp(feature, 'i'));
        if (element.length === 0) {
          throw new Error(
            `🚨 REGRESSION DETECTED: Release Notes tab is missing "${feature}"`
          );
        }
      });

      // Switch to What's New and check content
      fireEvent.click(screen.getByRole('tab', { name: /what's new/i }));
      expectedFeatures.whatsNewContent.forEach(feature => {
        const element = screen.queryAllByText(new RegExp(feature, 'i'));
        if (element.length === 0) {
          throw new Error(
            `🚨 REGRESSION DETECTED: What's New tab is missing "${feature}"`
          );
        }
      });

      // If we get here, all features are present
      expect(true).toBe(true);
    });
  });
});
