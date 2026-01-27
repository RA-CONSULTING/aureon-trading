#!/usr/bin/env python3
"""
PLATYPUS CONFIGURATION & PRESETS
================================

Configurable presets for different analysis modes.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from platypus import PlatypusConfig


# ═══════════════════════════════════════════════════════════════════════════════
# PRESETS
# ═══════════════════════════════════════════════════════════════════════════════

# DEFAULT: Balanced for general ephemeris analysis
DEFAULT = PlatypusConfig(
    dt_hours=6,
    w_S=0.20, w_Q=0.25, w_H=0.25, w_E=0.20, w_O=0.10,
    alpha=0.2,
    beta=0.1,
    use_exponential_memory=True
)

# HIGH_MEMORY: Strong temporal persistence
HIGH_MEMORY = PlatypusConfig(
    dt_hours=6,
    w_S=0.15, w_Q=0.20, w_H=0.20, w_E=0.35, w_O=0.10,
    alpha=0.4,  # Slower decay
    beta=0.15,
    use_exponential_memory=True
)

# LOW_LATENCY: Fast response, minimal memory
LOW_LATENCY = PlatypusConfig(
    dt_hours=3,  # Finer time resolution
    w_S=0.25, w_Q=0.30, w_H=0.30, w_E=0.10, w_O=0.05,
    alpha=0.05,  # Very fast decay
    beta=0.05,
    use_exponential_memory=True
)

# GEOMETRIC_FOCUS: Emphasizes alignment patterns
GEOMETRIC_FOCUS = PlatypusConfig(
    dt_hours=6,
    w_S=0.15, w_Q=0.40, w_H=0.20, w_E=0.15, w_O=0.10,
    alpha=0.2,
    beta=0.1,
    conjunction_threshold_deg=2.0,  # Stricter event detection
    opposition_threshold_deg=2.0
)

# FORCING_FOCUS: Emphasizes distance-based forcing
FORCING_FOCUS = PlatypusConfig(
    dt_hours=6,
    w_S=0.15, w_Q=0.20, w_H=0.40, w_E=0.15, w_O=0.10,
    alpha=0.2,
    beta=0.1
)

# OBSERVER_HEAVY: Strong self-reference / inertia
OBSERVER_HEAVY = PlatypusConfig(
    dt_hours=6,
    w_S=0.15, w_Q=0.20, w_H=0.20, w_E=0.20, w_O=0.25,
    alpha=0.2,
    beta=0.25,  # Stronger self-reference
    use_exponential_memory=True
)

# MOVING_AVERAGE: Use W-step moving average instead of exponential
MOVING_AVERAGE = PlatypusConfig(
    dt_hours=6,
    w_S=0.20, w_Q=0.25, w_H=0.25, w_E=0.20, w_O=0.10,
    memory_window=8,  # 8-step (48h) moving average
    use_exponential_memory=False,
    beta=0.1
)

# STRICT_VALIDATION: More stringent permutation testing
STRICT_VALIDATION = PlatypusConfig(
    dt_hours=6,
    w_S=0.20, w_Q=0.25, w_H=0.25, w_E=0.20, w_O=0.10,
    alpha=0.2,
    beta=0.1,
    n_permutations=5000,  # More permutations
    block_hours=48,  # Larger blocks
    epoch_window_hours=96  # ±4 days
)


# ═══════════════════════════════════════════════════════════════════════════════
# PRESET LOADER
# ═══════════════════════════════════════════════════════════════════════════════

PRESETS = {
    'default': DEFAULT,
    'high_memory': HIGH_MEMORY,
    'low_latency': LOW_LATENCY,
    'geometric': GEOMETRIC_FOCUS,
    'forcing': FORCING_FOCUS,
    'observer': OBSERVER_HEAVY,
    'moving_avg': MOVING_AVERAGE,
    'strict': STRICT_VALIDATION
}


def get_preset(name: str = 'default') -> PlatypusConfig:
    """Get configuration preset by name."""
    if name not in PRESETS:
        valid = ', '.join(PRESETS.keys())
        raise ValueError(f"Unknown preset '{name}'. Valid: {valid}")
    return PRESETS[name]


def list_presets():
    """Print available presets."""
    print("Available Platypus Presets:")
    print("=" * 40)
    for name, config in PRESETS.items():
        print(f"\n{name}:")
        print(f"  Weights: S={config.w_S:.2f} Q={config.w_Q:.2f} H={config.w_H:.2f} E={config.w_E:.2f} O={config.w_O:.2f}")
        print(f"  Memory: α={config.alpha} (exp={config.use_exponential_memory})")
        print(f"  Observer: β={config.beta}")


if __name__ == '__main__':
    list_presets()
