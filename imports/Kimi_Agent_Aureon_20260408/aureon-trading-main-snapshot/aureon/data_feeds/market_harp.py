"""
market_harp.py  —  Cross-Market Resonance Detector

The Financial Harp:
  Every asset is a string on a harp. When one string is plucked
  (a sudden volatility spike), the vibration travels through the
  instrument and correlated strings resonate — with different
  strengths and lags depending on how tightly they are coupled.

  We detect the pluck in real time, map the resonance path through
  the correlation graph, and generate trade signals on each secondary
  string BEFORE the ripple fully arrives.

Architecture:
  HarpString    — one instrument with rolling volatility tracking
  RippleSignal  — a predicted cross-market trade opportunity
  MarketHarp    — orchestrates detection, propagation, and reporting

Instrument coverage (unified across all sub-traders):
  Crypto      — BTC · ETH · SOL · XRP · ADA · DOT · LINK · LTC
  Indices     — UK100 · US500 · US30 · DE40 · JP225
  Commodities — GOLD · SILVER · OIL · NATGAS
  Forex       — EURUSD · GBPUSD · USDJPY · AUDUSD · USDCAD · EURGBP
  Stocks      — AAPL · TSLA · NVDA · AMZN · MSFT

Integration:
  tick(price_map) → Dict[str, float]  (symbol → boost_factor 0–1)
  Boost factors feed directly into orca's _intel_boosts pipeline.

Author: Aureon Trading System  |  March 2026
"""

import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ── SYMBOL ALIASES ─────────────────────────────────────────────────────────────
# Maps every exchange-specific symbol to a canonical harp string name.
# Canonical names are used throughout the resonance map.
HARP_ALIASES: Dict[str, str] = {
    # Crypto — Kraken, Alpaca, Binance variants
    "XBTUSD":     "BTC",  "BTCUSD":     "BTC",  "BTC/USD":    "BTC",
    "ETHUSD":     "ETH",  "XETHUSD":    "ETH",  "ETH/USD":    "ETH",
    "SOLUSD":     "SOL",  "SOL/USD":    "SOL",
    "XRPUSD":     "XRP",  "XXRPZUSD":   "XRP",  "XRP/USD":    "XRP",
    "ADAUSD":     "ADA",  "ADA/USD":    "ADA",
    "DOTUSD":     "DOT",  "DOT/USD":    "DOT",
    "LINKUSD":    "LINK", "LINK/USD":   "LINK",
    "LTCUSD":     "LTC",  "XLTCZUSD":   "LTC",  "LTC/USD":    "LTC",
    "UNIUSD":     "UNI",  "UNI/USD":    "UNI",
    "AVAXUSD":    "AVAX", "AVAX/USD":   "AVAX",
    "MATICUSD":   "MATIC","MATIC/USD":  "MATIC",
    # Indices — Capital.com names
    "UK100":      "UK100",
    "US500":      "US500",
    "US30":       "US30",
    "DE40":       "DE40",
    "JP225":      "JP225",
    # Commodities — Capital.com names
    "GOLD":       "GOLD",
    "SILVER":     "SILVER",
    "OIL_CRUDE":  "OIL",   "OIL":       "OIL",
    "NATURALGAS": "NATGAS","NATGAS":    "NATGAS",
    # Forex — standard pairs
    "EURUSD":     "EURUSD",
    "GBPUSD":     "GBPUSD",
    "USDJPY":     "USDJPY",
    "AUDUSD":     "AUDUSD",
    "USDCAD":     "USDCAD",
    "EURGBP":     "EURGBP",
    # Stocks — ticker symbols
    "AAPL":       "AAPL",
    "TSLA":       "TSLA",
    "NVDA":       "NVDA",
    "AMZN":       "AMZN",
    "MSFT":       "MSFT",
}

# Reverse alias map: canonical → list of all known exchange symbols
# Built at module load time
_CANONICAL_TO_ALIASES: Dict[str, List[str]] = {}
for _alias, _canonical in HARP_ALIASES.items():
    _CANONICAL_TO_ALIASES.setdefault(_canonical, []).append(_alias)

# Asset class for each canonical string
HARP_CLASSES: Dict[str, str] = {
    "BTC": "crypto",  "ETH": "crypto",  "SOL": "crypto",  "XRP": "crypto",
    "ADA": "crypto",  "DOT": "crypto",  "LINK": "crypto", "LTC": "crypto",
    "UNI": "crypto",  "AVAX": "crypto", "MATIC": "crypto",
    "UK100": "index", "US500": "index", "US30": "index",
    "DE40": "index",  "JP225": "index",
    "GOLD": "commodity", "SILVER": "commodity",
    "OIL": "commodity",  "NATGAS": "commodity",
    "EURUSD": "forex", "GBPUSD": "forex", "USDJPY": "forex",
    "AUDUSD": "forex", "USDCAD": "forex", "EURGBP": "forex",
    "AAPL": "stock", "TSLA": "stock", "NVDA": "stock",
    "AMZN": "stock", "MSFT": "stock",
}

# ── RESONANCE MAP ──────────────────────────────────────────────────────────────
# When a string (key) is plucked, the correlated strings (values) resonate.
# Format: source → [(target, correlation_coefficient, description)]
#   correlation_coefficient:
#     +1.0 = perfectly correlated  (target moves in SAME direction)
#     -1.0 = perfectly inverse     (target moves in OPPOSITE direction)
#     magnitude determines ripple strength; signs determine direction
#   Only pairs with |correlation| >= 0.35 are listed (below that = noise).

RESONANCE_MAP: Dict[str, List[Tuple[str, float, str]]] = {
    # ── CRYPTO ────────────────────────────────────────────────────────────────
    "BTC": [
        ("ETH",    +0.88, "BTC leads ETH (institutional flow)"),
        ("SOL",    +0.80, "BTC leads layer-1 alts"),
        ("XRP",    +0.72, "BTC leads XRP"),
        ("ADA",    +0.70, "BTC leads ADA"),
        ("DOT",    +0.68, "BTC leads DOT"),
        ("LINK",   +0.65, "BTC leads DeFi"),
        ("LTC",    +0.74, "BTC leads LTC (digital silver)"),
        ("AVAX",   +0.72, "BTC leads AVAX"),
        ("MATIC",  +0.68, "BTC leads layer-2"),
        ("UNI",    +0.62, "BTC leads DEX tokens"),
        ("GOLD",   -0.35, "BTC/Gold risk-on tension"),
        ("US500",  +0.42, "crypto-equity sentiment link"),
        ("TSLA",   +0.45, "Musk-BTC sentiment"),
        ("NVDA",   +0.35, "AI/crypto sentiment"),
    ],
    "ETH": [
        ("BTC",    +0.88, "ETH-BTC pair"),
        ("SOL",    +0.82, "ETH leads smart contract alts"),
        ("ADA",    +0.78, "ETH leads smart contract alts"),
        ("DOT",    +0.72, "ETH leads interop alts"),
        ("LINK",   +0.75, "ETH ecosystem token"),
        ("UNI",    +0.78, "Uniswap is ETH-native"),
        ("MATIC",  +0.80, "ETH layer-2 link"),
        ("AVAX",   +0.75, "ETH competitor correlation"),
    ],
    "SOL":  [("BTC", +0.80, "SOL follows BTC"), ("ETH", +0.82, "SOL-ETH alt"), ("AVAX", +0.78, "layer-1 peers")],
    "XRP":  [("BTC", +0.72, "XRP follows BTC"), ("ETH", +0.68, "XRP-ETH"), ("LTC", +0.65, "payments alts")],
    "LTC":  [("BTC", +0.74, "LTC follows BTC"), ("XRP", +0.65, "payments alts")],
    "AVAX": [("ETH", +0.75, "AVAX-ETH peers"), ("SOL", +0.78, "layer-1 peers"), ("BTC", +0.72, "risk-on crypto")],
    "MATIC":[("ETH", +0.80, "Polygon is ETH layer-2"), ("BTC", +0.68, "risk-on crypto")],
    "UNI":  [("ETH", +0.78, "Uniswap is ETH-native"), ("BTC", +0.62, "DeFi-risk-on")],
    "LINK": [("ETH", +0.75, "Chainlink-ETH ecosystem"), ("BTC", +0.65, "DeFi-risk-on")],
    "ADA":  [("ETH", +0.78, "smart contract alt"), ("BTC", +0.70, "risk-on crypto"), ("SOL", +0.72, "layer-1 peers")],
    "DOT":  [("ETH", +0.72, "interop alt"), ("BTC", +0.68, "risk-on crypto")],

    # ── INDICES ───────────────────────────────────────────────────────────────
    "US500": [
        ("US30",   +0.96, "S&P500 and Dow Jones — near-perfect pair"),
        ("UK100",  +0.72, "US leads Europe (New York hours)"),
        ("DE40",   +0.68, "US leads Germany"),
        ("JP225",  +0.60, "US leads Asian equity open"),
        ("USDJPY", +0.55, "risk-on: equities up → JPY weakens"),
        ("AUDUSD", +0.50, "risk-on: equities up → AUD strengthens"),
        ("GOLD",   -0.55, "risk-off flight to safe haven"),
        ("BTC",    +0.42, "equity risk sentiment bleeds into crypto"),
        ("NVDA",   +0.80, "NVDA is S&P500 heavyweight"),
        ("AAPL",   +0.75, "AAPL is S&P500 heavyweight"),
        ("MSFT",   +0.78, "MSFT is S&P500 heavyweight"),
    ],
    "US30": [
        ("US500",  +0.96, "Dow-S&P near-perfect pair"),
        ("UK100",  +0.70, "Dow leads FTSE"),
        ("AAPL",   +0.75, "Dow component proxy"),
        ("MSFT",   +0.76, "Dow component proxy"),
    ],
    "UK100": [
        ("US500",  +0.72, "FTSE follows Wall Street"),
        ("DE40",   +0.82, "European market sync"),
        ("GBPUSD", -0.45, "FTSE-GBP inverse (cheap GBP boosts exporters)"),
        ("EURGBP", +0.38, "EUR/GBP cross effect"),
        ("GOLD",   -0.40, "risk-off gold vs equities"),
        ("NATGAS", -0.28, "energy cost impact on UK firms"),
    ],
    "DE40": [
        ("UK100",  +0.82, "European session sync"),
        ("US500",  +0.68, "EU follows US"),
        ("EURUSD", +0.40, "DAX-EUR relationship"),
        ("JP225",  +0.55, "global equity chain"),
    ],
    "JP225": [
        ("US500",  +0.60, "Asian session follows US"),
        ("USDJPY", -0.70, "Nikkei UP → JPY weakens (exports competitive)"),
        ("DE40",   +0.55, "global equity chain"),
    ],

    # ── COMMODITIES ───────────────────────────────────────────────────────────
    "GOLD": [
        ("SILVER",  +0.82, "precious metals pair — silver amplifies gold"),
        ("EURUSD",  +0.48, "gold priced in USD; EUR strengthens when USD falls"),
        ("AUDUSD",  +0.55, "Australia is world's 2nd gold producer"),
        ("USDJPY",  -0.50, "gold/JPY safe haven pair"),
        ("US500",   -0.55, "safe haven flight when equities fall"),
        ("OIL",     +0.38, "commodity complex correlation"),
        ("BTC",     -0.35, "digital vs physical safe haven tension"),
    ],
    "SILVER": [
        ("GOLD",    +0.82, "silver amplifies gold moves"),
        ("EURUSD",  +0.42, "metal/USD relationship"),
        ("OIL",     +0.35, "commodity complex"),
    ],
    "OIL": [
        ("USDCAD",  -0.65, "Canada is oil exporter: oil UP → CAD strengthens → USDCAD falls"),
        ("GOLD",    +0.38, "commodity complex"),
        ("NATGAS",  +0.55, "energy complex"),
        ("US500",   -0.35, "oil spike = cost-push pressure on equities"),
        ("AUDUSD",  +0.38, "AUD is commodity currency"),
    ],
    "NATGAS": [
        ("OIL",     +0.55, "energy complex — oil leads gas"),
        ("UK100",   -0.28, "high energy costs hit UK equities"),
    ],

    # ── FOREX ─────────────────────────────────────────────────────────────────
    "EURUSD": [
        ("GBPUSD",  +0.78, "EUR and GBP both vs USD — tight correlation"),
        ("AUDUSD",  +0.65, "risk FX group"),
        ("USDCAD",  -0.70, "USD-bloc: EUR up = USD down = CAD up"),
        ("GOLD",    +0.48, "EUR/Gold both anti-USD"),
        ("DE40",    +0.40, "Euro strength boosts German exporters... inversely"),
        ("EURGBP",  +0.62, "EUR numerator"),
    ],
    "GBPUSD": [
        ("EURUSD",  +0.78, "GBP-EUR correlation (closely tied post-Brexit)"),
        ("AUDUSD",  +0.62, "risk FX group"),
        ("UK100",   -0.45, "GBP up = FTSE exporters hurt"),
        ("EURGBP",  -0.60, "GBP denominator: GBP up → EURGBP falls"),
    ],
    "USDJPY": [
        ("GOLD",    -0.50, "JPY and Gold are safe havens: risk-off → both up"),
        ("US500",   +0.55, "risk-on: equities up → JPY weakens → USDJPY rises"),
        ("JP225",   -0.70, "JPY weak → Nikkei exports competitive → JP225 up"),
        ("AUDUSD",  +0.55, "risk FX pair — both respond to risk appetite"),
    ],
    "AUDUSD": [
        ("EURUSD",  +0.65, "risk FX group"),
        ("GBPUSD",  +0.62, "risk FX group"),
        ("GOLD",    +0.55, "AUD-Gold link — Australia is major gold miner"),
        ("OIL",     +0.38, "commodity currency"),
        ("US500",   +0.50, "risk-on: equities up → AUD up"),
        ("BTC",     +0.38, "risk asset connection"),
    ],
    "USDCAD": [
        ("OIL",     -0.65, "petro-currency: oil up → CAD up → USDCAD down"),
        ("EURUSD",  -0.70, "USD bloc: EURUSD up → USDCAD down"),
        ("US500",   +0.35, "risk-on: equities up → USD demand rises"),
    ],
    "EURGBP": [
        ("EURUSD",  +0.62, "EUR numerator cross"),
        ("GBPUSD",  -0.60, "GBP denominator cross"),
        ("UK100",   +0.38, "cross-rate effect on FTSE"),
    ],

    # ── STOCKS (CFDs) ─────────────────────────────────────────────────────────
    "NVDA": [
        ("AAPL",    +0.72, "big tech sector correlation"),
        ("MSFT",    +0.75, "Azure/AI infrastructure pair"),
        ("AMZN",    +0.70, "mega cap tech pair"),
        ("US500",   +0.80, "NVDA is S&P500 major heavyweight"),
        ("BTC",     +0.38, "AI/GPU demand bleeds into crypto sentiment"),
        ("TSLA",    +0.65, "growth tech peers"),
    ],
    "AAPL": [
        ("MSFT",    +0.82, "big tech pair — move together on macro"),
        ("NVDA",    +0.72, "tech sector"),
        ("AMZN",    +0.75, "mega cap tech"),
        ("US500",   +0.75, "AAPL is largest S&P component"),
    ],
    "MSFT": [
        ("AAPL",    +0.82, "big tech pair"),
        ("NVDA",    +0.75, "Azure/AI infrastructure"),
        ("AMZN",    +0.78, "mega cap cloud trio"),
        ("US500",   +0.78, "MSFT is S&P500 heavyweight"),
    ],
    "TSLA": [
        ("NVDA",    +0.65, "growth/momentum tech peers"),
        ("US500",   +0.65, "equity risk sentiment"),
        ("BTC",     +0.45, "Elon/Musk sentiment link"),
        ("AMZN",    +0.60, "growth stock peers"),
    ],
    "AMZN": [
        ("MSFT",    +0.78, "mega cap cloud pair"),
        ("AAPL",    +0.75, "mega cap tech"),
        ("NVDA",    +0.70, "AI infrastructure ecosystem"),
        ("US500",   +0.72, "S&P500 heavyweight"),
    ],
}

# ── TUNING CONSTANTS ───────────────────────────────────────────────────────────
PLUCK_THRESHOLD     = 2.5    # Pluck fires when volatility > 2.5x rolling baseline
HISTORY_DEPTH       = 24     # Price history window (N data points)
MIN_HISTORY         = 6      # Minimum points before pluck detection activates
RIPPLE_TTL_SECS     = 120.0  # Ripple signals expire after 2 minutes
MIN_CORRELATION     = 0.40   # Only generate ripples for correlations above this
MIN_RIPPLE_CONF     = 0.30   # Minimum confidence to include in intel_boosts
PLUCK_COOLDOWN_SECS = 60.0   # Min gap between plucks on the same string
MAX_RIPPLES         = 50     # Cap total active ripple signals in memory


# ── DATA STRUCTURES ────────────────────────────────────────────────────────────
@dataclass
class HarpString:
    """One instrument being monitored for volatility."""
    canonical:   str
    asset_class: str
    prices:      Deque[float]  = field(default_factory=lambda: deque(maxlen=HISTORY_DEPTH))
    changes:     Deque[float]  = field(default_factory=lambda: deque(maxlen=HISTORY_DEPTH - 1))
    last_pluck:  float         = 0.0   # timestamp of last pluck
    pluck_mag:   float         = 0.0   # magnitude of last pluck (0 = quiet)
    pluck_dir:   float         = 0.0   # direction: +1 = up pluck, -1 = down pluck
    current_price: float       = 0.0

    def update(self, price: float) -> bool:
        """
        Feed a new price tick. Returns True if a NEW pluck is detected.
        """
        if price <= 0:
            return False
        prev = self.prices[-1] if self.prices else 0.0
        self.prices.append(price)
        self.current_price = price

        if prev <= 0:
            return False

        # Percent change from previous tick
        pct = (price - prev) / prev * 100
        self.changes.append(pct)

        if len(self.changes) < MIN_HISTORY:
            return False

        # Rolling baseline volatility (mean absolute change, excluding latest)
        history = list(self.changes)[:-1]
        baseline = sum(abs(c) for c in history) / max(len(history), 1)

        abs_pct = abs(pct)
        if baseline < 0.001:
            return False   # Instrument not moving at all — skip

        magnitude = abs_pct / baseline

        # Check pluck cooldown
        now = time.time()
        if magnitude >= PLUCK_THRESHOLD and (now - self.last_pluck) >= PLUCK_COOLDOWN_SECS:
            self.pluck_mag  = magnitude
            self.pluck_dir  = 1.0 if pct > 0 else -1.0
            self.last_pluck = now
            return True

        # Decay magnitude if no pluck
        if magnitude < PLUCK_THRESHOLD:
            self.pluck_mag = max(0.0, self.pluck_mag - 0.1)

        return False

    @property
    def is_resonating(self) -> bool:
        """True if this string was recently plucked (within ripple TTL)."""
        return (time.time() - self.last_pluck) < RIPPLE_TTL_SECS and self.pluck_mag > 0

    @property
    def ripple_age_factor(self) -> float:
        """Decay factor based on age of the pluck (1.0 = fresh, 0.0 = expired)."""
        age = time.time() - self.last_pluck
        if age >= RIPPLE_TTL_SECS:
            return 0.0
        return 1.0 - (age / RIPPLE_TTL_SECS)


@dataclass
class RippleSignal:
    """
    A predicted cross-market trade opportunity spawned by a pluck.
    """
    source:       str     # canonical name of plucked string
    source_class: str
    target:       str     # canonical name of resonating string
    target_class: str
    direction:    str     # "BUY" or "SELL" (on the TARGET)
    correlation:  float   # raw correlation coefficient
    confidence:   float   # 0.0 – 1.0
    pluck_mag:    float   # magnitude of the source pluck
    description:  str
    generated_at: float   = field(default_factory=time.time)

    @property
    def age_secs(self) -> float:
        return time.time() - self.generated_at

    @property
    def is_fresh(self) -> bool:
        return self.age_secs < RIPPLE_TTL_SECS

    @property
    def decayed_confidence(self) -> float:
        """Confidence decayed by ripple age (halved at TTL)."""
        decay = 1.0 - 0.5 * (self.age_secs / RIPPLE_TTL_SECS)
        return max(0.0, self.confidence * decay)

    def one_line(self) -> str:
        age_s = int(self.age_secs)
        return (
            f"  RIPPLE  {self.source:8} → {self.target:12}  {self.direction:4} "
            f"corr:{self.correlation:+.2f}  conf:{self.decayed_confidence:.2f}  "
            f"pluck:{self.pluck_mag:.1f}x  age:{age_s}s  [{self.description}]"
        )


# ── MARKET HARP ────────────────────────────────────────────────────────────────
class MarketHarp:
    """
    Cross-Market Resonance Detector.

    Feed price ticks from ANY exchange via update_prices() and the harp
    detects which strings are plucked, then propagates ripple signals through
    the correlation graph.

    Integration with orca:
      boosts = harp.tick(batch_prices)
      # boosts: {exchange_symbol: confidence_float}
      # Feed directly into _intel_boosts pipeline.
    """

    def __init__(self) -> None:
        # Build string registry
        self.strings: Dict[str, HarpString] = {
            canonical: HarpString(canonical=canonical, asset_class=cls)
            for canonical, cls in HARP_CLASSES.items()
        }
        # Active ripple signals
        self.ripples: List[RippleSignal] = []
        # Per-cycle stats
        self._plucks_this_cycle:  int = 0
        self._ripples_this_cycle: int = 0

        logger.info(f"MarketHarp: {len(self.strings)} strings tuned across "
                    f"{len(set(HARP_CLASSES.values()))} asset classes")

    # ── PRICE INGESTION ────────────────────────────────────────────────────────
    def _canonicalize(self, symbol: str) -> Optional[str]:
        """Map any exchange symbol to its canonical harp string name."""
        s = symbol.upper().strip()
        if s in HARP_ALIASES:
            return HARP_ALIASES[s]
        # Try without slashes/dashes
        s2 = s.replace("/", "").replace("-", "")
        if s2 in HARP_ALIASES:
            return HARP_ALIASES[s2]
        # Direct canonical hit (e.g. already "BTC")
        if s in self.strings:
            return s
        return None

    def update_prices(self, price_map: Dict[str, float]) -> List[str]:
        """
        Feed a price dict (any exchange format) into the harp.
        Returns list of canonical string names that were freshly plucked.
        """
        freshly_plucked: List[str] = []
        for symbol, price in price_map.items():
            canonical = self._canonicalize(str(symbol))
            if not canonical:
                continue
            hstring = self.strings.get(canonical)
            if not hstring:
                continue
            try:
                if hstring.update(float(price)):
                    freshly_plucked.append(canonical)
            except (ValueError, TypeError):
                continue
        return freshly_plucked

    # ── RIPPLE PROPAGATION ─────────────────────────────────────────────────────
    def _generate_ripples_from(self, source_name: str) -> List[RippleSignal]:
        """
        Given a freshly plucked string, walk the resonance graph and
        create RippleSignal objects for every correlated target.
        """
        source = self.strings.get(source_name)
        if not source or source.pluck_mag <= 0:
            return []

        targets = RESONANCE_MAP.get(source_name, [])
        new_ripples: List[RippleSignal] = []

        for target_name, correlation, description in targets:
            if abs(correlation) < MIN_CORRELATION:
                continue
            target = self.strings.get(target_name)
            if not target:
                continue

            # Confidence = |correlation| × pluck_strength_factor
            pluck_strength_factor = min(1.0, source.pluck_mag / 4.0)
            confidence = abs(correlation) * pluck_strength_factor

            if confidence < MIN_RIPPLE_CONF:
                continue

            # Direction on the TARGET:
            #   source went UP   + positive corr  → target goes UP   → BUY
            #   source went UP   + negative corr  → target goes DOWN → SELL
            #   source went DOWN + positive corr  → target goes DOWN → SELL
            #   source went DOWN + negative corr  → target goes UP   → BUY
            net_direction = source.pluck_dir * (1.0 if correlation > 0 else -1.0)
            direction = "BUY" if net_direction > 0 else "SELL"

            # Avoid duplicating a fresh same-source/same-target ripple
            already = any(
                r.source == source_name and r.target == target_name and r.is_fresh
                for r in self.ripples
            )
            if already:
                continue

            new_ripples.append(RippleSignal(
                source=source_name,
                source_class=source.asset_class,
                target=target_name,
                target_class=target.asset_class,
                direction=direction,
                correlation=correlation,
                confidence=confidence,
                pluck_mag=source.pluck_mag,
                description=description,
            ))

        return new_ripples

    def _expire_stale_ripples(self) -> None:
        self.ripples = [r for r in self.ripples if r.is_fresh]
        # Hard cap
        if len(self.ripples) > MAX_RIPPLES:
            # Keep highest-confidence fresh ripples
            self.ripples.sort(key=lambda r: r.decayed_confidence, reverse=True)
            self.ripples = self.ripples[:MAX_RIPPLES]

    # ── INTEL BOOST EXPORT ─────────────────────────────────────────────────────
    def _build_intel_boosts(self) -> Dict[str, float]:
        """
        Aggregate all fresh ripple signals into a boost map keyed by
        EVERY known exchange symbol for each canonical target.

        Returns {symbol: confidence_factor} where confidence_factor is
        the decayed, aggregated confidence across all active ripples
        pointing at that target (for BUY signals only).

        The orca applies this as:
          _intel_boosts[sym] *= (1.0 + confidence_factor * WEIGHT)
        """
        # Accumulate per canonical target
        target_boosts: Dict[str, float] = {}
        for ripple in self.ripples:
            if not ripple.is_fresh:
                continue
            if ripple.direction != "BUY":
                continue  # Only boost; penalties handled separately
            conf = ripple.decayed_confidence
            if conf < MIN_RIPPLE_CONF:
                continue
            # Accumulate: each additional source adds diminishing return
            prev = target_boosts.get(ripple.target, 0.0)
            target_boosts[ripple.target] = prev + conf * (1.0 - prev * 0.5)

        # Expand canonicals to all exchange symbol aliases
        result: Dict[str, float] = {}
        for canonical, boost in target_boosts.items():
            boost = min(1.0, boost)  # Cap at 1.0
            for alias in _CANONICAL_TO_ALIASES.get(canonical, [canonical]):
                result[alias] = boost
            # Include canonical itself
            result[canonical] = boost

        return result

    # ── HEADLESS TICK ──────────────────────────────────────────────────────────
    def tick(self, price_map: Dict[str, float]) -> Dict[str, float]:
        """
        One complete harp cycle:
          1. Feed prices to all strings
          2. Detect freshly plucked strings
          3. Expire stale ripples
          4. Propagate new ripples from fresh plucks
          5. Return intel boost map for orca pipeline

        Args:
            price_map: {symbol: price} in any exchange format

        Returns:
            {symbol: confidence_factor} — feed into _intel_boosts
        """
        # Phase 1: ingest prices
        freshly_plucked = self.update_prices(price_map)
        self._plucks_this_cycle = len(freshly_plucked)

        # Phase 2: expire stale signals
        self._expire_stale_ripples()

        # Phase 3: generate ripples from fresh plucks
        new_ripples: List[RippleSignal] = []
        for source_name in freshly_plucked:
            new_ripples.extend(self._generate_ripples_from(source_name))
        self.ripples.extend(new_ripples)
        self._ripples_this_cycle = len(new_ripples)

        # Log pluck events
        for source_name in freshly_plucked:
            src = self.strings[source_name]
            direction_word = "SURGE" if src.pluck_dir > 0 else "DROP"
            print(
                f"  HARP PLUCK: {source_name:8} [{src.asset_class:9}] "
                f"{direction_word} {src.pluck_mag:.1f}x baseline → "
                f"{sum(1 for r in new_ripples if r.source == source_name)} ripples"
            )

        # Phase 4: build and return intel boosts
        return self._build_intel_boosts()

    # ── PROPERTIES ─────────────────────────────────────────────────────────────
    @property
    def active_pluck_count(self) -> int:
        """Number of strings currently resonating (plucked within TTL)."""
        return sum(1 for s in self.strings.values() if s.is_resonating)

    @property
    def active_ripple_count(self) -> int:
        """Number of fresh ripple signals."""
        return sum(1 for r in self.ripples if r.is_fresh)

    def plucked_strings(self) -> List[HarpString]:
        return [s for s in self.strings.values() if s.is_resonating]

    def fresh_ripples(self, direction: Optional[str] = None, min_conf: float = 0.3) -> List[RippleSignal]:
        return [
            r for r in self.ripples
            if r.is_fresh
            and r.decayed_confidence >= min_conf
            and (direction is None or r.direction == direction)
        ]

    # ── STATUS ─────────────────────────────────────────────────────────────────
    def status_lines(self) -> List[str]:
        plucked = self.plucked_strings()
        fresh   = self.fresh_ripples()
        buy_sig = [r for r in fresh if r.direction == "BUY"]

        lines: List[str] = [
            f"  MARKET HARP: {len(self.strings)} strings | "
            f"{len(plucked)} plucked | "
            f"{len(fresh)} active ripples ({len(buy_sig)} BUY)"
        ]

        # Show plucked strings
        for s in sorted(plucked, key=lambda x: -x.pluck_mag):
            dir_str = "▲" if s.pluck_dir > 0 else "▼"
            age_s = int(time.time() - s.last_pluck)
            lines.append(
                f"    PLUCKED  {s.canonical:8} [{s.asset_class:9}] "
                f"{dir_str} {s.pluck_mag:.1f}x  age:{age_s}s  "
                f"price:{s.current_price:.5g}"
            )

        # Show top ripples by decayed confidence
        top = sorted(fresh, key=lambda r: -r.decayed_confidence)[:8]
        for r in top:
            lines.append(r.one_line())

        return lines

    def cross_class_summary(self) -> List[str]:
        """
        Summary of cross-asset-class ripples only (the most strategically
        interesting — e.g., BTC pluck triggering a GOLD or EURUSD ripple).
        """
        fresh = self.fresh_ripples()
        cross = [r for r in fresh if r.source_class != r.target_class]
        if not cross:
            return ["  HARP CROSS-CLASS: no active cross-asset ripples"]
        lines = [f"  HARP CROSS-CLASS: {len(cross)} active"]
        for r in sorted(cross, key=lambda x: -x.decayed_confidence)[:5]:
            lines.append(r.one_line())
        return lines
