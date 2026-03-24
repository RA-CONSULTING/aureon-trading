#!/usr/bin/env python3
"""
🦑💰 KRAKEN FEE TRACKER & TIER MANAGER 💰🦑
============================================

Volume-tiered fee detection for Kraken Spot trading.
NO DEATH BY 1000 CUTS - Use the REAL fee rate for your 30-day volume tier!

Kraken Spot Crypto Fee Tiers:
┌─────────────────────┬────────────┬────────────┐
│ 30-Day Volume (USD) │ Maker Fee  │ Taker Fee  │
├─────────────────────┼────────────┼────────────┤
│ $0                  │ 25 bps     │ 40 bps     │
│ $10,000             │ 20 bps     │ 35 bps     │
│ $50,000             │ 14 bps     │ 24 bps     │
│ $100,000            │ 12 bps     │ 22 bps     │  ← ~$123K current tier
│ $250,000            │ 10 bps     │ 20 bps     │
│ $500,000            │  8 bps     │ 18 bps     │
│ $1,000,000          │  6 bps     │ 16 bps     │
│ $2,500,000          │  4 bps     │ 14 bps     │
│ $5,000,000          │  2 bps     │ 12 bps     │
│ $10,000,000         │  0 bps     │ 10 bps     │
│ $100,000,000        │  0 bps     │  8 bps     │
│ $500,000,000        │  0 bps     │  5 bps     │
└─────────────────────┴────────────┴────────────┘

Stablecoin / Pegged Token / FX Pairs Fee Tiers:
┌─────────────────────┬────────────┬────────────┐
│ 30-Day Volume (USD) │ Maker Fee  │ Taker Fee  │
├─────────────────────┼────────────┼────────────┤
│ $0                  │ 20 bps     │ 20 bps     │
│ $50,000             │ 16 bps     │ 16 bps     │
│ $100,000            │ 12 bps     │ 12 bps     │
│ $250,000            │  8 bps     │  8 bps     │
│ $500,000            │  4 bps     │  4 bps     │
│ $1,000,000          │  2 bps     │  2 bps     │
│ $10,000,000         │  0 bps     │  1 bps     │
│ $100,000,000        │  0 bps     │  0.1 bps   │
└─────────────────────┴────────────┴────────────┘

Gary Leckey | March 2026 | PROTECT THE SNOWBALL!
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# 💰 KRAKEN FEE TIER STRUCTURES (As of 2025-2026)
# ═══════════════════════════════════════════════════════════════════════════

# Spot Crypto pairs (BTC, ETH, SOL, etc.)
# (min_volume_usd, max_volume_usd, maker_bps, taker_bps)
KRAKEN_SPOT_CRYPTO_TIERS = [
    (0,               10_000,          25, 40),   # Tier 1
    (10_000,          50_000,          20, 35),   # Tier 2
    (50_000,          100_000,         14, 24),   # Tier 3
    (100_000,         250_000,         12, 22),   # Tier 4  ← ~$123K current
    (250_000,         500_000,         10, 20),   # Tier 5
    (500_000,         1_000_000,        8, 18),   # Tier 6
    (1_000_000,       2_500_000,        6, 16),   # Tier 7
    (2_500_000,       5_000_000,        4, 14),   # Tier 8
    (5_000_000,       10_000_000,       2, 12),   # Tier 9
    (10_000_000,      100_000_000,      0, 10),   # Tier 10
    (100_000_000,     500_000_000,      0,  8),   # Tier 11
    (500_000_000,     float('inf'),     0,  5),   # Tier 12
]

# Stablecoin, Pegged Token, and FX Pairs (USDT/USD, USDC/USD, EUR/USD, etc.)
KRAKEN_STABLE_FX_TIERS = [
    (0,               50_000,          20, 20),   # Tier 1
    (50_000,          100_000,         16, 16),   # Tier 2
    (100_000,         250_000,         12, 12),   # Tier 3  ← ~$123K current
    (250_000,         500_000,          8,  8),   # Tier 4
    (500_000,         1_000_000,        4,  4),   # Tier 5
    (1_000_000,       10_000_000,       2,  2),   # Tier 6
    (10_000_000,      100_000_000,      0,  1),   # Tier 7
    (100_000_000,     float('inf'),     0,  0.1), # Tier 8
]

# Stablecoin / stable-pegged pairs recognized by Kraken
STABLE_FX_QUOTE_ASSETS = {
    'USDT', 'USDC', 'TUSD', 'DAI', 'BUSD', 'USDP', 'GUSD',  # USD stables
    'EUR', 'GBP', 'AUD', 'CAD', 'CHF', 'JPY',                 # FX pairs
    'EURT', 'PYUSD',                                           # Other pegged
}


@dataclass
class KrakenFeeTier:
    """Kraken fee tier for a specific pair type."""
    tier: int
    pair_type: str  # 'spot_crypto' or 'stable_fx'
    min_volume: float
    max_volume: float
    maker_bps: float  # Basis points (1 bps = 0.01%)
    taker_bps: float
    maker_pct: float = field(init=False)
    taker_pct: float = field(init=False)

    def __post_init__(self):
        self.maker_pct = self.maker_bps / 10000
        self.taker_pct = self.taker_bps / 10000

    @property
    def name(self) -> str:
        return f"Tier {self.tier} {self.pair_type} (${self.min_volume:,.0f}-${self.max_volume:,.0f})"

    def __str__(self) -> str:
        return (
            f"KrakenFeeTier(tier={self.tier}, pair_type={self.pair_type}, "
            f"vol=${self.min_volume:,.0f}-${self.max_volume:,.0f}, "
            f"maker={self.maker_bps}bps, taker={self.taker_bps}bps)"
        )


def _resolve_tier(volume: float, tiers: list, pair_type: str) -> KrakenFeeTier:
    """Find the matching fee tier for a given volume."""
    for idx, (min_vol, max_vol, maker, taker) in enumerate(tiers, 1):
        if min_vol <= volume < max_vol:
            return KrakenFeeTier(
                tier=idx,
                pair_type=pair_type,
                min_volume=min_vol,
                max_volume=max_vol,
                maker_bps=maker,
                taker_bps=taker,
            )
    # Fallback: last tier
    min_vol, max_vol, maker, taker = tiers[-1]
    return KrakenFeeTier(
        tier=len(tiers),
        pair_type=pair_type,
        min_volume=min_vol,
        max_volume=max_vol,
        maker_bps=maker,
        taker_bps=taker,
    )


def get_spot_crypto_tier(volume_30d: float) -> KrakenFeeTier:
    """Return the Spot Crypto fee tier for a given 30-day USD volume."""
    return _resolve_tier(volume_30d, KRAKEN_SPOT_CRYPTO_TIERS, 'spot_crypto')


def get_stable_fx_tier(volume_30d: float) -> KrakenFeeTier:
    """Return the Stablecoin/FX fee tier for a given 30-day USD volume."""
    return _resolve_tier(volume_30d, KRAKEN_STABLE_FX_TIERS, 'stable_fx')


def is_stable_fx_pair(symbol: str) -> bool:
    """
    Detect if a symbol uses the Stablecoin/Pegged/FX fee schedule.

    Kraken stable/FX pairs have both legs as stable or fiat currencies,
    e.g. USDT/USD, EUR/USD, GBP/USDT.
    """
    # Normalise: "USDT/USD" -> ["USDT", "USD"], "USDTUSD" -> try split
    if '/' in symbol:
        parts = symbol.upper().split('/')
    else:
        # Try to split e.g. "USDTUSD" into known assets — best-effort
        s = symbol.upper()
        parts = []
        for asset in sorted(STABLE_FX_QUOTE_ASSETS, key=len, reverse=True):
            if s.startswith(asset):
                parts = [asset, s[len(asset):]]
                break
            if s.endswith(asset):
                parts = [s[:-len(asset)], asset]
                break

    if len(parts) == 2:
        base, quote = parts[0], parts[1]
        return base in STABLE_FX_QUOTE_ASSETS and quote in STABLE_FX_QUOTE_ASSETS

    return False


# ═══════════════════════════════════════════════════════════════════════════
# 🦑 KRAKEN FEE TRACKER
# ═══════════════════════════════════════════════════════════════════════════

class KrakenFeeTracker:
    """
    Dynamic Kraken fee tracker.

    Calculates the account's 30-day trading volume by querying
    TradesHistory, then looks up the correct maker/taker rate for
    both Spot Crypto and Stablecoin/FX pairs.

    Results are cached (default 1 hour) to avoid hammering the API.
    """

    def __init__(self, kraken_client=None):
        self.client = kraken_client
        self._30d_volume: float = 0.0
        self._last_check: float = 0.0
        self._check_interval: float = 3600.0  # 1-hour cache

        self._state_file = Path("kraken_fee_tracker_state.json")
        self._load_state()

        logger.info("🦑💰 Kraken Fee Tracker initialized")

    # ───────────────────────────────────────────────────────────────────────
    # Persistence helpers
    # ───────────────────────────────────────────────────────────────────────

    def _load_state(self):
        try:
            if self._state_file.exists():
                data = json.loads(self._state_file.read_text())
                self._30d_volume = float(data.get('volume_30d', 0.0))
                self._last_check = float(data.get('last_check', 0.0))
                logger.info(f"   📂 Loaded state: 30d volume=${self._30d_volume:,.2f}")
        except Exception as e:
            logger.warning(f"   ⚠️  Could not load Kraken fee tracker state: {e}")

    def _save_state(self):
        try:
            self._state_file.write_text(json.dumps({
                'volume_30d': self._30d_volume,
                'last_check': self._last_check,
                'updated_at': datetime.utcnow().isoformat(),
            }, indent=2))
        except Exception as e:
            logger.warning(f"   ⚠️  Could not save Kraken fee tracker state: {e}")

    # ───────────────────────────────────────────────────────────────────────
    # Volume calculation
    # ───────────────────────────────────────────────────────────────────────

    def _calculate_30d_volume(self) -> float:
        """
        Sum the USD cost of all trades in the past 30 days from TradesHistory.

        Each trade record contains a 'cost' field in quote currency (USD for
        most pairs). We sum those to get total 30-day notional volume.
        """
        if self.client is None:
            logger.warning("   ⚠️  No Kraken client — using cached volume")
            return self._30d_volume

        cutoff = time.time() - 30 * 86_400  # 30 days ago
        try:
            trades = self.client.get_trades_history(since=int(cutoff))
        except Exception as e:
            logger.warning(f"   ⚠️  TradesHistory error: {e} — using cached volume")
            return self._30d_volume

        total = 0.0
        for t in trades:
            if float(t.get('time', 0)) >= cutoff:
                total += float(t.get('cost', 0))

        logger.info(f"   📊 30-day volume from {len(trades)} trades: ${total:,.2f}")
        return total

    # ───────────────────────────────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────────────────────────────

    def set_client(self, client):
        """Wire in a KrakenClient after construction."""
        self.client = client
        logger.info("🦑 Fee tracker wired to Kraken client")

    def refresh(self, force: bool = False) -> float:
        """
        Refresh 30-day volume (respects cache interval unless force=True).

        Returns the updated 30-day volume.
        """
        now = time.time()
        if not force and (now - self._last_check) < self._check_interval:
            return self._30d_volume

        self._30d_volume = self._calculate_30d_volume()
        self._last_check = now
        self._save_state()
        return self._30d_volume

    @property
    def volume_30d(self) -> float:
        """30-day trading volume (USD), refreshed if stale."""
        return self.refresh()

    def get_fee_tier(self, symbol: str = '', force_refresh: bool = False) -> KrakenFeeTier:
        """
        Return the current fee tier for *symbol*.

        If *symbol* looks like a stable/FX pair it uses the Stablecoin
        schedule; otherwise the Spot Crypto schedule.
        """
        volume = self.refresh(force=force_refresh)
        if is_stable_fx_pair(symbol):
            return get_stable_fx_tier(volume)
        return get_spot_crypto_tier(volume)

    def get_fee_rates(self, symbol: str = '', is_taker: bool = True) -> Dict[str, float]:
        """
        Return a dict with maker/taker/current fee rates for *symbol*.

        Example return value::

            {
                'maker': 0.0012,   # 12 bps
                'taker': 0.0022,   # 22 bps
                'current': 0.0022, # the rate to use (taker or maker)
                'tier': 4,
                'volume_30d': 123165.87,
                'pair_type': 'spot_crypto',
            }
        """
        tier = self.get_fee_tier(symbol)
        return {
            'maker': tier.maker_pct,
            'taker': tier.taker_pct,
            'current': tier.taker_pct if is_taker else tier.maker_pct,
            'tier': tier.tier,
            'volume_30d': self._30d_volume,
            'pair_type': tier.pair_type,
        }

    def log_summary(self):
        """Print a human-readable fee tier summary to stdout."""
        volume = self.volume_30d
        spot_tier = get_spot_crypto_tier(volume)
        stable_tier = get_stable_fx_tier(volume)

        print("\n" + "=" * 60)
        print("🦑💰 KRAKEN FEE TIER SUMMARY")
        print("=" * 60)
        print(f"   30-Day Volume : ${volume:>15,.2f} USD")
        print(f"   Spot Crypto   : Tier {spot_tier.tier}  "
              f"maker={spot_tier.maker_bps}bps  taker={spot_tier.taker_bps}bps")
        print(f"   Stable / FX   : Tier {stable_tier.tier}  "
              f"maker={stable_tier.maker_bps}bps  taker={stable_tier.taker_bps}bps")
        print("=" * 60 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton (lazy-initialized)
# ─────────────────────────────────────────────────────────────────────────────

_tracker: Optional[KrakenFeeTracker] = None


def get_kraken_fee_tracker(kraken_client=None) -> KrakenFeeTracker:
    """Return (or create) the module-level KrakenFeeTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = KrakenFeeTracker(kraken_client)
    elif kraken_client is not None and _tracker.client is None:
        _tracker.set_client(kraken_client)
    return _tracker


# ─────────────────────────────────────────────────────────────────────────────
# CLI / quick test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Optionally pass a volume on the command line for offline testing
    test_volume = float(sys.argv[1]) if len(sys.argv) > 1 else 123_165.87

    print(f"\nTest volume: ${test_volume:,.2f} USD")
    spot = get_spot_crypto_tier(test_volume)
    stable = get_stable_fx_tier(test_volume)
    print(f"  Spot Crypto  → {spot}")
    print(f"  Stable / FX  → {stable}")

    tracker = KrakenFeeTracker()   # no client — offline test
    tracker._30d_volume = test_volume
    tracker._last_check = time.time()
    tracker.log_summary()
