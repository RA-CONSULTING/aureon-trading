# 🦈 Aureon Trading System - DigitalOcean Deployment
# Production-ready Docker image for autonomous trading with parallel processes

FROM python:3.12-slim

# Install system dependencies including supervisor for parallel process management
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    ca-certificates \
    supervisor \
    procps \
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
ENV AUREON_ENABLE_AUTONOMOUS_CONTROL=1

# Create directories for state files and logs
RUN mkdir -p /app/state /app/logs /var/log/supervisor

# Make startup scripts executable
RUN chmod +x /app/deploy/start_orca.sh 2>/dev/null || true

# Expose HTTP port for DO App Platform
EXPOSE 8080

# 👑 PARALLEL STARTUP: Use supervisord to run Command Center + Orca + Autonomous Engine together
# This ensures all parallel processes start on boot in Digital Ocean
CMD ["supervisord", "-n", "-c", "/app/deploy/supervisord.conf"]
