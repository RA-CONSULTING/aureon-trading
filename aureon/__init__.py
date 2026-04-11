"""
AUREON TRADING SYSTEM
=====================

The Unified Quantum Trading System
From Atom to Multiverse

Core Modules:
- aureon_nexus: The central nervous system connecting all modules
- aureon_omega: Complete Omega equation system
- aureon_infinite: 10-9-1 Queen Hive model
- aureon_multiverse: Atom to Multiverse ladder
- aureon_piano: Multi-coin harmonic trading
- aureon_unified: State bus and communication layer
- aureon_qgita: Quantum Gita consciousness
- binance_client: Single execution layer

Subpackages:
- aureon.decoders: Hermetic-to-computational translation layer
    Civilizational DNA decoders (Aztec, Celtic, Egyptian, I Ching, Japanese,
    Maya, Ming/Japan, Mogollon, Sumerian) plus Emerald Tablet spec,
    Maeshowe Seer decode, and Grail Convergence triangulation.
- aureon.civilizational_dna: Ten-Sequence Map Engine
- aureon.geopolitical_forensics: Geopolitical pattern analysis
- aureon.harmonic_nexus_bridge: Bridge between harmonic and nexus layers

Usage:
    from aureon import AureonNexus

    nexus = AureonNexus()
    nexus.run(cycles=100, interval=5)

    # Access decoders directly:
    from aureon.decoders import EgyptianDecoder, MingJapanDecoder
    from aureon.decoders.grail_convergence import triangulate

Gary Leckey & GitHub Copilot | November 2025
"""

from importlib import import_module

__version__ = "1.0.0"
__author__ = "Gary Leckey & GitHub Copilot"

_NEXUS_EXPORTS = {
    "AureonNexus",
    "MasterEquation",
    "QueenHive",
    "NexusBus",
    "NEXUS",
    "ModuleState",
    "PHI",
    "LOVE_FREQUENCY",
    "SCHUMANN_BASE",
    "FIBONACCI",
    "PRIMES",
    "SOLFEGGIO",
    "AURIS_NODES",
    "RAINBOW_STATES",
    "LADDER_LEVELS",
    "kelly_fraction",
    "get_ladder_level",
}


def __getattr__(name: str):
    if name in _NEXUS_EXPORTS:
        module = import_module("aureon_nexus")
        return getattr(module, name)
    if name == "BinanceClient":
        module = import_module("binance_client")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | _NEXUS_EXPORTS | {"BinanceClient"})

# Convenience function for quick start
def start_trading(cycles: int = 100, interval: float = 5.0, symbol: str = "BTCUSDT"):
    """
    Quick start function to begin trading.
    
    Args:
        cycles: Number of trading cycles
        interval: Seconds between cycles
        symbol: Trading symbol (default BTCUSDT)
    """
    AureonNexus = __getattr__("AureonNexus")
    nexus = AureonNexus()
    nexus.run(cycles=cycles, interval=interval)
    return nexus

__all__ = [
    # Classes
    "AureonNexus",
    "MasterEquation", 
    "QueenHive",
    "NexusBus",
    "BinanceClient",
    "ModuleState",
    
    # Global instances
    "NEXUS",
    
    # Constants
    "PHI",
    "LOVE_FREQUENCY",
    "SCHUMANN_BASE",
    "FIBONACCI",
    "PRIMES",
    "SOLFEGGIO",
    "AURIS_NODES",
    "RAINBOW_STATES",
    "LADDER_LEVELS",
    
    # Functions
    "kelly_fraction",
    "get_ladder_level",
    "start_trading",
]
