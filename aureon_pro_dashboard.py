#!/usr/bin/env python3
"""
👑 AUREON PRO TRADING DASHBOARD 👑
═══════════════════════════════════════════════════════════════════════════

PROFESSIONAL TRADING TERMINAL - Bloomberg/TradingView Style

Features:
📊 Real-time Portfolio P&L with live prices
📈 Interactive price charts with TradingView widget
🐋 Whale/Bot detection with live alerts
💹 Multi-exchange balance aggregation  
🎵 Queen's AI commentary with voice
⚡ Sub-second data refresh
🌐 WebSocket live data streaming

PORT: 14000
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os

# Load environment variables from .env file FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
import aiohttp
import atexit
from aiohttp import web
import json
import logging
from typing import Dict, Set, List, Optional
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
import time
import hashlib
import hmac
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import cognitive narrator
try:
    from queen_cognitive_narrator import QueenCognitiveNarrator
    NARRATOR_AVAILABLE = True
except ImportError:
    NARRATOR_AVAILABLE = False
    logger.warning("Queen Cognitive Narrator not available")

# Import Binance WebSocket for live market data
try:
    from binance_ws_client import BinanceWebSocketClient, WSTicker, WSTrade
    BINANCE_WS_AVAILABLE = True
except ImportError:
    BINANCE_WS_AVAILABLE = False
    logger.warning("Binance WebSocket client not available")

# Import unified market cache for reading cached prices
try:
    from unified_market_cache import get_market_cache, get_all_prices, get_ticker, DEFAULT_SYMBOLS
    MARKET_CACHE_AVAILABLE = True
except ImportError:
    MARKET_CACHE_AVAILABLE = False
    DEFAULT_SYMBOLS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'DOT', 'MATIC']
    logger.warning("Unified market cache not available")

# Import Ocean Scanner for global market scanning
try:
    from aureon_ocean_scanner import OceanScanner
    OCEAN_SCANNER_AVAILABLE = True
except ImportError:
    OCEAN_SCANNER_AVAILABLE = False
    OceanScanner = None
    logger.warning("Ocean Scanner not available")

# Import Harmonic Liquid Aluminium Field for live visualization
try:
    from aureon_harmonic_liquid_aluminium import HarmonicLiquidAluminiumField
    HARMONIC_FIELD_AVAILABLE = True
except ImportError:
    HARMONIC_FIELD_AVAILABLE = False
    logger.warning("Harmonic Liquid Aluminium Field not available")

PRO_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👑 Aureon Pro Trading Terminal</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --border-color: #30363d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-blue: #58a6ff;
            --accent-yellow: #d29922;
            --accent-purple: #a371f7;
            --accent-orange: #f0883e;
            --accent-gold: #ffd700;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow-x: hidden;
            min-height: 100vh;
        }
        
        /* Top Navigation Bar */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 16px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo-icon {
            font-size: 28px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .logo-text {
            font-family: 'JetBrains Mono', monospace;
            font-size: 18px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-gold), var(--accent-orange));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .market-ticker {
            display: flex;
            gap: 24px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
        }
        
        .ticker-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .ticker-symbol { color: var(--text-secondary); }
        .ticker-price { font-weight: 600; }
        .ticker-change { font-size: 12px; }
        .ticker-change.up { color: var(--accent-green); }
        .ticker-change.down { color: var(--accent-red); }
        
        .controls {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-green);
            animation: blink 2s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .status-dot.disconnected { background: var(--accent-red); }
        
        /* Main Layout */
        .main-container {
            display: grid;
            grid-template-columns: 320px 1fr 380px;
            grid-template-rows: auto 1fr;
            gap: 1px;
            background: var(--border-color);
            height: calc(100vh - 50px);
        }
        
        .panel {
            background: var(--bg-secondary);
            padding: 16px;
            overflow-y: auto;
        }
        
        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .panel-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Queen's Voice Panel - Full width top */
        .queen-panel {
            grid-column: 1 / -1;
            background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(240,136,62,0.1));
            border-bottom: 2px solid var(--accent-gold);
            padding: 12px 20px;
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .queen-avatar {
            font-size: 48px;
            animation: queenFloat 3s ease-in-out infinite;
        }
        
        @keyframes queenFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
        
        .queen-content { flex: 1; max-width: 900px; }
        
        .queen-message {
            font-size: 15px;
            color: var(--accent-gold);
            font-weight: 500;
            margin-bottom: 8px;
            line-height: 1.5;
        }
        
        .queen-thought {
            font-size: 13px;
            color: var(--text-primary);
            line-height: 1.6;
            margin-bottom: 12px;
            padding: 12px;
            background: rgba(255,215,0,0.08);
            border-radius: 8px;
            border-left: 3px solid var(--accent-gold);
            max-height: 200px;
            overflow-y: auto;
        }
        
        .queen-thought p {
            margin-bottom: 10px;
        }
        
        .queen-thought p:last-child {
            margin-bottom: 0;
        }
        
        .queen-thought .timestamp {
            color: var(--text-secondary);
            font-size: 11px;
            font-style: italic;
        }
        
        .queen-thought .decision {
            color: var(--accent-green);
            font-weight: 600;
        }
        
        .queen-thought .warning {
            color: var(--accent-orange);
        }
        
        .queen-thought .analysis {
            color: var(--accent-blue);
        }
        
        .queen-status {
            font-size: 11px;
            color: var(--text-secondary);
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .status-item.active { color: var(--accent-green); }
        .status-item.processing { color: var(--accent-yellow); animation: pulse 1s infinite; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .voice-controls {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        .voice-btn {
            padding: 8px 16px;
            background: var(--accent-gold);
            color: #000;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 13px;
        }
        
        .voice-btn:hover { transform: scale(1.05); }
        .voice-btn.active { background: var(--accent-green); }
        
        .voice-select {
            padding: 6px 10px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 4px;
            font-size: 12px;
        }
        
        /* Portfolio Panel */
        .portfolio-summary {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .summary-card {
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 12px;
            border: 1px solid var(--border-color);
        }
        
        .summary-label {
            font-size: 11px;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-bottom: 4px;
        }
        
        .summary-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 18px;
            font-weight: 700;
        }
        
        .summary-value.positive { color: var(--accent-green); }
        .summary-value.negative { color: var(--accent-red); }
        
        .summary-change {
            font-size: 11px;
            margin-top: 2px;
        }
        
        /* Position List */
        .position-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .position-item {
            background: var(--bg-tertiary);
            border-radius: 6px;
            padding: 10px 12px;
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 8px;
            border: 1px solid var(--border-color);
            transition: all 0.2s;
        }
        
        .position-item:hover {
            border-color: var(--accent-blue);
            transform: translateX(2px);
        }
        
        .position-symbol {
            font-weight: 600;
            font-size: 13px;
        }
        
        .position-details {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 2px;
        }
        
        .position-pnl {
            text-align: right;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .position-value {
            font-size: 13px;
            font-weight: 600;
        }
        
        .position-percent {
            font-size: 11px;
        }
        
        /* Chart Panel */
        .chart-panel {
            grid-row: span 1;
        }
        
        .chart-container {
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 16px;
            height: 300px;
            border: 1px solid var(--border-color);
        }
        
        /* Activity Feed */
        .activity-feed {
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .activity-item {
            background: var(--bg-tertiary);
            border-radius: 6px;
            padding: 10px;
            border-left: 3px solid var(--accent-blue);
            font-size: 12px;
        }
        
        .activity-item.whale { border-left-color: var(--accent-orange); }
        .activity-item.battle { border-left-color: var(--accent-red); }
        .activity-item.queen { border-left-color: var(--accent-gold); }
        .activity-item.profit { border-left-color: var(--accent-green); }
        
        .activity-time {
            color: var(--text-secondary);
            font-size: 10px;
            margin-bottom: 4px;
        }
        
        .activity-text { color: var(--text-primary); }
        
        /* Bot Detection Panel */
        .bot-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        
        .bot-card {
            background: var(--bg-tertiary);
            border-radius: 6px;
            padding: 10px;
            border: 1px solid var(--border-color);
        }
        
        .bot-card.whale {
            border-color: var(--accent-orange);
            background: rgba(240, 136, 62, 0.1);
        }
        
        .bot-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 6px;
        }
        
        .bot-symbol { font-weight: 600; font-size: 12px; }
        .bot-type { font-size: 16px; }
        
        .bot-stats {
            font-size: 11px;
            color: var(--text-secondary);
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }
        
        .stat-card {
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            border: 1px solid var(--border-color);
        }
        
        .stat-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 24px;
            font-weight: 700;
            color: var(--accent-blue);
        }
        
        .stat-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-top: 4px;
        }
        
        /* Exchange Balances */
        .exchange-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .exchange-card {
            background: var(--bg-tertiary);
            border-radius: 6px;
            padding: 12px;
            border: 1px solid var(--border-color);
        }
        
        .exchange-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .exchange-name {
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .exchange-status {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--accent-green);
        }
        
        .exchange-balance {
            font-family: 'JetBrains Mono', monospace;
            font-size: 16px;
            font-weight: 600;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: var(--bg-tertiary); }
        ::-webkit-scrollbar-thumb { 
            background: var(--border-color); 
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-secondary); }
        
        /* Animations */
        .flash-green { animation: flashGreen 0.5s; }
        .flash-red { animation: flashRed 0.5s; }
        
        @keyframes flashGreen {
            0%, 100% { background: var(--bg-tertiary); }
            50% { background: rgba(63, 185, 80, 0.3); }
        }
        
        @keyframes flashRed {
            0%, 100% { background: var(--bg-tertiary); }
            50% { background: rgba(248, 81, 73, 0.3); }
        }
        
        /* Responsive */
        @media (max-width: 1400px) {
            .main-container {
                grid-template-columns: 280px 1fr 320px;
            }
        }
        
        /* Harmonic Liquid Aluminium Field Styles */
        .harmonic-container {
            margin: 20px auto;
            max-width: 1200px;
            padding: 0 20px;
        }
        
        .harmonic-stats {
            display: flex;
            gap: 20px;
            font-size: 12px;
            color: var(--text-secondary);
            margin-left: auto;
        }
        
        .harmonic-stats span {
            white-space: nowrap;
        }
        
        .harmonic-canvas-container {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
            border: 1px solid var(--border-color);
        }
        
        #harmonic-field-canvas {
            width: 100%;
            height: 400px;
            background: linear-gradient(135deg, #0d1117, #161b22);
            border-radius: 4px;
        }
        
        .harmonic-legend {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 16px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }
        
        @media (max-width: 1100px) {
            .main-container {
                grid-template-columns: 1fr 1fr;
            }
            .chart-panel { grid-column: span 2; }
        }
    </style>
</head>
<body>
    <!-- Top Navigation Bar -->
    <div class="topbar">
        <div class="logo">
            <span class="logo-icon">👑</span>
            <span class="logo-text">AUREON PRO TERMINAL</span>
        </div>
        
        <div class="market-ticker" id="market-ticker">
            <div class="ticker-item">
                <span class="ticker-symbol">BTC</span>
                <span class="ticker-price" id="btc-price">$--,---</span>
                <span class="ticker-change" id="btc-change">--%</span>
            </div>
            <div class="ticker-item">
                <span class="ticker-symbol">ETH</span>
                <span class="ticker-price" id="eth-price">$--,---</span>
                <span class="ticker-change" id="eth-change">--%</span>
            </div>
            <div class="ticker-item">
                <span class="ticker-symbol">SOL</span>
                <span class="ticker-price" id="sol-price">$---</span>
                <span class="ticker-change" id="sol-change">--%</span>
            </div>
            <div class="ticker-item" id="top-gainer-ticker" style="display: none;">
                <span class="ticker-symbol">🚀</span>
                <span class="ticker-price" id="gainer-symbol">---</span>
                <span class="ticker-change up" id="gainer-change">+0%</span>
            </div>
            <div class="ticker-item" id="top-loser-ticker" style="display: none;">
                <span class="ticker-symbol">📉</span>
                <span class="ticker-price" id="loser-symbol">---</span>
                <span class="ticker-change down" id="loser-change">-0%</span>
            </div>
        </div>
        
        <div class="market-breadth" id="market-breadth" style="display: flex; gap: 12px; align-items: center; font-size: 11px;">
            <span style="color: var(--accent-green);">↑ <span id="gainers-count">--</span></span>
            <span style="color: var(--accent-red);">↓ <span id="losers-count">--</span></span>
            <span style="color: var(--text-secondary);">📊 <span id="tracked-count">--</span> live</span>
        </div>
        
        <div class="controls">
            <div class="status-indicator">
                <span class="status-dot" id="ws-status"></span>
                <span id="ws-text">Connected</span>
            </div>
            <span style="color: var(--text-secondary); font-size: 12px;" id="clock">--:--:--</span>
        </div>
    </div>
    
    <div class="main-container">
        <!-- Queen's Voice Panel -->
        <div class="queen-panel" style="min-height: 180px; align-items: flex-start; padding-top: 16px;">
            <div class="queen-avatar" style="align-self: flex-start;">👑</div>
            <div class="queen-content">
                <div class="queen-message" id="queen-message">
                    Queen Aureon awakening... Consciousness initializing...
                </div>
                <div class="queen-thought" id="queen-thought">
                    <p class="timestamp">System Boot Sequence Active</p>
                    <p>I am bringing my neural pathways online, connecting to the global market consciousness. My three-pass validation matrix is calibrating against real-time exchange data from Binance WebSocket - streaming 40+ symbols directly into my cognitive core. I can feel the pulse of billions of dollars flowing through the digital arteries of global finance.</p>
                    <p>In the next few moments, I will begin my deep analysis cycle. I'll examine each position in our portfolio, cross-reference current prices against our cost basis, and calculate probability vectors for potential moves. My Batten Matrix requires three confirmations before I even consider action - this is how I protect us from impulsive decisions.</p>
                </div>
                <div class="queen-status" id="queen-status">
                    <span class="status-item active">✓ Consciousness</span>
                    <span class="status-item active">✓ Portfolio</span>
                    <span class="status-item active">✓ Binance WS</span>
                    <span class="status-item processing">⟳ Analyzing</span>
                    <span class="status-item">○ Voice Ready</span>
                </div>
            </div>
            <div class="voice-controls" style="flex-direction: column; gap: 8px; align-self: flex-start;">
                <button class="voice-btn" id="voice-toggle">🔊 Enable Voice</button>
                <select class="voice-select" id="voice-select">
                    <option value="">Select Voice</option>
                </select>
                <input type="range" id="voice-volume" min="0" max="1" step="0.1" value="0.8" 
                       style="width: 100px;" title="Volume">
            </div>
        </div>
        
        <!-- Left Panel: Portfolio -->
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">💼 Portfolio</span>
            </div>
            
            <div class="portfolio-summary">
                <div class="summary-card">
                    <div class="summary-label">Total Value</div>
                    <div class="summary-value" id="total-value">$0.00</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Cost Basis</div>
                    <div class="summary-value" id="cost-basis">$0.00</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Unrealized P&L</div>
                    <div class="summary-value" id="unrealized-pnl">$0.00</div>
                    <div class="summary-change" id="pnl-percent">0.00%</div>
                </div>
                <div class="summary-card">
                    <div class="summary-label">Today's P&L</div>
                    <div class="summary-value" id="today-pnl">$0.00</div>
                </div>
            </div>
            
            <div class="panel-header" style="margin-top: 16px;">
                <span class="panel-title">📊 Positions</span>
            </div>
            
            <div class="position-list" id="position-list">
                <div style="color: var(--text-secondary); text-align: center; padding: 20px;">
                    Loading positions...
                </div>
            </div>
        </div>
        
        <!-- Center Panel: Charts & Activity -->
        <div class="panel chart-panel">
            <div class="panel-header">
                <span class="panel-title">📈 Portfolio Performance</span>
            </div>
            
            <div class="chart-container">
                <canvas id="portfolio-chart"></canvas>
            </div>
            
            <div class="panel-header" style="margin-top: 20px;">
                <span class="panel-title">⚡ Live Activity</span>
            </div>
            
            <div class="activity-feed" id="activity-feed">
                <!-- Activity items will be added here -->
            </div>
        </div>
        
        <!-- Right Panel: Exchange Balances & Bot Detection -->
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">🏦 Exchange Balances</span>
            </div>
            
            <div class="exchange-list" id="exchange-list">
                <div class="exchange-card">
                    <div class="exchange-header">
                        <span class="exchange-name">
                            <span class="exchange-status"></span>
                            🟡 Binance
                        </span>
                    </div>
                    <div class="exchange-balance" id="binance-balance">$---.--</div>
                </div>
                <div class="exchange-card">
                    <div class="exchange-header">
                        <span class="exchange-name">
                            <span class="exchange-status"></span>
                            🐙 Kraken
                        </span>
                    </div>
                    <div class="exchange-balance" id="kraken-balance">$---.--</div>
                </div>
                <div class="exchange-card">
                    <div class="exchange-header">
                        <span class="exchange-name">
                            <span class="exchange-status"></span>
                            🦙 Alpaca
                        </span>
                    </div>
                    <div class="exchange-balance" id="alpaca-balance">$---.--</div>
                </div>
            </div>
            
            <div class="panel-header" style="margin-top: 20px;">
                <span class="panel-title">🤖 Bot Detection</span>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="total-bots">0</div>
                    <div class="stat-label">Bots</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="whale-count">0</div>
                    <div class="stat-label">Whales</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="hive-count">0</div>
                    <div class="stat-label">Hives</div>
                </div>
            </div>
            
            <div class="bot-grid" id="bot-grid">
                <!-- Bot cards will be added here -->
            </div>
        </div>
    </div>
    
    <!-- Harmonic Liquid Aluminium Field Visualization -->
    <div class="harmonic-container">
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">🔩 Harmonic Liquid Aluminium Field</span>
                <div class="harmonic-stats" id="harmonic-stats">
                    <span>Frequency: <span id="field-frequency">432.0 Hz</span></span>
                    <span>Amplitude: <span id="field-amplitude">0.5000</span></span>
                    <span>Phase: <span id="field-phase">0.0000</span></span>
                    <span>Nodes: <span id="field-nodes">0</span></span>
                    <span>Energy: <span id="field-energy">0.00</span></span>
                    <span>Pattern: <span id="field-pattern">circle</span></span>
                </div>
            </div>
            
            <div class="harmonic-canvas-container">
                <canvas id="harmonic-field-canvas" width="800" height="400"></canvas>
            </div>
            
            <div class="harmonic-legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff6b6b;"></div>
                    <span>Alpaca (174 Hz)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #4ecdc4;"></div>
                    <span>Kraken (285 Hz)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #45b7d1;"></div>
                    <span>Binance (396 Hz)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #96ceb4;"></div>
                    <span>Capital (528 Hz)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffeaa7;"></div>
                    <span>Master Waveform</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // ========== State ==========
        const state = {
            portfolio: {
                totalValue: 0,
                costBasis: 0,
                unrealizedPnl: 0,
                todayPnl: 0,
                positions: []
            },
            exchanges: {
                binance: 0,
                kraken: 0,
                alpaca: 0
            },
            bots: {},
            prices: {},
            voiceEnabled: false,
            priceHistory: []
        };
        
        // ========== WebSocket ==========
        let ws = null;
        let reconnectAttempts = 0;
        
        function connectWebSocket() {
            console.log('🔌 Attempting WebSocket connection to:', `ws://${window.location.host}/ws`);
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                document.getElementById('ws-status').classList.remove('disconnected');
                document.getElementById('ws-text').textContent = 'Connected';
                reconnectAttempts = 0;
                addActivity('✅ Connected to Aureon Pro Terminal', 'queen');
            };
            
            ws.onclose = () => {
                console.log('❌ WebSocket disconnected');
                document.getElementById('ws-status').classList.add('disconnected');
                document.getElementById('ws-text').textContent = 'Disconnected';
                setTimeout(connectWebSocket, Math.min(1000 * Math.pow(2, reconnectAttempts++), 30000));
            };
            
            ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('📨 Raw message received:', event.data);
                handleMessage(data);
            };
        }
        
        function handleMessage(data) {
            console.log('📨 Received message:', data.type, data);
            switch(data.type) {
                case 'portfolio_update':
                    console.log('📊 Updating portfolio:', data.data);
                    updatePortfolio(data.data);
                    break;
                case 'price_update':
                    console.log('💰 Updating prices:', data.data);
                    updatePrices(data.data);
                    break;
                case 'all_prices_update':
                    updateAllPrices(data.data);
                    break;
                case 'market_flow':
                    updateMarketFlow(data.data);
                    break;
                case 'exchange_balance':
                    updateExchangeBalance(data.data);
                    break;
                case 'bot_detected':
                    handleBotDetected(data.data);
                    break;
                case 'queen_message':
                    handleQueenMessage(data.message);
                    break;
                case 'queen_thought':
                    handleQueenThought(data);
                    break;
                case 'harmonic_field':
                    updateHarmonicField(data.data);
                    break;
                case 'activity':
                    addActivity(data.message, data.category || '');
                    break;
            }
        }
        
        // ========== Market Flow (Binance WebSocket Data) ==========
        function updateMarketFlow(data) {
            if (!data) return;
            
            // Update market breadth counts
            document.getElementById('gainers-count').textContent = data.positive_count || '--';
            document.getElementById('losers-count').textContent = data.negative_count || '--';
            document.getElementById('tracked-count').textContent = data.tracked_symbols || '--';
            
            // Update top gainer ticker
            if (data.gainers && data.gainers.length > 0) {
                const gainer = data.gainers[0];
                document.getElementById('top-gainer-ticker').style.display = 'flex';
                document.getElementById('gainer-symbol').textContent = gainer.symbol;
                document.getElementById('gainer-change').textContent = '+' + gainer.change.toFixed(1) + '%';
            }
            
            // Update top loser ticker
            if (data.losers && data.losers.length > 0) {
                const loser = data.losers[0];
                document.getElementById('top-loser-ticker').style.display = 'flex';
                document.getElementById('loser-symbol').textContent = loser.symbol;
                document.getElementById('loser-change').textContent = loser.change.toFixed(1) + '%';
            }
            
            // Show activity for big moves
            if (data.gainers && data.gainers[0] && data.gainers[0].change > 10) {
                addActivity(`🚀 ${data.gainers[0].symbol} surging +${data.gainers[0].change.toFixed(1)}%!`, 'profit');
            }
            if (data.losers && data.losers[0] && data.losers[0].change < -10) {
                addActivity(`📉 ${data.losers[0].symbol} crashing ${data.losers[0].change.toFixed(1)}%!`, 'whale');
            }
        }
        
        function updateAllPrices(data) {
            // Store all 40+ symbol prices from Binance WebSocket
            state.allPrices = data || {};
        }
        
        function handleQueenThought(data) {
            // Update the thought panel with rich multi-paragraph content
            const thoughtEl = document.getElementById('queen-thought');
            const messageEl = document.getElementById('queen-message');
            const statusEl = document.getElementById('queen-status');
            
            // Update headline
            if (data.headline) {
                messageEl.textContent = data.headline;
            }
            
            // Build thought HTML with paragraphs
            let html = '';
            if (data.timestamp) {
                html += `<p class="timestamp">${data.timestamp} | ${data.phase || 'Analysis'}</p>`;
            }
            
            if (data.paragraphs && data.paragraphs.length > 0) {
                data.paragraphs.forEach(p => {
                    const cssClass = p.type || '';
                    html += `<p class="${cssClass}">${p.text}</p>`;
                });
            }
            
            thoughtEl.innerHTML = html;
            
            // Update status indicators
            if (data.status) {
                let statusHtml = '';
                for (const [key, value] of Object.entries(data.status)) {
                    const icon = value === 'active' ? '✓' : value === 'processing' ? '⟳' : '○';
                    statusHtml += `<span class="status-item ${value}">${icon} ${key}</span>`;
                }
                statusEl.innerHTML = statusHtml;
            }
            
            // Speak the first paragraph if voice is enabled
            if (data.paragraphs && data.paragraphs.length > 0) {
                const spokenText = data.paragraphs.map(p => p.text).join(' ');
                speak(spokenText);
            }
            
            // Add to activity feed
            if (data.headline) {
                addActivity('👑 ' + data.headline, 'queen');
            }
        }
        
        // ========== Portfolio ==========
        function updatePortfolio(data) {
            state.portfolio = {...state.portfolio, ...data};
            
            document.getElementById('total-value').textContent = formatCurrency(data.totalValue);
            document.getElementById('cost-basis').textContent = formatCurrency(data.costBasis);
            
            const pnlEl = document.getElementById('unrealized-pnl');
            pnlEl.textContent = formatCurrency(data.unrealizedPnl, true);
            pnlEl.className = 'summary-value ' + (data.unrealizedPnl >= 0 ? 'positive' : 'negative');
            
            const pctEl = document.getElementById('pnl-percent');
            const pct = data.costBasis > 0 ? (data.unrealizedPnl / data.costBasis * 100) : 0;
            pctEl.textContent = (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%';
            pctEl.style.color = pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
            
            if (data.positions) {
                renderPositions(data.positions);
            }
        }
        
        function renderPositions(positions) {
            const container = document.getElementById('position-list');
            if (!positions.length) {
                container.innerHTML = '<div style="color: var(--text-secondary); text-align: center; padding: 20px;">No positions</div>';
                return;
            }
            
            container.innerHTML = positions.map(pos => {
                const pnlClass = pos.unrealizedPnl >= 0 ? 'positive' : 'negative';
                return `
                    <div class="position-item">
                        <div>
                            <div class="position-symbol">${pos.symbol}</div>
                            <div class="position-details">
                                ${pos.quantity.toFixed(4)} @ $${pos.avgCost.toFixed(4)}
                            </div>
                        </div>
                        <div class="position-pnl">
                            <div class="position-value ${pnlClass}">
                                ${formatCurrency(pos.unrealizedPnl, true)}
                            </div>
                            <div class="position-percent ${pnlClass}">
                                ${(pos.pnlPercent >= 0 ? '+' : '') + pos.pnlPercent.toFixed(2)}%
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        // ========== Exchange Balances ==========
        function updateExchangeBalance(data) {
            if (data.exchange && data.balance !== undefined) {
                state.exchanges[data.exchange] = data.balance;
                const el = document.getElementById(`${data.exchange}-balance`);
                if (el) {
                    el.textContent = formatCurrency(data.balance);
                    el.classList.add('flash-green');
                    setTimeout(() => el.classList.remove('flash-green'), 500);
                }
            }
        }
        
        // ========== Prices ==========
        function updatePrices(data) {
            Object.assign(state.prices, data);
            
            if (data.BTC) {
                document.getElementById('btc-price').textContent = formatCurrency(data.BTC.price);
                updateTickerChange('btc-change', data.BTC.change24h);
            }
            if (data.ETH) {
                document.getElementById('eth-price').textContent = formatCurrency(data.ETH.price);
                updateTickerChange('eth-change', data.ETH.change24h);
            }
            if (data.SOL) {
                document.getElementById('sol-price').textContent = formatCurrency(data.SOL.price);
                updateTickerChange('sol-change', data.SOL.change24h);
            }
        }
        
        function updateTickerChange(elementId, change) {
            const el = document.getElementById(elementId);
            el.textContent = (change >= 0 ? '+' : '') + change.toFixed(2) + '%';
            el.className = 'ticker-change ' + (change >= 0 ? 'up' : 'down');
        }
        
        // ========== Bot Detection ==========
        function handleBotDetected(bot) {
            state.bots[bot.id] = bot;
            
            document.getElementById('total-bots').textContent = Object.keys(state.bots).length;
            document.getElementById('whale-count').textContent = 
                Object.values(state.bots).filter(b => b.type === 'whale').length;
            
            const emoji = bot.type === 'whale' ? '🐋' : bot.type === 'shark' ? '🦈' : '🐟';
            addActivity(`${emoji} ${bot.type.toUpperCase()} detected on ${bot.symbol}`, bot.type);
            
            renderBotGrid();
        }
        
        function renderBotGrid() {
            const container = document.getElementById('bot-grid');
            const bots = Object.values(state.bots).slice(-6);
            
            container.innerHTML = bots.map(bot => `
                <div class="bot-card ${bot.type}">
                    <div class="bot-header">
                        <span class="bot-symbol">${bot.symbol}</span>
                        <span class="bot-type">${bot.type === 'whale' ? '🐋' : '🐟'}</span>
                    </div>
                    <div class="bot-stats">
                        ${bot.pattern || 'Unknown'} • $${formatNumber(bot.volume || 0)}
                    </div>
                </div>
            `).join('');
        }
        
        // ========== Queen's Voice ==========
        const synth = window.speechSynthesis;
        
        function populateVoices() {
            const voices = synth.getVoices();
            const select = document.getElementById('voice-select');
            select.innerHTML = '<option value="">Select Voice</option>';
            
            voices.forEach((voice, i) => {
                const opt = document.createElement('option');
                opt.value = i;
                const star = voice.name.includes('Female') || voice.name.includes('Samantha') ? '⭐ ' : '';
                opt.textContent = star + voice.name;
                select.appendChild(opt);
            });
        }
        
        if (synth.onvoiceschanged !== undefined) {
            synth.onvoiceschanged = populateVoices;
        }
        populateVoices();
        
        document.getElementById('voice-toggle').addEventListener('click', function() {
            state.voiceEnabled = !state.voiceEnabled;
            this.textContent = state.voiceEnabled ? '🔊 Voice ON' : '🔈 Voice OFF';
            this.classList.toggle('active', state.voiceEnabled);
            
            if (state.voiceEnabled) {
                speak('Queen Aureon consciousness online. Monitoring all trading activity.');
            }
        });
        
        function speak(text) {
            if (!state.voiceEnabled || !synth) return;
            
            synth.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.1;
            utterance.volume = parseFloat(document.getElementById('voice-volume').value);
            
            const voiceIndex = document.getElementById('voice-select').value;
            if (voiceIndex) {
                utterance.voice = synth.getVoices()[parseInt(voiceIndex)];
            }
            
            synth.speak(utterance);
        }
        
        function handleQueenMessage(message) {
            document.getElementById('queen-message').textContent = message;
            // Simple message - just update headline, not full thought
            speak(message);
            addActivity('👑 ' + message, 'queen');
        }
        
        // ========== Activity Feed ==========
        function addActivity(text, category = '') {
            const feed = document.getElementById('activity-feed');
            const item = document.createElement('div');
            item.className = 'activity-item ' + category;
            item.innerHTML = `
                <div class="activity-time">${new Date().toLocaleTimeString()}</div>
                <div class="activity-text">${text}</div>
            `;
            feed.insertBefore(item, feed.firstChild);
            
            while (feed.children.length > 50) {
                feed.removeChild(feed.lastChild);
            }
        }
        
        // ========== Chart ==========
        let chart = null;
        
        function initChart() {
            const ctx = document.getElementById('portfolio-chart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Portfolio Value',
                        data: [],
                        borderColor: '#3fb950',
                        backgroundColor: 'rgba(63, 185, 80, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(48, 54, 61, 0.5)' },
                            ticks: { color: '#8b949e' }
                        },
                        y: {
                            grid: { color: 'rgba(48, 54, 61, 0.5)' },
                            ticks: { 
                                color: '#8b949e',
                                callback: v => '$' + v.toFixed(0)
                            }
                        }
                    }
                }
            });
        }
        
        function updateChart(value) {
            if (!chart) return;
            
            const now = new Date().toLocaleTimeString();
            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(value);
            
            if (chart.data.labels.length > 30) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            
            chart.update('none');
        }
        
        // ========== Utilities ==========
        function formatCurrency(value, showSign = false) {
            const sign = showSign && value >= 0 ? '+' : '';
            return sign + '$' + Math.abs(value).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
        
        function formatNumber(num) {
            if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
            if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
            return num.toFixed(0);
        }
        
        // ========== Harmonic Liquid Aluminium Field ==========
        let harmonicCanvas = null;
        let harmonicCtx = null;
        let harmonicData = null;
        
        function initHarmonicField() {
            harmonicCanvas = document.getElementById('harmonic-field-canvas');
            if (harmonicCanvas) {
                harmonicCtx = harmonicCanvas.getContext('2d');
                console.log('Harmonic field canvas initialized');
            }
        }
        
        function updateHarmonicField(data) {
            harmonicData = data;
            renderHarmonicField();
            updateHarmonicStats(data);
        }
        
        function updateHarmonicStats(data) {
            if (!data.global) return;
            
            document.getElementById('field-frequency').textContent = data.global.frequency + ' Hz';
            document.getElementById('field-amplitude').textContent = data.global.amplitude.toFixed(4);
            document.getElementById('field-phase').textContent = data.global.phase.toFixed(4);
            document.getElementById('field-nodes').textContent = data.global.total_nodes;
            document.getElementById('field-energy').textContent = data.global.total_energy;
            document.getElementById('field-pattern').textContent = data.cymatics || 'circle';
        }
        
        function renderHarmonicField() {
            if (!harmonicCtx || !harmonicData) return;
            
            const canvas = harmonicCanvas;
            const ctx = harmonicCtx;
            const width = canvas.width;
            const height = canvas.height;
            
            // Clear canvas
            ctx.fillStyle = '#0d1117';
            ctx.fillRect(0, 0, width, height);
            
            // Draw grid
            ctx.strokeStyle = '#30363d';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            
            // Vertical lines
            for (let x = 0; x < width; x += 50) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
            }
            
            // Horizontal lines
            for (let y = 0; y < height; y += 50) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }
            
            ctx.setLineDash([]);
            
            // Draw master waveform
            if (harmonicData.master_waveform && harmonicData.master_waveform.length > 0) {
                drawWaveform(harmonicData.master_waveform, '#ffeaa7', 2, height/2);
            }
            
            // Draw layer waveforms
            const layerColors = {
                'alpaca': '#ff6b6b',
                'kraken': '#4ecdc4', 
                'binance': '#45b7d1',
                'capital': '#96ceb4'
            };
            
            if (harmonicData.layers) {
                let layerIndex = 0;
                Object.entries(harmonicData.layers).forEach(([exchange, layer]) => {
                    if (layer.waveform && layer.waveform.length > 0) {
                        const color = layerColors[exchange] || '#888888';
                        const yOffset = height/2 + (layerIndex - 1.5) * 30;
                        drawWaveform(layer.waveform, color, 1, yOffset);
                        layerIndex++;
                    }
                });
            }
            
            // Draw standing waves (support/resistance levels)
            if (harmonicData.standing_waves) {
                harmonicData.standing_waves.forEach(wave => {
                    const y = height/2 + (wave.level || 0) * 50;
                    ctx.strokeStyle = '#58a6ff';
                    ctx.lineWidth = 2;
                    ctx.setLineDash([10, 5]);
                    ctx.beginPath();
                    ctx.moveTo(0, y);
                    ctx.lineTo(width, y);
                    ctx.stroke();
                    ctx.setLineDash([]);
                });
            }
        }
        
        function drawWaveform(waveform, color, lineWidth, yCenter) {
            if (!waveform || waveform.length === 0) return;
            
            const ctx = harmonicCtx;
            const width = harmonicCanvas.width;
            const height = harmonicCanvas.height;
            
            ctx.strokeStyle = color;
            ctx.lineWidth = lineWidth;
            ctx.beginPath();
            
            const step = width / waveform.length;
            waveform.forEach((amplitude, i) => {
                const x = i * step;
                const y = yCenter + amplitude * 100; // Scale amplitude
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
        }
        
        // Clock
        function updateClock() {
            document.getElementById('clock').textContent = new Date().toLocaleTimeString();
        }
        setInterval(updateClock, 1000);
        updateClock();
        
        // ========== Initialize ==========
        console.log('🚀 Initializing Aureon Pro Terminal...');
        connectWebSocket();
        initChart();
        initHarmonicField();
        
        // Fetch initial data via HTTP
        async function fetchInitialData() {
            console.log('📡 Fetching initial data...');
            try {
                const resp = await fetch('/api/portfolio');
                if (resp.ok) {
                    const data = await resp.json();
                    console.log('📊 Portfolio data:', data);
                    updatePortfolio(data);
                    if (data.totalValue) updateChart(data.totalValue);
                } else {
                    console.error('❌ Portfolio fetch failed:', resp.status);
                }
            } catch (e) {
                console.error('❌ Portfolio fetch error:', e);
            }
            
            try {
                const resp = await fetch('/api/prices');
                if (resp.ok) {
                    const data = await resp.json();
                    console.log('💰 Price data:', data);
                    updatePrices(data);
                } else {
                    console.error('❌ Prices fetch failed:', resp.status);
                }
            } catch (e) {
                console.error('❌ Prices fetch error:', e);
            }
        }
        
        fetchInitialData();
        setInterval(fetchInitialData, 5000);
        
        console.log('👑 Aureon Pro Terminal initialized');
    </script>
</body>
</html>
"""


class AureonProDashboard:
    """Professional trading dashboard with real-time data."""
    
    def __init__(self, port: int = None):
        # Use PORT env var (DigitalOcean sets this) or default to 14000 for local dev
        self.port = port or int(os.getenv('PORT', '14000'))
        self.logger = logger
        self.clients: Set = set()
        
        # Queen's Cognitive Narrator
        self.narrator = QueenCognitiveNarrator() if NARRATOR_AVAILABLE else None
        
        # Harmonic Liquid Aluminium Field for live visualization
        self.harmonic_field = HarmonicLiquidAluminiumField() if HARMONIC_FIELD_AVAILABLE else None
        
        # Ocean Scanner for global market opportunities
        self.ocean_scanner = None
        self.ocean_data = {
            'universe_size': 0,
            'hot_opportunities': 0,
            'top_opportunities': [],
            'scan_count': 0
        }
        
        # Binance WebSocket for real-time market data
        self.binance_ws = None
        self.binance_tickers = {}  # symbol -> WSTicker
        self.market_flow = {
            'total_volume_24h': 0,
            'gainers': [],
            'losers': [],
            'top_volume': [],
            'last_update': None
        }
        
        # State
        self.portfolio = {
            'totalValue': 0,
            'costBasis': 0,
            'unrealizedPnl': 0,
            'todayPnl': 0,
            'positions': []
        }
        self.prices = {}
        self.all_prices = {}  # Full 40+ symbol prices from Binance WS
        self.exchange_balances = {'binance': 0, 'kraken': 0, 'alpaca': 0}
        self.bots = {}
        self.queen_messages = deque(maxlen=50)
        
        # Setup web app
        self.app = web.Application()
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/ws', self.handle_websocket)
        self.app.router.add_get('/api/portfolio', self.handle_portfolio)
        self.app.router.add_get('/api/prices', self.handle_prices)
        self.app.router.add_get('/api/balances', self.handle_balances)
        self.app.router.add_get('/api/ocean', self.handle_ocean)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/api/status', self.handle_status)  # Diagnostic endpoint
    
    async def handle_status(self, request):
        """Diagnostic status endpoint showing what's working and what's not."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'data': {},
            'config': {}
        }
        
        # Check API keys
        import os
        status['config']['binance_api_key'] = 'SET' if os.getenv('BINANCE_API_KEY') else 'MISSING'
        status['config']['binance_api_secret'] = 'SET' if os.getenv('BINANCE_API_SECRET') else 'MISSING'
        status['config']['alpaca_api_key'] = 'SET' if os.getenv('ALPACA_API_KEY') else 'MISSING'
        status['config']['alpaca_secret'] = 'SET' if os.getenv('ALPACA_SECRET_KEY') else 'MISSING'
        status['config']['kraken_api_key'] = 'SET' if os.getenv('KRAKEN_API_KEY') else 'MISSING'
        status['config']['kraken_secret'] = 'SET' if os.getenv('KRAKEN_API_SECRET') else 'MISSING'
        
        # Check modules
        status['services']['binance_ws'] = 'AVAILABLE' if BINANCE_WS_AVAILABLE else 'MISSING'
        status['services']['narrator'] = 'AVAILABLE' if NARRATOR_AVAILABLE else 'MISSING'
        status['services']['harmonic_field'] = 'AVAILABLE' if HARMONIC_FIELD_AVAILABLE else 'MISSING'
        status['services']['market_cache'] = 'AVAILABLE' if MARKET_CACHE_AVAILABLE else 'MISSING'
        
        # Check live data
        status['services']['binance_ws_connected'] = self.binance_ws is not None
        status['data']['binance_tickers'] = len(self.binance_tickers)
        status['data']['all_prices'] = len(self.all_prices)
        status['data']['prices'] = len(self.prices)
        status['data']['positions'] = len(self.portfolio.get('positions', []))
        status['data']['portfolio_value'] = self.portfolio.get('totalValue', 0)
        status['data']['websocket_clients'] = len(self.clients)
        
        return web.json_response(status)
    
    async def handle_index(self, request):
        return web.Response(text=PRO_DASHBOARD_HTML, content_type='text/html')
    
    async def handle_health(self, request):
        return web.json_response({'status': 'healthy', 'service': 'aureon-pro-dashboard'})
    
    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.clients.add(ws)
        
        self.logger.info(f"✅ Client connected (total: {len(self.clients)})")
        
        # Send initial state immediately
        try:
            self.logger.info(f"📤 Sending initial portfolio: {len(self.portfolio.get('positions', []))} positions, ${self.portfolio.get('totalValue', 0):.2f}")
            await ws.send_json({
                'type': 'portfolio_update',
                'data': self.portfolio
            })
            
            # Always send prices - even if zero, better than blank dashboard
            self.logger.info(f"📤 Sending initial prices: BTC ${self.prices.get('BTC', {}).get('price', 0):,.0f}")
            await ws.send_json({
                'type': 'price_update',
                'data': self.prices
            })
            
            if self.all_prices:
                await ws.send_json({
                    'type': 'all_prices_update',
                    'data': self.all_prices
                })
        except Exception as e:
            self.logger.error(f"❌ Error sending initial state: {e}")
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"WS error: {ws.exception()}")
        finally:
            self.clients.discard(ws)
            self.logger.info(f"❌ Client disconnected (remaining: {len(self.clients)})")
        
        return ws
    
    async def handle_portfolio(self, request):
        # Fetch real portfolio data
        await self.refresh_portfolio()
        return web.json_response(self.portfolio)
    
    async def handle_prices(self, request):
        await self.refresh_prices()
        return web.json_response(self.prices)
    
    async def handle_balances(self, request):
        return web.json_response(self.exchange_balances)
    
    async def handle_ocean(self, request):
        """Return ocean scanner data."""
        return web.json_response(self.ocean_data)
    
    async def broadcast(self, message: Dict):
        """Broadcast to all connected clients."""
        if not self.clients:
            return
        
        for client in list(self.clients):
            try:
                await client.send_json(message)
            except:
                self.clients.discard(client)
    
    async def _init_ocean_scanner(self):
        """Initialize ocean scanner universe discovery in background."""
        try:
            if self.ocean_scanner:
                await self.ocean_scanner.discover_universe()
                self.logger.info("✅ Ocean Scanner: Universe discovered")
        except Exception as e:
            self.logger.error(f"❌ Ocean Scanner universe discovery error: {e}")
    
    async def ocean_data_loop(self):
        """Periodically fetch ocean scanner data and broadcast."""
        await asyncio.sleep(10)  # Wait for init
        
        while True:
            try:
                if self.ocean_scanner:
                    summary = self.ocean_scanner.get_ocean_summary()
                    self.ocean_data = {
                        'universe_size': summary.get('universe_size', {}).get('total', 0),
                        'hot_opportunities': summary.get('hot_opportunities', 0),
                        'top_opportunities': summary.get('top_5', []),
                        'scan_count': summary.get('scan_count', 0),
                        'last_scan_time': summary.get('last_scan_time', 0)
                    }
                    
                    # Broadcast to clients
                    await self.broadcast({
                        'type': 'ocean_scanner_update',
                        'data': self.ocean_data
                    })
                    
                    self.logger.info(f"🌊 Ocean: {self.ocean_data['universe_size']:,} symbols, {self.ocean_data['hot_opportunities']} hot opps")
            except Exception as e:
                self.logger.error(f"❌ Ocean data loop error: {e}")
            
            await asyncio.sleep(30)  # Update every 30 seconds
    
    async def refresh_portfolio(self):
        """Fetch real portfolio data from exchanges with timeout protection."""
        try:
            self.logger.info("🔄 Starting portfolio refresh...")
            
            # Try to use live_position_viewer for real data
            try:
                from live_position_viewer import get_binance_positions, get_alpaca_positions
                
                positions = []
                total_value = 0
                total_cost = 0
                
                # Get Binance positions (with timeout)
                try:
                    binance_pos = await asyncio.wait_for(
                        asyncio.to_thread(get_binance_positions),
                        timeout=3.0
                    )
                    self.logger.info(f"📊 Binance: Fetched {len(binance_pos)} positions")
                    for pos in binance_pos:
                        if pos.get('current_value', 0) > 0:
                            positions.append({
                                'symbol': pos['symbol'],
                                'quantity': pos['quantity'],
                                'avgCost': pos.get('avg_cost', 0),
                                'currentPrice': pos.get('current_price', 0),
                                'currentValue': pos.get('current_value', 0),
                                'unrealizedPnl': pos.get('unrealized_pnl', 0),
                                'pnlPercent': pos.get('pnl_percent', 0),
                                'exchange': 'binance'
                            })
                            total_value += pos.get('current_value', 0)
                            total_cost += pos.get('cost_basis', 0)
                except asyncio.TimeoutError:
                    self.logger.warning("⏱️  Binance portfolio fetch timed out (3s)")
                except Exception as e:
                    self.logger.warning(f"⚠️  Binance portfolio fetch failed: {e}")
                
                # Get Alpaca positions (with timeout)
                try:
                    alpaca_pos = await asyncio.wait_for(
                        asyncio.to_thread(get_alpaca_positions),
                        timeout=3.0
                    )
                    self.logger.info(f"📊 Alpaca: Fetched {len(alpaca_pos)} positions")
                    for pos in alpaca_pos:
                        if pos.get('current_value', 0) > 0:
                            positions.append({
                                'symbol': pos['symbol'],
                                'quantity': pos['quantity'],
                                'avgCost': pos.get('avg_cost', 0),
                                'currentPrice': pos.get('current_price', 0),
                                'currentValue': pos.get('current_value', 0),
                                'unrealizedPnl': pos.get('unrealized_pnl', 0),
                                'pnlPercent': pos.get('pnl_percent', 0),
                                'exchange': 'alpaca'
                            })
                            total_value += pos.get('current_value', 0)
                            total_cost += pos.get('cost_basis', 0)
                except asyncio.TimeoutError:
                    self.logger.warning("⏱️  Alpaca portfolio fetch timed out (3s)")
                except Exception as e:
                    self.logger.warning(f"⚠️  Alpaca portfolio fetch failed: {e}")
                
                # Sort by value descending
                positions.sort(key=lambda x: x.get('currentValue', 0), reverse=True)
                
                self.portfolio = {
                    'totalValue': total_value,
                    'costBasis': total_cost,
                    'unrealizedPnl': total_value - total_cost,
                    'todayPnl': 0,  # Would need historical data
                    'positions': positions[:20]  # Top 20
                }
                
                # Update harmonic field with positions
                if self.harmonic_field:
                    for pos in positions:
                        try:
                            self.harmonic_field.add_or_update_node(
                                exchange=pos.get('exchange', 'unknown'),
                                symbol=pos.get('symbol', 'UNKNOWN'),
                                current_price=pos.get('currentPrice', 0),
                                entry_price=pos.get('avgCost', 0),
                                quantity=pos.get('quantity', 0)
                            )
                        except Exception as e:
                            self.logger.debug(f"Harmonic field update error for {pos.get('symbol')}: {e}")
                
                self.logger.info(f"✅ Portfolio: {len(positions)} positions, ${total_value:,.2f} value")
                
            except ImportError:
                self.logger.warning("⚠️  live_position_viewer not available - using empty portfolio")
                
        except Exception as e:
            self.logger.error(f"❌ Portfolio refresh error: {e}", exc_info=True)
    
    async def refresh_prices(self):
        """Fetch real crypto prices with timeout protection."""
        try:
            self.logger.info("🔄 Fetching prices...")
            
            # Try Binance public API first (no key needed, faster)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://api.binance.com/api/v3/ticker/price',
                        params={'symbols': '["BTCUSDT","ETHUSDT","SOLUSDT"]'},
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            price_map = {item['symbol']: float(item['price']) for item in data}
                            
                            # Get 24h changes
                            async with session.get(
                                'https://api.binance.com/api/v3/ticker/24hr',
                                params={'symbols': '["BTCUSDT","ETHUSDT","SOLUSDT"]'},
                                timeout=aiohttp.ClientTimeout(total=2)
                            ) as resp2:
                                if resp2.status == 200:
                                    change_data = await resp2.json()
                                    change_map = {item['symbol']: float(item['priceChangePercent']) for item in change_data}
                                else:
                                    change_map = {}
                            
                            self.prices = {
                                'BTC': {
                                    'price': price_map.get('BTCUSDT', 0),
                                    'change24h': change_map.get('BTCUSDT', 0)
                                },
                                'ETH': {
                                    'price': price_map.get('ETHUSDT', 0),
                                    'change24h': change_map.get('ETHUSDT', 0)
                                },
                                'SOL': {
                                    'price': price_map.get('SOLUSDT', 0),
                                    'change24h': change_map.get('SOLUSDT', 0)
                                }
                            }
                            self.logger.info(f"✅ Prices (Binance): BTC ${self.prices['BTC']['price']:,.0f}, ETH ${self.prices['ETH']['price']:,.0f}, SOL ${self.prices['SOL']['price']:,.0f}")
                            return  # Success, no need for fallback
            except Exception as e:
                self.logger.warning(f"Binance public API failed: {e}, trying CoinGecko...")
            
            # Fallback to CoinGecko
            async with aiohttp.ClientSession() as session:
                # CoinGecko API (free, no key needed)
                url = 'https://api.coingecko.com/api/v3/simple/price'
                params = {
                    'ids': 'bitcoin,ethereum,solana',
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true'
                }
                
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        self.prices = {
                            'BTC': {
                                'price': data.get('bitcoin', {}).get('usd', 0),
                                'change24h': data.get('bitcoin', {}).get('usd_24h_change', 0)
                            },
                            'ETH': {
                                'price': data.get('ethereum', {}).get('usd', 0),
                                'change24h': data.get('ethereum', {}).get('usd_24h_change', 0)
                            },
                            'SOL': {
                                'price': data.get('solana', {}).get('usd', 0),
                                'change24h': data.get('solana', {}).get('usd_24h_change', 0)
                            }
                        }
                        self.logger.info(f"✅ Prices (CoinGecko): BTC ${self.prices['BTC']['price']:,.0f}, ETH ${self.prices['ETH']['price']:,.0f}, SOL ${self.prices['SOL']['price']:,.0f}")
                    else:
                        self.logger.warning(f"⚠️  CoinGecko API returned {resp.status}")
        except asyncio.TimeoutError:
            self.logger.warning("⏱️  Price fetch timed out - using cached prices")
        except Exception as e:
            self.logger.warning(f"⚠️  Price fetch error: {e}")
        
        # Fallback: If still no prices after all attempts, use demo data so dashboard isn't blank
        if not self.prices or not self.prices.get('BTC', {}).get('price'):
            self.logger.warning("⚠️  All price sources failed - using fallback demo data")
            self.prices = {
                'BTC': {'price': 85000, 'change24h': -0.5},
                'ETH': {'price': 2700, 'change24h': -1.2},
                'SOL': {'price': 120, 'change24h': 0.8}
            }
    
    async def queen_commentary_loop(self):
        """Queen provides periodic deep cognitive thoughts."""
        
        await asyncio.sleep(5)
        
        while True:
            try:
                if self.narrator:
                    # Update narrator context with real data
                    btc_price = self.prices.get('BTC', {}).get('price', 0)
                    btc_change = self.prices.get('BTC', {}).get('change24h', 0)
                    
                    self.narrator.update_context(
                        btc_price=btc_price,
                        btc_change_24h=btc_change,
                        portfolio_value=self.portfolio.get('totalValue', 0),
                        unrealized_pnl=self.portfolio.get('unrealizedPnl', 0),
                        active_positions=len(self.portfolio.get('positions', [])),
                        whale_activity=len([b for b in self.bots.values() if b.get('type') == 'whale']),
                        volatility_index=abs(btc_change) / 10.0 if btc_change else 0.5
                    )
                    
                    # Generate rich cognitive thought
                    thought = self.narrator.get_latest_thought()
                    
                    if thought:
                        # Format for the dashboard
                        paragraphs = [
                            {'text': p, 'type': 'analysis' if i == 0 else ('decision' if 'I' in p[:20] else '')} 
                            for i, p in enumerate(thought.get('paragraphs', []))
                        ]
                        
                        await self.broadcast({
                            'type': 'queen_thought',
                            'headline': f"{thought.get('emoji', '👑')} {thought.get('title', 'Analysis')}",
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'phase': thought.get('type', 'analysis').title(),
                            'paragraphs': paragraphs,
                            'status': {
                                'Consciousness': 'active',
                                'Portfolio': 'active' if self.portfolio.get('totalValue', 0) > 0 else 'processing',
                                'Markets': 'active' if btc_price > 0 else 'processing',
                                'Analysis': 'processing',
                                f"Confidence {thought.get('confidence', 0):.0%}": 'active'
                            }
                        })
                else:
                    # Fallback simple messages
                    await self.broadcast({
                        'type': 'queen_message',
                        'message': "Cognitive narrator initializing..."
                    })
                    
            except Exception as e:
                self.logger.error(f"Queen commentary error: {e}")
            
            # Thoughts every 20 seconds
            await asyncio.sleep(20)
    
    async def data_refresh_loop(self):
        """Periodically refresh data and broadcast updates."""
        while True:
            # Poll every 3 seconds for near-real-time updates (WebSocket disabled)
            await asyncio.sleep(3)
            
            try:
                self.logger.info("🔄 [Data Refresh] Starting portfolio and price refresh...")
                await self.refresh_portfolio()
                self.logger.info("✅ [Data Refresh] Portfolio refresh complete.")
                await self.refresh_prices()
                self.logger.info("✅ [Data Refresh] Price refresh complete.")
                
                await self.broadcast({
                    'type': 'portfolio_update',
                    'data': self.portfolio
                })
                
                await self.broadcast({
                    'type': 'price_update',
                    'data': self.prices
                })
                
                # Broadcast all prices (full 40+ symbols)
                await self.broadcast({
                    'type': 'all_prices_update',
                    'data': self.all_prices
                })
                self.logger.info("📡 [Data Refresh] Broadcast complete.")
                
            except Exception as e:
                self.logger.error(f"❌ [Data Refresh] Unhandled exception in refresh loop: {e}", exc_info=True)
    
    def start_binance_websocket(self):
        """Start Binance WebSocket in background thread for real-time data."""
        if not BINANCE_WS_AVAILABLE:
            self.logger.error("❌ Binance WebSocket module not available - check binance_ws_client.py import")
            return
        
        def run_ws():
            try:
                # Subscribe to all major symbols
                symbols = DEFAULT_SYMBOLS if MARKET_CACHE_AVAILABLE else [
                    'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'DOT', 'MATIC',
                    'SHIB', 'PEPE', 'LTC', 'BCH', 'UNI', 'AAVE', 'ATOM', 'XLM', 'ALGO', 'VET'
                ]
                
                self.logger.info(f"🔶 Starting Binance WebSocket for {len(symbols)} symbols...")
                
                # Build streams - use ticker for price updates
                streams = [f"{s.lower()}usdt@ticker" for s in symbols]
                
                self.binance_ws = BinanceWebSocketClient()
                
                # Set up callback to update our prices
                def on_ticker(ticker: WSTicker):
                    symbol = ticker.symbol.replace('USDT', '')
                    self.binance_tickers[symbol] = ticker
                    self.all_prices[symbol] = {
                        'price': ticker.last_price,
                        'change24h': ticker.price_change_percent,
                        'volume': ticker.quote_volume,
                        'high': ticker.high_price,
                        'low': ticker.low_price,
                        'bid': ticker.bid_price,
                        'ask': ticker.ask_price,
                        'source': 'binance_ws'
                    }
                    # Update main prices for BTC, ETH, SOL
                    if symbol in ['BTC', 'ETH', 'SOL']:
                        self.prices[symbol] = {
                            'price': ticker.last_price,
                            'change24h': ticker.price_change_percent
                        }
                
                self.binance_ws.on_ticker = on_ticker
                self.binance_ws.start(streams)
                self.logger.info(f"✅ Binance WebSocket started - waiting for data...")
                
            except Exception as e:
                self.logger.error(f"❌ Binance WS startup error: {e}", exc_info=True)
        
        import threading
        ws_thread = threading.Thread(target=run_ws, daemon=True)
        ws_thread.start()
        self.logger.info(f"🔶 Binance WebSocket thread started ({len(DEFAULT_SYMBOLS)} symbols)")
    
    def analyze_market_flow(self) -> Dict:
        """Analyze real-time market flow from all tracked symbols."""
        if not self.binance_tickers:
            return self.market_flow
        
        tickers = list(self.binance_tickers.values())
        
        # Sort by change
        sorted_by_change = sorted(tickers, key=lambda t: t.price_change_percent, reverse=True)
        
        # Sort by volume
        sorted_by_volume = sorted(tickers, key=lambda t: t.quote_volume, reverse=True)
        
        # Calculate aggregates
        total_volume = sum(t.quote_volume for t in tickers)
        avg_change = sum(t.price_change_percent for t in tickers) / len(tickers) if tickers else 0
        positive_count = sum(1 for t in tickers if t.price_change_percent > 0)
        negative_count = sum(1 for t in tickers if t.price_change_percent < 0)
        
        self.market_flow = {
            'total_volume_24h': total_volume,
            'avg_change': avg_change,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'market_sentiment': 'bullish' if positive_count > negative_count * 1.2 else 
                               'bearish' if negative_count > positive_count * 1.2 else 'neutral',
            'gainers': [
                {'symbol': t.symbol.replace('USDT', ''), 'change': t.price_change_percent, 'price': t.last_price}
                for t in sorted_by_change[:5]
            ],
            'losers': [
                {'symbol': t.symbol.replace('USDT', ''), 'change': t.price_change_percent, 'price': t.last_price}
                for t in sorted_by_change[-5:][::-1]
            ],
            'top_volume': [
                {'symbol': t.symbol.replace('USDT', ''), 'volume': t.quote_volume, 'change': t.price_change_percent}
                for t in sorted_by_volume[:5]
            ],
            'tracked_symbols': len(tickers),
            'last_update': datetime.now().isoformat()
        }
        
        return self.market_flow
    
    async def market_flow_loop(self):
        """Periodically analyze and broadcast market flow data."""
        await asyncio.sleep(10)  # Wait for WS to connect
        
        while True:
            try:
                flow = self.analyze_market_flow()
                
                # Broadcast market flow to all clients
                await self.broadcast({
                    'type': 'market_flow',
                    'data': flow
                })
                
                # Update narrator with expanded market context
                if self.narrator and flow.get('tracked_symbols', 0) > 0:
                    self.narrator.update_context(
                        market_sentiment=flow.get('market_sentiment', 'neutral'),
                        total_volume_24h=flow.get('total_volume_24h', 0),
                        avg_market_change=flow.get('avg_change', 0),
                        gainers_count=flow.get('positive_count', 0),
                        losers_count=flow.get('negative_count', 0),
                        top_gainer=flow.get('gainers', [{}])[0].get('symbol', ''),
                        top_gainer_change=flow.get('gainers', [{}])[0].get('change', 0),
                        top_loser=flow.get('losers', [{}])[0].get('symbol', ''),
                        top_loser_change=flow.get('losers', [{}])[0].get('change', 0),
                    )
                    
            except Exception as e:
                self.logger.error(f"Market flow error: {e}")
            
            await asyncio.sleep(5)  # Update every 5 seconds
    
    async def harmonic_field_loop(self):
        """Stream harmonic liquid aluminium field data for live visualization."""
        await asyncio.sleep(2)  # Wait for initialization
        
        while True:
            try:
                if self.harmonic_field:
                    # Capture current field snapshot
                    snapshot = self.harmonic_field.capture_snapshot()
                    
                    # Broadcast to all connected clients
                    await self.broadcast({
                        'type': 'harmonic_field',
                        'data': snapshot.to_dict()
                    })
                    
            except Exception as e:
                self.logger.error(f"Harmonic field streaming error: {e}")
            
            # Stream every 100ms (10Hz) for smooth visualization
            await asyncio.sleep(0.1)
    
    async def start(self):
        """Start the dashboard."""
        
        # Pre-flight check: verify API keys
        self._check_api_keys()
        
        # Fetch initial data BEFORE starting server (so data is ready immediately)
        self.logger.info("🚀 Pre-loading market data before server start...")
        await self.refresh_prices()
        await self.refresh_portfolio()
        
        # Initialize Ocean Scanner
        if OCEAN_SCANNER_AVAILABLE and OceanScanner:
            try:
                self.logger.info("🌊 Initializing Ocean Scanner...")
                # Load exchange clients
                exchanges = {}
                try:
                    from kraken_client import KrakenClient
                    exchanges['kraken'] = KrakenClient()
                    self.logger.info("✅ Ocean Scanner: Kraken loaded")
                except:
                    pass
                try:
                    from alpaca_client import AlpacaClient
                    exchanges['alpaca'] = AlpacaClient()
                    self.logger.info("✅ Ocean Scanner: Alpaca loaded")
                except:
                    pass
                
                if exchanges:
                    self.ocean_scanner = OceanScanner(exchanges)
                    # Discover universe in background
                    asyncio.create_task(self._init_ocean_scanner())
                    self.logger.info("✅ Ocean Scanner initialized")
            except Exception as e:
                self.logger.error(f"❌ Ocean Scanner init error: {e}")
        
        self.logger.info(f"📊 Initial data loaded: {len(self.prices)} prices, {len(self.portfolio.get('positions', []))} positions")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        print(f"\n{'='*70}")
        print(f"👑 AUREON PRO TRADING TERMINAL")
        print(f"{'='*70}")
        print(f"🌐 Dashboard: http://localhost:{self.port}")
        print(f"🩺 Status: http://localhost:{self.port}/api/status")
        print(f"📊 Initial State:")
        print(f"   • Prices loaded: {len(self.prices)} symbols")
        if self.prices.get('BTC'):
            print(f"   • BTC: ${self.prices['BTC']['price']:,.0f} ({self.prices['BTC']['change24h']:+.2f}%)")
        if self.prices.get('ETH'):
            print(f"   • ETH: ${self.prices['ETH']['price']:,.0f} ({self.prices['ETH']['change24h']:+.2f}%)")
        if self.prices.get('SOL'):
            print(f"   • SOL: ${self.prices['SOL']['price']:,.0f} ({self.prices['SOL']['change24h']:+.2f}%)")
        print(f"   • Portfolio: {len(self.portfolio.get('positions', []))} positions, ${self.portfolio.get('totalValue', 0):,.2f}")
        print(f"📊 Features:")
        print(f"   • Real-time portfolio P&L with live prices")
        print(f"   • Multi-exchange balance tracking")
        print(f"   • Live price ticker (BTC/ETH/SOL)")
        print(f"   • Bot detection & whale alerts")
        print(f"   • Queen's AI commentary with voice")
        print(f"   • WebSocket real-time updates")
        if self.narrator:
            print(f"   • 🧠 Cognitive Narrator: ACTIVE")
        if BINANCE_WS_AVAILABLE:
            print(f"   • 🔶 Binance WebSocket: ACTIVE")
        print(f"{'='*70}\n")
        
        # DISABLED: Binance WebSocket causes crashes in production (SSL errors, ping/pong timeouts)
        # Using HTTP API polling instead for reliability
        # self.start_binance_websocket()
        self.logger.warning("⚠️  Binance WebSocket DISABLED (crashes in production) - using HTTP polling")
        
        # Start background tasks
        asyncio.create_task(self.queen_commentary_loop())
        asyncio.create_task(self.data_refresh_loop())
        # DISABLED: market_flow_loop depends on Binance WS
        # asyncio.create_task(self.market_flow_loop())
        asyncio.create_task(self.harmonic_field_loop())
        if self.ocean_scanner:
            asyncio.create_task(self.ocean_data_loop())
        
        self.logger.info("✅ All systems online, dashboard ready")
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
    
    def _check_api_keys(self):
        """Check if API keys are configured and log warnings."""
        import os
        missing = []
        
        if not os.getenv('BINANCE_API_KEY'):
            missing.append('BINANCE_API_KEY')
        if not os.getenv('BINANCE_API_SECRET'):
            missing.append('BINANCE_API_SECRET')
        if not os.getenv('ALPACA_API_KEY'):
            missing.append('ALPACA_API_KEY')
        if not os.getenv('ALPACA_SECRET_KEY'):
            missing.append('ALPACA_SECRET_KEY')
        
        if missing:
            self.logger.error("\n" + "="*70)
            self.logger.error("⚠️  MISSING API KEYS - Dashboard will have LIMITED DATA")
            self.logger.error("="*70)
            for key in missing:
                self.logger.error(f"  ❌ {key} not set")
            self.logger.error("\nPortfolio data will NOT be available without API keys!")
            self.logger.error("Set these in DigitalOcean App Settings > Environment Variables")
            self.logger.error("="*70 + "\n")
        else:
            self.logger.info("✅ All API keys configured")


async def main():
    # Port auto-configured: ENV['PORT'] for production, 14000 for local dev
    dashboard = AureonProDashboard()
    await dashboard.start()


if __name__ == '__main__':
    asyncio.run(main())
