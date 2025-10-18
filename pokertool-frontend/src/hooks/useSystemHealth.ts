/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/hooks/useSystemHealth.ts
version: v86.3.1
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Created custom hook for reusable system health data fetching with caching and WebSocket support
---
POKERTOOL-HEADER-END */

import { useState, useEffect, useRef, useCallback } from 'react';
import { buildApiUrl, httpToWs } from '../config/api';

export interface HealthStatus {
  feature_name: string;
  category: string;
  status: 'healthy' | 'degraded' | 'failing' | 'unknown';
  last_check: string;
  latency_ms?: number;
  error_message?: string;
  metadata?: Record<string, any>;
  description?: string;
}

export interface HealthData {
  timestamp: string;
  overall_status: string;
  categories: Record<string, {
    status: string;
    checks: HealthStatus[];
  }>;
  failing_count: number;
  degraded_count: number;
}

interface CacheEntry {
  data: HealthData;
  timestamp: number;
}

interface UseSystemHealthOptions {
  enableWebSocket?: boolean;
  enableCache?: boolean;
  cacheTTL?: number; // Time to live in milliseconds (default: 5 minutes)
  autoFetch?: boolean;
  onStatusChange?: (data: HealthData) => void;
}

interface UseSystemHealthReturn {
  healthData: HealthData | null;
  loading: boolean;
  error: string | null;
  refreshing: boolean;
  fetchHealthData: () => Promise<void>;
  clearCache: () => void;
  isConnected: boolean;
}

const CACHE_KEY = 'system_health_cache';
const DEFAULT_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export const useSystemHealth = (
  options: UseSystemHealthOptions = {}
): UseSystemHealthReturn => {
  const {
    enableWebSocket = true,
    enableCache = true,
    cacheTTL = DEFAULT_CACHE_TTL,
    autoFetch = true,
    onStatusChange,
  } = options;

  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const previousDataRef = useRef<HealthData | null>(null);

  // Load data from cache
  const loadFromCache = useCallback((): HealthData | null => {
    if (!enableCache) return null;

    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (!cached) return null;

      const cacheEntry: CacheEntry = JSON.parse(cached);
      const now = Date.now();

      // Check if cache is still valid
      if (now - cacheEntry.timestamp < cacheTTL) {
        return cacheEntry.data;
      }

      // Cache expired, remove it
      localStorage.removeItem(CACHE_KEY);
      return null;
    } catch (err) {
      console.error('Failed to load from cache:', err);
      return null;
    }
  }, [enableCache, cacheTTL]);

  // Save data to cache
  const saveToCache = useCallback((data: HealthData) => {
    if (!enableCache) return;

    try {
      const cacheEntry: CacheEntry = {
        data,
        timestamp: Date.now(),
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheEntry));
    } catch (err) {
      console.error('Failed to save to cache:', err);
    }
  }, [enableCache]);

  // Clear cache
  const clearCache = useCallback(() => {
    try {
      localStorage.removeItem(CACHE_KEY);
    } catch (err) {
      console.error('Failed to clear cache:', err);
    }
  }, []);

  // Fetch health data from API with optimistic updates
  const fetchHealthData = useCallback(async () => {
    // First, try to load from cache for immediate display
    if (loading && enableCache) {
      const cachedData = loadFromCache();
      if (cachedData) {
        setHealthData(cachedData);
        setLoading(false);
      }
    }

    try {
      setError(null);
      setRefreshing(true);

      const response = await fetch(buildApiUrl('/api/system/health'));
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data: HealthData = await response.json();

      // Save to cache
      saveToCache(data);

      // Update state
      setHealthData(data);
      setLoading(false);
      setRefreshing(false);

      // Notify status change if callback provided
      if (onStatusChange &&
          JSON.stringify(previousDataRef.current) !== JSON.stringify(data)) {
        onStatusChange(data);
        previousDataRef.current = data;
      }
    } catch (err) {
      console.error('Failed to fetch health data:', err);
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(`Waiting for backend API at http://localhost:5001/api/system/health - ${errorMsg}. Check that start.py is running.`);
      setLoading(false);
      setRefreshing(false);

      // On error, if we have cached data, keep showing it
      if (!healthData && enableCache) {
        const cachedData = loadFromCache();
        if (cachedData) {
          setHealthData(cachedData);
        }
      }
    }
  }, [loading, enableCache, loadFromCache, saveToCache, healthData, onStatusChange]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!enableWebSocket) return;

    const connectWebSocket = () => {
      try {
        const wsUrl = httpToWs(buildApiUrl('/ws/system-health'));
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('System health WebSocket connected');
          setIsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            if (message.type === 'health_update') {
              // Trigger data refresh on update notification
              fetchHealthData();
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setIsConnected(false);
        };

        ws.onclose = () => {
          console.log('WebSocket closed, reconnecting in 10 seconds...');
          setIsConnected(false);
          setTimeout(connectWebSocket, 10000);
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to connect WebSocket:', err);
        setIsConnected(false);
        setTimeout(connectWebSocket, 10000);
      }
    };

    connectWebSocket();

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [enableWebSocket, fetchHealthData]);

  // Initial data fetch
  useEffect(() => {
    if (autoFetch) {
      fetchHealthData();
    }
  }, [autoFetch]); // Only run once on mount

  return {
    healthData,
    loading,
    error,
    refreshing,
    fetchHealthData,
    clearCache,
    isConnected,
  };
};
