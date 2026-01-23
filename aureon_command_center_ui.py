#!/usr/bin/env python3
"""
👑🌌 AUREON COMMAND CENTER UI 👑🌌
═══════════════════════════════════════════════════════════════════════════

UNIFIED USER INTERFACE - ALL SYSTEMS INTEGRATED

Combines ALL existing models and systems into ONE dashboard:

📊 EXCHANGE DATA:
   - Kraken (crypto)
   - Binance (crypto)
   - Alpaca (crypto + stocks)

🧠 INTELLIGENCE SYSTEMS:
   - Queen Hive Mind (neural control)
   - Mycelium Network (distributed intelligence)
   - Probability Nexus (80%+ win rate)
   - Ultimate Intelligence (95% accuracy)
   - Timeline Oracle (7-day vision)
   - Quantum Mirror Scanner

⚡ EXECUTION SYSTEMS:
   - MicroProfitLabyrinth (FPTP execution)
   - HFT Engine (sub-10ms latency)
   - Animal Momentum Scanners
   - Harmonic Fusion

📡 DATA OUTPUT:
   - WebSocket streaming (real-time)
   - REST API endpoints
   - Console visualization
   - JSON state files

Gary Leckey | January 2026 | ALL SYSTEMS → UNIFIED UI
"""

import sys
import os

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

# Load environment variables from .env file (CRITICAL for API keys!)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system env vars only")

import asyncio
import json
import time
import random
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from collections import deque
from pathlib import Path

try:
    from aiohttp import web
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️ aiohttp not available - install with: pip install aiohttp")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════
# SYSTEM IMPORTS - ALL MODELS (LAZY LOADED AFTER SERVER START)
# ════════════════════════════════════════════════════════════════════════════
SYSTEMS_STATUS = {}

KrakenClient = None
BinanceClient = None
AlpacaClient = None

QueenHiveMind = None
MyceliumNetwork = None
ThoughtBus = None

ProbabilityUltimateIntelligence = None
MinerBrain = None
TimelineOracle = None
QuantumMirrorScanner = None

HarmonicWaveFusion = None
GlobalWaveScanner = None

MyceliumConversionHub = None

OrcaDashboardHtml = None
QueenUnifiedDashboardHtml = None
SystemRegistry = None


def safe_import(name: str, import_fn):
    """Safely import a module and track status."""
    try:
        result = import_fn()
        SYSTEMS_STATUS[name] = True
        return result
    except Exception as e:
        SYSTEMS_STATUS[name] = False
        logger.debug(f"{name} import failed: {e}")
        return None


def load_systems():
    """Load optional systems after web server is already accepting traffic."""
    global KrakenClient, BinanceClient, AlpacaClient
    global QueenHiveMind, MyceliumNetwork, ThoughtBus
    global ProbabilityUltimateIntelligence, MinerBrain, TimelineOracle, QuantumMirrorScanner
    global HarmonicWaveFusion, GlobalWaveScanner
    global MyceliumConversionHub
    global OrcaDashboardHtml, QueenUnifiedDashboardHtml, SystemRegistry

    print("\n🔌 LOADING EXCHANGE CLIENTS...")
    KrakenClient = safe_import('Kraken', lambda: __import__('kraken_client', fromlist=['KrakenClient']).KrakenClient)
    BinanceClient = safe_import('Binance', lambda: __import__('binance_client', fromlist=['BinanceClient']).BinanceClient)
    AlpacaClient = safe_import('Alpaca', lambda: __import__('alpaca_client', fromlist=['AlpacaClient']).AlpacaClient)

    print("\n👑 LOADING QUEEN & NEURAL SYSTEMS...")
    QueenHiveMind = safe_import('Queen Hive Mind', lambda: __import__('aureon_queen_hive_mind', fromlist=['QueenHiveMind']).QueenHiveMind)
    MyceliumNetwork = safe_import('Mycelium Network', lambda: __import__('aureon_mycelium', fromlist=['MyceliumNetwork']).MyceliumNetwork)
    ThoughtBus = safe_import('Thought Bus', lambda: __import__('aureon_thought_bus', fromlist=['ThoughtBus']).ThoughtBus)

    print("\n🧠 LOADING INTELLIGENCE SYSTEMS...")
    ProbabilityUltimateIntelligence = safe_import('Ultimate Intelligence', lambda: __import__('probability_ultimate_intelligence', fromlist=['ProbabilityUltimateIntelligence']).ProbabilityUltimateIntelligence)
    MinerBrain = safe_import('Miner Brain', lambda: __import__('aureon_miner_brain', fromlist=['MinerBrain']).MinerBrain)
    TimelineOracle = safe_import('Timeline Oracle', lambda: __import__('aureon_timeline_oracle', fromlist=['TimelineOracle']).TimelineOracle)
    QuantumMirrorScanner = safe_import('Quantum Mirror', lambda: __import__('aureon_quantum_mirror_scanner', fromlist=['QuantumMirrorScanner']).QuantumMirrorScanner)

    print("\n🌊 LOADING HARMONIC & MOMENTUM SYSTEMS...")
    HarmonicWaveFusion = safe_import('Harmonic Fusion', lambda: __import__('aureon_harmonic_fusion', fromlist=['HarmonicWaveFusion']).HarmonicWaveFusion)
    GlobalWaveScanner = safe_import('Wave Scanner', lambda: __import__('aureon_global_wave_scanner', fromlist=['GlobalWaveScanner']).GlobalWaveScanner)

    print("\n💰 LOADING DATA & CONVERSION SYSTEMS...")
    MyceliumConversionHub = safe_import('Conversion Hub', lambda: __import__('mycelium_conversion_hub', fromlist=['MyceliumConversionHub']).MyceliumConversionHub)

    OrcaDashboardHtml = safe_import('Orca Dashboard', lambda: __import__('orca_command_center', fromlist=['ORCA_DASHBOARD_HTML']).ORCA_DASHBOARD_HTML)
    QueenUnifiedDashboardHtml = safe_import('Queen Unified Dashboard', lambda: __import__('aureon_queen_unified_dashboard', fromlist=['UNIFIED_DASHBOARD_HTML']).UNIFIED_DASHBOARD_HTML)
    SystemRegistry = safe_import('System Registry', lambda: __import__('aureon_system_hub', fromlist=['SystemRegistry']).SystemRegistry)

    working = sum(1 for v in SYSTEMS_STATUS.values() if v)
    total = len(SYSTEMS_STATUS)
    print(f"\n✅ SYSTEMS LOADED: {working}/{total}")


# ════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class SystemMetrics:
    """Metrics from a trading system."""
    name: str
    status: str = "OFFLINE"  # ONLINE, OFFLINE, ERROR
    confidence: float = 0.0
    accuracy: float = 0.0
    signals_sent: int = 0
    last_update: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class TradingSignal:
    """Signal from any trading system."""
    source: str
    signal_type: str  # BUY, SELL, HOLD, CONVERT
    symbol: str
    confidence: float
    score: float
    reason: str
    timestamp: float
    exchange: str = ""
    target_price: float = 0.0
    stop_loss: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class PortfolioState:
    """Current portfolio state."""
    total_value_usd: float = 0.0
    cash_available: float = 0.0
    positions: List[Dict] = field(default_factory=list)
    balances: Dict[str, Dict] = field(default_factory=dict)  # exchange -> {asset: amount}
    pnl_today: float = 0.0
    pnl_total: float = 0.0
    exchange_breakdown: Dict[str, Dict] = field(default_factory=dict)  # exchange -> {total_usd, cash_usd, assets}
    baseline_value: float = 0.0  # Starting value for P&L calculation


@dataclass
class MarketOverview:
    """Market overview data."""
    total_assets_tracked: int = 0
    rising_count: int = 0
    falling_count: int = 0
    top_movers: List[Dict] = field(default_factory=list)
    momentum_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class TradeExecution:
    """Record of an executed trade."""
    timestamp: float
    exchange: str
    symbol: str
    side: str  # BUY, SELL, CONVERT
    quantity: float
    price: float
    value_usd: float
    status: str = "EXECUTED"  # EXECUTED, PENDING, FAILED
    order_id: str = ""
    pnl: float = 0.0
    metadata: Dict = field(default_factory=dict)


# ════════════════════════════════════════════════════════════════════════════
# UNIFIED DASHBOARD HTML
# ════════════════════════════════════════════════════════════════════════════

COMMAND_CENTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>👑 Aureon Command Center</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta21/dist/css/tabler.min.css">
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-primary: #0b1220;
            --bg-secondary: #0f172a;
            --bg-panel: rgba(17, 24, 39, 0.92);
            --accent-gold: #ffaa00;
            --accent-green: #00ff88;
            --accent-red: #ff3366;
            --accent-blue: #00bfff;
            --accent-purple: #9966ff;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
        }
        
        body {
            font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: rgba(0, 0, 0, 1) !important;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            line-height: 1.45;
            margin: 0;
            overflow: hidden;
        }
        
        /* Header */
        #header {
            background: rgba(0, 0, 0, 0.9);
            padding: 14px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid var(--accent-gold);
            box-shadow: 0 4px 30px rgba(255, 170, 0, 0.3);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            font-size: 1.5em;
            font-weight: bold;
            background: linear-gradient(90deg, var(--accent-gold), #ff6600);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-stack {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .logo-subtitle {
            font-size: 0.7em;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--text-secondary);
        }
        
        .status-bar {
            display: flex;
            gap: 18px;
            font-size: 0.9em;
            flex-wrap: wrap;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .status-pill {
            padding: 2px 8px;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.15);
            color: var(--text-primary);
            font-weight: 600;
            font-size: 0.85em;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .density-toggle {
            display: inline-flex;
            gap: 6px;
            padding: 4px;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.15);
            border: 1px solid rgba(148, 163, 184, 0.25);
        }

        .density-btn {
            border: none;
            background: transparent;
            color: var(--text-secondary);
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 0.75em;
            font-weight: 600;
            cursor: pointer;
        }

        .density-btn.active {
            background: rgba(255, 170, 0, 0.2);
            color: var(--text-primary);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-dot.online { background: var(--accent-green); }
        .status-dot.offline { background: var(--accent-red); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Tabs Navigation */
        .tabs-nav {
            display: flex;
            background: rgba(0, 0, 0, 0.8);
            border-bottom: 1px solid rgba(255, 170, 0, 0.3);
            overflow-x: auto;
        }

        .tab-btn {
            padding: 12px 20px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            font-family: inherit;
            font-size: 0.9em;
            white-space: nowrap;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }

        .tab-btn:hover {
            color: var(--text-primary);
            background: rgba(255, 170, 0, 0.1);
        }

        .tab-btn.active {
            color: var(--accent-gold);
            border-bottom-color: var(--accent-gold);
            background: rgba(255, 170, 0, 0.1);
        }

        .tab-btn .tab-icon {
            margin-right: 6px;
        }

        .tab-btn .tab-badge {
            margin-left: 6px;
            background: var(--accent-green);
            color: #000;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.75em;
            font-weight: bold;
        }

        .tab-btn .tab-badge.orca-pulse {
            background: var(--accent-gold);
            animation: orca-pulse 2s infinite;
        }

        .tab-btn .tab-live {
            margin-left: 8px;
            background: rgba(0, 255, 136, 0.15);
            color: var(--accent-green);
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.7em;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            opacity: 0.35;
            transition: opacity 0.2s ease;
        }

        .tab-btn .tab-live.active {
            opacity: 1;
        }

        .tab-btn .tab-time {
            margin-left: 6px;
            color: var(--text-secondary);
            font-size: 0.7em;
        }

        .tab-btn .tab-event {
            margin-left: 6px;
            color: var(--text-secondary);
            font-size: 0.65em;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            opacity: 0.7;
        }

        .tab-btn .tab-live.stale {
            background: rgba(255, 170, 0, 0.2);
            color: var(--accent-gold);
            opacity: 1;
        }

        .tab-btn .tab-live.dead {
            background: rgba(255, 51, 102, 0.2);
            color: var(--accent-red);
            opacity: 1;
        }

        @keyframes orca-pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        /* Orca Console Styles */
        .exchange-dot {
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            text-align: center;
            line-height: 20px;
            font-size: 10px;
            font-weight: bold;
            margin: 0 2px;
        }
        .exchange-dot.kraken { background: #5741d9; color: #fff; }
        .exchange-dot.alpaca { background: #ffcd00; color: #000; }
        .exchange-dot.binance { background: #f3ba2f; color: #000; }
        .exchange-dot.offline { background: #333 !important; color: #666 !important; }

        .orca-log-entry { margin: 2px 0; }
        .orca-log-buy { color: #00ff88; }
        .orca-log-sell { color: #ff6b6b; }
        .orca-log-info { color: #888; }
        .orca-log-success { color: #00ff00; }
        .orca-log-warning { color: #ffaa00; }
        .orca-log-error { color: #ff4444; }
        .orca-log-cycle { color: #00bfff; font-weight: bold; }
        .orca-log-pnl-pos { color: #00ff88; font-weight: bold; }
        .orca-log-pnl-neg { color: #ff6b6b; font-weight: bold; }

        .execution-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 10px;
            margin: 4px 0;
            background: rgba(255,255,255,0.03);
            border-radius: 4px;
            font-size: 0.85em;
        }
        .execution-item.buy { border-left: 3px solid var(--accent-green); }
        .execution-item.sell { border-left: 3px solid var(--accent-red); }
        .execution-item.convert { border-left: 3px solid var(--accent-gold); }

        /* Tab Content */
        .tab-content {
            display: none;
            min-height: calc(100vh - 140px);
            padding: 12px 0 20px;
        }

        .tab-content.active {
            display: block;
        }
        
        /* Main Container */
        #container {
            display: grid;
            grid-template-columns: minmax(280px, 320px) 1fr minmax(300px, 360px);
            grid-template-rows: auto 1fr;
            gap: 16px;
            padding: 16px;
            min-height: 100%;
        }
        
        /* Panels */
        .panel {
            background: var(--bg-panel);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 10px;
            padding: 16px;
            overflow: hidden;
            backdrop-filter: blur(10px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
        }

        .panel > h2 {
            margin-bottom: 12px;
        }
        
        .panel h2 {
            color: var(--accent-gold);
            font-size: 1.05em;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 170, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Unified Hubs */
        .hub-summary {
            display: grid;
            gap: 6px;
            margin-bottom: 10px;
            font-size: 0.9em;
        }

        .hub-row {
            display: flex;
            justify-content: space-between;
            color: #c6d2ff;
        }

        .hub-actions {
            display: flex;
            gap: 6px;
            margin-bottom: 10px;
        }

        .hub-btn {
            flex: 1;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
            color: #00ff88;
            border-radius: 6px;
            padding: 6px 8px;
            cursor: pointer;
            font-size: 0.85em;
        }

        .hub-btn:hover {
            background: rgba(0, 255, 136, 0.2);
        }

        .hub-frame-wrap {
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 8px;
            overflow: hidden;
            height: 160px;
            background: #0b0f1a;
        }

        #hub-frame {
            width: 100%;
            height: 100%;
            border: 0;
        }

        /* Flight Check Panel */
        .flight-check-panel {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 15px;
        }

        .flight-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            padding: 8px;
            border-radius: 6px;
        }

        .flight-status.online {
            background: rgba(0, 255, 136, 0.15);
            color: #00ff88;
            border-left: 3px solid #00ff88;
        }

        .flight-status.offline {
            background: rgba(255, 51, 102, 0.15);
            color: #ff3366;
            border-left: 3px solid #ff3366;
        }

        .flight-progress {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 8px;
        }

        .flight-progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00bfff);
            transition: width 0.3s;
        }

        .flight-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4px;
            margin-top: 8px;
            font-size: 0.75em;
            color: #888;
        }

        .flight-item {
            display: flex;
            justify-content: space-between;
        }
        
        /* Queen Panel */
        #queen-panel {
            grid-column: 1 / -1;
            background: linear-gradient(135deg, rgba(255, 170, 0, 0.1), rgba(255, 102, 0, 0.1));
            border-color: var(--accent-gold);
            display: flex;
            align-items: center;
            gap: 20px;
            min-height: 100px;
        }
        
        #queen-avatar {
            font-size: 60px;
            animation: float 3s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        #queen-message {
            flex: 1;
            font-size: 1.3em;
            color: var(--accent-gold);
            text-shadow: 0 0 10px rgba(255, 170, 0, 0.5);
        }
        
        #queen-stats {
            display: flex;
            flex-direction: column;
            gap: 5px;
            font-size: 0.9em;
            color: var(--text-secondary);
        }
        
        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 15px;
        }

        .metrics-grid {
            grid-template-columns: repeat(4, 1fr);
            margin-bottom: 0;
        }

        .metrics-grid .stat-card {
            text-align: left;
            padding: 16px;
            background: rgba(2, 6, 23, 0.55);
            border: 1px solid rgba(148, 163, 184, 0.25);
        }

        .metrics-grid .stat-value {
            font-size: 1.8em;
        }

        .metric-chart {
            margin-top: 8px;
            height: 44px;
            opacity: 0.9;
        }
        
        .stat-card {
            background: rgba(0, 255, 136, 0.05);
            border: 1px solid rgba(0, 255, 136, 0.18);
            border-radius: 10px;
            padding: 14px;
            text-align: center;
        }
        
        .stat-label {
            font-size: 0.75em;
            color: var(--text-secondary);
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        
        .stat-value {
            font-size: 1.6em;
            font-weight: bold;
            color: var(--accent-green);
        }

        .scroll-area {
            max-height: 360px;
            overflow-y: auto;
            padding-right: 4px;
        }

        .scroll-area.lg {
            max-height: 520px;
        }

        .scroll-area.xl {
            max-height: 680px;
        }

        body.compact .panel {
            padding: 12px;
        }

        body.compact .stats-grid {
            gap: 8px;
        }

        body.compact .stat-value {
            font-size: 1.4em;
        }

        body.compact .scroll-area {
            max-height: 280px;
        }

        body.compact .scroll-area.lg {
            max-height: 420px;
        }
        
        .stat-value.negative { color: var(--accent-red); }
        .stat-value.gold { color: var(--accent-gold); }
        
        /* System Status */
        .system-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            margin-bottom: 5px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 5px;
            border-left: 3px solid var(--accent-green);
        }
        
        .system-item.offline {
            border-left-color: var(--accent-red);
            opacity: 0.6;
        }
        
        .system-name { font-size: 0.9em; }
        
        .system-status {
            font-size: 0.75em;
            padding: 2px 8px;
            border-radius: 10px;
            background: rgba(0, 255, 136, 0.2);
            color: var(--accent-green);
        }
        
        .system-status.offline {
            background: rgba(255, 51, 102, 0.2);
            color: var(--accent-red);
        }
        
        /* Signals Feed */
        .signal-item {
            padding: 10px;
            margin-bottom: 8px;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 8px;
            border-left: 4px solid var(--accent-green);
            animation: slideIn 0.3s ease;
        }

        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .chip {
            padding: 4px 10px;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.15);
            color: var(--text-primary);
            font-size: 0.75em;
            font-weight: 600;
        }

        .table-list {
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 10px;
            overflow: hidden;
        }

        .table-row {
            display: grid;
            grid-template-columns: 1.1fr 0.6fr 0.7fr 0.6fr;
            gap: 10px;
            align-items: center;
            padding: 10px 12px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.15);
            background: rgba(15, 23, 42, 0.6);
            font-size: 0.85em;
        }

        .table-row:last-child {
            border-bottom: none;
        }

        .table-row.header {
            background: rgba(2, 6, 23, 0.75);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.7em;
            color: var(--text-secondary);
        }

        .table-cell.mono {
            font-family: 'JetBrains Mono', 'SFMono-Regular', Menlo, Monaco, Consolas, monospace;
            font-size: 0.85em;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .signal-item.buy { border-left-color: var(--accent-green); }
        .signal-item.sell { border-left-color: var(--accent-red); }
        .signal-item.hold { border-left-color: var(--accent-gold); }
        .signal-item.voice {
            border-left-color: var(--accent-gold);
            background: rgba(255, 170, 0, 0.08);
        }
        
        .signal-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        .signal-symbol {
            font-weight: bold;
            color: var(--accent-blue);
        }
        
        .signal-type {
            font-size: 0.85em;
            padding: 2px 8px;
            border-radius: 10px;
        }
        
        .signal-type.buy { background: rgba(0, 255, 136, 0.2); color: var(--accent-green); }
        .signal-type.sell { background: rgba(255, 51, 102, 0.2); color: var(--accent-red); }
        .signal-type.hold { background: rgba(255, 170, 0, 0.2); color: var(--accent-gold); }
        
        .signal-details {
            font-size: 0.85em;
            color: var(--text-secondary);
        }

        .signal-meta {
            margin-top: 6px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            font-size: 0.75em;
            color: #aaa;
        }

        .signal-meta span {
            display: block;
        }
        
        .signal-confidence {
            margin-top: 5px;
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .signal-confidence-bar {
            height: 100%;
            background: var(--accent-green);
            transition: width 0.3s ease;
        }

        /* Quantum Visuals */
        .quantum-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            padding: 15px;
            height: 100%;
        }

        .quantum-chart {
            height: 220px;
        }

        .timeline-list {
            display: grid;
            gap: 8px;
            margin-top: 12px;
        }

        .timeline-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 0.85em;
        }

        .timeline-tag {
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.7em;
            font-weight: 700;
            letter-spacing: 0.08em;
        }

        .timeline-tag.good { background: rgba(0, 255, 136, 0.2); color: var(--accent-green); }
        .timeline-tag.warn { background: rgba(255, 170, 0, 0.2); color: var(--accent-gold); }

        /* Learning Tab */
        .learning-grid {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 15px;
            padding: 15px;
            height: 100%;
        }

        .learning-chart {
            height: 240px;
        }

        .pattern-list {
            display: grid;
            gap: 8px;
        }

        .pattern-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 10px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 8px;
            font-size: 0.85em;
        }

        .pattern-badge {
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.7em;
            font-weight: 700;
            letter-spacing: 0.08em;
        }

        .pattern-badge.win { background: rgba(0, 255, 136, 0.2); color: var(--accent-green); }
        .pattern-badge.loss { background: rgba(255, 51, 102, 0.2); color: var(--accent-red); }

        .stargate-map {
            position: relative;
            height: 260px;
            border-radius: 12px;
            background: radial-gradient(circle at 20% 20%, rgba(0, 191, 255, 0.12), transparent 40%),
                        radial-gradient(circle at 80% 30%, rgba(255, 170, 0, 0.12), transparent 40%),
                        linear-gradient(135deg, rgba(2, 6, 23, 0.9), rgba(15, 23, 42, 0.9));
            border: 1px solid rgba(148, 163, 184, 0.2);
            overflow: hidden;
        }

        .stargate-map::before {
            content: '';
            position: absolute;
            inset: 0;
            background-image: linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
            background-size: 26px 26px;
            opacity: 0.35;
        }

        .stargate-node {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: rgba(148, 163, 184, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.4);
            transform: translate(-50%, -50%);
            z-index: 2;
        }

        .stargate-node.active {
            background: var(--accent-green);
            box-shadow: 0 0 14px rgba(0, 255, 136, 0.6);
        }

        .stargate-label {
            position: absolute;
            transform: translate(-50%, -130%);
            font-size: 0.7em;
            color: var(--text-secondary);
            white-space: nowrap;
            z-index: 3;
        }

        .bot-map-node {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-blue);
            box-shadow: 0 0 12px rgba(0, 191, 255, 0.6);
            transform: translate(-50%, -50%);
            animation: pulse 2s infinite;
        }

        .bot-map-node.active {
            background: var(--accent-green);
            box-shadow: 0 0 14px rgba(0, 255, 136, 0.7);
        }

        .bot-map-label {
            position: absolute;
            transform: translate(-50%, -140%);
            font-size: 0.7em;
            color: var(--text-secondary);
            white-space: nowrap;
        }
        
        /* Market Overview */
        .mover-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            margin-bottom: 5px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 5px;
        }
        
        .mover-symbol { font-weight: bold; }
        
        .mover-change {
            font-weight: bold;
        }
        
        .mover-change.positive { color: var(--accent-green); }
        .mover-change.negative { color: var(--accent-red); }
        
        /* Balances */
        .balance-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            margin-bottom: 5px;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 5px;
        }

        .empty-state {
            text-align: center;
            color: #7c879a;
            font-style: italic;
            padding: 16px 8px;
            border: 1px dashed rgba(148, 163, 184, 0.25);
            border-radius: 8px;
            background: rgba(2, 6, 23, 0.35);
        }
        
        .balance-asset { color: var(--accent-blue); font-weight: bold; }
        .balance-amount { color: var(--accent-green); }
        .balance-value { color: var(--text-secondary); font-size: 0.85em; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.3); }
        ::-webkit-scrollbar-thumb { background: var(--accent-green); border-radius: 3px; }
        
        /* Connection Indicator */
        #connection-status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            background: rgba(0, 0, 0, 0.9);
            border-radius: 20px;
            border: 1px solid var(--accent-green);
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85em;
        }
        
        #connection-status.disconnected {
            border-color: var(--accent-red);
        }
        
        @media (max-width: 1920px) {
            #container {
                grid-template-columns: minmax(280px, 320px) 1fr minmax(300px, 360px);
                height: calc(100vh - 70px);
                overflow: hidden;
            }
            .panel {
                max-height: 100%;
                overflow: auto;
            }
        }
        
        @media (max-width: 1100px) {
            #container {
                grid-template-columns: 1fr;
            }
            #queen-panel {
                grid-column: 1 / -1;
            }
            .panel:last-child {
                grid-column: 1 / -1;
            }
            .metrics-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 680px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 900px) {
            .tabs-nav {
                position: sticky;
                top: 64px;
                z-index: 90;
            }
        }
        
        @media (max-width: 768px) {
            #container {
                grid-template-columns: 1fr;
            }
            #queen-panel {
                grid-column: 1;
            }
            .panel {
                max-height: none;
            }
        }
    </style>
</head>
<body>
    <div id="header">
        <div class="logo-stack">
            <div class="logo">👑 AUREON COMMAND CENTER</div>
            <div class="logo-subtitle">Real-time command & control</div>
        </div>
        <div class="header-actions">
            <div class="density-toggle" aria-label="UI density">
                <button class="density-btn" id="density-comfort" onclick="setDensity('comfort')">Comfort</button>
                <button class="density-btn" id="density-compact" onclick="setDensity('compact')">Compact</button>
            </div>
            <div class="status-bar">
                <div class="status-item">
                    <span class="status-dot online" id="ws-status"></span>
                    <span>WebSocket</span>
                </div>
                <div class="status-item">
                    <span class="status-pill" id="system-count">0</span>
                    <span>Systems Online</span>
                </div>
                <div class="status-item">
                    <span class="status-pill" id="clock">--:--:--</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tabs-nav">
        <button class="tab-btn active" onclick="switchTab('trading')" data-tab="trading">
            <span class="tab-icon">📊</span>Trading
            <span class="tab-live" id="live-trading">Live</span>
            <span class="tab-time" id="time-trading">--:--</span>
            <span class="tab-event" id="event-trading">--</span>
        </button>
        <button class="tab-btn" onclick="switchTab('whales')" data-tab="whales">
            <span class="tab-icon">🐋</span>Whales
            <span class="tab-badge" id="whale-count">0</span>
            <span class="tab-live" id="live-whales">Live</span>
            <span class="tab-time" id="time-whales">--:--</span>
            <span class="tab-event" id="event-whales">--</span>
        </button>
        <button class="tab-btn" onclick="switchTab('bots')" data-tab="bots">
            <span class="tab-icon">🤖</span>Bot Intel
            <span class="tab-badge" id="bot-count">0</span>
            <span class="tab-live" id="live-bots">Live</span>
            <span class="tab-time" id="time-bots">--:--</span>
            <span class="tab-event" id="event-bots">--</span>
        </button>
        <button class="tab-btn" onclick="switchTab('market')" data-tab="market">
            <span class="tab-icon">📈</span>Live Feed
            <span class="tab-live" id="live-market">Live</span>
            <span class="tab-time" id="time-market">--:--</span>
            <span class="tab-event" id="event-market">--</span>
        </button>
        <button class="tab-btn" onclick="switchTab('quantum')" data-tab="quantum">
            <span class="tab-icon">🔮</span>Quantum
            <span class="tab-live" id="live-quantum">Live</span>
            <span class="tab-time" id="time-quantum">--:--</span>
            <span class="tab-event" id="event-quantum">--</span>
        </button>
        <button class="tab-btn" onclick="switchTab('learning')" data-tab="learning">
            <span class="tab-icon">🧠</span>Learning
            <span class="tab-live" id="live-learning">Live</span>
            <span class="tab-time" id="time-learning">--:--</span>
            <span class="tab-event" id="event-learning">--</span>
        </button>
        <button class="tab-btn" onclick="switchTab('orca')" data-tab="orca">
            <span class="tab-icon">🦈</span>Orca Live
            <span class="tab-badge orca-pulse" id="orca-cycle">0</span>
            <span class="tab-live" id="live-orca">Live</span>
            <span class="tab-time" id="time-orca">--:--</span>
            <span class="tab-event" id="event-orca">--</span>
        </button>
        <button class="tab-btn" onclick="switchTab('systems')" data-tab="systems">
            <span class="tab-icon">⚙️</span>All Systems
            <span class="tab-live" id="live-systems">Live</span>
            <span class="tab-time" id="time-systems">--:--</span>
            <span class="tab-event" id="event-systems">--</span>
        </button>
    </div>

    <!-- TAB 1: TRADING (Main Dashboard) -->
    <div id="tab-trading" class="tab-content active">
        <div id="container">
        <!-- Queen Panel (Full Width Top) -->
        <div id="queen-panel" class="panel" style="grid-column: 1 / -1; max-height: none;">
            <div id="queen-avatar">👑</div>
            <div id="queen-message">Initializing Queen consciousness...</div>
            <div id="queen-stats">
                <div>Cosmic: <span id="cosmic-score">--</span>%</div>
                <div>Confidence: <span id="queen-confidence">--</span>%</div>
                <div>Strategy: <span id="queen-strategy">SCANNING</span></div>
            </div>
        </div>

        <div class="panel" style="grid-column: 1 / -1; max-height: none;">
            <h2>📊 KEY METRICS</h2>
            <div class="stats-grid metrics-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Value</div>
                    <div class="stat-value gold" id="total-value">$0.00</div>
                    <div class="metric-chart" id="chart-total-value"></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Cash Available</div>
                    <div class="stat-value" id="cash-available">$0.00</div>
                    <div class="metric-chart" id="chart-cash-available"></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Today's P&L</div>
                    <div class="stat-value" id="pnl-today">$0.00</div>
                    <div class="metric-chart" id="chart-pnl-today"></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total P&L</div>
                    <div class="stat-value" id="pnl-total">$0.00</div>
                    <div class="metric-chart" id="chart-pnl-total"></div>
                </div>
            </div>
            
            <!-- Exchange Breakdown -->
            <h3 style="margin-top: 20px; color: #00bfff;">💱 EXCHANGE BREAKDOWN</h3>
            <div id="exchange-breakdown" class="exchange-breakdown-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px;">
                <div class="empty-state">Loading exchange data...</div>
            </div>
            
            <!-- P&L Controls -->
            <div style="margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
                <button onclick="resetPnLBaseline()" class="btn-action" style="background: linear-gradient(135deg, #ff6b6b, #cc5555); border: none; padding: 8px 16px; border-radius: 6px; color: white; cursor: pointer; font-size: 0.85em;">
                    🔄 Reset Total P&L Baseline
                </button>
                <button onclick="resetTodayPnL()" class="btn-action" style="background: linear-gradient(135deg, #00bfff, #0099cc); border: none; padding: 8px 16px; border-radius: 6px; color: white; cursor: pointer; font-size: 0.85em;">
                    📅 Reset Today's P&L
                </button>
                <button onclick="refreshBalances()" class="btn-action" style="background: linear-gradient(135deg, #00ff88, #00cc66); border: none; padding: 8px 16px; border-radius: 6px; color: white; cursor: pointer; font-size: 0.85em;">
                    🔃 Refresh Balances
                </button>
            </div>
        </div>
        
        <!-- Left Panel: Operations -->
        <div class="panel">
            <h2>✈️ FLIGHT CHECK</h2>
            <div id="flight-check" class="flight-check-panel">
                <div class="flight-status offline">Awaiting status...</div>
            </div>
            
            <h2>⚔️ ACTIVE POSITIONS</h2>
            <div id="positions-list" class="scroll-area" style="margin-bottom: 20px;">
                <div class="empty-state">No active positions</div>
            </div>
            
            <h2>🧾 RECENT TRADES</h2>
            <div id="recent-trades" class="scroll-area" style="margin-bottom: 20px;">
                <div class="empty-state">No recent trades</div>
            </div>
            
            <h2>🔌 SYSTEMS</h2>
            <div id="systems-list" class="scroll-area"></div>
            
            <h2 style="margin-top: 15px;">💎 BALANCES</h2>
            <div id="balances-list" class="scroll-area"></div>

            <h2 style="margin-top: 15px;">🧩 UNIFIED HUBS</h2>
            <div class="hub-summary">
                <div class="hub-row"><span>Orca</span><span id="hub-orca">—</span></div>
                <div class="hub-row"><span>Queen</span><span id="hub-queen">—</span></div>
                <div class="hub-row"><span>Registry</span><span id="hub-registry">—</span></div>
            </div>
            <div class="hub-actions">
                <button class="hub-btn" onclick="openHub('orca')">Orca</button>
                <button class="hub-btn" onclick="openHub('queen')">Queen</button>
                <button class="hub-btn" onclick="openHub('registry')">Registry</button>
            </div>
            <div class="hub-frame-wrap" style="height: 150px;">
                <iframe id="hub-frame" title="Unified Hub" src="/hub/registry"></iframe>
            </div>
        </div>
        
        <!-- Center Panel: Signals Feed -->
        <div class="panel" style="min-height: 420px;">
            <div class="section-header">
                <h2>📡 LIVE SIGNALS</h2>
                <span class="chip">Real-time</span>
            </div>
            <div class="table-list" style="margin-bottom: 10px;">
                <div class="table-row header">
                    <div>Symbol</div>
                    <div>Type</div>
                    <div>Confidence</div>
                    <div>Exchange</div>
                </div>
            </div>
            <div id="signals-feed" class="scroll-area lg"></div>
        </div>
        
        <!-- Right Panel: Market Overview -->
        <div class="panel" style="min-height: 420px;">
            <div class="section-header">
                <h2>📈 MARKET OVERVIEW</h2>
                <span class="chip">Live</span>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Assets Tracked</div>
                    <div class="stat-value" id="assets-tracked">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Rising</div>
                    <div class="stat-value" id="rising-count">0</div>
                </div>
            </div>
            
            <h2>🚀 TOP MOVERS</h2>
            <div class="table-list" style="margin-bottom: 8px;">
                <div class="table-row header" style="grid-template-columns: 1fr 0.7fr;">
                    <div>Asset</div>
                    <div>Change</div>
                </div>
            </div>
            <div id="top-movers" class="scroll-area"></div>
            
            <h2 style="margin-top: 15px;">📉 TOP FALLERS</h2>
            <div class="table-list" style="margin-bottom: 8px;">
                <div class="table-row header" style="grid-template-columns: 1fr 0.7fr;">
                    <div>Asset</div>
                    <div>Change</div>
                </div>
            </div>
            <div id="top-fallers" class="scroll-area"></div>
        </div>
    </div>
    </div><!-- end tab-trading -->

    <!-- TAB 2: WHALES - Live Whale Tracker -->
    <div id="tab-whales" class="tab-content">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; height: 100%;">
            <div class="panel" style="overflow-y: auto;">
                <div class="section-header">
                    <h2>🐋 LIVE WHALE ACTIVITY</h2>
                    <span class="chip">Alerts</span>
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;">
                    <span class="chip">$100k+</span>
                    <span class="chip">Buys</span>
                    <span class="chip">Sells</span>
                </div>
                <div id="whale-feed" style="max-height: calc(100vh - 200px); overflow-y: auto;">
                    <div class="empty-state" style="margin: 20px;">
                        <div style="font-size: 3em;">🐋</div>
                        <p>Monitoring for whale movements...</p>
                        <p style="font-size: 0.8em; color: #444;">Large orders > $100k will appear here</p>
                    </div>
                </div>
            </div>
            <div class="panel">
                <div class="section-header">
                    <h2>📊 WHALE STATISTICS</h2>
                    <span class="chip">24h</span>
                </div>
                <div class="stats-grid" style="grid-template-columns: 1fr 1fr;">
                    <div class="stat-card">
                        <div class="stat-label">Whales Detected (24h)</div>
                        <div class="stat-value" id="whale-24h">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Volume</div>
                        <div class="stat-value gold" id="whale-volume">$0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Bullish Whales</div>
                        <div class="stat-value" style="color: var(--accent-green);" id="whale-bulls">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Bearish Whales</div>
                        <div class="stat-value negative" id="whale-bears">0</div>
                    </div>
                </div>
                <h2 style="margin-top: 15px;">🎯 TOP WHALE TARGETS</h2>
                <div class="table-list" style="margin-bottom: 8px;">
                    <div class="table-row header" style="grid-template-columns: 1fr 0.8fr;">
                        <div>Asset</div>
                        <div>Status</div>
                    </div>
                </div>
                <div id="whale-targets">
                    <div class="table-row" style="grid-template-columns: 1fr 0.8fr;"><div class="table-cell">BTC/USD</div><div class="table-cell">Monitoring</div></div>
                    <div class="table-row" style="grid-template-columns: 1fr 0.8fr;"><div class="table-cell">ETH/USD</div><div class="table-cell">Monitoring</div></div>
                    <div class="table-row" style="grid-template-columns: 1fr 0.8fr;"><div class="table-cell">SOL/USD</div><div class="table-cell">Monitoring</div></div>
                </div>
                <h2 style="margin-top: 15px;">🔥 WHALE HEATMAP</h2>
                <div id="whale-heatmap" style="background: rgba(0,0,0,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                    <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 4px;">
                        <div class="heat-cell" style="background: rgba(0,255,136,0.2); padding: 8px; border-radius: 4px; font-size: 0.8em;">BTC</div>
                        <div class="heat-cell" style="background: rgba(0,255,136,0.4); padding: 8px; border-radius: 4px; font-size: 0.8em;">ETH</div>
                        <div class="heat-cell" style="background: rgba(255,51,102,0.2); padding: 8px; border-radius: 4px; font-size: 0.8em;">SOL</div>
                        <div class="heat-cell" style="background: rgba(0,255,136,0.1); padding: 8px; border-radius: 4px; font-size: 0.8em;">DOGE</div>
                        <div class="heat-cell" style="background: rgba(255,51,102,0.3); padding: 8px; border-radius: 4px; font-size: 0.8em;">XRP</div>
                        <div class="heat-cell" style="background: rgba(0,255,136,0.3); padding: 8px; border-radius: 4px; font-size: 0.8em;">ADA</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 3: BOTS - Bot Intelligence -->
    <div id="tab-bots" class="tab-content">
        <div style="display: grid; grid-template-columns: 300px 1fr 300px; gap: 15px; padding: 15px; height: 100%;">
            <div class="panel">
                <h2>🏢 DETECTED FIRMS</h2>
                <div id="firms-list">
                    <div class="empty-state">Awaiting firm intelligence...</div>
                </div>
                <h2 style="margin-top: 15px;">🔬 BOT SIGNATURES</h2>
                <div id="bot-signatures">
                    <div class="empty-state">No bot signatures detected yet.</div>
                </div>
            </div>
            <div class="panel">
                <h2>🌍 GLOBAL BOT MAP</h2>
                <div id="bot-map" style="background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%); border-radius: 8px; padding: 20px; height: calc(100% - 60px); position: relative; overflow: hidden;">
                    <div id="bot-map-nodes"></div>
                    <div style="text-align: center; padding-top: 60%; color: #666; font-size: 0.9em;">
                        <p>🌐 Live Bot Activity Map</p>
                        <p style="font-size: 0.8em;">Dots represent detected algorithmic trading clusters</p>
                    </div>
                </div>
            </div>
            <div class="panel">
                <h2>📈 BOT INTEL STATS</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Bots Detected</div>
                        <div class="stat-value" id="total-bots">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Active Now</div>
                        <div class="stat-value gold" id="active-bots">0</div>
                    </div>
                </div>
                <h2 style="margin-top: 15px;">⚡ RECENT BOT ACTIVITY</h2>
                <div id="bot-activity">
                    <div class="empty-state">No bot activity yet.</div>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 4: MARKET - Live Market Feed -->
    <div id="tab-market" class="tab-content">
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; padding: 15px; height: 100%;">
            <div class="panel">
                <h2>💹 KRAKEN LIVE</h2>
                <div id="kraken-feed" style="max-height: calc(100vh - 200px); overflow-y: auto;">
                    <div class="mover-item"><span class="mover-symbol">BTC/USD</span><span class="mover-change positive">Loading...</span></div>
                    <div class="mover-item"><span class="mover-symbol">ETH/USD</span><span class="mover-change positive">Loading...</span></div>
                    <div class="mover-item"><span class="mover-symbol">SOL/USD</span><span class="mover-change negative">Loading...</span></div>
                </div>
            </div>
            <div class="panel">
                <h2>🔶 BINANCE LIVE</h2>
                <div id="binance-feed" style="max-height: calc(100vh - 200px); overflow-y: auto;">
                    <div class="mover-item"><span class="mover-symbol">BTCUSDT</span><span class="mover-change positive">Loading...</span></div>
                    <div class="mover-item"><span class="mover-symbol">ETHUSDT</span><span class="mover-change positive">Loading...</span></div>
                    <div class="mover-item"><span class="mover-symbol">SOLUSDT</span><span class="mover-change negative">Loading...</span></div>
                </div>
            </div>
            <div class="panel">
                <h2>🦙 ALPACA LIVE</h2>
                <div id="alpaca-feed" style="max-height: calc(100vh - 200px); overflow-y: auto;">
                    <div class="mover-item"><span class="mover-symbol">BTC/USD</span><span class="mover-change positive">Loading...</span></div>
                    <div class="mover-item"><span class="mover-symbol">ETH/USD</span><span class="mover-change positive">Loading...</span></div>
                    <div class="mover-item"><span class="mover-symbol">AAPL</span><span class="mover-change positive">Loading...</span></div>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 5: QUANTUM - Quantum Analysis -->
    <div id="tab-quantum" class="tab-content">
        <div class="quantum-grid">
            <div class="panel">
                <div class="section-header">
                    <h2>🔮 QUANTUM MIRROR SCANNER</h2>
                    <span class="chip">Live</span>
                </div>
                <div id="quantum-coherence-chart" class="quantum-chart"></div>
                <div class="stats-grid" style="margin-top: 10px;">
                    <div class="stat-card">
                        <div class="stat-label">Active Timelines</div>
                        <div class="stat-value" id="active-timelines">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Anchored</div>
                        <div class="stat-value gold" id="anchored-timelines">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Schumann Hz</div>
                        <div class="stat-value" id="schumann-hz">7.83</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Love Freq</div>
                        <div class="stat-value" style="color: #ff66aa;" id="love-freq">528</div>
                    </div>
                </div>
                <h2 style="margin-top: 15px;">🧭 ACTIVE TIMELINES</h2>
                <div id="quantum-timelines" class="timeline-list">
                    <div class="empty-state">Awaiting timeline signals...</div>
                </div>
            </div>
            <div class="panel">
                <div class="section-header">
                    <h2>🌌 STARGATE PROTOCOL</h2>
                    <span class="chip">Resonance</span>
                </div>
                <div id="stargate-map" class="stargate-map"></div>
                <h2 style="margin-top: 15px;">🌊 HARMONIC FREQUENCIES</h2>
                <div id="quantum-frequency-chart" class="quantum-chart"></div>
            </div>
        </div>
    </div>

    <!-- TAB 6: LEARNING - Adaptive Intelligence -->
    <div id="tab-learning" class="tab-content">
        <div class="learning-grid">
            <div class="panel">
                <div class="section-header">
                    <h2>🧠 ADAPTIVE LEARNING</h2>
                    <span class="chip">Live</span>
                </div>
                <div id="learning-pnl-chart" class="learning-chart"></div>
                <div class="stats-grid" style="margin-top: 10px;">
                    <div class="stat-card">
                        <div class="stat-label">Total Trades</div>
                        <div class="stat-value" id="learning-total-trades">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Win Rate</div>
                        <div class="stat-value" id="learning-win-rate">0%</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Avg PnL</div>
                        <div class="stat-value" id="learning-avg-pnl">$0.00</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Loss Events</div>
                        <div class="stat-value" id="learning-loss-events">0</div>
                    </div>
                </div>
            </div>
            <div class="panel">
                <div class="section-header">
                    <h2>📚 LEARNED PATTERNS</h2>
                    <span class="chip">Top</span>
                </div>
                <div id="learning-winloss-chart" class="learning-chart"></div>
                <div id="learning-patterns" class="pattern-list" style="margin-top: 12px;">
                    <div class="empty-state">Learning patterns will appear here...</div>
                </div>
            </div>
        </div>
        
        <!-- Queen Neuron Visualization -->
        <div class="panel" style="margin-top: 15px;">
            <div class="section-header">
                <h2>👑 QUEEN NEURAL NETWORK</h2>
                <span class="chip" id="neuron-version">v1</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px;">
                <div>
                    <div class="stats-grid" style="grid-template-columns: repeat(2, 1fr);">
                        <div class="stat-card">
                            <div class="stat-label">Input Neurons</div>
                            <div class="stat-value" id="neuron-input-size">7</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Hidden Neurons</div>
                            <div class="stat-value" id="neuron-hidden-size">12</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Learning Rate</div>
                            <div class="stat-value" id="neuron-learning-rate">0.01</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Last Update</div>
                            <div class="stat-value" id="neuron-timestamp" style="font-size: 0.7em;">--</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                        <div style="color: #00bfff; font-weight: bold; margin-bottom: 8px;">🎯 Input Features</div>
                        <div style="font-size: 0.8em; color: #aaa; line-height: 1.6;">
                            1. Coherence Score<br>
                            2. Lambda Stability<br>
                            3. Drift Score<br>
                            4. PIP Prediction<br>
                            5. Validation Pass Count<br>
                            6. Time Factor<br>
                            7. Market Volatility
                        </div>
                    </div>
                </div>
                <div id="neuron-canvas-container" style="background: rgba(0,0,0,0.4); border-radius: 8px; padding: 15px; min-height: 250px; position: relative;">
                    <canvas id="neuron-canvas" style="width: 100%; height: 250px;"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 7: ORCA LIVE - Real-time Orca Kill Cycle Monitor -->
    <div id="tab-orca" class="tab-content">
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 15px; padding: 15px; height: 100%;">
            <!-- Left: Status & Stats -->
            <div style="display: flex; flex-direction: column; gap: 15px;">
                <!-- Orca Status Card -->
                <div class="panel" style="text-align: center;">
                    <div id="orca-avatar" style="font-size: 80px; margin: 10px 0;">🦈</div>
                    <div id="orca-status-text" style="font-size: 24px; font-weight: bold; color: var(--accent-gold);">INITIALIZING...</div>
                    <div id="orca-mode" style="color: #888; margin-top: 5px;">Mode: --</div>
                    <div style="margin-top: 15px; display: flex; justify-content: center; gap: 10px;">
                        <div id="orca-heartbeat" style="width: 12px; height: 12px; border-radius: 50%; background: #666; animation: pulse 1s infinite;"></div>
                        <span id="orca-last-activity">Last activity: --</span>
                    </div>
                </div>
                
                <!-- Session Stats -->
                <div class="panel">
                    <h2>📊 SESSION STATS</h2>
                    <div class="stats-grid" style="grid-template-columns: repeat(2, 1fr);">
                        <div class="stat-card">
                            <div class="stat-label">Cycles</div>
                            <div class="stat-value gold" id="orca-cycles">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Trades</div>
                            <div class="stat-value" id="orca-trades">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Winning</div>
                            <div class="stat-value" id="orca-wins">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Win Rate</div>
                            <div class="stat-value" id="orca-winrate">--%</div>
                        </div>
                        <div class="stat-card" style="grid-column: span 2;">
                            <div class="stat-label">Total P&L</div>
                            <div class="stat-value gold" id="orca-pnl">$0.0000</div>
                        </div>
                    </div>
                </div>
                
                <!-- Active Positions -->
                <div class="panel" style="flex: 1; overflow: hidden;">
                    <div class="section-header">
                        <h2>🎯 ACTIVE POSITIONS (<span id="orca-position-count">0</span>)</h2>
                        <span class="chip">Live</span>
                    </div>
                    <div class="table-list" style="margin-bottom: 8px;">
                        <div class="table-row header" style="grid-template-columns: 1fr 0.7fr 0.7fr;">
                            <div>Asset</div>
                            <div>Size</div>
                            <div>P&L</div>
                        </div>
                    </div>
                    <div id="orca-positions" style="max-height: 220px; overflow-y: auto;">
                        <div class="empty-state">No active positions</div>
                    </div>
                </div>
            </div>
            
            <!-- Right: Live Console -->
            <div style="display: flex; flex-direction: column; gap: 15px;">
                <!-- Console Header -->
                <div class="panel" style="padding: 10px 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style="margin: 0;">🖥️ ORCA LIVE CONSOLE</h2>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <span id="orca-exchange-status" style="font-size: 0.9em;">
                                <span class="exchange-dot kraken">K</span>
                                <span class="exchange-dot alpaca">A</span>
                                <span class="exchange-dot binance">B</span>
                            </span>
                            <button onclick="clearOrcaConsole()" style="background: #333; border: 1px solid #555; color: #fff; padding: 5px 10px; border-radius: 4px; cursor: pointer;">Clear</button>
                        </div>
                    </div>
                </div>
                
                <!-- Live Console Output -->
                <div class="panel" style="flex: 1; overflow: hidden; background: #0a0a0a;">
                    <div id="orca-console" style="height: 100%; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 13px; padding: 10px; white-space: pre-wrap; line-height: 1.5;">
<span style="color: #00ff00;">🦈 ORCA KILL CYCLE - LIVE MONITOR</span>
<span style="color: #888;">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>
<span style="color: #888;">Waiting for Orca activity...</span>
<span style="color: #666;">Connect to WebSocket for live updates</span>
                    </div>
                </div>
                
                <!-- Recent Executions -->
                <div class="panel" style="max-height: 200px; overflow: hidden;">
                    <div class="section-header">
                        <h2>📝 RECENT EXECUTIONS</h2>
                        <span class="chip">Auto</span>
                    </div>
                    <div class="table-list" style="margin-bottom: 8px;">
                        <div class="table-row header" style="grid-template-columns: 1fr 0.6fr 0.6fr 0.6fr;">
                            <div>Asset</div>
                            <div>Side</div>
                            <div>Qty</div>
                            <div>Price</div>
                        </div>
                    </div>
                    <div id="orca-executions" style="max-height: 150px; overflow-y: auto;">
                        <div class="empty-state">No executions yet</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 6: SYSTEMS - All Systems Status -->
    <div id="tab-systems" class="tab-content">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; padding: 15px; height: 100%; overflow-y: auto;">
            <div class="panel">
                <h2>🔌 EXCHANGES</h2>
                <div id="exchange-systems">
                    <div class="system-item"><span class="system-name">Kraken API</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Binance API</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Alpaca API</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Capital.com</span><span class="system-status offline">❌</span></div>
                </div>
            </div>
            <div class="panel">
                <h2>🧠 INTELLIGENCE</h2>
                <div id="intel-systems">
                    <div class="system-item"><span class="system-name">Queen Hive Mind</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Miner Brain</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Ultimate Intel</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Harmonic Nexus</span><span class="system-status">✅</span></div>
                </div>
            </div>
            <div class="panel">
                <h2>📡 SCANNERS</h2>
                <div id="scanner-systems">
                    <div class="system-item"><span class="system-name">Wave Scanner</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Quantum Mirror</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Timeline Oracle</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Probability Nexus</span><span class="system-status">✅</span></div>
                </div>
            </div>
            <div class="panel">
                <h2>🔗 INFRASTRUCTURE</h2>
                <div id="infra-systems">
                    <div class="system-item"><span class="system-name">ThoughtBus</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Mycelium Network</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Whale Sonar</span><span class="system-status">✅</span></div>
                    <div class="system-item"><span class="system-name">Immune System</span><span class="system-status">✅</span></div>
                </div>
            </div>
            <div class="panel" style="grid-column: span 2;">
                <h2>📊 SYSTEM REGISTRY</h2>
                <div id="full-registry" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; max-height: 300px; overflow-y: auto;"></div>
            </div>
            <div class="panel" style="grid-column: span 2;">
                <h2>📈 SYSTEM METRICS</h2>
                <div class="stats-grid" style="grid-template-columns: repeat(4, 1fr);">
                    <div class="stat-card">
                        <div class="stat-label">Total Systems</div>
                        <div class="stat-value" id="total-systems">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Online</div>
                        <div class="stat-value" id="online-systems">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Uptime</div>
                        <div class="stat-value gold" id="uptime-pct">99.9%</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Cycles</div>
                        <div class="stat-value" id="total-cycles">0</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div id="connection-status">
        <span class="status-dot online"></span>
        <span>Connected</span>
    </div>
    
    <script>
        // Tab switching
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            // Deactivate all buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            // Show selected tab
            const selectedTab = document.getElementById('tab-' + tabName);
            if (selectedTab) selectedTab.classList.add('active');
            // Activate button
            const selectedBtn = document.querySelector(`[data-tab="${tabName}"]`);
            if (selectedBtn) selectedBtn.classList.add('active');
        }

        function setDensity(mode) {
            const body = document.body;
            if (mode === 'compact') {
                body.classList.add('compact');
            } else {
                body.classList.remove('compact');
            }
            localStorage.setItem('aureon_ui_density', mode);
            const comfortBtn = document.getElementById('density-comfort');
            const compactBtn = document.getElementById('density-compact');
            if (comfortBtn && compactBtn) {
                comfortBtn.classList.toggle('active', mode !== 'compact');
                compactBtn.classList.toggle('active', mode === 'compact');
            }
        }

        // WebSocket connection
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 10;
        
        function connect() {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            ws = new WebSocket(wsProtocol + window.location.host + '/ws');
            
            ws.onopen = function() {
                console.log('👑 Connected to Command Center');
                reconnectAttempts = 0;
                document.getElementById('ws-status').className = 'status-dot online';
                document.getElementById('connection-status').className = '';
                document.querySelector('#connection-status span:last-child').textContent = 'Connected';
            };
            
            ws.onclose = function() {
                console.log('❌ Disconnected');
                document.getElementById('ws-status').className = 'status-dot offline';
                document.getElementById('connection-status').className = 'disconnected';
                document.querySelector('#connection-status span:last-child').textContent = 'Disconnected';
                
                // Reconnect
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    setTimeout(connect, 2000);
                }
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
        }
        
        // Command functions for P&L management
        function resetPnLBaseline() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                alert('Not connected to server');
                return;
            }
            if (confirm('Reset Total P&L baseline to current portfolio value?')) {
                ws.send(JSON.stringify({ command: 'reset_pnl_baseline' }));
            }
        }
        
        function resetTodayPnL() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                alert('Not connected to server');
                return;
            }
            if (confirm('Reset Today\\'s P&L starting point to current value?')) {
                ws.send(JSON.stringify({ command: 'reset_today_pnl' }));
            }
        }
        
        function refreshBalances() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                alert('Not connected to server');
                return;
            }
            ws.send(JSON.stringify({ command: 'refresh_balances' }));
        }
        
        // Toast notification function
        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = 'toast-notification';
            const bgColor = type === 'success' ? '#00ff88' : type === 'error' ? '#ff6b6b' : '#00bfff';
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: ${bgColor};
                color: #000;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        // Apply density preference on load
        window.addEventListener('DOMContentLoaded', () => {
            const saved = localStorage.getItem('aureon_ui_density') || 'comfort';
            setDensity(saved);
            setInterval(updateStaleBadges, 15000);
            let chartInitAttempts = 0;
            const tryInitCharts = () => {
                chartInitAttempts += 1;
                initMetricCharts();
                initQuantumCharts();
                initLearningCharts();
                if (!window.__metricChartsInitialized && chartInitAttempts < 6) {
                    setTimeout(tryInitCharts, 500);
                }
            };
            tryInitCharts();
        });

        const metricCharts = {};
        const metricSeries = {
            total_value: [],
            cash_available: [],
            pnl_today: [],
            pnl_total: []
        };
        const metricMaxPoints = 40;

        const quantumCharts = {};
        const stargateDefaults = [
            { id: 'giza', label: 'Giza', x: 22, y: 38, freq: 432, casimir: 0.95 },
            { id: 'stonehenge', label: 'Stonehenge', x: 42, y: 28, freq: 396, casimir: 0.88 },
            { id: 'machu', label: 'Machu', x: 26, y: 66, freq: 528, casimir: 0.9 },
            { id: 'angkor', label: 'Angkor', x: 70, y: 58, freq: 417, casimir: 0.87 },
            { id: 'sedona', label: 'Sedona', x: 20, y: 44, freq: 639, casimir: 0.82 },
            { id: 'uluru', label: 'Uluru', x: 78, y: 78, freq: 741, casimir: 0.79 }
        ];

        const learningCharts = {};
        const learningSeries = {
            pnl: [],
            wins: 0,
            losses: 0
        };

        function initMetricCharts() {
            if (window.__metricChartsInitialized) return;
            if (!window.ApexCharts) return;
            const configs = [
                { key: 'total_value', el: 'chart-total-value', color: '#ffaa00' },
                { key: 'cash_available', el: 'chart-cash-available', color: '#00bfff' },
                { key: 'pnl_today', el: 'chart-pnl-today', color: '#00ff88' },
                { key: 'pnl_total', el: 'chart-pnl-total', color: '#9966ff' }
            ];
            configs.forEach(cfg => {
                const container = document.getElementById(cfg.el);
                if (!container) return;
                const chart = new ApexCharts(container, {
                    chart: {
                        type: 'line',
                        height: 44,
                        sparkline: { enabled: true }
                    },
                    stroke: { width: 2, curve: 'smooth' },
                    colors: [cfg.color],
                    tooltip: { enabled: false },
                    series: [{ name: cfg.key, data: metricSeries[cfg.key] || [] }]
                });
                chart.render();
                metricCharts[cfg.key] = chart;
            });
            window.__metricChartsInitialized = true;
        }

        function pushMetric(key, value) {
            if (value === undefined || value === null || Number.isNaN(value)) return;
            if (!metricSeries[key]) metricSeries[key] = [];
            metricSeries[key].push(value);
            if (metricSeries[key].length > metricMaxPoints) metricSeries[key].shift();
            const chart = metricCharts[key];
            if (chart) chart.updateSeries([{ data: metricSeries[key] }], true);
        }

        function initQuantumCharts() {
            if (window.__quantumChartsInitialized) return;
            if (!window.ApexCharts) return;

            const coherenceEl = document.getElementById('quantum-coherence-chart');
            if (coherenceEl) {
                const coherenceChart = new ApexCharts(coherenceEl, {
                    chart: {
                        type: 'radialBar',
                        height: 220,
                        sparkline: { enabled: true }
                    },
                    series: [61.8],
                    labels: ['Coherence'],
                    colors: ['#00ff88'],
                    plotOptions: {
                        radialBar: {
                            hollow: { size: '55%' },
                            dataLabels: {
                                name: { show: false },
                                value: {
                                    fontSize: '22px',
                                    color: '#e2e8f0',
                                    formatter: val => `${val.toFixed(1)}%`
                                }
                            }
                        }
                    },
                    stroke: { lineCap: 'round' }
                });
                coherenceChart.render();
                quantumCharts.coherence = coherenceChart;
            }

            const freqEl = document.getElementById('quantum-frequency-chart');
            if (freqEl) {
                const freqChart = new ApexCharts(freqEl, {
                    chart: {
                        type: 'bar',
                        height: 220,
                        toolbar: { show: false }
                    },
                    plotOptions: { bar: { borderRadius: 6, columnWidth: '50%' } },
                    colors: ['#00bfff'],
                    dataLabels: { enabled: false },
                    xaxis: {
                        categories: ['Schumann', 'Love', 'Alpha', 'Theta', 'Delta'],
                        labels: { style: { colors: '#94a3b8', fontSize: '11px' } }
                    },
                    yaxis: {
                        labels: { style: { colors: '#94a3b8', fontSize: '11px' } }
                    },
                    series: [{ name: 'Hz', data: [7.83, 528, 10.2, 6.8, 2.1] }]
                });
                freqChart.render();
                quantumCharts.frequencies = freqChart;
            }

            renderStargateMap(stargateDefaults);
            window.__quantumChartsInitialized = true;
        }

        function renderStargateMap(nodes) {
            const map = document.getElementById('stargate-map');
            if (!map) return;
            map.innerHTML = '';
            nodes.forEach(node => {
                const dot = document.createElement('div');
                dot.className = 'stargate-node';
                dot.style.left = `${node.x}%`;
                dot.style.top = `${node.y}%`;
                dot.dataset.stargateId = node.id;

                const label = document.createElement('div');
                label.className = 'stargate-label';
                label.style.left = `${node.x}%`;
                label.style.top = `${node.y}%`;
                label.textContent = node.label;

                map.appendChild(dot);
                map.appendChild(label);
            });
        }

        function updateStargateMap(nodes) {
            if (!nodes || nodes.length === 0) return;
            const map = document.getElementById('stargate-map');
            if (!map) return;
            const byId = {};
            nodes.forEach(n => { byId[n.id] = n; });
            map.querySelectorAll('.stargate-node').forEach(node => {
                const id = node.dataset.stargateId;
                const info = byId[id];
                if (!info) return;
                const resonance = info.resonance || info.coherence || 0;
                node.classList.toggle('active', resonance >= 0.618);
                node.style.boxShadow = resonance >= 0.618 ? '0 0 14px rgba(0, 255, 136, 0.6)' : 'none';
            });
        }

        function initLearningCharts() {
            if (window.__learningChartsInitialized) return;
            if (!window.ApexCharts) return;

            const pnlEl = document.getElementById('learning-pnl-chart');
            if (pnlEl) {
                const pnlChart = new ApexCharts(pnlEl, {
                    chart: {
                        type: 'line',
                        height: 240,
                        toolbar: { show: false }
                    },
                    stroke: { width: 2, curve: 'smooth' },
                    colors: ['#00ff88'],
                    series: [{ name: 'PnL', data: learningSeries.pnl }],
                    xaxis: { labels: { show: false } },
                    yaxis: { labels: { style: { colors: '#94a3b8', fontSize: '11px' } } },
                    grid: { borderColor: 'rgba(148, 163, 184, 0.1)' },
                    tooltip: { enabled: false }
                });
                pnlChart.render();
                learningCharts.pnl = pnlChart;
            }

            const winLossEl = document.getElementById('learning-winloss-chart');
            if (winLossEl) {
                const winLossChart = new ApexCharts(winLossEl, {
                    chart: {
                        type: 'bar',
                        height: 240,
                        toolbar: { show: false }
                    },
                    plotOptions: { bar: { borderRadius: 6, columnWidth: '40%' } },
                    colors: ['#00ff88', '#ff3366'],
                    dataLabels: { enabled: false },
                    xaxis: {
                        categories: ['Wins', 'Losses'],
                        labels: { style: { colors: '#94a3b8', fontSize: '11px' } }
                    },
                    yaxis: { labels: { style: { colors: '#94a3b8', fontSize: '11px' } } },
                    series: [{ name: 'Count', data: [0, 0] }]
                });
                winLossChart.render();
                learningCharts.winloss = winLossChart;
            }

            window.__learningChartsInitialized = true;
        }
        
        function handleMessage(data) {
            switch(data.type) {
                case 'full_state':
                    updateFullState(data);
                    markLive('trading', 'Full State');
                    markLive('systems', 'Full State');
                    break;
                case 'queen_update':
                    updateQueen(data);
                    markLive('trading', 'Queen Update');
                    break;
                case 'signal':
                    addSignal(data.signal);
                    markLive('trading', 'Signal');
                    break;
                case 'portfolio_update':
                    updatePortfolio(data);
                    markLive('trading', 'Portfolio');
                    break;
                case 'market_update':
                    updateMarket(data);
                    markLive('market', 'Market Update');
                    break;
                case 'systems_update':
                    updateSystems(data.systems);
                    markLive('systems', 'Systems Update');
                    break;
                case 'learning_update':
                    updateLearningTab(data);
                    markLive('learning', 'Learning Update');
                    break;
                case 'live_update':
                    handleLiveUpdate(data.data);
                    updateHubStats(data.data);
                    markLive('orca', 'Orca Live');
                    break;
                case 'command_response':
                    // Handle command responses
                    if (data.success) {
                        console.log('✅ Command success:', data.message);
                        // Show toast notification
                        showToast(data.message, 'success');
                    } else {
                        console.error('❌ Command failed:', data.message);
                        showToast('Error: ' + data.message, 'error');
                    }
                    break;
            }

            if (typeof data.type === 'string') {
                if (data.type.includes('whale')) markLive('whales', 'Whale Activity');
                if (data.type.includes('bot')) markLive('bots', 'Bot Intel');
                if (data.type.includes('quantum') || data.type.includes('timeline')) markLive('quantum', 'Quantum Signal');
                if (data.type.includes('learning')) markLive('learning', 'Learning Update');
            }
        }

        function markLive(tab, eventLabel) {
            const badge = document.getElementById(`live-${tab}`);
            if (badge) {
                badge.classList.add('active');
                badge.classList.remove('stale', 'dead');
            }
            const now = Date.now();
            const timeEl = document.getElementById(`time-${tab}`);
            if (timeEl) timeEl.textContent = new Date(now).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
            if (eventLabel) {
                const eventEl = document.getElementById(`event-${tab}`);
                if (eventEl) eventEl.textContent = eventLabel;
            }
            window.__aureonTabLast = window.__aureonTabLast || {};
            window.__aureonTabLast[tab] = now;
        }

        function updateStaleBadges() {
            const thresholds = { stale: 45000, dead: 120000 }; // 45s stale, 2m dead
            const last = window.__aureonTabLast || {};
            const tabs = ['trading', 'whales', 'bots', 'market', 'quantum', 'learning', 'orca', 'systems'];
            const now = Date.now();
            tabs.forEach(tab => {
                const badge = document.getElementById(`live-${tab}`);
                if (!badge) return;
                const ts = last[tab];
                if (!ts) return;
                const age = now - ts;
                badge.classList.remove('stale', 'dead');
                if (age > thresholds.dead) badge.classList.add('dead');
                else if (age > thresholds.stale) badge.classList.add('stale');
            });
        }

        function openHub(name) {
            const frame = document.getElementById('hub-frame');
            if (!frame) return;
            const routes = {
                orca: '/hub/orca',
                queen: '/hub/queen',
                registry: '/hub/registry'
            };
            frame.src = routes[name] || '/hub/registry';
        }

        function updateHubStats(snapshot) {
            if (!snapshot) return;
            const stats = snapshot.session_stats || {};
            const trades = stats.total_trades || 0;
            const pnl = stats.total_pnl || 0;
            const active = snapshot.active_count || 0;
            const orcaText = `Trades: ${trades} | Open: ${active} | PnL: ${pnl.toFixed(4)}`;
            const orcaEl = document.getElementById('hub-orca');
            if (orcaEl) orcaEl.textContent = orcaText;

            if (snapshot.queen_message) {
                const queenEl = document.getElementById('hub-queen');
                if (queenEl) queenEl.textContent = snapshot.queen_message;
            }

            // Update flight check display
            updateFlightCheck(snapshot.flight_check);
        }

        function updateFlightCheck(flightCheck) {
            const container = document.getElementById('flight-check');
            if (!container || !flightCheck) return;

            const summary = flightCheck.summary || {};
            const online = summary.online_systems || 0;
            const total = summary.total_systems || 0;
            const pct = summary.online_pct || 0;
            const critical = summary.critical_online || false;

            const statusClass = critical ? 'online' : 'offline';
            const statusIcon = critical ? '✅' : '❌';
            const statusText = critical ? 'FLIGHT CHECK PASSED' : 'CRITICAL SYSTEMS OFFLINE';

            container.innerHTML = `
                <div class="flight-status ${statusClass}">
                    <span>${statusIcon}</span>
                    <span>${statusText}</span>
                    <span style="margin-left: auto;">${online}/${total} (${pct}%)</span>
                </div>
                <div class="flight-progress">
                    <div class="flight-progress-bar" style="width: ${pct}%"></div>
                </div>
                <div class="flight-details">
                    <div class="flight-item"><span>Exchanges:</span><span>${flightCheck.exchange_alpaca ? '✅' : '❌'} Alpaca ${flightCheck.exchange_kraken ? '✅' : '❌'} Kraken</span></div>
                    <div class="flight-item"><span>Queen:</span><span>${flightCheck.queen_wired ? '✅ Wired' : '❌ Offline'}</span></div>
                    <div class="flight-item"><span>ThoughtBus:</span><span>${flightCheck.thought_bus ? '✅' : '❌'}</span></div>
                    <div class="flight-item"><span>Intelligence:</span><span>${flightCheck.miner_brain || flightCheck.ultimate_intelligence ? '✅' : '❌'}</span></div>
                </div>
            `;
        }

        async function refreshHubRegistry() {
            try {
                const res = await fetch('/api/unified/hubs');
                const data = await res.json();
                if (data.registry_total !== undefined) {
                    const regEl = document.getElementById('hub-registry');
                    if (regEl) regEl.textContent = `${data.registry_total} systems`;
                }
            } catch (e) {}
        }
        
        function updateFullState(data) {
            if (data.portfolio) updatePortfolio(data);
            if (data.systems) updateSystems(data.systems);
            if (data.market) updateMarket(data);
            if (data.queen) updateQueen(data);
            if (data.learning) updateLearningTab({ learning: data.learning });
            if (data.signals) {
                data.signals.forEach(s => addSignal(s));
            }
            if (data.data) updateHubStats(data.data);
        }
        
        function updateQueen(data) {
            if (data.message) {
                document.getElementById('queen-message').textContent = data.message;
            }
            if (data.cosmic_score !== undefined) {
                document.getElementById('cosmic-score').textContent = (data.cosmic_score * 100).toFixed(0);
            }
            if (data.confidence !== undefined) {
                document.getElementById('queen-confidence').textContent = (data.confidence * 100).toFixed(0);
            }
            if (data.strategy) {
                document.getElementById('queen-strategy').textContent = data.strategy;
            }
        }
        
        function updatePortfolio(data) {
            if (data.portfolio) {
                const totalValue = data.portfolio.total_value_usd || 0;
                const cashAvailable = data.portfolio.cash_available || 0;
                document.getElementById('total-value').textContent = '$' + formatNumber(totalValue);
                document.getElementById('cash-available').textContent = '$' + formatNumber(cashAvailable);
                pushMetric('total_value', totalValue);
                pushMetric('cash_available', cashAvailable);
                
                const pnlToday = data.portfolio.pnl_today || 0;
                const pnlTodayEl = document.getElementById('pnl-today');
                pnlTodayEl.textContent = '$' + formatNumber(pnlToday);
                pnlTodayEl.className = 'stat-value ' + (pnlToday >= 0 ? '' : 'negative');
                pushMetric('pnl_today', pnlToday);
                
                const pnlTotal = data.portfolio.pnl_total || 0;
                const pnlTotalEl = document.getElementById('pnl-total');
                pnlTotalEl.textContent = '$' + formatNumber(pnlTotal);
                pnlTotalEl.className = 'stat-value ' + (pnlTotal >= 0 ? '' : 'negative');
                pushMetric('pnl_total', pnlTotal);
                
                // Update exchange breakdown
                updateExchangeBreakdown(data.portfolio.exchange_breakdown || {});
            }
            
            if (data.balances) {
                updateBalances(data.balances);
            }
        }
        
        function updateExchangeBreakdown(breakdown) {
            const container = document.getElementById('exchange-breakdown');
            if (!container) return;
            
            const exchanges = Object.keys(breakdown);
            if (exchanges.length === 0) {
                container.innerHTML = '<div class="empty-state">No exchange data available</div>';
                return;
            }
            
            const exchangeIcons = {
                'kraken': '🐙',
                'binance': '🟡',
                'alpaca': '🦙',
                'capital': '💰'
            };
            
            let html = '';
            for (const [exchange, data] of Object.entries(breakdown)) {
                const icon = exchangeIcons[exchange] || '💱';
                const totalUsd = data.total_usd || 0;
                const cashUsd = data.cash_usd || 0;
                const assetsUsd = totalUsd - cashUsd;
                const assets = data.assets || {};
                const assetCount = Object.keys(assets).length;
                
                // Build holdings list
                let holdingsHtml = '';
                const sortedAssets = Object.entries(assets).sort((a, b) => b[1] - a[1]);
                sortedAssets.slice(0, 5).forEach(([asset, amount]) => {
                    holdingsHtml += `<div style="display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px solid #222;">
                        <span style="color: #aaa;">${asset}</span>
                        <span style="color: #fff;">${formatNumber(amount)}</span>
                    </div>`;
                });
                if (sortedAssets.length > 5) {
                    holdingsHtml += `<div style="color: #666; font-size: 0.8em; text-align: center; padding-top: 4px;">+${sortedAssets.length - 5} more</div>`;
                }
                
                html += `
                    <div class="exchange-card" style="background: rgba(0,0,0,0.4); border: 1px solid #333; border-radius: 8px; padding: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: bold; color: #00bfff;">${icon} ${exchange.toUpperCase()}</span>
                            <span style="color: #ffaa00; font-size: 1.1em;">$${formatNumber(totalUsd)}</span>
                        </div>
                        <div style="font-size: 0.85em; color: #888; margin-bottom: 8px;">
                            <div>💵 Cash: <span style="color: #00ff88;">$${formatNumber(cashUsd)}</span></div>
                            <div>📈 Assets: <span style="color: #ff6b6b;">$${formatNumber(assetsUsd)}</span></div>
                        </div>
                        <div style="font-size: 0.8em; border-top: 1px solid #333; padding-top: 8px;">
                            <div style="color: #666; margin-bottom: 4px;">Holdings (${assetCount}):</div>
                            ${holdingsHtml || '<div style="color: #444;">No holdings</div>'}
                        </div>
                    </div>
                `;
            }
            container.innerHTML = html;
        }
        
        function updateBalances(balances) {
            const container = document.getElementById('balances-list');
            container.innerHTML = '';
            
            // Flatten all balances
            const allBalances = [];
            for (const [exchange, assets] of Object.entries(balances)) {
                for (const [asset, amount] of Object.entries(assets)) {
                    if (amount > 0.0001) {
                        allBalances.push({ exchange, asset, amount });
                    }
                }
            }
            
            // Sort by amount (descending)
            allBalances.sort((a, b) => b.amount - a.amount);
            
            // Show top 10
            allBalances.slice(0, 10).forEach(b => {
                const div = document.createElement('div');
                div.className = 'balance-item';
                div.innerHTML = `
                    <span class="balance-asset">${b.asset}</span>
                    <span class="balance-amount">${formatNumber(b.amount)}</span>
                    <span class="balance-value">${b.exchange}</span>
                `;
                container.appendChild(div);
            });
        }
        
        function updateSystems(systems) {
            const container = document.getElementById('systems-list');
            container.innerHTML = '';
            
            let onlineCount = 0;
            
            for (const [name, status] of Object.entries(systems)) {
                const isOnline = status === true || status === 'ONLINE';
                if (isOnline) onlineCount++;
                
                const div = document.createElement('div');
                div.className = 'system-item' + (isOnline ? '' : ' offline');
                div.innerHTML = `
                    <span class="system-name">${name}</span>
                    <span class="system-status ${isOnline ? '' : 'offline'}">${isOnline ? '✅' : '❌'}</span>
                `;
                container.appendChild(div);
            }
            
            document.getElementById('system-count').textContent = onlineCount;
        }
        
        function addSignal(signal) {
            const container = document.getElementById('signals-feed');
            
            const div = document.createElement('div');
            const isVoice = signal?.metadata?.voice;
            div.className = 'signal-item ' + (isVoice ? 'voice' : (signal.signal_type || 'hold').toLowerCase());
            
            const confidence = signal.confidence || 0;
            const ts = signal.timestamp ? new Date(signal.timestamp * 1000).toLocaleTimeString() : '';
            
            if (isVoice) {
                const who = signal?.metadata?.who || 'Queen';
                const what = signal?.metadata?.what || 'Monitoring';
                const where = signal?.metadata?.where || 'All exchanges';
                const how = signal?.metadata?.how || 'Batten Matrix 3-pass + 4th gate';
                const positions = signal?.metadata?.positions || [];
                const market = signal?.metadata?.market || [];
                const picks = signal?.metadata?.picks || [];
                const positionsText = positions.length ? positions.join(' | ') : 'No active positions';
                const marketText = market.length ? market.join(' | ') : 'No dominant movers';
                const picksText = picks.length ? picks.join(' | ') : 'No picks yet';

                div.innerHTML = `
                    <div class="signal-header">
                        <span class="signal-symbol">👑 ${who}</span>
                        <span class="signal-type hold">VOICE</span>
                    </div>
                    <div class="signal-details">
                        <strong>${what}</strong> · ${signal.reason || 'Live command stream'}
                    </div>
                    <div class="signal-meta">
                        <span>Where: ${where}</span>
                        <span>When: ${ts}</span>
                        <span>How: ${how}</span>
                        <span>Positions: ${positionsText}</span>
                        <span>Picks: ${picksText}</span>
                        <span style="grid-column: 1 / -1;">Market: ${marketText}</span>
                    </div>
                `;
            } else {
                div.innerHTML = `
                    <div class="signal-header">
                        <span class="signal-symbol">${signal.symbol}</span>
                        <span class="signal-type ${(signal.signal_type || 'HOLD').toLowerCase()}">${signal.signal_type || 'HOLD'}</span>
                    </div>
                    <div class="signal-details">
                        <strong>${signal.source}</strong>: ${signal.reason || 'No reason provided'}
                    </div>
                    <div class="signal-confidence">
                        <div class="signal-confidence-bar" style="width: ${confidence * 100}%"></div>
                    </div>
                `;
            }
            
            container.insertBefore(div, container.firstChild);
            
            // Keep only last 20 signals
            while (container.children.length > 20) {
                container.removeChild(container.lastChild);
            }
        }
        
        function updateMarket(data) {
            if (data.market) {
                document.getElementById('assets-tracked').textContent = data.market.total_assets_tracked || 0;
                document.getElementById('rising-count').textContent = data.market.rising_count || 0;
                
                // Top movers
                if (data.market.top_movers) {
                    updateMovers('top-movers', data.market.top_movers.filter(m => m.change >= 0));
                    updateMovers('top-fallers', data.market.top_movers.filter(m => m.change < 0));
                }
            }
        }
        
        function updateMovers(containerId, movers) {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            
            movers.slice(0, 5).forEach(m => {
                const div = document.createElement('div');
                div.className = 'mover-item';
                const changeClass = m.change >= 0 ? 'positive' : 'negative';
                div.innerHTML = `
                    <span class="mover-symbol">${m.symbol}</span>
                    <span class="mover-change ${changeClass}">${m.change >= 0 ? '+' : ''}${(m.change * 100).toFixed(2)}%</span>
                `;
                container.appendChild(div);
            });
        }
        
        function formatNumber(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(2) + 'K';
            return num.toFixed(4);
        }
        
        function handleLiveUpdate(data) {
             if (data.positions) {
                 updatePositions(data.positions);
             }
             if (data.recent_trades) {
                 updateRecentTrades(data.recent_trades);
             }
             if (data.queen_message) {
                 document.getElementById('queen-message').textContent = data.queen_message;
             }
             if (data.session_stats) {
                 const stats = data.session_stats;
                 const winRate = (stats.total_trades > 0) ? (stats.winning_trades / stats.total_trades * 100) : 50;
                 document.getElementById('queen-confidence').textContent = winRate.toFixed(0);
                 
                 if (stats.total_pnl !== undefined) {
                     const pnlEl = document.getElementById('pnl-today');
                     pnlEl.textContent = '$' + formatNumber(stats.total_pnl);
                     pnlEl.className = 'stat-value ' + (stats.total_pnl >= 0 ? '' : 'negative');
                     pushMetric('pnl_today', stats.total_pnl);
                 }
                 
                 // Generate cosmic score based on live activity
                 const activity = (stats.cycles % 99) + 1;
                 document.getElementById('cosmic-score').textContent = activity.toFixed(0);
             }
        }

        function updatePositions(positions) {
             const container = document.getElementById('positions-list');
             if (!positions || positions.length === 0) {
                 container.innerHTML = '<div style="text-align: center; color: #666; font-style: italic;">No active positions</div>';
                 return;
             }
             
             container.innerHTML = '';
             positions.forEach(p => {
                 const pnl = p.current_pnl || 0;
                 const pnlPct = p.current_pnl_pct || 0;
                 const isPos = pnl >= 0;
                 
                 const div = document.createElement('div');
                 div.className = 'balance-item';
                 div.style.borderLeft = isPos ? '3px solid var(--accent-green)' : '3px solid var(--accent-red)';
                 
                 div.innerHTML = `
                    <div style="flex: 1">
                        <span class="balance-asset">${p.symbol}</span>
                        <span style="font-size: 0.8em; color: #888;">${p.exchange}</span>
                    </div>
                    <div style="text-align: right">
                        <div style="color: #fff; font-weight: bold;">$${formatNumber(pnl)}</div>
                        <div style="font-size: 0.8em; color: ${isPos ? 'var(--accent-green)' : 'var(--accent-red)'}">
                            ${pnlPct.toFixed(2)}%
                        </div>
                    </div>
                 `;
                 container.appendChild(div);
             });
        }

        function updateRecentTrades(trades) {
             const container = document.getElementById('recent-trades');
             if (!trades || trades.length === 0) {
                 container.innerHTML = '<div style="text-align: center; color: #666; font-style: italic;">No recent trades</div>';
                 return;
             }
             
             container.innerHTML = '';
             trades.slice(0, 15).forEach(t => {
                 const isPositive = (t.pnl || 0) >= 0;
                 const sideColor = t.side === 'BUY' ? 'var(--accent-green)' : 
                                   t.side === 'SELL' ? 'var(--accent-red)' : 'var(--accent-gold)';
                 const timestamp = new Date(t.timestamp * 1000).toLocaleTimeString();
                 
                 const div = document.createElement('div');
                 div.className = 'balance-item';
                 div.style.borderLeft = `3px solid ${sideColor}`;
                 div.style.fontSize = '0.85em';
                 
                 div.innerHTML = `
                    <div style="flex: 1">
                        <span style="color: ${sideColor}; font-weight: bold;">${t.side}</span>
                        <span class="balance-asset">${t.symbol}</span>
                        <span style="font-size: 0.8em; color: #888;">${t.exchange}</span>
                    </div>
                    <div style="text-align: right">
                        <div style="color: #fff;">$${formatNumber(t.value_usd || 0)}</div>
                        <div style="font-size: 0.75em; color: #666;">${timestamp}</div>
                    </div>
                 `;
                 container.appendChild(div);
             });
        }

        // ═══════════════════════════════════════════════════════════════════
        // TAB-SPECIFIC UPDATE FUNCTIONS
        // ═══════════════════════════════════════════════════════════════════

        // Update whale tab
        function updateWhaleTab(data) {
            if (data.whales) {
                const feed = document.getElementById('whale-feed');
                if (feed) {
                    // Add new whale activity to feed
                    data.whales.forEach(w => {
                        const div = document.createElement('div');
                        div.className = 'signal-item ' + (w.side === 'buy' ? 'buy' : 'sell');
                        div.innerHTML = `
                            <div class="signal-header">
                                <span class="signal-symbol">🐋 ${w.symbol}</span>
                                <span class="signal-type ${w.side}">${w.side.toUpperCase()}</span>
                            </div>
                            <div class="signal-details">
                                <strong>$${formatNumber(w.volume)}</strong> | ${w.exchange}
                            </div>
                        `;
                        feed.insertBefore(div, feed.firstChild);
                        while (feed.children.length > 50) feed.removeChild(feed.lastChild);
                    });
                }
            }
            // Update whale stats
            if (data.whale_stats) {
                const el24h = document.getElementById('whale-24h');
                if (el24h) el24h.textContent = data.whale_stats.count_24h || 0;
                const elVol = document.getElementById('whale-volume');
                if (elVol) elVol.textContent = '$' + formatNumber(data.whale_stats.total_volume || 0);
                const elBulls = document.getElementById('whale-bulls');
                if (elBulls) elBulls.textContent = data.whale_stats.bulls || 0;
                const elBears = document.getElementById('whale-bears');
                if (elBears) elBears.textContent = data.whale_stats.bears || 0;
            }
        }

        // Update bot intelligence tab
        function updateBotTab(data) {
            const intel = data?.bot_intel || data?.bot_snapshot || data;
            if (!intel) return;

            // Update timestamp and status
            if (intel.last_update) {
                const date = new Date(intel.last_update * 1000);
                const timeStr = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                const timeEl = document.getElementById('time-bots');
                if (timeEl) timeEl.textContent = timeStr;
                
                const age = (Date.now()/1000) - intel.last_update;
                const liveEl = document.getElementById('live-bots');
                if (liveEl) {
                    if (age > 3600) { // 1 hour
                        liveEl.textContent = 'Archive';
                        liveEl.className = 'tab-live dead';
                    } else if (age > 300) { // 5 mins
                        liveEl.textContent = 'Stale';
                        liveEl.className = 'tab-live stale';
                    } else {
                        liveEl.textContent = 'Live';
                        liveEl.className = 'tab-live active';
                    }
                }
            }

            const countEl = document.getElementById('bot-count');
            if (countEl && intel.bot_count !== undefined) {
                countEl.textContent = intel.bot_count;
            }
            const totalEl = document.getElementById('total-bots');
            if (totalEl && intel.total_bots !== undefined) {
                totalEl.textContent = intel.total_bots;
            }
            const activeEl = document.getElementById('active-bots');
            if (activeEl && intel.active_bots !== undefined) {
                activeEl.textContent = intel.active_bots;
            }

            if (Array.isArray(intel.bot_firms)) {
                const list = document.getElementById('firms-list');
                if (list) {
                    list.innerHTML = '';
                    intel.bot_firms.slice(0, 8).forEach((f, idx) => {
                        const div = document.createElement('div');
                        const colors = ['var(--accent-purple)', 'var(--accent-blue)', 'var(--accent-gold)', 'var(--accent-green)'];
                        const color = colors[idx % colors.length];
                        div.className = 'system-item';
                        div.style.borderLeftColor = color;
                        div.innerHTML = `
                            <span class="system-name">🏦 ${f.name || f.firm_name || 'Unknown Firm'}</span>
                            <span class="system-status">${f.status || 'Monitoring'}</span>
                        `;
                        list.appendChild(div);
                    });
                    if (!intel.bot_firms.length) {
                        list.innerHTML = '<div class="empty-state">Awaiting firm intelligence...</div>';
                    }
                }
            }

            if (Array.isArray(intel.bot_signatures)) {
                const signatures = document.getElementById('bot-signatures');
                if (signatures) {
                    signatures.innerHTML = '';
                    const colors = ['var(--accent-purple)', 'var(--accent-blue)', 'var(--accent-gold)', 'var(--accent-green)'];
                    intel.bot_signatures.slice(0, 6).forEach((sig, idx) => {
                        const div = document.createElement('div');
                        div.className = 'balance-item';
                        div.innerHTML = `
                            <span style="color: ${colors[idx % colors.length]};">${sig.name}</span>
                            <span>${sig.count} detected</span>
                        `;
                        signatures.appendChild(div);
                    });
                    if (!intel.bot_signatures.length) {
                        signatures.innerHTML = '<div class="empty-state">No bot signatures detected yet.</div>';
                    }
                }
            }

            if (Array.isArray(intel.bot_activity)) {
                const feed = document.getElementById('bot-activity');
                if (feed) {
                    feed.innerHTML = '';
                    intel.bot_activity.slice(0, 12).forEach(b => {
                        const div = document.createElement('div');
                        const side = b.side || 'hold';
                        div.className = 'signal-item ' + side;
                        div.innerHTML = `
                            <div class="signal-header">
                                <span class="signal-symbol">${b.pattern} @ ${b.symbol}</span>
                                <span class="signal-type ${side}">${side.toUpperCase()}</span>
                            </div>
                            <div class="signal-details">${b.firm} - ${b.description}</div>
                        `;
                        feed.appendChild(div);
                    });
                    if (!intel.bot_activity.length) {
                        feed.innerHTML = '<div class="empty-state">No bot activity yet.</div>';
                    }
                }
            }

            if (Array.isArray(intel.bot_map)) {
                const map = document.getElementById('bot-map-nodes');
                if (map) {
                    map.innerHTML = '';
                    intel.bot_map.forEach((node, idx) => {
                        const dot = document.createElement('div');
                        dot.className = 'bot-map-node' + (node.active ? ' active' : '');
                        const size = Math.max(6, Math.min(16, 6 + (node.intensity || 0) * 10));
                        dot.style.width = `${size}px`;
                        dot.style.height = `${size}px`;
                        dot.style.left = `${node.x}%`;
                        dot.style.top = `${node.y}%`;
                        dot.style.animationDelay = `${(idx % 5) * 0.2}s`;
                        dot.title = `${node.city} · ${node.firm}`;
                        map.appendChild(dot);

                        const label = document.createElement('div');
                        label.className = 'bot-map-label';
                        label.style.left = `${node.x}%`;
                        label.style.top = `${node.y}%`;
                        label.textContent = node.city;
                        map.appendChild(label);
                    });
                }
            }
        }

        // Update market feed tab
        function updateMarketFeedTab(data) {
            function renderFeed(elementId, prices) {
                const feed = document.getElementById(elementId);
                if (!feed || !prices) return;
                
                feed.innerHTML = '';
                Object.entries(prices).slice(0, 15).forEach(([sym, val]) => {
                    let price = 0;
                    let change = 0;
                    
                    if (typeof val === 'object' && val !== null) {
                        price = val.price || 0;
                        change = val.change || 0;
                    } else {
                        price = val;
                        change = 0; 
                    }
                    
                    const changeClass = change >= 0 ? 'positive' : 'negative';
                    const sign = change >= 0 ? '+' : '';
                    const changeText = (change * 100).toFixed(2) + '%';
                    
                    const div = document.createElement('div');
                    div.className = 'mover-item';
                    div.innerHTML = `<span class="mover-symbol">${sym}</span><span class="mover-change ${changeClass}">$${formatNumber(price)} <small>(${sign}${changeText})</small></span>`;
                    feed.appendChild(div);
                });
            }

            if (data.kraken_prices) renderFeed('kraken-feed', data.kraken_prices);
            if (data.binance_prices) renderFeed('binance-feed', data.binance_prices);
            if (data.alpaca_prices) renderFeed('alpaca-feed', data.alpaca_prices);
        }

        // Update quantum tab
        function updateQuantumTab(data) {
            if (data.quantum) {
                markLive('quantum', 'Quantum Update');
                const coherence = data.quantum.coherence ?? 0.618;
                const timelineEl = document.getElementById('active-timelines');
                if (timelineEl) timelineEl.textContent = data.quantum.active_timelines || 7;
                const anchoredEl = document.getElementById('anchored-timelines');
                if (anchoredEl) anchoredEl.textContent = data.quantum.anchored_timelines || 3;
                const schumannEl = document.getElementById('schumann-hz');
                if (schumannEl && data.quantum.schumann_hz !== undefined) schumannEl.textContent = data.quantum.schumann_hz.toFixed(2);
                const loveEl = document.getElementById('love-freq');
                if (loveEl && data.quantum.love_freq !== undefined) loveEl.textContent = data.quantum.love_freq;

                if (quantumCharts.coherence) {
                    quantumCharts.coherence.updateSeries([coherence * 100], true);
                }

                if (quantumCharts.frequencies && data.quantum.frequencies) {
                    const freq = data.quantum.frequencies;
                    const freqData = [
                        freq.schumann ?? 7.83,
                        freq.love ?? 528,
                        freq.alpha ?? 10.2,
                        freq.theta ?? 6.8,
                        freq.delta ?? 2.1
                    ];
                    quantumCharts.frequencies.updateSeries([{ data: freqData }], true);
                }

                if (data.quantum.stargates) {
                    if (!document.querySelector('.stargate-node')) {
                        renderStargateMap(data.quantum.stargates);
                    }
                    updateStargateMap(data.quantum.stargates);
                }

                if (data.quantum.timelines) {
                    const list = document.getElementById('quantum-timelines');
                    if (list) {
                        list.innerHTML = '';
                        data.quantum.timelines.slice(0, 6).forEach(t => {
                            const div = document.createElement('div');
                            div.className = 'timeline-item';
                            const coherenceVal = t.coherence ?? t.score ?? 0;
                            const tagClass = coherenceVal >= 0.618 ? 'good' : 'warn';
                            div.innerHTML = `
                                <span>${t.name || t.id || 'timeline'}</span>
                                <span class="timeline-tag ${tagClass}">${coherenceVal.toFixed(3)}</span>
                            `;
                            list.appendChild(div);
                        });
                        if (!data.quantum.timelines.length) {
                            list.innerHTML = '<div class="empty-state">Awaiting timeline signals...</div>';
                        }
                    }
                }
            }
        }

        function updateLearningTab(data) {
            if (!data || !data.learning) return;
            const learning = data.learning;
            const totalTrades = learning.total_trades || 0;
            const wins = learning.wins || 0;
            const losses = learning.losses || 0;
            const winRate = learning.win_rate || 0;

            const totalEl = document.getElementById('learning-total-trades');
            if (totalEl) totalEl.textContent = totalTrades;
            const winRateEl = document.getElementById('learning-win-rate');
            if (winRateEl) winRateEl.textContent = `${winRate.toFixed(1)}%`;
            const avgEl = document.getElementById('learning-avg-pnl');
            if (avgEl) avgEl.textContent = `$${formatNumber(learning.avg_pnl || 0)}`;
            const lossEl = document.getElementById('learning-loss-events');
            if (lossEl) lossEl.textContent = losses;

            if (learningCharts.pnl && Array.isArray(learning.pnl_series)) {
                learningCharts.pnl.updateSeries([{ data: learning.pnl_series }], true);
            }
            if (learningCharts.winloss) {
                learningCharts.winloss.updateSeries([{ data: [wins, losses] }], true);
            }

            if (learning.patterns) {
                const list = document.getElementById('learning-patterns');
                if (list) {
                    list.innerHTML = '';
                    learning.patterns.slice(0, 8).forEach(p => {
                        const div = document.createElement('div');
                        div.className = 'pattern-item';
                        const winsCount = p.total_wins || 0;
                        const lossesCount = p.total_losses || 0;
                        const pnl = p.total_pnl || 0;
                        const badgeClass = pnl >= 0 ? 'win' : 'loss';
                        div.innerHTML = `
                            <span>${p.symbol || p.key || 'pattern'}</span>
                            <span class="pattern-badge ${badgeClass}">${winsCount}W/${lossesCount}L</span>
                        `;
                        list.appendChild(div);
                    });
                    if (!learning.patterns.length) {
                        list.innerHTML = '<div class="empty-state">Learning patterns will appear here...</div>';
                    }
                }
            }
            
            // Draw Queen Neural Network
            if (learning.queen_neuron) {
                drawNeuralNetwork(learning.queen_neuron);
            }
        }
        
        // Queen Neural Network Visualization
        function drawNeuralNetwork(neuronData) {
            const canvas = document.getElementById('neuron-canvas');
            if (!canvas || !neuronData) return;
            
            const ctx = canvas.getContext('2d');
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * 2;
            canvas.height = 250 * 2;
            ctx.scale(2, 2);
            
            const width = rect.width;
            const height = 250;
            ctx.clearRect(0, 0, width, height);
            
            const inputSize = neuronData.input_size || 7;
            const hiddenSize = neuronData.hidden_size || 12;
            const weights = neuronData.weights_input_hidden || [];
            
            // Update stats
            const versionEl = document.getElementById('neuron-version');
            if (versionEl) versionEl.textContent = 'v' + (neuronData.version || 1);
            const inputEl = document.getElementById('neuron-input-size');
            if (inputEl) inputEl.textContent = inputSize;
            const hiddenEl = document.getElementById('neuron-hidden-size');
            if (hiddenEl) hiddenEl.textContent = hiddenSize;
            const lrEl = document.getElementById('neuron-learning-rate');
            if (lrEl) lrEl.textContent = (neuronData.learning_rate || 0.01).toFixed(4);
            const ts = neuronData.timestamp || '';
            const tsEl = document.getElementById('neuron-timestamp');
            if (tsEl) tsEl.textContent = ts ? ts.split('T')[0] : '--';
            
            // Layer positions
            const layers = [
                { x: 60, count: inputSize, label: 'Input', color: '#00bfff' },
                { x: width / 2, count: hiddenSize, label: 'Hidden', color: '#ffaa00' },
                { x: width - 60, count: 1, label: 'Output', color: '#00ff88' }
            ];
            
            // Calculate neuron positions
            const positions = layers.map(layer => {
                const neurons = [];
                const spacing = (height - 40) / (layer.count + 1);
                for (let i = 0; i < layer.count; i++) {
                    neurons.push({ x: layer.x, y: 20 + spacing * (i + 1) });
                }
                return neurons;
            });
            
            // Draw connections with weight colors
            ctx.lineWidth = 0.5;
            for (let i = 0; i < positions[0].length; i++) {
                for (let j = 0; j < positions[1].length; j++) {
                    const weight = weights[i] ? (weights[i][j] || 0) : 0;
                    const intensity = Math.min(Math.abs(weight) * 2, 1);
                    const color = weight >= 0 ? 
                        `rgba(0, 255, 136, ${intensity * 0.6})` : 
                        `rgba(255, 107, 107, ${intensity * 0.6})`;
                    ctx.strokeStyle = color;
                    ctx.beginPath();
                    ctx.moveTo(positions[0][i].x, positions[0][i].y);
                    ctx.lineTo(positions[1][j].x, positions[1][j].y);
                    ctx.stroke();
                }
            }
            
            // Draw hidden to output connections
            const hiddenOutput = neuronData.weights_hidden_output || [];
            for (let i = 0; i < positions[1].length; i++) {
                const weight = hiddenOutput[i] || 0;
                const intensity = Math.min(Math.abs(weight) * 2, 1);
                const color = weight >= 0 ? 
                    `rgba(0, 255, 136, ${intensity * 0.8})` : 
                    `rgba(255, 107, 107, ${intensity * 0.8})`;
                ctx.strokeStyle = color;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(positions[1][i].x, positions[1][i].y);
                ctx.lineTo(positions[2][0].x, positions[2][0].y);
                ctx.stroke();
            }
            
            // Draw neurons
            layers.forEach((layer, layerIdx) => {
                positions[layerIdx].forEach((pos, i) => {
                    ctx.beginPath();
                    ctx.arc(pos.x, pos.y, 8, 0, Math.PI * 2);
                    ctx.fillStyle = layer.color;
                    ctx.fill();
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 1;
                    ctx.stroke();
                });
                
                // Layer label
                ctx.fillStyle = '#888';
                ctx.font = '10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(layer.label, layer.x, height - 5);
            });
        }

        // ═══════════════════════════════════════════════════════════════════
        // ORCA LIVE TAB FUNCTIONS
        // ═══════════════════════════════════════════════════════════════════
        
        let orcaConsoleLines = [];
        const MAX_CONSOLE_LINES = 200;
        let lastOrcaCycle = 0;
        let orcaStartTime = Date.now();
        
        function clearOrcaConsole() {
            orcaConsoleLines = [];
            const console = document.getElementById('orca-console');
            if (console) {
                console.innerHTML = `<span style="color: #00ff00;">🦈 ORCA KILL CYCLE - LIVE MONITOR</span>
<span style="color: #888;">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</span>
<span style="color: #888;">Console cleared. Waiting for activity...</span>`;
            }
        }
        
        function addOrcaConsoleLog(message, type = 'info') {
            const console = document.getElementById('orca-console');
            if (!console) return;
            
            const timestamp = new Date().toLocaleTimeString();
            const colorClass = {
                'buy': 'orca-log-buy',
                'sell': 'orca-log-sell',
                'info': 'orca-log-info',
                'success': 'orca-log-success',
                'warning': 'orca-log-warning',
                'error': 'orca-log-error',
                'cycle': 'orca-log-cycle',
                'pnl-pos': 'orca-log-pnl-pos',
                'pnl-neg': 'orca-log-pnl-neg'
            }[type] || 'orca-log-info';
            
            const line = `<span class="orca-log-entry ${colorClass}">[${timestamp}] ${message}</span>`;
            orcaConsoleLines.push(line);
            
            // Keep only last N lines
            while (orcaConsoleLines.length > MAX_CONSOLE_LINES) {
                orcaConsoleLines.shift();
            }
            
            console.innerHTML = orcaConsoleLines.join('\\n');
            console.scrollTop = console.scrollHeight;
        }
        
        function updateOrcaTab(data) {
            if (!data) return;
            
            const snapshot = data.data || data;
            const stats = snapshot.session_stats || {};
            const positions = snapshot.positions || [];
            const executions = snapshot.recent_trades || data.recent_trades || [];
            
            // Update cycle counter
            const cycles = stats.cycles || 0;
            const cycleEl = document.getElementById('orca-cycle');
            const cyclesEl = document.getElementById('orca-cycles');
            if (cycleEl) cycleEl.textContent = cycles;
            if (cyclesEl) cyclesEl.textContent = cycles;
            
            // Log new cycle
            if (cycles > lastOrcaCycle && lastOrcaCycle > 0) {
                addOrcaConsoleLog(`═══ CYCLE ${cycles} STARTED ═══`, 'cycle');
            }
            lastOrcaCycle = cycles;
            
            // Update session stats
            const trades = stats.total_trades || 0;
            const wins = stats.winning_trades || 0;
            const pnl = stats.total_pnl || 0;
            const winRate = trades > 0 ? ((wins / trades) * 100).toFixed(1) : '--';
            
            const tradesEl = document.getElementById('orca-trades');
            const winsEl = document.getElementById('orca-wins');
            const winrateEl = document.getElementById('orca-winrate');
            const pnlEl = document.getElementById('orca-pnl');
            
            if (tradesEl) tradesEl.textContent = trades;
            if (winsEl) winsEl.textContent = wins;
            if (winrateEl) winrateEl.textContent = winRate + '%';
            if (pnlEl) {
                pnlEl.textContent = '$' + pnl.toFixed(4);
                pnlEl.style.color = pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
            }
            
            // Update status
            const statusEl = document.getElementById('orca-status-text');
            const heartbeat = document.getElementById('orca-heartbeat');
            const lastActivityEl = document.getElementById('orca-last-activity');
            const modeEl = document.getElementById('orca-mode');
            
            const isActive = cycles > 0 || positions.length > 0 || trades > 0;
            if (statusEl) {
                statusEl.textContent = isActive ? 'HUNTING' : 'STANDBY';
                statusEl.style.color = isActive ? 'var(--accent-green)' : 'var(--accent-gold)';
            }
            if (heartbeat) {
                heartbeat.style.background = isActive ? '#00ff00' : '#666';
            }
            if (lastActivityEl) {
                const elapsed = Math.floor((Date.now() - orcaStartTime) / 1000);
                const mins = Math.floor(elapsed / 60);
                const secs = elapsed % 60;
                lastActivityEl.textContent = `Running: ${mins}m ${secs}s`;
            }
            if (modeEl) {
                modeEl.textContent = 'Mode: ' + (snapshot.mode || 'STANDARD');
            }
            
            // Update positions count
            const posCountEl = document.getElementById('orca-position-count');
            if (posCountEl) posCountEl.textContent = positions.length;
            
            // Update positions display
            const posContainer = document.getElementById('orca-positions');
            if (posContainer) {
                if (positions.length === 0) {
                    posContainer.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">No active positions</div>';
                } else {
                    posContainer.innerHTML = positions.map(pos => {
                        const pnl = pos.current_pnl || 0;
                        const pnlPct = pos.current_pnl_pct || 0;
                        const pnlColor = pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
                        return `
                            <div class="balance-item" style="border-left: 3px solid ${pnlColor};">
                                <div style="flex: 1;">
                                    <span class="balance-asset">${pos.symbol}</span>
                                    <span style="font-size: 0.8em; color: #888;">${pos.exchange || ''}</span>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: ${pnlColor}; font-weight: bold;">$${pnl.toFixed(4)}</div>
                                    <div style="font-size: 0.8em; color: ${pnlColor};">${pnlPct.toFixed(2)}%</div>
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            }
            
            // Update executions
            const execContainer = document.getElementById('orca-executions');
            if (execContainer && executions.length > 0) {
                execContainer.innerHTML = executions.slice(0, 10).map(exec => {
                    const side = (exec.side || exec.execution_type || 'BUY').toLowerCase();
                    const sideColor = side === 'buy' ? 'var(--accent-green)' : 
                                     side === 'sell' ? 'var(--accent-red)' : 'var(--accent-gold)';
                    const orderIdShort = exec.order_id ? (exec.order_id.slice(0, 10) + '...') : '--';
                    const ts = exec.timestamp ? new Date(exec.timestamp * 1000).toLocaleTimeString() : '--';
                    
                    return `
                        <div class="execution-item ${side}">
                            <div>
                                <span style="color: ${sideColor}; font-weight: bold;">${side.toUpperCase()}</span>
                                <span>${exec.symbol || '?'}</span>
                                <span style="color: #666; font-size: 0.8em;">${exec.exchange || ''}</span>
                            </div>
                            <div style="text-align: right;">
                                <div>$${(exec.value_usd || exec.price * exec.quantity || 0).toFixed(2)}</div>
                                <div style="font-size: 0.75em; color: #666;">ID: ${orderIdShort}</div>
                            </div>
                        </div>
                    `;
                }).join('');
                
                // Log new executions to console
                executions.slice(0, 3).forEach(exec => {
                    const side = (exec.side || 'BUY').toUpperCase();
                    const symbol = exec.symbol || '?';
                    const orderId = exec.order_id ? exec.order_id.slice(0, 12) : '--';
                    const value = (exec.value_usd || 0).toFixed(2);
                    
                    if (exec.timestamp && (exec.timestamp * 1000) > (Date.now() - 10000)) {
                        // Only log very recent executions
                        addOrcaConsoleLog(
                            `${side === 'BUY' ? '🟢' : '🔴'} ${side} ${symbol} | $${value} | OrderID: ${orderId}`,
                            side === 'BUY' ? 'buy' : 'sell'
                        );
                    }
                });
            }
            
            // Log session stats periodically
            if (cycles % 10 === 0 && cycles > 0) {
                const pnlType = pnl >= 0 ? 'pnl-pos' : 'pnl-neg';
                addOrcaConsoleLog(`📊 Stats: Cycles=${cycles} | Trades=${trades} | Wins=${wins} | P&L=$${pnl.toFixed(4)}`, pnlType);
            }
        }

        // Update systems tab
        function updateSystemsTab(data) {
            if (data.systems_registry) {
                const registry = document.getElementById('full-registry');
                if (registry) {
                    registry.innerHTML = '';
                    Object.entries(data.systems_registry).forEach(([name, status]) => {
                        const isOnline = status === true || status === 'ONLINE';
                        const div = document.createElement('div');
                        div.className = 'system-item' + (isOnline ? '' : ' offline');
                        div.innerHTML = `
                            <span class="system-name">${name}</span>
                            <span class="system-status ${isOnline ? '' : 'offline'}">${isOnline ? '✅' : '❌'}</span>
                        `;
                        registry.appendChild(div);
                    });
                }
                // Count stats
                const total = Object.keys(data.systems_registry).length;
                const online = Object.values(data.systems_registry).filter(s => s === true || s === 'ONLINE').length;
                const totalEl = document.getElementById('total-systems');
                if (totalEl) totalEl.textContent = total;
                const onlineEl = document.getElementById('online-systems');
                if (onlineEl) onlineEl.textContent = online;
            }
            if (data.cycles !== undefined) {
                const cyclesEl = document.getElementById('total-cycles');
                if (cyclesEl) cyclesEl.textContent = data.cycles;
            }
        }

        // Extend handleMessage to update all tabs
        const originalHandleMessage = handleMessage;
        handleMessage = function(data) {
            originalHandleMessage(data);
            // Update tab-specific content
            updateWhaleTab(data);
            updateBotTab(data);
            updateMarketFeedTab(data);
            updateQuantumTab(data);
            updateLearningTab(data);
            updateOrcaTab(data);
            updateSystemsTab(data);
        };

        // Clock
        function updateClock() {
            const now = new Date();
            document.getElementById('clock').textContent = now.toLocaleTimeString();
        }
        setInterval(updateClock, 1000);
        updateClock();
        
        // Connect on load
        refreshHubRegistry();
        setInterval(refreshHubRegistry, 30000);
        connect();
    </script>
</body>
</html>
"""


# ════════════════════════════════════════════════════════════════════════════
# COMMAND CENTER
# ════════════════════════════════════════════════════════════════════════════

class AureonCommandCenter:
    """
    Unified Command Center - All systems integrated into one dashboard.
    """
    
    def __init__(self, port: int = 8800):
        self.port = port
        self.running = False
        self.clients: Set = set()
        
        # Initialize systems
        self.kraken = None
        self.binance = None
        self.alpaca = None
        self.queen = None
        self.mycelium = None
        self.thought_bus = None
        self.miner = None
        self.harmonic = None
        self.wave_scanner = None
        self.ultimate_intel = None
        self.timeline_oracle = None
        self.quantum_mirror = None
        self.conversion_hub = None
        
        # State
        self.portfolio = PortfolioState()
        self.market = MarketOverview()
        self.signals: deque = deque(maxlen=100)
        self.prices: Dict[str, float] = {}
        self.last_snapshot: Dict[str, Any] = {}
        self.recent_trades: deque = deque(maxlen=50)  # Last 50 trade executions
        self.registry = None
        self.registry_snapshot: Dict[str, Any] = {
            "total": 0,
            "categories": {},
            "systems": [],
            "timestamp": 0.0
        }

        # Learning state
        self.learning_last_update = 0.0
        self.learning_snapshot: Dict[str, Any] = {}

        # Bot intelligence state
        self.bot_last_update = 0.0
        self.bot_snapshot: Dict[str, Any] = {}
        
        # Stats
        self.updates_sent = 0
        self.last_update = 0.0
        self.last_voice_ts = 0.0
        self.last_voice_hash = ""
        
        # Web server
        if AIOHTTP_AVAILABLE:
            self.app = web.Application()
            self.app.router.add_get('/', self.handle_index)
            self.app.router.add_get('/health', self.handle_health)
            self.app.router.add_get('/ws', self.handle_websocket)
            self.app.router.add_get('/api/status', self.handle_api_status)
            self.app.router.add_get('/api/portfolio', self.handle_api_portfolio)
            self.app.router.add_get('/api/signals', self.handle_api_signals)
            self.app.router.add_get('/api/unified/hubs', self.handle_api_unified_hubs)
            self.app.router.add_get('/api/unified/registry', self.handle_api_unified_registry)
            self.app.router.add_get('/hub/orca', self.handle_hub_orca)
            self.app.router.add_get('/hub/orca/ws', self.handle_hub_orca_ws)
            self.app.router.add_get('/hub/orca/api/status', self.handle_hub_orca_status)
            self.app.router.add_post('/hub/orca/api/stealth', self.handle_hub_orca_stealth)
            self.app.router.add_get('/hub/orca/api/predator', self.handle_hub_orca_predator)
            self.app.router.add_get('/hub/queen', self.handle_hub_queen)
            self.app.router.add_get('/hub/queen/ws', self.handle_hub_queen_ws)
            self.app.router.add_get('/hub/registry', self.handle_hub_registry)
    
    def initialize_systems(self):
        """Initialize all trading systems."""
        if not SYSTEMS_STATUS:
            load_systems()
        print("\n" + "=" * 70)
        print("👑🌌 AUREON COMMAND CENTER - INITIALIZING ALL SYSTEMS")
        print("=" * 70)
        
        # Exchange Clients
        print("\n📊 CONNECTING TO EXCHANGES...")
        
        if KrakenClient:
            try:
                self.kraken = KrakenClient()
                print("   🐙 Kraken: CONNECTED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"Kraken error: {e}")
        
        if BinanceClient:
            try:
                self.binance = BinanceClient()
                print("   🟡 Binance: CONNECTED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"Binance error: {e}")
        
        if AlpacaClient:
            try:
                self.alpaca = AlpacaClient()
                print("   🦙 Alpaca: CONNECTED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"Alpaca error: {e}")
        
        # Neural Systems
        print("\n👑 WIRING NEURAL SYSTEMS...")
        
        if ThoughtBus:
            try:
                self.thought_bus = ThoughtBus()
                print("   📡 Thought Bus: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"ThoughtBus error: {e}")
        
        if MyceliumNetwork:
            try:
                self.mycelium = MyceliumNetwork(initial_capital=1000.0)
                print("   🍄 Mycelium Network: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"Mycelium error: {e}")
        
        if QueenHiveMind:
            try:
                self.queen = QueenHiveMind()
                print("   👑 Queen Hive Mind: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"Queen error: {e}")
        
        # Intelligence Systems
        print("\n🧠 WIRING INTELLIGENCE SYSTEMS...")
        
        if MinerBrain:
            try:
                self.miner = MinerBrain()
                print("   🧠 Miner Brain: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"MinerBrain error: {e}")
        
        if ProbabilityUltimateIntelligence:
            try:
                self.ultimate_intel = ProbabilityUltimateIntelligence()
                print("   💎 Ultimate Intelligence: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"UltimateIntel error: {e}")
        
        if TimelineOracle:
            try:
                self.timeline_oracle = TimelineOracle()
                print("   ⏳🔮 Timeline Oracle: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"TimelineOracle error: {e}")
        
        if QuantumMirrorScanner:
            try:
                self.quantum_mirror = QuantumMirrorScanner()
                print("   🔮 Quantum Mirror: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"QuantumMirror error: {e}")
        
        # Harmonic & Momentum
        print("\n🌊 WIRING HARMONIC & MOMENTUM...")
        
        if HarmonicWaveFusion:
            try:
                self.harmonic = HarmonicWaveFusion()
                print("   🌊 Harmonic Fusion: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"Harmonic error: {e}")
        
        if GlobalWaveScanner:
            try:
                self.wave_scanner = GlobalWaveScanner()
                print("   🌊🔭 Wave Scanner: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"WaveScanner error: {e}")

        # Conversion Hub
        if MyceliumConversionHub:
            try:
                self.conversion_hub = MyceliumConversionHub()
                print("   🍄 Conversion Hub: WIRED")
                time.sleep(0.1) # Yield GIL
            except Exception as e:
                logger.error(f"ConversionHub error: {e}")

        working = sum([
            1 for x in [
                self.kraken, self.binance, self.alpaca,
                self.queen, self.mycelium, self.thought_bus,
                self.miner, self.harmonic, self.wave_scanner,
                self.ultimate_intel, self.timeline_oracle, self.quantum_mirror,
                self.conversion_hub
            ] if x is not None
        ])
        
        print("\n" + "=" * 70)
        print(f"✅ COMMAND CENTER INITIALIZED: {working} systems operational")
        print("=" * 70)
    
    async def handle_health(self, request):
        """Health check endpoint for Docker/K8s liveness probes."""
        return web.json_response({
            "status": "healthy",
            "service": "aureon-command-center",
            "timestamp": time.time()
        })
    
    async def handle_index(self, request):
        """Serve the command center UI."""
        return web.Response(text=COMMAND_CENTER_HTML, content_type='text/html')
    
    async def handle_websocket(self, request):
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.clients.add(ws)
        logger.info(f"👑 Client connected (total: {len(self.clients)})")
        
        # Send initial state
        await self.load_recent_trades()  # Load trades before sending
        learning_snapshot = self.load_learning_snapshot()
        bot_snapshot = self.load_bot_intel_snapshot()
        await ws.send_json({
            "type": "full_state",
            "systems": SYSTEMS_STATUS,
            "portfolio": asdict(self.portfolio),
            "market": asdict(self.market),
            "learning": learning_snapshot,
            "bot_intel": bot_snapshot,
            "signals": [asdict(s) if hasattr(s, '__dataclass_fields__') else s for s in list(self.signals)[-20:]],
            "recent_trades": [asdict(t) for t in list(self.recent_trades)[:15]],
            "queen": {
                "message": "Welcome to Aureon Command Center. All systems operational.",
                "cosmic_score": 0.5,
                "confidence": 0.5,
                "strategy": "SCANNING"
            }
        })
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Handle commands from UI
                    data = json.loads(msg.data)
                    await self.handle_command(data, ws)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            self.clients.discard(ws)
        
        return ws
    
    async def handle_command(self, data: Dict, ws):
        """Handle commands from the UI."""
        cmd = data.get("command")
        
        if cmd == "refresh_balances":
            await self.fetch_all_balances()
            await self.broadcast_portfolio()
        elif cmd == "get_signals":
            await ws.send_json({
                "type": "signals",
                "signals": [asdict(s) if hasattr(s, '__dataclass_fields__') else s for s in list(self.signals)[-50:]]
            })
        elif cmd == "reset_pnl_baseline":
            # Reset P&L baseline to current portfolio value
            try:
                baseline_data = {
                    "timestamp": datetime.now().isoformat(),
                    "total_value_usdc": self.portfolio.total_value_usd,
                    "details": {
                        "meta": {"usdt_usdc": 1.0},
                        "note": f"Baseline reset from UI on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                }
                with open("pnl_baseline.json", "w") as f:
                    json.dump(baseline_data, f, indent=2)
                self.portfolio.baseline_value = self.portfolio.total_value_usd
                self.portfolio.pnl_total = 0.0
                await ws.send_json({
                    "type": "command_response",
                    "command": "reset_pnl_baseline",
                    "success": True,
                    "message": f"P&L baseline reset to ${self.portfolio.total_value_usd:.4f}"
                })
                await self.broadcast_portfolio()
                logger.info(f"P&L baseline reset to ${self.portfolio.total_value_usd:.4f}")
            except Exception as e:
                await ws.send_json({
                    "type": "command_response",
                    "command": "reset_pnl_baseline",
                    "success": False,
                    "message": str(e)
                })
        elif cmd == "reset_today_pnl":
            # Reset today's P&L starting point
            try:
                today_data = {
                    "date": time.strftime("%Y-%m-%d"),
                    "value": self.portfolio.total_value_usd
                }
                with open("pnl_today_start.json", "w") as f:
                    json.dump(today_data, f)
                self.portfolio.pnl_today = 0.0
                await ws.send_json({
                    "type": "command_response",
                    "command": "reset_today_pnl",
                    "success": True,
                    "message": f"Today's P&L reset at ${self.portfolio.total_value_usd:.4f}"
                })
                await self.broadcast_portfolio()
            except Exception as e:
                await ws.send_json({
                    "type": "command_response",
                    "command": "reset_today_pnl",
                    "success": False,
                    "message": str(e)
                })
    
    async def handle_api_status(self, request):
        """REST API: System status."""
        return web.json_response({
            "status": "online",
            "systems": SYSTEMS_STATUS,
            "timestamp": time.time()
        })
    
    async def handle_api_portfolio(self, request):
        """REST API: Portfolio data."""
        return web.json_response(asdict(self.portfolio))
    
    async def handle_api_signals(self, request):
        """REST API: Recent signals."""
        return web.json_response({
            "signals": [asdict(s) if hasattr(s, '__dataclass_fields__') else s for s in list(self.signals)[-50:]]
        })

    # ═══════════════════════════════════════════════════════════════════════
    # UNIFIED HUB HANDLERS
    # ═══════════════════════════════════════════════════════════════════════

    async def handle_api_unified_hubs(self, request):
        """REST API: Unified hub status summary."""
        # Read Orca snapshot for live stats
        state_dir = os.environ.get("AUREON_STATE_DIR", "state")
        snapshot_file = os.path.join(state_dir, "dashboard_snapshot.json")
        orca_stats = {}
        if os.path.exists(snapshot_file):
            try:
                with open(snapshot_file, "r") as f:
                    orca_stats = json.load(f)
            except Exception:
                pass

        session = orca_stats.get("session_stats", {})
        return web.json_response({
            "hubs": [
                {"id": "orca", "name": "Orca Kill Cycle", "status": "online" if orca_stats else "offline",
                 "trades": session.get("total_trades", 0), "pnl": session.get("total_pnl", 0.0)},
                {"id": "queen", "name": "Queen Hive Mind", "status": "online" if self.queen else "offline",
                 "confidence": 0.85},
                {"id": "registry", "name": "System Registry", "status": "online",
                 "systems": self.registry_snapshot.get("total", 0)}
            ],
            "timestamp": time.time()
        })

    async def handle_api_unified_registry(self, request):
        """REST API: System registry data."""
        return web.json_response(self.registry_snapshot)

    async def handle_hub_orca(self, request):
        """Serve Orca dashboard HTML."""
        if OrcaDashboardHtml:
            # Adjust paths for /hub/orca prefix
            html = OrcaDashboardHtml.replace('"/ws"', '"/hub/orca/ws"')
            html = html.replace('"/api/', '"/hub/orca/api/')
            return web.Response(text=html, content_type='text/html')
        return web.Response(text="<h1>Orca Dashboard not available</h1>", content_type='text/html')

    async def handle_hub_orca_ws(self, request):
        """WebSocket proxy for Orca dashboard."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Serve Orca state via WebSocket
        try:
            while not ws.closed:
                state_dir = os.environ.get("AUREON_STATE_DIR", "state")
                snapshot_file = os.path.join(state_dir, "dashboard_snapshot.json")
                if os.path.exists(snapshot_file):
                    try:
                        with open(snapshot_file, "r") as f:
                            data = json.load(f)
                        await ws.send_json(data)
                    except Exception:
                        pass
                await asyncio.sleep(1)
        except Exception:
            pass
        return ws

    async def handle_hub_orca_status(self, request):
        """Orca API: Status endpoint."""
        state_dir = os.environ.get("AUREON_STATE_DIR", "state")
        snapshot_file = os.path.join(state_dir, "dashboard_snapshot.json")
        if os.path.exists(snapshot_file):
            try:
                with open(snapshot_file, "r") as f:
                    return web.json_response(json.load(f))
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)
        return web.json_response({"status": "no_data"})

    async def handle_hub_orca_stealth(self, request):
        """Orca API: Toggle stealth mode (stub)."""
        return web.json_response({"stealth": True, "message": "Stealth mode toggled"})

    async def handle_hub_orca_predator(self, request):
        """Orca API: Predator stats (stub)."""
        return web.json_response({
            "predator_mode": True,
            "stalking": 0,
            "ambush_ready": 0,
            "kills_today": 0
        })

    async def handle_hub_queen(self, request):
        """Serve Queen Unified dashboard HTML."""
        if QueenUnifiedDashboardHtml:
            # Adjust paths for /hub/queen prefix
            html = QueenUnifiedDashboardHtml.replace('"/ws"', '"/hub/queen/ws"')
            return web.Response(text=html, content_type='text/html')
        return web.Response(text="<h1>Queen Dashboard not available</h1>", content_type='text/html')

    async def handle_hub_queen_ws(self, request):
        """WebSocket proxy for Queen dashboard."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        try:
            while not ws.closed:
                # Provide Queen state
                queen_state = {
                    "status": "online" if self.queen else "offline",
                    "confidence": 0.85,
                    "cosmic_score": 0.75,
                    "strategy": "LIVE TRADE",
                    "portfolio": asdict(self.portfolio),
                    "timestamp": time.time()
                }
                await ws.send_json(queen_state)
                await asyncio.sleep(1)
        except Exception:
            pass
        return ws

    async def handle_hub_registry(self, request):
        """Serve System Registry dashboard."""
        html = """<!DOCTYPE html>
<html><head><title>System Registry</title>
<style>
body { background: #0a0a1a; color: #fff; font-family: monospace; padding: 20px; }
h1 { color: #ffaa00; }
.system { background: rgba(0,255,136,0.1); padding: 10px; margin: 5px 0; border-radius: 5px; }
.online { border-left: 3px solid #00ff88; }
.offline { border-left: 3px solid #ff3366; opacity: 0.6; }
</style></head><body>
<h1>🔌 System Registry</h1>
<div id="systems"></div>
<script>
const systems = """ + json.dumps(SYSTEMS_STATUS) + """;
const container = document.getElementById('systems');
Object.entries(systems).forEach(([name, online]) => {
    const div = document.createElement('div');
    div.className = 'system ' + (online ? 'online' : 'offline');
    div.innerHTML = (online ? '✅' : '❌') + ' ' + name;
    container.appendChild(div);
});
</script></body></html>"""
        return web.Response(text=html, content_type='text/html')
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return
        
        msg_str = json.dumps(message)
        for client in list(self.clients):
            try:
                await client.send_str(msg_str)
            except:
                self.clients.discard(client)
        
        self.updates_sent += 1
    
    async def broadcast_portfolio(self):
        """Broadcast portfolio update."""
        await self.broadcast({
            "type": "portfolio_update",
            "portfolio": asdict(self.portfolio),
            "balances": self.portfolio.balances
        })
    
    async def broadcast_signal(self, signal: TradingSignal):
        """Broadcast a new signal."""
        self.signals.append(signal)
        await self.broadcast({
            "type": "signal",
            "signal": asdict(signal)
        })
    
    async def broadcast_queen_update(self, message: str, cosmic: float = 0.5, confidence: float = 0.5, strategy: str = "SCANNING"):
        """Broadcast Queen update."""
        await self.broadcast({
            "type": "queen_update",
            "message": message,
            "cosmic_score": cosmic,
            "confidence": confidence,
            "strategy": strategy
        })

    def _build_queen_voice_signal(self, snapshot: Dict[str, Any]) -> Optional[TradingSignal]:
        """Build a Queen Voice signal summarizing who/what/where/when/how."""
        positions = snapshot.get('positions', []) or []
        active_count = snapshot.get('active_count', len(positions))
        exchange_status = snapshot.get('exchange_status', {}) or {}
        connected_exchanges = [k for k, v in exchange_status.items() if isinstance(v, dict) and v.get('connected')]
        where = ", ".join(connected_exchanges) if connected_exchanges else "unknown"

        # Summarize top positions by absolute PnL
        top_positions = sorted(
            positions,
            key=lambda p: abs(float(p.get('current_pnl', 0.0) or 0.0)),
            reverse=True
        )[:3]
        position_lines = []
        for p in top_positions:
            symbol = p.get('symbol', 'UNKNOWN')
            exch = p.get('exchange', 'n/a')
            pnl = float(p.get('current_pnl', 0.0) or 0.0)
            position_lines.append(f"{symbol}@{exch} {pnl:+.4f}")

        movers = (self.market.top_movers or [])[:3]
        market_lines = []
        for m in movers:
            symbol = m.get('symbol', 'UNKNOWN')
            change = float(m.get('change', 0.0) or 0.0) * 100
            exchange = m.get('exchange', 'mkt')
            market_lines.append(f"{symbol} {change:+.2f}% ({exchange})")

        winners = snapshot.get('last_winners', []) or []
        decisions = snapshot.get('last_queen_decisions', []) or []
        picks = []
        for w in winners[:3]:
            picks.append(
                f"{w.get('symbol','?')}@{w.get('exchange','?')} score={float(w.get('score',0)):.2f}"
            )
        if not picks and decisions:
            for d in decisions[:3]:
                picks.append(
                    f"{d.get('symbol','?')} {d.get('action','HOLD')} {float(d.get('confidence',0)):.0%}"
                )

        queen_message = snapshot.get('queen_message') or "Scanning markets"
        session_stats = snapshot.get('session_stats', {}) or {}
        cycles = session_stats.get('cycles', 0)
        trades = session_stats.get('total_trades', 0)
        wins = session_stats.get('winning_trades', 0)
        pnl = session_stats.get('total_pnl', 0.0)

        # 🧠 COGNITIVE ENGINE CHECK - Deep Learning & Historical Memory
        # ------------------------------------------------------------
        neuron_weights_file = "queen_neuron_weights.json"
        elephant_memory_file = "queen_elephant_memory.json"
        
        learning_active = False
        memory_active = False
        cognitive_notes = []
        
        try:
            # Check for recent backpropagation (Deep Learning)
            if os.path.exists(neuron_weights_file):
                mtime = os.path.getmtime(neuron_weights_file)
                age = time.time() - mtime
                if age < 300:  # Updated in last 5 mins
                    learning_active = True
                    cognitive_notes.append(f"Neural Weights Updated {int(age)}s ago")
            
            # Check for historical memory access
            if os.path.exists(elephant_memory_file):
                mtime = os.path.getmtime(elephant_memory_file)
                age = time.time() - mtime
                if age < 300:
                    memory_active = True
                    cognitive_notes.append(f"Elephant Memory Recall {int(age)}s ago")
        except Exception:
            pass

        intent = "Evaluating entries" if active_count == 0 else "Managing positions + scouting"
        
        # Determine "Who" based on cognitive state
        who = "Queen Sero"
        if learning_active and memory_active:
            who = "Queen Sero (Full/Cognitive)"
        elif learning_active:
            who = "Queen Sero (Learning)"
        
        # Determine "How" based on active systems
        base_how = "Batten Matrix 3-pass + 4th execution gate"
        if cognitive_notes:
            how = f"{base_how} + {' + '.join(cognitive_notes)}"
        else:
            how = base_how

        # Richer reason string
        reason_parts = [queen_message]
        if learning_active:
            reason_parts.append("🧠 Backpropagation Active")
        if memory_active:
            reason_parts.append("📜 Historical Pattern Match")
        
        # 🗣️ NARRATIVE GENERATION - The "Human" Voice
        # ------------------------------------------------------------
        narrative_parts = []
        
        # 1. CURRENT STATE & INTENT
        context_time = datetime.utcnow().strftime("%H:%M")
        
        if active_count == 0:
            narrative_parts.append(f"It is {context_time} UTC. I am currently in <strong>Hunter Mode</strong>, scanning the {where} ecosystem for high-probability setups.")
        else:
            narrative_parts.append(f"It is {context_time} UTC. I am actively managing {active_count} positions across {where}.")
            narrative_parts.append(f"My primary focus is maximizing our floating PnL of {pnl:+.4f}.")
            
            # 🔍 POSITION DEEP DIVE (Refined)
            for p in top_positions[:2]:  # Focus on top 2 movers
                sym = p.get('symbol', 'UNKNOWN')
                curr_pnl = float(p.get('current_pnl', 0.0) or 0.0)
                curr_price = float(p.get('current_price', 0.0) or 0.0)
                entry_price = float(p.get('entry_price', 0.0) or 0.0)
                target_price = float(p.get('target_price', 0.0) or 0.0)
                
                # Calculate PnL % safely
                if entry_price > 0:
                    pnl_pct = ((curr_price - entry_price) / entry_price) * 100
                else:
                    pnl_pct = 0.0
                
                # Calculate Target distance
                if curr_price > 0 and target_price > 0:
                    dist_to_target = ((target_price - curr_price) / curr_price) * 100
                    target_str = f"aiming for {target_price:.4f} (+{dist_to_target:.1f}%)"
                else:
                    target_str = "calculating optimal exit"

                # Attempt to determine entry time
                try:
                    # Look for timestamp keys, fallback to recent
                    entry_ts = float(p.get('timestamp') or p.get('entry_time') or p.get('open_time') or (time.time() - 7200))
                    duration_hrs = (time.time() - entry_ts) / 3600
                    entry_dt = datetime.fromtimestamp(entry_ts)
                    # Format: "9am on Friday"
                    time_str = entry_dt.strftime("%I%p").lstrip('0').lower() + " on " + entry_dt.strftime("%A")
                    duration_str = f"({duration_hrs:.1f}h ago)"
                except:
                    time_str = "earlier this session"
                    duration_str = ""
                
                # Determine narrative arc based on PnL
                if curr_pnl > 0:
                    performance = f"has gained <strong>{pnl_pct:+.2f}%</strong> since entry"
                    projection = f"My probability systems are {target_str}."
                else:
                    performance = f"is currently <strong>{pnl_pct:+.2f}%</strong> down"
                    projection = f"Deep learning suggests holding for reversal; {target_str}."
                
                narrative_parts.append(f"Regarding <strong>{sym}</strong>: I opened this position at {time_str} {duration_str}. It {performance}. {projection}")

        # 2. DECISION PROCESS & PICKS
        if picks:
            # picks format: "SYMBOL@EXCH score=123" or "SYMBOL ACTION CONF%"
            top_pick = picks[0] 
            try:
                # Naive parsing
                pick_sym = top_pick.split()[0].split('@')[0]
                pick_score = top_pick.split('score=')[-1] if 'score=' in top_pick else "?"
                narrative_parts.append(f"I have identified {pick_sym} as a Rising Star candidate (Score: {pick_score}).")
            except:
                narrative_parts.append(f"I am tracking {top_pick} as a potential opportunity.")
        elif active_count > 0:
            narrative_parts.append("I am calculating probability drift on open positions to determine the optimal exit point.")
        
        # 3. HISTORICAL INTELLIGENCE & TRIBAL WISDOM
        # Contextual wisdom similar to "Mogollon Tribes"
        mogollon_proverbs = {
            "profit": [
                "Small quick gains compound. Move like the rabbit. 🐇",
                "The sun feeds the earth. It is harvest season. ☀️",
                "Look beneath the surface. Hidden value exists like the fish. 🐟"
            ],
            "loss": [
                "Sometimes retreat is wisdom. The bear hibernates through storms. 🐻",
                "Navigate heights carefully. Mountain paths are steep. 🐏",
                "Transform positions. The snake sheds what no longer serves. 🐍"
            ],
            "neutral": [
                "Patience wins. The turtle carries its home. 🐢",
                "Watch for signals from above. Patterns in flight. 🦅",
                "Build your foundation deep. Roots survive the wind. 🌵"
            ]
        }
        
        # Select proverb based on session state
        if pnl > 0.5 or wins > trades/2 or (active_count > 0 and pnl >= 0):
            wisdom = random.choice(mogollon_proverbs["profit"])
            wisdom_context = "The tribe gathers for harvest"
        elif pnl < -0.5:
            wisdom = random.choice(mogollon_proverbs["loss"])
            wisdom_context = "The tribe seeks shelter in the mountains"
        else:
            wisdom = random.choice(mogollon_proverbs["neutral"])
            wisdom_context = "The tribe waits for the rain"
            
        narrative_parts.append(f"<br><strong>🏺 Mogollon Wisdom</strong>: \"{wisdom}\"")
        
        # 4. LEARNING & COGNITION
        if learning_active:
            narrative_parts.append(f"My deep learning modules are synthesizing this ancient wisdom ({wisdom_context}) with live price action.")
        elif memory_active:
            narrative_parts.append("I am cross-referencing this pattern against my <strong>Elephant Memory</strong> database.")
        else:
            narrative_parts.append("Cognitive systems are stable.")
        
        # 4. TRADING PERFORMANCE & CLOSING
        win_rate = (wins / trades * 100) if trades > 0 else 0
        if trades > 0:
            narrative_parts.append(f"My session win rate is currently {win_rate:.1f}%.")
        
        narrative_parts.append(f"I will continue to execute the Batten Matrix protocol to secure profit.")

        narrative = " ".join(narrative_parts)

        voice_hash = f"{queen_message}|{active_count}|{trades}|{wins}|{pnl}|{picks}|{learning_active}|{memory_active}"
        if time.time() - self.last_voice_ts < 5 and voice_hash == self.last_voice_hash:
            return None

        self.last_voice_ts = time.time()
        self.last_voice_hash = voice_hash

        return TradingSignal(
            source="Queen Voice",
            signal_type="HOLD",
            symbol="NARRATIVE",
            confidence=1.0,
            score=0.0,
            reason=narrative,  # Replaces the short reason with full narrative
            timestamp=time.time(),
            exchange=where,
            metadata={
                "voice": True,
                "who": who,
                "what": intent,
                "where": where,
                "when": datetime.utcnow().strftime("%H:%M:%S") + " UTC",
                "how": how,
                "positions": position_lines,
                "market": market_lines,
                "picks": picks,
                "cognitive": {
                    "learning": learning_active,
                    "memory": memory_active,
                    "notes": cognitive_notes
                }
            }
        )

    def load_learning_snapshot(self) -> Dict[str, Any]:
        """Load adaptive learning data for UI display."""
        now = time.time()
        learning = {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_pnl": 0.0,
            "pnl_series": [],
            "patterns": []
        }

        history_path = Path("adaptive_learning_history.json")
        if history_path.exists():
            try:
                with history_path.open("r") as f:
                    history = json.load(f)
                trades = history.get("trades", [])
                learning["total_trades"] = len(trades)
                if trades:
                    pnl_values = [float(t.get("pnl", 0) or 0) for t in trades[-40:]]
                    learning["pnl_series"] = pnl_values
                    wins = sum(1 for v in pnl_values if v >= 0)
                    losses = sum(1 for v in pnl_values if v < 0)
                    total = wins + losses
                    learning["wins"] = wins
                    learning["losses"] = losses
                    learning["win_rate"] = (wins / total * 100) if total else 0.0
                    learning["avg_pnl"] = sum(pnl_values) / max(len(pnl_values), 1)
            except Exception as e:
                logger.debug(f"Learning history load error: {e}")

        patterns_path = Path("adaptive_learned_patterns.json")
        if patterns_path.exists():
            try:
                with patterns_path.open("r") as f:
                    patterns = json.load(f)
                pattern_rows = []
                for key, val in patterns.items():
                    if key == "default" or not isinstance(val, dict):
                        continue
                    # Calculate wins/losses from entry arrays if summary keys are missing/zero
                    wins = int(val.get("total_wins", 0) or 0)
                    losses = int(val.get("total_losses", 0) or 0)
                    if wins == 0 and "winning_rsi_entries" in val:
                        wins = len(val.get("winning_rsi_entries", []))
                    if losses == 0 and "losing_rsi_entries" in val:
                        losses = len(val.get("losing_rsi_entries", []))
                    pattern_rows.append({
                        "symbol": key,
                        "total_wins": wins,
                        "total_losses": losses,
                        "total_pnl": float(val.get("total_pnl", 0) or 0),
                        "verified_winner": bool(val.get("verified_winner", False)),
                        "best_rsi_buy": float(val.get("best_rsi_buy", 30) or 30),
                        "best_rsi_sell": float(val.get("best_rsi_sell", 70) or 70)
                    })
                pattern_rows.sort(key=lambda p: (p.get("total_pnl", 0), p.get("total_wins", 0)), reverse=True)
                learning["patterns"] = pattern_rows[:10]
            except Exception as e:
                logger.debug(f"Learning patterns load error: {e}")

        # Load Queen neuron weights for neural visualization
        neuron_path = Path("queen_neuron_weights.json")
        if neuron_path.exists():
            try:
                with neuron_path.open("r") as f:
                    neuron_data = json.load(f)
                learning["queen_neuron"] = {
                    "version": neuron_data.get("version", 1),
                    "input_size": neuron_data.get("input_size", 7),
                    "hidden_size": neuron_data.get("hidden_size", 12),
                    "learning_rate": neuron_data.get("base_learning_rate", 0.01),
                    "weights_input_hidden": neuron_data.get("weights_input_hidden", []),
                    "weights_hidden_output": neuron_data.get("weights_hidden_output", []),
                    "bias_hidden": neuron_data.get("bias_hidden", []),
                    "bias_output": neuron_data.get("bias_output", []),
                    "timestamp": neuron_data.get("timestamp", "")
                }
            except Exception as e:
                logger.debug(f"Queen neuron weights load error: {e}")

        learning["last_update"] = now
        self.learning_snapshot = learning
        return learning

    def load_bot_intel_snapshot(self) -> Dict[str, Any]:
        """Load bot intelligence data for UI display."""
        now = time.time()
        snapshot = {
            "bot_count": 0,
            "total_bots": 0,
            "active_bots": 0,
            "bot_firms": [],
            "bot_signatures": [],
            "bot_activity": [],
            "bot_map": [],
            "last_update": now
        }

        report_path = Path(os.environ.get("AUREON_BOT_INTEL_REPORT", "bot_intelligence_report.json"))
        firms_db_path = Path("all_firms_complete.json")
        if report_path.exists():
            try:
                # Get file modification time
                mtime = report_path.stat().st_mtime
                snapshot["last_update"] = mtime
                
                with report_path.open("r") as f:
                    report = json.load(f)
                
                # Prefer internal timestamp if available
                if "timestamp" in report:
                    snapshot["last_update"] = report["timestamp"]

                firms = report.get("firms", []) or []
                all_bots = report.get("all_bots", {}) or {}

                snapshot["bot_count"] = report.get("firms_detected", len(firms))
                snapshot["total_bots"] = report.get("total_bots_profiled", len(all_bots))

                # Active bots within last hour
                active_cutoff = now - 3600
                active_bots = [b for b in all_bots.values() if b.get("last_seen", 0) >= active_cutoff]
                snapshot["active_bots"] = len(active_bots)

                firm_rows = []
                for firm in firms:
                    total_bots = int(firm.get("total_bots", 0) or 0)
                    status = "Active" if total_bots > 0 else "Monitoring"
                    firm_rows.append({
                        "name": firm.get("firm_name") or firm.get("name") or firm.get("firm_id") or "Unknown",
                        "status": status,
                        "total_bots": total_bots,
                        "country": firm.get("country", ""),
                        "strategies": firm.get("strategies", []),
                        "total_volume_usd": firm.get("total_volume_usd", 0)
                    })
                firm_rows.sort(key=lambda f: f.get("total_bots", 0), reverse=True)
                snapshot["bot_firms"] = firm_rows

                # Signature counts from bot patterns
                signature_counts: Dict[str, int] = {}
                for bot in all_bots.values():
                    pattern = (bot.get("pattern") or "unknown").upper()
                    signature_counts[pattern] = signature_counts.get(pattern, 0) + 1
                snapshot["bot_signatures"] = [
                    {"name": name, "count": count}
                    for name, count in sorted(signature_counts.items(), key=lambda x: x[1], reverse=True)
                ]

                # Activity feed
                def _side_for_bot(bot_id: str, strategies: List[str]) -> str:
                    if any("arbitrage" in s for s in strategies):
                        return "sell"
                    if any("market_making" in s for s in strategies):
                        return "buy"
                    try:
                        return "buy" if int(bot_id[-1], 16) % 2 == 0 else "sell"
                    except Exception:
                        return "buy"

                activity = []
                sorted_bots = sorted(
                    all_bots.values(),
                    key=lambda b: b.get("last_seen", b.get("first_seen", 0)),
                    reverse=True
                )
                for bot in sorted_bots[:12]:
                    strategies = bot.get("strategies", []) or []
                    side = _side_for_bot(bot.get("bot_id", "0"), strategies)
                    role = bot.get("role", "")
                    size_class = bot.get("size_class", "")
                    desc_parts = [p for p in [role, size_class] if p]
                    desc = " · ".join(desc_parts) or "Algorithmic activity detected"
                    activity.append({
                        "pattern": (bot.get("pattern") or "HFT").upper(),
                        "symbol": bot.get("symbol", "--"),
                        "firm": bot.get("owner_name") or bot.get("likely_owner") or "Unknown",
                        "description": desc,
                        "side": side
                    })
                snapshot["bot_activity"] = activity

                # Build bot map nodes from detected firms
                city_coords = {
                    "Chicago": (20, 30),
                    "New York": (25, 28),
                    "London": (48, 26),
                    "Amsterdam": (47, 24),
                    "Paris": (49, 28),
                    "Zug": (50, 26),
                    "Toronto": (22, 27),
                    "San Francisco": (12, 30),
                    "Los Angeles": (12, 36),
                    "Singapore": (76, 42),
                    "Hong Kong": (78, 36),
                    "Tokyo": (82, 30),
                    "Sydney": (86, 66),
                    "Dubai": (62, 42)
                }

                firms_db: Dict[str, Any] = {}
                if firms_db_path.exists():
                    try:
                        with firms_db_path.open("r") as f:
                            firms_db = json.load(f).get("firms", {})
                    except Exception as e:
                        logger.debug(f"Firm database load error: {e}")

                max_bots = max([f.get("total_bots", 0) for f in firm_rows], default=1) or 1
                map_nodes = []
                for firm in firm_rows:
                    firm_id = firm.get("firm_id") or ""
                    firm_name = firm.get("name") or firm.get("firm_name") or firm_id
                    total_bots = firm.get("total_bots", 0)
                    intensity = min(1.0, max(0.25, total_bots / max_bots))

                    offices = []
                    firm_details = firms_db.get(firm_id, {}) if firm_id else {}
                    if firm_details.get("offices"):
                        offices = [o.get("city") for o in firm_details.get("offices", []) if o.get("city")]
                    if not offices:
                        hq = firm.get("hq_location") or firm_details.get("hq_location") or ""
                        if hq:
                            offices = [hq.split(",")[0].strip()]

                    for city in offices:
                        if city not in city_coords:
                            continue
                        x, y = city_coords[city]
                        map_nodes.append({
                            "city": city,
                            "x": x,
                            "y": y,
                            "intensity": intensity,
                            "firm": firm_name,
                            "active": total_bots > 0
                        })

                snapshot["bot_map"] = map_nodes
            except Exception as e:
                logger.debug(f"Bot intelligence report load error: {e}")

        self.bot_snapshot = snapshot
        return snapshot
    
    async def fetch_all_balances(self):
        """Fetch balances from all exchanges and calculate total USD value."""
        total_usd = 0.0
        total_cash = 0.0
        all_balances = {}
        exchange_breakdown = {}
        
        # Stable/cash assets that count as "cash available"
        cash_assets = {'USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD', 'GBP', 'ZGBP', 'EUR', 'ZEUR'}
        
        # Price lookup helper - use cached prices or fetch
        def get_usd_value(asset: str, amount: float, exchange: str) -> float:
            """Convert asset amount to USD value."""
            if amount <= 0:
                return 0.0
            
            # Direct USD values
            usd_assets = ['USD', 'ZUSD', 'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD']
            if asset.upper() in usd_assets:
                return amount
            
            # GBP conversion (approximate)
            if asset.upper() in ['GBP', 'ZGBP']:
                return amount * 1.27  # GBP to USD rate
            
            # EUR conversion
            if asset.upper() in ['EUR', 'ZEUR']:
                return amount * 1.08  # EUR to USD rate
            
            # Try to get price from cached prices
            price_key = f"{exchange}:{asset}/USD"
            if price_key in self.prices:
                return amount * self.prices[price_key]
            
            # Try Kraken ticker for crypto
            if self.kraken and asset.upper() in ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'AVAX', 'LINK', 'ATOM', 'TRX', 'SEI']:
                try:
                    ticker = self.kraken.get_ticker(f"{asset}/USD")
                    if ticker and ticker.get('price', 0) > 0:
                        price = float(ticker['price'])
                        self.prices[price_key] = price  # Cache it
                        return amount * price
                except:
                    pass
            
            # Fallback: estimate based on known prices
            crypto_estimates = {
                'BTC': 100000, 'ETH': 3500, 'SOL': 200, 'XRP': 2.5, 
                'ADA': 1.0, 'DOT': 8, 'AVAX': 40, 'LINK': 15,
                'ATOM': 10, 'TRX': 0.25, 'SEI': 0.5, 'DOGE': 0.35
            }
            if asset.upper() in crypto_estimates:
                return amount * crypto_estimates[asset.upper()]
            
            return 0.0  # Unknown asset
        
        # Kraken
        if self.kraken:
            try:
                balances = self.kraken.get_account_balance() or {}
                all_balances['kraken'] = {k: float(v) for k, v in balances.items() if float(v) > 0.0001}
                kraken_total = 0.0
                kraken_cash = 0.0
                for asset, amount in all_balances['kraken'].items():
                    usd_val = get_usd_value(asset, amount, 'kraken')
                    kraken_total += usd_val
                    total_usd += usd_val
                    if asset.upper() in cash_assets:
                        kraken_cash += usd_val
                        total_cash += usd_val
                exchange_breakdown['kraken'] = {
                    'total_usd': round(kraken_total, 4),
                    'cash_usd': round(kraken_cash, 4),
                    'assets': dict(all_balances.get('kraken', {}))
                }
            except Exception as e:
                logger.error(f"Kraken balance error: {e}")
        
        # Binance
        if self.binance:
            try:
                balances = None
                if hasattr(self.binance, 'get_balances'):
                    balances = self.binance.get_balances()
                elif hasattr(self.binance, 'get_balance'):
                    balances = self.binance.get_balance()
                if balances:
                    all_balances['binance'] = {k: float(v) for k, v in balances.items() if float(v) > 0.0001}
                    binance_total = 0.0
                    binance_cash = 0.0
                    for asset, amount in all_balances['binance'].items():
                        usd_val = get_usd_value(asset, amount, 'binance')
                        binance_total += usd_val
                        total_usd += usd_val
                        if asset.upper() in cash_assets:
                            binance_cash += usd_val
                            total_cash += usd_val
                    exchange_breakdown['binance'] = {
                        'total_usd': round(binance_total, 4),
                        'cash_usd': round(binance_cash, 4),
                        'assets': dict(all_balances.get('binance', {}))
                    }
            except Exception as e:
                logger.error(f"Binance balance error: {e}")
        
        # Alpaca
        if self.alpaca:
            try:
                if hasattr(self.alpaca, 'get_account'):
                    account = self.alpaca.get_account()
                    if account:
                        cash = float(getattr(account, 'cash', 0) or 0)
                        equity = float(getattr(account, 'equity', cash) or cash)
                        all_balances['alpaca'] = {'USD': cash}
                        alpaca_total = cash
                        alpaca_cash = cash
                        total_cash += cash
                        # Also get crypto positions
                        try:
                            positions = self.alpaca.get_positions() if hasattr(self.alpaca, 'get_positions') else []
                            for pos in (positions or []):
                                symbol = pos.get('symbol', '')
                                qty = float(pos.get('qty', 0))
                                market_val = float(pos.get('market_value', 0))
                                if qty > 0 and market_val > 0:
                                    all_balances['alpaca'][symbol] = qty
                                    alpaca_total += market_val
                        except:
                            pass
                        total_usd += alpaca_total
                        exchange_breakdown['alpaca'] = {
                            'total_usd': round(alpaca_total, 4),
                            'cash_usd': round(alpaca_cash, 4),
                            'equity': round(equity, 4),
                            'assets': dict(all_balances.get('alpaca', {}))
                        }
            except Exception as e:
                logger.error(f"Alpaca balance error: {e}")
        
        # Capital.com - check if we have a client
        # (Capital uses different balance structure - check if available)
        
        # Load baseline for P&L calculation
        baseline_value = 0.0
        baseline_path = Path("pnl_baseline.json")
        if baseline_path.exists():
            try:
                with baseline_path.open("r") as f:
                    baseline_data = json.load(f)
                    baseline_value = float(baseline_data.get("total_value_usdc", 0) or 0)
            except Exception as e:
                logger.debug(f"P&L baseline load error: {e}")
        
        # Calculate P&L
        pnl_total = total_usd - baseline_value if baseline_value > 0 else 0.0
        
        # Load today's starting value for daily P&L
        today_start_path = Path("pnl_today_start.json")
        today_start_value = total_usd  # Default to current if no file
        today_date = time.strftime("%Y-%m-%d")
        if today_start_path.exists():
            try:
                with today_start_path.open("r") as f:
                    today_data = json.load(f)
                    if today_data.get("date") == today_date:
                        today_start_value = float(today_data.get("value", total_usd))
                    else:
                        # New day, save new starting value
                        with today_start_path.open("w") as fw:
                            json.dump({"date": today_date, "value": total_usd}, fw)
            except Exception:
                pass
        else:
            # Create today's start file
            try:
                with today_start_path.open("w") as f:
                    json.dump({"date": today_date, "value": total_usd}, f)
            except Exception:
                pass
        
        pnl_today = total_usd - today_start_value
        
        self.portfolio.balances = all_balances
        self.portfolio.total_value_usd = round(total_usd, 4)
        self.portfolio.cash_available = round(total_cash, 4)
        self.portfolio.pnl_today = round(pnl_today, 4)
        self.portfolio.pnl_total = round(pnl_total, 4)
        self.portfolio.exchange_breakdown = exchange_breakdown
        self.portfolio.baseline_value = round(baseline_value, 4)

        # Basic market overview from balances
        unique_assets = set()
        for _, balances in all_balances.items():
            unique_assets.update(balances.keys())
        self.market.total_assets_tracked = len(unique_assets)
        self.market.rising_count = 0

    async def fetch_market_prices(self):
        """Fetch live market prices from exchanges."""
        kraken_prices = {}
        binance_prices = {}
        alpaca_prices = {}
        top_movers = []
        
        # Common trading pairs to track
        kraken_symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "ADA/USD", "DOT/USD", "AVAX/USD", "LINK/USD"]
        binance_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT"]
        alpaca_symbols = ["BTC/USD", "ETH/USD", "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN"]
        
        # Fetch from Kraken
        if self.kraken:
            for symbol in kraken_symbols:
                try:
                    ticker = self.kraken.get_ticker(symbol)
                    if ticker and ticker.get("price", 0) > 0:
                        price = float(ticker.get("price", 0))
                        
                        # Calculate change from stored price
                        old_price = self.prices.get(f"kraken:{symbol}", price)
                        change = 0.0
                        if old_price > 0:
                            change = (price - old_price) / old_price
                            top_movers.append({
                                "symbol": symbol,
                                "price": price,
                                "change": change,
                                "exchange": "kraken"
                            })
                        self.prices[f"kraken:{symbol}"] = price
                        kraken_prices[symbol] = {"price": price, "change": change}
                except Exception as e:
                    logger.debug(f"Kraken ticker error for {symbol}: {e}")
        
        # Fetch from Binance (if available)
        if self.binance and hasattr(self.binance, 'get_ticker'):
            for symbol in binance_symbols[:4]:  # Limit to avoid rate limits
                try:
                    ticker = self.binance.get_ticker(symbol)
                    if ticker:
                        price = float(ticker.get("lastPrice", ticker.get("price", 0)))
                        if price > 0:
                            # Calculate change from stored price
                            old_price = self.prices.get(f"binance:{symbol}", price)
                            change = 0.0
                            if old_price > 0:
                                change = (price - old_price) / old_price
                                top_movers.append({
                                    "symbol": symbol,
                                    "price": price,
                                    "change": change,
                                    "exchange": "binance"
                                })
                            self.prices[f"binance:{symbol}"] = price
                            binance_prices[symbol] = {"price": price, "change": change}
                except Exception as e:
                    logger.debug(f"Binance ticker error for {symbol}: {e}")
        
        # Fetch from Alpaca
        if self.alpaca:
            for symbol in alpaca_symbols:
                try:
                    ticker = self.alpaca.get_ticker(symbol)
                    if ticker and "price" in ticker:
                        price = float(ticker["price"])
                        
                        old_price = self.prices.get(f"alpaca:{symbol}", price)
                        change = 0.0
                        if old_price > 0:
                            change = (price - old_price) / old_price
                            top_movers.append({
                                "symbol": symbol,
                                "price": price,
                                "change": change,
                                "exchange": "alpaca"
                            })
                        self.prices[f"alpaca:{symbol}"] = price
                        alpaca_prices[symbol] = {"price": price, "change": change}
                except Exception as e:
                    logger.debug(f"Alpaca ticker error for {symbol}: {e}")
        
        # Sort movers by absolute change
        top_movers.sort(key=lambda x: abs(x.get("change", 0)), reverse=True)
        
        # Update market overview
        rising = sum(1 for m in top_movers if m.get("change", 0) > 0)
        falling = sum(1 for m in top_movers if m.get("change", 0) < 0)
        
        self.market.total_assets_tracked = len(top_movers)
        self.market.rising_count = rising
        self.market.falling_count = falling
        self.market.top_movers = top_movers[:10]
        
        return {
            "kraken_prices": kraken_prices,
            "binance_prices": binance_prices,
            "alpaca_prices": alpaca_prices,
            "top_movers": top_movers
        }
        self.market.falling_count = 0
        self.market.top_movers = []
    
    async def load_recent_trades(self):
        """Load recent trades from trade log files or Orca snapshot."""
        trades = []
        
        # 1. Try to read from Orca snapshot first (recent executions)
        state_dir = os.environ.get("AUREON_STATE_DIR", "state")
        snapshot_file = os.path.join(state_dir, "dashboard_snapshot.json")
        if os.path.exists(snapshot_file):
            try:
                with open(snapshot_file, "r") as f:
                    data = json.load(f)
                
                # Check for closed positions (completed trades)
                closed = data.get("closed_positions", [])
                for pos in closed[-20:]:  # Last 20
                    trades.append(TradeExecution(
                        timestamp=pos.get("close_time", time.time()),
                        exchange=pos.get("exchange", ""),
                        symbol=pos.get("symbol", ""),
                        side="SELL",  # Closed = sold
                        quantity=pos.get("qty", 0),
                        price=pos.get("close_price", 0),
                        value_usd=pos.get("close_value", 0),
                        pnl=pos.get("pnl", 0),
                        status="EXECUTED"
                    ))
                
                # Check for recent opens
                positions = data.get("positions", [])
                for pos in positions:
                    if pos.get("entry_time", 0) > time.time() - 86400:  # Last 24h
                        trades.append(TradeExecution(
                            timestamp=pos.get("entry_time", time.time()),
                            exchange=pos.get("exchange", ""),
                            symbol=pos.get("symbol", ""),
                            side="BUY",
                            quantity=pos.get("qty", 0),
                            price=pos.get("entry_price", 0),
                            value_usd=pos.get("entry_value", 0),
                            status="EXECUTED"
                        ))
            except Exception as e:
                logger.debug(f"Error loading trades from snapshot: {e}")
        
        # 2. Try trade log directory
        trade_log_dir = os.environ.get("AUREON_TRADE_LOG_DIR", "/tmp/aureon_trade_logs")
        if os.path.exists(trade_log_dir):
            try:
                log_files = sorted(
                    [f for f in os.listdir(trade_log_dir) if f.endswith('.jsonl')],
                    reverse=True
                )[:3]  # Last 3 log files
                
                for log_file in log_files:
                    log_path = os.path.join(trade_log_dir, log_file)
                    try:
                        with open(log_path, 'r') as f:
                            lines = f.readlines()[-30:]  # Last 30 lines
                            for line in reversed(lines):
                                try:
                                    entry = json.loads(line.strip())
                                    if entry.get("type") in ["trade", "execution", "order"]:
                                        trades.append(TradeExecution(
                                            timestamp=entry.get("timestamp", time.time()),
                                            exchange=entry.get("exchange", ""),
                                            symbol=entry.get("symbol", entry.get("pair", "")),
                                            side=entry.get("side", "BUY").upper(),
                                            quantity=float(entry.get("qty", entry.get("quantity", 0))),
                                            price=float(entry.get("price", 0)),
                                            value_usd=float(entry.get("value", entry.get("cost", 0))),
                                            pnl=float(entry.get("pnl", 0)),
                                            status=entry.get("status", "EXECUTED").upper(),
                                            order_id=entry.get("order_id", "")
                                        ))
                                except (json.JSONDecodeError, ValueError):
                                    continue
                    except Exception:
                        continue
            except Exception as e:
                logger.debug(f"Error loading trade logs: {e}")
        
        # Sort by timestamp descending
        trades.sort(key=lambda t: t.timestamp, reverse=True)
        
        # Keep last 50
        self.recent_trades = deque(trades[:50], maxlen=50)
        return list(self.recent_trades)
    
    async def update_loop(self):
        """Main update loop."""
        price_fetch_counter = 0
        
        while self.running:
            try:
                # 1. Read live dashboard snapshot from Orca
                state_dir = os.environ.get("AUREON_STATE_DIR", "state")
                snapshot_file = os.path.join(state_dir, "dashboard_snapshot.json")
                if os.path.exists(snapshot_file):
                    try:
                        with open(snapshot_file, "r") as f:
                             data = json.load(f)
                        
                        # Load recent trades
                        await self.load_recent_trades()
                        data['recent_trades'] = [asdict(t) for t in list(self.recent_trades)[:15]]
                        
                        # Broadcast live update
                        await self.broadcast({
                            "type": "live_update",
                            "data": data
                        })
                        
                        # Sync positions
                        if 'positions' in data:
                            self.portfolio.positions = data['positions']
                        
                        # Sync queen message if present
                        if 'queen_message' in data:
                             await self.broadcast_queen_update(
                                data['queen_message'],
                                cosmic=0.7,
                                confidence=0.8,
                                strategy="WAR ROOM"
                            )

                        voice_signal = self._build_queen_voice_signal(data)
                        if voice_signal:
                            await self.broadcast_signal(voice_signal)

                        # Surface Orca session stats in Queen updates for live verification
                        if 'session_stats' in data:
                            stats = data['session_stats'] or {}
                            cycles = stats.get('cycles', 0)
                            trades = stats.get('total_trades', 0)
                            wins = stats.get('winning_trades', 0)
                            pnl = stats.get('total_pnl', 0.0)
                            active = data.get('active_count', 0)
                            msg = (
                                f"Live | Cycles: {cycles} | Trades: {trades} | Wins: {wins} "
                                f"| Open: {active} | PnL: {pnl:.4f}"
                            )
                            await self.broadcast_queen_update(
                                msg,
                                cosmic=0.75,
                                confidence=0.85,
                                strategy="LIVE TRADE"
                            )

                    except Exception:
                        pass

                # 2. Fetch market prices every 5 seconds
                price_fetch_counter += 1
                if price_fetch_counter >= 5:
                    price_fetch_counter = 0
                    try:
                        market_data = await self.fetch_market_prices()
                        
                        # Broadcast market update with live prices
                        await self.broadcast({
                            "type": "market_update",
                            "market": asdict(self.market),
                            "kraken_prices": market_data.get("kraken_prices", {}),
                            "binance_prices": market_data.get("binance_prices", {}),
                            "alpaca_prices": market_data.get("alpaca_prices", {})
                        })
                        
                        # Generate signals from price movements
                        for mover in market_data.get("top_movers", [])[:3]:
                            if abs(mover.get("change", 0)) > 0.01:  # 1% threshold
                                signal_type = "BUY" if mover["change"] > 0 else "SELL"
                                signal = TradingSignal(
                                    source="Market Scanner",
                                    signal_type=signal_type,
                                    symbol=mover["symbol"],
                                    confidence=min(abs(mover["change"]) * 10, 0.95),
                                    score=abs(mover["change"]) * 100,
                                    reason=f"{mover['change']*100:.2f}% move on {mover['exchange']}",
                                    timestamp=time.time(),
                                    exchange=mover["exchange"]
                                )
                                await self.broadcast_signal(signal)
                    except Exception as e:
                        logger.debug(f"Market price fetch error: {e}")

                # 3. Fetch balances every 30 seconds
                if time.time() - self.last_update > 30:
                    await self.fetch_all_balances()
                    await self.broadcast_portfolio()
                    
                    # Update Queen with system status
                    online_systems = sum(1 for v in SYSTEMS_STATUS.values() if v)
                    total_systems = len(SYSTEMS_STATUS)
                    await self.broadcast_queen_update(
                        f"Systems: {online_systems}/{total_systems} | Portfolio: ${self.portfolio.total_value_usd:.4f} | Scanning markets...",
                        cosmic=0.618,  # Golden ratio
                        confidence=online_systems / max(total_systems, 1),
                        strategy="SCANNING"
                    )
                    
                    self.last_update = time.time()

                # 4. Learning updates every 15 seconds
                if time.time() - self.learning_last_update > 15:
                    learning_snapshot = self.load_learning_snapshot()
                    await self.broadcast({
                        "type": "learning_update",
                        "learning": learning_snapshot
                    })
                    self.learning_last_update = time.time()

                # 5. Bot intelligence updates every 20 seconds
                if time.time() - self.bot_last_update > 20:
                    bot_snapshot = self.load_bot_intel_snapshot()
                    await self.broadcast({
                        "type": "bot_update",
                        "bot_intel": bot_snapshot
                    })
                    self.bot_last_update = time.time()
                
                await asyncio.sleep(1) 
                
            except Exception as e:
                logger.error(f"Update loop error: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the command center."""
        self.running = True
        
        # START WEB SERVER FIRST - so health checks pass immediately!
        if AIOHTTP_AVAILABLE:
            try:
                runner = web.AppRunner(self.app)
                await runner.setup()
                site = web.TCPSite(runner, '0.0.0.0', self.port)
                await site.start()

                print(f"\n{'=' * 70}")
                print(f"👑🌌 AUREON COMMAND CENTER STARTING...")
                print(f"{'=' * 70}")
                print(f"🌐 Dashboard: http://localhost:{self.port}")
                print(f"📡 WebSocket: ws://localhost:{self.port}/ws")
                print(f"✅ Health endpoint ready at /health")
                print(f"{'=' * 70}\n")
            except Exception as e:
                logger.exception("AIOHTTP server failed to start, falling back to basic HTTP", exc_info=e)
                self._start_basic_http_server()
        else:
            self._start_basic_http_server()
        
        # THEN initialize heavy systems (in background, so health checks don't fail)
        print("🔧 Initializing trading systems in background...")
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, self.initialize_systems)
        
        print(f"\n{'=' * 70}")
        print(f"👑🌌 AUREON COMMAND CENTER FULLY ONLINE")
        print(f"{'=' * 70}")
        print(f"🔌 REST API:")
        print(f"   GET /api/status   - System status")
        print(f"   GET /api/portfolio - Portfolio data")
        print(f"   GET /api/signals  - Recent signals")
        print(f"{'=' * 70}\n")
        
        # Start update loop
        asyncio.create_task(self.update_loop())
        
        # Keep running
        await asyncio.Event().wait()

    def _start_basic_http_server(self):
        """Fallback HTTP server when aiohttp isn't available."""
        center = self

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/health":
                    body = json.dumps({
                        "status": "healthy",
                        "service": "aureon-command-center",
                        "timestamp": time.time()
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return

                if self.path == "/":
                    body = "Aureon Command Center".encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return

                self.send_response(404)
                self.end_headers()

            def log_message(self, format, *args):
                logger.info("Basic HTTP server: " + format, *args)

        server = HTTPServer(("0.0.0.0", center.port), HealthHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        print(f"\n{'=' * 70}")
        print(f"👑🌌 AUREON COMMAND CENTER STARTING (BASIC HTTP FALLBACK)...")
        print(f"{'=' * 70}")
        print(f"🌐 Health endpoint ready at http://localhost:{center.port}/health")
        print(f"{'=' * 70}\n")


async def main():
    """Main entry point."""
    port = int(os.environ.get("PORT", os.environ.get("AUREON_UI_PORT", "8800")))
    center = AureonCommandCenter(port=port)
    await center.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👑 Command Center stopped")
    except Exception as e:
        logger.exception("Command Center crashed", exc_info=e)
        raise
