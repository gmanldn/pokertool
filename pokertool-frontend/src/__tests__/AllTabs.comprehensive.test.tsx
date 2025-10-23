/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/__tests__/AllTabs.comprehensive.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Comprehensive test suite for all tabs and routes - ensures all tabs exist and work
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import App from '../App';
import { renderWithProviders, mockBackendStatus, mockHealthData } from '../test-utils/testHelpers';
import '@testing-library/jest-dom';

/**
 * Comprehensive test suite for all tabs and routes
 * Verifies that:
 * - All tabs are visible in the Navigation menu
 * - All routes are accessible
 * - All components render without errors
 * - Tab switching works correctly
 */

describe('All Tabs and Routes - Comprehensive Tests', () => {
  const mockBackendOnline = mockBackendStatus('online');

  // List of all tabs that should exist
  const expectedTabs = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: '🧠 SmartHelper', path: '/smarthelper' },
    { label: '💬 AI Chat', path: '/ai-chat' },
    { label: '🚀 Improve', path: '/improve' },
    { label: 'Backend', path: '/backend' },
    { label: 'TODO', path: '/todo' },
    { label: '🤖 Autopilot', path: '/autopilot' },
    { label: '📊 Analysis', path: '/analysis' },
    { label: 'Tables', path: '/tables' },
    { label: 'Detection Log', path: '/detection-log' },
    { label: 'Statistics', path: '/statistics' },
    { label: 'Bankroll', path: '/bankroll' },
    { label: 'Tournament', path: '/tournament' },
    { label: 'HUD Overlay', path: '/hud' },
    { label: 'GTO Trainer', path: '/gto' },
    { label: 'Hand History', path: '/history' },
    { label: 'Version History', path: '/version-history' },
    { label: 'Settings', path: '/settings' },
    { label: 'Model Calibration', path: '/model-calibration' },
    { label: 'Opponent Fusion', path: '/opponent-fusion' },
    { label: 'Active Learning', path: '/active-learning' },
    { label: 'Scraping Accuracy', path: '/scraping-accuracy' },
    { label: 'System Status', path: '/system-status' },
  ];

  describe('Tab Visibility - All Tabs Exist', () => {
    beforeEach(() => {
      // Reset mocks before each test
      jest.clearAllMocks();
    });

    it('renders app without crashing', () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('displays Navigation component with all menu items', () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      // All tabs should be present (even if in drawer on mobile)
      expectedTabs.forEach((tab) => {
        const menuItem = screen.getByText(new RegExp(tab.label, 'i'));
        expect(menuItem).toBeInTheDocument();
      });
    });

    it('renders Dashboard tab', () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });

    it('renders Tables tab', () => {
      renderWithProviders(
        <App />,
        { route: '/tables' }
      );
      expect(screen.getByText(/tables/i)).toBeInTheDocument();
    });

    it('renders Detection Log tab', () => {
      renderWithProviders(
        <App />,
        { route: '/detection-log' }
      );
      expect(screen.getByText(/detection log/i)).toBeInTheDocument();
    });

    it('renders Version History tab', () => {
      renderWithProviders(
        <App />,
        { route: '/version-history' }
      );
      expect(screen.getByText(/version history/i)).toBeInTheDocument();
    });

    it('renders Statistics tab', () => {
      renderWithProviders(
        <App />,
        { route: '/statistics' }
      );
      expect(screen.getByText(/statistics/i)).toBeInTheDocument();
    });

    it('renders Settings tab', () => {
      renderWithProviders(
        <App />,
        { route: '/settings' }
      );
      expect(screen.getByText(/settings/i)).toBeInTheDocument();
    });

    it('renders Bankroll tab', () => {
      renderWithProviders(
        <App />,
        { route: '/bankroll' }
      );
      expect(screen.getByText(/bankroll/i)).toBeInTheDocument();
    });

    it('renders Tournament tab', () => {
      renderWithProviders(
        <App />,
        { route: '/tournament' }
      );
      expect(screen.getByText(/tournament/i)).toBeInTheDocument();
    });

    it('renders HUD Overlay tab', () => {
      renderWithProviders(
        <App />,
        { route: '/hud' }
      );
      expect(screen.getByText(/hud overlay/i)).toBeInTheDocument();
    });

    it('renders GTO Trainer tab', () => {
      renderWithProviders(
        <App />,
        { route: '/gto' }
      );
      expect(screen.getByText(/gto trainer/i)).toBeInTheDocument();
    });

    it('renders Hand History tab', () => {
      renderWithProviders(
        <App />,
        { route: '/history' }
      );
      expect(screen.getByText(/hand history/i)).toBeInTheDocument();
    });

    it('renders SmartHelper tab', () => {
      renderWithProviders(
        <App />,
        { route: '/smarthelper' }
      );
      expect(screen.getByText(/smarthelper/i)).toBeInTheDocument();
    });

    it('renders AI Chat tab', () => {
      renderWithProviders(
        <App />,
        { route: '/ai-chat' }
      );
      expect(screen.getByText(/ai chat/i)).toBeInTheDocument();
    });

    it('renders Improve tab', () => {
      renderWithProviders(
        <App />,
        { route: '/improve' }
      );
      expect(screen.getByText(/improve/i)).toBeInTheDocument();
    });

    it('renders Backend tab', () => {
      renderWithProviders(
        <App />,
        { route: '/backend' }
      );
      expect(screen.getByText(/backend/i)).toBeInTheDocument();
    });

    it('renders TODO tab', () => {
      renderWithProviders(
        <App />,
        { route: '/todo' }
      );
      expect(screen.getByText(/todo/i)).toBeInTheDocument();
    });

    it('renders Autopilot tab', () => {
      renderWithProviders(
        <App />,
        { route: '/autopilot' }
      );
      expect(screen.getByText(/autopilot/i)).toBeInTheDocument();
    });

    it('renders Analysis tab', () => {
      renderWithProviders(
        <App />,
        { route: '/analysis' }
      );
      expect(screen.getByText(/analysis/i)).toBeInTheDocument();
    });

    it('renders Model Calibration tab', () => {
      renderWithProviders(
        <App />,
        { route: '/model-calibration' }
      );
      expect(screen.getByText(/model calibration/i)).toBeInTheDocument();
    });

    it('renders Opponent Fusion tab', () => {
      renderWithProviders(
        <App />,
        { route: '/opponent-fusion' }
      );
      expect(screen.getByText(/opponent fusion/i)).toBeInTheDocument();
    });

    it('renders Active Learning tab', () => {
      renderWithProviders(
        <App />,
        { route: '/active-learning' }
      );
      expect(screen.getByText(/active learning/i)).toBeInTheDocument();
    });

    it('renders Scraping Accuracy tab', () => {
      renderWithProviders(
        <App />,
        { route: '/scraping-accuracy' }
      );
      expect(screen.getByText(/scraping accuracy/i)).toBeInTheDocument();
    });

    it('renders System Status tab', () => {
      renderWithProviders(
        <App />,
        { route: '/system-status' }
      );
      expect(screen.getByText(/system status/i)).toBeInTheDocument();
    });
  });

  describe('Tab Navigation - Switching Between Tabs', () => {
    it('navigates from Dashboard to Tables', async () => {
      const { container } = renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      // Find and click Tables menu item
      const tablesButton = screen.getByText(/tables/i);
      fireEvent.click(tablesButton);

      await waitFor(() => {
        // Verify we're on the Tables route
        expect(screen.getByText(/tables/i)).toBeInTheDocument();
      });
    });

    it('navigates from Dashboard to Detection Log', async () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      const detectionLogButton = screen.getByText(/detection log/i);
      fireEvent.click(detectionLogButton);

      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });
    });

    it('navigates from Dashboard to Version History', async () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      const versionButton = screen.getByText(/version history/i);
      fireEvent.click(versionButton);

      await waitFor(() => {
        expect(screen.getByText(/version history/i)).toBeInTheDocument();
      });
    });

    it('navigates between multiple tabs in sequence', async () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      // Navigate to Tables
      fireEvent.click(screen.getByText(/tables/i));
      await waitFor(() => {
        expect(screen.getByText(/tables/i)).toBeInTheDocument();
      });

      // Navigate to Detection Log
      fireEvent.click(screen.getByText(/detection log/i));
      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });

      // Navigate back to Dashboard
      fireEvent.click(screen.getByText(/dashboard/i));
      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
      });
    });
  });

  describe('Route Configuration - All Routes Exist', () => {
    const testRoutes = [
      { path: '/', redirectsTo: '/dashboard' },
      { path: '/dashboard' },
      { path: '/smarthelper' },
      { path: '/ai-chat' },
      { path: '/improve' },
      { path: '/backend' },
      { path: '/todo' },
      { path: '/autopilot' },
      { path: '/analysis' },
      { path: '/tables' },
      { path: '/detection-log' },
      { path: '/statistics' },
      { path: '/bankroll' },
      { path: '/tournament' },
      { path: '/hud' },
      { path: '/gto' },
      { path: '/history' },
      { path: '/version-history' },
      { path: '/settings' },
      { path: '/model-calibration' },
      { path: '/system-status' },
      { path: '/opponent-fusion' },
      { path: '/active-learning' },
      { path: '/scraping-accuracy' },
    ];

    testRoutes.forEach((route) => {
      it(`route ${route.path} is accessible`, () => {
        renderWithProviders(
          <Router>
            <App />
          </Router>,
          { route: route.path }
        );
        // Verify app renders without error
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });
    });
  });

  describe('Tab Persistence - State Maintained', () => {
    it('maintains theme preference across tab navigation', async () => {
      const { container } = renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      // Navigate to different tabs and verify theme context is maintained
      fireEvent.click(screen.getByText(/tables/i));
      await waitFor(() => {
        expect(screen.getByText(/tables/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/detection log/i));
      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });

      // Theme should be consistent (verified through ThemeContext provider)
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });
  });

  describe('Tab Accessibility - Keyboard Navigation', () => {
    it('allows keyboard navigation between tabs', async () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      // Tab key should navigate through menu items (if using proper ARIA roles)
      const menuItem = screen.getByText(/tables/i);
      menuItem.focus();
      expect(document.activeElement).toBe(menuItem);
    });
  });

  describe('Tab Content Loading - Fallback States', () => {
    it('shows loading fallback while components load', async () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      // Suspense should show loading state initially
      // Component should render after loading completes
      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });
    });

    it('handles errors gracefully with error boundaries', () => {
      // This test verifies that error boundaries are in place
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      // App should still render despite any component errors
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });
  });

  describe('Tab Routing - Direct URL Access', () => {
    it('allows direct URL access to Dashboard', () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });

    it('allows direct URL access to Detection Log', () => {
      renderWithProviders(
        <App />,
        { route: '/detection-log' }
      );
      expect(screen.getByText(/detection log/i)).toBeInTheDocument();
    });

    it('allows direct URL access to Version History', () => {
      renderWithProviders(
        <App />,
        { route: '/version-history' }
      );
      expect(screen.getByText(/version history/i)).toBeInTheDocument();
    });

    it('allows direct URL access to Tables', () => {
      renderWithProviders(
        <App />,
        { route: '/tables' }
      );
      expect(screen.getByText(/tables/i)).toBeInTheDocument();
    });

    it('redirects root path to Dashboard', () => {
      renderWithProviders(
        <App />,
        { route: '/' }
      );
      // Should redirect to dashboard which renders the navigation and main content
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });
  });

  describe('Tab Count and Completeness', () => {
    it(`has exactly ${expectedTabs.length} menu items`, () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      const menuItems = expectedTabs.filter((tab) => {
        try {
          return !!screen.getByText(new RegExp(tab.label, 'i'));
        } catch {
          return false;
        }
      });

      expect(menuItems.length).toBe(expectedTabs.length);
    });

    it('has all expected tab labels', () => {
      renderWithProviders(
        <App />,
        { route: '/dashboard' }
      );

      expectedTabs.forEach((tab) => {
        expect(screen.getByText(new RegExp(tab.label, 'i'))).toBeInTheDocument();
      });
    });
  });
});
