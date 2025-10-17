/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/hooks/useWebSocket.ts
version: v28.0.0
last_commit: '2025-09-23T08:41:38+01:00'
fixes:
- date: '2025-09-25'
  summary: Enhanced enterprise documentation and comprehensive unit tests added
---
POKERTOOL-HEADER-END */

import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketMessageData } from '../types/common';

export interface WebSocketMessage {
  type: string;
  data: WebSocketMessageData;
  timestamp: number;
}

export enum ConnectionStatus {
  CONNECTED = 'connected',
  CONNECTING = 'connecting',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
}

interface UseWebSocketReturn {
  connected: boolean;
  connectionStatus: ConnectionStatus;
  messages: WebSocketMessage[];
  sendMessage: (message: WebSocketMessageData | string) => void;
  clearMessages: () => void;
  reconnect: () => void;
  reconnectCountdown: number;
  cachedMessageCount: number;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [connected, setConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [reconnectCountdown, setReconnectCountdown] = useState(0);
  const [cachedMessageCount, setCachedMessageCount] = useState(0);
  
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountdownIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastHeartbeatRef = useRef<number>(Date.now());
  const messageQueueRef = useRef<(WebSocketMessageData | string)[]>([]);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 10;
  const baseReconnectDelay = 1000;
  const heartbeatInterval = 30000; // 30 seconds
  const heartbeatTimeout = 35000; // 35 seconds

  // Calculate exponential backoff delay
  const getReconnectDelay = useCallback((attempt: number): number => {
    const delay = Math.min(baseReconnectDelay * Math.pow(2, attempt), 30000);
    return delay;
  }, []);

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    heartbeatIntervalRef.current = setInterval(() => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        // Send ping
        socketRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        
        // Check if we received a pong recently
        if (Date.now() - lastHeartbeatRef.current > heartbeatTimeout) {
          console.warn('Heartbeat timeout - reconnecting');
          socketRef.current.close();
        }
      }
    }, heartbeatInterval);
  }, []);

  // Stop heartbeat
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Replay cached messages
  const replayCachedMessages = useCallback(() => {
    if (messageQueueRef.current.length > 0) {
      console.log(`Replaying ${messageQueueRef.current.length} cached messages`);
      messageQueueRef.current.forEach(msg => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(typeof msg === 'string' ? msg : JSON.stringify(msg));
        }
      });
      messageQueueRef.current = [];
      setCachedMessageCount(0);
    }
  }, []);

  const connect = useCallback(() => {
    try {
      // Clear any existing countdown
      if (reconnectCountdownIntervalRef.current) {
        clearInterval(reconnectCountdownIntervalRef.current);
      }

      setConnectionStatus(reconnectAttempts.current > 0 ? ConnectionStatus.RECONNECTING : ConnectionStatus.CONNECTING);
      
      // For demo purposes, use a mock user_id and token
      // In production, these would come from authentication context
      const userId = 'demo_user';
      const token = 'demo_token';
      
      // Convert HTTP URL to WebSocket URL and add authentication parameters
      const wsUrl = url.replace('http://', 'ws://').replace('https://', 'wss://');
      const fullUrl = `${wsUrl}/ws/${userId}?token=${token}`;
      
      console.log('Connecting to WebSocket:', fullUrl);
      socketRef.current = new WebSocket(fullUrl);

      socketRef.current.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setConnectionStatus(ConnectionStatus.CONNECTED);
        reconnectAttempts.current = 0;
        setReconnectCountdown(0);
        
        // Start heartbeat
        startHeartbeat();
        
        // Replay any cached messages
        replayCachedMessages();
      };

      socketRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnected(false);
        setConnectionStatus(ConnectionStatus.DISCONNECTED);
        stopHeartbeat();
        
        // Attempt to reconnect if not manually closed
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = getReconnectDelay(reconnectAttempts.current - 1);
          console.log(`Reconnect attempt ${reconnectAttempts.current}/${maxReconnectAttempts} in ${delay}ms`);
          
          setConnectionStatus(ConnectionStatus.RECONNECTING);
          setReconnectCountdown(Math.ceil(delay / 1000));
          
          // Start countdown
          reconnectCountdownIntervalRef.current = setInterval(() => {
            setReconnectCountdown(prev => Math.max(0, prev - 1));
          }, 1000);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };

      socketRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle pong response
          if (data.type === 'pong') {
            lastHeartbeatRef.current = Date.now();
            return;
          }
          
          const message: WebSocketMessage = {
            type: data.type || 'message',
            data: data.data || data,
            timestamp: Date.now(),
          };
          
          console.log('WebSocket message received:', message);
          setMessages(prev => [...prev, message]);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      socketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        const message: WebSocketMessage = {
          type: 'error',
          data: { error: 'WebSocket connection error' },
          timestamp: Date.now(),
        };
        setMessages(prev => [...prev, message]);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionStatus(ConnectionStatus.DISCONNECTED);
    }
  }, [url, getReconnectDelay, startHeartbeat, stopHeartbeat, replayCachedMessages]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (reconnectCountdownIntervalRef.current) {
        clearInterval(reconnectCountdownIntervalRef.current);
      }
      stopHeartbeat();
      if (socketRef.current) {
        socketRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect, stopHeartbeat]);

  const sendMessage = useCallback((message: WebSocketMessageData | string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      try {
        const messageData = typeof message === 'string' ? message : JSON.stringify(message);
        socketRef.current.send(messageData);
        console.log('Message sent:', message);
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
      }
    } else {
      // Cache message for later replay
      console.warn('WebSocket is not connected - caching message');
      messageQueueRef.current.push(message);
      setCachedMessageCount(messageQueueRef.current.length);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const reconnect = useCallback(() => {
    // Manual reconnect - reset attempts and connect immediately
    console.log('Manual reconnect requested');
    reconnectAttempts.current = 0;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (reconnectCountdownIntervalRef.current) {
      clearInterval(reconnectCountdownIntervalRef.current);
    }
    
    if (socketRef.current) {
      socketRef.current.close();
    }
    
    connect();
  }, [connect]);

  return {
    connected,
    connectionStatus,
    messages,
    sendMessage,
    clearMessages,
    reconnect,
    reconnectCountdown,
    cachedMessageCount,
  };
};

// Custom hook for subscribing to specific message types
export const useWebSocketSubscription = (
  messages: WebSocketMessage[],
  messageType: string
): WebSocketMessage[] => {
  const [filteredMessages, setFilteredMessages] = useState<WebSocketMessage[]>([]);

  useEffect(() => {
    const filtered = messages.filter(msg => msg.type === messageType);
    setFilteredMessages(filtered);
  }, [messages, messageType]);

  return filteredMessages;
};
