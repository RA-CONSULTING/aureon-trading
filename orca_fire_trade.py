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
        try:
            k_balances = self.kraken.get_balance()
            for asset, amt in k_balances.items():
                amt = float(amt)
                if amt > 0:
                    log_fire(f"   {asset}: {amt}")
                    if asset not in ['USD', 'ZUSD', 'ZGBP']:
                        tradeable_kraken[asset] = amt
        except Exception as e:
            log_fire(f"   Error: {e}")
        
        # Binance balances
        log_fire("\n🟡 BINANCE:")
        tradeable_binance = {}
        try:
            b_balances = self.binance.get_balance()
            for asset, amt in b_balances.items():
                amt = float(amt)
                if amt > 0:
                    log_fire(f"   {asset}: {amt}")
                    if asset not in ['USDT', 'USDC', 'BUSD']:
                        tradeable_binance[asset] = amt
        except Exception as e:
            log_fire(f"   Error: {e}")
        
        # Get prices and find best opportunity
        log_fire("\n🔍 SCANNING FOR BEST SELL OPPORTUNITY ON BINANCE...")
        best_sell = None
        best_value = 0
        
        for asset, qty in tradeable_binance.items():
            try:
                symbol = f"{asset}USDT"
                ticker = self.binance.get_24h_ticker(symbol)
                if not ticker:
                    continue

                price = float(ticker.get('lastPrice', 0))
                change = float(ticker.get('priceChangePercent', 0))
                value = qty * price

                if value <= 1:
                    continue

                log_fire(f"   {asset}: {qty:.2f} @ ${price:.6f} = ${value:.2f} ({change:+.1f}%)")

                if change > 0 and value > best_value:
                    best_sell = {
                        'asset': asset,
                        'symbol': symbol,
                        'qty': qty,
                        'price': price,
                        'value': value,
                        'change': change
                    }
                    best_value = value
            except Exception as e:
                log_fire(f"   [DEBUG] Binance {asset}: error while evaluating sell opportunity - {e}")

        if best_sell:
            log_fire(f"   [DEBUG] Binance candidate {best_sell['symbol']}: change={best_sell['change']:.2f}%, value=${best_sell['value']:.2f}")
        else:
            log_fire("   [DEBUG] Binance: no positive change opportunities detected")
        
        # Skip Binance (too many UK restrictions), go straight to Kraken
        log_fire("\n🔍 Scanning Kraken for profit opportunities...")
        
        for asset, qty in tradeable_kraken.items():
            if qty <= 0:
                continue
                
            # Get current price and check if profitable
            try:
                pair = f"{asset}USD"
                ticker = self.kraken.get_ticker(pair)
                if not ticker or not ticker.get('price'):
                    continue
                    
                price = float(ticker['price'])
                value = qty * price
                
                if value < 5:  # Skip small positions
                    continue
                    
                # Check 24h data
                high = float(ticker.get('high', price))
                low = float(ticker.get('low', price))
                
                if high <= low:
                    log_fire(f"   [DEBUG] Kraken {asset}: invalid range high={high:.4f} low={low:.4f}")
                    continue

                position_pct = ((price - low) / (high - low)) * 100
                log_fire(f"   [DEBUG] Kraken {asset}: qty={qty:.4f}, price=${price:.4f}, low=${low:.4f}, high=${high:.4f}, position%={position_pct:.2f}")

                # Load cost basis to ensure we're not selling at a loss
                cost_basis = None
                try:
                    with open('cost_basis_history.json', 'r') as f:
                        cb_data = json.load(f)
                        for pos in cb_data.get('positions', []):
                            if pos.get('symbol') == pair and pos.get('exchange') == 'kraken':
                                cost_basis = float(pos.get('average_cost', 0))
                                break
                except Exception:
                    pass
                
                # Calculate profit margin including 0.26% taker fee
                fee_rate = 0.0026
                net_price = price * (1 - fee_rate)
                profit_margin = ((net_price - (cost_basis or low)) / (cost_basis or low)) * 100 if (cost_basis or low) > 0 else 0

                log_fire(f"   [DEBUG] Kraken {asset}: cost_basis=${cost_basis:.4f if cost_basis else 0}, net_after_fees=${net_price:.4f}, profit_margin={profit_margin:.2f}%")

                # Only sell if: (1) in upper range AND (2) actual profit after fees > 0.5%
                if position_pct > 60 and profit_margin > 0.5:  # In profit zone with real profit
                    log_fire(f"   📈 {asset}: ${value:.2f} @ ${price:.4f} ({position_pct:.0f}% of range, +{profit_margin:.2f}% profit)")
                    
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
        
        return False

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
