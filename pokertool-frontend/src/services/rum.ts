import { getCLS, getFCP, getFID, getLCP, getTTFB, type Metric } from 'web-vitals';

type RumOptions = {
  endpoint: string;
  enabled: boolean;
  sampleRate: number;
  environment?: string;
  release?: string;
};

type RumPayload = {
  metric: string;
  value: number;
  delta?: number | null;
  rating?: string | null;
  session_id?: string;
  navigation_type?: string;
  page?: string;
  client_timestamp?: string;
  app_version?: string;
  environment?: Record<string, unknown>;
  attribution?: Record<string, unknown>;
  trace_id?: string;
  span_id?: string;
};

const SESSION_STORAGE_KEY = 'pokertool_rum_session';
const SAMPLE_STORAGE_KEY = 'pokertool_rum_sampled';

const DEFAULT_OPTIONS: RumOptions = {
  endpoint: process.env.REACT_APP_RUM_ENDPOINT || '/api/rum/metrics',
  enabled: (process.env.REACT_APP_RUM_ENABLED || 'true').toLowerCase() !== 'false',
  sampleRate: parseFloat(process.env.REACT_APP_RUM_SAMPLE_RATE || '1.0'),
  environment: process.env.REACT_APP_ENV || process.env.NODE_ENV,
  release: process.env.REACT_APP_VERSION,
};

function getSessionId(): string {
  if (typeof window === 'undefined' || !window.sessionStorage) {
    return '';
  }
  const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) {
    return existing;
  }
  const newId = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  window.sessionStorage.setItem(SESSION_STORAGE_KEY, newId);
  return newId;
}

function shouldSample(sampleRate: number): boolean {
  if (sampleRate <= 0) {
    return false;
  }
  if (sampleRate >= 1) {
    return true;
  }
  if (typeof window === 'undefined' || !window.sessionStorage) {
    return Math.random() < sampleRate;
  }
  const stored = window.sessionStorage.getItem(SAMPLE_STORAGE_KEY);
  if (stored !== null) {
    return stored === '1';
  }
  const sampled = Math.random() < sampleRate;
  window.sessionStorage.setItem(SAMPLE_STORAGE_KEY, sampled ? '1' : '0');
  return sampled;
}

function serializeAttribution(metric: Metric): Record<string, unknown> {
  const attribution: Record<string, unknown> = {};
  const value = (metric as Metric & { attribution?: Record<string, unknown> }).attribution;
  if (!value) {
    return attribution;
  }

  if (typeof value.largestShiftValue === 'number') {
    attribution.largestShiftValue = Number(value.largestShiftValue.toFixed(4));
  }
  if (value.largestShiftTarget) {
    attribution.largestShiftTarget = String(value.largestShiftTarget).slice(0, 160);
  }
  if (value.largestContentfulPaintElement) {
    attribution.largestContentfulPaintElement = String(value.largestContentfulPaintElement).slice(0, 160);
  }
  if (typeof value.timeToFirstByte === 'number') {
    attribution.timeToFirstByte = Number(value.timeToFirstByte.toFixed(2));
  }
  if (value.interactionTarget) {
    attribution.interactionTarget = String(value.interactionTarget).slice(0, 160);
  }
  if (typeof value.interactionTime === 'number') {
    attribution.interactionTime = Number(value.interactionTime.toFixed(2));
  }
  if (value.eventTarget) {
    attribution.eventTarget = String(value.eventTarget).slice(0, 160);
  }
  return attribution;
}

function buildEnvironment(options: RumOptions): Record<string, unknown> {
  if (typeof window === 'undefined' || typeof navigator === 'undefined') {
    return {};
  }
  const userAgentData = (navigator as Navigator & { userAgentData?: { mobile?: boolean } }).userAgentData;
  return {
    environment: options.environment,
    release: options.release,
    platform: navigator.platform,
    device: userAgentData?.mobile ? 'mobile' : 'desktop',
    language: navigator.language,
  };
}

function sendPayload(endpoint: string, payload: RumPayload) {
  const body = JSON.stringify(payload);
  if (navigator.sendBeacon) {
    try {
      const blob = new Blob([body], { type: 'application/json' });
      if (navigator.sendBeacon(endpoint, blob)) {
        return;
      }
    } catch {
      // Fallback to fetch below
    }
  }

  try {
    void fetch(endpoint, {
      method: 'POST',
      body,
      keepalive: true,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    // Silently swallow; RUM should never break the app
  }
}

function reportMetric(metric: Metric, options: RumOptions, sessionId: string) {
  if (!Number.isFinite(metric.value)) {
    return;
  }

  const metricWithExtras = metric as Metric & { rating?: string; navigationType?: string };
  const payload: RumPayload = {
    metric: metric.name,
    value: Number(metric.value.toFixed(4)),
    delta: metric.delta != null ? Number(metric.delta.toFixed(4)) : undefined,
    rating: metricWithExtras.rating || null,
    session_id: sessionId || undefined,
    navigation_type: metricWithExtras.navigationType,
    page: typeof window !== 'undefined' ? window.location.pathname : undefined,
    client_timestamp: new Date().toISOString(),
    app_version: options.release,
    environment: buildEnvironment(options),
    attribution: serializeAttribution(metric),
  };

  sendPayload(options.endpoint, payload);
}

function reportNavigationTiming(options: RumOptions, sessionId: string) {
  if (typeof performance === 'undefined' || typeof performance.getEntriesByType !== 'function') {
    return;
  }
  const [navigation] = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[];
  if (!navigation) {
    return;
  }

  const payload: RumPayload = {
    metric: 'NAVIGATION',
    value: Number(navigation.duration.toFixed(2)),
    rating: null,
    session_id: sessionId || undefined,
    navigation_type: navigation.type,
    page: typeof window !== 'undefined' ? window.location.pathname : undefined,
    client_timestamp: new Date().toISOString(),
    app_version: options.release,
    environment: buildEnvironment(options),
    attribution: {
      domContentLoaded: Number(navigation.domContentLoadedEventEnd.toFixed(2)),
      loadEventEnd: Number(navigation.loadEventEnd.toFixed(2)),
      transferSize: navigation.transferSize,
    },
  };

  sendPayload(options.endpoint, payload);
}

export function initializeRUM(customOptions?: Partial<RumOptions>) {
  if (typeof window === 'undefined') {
    return;
  }

  const options: RumOptions = {
    ...DEFAULT_OPTIONS,
    ...customOptions,
  };

  if (!options.enabled) {
    return;
  }

  options.sampleRate = Number.isFinite(options.sampleRate) ? Math.min(Math.max(options.sampleRate, 0), 1) : 1;
  if (!shouldSample(options.sampleRate)) {
    return;
  }

  const sessionId = getSessionId();

  try {
    const handler = (metric: Metric) => reportMetric(metric, options, sessionId);
    getCLS(handler);
    getLCP(handler);
    getFID(handler);
    getTTFB(handler);
    getFCP(handler);
    reportNavigationTiming(options, sessionId);
  } catch (error) {
    if (process.env.NODE_ENV !== 'production') {
      console.warn('RUM initialisation failed', error);
    }
  }
}

export default {
  initialize: initializeRUM,
};
