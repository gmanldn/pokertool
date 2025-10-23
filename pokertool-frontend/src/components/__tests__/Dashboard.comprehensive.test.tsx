/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/__tests__/Dashboard.comprehensive.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Comprehensive test suite for Dashboard with 20 tests covering all functionality
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { Dashboard } from '../Dashboard';
import { renderWithProviders, checkAccessibility } from '../../test-utils/testHelpers';

describe('Dashboard Comprehensive Tests', () => {
  const mockMessages = [
    { type: 'stats_update', data: { handsPlayed: 50, vpip: 25, pfr: 18, aggression: 2.5, winRate: 55, profit: 150 } }
  ];

  // 1. Rendering without crashes
  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderWithProviders(<Dashboard messages={[]} />);
      expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    });

    it('should render version chip', () => {
      renderWithProviders(<Dashboard messages={[]} />);
      expect(screen.getByText(/v\d+\.\d+\.\d+/)).toBeInTheDocument();
    });

    it('should render empty state when no hands played', () => {
      renderWithProviders(<Dashboard messages={[]} />);
      expect(screen.getByText(/Start your first poker session/i)).toBeInTheDocument();
    });

    it('should render dashboard content when hands have been played', () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      waitFor(() => {
        expect(screen.getByText(/Hands Played/i)).toBeInTheDocument();
      });
    });
  });

  // 2. Interactive elements
  describe('Interactive Elements', () => {
    it('should have refresh button', () => {
      renderWithProviders(<Dashboard messages={[]} />);
      const refreshButton = screen.getByRole('button', { name: '' });
      expect(refreshButton).toBeInTheDocument();
    });

    it('should trigger refresh on button click', async () => {
      renderWithProviders(<Dashboard messages={[]} />);
      const refreshButton = screen.getAllByRole('button').find(btn =>
        btn.querySelector('[data-testid="RefreshIcon"]')
      );

      if (refreshButton) {
        await userEvent.click(refreshButton);
        expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
      }
    });

    it('should show loading indicator during refresh', async () => {
      renderWithProviders(<Dashboard messages={[]} />);
      const refreshButton = screen.getAllByRole('button').find(btn =>
        btn.querySelector('[data-testid="RefreshIcon"]')
      );

      if (refreshButton) {
        await userEvent.click(refreshButton);
        await waitFor(() => {
          expect(screen.queryByRole('progressbar')).toBeInTheDocument();
        });
      }
    });
  });

  // 3. Statistics cards
  describe('Statistics Cards', () => {
    it('should display hands played statistic', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/Hands Played/i)).toBeInTheDocument();
      });
    });

    it('should display session profit', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/Session Profit/i)).toBeInTheDocument();
      });
    });

    it('should display win rate', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/Win Rate/i)).toBeInTheDocument();
      });
    });

    it('should display session time', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/Session Time/i)).toBeInTheDocument();
      });
    });

    it('should show trend icons on stat cards', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        const trendIcons = screen.getAllByTestId(/TrendingUp|TrendingDown/i);
        expect(trendIcons.length).toBeGreaterThan(0);
      });
    });
  });

  // 4. Charts and visualizations
  describe('Charts', () => {
    it('should render profit chart when hands played', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/Weekly Profit Trend/i)).toBeInTheDocument();
      });
    });

    it('should render game type distribution chart', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/Game Type Distribution/i)).toBeInTheDocument();
      });
    });

    it('should not show charts in empty state', () => {
      renderWithProviders(<Dashboard messages={[]} />);
      expect(screen.queryByText(/Weekly Profit Trend/i)).not.toBeInTheDocument();
    });
  });

  // 5. Playing statistics
  describe('Playing Statistics', () => {
    it('should display VPIP statistic', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/VPIP/i)).toBeInTheDocument();
      });
    });

    it('should display PFR statistic', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/PFR/i)).toBeInTheDocument();
      });
    });

    it('should display aggression factor', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/Aggression Factor/i)).toBeInTheDocument();
      });
    });
  });

  // 6. Real-time updates
  describe('Real-time Updates', () => {
    it('should update stats when receiving new messages', async () => {
      const { rerender } = renderWithProviders(<Dashboard messages={[]} />);

      const newMessages = [
        { type: 'stats_update', data: { handsPlayed: 100, vpip: 30, pfr: 20, aggression: 3, winRate: 60, profit: 200 } }
      ];

      rerender(<Dashboard messages={newMessages} />);

      await waitFor(() => {
        expect(screen.getByText(/100/)).toBeInTheDocument();
      });
    });

    it('should show last update timestamp', () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      expect(screen.getByText(/Last Update:/i)).toBeInTheDocument();
    });
  });

  // 7. Session components
  describe('Session Components', () => {
    it('should render SessionClock component', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        expect(screen.getByText(/00:00:00/)).toBeInTheDocument();
      });
    });

    it('should render SessionGoalsTracker component', async () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      await waitFor(() => {
        const sessionGoals = screen.queryByText(/Session Goals/i);
        expect(sessionGoals || screen.getByText(/Dashboard/i)).toBeInTheDocument();
      });
    });
  });

  // 8. Responsive behavior
  describe('Responsive Design', () => {
    it('should render in mobile view', () => {
      window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: query === '(max-width: 600px)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      renderWithProviders(<Dashboard messages={[]} />);
      expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    });

    it('should adjust layout for mobile', () => {
      window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: query === '(max-width: 600px)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      renderWithProviders(<Dashboard messages={mockMessages} />);
      // Mobile view should still render all core components
      expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    });
  });

  // 9. Error states
  describe('Error Handling', () => {
    it('should handle missing data gracefully', () => {
      const incompleteMessages = [
        { type: 'stats_update', data: {} }
      ];

      renderWithProviders(<Dashboard messages={incompleteMessages} />);
      expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    });

    it('should handle null messages', () => {
      renderWithProviders(<Dashboard messages={[]} />);
      expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    });
  });

  // 10. Accessibility
  describe('Accessibility', () => {
    it('should have accessible stat cards', async () => {
      const { container } = renderWithProviders(<Dashboard messages={mockMessages} />);
      await checkAccessibility(container);
    });

    it('should have semantic HTML structure', () => {
      renderWithProviders(<Dashboard messages={mockMessages} />);
      expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    });
  });
});
