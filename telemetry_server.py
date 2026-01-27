#!/usr/bin/env python3
"""
Telemetry Server - Prometheus Metrics Exporter
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import logging
import threading
import socket
import os

logger = logging.getLogger(__name__)

_server_started = False
_server_lock = threading.Lock()
_error_logged = False  # Only log the error once

def _is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return False
        except OSError:
            return True

def start_telemetry_server(port: int = 8000):
    """Start the Prometheus HTTP server."""
    global _server_started, _error_logged
    with _server_lock:
        if _server_started:
            return True  # Already running in this process
        
        # Check if port is already in use (maybe from another process)
        if _is_port_in_use(port):
            if not _error_logged:
                logger.info(f"🔭 Telemetry: Port {port} already in use (metrics server running elsewhere)")
                _error_logged = True
            _server_started = True  # Mark as started to prevent retries
            return True  # Non-blocking - another instance has it
        
        try:
            from prometheus_client import start_http_server
            start_http_server(port)
            _server_started = True
            logger.info(f"🔭 Telemetry: Prometheus metrics server started on port {port}")
            return True
        except Exception as e:
            if not _error_logged:
                logger.warning(f"🔭 Telemetry: Could not start metrics server: {e}")
                _error_logged = True
            _server_started = True  # Prevent repeated attempts
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_telemetry_server()
    import time
    while True:
        time.sleep(1)