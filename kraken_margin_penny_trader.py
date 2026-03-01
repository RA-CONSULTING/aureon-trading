#!/usr/bin/env python3
"""
KRAKEN MARGIN UNIVERSE — PENNY PROFIT TRADER
=============================================
Scans the ENTIRE Kraken margin universe and trades every eligible pair.
Target: $0.01 net profit per trade. That's it. One penny.

Strategy:
  1. Fetch all margin-eligible pairs from Kraken
  2. Get live prices for every pair
  3. Open margin positions (long or short based on momentum)
  4. Monitor all open positions
  5. Close the INSTANT net P&L >= $0.01 (after fees)
  6. No stop loss — hold with patience until profitable
  7. Only exception: liquidation risk

Philosophy: "One penny profit is still profit."

Usage:
    python kraken_margin_penny_trader.py              # Live trading
    python kraken_margin_penny_trader.py --dry-run     # Simulation mode
    python kraken_margin_penny_trader.py --scan-only   # Just show margin pairs
"""

import os
import sys
import json
import time
import math
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('margin_penny_trader')

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════
PENNY_PROFIT_TARGET = 0.01    # $0.01 net profit target
MIN_PROFIT_USD = 0.01         # Minimum net profit to close
SCAN_INTERVAL = 15            # Seconds between full scans
POSITION_CHECK_INTERVAL = 10  # Seconds between position checks
LIQUIDATION_WARN = 150        # Margin level % warning
LIQUIDATION_FORCE = 115       # Margin level % force-close
MAX_CONCURRENT_POSITIONS = 10 # Max open margin positions
MIN_TRADE_USD = 10.0          # Minimum trade value in USD
MAX_TRADE_USD = 50.0          # Maximum trade value per position
KRAKEN_TAKER_FEE = 0.0026     # 0.26% taker fee
STATE_FILE = "kraken_margin_penny_state.json"
RESULTS_FILE = "kraken_margin_penny_results.json"

# Quote currencies we trade against (USD-denominated for penny tracking)
USD_QUOTES = {"USD", "ZUSD"}


@dataclass
class MarginPairInfo:
    """Info about a margin-eligible trading pair."""
    pair: str               # Altname e.g. "ETHUSD"
    internal: str           # Kraken internal name
    base: str               # Base asset e.g. "ETH"
    quote: str              # Quote asset e.g. "USD"
    leverage_buy: list       # Available buy leverages
    leverage_sell: list      # Available sell leverages
    max_leverage: int        # Max leverage
    ordermin: float          # Minimum order size
    lot_decimals: int        # Decimal places for volume
    price_decimals: int      # Decimal places for price
    last_price: float = 0.0  # Current price
    bid: float = 0.0
    ask: float = 0.0
    spread_pct: float = 0.0  # Spread as percentage
    volume_24h: float = 0.0
    momentum: float = 0.0    # Price change % 24h


@dataclass
class PennyTrade:
    """A tracked penny-profit margin trade."""
    pair: str
    side: str               # 'buy' (long) or 'sell' (short)
    volume: float
    entry_price: float
    leverage: int
    entry_fee: float
    entry_time: float
    order_id: str
    # Calculated
    cost: float = 0.0
    breakeven_price: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class KrakenMarginPennyTrader:
    """
    Trades the ENTIRE Kraken margin universe targeting $0.01 profit per trade.
    """

    def __init__(self, dry_run: bool = False):
        from kraken_client import KrakenClient, get_kraken_client
        self.client = get_kraken_client()

        if dry_run:
            self.client.dry_run = True
        self.dry_run = self.client.dry_run

        # All margin-eligible USD pairs
        self.margin_pairs: Dict[str, MarginPairInfo] = {}
        # Active trades we're monitoring
        self.active_trades: Dict[str, PennyTrade] = {}
        # Completed trades for this session
        self.completed_trades: List[dict] = []
        # Stats
        self.total_profit = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.start_time = time.time()

        self._load_state()

    # ──────────────────────────────────────────────────────────
    #  MARGIN UNIVERSE DISCOVERY
    # ──────────────────────────────────────────────────────────
    def discover_margin_universe(self) -> Dict[str, MarginPairInfo]:
        """Fetch ALL margin-eligible pairs from Kraken."""
        logger.info("Scanning Kraken margin universe...")

        margin_pairs_raw = self.client.get_margin_pairs()
        pairs_data = self.client._load_asset_pairs()

        usd_margin_pairs = {}

        for mp in margin_pairs_raw:
            pair_name = mp["pair"]
            internal = mp["internal"]
            base = mp["base"]
            quote = mp["quote"]

            # Only trade USD-quoted pairs for penny tracking
            if quote not in USD_QUOTES and quote != "USD":
                continue

            # Get additional pair info
            pair_info = pairs_data.get(internal, {})
            ordermin = float(pair_info.get("ordermin", 0.0001))
            lot_decimals = int(pair_info.get("lot_decimals", 8))
            price_decimals = int(pair_info.get("pair_decimals", 4))

            info = MarginPairInfo(
                pair=pair_name,
                internal=internal,
                base=base,
                quote="USD",
                leverage_buy=mp["leverage_buy"],
                leverage_sell=mp["leverage_sell"],
                max_leverage=mp["max_leverage"],
                ordermin=ordermin,
                lot_decimals=lot_decimals,
                price_decimals=price_decimals,
            )

            usd_margin_pairs[pair_name] = info

        self.margin_pairs = usd_margin_pairs
        logger.info(f"Found {len(usd_margin_pairs)} USD margin-eligible pairs")
        return usd_margin_pairs

    def refresh_prices(self):
        """Get live prices for all margin pairs."""
        if not self.margin_pairs:
            return

        updated = 0
        # Batch ticker requests to respect rate limits
        pair_names = list(self.margin_pairs.keys())

        for pair_name in pair_names:
            info = self.margin_pairs[pair_name]
            try:
                ticker = self.client.get_ticker(pair_name)
                if ticker and ticker.get("price", 0) > 0:
                    info.last_price = ticker["price"]
                    info.bid = ticker.get("bid", ticker["price"])
                    info.ask = ticker.get("ask", ticker["price"])
                    if info.bid > 0:
                        info.spread_pct = (info.ask - info.bid) / info.bid * 100
                    updated += 1
            except Exception as e:
                logger.debug(f"Ticker error for {pair_name}: {e}")

            # Rate limiting — don't hammer the API
            time.sleep(0.3)

        # Get 24h data for momentum
        try:
            tickers_24h = self.client.get_24h_tickers()
            for t in tickers_24h:
                sym = t.get("symbol", "")
                if sym in self.margin_pairs:
                    try:
                        self.margin_pairs[sym].momentum = float(
                            t.get("priceChangePercent", 0)
                        )
                        self.margin_pairs[sym].volume_24h = float(
                            t.get("quoteVolume", 0)
                        )
                    except (ValueError, TypeError):
                        pass
        except Exception as e:
            logger.warning(f"24h ticker batch error: {e}")

        logger.info(f"Prices updated for {updated}/{len(pair_names)} pairs")

    # ──────────────────────────────────────────────────────────
    #  TRADE SIZING & ENTRY LOGIC
    # ──────────────────────────────────────────────────────────
    def calculate_min_volume(self, pair_info: MarginPairInfo) -> Tuple[float, float]:
        """
        Calculate the minimum volume needed to achieve $0.01 profit
        after fees, and the required price move.

        Returns: (volume, trade_value_usd)
        """
        price = pair_info.last_price
        if price <= 0:
            return 0, 0

        # We need: (price_move * volume) - (2 * fee_rate * trade_value) >= $0.01
        # With leverage, our margin is trade_value / leverage
        # But profit is on the full trade_value
        #
        # fee per side = trade_value * 0.0026
        # total fees = 2 * trade_value * 0.0026 = trade_value * 0.0052
        # Required gross profit = $0.01 + total_fees
        # price_move = required_gross_profit / volume
        #
        # Using minimum trade value to keep margin requirement low
        lev = min(pair_info.leverage_buy) if pair_info.leverage_buy else 2

        # Start with minimum order size
        min_vol = pair_info.ordermin
        trade_value = min_vol * price

        # Ensure trade is at least MIN_TRADE_USD
        if trade_value < MIN_TRADE_USD:
            min_vol = MIN_TRADE_USD / price
            trade_value = min_vol * price

        # Cap at MAX_TRADE_USD
        if trade_value > MAX_TRADE_USD:
            min_vol = MAX_TRADE_USD / price
            trade_value = min_vol * price

        # Round to lot decimals
        min_vol = round(min_vol, pair_info.lot_decimals)

        # Ensure still above ordermin
        if min_vol < pair_info.ordermin:
            min_vol = pair_info.ordermin
            trade_value = min_vol * price

        return min_vol, trade_value

    def select_entry_side(self, pair_info: MarginPairInfo) -> str:
        """
        Decide whether to go long or short based on momentum.
        Simple: positive momentum = long, negative = short.
        Near zero = long (slight long bias).
        """
        if pair_info.momentum > 0.1:
            return "buy"   # Long — ride the trend
        elif pair_info.momentum < -0.1:
            return "sell"  # Short — ride the downtrend
        else:
            return "buy"   # Default long in sideways

    def find_trade_opportunities(self) -> List[Tuple[MarginPairInfo, str, float, float]]:
        """
        Scan all margin pairs and find ones worth trading.

        Returns list of (pair_info, side, volume, trade_value)
        """
        opportunities = []

        # How many more positions can we open?
        open_count = len(self.active_trades)
        slots_available = MAX_CONCURRENT_POSITIONS - open_count

        if slots_available <= 0:
            return []

        # Check margin availability
        try:
            tb = self.client.get_trade_balance()
            free_margin = tb.get("free_margin", 0)
            margin_level = tb.get("margin_level", 0)
        except Exception as e:
            logger.warning(f"Could not get trade balance: {e}")
            free_margin = 0
            margin_level = 0

        if free_margin < MIN_TRADE_USD:
            logger.info(f"Insufficient free margin: ${free_margin:.2f}")
            return []

        # Don't open new trades if margin level is getting low
        if margin_level > 0 and margin_level < 200:
            logger.warning(f"Margin level {margin_level:.0f}% too low for new trades")
            return []

        # Skip pairs we already have positions in
        active_pairs = {t.pair for t in self.active_trades.values()}

        for pair_name, info in self.margin_pairs.items():
            if pair_name in active_pairs:
                continue
            if info.last_price <= 0:
                continue
            if info.spread_pct > 1.0:
                # Skip pairs with >1% spread — too expensive
                continue

            side = self.select_entry_side(info)
            vol, trade_val = self.calculate_min_volume(info)

            if vol <= 0 or trade_val <= 0:
                continue

            # Check we can afford the margin
            lev = min(info.leverage_buy if side == "buy" else info.leverage_sell)
            margin_required = trade_val / lev
            if margin_required > free_margin * 0.5:
                # Don't use more than 50% of free margin on one trade
                continue

            opportunities.append((info, side, vol, trade_val))

        # Sort by volume (most liquid first) then take available slots
        opportunities.sort(key=lambda x: x[0].volume_24h, reverse=True)
        return opportunities[:slots_available]

    # ──────────────────────────────────────────────────────────
    #  ORDER EXECUTION
    # ──────────────────────────────────────────────────────────
    def open_position(self, pair_info: MarginPairInfo, side: str, volume: float) -> Optional[PennyTrade]:
        """Open a margin position."""
        leverages = pair_info.leverage_buy if side == "buy" else pair_info.leverage_sell
        if not leverages:
            logger.warning(f"No leverage available for {pair_info.pair} {side}")
            return None

        # Use lowest leverage for safety
        lev = min(leverages)
        price = pair_info.bid if side == "buy" else pair_info.ask

        logger.info(
            f"OPENING {side.upper()} {volume} {pair_info.base} "
            f"@ ${price:,.4f} ({lev}x leverage) on {pair_info.pair}"
        )

        try:
            result = self.client.place_margin_order(
                symbol=pair_info.pair,
                side=side,
                quantity=volume,
                leverage=lev,
                order_type="market",
            )

            if result.get("error"):
                logger.error(f"Order error for {pair_info.pair}: {result}")
                return None

            order_id = result.get("orderId", "unknown")
            trade_value = volume * price
            entry_fee = trade_value * KRAKEN_TAKER_FEE

            trade = PennyTrade(
                pair=pair_info.pair,
                side=side,
                volume=volume,
                entry_price=price,
                leverage=lev,
                entry_fee=entry_fee,
                entry_time=time.time(),
                order_id=order_id,
                cost=trade_value,
            )

            # Calculate breakeven (need to cover entry + exit fees + $0.01)
            total_fees = 2 * entry_fee  # Entry + exit fee estimate
            if side == "buy":
                trade.breakeven_price = price + (total_fees + PENNY_PROFIT_TARGET) / volume
            else:
                trade.breakeven_price = price - (total_fees + PENNY_PROFIT_TARGET) / volume

            self.active_trades[pair_info.pair] = trade
            self._save_state()

            logger.info(
                f"OPENED {pair_info.pair} {side.upper()} | "
                f"Entry: ${price:,.4f} | Breakeven: ${trade.breakeven_price:,.4f} | "
                f"Fees est: ${total_fees:.4f} | Order: {order_id}"
            )

            return trade

        except Exception as e:
            logger.error(f"Failed to open {pair_info.pair}: {e}")
            return None

    def close_position(self, pair: str, reason: str = "PENNY_PROFIT") -> Optional[dict]:
        """Close a margin position."""
        trade = self.active_trades.get(pair)
        if not trade:
            return None

        close_side = "sell" if trade.side == "buy" else "buy"

        logger.info(f"CLOSING {pair} ({reason}) — {close_side} {trade.volume}")

        try:
            result = self.client.close_margin_position(
                symbol=pair,
                side=close_side,
                volume=trade.volume,
                leverage=trade.leverage,
            )

            if result.get("error"):
                logger.error(f"Close error for {pair}: {result}")
                return None

            close_id = result.get("orderId", "unknown")
            logger.info(f"CLOSED {pair} | Order: {close_id} | Reason: {reason}")

            # Record the completed trade
            pair_info = self.margin_pairs.get(pair)
            exit_price = 0
            if pair_info:
                exit_price = pair_info.bid if close_side == "sell" else pair_info.ask

            completed = {
                "pair": pair,
                "side": trade.side,
                "volume": trade.volume,
                "entry_price": trade.entry_price,
                "exit_price": exit_price,
                "leverage": trade.leverage,
                "entry_fee": trade.entry_fee,
                "reason": reason,
                "entry_time": datetime.fromtimestamp(trade.entry_time).isoformat(),
                "exit_time": datetime.now().isoformat(),
                "order_id": trade.order_id,
                "close_order_id": close_id,
            }

            # Calculate actual P&L from Kraken's reported positions if available
            self.completed_trades.append(completed)
            del self.active_trades[pair]
            self._save_state()

            return completed

        except Exception as e:
            logger.error(f"Failed to close {pair}: {e}")
            return None

    # ──────────────────────────────────────────────────────────
    #  POSITION MONITORING — THE PENNY PROFIT CHECK
    # ──────────────────────────────────────────────────────────
    def monitor_positions(self) -> List[dict]:
        """
        Check all open margin positions. Close any that hit $0.01 profit.
        Returns list of closed trades.
        """
        if not self.active_trades:
            return []

        closed = []

        # Get actual open positions from Kraken
        try:
            kraken_positions = self.client.get_open_margin_positions(do_calcs=True)
        except Exception as e:
            logger.error(f"Could not fetch open positions: {e}")
            kraken_positions = []

        # Build map of Kraken positions by pair
        kraken_pos_map: Dict[str, dict] = {}
        for pos in kraken_positions:
            pair_key = pos.get("pair", "")
            # Map internal pair name to altname
            alt = self.client._int_to_alt.get(pair_key, pair_key)
            if alt not in kraken_pos_map:
                kraken_pos_map[alt] = pos
            # Also try the raw pair key
            if pair_key not in kraken_pos_map:
                kraken_pos_map[pair_key] = pos

        # Check margin health
        try:
            tb = self.client.get_trade_balance()
            margin_level = tb.get("margin_level", 0)
            free_margin = tb.get("free_margin", 0)
        except Exception:
            margin_level = 0
            free_margin = 0

        timestamp = datetime.now().strftime('%H:%M:%S')

        # Force close everything if margin is critical
        if margin_level > 0 and margin_level < LIQUIDATION_FORCE:
            logger.warning(
                f"CRITICAL: Margin level {margin_level:.1f}% — "
                f"force closing ALL positions!"
            )
            for pair in list(self.active_trades.keys()):
                result = self.close_position(pair, reason="LIQUIDATION_RISK")
                if result:
                    closed.append(result)
            return closed

        if margin_level > 0 and margin_level < LIQUIDATION_WARN:
            logger.warning(f"WARNING: Margin level {margin_level:.1f}% approaching danger")

        # Check each tracked trade
        for pair in list(self.active_trades.keys()):
            trade = self.active_trades.get(pair)
            if not trade:
                continue

            # Find matching Kraken position
            kpos = kraken_pos_map.get(pair)

            # Try to get current price
            pair_info = self.margin_pairs.get(pair)
            current_price = 0
            if pair_info:
                current_price = pair_info.bid if trade.side == "buy" else pair_info.ask
            if current_price <= 0:
                try:
                    ticker = self.client.get_ticker(pair)
                    current_price = ticker.get("bid" if trade.side == "buy" else "ask", 0)
                except Exception:
                    pass

            if current_price <= 0:
                continue

            # Calculate P&L
            if trade.side == "buy":
                gross_pnl = (current_price - trade.entry_price) * trade.volume
            else:
                gross_pnl = (trade.entry_price - current_price) * trade.volume

            # Use Kraken's reported unrealized P&L if available
            if kpos:
                kraken_pnl = kpos.get("unrealized_pnl", 0)
                if kraken_pnl != 0:
                    gross_pnl = kraken_pnl

            # Estimate exit fee
            exit_value = current_price * trade.volume
            exit_fee = exit_value * KRAKEN_TAKER_FEE
            total_fees = trade.entry_fee + exit_fee

            net_pnl = gross_pnl - total_fees

            # Status display
            if net_pnl >= PENNY_PROFIT_TARGET:
                status = f"PROFITABLE +${net_pnl:.4f}"
            elif gross_pnl > 0:
                status = f"GROSS+ but fees (net ${net_pnl:+.4f})"
            else:
                status = f"UNDERWATER ${net_pnl:+.4f}"

            logger.debug(
                f"[{timestamp}] {pair} {trade.side.upper()} | "
                f"Entry: ${trade.entry_price:,.4f} | Now: ${current_price:,.4f} | "
                f"Gross: ${gross_pnl:+.4f} | Fees: ${total_fees:.4f} | "
                f"Net: ${net_pnl:+.4f} | {status}"
            )

            # ═══════════════════════════════════════════════════
            #  THE PENNY PROFIT CHECK — close at $0.01 net profit
            # ═══════════════════════════════════════════════════
            if net_pnl >= MIN_PROFIT_USD:
                logger.info(
                    f"PENNY PROFIT HIT on {pair}! "
                    f"Net: ${net_pnl:+.4f} >= ${MIN_PROFIT_USD}"
                )
                result = self.close_position(pair, reason=f"PENNY_PROFIT (${net_pnl:+.4f})")
                if result:
                    result["net_pnl"] = net_pnl
                    self.total_profit += net_pnl
                    self.total_trades += 1
                    self.winning_trades += 1
                    closed.append(result)

        return closed

    # ──────────────────────────────────────────────────────────
    #  STATE PERSISTENCE
    # ──────────────────────────────────────────────────────────
    def _save_state(self):
        """Save active trades to disk."""
        try:
            state = {
                "active_trades": {k: v.to_dict() for k, v in self.active_trades.items()},
                "total_profit": self.total_profit,
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "last_updated": datetime.now().isoformat(),
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        """Load active trades from disk."""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE) as f:
                    state = json.load(f)

                for pair, data in state.get("active_trades", {}).items():
                    self.active_trades[pair] = PennyTrade(**data)

                self.total_profit = state.get("total_profit", 0)
                self.total_trades = state.get("total_trades", 0)
                self.winning_trades = state.get("winning_trades", 0)

                if self.active_trades:
                    logger.info(
                        f"Resumed {len(self.active_trades)} active trades | "
                        f"Session profit: ${self.total_profit:+.4f}"
                    )
        except Exception as e:
            logger.warning(f"Could not load state: {e}")

    def _save_results(self):
        """Save completed trades."""
        try:
            results = {
                "session_start": datetime.fromtimestamp(self.start_time).isoformat(),
                "session_end": datetime.now().isoformat(),
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "total_profit": self.total_profit,
                "completed_trades": self.completed_trades,
            }
            with open(RESULTS_FILE, 'w') as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    # ──────────────────────────────────────────────────────────
    #  DISPLAY
    # ──────────────────────────────────────────────────────────
    def print_universe(self):
        """Print all margin-eligible pairs."""
        print(f"\n{'=' * 80}")
        print(f"  KRAKEN MARGIN UNIVERSE — {len(self.margin_pairs)} USD PAIRS")
        print(f"{'=' * 80}")
        print(f"  {'Pair':<12} {'Base':<6} {'Price':>12} {'Spread':>8} "
              f"{'MaxLev':>7} {'MinOrder':>10} {'24h Vol':>14} {'Mom%':>8}")
        print(f"  {'-' * 75}")

        sorted_pairs = sorted(
            self.margin_pairs.values(),
            key=lambda x: x.volume_24h,
            reverse=True
        )

        for info in sorted_pairs:
            print(
                f"  {info.pair:<12} {info.base:<6} "
                f"${info.last_price:>11,.4f} "
                f"{info.spread_pct:>7.3f}% "
                f"{info.max_leverage:>5}x "
                f"{info.ordermin:>10.6f} "
                f"${info.volume_24h:>13,.0f} "
                f"{info.momentum:>+7.2f}%"
            )

        print(f"{'=' * 80}\n")

    def print_status(self):
        """Print current trading status."""
        runtime = time.time() - self.start_time
        hours = int(runtime // 3600)
        mins = int((runtime % 3600) // 60)

        print(f"\n{'─' * 60}")
        print(f"  PENNY PROFIT STATUS | Runtime: {hours}h {mins}m")
        print(f"  Active positions: {len(self.active_trades)}/{MAX_CONCURRENT_POSITIONS}")
        print(f"  Completed trades: {self.total_trades} "
              f"({self.winning_trades} wins)")
        print(f"  Session profit: ${self.total_profit:+.4f}")
        print(f"  Target per trade: ${PENNY_PROFIT_TARGET}")

        if self.active_trades:
            print(f"  {'─' * 55}")
            for pair, trade in self.active_trades.items():
                age_min = (time.time() - trade.entry_time) / 60
                print(
                    f"  {pair:<12} {trade.side.upper():<5} "
                    f"vol={trade.volume:.6f} @ ${trade.entry_price:,.4f} "
                    f"BE=${trade.breakeven_price:,.4f} "
                    f"({age_min:.0f}m ago)"
                )
        print(f"{'─' * 60}\n")

    # ──────────────────────────────────────────────────────────
    #  MAIN TRADING LOOP
    # ──────────────────────────────────────────────────────────
    def run(self, scan_only: bool = False):
        """Main trading loop."""
        mode = "DRY RUN" if self.dry_run else "LIVE"

        print("=" * 70)
        print(f"  KRAKEN MARGIN UNIVERSE — PENNY PROFIT TRADER")
        print(f"  Mode: {mode}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Profit target: ${PENNY_PROFIT_TARGET} per trade")
        print(f"  Max positions: {MAX_CONCURRENT_POSITIONS}")
        print(f"  Trade range: ${MIN_TRADE_USD}-${MAX_TRADE_USD}")
        print(f"  Stop loss: NONE (hold until profitable)")
        print("=" * 70)

        # Step 1: Discover all margin pairs
        self.discover_margin_universe()

        # Step 2: Get live prices
        self.refresh_prices()

        # Step 3: Display the universe
        self.print_universe()

        if scan_only:
            print("Scan-only mode. Exiting.")
            return

        # Step 4: Trading loop
        cycle = 0
        last_price_refresh = 0
        last_entry_scan = 0

        try:
            while True:
                cycle += 1
                now = time.time()

                # Refresh prices periodically
                if now - last_price_refresh > SCAN_INTERVAL * 4:
                    self.refresh_prices()
                    last_price_refresh = now
                else:
                    # Quick price update for active positions only
                    for pair in self.active_trades:
                        if pair in self.margin_pairs:
                            try:
                                ticker = self.client.get_ticker(pair)
                                if ticker and ticker.get("price", 0) > 0:
                                    self.margin_pairs[pair].last_price = ticker["price"]
                                    self.margin_pairs[pair].bid = ticker.get("bid", ticker["price"])
                                    self.margin_pairs[pair].ask = ticker.get("ask", ticker["price"])
                            except Exception:
                                pass
                            time.sleep(0.3)

                # Monitor existing positions (THE PENNY CHECK)
                closed = self.monitor_positions()
                for c in closed:
                    pnl = c.get("net_pnl", 0)
                    logger.info(
                        f"TRADE COMPLETED: {c['pair']} {c['side'].upper()} | "
                        f"Net P&L: ${pnl:+.4f} | Reason: {c['reason']}"
                    )

                # Look for new entries periodically
                if now - last_entry_scan > SCAN_INTERVAL:
                    opportunities = self.find_trade_opportunities()
                    if opportunities:
                        logger.info(f"Found {len(opportunities)} trade opportunities")
                        for pair_info, side, vol, trade_val in opportunities:
                            trade = self.open_position(pair_info, side, vol)
                            if trade:
                                # Brief pause between orders
                                time.sleep(2)
                    last_entry_scan = now

                # Status display every 10 cycles
                if cycle % 10 == 0:
                    self.print_status()

                # Save results periodically
                if cycle % 30 == 0:
                    self._save_results()

                time.sleep(POSITION_CHECK_INTERVAL)

        except KeyboardInterrupt:
            print(f"\nTrader stopped by user.")
            self.print_status()
            self._save_state()
            self._save_results()


def main():
    global MAX_CONCURRENT_POSITIONS, MAX_TRADE_USD, PENNY_PROFIT_TARGET, MIN_PROFIT_USD

    parser = argparse.ArgumentParser(
        description="Kraken Margin Universe Penny Profit Trader"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run in simulation mode (no real orders)"
    )
    parser.add_argument(
        "--scan-only", action="store_true",
        help="Only scan and display margin pairs, don't trade"
    )
    parser.add_argument(
        "--max-positions", type=int, default=MAX_CONCURRENT_POSITIONS,
        help=f"Maximum concurrent positions (default: {MAX_CONCURRENT_POSITIONS})"
    )
    parser.add_argument(
        "--max-trade", type=float, default=MAX_TRADE_USD,
        help=f"Maximum trade size in USD (default: {MAX_TRADE_USD})"
    )
    parser.add_argument(
        "--profit-target", type=float, default=PENNY_PROFIT_TARGET,
        help=f"Profit target in USD (default: {PENNY_PROFIT_TARGET})"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Verbose logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Apply overrides
    MAX_CONCURRENT_POSITIONS = args.max_positions
    MAX_TRADE_USD = args.max_trade
    PENNY_PROFIT_TARGET = args.profit_target
    MIN_PROFIT_USD = args.profit_target

    trader = KrakenMarginPennyTrader(dry_run=args.dry_run)
    trader.run(scan_only=args.scan_only)


if __name__ == "__main__":
    main()
