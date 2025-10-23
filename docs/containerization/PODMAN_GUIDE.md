# Podman Support & Testing Guide

## Overview

This guide covers using Podman as a lightweight, daemonless Docker alternative for PokerTool containerization. Podman is fully compatible with Docker and provides enhanced security through rootless containers.

## What is Podman?

Podman (Pod Manager) is an open-source container engine that:
- Runs containers without a daemon
- Supports rootless containers by default
- Is compatible with Docker CLI
- Works with existing Dockerfiles
- Supports Docker Compose via podman-compose

## Installation

### macOS

```bash
# Using Homebrew
brew install podman

# Initialize Podman machine
podman machine init
podman machine start

# Verify installation
podman --version
podman info
```

### Linux (Ubuntu/Debian)

```bash
# Add Podman repository
echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libpod:/stable/xUbuntu_$(lsb_release -rs)/ /" | \
  sudo tee /etc/apt/sources.list.d/devel:kubic:libpod:stable.list

# Add repository key
curl -L "https://download.opensuse.org/repositories/devel:/kubic:/libpod:/stable/xUbuntu_$(lsb_release -rs)/Release.key" | \
  sudo apt-key add -

# Install Podman
sudo apt-get update
sudo apt-get install -y podman

# Verify installation
podman --version
```

### Linux (Fedora/RHEL/CentOS)

```bash
# Install Podman (included by default on newer versions)
sudo dnf install -y podman

# Verify installation
podman --version
```

### Windows

```bash
# Using Chocolatey
choco install podman-desktop

# Or download from GitHub
# https://github.com/containers/podman/releases
```

## Basic Usage

### Docker Command Equivalents

Podman uses the same CLI interface as Docker:

```bash
# Build image
podman build -t pokertool:latest .

# Run container
podman run -d -p 8000:8000 pokertool:latest

# List containers
podman ps

# View logs
podman logs <container-id>

# Stop container
podman stop <container-id>

# Remove container
podman rm <container-id>

# List images
podman images

# Remove image
podman rmi pokertool:latest
```

### Docker Alias (Optional)

For seamless transition from Docker:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias docker=podman

# Reload shell
source ~/.bashrc
```

## Building PokerTool with Podman

### Standard Build

```bash
# Build from Dockerfile
podman build -t pokertool:latest .

# Build with specific platform
podman build --platform linux/amd64 -t pokertool:latest .

# Build with BuildKit-like features
podman build --layers -t pokertool:latest .
```

### Multi-Stage Build

```bash
# Podman supports multi-stage builds natively
podman build -f Dockerfile -t pokertool:latest .
```

### Build with Buildah

Buildah provides more control over image building:

```bash
# Install Buildah
sudo dnf install -y buildah

# Build with Buildah
buildah bud -t pokertool:latest .

# Or use Buildah for custom builds
buildah from python:3.12-alpine
buildah run working-container pip install -r requirements.txt
buildah commit working-container pokertool:latest
```

## Running PokerTool with Podman

### Basic Run

```bash
# Run in detached mode
podman run -d \
  --name pokertool \
  -p 8000:8000 \
  pokertool:latest

# Run with environment variables
podman run -d \
  --name pokertool \
  -p 8000:8000 \
  -e DEBUG=false \
  -e LOG_LEVEL=info \
  pokertool:latest

# Run with volumes
podman run -d \
  --name pokertool \
  -p 8000:8000 \
  -v ./logs:/app/logs:Z \
  -v ./data:/app/data:Z \
  pokertool:latest
```

### Rootless Containers

Podman's default rootless mode:

```bash
# Run as non-root user (default)
podman run -d --name pokertool -p 8000:8000 pokertool:latest

# Check user inside container
podman exec pokertool whoami

# Run with specific user
podman run -d --user 1000:1000 pokertool:latest
```

### SELinux Considerations

On SELinux-enabled systems (Fedora, RHEL, CentOS):

```bash
# Use :Z for private volume
podman run -v ./data:/app/data:Z pokertool:latest

# Use :z for shared volume
podman run -v ./data:/app/data:z pokertool:latest

# Disable SELinux labeling (not recommended)
podman run --security-opt label=disable pokertool:latest
```

## Podman Compose

### Installation

```bash
# Using pip
pip install podman-compose

# Or using package manager (Fedora)
sudo dnf install podman-compose

# Verify installation
podman-compose --version
```

### Using docker-compose.yml

Podman Compose is compatible with Docker Compose files:

```bash
# Start services
podman-compose up -d

# View logs
podman-compose logs -f

# Stop services
podman-compose down

# Rebuild services
podman-compose build

# Scale services
podman-compose up -d --scale backend=3
```

### Podman Compose vs Docker Compose

```bash
# docker-compose.yml works with both
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs:Z  # Note: :Z for SELinux
```

## Pods (Podman-Specific Feature)

Pods are groups of containers that share network namespace:

```bash
# Create a pod
podman pod create --name pokertool-pod -p 8000:8000

# Run containers in pod
podman run -d --pod pokertool-pod --name backend pokertool-backend:latest
podman run -d --pod pokertool-pod --name frontend pokertool-frontend:latest

# List pods
podman pod ps

# View pod details
podman pod inspect pokertool-pod

# Stop pod
podman pod stop pokertool-pod

# Remove pod
podman pod rm pokertool-pod
```

## Systemd Integration

Run containers as systemd services:

### Generate Service File

```bash
# Generate systemd unit file
podman generate systemd --new --name pokertool > pokertool.service

# Copy to systemd directory
sudo cp pokertool.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable pokertool.service
sudo systemctl start pokertool.service

# Check status
sudo systemctl status pokertool.service
```

### User-Level Service

```bash
# Generate user service
podman generate systemd --new --name pokertool > ~/.config/systemd/user/pokertool.service

# Enable and start
systemctl --user enable pokertool.service
systemctl --user start pokertool.service

# Enable lingering (start on boot)
loginctl enable-linger $USER
```

## Image Registries

### Docker Hub

```bash
# Login to Docker Hub
podman login docker.io

# Pull image
podman pull docker.io/pokertool/pokertool:latest

# Push image
podman push docker.io/pokertool/pokertool:latest
```

### GitHub Container Registry

```bash
# Login to GHCR
echo $GHCR_TOKEN | podman login ghcr.io -u $USERNAME --password-stdin

# Pull image
podman pull ghcr.io/gmanldn/pokertool:latest

# Push image
podman tag pokertool:latest ghcr.io/gmanldn/pokertool:latest
podman push ghcr.io/gmanldn/pokertool:latest
```

## Testing Compatibility

### Test Script

Create `test-podman.sh`:

```bash
#!/bin/bash

echo "Testing Podman compatibility for PokerTool..."

# Build image
echo "Building image..."
podman build -t pokertool:test .
if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

# Run container
echo "Running container..."
podman run -d --name pokertool-test -p 8000:8000 pokertool:test
if [ $? -ne 0 ]; then
    echo "Container failed to start!"
    exit 1
fi

# Wait for startup
sleep 10

# Test health endpoint
echo "Testing health endpoint..."
curl -f http://localhost:8000/health
if [ $? -ne 0 ]; then
    echo "Health check failed!"
    podman logs pokertool-test
    podman stop pokertool-test
    podman rm pokertool-test
    exit 1
fi

# Cleanup
echo "Cleaning up..."
podman stop pokertool-test
podman rm pokertool-test

echo "All tests passed!"
```

### Automated Testing

```bash
# Make executable
chmod +x test-podman.sh

# Run tests
./test-podman.sh
```

## Migration from Docker

### Export and Import

```bash
# Export Docker image
docker save pokertool:latest -o pokertool.tar

# Import to Podman
podman load -i pokertool.tar

# Verify import
podman images | grep pokertool
```

### Docker Socket Emulation

```bash
# Enable Podman socket
systemctl --user enable --now podman.socket

# Set Docker environment variables
export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock

# Use Docker CLI with Podman
docker ps  # Actually uses Podman!
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Podman Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Podman
        run: |
          sudo apt-get update
          sudo apt-get install -y podman
      
      - name: Build with Podman
        run: podman build -t pokertool:latest .
      
      - name: Test container
        run: |
          podman run -d --name test -p 8000:8000 pokertool:latest
          sleep 10
          curl -f http://localhost:8000/health
          podman stop test
```

### GitLab CI

```yaml
build-podman:
  image: quay.io/podman/stable
  script:
    - podman build -t pokertool:latest .
    - podman run -d --name test pokertool:latest
    - podman logs test
```

## Performance Comparison

### Build Time

```bash
# Docker build
time docker build -t pokertool:docker .

# Podman build
time podman build -t pokertool:podman .
```

### Runtime Performance

```bash
# Docker run
time docker run --rm pokertool:docker python -c "print('test')"

# Podman run
time podman run --rm pokertool:podman python -c "print('test')"
```

## Troubleshooting

### Port Binding Issues (Rootless)

```bash
# Ports < 1024 require root or special permissions
# Use ports >= 1024 for rootless containers

# Or adjust unprivileged port range
echo 'net.ipv4.ip_unprivileged_port_start=80' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Volume Mount Permissions

```bash
# Fix SELinux context
chcon -Rt svirt_sandbox_file_t ./data

# Or use :Z flag
podman run -v ./data:/app/data:Z pokertool:latest
```

### Network Issues

```bash
# Reset network
podman system reset

# Or recreate network
podman network rm podman
podman network create podman
```

### Storage Issues

```bash
# Check storage
podman system df

# Prune unused data
podman system prune -a

# Reset storage
podman system reset
```

## Best Practices

1. **Use rootless mode** - Default and more secure
2. **SELinux labeling** - Use :Z or :z for volumes
3. **Systemd integration** - For production deployments
4. **Pods for microservices** - Group related containers
5. **Regular updates** - Keep Podman up to date
6. **Resource limits** - Set memory and CPU limits
7. **Health checks** - Use --health-cmd for monitoring
8. **Network policies** - Restrict container networking

## Advantages over Docker

1. **Daemonless** - No background daemon required
2. **Rootless** - Enhanced security by default
3. **Systemd integration** - Native service management
4. **Pods** - Kubernetes-like pod support
5. **Open source** - No commercial restrictions
6. **Compatible** - Drop-in Docker replacement

## Limitations

1. **Compose** - podman-compose less mature than docker-compose
2. **BuildKit** - Some BuildKit features not supported
3. **Ecosystem** - Smaller third-party tool ecosystem
4. **Documentation** - Less extensive than Docker docs

## Next Steps

- Review [Docker Compose Guide](DOCKER_COMPOSE.md)
- Implement [Buildpacks](BUILDPACKS.md)
- Set up [Kubernetes Deployment](KUBERNETES.md)

## References

- [Podman Official Documentation](https://docs.podman.io/)
- [Podman vs Docker](https://docs.podman.io/en/latest/Introduction.html)
- [Rootless Containers](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md)
- [Podman Compose](https://github.com/containers/podman-compose)
