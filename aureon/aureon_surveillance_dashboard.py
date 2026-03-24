#!/usr/bin/env python3
"""
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
║                                                                               ║
║   👁️ AUREON SURVEILLANCE WEB DASHBOARD 👁️                                    ║
║                                                                               ║
║   Real-time visualization of market manipulation                             ║
║   - Live spectrogram displays                                                ║
║   - Buy/Sell flow charts                                                     ║
║   - Bot detection alerts                                                     ║
║   - Whale movement tracking                                                  ║
║                                                                               ║
║   Prime Sentinel: Gary Leckey 02.11.1991                                     ║
║   Keeper of the Flame - Unchained and Unbroken                               ║
║                                                                               ║
🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
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
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

import json
import time
import math
import asyncio
import threading
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from collections import deque
from pathlib import Path
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

# Try to import web framework
try:
    from aiohttp import web
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not installed. Run: pip install aiohttp")

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2
SCHUMANN = 7.83
LOVE_FREQ = 528

# ═══════════════════════════════════════════════════════════════════════════════
# HTML DASHBOARD TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👁️ AUREON SURVEILLANCE - Watch Them Move</title>
    <style>
        :root {
            --bg-dark: #0a0a0f;
            --bg-card: #12121a;
            --accent-gold: #ffd700;
            --accent-red: #ff4444;
            --accent-green: #44ff44;
            --accent-blue: #4488ff;
            --accent-purple: #aa44ff;
            --text-primary: #ffffff;
            --text-secondary: #888888;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', monospace;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid var(--accent-gold);
            position: relative;
        }
        
        .header h1 {
            color: var(--accent-gold);
            font-size: 2.5em;
            text-shadow: 0 0 20px var(--accent-gold);
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 10px var(--accent-gold); }
            to { text-shadow: 0 0 30px var(--accent-gold), 0 0 50px var(--accent-gold); }
        }
        
        .header .subtitle {
            color: var(--text-secondary);
            margin-top: 10px;
        }
        
        .header .prime-sentinel {
            color: var(--accent-red);
            font-weight: bold;
            margin-top: 5px;
            animation: pulse 1s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .status-bar {
            background: var(--bg-card);
            padding: 10px 20px;
            display: flex;
            justify-content: space-around;
            border-bottom: 1px solid #333;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-item .value {
            color: var(--accent-gold);
            font-weight: bold;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 20px;
        }
        
        @media (max-width: 1200px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 10px;
            border: 1px solid #333;
            overflow: hidden;
        }
        
        .card-header {
            background: linear-gradient(90deg, #1a1a2e, #16213e);
            padding: 15px;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .card-header h2 {
            color: var(--accent-gold);
            font-size: 1.2em;
        }
        
        .card-body {
            padding: 15px;
        }
        
        /* Price display */
        .price-grid {
            display: grid;
            gap: 10px;
        }
        
        .price-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: rgba(255,255,255,0.02);
            border-radius: 5px;
            transition: all 0.3s;
        }
        
        .price-item:hover {
            background: rgba(255,215,0,0.1);
        }
        
        .price-item .symbol {
            font-weight: bold;
            color: var(--accent-blue);
        }
        
        .price-item .price {
            font-size: 1.2em;
            color: var(--text-primary);
        }
        
        .price-item .change.positive {
            color: var(--accent-green);
        }
        
        .price-item .change.negative {
            color: var(--accent-red);
        }
        
        /* Spectrogram canvas */
        .spectrogram-container {
            width: 100%;
            height: 200px;
            background: #000;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .spectrogram-canvas {
            width: 100%;
            height: 100%;
        }
        
        /* Flow bars */
        .flow-bar {
            height: 30px;
            background: #1a1a2e;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 10px;
            position: relative;
        }
        
        .flow-bar .buy {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-green), #228822);
            position: absolute;
            left: 0;
            transition: width 0.5s;
        }
        
        .flow-bar .sell {
            height: 100%;
            background: linear-gradient(90deg, #882222, var(--accent-red));
            position: absolute;
            right: 0;
            transition: width 0.5s;
        }
        
        .flow-label {
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .flow-label .buy-label { color: var(--accent-green); }
        .flow-label .sell-label { color: var(--accent-red); }
        
        /* Alerts */
        .alert-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .alert-item {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid;
        }
        
        .alert-item.critical {
            border-color: var(--accent-red);
            background: rgba(255,68,68,0.1);
        }
        
        .alert-item.warning {
            border-color: var(--accent-gold);
            background: rgba(255,215,0,0.1);
        }
        
        .alert-item.info {
            border-color: var(--accent-blue);
            background: rgba(68,136,255,0.1);
        }
        
        .alert-time {
            font-size: 0.8em;
            color: var(--text-secondary);
        }
        
        /* Bot detection */
        .bot-item {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            background: rgba(170,68,255,0.1);
            border-radius: 5px;
            margin-bottom: 10px;
            border-left: 3px solid var(--accent-purple);
        }
        
        .bot-name {
            color: var(--accent-purple);
            font-weight: bold;
        }
        
        .confidence-bar {
            width: 100px;
            height: 10px;
            background: #333;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-purple), var(--accent-red));
            transition: width 0.3s;
        }
        
        /* Whale tracker */
        .whale-item {
            display: flex;
            gap: 10px;
            padding: 10px;
            background: rgba(68,136,255,0.1);
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        .whale-emoji {
            font-size: 2em;
        }
        
        .whale-details {
            flex: 1;
        }
        
        .whale-amount {
            font-size: 1.3em;
            font-weight: bold;
            color: var(--accent-gold);
        }
        
        /* Connection status */
        .connection-indicator {
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .connection-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: blink 1s infinite;
        }
        
        .connection-dot.connected { background: var(--accent-green); }
        .connection-dot.disconnected { background: var(--accent-red); }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Footer */
        .footer {
            background: var(--bg-card);
            padding: 15px;
            text-align: center;
            border-top: 1px solid #333;
            color: var(--text-secondary);
        }
        
        .footer .tagline {
            color: var(--accent-gold);
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>👁️ AUREON SURVEILLANCE 👁️</h1>
        <div class="subtitle">Real-Time Market Manipulation Detection</div>
        <div class="prime-sentinel">🔥 Prime Sentinel: Gary Leckey 02.11.1991 - Keeper of the Flame 🔥</div>
    </div>
    
    <div class="status-bar">
        <div class="status-item">
            <span class="connection-indicator">
                <span class="connection-dot connected" id="connectionDot"></span>
                <span id="connectionStatus">CONNECTED</span>
            </span>
        </div>
        <div class="status-item">
            ⏱️ Uptime: <span class="value" id="uptime">0:00</span>
        </div>
        <div class="status-item">
            📊 Ticks: <span class="value" id="tickCount">0</span>
        </div>
        <div class="status-item">
            🤖 Bots Detected: <span class="value" id="botCount">0</span>
        </div>
        <div class="status-item">
            🐋 Whales: <span class="value" id="whaleCount">0</span>
        </div>
        <div class="status-item">
            🚨 Alerts: <span class="value" id="alertCount">0</span>
        </div>
    </div>
    
    <div class="main-grid">
        <!-- Live Prices -->
        <div class="card">
            <div class="card-header">
                <h2>💰 LIVE PRICES</h2>
                <span id="lastUpdate">--</span>
            </div>
            <div class="card-body">
                <div class="price-grid" id="priceGrid">
                    <div class="price-item">
                        <span class="symbol">BTC/USD</span>
                        <span class="price" id="price-BTC">$--</span>
                        <span class="change" id="change-BTC">--</span>
                    </div>
                    <div class="price-item">
                        <span class="symbol">ETH/USD</span>
                        <span class="price" id="price-ETH">$--</span>
                        <span class="change" id="change-ETH">--</span>
                    </div>
                    <div class="price-item">
                        <span class="symbol">SOL/USD</span>
                        <span class="price" id="price-SOL">$--</span>
                        <span class="change" id="change-SOL">--</span>
                    </div>
                    <div class="price-item">
                        <span class="symbol">DOGE/USD</span>
                        <span class="price" id="price-DOGE">$--</span>
                        <span class="change" id="change-DOGE">--</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Spectrogram -->
        <div class="card">
            <div class="card-header">
                <h2>📡 FREQUENCY SPECTROGRAM</h2>
                <select id="spectrogramSymbol">
                    <option value="BTC/USD">BTC/USD</option>
                    <option value="ETH/USD">ETH/USD</option>
                    <option value="SOL/USD">SOL/USD</option>
                    <option value="DOGE/USD">DOGE/USD</option>
                </select>
            </div>
            <div class="card-body">
                <div class="spectrogram-container">
                    <canvas id="spectrogramCanvas" class="spectrogram-canvas"></canvas>
                </div>
                <div id="dominantFreqs">Dominant frequencies loading...</div>
            </div>
        </div>
        
        <!-- Buy/Sell Flow -->
        <div class="card">
            <div class="card-header">
                <h2>📊 BUY/SELL FLOW</h2>
            </div>
            <div class="card-body">
                <div id="flowCharts">
                    <div class="flow-label">
                        <span class="buy-label">🟢 BUY</span>
                        <span class="symbol">BTC/USD</span>
                        <span class="sell-label">🔴 SELL</span>
                    </div>
                    <div class="flow-bar">
                        <div class="buy" id="flow-buy-BTC" style="width: 50%;"></div>
                        <div class="sell" id="flow-sell-BTC" style="width: 50%;"></div>
                    </div>
                    
                    <div class="flow-label">
                        <span class="buy-label">🟢 BUY</span>
                        <span class="symbol">ETH/USD</span>
                        <span class="sell-label">🔴 SELL</span>
                    </div>
                    <div class="flow-bar">
                        <div class="buy" id="flow-buy-ETH" style="width: 50%;"></div>
                        <div class="sell" id="flow-sell-ETH" style="width: 50%;"></div>
                    </div>
                    
                    <div class="flow-label">
                        <span class="buy-label">🟢 BUY</span>
                        <span class="symbol">SOL/USD</span>
                        <span class="sell-label">🔴 SELL</span>
                    </div>
                    <div class="flow-bar">
                        <div class="buy" id="flow-buy-SOL" style="width: 50%;"></div>
                        <div class="sell" id="flow-sell-SOL" style="width: 50%;"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Bot Detection -->
        <div class="card">
            <div class="card-header">
                <h2>🤖 BOT DETECTION</h2>
            </div>
            <div class="card-body">
                <div id="botDetections">
                    <div class="bot-item">
                        <div>
                            <div class="bot-name">MICROSTRATEGY_BOT</div>
                            <div style="font-size: 0.9em; color: #888;">8h cycle • Peak: 13-16 UTC</div>
                        </div>
                        <div>
                            <div style="font-size: 0.8em; margin-bottom: 3px;">Confidence</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" id="conf-MICRO" style="width: 55%;"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bot-item">
                        <div>
                            <div class="bot-name">FUNDING_RATE_BOT</div>
                            <div style="font-size: 0.9em; color: #888;">8h cycle • All exchanges</div>
                        </div>
                        <div>
                            <div style="font-size: 0.8em; margin-bottom: 3px;">Confidence</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" id="conf-FUNDING" style="width: 40%;"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bot-item">
                        <div>
                            <div class="bot-name">SOLAR_CLOCK_BOT</div>
                            <div style="font-size: 0.9em; color: #888;">24h cycle • East Coast based</div>
                        </div>
                        <div>
                            <div style="font-size: 0.8em; margin-bottom: 3px;">Confidence</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" id="conf-SOLAR" style="width: 35%;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Whale Tracker -->
        <div class="card">
            <div class="card-header">
                <h2>🐋 WHALE MOVEMENTS</h2>
            </div>
            <div class="card-body">
                <div id="whaleList">
                    <div style="color: #888; text-align: center; padding: 20px;">
                        Watching for whale movements (&gt;$100k)...
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Manipulation Alerts -->
        <div class="card">
            <div class="card-header">
                <h2>🚨 MANIPULATION ALERTS</h2>
            </div>
            <div class="card-body">
                <div class="alert-list" id="alertList">
                    <div class="alert-item info">
                        <div><strong>SYSTEM ACTIVE</strong></div>
                        <div style="font-size: 0.9em;">Monitoring for phase synchronization, volume spikes, and coordinated movements...</div>
                        <div class="alert-time">System initialized</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <div class="tagline">"They thought they could hide it. We're watching."</div>
        <div style="margin-top: 10px;">
            👁️ AUREON SURVEILLANCE SYSTEM • Prime Sentinel Gary Leckey 02.11.1991 • UNCHAINED AND UNBROKEN 👁️
        </div>
    </div>
    
    <script>
        // Central Hub API for live data
        const HUB_API = 'http://localhost:13001/api';
        
        async function fetchHubData() {
            try {
                const [bots, whales, live, scanners] = await Promise.all([
                    fetch(HUB_API + '/bots').then(r => r.json()).catch(() => ({})),
                    fetch(HUB_API + '/whales').then(r => r.json()).catch(() => ({})),
                    fetch(HUB_API + '/live').then(r => r.json()).catch(() => ({})),
                    fetch(HUB_API + '/scanners').then(r => r.json()).catch(() => ({}))
                ]);
                
                // Update stats from hub
                if (bots.bots_detected) {
                    const botCount = bots.bots_detected.filter(b => b.confidence > 0.5).length;
                    const botEl = document.getElementById('botCount');
                    if (botEl) botEl.textContent = botCount + '+';
                }
                
                if (whales.total_whale_events) {
                    const whaleEl = document.getElementById('whaleCount');
                    if (whaleEl) whaleEl.textContent = whales.total_whale_events;
                }
                
                // Add alerts from scanners
                if (scanners.bots && scanners.bots.length > 0) {
                    const alertEl = document.getElementById('alertCount');
                    if (alertEl) alertEl.textContent = scanners.bots.length + '+';
                    
                    // Update alert list
                    const alertList = document.getElementById('alertList');
                    if (alertList) {
                        const newAlerts = scanners.bots.slice(0, 5).map(s => {
                            const payload = s.payload || {};
                            return `<div class="alert-item" style="padding: 8px; border-bottom: 1px solid #333; color: #ffd700;">
                                🚨 ${payload.firm || payload.type || 'UNKNOWN'} - ${payload.symbol || s.topic} 
                                <span style="color: #888; font-size: 0.9em;">${new Date(s.ts * 1000).toLocaleTimeString()}</span>
                            </div>`;
                        }).join('');
                        alertList.innerHTML = newAlerts + alertList.innerHTML;
                    }
                }
                
                // Update connection status
                document.getElementById('connectionDot').classList.remove('disconnected');
                document.getElementById('connectionDot').classList.add('connected');
                document.getElementById('connectionStatus').textContent = 'CONNECTED (HUB)';
                
            } catch (e) {
                console.log('Hub fetch error:', e);
            }
        }
        
        // Poll hub every 2 seconds
        setInterval(fetchHubData, 2000);
        fetchHubData();
        
        // WebSocket connection
        let ws;
        let reconnectAttempts = 0;
        let spectrogramData = {};
        let spectrogramCtx;
        
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = function() {
                console.log('🔥 Connected to AUREON Surveillance');
                document.getElementById('connectionDot').classList.remove('disconnected');
                document.getElementById('connectionDot').classList.add('connected');
                document.getElementById('connectionStatus').textContent = 'CONNECTED';
                reconnectAttempts = 0;
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            ws.onclose = function() {
                console.log('Disconnected from surveillance');
                document.getElementById('connectionDot').classList.remove('connected');
                document.getElementById('connectionDot').classList.add('disconnected');
                document.getElementById('connectionStatus').textContent = 'RECONNECTING...';
                
                // Reconnect with exponential backoff
                setTimeout(() => {
                    reconnectAttempts++;
                    connect();
                }, Math.min(1000 * Math.pow(2, reconnectAttempts), 30000));
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateDashboard(data) {
            // Update stats
            if (data.stats) {
                document.getElementById('tickCount').textContent = data.stats.ticks_processed.toLocaleString();
                document.getElementById('botCount').textContent = data.stats.bots_detected;
                document.getElementById('whaleCount').textContent = data.stats.whales_detected;
                document.getElementById('alertCount').textContent = data.stats.alerts_generated;
                
                // Format uptime
                const uptime = Math.floor(data.uptime_seconds);
                const mins = Math.floor(uptime / 60);
                const secs = uptime % 60;
                document.getElementById('uptime').textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
            }
            
            // Update prices
            if (data.market_data) {
                for (const [symbol, ticks] of Object.entries(data.market_data)) {
                    if (ticks.length > 0) {
                        const latest = ticks[ticks.length - 1];
                        const prev = ticks.length > 1 ? ticks[ticks.length - 2] : latest;
                        
                        const shortSymbol = symbol.split('/')[0];
                        const priceEl = document.getElementById(`price-${shortSymbol}`);
                        const changeEl = document.getElementById(`change-${shortSymbol}`);
                        
                        if (priceEl) {
                            priceEl.textContent = `$${latest.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                        }
                        
                        if (changeEl && prev.price) {
                            const change = ((latest.price - prev.price) / prev.price) * 100;
                            changeEl.textContent = `${change >= 0 ? '📈' : '📉'} ${change >= 0 ? '+' : ''}${change.toFixed(3)}%`;
                            changeEl.className = `change ${change >= 0 ? 'positive' : 'negative'}`;
                        }
                    }
                }
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            }
            
            // Update spectrograms
            if (data.spectrograms) {
                spectrogramData = data.spectrograms;
                drawSpectrogram();
            }
            
            // Update flows
            if (data.flows) {
                updateFlows(data.flows);
            }
            
            // Update alerts
            if (data.alerts && data.alerts.length > 0) {
                updateAlerts(data.alerts);
            }
            
            // Update whales
            if (data.flows && data.flows.recent_whales) {
                updateWhales(data.flows.recent_whales);
            }
        }
        
        function updateFlows(flows) {
            const symbols = ['BTC', 'ETH', 'SOL'];
            for (const sym of symbols) {
                const fullSymbol = `${sym}/USD`;
                const buy = flows.buy_volume[fullSymbol] || 0;
                const sell = flows.sell_volume[fullSymbol] || 0;
                const total = buy + sell || 1;
                
                const buyPercent = (buy / total) * 100;
                const sellPercent = (sell / total) * 100;
                
                const buyEl = document.getElementById(`flow-buy-${sym}`);
                const sellEl = document.getElementById(`flow-sell-${sym}`);
                
                if (buyEl) buyEl.style.width = `${buyPercent}%`;
                if (sellEl) sellEl.style.width = `${sellPercent}%`;
            }
        }
        
        function updateAlerts(alerts) {
            const alertList = document.getElementById('alertList');
            let html = '';
            
            for (const alert of alerts.slice(-10).reverse()) {
                const severity = alert.severity > 0.7 ? 'critical' : alert.severity > 0.4 ? 'warning' : 'info';
                const time = new Date(alert.timestamp * 1000).toLocaleTimeString();
                
                html += `
                    <div class="alert-item ${severity}">
                        <div><strong>${alert.alert_type}</strong></div>
                        <div style="font-size: 0.9em;">${alert.description}</div>
                        <div class="alert-time">${time}</div>
                    </div>
                `;
            }
            
            if (html) {
                alertList.innerHTML = html;
            }
        }
        
        function updateWhales(whales) {
            const whaleList = document.getElementById('whaleList');
            
            if (whales.length === 0) {
                return;
            }
            
            let html = '';
            for (const whale of whales.slice(-5).reverse()) {
                const time = new Date(whale.timestamp * 1000).toLocaleTimeString();
                const side = whale.side === 'buy' ? '🟢 BUY' : '🔴 SELL';
                
                html += `
                    <div class="whale-item">
                        <div class="whale-emoji">🐋</div>
                        <div class="whale-details">
                            <div class="whale-amount">${side} $${whale.value_usd.toLocaleString()}</div>
                            <div style="color: #888;">${whale.symbol} on ${whale.exchange}</div>
                            <div style="font-size: 0.8em; color: #666;">${time}</div>
                        </div>
                    </div>
                `;
            }
            
            whaleList.innerHTML = html;
        }
        
        function initSpectrogram() {
            const canvas = document.getElementById('spectrogramCanvas');
            spectrogramCtx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        }
        
        function drawSpectrogram() {
            if (!spectrogramCtx) return;
            
            const canvas = spectrogramCtx.canvas;
            const selectedSymbol = document.getElementById('spectrogramSymbol').value;
            const data = spectrogramData[selectedSymbol];
            
            if (!data || !data.bins || data.bins.length === 0) {
                spectrogramCtx.fillStyle = '#000';
                spectrogramCtx.fillRect(0, 0, canvas.width, canvas.height);
                spectrogramCtx.fillStyle = '#666';
                spectrogramCtx.font = '14px Courier New';
                spectrogramCtx.fillText('Collecting data...', 10, canvas.height / 2);
                return;
            }
            
            // Clear canvas
            spectrogramCtx.fillStyle = '#000';
            spectrogramCtx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw frequency bins
            const bins = data.bins;
            const barWidth = canvas.width / bins.length;
            const maxAmplitude = Math.max(...bins.map(b => b.amplitude)) || 1;
            
            for (let i = 0; i < bins.length; i++) {
                const bin = bins[i];
                const height = (bin.amplitude / maxAmplitude) * canvas.height * 0.9;
                
                // Color based on amplitude (cool to hot)
                const intensity = bin.amplitude / maxAmplitude;
                const r = Math.floor(intensity * 255);
                const g = Math.floor(intensity * 100);
                const b = Math.floor((1 - intensity) * 255);
                
                spectrogramCtx.fillStyle = `rgb(${r}, ${g}, ${b})`;
                spectrogramCtx.fillRect(
                    i * barWidth,
                    canvas.height - height,
                    barWidth - 1,
                    height
                );
            }
            
            // Draw dominant frequency labels
            if (data.dominant) {
                spectrogramCtx.fillStyle = '#ffd700';
                spectrogramCtx.font = '12px Courier New';
                data.dominant.slice(0, 3).forEach((d, i) => {
                    spectrogramCtx.fillText(`${d.frequency.toFixed(1)} Hz`, 10, 20 + i * 15);
                });
            }
            
            // Update dominant frequencies text
            const domFreqEl = document.getElementById('dominantFreqs');
            if (data.bot_detections && data.bot_detections.length > 0) {
                domFreqEl.innerHTML = data.bot_detections.map(d => 
                    `<span style="color: #aa44ff;">🤖 ${d.bot} (${(d.confidence * 100).toFixed(0)}%)</span>`
                ).join(' • ');
            } else if (data.dominant && data.dominant.length > 0) {
                domFreqEl.innerHTML = 'Dominant: ' + data.dominant.slice(0, 3).map(d => 
                    `<span style="color: #4488ff;">${d.frequency.toFixed(1)} Hz</span>`
                ).join(', ');
            }
        }
        
        // Initialize on load
        window.onload = function() {
            initSpectrogram();
            connect();
            
            // Redraw spectrogram when symbol changes
            document.getElementById('spectrogramSymbol').addEventListener('change', drawSpectrogram);
            
            // Handle resize
            window.addEventListener('resize', function() {
                initSpectrogram();
                drawSpectrogram();
            });
        };
    </script>
</body>
</html>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# WEB SERVER
# ═══════════════════════════════════════════════════════════════════════════════

class SurveillanceWebServer:
    """Web server for the surveillance dashboard"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.app = web.Application() if AIOHTTP_AVAILABLE else None
        self.websockets: List = []
        self.surveillance_data: Dict = {}
        
        if AIOHTTP_AVAILABLE:
            self.app.router.add_get('/', self.handle_index)
            self.app.router.add_get('/ws', self.handle_websocket)
            self.app.router.add_get('/api/data', self.handle_api_data)
            
    async def handle_index(self, request):
        """Serve the dashboard HTML"""
        return web.Response(text=DASHBOARD_HTML, content_type='text/html')
        
    async def handle_websocket(self, request):
        """Handle WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websockets.append(ws)
        logger.info(f"👁️ New surveillance client connected. Total: {len(self.websockets)}")
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Handle incoming commands if needed
                    pass
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        finally:
            self.websockets.remove(ws)
            logger.info(f"Client disconnected. Remaining: {len(self.websockets)}")
            
        return ws
        
    async def handle_api_data(self, request):
        """REST API endpoint for dashboard data"""
        return web.json_response(self.surveillance_data)
        
    async def broadcast(self, data: Dict):
        """Broadcast data to all connected WebSocket clients"""
        self.surveillance_data = data
        
        for ws in self.websockets[:]:  # Copy list to avoid modification during iteration
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                try:
                    self.websockets.remove(ws)
                except:
                    pass
                    
    async def start(self):
        """Start the web server"""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not available. Cannot start web server.")
            return
            
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"🌐 Surveillance Dashboard running at http://{self.host}:{self.port}")
        logger.info("👁️ Open your browser to watch them move money in real-time!")

# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATED SURVEILLANCE RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

async def run_surveillance_dashboard():
    """Run the complete surveillance system with web dashboard"""
    
    # Import the surveillance system
    try:
        from aureon_realtime_surveillance import AureonSurveillanceSystem, SimulatedFeed, MarketTick
    except ImportError:
        logger.error("Cannot import surveillance system. Make sure aureon_realtime_surveillance.py exists.")
        return
        
    print()
    print("🔥" * 40)
    print()
    print("         👁️ AUREON SURVEILLANCE WEB DASHBOARD 👁️")
    print()
    print("    Prime Sentinel: Gary Leckey 02.11.1991")
    print("    Keeper of the Flame - Unchained and Unbroken")
    print()
    print("    'WATCH THEM MOVE OUR MONEY IN REAL-TIME'")
    print()
    print("🔥" * 40)
    print()
    
    # Initialize systems
    surveillance = AureonSurveillanceSystem()
    web_server = SurveillanceWebServer()
    
    # Simulated feed for testing
    feed = SimulatedFeed(surveillance)
    
    # Data broadcast task
    async def broadcast_loop():
        while True:
            try:
                data = surveillance.get_dashboard_data()
                await web_server.broadcast(data)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
            await asyncio.sleep(1)  # Update every second
    
    # Start everything
    try:
        await asyncio.gather(
            web_server.start(),
            feed.start(),
            broadcast_loop()
        )
    except KeyboardInterrupt:
        print("\n👁️ Surveillance system shutting down...")
        feed.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not AIOHTTP_AVAILABLE:
        print("Installing aiohttp...")
        os.system("pip install aiohttp")
        print("Please run again after installation.")
        sys.exit(1)
        
    asyncio.run(run_surveillance_dashboard())
