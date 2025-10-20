# PokerTool Configuration Guide

This document provides a comprehensive reference for all environment variables and configuration options available in PokerTool.

## Table of Contents

- [Frontend Configuration](#frontend-configuration)
- [Backend Configuration](#backend-configuration)
- [Database Configuration](#database-configuration)
- [OCR Configuration](#ocr-configuration)
- [Runtime Configuration](#runtime-configuration)

---

## Frontend Configuration

Frontend environment variables are configured in the `pokertool-frontend` directory using `.env` files.

### Environment File Priority

1. `.env.local` - Highest priority, used for local development overrides (not committed)
2. `.env.development` - Development environment defaults
3. `.env.production` - Production environment defaults
4. `.env` - Base configuration (fallback)

### Frontend Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REACT_APP_API_URL` | string | `http://localhost:5001` | REST API server URL for backend communication |
| `REACT_APP_WS_URL` | string | `http://localhost:8000` | WebSocket server URL for real-time updates |

### Frontend Configuration Examples

**Local Development:**
```bash
# .env.local
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=http://localhost:8000
```

**Custom IP (Network Testing):**
```bash
# .env.local
REACT_APP_API_URL=http://192.168.1.100:5001
REACT_APP_WS_URL=http://192.168.1.100:8000
```

**Production:**
```bash
# .env.production
REACT_APP_API_URL=https://api.pokertool.app
REACT_APP_WS_URL=wss://ws.pokertool.app
```

---

## Backend Configuration

### General Backend Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POKER_DB_PATH` | string | `poker_decisions.db` | SQLite database file path (used when POKER_DB_TYPE=sqlite) |

---

## Database Configuration

PokerTool supports both SQLite and PostgreSQL databases. The database type is controlled by the `POKER_DB_TYPE` environment variable.

### Database Type Selection

| Variable | Type | Default | Options | Description |
|----------|------|---------|---------|-------------|
| `POKER_DB_TYPE` | string | `sqlite` | `sqlite`, `postgresql`, `postgres` | Database backend to use |

### SQLite Configuration

SQLite is the default database backend, suitable for single-user installations and development.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POKER_DB_PATH` | string | `poker_decisions.db` | Path to SQLite database file |

**Example SQLite Configuration:**
```bash
export POKER_DB_TYPE=sqlite
export POKER_DB_PATH=/path/to/poker_decisions.db
```

### PostgreSQL Configuration

PostgreSQL is recommended for production deployments, multi-user setups, and high-performance requirements.

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `POKER_DB_TYPE` | string | `sqlite` | Yes | Must be `postgresql` or `postgres` |
| `POKER_DB_HOST` | string | `localhost` | No | PostgreSQL server hostname or IP |
| `POKER_DB_PORT` | integer | `5432` | No | PostgreSQL server port |
| `POKER_DB_NAME` | string | `pokertool` | No | Database name |
| `POKER_DB_USER` | string | `postgres` | No | Database username |
| `POKER_DB_PASSWORD` | string | *(none)* | **Yes** | Database password |
| `POKER_DB_MIN_CONN` | integer | `2` | No | Minimum connections in pool |
| `POKER_DB_MAX_CONN` | integer | `20` | No | Maximum connections in pool |
| `POKER_DB_SSL_MODE` | string | `prefer` | No | SSL/TLS mode: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full` |

**Example PostgreSQL Configuration:**
```bash
export POKER_DB_TYPE=postgresql
export POKER_DB_HOST=localhost
export POKER_DB_PORT=5432
export POKER_DB_NAME=pokertool
export POKER_DB_USER=pokertool_user
export POKER_DB_PASSWORD=secure_password_here
export POKER_DB_MIN_CONN=2
export POKER_DB_MAX_CONN=20
export POKER_DB_SSL_MODE=prefer
```

### PostgreSQL SSL Modes

| Mode | Description |
|------|-------------|
| `disable` | No SSL/TLS encryption |
| `allow` | Try non-SSL first, then SSL if server requires it |
| `prefer` | Try SSL first, fall back to non-SSL (default) |
| `require` | Require SSL, but don't verify server certificate |
| `verify-ca` | Require SSL and verify server certificate against CA |
| `verify-full` | Require SSL, verify certificate and hostname |

---

## Production Database Configuration

For production PostgreSQL deployments (used in `production_database.py`):

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POSTGRES_HOST` | string | `localhost` | PostgreSQL server hostname |
| `POSTGRES_PORT` | integer | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | string | `pokertool` | Production database name |
| `POSTGRES_USER` | string | `pokertool_user` | Production database username |
| `POSTGRES_PASSWORD` | string | *(none)* | Production database password (required) |
| `POSTGRES_SSL_MODE` | string | `prefer` | SSL/TLS connection mode |

### Test Database Configuration

For running tests with PostgreSQL:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POSTGRES_HOST` | string | `localhost` | Test database server hostname |
| `POSTGRES_DB` | string | `pokertool_test` | Test database name |
| `POSTGRES_USER` | string | `postgres` | Test database username |
| `POSTGRES_PASSWORD` | string | *(none)* | Test database password |

**Example Production Configuration:**
```bash
# Production PostgreSQL
export POSTGRES_HOST=db.production.example.com
export POSTGRES_PORT=5432
export POSTGRES_DB=pokertool
export POSTGRES_USER=pokertool_prod
export POSTGRES_PASSWORD=super_secure_production_password
export POSTGRES_SSL_MODE=verify-full
```

---

## OCR Configuration

### Windows Tesseract Configuration

On Windows systems, PokerTool attempts to locate Tesseract OCR automatically. The system user is derived from:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `USERNAME` | string | `user` | Windows username (used to locate Tesseract installation path) |

**Tesseract Search Paths (Windows):**
```
C:\Users\{USERNAME}\AppData\Local\Tesseract-OCR\tesseract.exe
```

**Note:** On macOS and Linux, Tesseract is expected to be in the system PATH.

---

## Runtime Configuration

### System User Identification

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `USER` | string | `anonymous` | Unix/Linux username (used for analytics and session identification) |

This variable is used to generate unique user identifiers for analytics purposes combined with hostname and timestamp.

---

## Configuration Best Practices

### Security

1. **Never commit secrets:** Add `.env`, `.env.local`, and any files containing passwords to `.gitignore`
2. **Use strong passwords:** Especially for production PostgreSQL databases
3. **Enable SSL/TLS:** Use `POSTGRES_SSL_MODE=verify-full` in production
4. **Rotate credentials:** Regularly update database passwords
5. **Principle of least privilege:** Grant database users only necessary permissions

### Performance

1. **Connection pooling:** Tune `POKER_DB_MIN_CONN` and `POKER_DB_MAX_CONN` based on load
   - Low traffic: `MIN_CONN=2`, `MAX_CONN=10`
   - Medium traffic: `MIN_CONN=5`, `MAX_CONN=20`
   - High traffic: `MIN_CONN=10`, `MAX_CONN=50`

2. **Database choice:**
   - Development: SQLite is sufficient
   - Production: Use PostgreSQL for better performance and concurrency

### Environment Separation

Create separate configuration files for each environment:

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production
```

### Docker Configuration

When running in Docker, environment variables can be passed via:

1. **docker-compose.yml:**
```yaml
environment:
  - POKER_DB_TYPE=postgresql
  - POKER_DB_HOST=postgres
  - POKER_DB_NAME=pokertool
  - POKER_DB_USER=pokertool
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

2. **Docker .env file:**
```bash
# docker.env
POKER_DB_TYPE=postgresql
POKER_DB_HOST=postgres
POSTGRES_PASSWORD=secure_password
```

Then run:
```bash
docker-compose --env-file docker.env up
```

---

## Verification

### Verify Frontend Configuration

1. Check that environment variables are loaded:
```bash
cd pokertool-frontend
npm start
# Check browser console for API_URL and WS_URL
```

2. Inspect the React build:
```bash
cd pokertool-frontend
npm run build
# Environment variables are embedded at build time
```

### Verify Backend Configuration

1. Check database connection:
```bash
PYTHONPATH=src python3 -c "from pokertool.database import PokerDatabase; db = PokerDatabase(); print('DB connected successfully')"
```

2. Check all environment variables:
```bash
env | grep -E "POKER_|POSTGRES_|REACT_APP_"
```

---

## Troubleshooting

### Common Issues

**Issue: Frontend can't connect to backend**
- Check `REACT_APP_API_URL` matches backend server address
- Verify backend is running: `curl http://localhost:5001/health`
- Check CORS settings if accessing from different origin

**Issue: Database connection fails**
- Verify database credentials with manual connection
- Check network connectivity to database host
- Ensure database exists and user has permissions
- Verify SSL/TLS settings match server requirements

**Issue: Environment variables not loaded**
- Frontend: Variables must start with `REACT_APP_` prefix
- Frontend: Restart development server after changing `.env`
- Backend: Export variables or use `.env` loader
- Check variable names for typos

**Issue: OCR not working on Windows**
- Verify `USERNAME` environment variable is set
- Install Tesseract OCR to standard location
- Add Tesseract to system PATH as alternative

---

## Migration Guide

### Migrating from SQLite to PostgreSQL

1. **Set up PostgreSQL database:**
```sql
CREATE DATABASE pokertool;
CREATE USER pokertool_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE pokertool TO pokertool_user;
```

2. **Update environment variables:**
```bash
export POKER_DB_TYPE=postgresql
export POKER_DB_HOST=localhost
export POKER_DB_NAME=pokertool
export POKER_DB_USER=pokertool_user
export POKER_DB_PASSWORD=your_password
```

3. **Run migrations** (if migration scripts exist):
```bash
python scripts/migrate_db.py
```

4. **Verify connection:**
```bash
python -c "from pokertool.database import PokerDatabase; db = PokerDatabase(); print(db.get_database_stats())"
```

---

## Reference

### File Locations

- Frontend config: `pokertool-frontend/.env.example`
- Database implementation: `src/pokertool/database.py`
- Production database: `src/pokertool/production_database.py`
- API server: `src/pokertool/api.py`
- OCR configuration: `src/pokertool/ocr_recognition.py`

### Related Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [README](../README.md)

---

## Quick Reference Card

**Frontend:**
```bash
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=http://localhost:8000
```

**Backend (SQLite):**
```bash
POKER_DB_TYPE=sqlite
POKER_DB_PATH=poker_decisions.db
```

**Backend (PostgreSQL):**
```bash
POKER_DB_TYPE=postgresql
POKER_DB_HOST=localhost
POKER_DB_PORT=5432
POKER_DB_NAME=pokertool
POKER_DB_USER=pokertool_user
POKER_DB_PASSWORD=your_password
POKER_DB_MIN_CONN=2
POKER_DB_MAX_CONN=20
POKER_DB_SSL_MODE=prefer
```

**Production PostgreSQL:**
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=pokertool
POSTGRES_USER=pokertool_user
POSTGRES_PASSWORD=your_password
POSTGRES_SSL_MODE=prefer
```

---

*Last updated: October 2025 (v86.4.0)*
