#!/usr/bin/env python3
"""
🔥 ORCA FIRE TRADE - REAL EXECUTION ONLY
No smoke. Just fire.

This script makes REAL trades immediately.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

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

    def run_fire_check(self):
        """Run the fire trade logic using SHARED clients."""
        log_fire("=" * 50)
        log_fire("   ORCA FIRE TRADE - REAL EXECUTION")
        log_fire("=" * 50)

        if not self.kraken or not self.binance:
            log_fire("⚠️ Clients not initialized")
            return False

        # Check what we have
        log_fire("\n📊 CHECKING REAL BALANCES...")
        
        # Kraken balances
        log_fire("\n🐙 KRAKEN:")
        tradeable_kraken = {}
        kraken_cash = 0.0
        kraken_usd_cash = 0.0
        kraken_usdc_cash = 0.0
        try:
            k_balances = self.kraken.get_balance()
            for asset, amt in k_balances.items():
                amt = float(amt)
                if amt > 0:
                    log_fire(f"   {asset}: {amt}")
                    if asset in ['USD', 'ZUSD', 'USDC', 'USDT']:
                        kraken_cash += amt
                    if asset in ['USD', 'ZUSD']:
                        kraken_usd_cash += amt
                    if asset == 'USDC':
                        kraken_usdc_cash += amt
                    if asset not in ['USD', 'ZUSD', 'ZGBP']:
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
        
        # Get prices and find best opportunity
        log_fire("\n🔍 SCANNING FOR BEST SELL OPPORTUNITY ON BINANCE (USDC pairs)...")
        best_sell = None
        best_value = 0
        
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

                if profit_margin > 0.3 and change > -2.0 and value > best_value:
                    best_sell = {
                        'asset': asset,
                        'symbol': symbol,
                        'qty': qty,
                        'price': price,
                        'value': value,
                        'change': change,
                        'profit_margin': profit_margin
                    }
                    best_value = value
            except Exception as e:
                log_fire(f"   [DEBUG] Binance {asset}: error while evaluating sell opportunity - {e}")

        if best_sell:
            log_fire(f"\n🎯 PROFIT OPPORTUNITY (Binance): {best_sell['asset']}")
            log_fire(f"   Sell 50% to lock +{best_sell['profit_margin']:.2f}% profit")
            sell_qty = best_sell['qty'] * 0.5
            try:
                order = self.binance.place_market_order(best_sell['symbol'], 'sell', sell_qty)
                log_result(f"SELL ORDER RESULT: {json.dumps(order, indent=2) if order else 'None'}")
                if order and order.get('status') == 'FILLED':
                    log_fire(f"💥💥💥 BINANCE SELL FILLED! 💥💥💥")
                    with open('orca_real_trades.json', 'a') as f:
                        f.write(json.dumps({
                            'timestamp': datetime.now().isoformat(),
                            'exchange': 'binance',
                            'symbol': best_sell['symbol'],
                            'side': 'SELL',
                            'qty': sell_qty,
                            'price': best_sell['price'],
                            'value': best_sell['value'],
                            'order': order
                        }) + '\n')
                    return True
                else:
                    log_fire(f"❌ Binance sell not filled: {order}")
            except Exception as e:
                log_fire(f"❌ Binance sell failed: {e}")
        else:
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

                # Sell if: (1) actual profit after fees > 0.3% and (2) momentum isn't strongly down
                if profit_margin > 0.3 and change_24h > -2.0:
                    log_fire(f"   📈 {asset}: ${value:.2f} @ ${price:.4f} (24h {change_24h:+.2f}%, +{profit_margin:.2f}% profit)")
                    
                    # This is our best sell
                    log_fire(f"\n🎯 PROFIT OPPORTUNITY: {asset}")
                    log_fire(f"   Sell 50% to lock +{profit_margin:.2f}% profit")
                    
                    sell_qty = qty * 0.5
                    
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
                            
                        return True
                    else:
                        log_fire(f"❌ Order not filled: {order}")
                        
            except Exception as e:
                log_fire(f"   [DEBUG] Kraken {asset}: error while checking profit - {e}")
        
        log_fire("\n⚠️ No profitable positions to sell")

        # -----------------------------------------------------------------
        # BUY FALLBACK: if we have real cash but no sell candidates, try a
        # conservative momentum/dip entry with small size.
        # -----------------------------------------------------------------
        total_cash = kraken_cash + binance_cash
        if total_cash < 1.0:
            log_fire("   [DEBUG] Buy fallback skipped: insufficient total cash")
            return False

        log_fire("\n🛒 No sell found - scanning for BUY opportunities with available cash...")
        log_fire(f"   [DEBUG] Cash available: Kraken=${kraken_cash:.2f}, Binance=${binance_cash:.2f}")

        bought_any = False

        # Prefer Kraken if it has more cash (current setup often has Kraken USDC)
        prefer_kraken = kraken_cash >= binance_cash and self.kraken is not None

        # Deploy 85% of funded exchange cash, capped at $20, minimum $5
        # Higher deployment rate to maximize position size per trade
        def _buy_amount(cash_amt: float) -> float:
            return max(5.0, min(20.0, cash_amt * 0.85))

        watchlist = ["ETH", "SOL", "BTC", "ADA", "XRP", "LINK", "AVAX", "DOT", "ATOM", "TRX"]

        if prefer_kraken and kraken_cash >= 1.0:
            best_buy = None
            for base in watchlist:
                for pair in (f"{base}USDC", f"{base}USD", f"X{base}ZUSD"):
                    try:
                        # Enforce quote-currency funding compatibility
                        if pair.endswith("USDC") and kraken_usdc_cash < 1.0:
                            continue
                        if (pair.endswith("USD") or pair.endswith("ZUSD")) and kraken_usd_cash < 1.0:
                            continue

                        ticker24 = self.kraken.get_24h_ticker(pair)
                        if not ticker24:
                            continue
                        price = float(ticker24.get('lastPrice', 0) or 0)
                        change_24h = float(ticker24.get('priceChangePercent', 0) or 0)
                        quote_vol = float(ticker24.get('quoteVolume', 0) or 0)
                        if price <= 0 or quote_vol < 10000:
                            continue
                        # Favor positive momentum + high liquidity
                        score = change_24h + min(quote_vol / 1_000_000, 5)
                        if best_buy is None or score > best_buy['score']:
                            best_buy = {
                                'pair': pair,
                                'price': price,
                                'change_24h': change_24h,
                                'quote_vol': quote_vol,
                                'score': score,
                            }
                    except Exception:
                        continue

            if best_buy:
                if best_buy['pair'].endswith('USDC'):
                    funded_cash = kraken_usdc_cash
                    quote_ccy = 'USDC'
                else:
                    funded_cash = kraken_usd_cash
                    quote_ccy = 'USD'

                quote_qty = min(_buy_amount(funded_cash), funded_cash * 0.9)
                log_fire(f"\n🎯 BUY OPPORTUNITY (Kraken): {best_buy['pair']}")
                log_fire(
                    f"   Price=${best_buy['price']:.6f} | 24h={best_buy['change_24h']:+.2f}% | "
                    f"Vol=${best_buy['quote_vol']:.0f}"
                )
                log_fire(f"   Executing BUY quote_qty={quote_qty:.2f} {quote_ccy}")
                try:
                    order = self.kraken.place_market_order(best_buy['pair'], 'buy', quote_qty=quote_qty)
                    log_result(f"BUY ORDER RESULT: {json.dumps(order, indent=2) if order else 'None'}")
                    if order and not order.get('error') and not order.get('rejected'):
                        log_fire("💥 BUY EXECUTED (Kraken)")
                        # Record cost basis so we can track profit and sell later
                        self._record_buy_cost_basis(best_buy['pair'], order, 'kraken')
                        bought_any = True
                    else:
                        log_fire(f"❌ Buy not filled/rejected: {order}")
                except Exception as e:
                    log_fire(f"❌ Kraken buy failed: {e}")

        if self.binance is not None and binance_cash >= 1.0:
            best_buy = None
            for base in watchlist:
                # UK accounts: USDC pairs ONLY (USDT restricted)
                for pair in (f"{base}USDC",):
                    try:
                        ticker = self.binance.get_24h_ticker(pair)
                        if not ticker:
                            continue
                        price = float(ticker.get('lastPrice', 0) or 0)
                        change = float(ticker.get('priceChangePercent', 0) or 0)
                        volume = float(ticker.get('quoteVolume', 0) or 0)
                        if price <= 0 or volume < 25000:
                            continue
                        score = change + min(volume / 1_000_000, 5)
                        if best_buy is None or score > best_buy['score']:
                            best_buy = {'pair': pair, 'price': price, 'change': change, 'volume': volume, 'score': score}
                    except Exception:
                        continue

            if best_buy:
                quote_qty = min(_buy_amount(binance_cash), binance_cash * 0.9)
                log_fire(f"\n🎯 BUY OPPORTUNITY (Binance): {best_buy['pair']}")
                log_fire(f"   Price=${best_buy['price']:.6f} | 24h={best_buy['change']:+.2f}% | Vol=${best_buy['volume']:.0f}")
                log_fire(f"   Executing BUY quote_qty=${quote_qty:.2f}")
                try:
                    order = self.binance.place_market_order(best_buy['pair'], 'buy', quote_qty=quote_qty)
                    log_result(f"BUY ORDER RESULT: {json.dumps(order, indent=2) if order else 'None'}")
                    if order and not order.get('error') and not order.get('rejected'):
                        log_fire("💥 BUY EXECUTED (Binance)")
                        # Record cost basis so we can track profit and sell later
                        self._record_buy_cost_basis(best_buy['pair'], order, 'binance')
                        bought_any = True
                    else:
                        log_fire(f"❌ Buy not filled/rejected: {order}")
                except Exception as e:
                    log_fire(f"❌ Binance buy failed: {e}")

        if not bought_any:
            log_fire("⚠️ No valid buy opportunities after fallback scan")
        return bought_any

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
