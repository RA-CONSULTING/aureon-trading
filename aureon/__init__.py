"""
AUREON TRADING SYSTEM
=====================

The Unified Quantum Trading System
From Atom to Multiverse 🌌

Core Modules:
- aureon_nexus: The central nervous system connecting all modules
- aureon_omega: Complete Ω equation system
- aureon_infinite: 10-9-1 Queen Hive model  
- aureon_multiverse: Atom to Multiverse ladder
- aureon_piano: Multi-coin harmonic trading
- aureon_unified: State bus and communication layer
- aureon_qgita: Quantum Gita consciousness
- binance_client: Single execution layer

Usage:
    from aureon import AureonNexus
    
    nexus = AureonNexus()
    nexus.run(cycles=100, interval=5)

Gary Leckey & GitHub Copilot | November 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
__version__ = "1.0.0"
__author__ = "Gary Leckey & GitHub Copilot"

# Core exports
from aureon_nexus import (
    AureonNexus,
    MasterEquation,
    QueenHive,
    NexusBus,
    NEXUS,
    ModuleState,
    
    # Constants
    PHI,
    LOVE_FREQUENCY,
    SCHUMANN_BASE,
    FIBONACCI,
    PRIMES,
    SOLFEGGIO,
    AURIS_NODES,
    RAINBOW_STATES,
    LADDER_LEVELS,
    
    # Functions
    kelly_fraction,
    get_ladder_level,
)

from binance_client import BinanceClient

# Convenience function for quick start
def start_trading(cycles: int = 100, interval: float = 5.0, symbol: str = "BTCUSDT"):
    """
    Quick start function to begin trading.
    
    Args:
        cycles: Number of trading cycles
        interval: Seconds between cycles
        symbol: Trading symbol (default BTCUSDT)
    """
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
