# Multi-stage build for PokerTool
FROM node:18-alpine AS frontend-build

# Build frontend
WORKDIR /app/frontend
COPY pokertool-frontend/package*.json ./
RUN npm ci --only=production
COPY pokertool-frontend/ ./
RUN npm run build

# Python backend
FROM python:3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY src/ src/
COPY launch_pokertool.py .
COPY poker_config.json .

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/build /app/static

# Create non-root user for security
RUN groupadd -r pokertool && useradd -r -g pokertool pokertool
RUN chown -R pokertool:pokertool /app
USER pokertool

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["python", "launch_pokertool.py", "--production"]
