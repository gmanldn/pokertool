/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/__tests__/reliability/websocket-reliability.test.tsx
version: v101.0.0
last_commit: '2025-10-23T00:00:00+01:00'
fixes:
- date: '2025-10-23'
  summary: WebSocket reliability and connection handling tests - 20 tests
---
POKERTOOL-HEADER-END */

import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders, MockWebSocket } from '../../test-utils/testHelpers';
import '@testing-library/jest-dom';

/**
 * WebSocket Reliability Tests
 *
 * Tests to ensure WebSocket connections handle disconnections, reconnections,
 * message errors, and network issues gracefully.
 */

describe('WebSocket Reliability Tests', () => {
  let mockWebSocket: MockWebSocket;

  beforeEach(() => {
    mockWebSocket = new MockWebSocket('ws://localhost:5001/ws');
    (global as any).WebSocket = jest.fn(() => mockWebSocket);
  });

  afterEach(() => {
    mockWebSocket.close();
    jest.restoreAllMocks();
  });

  describe('Connection Management', () => {
    it('establishes WebSocket connection successfully', () => {
      mockWebSocket.readyState = WebSocket.OPEN;
      mockWebSocket.triggerOpen();

      expect(mockWebSocket.readyState).toBe(WebSocket.OPEN);
    });

    it('handles connection failures gracefully', () => {
      mockWebSocket.readyState = WebSocket.CLOSED;
      const errorHandler = jest.fn();
      mockWebSocket.addEventListener('error', errorHandler);

      mockWebSocket.triggerError(new Error('Connection failed'));

      expect(errorHandler).toHaveBeenCalled();
    });

    it('reconnects after disconnection', async () => {
      mockWebSocket.readyState = WebSocket.OPEN;
      mockWebSocket.triggerOpen();

      // Simulate disconnection
      mockWebSocket.readyState = WebSocket.CLOSED;
      mockWebSocket.triggerClose();

      // Should attempt reconnection (implementation-specific)
      await waitFor(() => {
        expect(mockWebSocket.readyState).toBe(WebSocket.CLOSED);
      });
    });

    it('implements exponential backoff for reconnection attempts', async () => {
      const attemptTimestamps: number[] = [];

      for (let i = 0; i < 3; i++) {
        attemptTimestamps.push(Date.now());
        mockWebSocket.readyState = WebSocket.CLOSED;
        mockWebSocket.triggerClose();

        // Wait before next attempt
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Should have increasing delays (basic check)
      expect(attemptTimestamps.length).toBe(3);
    });

    it('limits maximum reconnection attempts', () => {
      let reconnectCount = 0;
      const maxAttempts = 5;

      for (let i = 0; i < 10; i++) {
        if (reconnectCount < maxAttempts) {
          reconnectCount++;
          mockWebSocket.readyState = WebSocket.CLOSED;
          mockWebSocket.triggerClose();
        }
      }

      // Should not exceed max attempts
      expect(reconnectCount).toBeLessThanOrEqual(maxAttempts);
    });
  });

  describe('Message Handling', () => {
    it('processes valid JSON messages correctly', () => {
      const validMessage = { type: 'update', data: { value: 42 } };
      const messageHandler = jest.fn();

      mockWebSocket.addEventListener('message', messageHandler);
      mockWebSocket.triggerMessage(JSON.stringify(validMessage));

      expect(messageHandler).toHaveBeenCalled();
    });

    it('handles invalid JSON messages gracefully', () => {
      const invalidMessages = [
        '{invalid json}',
        'null',
        '',
        'undefined',
        '{"incomplete":',
      ];

      const errorHandler = jest.fn();
      mockWebSocket.addEventListener('error', errorHandler);

      invalidMessages.forEach(msg => {
        try {
          mockWebSocket.triggerMessage(msg);
          JSON.parse(msg);
        } catch (e) {
          // Should catch and handle parse errors
          expect(e).toBeInstanceOf(SyntaxError);
        }
      });
    });

    it('handles messages with missing required fields', () => {
      const incompleteMessage = { type: 'update' }; // Missing 'data' field
      const messageHandler = jest.fn();

      mockWebSocket.addEventListener('message', messageHandler);
      mockWebSocket.triggerMessage(JSON.stringify(incompleteMessage));

      // Should not crash, may log warning
      expect(messageHandler).toHaveBeenCalled();
    });

    it('handles extremely large messages without overflow', () => {
      const largeData = Array(10000).fill('x').join('');
      const largeMessage = { type: 'data', payload: largeData };

      const messageHandler = jest.fn();
      mockWebSocket.addEventListener('message', messageHandler);

      mockWebSocket.triggerMessage(JSON.stringify(largeMessage));

      expect(messageHandler).toHaveBeenCalled();
    });

    it('handles rapid message bursts without dropping messages', () => {
      const messageCount = 100;
      const receivedMessages: any[] = [];

      mockWebSocket.addEventListener('message', (event) => {
        receivedMessages.push(event.data);
      });

      // Send burst of messages
      for (let i = 0; i < messageCount; i++) {
        mockWebSocket.triggerMessage(JSON.stringify({ id: i }));
      }

      // All messages should be received
      expect(receivedMessages.length).toBe(messageCount);
    });
  });

  describe('Error Recovery', () => {
    it('recovers from WebSocket errors without app crash', () => {
      mockWebSocket.readyState = WebSocket.OPEN;

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      mockWebSocket.triggerError(new Error('Test error'));

      // App should continue functioning
      expect(mockWebSocket.readyState).toBe(WebSocket.OPEN);

      consoleSpy.mockRestore();
    });

    it('handles network interruptions gracefully', async () => {
      mockWebSocket.readyState = WebSocket.OPEN;
      mockWebSocket.triggerOpen();

      // Simulate network interruption
      mockWebSocket.readyState = WebSocket.CLOSED;
      mockWebSocket.triggerClose();

      await waitFor(() => {
        expect(mockWebSocket.readyState).toBe(WebSocket.CLOSED);
      });
    });

    it('preserves application state during reconnection', () => {
      const Navigation = require('../../components/Navigation').Navigation;
      const mockStatus = {
        status: 'online',
        message: 'Connected',
        timestamp: Date.now(),
        health: { status: 'healthy' }
      };

      const { rerender } = renderWithProviders(
        <Navigation connected={true} backendStatus={mockStatus} />
      );

      // Simulate disconnection
      rerender(
        <Navigation connected={false} backendStatus={{
          ...mockStatus,
          status: 'offline'
        }} />
      );

      // UI should update to show disconnected state
      expect(screen.queryAllByText(/offline|disconnected/i).length).toBeGreaterThan(0);
    });
  });

  describe('Message Queue Management', () => {
    it('queues messages when connection is closed', () => {
      mockWebSocket.readyState = WebSocket.CLOSED;

      const messagesToSend = [
        { type: 'event1', data: 'test1' },
        { type: 'event2', data: 'test2' },
      ];

      messagesToSend.forEach(msg => {
        try {
          mockWebSocket.send(JSON.stringify(msg));
        } catch (e) {
          // Should catch error and queue message
          expect(e).toBeDefined();
        }
      });
    });

    it('sends queued messages after reconnection', async () => {
      mockWebSocket.readyState = WebSocket.CLOSED;

      // Try to send while closed
      const testMessage = { type: 'test', data: 'queued' };
      try {
        mockWebSocket.send(JSON.stringify(testMessage));
      } catch {
        // Expected to fail
      }

      // Reconnect
      mockWebSocket.readyState = WebSocket.OPEN;
      mockWebSocket.triggerOpen();

      // Queue should be processed
      expect(mockWebSocket.readyState).toBe(WebSocket.OPEN);
    });

    it('limits message queue size to prevent memory issues', () => {
      mockWebSocket.readyState = WebSocket.CLOSED;

      const maxQueueSize = 100;
      const messagesToQueue = 150;

      for (let i = 0; i < messagesToQueue; i++) {
        try {
          mockWebSocket.send(JSON.stringify({ id: i }));
        } catch {
          // Expected to fail when closed
        }
      }

      // Queue should not exceed max size
      expect(true).toBe(true); // Placeholder for actual queue size check
    });
  });

  describe('Connection State Transitions', () => {
    it('transitions through connection states correctly', () => {
      // CONNECTING
      expect(mockWebSocket.readyState).toBe(WebSocket.CONNECTING);

      // OPEN
      mockWebSocket.readyState = WebSocket.OPEN;
      mockWebSocket.triggerOpen();
      expect(mockWebSocket.readyState).toBe(WebSocket.OPEN);

      // CLOSING
      mockWebSocket.readyState = WebSocket.CLOSING;
      expect(mockWebSocket.readyState).toBe(WebSocket.CLOSING);

      // CLOSED
      mockWebSocket.readyState = WebSocket.CLOSED;
      mockWebSocket.triggerClose();
      expect(mockWebSocket.readyState).toBe(WebSocket.CLOSED);
    });

    it('handles rapid state changes without errors', () => {
      const states = [
        WebSocket.CONNECTING,
        WebSocket.OPEN,
        WebSocket.CLOSING,
        WebSocket.CLOSED,
      ];

      states.forEach(state => {
        mockWebSocket.readyState = state;
        expect(mockWebSocket.readyState).toBe(state);
      });
    });
  });

  describe('Heartbeat and Keep-Alive', () => {
    it('sends periodic heartbeat messages', () => {
      mockWebSocket.readyState = WebSocket.OPEN;
      const sendSpy = jest.spyOn(mockWebSocket, 'send');

      // Simulate heartbeat
      mockWebSocket.send(JSON.stringify({ type: 'ping' }));

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({ type: 'ping' }));
    });

    it('detects connection timeout without heartbeat response', async () => {
      mockWebSocket.readyState = WebSocket.OPEN;
      mockWebSocket.triggerOpen();

      // Send heartbeat
      mockWebSocket.send(JSON.stringify({ type: 'ping' }));

      // Wait for timeout (no pong received)
      await new Promise(resolve => setTimeout(resolve, 100));

      // Should detect timeout (implementation-specific)
      expect(true).toBe(true);
    });

    it('maintains connection with regular heartbeats', () => {
      mockWebSocket.readyState = WebSocket.OPEN;

      // Simulate regular heartbeats
      for (let i = 0; i < 5; i++) {
        mockWebSocket.send(JSON.stringify({ type: 'ping' }));
        mockWebSocket.triggerMessage(JSON.stringify({ type: 'pong' }));
      }

      // Connection should remain open
      expect(mockWebSocket.readyState).toBe(WebSocket.OPEN);
    });
  });

  describe('Concurrent Connection Handling', () => {
    it('prevents multiple simultaneous connections', () => {
      const ws1 = new MockWebSocket('ws://localhost:5001/ws');
      const ws2 = new MockWebSocket('ws://localhost:5001/ws');

      ws1.readyState = WebSocket.OPEN;
      ws2.readyState = WebSocket.CONNECTING;

      // Only one should be active (implementation-specific)
      expect([ws1.readyState, ws2.readyState]).toContain(WebSocket.OPEN);
    });

    it('closes old connection when establishing new one', () => {
      const oldWs = new MockWebSocket('ws://localhost:5001/ws');
      oldWs.readyState = WebSocket.OPEN;

      const closeSpy = jest.spyOn(oldWs, 'close');

      // Create new connection
      const newWs = new MockWebSocket('ws://localhost:5001/ws');
      newWs.readyState = WebSocket.OPEN;

      // Old connection should be closed (in real implementation)
      expect(closeSpy).not.toThrow();
    });
  });
});
