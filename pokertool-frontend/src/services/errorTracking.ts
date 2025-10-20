/**
 * Error Tracking Service
 * 
 * Integrates Sentry for frontend error tracking with correlation IDs
 */

import * as Sentry from '@sentry/react';
import type { BrowserOptions } from '@sentry/browser';
import type { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

/**
 * Initialize Sentry error tracking
 */
export function initializeErrorTracking() {
  const sentryDsn = process.env.REACT_APP_SENTRY_DSN;
  
  if (!sentryDsn) {
    console.info('Sentry DSN not configured - error tracking disabled');
    return;
  }

  try {
    Sentry.init({
      dsn: sentryDsn,
      integrations: [
        Sentry.browserTracingIntegration(),
        Sentry.replayIntegration({
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],
      
      // Performance Monitoring
      tracesSampleRate: parseFloat(process.env.REACT_APP_SENTRY_TRACES_SAMPLE_RATE || '0.1'),
      
      // Session Replay
      replaysSessionSampleRate: parseFloat(process.env.REACT_APP_SENTRY_REPLAYS_SESSION_SAMPLE_RATE || '0.1'),
      replaysOnErrorSampleRate: parseFloat(process.env.REACT_APP_SENTRY_REPLAYS_ERROR_SAMPLE_RATE || '1.0'),
      
      environment: process.env.REACT_APP_ENV || process.env.NODE_ENV || 'development',
      release: process.env.REACT_APP_VERSION || 'unknown',
      
      beforeSend(event: Parameters<NonNullable<BrowserOptions['beforeSend']>>[0]) {
        // Add correlation ID from request if available
        const correlationId = getCorrelationId();
        if (correlationId) {
          event.tags = event.tags || {};
          event.tags.correlation_id = correlationId;
        }
        
        return event;
      },
    });

    console.info('Sentry error tracking initialized');
  } catch (error) {
    console.error('Failed to initialize Sentry:', error);
  }
}

/**
 * Get correlation ID from current request context
 */
function getCorrelationId(): string | null {
  // Try to get from response headers in recent API calls
  const correlationId = sessionStorage.getItem('last_correlation_id');
  return correlationId;
}

/**
 * Store correlation ID for error tracking
 */
export function setCorrelationId(correlationId: string) {
  sessionStorage.setItem('last_correlation_id', correlationId);
  Sentry.setTag('correlation_id', correlationId);
}

/**
 * Capture an error with additional context
 */
export function captureError(error: Error, context?: Record<string, any>) {
  if (context) {
    Sentry.setContext('additional_context', context);
  }
  Sentry.captureException(error);
}

/**
 * Capture a message
 */
export function captureMessage(message: string, level: Sentry.SeverityLevel = 'info') {
  Sentry.captureMessage(message, level);
}

/**
 * Set user context
 */
export function setUser(user: { id: string; username?: string; email?: string }) {
  Sentry.setUser(user);
}

/**
 * Clear user context
 */
export function clearUser() {
  Sentry.setUser(null);
}

/**
 * Add breadcrumb for tracking user actions
 */
export function addBreadcrumb(message: string, category?: string, data?: Record<string, any>) {
  Sentry.addBreadcrumb({
    message,
    category: category || 'user-action',
    data,
    level: 'info',
  });
}

/**
 * Axios interceptor to capture correlation IDs from API responses
 */
export function setupAxiosInterceptor(axiosInstance: AxiosInstance) {
  axiosInstance.interceptors.response.use(
    (response: AxiosResponse) => {
      // Extract correlation ID from response headers
      const correlationId = response.headers['x-correlation-id'];
      if (correlationId) {
        setCorrelationId(correlationId);
      }
      return response;
    },
    (error: AxiosError) => {
      // Extract correlation ID even from error responses
      if (error.response?.headers?.['x-correlation-id']) {
        setCorrelationId(error.response.headers['x-correlation-id']);
      }
      return Promise.reject(error);
    }
  );
}

export default {
  initialize: initializeErrorTracking,
  captureError,
  captureMessage,
  setUser,
  clearUser,
  addBreadcrumb,
  setCorrelationId,
  setupAxiosInterceptor,
};
