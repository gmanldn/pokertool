import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import gameReducer from './slices/gameSlice';
import adviceReducer from './slices/adviceSlice';
import sessionReducer from './slices/sessionSlice';
import settingsReducer from './slices/settingsSlice';
import bankrollReducer from './slices/bankrollSlice';
import tournamentReducer from './slices/tournamentSlice';

// Configure store with all slices
export const store = configureStore({
  reducer: {
    game: gameReducer,
    advice: adviceReducer,
    session: sessionReducer,
    settings: settingsReducer,
    bankroll: bankrollReducer,
    tournament: tournamentReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types for serialization checks
        ignoredActions: ['game/updateTable', 'advice/receiveAdvice'],
      },
    }),
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Export typed hooks for use throughout the app
export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Load persisted state from localStorage
export const loadState = (): Partial<RootState> | undefined => {
  try {
    const serializedState = localStorage.getItem('pokertool-state');
    if (serializedState === null) {
      return undefined;
    }
    return JSON.parse(serializedState);
  } catch (err) {
    console.error('Failed to load state from localStorage:', err);
    return undefined;
  }
};

// Save state to localStorage
export const saveState = (state: RootState) => {
  try {
    // Only persist settings, session, bankroll, and tournament data (not real-time game/advice state)
    const stateToPersist = {
      settings: state.settings,
      session: {
        ...state.session,
        // Don't persist real-time metrics
        connected: false,
      },
      bankroll: state.bankroll,
      tournament: state.tournament,
    };
    const serializedState = JSON.stringify(stateToPersist);
    localStorage.setItem('pokertool-state', serializedState);
  } catch (err) {
    console.error('Failed to save state to localStorage:', err);
  }
};

// Subscribe to store changes and persist state
store.subscribe(() => {
  saveState(store.getState());
});
