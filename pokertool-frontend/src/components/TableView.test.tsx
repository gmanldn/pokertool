/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/components/TableView.test.tsx
version: v1.0.0
last_commit: '2025-10-18T00:00:00+01:00'
fixes:
- date: '2025-10-18'
  summary: Added unit tests verifying table detection data renders in TableView
---
POKERTOOL-HEADER-END */

import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { TableView } from './TableView';
import { useWebSocket, ConnectionStatus } from '../hooks/useWebSocket';
import { WebSocketMessageData } from '../types/common';

jest.mock('@mui/material', () => {
  // Preserve all of MUI while overriding useMediaQuery to avoid relying on matchMedia
  const actual = jest.requireActual('@mui/material');
  return {
    ...actual,
    useMediaQuery: jest.fn().mockImplementation(() => false),
  };
});

jest.mock('../hooks/useWebSocket', () => ({
  useWebSocket: jest.fn(),
  ConnectionStatus: {
    CONNECTED: 'connected',
    CONNECTING: 'connecting',
    DISCONNECTED: 'disconnected',
    RECONNECTING: 'reconnecting',
  },
}));

jest.mock('./AdvicePanel', () => ({
  AdvicePanel: () => <div data-testid="advice-panel" />,
}));

jest.mock('./DecisionTimer', () => ({
  DecisionTimer: () => <div data-testid="decision-timer" />,
}));

jest.mock('./HandStrengthMeter', () => ({
  HandStrengthMeter: () => <div data-testid="hand-strength-meter" />,
}));

jest.mock('./EquityCalculator', () => ({
  EquityCalculator: () => <div data-testid="equity-calculator" />,
}));

jest.mock('./BetSizingRecommendations', () => ({
  BetSizingRecommendations: () => <div data-testid="bet-sizing" />,
}));

const mockedUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>;

const theme = createTheme();

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
});

beforeEach(() => {
  mockedUseWebSocket.mockReset();
});

it('renders detected table and card data when websocket updates arrive', async () => {
  const detectedTable = {
    tableId: 'table-1',
    tableName: 'High Roller Table',
    players: [
      {
        seat: 1,
        name: 'Hero Player',
        chips: 1000,
        cards: ['Ah', 'Kd'],
        isActive: true,
        isFolded: false,
      },
      {
        seat: 2,
        name: 'Opponent',
        chips: 850,
        cards: ['Qs', 'Qc'],
        isActive: true,
        isFolded: false,
      },
    ],
    pot: 250,
    communityCards: ['2c', '7d', 'Jc'],
    currentAction: 'Hero to act',
    isActive: true,
  };

  mockedUseWebSocket.mockReturnValue({
    connected: true,
    connectionStatus: ConnectionStatus.CONNECTED,
    messages: [
      {
        type: 'table_update',
        data: detectedTable as unknown as WebSocketMessageData,
        timestamp: Date.now(),
      },
    ],
    sendMessage: jest.fn(),
    clearMessages: jest.fn(),
    reconnect: jest.fn(),
    reconnectCountdown: 0,
    cachedMessageCount: 0,
  });

  render(
    <ThemeProvider theme={theme}>
      <TableView sendMessage={jest.fn()} />
    </ThemeProvider>,
  );

  await waitFor(() => expect(screen.getByText('Pot: $250')).toBeInTheDocument());

  expect(screen.getAllByText('High Roller Table').length).toBeGreaterThan(0);
  expect(screen.getByText('Hero to act')).toBeInTheDocument();
  expect(screen.getByText('Hero Player')).toBeInTheDocument();
  expect(screen.getByText('Opponent')).toBeInTheDocument();
  expect(screen.getByText('Ah')).toBeInTheDocument();
  expect(screen.getByText('Kd')).toBeInTheDocument();
  expect(screen.getByText('2c')).toBeInTheDocument();
  expect(screen.getByText('7d')).toBeInTheDocument();
  expect(screen.getByText('Jc')).toBeInTheDocument();
});
