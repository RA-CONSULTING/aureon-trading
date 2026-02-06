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
    "version": "1.0",
    "autonomous_control": os.environ.get("AUREON_ENABLE_AUTONOMOUS_CONTROL", "0"),
    "autonomy_level": os.environ.get("AUREON_AUTONOMY_LEVEL", "UNKNOWN")
}

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
                # Health check endpoint - always returns 200 if server is running
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {"status": "healthy", "uptime": HEALTH_STATUS["uptime"]}
                self.wfile.write(json.dumps(response).encode())
                
            elif path == "/status":
                # Full status endpoint
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(HEALTH_STATUS).encode())
                
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
    port = int(os.environ.get("HEALTH_CHECK_PORT", "8080"))
    
    try:
        logger.info(f"🏥 Starting Health Check Server on 0.0.0.0:{port}")
        
        # Create HTTP server
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        
        logger.info(f"✅ Health Check Server listening on port {port}")
        logger.info(f"   Endpoints: GET /health, GET /status, GET /")
        logger.info(f"   Autonomous: {HEALTH_STATUS['autonomous_control']}")
        
        # Start serving requests
        server.serve_forever()
        
    except OSError as e:
        logger.error(f"❌ Failed to bind to port {port}: {e}")
        # Try with SO_REUSEADDR
        try:
            server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            logger.info(f"✅ Retried with SO_REUSEADDR")
            server.serve_forever()
        except Exception as e2:
            logger.error(f"❌ Fatal error: {e2}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
