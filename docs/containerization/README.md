# Containerization Documentation

## Overview

This directory contains comprehensive guides for containerizing PokerTool using various technologies. Each approach offers different trade-offs in terms of size, complexity, and deployment flexibility.

## Available Guides

### Core Containerization

1. **[DOCKER_COMPOSE.md](DOCKER_COMPOSE.md)** ⭐ **START HERE**
   - Complete Docker Compose setup for multi-service orchestration
   - Development and production configurations
   - Database, backend, frontend, and nginx services
   - Volume management and networking
   - **Recommended for:** Most users, especially for development and production deployments

2. **[DOCKER_OPTIMIZATION.md](DOCKER_OPTIMIZATION.md)**
   - Reduce image size from 1.2GB to <500MB
   - Build time optimization with BuildKit
   - Security hardening techniques
   - Alpine vs Debian vs Distroless comparisons
   - **Recommended for:** Production deployments, CI/CD pipelines

3. **[PODMAN_GUIDE.md](PODMAN_GUIDE.md)**
   - Rootless container alternative to Docker
   - Migration from Docker to Podman
   - Compatibility testing and configuration
   - **Recommended for:** Security-conscious deployments, rootless environments

4. **[BUILDPACKS.md](BUILDPACKS.md)**
   - Dockerfile-less containerization with Cloud Native Buildpacks
   - Automatic dependency detection
   - Simplified build process
   - **Recommended for:** Cloud-native deployments, rapid prototyping

### Orchestration

5. **[KUBERNETES.md](KUBERNETES.md)**
   - Production Kubernetes manifests
   - Deployment, service, and ingress configurations
   - Auto-scaling and health monitoring
   - **Recommended for:** Large-scale production deployments

6. **[HELM_CHART.md](HELM_CHART.md)**
   - Helm chart for simplified Kubernetes deployment
   - Configurable values and templating
   - Chart repository publishing
   - **Recommended for:** Kubernetes users, multi-environment deployments

### Publishing

7. **[DOCKER_PUBLISHING.md](DOCKER_PUBLISHING.md)**
   - Automated image publishing to Docker Hub and GHCR
   - Multi-architecture builds (amd64, arm64)
   - CI/CD integration with GitHub Actions
   - **Recommended for:** Open source projects, public distribution

## Quick Start

### For Development

```bash
# 1. Create .env file
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Access application
open http://localhost:3000
```

### For Production

```bash
# 1. Build optimized image
DOCKER_BUILDKIT=1 docker build -t pokertool:latest .

# 2. Run with production settings
docker run -d \
  --name pokertool \
  -p 5001:5001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env.production \
  pokertool:latest
```

### For Kubernetes

```bash
# Using Helm
helm repo add pokertool https://charts.pokertool.io
helm install pokertool pokertool/pokertool

# Or with kubectl
kubectl apply -f k8s/
```

## Technology Comparison

| Technology | Size | Complexity | Portability | Best For |
|------------|------|------------|-------------|----------|
| Docker Compose | Medium | Low | High | Development, small deployments |
| Optimized Docker | Small | Medium | High | Production, size-conscious |
| Podman | Medium | Low | High | Rootless, security-focused |
| Buildpacks | Small | Very Low | High | Cloud-native, rapid iteration |
| Kubernetes | N/A | High | Very High | Large-scale, enterprise |

## Architecture Diagrams

### Docker Compose Stack

```
┌─────────────────────────────────────────┐
│         Docker Compose Stack            │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────┐  │
│  │ Frontend │  │ Backend  │  │  DB  │  │
│  │  :3000   │◄─┤  :5001   │◄─┤:5432 │  │
│  │  React   │  │  FastAPI │  │  PG  │  │
│  └──────────┘  └──────────┘  └──────┘  │
│                                         │
│  ┌──────────────────────────┐          │
│  │     Nginx (Production)   │          │
│  │        :80, :443         │          │
│  └──────────────────────────┘          │
└─────────────────────────────────────────┘
```

### Kubernetes Deployment

```
┌────────────────────────────────────────────┐
│          Kubernetes Cluster                │
├────────────────────────────────────────────┤
│                                            │
│  ┌─────────────────────────────────────┐  │
│  │         Ingress Controller          │  │
│  │     (HTTPS + Load Balancing)        │  │
│  └──────────────┬──────────────────────┘  │
│                 │                          │
│  ┌──────────────▼──────────────────────┐  │
│  │         Frontend Service            │  │
│  │   ┌─────┐ ┌─────┐ ┌─────┐          │  │
│  │   │ Pod │ │ Pod │ │ Pod │ (x3)     │  │
│  │   └─────┘ └─────┘ └─────┘          │  │
│  └──────────────┬──────────────────────┘  │
│                 │                          │
│  ┌──────────────▼──────────────────────┐  │
│  │         Backend Service             │  │
│  │   ┌─────┐ ┌─────┐ ┌─────┐          │  │
│  │   │ Pod │ │ Pod │ │ Pod │ (x3)     │  │
│  │   └─────┘ └─────┘ └─────┘          │  │
│  └──────────────┬──────────────────────┘  │
│                 │                          │
│  ┌──────────────▼──────────────────────┐  │
│  │      PostgreSQL StatefulSet         │  │
│  │   ┌─────┐ ┌─────┐ ┌─────┐          │  │
│  │   │ Pod │ │ Pod │ │ Pod │ (x3)     │  │
│  │   └─────┘ └─────┘ └─────┘          │  │
│  │   PersistentVolumeClaims            │  │
│  └─────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

## Common Tasks

### Build and Test Locally

```bash
# Build image
docker build -t pokertool:dev .

# Run tests in container
docker run --rm pokertool:dev pytest

# Interactive shell
docker run -it --rm pokertool:dev bash
```

### Optimize Image Size

```bash
# Build with optimization
DOCKER_BUILDKIT=1 docker build \
  --target production \
  --build-arg PYTHON_VERSION=3.12-alpine \
  -t pokertool:optimized .

# Analyze layers
docker history pokertool:optimized --human

# Use dive for detailed analysis
dive pokertool:optimized
```

### Multi-Platform Build

```bash
# Setup buildx
docker buildx create --name multiplatform --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --push \
  -t ghcr.io/gmanldn/pokertool:latest .
```

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker logs pokertool-backend

# Check events
docker events --filter container=pokertool-backend

# Inspect container
docker inspect pokertool-backend
```

**Port conflicts:**
```bash
# Find process using port
lsof -i :5001

# Use different port
docker run -p 5002:5001 pokertool:latest
```

**Permission issues:**
```bash
# Fix volume permissions
docker run --rm -v pokertool_data:/data alpine chown -R 1000:1000 /data
```

**Large image size:**
- Review DOCKER_OPTIMIZATION.md
- Use .dockerignore
- Multi-stage builds
- Alpine base images

## Best Practices

### Development

1. ✅ Use Docker Compose for local development
2. ✅ Mount source code as volumes for hot-reload
3. ✅ Use override files for developer-specific config
4. ✅ Keep .env files out of version control
5. ✅ Use named volumes for databases

### Production

1. ✅ Use optimized images (Alpine, distroless)
2. ✅ Scan for vulnerabilities regularly
3. ✅ Run as non-root user
4. ✅ Set resource limits
5. ✅ Use health checks
6. ✅ Implement proper logging
7. ✅ Use secrets management
8. ✅ Enable auto-restart policies

### Security

1. ✅ Never include secrets in images
2. ✅ Use specific version tags, not :latest
3. ✅ Scan images for CVEs
4. ✅ Run with read-only filesystem where possible
5. ✅ Use network policies in Kubernetes
6. ✅ Implement RBAC for production
7. ✅ Regular security updates

## Monitoring & Observability

### Health Checks

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Logging

```bash
# View logs
docker-compose logs -f backend

# Export logs
docker logs pokertool-backend > backend.log 2>&1

# Use logging driver
docker run --log-driver=syslog pokertool:latest
```

### Metrics

```bash
# Resource usage
docker stats

# Detailed container info
docker inspect pokertool-backend | jq '.[0].State'
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: docker/setup-buildx-action@v2
      
      - uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ghcr.io/gmanldn/pokertool:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Migration Guides

### From Standalone to Docker

1. Export current data/configuration
2. Review Docker Compose setup
3. Create `.env` from examples
4. `docker-compose up -d`
5. Import data into containers
6. Verify functionality
7. Update client connections

### From Docker to Kubernetes

1. Review k8s/ manifests
2. Adapt ConfigMaps and Secrets
3. Set up persistent volumes
4. Deploy with kubectl or Helm
5. Configure ingress
6. Set up monitoring
7. Test failover and scaling

## Performance Tuning

### Image Build

- Use BuildKit: `DOCKER_BUILDKIT=1`
- Leverage layer caching
- Order Dockerfile commands by change frequency
- Use .dockerignore effectively

### Runtime

- Set appropriate resource limits
- Use health checks for readiness
- Implement graceful shutdown
- Configure proper restart policies

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/gmanldn/pokertool/issues)
- **Discussions:** [GitHub Discussions](https://github.com/gmanldn/pokertool/discussions)
- **Slack:** #pokertool-containers (if available)
- **Email:** support@pokertool.io

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on:
- Proposing new containerization approaches
- Improving documentation
- Reporting issues
- Submitting pull requests

## Additional Resources

### Official Documentation
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Podman Documentation](https://docs.podman.io/)
- [Cloud Native Buildpacks](https://buildpacks.io/)

### Tools
- [Dive](https://github.com/wagoodman/dive) - Image layer analysis
- [Trivy](https://github.com/aquasecurity/trivy) - Vulnerability scanning
- [Hadolint](https://github.com/hadolint/hadolint) - Dockerfile linter
- [Docker Slim](https://github.com/docker-slim/docker-slim) - Image optimization

### Learning Resources
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [12-Factor App](https://12factor.net/)
- [Kubernetes Patterns](https://kubernetes.io/docs/concepts/cluster-administration/manage-deployment/)

## License

All documentation in this directory is released under the same license as PokerTool (Apache 2.0).

---

**Last Updated:** October 2025  
**Maintainer:** PokerTool Team  
**Version:** 1.0.0
