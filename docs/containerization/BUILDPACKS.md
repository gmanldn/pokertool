# Cloud Native Buildpacks Guide

## Overview

This guide covers implementing Cloud Native Buildpacks for PokerTool, providing a simpler alternative to maintaining Dockerfiles while still producing optimized container images.

## What are Buildpacks?

Cloud Native Buildpacks (CNB) transform application source code into container images without requiring a Dockerfile. They:
- Auto-detect application languages and frameworks
- Apply best practices automatically
- Create minimal, optimized images
- Support dependency caching
- Enable reproducible builds
- Integrate with CI/CD pipelines

## Benefits over Dockerfile

1. **No Dockerfile Maintenance** - Buildpacks handle image configuration
2. **Best Practices** - Built-in security and optimization
3. **Automatic Updates** - Update base images without code changes
4. **Language Detection** - Auto-detects Python, Node.js, etc.
5. **Layer Reuse** - Efficient caching and updates
6. **Reproducible** - Same input → same output

## Prerequisites

### Install Pack CLI

```bash
# macOS
brew install buildpacks/tap/pack

# Linux
curl -sSL "https://github.com/buildpacks/pack/releases/download/v0.31.0/pack-v0.31.0-linux.tgz" | tar -xz -C /usr/local/bin

# Windows (via Chocolatey)
choco install pack

# Verify installation
pack --version
```

### Install Docker or Podman

Buildpacks require a container runtime:

```bash
# Check Docker
docker --version

# Or Podman
podman --version
```

## Project Configuration

### Create project.toml

Create `project.toml` in project root:

```toml
[project]
id = "pokertool"
name = "PokerTool"
version = "1.0.0"
authors = ["PokerTool Team <team@pokertool.com>"]
license = "MIT"

[build]
include = [
    "src/",
    "requirements.txt",
    "pyproject.toml",
    "config/"
]

exclude = [
    "tests/",
    "docs/",
    "*.md",
    ".git/",
    "__pycache__/",
    "*.pyc",
    ".venv/",
    "node_modules/"
]

[[build.env]]
name = "PYTHON_VERSION"
value = "3.12"

[[build.env]]
name = "BP_CPYTHON_VERSION"
value = "3.12.*"

[[build.env]]
name = "BP_PIP_VERSION"
value = "latest"

[metadata]
description = "AI-Powered Poker Analysis Tool"
documentation = "https://github.com/gmanldn/pokertool"
```

### Python-Specific Configuration

For Python applications, ensure you have:

```toml
# pyproject.toml
[project]
name = "pokertool"
version = "1.0.0"
description = "AI-Powered Poker Analysis Tool"
requires-python = ">=3.12"

[project.scripts]
pokertool = "pokertool.main:main"

[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"
```

## Building with Buildpacks

### Basic Build

```bash
# Build with default Python buildpack
pack build pokertool \
  --builder paketobuildpacks/builder:base

# Build with specific builder
pack build pokertool \
  --builder gcr.io/buildpacks/builder:v1
```

### Paketo Buildpacks (Recommended)

```bash
# Build Python application
pack build pokertool \
  --builder paketobuildpacks/builder-jammy-base:latest \
  --env BP_CPYTHON_VERSION=3.12 \
  --env BP_PIP_VERSION=latest

# Build with specific buildpack
pack build pokertool \
  --builder paketobuildpacks/builder-jammy-base:latest \
  --buildpack paketo-buildpacks/python
```

### Google Cloud Buildpacks

```bash
# Build with Google Cloud Builder
pack build pokertool \
  --builder gcr.io/buildpacks/builder:v1 \
  --env GOOGLE_RUNTIME=python312
```

### Heroku Buildpacks

```bash
# Build with Heroku builder
pack build pokertool \
  --builder heroku/builder:22
```

## Advanced Configuration

### Custom Start Command

```toml
# project.toml
[[build.env]]
name = "BP_LAUNCHPOINT"
value = "./src/main.py"

[[build.env]]
name = "BP_PYTHON_FULL_VERSION"
value = "3.12.0"
```

### Procfile Support

Create `Procfile`:

```
web: python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
worker: python -m celery -A src.tasks worker
```

### Environment Variables

```bash
# Build with environment variables
pack build pokertool \
  --builder paketobuildpacks/builder:base \
  --env PORT=8000 \
  --env DEBUG=false \
  --env LOG_LEVEL=info
```

### Multi-Stage Dependencies

```toml
# project.toml
[[build.env]]
name = "BP_PIP_INSTALL_ARGS"
value = "--no-cache-dir --compile"

[[build.env]]
name = "BP_INCLUDE_FILES"
value = "requirements.txt:requirements-prod.txt"
```

## Running Built Images

### Basic Run

```bash
# Run the built image
docker run -p 8000:8000 pokertool

# Run with environment variables
docker run -p 8000:8000 \
  -e DEBUG=true \
  -e LOG_LEVEL=debug \
  pokertool
```

### With Volumes

```bash
# Run with persistent volumes
docker run -p 8000:8000 \
  -v $(pwd)/logs:/workspace/logs \
  -v $(pwd)/data:/workspace/data \
  pokertool
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Buildpack Build

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Pack CLI
        run: |
          curl -sSL "https://github.com/buildpacks/pack/releases/download/v0.31.0/pack-v0.31.0-linux.tgz" | \
          sudo tar -xz -C /usr/local/bin
      
      - name: Build with Buildpacks
        run: |
          pack build pokertool \
            --builder paketobuildpacks/builder-jammy-base:latest \
            --env BP_CPYTHON_VERSION=3.12
      
      - name: Test image
        run: |
          docker run -d --name test -p 8000:8000 pokertool
          sleep 10
          curl -f http://localhost:8000/health
          docker stop test
      
      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        run: |
          echo ${{ secrets.DOCKERHUB_TOKEN }} | docker login -u ${{ secrets.DOCKERHUB_USERNAME }} --password-stdin
          docker tag pokertool pokertool/pokertool:latest
          docker push pokertool/pokertool:latest
```

### GitLab CI

```yaml
buildpack-build:
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - apk add curl
    - curl -sSL "https://github.com/buildpacks/pack/releases/download/v0.31.0/pack-v0.31.0-linux.tgz" | tar -xz
    - mv pack /usr/local/bin/
  script:
    - pack build pokertool --builder paketobuildpacks/builder:base
    - docker run -d --name test pokertool
    - docker logs test
```

### Cloud Build (GCP)

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/k8s-skaffold/pack'
    args:
      - 'build'
      - 'gcr.io/$PROJECT_ID/pokertool'
      - '--builder=gcr.io/buildpacks/builder:v1'
images:
  - 'gcr.io/$PROJECT_ID/pokertool'
```

## Buildpack Comparison

### Paketo Buildpacks

**Pros:**
- Comprehensive Python support
- Regular updates
- Good documentation
- Active community

**Build Command:**
```bash
pack build pokertool \
  --builder paketobuildpacks/builder-jammy-base:latest
```

### Google Cloud Buildpacks

**Pros:**
- GCP integration
- Fast builds
- Minimal images

**Build Command:**
```bash
pack build pokertool \
  --builder gcr.io/buildpacks/builder:v1
```

### Heroku Buildpacks

**Pros:**
- Heroku compatibility
- Simple configuration
- Proven track record

**Build Command:**
```bash
pack build pokertool \
  --builder heroku/builder:22
```

## Optimization

### Layer Caching

```bash
# Use cache volume for faster builds
pack build pokertool \
  --builder paketobuildpacks/builder:base \
  --cache-image pokertool/cache
```

### Build Time Optimization

```bash
# Clear cache
pack build pokertool \
  --builder paketobuildpacks/builder:base \
  --clear-cache

# Verbose output
pack build pokertool \
  --builder paketobuildpacks/builder:base \
  --verbose
```

### Size Optimization

```toml
# project.toml - Exclude unnecessary files
[build]
exclude = [
    "tests/",
    "docs/",
    "examples/",
    "*.md",
    ".git/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    "node_modules/",
    ".vscode/",
    ".idea/"
]
```

## Inspecting Built Images

```bash
# Inspect image
pack inspect pokertool

# View buildpack metadata
pack inspect-image pokertool

# Check build info
docker inspect pokertool

# View layers
dive pokertool
```

## Rebase (Update Base Image)

Update base image without rebuilding:

```bash
# Rebase to new base image
pack rebase pokertool \
  --run-image paketobuildpacks/run:base-cnb

# Rebase with builder
pack rebase pokertool \
  --builder paketobuildpacks/builder:base
```

## Custom Buildpacks

### Create Custom Buildpack

```bash
# Create buildpack directory
mkdir -p custom-buildpack/{bin,buildpack.toml}

# buildpack.toml
cat > custom-buildpack/buildpack.toml << EOF
api = "0.8"

[buildpack]
id = "custom/pokertool"
version = "0.1.0"
name = "PokerTool Custom Buildpack"

[[stacks]]
id = "io.buildpacks.stacks.jammy"
EOF

# detect script
cat > custom-buildpack/bin/detect << 'EOF'
#!/usr/bin/env bash
set -e
if [[ -f requirements.txt ]] && [[ -f src/main.py ]]; then
  exit 0
else
  exit 100
fi
EOF

# build script
cat > custom-buildpack/bin/build << 'EOF'
#!/usr/bin/env bash
set -e
echo "---> Custom PokerTool buildpack"
# Add custom build logic
EOF

chmod +x custom-buildpack/bin/*
```

### Use Custom Buildpack

```bash
# Build with custom buildpack
pack build pokertool \
  --builder paketobuildpacks/builder:base \
  --buildpack ./custom-buildpack \
  --buildpack paketo-buildpacks/python
```

## Troubleshooting

### Detection Failures

```bash
# Check why detection failed
pack build pokertool --verbose

# Ensure required files exist
ls -la requirements.txt pyproject.toml
```

### Build Failures

```bash
# Clear cache and rebuild
pack build pokertool --clear-cache

# Use specific Python version
pack build pokertool \
  --env BP_CPYTHON_VERSION=3.12.0
```

### Runtime Issues

```bash
# Check container logs
docker run --rm pokertool

# Inspect environment
docker run --rm pokertool env

# Debug interactively
docker run --rm -it pokertool /bin/bash
```

### Performance Issues

```bash
# Use cache image
pack build pokertool --cache-image pokertool/cache

# Parallel builds
pack build pokertool --jobs 4
```

## Comparison: Buildpacks vs Dockerfile

| Feature | Buildpacks | Dockerfile |
|---------|-----------|------------|
| Maintenance | Low | High |
| Expertise Required | Low | Medium-High |
| Flexibility | Medium | High |
| Build Time (first) | Slower | Faster |
| Build Time (cached) | Fast | Fast |
| Image Size | Optimized | Variable |
| Security Updates | Automatic | Manual |
| Best Practices | Built-in | Manual |

## When to Use Buildpacks

**Use Buildpacks when:**
- Standard application structure
- Want automatic updates
- Prefer convention over configuration
- Need quick setup
- Team has limited Docker expertise

**Use Dockerfile when:**
- Complex custom requirements
- Need fine-grained control
- Non-standard architecture
- Existing Dockerfile works well
- Building system images

## Best Practices

1. **Use project.toml** - Configure buildpack behavior
2. **Specify versions** - Pin Python version
3. **Optimize dependencies** - Keep requirements.txt minimal
4. **Use caching** - Speed up builds with cache images
5. **Test locally** - Verify before CI/CD
6. **Monitor size** - Track image size over time
7. **Update builders** - Keep builders up to date
8. **Document choices** - Explain buildpack configuration

## Next Steps

- Review [Docker Compose Guide](DOCKER_COMPOSE.md)
- Compare with [Docker Optimization](DOCKER_OPTIMIZATION.md)
- Set up [Kubernetes Deployment](KUBERNETES.md)
- Test [Podman Support](PODMAN_GUIDE.md)

## References

- [Cloud Native Buildpacks](https://buildpacks.io/)
- [Paketo Buildpacks](https://paketo.io/)
- [Pack CLI Documentation](https://buildpacks.io/docs/tools/pack/)
- [Google Cloud Buildpacks](https://cloud.google.com/docs/buildpacks/overview)
- [Heroku Buildpacks](https://devcenter.heroku.com/articles/buildpacks)
