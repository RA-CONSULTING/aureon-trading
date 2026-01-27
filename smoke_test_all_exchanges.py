#!/usr/bin/env python3
"""
🔥 SMOKE TEST - ALL EXCHANGES BUY/SELL CYCLE
============================================
Opens a SMALL position on each exchange and sells it immediately
to verify the complete trading cycle works.

THIS USES REAL MONEY! (but minimum amounts)

Exchanges tested:
- Alpaca (crypto)
- Kraken (crypto)
- Binance (crypto)

Gary Leckey | January 2026
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import time
import argparse
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SmokeTestResult:
    exchange: str
    symbol: str
    buy_success: bool
    buy_order_id: Optional[str]
    buy_price: Optional[float]
    buy_qty: Optional[float]
    buy_error: Optional[str]
    sell_success: bool
    sell_order_id: Optional[str]
    sell_price: Optional[float]
    sell_error: Optional[str]
    net_pnl: Optional[float]
    duration_seconds: float


def test_alpaca(dry_run: bool = True) -> SmokeTestResult:
    """Test buy/sell cycle on Alpaca."""
    start = time.time()
    result = SmokeTestResult(
        exchange='alpaca',
        symbol='BTC/USD',
        buy_success=False, buy_order_id=None, buy_price=None, buy_qty=None, buy_error=None,
        sell_success=False, sell_order_id=None, sell_price=None, sell_error=None,
        net_pnl=None, duration_seconds=0
    )
    
    try:
        from alpaca_client import AlpacaClient
        client = AlpacaClient()
        
        # Get current price
        ticker = client.get_ticker('BTC/USD')
        if not ticker:
            result.buy_error = "Could not get ticker"
            result.duration_seconds = time.time() - start
            return result
        
        current_price = ticker.get('last') or ticker.get('ask') or ticker.get('bid')
        if not current_price:
            result.buy_error = f"No price in ticker: {ticker}"
            result.duration_seconds = time.time() - start
            return result
        
        # Calculate minimum qty ($1.10 worth to ensure above $1 minimum)
        min_notional = 1.10
        qty = round(min_notional / current_price, 8)
        
        print(f"  📊 BTC/USD price: ${current_price:,.2f}")
        print(f"  📦 Quantity: {qty} BTC (~${qty * current_price:.2f})")
        
        if dry_run:
            print(f"  🔸 DRY RUN - Would buy {qty} BTC/USD")
            result.buy_success = True
            result.buy_price = current_price
            result.buy_qty = qty
            result.sell_success = True
            result.sell_price = current_price
            result.net_pnl = 0.0
            result.duration_seconds = time.time() - start
            return result
        
        # === REAL BUY ===
        print(f"  🛒 Buying {qty} BTC/USD...")
        buy_result = client.place_order(
            symbol='BTC/USD',
            side='buy',
            qty=qty,
            order_type='market'
        )
        
        if not buy_result or buy_result.get('status') == 'rejected':
            result.buy_error = f"Buy rejected: {buy_result}"
            result.duration_seconds = time.time() - start
            return result
        
        result.buy_success = True
        result.buy_order_id = buy_result.get('id')
        result.buy_qty = qty
        
        # Wait for fill
        print(f"  ⏳ Waiting for fill...")
        time.sleep(2)
        
        # Get fill price
        if result.buy_order_id:
            order_status = client.get_order(result.buy_order_id)
            if order_status:
                result.buy_price = float(order_status.get('filled_avg_price', current_price))
        
        if not result.buy_price:
            result.buy_price = current_price
        
        print(f"  ✅ Bought at ${result.buy_price:,.2f}")
        
        # === REAL SELL ===
        print(f"  💰 Selling {qty} BTC/USD...")
        time.sleep(1)  # Brief pause
        
        sell_result = client.place_order(
            symbol='BTC/USD',
            side='sell',
            qty=qty,
            order_type='market'
        )
        
        if not sell_result or sell_result.get('status') == 'rejected':
            result.sell_error = f"Sell rejected: {sell_result}"
            result.duration_seconds = time.time() - start
            return result
        
        result.sell_success = True
        result.sell_order_id = sell_result.get('id')
        
        # Wait for fill
        time.sleep(2)
        
        # Get fill price
        if result.sell_order_id:
            order_status = client.get_order(result.sell_order_id)
            if order_status:
                result.sell_price = float(order_status.get('filled_avg_price', current_price))
        
        if not result.sell_price:
            result.sell_price = current_price
        
        print(f"  ✅ Sold at ${result.sell_price:,.2f}")
        
        # Calculate P&L
        if result.buy_price and result.sell_price and result.buy_qty:
            buy_cost = result.buy_price * result.buy_qty * 1.0025  # +0.25% fee
            sell_value = result.sell_price * result.buy_qty * 0.9975  # -0.25% fee
            result.net_pnl = sell_value - buy_cost
        
    except Exception as e:
        if not result.buy_success:
            result.buy_error = str(e)
        else:
            result.sell_error = str(e)
    
    result.duration_seconds = time.time() - start
    return result


def test_kraken(dry_run: bool = True) -> SmokeTestResult:
    """Test buy/sell cycle on Kraken."""
    start = time.time()
    result = SmokeTestResult(
        exchange='kraken',
        symbol='BTC/USD',
        buy_success=False, buy_order_id=None, buy_price=None, buy_qty=None, buy_error=None,
        sell_success=False, sell_order_id=None, sell_price=None, sell_error=None,
        net_pnl=None, duration_seconds=0
    )
    
    try:
        from kraken_client import KrakenClient
        client = KrakenClient()
        
        # Get current price
        ticker = client.get_ticker('XXBTZUSD')  # Kraken uses this format
        if not ticker:
            # Try alternative format
            ticker = client.get_ticker('BTC/USD')
        
        if not ticker:
            result.buy_error = "Could not get ticker"
            result.duration_seconds = time.time() - start
            return result
        
        current_price = ticker.get('last') or ticker.get('ask') or ticker.get('bid')
        if not current_price:
            result.buy_error = f"No price in ticker: {ticker}"
            result.duration_seconds = time.time() - start
            return result
        
        current_price = float(current_price)
        
        # Kraken minimum is 0.0001 BTC (~$10 at $100k)
        # Use $5 minimum notional if we have enough balance
        min_notional = 5.50  # Kraken min is $5
        qty = round(min_notional / current_price, 6)
        qty = max(qty, 0.0001)  # Kraken absolute minimum
        
        print(f"  📊 BTC/USD price: ${current_price:,.2f}")
        print(f"  📦 Quantity: {qty} BTC (~${qty * current_price:.2f})")
        
        if dry_run:
            print(f"  🔸 DRY RUN - Would buy {qty} XBT (BTC)")
            result.buy_success = True
            result.buy_price = current_price
            result.buy_qty = qty
            result.sell_success = True
            result.sell_price = current_price
            result.net_pnl = 0.0
            result.duration_seconds = time.time() - start
            return result
        
        # === REAL BUY ===
        print(f"  🛒 Buying {qty} XBT/USD...")
        buy_result = client.place_order(
            pair='XXBTZUSD',
            side='buy',
            volume=qty,
            order_type='market'
        )
        
        if not buy_result or 'error' in str(buy_result).lower():
            result.buy_error = f"Buy failed: {buy_result}"
            result.duration_seconds = time.time() - start
            return result
        
        result.buy_success = True
        result.buy_order_id = buy_result.get('txid', [None])[0] if isinstance(buy_result.get('txid'), list) else buy_result.get('txid')
        result.buy_qty = qty
        result.buy_price = current_price  # Market order, use current price
        
        print(f"  ✅ Buy order placed: {result.buy_order_id}")
        
        # Wait for fill
        print(f"  ⏳ Waiting for fill...")
        time.sleep(3)
        
        # === REAL SELL ===
        print(f"  💰 Selling {qty} XBT/USD...")
        
        sell_result = client.place_order(
            pair='XXBTZUSD',
            side='sell',
            volume=qty,
            order_type='market'
        )
        
        if not sell_result or 'error' in str(sell_result).lower():
            result.sell_error = f"Sell failed: {sell_result}"
            result.duration_seconds = time.time() - start
            return result
        
        result.sell_success = True
        result.sell_order_id = sell_result.get('txid', [None])[0] if isinstance(sell_result.get('txid'), list) else sell_result.get('txid')
        result.sell_price = current_price
        
        print(f"  ✅ Sell order placed: {result.sell_order_id}")
        
        # Calculate P&L (approximate)
        if result.buy_price and result.sell_price and result.buy_qty:
            buy_cost = result.buy_price * result.buy_qty * 1.0026  # +0.26% fee
            sell_value = result.sell_price * result.buy_qty * 0.9974  # -0.26% fee
            result.net_pnl = sell_value - buy_cost
        
    except Exception as e:
        if not result.buy_success:
            result.buy_error = str(e)
        else:
            result.sell_error = str(e)
    
    result.duration_seconds = time.time() - start
    return result


def test_binance(dry_run: bool = True) -> SmokeTestResult:
    """Test buy/sell cycle on Binance."""
    start = time.time()
    result = SmokeTestResult(
        exchange='binance',
        symbol='BTC/USDT',
        buy_success=False, buy_order_id=None, buy_price=None, buy_qty=None, buy_error=None,
        sell_success=False, sell_order_id=None, sell_price=None, sell_error=None,
        net_pnl=None, duration_seconds=0
    )
    
    try:
        from binance_client import BinanceClient
        client = BinanceClient()
        
        # Get current price
        ticker = client.get_ticker('BTCUSDT')
        if not ticker:
            result.buy_error = "Could not get ticker"
            result.duration_seconds = time.time() - start
            return result
        
        current_price = ticker.get('price') or ticker.get('last') or ticker.get('askPrice')
        if not current_price:
            result.buy_error = f"No price in ticker: {ticker}"
            result.duration_seconds = time.time() - start
            return result
        
        current_price = float(current_price)
        
        # Binance minimum notional is typically $5-10 for BTC
        min_notional = 6.0
        qty = round(min_notional / current_price, 6)
        qty = max(qty, 0.00001)  # Binance BTC minimum
        
        print(f"  📊 BTC/USDT price: ${current_price:,.2f}")
        print(f"  📦 Quantity: {qty} BTC (~${qty * current_price:.2f})")
        
        if dry_run:
            print(f"  🔸 DRY RUN - Would buy {qty} BTCUSDT")
            result.buy_success = True
            result.buy_price = current_price
            result.buy_qty = qty
            result.sell_success = True
            result.sell_price = current_price
            result.net_pnl = 0.0
            result.duration_seconds = time.time() - start
            return result
        
        # === REAL BUY ===
        print(f"  🛒 Buying {qty} BTCUSDT...")
        buy_result = client.place_order(
            symbol='BTCUSDT',
            side='BUY',
            order_type='MARKET',
            quantity=qty
        )
        
        if not buy_result or buy_result.get('status') == 'REJECTED':
            result.buy_error = f"Buy failed: {buy_result}"
            result.duration_seconds = time.time() - start
            return result
        
        result.buy_success = True
        result.buy_order_id = str(buy_result.get('orderId', ''))
        result.buy_qty = float(buy_result.get('executedQty', qty))
        
        # Get fill price from fills
        fills = buy_result.get('fills', [])
        if fills:
            total_cost = sum(float(f['price']) * float(f['qty']) for f in fills)
            total_qty = sum(float(f['qty']) for f in fills)
            result.buy_price = total_cost / total_qty if total_qty > 0 else current_price
        else:
            result.buy_price = current_price
        
        print(f"  ✅ Bought at ${result.buy_price:,.2f}")
        
        # Wait briefly
        time.sleep(1)
        
        # === REAL SELL ===
        print(f"  💰 Selling {result.buy_qty} BTCUSDT...")
        
        sell_result = client.place_order(
            symbol='BTCUSDT',
            side='SELL',
            order_type='MARKET',
            quantity=result.buy_qty
        )
        
        if not sell_result or sell_result.get('status') == 'REJECTED':
            result.sell_error = f"Sell failed: {sell_result}"
            result.duration_seconds = time.time() - start
            return result
        
        result.sell_success = True
        result.sell_order_id = str(sell_result.get('orderId', ''))
        
        # Get fill price from fills
        fills = sell_result.get('fills', [])
        if fills:
            total_value = sum(float(f['price']) * float(f['qty']) for f in fills)
            total_qty = sum(float(f['qty']) for f in fills)
            result.sell_price = total_value / total_qty if total_qty > 0 else current_price
        else:
            result.sell_price = current_price
        
        print(f"  ✅ Sold at ${result.sell_price:,.2f}")
        
        # Calculate P&L (Binance 0.1% fee)
        if result.buy_price and result.sell_price and result.buy_qty:
            buy_cost = result.buy_price * result.buy_qty * 1.001  # +0.1% fee
            sell_value = result.sell_price * result.buy_qty * 0.999  # -0.1% fee
            result.net_pnl = sell_value - buy_cost
        
    except Exception as e:
        if not result.buy_success:
            result.buy_error = str(e)
        else:
            result.sell_error = str(e)
    
    result.duration_seconds = time.time() - start
    return result


def print_result(result: SmokeTestResult):
    """Pretty print a smoke test result."""
    status = "✅ PASS" if (result.buy_success and result.sell_success) else "❌ FAIL"
    
    print(f"\n{'='*60}")
    print(f"  {result.exchange.upper()} - {result.symbol} - {status}")
    print(f"{'='*60}")
    
    print(f"  Buy:  {'✅' if result.buy_success else '❌'} ", end='')
    if result.buy_success:
        print(f"Order {result.buy_order_id} @ ${result.buy_price:,.2f} x {result.buy_qty}")
    else:
        print(f"ERROR: {result.buy_error}")
    
    print(f"  Sell: {'✅' if result.sell_success else '❌'} ", end='')
    if result.sell_success:
        print(f"Order {result.sell_order_id} @ ${result.sell_price:,.2f}")
    else:
        print(f"ERROR: {result.sell_error}")
    
    if result.net_pnl is not None:
        pnl_emoji = "🟢" if result.net_pnl >= 0 else "🔴"
        print(f"  P&L:  {pnl_emoji} ${result.net_pnl:+.4f}")
    
    print(f"  Time: {result.duration_seconds:.2f}s")


def main():
    parser = argparse.ArgumentParser(description='Smoke test all exchanges with buy/sell cycle')
    parser.add_argument('--live', action='store_true', help='Execute REAL trades (default: dry-run)')
    parser.add_argument('--exchange', type=str, help='Test only this exchange (alpaca, kraken, binance)')
    args = parser.parse_args()
    
    dry_run = not args.live
    
    print("\n" + "="*60)
    print("  🔥 SMOKE TEST - ALL EXCHANGES BUY/SELL CYCLE")
    print("="*60)
    print(f"  Mode: {'🔴 LIVE TRADING' if not dry_run else '🔸 DRY RUN (no real trades)'}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if not dry_run:
        print("\n  ⚠️  WARNING: This will execute REAL trades!")
        print("  ⚠️  Small amounts (~$5-10 per exchange)")
        confirm = input("\n  Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("  Aborted.")
            return
    
    results = []
    
    # Test each exchange
    exchanges_to_test = ['alpaca', 'kraken', 'binance']
    if args.exchange:
        exchanges_to_test = [args.exchange.lower()]
    
    for exchange in exchanges_to_test:
        print(f"\n{'─'*60}")
        print(f"  Testing {exchange.upper()}...")
        print(f"{'─'*60}")
        
        if exchange == 'alpaca':
            result = test_alpaca(dry_run)
        elif exchange == 'kraken':
            result = test_kraken(dry_run)
        elif exchange == 'binance':
            result = test_binance(dry_run)
        else:
            print(f"  ❌ Unknown exchange: {exchange}")
            continue
        
        results.append(result)
        print_result(result)
    
    # Summary
    print("\n" + "="*60)
    print("  📊 SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r.buy_success and r.sell_success)
    failed = len(results) - passed
    total_pnl = sum(r.net_pnl for r in results if r.net_pnl is not None)
    
    print(f"  Passed: {passed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    if not dry_run:
        print(f"  Total P&L: ${total_pnl:+.4f}")
    
    for r in results:
        status = "✅" if (r.buy_success and r.sell_success) else "❌"
        print(f"    {status} {r.exchange}: ", end='')
        if r.buy_success and r.sell_success:
            print(f"BUY→SELL complete")
        elif not r.buy_success:
            print(f"Buy failed: {r.buy_error}")
        else:
            print(f"Sell failed: {r.sell_error}")
    
    print("\n" + "="*60)
    
    # Return exit code
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main() or 0)
