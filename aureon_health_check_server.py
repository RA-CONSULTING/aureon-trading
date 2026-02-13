#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏥 AUREON HEALTH CHECK SERVER
Minimal HTTP server for DigitalOcean App Platform health checks.
Returns 200 OK at /health endpoint when supervisor is running.
"""

import os
import sys
import json
import time
import socket
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import threading

# Disable default HTTP server logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Configure logging to STDOUT for Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - HEALTH_CHECK - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("HEALTH_CHECK")

# Health check status
STARTUP_TIME = time.time()
HEALTH_STATUS = {
    "status": "healthy",
    "uptime": 0,
    "timestamp": datetime.now().isoformat(),
    "version": "2.0",
    "autonomous_control": os.environ.get("AUREON_ENABLE_AUTONOMOUS_CONTROL", "0"),
    "autonomy_level": os.environ.get("AUREON_AUTONOMY_LEVEL", "UNKNOWN")
}

# 🔧 FIX #9: Real system health — checks actual subsystem state
def _get_real_health() -> dict:
    """
    Query the Operational Core for real system health.
    Falls back to basic uptime-only check if Ops Core not available.
    """
    base = {
        "uptime": int(time.time() - STARTUP_TIME),
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
    }

    # Check heartbeat file freshness
    heartbeat_stale = True
    heartbeat_age = None
    try:
        hb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.aureon_heartbeat')
        if os.path.exists(hb_path):
            with open(hb_path, 'r') as f:
                hb = json.load(f)
            heartbeat_age = time.time() - hb.get('timestamp', 0)
            heartbeat_stale = heartbeat_age > 120  # Stale if >2 minutes old
            base['heartbeat'] = {
                'age_seconds': round(heartbeat_age, 1),
                'iteration': hb.get('iteration', 0),
                'positions': hb.get('positions', 0),
                'equity': hb.get('equity', 0),
                'stale': heartbeat_stale,
            }
    except Exception:
        base['heartbeat'] = {'stale': True, 'error': 'unreadable'}

    # Check state file freshness
    state_stale = True
    try:
        state_path = '/tmp/aureon_state/aureon_live_state.json'
        if os.path.exists(state_path):
            state_age = time.time() - os.path.getmtime(state_path)
            state_stale = state_age > 300  # Stale if >5 minutes
            base['state_file'] = {
                'age_seconds': round(state_age, 1),
                'stale': state_stale,
            }
    except Exception:
        base['state_file'] = {'stale': True, 'error': 'unreadable'}

    # Check circuit breaker status
    cb_tripped = False
    try:
        from aureon_operational_core import get_operational_core
        ops = get_operational_core()
        ops_health = ops.get_health()
        base['operational_core'] = ops_health
        cb_tripped = ops_health.get('circuit_breaker', {}).get('global_readonly', False)
    except Exception:
        base['operational_core'] = {'status': 'unavailable'}

    # Determine overall status
    issues = []
    if heartbeat_stale:
        issues.append('Trading loop heartbeat stale')
    if state_stale:
        issues.append('State file stale')
    if cb_tripped:
        issues.append('Global circuit breaker: READ-ONLY')

    if cb_tripped:
        base['status'] = 'critical'
    elif len(issues) >= 2:
        base['status'] = 'unhealthy'
    elif len(issues) == 1:
        base['status'] = 'degraded'
    else:
        base['status'] = 'healthy'

    base['issues'] = issues
    return base

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks and status"""
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            path = self.path.split('?')[0]  # Remove query string
            
            # Update health status
            HEALTH_STATUS["uptime"] = int(time.time() - STARTUP_TIME)
            HEALTH_STATUS["timestamp"] = datetime.now().isoformat()
            
            if path == "/health":
                # 🔧 FIX #9: Real health check — not just "server is up"
                real_health = _get_real_health()
                # DigitalOcean needs 200 for the app to stay running,
                # but we report actual status in the payload
                status_code = 200 if real_health['status'] != 'critical' else 503
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {
                    "status": real_health['status'],
                    "uptime": real_health['uptime'],
                    "issues": real_health.get('issues', []),
                }
                self.wfile.write(json.dumps(response).encode())

            elif path == "/status":
                # Full status endpoint with operational details
                real_health = _get_real_health()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(real_health, default=str).encode())
                
            elif path == "/":
                # Root endpoint - simple HTML
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                html = f"""<!DOCTYPE html>
<html><head><title>Aureon Health</title></head>
<body><h1>👑 Aureon Trading System</h1>
<p>Status: {HEALTH_STATUS["status"]}</p>
<p>Uptime: {HEALTH_STATUS["uptime"]}s</p>
</body></html>"""
                self.wfile.write(html.encode())
            else:
                # 404
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            try:
                self.send_response(500)
                self.end_headers()
            except:
                pass

def main():
    """Start the health check server"""
    # DigitalOcean App Platform sets PORT automatically, fallback to 8080
    port = int(os.environ.get("PORT", os.environ.get("HEALTH_CHECK_PORT", "8080")))
    
    try:
        logger.info(f"🏥 Starting Health Check Server on 0.0.0.0:{port}")
        logger.info(f"   PORT env: {os.environ.get('PORT', 'not set')}")
        logger.info(f"   HEALTH_CHECK_PORT env: {os.environ.get('HEALTH_CHECK_PORT', 'not set')}")
        
        # Create HTTP server with SO_REUSEADDR from the start
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        logger.info(f"✅ Health Check Server listening on port {port}")
        logger.info(f"   Endpoints: GET /health, GET /status, GET /")
        logger.info(f"   Autonomous: {HEALTH_STATUS['autonomous_control']}")
        logger.info(f"   Ready to receive health check requests")
        
        # Flush logs immediately
        sys.stdout.flush()
        
        # Start serving requests
        server.serve_forever()
        
    except Exception as e:
        logger.error(f"❌ Fatal error starting server on port {port}: {e}", exc_info=True)
        sys.stderr.flush()
        sys.exit(1)

if __name__ == "__main__":
    main()
