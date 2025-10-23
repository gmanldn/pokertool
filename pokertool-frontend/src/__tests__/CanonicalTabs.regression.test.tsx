/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/__tests__/CanonicalTabs.regression.test.tsx
version: v1.0.0
last_commit: '2025-10-23T20:35:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Comprehensive regression tests for canonical tabs to prevent disappearance
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { renderWithProviders } from '../test-utils/testHelpers';
import '@testing-library/jest-dom';

/**
 * CANONICAL TABS REGRESSION TEST SUITE
 *
 * These tests ensure that canonical tabs (core navigation items) are NEVER removed
 * or hidden from the UI. These are critical user-facing navigation elements that
 * MUST always exist in the navigation.
 *
 * Canonical tabs in desktop navigation order:
 * 1. Dashboard
 * 2. SmartHelper
 * 3. AI Chat
 * 4. Improve
 * 5. Backend
 * 6. Tables          <- CRITICAL: Must always be visible
 * 7. Detection Log   <- CRITICAL: Must always be visible
 * 8. Version History <- CRITICAL: Must always be visible
 * 9. System Status
 */

describe('CANONICAL TABS - REGRESSION PREVENTION SUITE', () => {
  /**
   * CRITICAL TESTS: Tables Tab
   * These tests ensure the Tables tab is NEVER removed from navigation
   */
  describe('Tables Tab - CRITICAL REGRESSION TESTS', () => {
    it('Tables tab MUST always be present in navigation', () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const tablesItem = screen.getByText(/^Tables$/i);
      expect(tablesItem).toBeInTheDocument();
      expect(tablesItem).toBeVisible();
    });

    it('Tables route MUST be accessible', async () => {
      renderWithProviders(<App />, { route: '/tables' });

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });
    });

    it('Tables tab MUST be clickable from Dashboard', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const tablesItem = screen.getByText(/^Tables$/i);
      fireEvent.click(tablesItem);

      await waitFor(() => {
        expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      });
    });

    it('Tables MUST remain visible in navigation after clicking', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const tablesItem = screen.getByText(/^Tables$/i);
      fireEvent.click(tablesItem);

      await waitFor(() => {
        // Tables should still be in the navigation
        expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      });
    });

    it('Tables MUST be visible in mobile drawer', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      // Open drawer on mobile
      const menuButton = screen.getByRole('button', { name: /menu/i });
      fireEvent.click(menuButton);

      await waitFor(() => {
        expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      });
    });
  });

  /**
   * CRITICAL TESTS: Detection Log Tab
   * These tests ensure the Detection Log tab is NEVER removed from navigation
   */
  describe('Detection Log Tab - CRITICAL REGRESSION TESTS', () => {
    it('Detection Log tab MUST always be present in navigation', () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const detectionLogItem = screen.getByText(/detection log/i);
      expect(detectionLogItem).toBeInTheDocument();
      expect(detectionLogItem).toBeVisible();
    });

    it('Detection Log route MUST be accessible', async () => {
      renderWithProviders(<App />, { route: '/detection-log' });

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });
    });

    it('Detection Log tab MUST be clickable from Dashboard', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const detectionLogItem = screen.getByText(/detection log/i);
      fireEvent.click(detectionLogItem);

      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });
    });

    it('Detection Log MUST remain visible in navigation after clicking', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const detectionLogItem = screen.getByText(/detection log/i);
      fireEvent.click(detectionLogItem);

      await waitFor(() => {
        // Detection Log should still be in the navigation
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });
    });

    it('Detection Log MUST be visible in mobile drawer', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      // Open drawer on mobile
      const menuButton = screen.getByRole('button', { name: /menu/i });
      fireEvent.click(menuButton);

      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });
    });
  });

  /**
   * CRITICAL TESTS: Version History Tab
   * These tests ensure the Version History tab is NEVER removed from navigation
   */
  describe('Version History Tab - CRITICAL REGRESSION TESTS', () => {
    it('Version History tab MUST always be present in navigation', () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const versionHistoryItem = screen.getByText(/version history/i);
      expect(versionHistoryItem).toBeInTheDocument();
      expect(versionHistoryItem).toBeVisible();
    });

    it('Version History route MUST be accessible', async () => {
      renderWithProviders(<App />, { route: '/version-history' });

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });
    });

    it('Version History tab MUST be clickable from Dashboard', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const versionHistoryItem = screen.getByText(/version history/i);
      fireEvent.click(versionHistoryItem);

      await waitFor(() => {
        expect(screen.getByText(/version history/i)).toBeInTheDocument();
      });
    });

    it('Version History MUST remain visible in navigation after clicking', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const versionHistoryItem = screen.getByText(/version history/i);
      fireEvent.click(versionHistoryItem);

      await waitFor(() => {
        // Version History should still be in the navigation
        expect(screen.getByText(/version history/i)).toBeInTheDocument();
      });
    });

    it('Version History MUST be visible in mobile drawer', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      // Open drawer on mobile
      const menuButton = screen.getByRole('button', { name: /menu/i });
      fireEvent.click(menuButton);

      await waitFor(() => {
        expect(screen.getByText(/version history/i)).toBeInTheDocument();
      });
    });
  });

  /**
   * CANONICAL TAB INTERACTION TESTS
   * These tests ensure canonical tabs work correctly together
   */
  describe('Canonical Tabs - Interaction Tests', () => {
    it('All three critical tabs (Tables, Detection Log, Version History) MUST be visible simultaneously', () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      const tablesItem = screen.getByText(/^Tables$/i);
      const detectionLogItem = screen.getByText(/detection log/i);
      const versionHistoryItem = screen.getByText(/version history/i);

      expect(tablesItem).toBeInTheDocument();
      expect(detectionLogItem).toBeInTheDocument();
      expect(versionHistoryItem).toBeInTheDocument();
    });

    it('MUST be able to navigate between Tables, Detection Log, and Version History', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      // Navigate to Tables
      fireEvent.click(screen.getByText(/^Tables$/i));

      await waitFor(() => {
        expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      });

      // Navigate to Detection Log
      fireEvent.click(screen.getByText(/detection log/i));

      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });

      // Navigate to Version History
      fireEvent.click(screen.getByText(/version history/i));

      await waitFor(() => {
        expect(screen.getByText(/version history/i)).toBeInTheDocument();
      });

      // Navigate back to Tables
      fireEvent.click(screen.getByText(/^Tables$/i));

      await waitFor(() => {
        expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      });
    });

    it('MUST persist all canonical tabs through multiple navigation cycles', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      // First cycle
      fireEvent.click(screen.getByText(/^Tables$/i));
      await waitFor(() => {
        expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/detection log/i));
      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });

      // Second cycle
      fireEvent.click(screen.getByText(/^Tables$/i));
      await waitFor(() => {
        expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      });

      // Both should still exist
      expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      expect(screen.getByText(/detection log/i)).toBeInTheDocument();
    });

    it('Detection Log MUST be clickable from Tables view', async () => {
      renderWithProviders(<App />, { route: '/tables' });

      const detectionLogItem = screen.getByText(/detection log/i);
      expect(detectionLogItem).toBeInTheDocument();

      fireEvent.click(detectionLogItem);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });
    });

    it('Tables MUST be clickable from Detection Log view', async () => {
      renderWithProviders(<App />, { route: '/detection-log' });

      const tablesItem = screen.getByText(/^Tables$/i);
      expect(tablesItem).toBeInTheDocument();

      fireEvent.click(tablesItem);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });
    });
  });

  /**
   * CANONICAL TABS IN MENU STRUCTURE
   * These tests ensure canonical tabs are properly positioned in the menu
   */
  describe('Canonical Tabs - Menu Structure', () => {
    it('All canonical tabs MUST be in the menu items array', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      // Check all 9 canonical tabs
      const canonicalTabTexts = [
        'Dashboard',
        '🧠 SmartHelper',
        '💬 AI Chat',
        '🚀 Improve',
        'Backend',
        /^Tables$/i,
        /detection log/i,
        /version history/i,
        'System Status',
      ];

      for (const tabText of canonicalTabTexts) {
        await waitFor(() => {
          expect(screen.getByText(tabText)).toBeInTheDocument();
        });
      }
    });

    it('Tables, Detection Log, and Version History MUST appear together in mobile drawer', async () => {
      renderWithProviders(<App />, { route: '/dashboard' });

      // Open mobile drawer
      const menuButton = screen.getByRole('button', { name: /menu/i });
      fireEvent.click(menuButton);

      await waitFor(() => {
        const tablesItem = screen.getByText(/^Tables$/i);
        const detectionLogItem = screen.getByText(/detection log/i);
        const versionHistoryItem = screen.getByText(/version history/i);

        expect(tablesItem).toBeInTheDocument();
        expect(detectionLogItem).toBeInTheDocument();
        expect(versionHistoryItem).toBeInTheDocument();

        // They should be in the drawer
        const drawer = tablesItem.closest('[role="presentation"]');
        expect(drawer).toContainElement(detectionLogItem);
        expect(drawer).toContainElement(versionHistoryItem);
      });
    });
  });
});
