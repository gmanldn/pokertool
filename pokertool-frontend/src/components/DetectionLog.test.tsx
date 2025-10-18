/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/DetectionLog.test.tsx
version: v1.0.0
last_commit: '2025-10-18T00:00:00+01:00'
fixes:
- date: '2025-10-18'
  summary: Added unit tests verifying detection log renders card and table updates
---
POKERTOOL-HEADER-END */

import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, waitFor, act } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { DetectionLog } from './DetectionLog';

jest.mock('../config/api', () => ({
  buildApiUrl: jest.fn((path: string) => `http://localhost:5001${path}`),
  httpToWs: jest.fn((url: string) => url.replace('http://', 'ws://')),
}));

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');
  return {
    ...actual,
    useMediaQuery: jest.fn().mockImplementation(() => false),
  };
});

const theme = createTheme();

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: { data: string }) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public onclose: ((event: { code?: number }) => void) | null = null;
  public sentMessages: string[] = [];

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sentMessages.push(data);
  }

  close() {
    this.onclose?.({ code: 1000 });
  }
}

const originalWebSocket = global.WebSocket;

beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });

  // @ts-expect-error -- override WebSocket for tests
  global.WebSocket = MockWebSocket;
});

afterAll(() => {
  global.WebSocket = originalWebSocket;
});

afterEach(() => {
  MockWebSocket.instances.length = 0;
  jest.clearAllTimers();
  jest.useRealTimers();
});

it('displays card and player detection events with their payload data', async () => {
  render(
    <ThemeProvider theme={theme}>
      <DetectionLog />
    </ThemeProvider>,
  );

  const socket = MockWebSocket.instances[0];
  expect(socket).toBeDefined();

  act(() => {
    socket.onopen?.(new Event('open'));
  });

  act(() => {
    socket.onmessage?.({
      data: JSON.stringify({
        type: 'card',
        severity: 'success',
        message: 'Community cards updated',
        data: {
          cards: ['Ah', 'Kd', 'Qs'],
          cardType: 'community',
        },
        timestamp: new Date().toISOString(),
      }),
    });
  });

  await waitFor(() => {
    expect(screen.getByText('Community cards updated')).toBeInTheDocument();
  });

  expect(screen.getAllByText('CARD').length).toBeGreaterThan(0);
  expect(
    screen.getByText(/"cards":\s+\[\s+"Ah",\s+"Kd",\s+"Qs"\s+\]/),
  ).toBeInTheDocument();

  act(() => {
    socket.onmessage?.({
      data: JSON.stringify({
        type: 'player',
        severity: 'info',
        message: 'Seat 3 assigned to Hero',
        data: {
          tableId: 'table-1',
          seat: 3,
          name: 'Hero',
          chips: 1000,
        },
        timestamp: new Date().toISOString(),
      }),
    });
  });

  await waitFor(() => {
    expect(screen.getByText('Seat 3 assigned to Hero')).toBeInTheDocument();
  });

  expect(screen.getAllByText('PLAYER').length).toBeGreaterThan(0);
  expect(screen.getByText(/"tableId":\s*"table-1"/)).toBeInTheDocument();
});
