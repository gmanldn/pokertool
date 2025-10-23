/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/test-utils/testHelpers.tsx
version: v100.3.1
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: Created comprehensive test utilities for 200+ regression tests
---
POKERTOOL-HEADER-END */

import React, { ReactElement, useState } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore, PreloadedState } from '@reduxjs/toolkit';
import { ThemeContext } from '../contexts/ThemeContext';
import { ThemeProvider, createTheme } from '@mui/material/styles';

// Import all reducers
import gameReducer from '../store/slices/gameSlice';
import adviceReducer from '../store/slices/adviceSlice';
import sessionReducer from '../store/slices/sessionSlice';
import settingsReducer from '../store/slices/settingsSlice';
import bankrollReducer from '../store/slices/bankrollSlice';
import tournamentReducer from '../store/slices/tournamentSlice';
import type { RootState } from '../store';

// Create a test store factory
export function createTestStore(preloadedState?: PreloadedState<RootState>) {
  return configureStore({
    reducer: {
      game: gameReducer,
      advice: adviceReducer,
      session: sessionReducer,
      settings: settingsReducer,
      bankroll: bankrollReducer,
      tournament: tournamentReducer,
    },
    preloadedState,
  });
}

// Custom render function with all providers
interface ExtendedRenderOptions extends Omit<RenderOptions, 'queries'> {
  preloadedState?: PreloadedState<RootState>;
  store?: ReturnType<typeof createTestStore>;
  route?: string;
}

export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState,
    store = createTestStore(preloadedState),
    route = '/',
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  window.history.pushState({}, 'Test page', route);

  const theme = createTheme({
    palette: {
      mode: 'light',
    },
  });

  function Wrapper({ children }: { children: React.ReactNode }) {
    const [darkMode, setDarkMode] = useState(false);
    const toggleDarkMode = () => setDarkMode(!darkMode);

    return (
      <Provider store={store}>
        <BrowserRouter>
          <ThemeProvider theme={theme}>
            <ThemeContext.Provider value={{ darkMode, toggleDarkMode }}>
              {children}
            </ThemeContext.Provider>
          </ThemeProvider>
        </BrowserRouter>
      </Provider>
    );
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}

// Mock WebSocket for real-time features
export class MockWebSocket {
  static instances: MockWebSocket[] = [];
  readyState: number = WebSocket.CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string): void {
    // Store sent messages for assertions
  }

  close(): void {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  static reset(): void {
    MockWebSocket.instances = [];
  }
}

// Mock fetch for API calls
export function mockFetch(response: any, options: { ok?: boolean; status?: number } = {}) {
  const { ok = true, status = 200 } = options;
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok,
      status,
      json: () => Promise.resolve(response),
      text: () => Promise.resolve(JSON.stringify(response)),
    } as Response)
  );
}

// Helper to wait for async updates
export const waitForAsync = () => new Promise((resolve) => setTimeout(resolve, 0));

// Mock backend status
export const mockBackendStatus = (state: 'online' | 'offline' | 'starting' = 'online') => ({
  state,
  startTime: Date.now(),
  version: 'v100.3.1',
  lastChecked: new Date().toISOString(),
  attempts: 0,
  expectedStartupTime: 30000,
});

// Mock system health data
export const mockHealthData = (status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy') => ({
  status,
  timestamp: Date.now(),
  categories: {
    api: { status, message: 'API working' },
    database: { status, message: 'Database connected' },
    websocket: { status, message: 'WebSocket connected' },
  },
});

// Common test data factories
export const createMockTableData = () => ({
  id: 'table-1',
  name: 'Test Table',
  players: [
    { id: 'p1', name: 'Player 1', stack: 1000, position: 0, cards: [] },
    { id: 'p2', name: 'Player 2', stack: 1500, position: 1, cards: [] },
  ],
  pot: 100,
  communityCards: [],
  currentBet: 20,
  button: 0,
});

export const createMockTransaction = (amount: number = 100) => ({
  id: Date.now().toString(),
  amount,
  type: 'win' as const,
  description: 'Test transaction',
  timestamp: Date.now(),
});

export const createMockTournament = () => ({
  id: Date.now().toString(),
  name: 'Test Tournament',
  buyin: 50,
  rebuy: 0,
  addon: 0,
  totalEntrants: 100,
  structure: 'freezeout' as const,
  startTime: Date.now(),
  position: null,
  notes: '',
});

export const createMockSession = () => ({
  id: Date.now().toString(),
  startTime: Date.now(),
  hands: [],
  stats: {
    handsPlayed: 0,
    totalProfit: 0,
    vpip: 0,
    pfr: 0,
    winRate: 0,
  },
});

// Accessibility testing helpers
export const checkAccessibility = async (container: HTMLElement) => {
  // Check for ARIA labels
  const buttons = container.querySelectorAll('button');
  buttons.forEach((button) => {
    expect(
      button.textContent || button.getAttribute('aria-label')
    ).toBeTruthy();
  });

  // Check for form labels
  const inputs = container.querySelectorAll('input');
  inputs.forEach((input) => {
    const id = input.getAttribute('id');
    if (id) {
      const label = container.querySelector(`label[for="${id}"]`);
      expect(label || input.getAttribute('aria-label')).toBeTruthy();
    }
  });
};

// Keyboard navigation helper
export const simulateKeyPress = (element: Element, key: string, keyCode?: number) => {
  const event = new KeyboardEvent('keydown', {
    key,
    keyCode,
    bubbles: true,
  });
  element.dispatchEvent(event);
};

// Mock chart library (recharts) - moved to setupTests.ts to avoid Babel issues

// Export all from testing-library for convenience
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
