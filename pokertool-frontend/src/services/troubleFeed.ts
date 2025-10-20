/**
 * Trouble Feed Frontend Error Tracking
 * =====================================
 *
 * Captures frontend errors and sends them to the backend trouble feed
 * for centralized AI-powered error analysis and debugging.
 *
 * Features:
 * - Automatic error boundary integration
 * - Manual error logging
 * - Stack trace capture
 * - Context preservation
 * - Retry logic for network failures
 */

interface FrontendErrorPayload {
  error_type: string;
  error_message: string;
  stack_trace: string;
  component: string;
  severity: 'WARNING' | 'ERROR' | 'CRITICAL';
  context: Record<string, unknown>;
  url?: string;
  user_agent?: string;
}

interface ErrorContext {
  component?: string;
  props?: Record<string, unknown>;
  state?: Record<string, unknown>;
  route?: string;
  [key: string]: unknown;
}

class TroubleFeedTracker {
  private endpoint: string;
  private enabled: boolean;
  private queue: FrontendErrorPayload[] = [];
  private processing = false;
  private maxQueueSize = 50;
  private retryDelay = 5000; // 5 seconds

  constructor() {
    this.endpoint = process.env.REACT_APP_API_URL || 'http://localhost:5001';
    this.enabled = (process.env.REACT_APP_TROUBLE_FEED_ENABLED || 'true').toLowerCase() !== 'false';

    if (this.enabled) {
      this.setupGlobalErrorHandler();
      this.setupUnhandledRejectionHandler();
    }
  }

  /**
   * Setup global error handler to catch uncaught errors
   */
  private setupGlobalErrorHandler() {
    window.addEventListener('error', (event) => {
      this.captureError(
        event.error || new Error(event.message),
        {
          component: 'Global',
          url: window.location.href,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
        'ERROR'
      );
    });
  }

  /**
   * Setup unhandled promise rejection handler
   */
  private setupUnhandledRejectionHandler() {
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError(
        event.reason instanceof Error ? event.reason : new Error(String(event.reason)),
        {
          component: 'Promise',
          url: window.location.href,
          promise: String(event.promise),
        },
        'ERROR'
      );
    });
  }

  /**
   * Capture and log an error to the trouble feed
   */
  public captureError(
    error: Error,
    context: ErrorContext = {},
    severity: 'WARNING' | 'ERROR' | 'CRITICAL' = 'ERROR'
  ): void {
    if (!this.enabled) {
      console.warn('[TroubleFeed] Disabled - error not logged:', error);
      return;
    }

    try {
      const payload: FrontendErrorPayload = {
        error_type: error.name || 'Error',
        error_message: error.message || 'Unknown error',
        stack_trace: error.stack || new Error().stack || 'No stack trace available',
        component: context.component || 'Unknown',
        severity,
        context: {
          ...context,
          route: window.location.pathname,
          timestamp: new Date().toISOString(),
        },
        url: window.location.href,
        user_agent: navigator.userAgent,
      };

      // Add to queue
      this.enqueue(payload);

      // Log to console in development
      if (process.env.NODE_ENV !== 'production') {
        console.error('[TroubleFeed] Captured error:', {
          type: payload.error_type,
          message: payload.error_message,
          component: payload.component,
          context: payload.context,
        });
      }
    } catch (captureError) {
      console.error('[TroubleFeed] Failed to capture error:', captureError);
    }
  }

  /**
   * Capture a warning
   */
  public captureWarning(
    message: string,
    context: ErrorContext = {}
  ): void {
    this.captureError(
      new Error(message),
      context,
      'WARNING'
    );
  }

  /**
   * Capture a critical error
   */
  public captureCritical(
    error: Error,
    context: ErrorContext = {}
  ): void {
    this.captureError(error, context, 'CRITICAL');
  }

  /**
   * Add error to queue and trigger processing
   */
  private enqueue(payload: FrontendErrorPayload): void {
    // Prevent queue overflow
    if (this.queue.length >= this.maxQueueSize) {
      console.warn('[TroubleFeed] Queue full, dropping oldest error');
      this.queue.shift();
    }

    this.queue.push(payload);
    this.processQueue();
  }

  /**
   * Process the error queue
   */
  private async processQueue(): Promise<void> {
    if (this.processing || this.queue.length === 0) {
      return;
    }

    this.processing = true;

    while (this.queue.length > 0) {
      const payload = this.queue[0];

      try {
        await this.sendToBackend(payload);
        // Success - remove from queue
        this.queue.shift();
      } catch (error) {
        console.error('[TroubleFeed] Failed to send error to backend:', error);
        // Keep in queue and retry later
        break;
      }
    }

    this.processing = false;

    // If there are still items in queue, retry after delay
    if (this.queue.length > 0) {
      setTimeout(() => this.processQueue(), this.retryDelay);
    }
  }

  /**
   * Send error payload to backend
   */
  private async sendToBackend(payload: FrontendErrorPayload): Promise<void> {
    const url = `${this.endpoint}/api/errors/frontend`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      // Use keepalive to ensure errors are sent even during page unload
      keepalive: true,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }

  /**
   * Flush all pending errors (useful before page unload)
   */
  public async flush(): Promise<void> {
    await this.processQueue();
  }

  /**
   * Get current queue size
   */
  public getQueueSize(): number {
    return this.queue.length;
  }
}

// Global instance
const troubleFeed = new TroubleFeedTracker();

// Export convenience functions
export const captureError = (error: Error, context?: ErrorContext) =>
  troubleFeed.captureError(error, context);

export const captureWarning = (message: string, context?: ErrorContext) =>
  troubleFeed.captureWarning(message, context);

export const captureCritical = (error: Error, context?: ErrorContext) =>
  troubleFeed.captureCritical(error, context);

export const flushErrors = () => troubleFeed.flush();

export default troubleFeed;

// Flush errors before page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    troubleFeed.flush();
  });
}
