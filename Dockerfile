# Watcher AI Backend - Production Dockerfile
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION=1.0.0
ARG COMMIT_SHA

# Set labels
LABEL maintainer="Sean McDonnell <sean@mothership-ai.com>"
LABEL version="${VERSION}"
LABEL description="Watcher AI - Real-Time Hallucination Defense Backend"
LABEL build-date="${BUILD_DATE}"
LABEL commit-sha="${COMMIT_SHA}"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO

# Create non-root user
RUN groupadd -r watcher && useradd -r -g watcher watcher

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY watcher_ai_sdk/ ./watcher_ai_sdk/

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/uploads && \
    chown -R watcher:watcher /app

# Switch to non-root user
USER watcher

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "-m", "uvicorn", "src.api.main_realtime:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]