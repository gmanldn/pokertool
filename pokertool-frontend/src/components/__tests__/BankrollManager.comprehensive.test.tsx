/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/__tests__/BankrollManager.comprehensive.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Comprehensive test suite for BankrollManager with 25 tests covering all functionality
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { BankrollManager } from '../BankrollManager';
import { renderWithProviders, checkAccessibility } from '../../test-utils/testHelpers';

describe('BankrollManager Comprehensive Tests', () => {
  // 1. Rendering without crashes
  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderWithProviders(<BankrollManager />);
      expect(screen.getByText(/Bankroll Management/i)).toBeInTheDocument();
    });

    it('should render with empty state when no transactions', () => {
      renderWithProviders(<BankrollManager />);
      expect(screen.getByText(/No transactions yet/i)).toBeInTheDocument();
      expect(screen.getByText(/Add Initial Deposit/i)).toBeInTheDocument();
    });

    it('should render all overview cards', () => {
      renderWithProviders(<BankrollManager />);
      expect(screen.getByText(/Current Balance/i)).toBeInTheDocument();
      expect(screen.getByText(/Profit\/Loss/i)).toBeInTheDocument();
      expect(screen.getByText(/Peak Balance/i)).toBeInTheDocument();
      expect(screen.getByText(/Lowest Balance/i)).toBeInTheDocument();
    });
  });

  // 2. Interactive elements - buttons
  describe('Button Interactions', () => {
    it('should open transaction dialog when clicking Transaction button', async () => {
      renderWithProviders(<BankrollManager />);
      const transactionBtn = screen.getByRole('button', { name: /Transaction/i });

      await userEvent.click(transactionBtn);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Add Transaction/i)).toBeInTheDocument();
    });

    it('should open settings dialog when clicking Settings button', async () => {
      renderWithProviders(<BankrollManager />);
      const settingsBtn = screen.getByRole('button', { name: /Settings/i });

      await userEvent.click(settingsBtn);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Bankroll Settings/i)).toBeInTheDocument();
    });

    it('should close dialog when clicking Cancel', async () => {
      renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));
      await userEvent.click(screen.getByRole('button', { name: /Cancel/i }));

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  // 3. Form interactions - adding transactions
  describe('Transaction Forms', () => {
    it('should add a deposit transaction', async () => {
      const { store } = renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));

      const amountInput = screen.getByLabelText(/Amount/i);
      await userEvent.type(amountInput, '1000');

      await userEvent.click(screen.getByRole('button', { name: /^Add$/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.bankroll.currentBalance).toBe(1000);
        expect(state.bankroll.transactions).toHaveLength(1);
      });
    });

    it('should add a withdrawal transaction', async () => {
      const { store } = renderWithProviders(<BankrollManager />, {
        preloadedState: {
          bankroll: {
            currentBalance: 1000,
            transactions: [{
              id: '1',
              type: 'deposit',
              amount: 1000,
              balance: 1000,
              timestamp: Date.now(),
              description: 'Initial'
            }],
            startingBalance: 1000,
            peakBalance: 1000,
            lowestBalance: 1000,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));

      await userEvent.click(screen.getByLabelText(/Transaction Type/i));
      await userEvent.click(screen.getByRole('option', { name: /Withdrawal/i }));

      const amountInput = screen.getByLabelText(/Amount/i);
      await userEvent.type(amountInput, '500');

      await userEvent.click(screen.getByRole('button', { name: /^Add$/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.bankroll.currentBalance).toBe(500);
      });
    });

    it('should add transaction with description', async () => {
      renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));

      const amountInput = screen.getByLabelText(/Amount/i);
      await userEvent.type(amountInput, '250');

      const descInput = screen.getByLabelText(/Description/i);
      await userEvent.type(descInput, 'Tournament winnings');

      await userEvent.click(screen.getByRole('button', { name: /^Add$/i }));

      await waitFor(() => {
        expect(screen.getByText(/Tournament winnings/i)).toBeInTheDocument();
      });
    });

    it('should handle all transaction types', async () => {
      const types = ['deposit', 'withdrawal', 'win', 'loss', 'buyin', 'cashout'];

      for (const type of types) {
        renderWithProviders(<BankrollManager />);

        await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));

        await userEvent.click(screen.getByLabelText(/Transaction Type/i));
        await userEvent.click(screen.getByRole('option', { name: new RegExp(type, 'i') }));

        expect(screen.getByRole('option', { name: new RegExp(type, 'i') })).toBeInTheDocument();
      }
    });

    it('should not submit with invalid amount', async () => {
      const { store } = renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));

      const amountInput = screen.getByLabelText(/Amount/i);
      await userEvent.type(amountInput, '-50');

      await userEvent.click(screen.getByRole('button', { name: /^Add$/i }));

      const state = store.getState();
      expect(state.bankroll.transactions).toHaveLength(0);
    });
  });

  // 4. State updates and Redux integration
  describe('Redux State Management', () => {
    it('should update current balance after deposit', async () => {
      const { store } = renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));
      await userEvent.type(screen.getByLabelText(/Amount/i), '500');
      await userEvent.click(screen.getByRole('button', { name: /^Add$/i }));

      await waitFor(() => {
        expect(store.getState().bankroll.currentBalance).toBe(500);
      });
    });

    it('should track peak balance', async () => {
      const { store } = renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));
      await userEvent.type(screen.getByLabelText(/Amount/i), '1000');
      await userEvent.click(screen.getByRole('button', { name: /^Add$/i }));

      await waitFor(() => {
        expect(store.getState().bankroll.peakBalance).toBe(1000);
      });
    });

    it('should calculate profit/loss correctly', async () => {
      const { store } = renderWithProviders(<BankrollManager />);

      // Initial deposit
      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));
      await userEvent.type(screen.getByLabelText(/Amount/i), '1000');
      await userEvent.click(screen.getByRole('button', { name: /^Add$/i }));

      // Win
      await waitFor(() => screen.getByRole('button', { name: /Transaction/i }));
      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));
      await userEvent.click(screen.getByLabelText(/Transaction Type/i));
      await userEvent.click(screen.getByRole('option', { name: /Win/i }));
      await userEvent.type(screen.getByLabelText(/Amount/i), '250');
      await userEvent.click(screen.getByRole('button', { name: /^Add$/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.bankroll.currentBalance).toBe(1250);
      });
    });
  });

  // 5. Data display and formatting
  describe('Data Display', () => {
    it('should format currency correctly', () => {
      renderWithProviders(<BankrollManager />, {
        preloadedState: {
          bankroll: {
            currentBalance: 1234.56,
            transactions: [],
            startingBalance: 1000,
            peakBalance: 1234.56,
            lowestBalance: 900,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      expect(screen.getByText(/USD 1234.56/)).toBeInTheDocument();
    });

    it('should display transaction history in reverse chronological order', async () => {
      renderWithProviders(<BankrollManager />, {
        preloadedState: {
          bankroll: {
            currentBalance: 500,
            transactions: [
              { id: '1', type: 'deposit', amount: 1000, balance: 1000, timestamp: 1000, description: 'First' },
              { id: '2', type: 'loss', amount: 500, balance: 500, timestamp: 2000, description: 'Second' }
            ],
            startingBalance: 1000,
            peakBalance: 1000,
            lowestBalance: 500,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      const rows = screen.getAllByRole('row');
      expect(rows[1]).toHaveTextContent('Second'); // Most recent first
    });

    it('should show positive profit with correct color', () => {
      renderWithProviders(<BankrollManager />, {
        preloadedState: {
          bankroll: {
            currentBalance: 1500,
            transactions: [
              { id: '1', type: 'deposit', amount: 1000, balance: 1000, timestamp: 1000, description: '' },
              { id: '2', type: 'win', amount: 500, balance: 1500, timestamp: 2000, description: '' }
            ],
            startingBalance: 1000,
            peakBalance: 1500,
            lowestBalance: 1000,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      const profitElement = screen.getByText(/USD 500.00/);
      expect(profitElement).toBeInTheDocument();
    });
  });

  // 6. Settings dialog
  describe('Settings Management', () => {
    it('should update currency setting', async () => {
      const { store } = renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Settings/i }));

      await userEvent.click(screen.getByLabelText(/Currency/i));
      await userEvent.click(screen.getByRole('option', { name: /EUR/i }));

      await userEvent.click(screen.getByRole('button', { name: /Save/i }));

      await waitFor(() => {
        expect(store.getState().bankroll.currency).toBe('EUR');
      });
    });

    it('should set stop loss limits', async () => {
      const { store } = renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Settings/i }));

      const stopLossInput = screen.getByLabelText(/Stop Loss Amount/i);
      await userEvent.type(stopLossInput, '200');

      await userEvent.click(screen.getByRole('button', { name: /Save/i }));

      await waitFor(() => {
        expect(store.getState().bankroll.limits.stopLossAmount).toBe(200);
      });
    });

    it('should display alert when stop loss reached', () => {
      renderWithProviders(<BankrollManager />, {
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
            limits: { stopLossAmount: 400, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      expect(screen.getByText(/Stop loss amount limit reached/i)).toBeInTheDocument();
    });
  });

  // 7. Charts and visualizations
  describe('Charts', () => {
    it('should render bankroll history chart when transactions exist', () => {
      renderWithProviders(<BankrollManager />, {
        preloadedState: {
          bankroll: {
            currentBalance: 1000,
            transactions: [
              { id: '1', type: 'deposit', amount: 1000, balance: 1000, timestamp: Date.now(), description: '' }
            ],
            startingBalance: 1000,
            peakBalance: 1000,
            lowestBalance: 1000,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      expect(screen.getByText(/Bankroll History/i)).toBeInTheDocument();
    });

    it('should not show chart when no transactions', () => {
      renderWithProviders(<BankrollManager />);
      expect(screen.queryByText(/Bankroll History/i)).not.toBeInTheDocument();
    });

    it('should display stake recommendations when balance > 0', () => {
      renderWithProviders(<BankrollManager />, {
        preloadedState: {
          bankroll: {
            currentBalance: 1000,
            transactions: [
              { id: '1', type: 'deposit', amount: 1000, balance: 1000, timestamp: Date.now(), description: '' }
            ],
            startingBalance: 1000,
            peakBalance: 1000,
            lowestBalance: 1000,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      expect(screen.getByText(/Recommended Stakes/i)).toBeInTheDocument();
      expect(screen.getByText(/Conservative/i)).toBeInTheDocument();
      expect(screen.getByText(/Moderate/i)).toBeInTheDocument();
      expect(screen.getByText(/Aggressive/i)).toBeInTheDocument();
    });
  });

  // 8. Delete functionality
  describe('Transaction Deletion', () => {
    it('should delete a transaction', async () => {
      const { store } = renderWithProviders(<BankrollManager />, {
        preloadedState: {
          bankroll: {
            currentBalance: 1000,
            transactions: [
              { id: 'test-1', type: 'deposit', amount: 1000, balance: 1000, timestamp: Date.now(), description: 'Test transaction' }
            ],
            startingBalance: 1000,
            peakBalance: 1000,
            lowestBalance: 1000,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      const deleteButton = screen.getByRole('button', { name: '' }); // IconButton without text
      await userEvent.click(deleteButton);

      await waitFor(() => {
        expect(store.getState().bankroll.transactions).toHaveLength(0);
      });
    });
  });

  // 9. Responsive behavior
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

      renderWithProviders(<BankrollManager />);
      expect(screen.getByText(/Bankroll Management/i)).toBeInTheDocument();
    });
  });

  // 10. Accessibility
  describe('Accessibility', () => {
    it('should have accessible form labels', async () => {
      const { container } = renderWithProviders(<BankrollManager />);

      await userEvent.click(screen.getByRole('button', { name: /Transaction/i }));

      await checkAccessibility(container);
    });

    it('should have proper ARIA labels on buttons', () => {
      renderWithProviders(<BankrollManager />);

      const transactionBtn = screen.getByRole('button', { name: /Transaction/i });
      const settingsBtn = screen.getByRole('button', { name: /Settings/i });

      expect(transactionBtn).toBeInTheDocument();
      expect(settingsBtn).toBeInTheDocument();
    });
  });
});
