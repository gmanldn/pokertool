/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/hooks/useBackendLifecycle.ts
version: v1.0.0
last_commit: '2025-10-16T00:00:00+01:00'
fixes:
- date: '2025-10-16'
  summary: Added automatic backend lifecycle management hook for frontend bootstrapping
---
POKERTOOL-HEADER-END */

import { useCallback, useEffect, useRef, useState } from 'react';
import { buildApiUrl } from '../config/api';

type BackendState = 'checking' | 'starting' | 'online' | 'offline';

export interface BackendStatus {
  state: BackendState;
  lastChecked: string | null;
  error?: string;
  message?: string;
  attempts: number;
  errorDetails?: {
    type: string; // 'network' | 'timeout' | 'api_error' | 'unknown'
    statusCode?: number;
    timestamp: string;
  };
  expectedStartupTime?: number; // milliseconds
}

async function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchJson(url: string, init?: RequestInit) {
  const response = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Request to ${url} failed with ${response.status}`);
  }

  const text = await response.text();
  return text ? JSON.parse(text) : {};
}

export function useBackendLifecycle(pollIntervalMs: number = 15000) {
  const [status, setStatus] = useState<BackendStatus>({
    state: 'checking',
    lastChecked: null,
    attempts: 0,
    expectedStartupTime: 30000, // 30 seconds expected startup
  });

  const runningCheckRef = useRef(false);
  const startupStartTimeRef = useRef<number | null>(null);

  const updateStatus = useCallback((partial: Partial<BackendStatus>) => {
    setStatus((prev) => ({
      ...prev,
      ...partial,
      attempts: partial.attempts ?? prev.attempts,
    }));
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

      await fetch(buildApiUrl('/health'), {
        cache: 'no-store',
        signal: controller.signal
      }).then(async (response) => {
        clearTimeout(timeoutId);
        if (!response.ok) {
          throw new Error(`Health check returned ${response.status}`);
        }
        return response.text().then(text => text ? JSON.parse(text) : {});
      });

      updateStatus({
        state: 'online',
        error: undefined,
        errorDetails: undefined,
        message: 'Backend API responded to health check.',
        lastChecked: new Date().toISOString(),
      });
      return true;
    } catch (error) {
      const err = error as Error;
      let errorType = 'unknown';
      let statusCode: number | undefined;

      if (err.name === 'AbortError') {
        errorType = 'timeout';
      } else if (err.message.includes('returned')) {
        errorType = 'api_error';
        const match = err.message.match(/returned (\d+)/);
        if (match) statusCode = parseInt(match[1]);
      } else if (err.message.includes('Failed to fetch') || err.message.includes('fetch')) {
        errorType = 'network';
      }

      updateStatus({
        state: 'offline',
        error: err.message,
        errorDetails: {
          type: errorType,
          statusCode,
          timestamp: new Date().toISOString(),
        },
        message: 'Backend health check failed.',
        lastChecked: new Date().toISOString(),
      });
      console.error('[BackendLifecycle] Health check failed:', err);
      return false;
    }
  }, [updateStatus]);

  const startBackend = useCallback(async () => {
    try {
      updateStatus({
        state: 'starting',
        message: 'Attempting to start backend API...',
      });

      await fetchJson(buildApiUrl('/api/start-backend'), {
        method: 'POST',
      });

      updateStatus({
        message: 'Backend start request sent.',
        attempts: status.attempts + 1,
      });

      await wait(2000);
    } catch (error) {
      const err = error as Error;
      updateStatus({
        state: 'offline',
        error: err.message,
        message: 'Failed to send backend start request.',
        lastChecked: new Date().toISOString(),
        attempts: status.attempts + 1,
      });
      console.error('[BackendLifecycle] Failed to start backend:', err);
    }
  }, [status.attempts, updateStatus]);

  const ensureBackend = useCallback(async () => {
    if (runningCheckRef.current) {
      return;
    }

    runningCheckRef.current = true;
    try {
      const healthy = await checkHealth();
      if (healthy) {
        // Backend came online - reset startup timer
        if (startupStartTimeRef.current !== null) {
          const elapsedTime = Date.now() - startupStartTimeRef.current;
          console.log(`[BackendLifecycle] Backend became online after ${elapsedTime}ms`);
          startupStartTimeRef.current = null;
        }
        return;
      }

      // Track startup start time on first check failure
      if (startupStartTimeRef.current === null) {
        startupStartTimeRef.current = Date.now();
      }

      await startBackend();
      // After starting, wait a bit then check again
      await wait(1000);
      await checkHealth();
    } finally {
      runningCheckRef.current = false;
    }
  }, [checkHealth, startBackend]);

  useEffect(() => {
    ensureBackend();

    const interval = setInterval(() => {
      ensureBackend();
    }, pollIntervalMs);

    return () => clearInterval(interval);
  }, [ensureBackend, pollIntervalMs]);

  return {
    status,
    refresh: ensureBackend,
  };
}

export type { BackendState };
