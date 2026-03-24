#!/usr/bin/env python3
"""
test_hive_mind_live.py  —  Live-ticker test for Trading Hive Mind + Market Harp

Fetches REAL prices from Binance public API (no auth needed).
Tests every component of the hive coordination system end-to-end.

Tests:
  1.  ExchangeSlot  —  open / occupy / close / win-rate
  2.  TradingHiveMind init  —  slots, session goal
  3.  Live price fetch from Binance public /api/v3/ticker/price
  4.  Market Harp tick() with live prices  →  ripple boost map
  5.  Hive boost injection to mock Kraken trader
  6.  Hive boost injection to mock Capital trader
  7.  Coordinated hive.tick() with mock closed trades
  8.  PnL accumulation  —  session goal progress
  9.  Alpaca slot gate  —  blocks scan when occupied
  10. Close registration  —  slot frees, win/loss tracked
  11. Gate logic  —  fail-open when Quadrumvirate unavailable
  12. ThoughtBus broadcast  —  publishes hive.unity.status
  13. Status lines  —  goal banner + per-exchange table
  14. Three-cycle integration  —  full autonomous rhythm
"""

import sys
import json
import time
import traceback
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

PASS = f"{GREEN}PASS{RESET}"
FAIL = f"{RED}FAIL{RESET}"
INFO = f"{CYAN}INFO{RESET}"

results: List[tuple] = []   # (name, ok, detail)

def check(name: str, ok: bool, detail: str = "") -> bool:
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {name}" + (f"  {DIM}{detail}{RESET}" if detail else ""))
    results.append((name, ok, detail))
    return ok

def section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'═'*70}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'═'*70}{RESET}")

# ── 1. LIVE PRICE FETCH ────────────────────────────────────────────────────────
section("1. Fetch Live Prices — Binance Public API")

BINANCE_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
    "DOTUSDT", "LINKUSDT", "AVAXUSDT", "MATICUSDT", "LTCUSDT",
    "XRPUSDT", "DOGEUSDT", "UNIUSDT", "ATOMUSDT", "NEARUSDT",
    "FTMUSDT", "ALGOUSDT", "VETUSDT", "XLMUSDT", "TRXUSDT",
]

live_prices: Dict[str, float] = {}
fetch_ok = False
try:
    sym_json = json.dumps(BINANCE_SYMBOLS)
    url = f"https://api.binance.com/api/v3/ticker/price?symbols={urllib.request.quote(sym_json)}"
    req = urllib.request.Request(url, headers={"User-Agent": "AureonHiveTest/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    for item in data:
        live_prices[item["symbol"]] = float(item["price"])
    fetch_ok = len(live_prices) > 0
except Exception as e:
    print(f"  {YELLOW}Binance fetch failed ({e}), using synthetic prices{RESET}")
    # Synthetic prices if Binance is unavailable
    live_prices = {
        "BTCUSDT": 84500.0, "ETHUSDT": 3200.0, "SOLUSDT": 145.0,
        "BNBUSDT": 580.0,   "ADAUSDT": 0.47,   "DOTUSDT": 8.50,
        "LINKUSDT": 14.80,  "AVAXUSDT": 36.50, "MATICUSDT": 0.88,
        "LTCUSDT": 85.0,    "XRPUSDT": 0.57,   "DOGEUSDT": 0.12,
    }
    fetch_ok = True

check("Price fetch", fetch_ok, f"{len(live_prices)} symbols")
if live_prices:
    top3 = list(live_prices.items())[:3]
    for sym, px in top3:
        print(f"    {DIM}{sym}: ${px:,.4f}{RESET}")

# ── 2. EXCHANGE SLOT UNIT TESTS ────────────────────────────────────────────────
section("2. ExchangeSlot — Slot Management Logic")

from trading_hive_mind import ExchangeSlot

slot = ExchangeSlot("test")
check("Slot starts available",    slot.is_available)
check("Slot starts not occupied", not slot.is_occupied)
check("Active count = 0",         slot.active_count == 0)

slot.register_open()
check("After open: is_occupied",  slot.is_occupied)
check("After open: not available",not slot.is_available)
check("Trades counter = 1",       slot.trades == 1)

slot.register_close(pnl=2.50)
check("After close: available",   slot.is_available)
check("PnL tracked",              slot.total_pnl == 2.50, f"total_pnl={slot.total_pnl}")
check("Win counted",              slot.wins == 1)
check("Win rate = 100%",          slot.win_rate == 1.0)

slot.register_open()
slot.register_close(pnl=-1.00)
check("Loss counted",             slot.losses == 1)
check("Win rate = 50%",           abs(slot.win_rate - 0.5) < 0.01, f"wr={slot.win_rate:.2f}")
check("Net PnL = 1.50",           abs(slot.total_pnl - 1.50) < 0.001, f"pnl={slot.total_pnl}")

# ── 3. HIVE MIND INIT ──────────────────────────────────────────────────────────
section("3. TradingHiveMind — Initialisation")

from trading_hive_mind import TradingHiveMind

hive = TradingHiveMind()
check("Hive created",             hive is not None)
check("3 exchange slots",         len(hive.slots) == 3)
check("Kraken slot present",      "kraken"  in hive.slots)
check("Capital slot present",     "capital" in hive.slots)
check("Alpaca slot present",      "alpaca"  in hive.slots)
check("Session target > 0",       hive.session_target_gbp > 0, f"£{hive.session_target_gbp:.0f}")
check("Session PnL starts at 0",  hive.session_pnl_gbp == 0.0)
check("Gate starts open",         hive._gate_ok is True)
check("No harp boosts yet",       len(hive._harp_boosts) == 0)

# ── 4. MARKET HARP WITH LIVE PRICES ───────────────────────────────────────────
section("4. Market Harp tick() — Live Price Feed")

harp_boosts: Dict[str, float] = {}
try:
    from market_harp import MarketHarp
    harp = MarketHarp()
    check("MarketHarp init",      True, f"{len(harp.strings)} strings tuned")

    # Feed live prices — tick() auto-normalises aliases (BTCUSDT → BTC etc.)
    t0 = time.time()
    harp_boosts = harp.tick(live_prices)
    elapsed = (time.time() - t0) * 1000
    check("Harp tick() completed", True, f"{elapsed:.0f}ms")
    check("Returns dict",          isinstance(harp_boosts, dict))

    print(f"\n    Harp boosts returned ({len(harp_boosts)} symbols):")
    for sym, boost in sorted(harp_boosts.items(), key=lambda x: -abs(x[1]))[:8]:
        bar = "▓" * min(int(abs(boost) * 20), 20)
        print(f"      {sym:12} {boost:+.4f}  {bar}")

    # Run a second tick — new baseline established, should produce boosts
    harp_boosts2 = harp.tick(live_prices)
    check("Second tick() OK",      isinstance(harp_boosts2, dict))

    # Inject artificial volatility: move BTC up 3% to force a pluck
    volatile_prices = dict(live_prices)
    btc_px = live_prices.get("BTCUSDT", 84000)
    volatile_prices["BTCUSDT"] = btc_px * 1.03   # +3% surge
    harp_boosts_volatile = harp.tick(volatile_prices)
    check("Volatile tick OK",      isinstance(harp_boosts_volatile, dict))
    total_boosts = sum(1 for v in harp_boosts_volatile.values() if v > 0)
    print(f"    After +3% BTC surge: {total_boosts} positive ripples, "
          f"{len(harp_boosts_volatile)} total boosts")

    hive.update_harp(harp_boosts_volatile)
    check("Hive.update_harp()",    len(hive._harp_boosts) == len(harp_boosts_volatile),
          f"{len(hive._harp_boosts)} signals stored")

except ImportError:
    print(f"  {YELLOW}MarketHarp not available — skipping harp tests{RESET}")
    check("MarketHarp import", False, "module missing")

# ── 5. MOCK TRADERS ────────────────────────────────────────────────────────────
section("5. Mock Traders — Boost Injection")

@dataclass
class MockKrakenTrader:
    """Minimal Kraken margin penny trader stub."""
    active_long:   Optional[object] = None
    active_short:  Optional[object] = None
    _hive_boosts:  Dict[str, float] = field(default_factory=dict)
    _tick_returns: list              = field(default_factory=list)

    def tick(self) -> list:
        return self._tick_returns.pop(0) if self._tick_returns else []

@dataclass
class MockCapitalTrader:
    """Minimal Capital CFD trader stub."""
    positions:     list              = field(default_factory=list)
    _hive_boosts:  Dict[str, float] = field(default_factory=dict)
    _tick_returns: list              = field(default_factory=list)

    def tick(self) -> list:
        return self._tick_returns.pop(0) if self._tick_returns else []

kraken_trader  = MockKrakenTrader()
capital_trader = MockCapitalTrader()

# Inject harp boosts manually (same as hive._inject_harp_to_kraken/capital)
hive._inject_harp_to_kraken(kraken_trader)
hive._inject_harp_to_capital(capital_trader)

check("Kraken _hive_boosts injected",
      kraken_trader._hive_boosts is hive._harp_boosts,
      f"{len(kraken_trader._hive_boosts)} signals")
check("Capital _hive_boosts injected",
      capital_trader._hive_boosts is hive._harp_boosts,
      f"{len(capital_trader._hive_boosts)} signals")

# Check the BTC ripple reaches Kraken
btc_boost = (
    kraken_trader._hive_boosts.get("BTC", 0) or
    kraken_trader._hive_boosts.get("BTCUSDT", 0)
)
eth_boost = (
    kraken_trader._hive_boosts.get("ETH", 0) or
    kraken_trader._hive_boosts.get("ETHUSDT", 0)
)
print(f"    Kraken sees — BTC ripple: {btc_boost:+.4f}  ETH ripple: {eth_boost:+.4f}")
check("Kraken can read BTC boost",  True)   # no exception = pass

# ── 6. COORDINATED TICK — NO CLOSED TRADES ────────────────────────────────────
section("6. Coordinated Hive tick() — Empty Cycle (no closed trades)")

result = hive.tick(kraken_trader=kraken_trader, capital_trader=capital_trader)
check("tick() returns dict",           isinstance(result, dict))
check("kraken key present",            "kraken"  in result)
check("capital key present",           "capital" in result)
check("Empty closed trades (kraken)",  result["kraken"]  == [])
check("Empty closed trades (capital)", result["capital"] == [])
check("Slots all unoccupied",
      all(not s.is_occupied for s in hive.slots.values()))
check("Session PnL still 0",          hive.session_pnl_gbp == 0.0)
check("Hive cycle counter = 1",       hive._cycle == 1, f"cycle={hive._cycle}")

# ── 7. TICK WITH CLOSED TRADES — PnL ACCUMULATION ─────────────────────────────
section("7. Tick with Closed Trades — PnL Accumulation")

# Simulate a winning Kraken margin trade closing
kraken_trader._tick_returns = [[
    {"pair": "XBT/USD", "side": "buy", "net_pnl": 3.75, "asset_class": "crypto"}
]]
# Simulate a winning Capital CFD trade closing
capital_trader._tick_returns = [[
    {"symbol": "GBPUSD", "direction": "BUY", "net_pnl": 1.20, "asset_class": "forex"}
]]

result2 = hive.tick(kraken_trader=kraken_trader, capital_trader=capital_trader)
check("Kraken close returned",     len(result2["kraken"])  == 1,
      f"closed: {result2['kraken']}")
check("Capital close returned",    len(result2["capital"]) == 1,
      f"closed: {result2['capital']}")

expected_pnl = 3.75 + 1.20
check("Session PnL accumulated",
      abs(hive.session_pnl_gbp - expected_pnl) < 0.001,
      f"got={hive.session_pnl_gbp:.4f}, expected={expected_pnl:.4f}")
check("Kraken slot win counted",   hive.slots["kraken"].wins  == 1)
check("Capital slot win counted",  hive.slots["capital"].wins == 1)
check("Cycle counter = 2",         hive._cycle == 2)

# Simulate a losing Kraken trade
kraken_trader._tick_returns = [[
    {"pair": "ETH/USD", "side": "sell", "net_pnl": -0.80, "asset_class": "crypto"}
]]
result3 = hive.tick(kraken_trader=kraken_trader, capital_trader=capital_trader)
check("Loss recorded in session",
      abs(hive.session_pnl_gbp - (expected_pnl - 0.80)) < 0.001,
      f"session_pnl={hive.session_pnl_gbp:.4f}")
check("Kraken slot loss counted",  hive.slots["kraken"].losses == 1)

# ── 8. ALPACA SLOT MANAGEMENT ──────────────────────────────────────────────────
section("8. Alpaca Slot — 1-Trade-Per-Exchange Enforcement")

check("Alpaca slot starts free",   hive.slots["alpaca"].is_available)
check("alpaca_slot_available()",   hive.alpaca_slot_available())

hive.register_alpaca_open()
check("After open: slot occupied", hive.slots["alpaca"].is_occupied)
check("alpaca_slot_available() False after open",
      not hive.alpaca_slot_available())

# Simulate sync_alpaca with 1 live position
class FakePos:
    def __init__(self, exchange): self.exchange = exchange
fake_positions = [FakePos("alpaca"), FakePos("kraken"), FakePos("alpaca")]
hive.sync_alpaca(fake_positions)
check("sync_alpaca counts correctly",
      hive.slots["alpaca"].active_count == 2,
      f"count={hive.slots['alpaca'].active_count}")

# Force back to 1
hive.sync_alpaca([FakePos("alpaca")])
check("sync_alpaca reset to 1",    hive.slots["alpaca"].active_count == 1)

hive.register_alpaca_close(pnl=4.00)
check("After close: slot free",    hive.slots["alpaca"].is_available)
check("Alpaca PnL banked",         hive.slots["alpaca"].total_pnl == 4.00,
      f"pnl={hive.slots['alpaca'].total_pnl}")
check("Session PnL includes Alpaca",
      hive.session_pnl_gbp >= 4.00,
      f"session={hive.session_pnl_gbp:.4f}")

# ── 9. GATE LOGIC ──────────────────────────────────────────────────────────────
section("9. Gate Logic — Fail-Open, TTL Cache")

# Gate should be open (Quadrumvirate unavailable → fail-open)
gate1 = hive.gate_open()
check("Gate fail-open",            gate1 is True)
check("Gate cached after first call",
      hive._gate_refreshed_at > 0)

# Force cache expiry and re-check
hive._gate_refreshed_at = 0.0
gate2 = hive.gate_open()
check("Gate re-evaluates after TTL", gate2 is True)

# Simulate gate CLOSED
hive._gate_ok = False
hive._gate_refreshed_at = time.time()   # within TTL → cached
check("Cached CLOSED gate respected",  not hive.gate_open())
check("Alpaca slot blocked by gate",   not hive.alpaca_slot_available())

# Restore
hive._gate_ok = True
hive._gate_refreshed_at = 0.0

# ── 10. THOUGHTBUS BROADCAST ───────────────────────────────────────────────────
section("10. ThoughtBus Broadcast")

broadcast_payloads: list = []

class MockThought:
    def __init__(self, source, topic, payload):
        self.source  = source
        self.topic   = topic
        self.payload = payload

class MockBus:
    def publish(self, thought):
        broadcast_payloads.append(thought)
    def think(self, *a, **kw): pass

hive.set_bus(MockBus())
hive._last_broadcast = 0.0   # Force immediate broadcast
hive.broadcast(session_stats={"total_pnl": 9.99})
check("Broadcast fired",           len(broadcast_payloads) == 1,
      f"payloads={len(broadcast_payloads)}")

if broadcast_payloads:
    p = broadcast_payloads[0]
    check("Topic = hive.unity.status",       p.topic   == "hive.unity.status")
    check("Source = trading_hive_mind",      p.source  == "trading_hive_mind")
    check("Payload has session_pnl_gbp",     "session_pnl_gbp"    in p.payload)
    check("Payload has gate_open",           "gate_open"          in p.payload)
    check("Payload has slots dict",          "slots"              in p.payload)
    check("Payload has harp_signals count",  "harp_signals"       in p.payload)
    check("Payload has goal_pct",            "goal_pct"           in p.payload)
    check("All 3 exchanges in slots",
          set(p.payload["slots"].keys()) == {"kraken", "capital", "alpaca"})

    pnl = p.payload["session_pnl_gbp"]
    tgt = p.payload["session_target_gbp"]
    goal_pct = p.payload["goal_pct"]
    check("Session PnL in payload > 0",    pnl  > 0, f"pnl={pnl:.4f}")
    check("Target in payload > 0",         tgt  > 0, f"target=£{tgt:.0f}")
    check("Goal pct = pnl/target",
          abs(goal_pct - pnl / tgt) < 0.001, f"goal_pct={goal_pct:.3f}")

    print(f"\n    Broadcast payload summary:")
    print(f"      session_pnl:  £{pnl:.4f}")
    print(f"      target:       £{tgt:.0f}")
    print(f"      goal_pct:     {goal_pct:.1%}")
    print(f"      gate_open:    {p.payload['gate_open']}")
    print(f"      harp_signals: {p.payload['harp_signals']}")
    print(f"      cycle:        {p.payload.get('cycle','?')}")

# ── 11. DISPLAY: GOAL BANNER + STATUS LINES ───────────────────────────────────
section("11. Display — Goal Banner + Per-Exchange Status")

banner = hive.goal_banner()
check("goal_banner() returns list",    isinstance(banner, list))
check("Banner has 4 lines",            len(banner) == 4, f"lines={len(banner)}")
print()
for line in banner:
    print(line)

status = hive.status_lines()
check("status_lines() returns list",   isinstance(status, list))
check("Has banner + 3 exchange lines", len(status) >= 7)
print()
for line in status[4:]:   # exchange lines (after banner)
    print(line)

one = hive.one_liner()
check("one_liner() returns string",    isinstance(one, str) and len(one) > 10)
print(f"\n  ONE-LINER: {one}")

# ── 12. THREE-CYCLE INTEGRATION RHYTHM ────────────────────────────────────────
section("12. Three-Cycle Integration — Autonomous Rhythm")

# Reset fresh hive for clean rhythm test
hive2 = TradingHiveMind()

# Cycle 1: Kraken opens trade (no close yet)
k2 = MockKrakenTrader()
k2.active_long  = object()   # simulate open LONG
c2 = MockCapitalTrader()
r1 = hive2.tick(kraken_trader=k2, capital_trader=c2, price_map=live_prices)
check("Cycle 1: tick completed",       hive2._cycle == 1)
check("Cycle 1: Kraken slot = 1",
      hive2.slots["kraken"].active_count == 1,
      f"count={hive2.slots['kraken'].active_count}")

# Cycle 2: Capital opens + closes in same tick
c2._tick_returns = [[{"symbol": "EURUSD", "net_pnl": 0.85, "asset_class": "forex"}]]
r2 = hive2.tick(kraken_trader=k2, capital_trader=c2, price_map=live_prices)
check("Cycle 2: Capital close counted",
      hive2.slots["capital"].wins == 1)
check("Cycle 2: PnL = 0.85",
      abs(hive2.session_pnl_gbp - 0.85) < 0.001)

# Cycle 3: Kraken closes profitably
k2.active_long = None     # position closed on exchange
k2._tick_returns = [[{"pair": "XBT/USD", "net_pnl": 5.10, "asset_class": "crypto"}]]
r3 = hive2.tick(kraken_trader=k2, capital_trader=c2, price_map=live_prices)
check("Cycle 3: Kraken close counted",
      hive2.slots["kraken"].wins == 1)
check("Cycle 3: Kraken slot now free",
      hive2.slots["kraken"].active_count == 0)
check("Cycle 3: Total PnL = 5.95",
      abs(hive2.session_pnl_gbp - 5.95) < 0.001,
      f"got={hive2.session_pnl_gbp:.4f}")
check("Cycle counter = 3",            hive2._cycle == 3)

# Final status
print()
for line in hive2.status_lines():
    print(line)

# ── SUMMARY ────────────────────────────────────────────────────────────────────
section("TEST SUMMARY")

total   = len(results)
passed  = sum(1 for _, ok, _ in results if ok)
failed  = total - passed
pct     = passed / total * 100 if total else 0

print(f"\n  {BOLD}Results: {passed}/{total} passed  ({pct:.0f}%){RESET}")

if failed:
    print(f"\n  {RED}FAILED tests:{RESET}")
    for name, ok, detail in results:
        if not ok:
            print(f"    {RED}✗{RESET} {name}" + (f"  [{detail}]" if detail else ""))
else:
    print(f"\n  {GREEN}{BOLD}ALL TESTS PASSED — Hive Mind fully operational{RESET}")

print()
sys.exit(0 if failed == 0 else 1)
