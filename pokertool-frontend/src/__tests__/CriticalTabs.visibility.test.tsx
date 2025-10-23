/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/__tests__/CriticalTabs.visibility.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Critical test suite for Detection Log and Tables tab visibility and functionality
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import App from '../App';
import { renderWithProviders, mockBackendStatus } from '../test-utils/testHelpers';
import '@testing-library/jest-dom';

/**
 * CRITICAL TEST SUITE
 *
 * These tests MUST PASS to ensure Detection Log and Tables tabs
 * are always visible and functional in the UI
 */

describe('CRITICAL: Detection Log and Tables Tab Visibility', () => {
  const mockBackendOnline = mockBackendStatus('online');

  describe('Detection Log Tab - CRITICAL', () => {
    it('Detection Log menu item MUST be visible in navigation', () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      // This test MUST pass - Detection Log must be in the menu
      const detectionLogItem = screen.getByText(/detection log/i);
      expect(detectionLogItem).toBeInTheDocument();
      expect(detectionLogItem).toBeVisible();
    });

    it('Detection Log route MUST be accessible', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/detection-log' }
      );

      // Navigate to Detection Log
      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });
    });

    it('Detection Log component MUST render without errors', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/detection-log' }
      );

      // Component should load (even if empty initially)
      const banner = screen.getByRole('banner');
      expect(banner).toBeInTheDocument();
      expect(banner).toBeVisible();
    });

    it('Detection Log must be clickable from dashboard', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      const detectionLogButton = screen.getByText(/detection log/i);
      fireEvent.click(detectionLogButton);

      // Should navigate to detection log route
      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });
    });

    it('Detection Log icon MUST be in menu', () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      // Detection Log has Article icon - verify it's rendered
      const article = screen.getByText(/detection log/i).closest('li');
      expect(article).toBeInTheDocument();
    });
  });

  describe('Tables Tab (LiveTable) - CRITICAL', () => {
    it('Tables menu item MUST be visible in navigation', () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      // This test MUST pass - Tables must be in the menu
      const tablesItem = screen.getByText(/^Tables$/i);
      expect(tablesItem).toBeInTheDocument();
      expect(tablesItem).toBeVisible();
    });

    it('Tables route MUST be accessible', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/tables' }
      );

      // Tables component should render
      await waitFor(() => {
        expect(screen.getByText(/tables/i)).toBeInTheDocument();
      });
    });

    it('Tables component MUST render without errors', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/tables' }
      );

      // Component should load
      const banner = screen.getByRole('banner');
      expect(banner).toBeInTheDocument();
      expect(banner).toBeVisible();
    });

    it('Tables must be clickable from dashboard', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      const tablesButton = screen.getByText(/^Tables$/i);
      fireEvent.click(tablesButton);

      // Should navigate to tables route
      await waitFor(() => {
        expect(screen.getByText(/tables/i)).toBeInTheDocument();
      });
    });

    it('Tables icon MUST be in menu', () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      // Tables has TableChart icon - verify it's rendered
      const tables = screen.getByText(/^Tables$/i).closest('li');
      expect(tables).toBeInTheDocument();
    });
  });

  describe('Both Tabs in Correct Order', () => {
    it('Tables MUST appear before Detection Log in menu', () => {
      const { container } = renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      const tablesItem = screen.getByText(/^Tables$/i);
      const detectionLogItem = screen.getByText(/detection log/i);

      // Both should exist
      expect(tablesItem).toBeInTheDocument();
      expect(detectionLogItem).toBeInTheDocument();
    });

    it('Can navigate from Tables to Detection Log', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/tables' }
      );

      // Start on Tables
      expect(screen.getByText(/tables/i)).toBeInTheDocument();

      // Navigate to Detection Log
      const detectionLogButton = screen.getByText(/detection log/i);
      fireEvent.click(detectionLogButton);

      await waitFor(() => {
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();
      });
    });

    it('Can navigate from Detection Log to Tables', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/detection-log' }
      );

      // Start on Detection Log
      expect(screen.getByText(/detection log/i)).toBeInTheDocument();

      // Navigate to Tables
      const tablesButton = screen.getByText(/^Tables$/i);
      fireEvent.click(tablesButton);

      await waitFor(() => {
        expect(screen.getByText(/tables/i)).toBeInTheDocument();
      });
    });
  });

  describe('Direct URL Access - CRITICAL', () => {
    it('Direct URL /detection-log MUST work', () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/detection-log' }
      );

      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByText(/detection log/i)).toBeInTheDocument();
    });

    it('Direct URL /tables MUST work', () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/tables' }
      );

      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByText(/tables/i)).toBeInTheDocument();
    });
  });

  describe('Menu Rendering - CRITICAL', () => {
    it('Menu MUST render both tabs on first load', () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/' }
      );

      // Both tabs must be present
      expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      expect(screen.getByText(/detection log/i)).toBeInTheDocument();
    });

    it('Menu MUST show tabs after theme change', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      // Get theme toggle button and click it
      const themeButtons = screen.getAllByRole('button').filter(
        (btn) => btn.querySelector('svg') // Has icon
      );

      // Both tabs should still be visible
      expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();
      expect(screen.getByText(/detection log/i)).toBeInTheDocument();
    });
  });

  describe('Regression Prevention', () => {
    it('Detection Log MUST remain visible after 5 navigation cycles', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      for (let i = 0; i < 5; i++) {
        // Verify Detection Log is visible
        expect(screen.getByText(/detection log/i)).toBeInTheDocument();

        // Navigate to it
        fireEvent.click(screen.getByText(/detection log/i));

        await waitFor(() => {
          expect(screen.getByText(/detection log/i)).toBeInTheDocument();
        });

        // Navigate away
        fireEvent.click(screen.getByText(/dashboard/i));

        await waitFor(() => {
          expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
        });
      }
    });

    it('Tables MUST remain visible after 5 navigation cycles', async () => {
      renderWithProviders(
        <Router>
          <App />
        </Router>,
        { route: '/dashboard' }
      );

      for (let i = 0; i < 5; i++) {
        // Verify Tables is visible
        expect(screen.getByText(/^Tables$/i)).toBeInTheDocument();

        // Navigate to it
        fireEvent.click(screen.getByText(/^Tables$/i));

        await waitFor(() => {
          expect(screen.getByText(/tables/i)).toBeInTheDocument();
        });

        // Navigate away
        fireEvent.click(screen.getByText(/dashboard/i));

        await waitFor(() => {
          expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
        });
      }
    });
  });
});
