/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/__tests__/Statistics.comprehensive.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Comprehensive test suite for Statistics with 20 tests covering all functionality
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { Statistics } from '../Statistics';
import { renderWithProviders, checkAccessibility } from '../../test-utils/testHelpers';

describe('Statistics Comprehensive Tests', () => {
  // 1. Rendering without crashes
  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/Statistics Dashboard/i)).toBeInTheDocument();
    });

    it('should render all summary cards', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/Total Profit/i)).toBeInTheDocument();
      expect(screen.getByText(/Hands Played/i)).toBeInTheDocument();
      expect(screen.getByText(/Win Rate/i)).toBeInTheDocument();
      expect(screen.getByText(/ROI/i)).toBeInTheDocument();
    });

    it('should render all tabs', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByRole('tab', { name: /Session Analysis/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Position Stats/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Hand Strength/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Opponent Analysis/i })).toBeInTheDocument();
    });
  });

  // 2. Filter controls
  describe('Filter Controls', () => {
    it('should have time range filter', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByLabelText(/Time Range/i)).toBeInTheDocument();
    });

    it('should have game type filter', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByLabelText(/Game Type/i)).toBeInTheDocument();
    });

    it('should change time range filter', async () => {
      renderWithProviders(<Statistics />);

      const timeRangeSelect = screen.getByLabelText(/Time Range/i);
      await userEvent.click(timeRangeSelect);
      await userEvent.click(screen.getByRole('option', { name: /Last 7 days/i }));

      expect(screen.getByText(/Last 7 days/i)).toBeInTheDocument();
    });

    it('should change game type filter', async () => {
      renderWithProviders(<Statistics />);

      const gameTypeSelect = screen.getByLabelText(/Game Type/i);
      await userEvent.click(gameTypeSelect);
      await userEvent.click(screen.getByRole('option', { name: /Cash Games/i }));

      expect(screen.getByText(/Cash Games/i)).toBeInTheDocument();
    });

    it('should have all time range options', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByLabelText(/Time Range/i));

      expect(screen.getByRole('option', { name: /Last 7 days/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Last 30 days/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Last 90 days/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Last year/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /All time/i })).toBeInTheDocument();
    });
  });

  // 3. Tab navigation
  describe('Tab Navigation', () => {
    it('should switch to Position Stats tab', async () => {
      renderWithProviders(<Statistics />);

      const positionTab = screen.getByRole('tab', { name: /Position Stats/i });
      await userEvent.click(positionTab);

      expect(positionTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByText(/Position Analysis/i)).toBeInTheDocument();
    });

    it('should switch to Hand Strength tab', async () => {
      renderWithProviders(<Statistics />);

      const handStrengthTab = screen.getByRole('tab', { name: /Hand Strength/i });
      await userEvent.click(handStrengthTab);

      expect(handStrengthTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByText(/Hand Strength Performance/i)).toBeInTheDocument();
    });

    it('should switch to Opponent Analysis tab', async () => {
      renderWithProviders(<Statistics />);

      const opponentTab = screen.getByRole('tab', { name: /Opponent Analysis/i });
      await userEvent.click(opponentTab);

      expect(opponentTab).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByText(/Opponent Types Encountered/i)).toBeInTheDocument();
    });

    it('should maintain tab selection state', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Position Stats/i }));
      const positionTab = screen.getByRole('tab', { name: /Position Stats/i });

      expect(positionTab).toHaveAttribute('aria-selected', 'true');
    });
  });

  // 4. Session Analysis tab
  describe('Session Analysis Tab', () => {
    it('should render profit trend chart', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/Profit Trend/i)).toBeInTheDocument();
    });

    it('should render session metrics', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/Session Metrics/i)).toBeInTheDocument();
    });

    it('should display VPIP metric', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/VPIP/i)).toBeInTheDocument();
    });

    it('should display PFR metric', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/PFR/i)).toBeInTheDocument();
    });

    it('should display 3-Bet percentage', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/3-Bet %/i)).toBeInTheDocument();
    });

    it('should show progress bars for metrics', () => {
      renderWithProviders(<Statistics />);
      const progressBars = screen.getAllByRole('progressbar');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  // 5. Position Stats tab
  describe('Position Stats Tab', () => {
    it('should render position analysis table', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Position Stats/i }));

      expect(screen.getByText(/Position Analysis/i)).toBeInTheDocument();
    });

    it('should display all positions', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Position Stats/i }));

      expect(screen.getByText(/BTN/i)).toBeInTheDocument();
      expect(screen.getByText(/CO/i)).toBeInTheDocument();
      expect(screen.getByText(/MP/i)).toBeInTheDocument();
      expect(screen.getByText(/UTG/i)).toBeInTheDocument();
      expect(screen.getByText(/SB/i)).toBeInTheDocument();
      expect(screen.getByText(/BB/i)).toBeInTheDocument();
    });

    it('should show position statistics columns', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Position Stats/i }));

      expect(screen.getByText(/Hands/i)).toBeInTheDocument();
      expect(screen.getByText(/Profit/i)).toBeInTheDocument();
      expect(screen.getByText(/VPIP %/i)).toBeInTheDocument();
      expect(screen.getByText(/PFR %/i)).toBeInTheDocument();
      expect(screen.getByText(/BB\/100/i)).toBeInTheDocument();
    });
  });

  // 6. Hand Strength tab
  describe('Hand Strength Tab', () => {
    it('should render hand strength performance chart', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Hand Strength/i }));

      expect(screen.getByText(/Hand Strength Performance/i)).toBeInTheDocument();
    });

    it('should render hand distribution chart', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Hand Strength/i }));

      expect(screen.getByText(/Hand Distribution/i)).toBeInTheDocument();
    });
  });

  // 7. Opponent Analysis tab
  describe('Opponent Analysis Tab', () => {
    it('should render opponent types chart', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Opponent Analysis/i }));

      expect(screen.getByText(/Opponent Types Encountered/i)).toBeInTheDocument();
    });

    it('should render profit vs opponent types chart', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Opponent Analysis/i }));

      expect(screen.getByText(/Profit vs Opponent Types/i)).toBeInTheDocument();
    });
  });

  // 8. Data display and formatting
  describe('Data Display', () => {
    it('should format currency values correctly', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/\$2,450/i)).toBeInTheDocument();
    });

    it('should format percentage values', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/12.5 BB\/100/i)).toBeInTheDocument();
    });

    it('should display trend indicators', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/\+15% vs last period/i)).toBeInTheDocument();
    });
  });

  // 9. Charts and visualizations
  describe('Charts', () => {
    it('should render all required charts', () => {
      renderWithProviders(<Statistics />);
      expect(screen.getByText(/Profit Trend/i)).toBeInTheDocument();
      expect(screen.getByText(/Session Metrics/i)).toBeInTheDocument();
    });
  });

  // 10. Accessibility
  describe('Accessibility', () => {
    it('should have accessible form controls', async () => {
      const { container } = renderWithProviders(<Statistics />);
      await checkAccessibility(container);
    });

    it('should have proper ARIA labels on tabs', () => {
      renderWithProviders(<Statistics />);

      const sessionTab = screen.getByRole('tab', { name: /Session Analysis/i });
      const positionTab = screen.getByRole('tab', { name: /Position Stats/i });

      expect(sessionTab).toHaveAttribute('aria-selected');
      expect(positionTab).toHaveAttribute('aria-selected');
    });

    it('should have accessible table headers', async () => {
      renderWithProviders(<Statistics />);

      await userEvent.click(screen.getByRole('tab', { name: /Position Stats/i }));

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });
  });
});
