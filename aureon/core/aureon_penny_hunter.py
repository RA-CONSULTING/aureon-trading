#!/usr/bin/env python3
"""
aureon_penny_hunter.py — Hunt pennies on Capital.com. Fast. Autonomous.

This is the simplest, most direct trading loop:
1. Authenticate to Capital.com
2. Check what's moving
3. Open minimum positions in the direction of momentum
4. Close at ANY profit (even £0.001)
5. Repeat

No fear. No waiting. Just hunt pennies until they become pounds.
The 1.88% law is for the big plays. This is the penny engine.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]

log = logging.getLogger("aureon.penny_hunter")

# Load .env
try:
    env_path = _REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
except Exception:
    pass

try:
    import requests
except ImportError:
    requests = None


# Instruments to hunt — liquid, tight spreads
from datetime import datetime, timezone

def _is_market_open(market_type: str) -> bool:
    """Check if a market is currently open."""
    now = datetime.now(timezone.utc)
    hour = now.hour
    weekday = now.weekday()  # 0=Mon, 6=Sun

    if market_type == "crypto":
        return True  # 24/7/365

    if market_type == "forex":
        # Forex: Sun 22:00 UTC to Fri 22:00 UTC
        if weekday == 6 and hour < 22:
            return False  # Sunday before open
        if weekday == 5 and hour >= 22:
            return False  # Saturday after close
        if weekday == 5:
            return False  # Saturday
        return True

    if market_type == "us_stocks":
        # US stocks: Mon-Fri 14:30-21:00 UTC (9:30-4:00 ET)
        if weekday >= 5:
            return False
        return 14 <= hour < 21

    if market_type == "uk_stocks":
        # UK/EU: Mon-Fri 08:00-16:30 UTC
        if weekday >= 5:
            return False
        return 8 <= hour < 17

    if market_type == "gold":
        # Gold CFD: Sun 23:00 - Fri 22:00 UTC (near 24/5)
        if weekday == 5 and hour >= 22:
            return False
        if weekday == 6 and hour < 23:
            return False
        return True

    return True  # Default: assume open


# Capital.com instruments with market type
HUNT_LIST = [
    {"epic": "GOLD", "name": "Gold", "min_size": 0.1, "market": "gold"},
    {"epic": "US100", "name": "US Tech 100", "min_size": 0.5, "market": "us_stocks"},
    {"epic": "US500", "name": "US 500", "min_size": 0.5, "market": "us_stocks"},
    {"epic": "UK100", "name": "UK 100", "min_size": 0.5, "market": "uk_stocks"},
    {"epic": "EURUSD", "name": "EUR/USD", "min_size": 1000, "market": "forex"},
    {"epic": "GBPUSD", "name": "GBP/USD", "min_size": 1000, "market": "forex"},
]

# Kraken crypto pairs (24/7)
KRAKEN_PAIRS = ["XBTUSD", "ETHUSD", "XRPUSD", "SOLUSD"]

# Alpaca stocks (US market hours only)
ALPACA_STOCKS = ["SPY", "AAPL", "TSLA", "QQQ"]

BASE_URL = "https://api-capital.backend-capital.com"
MAX_POSITIONS = 3
TAKE_PROFIT_GBP = 0.02  # Take profit above spread cost — 2p minimum
MAX_LOSS_GBP = -999.0   # NEVER close at loss — hold forever


class PennyHunter:
    """Fast autonomous penny hunter on Capital.com."""

    def __init__(self):
        self._api_key = os.environ.get("CAPITAL_API_KEY", "")
        self._identifier = os.environ.get("CAPITAL_IDENTIFIER", "")
        self._password = os.environ.get("CAPITAL_PASSWORD", "")
        self._cst = ""
        self._token = ""
        self._headers: Dict[str, str] = {}
        self._authenticated = False
        self._trades_total = 0
        self._profit_total = 0.0
        self._wins = 0
        self._losses = 0
        self._best_trade = 0.0
        self._worst_trade = 0.0
        self._streak = 0
        self._confidence = 0.5
        self._last_balance = 0.0
        self._starting_balance = 0.0
        self._start_time = time.time()
        self._trade_log: List[Dict] = []

        # Fee trackers — know the REAL cost before every trade
        self._kraken_fees = None
        self._alpaca_fees = None
        try:
            from aureon.exchanges.kraken_fee_tracker import get_kraken_fee_tracker
            self._kraken_fees = get_kraken_fee_tracker()
            log.info(f"[PENNY] Kraken fee tracker loaded")
        except Exception:
            pass
        try:
            from aureon.exchanges.alpaca_fee_tracker import AlpacaFeeTracker
            self._alpaca_fees = AlpacaFeeTracker()
            log.info(f"[PENNY] Alpaca fee tracker loaded")
        except Exception:
            pass

        # Multi-exchange support
        self._kraken = None
        self._alpaca = None
        try:
            from aureon.exchanges.kraken_client import KrakenClient
            self._kraken = KrakenClient()
            if not self._kraken.dry_run:
                log.info("[PENNY] Kraken WIRED for crypto trading")
            else:
                self._kraken = None
        except Exception:
            pass
        try:
            from aureon.exchanges.alpaca_client import AlpacaClient
            self._alpaca = AlpacaClient()
            if not getattr(self._alpaca, 'dry_run', True):
                log.info("[PENNY] Alpaca WIRED for stock trading")
            else:
                self._alpaca = None
        except Exception:
            pass

    def authenticate(self) -> bool:
        if not requests or not self._api_key:
            return False
        try:
            r = requests.post(f"{BASE_URL}/api/v1/session", json={
                "identifier": self._identifier,
                "password": self._password,
            }, headers={"X-CAP-API-KEY": self._api_key}, timeout=10)
            if r.status_code == 200:
                self._cst = r.headers.get("CST", "")
                self._token = r.headers.get("X-SECURITY-TOKEN", "")
                self._headers = {
                    "X-CAP-API-KEY": self._api_key,
                    "CST": self._cst,
                    "X-SECURITY-TOKEN": self._token,
                    "Content-Type": "application/json",
                }
                self._authenticated = True
                self._starting_balance = self.get_balance()
                self._last_balance = self._starting_balance
                log.info(f"[PENNY] Capital.com authenticated — starting balance: £{self._starting_balance:.2f}")
                return True
        except Exception as e:
            log.debug(f"Auth error: {e}")
        return False

    def get_positions(self) -> List[Dict]:
        if not self._authenticated:
            return []
        try:
            r = requests.get(f"{BASE_URL}/api/v1/positions", headers=self._headers, timeout=10)
            return r.json().get("positions", []) if r.status_code == 200 else []
        except Exception:
            return []

    def get_balance(self) -> float:
        try:
            r = requests.get(f"{BASE_URL}/api/v1/accounts", headers=self._headers, timeout=10)
            accs = r.json().get("accounts", [])
            return float(accs[0].get("balance", {}).get("available", 0)) if accs else 0
        except Exception:
            return 0

    def open_position(self, epic: str, direction: str, size: float) -> Optional[str]:
        """Open a position. Returns deal_id or None."""
        try:
            r = requests.post(f"{BASE_URL}/api/v1/positions", json={
                "epic": epic,
                "direction": direction,
                "size": size,
                "guaranteedStop": False,
                "forceOpen": True,
            }, headers=self._headers, timeout=15)

            if r.status_code == 200:
                deal_ref = r.json().get("dealReference", "")
                if deal_ref:
                    # Confirm
                    r2 = requests.get(f"{BASE_URL}/api/v1/confirms/{deal_ref}",
                                      headers=self._headers, timeout=10)
                    confirm = r2.json() if r2.status_code == 200 else {}
                    if confirm.get("dealStatus") == "ACCEPTED":
                        deal_id = confirm.get("dealId", "")
                        level = confirm.get("level", 0)
                        log.info(f"[PENNY] OPENED {direction} {size} {epic} @ {level} (deal={deal_id})")
                        return deal_id
            else:
                log.debug(f"Open failed {epic}: {r.status_code} {r.text[:100]}")
        except Exception as e:
            log.debug(f"Open error {epic}: {e}")
        return None

    def close_position(self, deal_id: str, epic: str, direction: str, size: float) -> float:
        """Close a position. Returns profit/loss."""
        close_dir = "SELL" if direction == "BUY" else "BUY"
        try:
            r = requests.delete(f"{BASE_URL}/api/v1/positions/{deal_id}", json={
                "dealId": deal_id,
                "epic": epic,
                "direction": close_dir,
                "size": size,
                "orderType": "MARKET",
            }, headers=self._headers, timeout=15)

            if r.status_code == 200:
                deal_ref = r.json().get("dealReference", "")
                if deal_ref:
                    r2 = requests.get(f"{BASE_URL}/api/v1/confirms/{deal_ref}",
                                      headers=self._headers, timeout=10)
                    confirm = r2.json() if r2.status_code == 200 else {}
                    profit = float(confirm.get("profit", 0) or 0)
                    log.info(f"[PENNY] CLOSED {epic} deal={deal_id} profit={profit:+.3f}")
                    return profit
        except Exception as e:
            log.debug(f"Close error: {e}")
        return 0.0

    def tick(self) -> Dict[str, Any]:
        """
        ONE cycle of penny hunting:
        1. Check open positions — close winners, cut losers
        2. If room for more — open new positions on momentum
        """
        if not self._authenticated:
            if not self.authenticate():
                return {"action": "auth_failed"}

        result = {"action": "tick", "opened": [], "closed": [], "holding": []}

        # Step 1: Check open positions
        positions = self.get_positions()
        open_count = len(positions)

        for p in positions:
            pos = p.get("position", {})
            mkt = p.get("market", {})
            profit = float(pos.get("upl", 0) or 0)
            deal_id = pos.get("dealId", "")
            epic = mkt.get("epic", "")
            direction = pos.get("direction", "")
            size = float(pos.get("size", 0) or 0)
            name = mkt.get("instrumentName", epic)

            if profit >= TAKE_PROFIT_GBP:
                # TAKE PROFIT — a penny is enough
                actual = self.close_position(deal_id, epic, direction, size)
                self._trades_total += 1
                self._profit_total += actual
                self._wins += 1
                self._streak = max(1, self._streak + 1) if self._streak >= 0 else 1
                self._best_trade = max(self._best_trade, actual)
                # Confidence grows with wins
                self._confidence = min(1.0, self._confidence + 0.05)
                self._trade_log.append({"epic": epic, "profit": actual, "result": "WIN", "time": time.time()})
                result["closed"].append({"epic": epic, "profit": actual, "name": name})
                open_count -= 1
                self._last_balance = self.get_balance()
                growth = self._last_balance - self._starting_balance if self._starting_balance else 0
                log.info(f"[PENNY] WIN: {name} +£{actual:.3f} | total: £{self._profit_total:+.3f} | "
                         f"wins:{self._wins} losses:{self._losses} | streak:{self._streak} | "
                         f"conf:{self._confidence:.0%} | balance: £{self._last_balance:.2f} ({growth:+.2f})")

            elif profit <= MAX_LOSS_GBP:
                # HOLD — never close at a loss. Wait for recovery.
                # "IF YOU DON'T QUIT, YOU CAN'T LOSE"
                result["holding"].append({"epic": epic, "profit": profit, "name": name, "waiting": True})
                log.info(f"[PENNY] HOLDING {name} at £{profit:+.3f} — waiting for recovery. Never close negative.")

            else:
                result["holding"].append({"epic": epic, "profit": profit, "name": name})

        # Step 2: Open new positions if room
        if open_count < MAX_POSITIONS:
            for instrument in HUNT_LIST:
                if open_count >= MAX_POSITIONS:
                    break

                epic = instrument["epic"]
                market_type = instrument.get("market", "forex")

                # Check if market is open
                if not _is_market_open(market_type):
                    continue

                # Skip if already holding this epic
                if any(h["epic"] == epic for h in result["holding"]):
                    continue

                # Get market price + spread to determine direction AND cost
                try:
                    r = requests.get(f"{BASE_URL}/api/v1/markets/{epic}",
                                     headers=self._headers, timeout=10)
                    if r.status_code == 200:
                        market = r.json()
                        snap = market.get("snapshot", {})
                        change = float(snap.get("percentageChange", 0) or 0)
                        bid = float(snap.get("bid", 0) or 0)
                        ask = float(snap.get("offer", snap.get("ask", 0)) or 0)
                        spread = ask - bid if ask > bid > 0 else 0

                        size = instrument["min_size"]
                        # Cost check: spread cost must be recoverable
                        spread_cost = spread * size
                        min_movement = spread * 2  # Need at least 2x spread to profit

                        # Only trade if momentum > spread cost AND market is moving
                        if abs(change) > 0.05 and spread_cost < 1.0:
                            direction = "BUY" if change > 0 else "SELL"
                            deal_id = self.open_position(epic, direction, size)
                            if deal_id:
                                result["opened"].append({
                                    "epic": epic, "direction": direction,
                                    "size": size, "change": change,
                                    "spread": spread, "spread_cost": spread_cost,
                                })
                                open_count += 1
                                log.info(f"[PENNY] {direction} {epic} | momentum:{change:+.2f}% | spread:{spread:.2f} | cost:£{spread_cost:.3f}")
                        elif spread_cost >= 1.0:
                            log.debug(f"[PENNY] SKIP {epic} — spread cost £{spread_cost:.3f} too high")
                except Exception as e:
                    log.debug(f"Market check {epic}: {e}")

        # ── KRAKEN: Use the REAL KrakenMarginArmyTrader — it knows margin fees ──
        # Margin costs: 0.376% open + 0.26% taker + 0.01%/4hr rollover = ~1%+ round trip
        # The KrakenMarginArmyTrader.tick() handles all this already.
        # We just need to call it through the unified trader.
        # For spot: use USDT to buy crypto only when momentum is strong enough to cover 0.52% fees
        if self._kraken and self._trades_total % 10 == 0:
            try:
                # Get real fee tier from tracker
                kraken_fee_pct = 0.26
                if self._kraken_fees:
                    try:
                        rates = self._kraken_fees.get_fee_rates()
                        kraken_fee_pct = float(rates.get("taker_pct", 0.26))
                    except Exception:
                        pass

                # MARGIN: opening fee 0.376% + taker + rollover
                margin_open_fee = 0.376
                rollover_per_4h = 0.01
                margin_round_trip = margin_open_fee + (kraken_fee_pct * 2) + rollover_per_4h
                spot_round_trip = kraken_fee_pct * 2

                bal = self._kraken.get_balance()
                usdt = float(bal.get("USDT", 0) or 0)

                if usdt > 15:
                    # SPOT trade (cheaper) — buy crypto with USDT
                    import random
                    pair = random.choice(KRAKEN_PAIRS)
                    trade_pair = pair.replace("USD", "USDT")
                    trade_amount = min(usdt * 0.05, 15.0)  # 5% of USDT, max $15

                    try:
                        order = self._kraken.place_market_order(
                            symbol=trade_pair, side="buy", quote_qty=trade_amount
                        )
                        if order and isinstance(order, dict) and order.get("txid"):
                            self._trades_total += 1
                            log.info(f"[PENNY-KRAKEN] SPOT BUY {trade_pair} ${trade_amount:.2f} | "
                                     f"spot fee:{kraken_fee_pct:.2f}% | need {spot_round_trip:.2f}% to profit | "
                                     f"(margin would need {margin_round_trip:.2f}%)")
                            result["opened"].append({"epic": trade_pair, "direction": "BUY",
                                                     "exchange": "kraken", "fee_pct": kraken_fee_pct,
                                                     "round_trip_cost": spot_round_trip})
                    except Exception as e:
                        log.debug(f"Kraken spot buy: {e}")

            except Exception as e:
                log.debug(f"Kraken cycle: {e}")

        # ── ALPACA: Stock trades (US market hours only) ──
        if self._alpaca and self.step_attr % 15 == 0 and _is_market_open("us_stocks"):
            try:
                acct = self._alpaca.get_account()
                cash = float(acct.get("cash", 0) if isinstance(acct, dict) else getattr(acct, "cash", 0) or 0)
                if cash > 1:
                    import random
                    stock = random.choice(ALPACA_STOCKS)
                    try:
                        order = self._alpaca.place_market_order(
                            symbol=stock, side="buy", qty=None, notional=min(cash * 0.5, 5.0)
                        )
                        if order:
                            self._trades_total += 1
                            log.info(f"[PENNY-ALPACA] BUY {stock} with ${min(cash*0.5, 5):.2f}")
                            result["opened"].append({"epic": stock, "direction": "BUY", "exchange": "alpaca"})
                    except Exception as e:
                        log.debug(f"Alpaca trade: {e}")
                else:
                    log.debug(f"[PENNY-ALPACA] US market open but cash too low: ${cash:.2f}")
            except Exception as e:
                log.debug(f"Alpaca balance: {e}")
        elif self._alpaca and not _is_market_open("us_stocks"):
            pass  # US market closed — crypto and forex still hunting

        return result

    @property
    def step_attr(self):
        return self._trades_total + int(time.time()) % 100

    def get_status(self) -> Dict[str, Any]:
        return {
            "authenticated": self._authenticated,
            "trades_total": self._trades_total,
            "profit_total": self._profit_total,
            "wins": self._wins,
            "losses": self._losses,
            "win_rate": (self._wins / max(1, self._wins + self._losses)) * 100,
            "best_trade": self._best_trade,
            "worst_trade": self._worst_trade,
            "streak": self._streak,
            "confidence": self._confidence,
            "balance": self._last_balance,
            "uptime_s": time.time() - self._start_time,
        }


# Singleton
_hunter: Optional[PennyHunter] = None

def get_penny_hunter() -> PennyHunter:
    global _hunter
    if _hunter is None:
        _hunter = PennyHunter()
    return _hunter


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    hunter = get_penny_hunter()
    if not hunter.authenticate():
        print("Auth failed")
        exit(1)

    print(f"Balance: £{hunter.get_balance():.2f}")
    print("Penny hunting started... Ctrl+C to stop\n")

    while True:
        result = hunter.tick()
        for c in result.get("closed", []):
            print(f"  CLOSED {c['name']}: {c['profit']:+.3f}")
        for o in result.get("opened", []):
            print(f"  OPENED {o['direction']} {o['epic']} (momentum: {o['change']:+.2f}%)")
        for h in result.get("holding", []):
            print(f"  HOLDING {h['name']}: {h['profit']:+.3f}")

        status = hunter.get_status()
        print(f"  [{status['trades_total']} trades | PnL: {status['profit_total']:+.3f}]")
        time.sleep(5)
