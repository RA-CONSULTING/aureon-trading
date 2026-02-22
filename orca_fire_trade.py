#!/usr/bin/env python3
"""
🔥 ORCA FIRE TRADE - REAL EXECUTION ONLY
No smoke. Just fire.

This script makes REAL trades immediately.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ─── Seer Integration (Third Pillar) ───
_seer_available = False
try:
    from aureon_seer import get_seer, SeerVision
    _seer_available = True
except ImportError:
    pass

def log_fire(msg):
    print(f"🔥 [FIRE] {msg}")

def log_result(msg):
    print(f"💥 [RESULT] {msg}")

class FireTrader:
    """Manual/Direct execution logic wrapper"""
    
    def __init__(self, kraken_client=None, binance_client=None):
        try:
            from kraken_client import KrakenClient, get_kraken_client
            from binance_client import BinanceClient, get_binance_client
            self.kraken = kraken_client if kraken_client else get_kraken_client()
            self.binance = binance_client if binance_client else BinanceClient()
        except ImportError:
            log_fire("⚠️ Clients not available")
            self.kraken = None
            self.binance = None

    def _record_buy_cost_basis(self, pair, order, exchange):
        """Record cost basis after a successful buy so we can sell at profit later."""
        try:
            fill_price = float(order.get('price', 0) or order.get('avgPrice', 0) or 0)
            fill_qty = float(order.get('executedQty', 0) or order.get('filledQty', 0) or 0)
            order_id = order.get('orderId', order.get('order_id', ''))
            
            # Binance market orders have price=0; get real price from fills or cummulativeQuoteQty
            if fill_price <= 0:
                fills = order.get('fills', [])
                if fills:
                    fill_price = float(fills[0].get('price', 0) or 0)
            if fill_price <= 0 and fill_qty > 0:
                cum_quote = float(order.get('cummulativeQuoteQty', 0) or 0)
                if cum_quote > 0:
                    fill_price = cum_quote / fill_qty
            
            if fill_price <= 0 or fill_qty <= 0:
                log_fire(f"   ⚠️ Cannot record cost basis: price={fill_price}, qty={fill_qty}")
                return
            
            # Calculate fee
            fee_rate = 0.0026 if exchange == 'kraken' else 0.001
            fee = fill_price * fill_qty * fee_rate
            
            # Record in cost_basis_history.json
            from cost_basis_tracker import CostBasisTracker
            tracker = CostBasisTracker()
            tracker.set_entry_price(pair, fill_price, fill_qty, exchange, fee, str(order_id))
            
            # Also record in tracked_positions.json
            try:
                tp_file = 'tracked_positions.json'
                tp = {}
                if os.path.exists(tp_file):
                    with open(tp_file, 'r') as f:
                        tp = json.load(f)
                tp[pair] = {
                    'symbol': pair,
                    'exchange': exchange,
                    'entry_price': fill_price,
                    'buy_price': fill_price,
                    'entry_qty': fill_qty,
                    'quantity': fill_qty,
                    'entry_cost': fill_price * fill_qty + fee,
                    'entry_fee': fee,
                    'breakeven_price': fill_price * (1 + fee_rate * 2),  # buy + sell fee
                    'buy_timestamp': datetime.now().isoformat(),
                    'source': 'fire_trade',
                    'auto_tracked': False,
                }
                import tempfile
                tmp = tp_file + '.tmp'
                with open(tmp, 'w') as f:
                    json.dump(tp, f, indent=4)
                os.replace(tmp, tp_file)
                log_fire(f"   💾 Cost basis recorded: {exchange}:{pair} @ ${fill_price:.6f} x {fill_qty:.6f}")
            except Exception as e:
                log_fire(f"   ⚠️ Failed to update tracked_positions: {e}")
        except Exception as e:
            log_fire(f"   ⚠️ Failed to record cost basis: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # SEER INTEGRATION — The Third Pillar gates every buy
    # ═══════════════════════════════════════════════════════════════════

    def _seer_global_gate(self):
        """
        Consult the Seer before ANY buying.
        Returns (should_buy: bool, risk_mod: float, vision_summary: dict).
        """
        if not _seer_available:
            log_fire("   [SEER] Not available — proceeding without gate")
            return True, 1.0, {"status": "unavailable"}

        try:
            seer = get_seer()
            vision = seer.see()
            grade = vision.grade
            action = vision.action
            risk_mod = vision.risk_modifier
            score = vision.unified_score

            summary = {
                "timestamp": datetime.now().isoformat(),
                "unified_score": round(score, 4),
                "grade": grade,
                "action": action,
                "risk_modifier": round(risk_mod, 3),
                "tactical_mode": vision.tactical_mode,
                "prophecy": vision.prophecy[:200] if vision.prophecy else "",
            }

            log_fire(f"\n🔮 SEER VISION: score={score:.3f} grade={grade} action={action} risk_mod={risk_mod:.2f}")
            log_fire(f"   Tactical: {vision.tactical_mode}")
            if vision.prophecy:
                log_fire(f"   Prophecy: {vision.prophecy[:150]}")

            # GATE: Block buys on BLIND, FOG, or DEFEND/SELL_BIAS
            if grade in ("BLIND",):
                log_fire("   🚫 SEER SAYS BLIND — no visibility, blocking ALL buys")
                return False, risk_mod, summary
            if action in ("DEFEND",):
                log_fire("   🛡️ SEER SAYS DEFEND — minimal exposure, blocking buys")
                return False, risk_mod, summary
            if action in ("SELL_BIAS",):
                log_fire("   ⚠️ SEER SAYS SELL_BIAS — not ideal for new entries, blocking buys")
                return False, risk_mod, summary
            if grade in ("FOG",):
                log_fire("   🌫️ SEER SEES FOG — reducing position sizes only")
                return True, risk_mod * 0.5, summary

            # CLEAR_SIGHT or DIVINE_CLARITY + BUY_BIAS/HOLD = green light
            log_fire(f"   ✅ SEER APPROVES entry (grade={grade}, action={action})")
            return True, risk_mod, summary

        except Exception as e:
            log_fire(f"   [SEER] Error consulting: {e} — proceeding cautiously")
            return True, 0.8, {"status": "error", "error": str(e)}

    def _seer_symbol_signal(self, base_asset: str):
        """
        Per-symbol directional signal using 1h candles from Binance public API.
        Returns (bullish: bool, confidence: float, details: dict).

        Checks:
        1. Last 6 hourly candles — are closes trending up?
        2. Price position in 24h range — near lows = better entry
        3. Volume trend — increasing = conviction
        """
        symbol = f"{base_asset}USDT"  # Use USDT pair for data (most liquid)
        details = {"symbol": symbol, "source": "binance_public_klines"}

        try:
            resp = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": symbol, "interval": "1h", "limit": 12},
                timeout=5
            )
            if resp.status_code != 200:
                log_fire(f"   [SEER-SYM] Kline fetch failed for {symbol}: HTTP {resp.status_code}")
                return True, 0.5, details  # Don't block on data failure

            candles = resp.json()
            if len(candles) < 6:
                return True, 0.5, details

            # Parse candles: [timestamp, open, high, low, close, volume, ...]
            closes = [float(c[4]) for c in candles]
            opens = [float(c[1]) for c in candles]
            highs = [float(c[2]) for c in candles]
            lows = [float(c[3]) for c in candles]
            volumes = [float(c[5]) for c in candles]

            current_price = closes[-1]
            high_24h = max(highs)
            low_24h = min(lows)
            price_range = high_24h - low_24h if high_24h > low_24h else 1

            # ── Signal 1: Short-term trend (last 6 candles) ──
            recent = candles[-6:]
            bullish_candles = sum(1 for c in recent if float(c[4]) > float(c[1]))
            trend_score = bullish_candles / 6.0

            # ── Signal 2: Price momentum (last 3h vs prior 3h) ──
            avg_recent_3 = sum(closes[-3:]) / 3
            avg_prior_3 = sum(closes[-6:-3]) / 3
            momentum_pct = ((avg_recent_3 - avg_prior_3) / avg_prior_3) * 100 if avg_prior_3 > 0 else 0

            # ── Signal 3: Position in 24h range (0.0 = at low, 1.0 = at high) ──
            range_position = (current_price - low_24h) / price_range

            # ── Signal 4: Volume trend (recent vs prior) ──
            vol_recent = sum(volumes[-3:])
            vol_prior = sum(volumes[-6:-3])
            vol_ratio = vol_recent / vol_prior if vol_prior > 0 else 1.0

            # ── Combined directional score ──
            momentum_signal = min(1.0, max(0.0, 0.5 + momentum_pct / 4))
            range_signal = 1.0 - range_position  # Near low = high signal
            vol_signal = min(1.0, max(0.0, 0.3 + vol_ratio * 0.35))

            direction_score = (
                trend_score * 0.35 +
                momentum_signal * 0.30 +
                range_signal * 0.15 +
                vol_signal * 0.20
            )

            confidence = min(1.0, len(candles) / 12.0)
            bullish = direction_score > 0.45

            details.update({
                "current_price": round(current_price, 6),
                "trend_score": round(trend_score, 3),
                "bullish_candles_6h": bullish_candles,
                "momentum_pct": round(momentum_pct, 4),
                "range_position": round(range_position, 3),
                "vol_ratio": round(vol_ratio, 3),
                "direction_score": round(direction_score, 4),
                "bullish": bullish,
                "confidence": round(confidence, 3),
            })

            direction = "BULLISH" if bullish else "BEARISH"
            log_fire(f"   [SEER-SYM] {base_asset}: {direction} dir={direction_score:.3f} "
                     f"trend={trend_score:.2f} mom={momentum_pct:+.2f}% "
                     f"range={range_position:.2f} vol={vol_ratio:.2f}")

            return bullish, confidence, details

        except Exception as e:
            log_fire(f"   [SEER-SYM] Error for {base_asset}: {e}")
            return True, 0.3, {"error": str(e)}

    # Timeframe layers — every prediction is validated at ALL these horizons
    _TIMEFRAME_LAYERS = [
        ("1m",    60),
        ("5m",    300),
        ("30m",   1_800),
        ("1h",    3_600),
        ("2h",    7_200),
        ("3h",    10_800),
        ("6h",    21_600),
        ("12h",   43_200),
        ("24h",   86_400),
        ("48h",   172_800),
        ("1w",    604_800),
        ("2w",    1_209_600),
        ("1mo",   2_592_000),
        ("3mo",   7_776_000),
        ("6mo",   15_552_000),
        ("1y",    31_536_000),
    ]

    def _log_seer_prediction(self, pair, exchange, buy_price, seer_summary, symbol_signal):
        """Record the Seer's prediction at time of trade for later validation.
        Embeds a layered timeline: 1m → 5m → 30m → 1h … → 1y.
        Each layer is validated independently as its horizon matures.
        """
        try:
            import time as _t
            now_ts = _t.time()
            is_bullish = symbol_signal.get("bullish", True) if symbol_signal else True

            timeframe_layers = [
                {
                    "label":       label,
                    "seconds":     secs,
                    "validate_at": now_ts + secs,       # epoch when to check
                    "is_bullish":  is_bullish,
                    "validated":   False,
                    "outcome":     None,                 # HIT / MISS / NEUTRAL
                    "price_at":    None,
                    "pct_change":  None,
                }
                for label, secs in self._TIMEFRAME_LAYERS
            ]

            prediction = {
                "timestamp": datetime.now().isoformat(),
                "pair": pair,
                "exchange": exchange,
                "buy_price": buy_price,
                "seer_global": seer_summary,
                "symbol_signal": symbol_signal,
                "validated": False,          # True when ALL layers done
                "outcome": None,             # overall (last validated layer)
                "timeframe_layers": timeframe_layers,
            }
            log_path = "seer_trade_predictions.jsonl"
            with open(log_path, "a") as f:
                f.write(json.dumps(prediction) + "\n")
            log_fire(f"   📝 Seer prediction logged for {exchange}:{pair} "
                     f"(16 timeframe layers: 1m → 1y)")
        except Exception as e:
            log_fire(f"   ⚠️ Failed to log prediction: {e}")

    def _validate_seer_predictions(self, sold_pair, sold_exchange, sell_price):
        """
        When a sell executes, validate the Seer's prediction at buy time.
        Closes the feedback loop so we know if the Seer was right.
        """
        log_path = "seer_trade_predictions.jsonl"
        validated_path = "seer_validated_predictions.jsonl"
        if not os.path.exists(log_path):
            return

        try:
            remaining = []
            validated = []
            with open(log_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        pred = json.loads(line)
                    except json.JSONDecodeError:
                        remaining.append(line)
                        continue

                    # Match by pair + exchange
                    if (pred.get("pair") == sold_pair and
                        pred.get("exchange") == sold_exchange and
                        not pred.get("validated")):
                        # Validate: was the prediction correct?
                        buy_price = pred.get("buy_price", 0)
                        if buy_price > 0 and sell_price > 0:
                            profit_pct = ((sell_price - buy_price) / buy_price) * 100
                            was_profitable = profit_pct > 0
                            pred["validated"] = True
                            pred["outcome"] = {
                                "sell_price": sell_price,
                                "profit_pct": round(profit_pct, 4),
                                "was_profitable": was_profitable,
                                "validated_at": datetime.now().isoformat(),
                            }
                            validated.append(pred)
                            direction = pred.get("symbol_signal", {}).get("direction_score", 0)
                            log_fire(f"   📊 SEER VALIDATION: {sold_exchange}:{sold_pair} "
                                     f"profit={profit_pct:+.2f}% | Seer said dir={direction:.3f} | "
                                     f"{'✅ CORRECT' if was_profitable else '❌ WRONG'}")
                        else:
                            remaining.append(json.dumps(pred))
                    else:
                        remaining.append(json.dumps(pred))

            # Write back unvalidated predictions
            with open(log_path, "w") as f:
                for line in remaining:
                    f.write(line + "\n")

            # Append validated predictions to history
            if validated:
                with open(validated_path, "a") as f:
                    for pred in validated:
                        f.write(json.dumps(pred) + "\n")

        except Exception as e:
            log_fire(f"   ⚠️ Seer validation error: {e}")

    def run_fire_check(self):
        """Run the fire trade logic using SHARED clients."""
        log_fire("=" * 50)
        log_fire("   ORCA FIRE TRADE - REAL EXECUTION")
        log_fire("=" * 50)

        if not self.kraken or not self.binance:
            log_fire("⚠️ Clients not initialized")
            return False

        sell_executed = False  # track whether any sell fired this cycle

        # Check what we have
        log_fire("\n📊 CHECKING REAL BALANCES...")
        
        # Kraken balances
        log_fire("\n🐙 KRAKEN:")
        tradeable_kraken = {}
        kraken_cash = 0.0
        kraken_usd_cash = 0.0
        kraken_usdc_cash = 0.0
        kraken_gbp_cash = 0.0   # ZGBP balance in GBP
        kraken_tusd_cash = 0.0  # TUSD balance
        GBP_TO_USD = 1.27       # approximate conversion for cash comparison
        try:
            k_balances = self.kraken.get_balance()
            for asset, amt in k_balances.items():
                amt = float(amt)
                if amt > 0:
                    log_fire(f"   {asset}: {amt}")
                    if asset in ['USD', 'ZUSD', 'USDC', 'USDT', 'TUSD']:
                        kraken_cash += amt
                    if asset in ['USD', 'ZUSD']:
                        kraken_usd_cash += amt
                    if asset == 'USDC':
                        kraken_usdc_cash += amt
                    if asset == 'TUSD':
                        kraken_tusd_cash += amt  # kraken_cash already incremented above
                    if asset == 'ZGBP':
                        kraken_gbp_cash += amt
                        kraken_cash += amt * GBP_TO_USD  # count as USD equivalent
                        log_fire(f"   ZGBP → ~${amt * GBP_TO_USD:.2f} USD equivalent")
                    if asset not in ['USD', 'ZUSD', 'ZGBP', 'USDC', 'USDT', 'TUSD']:
                        tradeable_kraken[asset] = amt
        except Exception as e:
            log_fire(f"   Error: {e}")
        
        # Binance balances
        log_fire("\n🟡 BINANCE:")
        tradeable_binance = {}
        binance_cash = 0.0
        try:
            b_balances = self.binance.get_balance()
            for asset, amt in b_balances.items():
                amt = float(amt)
                if amt > 0:
                    if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD', 'TUSD']:
                        binance_cash += amt
                    # Skip stablecoins and LD* (Binance Simple Earn/Locked) - not spot tradeable
                    if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD', 'TUSD'] or asset.startswith('LD'):
                        continue
                    log_fire(f"   {asset}: {amt}")
                    tradeable_binance[asset] = amt
        except Exception as e:
            log_fire(f"   Error: {e}")
        
        # Get prices and find ALL profitable opportunities
        log_fire("\n🔍 SCANNING BINANCE FOR ALL PROFITABLE POSITIONS (any real gain after fees)...")
        profitable_sells = []
        
        for asset, qty in tradeable_binance.items():
            try:
                # UK accounts: use USDC pairs only
                symbol = f"{asset}USDC"
                ticker = self.binance.get_24h_ticker(symbol)
                if not ticker:
                    continue

                price = float(ticker.get('lastPrice', 0))
                change = float(ticker.get('priceChangePercent', 0))
                value = qty * price

                if value <= 1:
                    continue

                # Check cost basis for profit calculation
                cost_basis = None
                try:
                    with open('cost_basis_history.json', 'r') as f:
                        cb_data = json.load(f)
                        positions_dict = cb_data.get('positions', {})
                        for try_key in (f"binance:{symbol}", f"binance:{asset}", f"binance:{asset}USDC", f"binance:{asset}USDT"):
                            if try_key in positions_dict:
                                entry = positions_dict[try_key]
                                cost_basis = float(entry.get('avg_entry_price', 0) or entry.get('avg_fill_price', 0) or 0)
                                if cost_basis > 0:
                                    break
                except Exception:
                    pass

                fee_rate = 0.001  # 0.1% Binance taker fee
                net_price = price * (1 - fee_rate)
                entry_ref = cost_basis if cost_basis and cost_basis > 0 else price
                profit_margin = ((net_price - entry_ref) / entry_ref) * 100 if entry_ref > 0 else 0

                log_fire(f"   [DEBUG] Binance {asset}: qty={qty:.4f}, price=${price:.4f}, "
                         f"cost_basis=${cost_basis or 0:.4f}, profit={profit_margin:+.2f}%, "
                         f"24h={change:+.1f}%")

                # ANY positive gain after fees is worth taking (user policy: take all real gains)
                if profit_margin > 0.0 and change > -2.0:
                    profitable_sells.append({
                        'asset': asset,
                        'symbol': symbol,
                        'qty': qty,
                        'price': price,
                        'value': value,
                        'change': change,
                        'profit_margin': profit_margin
                    })
            except Exception as e:
                log_fire(f"   [DEBUG] Binance {asset}: error while evaluating sell opportunity - {e}")

        # Sell ALL profitable positions (not just the best one) — take every real gain
        profitable_sells.sort(key=lambda x: -x['profit_margin'])
        for best_sell in profitable_sells:
            log_fire(f"\n🎯 PROFIT OPPORTUNITY (Binance): {best_sell['asset']} +{best_sell['profit_margin']:.2f}%")
            # Sell 100% if position is small (avoids min_notional rejection on partial sells)
            # Sell 50% if position is large enough that half still clears $5 notional
            half_value = best_sell['value'] * 0.5
            if half_value < 6.0:
                sell_qty = best_sell['qty']  # sell 100% — position too small to split
                log_fire(f"   Selling 100% (${best_sell['value']:.2f} — too small to split)")
            else:
                sell_qty = best_sell['qty'] * 0.5
                log_fire(f"   Selling 50% to lock +{best_sell['profit_margin']:.2f}% profit")
            try:
                order = self.binance.place_market_order(best_sell['symbol'], 'sell', sell_qty)
                log_result(f"SELL ORDER RESULT: {json.dumps(order, indent=2) if order else 'None'}")
                if order and order.get('status') == 'FILLED':
                    log_fire(f"💥💥💥 BINANCE SELL FILLED! +{best_sell['profit_margin']:.2f}% 💥💥💥")
                    with open('orca_real_trades.json', 'a') as f:
                        f.write(json.dumps({
                            'timestamp': datetime.now().isoformat(),
                            'exchange': 'binance',
                            'symbol': best_sell['symbol'],
                            'side': 'SELL',
                            'qty': sell_qty,
                            'price': best_sell['price'],
                            'value': best_sell['value'],
                            'profit_margin': best_sell['profit_margin'],
                            'order': order
                        }) + '\n')
                    self._validate_seer_predictions(best_sell['symbol'], 'binance', best_sell['price'])
                    sell_executed = True
                else:
                    log_fire(f"❌ Binance sell not filled: {order}")
            except Exception as e:
                log_fire(f"❌ Binance sell failed ({best_sell['symbol']}): {e}")
        if not profitable_sells:
            log_fire("   [DEBUG] Binance: no profitable positions to sell")

        log_fire("\n🔍 Scanning Kraken for profit opportunities...")
        
        for asset, qty in tradeable_kraken.items():
            if qty <= 0:
                continue
                
            # Get current price and check if profitable
            try:
                pair = f"{asset}USD"
                ticker24 = self.kraken.get_24h_ticker(pair)
                if ticker24 and ticker24.get('lastPrice'):
                    price = float(ticker24.get('lastPrice', 0) or 0)
                    change_24h = float(ticker24.get('priceChangePercent', 0) or 0)
                    quote_vol = float(ticker24.get('quoteVolume', 0) or 0)
                else:
                    ticker = self.kraken.get_ticker(pair)
                    if not ticker or not ticker.get('price'):
                        continue
                    price = float(ticker['price'])
                    change_24h = 0.0
                    quote_vol = 0.0

                if price <= 0:
                    continue

                value = qty * price
                
                if value < 5:  # Skip small positions
                    continue

                log_fire(
                    f"   [DEBUG] Kraken {asset}: qty={qty:.4f}, price=${price:.4f}, "
                    f"24h_change={change_24h:+.2f}%, vol=${quote_vol:,.0f}"
                )

                # Load cost basis to ensure we're not selling at a loss
                cost_basis = None
                try:
                    with open('cost_basis_history.json', 'r') as f:
                        cb_data = json.load(f)
                        positions_dict = cb_data.get('positions', {})
                        # Try multiple key formats: kraken:ADAUSD, kraken:ADA, kraken:ADAUSDC
                        for try_key in (f"kraken:{pair}", f"kraken:{asset}", f"kraken:{asset}USD", f"kraken:{asset}USDC"):
                            if try_key in positions_dict:
                                entry = positions_dict[try_key]
                                cost_basis = float(entry.get('avg_entry_price', 0) or entry.get('avg_fill_price', 0) or 0)
                                if cost_basis > 0:
                                    break
                except Exception:
                    pass
                
                # Calculate profit margin including 0.26% taker fee
                fee_rate = 0.0026
                net_price = price * (1 - fee_rate)
                entry_ref = cost_basis if cost_basis is not None else price
                profit_margin = ((net_price - entry_ref) / entry_ref) * 100 if entry_ref > 0 else 0

                cost_basis_dbg = f"{cost_basis:.4f}" if cost_basis is not None else "0.0000"
                log_fire(f"   [DEBUG] Kraken {asset}: cost_basis=${cost_basis_dbg}, net_after_fees=${net_price:.4f}, profit_margin={profit_margin:.2f}%")

                # ANY positive gain after fees (user policy: take all real gains, never sell at a loss)
                if profit_margin > 0.0 and change_24h > -2.0:
                    log_fire(f"   📈 {asset}: ${value:.2f} @ ${price:.4f} (24h {change_24h:+.2f}%, +{profit_margin:.2f}% profit)")
                    
                    log_fire(f"\n🎯 PROFIT OPPORTUNITY: {asset}")
                    # Sell 100% if small (avoids min_notional); 50% if large
                    half_value = value * 0.5
                    if half_value < 6.0:
                        sell_qty = qty  # 100% — position too small to split safely
                        log_fire(f"   Selling 100% (${value:.2f} — too small to split)")
                    else:
                        sell_qty = qty * 0.5
                        log_fire(f"   Selling 50% to lock +{profit_margin:.2f}% profit")
                    
                    log_fire(f"\n⚡ EXECUTING SELL: {sell_qty} {asset}...")
                    
                    # Use self.kraken to place order
                    order = self.kraken.place_market_order(pair, 'sell', sell_qty)
                    log_result(f"ORDER RESULT: {json.dumps(order, indent=2) if order else 'None'}")
                    
                    if order and order.get('status') == 'FILLED':
                        received = float(order.get('receivedQty', 0))
                        log_fire(f"💥💥💥 TRADE FILLED! 💥💥💥")
                        log_fire(f"   Received: ${received:.2f}")
                        
                        # Log to file
                        with open('orca_real_trades.json', 'a') as f:
                            f.write(json.dumps({
                                'timestamp': datetime.now().isoformat(),
                                'exchange': 'kraken',
                                'symbol': pair,
                                'side': 'SELL',
                                'qty': sell_qty,
                                'price': price,
                                'value': value,
                                'order': order
                            }) + '\n')
                        # Validate Seer prediction for this sell
                        self._validate_seer_predictions(pair, 'kraken', price)
                        sell_executed = True  # continue to buy phase instead of early-exit
                        break  # one sell per cycle is enough
                    else:
                        log_fire(f"❌ Order not filled: {order}")
                        
            except Exception as e:
                log_fire(f"   [DEBUG] Kraken {asset}: error while checking profit - {e}")
        
        if not sell_executed:
            log_fire("\n⚠️ No profitable positions to sell")
        else:
            log_fire("\n✅ Sell(s) executed — proceeding to buy phase with available cash")

        # -----------------------------------------------------------------
        # BUY PHASE: always runs after sell scan so cash (e.g. ZGBP/TUSD)
        # gets deployed in the same cycle that a sell fires.
        # -----------------------------------------------------------------
        total_cash = kraken_cash + binance_cash
        if total_cash < 1.0:
            log_fire("   [DEBUG] Buy phase skipped: insufficient total cash")
            return sell_executed

        log_fire("\n🛒 Scanning for BUY opportunities with available cash...")
        log_fire(f"   [DEBUG] Cash available: Kraken=${kraken_cash:.2f}, Binance=${binance_cash:.2f}")

        # ═══════ SEER GLOBAL GATE — Third Pillar must approve ═══════
        seer_ok, seer_risk_mod, seer_summary = self._seer_global_gate()
        if not seer_ok:
            log_fire("🚫 SEER BLOCKED all buys — waiting for better conditions")
            return sell_executed

        bought_any = False

        # Prefer Kraken if it has more cash (current setup often has Kraken USDC)
        prefer_kraken = kraken_cash >= binance_cash and self.kraken is not None

        # Deploy 85% of funded exchange cash, capped at $20, minimum $5
        # Higher deployment rate to maximize position size per trade
        def _buy_amount(cash_amt: float) -> float:
            return max(5.0, min(20.0, cash_amt * 0.85))

        # ─────────────────────────────────────────────────────────────────
        # KRAKEN BUY — Full dynamic universe: discover ALL pairs from the
        # exchange API for each funded quote currency (GBP / USDC / USD /
        # TUSD). No hardcoded asset list — uses get_available_pairs().
        # ─────────────────────────────────────────────────────────────────
        if prefer_kraken and kraken_cash >= 1.0:
            buy_candidates = []  # ranked list: try each in order on failure

            kraken_quote_map = []  # [(pair_altname, quote_ccy), ...]
            try:
                if kraken_gbp_cash >= 4.0:
                    gbp_pairs = self.kraken.get_available_pairs(quote='GBP')
                    kraken_quote_map += [(p['pair'] if isinstance(p, dict) else p, 'GBP') for p in gbp_pairs]
                if kraken_usdc_cash >= 1.0:
                    usdc_pairs = self.kraken.get_available_pairs(quote='USDC')
                    kraken_quote_map += [(p['pair'] if isinstance(p, dict) else p, 'USDC') for p in usdc_pairs]
                if kraken_usd_cash >= 1.0:
                    usd_pairs = self.kraken.get_available_pairs(quote='USD')
                    kraken_quote_map += [(p['pair'] if isinstance(p, dict) else p, 'USD') for p in usd_pairs]
                if kraken_tusd_cash >= 1.0:
                    tusd_pairs = self.kraken.get_available_pairs(quote='TUSD')
                    kraken_quote_map += [(p['pair'] if isinstance(p, dict) else p, 'TUSD') for p in tusd_pairs]
            except Exception as e:
                log_fire(f"   [WARN] Kraken pair discovery failed: {e} — using safe fallback")
                if kraken_gbp_cash >= 4.0:
                    kraken_quote_map += [("XBTGBP", 'GBP'), ("ETHGBP", 'GBP'), ("SOLGBP", 'GBP'),
                                         ("ADAGBP", 'GBP'), ("XRPGBP", 'GBP'), ("AVAXGBP", 'GBP')]
                if kraken_usdc_cash >= 1.0:
                    kraken_quote_map += [("BTCUSDC", 'USDC'), ("ETHUSDC", 'USDC'), ("SOLUSDC", 'USDC')]
                if kraken_usd_cash >= 1.0:
                    kraken_quote_map += [("XBTUSD", 'USD'), ("ETHUSD", 'USD'), ("SOLUSD", 'USD')]

            # Deduplicate while preserving order
            seen_kp = set()
            kraken_unique = []
            for pair, qccy in kraken_quote_map:
                if pair and pair not in seen_kp:
                    seen_kp.add(pair)
                    kraken_unique.append((pair, qccy))

            log_fire(f"   [SCAN] Kraken: fetching tickers for {len(kraken_unique)} pairs across funded quote currencies")

            for pair, quote_ccy in kraken_unique:
                try:
                    ticker24 = self.kraken.get_24h_ticker(pair)
                    if not ticker24:
                        continue
                    price = float(ticker24.get('lastPrice', 0) or 0)
                    change_24h = float(ticker24.get('priceChangePercent', 0) or 0)
                    quote_vol = float(ticker24.get('quoteVolume', 0) or 0)
                    if price <= 0 or quote_vol < 5000:
                        continue
                    score = change_24h + min(quote_vol / 1_000_000, 5)
                    buy_candidates.append({
                        'pair': pair, 'price': price, 'change_24h': change_24h,
                        'quote_vol': quote_vol, 'score': score, 'quote_ccy': quote_ccy,
                    })
                except Exception:
                    continue

            # Rank descending by score; test top 8 through SEER, execute first approved
            buy_candidates.sort(key=lambda x: -x['score'])
            log_fire(f"   [SCAN] Kraken: {len(buy_candidates)} liquid pairs found, testing top 8 with SEER")

            for candidate in buy_candidates[:8]:
                # ═══ SEER PER-SYMBOL CHECK ═══
                base_for_seer = (candidate['pair']
                    .replace('USDC', '').replace('TUSD', '').replace('ZGBP', '')
                    .replace('GBP', '').replace('ZUSD', '').replace('USD', '').lstrip('X'))
                if base_for_seer in ('XBT', 'XXBT', 'BT', ''):
                    base_for_seer = 'BTC'
                sym_bullish, sym_conf, sym_details = self._seer_symbol_signal(base_for_seer)
                if not sym_bullish:
                    log_fire(f"   🔮 SEER rejects {base_for_seer} — BEARISH, trying next")
                    continue

                qccy = candidate['quote_ccy']
                funded_cash = (kraken_gbp_cash if qccy == 'GBP'
                               else kraken_usdc_cash if qccy == 'USDC'
                               else kraken_tusd_cash if qccy == 'TUSD'
                               else kraken_usd_cash)
                raw_qty = _buy_amount(funded_cash)
                quote_qty = max(5.0, min(raw_qty * seer_risk_mod, funded_cash * 0.9))
                log_fire(f"\n🎯 BUY OPPORTUNITY (Kraken): {candidate['pair']}")
                log_fire(f"   Price=${candidate['price']:.6f} | 24h={candidate['change_24h']:+.2f}% | Vol=${candidate['quote_vol']:.0f}")
                log_fire(f"   Seer risk_mod={seer_risk_mod:.2f} → qty={quote_qty:.2f} {qccy}")
                try:
                    order = self.kraken.place_market_order(candidate['pair'], 'buy', quote_qty=quote_qty)
                    log_result(f"BUY ORDER RESULT: {json.dumps(order, indent=2) if order else 'None'}")
                    if order and not order.get('error') and not order.get('rejected'):
                        log_fire("💥 BUY EXECUTED (Kraken)")
                        self._record_buy_cost_basis(candidate['pair'], order, 'kraken')
                        self._log_seer_prediction(candidate['pair'], 'kraken', candidate['price'], seer_summary, sym_details)
                        bought_any = True
                        break
                    else:
                        log_fire(f"❌ Not filled: {order} — trying next")
                except Exception as e:
                    log_fire(f"❌ Kraken buy failed ({candidate['pair']}): {e} — trying next")

        # ─────────────────────────────────────────────────────────────────
        # BINANCE BUY — Full UK universe: all 521 UK-FCA-allowed USDC pairs.
        # Uses get_24h_tickers() (one API call for ALL pairs) filtered by
        # get_allowed_pairs_uk() — no hardcoded watchlist.
        # ─────────────────────────────────────────────────────────────────
        if self.binance is not None and binance_cash >= 1.0:
            buy_candidates = []
            try:
                uk_allowed = self.binance.get_allowed_pairs_uk()   # 521 pairs, 1hr cache
                all_tickers = self.binance.get_24h_tickers()       # ALL pairs, single call
                log_fire(f"   [SCAN] Binance: {len(all_tickers)} total tickers, {len(uk_allowed)} UK-allowed pairs")

                for t in all_tickers:
                    sym = t.get('symbol', '')
                    # UK accounts: USDC pairs ONLY (USDT not permitted)
                    if not sym.endswith('USDC'):
                        continue
                    if uk_allowed and sym not in uk_allowed:
                        continue
                    price = float(t.get('lastPrice', 0) or 0)
                    change = float(t.get('priceChangePercent', 0) or 0)
                    volume = float(t.get('quoteVolume', 0) or 0)
                    count = int(t.get('count', 0) or 0)
                    if price <= 0 or volume < 25000 or count < 200:
                        continue
                    score = change + min(volume / 1_000_000, 5)
                    buy_candidates.append({
                        'pair': sym, 'price': price, 'change': change,
                        'volume': volume, 'score': score,
                    })
            except Exception as e:
                log_fire(f"   [WARN] Binance full-universe scan failed: {e} — using safe fallback")
                for base in ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "LINK", "AVAX", "DOT", "MATIC"]:
                    try:
                        ticker = self.binance.get_24h_ticker(f"{base}USDC")
                        if ticker and float(ticker.get('lastPrice', 0)) > 0:
                            buy_candidates.append({
                                'pair': f"{base}USDC",
                                'price': float(ticker.get('lastPrice', 0)),
                                'change': float(ticker.get('priceChangePercent', 0)),
                                'volume': float(ticker.get('quoteVolume', 0)),
                                'score': float(ticker.get('priceChangePercent', 0)),
                            })
                    except Exception:
                        continue

            buy_candidates.sort(key=lambda x: -x['score'])
            log_fire(f"   [SCAN] Binance: {len(buy_candidates)} liquid UK USDC pairs found, testing top 8 with SEER")

            for candidate in buy_candidates[:8]:
                # ═══ SEER PER-SYMBOL CHECK ═══
                base_for_seer = candidate['pair'].replace('USDC', '').replace('USDT', '')
                sym_bullish, sym_conf, sym_details = self._seer_symbol_signal(base_for_seer)
                if not sym_bullish:
                    log_fire(f"   🔮 SEER rejects {base_for_seer} — BEARISH, trying next")
                    continue
                raw_qty = _buy_amount(binance_cash)
                quote_qty = max(5.0, min(raw_qty * seer_risk_mod, binance_cash * 0.9))
                log_fire(f"\n🎯 BUY OPPORTUNITY (Binance): {candidate['pair']}")
                log_fire(f"   Price=${candidate['price']:.6f} | 24h={candidate['change']:+.2f}% | Vol=${candidate['volume']:.0f}")
                log_fire(f"   Seer risk_mod={seer_risk_mod:.2f} → qty=${quote_qty:.2f} USDC")
                try:
                    order = self.binance.place_market_order(candidate['pair'], 'buy', quote_qty=quote_qty)
                    log_result(f"BUY ORDER RESULT: {json.dumps(order, indent=2) if order else 'None'}")
                    if order and not order.get('error') and not order.get('rejected'):
                        log_fire("💥 BUY EXECUTED (Binance)")
                        self._record_buy_cost_basis(candidate['pair'], order, 'binance')
                        self._log_seer_prediction(candidate['pair'], 'binance', candidate['price'], seer_summary, sym_details)
                        bought_any = True
                        break
                    else:
                        log_fire(f"❌ Not filled: {order} — trying next")
                except Exception as e:
                    log_fire(f"❌ Binance buy failed ({candidate['pair']}): {e} — trying next")

        if not bought_any:
            log_fire("⚠️ No valid buy opportunities after scan")
        return sell_executed or bought_any

def main():
    # Only for standalone run
    trader = FireTrader()
    success = trader.run_fire_check()
    if success:
        print("\n✅ REAL TRADE EXECUTED!")
    else:
        print("\n❌ No trades executed")

if __name__ == '__main__':
    main()
