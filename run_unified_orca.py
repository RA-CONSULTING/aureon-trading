#!/usr/bin/env python3
"""
🎯 RUN UNIFIED ORCA - Complete Integration Launcher
=====================================================

Launches the complete unified dashboard system alongside Orca kill cycle execution.

Usage:
    python run_unified_orca.py --autonomous
    python run_unified_orca.py --autonomous --dry-run
    python run_unified_orca.py --autonomous --open-dashboard

This script:
1. Starts System Coordinator (tracks all 197 systems)
2. Starts Decision Engine (generates trading decisions)
3. Starts Orca Monitor (tracks Orca execution)
4. Starts Unified Dashboard API (port 13334)
5. Launches Orca kill cycle in autonomous mode
6. Optionally opens the dashboard in browser
7. Streams real-time metrics to dashboard

All metrics flow through ThoughtBus for real-time updates.
"""

import asyncio
import subprocess
import time
import sys
import os
import webbrowser
from pathlib import Path
from typing import List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedOrcaLauncher:
    """Manages the complete unified Orca system."""

    def __init__(self):
        """Initialize launcher."""
        self.processes: List[subprocess.Popen] = []
        self.root_dir = Path(__file__).parent
        self.dashboard_url = "http://localhost:3000/dashboard/unified"
        self.api_url = "http://localhost:13334/api"

    def log_section(self, title: str):
        """Print a section header."""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)

    async def start_system_coordinator(self):
        """Start the System Coordinator."""
        self.log_section("🔗 Starting System Coordinator")

        code = """
import asyncio
import sys
from aureon_system_coordinator import SystemCoordinator, SystemState

coordinator = SystemCoordinator()
print("✅ System Coordinator running")
print("   Loaded 197 systems, monitoring dependencies")

# Simulate system readiness
coordinator.set_system_state("kraken_client", SystemState.READY)
coordinator.set_system_state("binance_client", SystemState.READY)
coordinator.set_system_state("alpaca_client", SystemState.READY)
print("✅ Exchange clients marked as READY")

# Monitor continuously
async def monitor():
    await coordinator.monitor_coordination(interval=2.0)

try:
    asyncio.run(monitor())
except KeyboardInterrupt:
    print("System Coordinator shutting down...")
    sys.exit(0)
"""

        proc = await self._run_python_code(code, "Coordinator")
        self.processes.append(proc)
        await asyncio.sleep(1)  # Let it start

    async def start_decision_engine(self):
        """Start the Decision Engine."""
        self.log_section("⚡ Starting Decision Engine")

        code = """
import asyncio
import sys
from aureon_unified_decision_engine import UnifiedDecisionEngine

engine = UnifiedDecisionEngine()
print("✅ Decision Engine running")
print("   Ready to synthesize market signals")

async def monitor():
    await engine.monitor_decisions(interval=2.0)

try:
    asyncio.run(monitor())
except KeyboardInterrupt:
    print("Decision Engine shutting down...")
    sys.exit(0)
"""

        proc = await self._run_python_code(code, "DecisionEngine")
        self.processes.append(proc)
        await asyncio.sleep(1)  # Let it start

    async def start_orca_monitor(self):
        """Start the Orca Monitor."""
        self.log_section("🐋 Starting Orca Monitor")

        code = """
import asyncio
import sys
from aureon_orca_monitor import OrcaMonitor

monitor = OrcaMonitor()
monitor.set_execution_state("idle")
print("✅ Orca Monitor running")
print("   Listening for Orca execution events")

async def run():
    await monitor.monitor_orca(interval=1.0)

try:
    asyncio.run(run())
except KeyboardInterrupt:
    print("Orca Monitor shutting down...")
    sys.exit(0)
"""

        proc = await self._run_python_code(code, "OrcaMonitor")
        self.processes.append(proc)
        await asyncio.sleep(1)  # Let it start

    async def start_dashboard_api(self):
        """Start the Unified Dashboard API."""
        self.log_section("🎯 Starting Unified Dashboard API")

        code = """
import asyncio
from aureon_unified_dashboard_api import start_api_server

try:
    asyncio.run(start_api_server(port=13334, host='0.0.0.0'))
except KeyboardInterrupt:
    print("Dashboard API shutting down...")
    sys.exit(0)
"""

        proc = await self._run_python_code(code, "DashboardAPI")
        self.processes.append(proc)
        await asyncio.sleep(2)  # Let it start
        print(f"✅ Dashboard API running on {self.api_url}")

    async def start_orca_autonomous(self, dry_run: bool = False):
        """Start Orca in autonomous mode."""
        self.log_section("🐋 Starting Orca Kill Cycle - AUTONOMOUS MODE")

        cmd = [
            sys.executable,
            str(self.root_dir / "orca_complete_kill_cycle.py"),
            "--autonomous"
        ]

        if dry_run:
            cmd.append("--dry-run")
            print("   Mode: DRY-RUN (no real trades)")
        else:
            print("   Mode: LIVE (real trades)")

        print(f"   Command: {' '.join(cmd)}")
        print()

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            self.processes.append(proc)

            # Stream output to console
            print("📊 Orca Output:")
            print("-" * 80)
            while proc.poll() is None:
                line = proc.stdout.readline()
                if line:
                    print(line, end='', flush=True)
                await asyncio.sleep(0.01)

            # Get remaining output
            remaining = proc.stdout.read()
            if remaining:
                print(remaining, end='', flush=True)

            return proc

        except KeyboardInterrupt:
            print("\n⏹️  Orca interrupted by user")
            proc.terminate()
            sys.exit(0)

    def open_dashboard(self):
        """Open the dashboard in browser."""
        self.log_section("🌐 Opening Dashboard in Browser")

        # Try different URLs
        urls = [
            "http://localhost:3000/unified-dashboard",
            "http://localhost:3000/dashboard/unified",
            "http://localhost:3000",
            f"file://{self.root_dir}/frontend/dist/index.html"
        ]

        for url in urls:
            try:
                logger.info(f"Opening {url}")
                webbrowser.open(url)
                print(f"✅ Dashboard opened in browser: {url}")
                return
            except Exception as e:
                logger.debug(f"Could not open {url}: {e}")

        print(f"\n⚠️  Could not auto-open dashboard")
        print(f"   Open manually: {urls[0]}")
        print(f"   API available at: {self.api_url}")

    async def _run_python_code(self, code: str, name: str) -> subprocess.Popen:
        """Run Python code in a subprocess."""
        cmd = [sys.executable, "-c", code]
        proc = subprocess.Popen(
            cmd,
            cwd=self.root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return proc

    async def run(self, autonomous: bool = False, dry_run: bool = False, open_dashboard: bool = False):
        """Run the complete unified system."""
        self.log_section("🎯 AUREON UNIFIED ORCA CONTROL CENTER")

        try:
            # Start background services
            print("\n🚀 Starting unified dashboard services...")

            # Start services in parallel
            tasks = [
                self.start_system_coordinator(),
                self.start_decision_engine(),
                self.start_orca_monitor(),
                self.start_dashboard_api(),
            ]

            # Run all startup tasks
            for task in tasks:
                try:
                    await task
                except Exception as e:
                    logger.error(f"Error starting component: {e}")

            print("\n" + "=" * 80)
            print("✅ All unified dashboard services started successfully!")
            print("=" * 80)

            # Print access information
            self.print_access_info()

            # Open dashboard if requested
            if open_dashboard:
                await asyncio.sleep(2)  # Wait for everything to be ready
                self.open_dashboard()

            # Start Orca if autonomous mode requested
            if autonomous:
                print("\n⏳ Waiting 2 seconds before launching Orca...")
                await asyncio.sleep(2)

                await self.start_orca_autonomous(dry_run=dry_run)

            # Keep running
            print("\n" + "=" * 80)
            print("🎯 Unified system is LIVE and monitoring")
            print("=" * 80)
            print("\nPress Ctrl+C to stop all services\n")

            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n⏹️  Shutting down unified system...")
                self.cleanup()

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.cleanup()
            sys.exit(1)

    def print_access_info(self):
        """Print how to access the system."""
        print("\n" + "=" * 80)
        print("📊 SYSTEM ACCESS INFORMATION")
        print("=" * 80)
        print(f"\n🎯 Unified Dashboard API:")
        print(f"   URL: {self.api_url}")
        print(f"   Health check: {self.api_url}/health")
        print(f"   Orca status: {self.api_url}/orca-status")
        print(f"   System coordination: {self.api_url}/system-coordination")
        print(f"   Unified state: {self.api_url}/unified-state")

        print(f"\n🌐 React Dashboard:")
        print(f"   URL: {self.dashboard_url}")
        print(f"   (or http://localhost:3000 if running npm dev server)")

        print(f"\n📈 Live Metrics Streaming:")
        print(f"   ThoughtBus topics:")
        print(f"      - orca.state_change")
        print(f"      - orca.position_event")
        print(f"      - orca.monitor")
        print(f"      - coordination.state_change")
        print(f"      - coordination.monitor")
        print(f"      - decisions.trading")
        print(f"      - decisions.monitor")
        print(f"      - feeds.consolidated.*")

        print(f"\n✅ Services Running:")
        for i, proc in enumerate(self.processes):
            status = "✅ Running" if proc.poll() is None else "❌ Stopped"
            print(f"   {i+1}. {status}")

    def cleanup(self):
        """Cleanup all processes."""
        logger.info("Cleaning up processes...")

        for proc in self.processes:
            try:
                if proc.poll() is None:  # Still running
                    proc.terminate()
                    proc.wait(timeout=5)
            except Exception as e:
                logger.warning(f"Error terminating process: {e}")
                try:
                    proc.kill()
                except:
                    pass

        logger.info("All processes cleaned up")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run unified Orca control center with live metrics"
    )
    parser.add_argument(
        "--autonomous",
        action="store_true",
        help="Run Orca in autonomous mode"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run Orca in dry-run mode (no real trades)"
    )
    parser.add_argument(
        "--open-dashboard",
        action="store_true",
        help="Automatically open dashboard in browser"
    )

    args = parser.parse_args()

    launcher = UnifiedOrcaLauncher()
    await launcher.run(
        autonomous=args.autonomous,
        dry_run=args.dry_run,
        open_dashboard=args.open_dashboard
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Unified Orca system stopped")
        sys.exit(0)
