# Environment Variables Reference

Complete reference for all environment variables used in PokerTool.

## Core Application Settings

### `POKERTOOL_HOST`
- **Default**: `127.0.0.1`
- **Description**: Backend API host address
- **Usage**: `export POKERTOOL_HOST=0.0.0.0` (bind to all interfaces)

### `POKERTOOL_PORT`
- **Default**: `5001`
- **Description**: Backend API server port
- **Usage**: `export POKERTOOL_PORT=8080`
- **Note**: Changed from 8000 to 5001 to avoid macOS Control Center conflict

### `POKERTOOL_BACKEND_URL`
- **Default**: `http://127.0.0.1:5001`
- **Description**: Full backend API URL
- **Usage**: `export POKERTOOL_BACKEND_URL=http://localhost:5001`

### `POKERTOOL_FRONTEND_URL`
- **Default**: `http://localhost:3000`
- **Description**: React frontend URL
- **Usage**: `export POKERTOOL_FRONTEND_URL=http://localhost:3000`

## Database Configuration

### `DATABASE_URL`
- **Default**: `sqlite:///data/pokertool.db`
- **Description**: Database connection string
- **Usage**: `export DATABASE_URL=postgresql://user:pass@localhost/pokertool`
- **Supported**: SQLite, PostgreSQL

### `DB_POOL_SIZE`
- **Default**: `10`
- **Description**: Database connection pool size
- **Usage**: `export DB_POOL_SIZE=20`

### `DB_MAX_OVERFLOW`
- **Default**: `20`
- **Description**: Maximum overflow connections beyond pool size
- **Usage**: `export DB_MAX_OVERFLOW=30`

## Security & Authentication

### `SECRET_KEY`
- **Default**: Auto-generated
- **Description**: Secret key for JWT token signing
- **Usage**: `export SECRET_KEY=your-secret-key-here`
- **Important**: Set in production! Use strong random value

### `JWT_ALGORITHM`
- **Default**: `HS256`
- **Description**: JWT signing algorithm
- **Options**: `HS256`, `RS256`

### `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Default**: `30`
- **Description**: JWT access token expiration time
- **Usage**: `export ACCESS_TOKEN_EXPIRE_MINUTES=60`

### `CORS_ORIGINS`
- **Default**: `["http://localhost:3000"]`
- **Description**: Allowed CORS origins (comma-separated)
- **Usage**: `export CORS_ORIGINS=http://localhost:3000,https://app.example.com`

## Rate Limiting

### `RATE_LIMIT_STORAGE_URL`
- **Default**: `memory://`
- **Description**: Rate limiter storage backend
- **Usage**: `export RATE_LIMIT_STORAGE_URL=redis://localhost:6379`
- **Options**: `memory://`, `redis://host:port`

### `DEFAULT_RATE_LIMIT`
- **Default**: `100/minute`
- **Description**: Default API rate limit
- **Usage**: `export DEFAULT_RATE_LIMIT=200/minute`

## Screen Scraping

### `TESSERACT_CMD`
- **Default**: System default
- **Description**: Path to Tesseract OCR executable
- **Usage**: `export TESSERACT_CMD=/usr/local/bin/tesseract`
- **Platform-specific**:
  - macOS: `/opt/homebrew/bin/tesseract` or `/usr/local/bin/tesseract`
  - Linux: `/usr/bin/tesseract`
  - Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### `SCRAPER_CACHE_SIZE`
- **Default**: `1000`
- **Description**: OCR result cache size
- **Usage**: `export SCRAPER_CACHE_SIZE=2000`

### `SCRAPER_TIMEOUT`
- **Default**: `5.0`
- **Description**: Screen scraping timeout (seconds)
- **Usage**: `export SCRAPER_TIMEOUT=10.0`

## Machine Learning

### `GTO_CACHE_SIZE`
- **Default**: `10000`
- **Description**: GTO solver result cache size
- **Usage**: `export GTO_CACHE_SIZE=20000`

### `ML_MODEL_PATH`
- **Default**: `models/`
- **Description**: Directory for ML model files
- **Usage**: `export ML_MODEL_PATH=/path/to/models`

### `ENABLE_GPU`
- **Default**: `false`
- **Description**: Enable GPU acceleration for ML models
- **Usage**: `export ENABLE_GPU=true`
- **Requires**: CUDA-compatible GPU and drivers

## Logging

### `LOG_LEVEL`
- **Default**: `INFO`
- **Description**: Minimum log level to output
- **Usage**: `export LOG_LEVEL=DEBUG`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### `LOG_FORMAT`
- **Default**: `structured`
- **Description**: Log output format
- **Options**: `structured` (JSON), `plain` (text)

### `LOG_DIR`
- **Default**: `logs/`
- **Description**: Directory for log files
- **Usage**: `export LOG_DIR=/var/log/pokertool`

### `ENABLE_TELEMETRY`
- **Default**: `true`
- **Description**: Enable telemetry collection
- **Usage**: `export ENABLE_TELEMETRY=false`

## Development & Testing

### `POKERTOOL_ENV`
- **Default**: `production`
- **Description**: Application environment
- **Usage**: `export POKERTOOL_ENV=development`
- **Options**: `development`, `staging`, `production`

### `DEBUG`
- **Default**: `false`
- **Description**: Enable debug mode
- **Usage**: `export DEBUG=true`
- **Effects**: Detailed error messages, SQL query logging, auto-reload

### `TESTING`
- **Default**: `false`
- **Description**: Enable testing mode
- **Usage**: `export TESTING=true`
- **Effects**: Uses test database, disables external API calls

### `PYTEST_MARKERS`
- **Default**: None
- **Description**: Pytest marker expressions
- **Usage**: `export PYTEST_MARKERS="not slow and not scraper"`

## Performance

### `WORKER_COUNT`
- **Default**: CPU count
- **Description**: Number of Uvicorn worker processes
- **Usage**: `export WORKER_COUNT=4`

### `THREAD_POOL_SIZE`
- **Default**: `10`
- **Description**: Thread pool size for parallel tasks
- **Usage**: `export THREAD_POOL_SIZE=20`

### `ENABLE_GZIP`
- **Default**: `true`
- **Description**: Enable gzip compression for API responses
- **Usage**: `export ENABLE_GZIP=false`

### `CACHE_TTL`
- **Default**: `300` (5 minutes)
- **Description**: Default cache time-to-live (seconds)
- **Usage**: `export CACHE_TTL=600`

## Third-Party Integrations

### `CHROME_BINARY_PATH`
- **Default**: Auto-detected
- **Description**: Path to Chrome/Chromium binary for CDP scraping
- **Usage**: `export CHROME_BINARY_PATH=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome`

### `CHROME_DEBUG_PORT`
- **Default**: `9222`
- **Description**: Chrome DevTools Protocol port
- **Usage**: `export CHROME_DEBUG_PORT=9223`

### `REACT_APP_SENTRY_DSN`
- **Default**: None (Sentry disabled)
- **Description**: Sentry error tracking DSN for frontend (React)
- **Format**: `https://public_key@sentry.io/project_id`
- **Usage**: `export REACT_APP_SENTRY_DSN=https://abc123@o123.ingest.sentry.io/456`
- **Where to get it**: Sentry Project Settings → Client Keys (DSN)
- **See**: [SENTRY_INTEGRATION_GUIDE.md](SENTRY_INTEGRATION_GUIDE.md) for complete setup

### `SENTRY_DSN`
- **Default**: None (Backend Sentry disabled)
- **Description**: Sentry error tracking DSN for backend (Python)
- **Format**: `https://public_key@sentry.io/project_id`
- **Usage**: `export SENTRY_DSN=https://key@sentry.io/project`
- **Note**: Currently for future backend integration

### `SENTRY_ENVIRONMENT`
- **Default**: `development`
- **Description**: Environment name for filtering errors in Sentry
- **Values**: `production`, `staging`, `development`, or custom
- **Usage**: `export SENTRY_ENVIRONMENT=production`
- **Purpose**: Group and filter errors by environment

### `SENTRY_RELEASE`
- **Default**: None
- **Description**: Release version for tracking deployments
- **Format**: Semantic version (e.g., `v88.6.0`) or git commit hash
- **Usage**: `export SENTRY_RELEASE=v88.6.0` or `export SENTRY_RELEASE=$(git rev-parse --short HEAD)`
- **Purpose**: Track which version caused errors, compare releases

### `SENTRY_TRACES_SAMPLE_RATE`
- **Default**: `0.1` (10%)
- **Description**: Percentage of transactions to track for performance monitoring
- **Range**: `0.0` (disabled) to `1.0` (100%)
- **Usage**: `export SENTRY_TRACES_SAMPLE_RATE=0.5` (track 50%)
- **Recommendation**: Use 0.1-0.2 in production to balance insight vs cost

### `SENTRY_REPLAYS_SESSION_SAMPLE_RATE`
- **Default**: `0.1` (10%)
- **Description**: Percentage of normal (non-error) sessions to replay
- **Range**: `0.0` to `1.0`
- **Usage**: `export SENTRY_REPLAYS_SESSION_SAMPLE_RATE=0.05` (5% of sessions)
- **Purpose**: Record user sessions for debugging UX issues
- **Privacy**: Consider GDPR implications, see Sentry guide

### `SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE`
- **Default**: `1.0` (100%)
- **Description**: Percentage of error sessions to replay
- **Range**: `0.0` to `1.0`
- **Usage**: `export SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE=1.0` (replay all errors)
- **Purpose**: Always capture sessions where errors occur

### `REDIS_URL`
- **Default**: `redis://localhost:6379`
- **Description**: Redis connection URL
- **Usage**: `export REDIS_URL=redis://user:pass@host:6379/0`

## Platform-Specific

### macOS

#### `QUARTZ_DEBUG`
- **Default**: `false`
- **Description**: Enable Quartz debugging for screen capture
- **Usage**: `export QUARTZ_DEBUG=true`

### Linux

#### `DISPLAY`
- **Default**: `:0`
- **Description**: X11 display for screen capture
- **Usage**: `export DISPLAY=:1`

#### `XAUTHORITY`
- **Default**: `~/.Xauthority`
- **Description**: X11 authority file
- **Usage**: `export XAUTHORITY=/path/to/.Xauthority`

### Windows

#### `PROCESSOR_ARCHITECTURE`
- **Default**: System value
- **Description**: Processor architecture (x86, AMD64, ARM64)
- **Usage**: Auto-detected, read-only

## Configuration File

Instead of environment variables, you can use a `.env` file:

```bash
# .env
POKERTOOL_PORT=5001
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///data/pokertool.db
LOG_LEVEL=DEBUG
ENABLE_TELEMETRY=false
```

Load with:
```bash
python -m pokertool --env-file .env web
```

## Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Use strong SECRET_KEY in production** - Generate with `openssl rand -hex 32`
3. **Set POKERTOOL_ENV=production** - Disables debug features
4. **Configure CORS_ORIGINS** - Only allow trusted domains
5. **Enable HTTPS in production** - Use reverse proxy (nginx/Caddy)
6. **Set appropriate LOG_LEVEL** - `INFO` for production, `DEBUG` for development
7. **Configure rate limiting** - Use Redis in production for distributed rate limiting
8. **Set database connection pooling** - Tune based on workload

## Validation

Validate your environment with:

```bash
python -c "from pokertool.config import validate_config; validate_config()"
```

Or check specific variables:

```bash
python -c "import os; print('PORT:', os.getenv('POKERTOOL_PORT', '5001'))"
```

## Troubleshooting

### Common Issues

**Issue**: "Connection refused on port 8000"
- **Solution**: Set `POKERTOOL_PORT=5001` (default changed from 8000)

**Issue**: "Tesseract not found"
- **Solution**: Set `TESSERACT_CMD` to full path or install Tesseract

**Issue**: "CORS error in browser"
- **Solution**: Add frontend URL to `CORS_ORIGINS`

**Issue**: "Database locked"  
- **Solution**: Increase `DB_POOL_SIZE` or use PostgreSQL

For more troubleshooting, see [`docs/TROUBLESHOOTING.md`](TROUBLESHOOTING.md)