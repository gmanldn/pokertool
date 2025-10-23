# Docker Image Publishing Guide

## Overview

This guide covers automated Docker image publishing to Docker Hub and GitHub Container Registry (GHCR) for PokerTool, including multi-architecture builds and security scanning.

## Publishing Platforms

### Docker Hub
- **URL**: https://hub.docker.com
- **Image Name**: `pokertool/pokertool`
- **Visibility**: Public (or Private)
- **Benefits**: Wide adoption, easy discovery, robust infrastructure

### GitHub Container Registry (GHCR)
- **URL**: https://ghcr.io
- **Image Name**: `ghcr.io/gmanldn/pokertool`
- **Visibility**: Public (or Private)
- **Benefits**: Integrated with GitHub, free for public repos, unlimited bandwidth

## Prerequisites

### Docker Hub Setup

1. Create Docker Hub account at https://hub.docker.com
2. Create repository: `pokertool/pokertool`
3. Generate access token:
   - Settings → Security → New Access Token
   - Name: `github-actions`
   - Permissions: Read, Write, Delete

### GitHub Container Registry Setup

1. Enable GHCR for your repository
2. Generate Personal Access Token (PAT):
   - Settings → Developer settings → Personal access tokens
   - Permissions: `write:packages`, `read:packages`, `delete:packages`

### GitHub Secrets Configuration

Add secrets to your repository:
- Settings → Secrets and variables → Actions → New repository secret

Required secrets:
```
DOCKERHUB_USERNAME: your_dockerhub_username
DOCKERHUB_TOKEN: your_dockerhub_token
GHCR_TOKEN: your_github_pat
```

## GitHub Actions Workflow

Create `.github/workflows/docker-publish.yml`:

```yaml
name: Docker Image Publishing

on:
  push:
    branches:
      - main
      - release/*
    tags:
      - 'v*.*.*'
  pull_request:
    branches:
      - main
  workflow_dispatch:

env:
  REGISTRY_IMAGE_DOCKERHUB: pokertool/pokertool
  REGISTRY_IMAGE_GHCR: ghcr.io/gmanldn/pokertool

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write
    
    strategy:
      fail-fast: false
      matrix:
        platform:
          - linux/amd64
          - linux/arm64
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ env.REGISTRY_IMAGE_DOCKERHUB }}
            ${{ env.REGISTRY_IMAGE_GHCR }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Login to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Login to GitHub Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push by digest
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: ${{ matrix.platform }}
          labels: ${{ steps.meta.outputs.labels }}
          outputs: type=image,name=${{ env.REGISTRY_IMAGE_DOCKERHUB }},push-by-digest=true,name-canonical=true,push=${{ github.event_name != 'pull_request' }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Export digest
        run: |
          mkdir -p /tmp/digests
          digest="${{ steps.build.outputs.digest }}"
          touch "/tmp/digests/${digest#sha256:}"
      
      - name: Upload digest
        uses: actions/upload-artifact@v4
        with:
          name: digests-${{ matrix.platform }}
          path: /tmp/digests/*
          if-no-files-found: error
          retention-days: 1

  merge:
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.event_name != 'pull_request'
    steps:
      - name: Download digests
        uses: actions/download-artifact@v4
        with:
          path: /tmp/digests
          pattern: digests-*
          merge-multiple: true
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ env.REGISTRY_IMAGE_DOCKERHUB }}
            ${{ env.REGISTRY_IMAGE_GHCR }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Create manifest list and push
        working-directory: /tmp/digests
        run: |
          docker buildx imagetools create $(jq -cr '.tags | map("-t " + .) | join(" ")' <<< "$DOCKER_METADATA_OUTPUT_JSON") \
            $(printf '${{ env.REGISTRY_IMAGE_DOCKERHUB }}@sha256:%s ' *)
          docker buildx imagetools create $(jq -cr '.tags | map("-t " + .) | join(" ")' <<< "$DOCKER_METADATA_OUTPUT_JSON") \
            $(printf '${{ env.REGISTRY_IMAGE_GHCR }}@sha256:%s ' *)
      
      - name: Inspect image
        run: |
          docker buildx imagetools inspect ${{ env.REGISTRY_IMAGE_DOCKERHUB }}:${{ steps.meta.outputs.version }}
          docker buildx imagetools inspect ${{ env.REGISTRY_IMAGE_GHCR }}:${{ steps.meta.outputs.version }}

  security-scan:
    runs-on: ubuntu-latest
    needs: merge
    if: github.event_name != 'pull_request'
    steps:
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY_IMAGE_DOCKERHUB }}:latest
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

## Image Tagging Strategy

### Semantic Versioning Tags

For release `v1.2.3`:
- `latest` - Latest stable release
- `1` - Major version
- `1.2` - Major.minor version
- `1.2.3` - Full semantic version
- `v1.2.3` - With v prefix

### Branch Tags

- `main` - Latest commit on main branch
- `release-100.4.0` - Branch name
- `main-a1b2c3d` - Branch + short commit SHA

### PR Tags

- `pr-123` - Pull request number

## Multi-Architecture Builds

### Supported Platforms

- `linux/amd64` - Intel/AMD 64-bit (most common)
- `linux/arm64` - ARM 64-bit (Apple Silicon, AWS Graviton)
- `linux/arm/v7` - ARM 32-bit (Raspberry Pi)

### QEMU Setup

QEMU enables building for multiple architectures on a single host:

```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3

- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```

### Platform-Specific Builds

```dockerfile
# Platform-aware Dockerfile
ARG TARGETPLATFORM
ARG BUILDPLATFORM

RUN echo "Building on $BUILDPLATFORM for $TARGETPLATFORM"

# Platform-specific optimization
RUN case "$TARGETPLATFORM" in \
    "linux/amd64") \
        pip install --no-cache-dir numpy==1.24.0 ;; \
    "linux/arm64") \
        pip install --no-cache-dir numpy==1.24.0 ;; \
    *) \
        echo "Unsupported platform: $TARGETPLATFORM" && exit 1 ;; \
    esac
```

## Manual Publishing

### Build Multi-Arch Image Locally

```bash
# Create builder
docker buildx create --name multiarch --use

# Build and push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag pokertool/pokertool:latest \
  --tag ghcr.io/gmanldn/pokertool:latest \
  --push \
  .
```

### Build for Specific Platform

```bash
# Build for ARM64
docker buildx build \
  --platform linux/arm64 \
  --tag pokertool/pokertool:arm64 \
  --push \
  .

# Build for AMD64
docker buildx build \
  --platform linux/amd64 \
  --tag pokertool/pokertool:amd64 \
  --push \
  .
```

## Docker Hub README

Create `README.dockerhub.md` for Docker Hub description:

```markdown
# PokerTool - AI-Powered Poker Analysis

Real-time poker analysis and decision support tool.

## Quick Start

```bash
docker run -d -p 8000:8000 pokertool/pokertool:latest
```

Open http://localhost:8000 in your browser.

## Supported Architectures

- `linux/amd64` - Intel/AMD 64-bit
- `linux/arm64` - ARM 64-bit (Apple Silicon, AWS Graviton)

## Configuration

Use environment variables:

```bash
docker run -d \
  -p 8000:8000 \
  -e DEBUG=false \
  -e LOG_LEVEL=info \
  pokertool/pokertool:latest
```

## Volumes

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  pokertool/pokertool:latest
```

## Documentation

- [GitHub Repository](https://github.com/gmanldn/pokertool)
- [Full Documentation](https://github.com/gmanldn/pokertool/blob/main/README.md)
- [Installation Guide](https://github.com/gmanldn/pokertool/blob/main/INSTALL.md)

## Support

- [GitHub Issues](https://github.com/gmanldn/pokertool/issues)
- [GitHub Discussions](https://github.com/gmanldn/pokertool/discussions)
```

## Security Scanning

### Trivy Integration

Scan for vulnerabilities:

```bash
# Scan image
trivy image pokertool/pokertool:latest

# Scan with severity filter
trivy image --severity HIGH,CRITICAL pokertool/pokertool:latest

# Generate report
trivy image --format json --output report.json pokertool/pokertool:latest
```

### Snyk Integration

```yaml
- name: Run Snyk scan
  uses: snyk/actions/docker@master
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
  with:
    image: pokertool/pokertool:latest
    args: --severity-threshold=high
```

### Grype Integration

```bash
# Scan with Grype
grype pokertool/pokertool:latest
```

## Image Signing

### Cosign Setup

```bash
# Generate key pair
cosign generate-key-pair

# Sign image
cosign sign --key cosign.key pokertool/pokertool:latest

# Verify signature
cosign verify --key cosign.pub pokertool/pokertool:latest
```

### GitHub Actions Integration

```yaml
- name: Install Cosign
  uses: sigstore/cosign-installer@v3

- name: Sign image
  run: |
    cosign sign --yes --key env://COSIGN_KEY \
      pokertool/pokertool:${{ steps.meta.outputs.version }}
  env:
    COSIGN_KEY: ${{ secrets.COSIGN_PRIVATE_KEY }}
    COSIGN_PASSWORD: ${{ secrets.COSIGN_PASSWORD }}
```

## Registry Configuration

### Docker Hub Repository Settings

1. **Visibility**: Set to Public or Private
2. **Description**: Add comprehensive description
3. **Categories**: Add relevant tags (tools, poker, analytics)
4. **README**: Link to README.dockerhub.md
5. **Builds**: Disable automated builds (use GitHub Actions)

### GHCR Repository Settings

1. **Visibility**: Settings → Packages → Change visibility
2. **Permissions**: Manage package access
3. **README**: Automatically synced from repository

## Cleanup Policies

### Docker Hub

Configure retention policy:
- Keep last 10 tags
- Keep all tags for 90 days
- Delete untagged images after 1 day

### GHCR

```bash
# Delete old versions
gh api --method DELETE \
  /user/packages/container/pokertool/versions/VERSION_ID
```

## Monitoring

### Download Statistics

```bash
# Docker Hub stats
curl -s "https://hub.docker.com/v2/repositories/pokertool/pokertool/" | jq .pull_count

# GHCR stats (requires authentication)
gh api /user/packages/container/pokertool/versions
```

### Webhook Notifications

Configure webhooks for:
- New image published
- Security scan results
- Pull activity

## Best Practices

1. **Tag immutably** - Never overwrite existing tags
2. **Sign images** - Use Cosign for verification
3. **Scan regularly** - Automate security scanning
4. **Multi-arch support** - Build for multiple platforms
5. **README updates** - Keep documentation current
6. **Cleanup old images** - Implement retention policies
7. **Use cache** - Leverage BuildKit cache for faster builds
8. **Monitor pulls** - Track download statistics

## Troubleshooting

### Authentication Failures

```bash
# Test Docker Hub login
echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USERNAME --password-stdin

# Test GHCR login
echo $GHCR_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin
```

### Build Failures

```bash
# Enable debug logging
docker buildx build --progress=plain --no-cache .

# Check builder status
docker buildx ls
```

### Multi-Arch Issues

```bash
# Verify QEMU installation
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Test cross-platform build
docker buildx build --platform linux/arm64 --load .
```

## Local Testing

```bash
# Build locally
docker buildx build --platform linux/amd64,linux/arm64 -t pokertool:test .

# Test AMD64
docker run --platform linux/amd64 pokertool:test

# Test ARM64
docker run --platform linux/arm64 pokertool:test
```

## Next Steps

- Review [Docker Compose Guide](DOCKER_COMPOSE.md)
- Implement [Kubernetes Deployment](KUBERNETES.md)
- Set up [Podman Support](PODMAN_GUIDE.md)

## References

- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [GitHub Actions for Docker](https://docs.docker.com/build/ci/github-actions/)
- [Multi-platform Images](https://docs.docker.com/build/building/multi-platform/)
