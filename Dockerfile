# 🦈 Aureon Trading System - DigitalOcean Deployment
# Production-ready Docker image for autonomous trading

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080
ENV AUREON_STATE_DIR=/app/state

# Create directories for state files
RUN mkdir -p /app/state /app/logs

# Install supervisor for process management
RUN pip install --no-cache-dir supervisor

# Copy supervisor config
COPY deploy/supervisord.conf /etc/supervisord.conf

# Expose HTTP port for DO App Platform
EXPOSE 8080

# Healthcheck - verify web UI is responding
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run both trading engine + web UI via supervisor
CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]
