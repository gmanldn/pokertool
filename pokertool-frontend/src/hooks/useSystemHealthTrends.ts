/* POKERTOOL-HEADER-START
---
schema: pokerheader.v1
project: pokertool
file: pokertool-frontend/src/hooks/useSystemHealthTrends.ts
version: v1.0.0
last_commit: '2025-10-20T00:00:00Z'
fixes:
- date: '2025-10-20'
  summary: Added reusable hook for loading cached system health history and trend analytics
---
POKERTOOL-HEADER-END */

import { useCallback, useEffect, useRef, useState } from 'react';
import { buildApiUrl } from '../config/api';
import type { HealthStatus } from './useSystemHealth';

export interface HealthHistoryEntry {
  timestamp: string;
  results: Record<string, HealthStatus>;
}

export interface FeatureTrendStats {
  healthy: number;
  degraded: number;
  failing: number;
  unknown: number;
  healthy_pct?: number;
  degraded_pct?: number;
  failing_pct?: number;
  avg_latency_ms?: number | null;
}

export interface HealthTrendsSummary {
  period_hours: number;
  data_points: number;
  start_time: string | null;
  end_time: string | null;
  feature_trends: Record<string, FeatureTrendStats>;
  summary: string;
}

interface UseSystemHealthTrendsOptions {
  autoFetch?: boolean;
}

interface UseSystemHealthTrendsReturn {
  trends: HealthTrendsSummary | null;
  history: HealthHistoryEntry[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

interface TrendsResponse {
  success: boolean;
  timestamp: string;
  trends: HealthTrendsSummary;
}

interface HistoryResponse {
  success: boolean;
  timestamp: string;
  period_hours: number;
  data_points: number;
  history: HealthHistoryEntry[];
}

export const useSystemHealthTrends = (
  hours = 24,
  options: UseSystemHealthTrendsOptions = {}
): UseSystemHealthTrendsReturn => {
  const { autoFetch = true } = options;

  const [trends, setTrends] = useState<HealthTrendsSummary | null>(null);
  const [history, setHistory] = useState<HealthHistoryEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(autoFetch);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    // When no trends loaded yet show loading skeleton
    if (!trends) {
      setLoading(true);
    }
    setRefreshing(true);
    setError(null);

    try {
      const trendUrl = buildApiUrl(`/api/system/health/trends?hours=${hours}`);
      const historyUrl = buildApiUrl(`/api/system/health/history?hours=${hours}`);

      const [trendResponse, historyResponse] = await Promise.all([
        fetch(trendUrl, { signal: controller.signal }),
        fetch(historyUrl, { signal: controller.signal }),
      ]);

      if (!trendResponse.ok) {
        throw new Error(`Trends API returned ${trendResponse.status}`);
      }
      if (!historyResponse.ok) {
        throw new Error(`History API returned ${historyResponse.status}`);
      }

      const trendJson: TrendsResponse = await trendResponse.json();
      const historyJson: HistoryResponse = await historyResponse.json();

      if (controller.signal.aborted) {
        return;
      }

      setTrends(trendJson.trends);
      setHistory(historyJson.history);
    } catch (err) {
      if (controller.signal.aborted) {
        return;
      }

      const message = err instanceof Error ? err.message : String(err);
      setError(`Unable to load health trends: ${message}`);
    } finally {
      if (!controller.signal.aborted) {
        setRefreshing(false);
        setLoading(false);
      }
    }
  }, [hours, trends]);

  useEffect(() => {
    if (!autoFetch) {
      return;
    }

    let mounted = true;
    refresh().catch((error) => {
      if (mounted) {
        console.error('Failed to refresh system health trends', error);
      }
    });

    return () => {
      mounted = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [autoFetch, refresh]);

  return {
    trends,
    history,
    loading,
    refreshing,
    error,
    refresh,
  };
};

export default useSystemHealthTrends;
