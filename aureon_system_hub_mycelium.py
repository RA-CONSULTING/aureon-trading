#!/usr/bin/env python3
"""
🍄 AUREON SYSTEM HUB - MYCELIUM INTEGRATION 🍄
==============================================
Connects the static System Hub registry to the live Mycelium Neural Network.

Features:
1. Scans codebase for systems (via SystemRegistry).
2. Connects to the ThoughtBus.
3. Maps dependencies/imports to Neural "Synapses".
4. Broadcasts system health and topography to the network.
5. Allows "Whale Sonar" monitoring of registry changes.

Integration:
- Extends: aureon_system_hub.SystemRegistry
- Connects: aureon_thought_bus.ThoughtBus
- Visualizes: aureon_mycelium.MyceliumNetwork

Author: Aureon Trading System
Date: January 2026
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Ensure UTF-8 on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import Base System Hub
try:
    from aureon_system_hub import SystemRegistry, SystemInfo, SystemCategory
except ImportError:
    print("❌ ERROR: aureon_system_hub.py not found. Cannot integrate.")
    sys.exit(1)

# Import ThoughtBus
try:
    from aureon_thought_bus import ThoughtBus, Thought
except ImportError:
    print("⚠️ WARNING: aureon_thought_bus.py not found. Bus integration disabled.")
    ThoughtBus = None

# Import Mycelium Network
try:
    from aureon_mycelium import MyceliumNetwork, Agent, Neuron, Synapse
except ImportError:
    print("⚠️ WARNING: aureon_mycelium.py not found. Neural mapping disabled.")
    MyceliumNetwork = None

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Hub-Mycelium")

class MyceliumSystemRegistry(SystemRegistry):
    """
    Enhanced SystemRegistry that is 'alive' and connected to the Mycelium Network.
    """
    
    def __init__(self, workspace_path: str = "/workspaces/aureon-trading", bus: Optional['ThoughtBus'] = None):
        super().__init__(workspace_path)
        self.bus = bus
        self.mycelium_node_id = "hub_registry_prime"
        self.network = None
        
        # Initialize Mycelium Network wrapper if available
        if MyceliumNetwork:
            try:
                # We create a lightweight network view
                # Initialize with 0 capital just for mapping structure
                self.network = MyceliumNetwork(initial_capital=0.0, agents_per_hive=1)
                logger.info("🍄 Mycelium Network initialized for topography mapping.")
            except Exception as e:
                logger.error(f"Failed to init MyceliumNetwork: {e}")

    def scan_and_broadcast(self):
        """Scans systems and broadcasts findings to the ThoughtBus."""
        logger.info("🔭 Scanning system topography...")
        self.scan_workspace()
        
        system_count = sum(c.system_count for c in self.categories.values())
        logger.info(f"✅ Scan complete. Found {system_count} systems in {len(self.categories)} categories.")
        
        if self.bus:
            # 1. Broadcast Registry State
            payload = {
                "total_systems": system_count,
                "categories": [c.name for c in self.categories.values()],
                "timestamp": time.time()
            }
            thought = Thought(
                source=self.mycelium_node_id,
                topic="system.registry.scan_complete",
                payload=payload
            )
            self.bus.publish(thought)
            logger.info("📡 Broadcasted 'scan_complete' to ThoughtBus.")
            
            # 2. Broadcast Individual System Nodes (Heartbeats)
            self._broadcast_system_nodes()

    def _broadcast_system_nodes(self):
        """Emits a thought for every key system found."""
        for cat_name, category in self.categories.items():
            for system in category.systems:
                # Calculate 'synaptic weight' based on imports/refs
                weight = 1.0 + (len(system.imports) * 0.1)
                
                payload = {
                    "name": system.name,
                    "category": cat_name,
                    "path": system.filepath,
                    "weight": weight,
                    "dependencies": system.dependencies
                }
                
                self.bus.publish(Thought(
                    source=self.mycelium_node_id,
                    topic=f"system.node.{system.name}",
                    payload=payload
                ))
        logger.info(f"📡 Broadcasted individual nodes for all systems.")

    def generate_neural_map(self) -> Dict[str, Any]:
        """
        Converts the static file dependency graph into a Neural Network structure.
        Files = Neurons
        Imports = Synapses
        """
        files_to_neurons = {}
        synapses = []
        
        # 1. Create Neurons from Systems
        for cat_name, category in self.categories.items():
            for sys in category.systems:
                # Neuron strength based on LOC and importance
                strength = min(1.0, sys.lines_of_code / 1000.0) 
                
                neuron_data = {
                    "id": sys.name,
                    "type": "system_module",
                    "layer": cat_name,
                    "bias": strength,
                    "activation": 0.0  # Static for now
                }
                files_to_neurons[sys.name] = neuron_data

        # 2. Create Synapses from Imports
        for cat_name, category in self.categories.items():
            for sys in category.systems:
                source_id = sys.name
                
                for dep in sys.dependencies:
                    # Clean dependency name (remove .py)
                    target_id = dep.replace('.py', '')
                    
                    if target_id in files_to_neurons:
                        synapses.append({
                            "source": source_id,
                            "target": target_id,
                            "weight": 0.5  # Standard import weight
                        })
        
        neural_map = {
            "neurons": list(files_to_neurons.values()),
            "synapses": synapses,
            "meta": {
                "generated_at": time.time(),
                "node_count": len(files_to_neurons),
                "connection_count": len(synapses)
            }
        }
        
        # If we have a live MyceliumNetwork, we could populate it here
        # But mostly this is for visualization export
        return neural_map

    def export_force_graph(self, filename="mycelium_graph.json"):
        """Exports the neural map for D3/Vis.js visualization."""
        neural_map = self.generate_neural_map()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(neural_map, f, indent=2)
        logger.info(f"🕸️  Exported neural graph to {filename}")


def main():
    print("🍄 Starting Aureon System Hub <-> Mycelium Bridge...")
    
    # Initialize Bus
    bus = None
    if ThoughtBus:
        bus = ThoughtBus()
        # Start bus (it runs in background threads usually, but here we just need to emit)
        print("✅ ThoughtBus connected.")
    
    # Initialize Registry
    registry = MyceliumSystemRegistry(bus=bus)
    
    # Run Scan
    registry.scan_and_broadcast()
    
    # Export Visualization
    registry.export_force_graph()
    
    # Keep alive briefly to ensure bus flush if threaded
    time.sleep(1)
    
    print("\n✅ Mycelium Integration Complete.")
    print(f"   - Systems Scanned: {sum(c.system_count for c in registry.categories.values())}")
    print(f"   - Graph Exported: mycelium_graph.json")

if __name__ == "__main__":
    main()
