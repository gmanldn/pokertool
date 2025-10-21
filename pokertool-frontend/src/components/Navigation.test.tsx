/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/Navigation.test.tsx
version: v96.1.4
last_commit: '2025-10-21T02:00:00Z'
fixes:
- date: '2025-10-21'
  summary: Consolidated backend status indicators - removed confusing realtime/backend split
---
POKERTOOL-HEADER-END */

import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Navigation } from './Navigation';
import { ThemeContext } from '../contexts/ThemeContext';
import type { BackendStatus } from '../hooks/useBackendLifecycle';

// Mock the hooks
const mockUseSystemHealth = jest.fn();
jest.mock('../hooks/useSystemHealth', () => ({
  useSystemHealth: (...args: any[]) => mockUseSystemHealth(...args),
}));

jest.mock('../config/api', () => ({
  buildApiUrl: (path: string) => `http://localhost:5001${path}`,
}));

// Helper to render with providers
const renderWithProviders = (ui: React.ReactElement) => {
  const theme = createTheme({ palette: { mode: 'dark' } });
  const themeContextValue = {
    darkMode: true,
    toggleDarkMode: jest.fn(),
  };

  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <ThemeContext.Provider value={themeContextValue}>
          {ui}
        </ThemeContext.Provider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Navigation - Backend Status Indicator', () => {
  beforeEach(() => {
    // Set default mock return value for useSystemHealth
    mockUseSystemHealth.mockReturnValue({
      healthData: {
        overall_status: 'healthy',
        categories: {},
      },
      loading: false,
      error: null,
    });

    // Mock fetch for startup status
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          total_steps: 0,
          steps_completed: 0,
          is_complete: true,
        }),
      })
    ) as jest.Mock;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should show "Backend Online" when all systems are healthy', async () => {
    const backendStatus: BackendStatus = {
      state: 'online',
      lastChecked: new Date().toISOString(),
      attempts: 1,
    };

    renderWithProviders(
      <Navigation connected={true} backendStatus={backendStatus} />
    );

    // Wait for debounce
    await waitFor(() => {
      expect(screen.getByText('Backend Online')).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('should show "Backend Offline" when API is down', async () => {
    const backendStatus: BackendStatus = {
      state: 'offline',
      lastChecked: new Date(Date.now() - 10000).toISOString(),
      attempts: 3,
    };

    renderWithProviders(
      <Navigation connected={true} backendStatus={backendStatus} />
    );

    await waitFor(() => {
      expect(screen.getByText('Backend Offline')).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('should show "Backend Offline" when WebSocket is disconnected', async () => {
    const backendStatus: BackendStatus = {
      state: 'online',
      lastChecked: new Date().toISOString(),
      attempts: 1,
    };

    renderWithProviders(
      <Navigation connected={false} backendStatus={backendStatus} />
    );

    // Wait for debounce (400ms for connected + 600ms for health)
    await waitFor(() => {
      expect(screen.getByText('Backend Offline')).toBeInTheDocument();
    }, { timeout: 1500 });
  });

  it('should show "Backend Degraded" when health checks fail', async () => {
    mockUseSystemHealth.mockReturnValue({
      healthData: {
        overall_status: 'degraded',
        categories: {
          database: { status: 'degraded' },
        },
      },
      loading: false,
      error: null,
    });

    const backendStatus: BackendStatus = {
      state: 'online',
      lastChecked: new Date().toISOString(),
      attempts: 1,
    };

    renderWithProviders(
      <Navigation connected={true} backendStatus={backendStatus} />
    );

    // Wait for debounce
    await waitFor(() => {
      expect(screen.getByText('Backend Degraded')).toBeInTheDocument();
    }, { timeout: 1000 });
  });

  it('should NOT show "Realtime Offline" status', async () => {
    // This test ensures we removed the confusing "Realtime Offline" label
    const backendStatus: BackendStatus = {
      state: 'online',
      lastChecked: new Date().toISOString(),
      attempts: 1,
    };

    renderWithProviders(
      <Navigation connected={false} backendStatus={backendStatus} />
    );

    await waitFor(() => {
      // Should NOT find "Realtime Offline" anywhere
      expect(screen.queryByText(/realtime offline/i)).not.toBeInTheDocument();
      // Should show "Backend Offline" instead
      expect(screen.getByText('Backend Offline')).toBeInTheDocument();
    }, { timeout: 1500 });
  });

  it('should show startup percentage when backend is starting', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          total_steps: 10,
          steps_completed: 5,
          is_complete: false,
        }),
      })
    ) as jest.Mock;

    const backendStatus: BackendStatus = {
      state: 'offline',
      lastChecked: new Date(Date.now() - 1000).toISOString(),
      attempts: 2,
    };

    renderWithProviders(
      <Navigation connected={false} backendStatus={backendStatus} />
    );

    await waitFor(() => {
      expect(screen.getByText('Backend Offline (50%)')).toBeInTheDocument();
    }, { timeout: 1500 });
  });

  it('should handle navigation clicks', async () => {
    const backendStatus: BackendStatus = {
      state: 'online',
      lastChecked: new Date().toISOString(),
      attempts: 1,
    };

    renderWithProviders(
      <Navigation connected={true} backendStatus={backendStatus} />
    );

    await waitFor(() => {
      expect(screen.getAllByText('PokerTool Pro')[0]).toBeInTheDocument();
    });

    // Click on logo should navigate to dashboard
    const logoElements = screen.getAllByText('PokerTool Pro');
    fireEvent.click(logoElements[0]);

    // Check URL changed to dashboard
    expect(window.location.pathname).toBe('/dashboard');
  });

  it('should toggle dark mode', async () => {
    const backendStatus: BackendStatus = {
      state: 'online',
      lastChecked: new Date().toISOString(),
      attempts: 1,
    };

    renderWithProviders(
      <Navigation connected={true} backendStatus={backendStatus} />
    );

    // Find dark mode toggle button
    const darkModeButton = screen.getAllByRole('button').find(
      btn => btn.querySelector('[data-testid="Brightness4Icon"], [data-testid="Brightness7Icon"]')
    );

    expect(darkModeButton).toBeDefined();
  });
});
