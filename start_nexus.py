#!/usr/bin/env python3
"""
Harmonic Nexus Charter - Complete System Startup
Launches validators + WebSocket bridge for real-time biofield validation
"""

import subprocess
import time
import os
import signal
import sys
from pathlib import Path

class NexusLauncher:
    def __init__(self):
        self.processes = []
        self.validation_dir = Path('validation')
        
    def setup_directories(self):
        """Create validation directory if it doesn't exist"""
        self.validation_dir.mkdir(exist_ok=True)
        print("✓ Validation directory ready")
        
    def start_validators(self):
        """Start Python validators"""
        print("🔄 Starting Auris Validator...")
        auris_process = subprocess.Popen(
            [sys.executable, 'validator_auris.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(auris_process)
        
        print("🔄 Starting Aura Validator...")
        aura_process = subprocess.Popen(
            [sys.executable, 'aura_validator.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(aura_process)
        
        # Wait for validators to initialize
        time.sleep(2)
        print("✓ Validators running")
        
    def start_websocket_bridge(self):
        """Start WebSocket bridge"""
        print("🔄 Starting WebSocket Bridge...")
        bridge_process = subprocess.Popen(
            ['node', 'auris_bridge.js'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.processes.append(bridge_process)
        time.sleep(1)
        print("✓ WebSocket Bridge running on ws://localhost:8787")
        
    def cleanup(self, signum=None, frame=None):
        """Clean shutdown of all processes"""
        print("\n🛑 Shutting down Harmonic Nexus Charter...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("✓ All processes stopped")
        sys.exit(0)
        
    def run(self):
        """Main launcher"""
        print("🌟 Harmonic Nexus Charter - Real-time Biofield Validation")
        print("=" * 60)
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        try:
            self.setup_directories()
            self.start_validators()
            self.start_websocket_bridge()
            
            print("\n✅ Harmonic Nexus Charter is ACTIVE")
            print("📊 Dashboard: http://localhost:5173")
            print("🔗 WebSocket: ws://localhost:8787")
            print("\nPress Ctrl+C to stop all services")
            
            # Keep running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            print(f"❌ Error: {e}")
            self.cleanup()

if __name__ == '__main__':
    launcher = NexusLauncher()
    launcher.run()