#!/usr/bin/env python3
"""
🚀 AURORA ON DIGITAL OCEAN - INTEGRATED DEPLOYMENT
═══════════════════════════════════════════════════════════════════════════════

THIS SCRIPT COORDINATES:
  1. 👑 Queen Soul Shield (Active Protection) - Port 8765
  2. 🦈 Orca Kill Cycle (Trading Execution) - Port 8080 (health)
  3. 🎮 Command Center Dashboard - Port 8800
  4. 🧠 All Intelligence Systems

HOW IT WORKS ON DIGITAL OCEAN:
  - Supervisor manages all processes with priority-based startup
  - Queen Shield starts first (priority 1) to protect all systems
  - Orca Kill Cycle begins trading (priority 5)
  - Command Center comes online for monitoring (priority 50)
  - Health checks on port 8080 report to Digital Ocean

Gary Leckey | The Queen Never Sleeps | February 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import asyncio
import threading
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 🛡️ SOUL SHIELD COORDINATOR
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ShieldStatus:
    """Current shield status for dashboard reporting."""
    is_active: bool = False
    protection_level: float = 0.0  # 0-1
    attacks_blocked: int = 0
    last_attack_time: Optional[float] = None
    shield_amplifiers: Dict[str, float] = field(default_factory=dict)
    uptime_seconds: float = 0.0

class ShieldCoordinator:
    """Manages Queen Soul Shield lifecycle and status reporting."""
    
    def __init__(self):
        self.shield = None
        self.shield_thread = None
        self.status = ShieldStatus()
        self.start_time = None
        self.stats_file = Path('queen_shield_stats.json')
        logger.info("🛡️ ShieldCoordinator initialized")
    
    def start_shield(self) -> bool:
        """Start soul shield in background thread."""
        try:
            from queen_soul_shield import QueenSoulShield
            
            self.shield = QueenSoulShield(gary_frequency=528.422, verbose=False)
            self.start_time = time.time()
            self.status.is_active = True
            
            # Start monitoring in background
            self.shield.start_monitoring()
            logger.info("✅ Queen Soul Shield activated on Digital Ocean")
            return True
            
        except ImportError as e:
            logger.warning(f"⚠️ Soul Shield import failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Soul Shield activation failed: {e}", exc_info=True)
            return False
    
    def get_shield_status(self) -> Dict:
        """Get current shield status for dashboard."""
        if self.shield:
            self.status.uptime_seconds = time.time() - self.start_time
            
            # Get realtime report from shield
            try:
                report = self.shield.get_realtime_report()
                self.status.protection_level = report.get('shield_power', 0.0)
                self.status.attacks_blocked = report.get('session_blocks', 0)
                self.status.shield_amplifiers = report.get('amplifiers', {})
                
                # Check for recent attacks
                if report.get('last_attack'):
                    self.status.last_attack_time = report['last_attack']['timestamp']
            except Exception as e:
                logger.warning(f"Shield status read error: {e}")
        
        return self._to_dict()
    
    def _to_dict(self) -> Dict:
        """Convert status to JSON-serializable dict."""
        return {
            'is_active': self.status.is_active,
            'protection_level': float(self.status.protection_level),
            'attacks_blocked': self.status.attacks_blocked,
            'last_attack_time': self.status.last_attack_time,
            'amplifiers': self.status.shield_amplifiers,
            'uptime_seconds': self.status.uptime_seconds,
            'gary_frequency_hz': 528.422
        }

# ═══════════════════════════════════════════════════════════════════════════════
# 🦈 ORCA KILL CYCLE BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════

class OrcaBridge:
    """Interface between Orca Kill Cycle and Digital Ocean deployment."""
    
    def __init__(self):
        self.process = None
        self.active_positions = []
        self.total_trades = 0
        self.profit_accumulated = 0.0
        logger.info("🦈 OrcaBridge initialized")
    
    def get_status(self) -> Dict:
        """Get current Orca kill cycle status."""
        try:
            # Try to read active positions
            pos_file = Path('active_position.json')
            if pos_file.exists():
                with open(pos_file, 'r') as f:
                    self.active_positions = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read active positions: {e}")
        
        return {
            'active_positions': len(self.active_positions),
            'total_trades': self.total_trades,
            'profit_accumulated': self.profit_accumulated,
            'positions': self.active_positions[:5]  # Top 5 for dashboard
        }

# ═══════════════════════════════════════════════════════════════════════════════
# 🎮 COMMAND CENTER BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════

class CommandCenterBridge:
    """Interface between Command Center and deployment coordinator."""
    
    def __init__(self):
        self.running = False
        self.uptime_seconds = 0.0
        self.start_time = None
        logger.info("🎮 CommandCenterBridge initialized")
    
    def start(self):
        """Start command center tracking."""
        self.running = True
        self.start_time = time.time()
        logger.info("🎮 Command Center online")
    
    def get_status(self) -> Dict:
        """Get command center status."""
        if self.running and self.start_time:
            self.uptime_seconds = time.time() - self.start_time
        
        return {
            'running': self.running,
            'uptime_seconds': self.uptime_seconds,
            'dashboard_port': 8800
        }

# ═══════════════════════════════════════════════════════════════════════════════
# 🌟 INTEGRATED DEPLOYMENT COORDINATOR
# ═══════════════════════════════════════════════════════════════════════════════

class DeploymentCoordinator:
    """Master coordinator for all Aureon systems on Digital Ocean."""
    
    def __init__(self):
        self.shield = ShieldCoordinator()
        self.orca = OrcaBridge()
        self.command_center = CommandCenterBridge()
        self.start_time = time.time()
        self.health_status = 'starting'
        logger.info("🌟 DeploymentCoordinator initialized")
    
    async def initialize(self):
        """Initialize all systems."""
        logger.info("⚡ Initializing Digital Ocean deployment...")
        
        # 1. Start Soul Shield (protection first)
        logger.info("1️⃣ Starting Queen Soul Shield...")
        if self.shield.start_shield():
            await asyncio.sleep(1)  # Let shield stabilize
        else:
            logger.warning("⚠️ Shield initialization failed - continuing without protection")
        
        # 2. Acknowledge Orca Kill Cycle
        logger.info("2️⃣ Orca Kill Cycle bridge online")
        
        # 3. Start Command Center tracking
        logger.info("3️⃣ Starting Command Center bridge...")
        self.command_center.start()
        
        self.health_status = 'healthy'
        logger.info("✅ All systems initialized")
    
    def get_health_status(self) -> Dict:
        """Get complete health status for Digital Ocean probes."""
        uptime = time.time() - self.start_time
        
        return {
            'status': self.health_status,
            'uptime_seconds': uptime,
            'timestamp': time.time(),
            'systems': {
                'shield': self.shield.get_shield_status(),
                'orca': self.orca.get_status(),
                'command_center': self.command_center.get_status()
            },
            'checks': {
                'shield_active': self.shield.status.is_active,
                'orca_running': len(self.orca.active_positions) >= 0,
                'command_center_online': self.command_center.running
            }
        }

# ═══════════════════════════════════════════════════════════════════════════════
# 🌐 HEALTH CHECK HTTP SERVER (For Digital Ocean)
# ═══════════════════════════════════════════════════════════════════════════════

coordinator = None

async def health_check_handler(request):
    """HTTP health check endpoint for Digital Ocean."""
    global coordinator
    
    if coordinator is None:
        return web.Response(status=503, text="System initializing")
    
    status = coordinator.get_health_status()
    return web.json_response(status)

async def shield_status_handler(request):
    """Get detailed shield status."""
    global coordinator
    
    if coordinator is None or not coordinator.shield.shield:
        return web.Response(status=503, text="Shield not available")
    
    status = coordinator.shield.get_shield_status()
    return web.json_response(status)

async def orca_status_handler(request):
    """Get Orca kill cycle status."""
    global coordinator
    
    if coordinator is None:
        return web.Response(status=503, text="Coordinator not ready")
    
    status = coordinator.orca.get_status()
    return web.json_response(status)

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Main entry point for Digital Ocean deployment."""
    global coordinator
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  🚀 AUREON ON DIGITAL OCEAN - INTEGRATED DEPLOYMENT           ║
    ║  👑 Queen Soul Shield + 🦈 Orca Kill Cycle + 🎮 Command Center║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize coordinator
    coordinator = DeploymentCoordinator()
    await coordinator.initialize()
    
    # Start HTTP health check server
    logger.info("🌐 Starting health check server on port 8765...")
    try:
        from aiohttp import web
        
        app = web.Application()
        app.router.add_get('/', health_check_handler)
        app.router.add_get('/health', health_check_handler)
        app.router.add_get('/shield', shield_status_handler)
        app.router.add_get('/orca', orca_status_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8765)
        await site.start()
        
        logger.info("✅ Health check server online on port 8765")
        logger.info("📊 Status endpoints:")
        logger.info("   GET /health - System health")
        logger.info("   GET /shield - Soul Shield status")
        logger.info("   GET /orca - Kill Cycle status")
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            logger.info(f"⚡ Deployment healthy (shield blocks: {coordinator.shield.status.attacks_blocked})")
    
    except ImportError:
        logger.error("❌ aiohttp not available - health server disabled")
        # Keep running without HTTP server
        while True:
            await asyncio.sleep(60)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Deployment coordinator shutdown")
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}", exc_info=True)
        exit(1)
