#!/usr/bin/env python3
"""
🗺️ AUREON GLOBAL BOT MAP DASHBOARD 🗺️
═══════════════════════════════════════════════════════════════════════════

Visual dashboard showing:
- World map with bot activity heatmap
- Country rankings (who's moving what)
- Clan/pack tracking (coordinated groups)
- Tidal wave patterns (global flow across timezones)
- Battle zones (high-conflict regions)

Real-time WebSocket updates from Planetary Bot Tracker.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
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
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

import asyncio
import aiohttp
from aiohttp import web
import json
import logging
from datetime import datetime

# Dashboard HTML with world map visualization
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🌍 Aureon Global Bot Map</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 100%);
            color: #00ff88;
            overflow-x: hidden;
        }
        
        #header {
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            text-align: center;
            border-bottom: 3px solid #00ff88;
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.3);
        }
        
        h1 {
            font-size: 2.5em;
            text-shadow: 0 0 20px #00ff88, 0 0 40px #00ff88;
            margin-bottom: 10px;
        }
        
        #subtitle {
            color: #ffaa00;
            font-size: 1.2em;
            text-shadow: 0 0 10px #ffaa00;
        }
        
        #container {
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
            gap: 20px;
            padding: 20px;
            height: calc(100vh - 120px);
        }
        
        .panel {
            background: rgba(0, 0, 0, 0.7);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 15px;
            overflow-y: auto;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
        }
        
        .panel h2 {
            color: #ffaa00;
            margin-bottom: 15px;
            text-align: center;
            font-size: 1.5em;
            text-shadow: 0 0 10px #ffaa00;
        }
        
        #map-container {
            position: relative;
            background: rgba(0, 0, 0, 0.9);
            border-radius: 10px;
            display: flex;
            flex-direction: column;
        }
        
        #world-map {
            flex: 1;
            width: 100%;
            position: relative;
            background-image: 
                radial-gradient(circle at 20% 50%, rgba(0, 255, 136, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 50%, rgba(255, 170, 0, 0.1) 0%, transparent 50%);
        }
        
        .country-marker {
            position: absolute;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00ff88;
            box-shadow: 0 0 15px #00ff88, 0 0 30px #00ff88;
            animation: pulse 2s infinite;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .country-marker:hover {
            transform: scale(2);
            z-index: 100;
        }
        
        .country-marker.high-activity {
            background: #ff3366;
            box-shadow: 0 0 20px #ff3366, 0 0 40px #ff3366;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.3); }
        }
        
        .country-item, .clan-item {
            background: rgba(0, 255, 136, 0.1);
            border-left: 3px solid #00ff88;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            transition: all 0.3s;
        }
        
        .country-item:hover, .clan-item:hover {
            background: rgba(0, 255, 136, 0.2);
            transform: translateX(5px);
        }
        
        .country-item.rank-1 { border-left-color: #ffd700; }
        .country-item.rank-2 { border-left-color: #c0c0c0; }
        .country-item.rank-3 { border-left-color: #cd7f32; }
        
        .stat-line {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        .stat-label { color: #888; }
        .stat-value { 
            color: #00ff88; 
            font-weight: bold;
        }
        
        .aggression-bar {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .aggression-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff88 0%, #ffaa00 50%, #ff3366 100%);
            transition: width 0.5s;
        }
        
        .clan-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            margin-right: 5px;
        }
        
        #stats-bar {
            background: rgba(0, 0, 0, 0.9);
            padding: 10px;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        
        .stat-box {
            text-align: center;
            padding: 10px;
            background: rgba(0, 255, 136, 0.1);
            border-radius: 5px;
            border: 1px solid #00ff88;
        }
        
        .stat-box-label {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .stat-box-value {
            color: #00ff88;
            font-size: 1.5em;
            font-weight: bold;
            text-shadow: 0 0 10px #00ff88;
        }
        
        #tidal-wave {
            height: 100px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 5px;
            position: relative;
            overflow: hidden;
        }
        
        .wave-line {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: #00ff88;
            box-shadow: 0 0 10px #00ff88;
        }
        
        .battle-alert {
            background: rgba(255, 51, 102, 0.2);
            border: 2px solid #ff3366;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
            animation: alert-pulse 1s infinite;
        }
        
        @keyframes alert-pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.3); }
        ::-webkit-scrollbar-thumb { 
            background: #00ff88; 
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div id="header">
        <h1>🌍 AUREON GLOBAL BOT MAP 🌍</h1>
        <div id="subtitle">Tracking the Planetary Tidal Wave</div>
    </div>
    
    <div id="container">
        <!-- Left Panel: Country Rankings -->
        <div class="panel">
            <h2>🏴 COUNTRY RANKINGS</h2>
            <div id="country-list"></div>
        </div>
        
        <!-- Center Panel: World Map + Stats -->
        <div id="map-container">
            <div id="stats-bar">
                <div class="stat-box">
                    <div class="stat-box-label">Total Bots</div>
                    <div class="stat-box-value" id="total-bots">0</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box-label">Active Clans</div>
                    <div class="stat-box-value" id="total-clans">0</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box-label">Most Active</div>
                    <div class="stat-box-value" id="most-active" style="font-size: 1.2em;">---</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box-label">Tidal Strength</div>
                    <div class="stat-box-value" id="tidal-strength">0.0</div>
                </div>
            </div>
            
            <div class="panel" style="flex: 1; position: relative;">
                <h2>🗺️ GLOBAL BOT ACTIVITY</h2>
                <div id="world-map"></div>
                <div id="tidal-wave"></div>
            </div>
            
            <div id="battle-zone"></div>
        </div>
        
        <!-- Right Panel: Clan Tracking -->
        <div class="panel">
            <h2>🐺 CLAN / PACK TRACKING</h2>
            <div id="clan-list"></div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket('ws://localhost:12000');
        
        // Central Hub API for live data
        const HUB_API = 'http://localhost:13001/api';
        
        async function fetchHubData() {
            try {
                const [bots, whales, scanners] = await Promise.all([
                    fetch(HUB_API + '/bots').then(r => r.json()).catch(() => ({})),
                    fetch(HUB_API + '/whales').then(r => r.json()).catch(() => ({})),
                    fetch(HUB_API + '/scanners').then(r => r.json()).catch(() => ({}))
                ]);
                
                // Update total bots from hub
                if (bots.bots_detected) {
                    const uniqueBots = bots.bots_detected.filter(b => b.symbol).length;
                    document.getElementById('total-bots').textContent = uniqueBots + '+';
                }
                
                // Update whales count
                if (whales.total_whale_events) {
                    document.getElementById('total-clans').textContent = whales.total_whale_events;
                }
                
                // Add activity from scanners
                if (scanners.bots) {
                    scanners.bots.slice(0, 3).forEach(s => {
                        if (s.payload && s.payload.firm) {
                            console.log('🌍 Firm activity:', s.payload.firm, s.payload.symbol);
                        }
                    });
                }
                
            } catch (e) {
                console.log('Hub fetch error:', e);
            }
        }
        
        // Poll hub every 3 seconds
        setInterval(fetchHubData, 3000);
        fetchHubData();
        
        // Country to lat/lon mapping (simplified)
        const countryCoords = {
            'USA': { lat: 37.0902, lon: -95.7129 },
            'UK': { lat: 55.3781, lon: -3.4360 },
            'Japan': { lat: 36.2048, lon: 138.2529 },
            'China': { lat: 35.8617, lon: 104.1954 },
            'Hong Kong': { lat: 22.3193, lon: 114.1694 },
            'Singapore': { lat: 1.3521, lon: 103.8198 },
            'Germany': { lat: 51.1657, lon: 10.4515 },
            'France': { lat: 46.2276, lon: 2.2137 },
            'Australia': { lat: -25.2744, lon: 133.7751 },
            'Canada': { lat: 56.1304, lon: -106.3468 },
            'Dubai': { lat: 25.2048, lon: 55.2708 },
            'Malta': { lat: 35.9375, lon: 14.3754 },
            'Luxembourg': { lat: 49.8153, lon: 6.1296 },
            'Seychelles': { lat: -4.6796, lon: 55.4920 },
            'Global': { lat: 0, lon: 0 },
        };
        
        // Convert lat/lon to pixel coordinates
        function latLonToPixel(lat, lon, container) {
            const x = ((lon + 180) / 360) * container.clientWidth;
            const y = ((90 - lat) / 180) * container.clientHeight;
            return { x, y };
        }
        
        ws.onmessage = function(event) {
            const msg = JSON.parse(event.data);
            
            if (msg.type === 'planetary_overview') {
                updateDashboard(msg.data);
            }
        };
        
        function updateDashboard(data) {
            // Update global stats
            document.getElementById('total-bots').textContent = data.stats.total_bots_tracked || 0;
            document.getElementById('total-clans').textContent = data.stats.total_clans_identified || 0;
            document.getElementById('most-active').textContent = data.stats.most_active_country || '---';
            document.getElementById('tidal-strength').textContent = (data.stats.tidal_wave_strength || 0).toFixed(2);
            
            // Update country list
            const countryList = document.getElementById('country-list');
            countryList.innerHTML = data.countries.map((country, index) => `
                <div class="country-item rank-${index + 1}">
                    <div class="stat-line">
                        <span class="stat-label">#${index + 1} ${country.country}</span>
                        <span class="stat-value">${country.bot_count} bots</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Pattern:</span>
                        <span class="stat-value">${country.dominant_pattern}</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Clans:</span>
                        <span class="stat-value">${country.clan_count}</span>
                    </div>
                    <div class="aggression-bar">
                        <div class="aggression-fill" style="width: ${country.aggression * 100}%"></div>
                    </div>
                </div>
            `).join('');
            
            // Update world map markers
            const mapContainer = document.getElementById('world-map');
            mapContainer.innerHTML = '';
            
            data.countries.forEach(country => {
                const coords = countryCoords[country.country.split('/')[0]] || countryCoords['Global'];
                const pixel = latLonToPixel(coords.lat, coords.lon, mapContainer);
                
                const marker = document.createElement('div');
                marker.className = 'country-marker' + (country.bot_count > 10 ? ' high-activity' : '');
                marker.style.left = pixel.x + 'px';
                marker.style.top = pixel.y + 'px';
                marker.style.width = Math.min(20, 5 + country.bot_count / 2) + 'px';
                marker.style.height = Math.min(20, 5 + country.bot_count / 2) + 'px';
                marker.title = `${country.country}: ${country.bot_count} bots`;
                
                mapContainer.appendChild(marker);
            });
            
            // Update clan list
            const clanList = document.getElementById('clan-list');
            clanList.innerHTML = data.clans.map(clan => `
                <div class="clan-item">
                    <div class="stat-line">
                        <span class="clan-badge" style="background: ${clan.color}; color: #000;">${clan.name}</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Country:</span>
                        <span class="stat-value">${clan.country}</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Members:</span>
                        <span class="stat-value">${clan.members}</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Strategy:</span>
                        <span class="stat-value">${clan.strategy}</span>
                    </div>
                </div>
            `).join('');
            
            // Update battle zones
            const battleZone = document.getElementById('battle-zone');
            if (data.active_battles && data.active_battles.length > 0) {
                battleZone.innerHTML = `
                    <div class="battle-alert">
                        <strong>⚔️ ACTIVE BATTLES:</strong> ${data.active_battles.join(', ')}
                    </div>
                `;
            } else {
                battleZone.innerHTML = '';
            }
        }
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        console.log('🌍 Global Bot Map Dashboard initialized');
    </script>
</body>
</html>
"""

class GlobalBotMapDashboard:
    """Dashboard server for global bot visualization."""
    
    def __init__(self, port=12000):
        self.port = port
        self.logger = logging.getLogger(__name__)
        self.app = web.Application()
        self.clients = set()
        
        # Setup routes
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/ws', self.handle_websocket)
    
    async def handle_index(self, request):
        """Serve the dashboard HTML."""
        return web.Response(text=DASHBOARD_HTML, content_type='text/html')
    
    async def handle_websocket(self, request):
        """Handle WebSocket connections."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.clients.add(ws)
        self.logger.info(f"🌐 Client connected (total: {len(self.clients)})")
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
        finally:
            self.clients.discard(ws)
            self.logger.info(f"🌐 Client disconnected (total: {len(self.clients)})")
        
        return ws
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if self.clients:
            msg_str = json.dumps(message)
            for client in list(self.clients):
                try:
                    await client.send_str(msg_str)
                except Exception as e:
                    self.logger.warning(f"Failed to send to client: {e}")
                    self.clients.discard(client)
    
    async def start(self):
        """Start the dashboard server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        self.logger.info(f"🗺️  Global Bot Map Dashboard started on http://localhost:{self.port}")
        print(f"\n{'='*80}")
        print(f"🌍 GLOBAL BOT MAP DASHBOARD")
        print(f"{'='*80}")
        print(f"Dashboard URL: http://localhost:{self.port}")
        print(f"WebSocket URL: ws://localhost:{self.port}/ws")
        print(f"\nTracking:")
        print(f"  • Country rankings (who's moving what)")
        print(f"  • Clan/pack formations (coordinated groups)")
        print(f"  • Tidal wave patterns (global flow)")
        print(f"  • Battle zones (high-conflict regions)")
        print(f"{'='*80}\n")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    dashboard = GlobalBotMapDashboard(port=12000)
    await dashboard.start()
    
    # Keep server running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n\n🌍 Global Bot Map Dashboard stopped")

if __name__ == "__main__":
    asyncio.run(main())
