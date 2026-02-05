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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HEALTH_CHECK")

# Health check status
STARTUP_TIME = time.time()
HEALTH_STATUS = {
    "status": "starting",
    "uptime": 0,
    "timestamp": datetime.now().isoformat(),
    "version": "1.0",
    "autonomous_control": os.environ.get("AUREON_ENABLE_AUTONOMOUS_CONTROL", "0"),
    "autonomy_level": os.environ.get("AUREON_AUTONOMY_LEVEL", "UNKNOWN")
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks and status"""
    
    def do_GET(self):
        """Handle GET requests"""
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
            logger.debug(f"Health check OK - uptime: {HEALTH_STATUS['uptime']}s")
            
        elif path == "/status":
            # Full status endpoint
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(HEALTH_STATUS).encode())
            logger.info(f"Status endpoint - uptime: {HEALTH_STATUS['uptime']}s")
            
        elif path == "/":
            # Root endpoint - simple HTML
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Aureon Health Check</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #00aa00; }}
                    .status {{ background: #f0f0f0; padding: 10px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <h1>👑 Aureon Trading System</h1>
                <div class="status">
                    <p><strong>Status:</strong> {HEALTH_STATUS["status"]}</p>
                    <p><strong>Uptime:</strong> {HEALTH_STATUS["uptime"]} seconds</p>
                    <p><strong>Autonomous:</strong> {HEALTH_STATUS["autonomous_control"]}</p>
                    <p><strong>Level:</strong> {HEALTH_STATUS["autonomy_level"]}</p>
                    <p><strong>Time:</strong> {HEALTH_STATUS["timestamp"]}</p>
                </div>
                <p><a href="/status">View JSON Status</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            # 404 for unknown paths
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def get_free_port(port=8080, max_attempts=10):
    """Find a free port starting from the specified port"""
    for port in range(port, port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"No free ports available starting from {port}")

def main():
    """Start the health check server"""
    port = int(os.environ.get("HEALTH_CHECK_PORT", "8080"))
    
    try:
        # Try to bind to the requested port
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        HEALTH_STATUS["status"] = "healthy"
        
        logger.info(f"🏥 Health Check Server starting on port {port}")
        logger.info(f"   Endpoints: /health, /status, /")
        logger.info(f"   Autonomous Control: {HEALTH_STATUS['autonomous_control']}")
        logger.info(f"   Autonomy Level: {HEALTH_STATUS['autonomy_level']}")
        
        # Keep running
        server.serve_forever()
        
    except Exception as e:
        logger.error(f"❌ Failed to start health check server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
