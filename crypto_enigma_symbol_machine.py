#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║   🔐⚡ CRYPTO ENIGMA SYMBOL MACHINE ⚡🔐                                              ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                                      ║
║   Every day new coins, tokens, and pairs enter the ecosystem.                        ║
║   This machine sees EVERYTHING - every symbol across every exchange,                 ║
║   from battle-tested veterans to freshly minted listings from today.                 ║
║                                                                                      ║
║   SOURCES:                                                                           ║
║     🟡 Binance   → 2,000+ pairs (public REST, no key)                               ║
║     🐙 Kraken    → 700+ pairs (public REST, no key)                                  ║
║     🦙 Alpaca    → 200+ crypto pairs                                                 ║
║     🦎 CoinGecko → full coin catalog + new listings                                  ║
║                                                                                      ║
║   CLASSIFICATION:                                                                    ║
║     🌱 NEWBORN    → Listed in last 7 days                                            ║
║     🚀 EMERGING   → 8–30 days old                                                    ║
║     🔥 ACTIVE     → 31–180 days old                                                  ║
║     💎 VETERAN    → 180+ days old                                                    ║
║                                                                                      ║
║   INTEGRATION:                                                                       ║
║     → Enriches Ocean Wave Scanner with ALL discovered symbols                        ║
║     → Feeds new discoveries to Thought Bus                                           ║
║     → Saves full catalog to enigma_symbol_catalog.json                              ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import os
import sys
import json
import time
import logging
import threading
import requests
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict

# Windows UTF-8 fix (MANDATORY per project convention)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                          errors='replace', line_buffering=True)
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ─── Thought Bus ──────────────────────────────────────────────────────────────
THOUGHT_BUS_AVAILABLE = False
try:
    from aureon_thought_bus import get_thought_bus, Thought
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    pass

# ─── Exchange clients (optional - public APIs used if unavailable) ─────────────
try:
    from alpaca_client import AlpacaClient
    ALPACA_AVAILABLE = True
except ImportError:
    AlpacaClient = None
    ALPACA_AVAILABLE = False

try:
    from kraken_client import get_kraken_client
    KRAKEN_CLIENT_AVAILABLE = True
except ImportError:
    get_kraken_client = None
    KRAKEN_CLIENT_AVAILABLE = False

# ─── Constants ────────────────────────────────────────────────────────────────
CATALOG_FILE    = "enigma_symbol_catalog.json"
CATALOG_LOCK    = threading.Lock()

NEWBORN_DAYS    = 7
EMERGING_DAYS   = 30
ACTIVE_DAYS     = 180

TIER_NEWBORN    = "🌱 NEWBORN"
TIER_EMERGING   = "🚀 EMERGING"
TIER_ACTIVE     = "🔥 ACTIVE"
TIER_VETERAN    = "💎 VETERAN"
TIER_UNKNOWN    = "❓ UNKNOWN"

# Binance UK/global compatible stable quote currencies
STABLE_QUOTES   = {"USDT", "USDC", "BUSD", "USDS", "USD", "EUR", "GBP"}

# ─── Data models ─────────────────────────────────────────────────────────────
@dataclass
class DiscoveredSymbol:
    """A single discovered trading symbol enriched with metadata."""
    symbol: str                      # e.g. BTC/USDC
    base: str                        # e.g. BTC
    quote: str                       # e.g. USDC
    exchange: str                    # binance | kraken | alpaca | coingecko
    raw_symbol: str                  # original format from exchange
    first_seen: float = 0.0          # unix timestamp when we first saw it
    last_seen: float = 0.0
    is_active: bool = True
    tier: str = TIER_UNKNOWN
    coingecko_id: Optional[str] = None
    market_cap_rank: Optional[int] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "DiscoveredSymbol":
        return DiscoveredSymbol(**{k: v for k, v in d.items()
                                   if k in DiscoveredSymbol.__dataclass_fields__})

    @property
    def age_days(self) -> float:
        if not self.first_seen:
            return 9999
        return (time.time() - self.first_seen) / 86400

    def compute_tier(self) -> str:
        d = self.age_days
        if d <= NEWBORN_DAYS:
            return TIER_NEWBORN
        if d <= EMERGING_DAYS:
            return TIER_EMERGING
        if d <= ACTIVE_DAYS:
            return TIER_ACTIVE
        return TIER_VETERAN


@dataclass
class EnigmaReport:
    """Result of a full discovery scan."""
    scan_time: float = field(default_factory=time.time)
    total_symbols: int = 0
    new_since_last_scan: int = 0
    by_exchange: Dict[str, int] = field(default_factory=dict)
    by_tier: Dict[str, int] = field(default_factory=dict)
    new_listings: List[str] = field(default_factory=list)    # symbols new today
    all_symbols: List[str] = field(default_factory=list)     # flat canonical list


# ─── Main Machine ─────────────────────────────────────────────────────────────
class CryptoEnigmaSymbolMachine:
    """
    Discovers every tradeable symbol across all connected exchanges.
    Tracks age, tier, and feeds new finds into the Ocean Wave Scanner.
    """

    def __init__(self):
        self.catalog: Dict[str, DiscoveredSymbol] = {}   # key = "exchange:BASE/QUOTE"
        self.thought_bus = None
        self._load_catalog()

        if THOUGHT_BUS_AVAILABLE:
            try:
                self.thought_bus = get_thought_bus()
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════

    def _load_catalog(self):
        """Load the persisted symbol catalog from disk."""
        if not os.path.exists(CATALOG_FILE):
            return
        try:
            with open(CATALOG_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for key, d in raw.get("symbols", {}).items():
                try:
                    self.catalog[key] = DiscoveredSymbol.from_dict(d)
                except Exception:
                    pass
            logger.info(f"🔐 Enigma Catalog: loaded {len(self.catalog)} known symbols")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load enigma catalog: {e}")

    def _save_catalog(self):
        """Atomic write of catalog to disk."""
        try:
            with CATALOG_LOCK:
                payload = {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "total": len(self.catalog),
                    "symbols": {k: v.to_dict() for k, v in self.catalog.items()},
                }
                tmp = CATALOG_FILE + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                os.replace(tmp, CATALOG_FILE)
        except Exception as e:
            logger.warning(f"⚠️  Catalog save failed: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # EXCHANGE FETCHERS (all use public REST — no API keys required)
    # ═══════════════════════════════════════════════════════════════════════

    def _fetch_binance_symbols(self) -> List[Tuple[str, str, str]]:
        """
        Fetch all Binance spot pairs via public exchangeInfo endpoint.
        Returns list of (base, quote, raw_symbol).
        """
        results = []
        try:
            url = "https://api.binance.com/api/v3/exchangeInfo"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for sym in data.get("symbols", []):
                if sym.get("status") != "TRADING":
                    continue
                base  = sym.get("baseAsset", "").upper()
                quote = sym.get("quoteAsset", "").upper()
                raw   = sym.get("symbol", "")
                if base and quote and raw:
                    results.append((base, quote, raw))
        except Exception as e:
            logger.warning(f"⚠️  Binance fetch failed: {e}")
        return results

    def _fetch_kraken_symbols(self) -> List[Tuple[str, str, str]]:
        """
        Fetch all Kraken pairs via public AssetPairs endpoint.
        Returns list of (base, quote, raw_symbol).
        """
        results = []
        try:
            url = "https://api.kraken.com/0/public/AssetPairs"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for pair_name, info in data.get("result", {}).items():
                if info.get("status") not in ("online", None):
                    continue
                wsname = info.get("wsname", "")
                if "/" in wsname:
                    base, quote = wsname.split("/", 1)
                else:
                    base  = info.get("base", "").lstrip("XZ")
                    quote = info.get("quote", "").lstrip("XZ")
                # Normalise XBT → BTC
                base  = base.replace("XBT", "BTC").upper()
                quote = quote.replace("XBT", "BTC").upper()
                if base and quote:
                    results.append((base, quote, pair_name))
        except Exception as e:
            logger.warning(f"⚠️  Kraken fetch failed: {e}")
        return results

    def _fetch_alpaca_symbols(self) -> List[Tuple[str, str, str]]:
        """
        Fetch tradeable crypto pairs from Alpaca.
        Returns list of (base, quote, raw_symbol).
        """
        results = []
        if not ALPACA_AVAILABLE:
            return results
        try:
            client = AlpacaClient()
            assets = client.get_tradeable_crypto_assets()
            for a in assets:
                sym = a.get("symbol", "")
                if "/" in sym:
                    base, quote = sym.split("/", 1)
                else:
                    base, quote = sym, "USD"
                results.append((base.upper(), quote.upper(), sym))
        except Exception as e:
            logger.warning(f"⚠️  Alpaca fetch failed: {e}")
        return results

    def _fetch_coingecko_catalog(self) -> List[dict]:
        """
        Fetch full coin list from CoinGecko (no key, rate-limited).
        Returns list of {id, symbol, name}.
        """
        try:
            url = "https://api.coingecko.com/api/v3/coins/list"
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"⚠️  CoinGecko catalog fetch failed: {e}")
            return []

    def _fetch_coingecko_new_listings(self) -> List[dict]:
        """
        Fetch recently added coins from CoinGecko /coins/list/new.
        Returns list of {id, symbol, name, activated_at}.
        """
        try:
            url = "https://api.coingecko.com/api/v3/coins/list/new"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.debug(f"CoinGecko new listings: {e}")
        return []

    # ═══════════════════════════════════════════════════════════════════════
    # CORE DISCOVERY
    # ═══════════════════════════════════════════════════════════════════════

    def discover_all(self) -> EnigmaReport:
        """
        Full discovery scan across all exchanges.
        Updates catalog, returns a rich report.
        """
        print("🔐 CRYPTO ENIGMA SYMBOL MACHINE — Full Scan Starting...")
        print("═" * 70)

        report      = EnigmaReport(scan_time=time.time())
        now         = time.time()
        seen_before = set(self.catalog.keys())
        newly_found : List[str] = []

        # ── 1. Binance ──────────────────────────────────────────────────
        print("  🟡 Scanning Binance...", end=" ", flush=True)
        binance_pairs = self._fetch_binance_symbols()
        binance_added = 0
        for base, quote, raw in binance_pairs:
            key = f"binance:{base}/{quote}"
            if key not in self.catalog:
                self.catalog[key] = DiscoveredSymbol(
                    symbol=f"{base}/{quote}", base=base, quote=quote,
                    exchange="binance", raw_symbol=raw,
                    first_seen=now, last_seen=now,
                )
                newly_found.append(key)
                binance_added += 1
            else:
                self.catalog[key].last_seen = now
        print(f"{len(binance_pairs)} pairs  (+{binance_added} new)")

        # ── 2. Kraken ───────────────────────────────────────────────────
        print("  🐙 Scanning Kraken...", end=" ", flush=True)
        kraken_pairs = self._fetch_kraken_symbols()
        kraken_added = 0
        for base, quote, raw in kraken_pairs:
            key = f"kraken:{base}/{quote}"
            if key not in self.catalog:
                self.catalog[key] = DiscoveredSymbol(
                    symbol=f"{base}/{quote}", base=base, quote=quote,
                    exchange="kraken", raw_symbol=raw,
                    first_seen=now, last_seen=now,
                )
                newly_found.append(key)
                kraken_added += 1
            else:
                self.catalog[key].last_seen = now
        print(f"{len(kraken_pairs)} pairs  (+{kraken_added} new)")

        # ── 3. Alpaca ───────────────────────────────────────────────────
        print("  🦙 Scanning Alpaca...", end=" ", flush=True)
        alpaca_pairs = self._fetch_alpaca_symbols()
        alpaca_added = 0
        for base, quote, raw in alpaca_pairs:
            key = f"alpaca:{base}/{quote}"
            if key not in self.catalog:
                self.catalog[key] = DiscoveredSymbol(
                    symbol=f"{base}/{quote}", base=base, quote=quote,
                    exchange="alpaca", raw_symbol=raw,
                    first_seen=now, last_seen=now,
                )
                newly_found.append(key)
                alpaca_added += 1
            else:
                self.catalog[key].last_seen = now
        print(f"{len(alpaca_pairs)} pairs  (+{alpaca_added} new)")

        # ── 4. CoinGecko new listings ───────────────────────────────────
        print("  🦎 Checking CoinGecko new listings...", end=" ", flush=True)
        cg_new = self._fetch_coingecko_new_listings()
        cg_added = 0
        for coin in cg_new:
            base = coin.get("symbol", "").upper()
            raw_id = coin.get("id", "")
            if not base:
                continue
            # Mark as NEWBORN in catalog against any quote
            for key, sym in self.catalog.items():
                if sym.base == base and sym.tier in (TIER_UNKNOWN, TIER_VETERAN):
                    sym.coingecko_id = raw_id
                    # Backfill first_seen if CoinGecko gives us activated_at
                    activated = coin.get("activated_at")
                    if activated:
                        try:
                            dt = datetime.fromisoformat(activated.replace("Z", "+00:00"))
                            sym.first_seen = dt.timestamp()
                        except Exception:
                            pass
                    cg_added += 1
            # If it's brand new and not in catalog at all, register as coingecko source
            cg_key = f"coingecko:{base}/USD"
            if cg_key not in self.catalog:
                activated = coin.get("activated_at")
                fs = now
                if activated:
                    try:
                        dt = datetime.fromisoformat(activated.replace("Z", "+00:00"))
                        fs = dt.timestamp()
                    except Exception:
                        pass
                self.catalog[cg_key] = DiscoveredSymbol(
                    symbol=f"{base}/USD", base=base, quote="USD",
                    exchange="coingecko", raw_symbol=raw_id,
                    first_seen=fs, last_seen=now,
                    coingecko_id=raw_id,
                    notes=coin.get("name", ""),
                )
                newly_found.append(cg_key)
                cg_added += 1
        print(f"{len(cg_new)} new coins  (+{cg_added} enriched)")

        # ── 5. Recompute tiers for ALL symbols ──────────────────────────
        for sym in self.catalog.values():
            sym.tier = sym.compute_tier()

        # ── 6. Build report ─────────────────────────────────────────────
        report.total_symbols    = len(self.catalog)
        report.new_since_last_scan = len(newly_found)

        by_exchange: Dict[str, int] = defaultdict(int)
        by_tier:     Dict[str, int] = defaultdict(int)
        for sym in self.catalog.values():
            by_exchange[sym.exchange] += 1
            by_tier[sym.tier]         += 1

        report.by_exchange  = dict(by_exchange)
        report.by_tier      = dict(by_tier)
        report.new_listings = [k.split(":", 1)[1] for k in newly_found[:100]]
        report.all_symbols  = self._build_flat_list()

        # ── 7. Persist & broadcast ──────────────────────────────────────
        self._save_catalog()
        self._emit_discoveries(newly_found)

        return report

    def _build_flat_list(self) -> List[str]:
        """
        Return deduplicated canonical symbols (BASE/QUOTE) sorted by exchange priority.
        Stable quotes only — useful for feeding the Ocean Scanner.
        """
        seen: Set[str] = set()
        result: List[str] = []
        # Priority: binance > kraken > alpaca > coingecko
        for exchange in ("binance", "kraken", "alpaca", "coingecko"):
            for key, sym in self.catalog.items():
                if sym.exchange != exchange:
                    continue
                canon = f"{sym.base}/{sym.quote}"
                if canon not in seen:
                    seen.add(canon)
                    result.append(canon)
        return result

    def _emit_discoveries(self, new_keys: List[str]):
        """Publish new symbol discoveries to the Thought Bus."""
        if not self.thought_bus or not new_keys:
            return
        try:
            from aureon_thought_bus import Thought
            payload = {
                "new_symbols": [k.split(":", 1)[1] for k in new_keys[:50]],
                "count": len(new_keys),
                "timestamp": time.time(),
            }
            self.thought_bus.publish(Thought(
                source="crypto_enigma_symbol_machine",
                topic="symbol.new_discoveries",
                payload=payload,
            ))
        except Exception as e:
            logger.debug(f"Thought bus emit failed: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # QUERY HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def get_new_listings(self, days: int = 7) -> List[DiscoveredSymbol]:
        """Return symbols first seen within the last N days."""
        cutoff = time.time() - (days * 86400)
        results = [s for s in self.catalog.values() if s.first_seen >= cutoff]
        results.sort(key=lambda s: s.first_seen, reverse=True)
        return results

    def get_by_tier(self, tier: str) -> List[DiscoveredSymbol]:
        """Return all symbols matching a given tier string."""
        return [s for s in self.catalog.values() if s.tier == tier]

    def get_by_exchange(self, exchange: str) -> List[DiscoveredSymbol]:
        """Return all symbols for a specific exchange."""
        return [s for s in self.catalog.values()
                if s.exchange.lower() == exchange.lower()]

    def search(self, query: str) -> List[DiscoveredSymbol]:
        """
        Search catalog by base asset, symbol, or notes (case-insensitive).
        """
        q = query.upper()
        results = []
        for sym in self.catalog.values():
            if (q in sym.base or q in sym.symbol.upper() or
                    q in sym.notes.upper() or q in (sym.coingecko_id or "").upper()):
                results.append(sym)
        results.sort(key=lambda s: (s.exchange, s.symbol))
        return results

    def get_for_ocean_scanner(self, exchange: str = "binance",
                               stable_only: bool = True,
                               limit: int = 500) -> List[str]:
        """
        Return symbol list formatted for the Ocean Wave Scanner's CRYPTO_PAIRS.
        Default format: BTCUSDT (no slash, uppercase).
        """
        results = []
        for sym in self.catalog.values():
            if sym.exchange != exchange:
                continue
            if stable_only and sym.quote not in STABLE_QUOTES:
                continue
            # Convert to exchange raw format
            raw = sym.raw_symbol or f"{sym.base}{sym.quote}"
            results.append(raw.upper())
        # Sort by tier (newborns first so they get scanned ASAP)
        tier_order = {TIER_NEWBORN: 0, TIER_EMERGING: 1,
                      TIER_ACTIVE: 2, TIER_VETERAN: 3, TIER_UNKNOWN: 4}
        results.sort(key=lambda r: tier_order.get(
            self.catalog.get(f"{exchange}:{r}", DiscoveredSymbol(
                r, "", "", "", r)).tier, 4))
        return list(dict.fromkeys(results))[:limit]  # dedup, limit

    def enrich_ocean_scanner(self, scanner) -> int:
        """
        Inject all discovered Binance symbols into an OceanWaveScanner instance.
        Returns number of NEW symbols added to its CRYPTO_PAIRS list.
        """
        if not hasattr(scanner, "__class__"):
            return 0

        import aureon_ocean_wave_scanner as _ows
        existing = set(getattr(_ows, "CRYPTO_PAIRS", []))
        new_pairs = self.get_for_ocean_scanner("binance", stable_only=True, limit=1000)
        added = 0
        for raw in new_pairs:
            if raw not in existing:
                _ows.CRYPTO_PAIRS.append(raw)
                added += 1

        if added:
            logger.info(f"🌊 Ocean Scanner enriched: +{added} new symbols injected")
        return added

    # ═══════════════════════════════════════════════════════════════════════
    # DASHBOARD DISPLAY
    # ═══════════════════════════════════════════════════════════════════════

    def print_dashboard(self, report: Optional[EnigmaReport] = None):
        """Print a rich terminal dashboard of the current symbol universe."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print()
        print("╔" + "═" * 70 + "╗")
        print("║  🔐⚡ CRYPTO ENIGMA SYMBOL MACHINE — UNIVERSE DASHBOARD ⚡🔐" + " " * 7 + "║")
        print("╠" + "═" * 70 + "╣")
        print(f"║  Scan time : {now_str:<55} ║")
        print(f"║  Total symbols in catalog : {len(self.catalog):<41} ║")
        if report:
            print(f"║  New this scan            : {report.new_since_last_scan:<41} ║")
        print("╠" + "═" * 70 + "╣")

        # By exchange
        print("║  BY EXCHANGE" + " " * 57 + "║")
        by_ex: Dict[str, int] = defaultdict(int)
        for s in self.catalog.values():
            by_ex[s.exchange] += 1
        icons = {"binance": "🟡", "kraken": "🐙", "alpaca": "🦙", "coingecko": "🦎"}
        for ex, cnt in sorted(by_ex.items(), key=lambda x: -x[1]):
            icon = icons.get(ex, "🔹")
            line = f"    {icon} {ex.capitalize():<12} {cnt:>6} symbols"
            print(f"║  {line:<68} ║")

        print("╠" + "═" * 70 + "╣")

        # By tier
        print("║  BY AGE TIER" + " " * 57 + "║")
        by_tier: Dict[str, int] = defaultdict(int)
        for s in self.catalog.values():
            by_tier[s.tier] += 1
        for tier in (TIER_NEWBORN, TIER_EMERGING, TIER_ACTIVE, TIER_VETERAN, TIER_UNKNOWN):
            cnt = by_tier.get(tier, 0)
            line = f"    {tier:<20} {cnt:>6} symbols"
            print(f"║  {line:<68} ║")

        print("╠" + "═" * 70 + "╣")

        # New listings (last 7 days)
        newborns = self.get_new_listings(7)
        if newborns:
            print(f"║  🌱 NEW LISTINGS (last 7 days) — {len(newborns)} found" + " " * max(0, 36 - len(str(len(newborns)))) + "  ║")
            for sym in newborns[:20]:
                age = f"{sym.age_days:.1f}d"
                line = f"    {sym.exchange:<10} {sym.symbol:<20} {age:>6}"
                if sym.notes:
                    line += f"  {sym.notes[:18]}"
                print(f"║  {line:<68} ║")
            if len(newborns) > 20:
                print(f"║    ... and {len(newborns) - 20} more" + " " * 53 + "║")
        else:
            print("║  🌱 No new listings in last 7 days" + " " * 35 + "║")

        print("╚" + "═" * 70 + "╝")
        print()

    def print_search_results(self, query: str):
        """Search and print results for a base asset query."""
        results = self.search(query)
        print(f"\n🔍 Search: '{query}' → {len(results)} results")
        print("─" * 60)
        if not results:
            print("  No symbols found.")
            return
        for sym in results[:50]:
            age = f"{sym.age_days:.0f}d" if sym.first_seen else "?"
            print(f"  {sym.exchange:<10} {sym.symbol:<22} {sym.tier}  age={age}")
        if len(results) > 50:
            print(f"  ... and {len(results) - 50} more")
        print()


# ─── Standalone CLI ───────────────────────────────────────────────────────────

def _parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="🔐 Crypto Enigma Symbol Machine — discover all symbols",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crypto_enigma_symbol_machine.py              # Full scan + dashboard
  python crypto_enigma_symbol_machine.py --new        # Show new listings only
  python crypto_enigma_symbol_machine.py --search BTC # Search for BTC pairs
  python crypto_enigma_symbol_machine.py --exchange kraken
  python crypto_enigma_symbol_machine.py --tier newborn
  python crypto_enigma_symbol_machine.py --ocean      # List Ocean Scanner symbols
        """,
    )
    parser.add_argument("--new",      action="store_true",  help="Show new listings (last 7 days)")
    parser.add_argument("--days",     type=int, default=7,  help="Days for --new filter (default 7)")
    parser.add_argument("--search",   type=str, default="", help="Search by base asset or name")
    parser.add_argument("--exchange", type=str, default="", help="Filter by exchange")
    parser.add_argument("--tier",     type=str, default="", help="Filter by tier: newborn|emerging|active|veteran")
    parser.add_argument("--ocean",    action="store_true",  help="Print symbols ready for Ocean Scanner")
    parser.add_argument("--no-scan",  action="store_true",  help="Skip live scan, use cached catalog only")
    return parser.parse_args()


def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    args = _parse_args()
    machine = CryptoEnigmaSymbolMachine()

    report = None
    if not args.no_scan:
        report = machine.discover_all()

    # ── Filter/display modes ──────────────────────────────────────────────
    if args.search:
        machine.print_search_results(args.search)
        return

    if args.new:
        listings = machine.get_new_listings(args.days)
        print(f"\n🌱 NEW LISTINGS (last {args.days} days) — {len(listings)} symbols")
        print("─" * 70)
        for sym in listings:
            dt = datetime.fromtimestamp(sym.first_seen).strftime("%Y-%m-%d %H:%M") \
                 if sym.first_seen else "unknown"
            print(f"  {sym.exchange:<10} {sym.symbol:<22} first seen: {dt}  {sym.tier}")
        return

    if args.exchange:
        syms = machine.get_by_exchange(args.exchange)
        print(f"\n📋 {args.exchange.upper()} — {len(syms)} symbols")
        print("─" * 60)
        for s in syms[:100]:
            print(f"  {s.symbol:<22} {s.tier}")
        if len(syms) > 100:
            print(f"  ... and {len(syms) - 100} more")
        return

    TIER_MAP = {
        "newborn":  TIER_NEWBORN,
        "emerging": TIER_EMERGING,
        "active":   TIER_ACTIVE,
        "veteran":  TIER_VETERAN,
    }
    if args.tier:
        tier_str = TIER_MAP.get(args.tier.lower())
        if not tier_str:
            print(f"Unknown tier '{args.tier}'. Use: newborn, emerging, active, veteran")
            return
        syms = machine.get_by_tier(tier_str)
        print(f"\n{tier_str} — {len(syms)} symbols")
        print("─" * 60)
        for s in syms[:100]:
            print(f"  {s.exchange:<10} {s.symbol:<24} age={s.age_days:.0f}d")
        if len(syms) > 100:
            print(f"  ... and {len(syms) - 100} more")
        return

    if args.ocean:
        pairs = machine.get_for_ocean_scanner("binance", limit=500)
        print(f"\n🌊 Ocean Scanner ready pairs (Binance, stable-quote): {len(pairs)}")
        print("─" * 60)
        # Show in columns of 6
        for i in range(0, min(len(pairs), 120), 6):
            row = pairs[i:i+6]
            print("  " + "  ".join(f"{p:<14}" for p in row))
        if len(pairs) > 120:
            print(f"  ... and {len(pairs) - 120} more")
        return

    # Default: full dashboard
    machine.print_dashboard(report)


if __name__ == "__main__":
    main()
