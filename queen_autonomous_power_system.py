#!/usr/bin/env python3
"""
Queen Autonomous Power System - Full Integration
Runs Queen's redistribution engine + live dashboard in integrated mode.

This is the complete autonomous system:
- Queen's consciousness analyzes and decides
- Power redistribution engine executes decisions
- Live dashboard displays Queen's intelligence in action

The Queen autonomously:
1. Monitors idle energy across all relays
2. Calculates exact energy drains (fees, slippage, spread)
3. Finds high-momentum conversion opportunities
4. Executes ONLY when (gain - drain) > 0
5. Compounds gains back into system
6. Displays all activity in real-time

Usage:
  # Dry-run mode (default, safe testing)
  python queen_autonomous_power_system.py
  
  # Live trading mode
  python queen_autonomous_power_system.py --live
  
  # Custom scan interval
  python queen_autonomous_power_system.py --interval 60
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
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
import subprocess
import signal
import time
import argparse
from datetime import datetime


class QueenAutonomousPowerSystem:
    """
    Full integration: Queen's intelligence → Redistribution → Dashboard
    """
    
    def __init__(self, dry_run: bool = True, scan_interval: int = 30):
        self.dry_run = dry_run
        self.scan_interval = scan_interval
        self.redistribution_process = None
        self.dashboard_process = None
        self.running = False
    
    def start_redistribution_engine(self):
        """Start Queen's redistribution engine as background process."""
        print("🐝 Starting Queen's Redistribution Engine...")
        
        cmd = ['python', 'queen_power_redistribution.py', '--interval', str(self.scan_interval)]
        if not self.dry_run:
            cmd.append('--live')
        
        self.redistribution_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        print(f"✅ Redistribution Engine started (PID: {self.redistribution_process.pid})")
        print(f"   Mode: {'🔶 DRY-RUN' if self.dry_run else '⚡ LIVE'}")
        print(f"   Interval: {self.scan_interval}s")
    
    def start_dashboard(self):
        """Start live dashboard as foreground display."""
        print("📊 Starting Live Dashboard...")
        
        # Dashboard runs in foreground (blocking)
        # We'll run it via subprocess but interact with it
        cmd = ['python', 'queen_power_dashboard.py', '--interval', '3']
        
        self.dashboard_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"✅ Dashboard started (PID: {self.dashboard_process.pid})")
    
    def stop_processes(self):
        """Gracefully stop all processes."""
        print("\n\n🛑 Stopping Queen Autonomous Power System...")
        
        if self.redistribution_process:
            print("   Stopping Redistribution Engine...")
            self.redistribution_process.terminate()
            try:
                self.redistribution_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.redistribution_process.kill()
            print("   ✅ Redistribution Engine stopped")
        
        if self.dashboard_process:
            print("   Stopping Dashboard...")
            self.dashboard_process.terminate()
            try:
                self.dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.dashboard_process.kill()
            print("   ✅ Dashboard stopped")
        
        print("✅ Queen Autonomous Power System stopped")
    
    async def run(self):
        """Run integrated system."""
        self.running = True
        
        print("=" * 80)
        print("🐝 QUEEN AUTONOMOUS POWER SYSTEM")
        print("=" * 80)
        print(f"Mode: {'🔶 DRY-RUN (Safe Testing)' if self.dry_run else '⚡ LIVE TRADING'}")
        print(f"Scan Interval: {self.scan_interval}s")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Start redistribution engine
        self.start_redistribution_engine()
        
        # Wait a moment for engine to initialize
        await asyncio.sleep(2)
        
        # Start dashboard
        self.start_dashboard()
        
        try:
            # Stream dashboard output to terminal
            while self.running:
                if self.dashboard_process and self.dashboard_process.poll() is None:
                    line = self.dashboard_process.stdout.readline()
                    if line:
                        print(line, end='')
                else:
                    # Dashboard stopped
                    break
                
                await asyncio.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Received interrupt signal...")
        
        finally:
            self.stop_processes()


async def main():
    parser = argparse.ArgumentParser(
        description="Queen Autonomous Power System - Full Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run mode (safe, default)
  python queen_autonomous_power_system.py
  
  # Live trading mode
  python queen_autonomous_power_system.py --live
  
  # Custom scan interval
  python queen_autonomous_power_system.py --interval 60
  
  # Live with custom interval
  python queen_autonomous_power_system.py --live --interval 120
"""
    )
    
    parser.add_argument('--live', action='store_true', 
                       help='Run in LIVE trading mode (default: dry-run)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Scan interval in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # Confirm live mode
    if args.live:
        print("⚠️  WARNING: LIVE TRADING MODE ENABLED")
        print("   Queen will execute REAL trades when opportunities are found.")
        response = input("   Type 'YES' to continue, anything else to exit: ")
        if response != 'YES':
            print("❌ Cancelled by user")
            return
    
    # Create and run system
    system = QueenAutonomousPowerSystem(
        dry_run=not args.live,
        scan_interval=args.interval
    )
    
    # Handle signals
    def signal_handler(signum, frame):
        system.running = False
        system.stop_processes()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    await system.run()


if __name__ == '__main__':
    asyncio.run(main())
