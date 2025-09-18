import { useState, useEffect, useCallback, useRef } from 'react';
import io, { Socket } from 'socket.io-client';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
}

interface UseWebSocketReturn {
  connected: boolean;
  messages: WebSocketMessage[];
  sendMessage: (message: any) => void;
  clearMessages: () => void;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Initialize socket connection
    socketRef.current = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    socket.on('message', (data: any) => {
      const message: WebSocketMessage = {
        type: data.type || 'message',
        data: data,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, message]);
    });

    // Handle specific event types
    socket.on('table_update', (data: any) => {
      const message: WebSocketMessage = {
        type: 'table_update',
        data: data,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, message]);
    });

    socket.on('hand_complete', (data: any) => {
      const message: WebSocketMessage = {
        type: 'hand_complete',
        data: data,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, message]);
    });

    socket.on('stats_update', (data: any) => {
      const message: WebSocketMessage = {
        type: 'stats_update',
        data: data,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, message]);
    });

    socket.on('error', (error: any) => {
      console.error('WebSocket error:', error);
      const message: WebSocketMessage = {
        type: 'error',
        data: error,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, message]);
    });

    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, [url]);

  const sendMessage = useCallback((message: any) => {
    if (socketRef.current && socketRef.current.connected) {
      socketRef.current.emit('message', message);
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    connected,
    messages,
    sendMessage,
    clearMessages,
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
