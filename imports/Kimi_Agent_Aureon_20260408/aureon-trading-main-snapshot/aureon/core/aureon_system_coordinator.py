#!/usr/bin/env python3
"""
🔗 AUREON SYSTEM COORDINATOR - Multi-System Synchronization & Dependency Manager
==================================================================================

Tracks system states, dependencies, and readiness. Ensures systems can safely
coordinate before critical operations like Orca kill cycle execution.

Features:
  - Real-time system state tracking (ready, running, failed, idle)
  - Dependency graph validation
  - Pre-execution readiness checks
  - Multi-system coordination events via ThoughtBus
  - System health monitoring and alerts

Author: Aureon Trading System
Date: March 2026
"""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime
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


class SystemState(Enum):
    """System operational states."""
    IDLE = "idle"
    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SystemCategory(Enum):
    """System categories from registry."""
    INTELLIGENCE = "Intelligence Gatherers"
    MARKET_SCANNERS = "Market Scanners"
    BOT_TRACKING = "Bot Tracking"
    MOMENTUM = "Momentum Systems"
    PROBABILITY = "Probability & Prediction"
    NEURAL_NETS = "Neural Networks"
    CODEBREAKING = "Codebreaking & Harmonics"
    QUANTUM = "Stargate & Quantum"
    DASHBOARDS = "Dashboards"
    COMMUNICATION = "Communication"
    EXECUTION = "Execution Engines"
    EXCHANGE = "Exchange Clients"


@dataclass
class SystemDependency:
    """Represents a system dependency."""
    system_name: str
    required_for: str  # System that requires this one
    required: bool = True  # If False, optional dependency
    min_version: Optional[str] = None


@dataclass
class SystemState_Data:
    """Current state of a system."""
    name: str
    category: str
    state: SystemState = SystemState.UNKNOWN
    last_heartbeat: float = field(default_factory=time.time)
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    ready_for_orca: bool = False  # Specifically for Orca execution


class SystemCoordinator:
    """
    Manages system coordination, dependencies, and readiness checks.
    """

    def __init__(self, registry_path: str = "aureon_system_registry.json"):
        """
        Initialize the coordinator.

        Args:
            registry_path: Path to system registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.systems: Dict[str, SystemState_Data] = {}
        self.dependencies: Dict[str, List[SystemDependency]] = {}
        self.thought_bus = ThoughtBus() if ThoughtBus else None
        self.startup_time = time.time()

        self._load_registry()
        self._initialize_dependencies()
        logger.info(f"SystemCoordinator initialized with {len(self.systems)} systems")

    def _load_registry(self):
        """Load system registry and initialize system states."""
        try:
            with open(self.registry_path, 'r') as f:
                registry = json.load(f)

            # Parse registry and create system states
            for category_name, category_data in registry.get("categories", {}).items():
                for system in category_data.get("systems", []):
                    sys_name = system.get("name")
                    self.systems[sys_name] = SystemState_Data(
                        name=sys_name,
                        category=category_name,
                        state=SystemState.IDLE,
                        metadata={
                            "filepath": system.get("filepath"),
                            "loc": system.get("loc"),
                            "is_dashboard": system.get("is_dashboard"),
                            "has_thought_bus": system.get("has_thought_bus"),
                            "has_queen_integration": system.get("has_queen_integration"),
                        }
                    )
            logger.info(f"Loaded {len(self.systems)} systems from registry")
        except Exception as e:
            logger.warning(f"Could not load registry: {e}")

    def _initialize_dependencies(self):
        """Initialize system dependencies."""
        # Orca execution requires exchange clients
        orca_requires = [
            "kraken_client",
            "binance_client",
            "alpaca_client",
        ]

        # Add dependencies
        for system_name in orca_requires:
            dep = SystemDependency(
                system_name=system_name,
                required_for="orca_complete_kill_cycle",
                required=True
            )
            if "orca_complete_kill_cycle" not in self.dependencies:
                self.dependencies["orca_complete_kill_cycle"] = []
            self.dependencies["orca_complete_kill_cycle"].append(dep)

        logger.info("Initialized system dependencies")

    def set_system_state(self, system_name: str, state: SystemState,
                         error_message: Optional[str] = None,
                         metadata: Optional[Dict] = None):
        """
        Update a system's state.

        Args:
            system_name: Name of the system
            state: New system state
            error_message: Error message if state is FAILED
            metadata: Additional metadata
        """
        if system_name not in self.systems:
            logger.warning(f"System {system_name} not found in registry")
            return

        sys = self.systems[system_name]
        old_state = sys.state
        sys.state = state
        sys.last_heartbeat = time.time()

        if error_message:
            sys.error_message = error_message

        if metadata:
            sys.metadata.update(metadata)

        # Determine Orca readiness
        if system_name in self._get_orca_dependencies():
            sys.ready_for_orca = state in [SystemState.READY, SystemState.RUNNING]

        logger.info(f"System {system_name}: {old_state.value} → {state.value}")

        # Publish to ThoughtBus
        self._publish_state_change(system_name, old_state, state)

    def _get_orca_dependencies(self) -> List[str]:
        """Get list of systems Orca depends on."""
        if "orca_complete_kill_cycle" in self.dependencies:
            return [
                dep.system_name
                for dep in self.dependencies["orca_complete_kill_cycle"]
                if dep.required
            ]
        return []

    def can_execute_orca(self) -> tuple[bool, List[str]]:
        """
        Check if all Orca dependencies are ready.

        Returns:
            (can_execute: bool, blocked_by: List[str])
        """
        blocked_systems = []

        for dep_name in self._get_orca_dependencies():
            if dep_name not in self.systems:
                blocked_systems.append(dep_name)
                continue

            sys = self.systems[dep_name]
            if sys.state not in [SystemState.READY, SystemState.RUNNING]:
                blocked_systems.append(f"{dep_name} ({sys.state.value})")

        return len(blocked_systems) == 0, blocked_systems

    def get_coordination_state(self) -> Dict:
        """
        Get current coordination state snapshot.

        Returns:
            Complete coordination state for dashboard display
        """
        can_orca, blocked = self.can_execute_orca()

        # Count systems by state
        state_counts = {}
        for state in SystemState:
            state_counts[state.value] = sum(
                1 for sys in self.systems.values() if sys.state == state
            )

        # Group by category
        by_category = {}
        for sys in self.systems.values():
            if sys.category not in by_category:
                by_category[sys.category] = []
            by_category[sys.category].append({
                "name": sys.name,
                "state": sys.state.value,
                "ready_for_orca": sys.ready_for_orca,
                "last_heartbeat": sys.last_heartbeat,
                "error": sys.error_message
            })

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - self.startup_time,
            "total_systems": len(self.systems),
            "state_counts": state_counts,
            "systems_by_category": by_category,
            "orca_ready": can_orca,
            "orca_blockers": blocked,
            "orca_dependencies": {
                "required": self._get_orca_dependencies(),
                "all_ready": all(
                    self.systems[dep].state in [SystemState.READY, SystemState.RUNNING]
                    for dep in self._get_orca_dependencies()
                    if dep in self.systems
                )
            }
        }

    def _publish_state_change(self, system_name: str, old_state: SystemState,
                              new_state: SystemState):
        """Publish system state change to ThoughtBus."""
        if not self.thought_bus:
            return

        try:
            event = {
                "timestamp": datetime.now().isoformat(),
                "system": system_name,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "coordination_state": self.get_coordination_state()
            }
            self.thought_bus.publish("coordination.state_change", event)
        except Exception as e:
            logger.error(f"Failed to publish state change: {e}")

    def check_system_health(self, timeout: float = 5.0) -> Dict[str, bool]:
        """
        Check health of all monitored systems.

        Args:
            timeout: Heartbeat timeout threshold in seconds

        Returns:
            Dict of system_name -> is_healthy
        """
        current_time = time.time()
        health = {}

        for sys_name, sys in self.systems.items():
            # System is healthy if:
            # 1. State is not FAILED or UNKNOWN
            # 2. Heartbeat is recent (within timeout)
            is_healthy = (
                sys.state not in [SystemState.FAILED, SystemState.UNKNOWN] and
                (current_time - sys.last_heartbeat) < timeout
            )
            health[sys_name] = is_healthy

            if not is_healthy and sys.state not in [SystemState.STOPPED, SystemState.IDLE]:
                logger.warning(f"System {sys_name} may be unhealthy")

        return health

    def get_system_state(self, system_name: str) -> Optional[Dict]:
        """Get state of a specific system."""
        if system_name not in self.systems:
            return None

        sys = self.systems[system_name]
        return {
            "name": sys.name,
            "category": sys.category,
            "state": sys.state.value,
            "last_heartbeat": sys.last_heartbeat,
            "error": sys.error_message,
            "ready_for_orca": sys.ready_for_orca,
            "metadata": sys.metadata
        }

    async def monitor_coordination(self, interval: float = 1.0):
        """
        Continuously monitor and publish coordination state.

        Args:
            interval: Update interval in seconds
        """
        logger.info("Starting coordination monitoring")

        try:
            while True:
                # Get and publish coordination state
                state = self.get_coordination_state()

                if self.thought_bus:
                    self.thought_bus.publish("coordination.monitor", state)

                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Coordination monitoring stopped")
        except Exception as e:
            logger.error(f"Error in coordination monitoring: {e}")


async def main():
    """Test the coordinator."""
    coordinator = SystemCoordinator()

    # Simulate some system state changes
    coordinator.set_system_state("kraken_client", SystemState.READY)
    coordinator.set_system_state("binance_client", SystemState.READY)
    coordinator.set_system_state("alpaca_client", SystemState.READY)

    # Check Orca readiness
    can_orca, blockers = coordinator.can_execute_orca()
    print(f"\n✅ Can execute Orca: {can_orca}")
    if blockers:
        print(f"   Blocked by: {blockers}")

    # Get coordination state
    state = coordinator.get_coordination_state()
    print(f"\n📊 Coordination State:")
    print(f"   Total systems: {state['total_systems']}")
    print(f"   Orca ready: {state['orca_ready']}")
    print(f"   State counts: {state['state_counts']}")


if __name__ == "__main__":
    asyncio.run(main())
