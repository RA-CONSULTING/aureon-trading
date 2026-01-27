#!/bin/bash
# DigitalOcean deployment setup script for Aureon Truth Prediction System
# Run this on a fresh Ubuntu 22.04/24.04 droplet

set -e

echo "🌊 Aureon Trading System - DigitalOcean Setup"
echo "================================================"

# 1. Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Install Python 3.12+ (if not present)
echo "🐍 Installing Python 3.12..."
sudo apt-get install -y python3.12 python3.12-venv python3-pip git

# 3. Install system dependencies
echo "📚 Installing system dependencies..."
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev jq curl

# 4. Create application directory
APP_DIR="/opt/aureon-trading"
echo "📁 Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
cd $APP_DIR

# 5. Clone repository (if not already present)
if [ ! -d ".git" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/your-repo/aureon-trading.git .
fi

# 6. Create Python virtual environment
echo "🔧 Creating Python virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# 7. Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install websockets asyncio requests python-dotenv

# If you have a requirements.txt:
# pip install -r requirements.txt

# 8. Create required directories with proper permissions
echo "📂 Creating data directories..."
mkdir -p ws_cache logs
chmod 755 ws_cache logs

# 9. Create environment file
echo "🔐 Creating .env file..."
cat > .env << 'EOF'
# Exchange API Keys (replace with your real keys)
KRAKEN_API_KEY=your_kraken_api_key_here
KRAKEN_API_SECRET=your_kraken_secret_here
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_secret_here
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_API_SECRET=your_alpaca_secret_here

# Paths (DigitalOcean-compatible)
WS_PRICE_CACHE_PATH=/opt/aureon-trading/ws_cache/ws_prices.json
LOG_PATH=/opt/aureon-trading/logs

# Network settings
HOST=0.0.0.0
PORT=8080
EOF

chmod 600 .env

# 10. Create systemd service for WebSocket feeder
echo "🔧 Creating systemd service for WS feeder..."
sudo tee /etc/systemd/system/aureon-ws-feeder.service > /dev/null << EOF
[Unit]
Description=Aureon WebSocket Market Data Feeder
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/ws_market_data_feeder.py --binance --write-interval-s 1.0
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/logs/ws-feeder.log
StandardError=append:$APP_DIR/logs/ws-feeder-error.log

[Install]
WantedBy=multi-user.target
EOF

# 11. Create systemd service for Truth Prediction Engine
echo "🔧 Creating systemd service for Truth Prediction Engine..."
sudo tee /etc/systemd/system/aureon-truth-engine.service > /dev/null << EOF
[Unit]
Description=Aureon Truth Prediction Engine (Live TV Station)
After=network.target aureon-ws-feeder.service
Requires=aureon-ws-feeder.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/aureon_live_tv_station.py
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/logs/truth-engine.log
StandardError=append:$APP_DIR/logs/truth-engine-error.log

[Install]
WantedBy=multi-user.target
EOF

# 12. Create systemd service for Orca trading (optional - for production)
echo "🔧 Creating systemd service for Orca trading..."
sudo tee /etc/systemd/system/aureon-orca-trading.service > /dev/null << EOF
[Unit]
Description=Aureon Orca Trading System
After=network.target aureon-truth-engine.service
Requires=aureon-truth-engine.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
# WARNING: Only enable in production with real capital!
# ExecStart=$APP_DIR/venv/bin/python $APP_DIR/orca_complete_kill_cycle.py --dry-run
ExecStart=/bin/true
Restart=on-failure
RestartSec=30
StandardOutput=append:$APP_DIR/logs/orca-trading.log
StandardError=append:$APP_DIR/logs/orca-trading-error.log

[Install]
WantedBy=multi-user.target
EOF

# 13. Reload systemd and enable services
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

echo "✅ Enabling services..."
sudo systemctl enable aureon-ws-feeder.service
sudo systemctl enable aureon-truth-engine.service
# sudo systemctl enable aureon-orca-trading.service  # Uncomment for production

# 14. Create logrotate config to prevent disk fill
echo "📜 Creating logrotate configuration..."
sudo tee /etc/logrotate.d/aureon-trading > /dev/null << EOF
$APP_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $USER $USER
}

$APP_DIR/*.jsonl {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $USER $USER
}
EOF

# 15. Create monitoring script
echo "📊 Creating monitoring script..."
cat > monitor.sh << 'EOF'
#!/bin/bash
# Monitor Aureon services

echo "🔍 Aureon System Status"
echo "======================="
echo ""

echo "📡 WS Feeder:"
systemctl status aureon-ws-feeder.service --no-pager | head -5
echo ""

echo "🌉 Truth Engine:"
systemctl status aureon-truth-engine.service --no-pager | head -5
echo ""

echo "📊 Recent Predictions:"
if [ -f "aureon_truth_prediction_state.json" ]; then
    jq -r '.validations[-5:] | .[] | "\(.symbol): \(.correct) (truth=\(.geometric_truth))"' aureon_truth_prediction_state.json 2>/dev/null || echo "No validations yet"
else
    echo "State file not found"
fi
echo ""

echo "💾 Disk Usage:"
df -h $APP_DIR | tail -1
echo ""

echo "📝 Recent Logs (last 5 lines):"
echo "--- WS Feeder ---"
tail -5 logs/ws-feeder.log 2>/dev/null || echo "No logs yet"
echo ""
echo "--- Truth Engine ---"
tail -5 logs/truth-engine.log 2>/dev/null || echo "No logs yet"
EOF

chmod +x monitor.sh

# 16. Create backup script
echo "💾 Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash
# Backup critical state files

BACKUP_DIR="/opt/aureon-trading/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup state files
cp aureon_truth_prediction_state.json $BACKUP_DIR/state_$DATE.json 2>/dev/null
cp live_tv_stream.jsonl $BACKUP_DIR/stream_$DATE.jsonl 2>/dev/null
cp probability_ultimate_state.json $BACKUP_DIR/prob_$DATE.json 2>/dev/null

# Keep only last 30 backups
ls -t $BACKUP_DIR/*.json | tail -n +31 | xargs rm -f 2>/dev/null
ls -t $BACKUP_DIR/*.jsonl | tail -n +31 | xargs rm -f 2>/dev/null

echo "✅ Backup complete: $DATE"
EOF

chmod +x backup.sh

# 17. Add backup to crontab (every 6 hours)
echo "⏰ Setting up automated backups..."
(crontab -l 2>/dev/null; echo "0 */6 * * * cd $APP_DIR && ./backup.sh >> logs/backup.log 2>&1") | crontab -

# 18. Create firewall rules (if ufw is enabled)
if command -v ufw &> /dev/null; then
    echo "🔥 Configuring firewall..."
    sudo ufw allow 22/tcp  # SSH
    # sudo ufw allow 8080/tcp  # If you add a web interface later
    echo "Firewall configured (SSH allowed)"
fi

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "📝 Next Steps:"
echo "1. Edit .env file with your real API keys:"
echo "   nano .env"
echo ""
echo "2. Start services:"
echo "   sudo systemctl start aureon-ws-feeder"
echo "   sudo systemctl start aureon-truth-engine"
echo ""
echo "3. Check status:"
echo "   ./monitor.sh"
echo ""
echo "4. View logs:"
echo "   tail -f logs/ws-feeder.log"
echo "   tail -f logs/truth-engine.log"
echo ""
echo "5. Check predictions:"
echo "   cat aureon_truth_prediction_state.json | jq '.validations[-10:]'"
echo ""
echo "⚠️  IMPORTANT: Do NOT enable orca-trading.service until you've tested thoroughly!"
echo ""
