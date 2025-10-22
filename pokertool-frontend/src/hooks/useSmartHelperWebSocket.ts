/**
 * SmartHelper WebSocket Hook
 *
 * React hook for real-time SmartHelper updates via WebSocket.
 * Handles connection, reconnection, and message processing.
 */
import { useState, useEffect, useCallback, useRef } from 'react';

export type MessageType =
  | 'recommendation'
  | 'table_state'
  | 'equity_update'
  | 'factor_update'
  | 'connection_ack'
  | 'ping'
  | 'pong'
  | 'error';

export interface WebSocketMessage<T = any> {
  type: MessageType;
  data: T;
  timestamp: number;
  session_id?: string;
}

export interface ConnectionStatus {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  latency: number;
  reconnectAttempts: number;
}

export interface UseSmartHelperWebSocketOptions {
  url?: string;
  tableId?: string;
  userId?: string;
  autoConnect?: boolean;
  reconnectInterval?: number; // milliseconds
  maxReconnectAttempts?: number;
  heartbeatInterval?: number; // milliseconds
  onRecommendation?: (data: any) => void;
  onTableState?: (data: any) => void;
  onEquityUpdate?: (data: any) => void;
  onFactorUpdate?: (data: any) => void;
  onError?: (error: string) => void;
}

export interface UseSmartHelperWebSocketReturn {
  status: ConnectionStatus;
  lastMessage: WebSocketMessage | null;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (type: MessageType, data: any) => void;
  subscribe: (messageType: MessageType, callback: (data: any) => void) => () => void;
}

/**
 * Hook for SmartHelper WebSocket connection
 *
 * @param options Configuration options
 * @returns WebSocket connection state and methods
 */
export const useSmartHelperWebSocket = (
  options: UseSmartHelperWebSocketOptions = {}
): UseSmartHelperWebSocketReturn => {
  const {
    url = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/smarthelper',
    tableId,
    userId,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    onRecommendation,
    onTableState,
    onEquityUpdate,
    onFactorUpdate,
    onError
  } = options;

  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pingTimeRef = useRef<number>(0);

  // State
  const [status, setStatus] = useState<ConnectionStatus>({
    connected: false,
    connecting: false,
    error: null,
    latency: 0,
    reconnectAttempts: 0
  });

  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  // Subscribers map
  const subscribersRef = useRef<Map<MessageType, Set<(data: any) => void>>>(new Map());

  // Generate connection ID
  const connectionIdRef = useRef<string>(
    `conn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  );

  /**
   * Build WebSocket URL with query parameters
   */
  const buildUrl = useCallback(() => {
    const params = new URLSearchParams();
    params.append('connection_id', connectionIdRef.current);
    if (userId) params.append('user_id', userId);
    if (tableId) params.append('table_id', tableId);
    return `${url}?${params.toString()}`;
  }, [url, userId, tableId]);

  /**
   * Send ping for latency measurement
   */
  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      pingTimeRef.current = Date.now();
      wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: pingTimeRef.current }));
    }
  }, []);

  /**
   * Handle incoming messages
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      setLastMessage(message);

      // Handle pong for latency calculation
      if (message.type === 'pong') {
        const latency = Date.now() - pingTimeRef.current;
        setStatus((prev) => ({ ...prev, latency }));
        return;
      }

      // Call specific handlers
      switch (message.type) {
        case 'recommendation':
          onRecommendation?.(message.data);
          break;
        case 'table_state':
          onTableState?.(message.data);
          break;
        case 'equity_update':
          onEquityUpdate?.(message.data);
          break;
        case 'factor_update':
          onFactorUpdate?.(message.data);
          break;
        case 'error':
          onError?.(message.data.error || 'Unknown error');
          break;
        case 'connection_ack':
          console.log('WebSocket connection acknowledged:', message.data);
          break;
      }

      // Notify subscribers
      const subscribers = subscribersRef.current.get(message.type);
      if (subscribers) {
        subscribers.forEach((callback) => callback(message.data));
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      onError?.('Failed to parse message');
    }
  }, [onRecommendation, onTableState, onEquityUpdate, onFactorUpdate, onError]);

  /**
   * Handle WebSocket open
   */
  const handleOpen = useCallback(() => {
    console.log('SmartHelper WebSocket connected');
    setStatus((prev) => ({
      ...prev,
      connected: true,
      connecting: false,
      error: null,
      reconnectAttempts: 0
    }));

    // Start heartbeat
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    heartbeatIntervalRef.current = setInterval(sendPing, heartbeatInterval);
  }, [sendPing, heartbeatInterval]);

  /**
   * Handle WebSocket close
   */
  const handleClose = useCallback(() => {
    console.log('SmartHelper WebSocket closed');
    setStatus((prev) => ({
      ...prev,
      connected: false,
      connecting: false
    }));

    // Stop heartbeat
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    // Attempt reconnection
    if (
      autoConnect &&
      status.reconnectAttempts < maxReconnectAttempts
    ) {
      console.log(`Reconnecting in ${reconnectInterval}ms (attempt ${status.reconnectAttempts + 1}/${maxReconnectAttempts})`);

      setStatus((prev) => ({
        ...prev,
        reconnectAttempts: prev.reconnectAttempts + 1
      }));

      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, reconnectInterval);
    } else if (status.reconnectAttempts >= maxReconnectAttempts) {
      const errorMsg = 'Max reconnection attempts reached';
      console.error(errorMsg);
      setStatus((prev) => ({
        ...prev,
        error: errorMsg
      }));
      onError?.(errorMsg);
    }
  }, [autoConnect, status.reconnectAttempts, maxReconnectAttempts, reconnectInterval, onError]);

  /**
   * Handle WebSocket error
   */
  const handleError = useCallback((event: Event) => {
    console.error('SmartHelper WebSocket error:', event);
    const errorMsg = 'WebSocket connection error';
    setStatus((prev) => ({
      ...prev,
      error: errorMsg,
      connecting: false
    }));
    onError?.(errorMsg);
  }, [onError]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    try {
      setStatus((prev) => ({ ...prev, connecting: true, error: null }));

      const ws = new WebSocket(buildUrl());
      ws.onopen = handleOpen;
      ws.onclose = handleClose;
      ws.onerror = handleError;
      ws.onmessage = handleMessage;

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setStatus((prev) => ({
        ...prev,
        connecting: false,
        error: 'Failed to create WebSocket connection'
      }));
    }
  }, [buildUrl, handleOpen, handleClose, handleError, handleMessage]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear heartbeat
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus({
      connected: false,
      connecting: false,
      error: null,
      latency: 0,
      reconnectAttempts: 0
    });
  }, []);

  /**
   * Send message through WebSocket
   */
  const sendMessage = useCallback((type: MessageType, data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: Date.now()
      };
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }, []);

  /**
   * Subscribe to specific message type
   */
  const subscribe = useCallback((messageType: MessageType, callback: (data: any) => void) => {
    if (!subscribersRef.current.has(messageType)) {
      subscribersRef.current.set(messageType, new Set());
    }
    subscribersRef.current.get(messageType)!.add(callback);

    // Return unsubscribe function
    return () => {
      const subscribers = subscribersRef.current.get(messageType);
      if (subscribers) {
        subscribers.delete(callback);
        if (subscribers.size === 0) {
          subscribersRef.current.delete(messageType);
        }
      }
    };
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect]); // Only run once on mount

  return {
    status,
    lastMessage,
    connect,
    disconnect,
    sendMessage,
    subscribe
  };
};
