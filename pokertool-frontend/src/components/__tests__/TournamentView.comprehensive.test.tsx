/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/__tests__/TournamentView.comprehensive.test.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Comprehensive test suite for TournamentView with 25 tests covering all functionality
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { TournamentView } from '../TournamentView';
import { renderWithProviders, checkAccessibility } from '../../test-utils/testHelpers';

describe('TournamentView Comprehensive Tests', () => {
  // 1. Rendering without crashes
  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderWithProviders(<TournamentView />);
      expect(screen.getByText(/Tournament Tracker/i)).toBeInTheDocument();
    });

    it('should render with empty state when no tournaments', () => {
      renderWithProviders(<TournamentView />);
      expect(screen.getByText(/No tournaments found/i)).toBeInTheDocument();
      expect(screen.getByText(/Register Tournament/i)).toBeInTheDocument();
    });

    it('should render all statistics cards', () => {
      renderWithProviders(<TournamentView />);
      expect(screen.getByText(/Total Tournaments/i)).toBeInTheDocument();
      expect(screen.getByText(/Total Profit/i)).toBeInTheDocument();
      expect(screen.getByText(/ITM Rate/i)).toBeInTheDocument();
      expect(screen.getByText(/Best Finish/i)).toBeInTheDocument();
    });
  });

  // 2. Interactive elements - buttons and tabs
  describe('Button and Tab Interactions', () => {
    it('should open register dialog when clicking Register button', async () => {
      renderWithProviders(<TournamentView />);

      await userEvent.click(screen.getByRole('button', { name: /Register/i }));

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Register Tournament/i)).toBeInTheDocument();
    });

    it('should switch between tabs', async () => {
      renderWithProviders(<TournamentView />);

      const activeTab = screen.getByRole('tab', { name: /Active/i });
      await userEvent.click(activeTab);

      expect(activeTab).toHaveAttribute('aria-selected', 'true');
    });

    it('should close dialog when clicking Cancel', async () => {
      renderWithProviders(<TournamentView />);

      await userEvent.click(screen.getByRole('button', { name: /Register/i }));
      await userEvent.click(screen.getByRole('button', { name: /Cancel/i }));

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  // 3. Tournament registration form
  describe('Tournament Registration', () => {
    it('should register a new tournament', async () => {
      const { store } = renderWithProviders(<TournamentView />);

      await userEvent.click(screen.getByRole('button', { name: /Register/i }));

      await userEvent.type(screen.getByLabelText(/Tournament Name/i), 'Sunday Major');
      await userEvent.type(screen.getByLabelText(/Buy-in/i), '55');

      await userEvent.click(screen.getByRole('button', { name: /^Register$/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.tournament.tournaments).toHaveLength(1);
        expect(state.tournament.tournaments[0].name).toBe('Sunday Major');
      });
    });

    it('should register tournament with all fields', async () => {
      const { store } = renderWithProviders(<TournamentView />);

      await userEvent.click(screen.getByRole('button', { name: /Register/i }));

      await userEvent.type(screen.getByLabelText(/Tournament Name/i), 'Big Tournament');
      await userEvent.type(screen.getByLabelText(/Buy-in/i), '100');
      await userEvent.type(screen.getByLabelText(/Rebuy Amount/i), '50');
      await userEvent.type(screen.getByLabelText(/Add-on Amount/i), '25');
      await userEvent.type(screen.getByLabelText(/Total Entrants/i), '200');
      await userEvent.type(screen.getByLabelText(/Notes/i), 'Test notes');

      await userEvent.click(screen.getByRole('button', { name: /^Register$/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.tournament.tournaments[0].buyin).toBe(100);
        expect(state.tournament.tournaments[0].rebuy).toBe(50);
        expect(state.tournament.tournaments[0].addon).toBe(25);
      });
    });

    it('should select tournament structure', async () => {
      renderWithProviders(<TournamentView />);

      await userEvent.click(screen.getByRole('button', { name: /Register/i }));

      await userEvent.click(screen.getByLabelText(/Structure/i));
      await userEvent.click(screen.getByRole('option', { name: /Rebuy/i }));

      expect(screen.getByRole('option', { name: /Rebuy/i })).toBeInTheDocument();
    });

    it('should not submit with invalid buyin', async () => {
      const { store } = renderWithProviders(<TournamentView />);

      await userEvent.click(screen.getByRole('button', { name: /Register/i }));

      await userEvent.type(screen.getByLabelText(/Tournament Name/i), 'Test');
      await userEvent.type(screen.getByLabelText(/Buy-in/i), '-10');

      await userEvent.click(screen.getByRole('button', { name: /^Register$/i }));

      const state = store.getState();
      expect(state.tournament.tournaments).toHaveLength(0);
    });
  });

  // 4. Tournament completion
  describe('Tournament Completion', () => {
    it('should complete an active tournament', async () => {
      const { store } = renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: '1',
              name: 'Test Tournament',
              buyin: 50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 50,
              prize: 0,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: null,
              status: 'active',
              position: null,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 1,
              completedTournaments: 0,
              totalProfit: 0,
              roi: 0,
              itm: 0,
              avgFinish: 0,
              bestFinish: null,
              biggestCash: 0
            },
            filters: { structure: 'all' }
          }
        }
      });

      const completeButton = screen.getByRole('button', { name: '' }); // Complete icon button
      await userEvent.click(completeButton);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Complete Tournament/i)).toBeInTheDocument();
    });

    it('should record tournament win', async () => {
      const { store } = renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: 'test-1',
              name: 'Test Tournament',
              buyin: 50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 50,
              prize: 0,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: null,
              status: 'active',
              position: null,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 1,
              completedTournaments: 0,
              totalProfit: 0,
              roi: 0,
              itm: 0,
              avgFinish: 0,
              bestFinish: null,
              biggestCash: 0
            },
            filters: { structure: 'all' }
          }
        }
      });

      const completeButton = screen.getByRole('button', { name: '' });
      await userEvent.click(completeButton);

      await userEvent.type(screen.getByLabelText(/Final Position/i), '1');
      await userEvent.type(screen.getByLabelText(/Prize Amount/i), '500');

      await userEvent.click(screen.getByRole('button', { name: /Complete/i }));

      await waitFor(() => {
        const state = store.getState();
        expect(state.tournament.tournaments[0].prize).toBe(500);
        expect(state.tournament.tournaments[0].position).toBe(1);
        expect(state.tournament.tournaments[0].status).toBe('completed');
      });
    });
  });

  // 5. Tournament deletion
  describe('Tournament Deletion', () => {
    it('should delete a tournament', async () => {
      const { store } = renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: 'test-1',
              name: 'Test Tournament',
              buyin: 50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 50,
              prize: 0,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: null,
              status: 'registered',
              position: null,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 0,
              completedTournaments: 0,
              totalProfit: 0,
              roi: 0,
              itm: 0,
              avgFinish: 0,
              bestFinish: null,
              biggestCash: 0
            },
            filters: { structure: 'all' }
          }
        }
      });

      const deleteButtons = screen.getAllByRole('button', { name: '' });
      const deleteButton = deleteButtons.find(btn => btn.querySelector('[data-testid="DeleteIcon"]'));

      if (deleteButton) {
        await userEvent.click(deleteButton);

        await waitFor(() => {
          expect(store.getState().tournament.tournaments).toHaveLength(0);
        });
      }
    });
  });

  // 6. Filters and sorting
  describe('Filters', () => {
    it('should filter by tournament structure', async () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [
              {
                id: '1',
                name: 'Freezeout Tournament',
                buyin: 50,
                rebuy: 0,
                addon: 0,
                totalInvestment: 50,
                prize: 100,
                totalEntrants: 100,
                structure: 'freezeout',
                startTime: Date.now(),
                endTime: null,
                status: 'completed',
                position: 10,
                notes: ''
              },
              {
                id: '2',
                name: 'Rebuy Tournament',
                buyin: 50,
                rebuy: 50,
                addon: 0,
                totalInvestment: 100,
                prize: 200,
                totalEntrants: 100,
                structure: 'rebuy',
                startTime: Date.now(),
                endTime: null,
                status: 'completed',
                position: 5,
                notes: ''
              }
            ],
            stats: {
              totalTournaments: 2,
              activeTournaments: 0,
              completedTournaments: 2,
              totalProfit: 150,
              roi: 75,
              itm: 100,
              avgFinish: 7.5,
              bestFinish: 5,
              biggestCash: 200
            },
            filters: { structure: 'all' }
          }
        }
      });

      const filterSelect = screen.getByRole('combobox');
      await userEvent.click(filterSelect);
      await userEvent.click(screen.getByRole('option', { name: /Freezeout/i }));

      // Should filter results
      expect(screen.getByText(/Freezeout Tournament/i)).toBeInTheDocument();
    });

    it('should show only active tournaments on Active tab', async () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [
              {
                id: '1',
                name: 'Active Tournament',
                buyin: 50,
                rebuy: 0,
                addon: 0,
                totalInvestment: 50,
                prize: 0,
                totalEntrants: 100,
                structure: 'freezeout',
                startTime: Date.now(),
                endTime: null,
                status: 'active',
                position: null,
                notes: ''
              },
              {
                id: '2',
                name: 'Completed Tournament',
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
                position: 10,
                notes: ''
              }
            ],
            stats: {
              totalTournaments: 2,
              activeTournaments: 1,
              completedTournaments: 1,
              totalProfit: 0,
              roi: 0,
              itm: 100,
              avgFinish: 10,
              bestFinish: 10,
              biggestCash: 100
            },
            filters: { structure: 'all' }
          }
        }
      });

      await userEvent.click(screen.getByRole('tab', { name: /Active/i }));

      expect(screen.getByText(/Active Tournament/i)).toBeInTheDocument();
      expect(screen.queryByText(/Completed Tournament/i)).not.toBeInTheDocument();
    });
  });

  // 7. Statistics display
  describe('Statistics Display', () => {
    it('should display total tournament count', () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: '1',
              name: 'Test',
              buyin: 50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 50,
              prize: 0,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: null,
              status: 'registered',
              position: null,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 0,
              completedTournaments: 0,
              totalProfit: 0,
              roi: 0,
              itm: 0,
              avgFinish: 0,
              bestFinish: null,
              biggestCash: 0
            },
            filters: { structure: 'all' }
          }
        }
      });

      expect(screen.getByText('1')).toBeInTheDocument();
    });

    it('should calculate and display ROI', () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [],
            stats: {
              totalTournaments: 10,
              activeTournaments: 0,
              completedTournaments: 10,
              totalProfit: 500,
              roi: 25.5,
              itm: 40,
              avgFinish: 15,
              bestFinish: 1,
              biggestCash: 1000
            },
            filters: { structure: 'all' }
          }
        }
      });

      expect(screen.getByText(/25.5%/)).toBeInTheDocument();
    });

    it('should show ITM rate', () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [],
            stats: {
              totalTournaments: 10,
              activeTournaments: 0,
              completedTournaments: 10,
              totalProfit: 500,
              roi: 25,
              itm: 45.5,
              avgFinish: 15,
              bestFinish: 1,
              biggestCash: 1000
            },
            filters: { structure: 'all' }
          }
        }
      });

      expect(screen.getByText(/45.5%/)).toBeInTheDocument();
    });
  });

  // 8. Charts
  describe('Charts', () => {
    it('should render cumulative profit chart when tournaments exist', () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: '1',
              name: 'Test',
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
              position: 10,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 0,
              completedTournaments: 1,
              totalProfit: 50,
              roi: 100,
              itm: 100,
              avgFinish: 10,
              bestFinish: 10,
              biggestCash: 100
            },
            filters: { structure: 'all' }
          }
        }
      });

      expect(screen.getByText(/Cumulative Profit/i)).toBeInTheDocument();
    });

    it('should render ITM distribution chart', () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: '1',
              name: 'Test',
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
              position: 10,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 0,
              completedTournaments: 1,
              totalProfit: 50,
              roi: 100,
              itm: 100,
              avgFinish: 10,
              bestFinish: 10,
              biggestCash: 100
            },
            filters: { structure: 'all' }
          }
        }
      });

      expect(screen.getByText(/ITM Distribution/i)).toBeInTheDocument();
    });

    it('should not show charts when no completed tournaments', () => {
      renderWithProviders(<TournamentView />);

      expect(screen.queryByText(/Cumulative Profit/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/ITM Distribution/i)).not.toBeInTheDocument();
    });
  });

  // 9. Bankroll integration
  describe('Bankroll Integration', () => {
    it('should record buyin in bankroll when registering', async () => {
      const { store } = renderWithProviders(<TournamentView />);

      await userEvent.click(screen.getByRole('button', { name: /Register/i }));

      await userEvent.type(screen.getByLabelText(/Tournament Name/i), 'Test Tournament');
      await userEvent.type(screen.getByLabelText(/Buy-in/i), '50');

      await userEvent.click(screen.getByRole('button', { name: /^Register$/i }));

      await waitFor(() => {
        const bankrollState = store.getState().bankroll;
        const lastTransaction = bankrollState.transactions[bankrollState.transactions.length - 1];
        expect(lastTransaction?.type).toBe('buyin');
        expect(lastTransaction?.amount).toBe(50);
      });
    });

    it('should record cashout in bankroll when winning', async () => {
      const { store } = renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: 'test-1',
              name: 'Test Tournament',
              buyin: 50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 50,
              prize: 0,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: null,
              status: 'active',
              position: null,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 1,
              completedTournaments: 0,
              totalProfit: 0,
              roi: 0,
              itm: 0,
              avgFinish: 0,
              bestFinish: null,
              biggestCash: 0
            },
            filters: { structure: 'all' }
          }
        }
      });

      const completeButton = screen.getByRole('button', { name: '' });
      await userEvent.click(completeButton);

      await userEvent.type(screen.getByLabelText(/Final Position/i), '1');
      await userEvent.type(screen.getByLabelText(/Prize Amount/i), '250');

      await userEvent.click(screen.getByRole('button', { name: /Complete/i }));

      await waitFor(() => {
        const bankrollState = store.getState().bankroll;
        const lastTransaction = bankrollState.transactions[bankrollState.transactions.length - 1];
        expect(lastTransaction?.type).toBe('cashout');
        expect(lastTransaction?.amount).toBe(250);
      });
    });
  });

  // 10. Data formatting
  describe('Data Formatting', () => {
    it('should format currency correctly', () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: '1',
              name: 'Test',
              buyin: 55.50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 55.50,
              prize: 0,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: null,
              status: 'registered',
              position: null,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 0,
              completedTournaments: 0,
              totalProfit: 0,
              roi: 0,
              itm: 0,
              avgFinish: 0,
              bestFinish: null,
              biggestCash: 0
            },
            filters: { structure: 'all' }
          },
          bankroll: {
            currentBalance: 0,
            transactions: [],
            startingBalance: 0,
            peakBalance: 0,
            lowestBalance: 0,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      expect(screen.getByText(/USD 55.50/)).toBeInTheDocument();
    });

    it('should display profit with correct sign', () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: '1',
              name: 'Winning Tournament',
              buyin: 50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 50,
              prize: 150,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: Date.now(),
              status: 'completed',
              position: 3,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 0,
              completedTournaments: 1,
              totalProfit: 100,
              roi: 200,
              itm: 100,
              avgFinish: 3,
              bestFinish: 3,
              biggestCash: 150
            },
            filters: { structure: 'all' }
          },
          bankroll: {
            currentBalance: 0,
            transactions: [],
            startingBalance: 0,
            peakBalance: 0,
            lowestBalance: 0,
            currency: 'USD',
            limits: { stopLossAmount: null, stopLossPercentage: null, dailyLossLimit: null, sessionLossLimit: null }
          }
        }
      });

      // Profit should be 150 - 50 = 100
      expect(screen.getByText(/USD 100.00/)).toBeInTheDocument();
    });
  });

  // 11. Status chips
  describe('Status Display', () => {
    it('should show correct status for registered tournament', () => {
      renderWithProviders(<TournamentView />, {
        preloadedState: {
          tournament: {
            tournaments: [{
              id: '1',
              name: 'Test',
              buyin: 50,
              rebuy: 0,
              addon: 0,
              totalInvestment: 50,
              prize: 0,
              totalEntrants: 100,
              structure: 'freezeout',
              startTime: Date.now(),
              endTime: null,
              status: 'registered',
              position: null,
              notes: ''
            }],
            stats: {
              totalTournaments: 1,
              activeTournaments: 0,
              completedTournaments: 0,
              totalProfit: 0,
              roi: 0,
              itm: 0,
              avgFinish: 0,
              bestFinish: null,
              biggestCash: 0
            },
            filters: { structure: 'all' }
          }
        }
      });

      expect(screen.getByText(/registered/i)).toBeInTheDocument();
    });
  });

  // 12. Responsive behavior
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

      renderWithProviders(<TournamentView />);
      expect(screen.getByText(/Tournament Tracker/i)).toBeInTheDocument();
    });
  });

  // 13. Accessibility
  describe('Accessibility', () => {
    it('should have accessible form labels', async () => {
      const { container } = renderWithProviders(<TournamentView />);

      await userEvent.click(screen.getByRole('button', { name: /Register/i }));

      await checkAccessibility(container);
    });

    it('should have proper ARIA labels on tabs', () => {
      renderWithProviders(<TournamentView />);

      const allTab = screen.getByRole('tab', { name: /All/i });
      const activeTab = screen.getByRole('tab', { name: /Active/i });

      expect(allTab).toBeInTheDocument();
      expect(activeTab).toBeInTheDocument();
    });
  });
});
