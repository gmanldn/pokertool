# Multi-stage Dockerfile for PokerTool
# Optimized for production deployment with minimal image size

# ============================================================================
# Stage 1: Backend Builder
# ============================================================================
FROM python:3.12-slim as backend-builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first (for layer caching)
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Frontend Builder
# ============================================================================
FROM node:18-alpine as frontend-builder

WORKDIR /build

# Copy package files
COPY pokertool-frontend/package.json pokertool-frontend/package-lock.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY pokertool-frontend/ ./

# Build frontend
RUN npm run build

# ============================================================================
# Stage 3: Production Runtime
# ============================================================================
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 pokertool && \
    mkdir -p /app/data /app/logs && \
    chown -R pokertool:pokertool /app

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=pokertool:pokertool src/ ./src/
COPY --chown=pokertool:pokertool scripts/ ./scripts/
COPY --chown=pokertool:pokertool requirements.txt ./

# Copy frontend build
COPY --from=frontend-builder --chown=pokertool:pokertool /build/build ./pokertool-frontend/build

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_TYPE=postgresql \
    API_PORT=5001 \
    LOG_LEVEL=INFO \
    ENABLE_API_CACHING=true

# Expose ports
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Switch to non-root user
USER pokertool

# Start application
CMD ["python", "-m", "uvicorn", "pokertool.api:app", "--host", "0.0.0.0", "--port", "5001"]
