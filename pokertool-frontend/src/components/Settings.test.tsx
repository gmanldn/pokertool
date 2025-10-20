/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/Settings.test.tsx
version: v1.0.0
last_commit: '2025-10-22T12:15:00+01:00'
fixes:
- date: '2025-10-22'
  summary: Added regression coverage for financial reset workflow
---
POKERTOOL-HEADER-END */

import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Settings } from './Settings';
import bankrollReducer, {
  initializeBankroll,
  recordWin,
  updateLimits,
} from '../store/slices/bankrollSlice';
import tournamentReducer, {
  registerTournament,
  completeTournament,
} from '../store/slices/tournamentSlice';
import sessionReducer, {
  startSession,
  addHandResult,
} from '../store/slices/sessionSlice';
import gameReducer from '../store/slices/gameSlice';
import adviceReducer from '../store/slices/adviceSlice';
import settingsReducer from '../store/slices/settingsSlice';

describe('Settings financial reset', () => {
  const renderWithStore = () => {
    const store = configureStore({
      reducer: {
        game: gameReducer,
        advice: adviceReducer,
        session: sessionReducer,
        settings: settingsReducer,
        bankroll: bankrollReducer,
        tournament: tournamentReducer,
      },
    });

    // Seed bankroll with non-zero data and custom limits/currency
    store.dispatch(initializeBankroll({ amount: 250, currency: 'EUR' }));
    store.dispatch(recordWin({ amount: 50, description: 'Cash game win' }));
    store.dispatch(
      updateLimits({
        stopLossAmount: 100,
        stopLossPercentage: 25,
      })
    );

    // Seed tournament history
    store.dispatch(
      registerTournament({
        name: 'Sunday Major',
        buyin: 55,
        rebuy: 0,
        addon: 0,
        totalEntrants: 120,
        structure: 'freezeout',
        startTime: Date.now(),
        position: null,
        notes: '',
      })
    );
    const stateAfterRegistration = store.getState().tournament.tournaments[0];
    store.dispatch(
      completeTournament({
        id: stateAfterRegistration.id,
        position: 10,
        prize: 250,
        totalEntrants: 120,
      })
    );

    // Seed session profit
    store.dispatch(startSession());
    store.dispatch(
      addHandResult({
        timestamp: Date.now(),
        result: 'win',
        amount: 30,
        adviceGiven: 'RAISE',
        actionTaken: 'CALL',
        followedAdvice: false,
      })
    );

    const utils = render(
      <Provider store={store}>
        <Settings />
      </Provider>
    );

    return { ...utils, store };
  };

  it('resets bankroll, tournament, and session financial data while preserving learning settings', async () => {
    const { store } = renderWithStore();

    fireEvent.click(screen.getByText('Reset Money History'));
    fireEvent.click(screen.getByText('Confirm Reset'));

    await waitFor(() =>
      expect(
        screen.getByText(/Financial history cleared/i)
      ).toBeInTheDocument()
    );

    const state = store.getState();
    expect(state.bankroll.transactions).toHaveLength(0);
    expect(state.bankroll.currentBalance).toBe(0);
    expect(state.bankroll.currency).toBe('EUR');
    expect(state.bankroll.limits.stopLossAmount).toBe(100);
    expect(state.bankroll.limits.stopLossPercentage).toBe(25);

    expect(state.tournament.tournaments).toHaveLength(0);
    expect(state.tournament.stats.totalProfit).toBe(0);

    expect(state.session.hands).toHaveLength(0);
    expect(state.session.stats.totalProfit).toBe(0);
    expect(state.session.isActive).toBe(false);
  });
});
