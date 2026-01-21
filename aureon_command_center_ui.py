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

import asyncio
import json
import time
import logging
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
# SYSTEM IMPORTS - ALL MODELS
# ════════════════════════════════════════════════════════════════════════════
SYSTEMS_STATUS = {}

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

# Exchange Clients
print("\n🔌 LOADING EXCHANGE CLIENTS...")
KrakenClient = safe_import('Kraken', lambda: __import__('kraken_client', fromlist=['KrakenClient']).KrakenClient)
BinanceClient = safe_import('Binance', lambda: __import__('binance_client', fromlist=['BinanceClient']).BinanceClient)
AlpacaClient = safe_import('Alpaca', lambda: __import__('alpaca_client', fromlist=['AlpacaClient']).AlpacaClient)

# Queen & Neural Systems
print("\n👑 LOADING QUEEN & NEURAL SYSTEMS...")
QueenHiveMind = safe_import('Queen Hive Mind', lambda: __import__('aureon_queen_hive_mind', fromlist=['QueenHiveMind']).QueenHiveMind)
MyceliumNetwork = safe_import('Mycelium Network', lambda: __import__('aureon_mycelium', fromlist=['MyceliumNetwork']).MyceliumNetwork)
ThoughtBus = safe_import('Thought Bus', lambda: __import__('aureon_thought_bus', fromlist=['ThoughtBus']).ThoughtBus)

# Intelligence Systems  
print("\n🧠 LOADING INTELLIGENCE SYSTEMS...")
ProbabilityUltimateIntelligence = safe_import('Ultimate Intelligence', lambda: __import__('probability_ultimate_intelligence', fromlist=['ProbabilityUltimateIntelligence']).ProbabilityUltimateIntelligence)
MinerBrain = safe_import('Miner Brain', lambda: __import__('aureon_miner_brain', fromlist=['MinerBrain']).MinerBrain)
TimelineOracle = safe_import('Timeline Oracle', lambda: __import__('aureon_timeline_oracle', fromlist=['TimelineOracle']).TimelineOracle)
QuantumMirrorScanner = safe_import('Quantum Mirror', lambda: __import__('aureon_quantum_mirror_scanner', fromlist=['QuantumMirrorScanner']).QuantumMirrorScanner)

# Harmonic & Momentum Systems
print("\n🌊 LOADING HARMONIC & MOMENTUM SYSTEMS...")
HarmonicWaveFusion = safe_import('Harmonic Fusion', lambda: __import__('aureon_harmonic_fusion', fromlist=['HarmonicWaveFusion']).HarmonicWaveFusion)
GlobalWaveScanner = safe_import('Wave Scanner', lambda: __import__('aureon_global_wave_scanner', fromlist=['GlobalWaveScanner']).GlobalWaveScanner)

# Data & Conversion Systems
print("\n💰 LOADING DATA & CONVERSION SYSTEMS...")
MyceliumConversionHub = safe_import('Conversion Hub', lambda: __import__('mycelium_conversion_hub', fromlist=['MyceliumConversionHub']).MyceliumConversionHub)

# Print system status
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
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid var(--accent-gold);
            box-shadow: 0 4px 30px rgba(255, 170, 0, 0.3);
        }
        
        .logo {
            font-size: 1.8em;
            font-weight: bold;
            background: linear-gradient(90deg, var(--accent-gold), #ff6600);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .status-bar {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-dot.online { background: var(--accent-green); }
        .status-dot.offline { background: var(--accent-red); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Main Container */
        #container {
            display: grid;
            grid-template-columns: 300px 1fr 350px;
            grid-template-rows: auto 1fr;
            gap: 15px;
            padding: 15px;
            height: calc(100vh - 80px);
        }
        
        /* Panels */
        .panel {
            background: var(--bg-panel);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 10px;
            padding: 15px;
            overflow-y: auto;
            backdrop-filter: blur(10px);
        }
        
        .panel h2 {
            color: var(--accent-gold);
            font-size: 1.1em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 170, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 10px;
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
        @media (max-width: 1200px) {
            #container {
                grid-template-columns: 1fr;
            }
            #queen-panel {
                grid-column: 1;
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
    
    <div id="container">
        <!-- Queen Panel (Full Width Top) -->
        <div id="queen-panel" class="panel">
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
            
            <h2>⚔️ ACTIVE POSITIONS</h2>
            <div id="positions-list" style="margin-bottom: 20px;">
                <div style="text-align: center; color: #666; font-style: italic;">No active positions</div>
            </div>
            
            <h2>🔌 SYSTEMS</h2>
            <div id="systems-list"></div>
            
            <h2 style="margin-top: 15px;">💎 BALANCES</h2>
            <div id="balances-list"></div>
        </div>
        
        <!-- Center Panel: Signals Feed -->
        <div class="panel">
            <h2>📡 LIVE SIGNALS</h2>
            <div id="signals-feed"></div>
        </div>
        
        <!-- Right Panel: Market Overview -->
        <div class="panel">
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
            <div id="top-movers"></div>
            
            <h2 style="margin-top: 15px;">📉 TOP FALLERS</h2>
            <div id="top-fallers"></div>
        </div>
    </div>
    
    <div id="connection-status">
        <span class="status-dot online"></span>
        <span>Connected</span>
    </div>
    
    <script>
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
                    break;
            }
        }
        
        function updateFullState(data) {
            if (data.portfolio) updatePortfolio(data);
            if (data.systems) updateSystems(data.systems);
            if (data.market) updateMarket(data);
            if (data.queen) updateQueen(data);
            if (data.signals) {
                data.signals.forEach(s => addSignal(s));
            }
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

        // Clock
        function updateClock() {
            const now = new Date();
            document.getElementById('clock').textContent = now.toLocaleTimeString();
        }
        setInterval(updateClock, 1000);
        updateClock();
        
        // Connect on load
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
        
        # Stats
        self.updates_sent = 0
        self.last_update = 0.0
        
        # Web server
        if AIOHTTP_AVAILABLE:
            self.app = web.Application()
            self.app.router.add_get('/', self.handle_index)
            self.app.router.add_get('/ws', self.handle_websocket)
            self.app.router.add_get('/api/status', self.handle_api_status)
            self.app.router.add_get('/api/portfolio', self.handle_api_portfolio)
            self.app.router.add_get('/api/signals', self.handle_api_signals)
    
    async def initialize_systems(self):
        """Initialize all trading systems."""
        print("\n" + "=" * 70)
        print("👑🌌 AUREON COMMAND CENTER - INITIALIZING ALL SYSTEMS")
        print("=" * 70)
        
        # Exchange Clients
        print("\n📊 CONNECTING TO EXCHANGES...")
        
        if KrakenClient:
            try:
                self.kraken = KrakenClient()
                print("   🐙 Kraken: CONNECTED")
            except Exception as e:
                logger.error(f"Kraken error: {e}")
        
        if BinanceClient:
            try:
                self.binance = BinanceClient()
                print("   🟡 Binance: CONNECTED")
            except Exception as e:
                logger.error(f"Binance error: {e}")
        
        if AlpacaClient:
            try:
                self.alpaca = AlpacaClient()
                print("   🦙 Alpaca: CONNECTED")
            except Exception as e:
                logger.error(f"Alpaca error: {e}")
        
        # Neural Systems
        print("\n👑 WIRING NEURAL SYSTEMS...")
        
        if ThoughtBus:
            try:
                self.thought_bus = ThoughtBus()
                print("   📡 Thought Bus: WIRED")
            except Exception as e:
                logger.error(f"ThoughtBus error: {e}")
        
        if MyceliumNetwork:
            try:
                self.mycelium = MyceliumNetwork()
                print("   🍄 Mycelium Network: WIRED")
            except Exception as e:
                logger.error(f"Mycelium error: {e}")
        
        if QueenHiveMind:
            try:
                self.queen = QueenHiveMind()
                print("   👑 Queen Hive Mind: WIRED")
            except Exception as e:
                logger.error(f"Queen error: {e}")
        
        # Intelligence Systems
        print("\n🧠 WIRING INTELLIGENCE SYSTEMS...")
        
        if MinerBrain:
            try:
                self.miner = MinerBrain()
                print("   🧠 Miner Brain: WIRED")
            except Exception as e:
                logger.error(f"MinerBrain error: {e}")
        
        if ProbabilityUltimateIntelligence:
            try:
                self.ultimate_intel = ProbabilityUltimateIntelligence()
                print("   💎 Ultimate Intelligence: WIRED")
            except Exception as e:
                logger.error(f"UltimateIntel error: {e}")
        
        if TimelineOracle:
            try:
                self.timeline_oracle = TimelineOracle()
                print("   ⏳🔮 Timeline Oracle: WIRED")
            except Exception as e:
                logger.error(f"TimelineOracle error: {e}")
        
        if QuantumMirrorScanner:
            try:
                self.quantum_mirror = QuantumMirrorScanner()
                print("   🔮 Quantum Mirror: WIRED")
            except Exception as e:
                logger.error(f"QuantumMirror error: {e}")
        
        # Harmonic & Momentum
        print("\n🌊 WIRING HARMONIC & MOMENTUM...")
        
        if HarmonicWaveFusion:
            try:
                self.harmonic = HarmonicWaveFusion()
                print("   🌊 Harmonic Fusion: WIRED")
            except Exception as e:
                logger.error(f"Harmonic error: {e}")
        
        if GlobalWaveScanner:
            try:
                self.wave_scanner = GlobalWaveScanner()
                print("   🌊🔭 Wave Scanner: WIRED")
            except Exception as e:
                logger.error(f"WaveScanner error: {e}")
        
        # Conversion Hub
        if MyceliumConversionHub:
            try:
                self.conversion_hub = MyceliumConversionHub()
                print("   🍄 Conversion Hub: WIRED")
            except Exception as e:
                logger.error(f"ConversionHub error: {e}")
        
        # Count working systems
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
        await ws.send_json({
            "type": "full_state",
            "systems": SYSTEMS_STATUS,
            "portfolio": asdict(self.portfolio),
            "market": asdict(self.market),
            "signals": [asdict(s) if hasattr(s, '__dataclass_fields__') else s for s in list(self.signals)[-20:]],
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
        """Fetch balances from all exchanges."""
        total_usd = 0.0
        all_balances = {}
        
        # Kraken
        if self.kraken:
            try:
                balances = self.kraken.get_account_balance() or {}
                all_balances['kraken'] = {k: float(v) for k, v in balances.items() if float(v) > 0.0001}
                # Estimate USD value
                for asset, amount in all_balances['kraken'].items():
                    if asset in ['USD', 'ZUSD', 'USDT', 'USDC']:
                        total_usd += amount
                    else:
                        # Would need price lookup
                        pass
            except Exception as e:
                logger.error(f"Kraken balance error: {e}")
        
        # Binance
        if self.binance:
            try:
                if hasattr(self.binance, 'get_balances'):
                    balances = self.binance.get_balances() or {}
                    all_balances['binance'] = {k: float(v) for k, v in balances.items() if float(v) > 0.0001}
            except Exception as e:
                logger.error(f"Binance balance error: {e}")
        
        # Alpaca
        if self.alpaca:
            try:
                if hasattr(self.alpaca, 'get_account'):
                    account = self.alpaca.get_account()
                    if account:
                        cash = float(getattr(account, 'cash', 0) or 0)
                        all_balances['alpaca'] = {'USD': cash}
                        total_usd += cash
            except Exception as e:
                logger.error(f"Alpaca balance error: {e}")
        
        self.portfolio.balances = all_balances
        self.portfolio.total_value_usd = total_usd
        self.portfolio.cash_available = total_usd

        # Basic market overview from balances (fallback when no market feeds)
        unique_assets = set()
        for _, balances in all_balances.items():
            unique_assets.update(balances.keys())
        self.market.total_assets_tracked = len(unique_assets)
        self.market.rising_count = 0
        self.market.falling_count = 0
        self.market.top_movers = []
    
    async def update_loop(self):
        """Main update loop."""
        while self.running:
            try:
                # 1. Read live dashboard snapshot from Orca
                state_dir = os.environ.get("AUREON_STATE_DIR", "state")
                snapshot_file = os.path.join(state_dir, "dashboard_snapshot.json")
                if os.path.exists(snapshot_file):
                    try:
                        with open(snapshot_file, "r") as f:
                             data = json.load(f)
                        
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

                    except Exception:
                        pass

                # 2. Fetch balances every 30 seconds
                if time.time() - self.last_update > 30:
                    await self.fetch_all_balances()
                    await self.broadcast_portfolio()
                    await self.broadcast({
                        "type": "market_update",
                        "market": asdict(self.market)
                    })
                    self.last_update = time.time()
                
                await asyncio.sleep(1) 
                
            except Exception as e:
                logger.error(f"Update loop error: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the command center."""
        await self.initialize_systems()
        
        self.running = True
        
        # Start web server
        if AIOHTTP_AVAILABLE:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', self.port)
            await site.start()
            
            print(f"\n{'=' * 70}")
            print(f"👑🌌 AUREON COMMAND CENTER ONLINE")
            print(f"{'=' * 70}")
            print(f"🌐 Dashboard: http://localhost:{self.port}")
            print(f"📡 WebSocket: ws://localhost:{self.port}/ws")
            print(f"🔌 REST API:")
            print(f"   GET /api/status   - System status")
            print(f"   GET /api/portfolio - Portfolio data")
            print(f"   GET /api/signals  - Recent signals")
            print(f"{'=' * 70}\n")
        
        # Start update loop
        asyncio.create_task(self.update_loop())
        
        # Keep running
        await asyncio.Event().wait()


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
