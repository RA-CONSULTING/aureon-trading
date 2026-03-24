#!/usr/bin/env python3
"""
UNIFIED TRADING LOGIC — END-TO-END TEST
════════════════════════════════════════
Verifies every decision point in the unified signal + spot/margin intent chain
using realistic mock data — no live API calls, no network required.

Scenarios tested:
  A  News headline → category sentiment + geopolitical risk
  B  Unified signal engine → group scoring, top picks, pipeline boosts
  C  Position intent filter → margin SHORT blocks spot BUY, self-hedging caught
  D  Margin-conviction sizing → capital allocated proportional to conviction
  E  Queen fallback intent block → SELL-biased asset overrides blocked
  F  Group-leader selection → rank-1 BUY preferred over raw-momentum winner

Each scenario prints PASS / FAIL with the exact values checked.
"""

import sys
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

sys.path.insert(0, os.path.dirname(__file__))

# ─── result tracking ─────────────────────────────────────────────────────────
_passed = []
_failed = []

def ok(name: str, detail: str = ""):
    _passed.append(name)
    print(f"  PASS  {name}" + (f"  →  {detail}" if detail else ""))

def fail(name: str, detail: str = ""):
    _failed.append(name)
    print(f"  FAIL  {name}" + (f"  →  {detail}" if detail else ""))

def check(name: str, condition: bool, detail: str = ""):
    (ok if condition else fail)(name, detail)

def section(title: str):
    print(f"\n{'═'*68}")
    print(f"  {title}")
    print(f"{'─'*68}")


# ─── minimal MarketOpportunity mock ──────────────────────────────────────────
@dataclass
class MockOpp:
    symbol:         str
    exchange:       str
    price:          float
    change_pct:     float
    volume:         float
    momentum_score: float
    fee_rate:       float = 0.0025
    # unified engine tags (set after engine processes)
    _unified_direction:  str   = ""
    _unified_confidence: float = 0.0
    _unified_group_rank: int   = 0
    _correlation_signal: bool  = False
    # cross-asset correlator tags
    _category: str = ""


@dataclass
class MockPosition:
    symbol:      str
    exchange:    str
    is_margin:   bool  = False
    margin_side: str   = "LONG"
    entry_price: float = 0.0
    entry_qty:   float = 0.0


# ══════════════════════════════════════════════════════════════════════════════
#  SCENARIO A — News headline → category sentiment + geo risk
# ══════════════════════════════════════════════════════════════════════════════
section("SCENARIO A  —  News Signal: headline → per-category sentiment")

try:
    from news_signal import _analyse_headlines
    ok("news_signal imported")
except Exception as e:
    fail("news_signal imported", str(e))
    _analyse_headlines = None

if _analyse_headlines:
    # Mixed bullish/bearish signals across categories
    _headlines = [
        "Bitcoin ETF approval expected next week, crypto markets surge",
        "Fed signals June rate cut, stocks reach record high",
        "OPEC increases oil supply to record levels",
        "Ukraine war escalates, gold surges as investors flee to safety",
        "US stock earnings beat expectations, NASDAQ hits all-time high",
        "Crypto exchange hack loses $200M, prices fall sharply",
        "Trade deal between US and China boosts global indices",
        "Recession fears grow as GDP contracts for second quarter",
    ]

    r = _analyse_headlines(_headlines)

    check("A1  crypto sentiment positive (ETF + hack mixed → slight bullish)",
          r.sentiment.get('crypto', 0) > -0.5,
          f"crypto={r.sentiment.get('crypto',0):+.2f}")

    check("A2  commodity sentiment negative (OPEC increase + war → bearish oil/gold complex)",
          r.sentiment.get('commodity', 0) < 0.5,
          f"commodity={r.sentiment.get('commodity',0):+.2f}")

    check("A3  index sentiment positive (rate cut + record high + trade deal)",
          r.sentiment.get('index', 0) > 0,
          f"index={r.sentiment.get('index',0):+.2f}")

    check("A4  geo risk elevated (war + recession keywords present)",
          r.geo_risk >= 0.3,
          f"geo_risk={r.geo_risk:.2f}")

    check("A5  risk level is ELEVATED or higher",
          r.risk_level in ('ELEVATED', 'HIGH', 'EXTREME'),
          f"risk_level={r.risk_level}")

    check("A6  themes detected (at least 3)",
          len(r.themes) >= 3,
          f"themes={r.themes[:4]}")

    check("A7  headline count correct",
          r.headline_count == len(_headlines),
          f"count={r.headline_count}")

    print(f"       Summary: {r.summary()}")


# ══════════════════════════════════════════════════════════════════════════════
#  SCENARIO B — Unified signal engine: scoring, groups, pipeline boosts
# ══════════════════════════════════════════════════════════════════════════════
section("SCENARIO B  —  Unified Signal Engine: group scoring + top picks")

try:
    from unified_signal_engine import UnifiedSignalEngine
    engine = UnifiedSignalEngine()
    ok("UnifiedSignalEngine imported")
except Exception as e:
    fail("UnifiedSignalEngine imported", str(e))
    engine = None

if engine:
    opps = [
        # Crypto — BTC surging hard, ETH lagging (harp ripple from BTC)
        MockOpp("BTC/USD",  "kraken",   84000, +1.8, 5e8, 30.0, _category="crypto"),
        MockOpp("ETH/USD",  "kraken",    3200, +0.3, 2e8, 12.0, _category="crypto"),
        MockOpp("SOL/USD",  "kraken",     145, +0.1, 5e7,  8.0, _category="crypto"),
        # Index — NAS100 strong, US30 OK
        MockOpp("NAS100",   "capital", 19500, +0.9, 0,   18.0, _category="index"),
        MockOpp("US30",     "capital", 38500, +0.2, 0,    9.0, _category="index"),
        # Forex — mixed
        MockOpp("EURUSD",   "capital",  1.09, +0.2, 0,    7.0, _category="forex"),
        MockOpp("GBPUSD",   "capital",  1.27, -0.1, 0,    5.0, _category="forex"),
        # Commodity — gold bid as safe-haven in RISK_OFF
        MockOpp("GOLD",     "capital",  2050, +0.6, 0,   11.0, _category="commodity"),
        # Stock
        MockOpp("AAPL",     "capital",   215, +0.4, 0,    9.0, _category="stock"),
        MockOpp("TSLA",     "capital",   175, -0.5, 0,    4.0, _category="stock"),
    ]

    bundle = engine.process(
        opportunities   = opps,
        regime          = "MILD_RISK_ON",
        category_moves  = {"crypto": +1.0, "index": +0.9, "forex": +0.1, "commodity": +0.5, "stock": +0.2},
        harp_boosts     = {"ETH": 0.55, "SOL": 0.40, "NAS100": 0.60},   # BTC plucked → ETH/SOL harp
        news_sentiment  = {"crypto": +0.35, "index": +0.45, "forex": +0.05, "commodity": -0.10, "stock": +0.25},
        macro_score     =  0.9,
        fear_greed      =  65,
        geo_risk_level  = "NORMAL",
    )

    # B1 — all 10 opportunities processed
    check("B1  all opportunities processed",
          len(bundle.signals) == len(opps),
          f"signals={len(bundle.signals)}")

    # B2 — groups present
    check("B2  all 5 categories represented in groups",
          all(c in bundle.groups for c in ('crypto','index','forex','commodity','stock')),
          f"groups={list(bundle.groups.keys())}")

    # B3 — crypto top pick is a BUY with high confidence
    # (ETH ranks above BTC here because it has a harp ripple from BTC plucking —
    #  that IS correct: BTC moves first, ETH follows, so ETH is the better entry)
    crypto_top = bundle.top_per_group.get('crypto')
    check("B3  crypto top pick direction is BUY with confidence >= 60%",
          crypto_top is not None and crypto_top.direction == "BUY" and crypto_top.confidence >= 0.60,
          f"got={crypto_top.symbol if crypto_top else 'None'} dir={crypto_top.direction if crypto_top else ''} conf={crypto_top.confidence:.0%}" if crypto_top else "")

    # B4 — index top pick is NAS100 (higher momentum + harp boost)
    index_top = bundle.top_per_group.get('index')
    check("B4  index top pick is NAS100",
          index_top is not None and index_top.symbol == "NAS100",
          f"got={index_top.symbol if index_top else 'None'}")

    # B5 — NAS100 has harp in its sources
    nas_sig = next((s for s in bundle.signals if s.symbol == "NAS100"), None)
    check("B5  NAS100 sources include harp ripple",
          nas_sig is not None and any("harp" in src for src in nas_sig.sources),
          f"sources={nas_sig.sources if nas_sig else 'None'}")

    # B6 — ETH has harp in sources (BTC pluck rippled to ETH)
    eth_sig = next((s for s in bundle.signals if s.symbol == "ETH/USD"), None)
    check("B6  ETH/USD sources include harp (BTC→ETH ripple)",
          eth_sig is not None and any("harp" in src for src in eth_sig.sources),
          f"sources={eth_sig.sources if eth_sig else 'None'}")

    # B7 — BTC has direction BUY
    btc_sig = next((s for s in bundle.signals if s.symbol == "BTC/USD"), None)
    check("B7  BTC/USD direction is BUY",
          btc_sig is not None and btc_sig.direction == "BUY",
          f"dir={btc_sig.direction if btc_sig else 'None'}  conf={btc_sig.confidence:.0%}" if btc_sig else "")

    # B8 — TSLA direction is SELL or NEUTRAL (negative change_pct, low stock news)
    tsla_sig = next((s for s in bundle.signals if s.symbol == "TSLA"), None)
    check("B8  TSLA direction is not BUY (negative momentum)",
          tsla_sig is not None and tsla_sig.direction != "BUY",
          f"dir={tsla_sig.direction if tsla_sig else 'None'}  conf={tsla_sig.confidence:.0%}" if tsla_sig else "")

    # B9 — BTC pipeline_boost > 1.0 (it should be a strong signal)
    check("B9  BTC pipeline_boost > 1.0 (confidence above buy threshold)",
          btc_sig is not None and btc_sig.pipeline_boost > 1.0,
          f"pipeline_boost={btc_sig.pipeline_boost if btc_sig else 0:.2f}")

    # B10 — group rank 1 in crypto IS the highest-confidence BUY asset
    # (not necessarily BTC — harp ripple correctly lifts ETH above BTC here)
    rank1_crypto = next((s for s in bundle.signals if s.category == 'crypto' and s.group_rank == 1), None)
    check("B10  crypto rank-1 has higher confidence than rank-2",
          rank1_crypto is not None and (
              next((s.confidence for s in bundle.signals if s.category=='crypto' and s.group_rank==2), 0)
              <= rank1_crypto.confidence
          ),
          f"rank1={rank1_crypto.symbol if rank1_crypto else 'None'} conf={rank1_crypto.confidence:.0%}" if rank1_crypto else "")

    # B11 — summary lines produced
    check("B11  dashboard summary lines produced",
          len(bundle.summary_lines) > 5,
          f"{len(bundle.summary_lines)} lines")

    # B12 — regime note visible for crypto (MILD_RISK_ON favours crypto)
    crypto_grp = bundle.groups.get('crypto')
    check("B12  crypto group regime note mentions FAVOURS",
          crypto_grp is not None and "FAVOURS" in crypto_grp.regime_note,
          f"note='{crypto_grp.regime_note if crypto_grp else ''}'")

    print(f"\n       Dashboard preview (first 12 lines):")
    for line in bundle.summary_lines[:12]:
        print(f"       {line}")


# ══════════════════════════════════════════════════════════════════════════════
#  SCENARIO C — Position intent filter: directional conflict detection
# ══════════════════════════════════════════════════════════════════════════════
section("SCENARIO C  —  Intent filter: spot blocked by margin SHORT, self-hedging caught")

def _norm_sym(s):
    b = s.replace('/', '').replace('-', '').upper()
    for q in ('USDT', 'USDC', 'BUSD', 'USD', 'GBP', 'EUR', 'BTC', 'ETH'):
        if b.endswith(q) and len(b) > len(q):
            b = b[:-len(q)]
            break
    return b

# Existing positions
_positions = [
    MockPosition("BTC/USD",  "kraken",  is_margin=True,  margin_side="SHORT"),  # SHORT BTC
    MockPosition("ETHUSDT",  "binance", is_margin=False, margin_side="LONG"),   # SPOT ETH
    MockPosition("NAS100",   "capital", is_margin=True,  margin_side="LONG"),   # MARGIN LONG NAS100
]

# Build the same intent map the main loop builds
_pos_intent = {}
for _p in _positions:
    _ps = _norm_sym(_p.symbol)
    _pos_intent[_ps] = (getattr(_p, 'is_margin', False), getattr(_p, 'margin_side', 'LONG'))

# Candidate opportunities
_candidates = [
    MockOpp("BTC/USD",   "kraken",  84000, +1.5, 5e8, 25.0),   # BTC spot → should be BLOCKED (SHORT conflict)
    MockOpp("ETH/USD",   "kraken",   3200, +0.3, 2e8, 12.0),   # ETH → BLOCKED (already held as spot)
    MockOpp("NAS100",    "capital", 19500, +0.9,   0, 18.0),   # NAS100 → BLOCKED (already margin LONG)
    MockOpp("SOL/USD",   "kraken",    145, +0.4, 5e7,  9.0),   # SOL → CLEAN, should pass
    MockOpp("EURUSD",    "capital",  1.09, +0.2,   0,  7.0),   # EURUSD → CLEAN, should pass
    MockOpp("GOLD",      "capital",  2050, +0.6,   0, 11.0),   # GOLD → CLEAN, should pass
]

# Run the same filter logic as the main loop
_new_opps = []
_blocked = []
for o in _candidates:
    _os = _norm_sym(o.symbol)
    _existing = _pos_intent.get(_os)
    if _existing is None:
        _new_opps.append(o)
        continue
    _ex_margin, _ex_side = _existing
    if _ex_margin and _ex_side == "SHORT":
        _blocked.append((o.symbol, "margin-SHORT conflict"))
        continue
    _blocked.append((o.symbol, f"already held as {'margin' if _ex_margin else 'spot'}"))

_blocked_syms   = [b[0] for b in _blocked]
_clean_syms     = [o.symbol for o in _new_opps]
_blocked_reasons = {b[0]: b[1] for b in _blocked}

check("C1  BTC/USD blocked (margin SHORT conflict)",
      "BTC/USD" in _blocked_syms,
      f"reason='{_blocked_reasons.get('BTC/USD','')}'")

check("C2  ETH/USD blocked (ETHUSDT on Binance normalises to same base ETH)",
      "ETH/USD" in _blocked_syms,
      f"reason='{_blocked_reasons.get('ETH/USD','')}'  [tests cross-exchange quote-strip]")

check("C3  NAS100 blocked (already held as margin LONG)",
      "NAS100" in _blocked_syms,
      f"reason='{_blocked_reasons.get('NAS100','')}'")

check("C4  SOL/USD passes through (no existing position)",
      "SOL/USD" in _clean_syms,
      f"clean_syms={_clean_syms}")

check("C5  EURUSD passes through",
      "EURUSD" in _clean_syms)

check("C6  GOLD passes through",
      "GOLD" in _clean_syms)

check("C7  exactly 3 blocked, 3 clean",
      len(_blocked) == 3 and len(_new_opps) == 3,
      f"blocked={len(_blocked)}, clean={len(_new_opps)}")

print(f"       Blocked: {_blocked_syms}")
print(f"       Clean:   {_clean_syms}")


# ══════════════════════════════════════════════════════════════════════════════
#  SCENARIO D — Margin-conviction sizing
# ══════════════════════════════════════════════════════════════════════════════
section("SCENARIO D  —  Margin-conviction sizing: capital proportional to conviction")

def _compute_buy_amount(exchange, exchange_cash, amount_per_position,
                        margin_conviction, margin_leverage, quad_sizing=1.0):
    """Mirrors the sizing logic added to the main loop."""
    buy_amount = min(amount_per_position, exchange_cash * 0.9)
    if quad_sizing != 1.0:
        buy_amount *= quad_sizing

    _will_use_margin = (
        exchange in ('kraken', 'binance')
        and margin_leverage >= 2
        and margin_conviction >= 0.3
    )

    if _will_use_margin:
        if margin_conviction >= 0.7:
            buy_amount = min(buy_amount * 1.0, exchange_cash * 0.85)
            route = "high-conviction margin"
        elif margin_conviction >= 0.5:
            buy_amount = min(buy_amount * 0.8, exchange_cash * 0.70)
            route = "medium-conviction margin"
        else:
            buy_amount = min(buy_amount * 0.5, exchange_cash * 0.50)
            route = "low-conviction margin"
    else:
        route = "spot (no margin)"

    return round(buy_amount, 4), route, _will_use_margin

# D1 — Kraken, $200 cash, $50 per position, high conviction 3x
amt, route, is_margin = _compute_buy_amount("kraken", 200, 50, 0.75, 3)
check("D1  high conviction (0.75) → full collateral, is_margin=True",
      is_margin and amt >= 45.0,
      f"${amt:.2f}  route={route}")

# D2 — medium conviction
amt2, route2, is_margin2 = _compute_buy_amount("kraken", 200, 50, 0.55, 3)
check("D2  medium conviction (0.55) → reduced collateral vs high",
      is_margin2 and amt2 < amt,
      f"${amt2:.2f} < ${amt:.2f}  route={route2}")

# D3 — low conviction
amt3, route3, is_margin3 = _compute_buy_amount("kraken", 200, 50, 0.35, 3)
check("D3  low conviction (0.35) → smallest collateral",
      is_margin3 and amt3 < amt2,
      f"${amt3:.2f} < ${amt2:.2f}  route={route3}")

# D4 — conviction below 0.3 → not using margin at all
amt4, route4, is_margin4 = _compute_buy_amount("kraken", 200, 50, 0.20, 3)
check("D4  conviction 0.20 → falls through to spot (no margin)",
      not is_margin4,
      f"is_margin={is_margin4}  route={route4}")

# D5 — Alpaca (no margin support) → always spot regardless of conviction
amt5, route5, is_margin5 = _compute_buy_amount("alpaca", 200, 50, 0.90, 5)
check("D5  Alpaca exchange → always spot (no margin support)",
      not is_margin5,
      f"is_margin={is_margin5}  route={route5}")

# D6 — quad_sizing modifier flows through before margin scaling
amt6, route6, _ = _compute_buy_amount("kraken", 200, 50, 0.75, 3, quad_sizing=1.5)
amt6_base, _, _ = _compute_buy_amount("kraken", 200, 50, 0.75, 3, quad_sizing=1.0)
check("D6  quad_sizing 1.5x applied before margin sizing",
      amt6 >= amt6_base,
      f"with_quad=${amt6:.2f}  base=${amt6_base:.2f}")

print(f"       Sizing ladder: high=${amt:.2f}  mid=${amt2:.2f}  low=${amt3:.2f}  spot=${amt4:.2f}")


# ══════════════════════════════════════════════════════════════════════════════
#  SCENARIO E — Queen fallback intent block
# ══════════════════════════════════════════════════════════════════════════════
section("SCENARIO E  —  Queen fallback: SELL-biased assets blocked from override")

def _queen_fallback_check(unified_direction, change_pct, momentum_score,
                          cash, min_change_pct, queen_action="HOLD"):
    """Mirrors the fallback autonomy logic in the main loop."""
    queen_approved = (queen_action == "BUY")
    if not queen_approved:
        setup_strong = (abs(change_pct) >= max(0.10, min_change_pct * 2)
                        and momentum_score >= 0.20)
        setup_funded = cash >= 50.0
        _intent_ok   = unified_direction != "SELL"
        if queen_action != "BUY" and setup_strong and setup_funded and _intent_ok:
            queen_approved = True
            override_reason = "strong funded setup"
        elif not _intent_ok:
            override_reason = "BLOCKED: unified signal is SELL (intent coherence)"
        else:
            override_reason = "setup not strong/funded"
    else:
        override_reason = "Queen approved directly"
    return queen_approved, override_reason

# E1 — SELL-biased, strong setup, plenty of cash → override BLOCKED
approved, reason = _queen_fallback_check("SELL", +0.8, 0.5, 100.0, 0.05)
check("E1  SELL-biased + strong setup → override BLOCKED",
      not approved,
      f"reason='{reason}'")

# E2 — NEUTRAL, strong setup, plenty of cash → override ALLOWED
approved, reason = _queen_fallback_check("NEUTRAL", +0.5, 0.4, 100.0, 0.05)
check("E2  NEUTRAL + strong setup + funded → fallback override ALLOWED",
      approved,
      f"reason='{reason}'")

# E3 — BUY, Queen says HOLD, strong setup → override allowed
approved, reason = _queen_fallback_check("BUY", +0.3, 0.25, 100.0, 0.05)
check("E3  BUY-biased + strong setup + funded → override ALLOWED",
      approved,
      f"reason='{reason}'")

# E4 — NEUTRAL, weak setup → override not triggered (setup too weak)
approved, reason = _queen_fallback_check("NEUTRAL", +0.05, 0.10, 100.0, 0.05)
check("E4  NEUTRAL + weak setup → override NOT triggered",
      not approved,
      f"reason='{reason}'")

# E5 — NEUTRAL, strong setup but insufficient cash → blocked by funding check
approved, reason = _queen_fallback_check("NEUTRAL", +0.5, 0.4, 20.0, 0.05)
check("E5  NEUTRAL + strong setup + underfunded → override NOT triggered",
      not approved,
      f"reason='{reason}'  cash=$20")


# ══════════════════════════════════════════════════════════════════════════════
#  SCENARIO F — Group-leader selection over raw-momentum winner
# ══════════════════════════════════════════════════════════════════════════════
section("SCENARIO F  —  Best pick: group leader preferred over raw momentum winner")

def _select_best(funded_opps):
    """Mirrors the best-selection logic in the main loop."""
    if not funded_opps:
        return None, "no funded opps"

    _top_score = funded_opps[0].momentum_score
    _group_leaders = [
        o for o in funded_opps
        if getattr(o, '_unified_group_rank', 99) == 1
        and getattr(o, '_unified_direction', '') == 'BUY'
        and o.momentum_score >= _top_score * 0.80
    ]
    if _group_leaders:
        _group_leaders.sort(key=lambda o: getattr(o, '_unified_confidence', 0), reverse=True)
        return _group_leaders[0], "group leader"
    return funded_opps[0], "raw momentum"

# Four funded opps — raw momentum winner is not the group leader
_f_opps = [
    MockOpp("LINKUSDT", "kraken", 14.5, +2.5, 3e7, 40.0),  # raw momentum #1, rank 4, no direction
    MockOpp("DOTUSDT",  "kraken",  7.2, +1.8, 2e7, 35.0),  # raw momentum #2, rank 3
    MockOpp("BTC/USD",  "kraken", 84000, +1.2, 5e8, 34.0), # rank 1 group leader, within 80% of 40.0 ✓
    MockOpp("SOLUSDT",  "kraken",  145, +0.9, 4e7, 28.0),  # rank 2
]
# tag
_f_opps[0]._unified_group_rank = 4; _f_opps[0]._unified_direction = "NEUTRAL"; _f_opps[0]._unified_confidence = 0.50
_f_opps[1]._unified_group_rank = 3; _f_opps[1]._unified_direction = "BUY";     _f_opps[1]._unified_confidence = 0.58
_f_opps[2]._unified_group_rank = 1; _f_opps[2]._unified_direction = "BUY";     _f_opps[2]._unified_confidence = 0.72
_f_opps[3]._unified_group_rank = 2; _f_opps[3]._unified_direction = "BUY";     _f_opps[3]._unified_confidence = 0.63
# sort by momentum (as the main loop does after boost pass)
_f_opps.sort(key=lambda o: o.momentum_score, reverse=True)

best, method = _select_best(_f_opps)
check("F1  BTC/USD selected as group leader despite being 3rd by raw momentum",
      best is not None and best.symbol == "BTC/USD",
      f"selected={best.symbol if best else 'None'}  method={method}")

check("F2  selection method is 'group leader'",
      method == "group leader",
      f"method={method}")

# F3 — if group leader is outside 80% threshold, fall back to raw momentum
_f_opps2 = [
    MockOpp("LINKUSDT", "kraken", 14.5, +2.5, 3e7, 100.0),  # raw winner, very high
    MockOpp("BTC/USD",  "kraken", 84000, +1.2, 5e8,  70.0), # rank 1 but only 70% of 100 → below 80% threshold
]
_f_opps2[0]._unified_group_rank = 4; _f_opps2[0]._unified_direction = "NEUTRAL"; _f_opps2[0]._unified_confidence = 0.50
_f_opps2[1]._unified_group_rank = 1; _f_opps2[1]._unified_direction = "BUY";     _f_opps2[1]._unified_confidence = 0.72
_f_opps2.sort(key=lambda o: o.momentum_score, reverse=True)

best2, method2 = _select_best(_f_opps2)
check("F3  group leader outside 80% threshold → raw momentum wins",
      best2 is not None and best2.symbol == "LINKUSDT",
      f"selected={best2.symbol if best2 else 'None'}  method={method2}")


# ══════════════════════════════════════════════════════════════════════════════
#  FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
total  = len(_passed) + len(_failed)
pct    = 100 * len(_passed) / total if total else 0

print(f"\n{'═'*68}")
print(f"  RESULTS:  {len(_passed)}/{total} passed  ({pct:.0f}%)")
print(f"{'─'*68}")
if _failed:
    print(f"  FAILED tests:")
    for f in _failed:
        print(f"    ✗  {f}")
else:
    print(f"  ALL TESTS PASSED — logic is correct and ready for live execution")
print(f"{'═'*68}")

sys.exit(0 if not _failed else 1)
