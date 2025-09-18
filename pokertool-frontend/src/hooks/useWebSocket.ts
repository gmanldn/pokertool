import { useState, useEffect, useCallback, useRef } from 'react';

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
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000;

  const connect = useCallback(() => {
    try {
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
        reconnectAttempts.current = 0;
      };

      socketRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnected(false);
        
        // Attempt to reconnect if not manually closed
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          console.log(`Reconnect attempt ${reconnectAttempts.current}/${maxReconnectAttempts}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay * reconnectAttempts.current);
        }
      };

      socketRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
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
    }
  }, [url]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      try {
        const messageData = typeof message === 'string' ? message : JSON.stringify(message);
        socketRef.current.send(messageData);
        console.log('Message sent:', message);
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
      }
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
