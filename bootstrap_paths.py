"""
Aureon Trading - Python Path Bootstrap

Adds all PEFCφS layer directories to sys.path so that existing flat-module
imports (like `from aureon_baton_link import ...`) continue to work after the
reorganization.

Usage:
    At the top of any script that uses cross-layer imports, add:

        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        # or if running from repo root:
        import bootstrap_paths

Alternatively, set the AUREON_ROOT env var and use:

        import bootstrap_paths

This exists because the codebase was reorganized into PEFCφS layers
(1_substrate, 2_dynamics, 3_forcing, 4_output) while the internal imports
still use flat top-level module names.
"""

import os
import sys
from pathlib import Path

# Detect repo root (directory containing this file)
_REPO_ROOT = Path(__file__).parent.resolve()

# All directories that contain flat Python modules referenced by other layers
_LAYER_DIRS = [
    "1_substrate/frequencies",
    "1_substrate/market_feeds",
    "1_substrate/data_models",
    "2_dynamics/trading_logic",
    "2_dynamics/probability_networks",
    "2_dynamics/echo_feedback",
    "2_dynamics/multiverse_branches",
    "3_forcing/market_events",
    "3_forcing/execution_engines",
    "3_forcing/coherence_gates",
    "3_forcing/real_time_triggers",
    "4_output/trade_outputs",
    "4_output/portfolio_management",
    "4_output/performance_metrics",
    "4_output/dashboard",
    "scripts/entry_points",
    "scripts/utilities",
    "scripts/management",
]


def setup_paths(repo_root: Path = _REPO_ROOT) -> list[str]:
    """
    Add all PEFCφS layer directories to sys.path.
    Returns the list of added paths.
    """
    added = []
    repo_root = Path(repo_root).resolve()

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
        added.append(str(repo_root))

    for layer_rel in _LAYER_DIRS:
        layer_path = repo_root / layer_rel
        if layer_path.is_dir() and str(layer_path) not in sys.path:
            sys.path.insert(0, str(layer_path))
            added.append(str(layer_path))

    return added


# Auto-run on import
_added_paths = setup_paths()

if __name__ == "__main__":
    print(f"Aureon PEFCφS Path Bootstrap")
    print(f"Repo root: {_REPO_ROOT}")
    print(f"\nAdded {len(_added_paths)} paths to sys.path:")
    for p in _added_paths:
        print(f"  + {p}")
