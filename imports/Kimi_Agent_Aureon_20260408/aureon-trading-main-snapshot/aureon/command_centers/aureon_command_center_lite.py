#!/usr/bin/env python3
"""
🎮👑 AUREON COMMAND CENTER LITE (Windows-Optimized) 👑🎮
═══════════════════════════════════════════════════════════════════════════════

A lightweight version of Command Center that starts FAST on Windows.
Skips heavy system imports - just runs the web dashboard immediately.

Usage:
    python aureon_command_center_lite.py
    
Then open: http://localhost:8888
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Only import aiohttp - nothing else heavy
try:
    from aiohttp import web
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("❌ aiohttp not available - pip install aiohttp")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# MINIMAL HTML DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

LITE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎮👑 AUREON COMMAND CENTER LITE 👑🎮</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a1a 100%);
            color: #00ff88;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 20px;
            text-shadow: 0 0 20px #00ff88;
            animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow {
            from { text-shadow: 0 0 10px #00ff88, 0 0 20px #00ff88; }
            to { text-shadow: 0 0 20px #00ff88, 0 0 40px #00ff88, 0 0 60px #00ff88; }
        }
        .status-box {
            background: rgba(0, 255, 136, 0.1);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .card {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid #00ff88;
            border-radius: 8px;
            padding: 15px;
        }
        .card h3 { color: #ffcc00; margin-bottom: 10px; }
        .stat { font-size: 2em; font-weight: bold; }
        .timestamp { color: #888; font-size: 0.9em; }
        .btn {
            background: linear-gradient(135deg, #00ff88, #00cc66);
            color: #000;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
        }
        .btn:hover { transform: scale(1.05); }
        .btn-danger { background: linear-gradient(135deg, #ff4444, #cc0000); color: #fff; }
        #log-output {
            background: #000;
            border: 1px solid #00ff88;
            border-radius: 5px;
            padding: 10px;
            height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }
        .log-line { margin: 2px 0; }
        .success { color: #00ff88; }
        .warning { color: #ffcc00; }
        .error { color: #ff4444; }
        .info { color: #00ccff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮👑 AUREON COMMAND CENTER LITE 👑🎮</h1>
        <p style="text-align: center; margin-bottom: 20px;">⚡ Windows-Optimized Fast Start Mode</p>
        
        <div class="status-box">
            <h2>🟢 Server Status: ONLINE</h2>
            <p class="timestamp">Started: <span id="start-time"></span></p>
            <p>Port: 8888 | Mode: Lite (Fast Start)</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🚀 Quick Launch</h3>
                <button class="btn" onclick="launchWarRoom()">⚔️ War Room Dashboard</button>
                <button class="btn" onclick="launchDryRun()">🧪 Dry Run Mode</button>
                <button class="btn btn-danger" onclick="launchLive()">💰 LIVE Trading</button>
            </div>
            
            <div class="card">
                <h3>📊 System Info</h3>
                <p>Platform: <span id="platform"></span></p>
                <p>Python: <span id="python-version"></span></p>
                <p>Uptime: <span id="uptime">0s</span></p>
            </div>
            
            <div class="card">
                <h3>🔗 Quick Links</h3>
                <p><a href="/api/status" style="color: #00ff88;">📈 API Status</a></p>
                <p><a href="/api/health" style="color: #00ff88;">💓 Health Check</a></p>
            </div>
        </div>
        
        <div class="card">
            <h3>📜 Server Log</h3>
            <div id="log-output"></div>
        </div>
    </div>
    
    <script>
        const startTime = new Date();
        document.getElementById('start-time').textContent = startTime.toLocaleString();
        document.getElementById('platform').textContent = navigator.platform;
        document.getElementById('python-version').textContent = '3.x';
        
        function updateUptime() {
            const now = new Date();
            const diff = Math.floor((now - startTime) / 1000);
            const hours = Math.floor(diff / 3600);
            const mins = Math.floor((diff % 3600) / 60);
            const secs = diff % 60;
            document.getElementById('uptime').textContent = 
                `${hours}h ${mins}m ${secs}s`;
        }
        setInterval(updateUptime, 1000);
        
        function addLog(message, type = 'info') {
            const log = document.getElementById('log-output');
            const line = document.createElement('div');
            line.className = 'log-line ' + type;
            line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            log.appendChild(line);
            log.scrollTop = log.scrollHeight;
        }
        
        addLog('🎮 Command Center Lite started!', 'success');
        addLog('⚡ Windows Fast-Start mode active', 'info');
        addLog('🌐 Listening on http://localhost:8888', 'success');
        
        function launchWarRoom() {
            addLog('🚀 Launching War Room Dashboard...', 'warning');
            fetch('/api/launch/warroom').then(r => r.json()).then(d => {
                addLog('✅ War Room: ' + d.message, 'success');
            }).catch(e => addLog('❌ ' + e, 'error'));
        }
        
        function launchDryRun() {
            addLog('🧪 Launching Dry Run...', 'warning');
            fetch('/api/launch/dryrun').then(r => r.json()).then(d => {
                addLog('✅ Dry Run: ' + d.message, 'success');
            }).catch(e => addLog('❌ ' + e, 'error'));
        }
        
        function launchLive() {
            if (!confirm('⚠️ This will start LIVE trading! Are you sure?')) return;
            addLog('💰 Launching LIVE Trading...', 'error');
            fetch('/api/launch/live').then(r => r.json()).then(d => {
                addLog('✅ Live: ' + d.message, 'success');
            }).catch(e => addLog('❌ ' + e, 'error'));
        }
        
        // Poll status
        setInterval(() => {
            fetch('/api/status').then(r => r.json()).then(d => {
                // Update stats if available
            }).catch(() => {});
        }, 5000);
    </script>
</body>
</html>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# WEB HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_index(request):
    """Serve the main dashboard"""
    return web.Response(text=LITE_HTML, content_type='text/html')

async def handle_health(request):
    """Health check endpoint"""
    return web.json_response({
        'status': 'healthy',
        'service': 'aureon-command-center-lite',
        'timestamp': datetime.now().isoformat(),
        'platform': sys.platform
    })

async def handle_status(request):
    """Status endpoint"""
    return web.json_response({
        'status': 'online',
        'mode': 'lite',
        'platform': sys.platform,
        'python': sys.version,
        'timestamp': datetime.now().isoformat()
    })

async def handle_launch_warroom(request):
    """Launch War Room in background"""
    try:
        import subprocess
        subprocess.Popen(
            [sys.executable, 'orca_complete_kill_cycle.py'],
            cwd=str(Path(__file__).parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        return web.json_response({'status': 'ok', 'message': 'War Room launched in new window'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

async def handle_launch_dryrun(request):
    """Launch dry run in background"""
    try:
        import subprocess
        subprocess.Popen(
            [sys.executable, 'micro_profit_labyrinth.py', '--dry-run'],
            cwd=str(Path(__file__).parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        return web.json_response({'status': 'ok', 'message': 'Dry run launched in new window'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

async def handle_launch_live(request):
    """Launch live trading in background"""
    try:
        import subprocess
        subprocess.Popen(
            [sys.executable, 'micro_profit_labyrinth.py', '--live', '--yes'],
            cwd=str(Path(__file__).parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        return web.json_response({'status': 'ok', 'message': 'Live trading launched in new window'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def create_app():
    """Create the aiohttp application"""
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/health', handle_health)
    app.router.add_get('/api/status', handle_status)
    app.router.add_get('/api/launch/warroom', handle_launch_warroom)
    app.router.add_get('/api/launch/dryrun', handle_launch_dryrun)
    app.router.add_get('/api/launch/live', handle_launch_live)
    return app

def main():
    """Main entry point"""
    print()
    print("=" * 70)
    print("""
    ██████╗ ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ 
   ██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗
   ██║     ██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║
   ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║
   ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝
    ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ 
                       
           ██╗     ██╗████████╗███████╗
           ██║     ██║╚══██╔══╝██╔════╝
           ██║     ██║   ██║   █████╗  
           ██║     ██║   ██║   ██╔══╝  
           ███████╗██║   ██║   ███████╗
           ╚══════╝╚═╝   ╚═╝   ╚══════╝
    """)
    print("=" * 70)
    print("🎮 AUREON COMMAND CENTER LITE - WINDOWS FAST START")
    print("=" * 70)
    print()
    print("   ⚡ Mode: Lite (No heavy imports)")
    print("   🌐 URL: http://localhost:8888")
    print("   📅 Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    print("   Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    app = create_app()
    
    print("🚀 Starting web server on port 8888...")
    try:
        web.run_app(app, host='0.0.0.0', port=8888, print=None)
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
