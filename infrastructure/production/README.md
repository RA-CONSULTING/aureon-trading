# 🎮👑 AUREON Trading System - Production Package

## Overview

AUREON is a quantum trading system powered by the **Queen's 4-Phase Master Plan**. The primary engine (`orca_complete_kill_cycle.py`) runs in a secure, sandboxed Docker container with a game-like launcher experience.

**Main Features:**
- 👑 **Queen's 4-Phase Strategy**: Adapts from $248 → $1B (Seed → Growth → Explosion → Billion)
- 🐝 **Phase-Aware Scoring**: Prioritizes opportunities aligned with current capital phase
- ⚡ **Batten Matrix**: 3-pass validation, 4th-pass execution (precision trading)
- 🌊 **Multi-Exchange**: Simultaneous scanning across Binance, Kraken, Alpaca

## Quick Start

### Windows
**Plug & Play (Recommended)**

**Option 1: One-line PowerShell install**
```powershell
irm https://raw.githubusercontent.com/RA-CONSULTING/aureon-trading/main/production/Install-AUREON.ps1 | iex
```

**Option 2: Double-click installer**
1. Download [Install-AUREON-Windows.bat](Install-AUREON-Windows.bat)
2. Double-click to install

**Option 3: Direct EXE download**
1. Download [AUREON.exe](https://github.com/RA-CONSULTING/aureon-trading/releases/latest/download/AUREON.exe)
2. Double-click to run

### Linux/macOS
```bash
chmod +x install.sh
./install.sh
```

### Docker (Advanced)
For containerized deployments or servers, use Docker with [install-windows.bat](install-windows.bat) or [install.sh](install.sh).

## Features

- 🎮 **Game-like Experience**: Red Alert 2 style launcher with Command Center UI
- 🔒 **Sandboxed**: Runs in isolated Docker container
- 🛡️ **Safe Defaults**: Starts in DRY RUN mode (paper trading)
- ⚙️ **Setup Wizard**: First-run configuration for API keys
- 📊 **Dashboard**: Web-based Command Center at http://localhost:8888
- 💾 **Persistent Data**: Trading state preserved across restarts

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    AUREON CONTAINER                              │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   COMMAND   │  │   TRADING   │  │   QUEEN     │              │
│  │   CENTER    │  │   ENGINE    │  │   HIVE      │              │
│  │   (UI)      │  │   (Core)    │  │   (Brain)   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                 ┌────────▼────────┐                              │
│                 │   THOUGHT BUS   │                              │
│                 │   (Event Mesh)  │                              │
│                 └────────┬────────┘                              │
│                          │                                       │
│         ┌────────────────┼────────────────┐                      │
│         │                │                │                      │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐              │
│  │   KRAKEN    │  │   ALPACA    │  │   BINANCE   │              │
│  │   CLIENT    │  │   CLIENT    │  │   CLIENT    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└──────────────────────────────────────────────────────────────────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                  ════════▼════════
                   EXCHANGE APIs
                  ═════════════════
```

## Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Game** (default) | `--mode game` | Full UI + Queen's Trading Engine |
| **Trading** | `--mode trading` | Headless Orca engine (autonomous) |
| **Orca** | `--mode orca` | Direct orca_complete_kill_cycle.py (**Main System**) |
| **Queen** | `--mode queen` | Queen dashboard only |
| **Shell** | `--mode shell` | Interactive bash shell |

**Recommended for Autonomous Trading**: Use `--mode orca` or `--mode trading` with the Orca system as the primary engine.

## Ports

| Port | Service |
|------|---------|
| 8888 | Command Center UI |
| 8889 | API Gateway |
| 9090 | Prometheus Metrics |

## Volumes

| Volume | Purpose |
|--------|---------|
| `aureon-data` | Trading state, positions, history |
| `aureon-logs` | Application logs |
| `aureon-config` | Configuration and credentials |

## Docker Commands

```bash
# Build image
docker build -t aureon-trading:latest -f production/Dockerfile .

# Run in game mode (default)
docker run -it --name aureon -p 8888:8888 aureon-trading:latest

# Run with monitoring stack
docker-compose -f production/docker-compose.yml --profile monitoring up -d

# View logs
docker logs -f aureon-game

# Enter container shell
docker exec -it aureon-game /bin/bash

# Stop
docker stop aureon-game

# Remove (keeps data volumes)
docker rm aureon-game
```

## First-Run Setup

On first launch, the setup wizard will guide you through:

1. **Safety Warning**: Important information about API key security
2. **Exchange Configuration**: Enter API keys for your exchanges
3. **Risk Limits**: Set position sizes and daily loss limits
4. **Review**: Confirm settings before saving

## Risk Management

Default safety settings:
- **DRY RUN**: Enabled by default (paper trading)
- **Max Position**: $10 USD
- **Max Daily Loss**: $5 USD
- **Max Trades/Day**: 100

⚠️ **WARNING**: Never enable withdrawal permissions on API keys!

## Monitoring (Optional)

Enable the monitoring stack for Prometheus + Grafana:

```bash
docker-compose -f production/docker-compose.yml --profile monitoring up -d
```

- Prometheus: http://localhost:9091
- Grafana: http://localhost:3000 (admin/aureon2026)

## Troubleshooting

### Container won't start
```bash
docker logs aureon-game
```

### Reset configuration
```bash
docker volume rm aureon-config
```

### Reset all data
```bash
docker volume rm aureon-data aureon-logs aureon-config
```

### Check health
```bash
curl http://localhost:8888/health
```

## Security

- Runs as non-root user inside container
- API credentials encrypted at rest
- Network isolated via Docker bridge
- Resource limits enforced (2 CPU, 2GB RAM)

## Support

- GitHub Issues: https://github.com/RA-CONSULTING/aureon-trading/issues
- Documentation: See `/docs` folder

---

*"Construction complete. Building. Unit ready."* 🎮
