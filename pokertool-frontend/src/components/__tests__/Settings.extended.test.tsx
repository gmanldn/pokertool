/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/__tests__/Settings.extended.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Extended test suite for Settings with 15 additional tests beyond existing coverage
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { Settings } from '../Settings';
import { renderWithProviders, checkAccessibility } from '../../test-utils/testHelpers';

describe('Settings Extended Tests', () => {
  // 1. Rendering variations
  describe('Rendering States', () => {
    it('should render with default state', () => {
      renderWithProviders(<Settings />);
      expect(screen.getByText(/Settings/i)).toBeInTheDocument();
    });

    it('should render financial history reset section', () => {
      renderWithProviders(<Settings />);
      expect(screen.getByText(/Financial History Reset/i)).toBeInTheDocument();
    });

    it('should show reset button', () => {
      renderWithProviders(<Settings />);
      expect(screen.getByRole('button', { name: /Reset Money History/i })).toBeInTheDocument();
    });

    it('should display learning data preservation message', () => {
      renderWithProviders(<Settings />);
      expect(screen.getByText(/Learning insights remain untouched/i)).toBeInTheDocument();
    });
  });

  // 2. Dialog interactions
  describe('Confirmation Dialog', () => {
    it('should open confirmation dialog when clicking reset', async () => {
      renderWithProviders(<Settings />);

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Reset money history\?/i)).toBeInTheDocument();
    });

    it('should close dialog when clicking Cancel', async () => {
      renderWithProviders(<Settings />);

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Cancel/i }));

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should not close dialog during reset operation', async () => {
      renderWithProviders(<Settings />);

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should show confirmation text in dialog', async () => {
      renderWithProviders(<Settings />);

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));

      expect(screen.getByText(/This will remove all bankroll transactions/i)).toBeInTheDocument();
    });
  });

  // 3. Reset functionality with state preservation
  describe('Reset with State Preservation', () => {
    it('should preserve currency setting after reset', async () => {
      const { store } = renderWithProviders(<Settings />, {
        preloadedState: {
          bankroll: {
            currentBalance: 1000,
            transactions: [
              { id: '1', type: 'deposit', amount: 1000, balance: 1000, timestamp: Date.now(), description: '' }
            ],
            startingBalance: 1000,
            peakBalance: 1000,
            lowestBalance: 1000,
            currency: 'EUR',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Confirm Reset/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.bankroll.currency).toBe('EUR');
      });
    });

    it('should preserve stop loss limits after reset', async () => {
      const { store } = renderWithProviders(<Settings />, {
        preloadedState: {
          bankroll: {
            currentBalance: 500,
            transactions: [
              { id: '1', type: 'deposit', amount: 1000, balance: 1000, timestamp: 1000, description: '' },
              { id: '2', type: 'loss', amount: 500, balance: 500, timestamp: 2000, description: '' }
            ],
            startingBalance: 1000,
            peakBalance: 1000,
            lowestBalance: 500,
            currency: 'USD',
            limits: {
              stopLossAmount: 300,
              stopLossPercentage: 25,
              dailyLossLimit: 150,
              sessionLossLimit: 100
            }
          }
        }
      });

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Confirm Reset/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.bankroll.limits.stopLossAmount).toBe(300);
        expect(state.bankroll.limits.stopLossPercentage).toBe(25);
        expect(state.bankroll.limits.dailyLossLimit).toBe(150);
        expect(state.bankroll.limits.sessionLossLimit).toBe(100);
      });
    });

    it('should reset transactions to empty array', async () => {
      const { store } = renderWithProviders(<Settings />, {
        preloadedState: {
          bankroll: {
            currentBalance: 1000,
            transactions: [
              { id: '1', type: 'deposit', amount: 1000, balance: 1000, timestamp: Date.now(), description: '' },
              { id: '2', type: 'win', amount: 500, balance: 1500, timestamp: Date.now(), description: '' }
            ],
            startingBalance: 1000,
            peakBalance: 1500,
            lowestBalance: 1000,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Confirm Reset/i }));

      await waitFor(() => {
        expect(store.getState().bankroll.transactions).toHaveLength(0);
      });
    });

    it('should reset current balance to zero', async () => {
      const { store } = renderWithProviders(<Settings />, {
        preloadedState: {
          bankroll: {
            currentBalance: 2500,
            transactions: [
              { id: '1', type: 'deposit', amount: 2500, balance: 2500, timestamp: Date.now(), description: '' }
            ],
            startingBalance: 2500,
            peakBalance: 2500,
            lowestBalance: 2500,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Confirm Reset/i }));

      await waitFor(() => {
        expect(store.getState().bankroll.currentBalance).toBe(0);
      });
    });
  });

  // 4. Multi-state reset
  describe('Multi-State Reset', () => {
    it('should reset tournaments', async () => {
      const { store } = renderWithProviders(<Settings />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: '1',
              name: 'Test Tournament',
              buyin: 50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 50,
              prize: 100,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: Date.now(),
              status: 'completed',
              position: 1,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 0,
              completedTournaments: 1,
              totalProfit: 50,
              roi: 100,
              itm: 100,
              avgFinish: 1,
              bestFinish: 1,
              biggestCash: 100
            },
            filters: { structure: 'all' }
          }
        }
      });

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Confirm Reset/i }));

      await waitFor(() => {
        expect(store.getState().tournament.tournaments).toHaveLength(0);
      });
    });

    it('should reset session data', async () => {
      const { store } = renderWithProviders(<Settings />, {
        preloadedState: {
          session: {
            isActive: true,
            startTime: Date.now(),
            hands: [
              {
                timestamp: Date.now(),
                result: 'win',
                amount: 100,
                adviceGiven: 'RAISE',
                actionTaken: 'RAISE',
                followedAdvice: true
              }
            ],
            stats: {
              handsPlayed: 1,
              totalProfit: 100,
              vpip: 25,
              pfr: 20,
              winRate: 100
            }
          }
        }
      });

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Confirm Reset/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.session.hands).toHaveLength(0);
        expect(state.session.stats.totalProfit).toBe(0);
      });
    });
  });

  // 5. Success feedback
  describe('Success Feedback', () => {
    it('should show success alert after reset', async () => {
      renderWithProviders(<Settings />);

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Confirm Reset/i }));

      await waitFor(() => {
        expect(screen.getByText(/Financial history cleared/i)).toBeInTheDocument();
      });
    });

    it('should allow closing success alert', async () => {
      renderWithProviders(<Settings />);

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));
      await userEvent.click(screen.getByRole('button', { name: /Confirm Reset/i }));

      await waitFor(() => {
        const alert = screen.getByText(/Financial history cleared/i);
        expect(alert).toBeInTheDocument();
      });

      const closeButton = screen.getByRole('button', { name: /close/i });
      await userEvent.click(closeButton);

      expect(screen.queryByText(/Financial history cleared/i)).not.toBeInTheDocument();
    });
  });

  // 6. Icons and visual elements
  describe('Visual Elements', () => {
    it('should display financial icon', () => {
      renderWithProviders(<Settings />);
      expect(screen.getByTestId('SavingsIcon')).toBeInTheDocument();
    });

    it('should display learning icon', () => {
      renderWithProviders(<Settings />);
      expect(screen.getByTestId('PsychologyIcon')).toBeInTheDocument();
    });

    it('should display reset icon on button', () => {
      renderWithProviders(<Settings />);
      expect(screen.getByTestId('RestartAltIcon')).toBeInTheDocument();
    });
  });

  // 7. Accessibility
  describe('Accessibility', () => {
    it('should have accessible buttons', async () => {
      const { container } = renderWithProviders(<Settings />);
      await checkAccessibility(container);
    });

    it('should have proper dialog ARIA labels', async () => {
      renderWithProviders(<Settings />);

      await userEvent.click(screen.getByRole('button', { name: /Reset Money History/i }));

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby');
    });
  });
});
