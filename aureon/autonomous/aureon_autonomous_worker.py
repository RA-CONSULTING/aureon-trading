#!/usr/bin/env python3
"""
👑🌌 AUREON AUTONOMOUS ENGINE WORKER 👑🌌
═══════════════════════════════════════════════════════════════════════════

DIGITALOCEAN WORKER SERVICE - FULL AUTONOMOUS TRADING

This worker runs the complete autonomous trading system:
- 9 continuous autonomous loops
- Parallel intelligence subsystems
- Billion dollar goal tracking
- Endless research engine
- Redis connectivity for messaging

Runs as a background service with no web interface.

Gary Leckey | January 2026 | AUTONOMOUS TRADING ENGINE
"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import logging
import signal
import threading

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

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not installed, using system env vars only")

# Enable autonomous control
os.environ['AUREON_ENABLE_AUTONOMOUS_CONTROL'] = '1'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════
# AUTONOMOUS ENGINE WORKER
# ════════════════════════════════════════════════════════════════════════════

class AureonAutonomousWorker:
    """DigitalOcean worker for autonomous trading engine."""

    def __init__(self):
        self.running = False
        self.threads = []
        self.orchestrator = None
        self.autonomous_controller = None

    def start(self):
        """Start the autonomous trading engine."""
        logger.info("🚀 Starting Aureon Autonomous Engine Worker")

        self.running = True

        # Import and start parallel orchestrator
        try:
            try:
                from aureon.autonomous.aureon_parallel_orchestrator import get_parallel_orchestrator
                self.orchestrator = get_parallel_orchestrator()
            except Exception:
                from aureon.autonomous.aureon_parallel_orchestrator import get_orchestrator
                self.orchestrator = get_orchestrator()
            orchestrator_thread = threading.Thread(
                target=self._run_orchestrator,
                daemon=True
            )
            orchestrator_thread.start()
            self.threads.append(orchestrator_thread)
            logger.info("✅ Parallel Orchestrator started")
        except Exception as e:
            logger.error(f"❌ Failed to start Parallel Orchestrator: {e}")

        # Import and start full autonomous controller
        try:
            from aureon.autonomous.aureon_full_autonomous import get_autonomous_controller
            self.autonomous_controller = get_autonomous_controller()
            autonomous_thread = threading.Thread(
                target=self._run_autonomous_controller,
                daemon=True
            )
            autonomous_thread.start()
            self.threads.append(autonomous_thread)
            logger.info("✅ Full Autonomous Controller started")
        except Exception as e:
            logger.error(f"❌ Failed to start Autonomous Controller: {e}")

        # Start Sentient Consciousness Loop (autonomous proactive communication)
        self._sentient_loop = None
        try:
            from aureon.queen.queen_sentient_loop import QueenSentientLoop
            self._sentient_loop = QueenSentientLoop(voice_enabled=True)
            self._sentient_loop.start()
            logger.info("✅ Sentient Consciousness Loop started (autonomous thought every 10s)")
        except Exception as e:
            logger.warning(f"Sentient loop not available: {e}")

        # Keep worker alive
        logger.info("🔄 Aureon Autonomous Engine running... (press Ctrl+C to stop)")
        while self.running:
            time.sleep(1)

    def stop(self):
        """Stop the autonomous trading engine."""
        logger.info("🛑 Stopping Aureon Autonomous Engine Worker")
        self.running = False

        # Stop sentient consciousness loop
        if getattr(self, '_sentient_loop', None):
            try:
                self._sentient_loop.stop()
                logger.info("Sentient Consciousness Loop stopped")
            except Exception:
                pass

        # Stop orchestrator
        if self.orchestrator:
            try:
                self.orchestrator.shutdown()
                logger.info("✅ Parallel Orchestrator stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping orchestrator: {e}")

        # Stop autonomous controller
        if self.autonomous_controller:
            try:
                self.autonomous_controller.stop()
                logger.info("✅ Autonomous Controller stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping autonomous controller: {e}")

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)

        logger.info("🏁 Aureon Autonomous Engine Worker stopped")

    def _run_orchestrator(self):
        """Run the parallel orchestrator in a thread."""
        try:
            self.orchestrator.start_all_systems()
        except Exception as e:
            logger.error(f"❌ Parallel Orchestrator error: {e}")

    def _run_autonomous_controller(self):
        """Run the autonomous controller in a thread."""
        try:
            self.autonomous_controller.start()
        except Exception as e:
            logger.error(f"❌ Autonomous Controller error: {e}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN WORKER ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

def main():
    """Main worker entry point."""
    worker = AureonAutonomousWorker()

    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        worker.start()
    except KeyboardInterrupt:
        worker.stop()
    except Exception as e:
        logger.error(f"Worker error: {e}")
        worker.stop()
        sys.exit(1)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("👑🌌 AUREON AUTONOMOUS ENGINE WORKER")
    print("=" * 70)
    print("   Full autonomous trading system")
    print("   Running as DigitalOcean worker...")
    print("=" * 70 + "\n")

    main()
