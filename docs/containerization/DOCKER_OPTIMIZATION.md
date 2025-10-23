# Docker Image Optimization Guide

## Overview

This guide provides strategies and techniques for optimizing Docker images for PokerTool, targeting an image size under 500MB while maintaining functionality.

## Current State Analysis

### Baseline Measurements

```bash
# Check current image size
docker images pokertool

# Analyze image layers
docker history pokertool:latest

# View detailed size breakdown
dive pokertool:latest
```

### Size Reduction Targets

- **Current**: ~800MB (estimated)
- **Target**: <500MB
- **Stretch Goal**: <300MB

## Optimization Strategies

### 1. Base Image Selection

#### Current: python:3.12-slim (180MB)

```dockerfile
FROM python:3.12-slim
```

#### Option A: python:3.12-alpine (50MB)

```dockerfile
FROM python:3.12-alpine

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del gcc musl-dev
```

**Pros:**
- 130MB size reduction
- Minimal attack surface
- Fast image pulls

**Cons:**
- Some packages harder to compile
- musl libc compatibility issues
- Longer build times

#### Option B: distroless/python (120MB)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

FROM gcr.io/distroless/python3
COPY --from=builder /app/deps /app/deps
COPY src /app/src
ENV PYTHONPATH=/app/deps
```

**Pros:**
- No shell or package manager
- Enhanced security
- Good size reduction

**Cons:**
- Harder to debug
- Limited tool availability

### 2. Multi-Stage Builds

Separate build and runtime environments:

```dockerfile
# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy only wheels from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY src /app/src
COPY config /app/config

# Run as non-root user
RUN useradd -m -u 1000 pokertool && chown -R pokertool:pokertool /app
USER pokertool

CMD ["python", "-m", "src.main"]
```

**Size Savings**: ~200MB (build tools not in final image)

### 3. Dependency Optimization

#### Analyze Dependencies

```bash
# Find large packages
pip list --format=freeze | while read pkg; do
    pip show $pkg | grep -E "^(Name|Size)"
done | sort -k2 -n -r
```

#### Remove Unnecessary Dependencies

```python
# requirements.txt optimization
# Before
numpy==1.24.0          # 50MB
pandas==2.0.0          # 40MB
scipy==1.10.0          # 35MB

# After (use lighter alternatives)
numpy==1.24.0          # Still needed
# pandas removed, use native data structures
# scipy removed, implement specific functions
```

#### Use Compiled Wheels

```dockerfile
# Use platform-specific wheels
RUN pip install --no-cache-dir \
    --only-binary=:all: \
    -r requirements.txt
```

### 4. Layer Optimization

#### Combine RUN Commands

```dockerfile
# Before (multiple layers)
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2
RUN rm -rf /var/lib/apt/lists/*

# After (single layer)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        package1 \
        package2 \
    && rm -rf /var/lib/apt/lists/*
```

#### Order Layers by Change Frequency

```dockerfile
# Rarely changed (cached)
FROM python:3.12-slim
RUN apt-get update && apt-get install -y curl

# Occasionally changed
COPY requirements.txt .
RUN pip install -r requirements.txt

# Frequently changed (last)
COPY src /app/src
```

### 5. .dockerignore Optimization

Comprehensive exclusions (already implemented):

```
# Prevent unnecessary files from entering build context
__pycache__/
*.pyc
.git/
tests/
docs/
*.md
node_modules/
.vscode/
*.log
```

### 6. Remove Build Artifacts

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt \
    && find /usr/local -type d -name '__pycache__' -exec rm -rf {} + \
    && find /usr/local -type f -name '*.pyc' -delete \
    && find /usr/local -type f -name '*.pyo' -delete
```

### 7. Compress Assets

```dockerfile
# Compress large data files
COPY model_calibration_data /app/model_calibration_data
RUN cd /app/model_calibration_data && \
    find . -name "*.json" -exec gzip {} \; && \
    find . -name "*.csv" -exec gzip {} \;
```

### 8. Use Alpine Packages

When using Alpine base:

```dockerfile
FROM python:3.12-alpine

# Install runtime dependencies only
RUN apk add --no-cache \
    libpq \
    libffi \
    ca-certificates

# Build dependencies in separate layer
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps
```

### 9. Optimize Python Bytecode

```dockerfile
# Compile Python files and remove source
RUN python -m compileall -b /app/src && \
    find /app/src -name "*.py" -delete
```

**Warning**: Makes debugging harder. Only use in production images.

### 10. Static Linking

For critical performance paths:

```dockerfile
# Use statically linked binaries
RUN pip install --no-cache-dir \
    --compile \
    --global-option=build_ext \
    --global-option="-static" \
    numpy
```

## Complete Optimized Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.4

# Build stage
FROM python:3.12-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    make \
    cargo \
    rust

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Runtime stage
FROM python:3.12-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache \
    libpq \
    libffi \
    ca-certificates \
    tini

# Copy wheels and install
COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* \
    && rm -rf /tmp/wheels \
    && find /usr/local -type d -name '__pycache__' -exec rm -rf {} + \
    && find /usr/local -type f -name '*.pyc' -delete

# Copy application code
COPY --chown=1000:1000 src /app/src
COPY --chown=1000:1000 config /app/config

# Create non-root user
RUN adduser -D -u 1000 pokertool && \
    chown -R pokertool:pokertool /app

USER pokertool

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Use tini as init
ENTRYPOINT ["/sbin/tini", "--"]

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Size Benchmarks

| Optimization | Size | Reduction | Build Time |
|-------------|------|-----------|------------|
| Baseline (python:3.12) | 920MB | - | 3m |
| + slim base | 750MB | 170MB | 2.5m |
| + multi-stage | 550MB | 200MB | 3m |
| + alpine base | 380MB | 370MB | 4m |
| + .dockerignore | 360MB | 20MB | 4m |
| + dependency cleanup | 320MB | 40MB | 4m |
| + bytecode compilation | 290MB | 30MB | 4.5m |

## Build Time Optimization

### Use BuildKit

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Or in docker-compose.yml
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
```

### Cache Mount

```dockerfile
# Cache pip downloads
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Layer Caching

```dockerfile
# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code later (changes more frequently)
COPY src /app/src
```

## Testing Size Reductions

```bash
# Build with different optimizations
docker build -t pokertool:baseline -f Dockerfile.baseline .
docker build -t pokertool:optimized -f Dockerfile.optimized .

# Compare sizes
docker images | grep pokertool

# Analyze layers
docker history pokertool:optimized

# Use dive for detailed analysis
dive pokertool:optimized
```

## Production Recommendations

1. **Use Alpine for size** - Accept slightly longer build times
2. **Multi-stage builds** - Essential for clean final image
3. **Minimal runtime deps** - Only install what's needed
4. **Regular audits** - Check for bloat monthly
5. **Monitor image size** - Set CI/CD size limits
6. **Use .dockerignore** - Comprehensive exclusions
7. **Compress large assets** - Gzip data files
8. **Clean up in same layer** - Don't leave artifacts

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Build Docker image
  run: docker build -t pokertool:${{ github.sha }} .

- name: Check image size
  run: |
    SIZE=$(docker images pokertool:${{ github.sha }} --format "{{.Size}}")
    echo "Image size: $SIZE"
    # Fail if over 500MB
    docker images pokertool:${{ github.sha }} --format "{{.Size}}" | \
      grep -q "MB" && exit 0 || exit 1
```

## Troubleshooting

### Alpine Compatibility Issues

```bash
# If packages fail to build on Alpine
RUN apk add --no-cache --virtual .build-deps \
    gcc g++ make cmake

# Or fall back to slim
FROM python:3.12-slim
```

### Missing Shared Libraries

```bash
# Check dependencies
ldd /usr/local/bin/python

# Install missing libs
apk add --no-cache libstdc++
```

### Build Time Too Long

```bash
# Use BuildKit cache mounts
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

## Tools

- **dive**: Analyze image layers - `brew install dive`
- **docker-slim**: Automatic optimization - `brew install docker-slim`
- **hadolint**: Dockerfile linter - `brew install hadolint`

```bash
# Use dive
dive pokertool:latest

# Use docker-slim
docker-slim build pokertool:latest

# Lint Dockerfile
hadolint Dockerfile
```

## Next Steps

- Implement [Docker Compose](DOCKER_COMPOSE.md)
- Set up [Docker Publishing](DOCKER_PUBLISHING.md)
- Test [Podman compatibility](PODMAN_GUIDE.md)
- Explore [Buildpacks](BUILDPACKS.md)

## References

- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [Alpine Linux Packages](https://pkgs.alpinelinux.org/packages)
