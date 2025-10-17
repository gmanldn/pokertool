# PokerTool Environment Variables Documentation

Complete reference for all environment variables used in PokerTool.

## Table of Contents
- [Required Variables](#required-variables)
- [Optional Variables](#optional-variables)
- [Development Variables](#development-variables)
- [Production Variables](#production-variables)
- [Feature Flags](#feature-flags)
- [Third-Party Integrations](#third-party-integrations)

---

## Required Variables

### Database Configuration

```bash
# Database connection string
DATABASE_URL=postgresql://user:password@localhost:5432/pokertool
# Example: postgresql://pokertool_user:secure_password@localhost:5432/pokertool_db

# Database pool size (default: 20)
DB_POOL_SIZE=20

# Database pool timeout in seconds (default: 30)
DB_POOL_TIMEOUT=30
```

### API Configuration

```bash
# API server host (default: 0.0.0.0)
API_HOST=0.0.0.0

# API server port (default: 5001)
API_PORT=5001

# API secret key for JWT tokens (REQUIRED in production)
API_SECRET_KEY=your-secret-key-here-min-32-chars

# CORS allowed origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5001
```

### Frontend Configuration

```bash
# Frontend dev server port (default: 3000)
REACT_APP_PORT=3000

# Backend API URL for frontend
REACT_APP_API_URL=http://localhost:5001

# WebSocket URL for real-time updates
REACT_APP_WS_URL=ws://localhost:5001/ws
```

---

## Optional Variables

### Logging Configuration

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
LOG_LEVEL=INFO

# Log file path (default: logs/pokertool.log)
LOG_FILE_PATH=logs/pokertool.log

# Enable structured JSON logging (default: false)
JSON_LOGGING=false

# Log rotation max bytes (default: 10MB)
LOG_MAX_BYTES=10485760

# Log backup count (default: 5)
LOG_BACKUP_COUNT=5
```

### Performance Tuning

```bash
# Thread pool workers for screen scraping (default: 20)
SCRAPER_WORKERS=20

# OCR strategy limit (default: 3)
OCR_MAX_STRATEGIES=3

# Image hash cache size (default: 1000)
IMAGE_HASH_CACHE_SIZE=1000

# State queue max size (default: 5)
STATE_QUEUE_SIZE=5

# GUI update throttle interval in ms (default: 500)
GUI_UPDATE_INTERVAL=500
```

### Cache Configuration

```bash
# Redis URL for caching (optional)
REDIS_URL=redis://localhost:6379/0

# Cache TTL in seconds (default: 300 = 5 minutes)
CACHE_TTL=300

# Enable cache compression (default: true)
CACHE_COMPRESSION=true
```

---

## Development Variables

### Debug & Testing

```bash
# Enable debug mode (DO NOT USE IN PRODUCTION)
DEBUG=true

# Enable hot reload for development
HOT_RELOAD=true

# Skip authentication in development
SKIP_AUTH=false

# Mock external services
MOCK_SERVICES=false

# Test database URL
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pokertool_test
```

### Development Tools

```bash
# Enable React DevTools
REACT_APP_ENABLE_DEVTOOLS=true

# Enable Redux DevTools
REACT_APP_ENABLE_REDUX_DEVTOOLS=true

# Source maps in production (default: false)
GENERATE_SOURCEMAP=false

# Webpack bundle analyzer
ANALYZE_BUNDLE=false
```

---

## Production Variables

### Security

```bash
# HTTPS enforcement (default: true in production)
HTTPS_ONLY=true

# Secure cookie flag (default: true in production)
SECURE_COOKIES=true

# HSTS max age in seconds (default: 31536000 = 1 year)
HSTS_MAX_AGE=31536000

# Content Security Policy
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline'"

# Rate limiting enabled (default: true)
RATE_LIMITING_ENABLED=true

# Rate limit: requests per minute (default: 60)
RATE_LIMIT_PER_MINUTE=60
```

### Monitoring & Observability

```bash
# Sentry DSN for error tracking
SENTRY_DSN=https://your-sentry-dsn

# Sentry environment
SENTRY_ENVIRONMENT=production

# Sentry sample rate (0.0 to 1.0, default: 1.0)
SENTRY_SAMPLE_RATE=1.0

# Enable performance monitoring
ENABLE_PERFORMANCE_MONITORING=true

# Metrics export interval in seconds (default: 60)
METRICS_EXPORT_INTERVAL=60
```

### Deployment

```bash
# Node environment (development, production, test)
NODE_ENV=production

# Python environment
PYTHON_ENV=production

# Build ID for versioning
BUILD_ID=1.0.0

# Deployment timestamp
DEPLOY_TIMESTAMP=2025-10-17T12:00:00Z

# Health check endpoint enabled
HEALTH_CHECK_ENABLED=true
```

---

## Feature Flags

Enable/disable specific features:

```bash
# Betfair scraping accuracy improvements
FEATURE_BETFAIR_ACCURACY=true

# System health monitor dashboard
FEATURE_HEALTH_MONITOR=true

# Active learning feedback loop
FEATURE_ACTIVE_LEARNING=true

# Model calibration system
FEATURE_MODEL_CALIBRATION=true

# Sequential opponent fusion
FEATURE_OPPONENT_FUSION=true

# Multi-table support
FEATURE_MULTI_TABLE=false

# Voice commands
FEATURE_VOICE_COMMANDS=false

# Hand replay system
FEATURE_HAND_REPLAY=true

# Gamification (badges, achievements)
FEATURE_GAMIFICATION=true

# Community features (sharing, forums)
FEATURE_COMMUNITY=false
```

---

## Third-Party Integrations

### Chrome DevTools Protocol

```bash
# Chrome DevTools port (default: 9222)
CHROME_DEVTOOLS_PORT=9222

# Chrome executable path (auto-detected if not set)
CHROME_EXECUTABLE_PATH=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome

# Chrome debug profile path
CHROME_DEBUG_PROFILE=~/.pokertool/chrome-debug-profile

# Auto-launch Chrome (default: true)
CHROME_AUTO_LAUNCH=true
```

### OCR & Computer Vision

```bash
# Tesseract executable path (auto-detected if not set)
TESSERACT_PATH=/usr/local/bin/tesseract

# Tesseract data path
TESSDATA_PREFIX=/usr/local/share/tessdata

# OpenCV version check
OPENCV_VERSION_CHECK=true
```

### Email (Optional)

```bash
# SMTP server for email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Email sender
EMAIL_FROM=noreply@pokertool.com
```

### Slack (Optional)

```bash
# Slack webhook for notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Slack channel for alerts
SLACK_ALERT_CHANNEL=#pokertool-alerts
```

---

## Environment-Specific Examples

### `.env.development`

```bash
# Development environment configuration
NODE_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Local services
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pokertool_dev
REDIS_URL=redis://localhost:6379/0

# API
API_SECRET_KEY=dev-secret-key-not-for-production
API_HOST=0.0.0.0
API_PORT=5001

# Frontend
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=ws://localhost:5001/ws

# Development tools
REACT_APP_ENABLE_DEVTOOLS=true
HOT_RELOAD=true

# Feature flags (all enabled for testing)
FEATURE_BETFAIR_ACCURACY=true
FEATURE_HEALTH_MONITOR=true
FEATURE_ACTIVE_LEARNING=true
```

### `.env.production`

```bash
# Production environment configuration
NODE_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Production database (use secret management in real deployment)
DATABASE_URL=${PRODUCTION_DATABASE_URL}
REDIS_URL=${PRODUCTION_REDIS_URL}

# API (use strong secrets)
API_SECRET_KEY=${API_SECRET_KEY}
API_HOST=0.0.0.0
API_PORT=5001

# Frontend
REACT_APP_API_URL=https://api.pokertool.com
REACT_APP_WS_URL=wss://api.pokertool.com/ws

# Security
HTTPS_ONLY=true
SECURE_COOKIES=true
RATE_LIMITING_ENABLED=true

# Monitoring
SENTRY_DSN=${SENTRY_DSN}
SENTRY_ENVIRONMENT=production
ENABLE_PERFORMANCE_MONITORING=true

# Feature flags (controlled rollout)
FEATURE_BETFAIR_ACCURACY=true
FEATURE_HEALTH_MONITOR=true
FEATURE_ACTIVE_LEARNING=false  # Beta feature
FEATURE_MULTI_TABLE=false  # Not ready yet
```

### `.env.test`

```bash
# Test environment configuration
NODE_ENV=test
DEBUG=false
LOG_LEVEL=WARNING

# Test database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pokertool_test
REDIS_URL=redis://localhost:6379/1

# API
API_SECRET_KEY=test-secret-key
API_HOST=127.0.0.1
API_PORT=5002

# Mock services
MOCK_SERVICES=true
SKIP_AUTH=true

# Disable external integrations
CHROME_AUTO_LAUNCH=false
SENTRY_DSN=  # Disabled
```

---

## Loading Environment Variables

### Python (Backend)

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Access variables
database_url = os.getenv('DATABASE_URL')
api_port = int(os.getenv('API_PORT', '5001'))
debug = os.getenv('DEBUG', 'false').lower() == 'true'
```

### TypeScript/React (Frontend)

```typescript
// All React environment variables must start with REACT_APP_

// Access in code
const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5001';
const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:5001/ws';
const enableDevtools = process.env.REACT_APP_ENABLE_DEVTOOLS === 'true';

// In package.json scripts
{
  "scripts": {
    "start": "REACT_APP_ENV=development react-scripts start",
    "build": "REACT_APP_ENV=production react-scripts build"
  }
}
```

---

## Validation & Troubleshooting

### Validating Configuration

Run the validation script to check all required environment variables:

```bash
python3 scripts/validate_env.py
```

### Common Issues

**Issue**: `DATABASE_URL not set`
**Solution**: Create a `.env` file in the project root with `DATABASE_URL=...`

**Issue**: `CORS errors in frontend`
**Solution**: Ensure `CORS_ORIGINS` includes your frontend URL (e.g., `http://localhost:3000`)

**Issue**: `WebSocket connection failed`
**Solution**: Check `REACT_APP_WS_URL` matches your backend WebSocket endpoint

**Issue**: `Chrome DevTools connection timeout`
**Solution**: Verify Chrome is running with remote debugging enabled on port `CHROME_DEVTOOLS_PORT`

### Environment Variable Precedence

1. System environment variables (highest priority)
2. `.env.local` file (local overrides, not in git)
3. `.env.{NODE_ENV}` file (environment-specific)
4. `.env` file (default values)
5. Code defaults (lowest priority)

---

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong, random values** for `API_SECRET_KEY` (minimum 32 characters)
3. **Rotate secrets regularly** (every 90 days recommended)
4. **Use secret management** in production (AWS Secrets Manager, HashiCorp Vault, etc.)
5. **Restrict environment variable access** to authorized personnel only
6. **Audit environment changes** and log access to secrets
7. **Use different secrets** for each environment (dev, staging, production)

---

## Additional Resources

- [dotenv documentation](https://github.com/motdotla/dotenv)
- [python-dotenv documentation](https://github.com/theskumar/python-dotenv)
- [Create React App environment variables](https://create-react-app.dev/docs/adding-custom-environment-variables/)
- [Twelve-Factor App Config](https://12factor.net/config)

---

**Last Updated**: 2025-10-17
**Maintainer**: PokerTool Development Team
