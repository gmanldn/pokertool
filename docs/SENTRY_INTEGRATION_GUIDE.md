# Sentry Integration Guide

**Version**: 88.6.0+
**Date**: 2025-10-23
**Status**: Production Ready

This guide covers the Sentry error tracking integration in PokerTool, including setup, configuration, and best practices.

---

## Overview

PokerTool integrates Sentry for comprehensive error tracking and performance monitoring across both frontend and backend.

### Features

- ✅ **Frontend Error Tracking**: React error boundaries and global handlers
- ✅ **Browser Tracing**: Performance monitoring for page loads and interactions
- ✅ **Session Replay**: Visual reproduction of user sessions
- ✅ **Correlation IDs**: Link frontend and backend errors
- ✅ **Source Maps**: Readable stack traces in production
- ✅ **Custom Context**: User, session, and application metadata

---

## Quick Start

### 1. Get Sentry DSN

1. Create account at [sentry.io](https://sentry.io)
2. Create new project (React for frontend, Python for backend)
3. Copy your DSN (looks like `https://key@sentry.io/project`)

### 2. Configure Environment

```bash
# Frontend Sentry DSN
export REACT_APP_SENTRY_DSN=https://your-frontend-key@sentry.io/frontend-project

# Backend Sentry DSN (optional, for future backend integration)
export SENTRY_DSN=https://your-backend-key@sentry.io/backend-project

# Environment (production, staging, development)
export SENTRY_ENVIRONMENT=production

# Release version (optional, for tracking deployments)
export SENTRY_RELEASE=v88.6.0
```

### 3. Start Application

```bash
# Sentry will automatically initialize if REACT_APP_SENTRY_DSN is set
python3 start.py
```

---

## Configuration

### Environment Variables

#### `REACT_APP_SENTRY_DSN` (Required)

**Description**: Sentry Data Source Name for frontend error tracking

**Format**: `https://public_key@sentry.io/project_id`

**Example**:
```bash
export REACT_APP_SENTRY_DSN=https://abc123def456@o123456.ingest.sentry.io/7890123
```

**Where to find it**: Sentry Project Settings → Client Keys (DSN)

#### `SENTRY_ENVIRONMENT` (Optional)

**Description**: Environment name for filtering errors

**Default**: `development`

**Values**: `production`, `staging`, `development`, custom

**Example**:
```bash
export SENTRY_ENVIRONMENT=production
```

#### `SENTRY_RELEASE` (Optional)

**Description**: Release version for tracking deployments

**Format**: Semantic version or git commit hash

**Example**:
```bash
export SENTRY_RELEASE=v88.6.0
# Or
export SENTRY_RELEASE=$(git rev-parse --short HEAD)
```

#### `SENTRY_TRACES_SAMPLE_RATE` (Optional)

**Description**: Percentage of transactions to track for performance

**Default**: `0.1` (10%)

**Range**: `0.0` to `1.0`

**Example**:
```bash
# Track 50% of transactions
export SENTRY_TRACES_SAMPLE_RATE=0.5

# Track all transactions (not recommended in production)
export SENTRY_TRACES_SAMPLE_RATE=1.0

# Disable performance tracking
export SENTRY_TRACES_SAMPLE_RATE=0.0
```

#### `SENTRY_REPLAYS_SESSION_SAMPLE_RATE` (Optional)

**Description**: Percentage of normal sessions to replay

**Default**: `0.1` (10%)

**Range**: `0.0` to `1.0`

**Example**:
```bash
# Replay 20% of sessions
export SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.2
```

#### `SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE` (Optional)

**Description**: Percentage of error sessions to replay

**Default**: `1.0` (100%)

**Range**: `0.0` to `1.0`

**Example**:
```bash
# Replay all sessions with errors
export SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE=1.0

# Replay 50% of error sessions
export SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE=0.5
```

---

## Frontend Integration

### Initialization

Sentry is automatically initialized in `pokertool-frontend/src/index.tsx`:

```typescript
import * as Sentry from "@sentry/react";

if (process.env.REACT_APP_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.REACT_APP_SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
    ],
    environment: process.env.SENTRY_ENVIRONMENT || 'development',
    release: process.env.SENTRY_RELEASE,
    tracesSampleRate: parseFloat(process.env.SENTRY_TRACES_SAMPLE_RATE || '0.1'),
    replaysSessionSampleRate: parseFloat(process.env.SENTRY_REPLAYS_SESSION_SAMPLE_RATE || '0.1'),
    replaysOnErrorSampleRate: parseFloat(process.env.SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE || '1.0'),

    beforeSend(event) {
      // Add correlation ID for linking with backend
      if (event.contexts) {
        event.contexts.correlation = {
          correlation_id: generateCorrelationId(),
        };
      }
      return event;
    },
  });
}
```

### Manual Error Reporting

```typescript
import * as Sentry from "@sentry/react";

// Capture exception
try {
  riskyOperation();
} catch (error) {
  Sentry.captureException(error);
}

// Capture message
Sentry.captureMessage("Something went wrong", "error");

// Add context
Sentry.setUser({ id: userId, email: userEmail });
Sentry.setTag("feature", "autopilot");
Sentry.setContext("game_state", { hand: "AsKh", pot: 100 });
```

### Error Boundaries

Wrap components with Sentry error boundaries:

```typescript
import * as Sentry from "@sentry/react";

function App() {
  return (
    <Sentry.ErrorBoundary fallback={<ErrorFallback />}>
      <YourApp />
    </Sentry.ErrorBoundary>
  );
}
```

---

## Features in Detail

### 1. Browser Tracing

Automatically tracks:
- Page loads
- Navigation timing
- API request duration
- User interactions

**Configuration:**
```typescript
Sentry.browserTracingIntegration({
  // Track specific routes
  routingInstrumentation: Sentry.reactRouterV6Instrumentation(
    React.useEffect,
    useLocation,
    useNavigationType,
    createRoutesFromChildren,
    matchRoutes
  ),
})
```

### 2. Session Replay

Records user sessions for debugging:
- DOM snapshots
- User interactions
- Console logs
- Network requests

**Configuration:**
```typescript
Sentry.replayIntegration({
  maskAllText: false,        // Don't mask text (be careful with sensitive data)
  blockAllMedia: false,      // Don't block images/videos
  maskAllInputs: true,       // Mask input fields (recommended)
})
```

**Privacy Considerations:**
- Mask sensitive data (passwords, credit cards)
- Review privacy policy implications
- Consider GDPR compliance

### 3. Correlation IDs

Link frontend and backend errors:

```typescript
// Generate correlation ID
const correlationId = `${Date.now()}-${Math.random().toString(36)}`;

// Send with API request
fetch('/api/endpoint', {
  headers: {
    'X-Correlation-ID': correlationId
  }
});

// Attach to Sentry event
Sentry.setContext("correlation", { correlation_id: correlationId });
```

### 4. Performance Monitoring

Track custom operations:

```typescript
const transaction = Sentry.startTransaction({
  name: "Hand Analysis",
  op: "poker.analysis"
});

try {
  await analyzeHand(hand);
  transaction.setStatus("ok");
} catch (error) {
  transaction.setStatus("error");
  throw error;
} finally {
  transaction.finish();
}
```

### 5. Custom Context

Add metadata to errors:

```typescript
// User context
Sentry.setUser({
  id: userId,
  username: username,
  email: email,
  ip_address: "{{auto}}"  // Auto-capture IP
});

// Tags (for filtering)
Sentry.setTag("table_id", tableId);
Sentry.setTag("game_type", "NLH");
Sentry.setTag("stake_level", "high");

// Custom context
Sentry.setContext("game_state", {
  hand: "AsKh",
  board: "Qh9c2d",
  pot: 100,
  position: "BTN",
  stack: 500
});

// Breadcrumbs (event trail)
Sentry.addBreadcrumb({
  category: "poker",
  message: "Player folded",
  level: "info",
  data: { hand: "AsKh", pot: 100 }
});
```

---

## Testing Sentry Integration

### 1. Test Error Capture

```typescript
// Add test button to development UI
<button onClick={() => {
  throw new Error("Sentry test error");
}}>
  Test Sentry
</button>
```

### 2. Verify in Sentry Dashboard

1. Go to your Sentry project
2. Check Issues tab
3. Look for test error
4. Verify source maps work (readable stack traces)
5. Check session replay (if enabled)

### 3. Test Performance Tracking

```typescript
// Generate test transaction
const transaction = Sentry.startTransaction({
  name: "Test Transaction",
  op: "test"
});

setTimeout(() => {
  transaction.finish();
}, 1000);
```

Check Performance tab in Sentry dashboard.

---

## Source Maps

### Why Source Maps Matter

Without source maps, production errors show minified code:
```
Error at Object.a (chunk.abc123.js:1:2345)
```

With source maps:
```
Error at analyzeHand (HandAnalysis.tsx:45:12)
```

### Configuring Source Maps

**Option 1: Upload to Sentry (Recommended)**

```bash
# Install Sentry CLI
npm install -g @sentry/cli

# Configure auth token
export SENTRY_AUTH_TOKEN=your_auth_token

# Upload source maps after build
sentry-cli sourcemaps upload \
  --org your-org \
  --project your-project \
  --release $SENTRY_RELEASE \
  ./build
```

**Option 2: Inline Source Maps (Development)**

Already configured in `package.json`:
```json
{
  "scripts": {
    "build": "GENERATE_SOURCEMAP=true react-scripts build"
  }
}
```

### Webpack Plugin (Alternative)

```javascript
// webpack.config.js
const SentryWebpackPlugin = require("@sentry/webpack-plugin");

module.exports = {
  plugins: [
    new SentryWebpackPlugin({
      org: "your-org",
      project: "your-project",
      authToken: process.env.SENTRY_AUTH_TOKEN,
      include: "./build",
      release: process.env.SENTRY_RELEASE,
    }),
  ],
};
```

---

## Best Practices

### 1. Error Filtering

**Filter noise:**
```typescript
beforeSend(event, hint) {
  // Ignore certain errors
  if (event.exception) {
    const error = hint.originalException;
    if (error instanceof ChunkLoadError) {
      return null;  // Don't send
    }
  }

  // Filter by environment
  if (process.env.NODE_ENV === 'development') {
    console.log("Would send to Sentry:", event);
    return null;  // Don't send in dev
  }

  return event;
}
```

### 2. Sampling Strategy

**Production:**
```bash
# Capture all errors, sample performance
SENTRY_TRACES_SAMPLE_RATE=0.1              # 10% of transactions
SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.05    # 5% of sessions
SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE=1.0    # 100% of error sessions
```

**Staging:**
```bash
# Higher sampling for testing
SENTRY_TRACES_SAMPLE_RATE=0.5
SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.2
```

**Development:**
```bash
# Don't send to Sentry in development
# Or use separate development project
SENTRY_ENVIRONMENT=development
```

### 3. Context Management

```typescript
// Add context at app initialization
Sentry.setContext("app_info", {
  version: APP_VERSION,
  build: BUILD_NUMBER,
  commit: GIT_COMMIT
});

// Add context per feature
function PokerTable() {
  useEffect(() => {
    Sentry.setTag("feature", "poker_table");
    return () => {
      Sentry.setTag("feature", null);
    };
  }, []);
}
```

### 4. Performance Budget

Monitor bundle size impact:
```bash
# Sentry packages add ~50KB gzipped
@sentry/react: ~45KB
@sentry/tracing: ~5KB
```

Consider lazy loading:
```typescript
// Load Sentry only in production
const Sentry = process.env.NODE_ENV === 'production'
  ? await import('@sentry/react')
  : null;
```

### 5. Privacy & GDPR

**Mask sensitive data:**
```typescript
beforeSend(event) {
  // Remove sensitive data
  if (event.request?.data) {
    delete event.request.data.password;
    delete event.request.data.creditCard;
  }

  // Mask email addresses
  if (event.user?.email) {
    event.user.email = event.user.email.replace(/@.+/, '@***');
  }

  return event;
}
```

**Session Replay:**
```typescript
Sentry.replayIntegration({
  maskAllText: true,        // Mask all text content
  maskAllInputs: true,      // Mask all input fields
  blockAllMedia: true,      // Block images/videos
  maskTextSelector: '.sensitive',  // Mask specific elements
})
```

---

## Troubleshooting

### Problem: No errors appearing in Sentry

**Check:**
1. DSN is set: `echo $REACT_APP_SENTRY_DSN`
2. Environment: Sentry might be disabled in development
3. Network: Check browser DevTools for Sentry requests
4. Filters: Check `beforeSend` isn't filtering everything

**Debug:**
```typescript
// Enable debug mode
Sentry.init({
  debug: true,  // Logs all Sentry activity
  // ...
});
```

### Problem: Source maps not working

**Check:**
1. Source maps generated: `ls build/static/js/*.map`
2. Uploaded to Sentry: Check Releases tab
3. Release matches: `SENTRY_RELEASE` matches uploaded version

**Fix:**
```bash
# Rebuild with source maps
GENERATE_SOURCEMAP=true npm run build

# Upload to Sentry
sentry-cli sourcemaps upload --release $SENTRY_RELEASE ./build
```

### Problem: Too many events

**Solution:**
Adjust sampling rates:
```bash
# Reduce sampling
export SENTRY_TRACES_SAMPLE_RATE=0.05      # 5% instead of 10%
export SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.01  # 1% instead of 10%
```

Or add filters:
```typescript
beforeSend(event) {
  // Only send critical errors
  if (event.level !== 'error' && event.level !== 'fatal') {
    return null;
  }
  return event;
}
```

### Problem: Performance impact

**Solution:**
1. Reduce sampling rates
2. Disable replays: `SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0`
3. Lazy load Sentry in production only
4. Use `beforeSend` to filter events

---

## Monitoring & Alerts

### 1. Create Alerts

In Sentry dashboard:
1. Go to Alerts → Create Alert
2. Choose trigger (e.g., "Error rate exceeds 10%")
3. Set action (email, Slack, PagerDuty)

**Example alerts:**
- Error rate > 10% in 5 minutes
- New issue type detected
- Performance degradation > 50%
- Memory usage > 500MB

### 2. Dashboard Widgets

Monitor key metrics:
- Error frequency over time
- Most common errors
- Affected users
- Performance by route
- Release comparison

### 3. Integrations

Connect Sentry with:
- **Slack**: Real-time error notifications
- **GitHub**: Link issues to code
- **Jira**: Create tickets from errors
- **PagerDuty**: On-call alerting

---

## Cost Management

Sentry pricing based on:
- Events per month
- Replays per month
- Data retention

### Free Tier (Developer)
- 5,000 errors/month
- 1 project
- 30-day retention

### Paid Tiers
- Team: $26/month + usage
- Business: $80/month + usage

### Optimization Tips

1. **Use sampling** to reduce events
2. **Filter noise** with `beforeSend`
3. **Adjust retention** (7 days vs 90 days)
4. **Use quota management** to cap costs
5. **Archive old projects** you don't need

---

## Summary

✅ **Setup**: Configure `REACT_APP_SENTRY_DSN`
✅ **Features**: Error tracking, performance monitoring, session replay
✅ **Integration**: Automatic initialization, manual capture, error boundaries
✅ **Best Practices**: Sampling, filtering, context, privacy
✅ **Troubleshooting**: Debug mode, source maps, sampling adjustment

For more details:
- [Sentry React Docs](https://docs.sentry.io/platforms/javascript/guides/react/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Session Replay](https://docs.sentry.io/product/session-replay/)

---

**Last Updated:** 2025-10-23
**Version:** 88.6.0+
**Maintained By:** PokerTool Development Team
