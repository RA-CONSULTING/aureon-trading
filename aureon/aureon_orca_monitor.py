#!/usr/bin/env python3
"""
🐋 AUREON ORCA MONITOR - Orca Kill Cycle State Publisher to ThoughtBus
=======================================================================

Monitors the Orca kill cycle execution and publishes its state to ThoughtBus
for consumption by the unified dashboard, system coordinator, and other systems.

Features:
  - Tracks Orca execution state
  - Monitors active positions
  - Publishes execution events to ThoughtBus
  - Integrates with System Coordinator for dependency management

Author: Aureon Trading System
Date: March 2026
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import logging

# Import ThoughtBus for pub/sub messaging
try:
    from aureon_thought_bus import ThoughtBus
except ImportError:
    ThoughtBus = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrcaMonitor:
    """
    Monitors Orca kill cycle state and publishes to ThoughtBus.
    """

    def __init__(self):
        """Initialize the Orca monitor."""
        self.thought_bus = ThoughtBus() if ThoughtBus else None
        self.state_file = Path(__file__).parent / "orca_state.json"
        self.is_running = False
        self.startup_time = time.time()

        # State tracking
        self.execution_state = "idle"  # idle, starting, running, stopping, stopped, failed
        self.active_positions: Dict[str, Dict] = {}
        self.total_positions_executed = 0
        self.total_pnl = 0.0
        self.last_heartbeat = time.time()

        logger.info("OrcaMonitor initialized")

    def set_execution_state(self, state: str, details: Optional[Dict] = None):
        """
        Update Orca execution state.

        Args:
            state: New execution state
            details: Optional details about the state change
        """
        old_state = self.execution_state
        self.execution_state = state
        self.last_heartbeat = time.time()

        logger.info(f"Orca state: {old_state} → {state}")

        # Publish state change to ThoughtBus
        self._publish_state_change(old_state, state, details)

        # Save state to disk
        self._save_state()

    def add_position(self, symbol: str, side: str, quantity: float, entry_price: float,
                     target_price: float, stop_loss: float):
        """
        Register a new position being executed by Orca.

        Args:
            symbol: Trading pair
            side: "BUY" or "SELL"
            quantity: Position size
            entry_price: Entry price
            target_price: Target profit price
            stop_loss: Stop loss price
        """
        position_id = f"{symbol}_{int(time.time() * 1000)}"

        self.active_positions[position_id] = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": entry_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "opened_at": datetime.now().isoformat(),
            "status": "open",
            "pnl": 0.0,
            "pnl_pct": 0.0
        }

        logger.info(
            f"Registered position {symbol}: {side} {quantity} @ {entry_price}, "
            f"target={target_price}, stop={stop_loss}"
        )

        # Publish position opened event
        self._publish_position_event("opened", position_id, self.active_positions[position_id])

    def update_position(self, position_id: str, current_price: float, status: str = "open"):
        """
        Update a position's current price and status.

        Args:
            position_id: Position identifier
            current_price: Current market price
            status: Position status ("open", "closed", "stopped_out")
        """
        if position_id not in self.active_positions:
            logger.warning(f"Position {position_id} not found")
            return

        position = self.active_positions[position_id]

        # Calculate P&L
        if position["side"] == "BUY":
            pnl = (current_price - position["entry_price"]) * position["quantity"]
        else:  # SELL
            pnl = (position["entry_price"] - current_price) * position["quantity"]

        position["current_price"] = current_price
        position["pnl"] = pnl
        position["pnl_pct"] = (pnl / (position["entry_price"] * position["quantity"])) * 100
        position["status"] = status

        if status != "open":
            position["closed_at"] = datetime.now().isoformat()
            self.total_pnl += pnl
            self.total_positions_executed += 1

        # Publish position update
        self._publish_position_event("updated", position_id, position)

    def get_orca_status(self) -> Dict:
        """
        Get current Orca execution status.

        Returns:
            Current status snapshot
        """
        return {
            "state": self.execution_state,
            "is_running": self.execution_state == "running",
            "uptime": time.time() - self.startup_time,
            "last_heartbeat": self.last_heartbeat,
            "active_positions": len(self.active_positions),
            "total_positions_executed": self.total_positions_executed,
            "total_pnl": self.total_pnl,
            "positions": list(self.active_positions.values()),
            "timestamp": datetime.now().isoformat()
        }

    def _publish_state_change(self, old_state: str, new_state: str, details: Optional[Dict] = None):
        """Publish Orca state change to ThoughtBus."""
        if not self.thought_bus:
            return

        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "old_state": old_state,
                "new_state": new_state,
                "details": details or {},
                "status": self.get_orca_status()
            }
            self.thought_bus.publish("orca.state_change", event)
        except Exception as e:
            logger.error(f"Failed to publish state change: {e}")

    def _publish_position_event(self, event_type: str, position_id: str, position: Dict):
        """Publish position event to ThoughtBus."""
        if not self.thought_bus:
            return

        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,  # "opened", "updated", "closed"
                "position_id": position_id,
                "position": position,
                "orca_status": self.get_orca_status()
            }
            self.thought_bus.publish("orca.position_event", event)
        except Exception as e:
            logger.error(f"Failed to publish position event: {e}")

    def _save_state(self):
        """Save current state to disk."""
        try:
            state_data = {
                "timestamp": datetime.now().isoformat(),
                "execution_state": self.execution_state,
                "active_positions": self.active_positions,
                "total_positions_executed": self.total_positions_executed,
                "total_pnl": self.total_pnl
            }

            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        """Load state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.execution_state = data.get("execution_state", "idle")
                    self.active_positions = data.get("active_positions", {})
                    self.total_positions_executed = data.get("total_positions_executed", 0)
                    self.total_pnl = data.get("total_pnl", 0.0)
                    logger.info(f"Loaded state from disk")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    async def monitor_orca(self, interval: float = 1.0):
        """
        Continuously monitor and publish Orca state.

        Args:
            interval: Update interval in seconds
        """
        logger.info("Starting Orca monitoring")
        self._load_state()

        try:
            while True:
                # Get current status
                status = self.get_orca_status()

                # Publish to ThoughtBus
                if self.thought_bus:
                    try:
                        self.thought_bus.publish("orca.monitor", status)
                    except Exception as e:
                        logger.debug(f"Error publishing monitor: {e}")

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Orca monitoring stopped")
        except Exception as e:
            logger.error(f"Error in orca monitoring: {e}")

    def register_with_coordinator(self):
        """Register Orca with the system coordinator."""
        try:
            from aureon_system_coordinator import SystemCoordinator

            coordinator = SystemCoordinator()
            coordinator.set_system_state(
                "orca_complete_kill_cycle",
                "running" if self.execution_state == "running" else "idle",
                metadata={"active_positions": len(self.active_positions)}
            )
            logger.info("Registered Orca with system coordinator")
        except Exception as e:
            logger.warning(f"Could not register with coordinator: {e}")


async def main():
    """Test the Orca monitor."""
    monitor = OrcaMonitor()

    # Simulate Orca execution
    monitor.set_execution_state("starting")
    await asyncio.sleep(0.5)

    monitor.set_execution_state("running")

    # Simulate a position
    monitor.add_position("BTC", "BUY", 1.0, 97500, 98500, 96500)

    # Simulate price update
    await asyncio.sleep(1)
    monitor.update_position("BTC_" + str(int(time.time() * 1000)), 98000, "open")

    # Show status
    status = monitor.get_orca_status()
    print(f"\n✅ Orca Status:")
    print(f"   State: {status['state']}")
    print(f"   Active Positions: {status['active_positions']}")
    print(f"   Total P&L: ${status['total_pnl']:.2f}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
