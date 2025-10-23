# Docker Compose Guide for PokerTool

## Overview

This guide covers the Docker Compose setup for PokerTool, providing simplified orchestration of the multi-service application architecture.

## Architecture

PokerTool uses a multi-service architecture:

- **Backend Service**: Python-based poker analysis engine
- **Frontend Service**: React-based web interface
- **Database Service**: PostgreSQL for data persistence
- **Redis Service**: Caching and session management

## Quick Start

### Prerequisites

- Docker 20.10+ or Podman 3.0+
- Docker Compose 2.0+ or podman-compose
- 4GB RAM minimum
- 10GB disk space

### Basic Usage

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Application Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=info

# Database Configuration
POSTGRES_USER=pokertool
POSTGRES_PASSWORD=change_this_password
POSTGRES_DB=pokertool
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
SECRET_KEY=change_this_secret_key
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Feature Flags
ENABLE_BETFAIR=false
ENABLE_LEARNING=true
ENABLE_AUTO_ACTIONS=false
```

### Volume Mounts

The compose file includes persistent volumes for:

- **Database Data**: `./data/postgres` - PostgreSQL data directory
- **Logs**: `./logs` - Application and service logs
- **Config**: `./config` - Configuration files
- **Models**: `./model_calibration_data` - ML model data
- **Exports**: `./exports` - Hand history and session exports

## Docker Compose File Structure

### Development Profile

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    environment:
      - DEBUG=true
    volumes:
      - ./src:/app/src:ro
      - ./logs:/app/logs
    command: python -m uvicorn src.main:app --reload --host 0.0.0.0
```

### Production Profile

```yaml
services:
  backend:
    image: pokertool/backend:latest
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
    restart: unless-stopped
```

## Service Details

### Backend Service

- **Image**: `pokertool/backend:latest` or built locally
- **Port**: 8000 (API)
- **Health Check**: `http://localhost:8000/health`
- **Dependencies**: Database, Redis
- **Restart Policy**: `unless-stopped`

### Frontend Service

- **Image**: `pokertool/frontend:latest` or built locally
- **Port**: 3000 (Web UI)
- **Health Check**: `http://localhost:3000`
- **Dependencies**: Backend
- **Restart Policy**: `unless-stopped`

### Database Service

- **Image**: `postgres:15-alpine`
- **Port**: 5432 (exposed for debugging)
- **Volume**: `postgres_data:/var/lib/postgresql/data`
- **Health Check**: `pg_isready`
- **Restart Policy**: `unless-stopped`

### Redis Service

- **Image**: `redis:7-alpine`
- **Port**: 6379 (internal only)
- **Volume**: `redis_data:/data`
- **Health Check**: `redis-cli ping`
- **Restart Policy**: `unless-stopped`

## Networking

All services are connected via a custom bridge network:

```yaml
networks:
  pokertool-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

Service DNS names:
- Backend: `backend` or `api`
- Frontend: `frontend` or `web`
- Database: `db` or `postgres`
- Redis: `redis` or `cache`

## Health Checks

Each service includes health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Common Operations

### Viewing Service Status

```bash
docker-compose ps
```

### Scaling Services

```bash
# Scale backend to 3 instances
docker-compose up -d --scale backend=3
```

### Accessing Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Executing Commands

```bash
# Run command in backend
docker-compose exec backend python manage.py migrate

# Open shell in backend
docker-compose exec backend sh

# Run one-off command
docker-compose run --rm backend python scripts/setup.py
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U pokertool

# Create database backup
docker-compose exec db pg_dump -U pokertool pokertool > backup.sql

# Restore database backup
docker-compose exec -T db psql -U pokertool pokertool < backup.sql
```

### Rebuilding Services

```bash
# Rebuild all services
docker-compose build

# Rebuild specific service
docker-compose build backend

# Rebuild without cache
docker-compose build --no-cache
```

## Profiles

Use profiles to run different configurations:

```bash
# Development mode
docker-compose --profile dev up

# Production mode
docker-compose --profile prod up

# With monitoring
docker-compose --profile monitoring up
```

## Troubleshooting

### Services Won't Start

Check logs for errors:
```bash
docker-compose logs backend
```

Verify environment variables:
```bash
docker-compose config
```

### Port Conflicts

Change ports in `.env`:
```bash
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

### Database Connection Issues

Check database is healthy:
```bash
docker-compose ps db
docker-compose logs db
```

Verify connection string in backend logs.

### Permission Issues

Fix volume permissions:
```bash
sudo chown -R $(id -u):$(id -g) logs/ data/
```

### Out of Memory

Increase Docker memory limit or reduce service replicas.

## Best Practices

1. **Always use .env files** - Never hardcode secrets
2. **Use named volumes** - For production data
3. **Set resource limits** - Prevent resource exhaustion
4. **Enable health checks** - For automatic recovery
5. **Use restart policies** - For high availability
6. **Regular backups** - Of volumes and databases
7. **Monitor logs** - Use log aggregation in production
8. **Update images** - Regularly pull latest versions

## Security Considerations

1. **Change default passwords** - Before production use
2. **Use secrets management** - Docker secrets or external vault
3. **Limit exposed ports** - Only expose what's necessary
4. **Use read-only volumes** - Where possible
5. **Run as non-root** - Inside containers
6. **Scan images** - For vulnerabilities
7. **Use private registries** - For proprietary images

## Performance Optimization

1. **Use build cache** - Speed up builds
2. **Multi-stage builds** - Reduce image size
3. **Resource limits** - Prevent noisy neighbors
4. **Connection pooling** - In database configuration
5. **Redis caching** - For frequently accessed data
6. **Load balancing** - With multiple backend replicas

## Monitoring

Add monitoring services (optional):

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
```

## Next Steps

- Review [Docker Optimization Guide](DOCKER_OPTIMIZATION.md)
- Set up [Docker Publishing](DOCKER_PUBLISHING.md)
- Explore [Kubernetes Deployment](KUBERNETES.md)
- Configure [Podman Support](PODMAN_GUIDE.md)

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Compose File Reference](https://docs.docker.com/compose/compose-file/)
- [Best Practices for Compose](https://docs.docker.com/compose/production/)
