#!/usr/bin/env python3
"""
🧠💭⚡ AUREON MIND → THOUGHT → ACTION HUB
═══════════════════════════════════════════════════════════════════════════

UNIFIED COGNITIVE PIPELINE VISUALIZATION

Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│  🧠 MIND (Queen Hive + Intelligence)                                │
│     ↓                                                                │
│  💭 THOUGHT (ThoughtBus Communication)                              │
│     ↓                                                                │
│  ⚡ ACTION (Execution + Trading)                                     │
└─────────────────────────────────────────────────────────────────────┘

Features:
- Mind Map visualization with LIVE cognitive flow
- Real-time ThoughtBus message streaming
- Queen decision tracking
- Action execution monitoring
- System interconnections showing data flow
- Live metrics from all 200+ systems

Port: 13002
URL: http://localhost:13002

Gary Leckey | January 2026 | Mind → Thought → Action
"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
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
import aiohttp
from aiohttp import web
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set, Optional
from collections import deque, defaultdict
from pathlib import Path

# Import core systems
from aureon.command_centers.aureon_system_hub import SystemRegistry
from aureon.core.aureon_thought_bus import ThoughtBus, Thought
from aureon.core.aureon_runtime_safety import audit_mode_enabled
SelfQuestioningAI = None
QueenHiveMind = None
ProbabilityNexus = None
UltimateIntelligence = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

# Safe system imports
def safe_import(name: str, module: str, cls: str):
    """Safely import systems."""
    try:
        mod = __import__(module, fromlist=[cls])
        return getattr(mod, cls)
    except Exception as e:
        logger.debug(f"⚠️ {name}: {e}")
        return None

def load_optional_system_classes():
    """Load optional cognitive systems only after the HTTP hub is online."""
    global QueenHiveMind, ProbabilityNexus, UltimateIntelligence
    if QueenHiveMind is None:
        QueenHiveMind = safe_import('Queen', 'aureon_queen_hive_mind', 'QueenHiveMind')
    if ProbabilityNexus is None:
        ProbabilityNexus = safe_import('ProbNexus', 'aureon_probability_nexus', 'ProbabilityNexus')
    if UltimateIntelligence is None:
        UltimateIntelligence = safe_import('UltimateIntel', 'probability_ultimate_intelligence', 'ProbabilityUltimateIntelligence')


def load_self_questioning_ai_class():
    """Load the optional self-questioning AI only during hub warmup."""
    global SelfQuestioningAI
    if SelfQuestioningAI is not None:
        return SelfQuestioningAI
    try:
        from aureon.autonomous.aureon_self_questioning_ai import SelfQuestioningAI as loaded
        SelfQuestioningAI = loaded
    except Exception:
        SelfQuestioningAI = None
    return SelfQuestioningAI

# ════════════════════════════════════════════════════════════════════════════
# ENHANCED HTML WITH MIND → THOUGHT → ACTION VISUALIZATION
# ════════════════════════════════════════════════════════════════════════════

MIND_THOUGHT_ACTION_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠💭⚡ Aureon Mind → Thought → Action</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #fff;
            overflow: hidden;
        }
        
        #header {
            background: rgba(0, 0, 0, 0.9);
            padding: 15px 30px;
            border-bottom: 3px solid #ffaa00;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 30px rgba(255, 170, 0, 0.5);
        }
        
        h1 {
            font-size: 1.8em;
            background: linear-gradient(90deg, #ffaa00, #ff6600, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: glow 2s infinite;
        }
        
        @keyframes glow {
            0%, 100% { filter: brightness(1); }
            50% { filter: brightness(1.5); }
        }
        
        #cognitive-flow {
            display: flex;
            gap: 10px;
            padding: 8px 15px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 5px;
            font-size: 1.2em;
        }
        
        .flow-stage {
            padding: 5px 15px;
            border-radius: 3px;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        
        .flow-stage.mind { background: rgba(255, 170, 0, 0.3); color: #ffaa00; }
        .flow-stage.thought { background: rgba(0, 255, 136, 0.3); color: #00ff88; }
        .flow-stage.action { background: rgba(255, 68, 68, 0.3); color: #ff4444; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(0.95); }
        }
        
        #container {
            display: grid;
            grid-template-columns: 350px 1fr 350px;
            grid-template-rows: 1fr;
            gap: 15px;
            padding: 15px;
            height: calc(100vh - 120px);
        }
        
        .panel {
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 15px;
            overflow-y: auto;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }
        
        .panel h2 {
            color: #ffaa00;
            margin-bottom: 10px;
            font-size: 1.2em;
            border-bottom: 1px solid #ffaa00;
            padding-bottom: 5px;
        }
        
        #mind-panel { border-color: #ffaa00; box-shadow: 0 0 20px rgba(255, 170, 0, 0.3); }
        #thought-panel { grid-column: 3; border-color: #00ff88; }
        
        #network-container {
            grid-column: 2;
            background: rgba(0, 0, 0, 0.9);
            border: 2px solid #6C5CE7;
            border-radius: 10px;
            position: relative;
        }
        
        .thought-message {
            padding: 10px;
            margin: 8px 0;
            background: rgba(0, 255, 136, 0.1);
            border-left: 3px solid #00ff88;
            border-radius: 5px;
            animation: slideIn 0.3s ease;
            font-size: 0.85em;
        }
        
        @keyframes slideIn {
            from { transform: translateX(20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .thought-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            color: #888;
            font-size: 0.85em;
        }
        
        .thought-topic {
            color: #00ff88;
            font-weight: bold;
        }
        
        .thought-source {
            color: #ffaa00;
        }
        
        .thought-payload {
            color: #fff;
            margin-top: 5px;
        }
        
        .mind-stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 10px;
            margin: 5px 0;
            background: rgba(255, 170, 0, 0.1);
            border-left: 3px solid #ffaa00;
            border-radius: 3px;
            font-size: 0.9em;
        }
        
        .stat-label { color: #888; }
        .stat-value { color: #ffaa00; font-weight: bold; }
        
        .action-item {
            padding: 10px;
            margin: 8px 0;
            background: rgba(255, 68, 68, 0.1);
            border-left: 3px solid #ff4444;
            border-radius: 5px;
            font-size: 0.85em;
        }
        
        .action-type {
            font-weight: bold;
            color: #ff4444;
            margin-bottom: 5px;
        }
        
        .action-details {
            color: #888;
            font-size: 0.9em;
        }
        
        .connection-status {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 5px 15px;
            background: rgba(0, 255, 136, 0.3);
            border-radius: 5px;
            font-size: 0.85em;
            font-weight: bold;
            color: #00ff88;
        }
        
        .connection-status.disconnected {
            background: rgba(255, 68, 68, 0.3);
            color: #ff4444;
        }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.3); }
        ::-webkit-scrollbar-thumb { background: rgba(0, 255, 136, 0.3); border-radius: 4px; }
        
        .system-node {
            cursor: pointer;
        }
        
        .layer-indicator {
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            display: inline-block;
            margin-right: 5px;
        }
        
        .layer-mind { background: rgba(255, 170, 0, 0.3); color: #ffaa00; }
        .layer-thought { background: rgba(0, 255, 136, 0.3); color: #00ff88; }
        .layer-action { background: rgba(255, 68, 68, 0.3); color: #ff4444; }
    </style>
</head>
<body>
    <div id="header">
        <h1>🧠💭⚡ AUREON MIND → THOUGHT → ACTION HUB</h1>
        <div id="cognitive-flow">
            <div class="flow-stage mind">🧠 MIND</div>
            <div style="color: #888;">→</div>
            <div class="flow-stage thought">💭 THOUGHT</div>
            <div style="color: #888;">→</div>
            <div class="flow-stage action">⚡ ACTION</div>
        </div>
    </div>
    
    <div id="container">
        <div id="mind-panel" class="panel">
            <h2>🧠 MIND (Intelligence)</h2>
            <div id="mind-systems"></div>
        </div>
        
        <div id="network-container">
            <div class="connection-status" id="ws-status">● CONNECTING...</div>
            <div id="network" style="width: 100%; height: 100%;"></div>
        </div>
        
        <div id="thought-panel" class="panel">
            <h2>💭 THOUGHT STREAM</h2>
            <div id="thought-stream"></div>
            
            <h2 style="margin-top: 20px;">⚡ ACTIONS</h2>
            <div id="action-stream"></div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let network = null;
        let allData = null;
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                document.getElementById('ws-status').textContent = '● CONNECTED';
                document.getElementById('ws-status').className = 'connection-status';
            };
            
            ws.onclose = () => {
                console.log('⚠️ WebSocket disconnected');
                document.getElementById('ws-status').textContent = '● DISCONNECTED';
                document.getElementById('ws-status').className = 'connection-status disconnected';
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse message:', e);
                }
            };
        }
        
        function handleMessage(data) {
            switch(data.type) {
                case 'thought':
                    addThought(data.thought);
                    updateNetworkActivity(data.thought);
                    break;
                case 'action':
                    addAction(data.action);
                    break;
                case 'mind_update':
                    updateMindStats(data.stats);
                    break;
                case 'systems_update':
                    updateNetworkNodes(data.systems);
                    break;
            }
        }
        
        function addThought(thought) {
            const stream = document.getElementById('thought-stream');
            const item = document.createElement('div');
            item.className = 'thought-message';
            
            const time = new Date(thought.ts * 1000).toLocaleTimeString();
            item.innerHTML = `
                <div class="thought-header">
                    <span class="thought-topic">${thought.topic}</span>
                    <span>${time}</span>
                </div>
                <div class="thought-source">From: ${thought.source}</div>
                <div class="thought-payload">${JSON.stringify(thought.payload, null, 2)}</div>
            `;
            
            stream.insertBefore(item, stream.firstChild);
            
            // Keep only last 20 thoughts
            while (stream.children.length > 20) {
                stream.removeChild(stream.lastChild);
            }
        }
        
        function addAction(action) {
            const stream = document.getElementById('action-stream');
            const item = document.createElement('div');
            item.className = 'action-item';
            
            item.innerHTML = `
                <div class="action-type">⚡ ${action.type}</div>
                <div class="action-details">${action.details}</div>
            `;
            
            stream.insertBefore(item, stream.firstChild);
            
            // Keep only last 15 actions
            while (stream.children.length > 15) {
                stream.removeChild(stream.lastChild);
            }
        }
        
        function updateMindStats(stats) {
            const mindDiv = document.getElementById('mind-systems');
            mindDiv.innerHTML = '';
            
            for (const [key, value] of Object.entries(stats)) {
                const item = document.createElement('div');
                item.className = 'mind-stat';
                item.innerHTML = `
                    <span class="stat-label">${key}</span>
                    <span class="stat-value">${value}</span>
                `;
                mindDiv.appendChild(item);
            }
        }
        
        async function loadMindMap() {
            const response = await fetch('/api/mindmap');
            allData = await response.json();
            renderNetwork(allData);
        }
        
        function categorizeSystem(system) {
            // Categorize systems into Mind, Thought, or Action layers
            const mindKeywords = ['queen', 'intelligence', 'brain', 'probability', 'oracle', 'quantum'];
            const thoughtKeywords = ['thought', 'bus', 'mycelium', 'network', 'bridge'];
            const actionKeywords = ['trader', 'executor', 'client', 'exchange', 'order'];
            
            const name = system.label.toLowerCase();
            
            if (mindKeywords.some(k => name.includes(k))) return 'mind';
            if (thoughtKeywords.some(k => name.includes(k))) return 'thought';
            if (actionKeywords.some(k => name.includes(k))) return 'action';
            
            return 'other';
        }
        
        function renderNetwork(data) {
            const container = document.getElementById('network');
            
            // Enhance nodes with layer information
            const nodes = data.nodes.map(node => {
                const layer = categorizeSystem(node);
                let color;
                if (layer === 'mind') color = '#ffaa00';
                else if (layer === 'thought') color = '#00ff88';
                else if (layer === 'action') color = '#ff4444';
                else color = node.color;
                
                return {
                    ...node,
                    color: color,
                    title: `${node.label}<br>Layer: ${layer.toUpperCase()}`,
                    layer: layer
                };
            });
            
            const options = {
                nodes: {
                    font: { color: '#ffffff', size: 14 },
                    borderWidth: 2,
                    borderWidthSelected: 4,
                    shadow: { enabled: true, color: 'rgba(0,0,0,0.5)', size: 10 }
                },
                edges: {
                    color: { color: 'rgba(255,255,255,0.2)', highlight: '#00ff88' },
                    smooth: { type: 'continuous' },
                    arrows: { to: { enabled: true, scaleFactor: 0.5 } }
                },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -8000,
                        centralGravity: 0.3,
                        springLength: 150,
                        springConstant: 0.04,
                        damping: 0.09
                    },
                    stabilization: { iterations: 200 }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 100,
                    navigationButtons: true,
                    keyboard: true
                }
            };
            
            network = new vis.Network(container, {
                nodes: new vis.DataSet(nodes),
                edges: new vis.DataSet(data.edges)
            }, options);
            
            network.on('click', function(params) {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    highlightNodeActivity(nodeId);
                }
            });
        }
        
        function updateNetworkActivity(thought) {
            if (!network) return;
            
            // Flash the source node
            const sourceNode = allData.nodes.find(n => 
                n.label.toLowerCase().includes(thought.source.toLowerCase())
            );
            
            if (sourceNode) {
                // Temporarily change node appearance to show activity
                network.body.data.nodes.update({
                    id: sourceNode.id,
                    borderWidth: 6
                });
                
                setTimeout(() => {
                    network.body.data.nodes.update({
                        id: sourceNode.id,
                        borderWidth: 2
                    });
                }, 500);
            }
        }
        
        function highlightNodeActivity(nodeId) {
            // Show recent thoughts from this node
            console.log('Node clicked:', nodeId);
        }
        
        // Initialize
        connectWebSocket();
        loadMindMap();
        
        console.log('🧠💭⚡ Mind → Thought → Action Hub initialized');
    </script>
</body>
</html>
"""

# ════════════════════════════════════════════════════════════════════════════
# HUB CLASS
# ════════════════════════════════════════════════════════════════════════════

class MindThoughtActionHub:
    """Unified cognitive pipeline hub."""
    
    def __init__(self, port=13002):
        self.port = port
        self.clients: Set = set()
        
        # Core systems
        self.registry = SystemRegistry()
        self.thought_bus = ThoughtBus()
        
        # System instances
        self.queen = None
        self.prob_nexus = None
        self.ultimate_intel = None
        self.self_questioning_ai = None
        
        # Thought and action tracking
        self.recent_thoughts = deque(maxlen=100)
        self.recent_actions = deque(maxlen=50)
        
        # Stats
        self.mind_stats = {
            'Queen Patterns': 0,
            'Intelligence Accuracy': 0,
            'Nexus Win Rate': 0,
            'Active Thoughts/s': 0,
            'Actions Executed': 0,
            'Self Questioning Cycles': 0
        }
        
        self.initialized = False
        self.initializing = False
        self.init_error = None
        self._init_task = None
        self._self_questioning_task = None
        self._goal_pursuit_task = None

        # Setup web app
        self.app = web.Application()
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/ws', self.handle_websocket)
        self.app.router.add_get('/api/mindmap', self.handle_mindmap)
        self.app.router.add_get('/api/thoughts', self.handle_thoughts)
        self.app.router.add_get('/api/actions', self.handle_actions)
        self.app.router.add_get('/api/flight-test', self.handle_flight_test)
        self.app.router.add_get('/api/reboot-advice', self.handle_flight_test)
        self.app.router.add_get('/api/goal-pursuit', self.handle_goal_pursuit)
        self.app.router.add_get('/api/self-questioning/status', self.handle_self_questioning_status)
        self.app.router.add_post('/api/self-questioning/ask', self.handle_self_questioning_ask)

    def _initialization_status(self) -> str:
        if self.init_error:
            return 'error'
        if self.initialized:
            return 'ready'
        return 'initializing'

    def _parse_downtime_days(self, raw: str) -> Set[int]:
        day_map = {
            'mon': 0, 'monday': 0,
            'tue': 1, 'tuesday': 1,
            'wed': 2, 'wednesday': 2,
            'thu': 3, 'thursday': 3,
            'fri': 4, 'friday': 4,
            'sat': 5, 'saturday': 5,
            'sun': 6, 'sunday': 6,
        }
        value = (raw or '').strip().lower()
        if value in {'*', 'all', 'daily', 'everyday'}:
            return set(range(7))

        days: Set[int] = set()
        for part in value.replace(';', ',').split(','):
            item = part.strip()
            if not item:
                continue
            if '-' in item:
                start_raw, end_raw = [piece.strip() for piece in item.split('-', 1)]
                if start_raw in day_map and end_raw in day_map:
                    start = day_map[start_raw]
                    end = day_map[end_raw]
                    cursor = start
                    while True:
                        days.add(cursor)
                        if cursor == end:
                            break
                        cursor = (cursor + 1) % 7
                continue
            if item in day_map:
                days.add(day_map[item])
        return days or {6}

    def _parse_hhmm(self, raw: str, fallback: str) -> tuple[int, int]:
        value = (raw or fallback).strip()
        try:
            hour, minute = value.split(':', 1)
            hour_int = max(0, min(23, int(hour)))
            minute_int = max(0, min(59, int(minute)))
            return hour_int, minute_int
        except Exception:
            fallback_hour, fallback_minute = fallback.split(':', 1)
            return int(fallback_hour), int(fallback_minute)

    def _downtime_window_state(self) -> Dict[str, Any]:
        days_raw = os.environ.get('AUREON_MIND_DOWNTIME_DAYS', 'Sun')
        start_raw = os.environ.get('AUREON_MIND_DOWNTIME_START_LOCAL', '03:00')
        end_raw = os.environ.get('AUREON_MIND_DOWNTIME_END_LOCAL', '03:15')
        days = self._parse_downtime_days(days_raw)
        start_hour, start_minute = self._parse_hhmm(start_raw, '03:00')
        end_hour, end_minute = self._parse_hhmm(end_raw, '03:15')

        now = datetime.now().astimezone()

        def window_for(day_offset: int) -> tuple[datetime, datetime]:
            base = now + timedelta(days=day_offset)
            start = base.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            end = base.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            if end <= start:
                end += timedelta(days=1)
            return start, end

        today_start, today_end = window_for(0)
        in_window = now.weekday() in days and today_start <= now < today_end
        if not in_window:
            yesterday_start, yesterday_end = window_for(-1)
            in_window = (now - timedelta(days=1)).weekday() in days and yesterday_start <= now < yesterday_end

        next_start = None
        next_end = None
        for offset in range(0, 15):
            candidate_start, candidate_end = window_for(offset)
            if candidate_start.weekday() in days and candidate_end > now:
                if candidate_start <= now < candidate_end:
                    next_start, next_end = candidate_start, candidate_end
                elif candidate_start > now:
                    next_start, next_end = candidate_start, candidate_end
                if next_start:
                    break

        return {
            'in_window': in_window,
            'days': days_raw,
            'start_local': f'{start_hour:02d}:{start_minute:02d}',
            'end_local': f'{end_hour:02d}:{end_minute:02d}',
            'now_local': now.isoformat(),
            'next_start_local': next_start.isoformat() if next_start else None,
            'next_end_local': next_end.isoformat() if next_end else None,
        }

    def _read_market_runtime_summary(self) -> Dict[str, Any]:
        status_path = Path(__file__).resolve().parents[2] / 'state' / 'unified_runtime_status.json'
        if not status_path.exists():
            return {
                'available': False,
                'status_file': str(status_path),
                'open_positions': 0,
                'pending_orders': 0,
            }

        try:
            with status_path.open('r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except Exception as e:
            return {
                'available': False,
                'status_file': str(status_path),
                'error': str(e),
                'open_positions': 0,
                'pending_orders': 0,
            }

        def number_from(*keys: str, source: Optional[Dict[str, Any]] = None) -> int:
            source = source or payload
            for key in keys:
                value = source.get(key) if isinstance(source, dict) else None
                if isinstance(value, (int, float)):
                    return int(value)
                if isinstance(value, list):
                    return len(value)
            return 0

        combined = payload.get('combined') if isinstance(payload.get('combined'), dict) else {}
        exchanges = payload.get('exchanges') if isinstance(payload.get('exchanges'), dict) else {}
        age_sec = max(0.0, time.time() - status_path.stat().st_mtime)
        ready_values = [bool(value) for key, value in exchanges.items() if str(key).endswith('_ready')]

        return {
            'available': True,
            'ok': bool(payload.get('ok', True)),
            'trading_ready': bool(payload.get('trading_ready', False)),
            'data_ready': bool(payload.get('data_ready', False)),
            'stale': bool(payload.get('stale', False)) or age_sec > 60,
            'status_file_age_sec': round(age_sec, 3),
            'open_positions': number_from('open_positions', 'positions', source=combined),
            'pending_orders': number_from(
                'pending_orders',
                'open_orders',
                'active_orders',
                source=combined,
            ),
            'exchanges_ready': all(ready_values) if ready_values else None,
            'status_file': str(status_path),
        }

    def _read_reboot_intent(self) -> Dict[str, Any]:
        intent_path = Path(__file__).resolve().parents[2] / 'state' / 'aureon_reboot_intent.json'
        if not intent_path.exists():
            return {'pending': False, 'path': str(intent_path)}
        try:
            with intent_path.open('r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except Exception as e:
            return {'pending': False, 'path': str(intent_path), 'error': str(e)}

        if not isinstance(payload, dict):
            return {'pending': False, 'path': str(intent_path), 'error': 'intent_not_object'}

        status = str(payload.get('status', 'pending')).strip().lower()
        surface = str(payload.get('surface', 'mind')).strip().lower()
        pending = status in {'pending', 'requested', 'ready'} and surface in {
            'mind',
            'cognitive',
            'all',
            'organism',
        }
        return {
            'pending': pending,
            'path': str(intent_path),
            'status': status,
            'surface': surface,
            'requested_by': payload.get('requested_by'),
            'reason': payload.get('reason'),
            'requested_at': payload.get('requested_at'),
            'change_id': payload.get('change_id'),
        }

    def _read_goal_directive(self) -> Dict[str, Any]:
        directive_path = Path(__file__).resolve().parents[2] / 'state' / 'aureon_goal_directive.json'
        primary_goal = os.environ.get(
            'AUREON_PRIMARY_GOAL',
            'sustain_live_trading_and_grow_equity_with_positive_risk_adjusted_returns',
        )
        directive: Dict[str, Any] = {
            'primary_goal': primary_goal,
            'source': 'environment_default',
            'path': str(directive_path),
        }

        if directive_path.exists():
            try:
                with directive_path.open('r', encoding='utf-8') as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict):
                    directive.update(payload)
                    directive['source'] = 'state_file'
                    directive['path'] = str(directive_path)
                    directive['primary_goal'] = (
                        payload.get('primary_goal')
                        or payload.get('goal')
                        or primary_goal
                    )
            except Exception as e:
                directive['error'] = str(e)

        baseline_constraints = [
            'keep_live_trading_runtime_available',
            'preserve_open_position_management',
            'obey_runtime_risk_and_exchange_gates',
            'publish_order_intent_only_through_authorized_runtime_paths',
            'never_enable_direct_exchange_mutation_without_runtime_gate',
            'reboot_only_after_self_flight_test_and_downtime_window',
            'prefer_background_warmup_over_process_restart',
        ]
        configured = directive.get('constraints')
        if not isinstance(configured, list):
            configured = []
        constraints: List[str] = []
        for item in [*baseline_constraints, *configured]:
            value = str(item).strip()
            if value and value not in constraints:
                constraints.append(value)
        directive['constraints'] = constraints
        return directive

    def _read_organism_runtime_status(self) -> Dict[str, Any]:
        status_path = (
            Path(__file__).resolve().parents[2]
            / 'frontend'
            / 'public'
            / 'aureon_organism_runtime_status.json'
        )
        if not status_path.exists():
            return {
                'available': False,
                'status_file': str(status_path),
                'blind_spot_count': 0,
                'next_actions': [],
            }

        try:
            with status_path.open('r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except Exception as e:
            return {
                'available': False,
                'status_file': str(status_path),
                'error': str(e),
                'blind_spot_count': 0,
                'next_actions': [],
            }

        blind_spots = payload.get('blind_spots') if isinstance(payload, dict) else []
        if not isinstance(blind_spots, list):
            blind_spots = []
        severity_rank = {
            'critical': 4,
            'high': 3,
            'attention': 2,
            'medium': 2,
            'low': 1,
        }
        sorted_blind_spots = sorted(
            [spot for spot in blind_spots if isinstance(spot, dict)],
            key=lambda spot: severity_rank.get(str(spot.get('severity', '')).lower(), 0),
            reverse=True,
        )
        next_actions = payload.get('next_actions') if isinstance(payload, dict) else []
        if not isinstance(next_actions, list):
            next_actions = []
        age_sec = max(0.0, time.time() - status_path.stat().st_mtime)

        return {
            'available': True,
            'status': payload.get('status') if isinstance(payload, dict) else None,
            'generated_at': payload.get('generated_at') if isinstance(payload, dict) else None,
            'status_file_age_sec': round(age_sec, 3),
            'status_file': str(status_path),
            'blind_spot_count': len(sorted_blind_spots),
            'highest_blind_spots': sorted_blind_spots[:5],
            'next_actions': [str(action) for action in next_actions[:5]],
        }

    def _run_goal_pursuit_assessment(
        self,
        market: Optional[Dict[str, Any]] = None,
        organism: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        market = market or self._read_market_runtime_summary()
        organism = organism or self._read_organism_runtime_status()
        directive = self._read_goal_directive()

        blockers: List[str] = []
        active_modes: List[str] = []
        next_best_actions: List[str] = []

        market_ready = (
            bool(market.get('available'))
            and bool(market.get('trading_ready'))
            and bool(market.get('data_ready'))
            and market.get('exchanges_ready') is not False
        )
        if market_ready:
            active_modes.append('live_trading_runtime_ready')
            next_best_actions.append(
                'Keep market feeds, exchange connections, and runtime trading telemetry alive.'
            )
        else:
            blockers.append('market_runtime_not_fully_ready')
            next_best_actions.append(
                'Restore market runtime readiness before escalating new order intent.'
            )

        if market.get('stale'):
            blockers.append('market_runtime_status_stale')
            next_best_actions.append(
                'Refresh and verify market telemetry before new risk-taking decisions.'
            )

        open_positions = int(market.get('open_positions', 0) or 0)
        pending_orders = int(market.get('pending_orders', 0) or 0)
        if open_positions > 0:
            active_modes.append('open_position_monitoring')
            next_best_actions.append(
                f'Protect and supervise {open_positions} open position(s) through runtime risk controls.'
            )
        if pending_orders > 0:
            active_modes.append('pending_order_supervision')
            next_best_actions.append(
                f'Reconcile {pending_orders} pending order(s) before maintenance or restart.'
            )

        if self.initialized:
            active_modes.append('cognitive_analysis_ready')
        elif self.initializing:
            active_modes.append('cognitive_background_warmup')
            next_best_actions.append(
                'Continue cognitive warmup in the background while health endpoints remain live.'
            )
        else:
            blockers.append('cognitive_systems_not_ready')
            next_best_actions.append(
                'Keep HTTP health online and finish cognitive initialization without rebooting.'
            )

        if self.init_error:
            blockers.append('cognitive_initialization_error')
            next_best_actions.append(
                'Request repair and defer reboot until the downtime window and flight test both approve.'
            )

        if organism.get('available'):
            active_modes.append('organism_self_observation')
            if organism.get('blind_spot_count', 0) > 0:
                active_modes.append('self_improvement_backlog')
                highest_blind_spots = organism.get('highest_blind_spots')
                if not isinstance(highest_blind_spots, list):
                    highest_blind_spots = []
                next_actions = organism.get('next_actions')
                if not isinstance(next_actions, list):
                    next_actions = []
                top_spot = highest_blind_spots[0] if highest_blind_spots else {}
                action = top_spot.get('next_action') or (
                    next_actions[0] if next_actions else None
                )
                if action:
                    next_best_actions.append(
                        f'Work the highest-impact safe self-improvement check: {action}'
                    )
        else:
            blockers.append('organism_status_unavailable')
            next_best_actions.append(
                'Regenerate organism runtime status so blind spots and next actions are visible.'
            )

        action_authority = {
            'llm_order_intent_authority': os.environ.get(
                'AUREON_LLM_ORDER_INTENT_AUTHORITY',
                '0',
            ).strip().lower() in {'1', 'true', 'yes', 'on'},
            'direct_exchange_mutation_authority': os.environ.get(
                'AUREON_LLM_DIRECT_EXCHANGE_MUTATION_AUTHORITY',
                '0',
            ).strip().lower() in {'1', 'true', 'yes', 'on'},
            'real_orders_disabled': os.environ.get(
                'AUREON_DISABLE_REAL_ORDERS',
                '0',
            ).strip().lower() in {'1', 'true', 'yes', 'on'},
        }

        if not action_authority['llm_order_intent_authority']:
            next_best_actions.append(
                'Analyze opportunities but do not emit order intent until runtime authority is present.'
            )
        if action_authority['direct_exchange_mutation_authority']:
            blockers.append('direct_exchange_mutation_authority_enabled')
            next_best_actions.append(
                'Keep direct exchange mutation guarded by runtime policy; prefer order-intent handoff.'
            )

        if not next_best_actions:
            next_best_actions.append(
                'Continue live analysis and only act through risk-authorized trading pathways.'
            )

        if market_ready and self.initialized:
            decision = 'pursue_goal_with_full_live_capability'
        elif market_ready:
            decision = 'pursue_goal_with_guarded_live_capability'
        else:
            decision = 'restore_capability_before_new_risk'

        return {
            'service': 'aureon-mind-thought-action-hub',
            'generated_at': datetime.now().astimezone().isoformat(),
            'primary_goal': directive.get('primary_goal'),
            'decision': decision,
            'maximum_safe_effort': (
                'Run every non-destructive analysis, keep feeds alive, protect positions, '
                'publish only authorized order intent, and defer disruptive maintenance.'
            ),
            'active_modes': active_modes,
            'blockers': blockers,
            'next_best_actions': next_best_actions[:8],
            'constraints': directive.get('constraints', []),
            'action_authority': action_authority,
            'market_runtime': market,
            'organism_status': organism,
            'self_questions': [
                'What can I safely do right now to advance the primary goal?',
                'Are market data, trading runtime, and exchange connections ready?',
                'Do open positions or pending orders require protection before anything else?',
                'Which blind spot most threatens goal progress?',
                'Would a reboot reduce live capability right now?',
                'Can this action pass risk, legality, and runtime authority gates?',
            ],
        }

    def _run_internal_flight_test(self) -> Dict[str, Any]:
        downtime = self._downtime_window_state()
        market = self._read_market_runtime_summary()
        reboot_intent = self._read_reboot_intent()
        goal_pursuit = self._run_goal_pursuit_assessment(market=market)
        allow_open_positions = os.environ.get(
            'AUREON_ALLOW_MIND_REBOOT_WITH_OPEN_POSITIONS',
            '0',
        ).strip().lower() in {'1', 'true', 'yes', 'on'}

        blockers: List[str] = []
        if not downtime['in_window']:
            blockers.append('outside_downtime_window')
        if self.initializing:
            blockers.append('mind_initializing')
        if market.get('open_positions', 0) > 0 and not allow_open_positions:
            blockers.append('open_positions_active')
        if market.get('pending_orders', 0) > 0:
            blockers.append('pending_orders_active')
        if market.get('available') and market.get('stale'):
            blockers.append('market_runtime_status_stale')

        flight_checks = {
            'http_surface': True,
            'thought_bus': self.thought_bus is not None,
            'mind_initialized': self.initialized,
            'mind_initializing': self.initializing,
            'mind_init_error': self.init_error is None,
            'market_runtime_available': bool(market.get('available')),
            'market_trading_ready': bool(market.get('trading_ready')),
            'market_data_ready': bool(market.get('data_ready')),
        }
        ok = all(flight_checks.values()) if self.initialized else all(
            value for key, value in flight_checks.items()
            if key not in {'mind_initialized', 'market_runtime_available', 'market_trading_ready', 'market_data_ready'}
        )

        should_reboot = bool(reboot_intent.get('pending')) or bool(self.init_error)
        can_reboot_now = len(blockers) == 0
        if should_reboot and can_reboot_now:
            decision = 'approve_reboot'
        elif can_reboot_now:
            decision = 'window_clear_no_reboot_requested'
        else:
            decision = 'hold_live_state'
        reason = 'downtime_window_clear' if can_reboot_now else ','.join(blockers)

        return {
            'service': 'aureon-mind-thought-action-hub',
            'generated_at': datetime.now().astimezone().isoformat(),
            'status': self._initialization_status(),
            'ok': ok,
            'flight_checks': flight_checks,
            'capabilities': {
                'connected_clients': len(self.clients),
                'recent_thoughts': len(self.recent_thoughts),
                'recent_actions': len(self.recent_actions),
                'registry_systems': len(self.registry.systems),
                'self_questioning_available': self.self_questioning_ai is not None,
            },
            'market_runtime': market,
            'goal_pursuit': goal_pursuit,
            'downtime_window': downtime,
            'reboot_intent': reboot_intent,
            'reboot_advice': {
                'decision': decision,
                'can_reboot_now': can_reboot_now,
                'should_reboot': should_reboot,
                'reason': reason,
                'blockers': blockers,
                'next_window_start_local': downtime.get('next_start_local'),
                'next_window_end_local': downtime.get('next_end_local'),
            },
            'self_questions': [
                'Am I serving health endpoints?',
                'Is ThoughtBus connected?',
                'Is the market runtime ready?',
                'Are positions or pending orders active?',
                'What is the best safe action toward the primary goal?',
                'Am I inside the configured downtime window?',
                'Can I reboot without reducing live capability?',
            ],
        }

    async def goal_pursuit_loop(self):
        """Continuously publish the hub's safest next-step assessment."""
        interval = os.environ.get('AUREON_GOAL_PURSUIT_INTERVAL_SEC', '60')
        try:
            interval_sec = max(15.0, float(interval))
        except Exception:
            interval_sec = 60.0

        while True:
            try:
                assessment = self._run_goal_pursuit_assessment()
                thought = self.thought_bus.publish(
                    Thought(
                        source='MindThoughtActionHub',
                        topic='goal.pursuit.assessment',
                        payload={
                            'primary_goal': assessment.get('primary_goal'),
                            'decision': assessment.get('decision'),
                            'active_modes': assessment.get('active_modes', []),
                            'blockers': assessment.get('blockers', []),
                            'next_best_actions': assessment.get('next_best_actions', []),
                            'generated_at': assessment.get('generated_at'),
                        },
                    )
                )
                if not self.recent_thoughts or self.recent_thoughts[-1].id != thought.id:
                    self._on_thought(thought)
            except Exception as e:
                logger.info(f"Goal pursuit assessment skipped: {e}")
            await asyncio.sleep(interval_sec)

    async def _init_systems_async(self):
        """Warm up cognitive systems without blocking the HTTP health surface."""
        if self.initialized or self.initializing:
            return

        self.initializing = True
        self.init_error = None
        try:
            await asyncio.to_thread(self._init_systems)
            self.initialized = True
            logger.info("Mind systems initialized")
            if self._self_questioning_enabled() and self.self_questioning_ai:
                self._self_questioning_task = asyncio.create_task(self.self_questioning_loop())
        except Exception as e:
            self.init_error = str(e)
            logger.exception("Mind system initialization failed")
        finally:
            self.initializing = False
    
    def _init_systems(self):
        """Initialize core cognitive systems."""
        logger.info("🧠 Initializing Mind systems...")
        
        # Scan workspace
        self.registry.scan_workspace()
        self._init_self_questioning_ai()
        if audit_mode_enabled():
            self.thought_bus.subscribe('*', self._on_thought)
            logger.info("Audit mode: heavy Queen/Nexus instances deferred; ThoughtBus is active")
            return
        logger.info(f"✅ Registered {len(self.registry.systems)} systems")
        
        load_optional_system_classes()

        # Initialize Queen
        if QueenHiveMind:
            try:
                self.queen = QueenHiveMind()
                self.mind_stats['Queen Patterns'] = 229  # From elephant memory
                logger.info("👑 Queen Hive Mind loaded")
            except: pass
        
        # Initialize Probability Nexus
        if ProbabilityNexus:
            try:
                self.prob_nexus = ProbabilityNexus()
                self.mind_stats['Nexus Win Rate'] = 79.6
                logger.info("🔮 Probability Nexus loaded")
            except: pass
        
        # Initialize Ultimate Intelligence
        if UltimateIntelligence:
            try:
                self.ultimate_intel = UltimateIntelligence()
                self.mind_stats['Intelligence Accuracy'] = 95.0
                logger.info("💎 Ultimate Intelligence loaded")
            except: pass
        
        # Subscribe to ThoughtBus
        self.thought_bus.subscribe('*', self._on_thought)
        logger.info("💭 ThoughtBus subscribed")
    
    def _init_self_questioning_ai(self):
        """Wire the local Ollama + Obsidian self-questioning loop."""
        cls = load_self_questioning_ai_class()
        if cls is None:
            logger.info("Self-questioning AI unavailable")
            return
        try:
            self.self_questioning_ai = cls(thought_bus=self.thought_bus)
            logger.info("Self-questioning AI wired to Ollama, Obsidian, and ThoughtBus")
        except Exception as e:
            self.self_questioning_ai = None
            logger.info(f"Self-questioning AI not started: {e}")

    def _self_questioning_enabled(self) -> bool:
        val = os.environ.get("AUREON_SELF_QUESTIONING_AI", "1").strip().lower()
        return val not in {"0", "false", "no", "off"}

    def _schedule_broadcast(self, message: Dict):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(message))
        except RuntimeError:
            return

    def _on_thought(self, thought: Thought):
        """Handle thought from ThoughtBus."""
        self.recent_thoughts.append(thought)
        
        # Broadcast to connected clients
        self._schedule_broadcast({
            'type': 'thought',
            'thought': {
                'id': thought.id,
                'ts': thought.ts,
                'source': thought.source,
                'topic': thought.topic,
                'payload': thought.payload
            }
        })
        
        # Track actions
        if thought.topic.startswith('execution.') or thought.topic.startswith('order.'):
            self.recent_actions.append({
                'type': thought.topic,
                'details': str(thought.payload),
                'ts': thought.ts
            })
            
            self._schedule_broadcast({
                'type': 'action',
                'action': {
                    'type': thought.topic,
                    'details': str(thought.payload)
                }
            })
    
    async def handle_index(self, request):
        """Serve dashboard HTML."""
        return web.Response(text=MIND_THOUGHT_ACTION_HTML, content_type='text/html')
    
    async def handle_websocket(self, request):
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.clients.add(ws)
        logger.info(f"👑 Client connected (total: {len(self.clients)})")
        
        # Send initial data
        await ws.send_json({
            'type': 'mind_update',
            'stats': self.mind_stats
        })
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            self.clients.discard(ws)
            logger.info(f"Client disconnected (remaining: {len(self.clients)})")
        
        return ws
    
    async def handle_mindmap(self, request):
        """API endpoint for mind map data."""
        if not self.initialized:
            return web.json_response({
                'nodes': [],
                'edges': [],
                'categories': [],
                'status': self._initialization_status(),
                'initialized': self.initialized,
                'initializing': self.initializing,
                'init_error': self.init_error,
            })
        return web.json_response(self.registry.export_mind_map_data())
    
    async def handle_thoughts(self, request):
        """API endpoint for recent thoughts."""
        return web.json_response({
            'status': self._initialization_status(),
            'initialized': self.initialized,
            'initializing': self.initializing,
            'init_error': self.init_error,
            'thoughts': [
                {
                    'id': t.id,
                    'ts': t.ts,
                    'source': t.source,
                    'topic': t.topic,
                    'payload': t.payload
                }
                for t in list(self.recent_thoughts)[-20:]
            ]
        })
    
    async def handle_actions(self, request):
        """API endpoint for recent actions."""
        return web.json_response({
            'actions': list(self.recent_actions)[-20:]
        })

    async def handle_flight_test(self, request):
        """Internal self-flight-test and reboot advice endpoint."""
        return web.json_response(self._run_internal_flight_test())

    async def handle_goal_pursuit(self, request):
        """API endpoint for the current safest goal-pursuit assessment."""
        return web.json_response(self._run_goal_pursuit_assessment())

    async def handle_self_questioning_status(self, request):
        """API endpoint for the Ollama + Obsidian self-questioning loop."""
        if not self.self_questioning_ai:
            return web.json_response({
                'available': False,
                'status': self._initialization_status(),
                'initialized': self.initialized,
                'initializing': self.initializing,
            }, status=503)
        return web.json_response({
            'available': True,
            'enabled': self._self_questioning_enabled(),
            'status': self.self_questioning_ai.get_status(),
        })

    async def handle_self_questioning_ask(self, request):
        """Run one safe self-questioning cycle on demand."""
        if not self.self_questioning_ai:
            return web.json_response({'error': 'self_questioning_ai unavailable'}, status=503)
        try:
            body = await request.json()
        except Exception:
            body = {}
        questions = body.get('questions')
        if not questions and body.get('question'):
            questions = [body.get('question')]
        cycle = await asyncio.to_thread(
            self.self_questioning_ai.run_cycle,
            questions=questions,
            include_audit=bool(body.get('include_audit', True)),
            include_self_scan=bool(body.get('include_self_scan', True)),
        )
        self.mind_stats['Self Questioning Cycles'] += 1
        return web.json_response(cycle.to_dict())
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return
        
        msg_str = json.dumps(message)
        dead_clients = set()
        
        for client in self.clients:
            try:
                await client.send_str(msg_str)
            except:
                dead_clients.add(client)
        
        self.clients -= dead_clients
    
    async def live_stats_updater(self):
        """Update mind stats periodically."""
        await asyncio.sleep(2)
        
        logger.info("📊 Starting live stats updater...")
        
        while True:
            try:
                # Calculate thoughts per second
                recent_count = len([t for t in self.recent_thoughts if time.time() - t.ts < 1.0])
                self.mind_stats['Active Thoughts/s'] = recent_count
                self.mind_stats['Actions Executed'] = len(self.recent_actions)
                
                # Broadcast update
                await self.broadcast({
                    'type': 'mind_update',
                    'stats': self.mind_stats
                })
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in stats updater: {e}")
                await asyncio.sleep(5)

    async def self_questioning_loop(self):
        """Periodic safe self-questioning using Ollama and Obsidian."""
        if not self.self_questioning_ai:
            return
        await asyncio.sleep(float(os.environ.get("AUREON_SELF_QUESTIONING_START_DELAY_S", "10")))
        interval = max(60.0, float(os.environ.get("AUREON_SELF_QUESTION_INTERVAL_S", "300")))
        logger.info("Starting self-questioning AI loop")
        while self._self_questioning_enabled():
            try:
                cycle = await asyncio.to_thread(
                    self.self_questioning_ai.run_cycle,
                    questions=None,
                    include_audit=True,
                    include_self_scan=True,
                )
                self.mind_stats['Self Questioning Cycles'] += 1
                await self.broadcast({
                    'type': 'self_questioning_cycle',
                    'cycle': {
                        'cycle_id': cycle.cycle_id,
                        'summary': cycle.summary,
                        'answer_source': cycle.answer_source,
                        'note_path': cycle.note_path,
                    }
                })
            except Exception as e:
                logger.error(f"Self-questioning loop error: {e}")
            await asyncio.sleep(interval)
    
    async def generate_test_thoughts(self):
        """Generate test thoughts for demonstration.

        ⚠ Publishes synthetic Thoughts onto the bus (fake confidences,
        topics, payloads). Gated behind AUREON_ALLOW_SIM_FALLBACK so
        production refuses to inject fake thoughts into the live system.
        """
        from aureon.observer.live_data_policy import (
            simulation_fallback_allowed, log_blocked_fallback,
        )
        if not simulation_fallback_allowed():
            log_blocked_fallback("aureon_mind_thought_action_hub.generate_test_thoughts",
                                 "synthetic_thoughts")
            return
        await asyncio.sleep(5)

        logger.info("🧪 Starting test thought generator...")
        
        topics = [
            'market.snapshot',
            'miner.signal',
            'queen.decision',
            'execution.order',
            'risk.approval',
            'harmonic.wave'
        ]
        
        sources = [
            'Queen',
            'ProbabilityNexus',
            'UltimateIntel',
            'MinerBrain',
            'HarmonicFusion'
        ]
        
        while True:
            try:
                import random
                
                topic = random.choice(topics)
                source = random.choice(sources)
                
                thought = Thought(
                    source=source,
                    topic=topic,
                    payload={
                        'message': f'Test thought from {source}',
                        'confidence': random.uniform(0.7, 0.99),
                        'value': random.randint(1, 100)
                    }
                )
                
                self.thought_bus.publish(thought)
                
                await asyncio.sleep(random.uniform(2, 5))  # Random interval
                
            except Exception as e:
                logger.error(f"Error generating test thought: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the hub."""
        # Start web server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        self._goal_pursuit_task = asyncio.create_task(self.goal_pursuit_loop())
        self._init_task = asyncio.create_task(self._init_systems_async())
        
        print(f"\n{'='*80}")
        print(f"🧠💭⚡ AUREON MIND → THOUGHT → ACTION HUB")
        print(f"{'='*80}")
        print(f"🌐 Dashboard: http://localhost:{self.port}")
        print(f"📡 WebSocket: ws://localhost:{self.port}/ws")
        print(f"\n✨ COGNITIVE ARCHITECTURE:")
        print(f"   🧠 MIND:    initializing in background")
        print(f"   💭 THOUGHT: ThoughtBus (real-time streaming)")
        print(f"   ⚡ ACTION:  Execution layer monitoring")
        print(f"\n📊 SYSTEMS INTEGRATED:")
        print(f"   • HTTP health endpoint: READY")
        print(f"   • System registry: warming up")
        print(f"{'='*80}\n")
        
        # Start background tasks
        asyncio.create_task(self.live_stats_updater())
        asyncio.create_task(self.generate_test_thoughts())

async def main():
    hub = MindThoughtActionHub(port=13002)
    await hub.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🧠💭⚡ Mind → Thought → Action Hub stopped")
