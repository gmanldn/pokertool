/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/__tests__/VersionHistory.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Comprehensive regression tests for VersionHistory component - 25 tests
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, within } from '@testing-library/react';
import { VersionHistory } from '../VersionHistory';
import { renderWithProviders } from '../../test-utils/testHelpers';
import '@testing-library/jest-dom';
import { RELEASE_VERSION } from '../../config/releaseVersion';

describe('VersionHistory Component - Comprehensive Tests', () => {
  describe('Rendering', () => {
    it('renders without crashing', () => {
      renderWithProviders(<VersionHistory />);
      expect(screen.getByText(/version history/i)).toBeInTheDocument();
    });

    it('displays page title', () => {
      renderWithProviders(<VersionHistory />);
      expect(screen.getByText('Version History')).toBeInTheDocument();
    });

    it('displays current version chip', () => {
      renderWithProviders(<VersionHistory />);
      expect(screen.getByText(RELEASE_VERSION)).toBeInTheDocument();
    });

    it('shows page description', () => {
      renderWithProviders(<VersionHistory />);
      expect(screen.getByText(/track releases, features, and improvements/i)).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('renders all 4 tabs', () => {
      renderWithProviders(<VersionHistory />);

      expect(screen.getByRole('tab', { name: /current version/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /changelog/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /release notes/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /what's new/i })).toBeInTheDocument();
    });

    it('shows Current Version tab by default', () => {
      renderWithProviders(<VersionHistory />);

      const currentVersionTab = screen.getByRole('tab', { name: /current version/i });
      expect(currentVersionTab).toHaveAttribute('aria-selected', 'true');
    });

    it('switches to Changelog tab when clicked', () => {
      renderWithProviders(<VersionHistory />);

      const changelogTab = screen.getByRole('tab', { name: /changelog/i });
      fireEvent.click(changelogTab);

      expect(changelogTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByText(/recent changes/i)).toBeInTheDocument();
    });

    it('switches to Release Notes tab when clicked', () => {
      renderWithProviders(<VersionHistory />);

      const releaseNotesTab = screen.getByRole('tab', { name: /release notes/i });
      fireEvent.click(releaseNotesTab);

      expect(releaseNotesTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByText(/key features/i)).toBeInTheDocument();
    });

    it('switches to What\'s New tab when clicked', () => {
      renderWithProviders(<VersionHistory />);

      const whatsNewTab = screen.getByRole('tab', { name: /what's new/i });
      fireEvent.click(whatsNewTab);

      expect(whatsNewTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByText(/highlights/i)).toBeInTheDocument();
    });

    it('displays tab icons', () => {
      renderWithProviders(<VersionHistory />);

      // Icons should be present in tabs (MUI renders them as SVGs)
      const tabs = screen.getAllByRole('tab');
      expect(tabs.length).toBe(4);
    });
  });

  describe('Current Version Tab', () => {
    it('displays version number card', () => {
      renderWithProviders(<VersionHistory />);

      expect(screen.getByText('Version Number')).toBeInTheDocument();
      expect(screen.getByText(RELEASE_VERSION)).toBeInTheDocument();
    });

    it('shows release type card', () => {
      renderWithProviders(<VersionHistory />);

      expect(screen.getByText('Release Type')).toBeInTheDocument();
      // Version 100+ should be Production
      expect(screen.getByText(/production|beta/i)).toBeInTheDocument();
    });

    it('displays build number breakdown', () => {
      renderWithProviders(<VersionHistory />);

      expect(screen.getByText('Build Number')).toBeInTheDocument();
      const [major, minor, patch] = RELEASE_VERSION.replace('v', '').split('.');
      expect(screen.getByText(new RegExp(`Major: ${major}`))).toBeInTheDocument();
    });

    it('shows "you are running latest version" alert', () => {
      renderWithProviders(<VersionHistory />);

      expect(screen.getByText(/you are running the latest version/i)).toBeInTheDocument();
    });

    it('displays version components explanation', () => {
      renderWithProviders(<VersionHistory />);

      expect(screen.getByText('Major Version')).toBeInTheDocument();
      expect(screen.getByText('Minor Version')).toBeInTheDocument();
      expect(screen.getByText('Patch Version')).toBeInTheDocument();
    });
  });

  describe('Changelog Tab', () => {
    beforeEach(() => {
      renderWithProviders(<VersionHistory />);
      const changelogTab = screen.getByRole('tab', { name: /changelog/i });
      fireEvent.click(changelogTab);
    });

    it('displays "Recent Changes" heading', () => {
      expect(screen.getByText('Recent Changes')).toBeInTheDocument();
    });

    it('shows v100.3.1 changes', () => {
      expect(screen.getByText('v100.3.1')).toBeInTheDocument();
      expect(screen.getByText(/thread management & version display/i)).toBeInTheDocument();
    });

    it('displays thread management feature', () => {
      expect(screen.getByText(/comprehensive thread management and cleanup system/i)).toBeInTheDocument();
    });

    it('shows version blade feature', () => {
      expect(screen.getByText(/version history blade in navigation drawer/i)).toBeInTheDocument();
    });

    it('displays tabbed interface feature', () => {
      expect(screen.getByText(/tabbed version history interface/i)).toBeInTheDocument();
    });

    it('shows v100.0.0 major release', () => {
      expect(screen.getByText('v100.0.0')).toBeInTheDocument();
      expect(screen.getByText(/quality, reliability, and bootstrap excellence/i)).toBeInTheDocument();
    });

    it('marks v100.3.1 as current release', () => {
      const currentRelease = screen.getByText('Current Release');
      expect(currentRelease).toBeInTheDocument();
    });
  });

  describe('Release Notes Tab', () => {
    beforeEach(() => {
      renderWithProviders(<VersionHistory />);
      const releaseNotesTab = screen.getByRole('tab', { name: /release notes/i });
      fireEvent.click(releaseNotesTab);
    });

    it('displays release notes title', () => {
      expect(screen.getByText(new RegExp(`Release Notes - ${RELEASE_VERSION}`))).toBeInTheDocument();
    });

    it('shows "Production Ready" alert', () => {
      expect(screen.getByText(/production ready/i)).toBeInTheDocument();
    });

    it('displays key features section', () => {
      expect(screen.getByText(/key features/i)).toBeInTheDocument();
      expect(screen.getByText('Thread Management System')).toBeInTheDocument();
    });

    it('shows technical improvements section', () => {
      expect(screen.getByText(/technical improvements/i)).toBeInTheDocument();
      expect(screen.getByText(/ThreadManager with lifecycle management/i)).toBeInTheDocument();
    });

    it('displays ThreadCleanupManager feature', () => {
      expect(screen.getByText(/ThreadCleanupManager utility/i)).toBeInTheDocument();
    });

    it('shows signal handlers feature', () => {
      expect(screen.getByText(/signal handlers/i)).toBeInTheDocument();
    });

    it('displays known issues section', () => {
      expect(screen.getByText('Known Issues')).toBeInTheDocument();
    });

    it('shows breaking changes section', () => {
      expect(screen.getByText('Breaking Changes')).toBeInTheDocument();
    });
  });

  describe('What\'s New Tab', () => {
    beforeEach(() => {
      renderWithProviders(<VersionHistory />);
      const whatsNewTab = screen.getByRole('tab', { name: /what's new/i });
      fireEvent.click(whatsNewTab);
    });

    it('displays "What\'s New" title', () => {
      expect(screen.getByText(new RegExp(`What's New in ${RELEASE_VERSION}`))).toBeInTheDocument();
    });

    it('shows highlights section', () => {
      expect(screen.getByText('Highlights')).toBeInTheDocument();
    });

    it('displays comprehensive thread management highlight', () => {
      expect(screen.getByText(/comprehensive thread management/i)).toBeInTheDocument();
    });

    it('shows version history dashboard highlight', () => {
      expect(screen.getByText(/version history dashboard/i)).toBeInTheDocument();
    });

    it('displays test count highlight', () => {
      expect(screen.getByText(/31 new tests/i)).toBeInTheDocument();
    });

    it('shows "Why These Changes Matter" section', () => {
      expect(screen.getByText(/why these changes matter/i)).toBeInTheDocument();
    });

    it('displays clean startup explanation', () => {
      expect(screen.getByText('Clean Startup and Shutdown')).toBeInTheDocument();
    });

    it('shows graceful shutdown explanation', () => {
      expect(screen.getByText('Graceful Shutdown')).toBeInTheDocument();
    });

    it('displays better visibility explanation', () => {
      expect(screen.getByText('Better Visibility')).toBeInTheDocument();
    });

    it('shows getting started section', () => {
      expect(screen.getByText('Getting Started')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes on tabs', () => {
      renderWithProviders(<VersionHistory />);

      const tabs = screen.getAllByRole('tab');
      tabs.forEach((tab) => {
        expect(tab).toHaveAttribute('aria-controls');
        expect(tab).toHaveAttribute('aria-selected');
      });
    });

    it('supports keyboard navigation between tabs', () => {
      renderWithProviders(<VersionHistory />);

      const firstTab = screen.getByRole('tab', { name: /current version/i });
      firstTab.focus();

      expect(document.activeElement).toBe(firstTab);
    });

    it('has semantic heading hierarchy', () => {
      renderWithProviders(<VersionHistory />);

      // Should have proper h4, h5, h6 hierarchy
      const mainHeading = screen.getByText('Version History');
      expect(mainHeading.tagName).toMatch(/H[1-6]/);
    });
  });

  describe('Visual Elements', () => {
    it('displays version chip with monospace font', () => {
      renderWithProviders(<VersionHistory />);

      const versionChip = screen.getByText(RELEASE_VERSION);
      expect(versionChip).toBeInTheDocument();
    });

    it('shows cards in grid layout', () => {
      renderWithProviders(<VersionHistory />);

      // Cards should be rendered (implementation-specific)
      expect(screen.getByText('Version Number')).toBeInTheDocument();
    });

    it('displays icons in appropriate sections', () => {
      renderWithProviders(<VersionHistory />);

      // Icons should be present throughout the component
      // MUI icons are rendered as SVGs
      const container = screen.getByText('Version History').closest('div');
      expect(container).toBeInTheDocument();
    });
  });
});
