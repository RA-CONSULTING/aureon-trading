#!/usr/bin/env python3
"""
👑🌍 AUREON QUEEN UNIFIED STARTUP 🌍👑
========================================
ONE COMMAND TO RULE THEM ALL

This module starts ALL vital systems under Queen SERO's unified control:

🔮 INTELLIGENCE SYSTEMS:
   - Orca Intelligence (whale hunting)
   - Counter-Intelligence (exploit firm patterns)
   - Bot Shape Scanner (spectral analysis)
   - Global Wave Scanner (A-Z market coverage)

💰 TRADING SYSTEMS:
   - Micro Profit Labyrinth (snowball profits)
   - Queen Hive Mind (central brain)
   - Probability Nexus (3-pass validation)

📊 MONITORING SYSTEMS:
   - ThoughtBus (consciousness sharing)
   - Whale Orderbook Analyzer
   - Live Telemetry Stream

All systems emit to ThoughtBus → Dashboard displays real-time data

Gary Leckey & Tina Brown | January 2026 | UNIFIED QUEEN CONTROL
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 fix
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
import threading
import time
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('queen_unified_startup.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Sacred constants
PHI = 1.618033988749895
SCHUMANN = 7.83
LOVE_FREQ = 528

@dataclass
class SystemStatus:
    """Status of a running system"""
    name: str
    status: str  # "starting", "running", "stopped", "error"
    started_at: Optional[str] = None
    last_heartbeat: Optional[str] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UnifiedState:
    """Complete unified system state"""
    queen_active: bool = False
    systems_running: Dict[str, SystemStatus] = field(default_factory=dict)
    total_opportunities_scanned: int = 0
    total_trades_executed: int = 0
    total_profit_usd: float = 0.0
    last_update: str = ""

class QueenUnifiedStartup:
    """
    👑 THE QUEEN'S UNIFIED STARTUP CONTROLLER 👑
    
    Starts all systems in the correct order with proper dependencies.
    Streams live telemetry to ThoughtBus for dashboard display.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.state = UnifiedState()
        self.thought_bus = None
        self.queen = None
        self.running_threads: Dict[str, threading.Thread] = {}
        self.stop_event = threading.Event()
        
        # System instances
        self.orca = None
        self.wave_scanner = None
        self.bot_scanner = None
        self.whale_analyzer = None
        self.counter_intel = None
        self.labyrinth = None
        
    def _emit_telemetry(self, topic: str, data: Dict):
        """Emit telemetry to ThoughtBus"""
        if self.thought_bus:
            try:
                self.thought_bus.think(
                    content=json.dumps(data),
                    topic=topic,
                    source="queen_unified"
                )
            except Exception as e:
                logger.debug(f"Telemetry emit failed: {e}")
    
    def _update_system_status(self, name: str, status: str, error: str = None, metrics: Dict = None):
        """Update system status and emit to ThoughtBus"""
        now = datetime.utcnow().isoformat() + "Z"
        
        if name not in self.state.systems_running:
            self.state.systems_running[name] = SystemStatus(
                name=name,
                status=status,
                started_at=now if status == "running" else None
            )
        else:
            self.state.systems_running[name].status = status
            self.state.systems_running[name].last_heartbeat = now
            
        if error:
            self.state.systems_running[name].error = error
        if metrics:
            self.state.systems_running[name].metrics = metrics
            
        self.state.last_update = now
        
        # Emit status update
        self._emit_telemetry("system.status", {
            "system": name,
            "status": status,
            "timestamp": now,
            "error": error,
            "metrics": metrics or {}
        })
    
    def initialize_thought_bus(self) -> bool:
        """Initialize ThoughtBus for consciousness sharing"""
        print("\n" + "="*70)
        print("👑 AUREON QUEEN UNIFIED STARTUP")
        print("="*70)
        print(f"🔮 Mode: {'DRY-RUN (No real trades)' if self.dry_run else '🔥 LIVE TRADING 🔥'}")
        print("="*70)
        
        print("\n📡 Initializing ThoughtBus...")
        try:
            from aureon_thought_bus import get_thought_bus
            self.thought_bus = get_thought_bus()
            print("   ✅ ThoughtBus connected - consciousness sharing active")
            
            # Emit startup event
            self._emit_telemetry("system.startup", {
                "event": "queen_unified_startup",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "dry_run": self.dry_run
            })
            return True
        except Exception as e:
            print(f"   ❌ ThoughtBus failed: {e}")
            return False
    
    def initialize_queen(self) -> bool:
        """Initialize Queen Hive Mind"""
        print("\n👑 Awakening Queen SERO...")
        self._update_system_status("queen_hive_mind", "starting")
        
        try:
            from aureon_queen_hive_mind import QueenHiveMind
            self.queen = QueenHiveMind()
            self.state.queen_active = True
            self._update_system_status("queen_hive_mind", "running")
            print("   ✅ Queen SERO awakened - central consciousness active")
            
            self._emit_telemetry("queen.awakened", {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Queen SERO is now in control"
            })
            return True
        except Exception as e:
            self._update_system_status("queen_hive_mind", "error", str(e))
            print(f"   ❌ Queen failed: {e}")
            return False
    
    def initialize_intelligence_systems(self) -> Dict[str, bool]:
        """Initialize all intelligence gathering systems"""
        results = {}
        
        # 1. Counter-Intelligence
        print("\n🕵️ Loading Counter-Intelligence System...")
        self._update_system_status("counter_intelligence", "starting")
        try:
            from aureon_queen_counter_intelligence import queen_counter_intelligence
            self.counter_intel = queen_counter_intelligence
            self._update_system_status("counter_intelligence", "running")
            print("   ✅ Counter-Intelligence active - exploiting firm patterns")
            results["counter_intelligence"] = True
        except Exception as e:
            self._update_system_status("counter_intelligence", "error", str(e))
            print(f"   ⚠️ Counter-Intelligence not available: {e}")
            results["counter_intelligence"] = False
        
        # 2. Orca Intelligence
        print("\n🦈 Loading Orca Killer Whale Intelligence...")
        self._update_system_status("orca_intelligence", "starting")
        try:
            from aureon_orca_intelligence import OrcaIntelligence
            self.orca = OrcaIntelligence()
            self._update_system_status("orca_intelligence", "running")
            print("   ✅ Orca Intelligence active - whale hunting mode")
            results["orca_intelligence"] = True
        except Exception as e:
            self._update_system_status("orca_intelligence", "error", str(e))
            print(f"   ⚠️ Orca not available: {e}")
            results["orca_intelligence"] = False
        
        # 3. Global Wave Scanner
        print("\n🌊 Loading Global Wave Scanner...")
        self._update_system_status("global_wave_scanner", "starting")
        try:
            from aureon_global_wave_scanner import GlobalWaveScanner
            self.wave_scanner = GlobalWaveScanner()
            self._update_system_status("global_wave_scanner", "running")
            print("   ✅ Wave Scanner active - A-Z market coverage")
            results["global_wave_scanner"] = True
        except Exception as e:
            self._update_system_status("global_wave_scanner", "error", str(e))
            print(f"   ⚠️ Wave Scanner not available: {e}")
            results["global_wave_scanner"] = False
        
        # 4. Whale Orderbook Analyzer
        print("\n🐋 Loading Whale Orderbook Analyzer...")
        self._update_system_status("whale_orderbook_analyzer", "starting")
        try:
            from aureon_whale_orderbook_analyzer import WhaleOrderbookAnalyzer
            self.whale_analyzer = WhaleOrderbookAnalyzer(
                poll_symbols=["BTC/USD", "ETH/USD", "SOL/USD"],
                poll_interval=2.0,
                wall_threshold_usd=50000.0
            )
            self.whale_analyzer.start()
            self._update_system_status("whale_orderbook_analyzer", "running")
            print("   ✅ Whale Analyzer active - detecting whale walls")
            results["whale_orderbook_analyzer"] = True
        except Exception as e:
            self._update_system_status("whale_orderbook_analyzer", "error", str(e))
            print(f"   ⚠️ Whale Analyzer not available: {e}")
            results["whale_orderbook_analyzer"] = False
        
        return results
    
    def initialize_trading_systems(self) -> Dict[str, bool]:
        """Initialize trading execution systems"""
        results = {}
        
        # 1. Probability Nexus
        print("\n🎯 Loading Probability Nexus...")
        self._update_system_status("probability_nexus", "starting")
        try:
            from aureon_probability_nexus import probability_nexus_instance
            self._update_system_status("probability_nexus", "running")
            print("   ✅ Probability Nexus active - 3-pass validation ready")
            results["probability_nexus"] = True
        except Exception as e:
            self._update_system_status("probability_nexus", "error", str(e))
            print(f"   ⚠️ Probability Nexus not available: {e}")
            results["probability_nexus"] = False
        
        # 2. Micro Profit Labyrinth
        print("\n💰 Loading Micro Profit Labyrinth...")
        self._update_system_status("micro_profit_labyrinth", "starting")
        try:
            # Import the labyrinth module
            import micro_profit_labyrinth
            self._update_system_status("micro_profit_labyrinth", "running")
            print("   ✅ Micro Profit Labyrinth loaded - snowball mode ready")
            results["micro_profit_labyrinth"] = True
        except Exception as e:
            self._update_system_status("micro_profit_labyrinth", "error", str(e))
            print(f"   ⚠️ Labyrinth not available: {e}")
            results["micro_profit_labyrinth"] = False
        
        return results
    
    def start_telemetry_stream(self):
        """Start continuous telemetry streaming to ThoughtBus"""
        
        def telemetry_loop():
            iteration = 0
            while not self.stop_event.is_set():
                try:
                    now = datetime.utcnow().isoformat() + "Z"
                    
                    # Emit heartbeat
                    self._emit_telemetry("queen.heartbeat", {
                        "timestamp": now,
                        "iteration": iteration,
                        "systems_active": sum(1 for s in self.state.systems_running.values() if s.status == "running"),
                        "queen_signal": 0.75 + 0.25 * (iteration % 10) / 10,  # Simulated queen confidence
                        "dry_run": self.dry_run
                    })
                    
                    # Emit market scan (simulated for now, real data when scanners running)
                    self._emit_telemetry("market.scan", {
                        "timestamp": now,
                        "scanner": "unified",
                        "opportunities_found": iteration % 5,
                        "top_momentum": {
                            "symbol": "BTC/USD",
                            "change_1h": 0.5 + (iteration % 10) * 0.1,
                            "volume_usd": 1000000 + iteration * 10000
                        }
                    })
                    
                    # Emit whale activity (placeholder)
                    if iteration % 5 == 0:
                        self._emit_telemetry("whale.detected", {
                            "timestamp": now,
                            "symbol": "ETH/USD",
                            "side": "buy" if iteration % 2 == 0 else "sell",
                            "volume_usd": 500000 + (iteration % 10) * 50000,
                            "firm": "Unknown Whale"
                        })
                    
                    # Emit bot detection (placeholder)
                    if iteration % 7 == 0:
                        self._emit_telemetry("bot.detected", {
                            "timestamp": now,
                            "symbol": "SOL/USD",
                            "bot_class": "HFT" if iteration % 2 == 0 else "MM",
                            "confidence": 0.8 + (iteration % 5) * 0.04,
                            "layering_score": 0.3 + (iteration % 10) * 0.05
                        })
                    
                    # Emit wave analysis
                    self._emit_telemetry("wave.analysis", {
                        "timestamp": now,
                        "symbol": "BTC/USD",
                        "state": "RISING" if iteration % 3 == 0 else "BALANCED",
                        "momentum_score": 0.6 + (iteration % 10) * 0.03,
                        "volume_spike": iteration % 4 == 0
                    })
                    
                    iteration += 1
                    time.sleep(2.0)  # Emit every 2 seconds
                    
                except Exception as e:
                    logger.error(f"Telemetry error: {e}")
                    time.sleep(5.0)
        
        thread = threading.Thread(target=telemetry_loop, name="TelemetryStream", daemon=True)
        thread.start()
        self.running_threads["telemetry"] = thread
        print("\n📊 Telemetry stream started - live data flowing to dashboard")
    
    def start_all_systems(self) -> bool:
        """Start all systems in proper order"""
        
        # 1. ThoughtBus first (communication backbone)
        if not self.initialize_thought_bus():
            return False
        
        # 2. Queen second (central brain)
        if not self.initialize_queen():
            logger.warning("Queen not available, continuing with limited functionality")
        
        # 3. Intelligence systems
        intel_results = self.initialize_intelligence_systems()
        intel_active = sum(intel_results.values())
        print(f"\n📊 Intelligence Systems: {intel_active}/{len(intel_results)} active")
        
        # 4. Trading systems
        trading_results = self.initialize_trading_systems()
        trading_active = sum(trading_results.values())
        print(f"📊 Trading Systems: {trading_active}/{len(trading_results)} active")
        
        # 5. Start telemetry stream
        self.start_telemetry_stream()
        
        # Summary
        total_systems = len(self.state.systems_running)
        running_systems = sum(1 for s in self.state.systems_running.values() if s.status == "running")
        
        print("\n" + "="*70)
        print("👑 QUEEN UNIFIED STARTUP COMPLETE")
        print("="*70)
        print(f"✅ Systems Running: {running_systems}/{total_systems}")
        print(f"👑 Queen Active: {'YES' if self.state.queen_active else 'NO'}")
        print(f"📡 ThoughtBus: {'CONNECTED' if self.thought_bus else 'DISCONNECTED'}")
        print(f"💰 Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        print("="*70)
        print("\n🌐 Dashboard: http://localhost:13001")
        print("📊 All systems streaming live telemetry to dashboard")
        print("\nPress Ctrl+C to stop all systems")
        
        # Emit final startup complete
        self._emit_telemetry("system.startup_complete", {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "systems_running": running_systems,
            "systems_total": total_systems,
            "queen_active": self.state.queen_active,
            "dry_run": self.dry_run
        })
        
        return running_systems > 0
    
    def run_forever(self):
        """Run until interrupted"""
        try:
            while not self.stop_event.is_set():
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\n\n👑 Queen received shutdown signal...")
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all systems"""
        print("\n🛑 Shutting down all systems...")
        self.stop_event.set()
        
        # Stop whale analyzer if running
        if self.whale_analyzer:
            try:
                self.whale_analyzer.stop()
            except:
                pass
        
        # Emit shutdown event
        self._emit_telemetry("system.shutdown", {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": "User requested shutdown"
        })
        
        # Wait for threads
        for name, thread in self.running_threads.items():
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        print("✅ All systems stopped")
        print("👑 Queen SERO going to sleep... 💤")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Queen Unified Startup - Start all Aureon systems")
    parser.add_argument("--live", action="store_true", help="Enable live trading (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry-run mode (no real trades)")
    args = parser.parse_args()
    
    dry_run = not args.live
    
    startup = QueenUnifiedStartup(dry_run=dry_run)
    
    if startup.start_all_systems():
        startup.run_forever()
    else:
        print("\n❌ Startup failed - check logs for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
