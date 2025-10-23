# Docker Compose Setup Guide

## Overview

This guide covers setting up Docker Compose for PokerTool to enable easy orchestration of all services (backend API, frontend, database) with a single command.

## Prerequisites

- Docker Desktop 20.10+ or Docker Engine 20.10+
- Docker Compose v2.0+ (included with Docker Desktop)
- 4GB RAM minimum, 8GB recommended
- 20GB free disk space

## Architecture

```
┌─────────────────────────────────────────┐
│         Docker Compose Stack            │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Frontend │  │ Backend  │  │  DB  │ │
│  │  :3000   │◄─┤  :5001   │◄─┤:5432 │ │
│  │  React   │  │  FastAPI │  │ PG   │ │
│  └──────────┘  └──────────┘  └──────┘ │
│       ▲              ▲                  │
│       │              │                  │
│       └──────┬───────┘                  │
│              │                          │
│         Volume Mounts                   │
│     (logs, data, configs)              │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Create docker-compose.yml

Create a `docker-compose.yml` file in your project root:

```yaml
version: '3.9'

services:
  # PostgreSQL Database
  database:
    image: postgres:15-alpine
    container_name: pokertool-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-pokertool}
      POSTGRES_USER: ${POSTGRES_USER:-pokertool}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-pokertool}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - pokertool-network
    ports:
      - "${POSTGRES_PORT:-5432}:5432"

  # Backend API
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: pokertool-backend
    restart: unless-stopped
    depends_on:
      database:
        condition: service_healthy
    environment:
      # Database
      DATABASE_TYPE: postgresql
      DATABASE_HOST: database
      DATABASE_PORT: 5432
      DATABASE_NAME: ${POSTGRES_DB:-pokertool}
      DATABASE_USER: ${POSTGRES_USER:-pokertool}
      DATABASE_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      
      # API Settings
      API_PORT: 5001
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      ENABLE_API_CACHING: ${ENABLE_API_CACHING:-true}
      
      # Security
      SECRET_KEY: ${SECRET_KEY:-change-this-in-production}
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./poker_config.json:/app/poker_config.json:ro
      - ./ranges:/app/ranges:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - pokertool-network
    ports:
      - "${API_PORT:-5001}:5001"

  # Frontend Development Server
  frontend:
    build:
      context: ./pokertool-frontend
      dockerfile: Dockerfile.dev
    container_name: pokertool-frontend
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    environment:
      REACT_APP_API_URL: ${REACT_APP_API_URL:-http://localhost:5001}
      REACT_APP_WS_URL: ${REACT_APP_WS_URL:-ws://localhost:5001}
      PORT: 3000
    volumes:
      - ./pokertool-frontend/src:/app/src:ro
      - ./pokertool-frontend/public:/app/public:ro
      - frontend_node_modules:/app/node_modules
    networks:
      - pokertool-network
    ports:
      - "${FRONTEND_PORT:-3000}:3000"

  # Nginx Reverse Proxy (Production)
  nginx:
    image: nginx:alpine
    container_name: pokertool-nginx
    restart: unless-stopped
    depends_on:
      - backend
      - frontend
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - pokertool-network
    ports:
      - "${NGINX_HTTP_PORT:-80}:80"
      - "${NGINX_HTTPS_PORT:-443}:443"
    profiles:
      - production

networks:
  pokertool-network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  frontend_node_modules:
    driver: local
```

### 2. Create .env File

Create a `.env` file for environment variables:

```bash
# Database Configuration
POSTGRES_DB=pokertool
POSTGRES_USER=pokertool
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_PORT=5432

# API Configuration
API_PORT=5001
LOG_LEVEL=INFO
ENABLE_API_CACHING=true

# Frontend Configuration
FRONTEND_PORT=3000
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=ws://localhost:5001

# Security
SECRET_KEY=generate-a-secure-random-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:80

# Nginx (Production only)
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
```

### 3. Create .env.example

Create a `.env.example` file for documentation:

```bash
# Copy this file to .env and fill in your values
# DO NOT commit .env to version control

POSTGRES_DB=pokertool
POSTGRES_USER=pokertool
POSTGRES_PASSWORD=changeme
POSTGRES_PORT=5432

API_PORT=5001
LOG_LEVEL=INFO
ENABLE_API_CACHING=true

FRONTEND_PORT=3000
REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=ws://localhost:5001

SECRET_KEY=change-this-in-production
CORS_ORIGINS=http://localhost:3000

NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
```

### 4. Create .dockerignore

Create a `.dockerignore` file to reduce build context:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Logs
logs/
*.log

# Test
.pytest_cache/
.coverage
htmlcov/

# Build
build/
dist/
*.egg-info/

# Documentation
docs/
*.md
!README.md

# CI/CD
.github/
.gitlab-ci.yml

# Local config
.env
.env.local
poker_config.json
```

## Commands

### Development

```bash
# Start all services in development mode
docker-compose up

# Start in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend

# Stop all services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (clean slate)
docker-compose down -v
```

### Production

```bash
# Start with production profile
docker-compose --profile production up -d

# Build without cache
docker-compose build --no-cache

# Scale services
docker-compose up -d --scale backend=3

# Update services
docker-compose pull
docker-compose up -d --force-recreate
```

### Maintenance

```bash
# Check service status
docker-compose ps

# Execute command in running container
docker-compose exec backend bash
docker-compose exec database psql -U pokertool

# View resource usage
docker-compose stats

# Inspect container
docker-compose inspect backend

# Restart specific service
docker-compose restart backend
```

## Advanced Configuration

### Multiple Profiles

Create different configurations for dev/staging/prod:

**docker-compose.override.yml** (development):
```yaml
version: '3.9'

services:
  backend:
    build:
      target: development
    volumes:
      - ./src:/app/src
    command: uvicorn pokertool.api:app --host 0.0.0.0 --port 5001 --reload
    
  frontend:
    volumes:
      - ./pokertool-frontend:/app
    environment:
      - CHOKIDAR_USEPOLLING=true
```

**docker-compose.prod.yml** (production):
```yaml
version: '3.9'

services:
  backend:
    build:
      target: production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    
  frontend:
    build:
      dockerfile: Dockerfile.prod
```

Use with:
```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### Health Checks

Enhanced health check for backend:

```yaml
healthcheck:
  test: |
    curl -f http://localhost:5001/health && \
    curl -f http://localhost:5001/api/status | grep -q '"status":"healthy"'
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Secrets Management

Use Docker secrets for sensitive data:

```yaml
services:
  backend:
    secrets:
      - db_password
      - api_secret_key
    environment:
      DATABASE_PASSWORD_FILE: /run/secrets/db_password
      SECRET_KEY_FILE: /run/secrets/api_secret_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_secret_key:
    file: ./secrets/api_secret_key.txt
```

### Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Networking

### Custom Network Configuration

```yaml
networks:
  pokertool-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
          gateway: 172.28.0.1
```

### External Network

Connect to existing network:

```yaml
networks:
  pokertool-network:
    external: true
    name: shared-network
```

## Volumes

### Backup Volumes

```bash
# Backup database volume
docker run --rm \
  --volumes-from pokertool-db \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/db-backup-$(date +%Y%m%d).tar.gz /var/lib/postgresql/data

# Restore database volume
docker run --rm \
  --volumes-from pokertool-db \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/db-backup-20251023.tar.gz -C /
```

### Named Volumes

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: /path/to/persistent/storage
      o: bind
```

## Logging

### Configure Logging Driver

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Send Logs to External System

```yaml
services:
  backend:
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://logs.example.com:514"
        tag: "pokertool-backend"
```

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Find process using port
lsof -i :5001
# or
netstat -tulpn | grep 5001

# Kill process
kill -9 <PID>
```

**2. Permission Denied on Volumes**
```bash
# Fix volume permissions
docker-compose exec backend chown -R pokertool:pokertool /app/logs
```

**3. Services Won't Start**
```bash
# Check logs
docker-compose logs backend

# Rebuild without cache
docker-compose build --no-cache backend

# Check network connectivity
docker-compose exec backend ping database
```

**4. Database Connection Refused**
```bash
# Wait for database to be ready
docker-compose exec backend bash -c 'until pg_isready -h database; do sleep 1; done'
```

### Debugging

```bash
# Interactive shell in container
docker-compose exec backend bash

# Check environment variables
docker-compose exec backend env

# Test database connection
docker-compose exec backend python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://pokertool:password@database:5432/pokertool'); print(engine.connect())"

# View container details
docker-compose config
```

## Security Best Practices

1. **Don't commit .env files** - Add to .gitignore
2. **Use secrets for sensitive data** - Not environment variables
3. **Run as non-root user** - Already configured in Dockerfile
4. **Keep images updated** - Regular `docker-compose pull`
5. **Scan images for vulnerabilities** - Use `docker scan`
6. **Limit resource usage** - Set memory/CPU limits
7. **Use read-only volumes** - Where possible
8. **Enable security options** - AppArmor, seccomp

## Performance Optimization

### Build Cache

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build
```

### Multi-stage Builds

Already implemented in Dockerfile - keeps final image small.

### Resource Allocation

```yaml
# Optimize for your hardware
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Docker Compose Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Create .env file
        run: cp .env.example .env
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for services
        run: docker-compose exec -T backend bash -c 'until curl -f http://localhost:5001/health; do sleep 5; done'
      
      - name: Run tests
        run: docker-compose exec -T backend pytest
      
      - name: View logs
        if: failure()
        run: docker-compose logs
      
      - name: Cleanup
        if: always()
        run: docker-compose down -v
```

## Migration from Standalone

If you're currently running without Docker:

1. Export current data
2. Update configuration files
3. Create .env from examples
4. Run `docker-compose up -d`
5. Import data into new containers
6. Verify functionality
7. Update client applications to new ports

## Next Steps

- [ ] Review `DOCKER_OPTIMIZATION.md` for image size reduction
- [ ] Check `DOCKER_PUBLISHING.md` for registry setup
- [ ] See `KUBERNETES.md` for production orchestration
- [ ] Review `../deployment/ONE_CLICK_DEPLOY.md` for cloud platforms

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Compose File Reference](https://docs.docker.com/compose/compose-file/)
