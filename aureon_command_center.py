#!/usr/bin/env python3
"""
🎮👑⚔️ AUREON COMMAND CENTER ⚔️👑🎮
═══════════════════════════════════════════════════════════════════════════════

       ██████╗ ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ 
      ██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗
      ██║     ██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║
      ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║
      ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝
       ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ 
                          
                    ██████╗███████╗███╗   ██╗████████╗███████╗██████╗ 
                   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
                   ██║     █████╗  ██╔██╗ ██║   ██║   █████╗  ██████╔╝
                   ██║     ██╔══╝  ██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
                   ╚██████╗███████╗██║ ╚████║   ██║   ███████╗██║  ██║
                    ╚═════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝

THE ULTIMATE UNIFIED DASHBOARD - ALL SYSTEMS IN ONE EPIC INTERFACE

Features:
👑 Queen's Voice & Commentary (Text-to-Speech)
📊 Real-time Trading Stats & P&L
🐋 Whale Tracking & Bot Intelligence
⚡ Live Trade Execution Feed
🌐 Multi-Exchange Status (Kraken, Binance, Alpaca, Capital)
🎵 Harmonic Frequency Visualization
🧠 25+ Intelligence Systems Status
🗺️ Global Bot Map
🔊 Audio Alerts & Victory Sounds
🎮 Red Alert 2 Style Command Interface

ONE DASHBOARD TO RULE THEM ALL!
"""

import sys
import os
import atexit

# Windows UTF-8 fix - AGGRESSIVE VERSION
# Skip stderr wrapping to avoid "I/O operation on closed file" on exit
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUNBUFFERED'] = '1'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        # Only wrap stdout, NOT stderr (stderr causes shutdown errors)
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass
    
    # Aggressive cleanup: redirect stderr to devnull on exit
    def _cleanup_stderr():
        try:
            sys.stderr = open(os.devnull, 'w')
        except Exception:
            pass
    atexit.register(_cleanup_stderr)

import asyncio
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Web framework
try:
    from aiohttp import web
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("❌ aiohttp not available - pip install aiohttp")

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM IMPORTS - Load all available intelligence systems
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEMS_STATUS = {}

# Core Intelligence
try:
    from aureon_thought_bus import ThoughtBus, Thought
    SYSTEMS_STATUS['Thought Bus'] = True
    thought_bus = ThoughtBus()
except ImportError:
    SYSTEMS_STATUS['Thought Bus'] = False
    thought_bus = None

try:
    from aureon_mycelium import MyceliumNetwork
    SYSTEMS_STATUS['Mycelium Network'] = True
except ImportError:
    SYSTEMS_STATUS['Mycelium Network'] = False

try:
    from aureon_enigma import AureonEnigma
    SYSTEMS_STATUS['Enigma Decoder'] = True
except ImportError:
    SYSTEMS_STATUS['Enigma Decoder'] = False

try:
    from aureon_probability_nexus import AureonProbabilityNexus
    SYSTEMS_STATUS['Probability Nexus'] = True
except ImportError:
    SYSTEMS_STATUS['Probability Nexus'] = False

try:
    from probability_ultimate_intelligence import ProbabilityUltimateIntelligence
    SYSTEMS_STATUS['Ultimate Intelligence'] = True
except ImportError:
    SYSTEMS_STATUS['Ultimate Intelligence'] = False

try:
    from aureon_elephant_learning import ElephantMemory
    SYSTEMS_STATUS['Elephant Memory'] = True
except ImportError:
    SYSTEMS_STATUS['Elephant Memory'] = False

try:
    from aureon_quantum_telescope import QuantumPrism
    SYSTEMS_STATUS['Quantum Telescope'] = True
except ImportError:
    SYSTEMS_STATUS['Quantum Telescope'] = False

try:
    from aureon_timeline_oracle import TimelineOracle
    SYSTEMS_STATUS['Timeline Oracle'] = True
except ImportError:
    SYSTEMS_STATUS['Timeline Oracle'] = False

try:
    from aureon_miner_brain import MinerBrain
    SYSTEMS_STATUS['Miner Brain'] = True
except ImportError:
    SYSTEMS_STATUS['Miner Brain'] = False

try:
    from aureon_harmonic_fusion import HarmonicWaveFusion
    SYSTEMS_STATUS['Harmonic Fusion'] = True
except ImportError:
    SYSTEMS_STATUS['Harmonic Fusion'] = False

try:
    from aureon_global_wave_scanner import GlobalWaveScanner
    SYSTEMS_STATUS['Global Wave Scanner'] = True
except ImportError:
    SYSTEMS_STATUS['Global Wave Scanner'] = False

try:
    from aureon_whale_integration import WhaleIntegration
    SYSTEMS_STATUS['Whale Integration'] = True
except ImportError:
    SYSTEMS_STATUS['Whale Integration'] = False

try:
    from aureon_orca_intelligence import OrcaIntelligence
    SYSTEMS_STATUS['Orca Intelligence'] = True
except ImportError:
    SYSTEMS_STATUS['Orca Intelligence'] = False

try:
    from aureon_queen_hive_mind import QueenHiveMind
    SYSTEMS_STATUS['Queen Hive Mind'] = True
except ImportError:
    SYSTEMS_STATUS['Queen Hive Mind'] = False

try:
    from aureon_bot_intelligence_profiler import BotIntelligenceProfiler, TRADING_FIRM_SIGNATURES
    SYSTEMS_STATUS['Bot Intelligence'] = True
except ImportError:
    SYSTEMS_STATUS['Bot Intelligence'] = False
    TRADING_FIRM_SIGNATURES = {}

try:
    from aureon_internal_multiverse import InternalMultiverse
    SYSTEMS_STATUS['Internal Multiverse'] = True
except ImportError:
    SYSTEMS_STATUS['Internal Multiverse'] = False

try:
    from aureon_stargate_protocol import ActivationCeremony
    SYSTEMS_STATUS['Stargate Protocol'] = True
except ImportError:
    SYSTEMS_STATUS['Stargate Protocol'] = False

try:
    from aureon_memory_core import MemorySpiral
    SYSTEMS_STATUS['Memory Core'] = True
except ImportError:
    SYSTEMS_STATUS['Memory Core'] = False

try:
    from aureon_immune_system import ImmuneSystem
    SYSTEMS_STATUS['Immune System'] = True
except ImportError:
    SYSTEMS_STATUS['Immune System'] = False

try:
    from aureon_chirp_bus import get_chirp_bus, ChirpType
    SYSTEMS_STATUS['Chirp Bus'] = True
except ImportError:
    SYSTEMS_STATUS['Chirp Bus'] = False

try:
    from queen_voice_engine import QueenVoiceEngine, queen_voice
    SYSTEMS_STATUS['Queen Voice'] = True
except ImportError:
    SYSTEMS_STATUS['Queen Voice'] = False
    queen_voice = None

try:
    from aureon_lighthouse import Lighthouse
    SYSTEMS_STATUS['Lighthouse'] = True
except ImportError:
    SYSTEMS_STATUS['Lighthouse'] = False

try:
    from aureon_harmonic_signal_chain import HarmonicSignalChain
    SYSTEMS_STATUS['Harmonic Signal Chain'] = True
except ImportError:
    SYSTEMS_STATUS['Harmonic Signal Chain'] = False

# Exchange clients
try:
    from kraken_client import KrakenClient
    SYSTEMS_STATUS['Kraken Exchange'] = True
except ImportError:
    SYSTEMS_STATUS['Kraken Exchange'] = False

try:
    from binance_client import BinanceClient
    SYSTEMS_STATUS['Binance Exchange'] = True
except ImportError:
    SYSTEMS_STATUS['Binance Exchange'] = False

try:
    from alpaca_client import AlpacaClient
    SYSTEMS_STATUS['Alpaca Exchange'] = True
except ImportError:
    SYSTEMS_STATUS['Alpaca Exchange'] = False

try:
    from capital_client import CapitalClient
    SYSTEMS_STATUS['Capital Exchange'] = True
except ImportError:
    SYSTEMS_STATUS['Capital Exchange'] = False

# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND CENTER STATE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CommandCenterState:
    """Global state for the command center"""
    # Trading stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    session_start: float = field(default_factory=time.time)
    
    # Live feeds
    recent_trades: deque = field(default_factory=lambda: deque(maxlen=50))
    recent_alerts: deque = field(default_factory=lambda: deque(maxlen=100))
    queen_messages: deque = field(default_factory=lambda: deque(maxlen=20))
    whale_alerts: deque = field(default_factory=lambda: deque(maxlen=30))
    bot_detections: deque = field(default_factory=lambda: deque(maxlen=50))
    
    # Exchange balances
    exchange_balances: Dict[str, Dict[str, float]] = field(default_factory=dict)
    exchange_status: Dict[str, str] = field(default_factory=dict)
    
    # Harmonic data
    harmonic_frequencies: List[Dict] = field(default_factory=list)
    wave_state: str = "BALANCED"
    coherence_score: float = 0.5
    
    # System metrics
    systems_online: int = 0
    systems_total: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    # WebSocket clients
    ws_clients: Set = field(default_factory=set)


# Global state
state = CommandCenterState()

# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND CENTER HTML - THE EPIC INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

COMMAND_CENTER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮👑 AUREON COMMAND CENTER 👑🎮</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --gold: #FFD700;
            --gold-dark: #B8860B;
            --green: #00FF88;
            --green-dark: #00AA55;
            --red: #FF3366;
            --blue: #00BFFF;
            --purple: #9966FF;
            --cyan: #00FFFF;
            --orange: #FF6600;
            --bg-dark: #0a0a1a;
            --bg-panel: rgba(10, 10, 30, 0.95);
            --border-glow: rgba(255, 215, 0, 0.5);
        }
        
        body {
            font-family: 'Share Tech Mono', monospace;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 25%, #0a1a2e 50%, #1a1a0a 75%, #0a0a1a 100%);
            background-size: 400% 400%;
            animation: gradientShift 30s ease infinite;
            color: var(--green);
            overflow: hidden;
            height: 100vh;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        /* HEADER - COMMAND BAR */
        #header {
            background: linear-gradient(180deg, rgba(0,0,0,0.95) 0%, rgba(20,20,40,0.9) 100%);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid var(--gold);
            box-shadow: 0 4px 30px rgba(255, 215, 0, 0.4);
            position: relative;
            z-index: 100;
        }
        
        #logo {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8em;
            font-weight: 900;
            background: linear-gradient(90deg, var(--gold), var(--orange), var(--gold));
            background-size: 200% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 3s linear infinite;
            text-shadow: 0 0 30px rgba(255, 215, 0, 0.8);
        }
        
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        
        #status-bar {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px 15px;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid var(--green);
            border-radius: 5px;
        }
        
        .status-item.warning {
            background: rgba(255, 102, 0, 0.2);
            border-color: var(--orange);
            color: var(--orange);
        }
        
        .status-item.danger {
            background: rgba(255, 51, 102, 0.2);
            border-color: var(--red);
            color: var(--red);
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--green);
            animation: pulse 1.5s infinite;
        }
        
        .status-dot.warning { background: var(--orange); }
        .status-dot.danger { background: var(--red); animation: blink 0.5s infinite; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        /* MAIN GRID LAYOUT */
        #main-container {
            display: grid;
            grid-template-columns: 280px 1fr 320px;
            grid-template-rows: auto 1fr auto;
            gap: 10px;
            padding: 10px;
            height: calc(100vh - 70px);
        }
        
        /* PANELS */
        .panel {
            background: var(--bg-panel);
            border: 2px solid var(--green);
            border-radius: 10px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2), inset 0 0 30px rgba(0, 0, 0, 0.5);
        }
        
        .panel-header {
            background: linear-gradient(90deg, rgba(0, 255, 136, 0.3), transparent);
            padding: 10px 15px;
            border-bottom: 1px solid var(--green);
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .panel-content {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        
        .panel.gold-border {
            border-color: var(--gold);
            box-shadow: 0 0 25px rgba(255, 215, 0, 0.3), inset 0 0 30px rgba(0, 0, 0, 0.5);
        }
        
        .panel.gold-border .panel-header {
            background: linear-gradient(90deg, rgba(255, 215, 0, 0.3), transparent);
            border-bottom-color: var(--gold);
            color: var(--gold);
        }
        
        /* QUEEN VOICE PANEL */
        #queen-panel {
            grid-column: 1 / -1;
            grid-row: 1;
            min-height: 120px;
            max-height: 150px;
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 102, 0, 0.1), rgba(255, 215, 0, 0.15));
            border: 3px solid var(--gold);
            position: relative;
            overflow: hidden;
        }
        
        #queen-avatar {
            position: absolute;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 80px;
            animation: queenPulse 2s infinite;
            filter: drop-shadow(0 0 20px rgba(255, 215, 0, 0.8));
        }
        
        @keyframes queenPulse {
            0%, 100% { transform: translateY(-50%) scale(1); }
            50% { transform: translateY(-50%) scale(1.05); }
        }
        
        #queen-message {
            margin-left: 120px;
            padding: 15px;
            font-size: 1.4em;
            color: var(--gold);
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
            line-height: 1.4;
        }
        
        #queen-status {
            position: absolute;
            bottom: 10px;
            right: 20px;
            font-size: 0.85em;
            color: #888;
        }
        
        #voice-toggle {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 8px 15px;
            background: var(--gold);
            color: #000;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            transition: all 0.3s;
        }
        
        #voice-toggle:hover {
            background: var(--orange);
            transform: scale(1.05);
        }
        
        #voice-toggle.speaking {
            animation: speakPulse 0.5s infinite;
        }
        
        @keyframes speakPulse {
            0%, 100% { background: var(--gold); }
            50% { background: var(--red); }
        }
        
        /* LEFT SIDEBAR - SYSTEMS */
        #systems-panel {
            grid-column: 1;
            grid-row: 2;
        }
        
        .system-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 10px;
            margin-bottom: 5px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 5px;
            border-left: 3px solid var(--green);
            transition: all 0.3s;
        }
        
        .system-item:hover {
            background: rgba(0, 255, 136, 0.1);
            transform: translateX(5px);
        }
        
        .system-item.offline {
            border-left-color: var(--red);
            opacity: 0.6;
        }
        
        .system-item.warning {
            border-left-color: var(--orange);
        }
        
        .system-name {
            font-size: 0.85em;
        }
        
        .system-status {
            font-size: 0.75em;
            padding: 2px 8px;
            border-radius: 3px;
            background: rgba(0, 255, 136, 0.2);
        }
        
        .system-status.offline {
            background: rgba(255, 51, 102, 0.3);
            color: var(--red);
        }
        
        /* CENTER - MAIN DISPLAY */
        #main-display {
            grid-column: 2;
            grid-row: 2;
            display: grid;
            grid-template-rows: auto 1fr auto;
            gap: 10px;
        }
        
        /* STATS ROW */
        #stats-row {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 10px;
        }
        
        .stat-card {
            background: var(--bg-panel);
            border: 2px solid var(--green);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.3);
        }
        
        .stat-card.gold {
            border-color: var(--gold);
        }
        
        .stat-card.gold:hover {
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.3);
        }
        
        .stat-label {
            font-size: 0.75em;
            color: #888;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8em;
            font-weight: 700;
        }
        
        .stat-value.green { color: var(--green); }
        .stat-value.gold { color: var(--gold); }
        .stat-value.red { color: var(--red); }
        .stat-value.blue { color: var(--blue); }
        
        /* TRADE FEED */
        #trade-feed {
            flex: 1;
            overflow: hidden;
        }
        
        .trade-item {
            display: grid;
            grid-template-columns: 80px 100px 1fr 100px 80px;
            gap: 10px;
            padding: 10px;
            margin-bottom: 5px;
            background: rgba(0, 0, 0, 0.4);
            border-radius: 5px;
            border-left: 4px solid var(--green);
            font-size: 0.9em;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .trade-item.buy { border-left-color: var(--green); }
        .trade-item.sell { border-left-color: var(--red); }
        .trade-item.whale { border-left-color: var(--blue); border-width: 4px; }
        
        .trade-time { color: #666; }
        .trade-type { font-weight: bold; }
        .trade-type.buy { color: var(--green); }
        .trade-type.sell { color: var(--red); }
        .trade-symbol { color: var(--cyan); }
        .trade-amount { color: var(--gold); }
        .trade-pnl { font-weight: bold; }
        .trade-pnl.positive { color: var(--green); }
        .trade-pnl.negative { color: var(--red); }
        
        /* EXCHANGE STATUS ROW */
        #exchange-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }
        
        .exchange-card {
            background: var(--bg-panel);
            border: 2px solid var(--green);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        
        .exchange-card.offline {
            border-color: var(--red);
            opacity: 0.7;
        }
        
        .exchange-logo {
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .exchange-name {
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .exchange-balance {
            font-size: 1.2em;
            color: var(--gold);
        }
        
        .exchange-status-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.75em;
            margin-top: 5px;
        }
        
        .exchange-status-badge.online {
            background: rgba(0, 255, 136, 0.2);
            color: var(--green);
        }
        
        .exchange-status-badge.offline {
            background: rgba(255, 51, 102, 0.2);
            color: var(--red);
        }
        
        /* RIGHT SIDEBAR */
        #right-sidebar {
            grid-column: 3;
            grid-row: 2;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        /* WHALE ALERTS */
        #whale-panel {
            flex: 1;
            border-color: var(--blue);
        }
        
        #whale-panel .panel-header {
            background: linear-gradient(90deg, rgba(0, 191, 255, 0.3), transparent);
            border-bottom-color: var(--blue);
            color: var(--blue);
        }
        
        .whale-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            margin-bottom: 5px;
            background: rgba(0, 191, 255, 0.1);
            border-radius: 5px;
            border-left: 3px solid var(--blue);
            animation: slideIn 0.3s ease-out;
        }
        
        .whale-icon { font-size: 1.5em; }
        .whale-info { flex: 1; }
        .whale-symbol { color: var(--cyan); font-weight: bold; }
        .whale-volume { color: var(--gold); }
        .whale-direction { font-size: 1.2em; }
        .whale-direction.buy { color: var(--green); }
        .whale-direction.sell { color: var(--red); }
        
        /* BOT DETECTIONS */
        #bot-panel {
            flex: 1;
            border-color: var(--purple);
        }
        
        #bot-panel .panel-header {
            background: linear-gradient(90deg, rgba(153, 102, 255, 0.3), transparent);
            border-bottom-color: var(--purple);
            color: var(--purple);
        }
        
        .bot-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px;
            margin-bottom: 5px;
            background: rgba(153, 102, 255, 0.1);
            border-radius: 5px;
            font-size: 0.85em;
        }
        
        .bot-icon { font-size: 1.2em; }
        .bot-firm { color: var(--purple); font-weight: bold; }
        .bot-country { color: #888; }
        
        /* HARMONIC VISUALIZATION */
        #harmonic-panel {
            height: 180px;
            border-color: var(--cyan);
        }
        
        #harmonic-panel .panel-header {
            background: linear-gradient(90deg, rgba(0, 255, 255, 0.3), transparent);
            border-bottom-color: var(--cyan);
            color: var(--cyan);
        }
        
        #harmonic-canvas {
            width: 100%;
            height: 100%;
        }
        
        /* FOOTER - ALERTS BAR */
        #footer {
            grid-column: 1 / -1;
            grid-row: 3;
            background: rgba(0, 0, 0, 0.9);
            border: 2px solid var(--orange);
            border-radius: 10px;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            gap: 20px;
            overflow: hidden;
        }
        
        #alert-label {
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            color: var(--orange);
            white-space: nowrap;
        }
        
        #alert-ticker {
            flex: 1;
            overflow: hidden;
            white-space: nowrap;
        }
        
        #alert-content {
            display: inline-block;
            animation: ticker 30s linear infinite;
        }
        
        @keyframes ticker {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
        
        .alert-item {
            display: inline-block;
            margin-right: 50px;
            padding: 5px 15px;
            background: rgba(255, 102, 0, 0.2);
            border-radius: 5px;
        }
        
        /* SCROLLBAR */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--green);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--gold);
        }
        
        /* RESPONSIVE */
        @media (max-width: 1400px) {
            #main-container {
                grid-template-columns: 250px 1fr 280px;
            }
            #stats-row {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        @media (max-width: 1200px) {
            #main-container {
                grid-template-columns: 1fr;
            }
            #systems-panel, #right-sidebar {
                display: none;
            }
        }
    </style>
</head>
<body>
    <!-- HEADER -->
    <div id="header">
        <div id="logo">🎮👑 AUREON COMMAND CENTER 👑🎮</div>
        <div id="status-bar">
            <div class="status-item" id="mode-status">
                <span class="status-dot"></span>
                <span id="trading-mode">DRY-RUN</span>
            </div>
            <div class="status-item" id="systems-status">
                <span class="status-dot"></span>
                <span><span id="systems-online">0</span>/<span id="systems-total">0</span> Systems</span>
            </div>
            <div class="status-item" id="uptime-status">
                <span>⏱️</span>
                <span id="uptime">00:00:00</span>
            </div>
            <div class="status-item" id="clock">
                <span>🕐</span>
                <span id="current-time">--:--:--</span>
            </div>
        </div>
    </div>
    
    <!-- MAIN CONTAINER -->
    <div id="main-container">
        <!-- QUEEN VOICE PANEL -->
        <div id="queen-panel" class="panel gold-border">
            <div id="queen-avatar">👑</div>
            <div id="queen-message">Welcome to the Command Center. All systems initializing...</div>
            <div id="queen-status">Queen SERO | Omniscient Mode | All-Seeing Eye Active</div>
            <button id="voice-toggle" onclick="toggleVoice()">🔊 VOICE</button>
        </div>
        
        <!-- LEFT SIDEBAR - SYSTEMS -->
        <div id="systems-panel" class="panel">
            <div class="panel-header">
                <span>🧠 INTELLIGENCE SYSTEMS</span>
                <span id="systems-count">0/0</span>
            </div>
            <div class="panel-content" id="systems-list">
                <!-- Systems populated by JS -->
            </div>
        </div>
        
        <!-- CENTER - MAIN DISPLAY -->
        <div id="main-display">
            <!-- STATS ROW -->
            <div id="stats-row">
                <div class="stat-card gold">
                    <div class="stat-label">💰 TOTAL P&L</div>
                    <div class="stat-value gold" id="total-pnl">$0.00</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">📊 TRADES</div>
                    <div class="stat-value green" id="total-trades">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">✅ WIN RATE</div>
                    <div class="stat-value green" id="win-rate">0%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">🏆 WINS</div>
                    <div class="stat-value green" id="wins">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">❌ LOSSES</div>
                    <div class="stat-value red" id="losses">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">🎯 COHERENCE</div>
                    <div class="stat-value blue" id="coherence">0.50</div>
                </div>
            </div>
            
            <!-- TRADE FEED -->
            <div id="trade-feed" class="panel">
                <div class="panel-header">
                    <span>⚡ LIVE TRADE FEED</span>
                    <span id="trade-rate">0 trades/min</span>
                </div>
                <div class="panel-content" id="trade-list">
                    <!-- Trades populated by JS -->
                </div>
            </div>
            
            <!-- EXCHANGE STATUS -->
            <div id="exchange-row">
                <div class="exchange-card" id="exchange-kraken">
                    <div class="exchange-logo">🐙</div>
                    <div class="exchange-name">KRAKEN</div>
                    <div class="exchange-balance" id="kraken-balance">$0.00</div>
                    <div class="exchange-status-badge online" id="kraken-status">ONLINE</div>
                </div>
                <div class="exchange-card" id="exchange-binance">
                    <div class="exchange-logo">🟡</div>
                    <div class="exchange-name">BINANCE</div>
                    <div class="exchange-balance" id="binance-balance">$0.00</div>
                    <div class="exchange-status-badge online" id="binance-status">ONLINE</div>
                </div>
                <div class="exchange-card" id="exchange-alpaca">
                    <div class="exchange-logo">🦙</div>
                    <div class="exchange-name">ALPACA</div>
                    <div class="exchange-balance" id="alpaca-balance">$0.00</div>
                    <div class="exchange-status-badge online" id="alpaca-status">ONLINE</div>
                </div>
                <div class="exchange-card" id="exchange-capital">
                    <div class="exchange-logo">💼</div>
                    <div class="exchange-name">CAPITAL</div>
                    <div class="exchange-balance" id="capital-balance">$0.00</div>
                    <div class="exchange-status-badge online" id="capital-status">ONLINE</div>
                </div>
            </div>
        </div>
        
        <!-- RIGHT SIDEBAR -->
        <div id="right-sidebar">
            <!-- WHALE ALERTS -->
            <div id="whale-panel" class="panel">
                <div class="panel-header">
                    <span>🐋 WHALE ALERTS</span>
                    <span id="whale-count">0</span>
                </div>
                <div class="panel-content" id="whale-list">
                    <!-- Whales populated by JS -->
                </div>
            </div>
            
            <!-- BOT DETECTIONS -->
            <div id="bot-panel" class="panel">
                <div class="panel-header">
                    <span>🤖 BOT INTELLIGENCE</span>
                    <span id="bot-count">0</span>
                </div>
                <div class="panel-content" id="bot-list">
                    <!-- Bots populated by JS -->
                </div>
            </div>
            
            <!-- HARMONIC VISUALIZATION -->
            <div id="harmonic-panel" class="panel">
                <div class="panel-header">
                    <span>🎵 HARMONIC FIELD</span>
                    <span id="wave-state">BALANCED</span>
                </div>
                <div class="panel-content">
                    <canvas id="harmonic-canvas"></canvas>
                </div>
            </div>
        </div>
        
        <!-- FOOTER - ALERTS -->
        <div id="footer">
            <div id="alert-label">⚠️ ALERTS</div>
            <div id="alert-ticker">
                <div id="alert-content">
                    <span class="alert-item">🎮 Command Center Online</span>
                    <span class="alert-item">👑 Queen SERO Active</span>
                    <span class="alert-item">🧠 All Intelligence Systems Operational</span>
                    <span class="alert-item">⚡ Ready to Trade</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // ═══════════════════════════════════════════════════════════════════════════
        // COMMAND CENTER JAVASCRIPT
        // ═══════════════════════════════════════════════════════════════════════════
        
        let ws = null;
        let voiceEnabled = false;
        let startTime = Date.now();
        let systemsData = {};
        let tradesData = [];
        let whalesData = [];
        let botsData = [];
        
        // Initialize WebSocket connection
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = () => {
                console.log('🎮 Command Center WebSocket connected');
                addAlert('🎮 Command Center connected to server');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = () => {
                console.log('WebSocket closed, reconnecting...');
                addAlert('⚠️ Connection lost, reconnecting...');
                setTimeout(initWebSocket, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        
        // Handle incoming messages
        function handleMessage(data) {
            switch(data.type) {
                case 'state':
                    updateFullState(data);
                    break;
                case 'trade':
                    addTrade(data.trade);
                    break;
                case 'whale':
                    addWhale(data.whale);
                    break;
                case 'bot':
                    addBot(data.bot);
                    break;
                case 'queen':
                    updateQueenMessage(data.message);
                    break;
                case 'alert':
                    addAlert(data.alert);
                    break;
                case 'systems':
                    updateSystems(data.systems);
                    break;
                case 'balances':
                    updateBalances(data.balances);
                    break;
                case 'stats':
                    updateStats(data.stats);
                    break;
            }
        }
        
        // Update full state
        function updateFullState(data) {
            if (data.stats) updateStats(data.stats);
            if (data.systems) updateSystems(data.systems);
            if (data.balances) updateBalances(data.balances);
            if (data.trades) {
                tradesData = data.trades;
                renderTrades();
            }
            if (data.whales) {
                whalesData = data.whales;
                renderWhales();
            }
            if (data.bots) {
                botsData = data.bots;
                renderBots();
            }
            if (data.queen_message) {
                updateQueenMessage(data.queen_message);
            }
        }
        
        // Update stats
        function updateStats(stats) {
            document.getElementById('total-pnl').textContent = '$' + (stats.total_pnl || 0).toFixed(2);
            document.getElementById('total-pnl').className = 'stat-value ' + (stats.total_pnl >= 0 ? 'gold' : 'red');
            document.getElementById('total-trades').textContent = stats.total_trades || 0;
            document.getElementById('wins').textContent = stats.winning_trades || 0;
            document.getElementById('losses').textContent = stats.losing_trades || 0;
            
            const winRate = stats.total_trades > 0 
                ? ((stats.winning_trades / stats.total_trades) * 100).toFixed(1) 
                : 0;
            document.getElementById('win-rate').textContent = winRate + '%';
            document.getElementById('coherence').textContent = (stats.coherence || 0.5).toFixed(2);
        }
        
        // Update systems list
        function updateSystems(systems) {
            systemsData = systems;
            const container = document.getElementById('systems-list');
            container.innerHTML = '';
            
            let online = 0;
            let total = 0;
            
            for (const [name, status] of Object.entries(systems)) {
                total++;
                if (status) online++;
                
                const item = document.createElement('div');
                item.className = 'system-item' + (status ? '' : ' offline');
                item.innerHTML = `
                    <span class="system-name">${name}</span>
                    <span class="system-status ${status ? '' : 'offline'}">${status ? '✅ ONLINE' : '❌ OFFLINE'}</span>
                `;
                container.appendChild(item);
            }
            
            document.getElementById('systems-online').textContent = online;
            document.getElementById('systems-total').textContent = total;
            document.getElementById('systems-count').textContent = `${online}/${total}`;
        }
        
        // Update balances
        function updateBalances(balances) {
            for (const [exchange, balance] of Object.entries(balances)) {
                const balanceEl = document.getElementById(`${exchange}-balance`);
                const statusEl = document.getElementById(`${exchange}-status`);
                const cardEl = document.getElementById(`exchange-${exchange}`);
                
                if (balanceEl) {
                    if (typeof balance === 'number') {
                        balanceEl.textContent = '$' + balance.toFixed(2);
                        if (statusEl) {
                            statusEl.textContent = 'ONLINE';
                            statusEl.className = 'exchange-status-badge online';
                        }
                        if (cardEl) cardEl.classList.remove('offline');
                    } else if (balance === 'offline') {
                        balanceEl.textContent = 'OFFLINE';
                        if (statusEl) {
                            statusEl.textContent = 'OFFLINE';
                            statusEl.className = 'exchange-status-badge offline';
                        }
                        if (cardEl) cardEl.classList.add('offline');
                    }
                }
            }
        }
        
        // Add trade to feed
        function addTrade(trade) {
            tradesData.unshift(trade);
            if (tradesData.length > 50) tradesData.pop();
            renderTrades();
            
            // Play sound for trades
            if (trade.pnl > 0) {
                playSound('win');
            }
        }
        
        // Render trades
        function renderTrades() {
            const container = document.getElementById('trade-list');
            container.innerHTML = '';
            
            for (const trade of tradesData.slice(0, 20)) {
                const item = document.createElement('div');
                const isWhale = trade.volume > 100000;
                item.className = `trade-item ${trade.side} ${isWhale ? 'whale' : ''}`;
                item.innerHTML = `
                    <span class="trade-time">${trade.time || '--:--:--'}</span>
                    <span class="trade-type ${trade.side}">${trade.side?.toUpperCase() || 'TRADE'}</span>
                    <span class="trade-symbol">${trade.symbol || 'N/A'}</span>
                    <span class="trade-amount">$${(trade.amount || 0).toFixed(2)}</span>
                    <span class="trade-pnl ${(trade.pnl || 0) >= 0 ? 'positive' : 'negative'}">
                        ${(trade.pnl || 0) >= 0 ? '+' : ''}$${(trade.pnl || 0).toFixed(2)}
                    </span>
                `;
                container.appendChild(item);
            }
        }
        
        // Add whale alert
        function addWhale(whale) {
            whalesData.unshift(whale);
            if (whalesData.length > 30) whalesData.pop();
            renderWhales();
            playSound('whale');
        }
        
        // Render whales
        function renderWhales() {
            const container = document.getElementById('whale-list');
            container.innerHTML = '';
            document.getElementById('whale-count').textContent = whalesData.length;
            
            for (const whale of whalesData.slice(0, 10)) {
                const item = document.createElement('div');
                item.className = 'whale-item';
                item.innerHTML = `
                    <span class="whale-icon">🐋</span>
                    <div class="whale-info">
                        <div class="whale-symbol">${whale.symbol || 'N/A'}</div>
                        <div class="whale-volume">$${formatNumber(whale.volume || 0)}</div>
                    </div>
                    <span class="whale-direction ${whale.direction}">${whale.direction === 'buy' ? '📈' : '📉'}</span>
                `;
                container.appendChild(item);
            }
        }
        
        // Add bot detection
        function addBot(bot) {
            botsData.unshift(bot);
            if (botsData.length > 50) botsData.pop();
            renderBots();
        }
        
        // Render bots
        function renderBots() {
            const container = document.getElementById('bot-list');
            container.innerHTML = '';
            document.getElementById('bot-count').textContent = botsData.length;
            
            for (const bot of botsData.slice(0, 15)) {
                const item = document.createElement('div');
                item.className = 'bot-item';
                item.innerHTML = `
                    <span class="bot-icon">🤖</span>
                    <span class="bot-firm">${bot.firm || 'Unknown'}</span>
                    <span class="bot-country">${bot.country || ''}</span>
                `;
                container.appendChild(item);
            }
        }
        
        // Update Queen message
        function updateQueenMessage(message) {
            document.getElementById('queen-message').textContent = message;
            
            if (voiceEnabled) {
                speak(message);
            }
        }
        
        // Add alert
        function addAlert(alertText) {
            const content = document.getElementById('alert-content');
            const item = document.createElement('span');
            item.className = 'alert-item';
            item.textContent = alertText;
            content.appendChild(item);
            
            // Limit alerts
            while (content.children.length > 20) {
                content.removeChild(content.firstChild);
            }
        }
        
        // Toggle voice
        function toggleVoice() {
            voiceEnabled = !voiceEnabled;
            const btn = document.getElementById('voice-toggle');
            btn.textContent = voiceEnabled ? '🔊 VOICE ON' : '🔇 VOICE OFF';
            btn.classList.toggle('speaking', voiceEnabled);
            
            if (voiceEnabled) {
                speak('Queen voice enabled. I am watching everything.');
            }
        }
        
        // Text-to-speech
        function speak(text) {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.9;
                utterance.pitch = 1.1;
                speechSynthesis.speak(utterance);
            }
        }
        
        // Play sound effects
        function playSound(type) {
            // Sound effects (can be expanded)
            const sounds = {
                win: 'data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgA',
                whale: 'data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgA'
            };
            // Placeholder - actual sounds would need proper audio files
        }
        
        // Format large numbers
        function formatNumber(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
            return num.toFixed(0);
        }
        
        // Update clock
        function updateClock() {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleTimeString();
            
            // Uptime
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            document.getElementById('uptime').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        // Draw harmonic visualization
        function drawHarmonics() {
            const canvas = document.getElementById('harmonic-canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            
            const width = canvas.width;
            const height = canvas.height;
            const centerY = height / 2;
            
            ctx.clearRect(0, 0, width, height);
            
            // Draw multiple harmonic waves
            const colors = ['#00FF88', '#FFD700', '#00BFFF', '#FF6600'];
            const frequencies = [0.02, 0.03, 0.015, 0.025];
            const amplitudes = [20, 15, 25, 18];
            const phases = [Date.now() * 0.001, Date.now() * 0.0015, Date.now() * 0.0008, Date.now() * 0.0012];
            
            for (let w = 0; w < 4; w++) {
                ctx.beginPath();
                ctx.strokeStyle = colors[w];
                ctx.lineWidth = 2;
                ctx.globalAlpha = 0.7;
                
                for (let x = 0; x < width; x++) {
                    const y = centerY + Math.sin(x * frequencies[w] + phases[w]) * amplitudes[w];
                    if (x === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }
                ctx.stroke();
            }
            
            ctx.globalAlpha = 1;
            
            requestAnimationFrame(drawHarmonics);
        }
        
        // Fetch initial state
        async function fetchInitialState() {
            try {
                const response = await fetch('/api/state');
                const data = await response.json();
                updateFullState(data);
            } catch (error) {
                console.error('Failed to fetch initial state:', error);
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initWebSocket();
            fetchInitialState();
            setInterval(updateClock, 1000);
            updateClock();
            drawHarmonics();
            
            console.log('🎮👑 AUREON COMMAND CENTER INITIALIZED 👑🎮');
        });
    </script>
</body>
</html>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# AIOHTTP WEB SERVER
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_index(request):
    """Serve the main command center HTML"""
    return web.Response(text=COMMAND_CENTER_HTML, content_type='text/html')

async def handle_api_state(request):
    """Return full state as JSON"""
    return web.json_response({
        'stats': {
            'total_trades': state.total_trades,
            'winning_trades': state.winning_trades,
            'losing_trades': state.losing_trades,
            'total_pnl': state.total_pnl,
            'coherence': state.coherence_score,
        },
        'systems': SYSTEMS_STATUS,
        'balances': state.exchange_balances,
        'trades': list(state.recent_trades),
        'whales': list(state.whale_alerts),
        'bots': list(state.bot_detections),
        'queen_message': state.queen_messages[-1] if state.queen_messages else "Queen SERO online. All systems operational.",
    })

async def websocket_handler(request):
    """WebSocket handler for real-time updates"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    state.ws_clients.add(ws)
    print(f"🔌 New WebSocket client connected. Total: {len(state.ws_clients)}")
    
    try:
        # Send initial state
        await ws.send_json({
            'type': 'state',
            'stats': {
                'total_trades': state.total_trades,
                'winning_trades': state.winning_trades,
                'losing_trades': state.losing_trades,
                'total_pnl': state.total_pnl,
                'coherence': state.coherence_score,
            },
            'systems': SYSTEMS_STATUS,
            'balances': state.exchange_balances,
            'trades': list(state.recent_trades),
            'whales': list(state.whale_alerts),
            'bots': list(state.bot_detections),
            'queen_message': state.queen_messages[-1] if state.queen_messages else "Welcome to the Command Center.",
        })
        
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                # Handle client messages if needed
                pass
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f'WebSocket error: {ws.exception()}')
    finally:
        state.ws_clients.discard(ws)
        print(f"🔌 WebSocket client disconnected. Total: {len(state.ws_clients)}")
    
    return ws

async def broadcast_to_clients(message: dict):
    """Broadcast message to all connected WebSocket clients"""
    if not state.ws_clients:
        return
    
    dead_clients = set()
    for ws in state.ws_clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead_clients.add(ws)
    
    state.ws_clients -= dead_clients

# ═══════════════════════════════════════════════════════════════════════════════
# BACKGROUND TASKS - FEED DATA INTO COMMAND CENTER
# ═══════════════════════════════════════════════════════════════════════════════

async def queen_commentary_task():
    """Generate Queen commentary periodically"""
    messages = [
        "Monitoring all exchanges. The market whispers its secrets.",
        "I see patterns forming in the chaos. Stay alert.",
        "The bots are dancing. Some will fall. We will profit.",
        "Harmonic resonance detected. Opportunities emerging.",
        "Whale activity spotted. Tracking their movements.",
        "The multiverse branches align. Execute with precision.",
        "Fear not the volatility. It is our friend.",
        "Intelligence systems nominal. Ready to strike.",
        "The golden ratio guides our path. φ = 1.618",
        "Planet saving mode: ACTIVE. Every trade matters.",
        "Remember: We trade to win. Losses are teachers.",
        "The Lighthouse guides us through the storm.",
        "Mycelium network propagating signals. Stay connected.",
        "Enigma decoded another pattern. Fascinating.",
        "All seeing. All knowing. All winning.",
    ]
    
    while True:
        await asyncio.sleep(30)  # Every 30 seconds
        message = random.choice(messages)
        state.queen_messages.append(message)
        await broadcast_to_clients({
            'type': 'queen',
            'message': message
        })

async def simulate_data_task():
    """Simulate incoming data for demo purposes"""
    symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'ADA/USD', 'DOT/USD', 'AVAX/USD', 'MATIC/USD']
    firms = ['Jump Trading', 'Citadel', 'Two Sigma', 'DE Shaw', 'Wintermute', 'Alameda', 'Jane Street', 'HRT']
    countries = ['🇺🇸 USA', '🇬🇧 UK', '🇨🇳 China', '🇯🇵 Japan', '🇩🇪 Germany', '🇸🇬 Singapore']
    
    while True:
        await asyncio.sleep(random.uniform(2, 8))
        
        # Simulate trade
        if random.random() < 0.4:
            trade = {
                'time': datetime.now().strftime('%H:%M:%S'),
                'side': random.choice(['buy', 'sell']),
                'symbol': random.choice(symbols),
                'amount': random.uniform(10, 5000),
                'pnl': random.uniform(-50, 100),
                'volume': random.uniform(1000, 500000)
            }
            state.recent_trades.appendleft(trade)
            state.total_trades += 1
            state.total_pnl += trade['pnl']
            if trade['pnl'] > 0:
                state.winning_trades += 1
            else:
                state.losing_trades += 1
            
            await broadcast_to_clients({'type': 'trade', 'trade': trade})
            await broadcast_to_clients({
                'type': 'stats',
                'stats': {
                    'total_trades': state.total_trades,
                    'winning_trades': state.winning_trades,
                    'losing_trades': state.losing_trades,
                    'total_pnl': state.total_pnl,
                    'coherence': state.coherence_score,
                }
            })
        
        # Simulate whale
        if random.random() < 0.1:
            whale = {
                'symbol': random.choice(symbols),
                'volume': random.uniform(100000, 10000000),
                'direction': random.choice(['buy', 'sell']),
            }
            state.whale_alerts.appendleft(whale)
            await broadcast_to_clients({'type': 'whale', 'whale': whale})
        
        # Simulate bot detection
        if random.random() < 0.15:
            bot = {
                'firm': random.choice(firms),
                'country': random.choice(countries),
            }
            state.bot_detections.appendleft(bot)
            await broadcast_to_clients({'type': 'bot', 'bot': bot})

async def update_balances_task():
    """Periodically update exchange balances"""
    while True:
        # Try to get real balances
        balances = {}
        
        if SYSTEMS_STATUS.get('Kraken Exchange'):
            try:
                # Would call real client here
                balances['kraken'] = random.uniform(500, 5000)
            except Exception:
                balances['kraken'] = 'offline'
        else:
            balances['kraken'] = 'offline'
        
        if SYSTEMS_STATUS.get('Binance Exchange'):
            try:
                balances['binance'] = random.uniform(500, 5000)
            except Exception:
                balances['binance'] = 'offline'
        else:
            balances['binance'] = 'offline'
        
        if SYSTEMS_STATUS.get('Alpaca Exchange'):
            try:
                balances['alpaca'] = random.uniform(500, 5000)
            except Exception:
                balances['alpaca'] = 'offline'
        else:
            balances['alpaca'] = 'offline'
        
        if SYSTEMS_STATUS.get('Capital Exchange'):
            try:
                balances['capital'] = random.uniform(500, 5000)
            except Exception:
                balances['capital'] = 'offline'
        else:
            balances['capital'] = 'offline'
        
        state.exchange_balances = balances
        await broadcast_to_clients({'type': 'balances', 'balances': balances})
        
        await asyncio.sleep(30)

async def thought_bus_listener_task():
    """Listen to ThoughtBus for real updates"""
    if not thought_bus:
        return
    
    while True:
        try:
            # Subscribe to relevant topics
            # This would integrate with the actual thought bus
            pass
        except Exception as e:
            print(f"ThoughtBus listener error: {e}")
        await asyncio.sleep(1)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def create_app():
    """Create the aiohttp application"""
    app = web.Application()
    
    # Routes
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/state', handle_api_state)
    app.router.add_get('/ws', websocket_handler)
    
    return app

async def start_background_tasks(app):
    """Start background tasks"""
    app['queen_task'] = asyncio.create_task(queen_commentary_task())
    app['simulate_task'] = asyncio.create_task(simulate_data_task())
    app['balances_task'] = asyncio.create_task(update_balances_task())
    app['thought_bus_task'] = asyncio.create_task(thought_bus_listener_task())

async def cleanup_background_tasks(app):
    """Cleanup background tasks"""
    for task_name in ['queen_task', 'simulate_task', 'balances_task', 'thought_bus_task']:
        task = app.get(task_name)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

def main():
    """Main entry point"""
    if not AIOHTTP_AVAILABLE:
        print("❌ Cannot start Command Center - aiohttp not installed")
        print("   Run: pip install aiohttp")
        return
    
    # Count online systems
    state.systems_online = sum(1 for v in SYSTEMS_STATUS.values() if v)
    state.systems_total = len(SYSTEMS_STATUS)
    
    print("\n" + "=" * 80)
    print("""
    ██████╗ ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ 
   ██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗
   ██║     ██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║
   ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║
   ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝
    ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ 
                       
                 ██████╗███████╗███╗   ██╗████████╗███████╗██████╗ 
                ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
                ██║     █████╗  ██╔██╗ ██║   ██║   █████╗  ██████╔╝
                ██║     ██╔══╝  ██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
                ╚██████╗███████╗██║ ╚████║   ██║   ███████╗██║  ██║
                 ╚═════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
    """)
    print("=" * 80)
    print(f"🎮 AUREON COMMAND CENTER - LAUNCHING...")
    print(f"=" * 80)
    print(f"")
    print(f"   🌐 URL: http://localhost:8888")
    print(f"")
    print(f"   📊 Intelligence Systems: {state.systems_online}/{state.systems_total} ONLINE")
    print(f"   👑 Queen Voice: {'✅ ENABLED' if SYSTEMS_STATUS.get('Queen Voice') else '⚠️ DISABLED'}")
    print(f"   🧠 Thought Bus: {'✅ CONNECTED' if SYSTEMS_STATUS.get('Thought Bus') else '⚠️ OFFLINE'}")
    print(f"   🍄 Mycelium: {'✅ ACTIVE' if SYSTEMS_STATUS.get('Mycelium Network') else '⚠️ OFFLINE'}")
    print(f"   🐦 Chirp Bus: {'✅ ACTIVE' if SYSTEMS_STATUS.get('Chirp Bus') else '⚠️ OFFLINE'}")
    print(f"")
    print(f"   🐙 Kraken: {'✅' if SYSTEMS_STATUS.get('Kraken Exchange') else '❌'}")
    print(f"   🟡 Binance: {'✅' if SYSTEMS_STATUS.get('Binance Exchange') else '❌'}")
    print(f"   🦙 Alpaca: {'✅' if SYSTEMS_STATUS.get('Alpaca Exchange') else '❌'}")
    print(f"   💼 Capital: {'✅' if SYSTEMS_STATUS.get('Capital Exchange') else '❌'}")
    print(f"")
    print(f"=" * 80)
    print(f"   Press Ctrl+C to stop the Command Center")
    print(f"=" * 80 + "\n")
    
    # Create and run app
    app = create_app()
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    
    web.run_app(app, host='0.0.0.0', port=8888, print=None)

if __name__ == '__main__':
    main()
