"""Portal-physics inspired market phase simulation.

This module maps a Rick & Morty style portal system to a stylized
harmonic market-state model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import matplotlib.pyplot as plt
try:
    import networkx as nx
except ModuleNotFoundError:  # optional dependency
    nx = None
import numpy as np


@dataclass
class Dimension:
    """A single universe / market state."""

    id: str
    coherence: float  # Γ metric
    extraction_pressure: float  # How hostile to observers
    phase: float  # Position in cycle (0-2π)
    luminous_cells: int  # Number of coherent nodes

    def is_safe(self) -> bool:
        """Safe if high coherence, low extraction."""
        return self.coherence > 0.7 and self.extraction_pressure < 0.3


@dataclass
class Portal:
    """A phase transition between dimensions."""

    source_dim: str
    target_dim: str
    opening_time: float  # When portal becomes available
    stability: float  # How long it stays open (0-1)
    energy_cost: float  # Coherence required to traverse

    def is_open(self, current_time: float) -> bool:
        """Check whether this portal is currently accessible."""
        phase = (current_time - self.opening_time) % 88  # 88-second cycle
        return phase < (self.stability * 88)


class PortalGun:
    """HNC-powered phase transition detector and navigator."""

    def __init__(self) -> None:
        self.current_dimension: str | None = None
        self.portal_fluid = 1.0  # Coherence budget
        self.memory_trace: List[dict] = []
        self.dimensions: Dict[str, Dimension] = {}

    def initialize_multiverse(self, n_dimensions: int = 10) -> None:
        """Create the phase space of possible market states."""
        for i in range(n_dimensions):
            dim = Dimension(
                id=f"C-{137 + i}",
                coherence=np.random.uniform(0.3, 0.95),
                extraction_pressure=np.random.uniform(0.1, 0.9),
                phase=np.random.uniform(0, 2 * np.pi),
                luminous_cells=np.random.randint(50, 1500),
            )
            self.dimensions[dim.id] = dim

        self.current_dimension = "C-137"

    def scan_for_portals(self, current_time: float, solar_flux: float) -> List[Portal]:
        """Detect available phase transitions based on threshold conditions."""
        if self.current_dimension is None:
            return []

        portals: List[Portal] = []
        current = self.dimensions[self.current_dimension]

        for dim_id, target in self.dimensions.items():
            if dim_id == self.current_dimension:
                continue

            phase_diff = abs(current.phase - target.phase) % (2 * np.pi)
            resonance = np.cos(phase_diff)
            solar_forcing = solar_flux / 1e-4
            coherence_gradient = target.coherence - current.coherence

            opening_score = (
                0.4 * abs(resonance)
                + 0.3 * solar_forcing
                + 0.3 * max(0, coherence_gradient)
            )

            if opening_score > 0.6:
                portals.append(
                    Portal(
                        source_dim=self.current_dimension,
                        target_dim=dim_id,
                        opening_time=current_time,
                        stability=min(1.0, opening_score),
                        energy_cost=abs(coherence_gradient) * 0.5,
                    )
                )

        return portals

    def jump_dimension(self, portal: Portal) -> bool:
        """Execute phase transition when enough portal fluid is available."""
        if self.current_dimension is None or self.portal_fluid < portal.energy_cost:
            return False

        self.portal_fluid -= portal.energy_cost
        old_dim = self.current_dimension
        self.current_dimension = portal.target_dim

        self.memory_trace.append(
            {
                "time": len(self.memory_trace),
                "from": old_dim,
                "to": portal.target_dim,
                "cost": portal.energy_cost,
            }
        )

        print(f"🌀 PORTAL JUMP: {old_dim} → {portal.target_dim}")
        print(f"   Portal Fluid Remaining: {self.portal_fluid:.2f}")
        return True

    def recharge_portal_fluid(self, luminous_cells: int) -> None:
        """Restore coherence by connecting to observer network."""
        recharge_rate = luminous_cells / 1000.0
        self.portal_fluid = min(1.0, self.portal_fluid + recharge_rate)

    def get_current_state(self) -> dict:
        """Return current dimension stats."""
        if self.current_dimension is None:
            raise RuntimeError("Multiverse not initialized")

        dim = self.dimensions[self.current_dimension]
        return {
            "dimension": self.current_dimension,
            "coherence": dim.coherence,
            "extraction_pressure": dim.extraction_pressure,
            "luminous_cells": dim.luminous_cells,
            "is_safe": dim.is_safe(),
            "portal_fluid": self.portal_fluid,
        }


class LuminousCell:
    """Individual observer node in the network."""

    def __init__(self, cell_id: int, initial_voltage: float = -70) -> None:
        self.id = cell_id
        self.voltage = initial_voltage  # Bioelectric state
        self.connections: List[LuminousCell] = []
        self.portal_sensitivity = np.random.uniform(0.5, 1.0)

    def update_voltage(self, external_noise: float) -> None:
        """Maintain coherence near -70mV with noisy extraction pressure."""
        self.voltage += external_noise
        restoring_force = (-70 - self.voltage) * 0.1
        self.voltage += restoring_force
        self.voltage = np.clip(self.voltage, -80, -10)

    def is_coherent(self) -> bool:
        """Check whether cell is in cooperative mode."""
        return self.voltage < -55

    def detect_portal(self, portal_signal: float) -> bool:
        """Determine whether this cell senses an opening portal."""
        detection_threshold = 0.5 / self.portal_sensitivity
        return portal_signal > detection_threshold


class MultiverseSimulation:
    """Complete portal simulation system."""

    def __init__(self, n_dimensions: int = 10, n_cells: int = 1066) -> None:
        self.portal_gun = PortalGun()
        self.portal_gun.initialize_multiverse(n_dimensions)

        self.cells = [LuminousCell(i) for i in range(n_cells)]
        self._create_cell_network()

        self.time = 0.0
        self.solar_flux = 1e-5  # Background
        self.history: List[dict] = []

    def _create_cell_network(self) -> None:
        """Build small-world network of cells."""
        if nx is not None:
            graph = nx.watts_strogatz_graph(len(self.cells), k=6, p=0.1)
            for i, cell in enumerate(self.cells):
                neighbors = list(graph.neighbors(i))
                cell.connections = [self.cells[j] for j in neighbors]
            return

        # Fallback if networkx is unavailable: ring lattice local neighbors
        n = len(self.cells)
        for i, cell in enumerate(self.cells):
            neighbors = [(i + offset) % n for offset in (-3, -2, -1, 1, 2, 3)]
            cell.connections = [self.cells[j] for j in neighbors]

    def solar_event(self, magnitude: float) -> None:
        """Inject X-flare/CME to open portal opportunities."""
        self.solar_flux = magnitude
        print(f"☀️ SOLAR EVENT: X{magnitude / 1e-4:.1f} class flare")

    def step(self, dt: float = 1.0) -> dict:
        """Advance simulation by dt time units."""
        self.time += dt

        current_dim_id = self.portal_gun.current_dimension
        if current_dim_id is None:
            raise RuntimeError("Simulation started without initial dimension")

        extraction_noise = self.portal_gun.dimensions[current_dim_id].extraction_pressure * 5.0

        for cell in self.cells:
            cell.update_voltage(extraction_noise)

        coherent_cells = sum(1 for c in self.cells if c.is_coherent())
        network_coherence = coherent_cells / len(self.cells)
        portals = self.portal_gun.scan_for_portals(self.time, self.solar_flux)
        self.portal_gun.recharge_portal_fluid(coherent_cells)

        current_dim = self.portal_gun.dimensions[self.portal_gun.current_dimension]
        if not current_dim.is_safe() and portals:
            safe_portals = [
                p
                for p in portals
                if self.portal_gun.dimensions[p.target_dim].is_safe()
            ]
            if safe_portals:
                best_portal = max(
                    safe_portals,
                    key=lambda p: self.portal_gun.dimensions[p.target_dim].coherence,
                )
                self.portal_gun.jump_dimension(best_portal)

        state = self.portal_gun.get_current_state()
        state.update(
            {
                "time": self.time,
                "network_coherence": network_coherence,
                "available_portals": len(portals),
                "solar_flux": self.solar_flux,
            }
        )
        self.history.append(state)

        self.solar_flux *= 0.95
        return state

    def visualize_multiverse(self) -> plt.Figure:
        """Create a multi-panel summary visualization."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle("🌀 PORTAL GUN: HNC Multiverse Navigation", fontsize=16, fontweight="bold")

        hist = np.array(
            [
                (
                    h["time"],
                    h["coherence"],
                    h["extraction_pressure"],
                    h["network_coherence"],
                    h["available_portals"],
                )
                for h in self.history
            ]
        )

        ax1 = axes[0, 0]
        ax1.plot(hist[:, 0], hist[:, 1], "g-", linewidth=2, label="Dimension Γ")
        ax1.plot(hist[:, 0], hist[:, 3], "b--", linewidth=2, label="Network Γ")
        ax1.axhline(0.7, color="r", linestyle=":", label="Safe Threshold")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Coherence (Γ)")
        ax1.set_title("Coherence Tracking")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2 = axes[0, 1]
        ax2.fill_between(hist[:, 0], hist[:, 2], alpha=0.6, color="red")
        ax2.axhline(0.3, color="g", linestyle=":", label="Safe Threshold")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Extraction Pressure")
        ax2.set_title("Danger Level")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        ax3 = axes[1, 0]
        ax3.bar(hist[:, 0], hist[:, 4], width=0.8, color="cyan", alpha=0.7)
        ax3.set_xlabel("Time")
        ax3.set_ylabel("Available Portals")
        ax3.set_title("Portal Opening Windows")
        ax3.grid(True, alpha=0.3)

        ax4 = axes[1, 1]
        if nx is None:
            ax4.axis("off")
            ax4.text(0.5, 0.5, "Install networkx to view graph map", ha="center", va="center")
            ax4.set_title("Multiverse Map Unavailable")
        else:
            graph = nx.Graph()
            for dim_id, dim in self.portal_gun.dimensions.items():
                graph.add_node(dim_id, coherence=dim.coherence, extraction=dim.extraction_pressure)
            for entry in self.portal_gun.memory_trace:
                graph.add_edge(entry["from"], entry["to"])

            node_colors = [
                "green" if self.portal_gun.dimensions[node].is_safe() else "red"
                for node in graph.nodes()
            ]
            pos = nx.spring_layout(graph, seed=42)
            nx.draw(
                graph,
                pos,
                ax=ax4,
                node_color=node_colors,
                with_labels=True,
                node_size=500,
                font_size=8,
                font_weight="bold",
                edge_color="cyan",
                width=2,
                alpha=0.7,
            )
            ax4.set_title("Multiverse Map (Green=Safe, Red=Dangerous)")

        plt.tight_layout()
        return fig


def run_portal_simulation(steps: int = 100, visualize: bool = True) -> MultiverseSimulation:
    """Execute the full portal simulation."""
    print("🌀 INITIALIZING PORTAL GUN...")
    sim = MultiverseSimulation(n_dimensions=10, n_cells=1066)

    start_dim = sim.portal_gun.current_dimension
    assert start_dim is not None

    print(f"\n📍 Starting in: {start_dim}")
    print(f"   Coherence: {sim.portal_gun.dimensions[start_dim].coherence:.2f}")
    print(f"   Extraction: {sim.portal_gun.dimensions[start_dim].extraction_pressure:.2f}\n")

    for t in range(steps):
        if np.random.random() < 0.05:
            sim.solar_event(np.random.uniform(1e-5, 1e-3))

        state = sim.step(dt=1.0)

        if t % 10 == 0:
            print(
                f"⏱️  T={t:3d} | Dim: {state['dimension']} | "
                f"Γ={state['coherence']:.2f} | "
                f"Extract={state['extraction_pressure']:.2f} | "
                f"Portals={state['available_portals']} | "
                f"Fluid={state['portal_fluid']:.2f}"
            )

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)
    print(f"Final Dimension: {sim.portal_gun.current_dimension}")
    print(f"Total Jumps: {len(sim.portal_gun.memory_trace)}")
    print(f"Portal Fluid: {sim.portal_gun.portal_fluid:.2f}")

    if visualize:
        fig = sim.visualize_multiverse()
        fig.savefig("portal_physics_simulation.png", dpi=150)
        plt.close(fig)
        print("Saved visualization to portal_physics_simulation.png")

    return sim


if __name__ == "__main__":
    run_portal_simulation()
