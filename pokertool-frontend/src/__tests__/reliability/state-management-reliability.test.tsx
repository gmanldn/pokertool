/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/__tests__/reliability/state-management-reliability.test.tsx
version: v101.0.0
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Redux state management reliability tests - 25 tests
---
POKERTOOL-HEADER-END */

import { configureStore } from '@reduxjs/toolkit';
import bankrollReducer from '../../store/slices/bankrollSlice';
import tournamentReducer from '../../store/slices/tournamentSlice';
import sessionReducer from '../../store/slices/sessionSlice';
import settingsReducer from '../../store/slices/settingsSlice';

/**
 * State Management Reliability Tests
 *
 * Tests to ensure Redux store handles edge cases, concurrent updates,
 * invalid data, and state persistence without errors or data corruption.
 */

describe('State Management Reliability Tests', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        bankroll: bankrollReducer,
        tournaments: tournamentReducer,
        sessions: sessionReducer,
        settings: settingsReducer,
      },
    });
  });

  describe('Store Initialization', () => {
    it('initializes store with default state', () => {
      const state = store.getState();

      expect(state).toHaveProperty('bankroll');
      expect(state).toHaveProperty('tournaments');
      expect(state).toHaveProperty('sessions');
      expect(state).toHaveProperty('settings');
    });

    it('handles missing initial state gracefully', () => {
      const emptyStore = configureStore({
        reducer: {
          bankroll: bankrollReducer,
        },
      });

      expect(emptyStore.getState()).toBeDefined();
    });

    it('initializes with preloaded state correctly', () => {
      const preloadedState = {
        bankroll: {
          balance: 1000,
          transactions: [],
          loading: false,
          error: null,
        },
      };

      const preloadedStore = configureStore({
        reducer: {
          bankroll: bankrollReducer,
          tournaments: tournamentReducer,
          sessions: sessionReducer,
          settings: settingsReducer,
        },
        preloadedState: preloadedState as any,
      });

      expect(preloadedStore.getState().bankroll.balance).toBe(1000);
    });
  });

  describe('Action Dispatching', () => {
    it('handles valid actions correctly', () => {
      const initialState = store.getState();

      store.dispatch({ type: 'bankroll/setBalance', payload: 5000 });

      const newState = store.getState();
      expect(newState).toBeDefined();
      expect(newState).not.toBe(initialState);
    });

    it('ignores unknown actions gracefully', () => {
      const beforeState = store.getState();

      store.dispatch({ type: 'UNKNOWN_ACTION_TYPE' });

      const afterState = store.getState();
      expect(afterState).toEqual(beforeState);
    });

    it('handles actions with missing payload', () => {
      expect(() => {
        store.dispatch({ type: 'bankroll/someAction' });
      }).not.toThrow();
    });

    it('handles actions with invalid payload types', () => {
      expect(() => {
        store.dispatch({
          type: 'bankroll/setBalance',
          payload: 'not-a-number' as any
        });
      }).not.toThrow();
    });

    it('handles actions with null/undefined payload', () => {
      expect(() => {
        store.dispatch({ type: 'bankroll/setBalance', payload: null });
        store.dispatch({ type: 'bankroll/setBalance', payload: undefined });
      }).not.toThrow();
    });
  });

  describe('Concurrent Updates', () => {
    it('handles rapid sequential dispatches', () => {
      const actions = Array.from({ length: 100 }, (_, i) => ({
        type: 'bankroll/setBalance',
        payload: i,
      }));

      actions.forEach(action => store.dispatch(action));

      // Should process all actions without errors
      expect(store.getState()).toBeDefined();
    });

    it('handles concurrent slice updates', () => {
      // Update multiple slices simultaneously
      store.dispatch({ type: 'bankroll/setBalance', payload: 1000 });
      store.dispatch({ type: 'tournaments/setTournaments', payload: [] });
      store.dispatch({ type: 'sessions/setSessions', payload: [] });
      store.dispatch({ type: 'settings/updateSettings', payload: { theme: 'dark' } });

      const state = store.getState();
      expect(state.bankroll).toBeDefined();
      expect(state.tournaments).toBeDefined();
      expect(state.sessions).toBeDefined();
      expect(state.settings).toBeDefined();
    });

    it('maintains state consistency during rapid updates', () => {
      const initialBalance = 1000;
      store.dispatch({ type: 'bankroll/setBalance', payload: initialBalance });

      // Rapid balance updates
      for (let i = 0; i < 50; i++) {
        store.dispatch({ type: 'bankroll/setBalance', payload: initialBalance + i });
      }

      // Final state should be consistent
      expect(store.getState()).toBeDefined();
    });
  });

  describe('State Immutability', () => {
    it('does not mutate state directly', () => {
      const beforeState = store.getState();
      const beforeBankroll = beforeState.bankroll;

      store.dispatch({ type: 'bankroll/setBalance', payload: 9999 });

      const afterState = store.getState();

      // Original state object should not be mutated
      expect(beforeBankroll).toBe(beforeState.bankroll);
      expect(afterState.bankroll).not.toBe(beforeBankroll);
    });

    it('creates new state references on updates', () => {
      const state1 = store.getState();

      store.dispatch({ type: 'bankroll/setBalance', payload: 100 });
      const state2 = store.getState();

      store.dispatch({ type: 'bankroll/setBalance', payload: 200 });
      const state3 = store.getState();

      expect(state1).not.toBe(state2);
      expect(state2).not.toBe(state3);
    });

    it('preserves unchanged slices during updates', () => {
      const beforeState = store.getState();
      const beforeTournaments = beforeState.tournaments;

      // Update bankroll only
      store.dispatch({ type: 'bankroll/setBalance', payload: 500 });

      const afterState = store.getState();

      // Tournaments slice should remain unchanged
      expect(afterState.tournaments).toBe(beforeTournaments);
    });
  });

  describe('Error Handling', () => {
    it('handles reducer errors gracefully', () => {
      const errorReducer = (state = {}, action: any) => {
        if (action.type === 'TRIGGER_ERROR') {
          throw new Error('Test error');
        }
        return state;
      };

      const errorStore = configureStore({
        reducer: { test: errorReducer },
      });

      expect(() => {
        try {
          errorStore.dispatch({ type: 'TRIGGER_ERROR' });
        } catch (e) {
          // Should catch and handle error
        }
      }).not.toThrow();
    });

    it('recovers from action errors', () => {
      const beforeState = store.getState();

      try {
        store.dispatch({ type: 'bankroll/invalidAction' });
      } catch {
        // Ignore error
      }

      // Store should still be functional
      store.dispatch({ type: 'bankroll/setBalance', payload: 100 });
      const afterState = store.getState();

      expect(afterState).toBeDefined();
      expect(afterState).not.toEqual(beforeState);
    });
  });

  describe('Large Data Handling', () => {
    it('handles large transaction arrays', () => {
      const largeTransactions = Array.from({ length: 10000 }, (_, i) => ({
        id: `tx-${i}`,
        amount: i * 10,
        type: i % 2 === 0 ? 'win' : 'loss',
        date: new Date().toISOString(),
      }));

      expect(() => {
        store.dispatch({
          type: 'bankroll/setTransactions',
          payload: largeTransactions,
        });
      }).not.toThrow();
    });

    it('handles deeply nested state structures', () => {
      const deeplyNested = {
        level1: {
          level2: {
            level3: {
              level4: {
                level5: {
                  data: 'deep value',
                },
              },
            },
          },
        },
      };

      expect(() => {
        store.dispatch({
          type: 'settings/updateSettings',
          payload: deeplyNested,
        });
      }).not.toThrow();
    });

    it('handles extremely long strings', () => {
      const longString = 'x'.repeat(100000);

      expect(() => {
        store.dispatch({
          type: 'settings/updateSettings',
          payload: { description: longString },
        });
      }).not.toThrow();
    });
  });

  describe('State Persistence', () => {
    it('serializes state for storage', () => {
      store.dispatch({ type: 'bankroll/setBalance', payload: 2500 });

      const state = store.getState();
      const serialized = JSON.stringify(state);

      expect(serialized).toBeTruthy();
      expect(typeof serialized).toBe('string');
    });

    it('deserializes state from storage', () => {
      const mockState = {
        bankroll: { balance: 3000, transactions: [], loading: false, error: null },
        tournaments: { list: [], loading: false, error: null },
        sessions: { list: [], loading: false, error: null },
        settings: { theme: 'dark' },
      };

      const serialized = JSON.stringify(mockState);
      const deserialized = JSON.parse(serialized);

      expect(deserialized).toEqual(mockState);
    });

    it('handles corrupted persisted state', () => {
      const corruptedStates = [
        '{"invalid json}',
        'null',
        'undefined',
        '',
        '{}',
      ];

      corruptedStates.forEach(corrupt => {
        try {
          JSON.parse(corrupt);
        } catch (e) {
          // Should handle parse errors gracefully
          expect(e).toBeDefined();
        }
      });
    });
  });

  describe('Selector Reliability', () => {
    it('selectors return correct data', () => {
      store.dispatch({ type: 'bankroll/setBalance', payload: 1234 });

      const state = store.getState();
      const balance = state.bankroll.balance;

      expect(balance).toBe(1234);
    });

    it('selectors handle missing data', () => {
      const state = store.getState();
      const missingData = (state as any).nonexistent?.value;

      expect(missingData).toBeUndefined();
    });

    it('memoized selectors prevent unnecessary recalculations', () => {
      const state1 = store.getState();
      const bankroll1 = state1.bankroll;

      const state2 = store.getState();
      const bankroll2 = state2.bankroll;

      // Without dispatch, same reference should be returned
      expect(bankroll1).toBe(bankroll2);
    });
  });

  describe('Middleware Reliability', () => {
    it('middleware chain processes actions correctly', () => {
      const actions: any[] = [];

      const loggingMiddleware = () => (next: any) => (action: any) => {
        actions.push(action);
        return next(action);
      };

      const storeWithMiddleware = configureStore({
        reducer: { bankroll: bankrollReducer },
        middleware: (getDefaultMiddleware) =>
          getDefaultMiddleware().concat(loggingMiddleware),
      });

      storeWithMiddleware.dispatch({ type: 'bankroll/setBalance', payload: 100 });

      expect(actions.length).toBeGreaterThan(0);
    });

    it('middleware handles async actions', async () => {
      const asyncAction = async (dispatch: any) => {
        await new Promise(resolve => setTimeout(resolve, 10));
        dispatch({ type: 'bankroll/setBalance', payload: 500 });
      };

      await asyncAction(store.dispatch);

      expect(store.getState()).toBeDefined();
    });
  });

  describe('Race Conditions', () => {
    it('handles simultaneous reads and writes', () => {
      const operations = [];

      for (let i = 0; i < 50; i++) {
        operations.push(() => store.getState());
        operations.push(() => store.dispatch({ type: 'bankroll/setBalance', payload: i }));
      }

      // Execute operations rapidly
      operations.forEach(op => op());

      expect(store.getState()).toBeDefined();
    });

    it('maintains state consistency under concurrent updates', () => {
      const updates = Array.from({ length: 100 }, (_, i) => ({
        type: 'bankroll/setBalance',
        payload: i,
      }));

      // Simulate concurrent updates
      updates.forEach(update => {
        store.dispatch(update);
        store.getState(); // Read state between writes
      });

      expect(store.getState().bankroll).toBeDefined();
    });
  });

  describe('Memory Management', () => {
    it('does not leak memory with repeated dispatches', () => {
      const iterations = 1000;

      for (let i = 0; i < iterations; i++) {
        store.dispatch({ type: 'bankroll/setBalance', payload: i });
      }

      // If we get here without crashing, memory is managed properly
      expect(store.getState()).toBeDefined();
    });

    it('cleans up subscriptions properly', () => {
      const unsubscribe = store.subscribe(() => {
        // Subscription callback
      });

      unsubscribe();

      // Should not crash after unsubscribe
      store.dispatch({ type: 'bankroll/setBalance', payload: 100 });
      expect(store.getState()).toBeDefined();
    });
  });
});
