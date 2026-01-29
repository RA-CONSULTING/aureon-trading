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

# Autonomous volatility trading defaults
ENV MODE=parallel
ENV MAX_POSITIONS=3
ENV AMOUNT_PER_POSITION=5.0
ENV TARGET_PCT=1.0
ENV MIN_CHANGE_PCT=0.25

# Create directories for state files and logs
RUN mkdir -p /app/state /app/logs /var/log/supervisor

# Make all startup scripts executable
RUN chmod +x /app/deploy/*.sh 2>/dev/null || true

# Create empty state files if they don't exist (prevents errors on first boot)
RUN touch /app/queen_redistribution_state.json \
    /app/power_station_state.json \
    /app/queen_energy_balance.json \
    /app/aureon_kraken_state.json \
    /app/binance_truth_tracker_state.json \
    /app/alpaca_truth_tracker_state.json \
    /app/7day_pending_validations.json && \
    echo '{"last_update":0.0,"total_net_energy_gained":0.0,"total_blocked_drains_avoided":0.0,"decisions_count":0,"executions_count":0,"recent_decisions":[],"recent_executions":[]}' > /app/queen_redistribution_state.json && \
    echo '{"status":"STOPPED","cycles_run":0,"total_energy_now":0.0,"energy_deployed":0.0,"net_flow":0.0,"efficiency":0.0}' > /app/power_station_state.json && \
    echo '{"last_update":0,"total_energy_in":0.0,"total_energy_out":0.0,"net_balance":0.0}' > /app/queen_energy_balance.json

# Expose ports
EXPOSE 8080 8800

# Health check - works for both parallel (HTTP) and autonomous (file) modes
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD if [ "$MODE" = "autonomous" ]; then python -c "import os, time; exit(0 if os.path.exists('/app/state') and any(os.path.getmtime(f) > time.time()-120 for f in ['/app/7day_pending_validations.json', '/app/active_position.json']) else 1)"; else curl -f http://localhost:8080/health || exit 1; fi

# Run startup validation before supervisor
RUN chmod +x /app/deploy/validate_startup.sh

# 👑 PARALLEL STARTUP: Use supervisord to run all systems
# Systems: Command Center + Orca + Autonomous Engine + Queen Power System + Kraken Cache
# For standalone autonomous mode: docker run -e MODE=autonomous aureon-trading
ENTRYPOINT ["/bin/bash", "-c", "if [ \"$MODE\" = \"autonomous\" ]; then exec python -u orca_complete_kill_cycle.py --autonomous ${MAX_POSITIONS:-3} ${AMOUNT_PER_POSITION:-5.0} ${TARGET_PCT:-1.0}; else /app/deploy/validate_startup.sh && exec supervisord -n -c /app/deploy/supervisord.conf; fi"]
