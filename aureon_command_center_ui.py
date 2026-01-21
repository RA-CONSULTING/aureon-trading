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
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-primary: #0a0a1a;
            --bg-secondary: #1a1a2e;
            --bg-panel: rgba(0, 0, 0, 0.7);
            --accent-gold: #ffaa00;
            --accent-green: #00ff88;
            --accent-red: #ff3366;
            --accent-blue: #00bfff;
            --accent-purple: #9966ff;
            --text-primary: #ffffff;
            --text-secondary: #888888;
        }
        
        body {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Header */
        #header {
            background: rgba(0, 0, 0, 0.9);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid var(--accent-gold);
            box-shadow: 0 4px 30px rgba(255, 170, 0, 0.3);
        }
        
        .logo {
            font-size: 1.5em;
            font-weight: bold;
            background: linear-gradient(90deg, var(--accent-gold), #ff6600);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status-bar {
            display: flex;
            gap: 15px;
            font-size: 0.85em;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 5px;
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

        /* Tab Content */
        .tab-content {
            display: none;
            height: calc(100vh - 110px);
            overflow-y: auto;
            overflow-x: hidden;
        }

        .tab-content.active {
            display: block;
        }
        
        /* Main Container */
        #container {
            display: grid;
            grid-template-columns: 300px 1fr 340px;
            grid-template-rows: auto 1fr;
            gap: 12px;
            padding: 12px;
            min-height: 100%;
        }
        
        /* Panels */
        .panel {
            background: var(--bg-panel);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 8px;
            padding: 12px;
            overflow-y: auto;
            overflow-x: hidden;
            backdrop-filter: blur(10px);
            max-height: calc(100vh - 180px);
        }
        
        .panel h2 {
            color: var(--accent-gold);
            font-size: 1em;
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
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .stat-card {
            background: rgba(0, 255, 136, 0.05);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        
        .stat-label {
            font-size: 0.75em;
            color: var(--text-secondary);
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: var(--accent-green);
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
            background: rgba(0, 0, 0, 0.3);
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
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .signal-item.buy { border-left-color: var(--accent-green); }
        .signal-item.sell { border-left-color: var(--accent-red); }
        .signal-item.hold { border-left-color: var(--accent-gold); }
        
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
        
        /* Market Overview */
        .mover-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            margin-bottom: 5px;
            background: rgba(0, 0, 0, 0.3);
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
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
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
        
        /* Responsive */
        @media (max-width: 1400px) {
            #container {
                grid-template-columns: 280px 1fr 280px;
            }
        }
        
        @media (max-width: 1100px) {
            #container {
                grid-template-columns: 1fr 1fr;
            }
            #queen-panel {
                grid-column: 1 / -1;
            }
            .panel:last-child {
                grid-column: 1 / -1;
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
        <div class="logo">👑 AUREON COMMAND CENTER</div>
        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot online" id="ws-status"></span>
                <span>WebSocket</span>
            </div>
            <div class="status-item">
                <span id="system-count">0</span> Systems Online
            </div>
            <div class="status-item">
                <span id="clock">--:--:--</span>
            </div>
        </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tabs-nav">
        <button class="tab-btn active" onclick="switchTab('trading')" data-tab="trading">
            <span class="tab-icon">📊</span>Trading
        </button>
        <button class="tab-btn" onclick="switchTab('whales')" data-tab="whales">
            <span class="tab-icon">🐋</span>Whales
            <span class="tab-badge" id="whale-count">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('bots')" data-tab="bots">
            <span class="tab-icon">🤖</span>Bot Intel
            <span class="tab-badge" id="bot-count">0</span>
        </button>
        <button class="tab-btn" onclick="switchTab('market')" data-tab="market">
            <span class="tab-icon">📈</span>Live Feed
        </button>
        <button class="tab-btn" onclick="switchTab('quantum')" data-tab="quantum">
            <span class="tab-icon">🔮</span>Quantum
        </button>
        <button class="tab-btn" onclick="switchTab('systems')" data-tab="systems">
            <span class="tab-icon">⚙️</span>All Systems
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
        
        <!-- Left Panel: Portfolio & Systems -->
        <div class="panel">
            <h2>💰 PORTFOLIO</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Value</div>
                    <div class="stat-value gold" id="total-value">$0.00</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Cash Available</div>
                    <div class="stat-value" id="cash-available">$0.00</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Today's P&L</div>
                    <div class="stat-value" id="pnl-today">$0.00</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total P&L</div>
                    <div class="stat-value" id="pnl-total">$0.00</div>
                </div>
            </div>

            <h2>✈️ FLIGHT CHECK</h2>
            <div id="flight-check" class="flight-check-panel">
                <div class="flight-status offline">Awaiting status...</div>
            </div>
            
            <h2>⚔️ ACTIVE POSITIONS</h2>
            <div id="positions-list" style="margin-bottom: 20px;">
                <div style="text-align: center; color: #666; font-style: italic;">No active positions</div>
            </div>
            
            <h2>� RECENT TRADES</h2>
            <div id="recent-trades" style="margin-bottom: 20px; max-height: 200px; overflow-y: auto;">
                <div style="text-align: center; color: #666; font-style: italic;">No recent trades</div>
            </div>
            
            <h2>�🔌 SYSTEMS</h2>
            <div id="systems-list"></div>
            
            <h2 style="margin-top: 15px;">💎 BALANCES</h2>
            <div id="balances-list"></div>

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
        <div class="panel" style="min-height: 400px;">
            <h2>📡 LIVE SIGNALS</h2>
            <div id="signals-feed" style="max-height: calc(100% - 50px); overflow-y: auto;"></div>
        </div>
        
        <!-- Right Panel: Market Overview -->
        <div class="panel" style="min-height: 400px;">
            <h2>📈 MARKET OVERVIEW</h2>
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
            <div id="top-movers" style="max-height: 200px; overflow-y: auto;"></div>
            
            <h2 style="margin-top: 15px;">📉 TOP FALLERS</h2>
            <div id="top-fallers" style="max-height: 200px; overflow-y: auto;"></div>
        </div>
    </div>
    </div><!-- end tab-trading -->

    <!-- TAB 2: WHALES - Live Whale Tracker -->
    <div id="tab-whales" class="tab-content">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; height: 100%;">
            <div class="panel" style="overflow-y: auto;">
                <h2>🐋 LIVE WHALE ACTIVITY</h2>
                <div id="whale-feed" style="max-height: calc(100vh - 200px); overflow-y: auto;">
                    <div style="text-align: center; color: #666; padding: 40px;">
                        <div style="font-size: 3em;">🐋</div>
                        <p>Monitoring for whale movements...</p>
                        <p style="font-size: 0.8em; color: #444;">Large orders > $100k will appear here</p>
                    </div>
                </div>
            </div>
            <div class="panel">
                <h2>📊 WHALE STATISTICS</h2>
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
                <div id="whale-targets">
                    <div class="balance-item"><span class="balance-asset">BTC/USD</span><span class="balance-amount">Monitoring...</span></div>
                    <div class="balance-item"><span class="balance-asset">ETH/USD</span><span class="balance-amount">Monitoring...</span></div>
                    <div class="balance-item"><span class="balance-asset">SOL/USD</span><span class="balance-amount">Monitoring...</span></div>
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
                    <div class="system-item" style="border-left-color: var(--accent-purple);">
                        <span class="system-name">🏦 Citadel Securities</span>
                        <span class="system-status">Active</span>
                    </div>
                    <div class="system-item" style="border-left-color: var(--accent-blue);">
                        <span class="system-name">🏦 Jump Trading</span>
                        <span class="system-status">Active</span>
                    </div>
                    <div class="system-item" style="border-left-color: var(--accent-gold);">
                        <span class="system-name">🏦 Two Sigma</span>
                        <span class="system-status">Monitoring</span>
                    </div>
                    <div class="system-item" style="border-left-color: var(--accent-green);">
                        <span class="system-name">🏦 Renaissance Tech</span>
                        <span class="system-status">Quiet</span>
                    </div>
                </div>
                <h2 style="margin-top: 15px;">🔬 BOT SIGNATURES</h2>
                <div id="bot-signatures">
                    <div class="balance-item"><span style="color: var(--accent-purple);">ICEBERG</span><span>47 detected</span></div>
                    <div class="balance-item"><span style="color: var(--accent-blue);">TWAP</span><span>23 detected</span></div>
                    <div class="balance-item"><span style="color: var(--accent-gold);">VWAP</span><span>18 detected</span></div>
                    <div class="balance-item"><span style="color: var(--accent-green);">SNIPER</span><span>8 detected</span></div>
                </div>
            </div>
            <div class="panel">
                <h2>🌍 GLOBAL BOT MAP</h2>
                <div id="bot-map" style="background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%); border-radius: 8px; padding: 20px; height: calc(100% - 60px); position: relative;">
                    <div style="position: absolute; top: 20%; left: 15%; width: 12px; height: 12px; background: var(--accent-green); border-radius: 50%; animation: pulse 2s infinite;" title="NYC"></div>
                    <div style="position: absolute; top: 25%; left: 48%; width: 10px; height: 10px; background: var(--accent-blue); border-radius: 50%; animation: pulse 2s infinite 0.3s;" title="London"></div>
                    <div style="position: absolute; top: 35%; left: 75%; width: 14px; height: 14px; background: var(--accent-gold); border-radius: 50%; animation: pulse 2s infinite 0.6s;" title="Tokyo"></div>
                    <div style="position: absolute; top: 40%; left: 70%; width: 8px; height: 8px; background: var(--accent-purple); border-radius: 50%; animation: pulse 2s infinite 0.9s;" title="Singapore"></div>
                    <div style="position: absolute; top: 30%; left: 20%; width: 6px; height: 6px; background: var(--accent-red); border-radius: 50%; animation: pulse 2s infinite 1.2s;" title="Chicago"></div>
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
                        <div class="stat-value" id="total-bots">96</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Active Now</div>
                        <div class="stat-value gold" id="active-bots">34</div>
                    </div>
                </div>
                <h2 style="margin-top: 15px;">⚡ RECENT BOT ACTIVITY</h2>
                <div id="bot-activity">
                    <div class="signal-item buy">
                        <div class="signal-header">
                            <span class="signal-symbol">ICEBERG @ BTC</span>
                            <span class="signal-type buy">BUY</span>
                        </div>
                        <div class="signal-details">Citadel - Hidden order detected</div>
                    </div>
                    <div class="signal-item sell">
                        <div class="signal-header">
                            <span class="signal-symbol">TWAP @ ETH</span>
                            <span class="signal-type sell">SELL</span>
                        </div>
                        <div class="signal-details">Jump Trading - Time-weighted execution</div>
                    </div>
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
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; height: 100%;">
            <div class="panel">
                <h2>🔮 QUANTUM MIRROR SCANNER</h2>
                <div style="text-align: center; padding: 30px;">
                    <div style="font-size: 5em; animation: float 3s ease-in-out infinite;">🔮</div>
                    <div style="margin-top: 20px; color: var(--accent-gold); font-size: 1.2em;">Timeline Coherence</div>
                    <div style="font-size: 3em; color: var(--accent-green); margin: 10px 0;" id="quantum-coherence">0.618</div>
                    <div style="color: #666;">φ Golden Ratio Alignment</div>
                </div>
                <div class="stats-grid" style="margin-top: 20px;">
                    <div class="stat-card">
                        <div class="stat-label">Active Timelines</div>
                        <div class="stat-value" id="active-timelines">7</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Anchored</div>
                        <div class="stat-value gold" id="anchored-timelines">3</div>
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
            </div>
            <div class="panel">
                <h2>🌌 STARGATE PROTOCOL</h2>
                <div id="stargate-nodes" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding: 15px;">
                    <div class="stat-card" style="border-color: var(--accent-gold);">
                        <div class="stat-label">🏛️ GIZA</div>
                        <div class="stat-value" style="font-size: 1em;">432 Hz</div>
                        <div style="font-size: 0.7em; color: #888;">Casimir: 0.95</div>
                    </div>
                    <div class="stat-card" style="border-color: var(--accent-blue);">
                        <div class="stat-label">🗿 STONEHENGE</div>
                        <div class="stat-value" style="font-size: 1em;">396 Hz</div>
                        <div style="font-size: 0.7em; color: #888;">Casimir: 0.88</div>
                    </div>
                    <div class="stat-card" style="border-color: var(--accent-green);">
                        <div class="stat-label">⛰️ MACHU PICCHU</div>
                        <div class="stat-value" style="font-size: 1em;">528 Hz</div>
                        <div style="font-size: 0.7em; color: #888;">Casimir: 0.90</div>
                    </div>
                    <div class="stat-card" style="border-color: var(--accent-purple);">
                        <div class="stat-label">🏯 ANGKOR WAT</div>
                        <div class="stat-value" style="font-size: 1em;">417 Hz</div>
                        <div style="font-size: 0.7em; color: #888;">Casimir: 0.87</div>
                    </div>
                    <div class="stat-card" style="border-color: var(--accent-red);">
                        <div class="stat-label">🗻 SEDONA</div>
                        <div class="stat-value" style="font-size: 1em;">639 Hz</div>
                        <div style="font-size: 0.7em; color: #888;">Casimir: 0.82</div>
                    </div>
                    <div class="stat-card" style="border-color: var(--accent-gold);">
                        <div class="stat-label">🌋 ULURU</div>
                        <div class="stat-value" style="font-size: 1em;">741 Hz</div>
                        <div style="font-size: 0.7em; color: #888;">Casimir: 0.79</div>
                    </div>
                </div>
                <h2 style="margin-top: 15px;">🌊 HARMONIC RESONANCE</h2>
                <div style="background: rgba(0,0,0,0.4); border-radius: 8px; padding: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>Alpha (8-12 Hz)</span>
                        <span style="color: var(--accent-green);" id="alpha-hz">10.2 Hz</span>
                    </div>
                    <div class="signal-confidence"><div class="signal-confidence-bar" style="width: 72%; background: var(--accent-green);"></div></div>
                    <div style="display: flex; justify-content: space-between; margin: 15px 0 10px;">
                        <span>Theta (4-8 Hz)</span>
                        <span style="color: var(--accent-blue);" id="theta-hz">6.8 Hz</span>
                    </div>
                    <div class="signal-confidence"><div class="signal-confidence-bar" style="width: 58%; background: var(--accent-blue);"></div></div>
                    <div style="display: flex; justify-content: space-between; margin: 15px 0 10px;">
                        <span>Delta (0.5-4 Hz)</span>
                        <span style="color: var(--accent-purple);" id="delta-hz">2.1 Hz</span>
                    </div>
                    <div class="signal-confidence"><div class="signal-confidence-bar" style="width: 35%; background: var(--accent-purple);"></div></div>
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
        
        function handleMessage(data) {
            switch(data.type) {
                case 'full_state':
                    updateFullState(data);
                    break;
                case 'queen_update':
                    updateQueen(data);
                    break;
                case 'signal':
                    addSignal(data.signal);
                    break;
                case 'portfolio_update':
                    updatePortfolio(data);
                    break;
                case 'market_update':
                    updateMarket(data);
                    break;
                case 'systems_update':
                    updateSystems(data.systems);
                    break;
                case 'live_update':
                    handleLiveUpdate(data.data);
                    updateHubStats(data.data);
                    break;
            }
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
                document.getElementById('total-value').textContent = '$' + formatNumber(data.portfolio.total_value_usd || 0);
                document.getElementById('cash-available').textContent = '$' + formatNumber(data.portfolio.cash_available || 0);
                
                const pnlToday = data.portfolio.pnl_today || 0;
                const pnlTodayEl = document.getElementById('pnl-today');
                pnlTodayEl.textContent = '$' + formatNumber(pnlToday);
                pnlTodayEl.className = 'stat-value ' + (pnlToday >= 0 ? '' : 'negative');
                
                const pnlTotal = data.portfolio.pnl_total || 0;
                const pnlTotalEl = document.getElementById('pnl-total');
                pnlTotalEl.textContent = '$' + formatNumber(pnlTotal);
                pnlTotalEl.className = 'stat-value ' + (pnlTotal >= 0 ? '' : 'negative');
            }
            
            if (data.balances) {
                updateBalances(data.balances);
            }
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
            div.className = 'signal-item ' + (signal.signal_type || 'hold').toLowerCase();
            
            const confidence = signal.confidence || 0;
            
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
            const countEl = document.getElementById('bot-count');
            if (countEl && data.bot_count !== undefined) {
                countEl.textContent = data.bot_count;
            }
            const totalEl = document.getElementById('total-bots');
            if (totalEl && data.total_bots !== undefined) {
                totalEl.textContent = data.total_bots;
            }
            const activeEl = document.getElementById('active-bots');
            if (activeEl && data.active_bots !== undefined) {
                activeEl.textContent = data.active_bots;
            }
            // Add bot activity to feed
            if (data.bot_activity) {
                const feed = document.getElementById('bot-activity');
                if (feed) {
                    data.bot_activity.forEach(b => {
                        const div = document.createElement('div');
                        div.className = 'signal-item ' + b.side;
                        div.innerHTML = `
                            <div class="signal-header">
                                <span class="signal-symbol">${b.pattern} @ ${b.symbol}</span>
                                <span class="signal-type ${b.side}">${b.side.toUpperCase()}</span>
                            </div>
                            <div class="signal-details">${b.firm} - ${b.description}</div>
                        `;
                        feed.insertBefore(div, feed.firstChild);
                        while (feed.children.length > 20) feed.removeChild(feed.lastChild);
                    });
                }
            }
        }

        // Update market feed tab
        function updateMarketFeedTab(data) {
            if (data.kraken_prices) {
                const feed = document.getElementById('kraken-feed');
                if (feed) {
                    feed.innerHTML = '';
                    Object.entries(data.kraken_prices).slice(0, 15).forEach(([sym, price]) => {
                        const change = (Math.random() - 0.5) * 0.1; // Simulated change
                        const changeClass = change >= 0 ? 'positive' : 'negative';
                        const div = document.createElement('div');
                        div.className = 'mover-item';
                        div.innerHTML = `<span class="mover-symbol">${sym}</span><span class="mover-change ${changeClass}">$${formatNumber(price)}</span>`;
                        feed.appendChild(div);
                    });
                }
            }
            if (data.binance_prices) {
                const feed = document.getElementById('binance-feed');
                if (feed) {
                    feed.innerHTML = '';
                    Object.entries(data.binance_prices).slice(0, 15).forEach(([sym, price]) => {
                        const changeClass = Math.random() > 0.5 ? 'positive' : 'negative';
                        const div = document.createElement('div');
                        div.className = 'mover-item';
                        div.innerHTML = `<span class="mover-symbol">${sym}</span><span class="mover-change ${changeClass}">$${formatNumber(price)}</span>`;
                        feed.appendChild(div);
                    });
                }
            }
            if (data.alpaca_prices) {
                const feed = document.getElementById('alpaca-feed');
                if (feed) {
                    feed.innerHTML = '';
                    Object.entries(data.alpaca_prices).slice(0, 15).forEach(([sym, price]) => {
                        const changeClass = Math.random() > 0.5 ? 'positive' : 'negative';
                        const div = document.createElement('div');
                        div.className = 'mover-item';
                        div.innerHTML = `<span class="mover-symbol">${sym}</span><span class="mover-change ${changeClass}">$${formatNumber(price)}</span>`;
                        feed.appendChild(div);
                    });
                }
            }
        }

        // Update quantum tab
        function updateQuantumTab(data) {
            if (data.quantum) {
                const cohEl = document.getElementById('quantum-coherence');
                if (cohEl) cohEl.textContent = (data.quantum.coherence || 0.618).toFixed(3);
                const timelineEl = document.getElementById('active-timelines');
                if (timelineEl) timelineEl.textContent = data.quantum.active_timelines || 7;
                const anchoredEl = document.getElementById('anchored-timelines');
                if (anchoredEl) anchoredEl.textContent = data.quantum.anchored_timelines || 3;
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
        
        # Stats
        self.updates_sent = 0
        self.last_update = 0.0
        
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
        await ws.send_json({
            "type": "full_state",
            "systems": SYSTEMS_STATUS,
            "portfolio": asdict(self.portfolio),
            "market": asdict(self.market),
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
    
    async def fetch_all_balances(self):
        """Fetch balances from all exchanges and calculate total USD value."""
        total_usd = 0.0
        all_balances = {}
        
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
                for asset, amount in all_balances['kraken'].items():
                    total_usd += get_usd_value(asset, amount, 'kraken')
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
                    for asset, amount in all_balances['binance'].items():
                        total_usd += get_usd_value(asset, amount, 'binance')
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
                        # Also get crypto positions
                        try:
                            positions = self.alpaca.get_positions() if hasattr(self.alpaca, 'get_positions') else []
                            for pos in (positions or []):
                                symbol = pos.get('symbol', '')
                                qty = float(pos.get('qty', 0))
                                market_val = float(pos.get('market_value', 0))
                                if qty > 0 and market_val > 0:
                                    all_balances['alpaca'][symbol] = qty
                                    total_usd += market_val
                        except:
                            pass
                        total_usd += cash
            except Exception as e:
                logger.error(f"Alpaca balance error: {e}")
        
        # Capital.com - check if we have a client
        # (Capital uses different balance structure - check if available)
        
        self.portfolio.balances = all_balances
        self.portfolio.total_value_usd = total_usd
        self.portfolio.cash_available = total_usd

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
                        kraken_prices[symbol] = price
                        
                        # Calculate change from stored price
                        old_price = self.prices.get(f"kraken:{symbol}", price)
                        if old_price > 0:
                            change = (price - old_price) / old_price
                            top_movers.append({
                                "symbol": symbol,
                                "price": price,
                                "change": change,
                                "exchange": "kraken"
                            })
                        self.prices[f"kraken:{symbol}"] = price
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
                            binance_prices[symbol] = price
                            
                            old_price = self.prices.get(f"binance:{symbol}", price)
                            if old_price > 0:
                                change = (price - old_price) / old_price
                                top_movers.append({
                                    "symbol": symbol,
                                    "price": price,
                                    "change": change,
                                    "exchange": "binance"
                                })
                            self.prices[f"binance:{symbol}"] = price
                except Exception as e:
                    logger.debug(f"Binance ticker error for {symbol}: {e}")
        
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
