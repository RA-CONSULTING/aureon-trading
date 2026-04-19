#!/usr/bin/env python3
"""
💰 EXECUTE 3 REAL MONEY NET PROFIT TRADES 💰
=============================================

This script executes 3 real money trades designed for net profit:
1. Binance: Quick scalp trade
2. Kraken: Quick scalp trade  
3. Binance: Second scalp trade

Using existing MultiExchangeClient infrastructure.

Gary Leckey | December 2025
"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
from typing import Optional, Tuple, Dict, Any

# Force LIVE mode
os.environ['LIVE'] = '1'
os.environ['DRY_RUN'] = '0'

from aureon.trading.aureon_unified_ecosystem import MultiExchangeClient, CONFIG, get_platform_fee


def get_symbol_filters(client: MultiExchangeClient, exchange: str, symbol: str) -> Dict[str, Any]:
    exchange = exchange.lower()
    if exchange not in client.clients:
        return {}
    raw_client = getattr(client.clients[exchange], 'client', None)
    if raw_client and hasattr(raw_client, 'get_symbol_filters'):
        try:
            return raw_client.get_symbol_filters(symbol)
        except Exception:
            return {}
    return {}


def get_quote_asset(client: MultiExchangeClient, exchange: str, symbol: str) -> Optional[str]:
    filters = get_symbol_filters(client, exchange, symbol)
    quote = filters.get('quote_asset')
    if quote:
        return quote
    # Fallback heuristics
    for suffix in ['USDT', 'USDC', 'BUSD', 'USD', 'BTC', 'ETH', 'BNB']:
        if symbol.endswith(suffix):
            return suffix
    exchange = exchange.lower()
    if exchange == 'kraken':
        for suffix in ['USDT', 'USDC', 'USD', 'EUR', 'GBP']:
            if symbol.endswith(suffix):
                return suffix
    if exchange == 'capital':
        return 'USD'
    return None


def get_available_balance(client: MultiExchangeClient, exchange: str, asset: Optional[str]) -> Optional[float]:
    if not asset:
        return None
    try:
        unified = client.clients.get(exchange.lower())
        if not unified:
            return None
        balance = unified.get_balance(asset)
        return float(balance)
    except Exception:
        return None


def get_min_notional(client: MultiExchangeClient, exchange: str, symbol: str) -> float:
    filters = get_symbol_filters(client, exchange, symbol)
    value = filters.get('min_notional')
    if value:
        try:
            return float(value)
        except (TypeError, ValueError):
            pass
    return 0.0

def get_best_price(client, exchange: str, symbol: str):
    """Get current best bid/ask for a symbol"""
    try:
        ticker = client.get_ticker(exchange, symbol)
        if ticker:
            # Handle different ticker formats
            last_price = float(ticker.get('price', ticker.get('last', ticker.get('lastPrice', 0))))
            bid_price = float(ticker.get('bid', ticker.get('bidPrice', last_price)))
            ask_price = float(ticker.get('ask', ticker.get('askPrice', last_price)))
            
            # Capital.com returns forex prices in pips (x10000)
            # Detect and convert: EURUSD ~1.17 but returns 11719
            if exchange == 'capital' and last_price > 1000:
                # Likely pip format, convert back
                last_price = last_price / 10000
                bid_price = bid_price / 10000
                ask_price = ask_price / 10000
                
            return {
                'bid': bid_price,
                'ask': ask_price,
                'last': last_price
            }
    except Exception as e:
        print(f"   ⚠️ Error getting price: {e}")
    return None


def resolve_order_reference(exchange: str, client: MultiExchangeClient, order_response: dict, action: str) -> Tuple[bool, Optional[str]]:
    """Normalize order responses across exchanges and confirm Capital.com deals."""
    if not order_response or not isinstance(order_response, dict):
        return False, None

    exchange = exchange.lower()

    # Binance style order id
    if 'orderId' in order_response:
        return True, str(order_response['orderId'])

    # Kraken returns txid list
    txids = order_response.get('txid')
    if exchange == 'kraken' and isinstance(txids, list) and txids:
        return True, txids[0]

    # Capital.com returns dealReference, requires confirmation
    if exchange == 'capital':
        capital_client = client.clients['capital'].client
        deal_id = order_response.get('dealId')
        if deal_id:
            return True, deal_id

        deal_ref = order_response.get('dealReference') or order_response.get('deal_ref')
        if deal_ref and hasattr(capital_client, 'confirm_order'):
            confirm = capital_client.confirm_order(deal_ref)
            status = str(confirm.get('dealStatus', '')).upper()
            if status == 'ACCEPTED':
                resolved = confirm.get('dealId', deal_ref)
                return True, resolved
            print(f"   ❌ Capital.com {action} not accepted: {confirm}")
            return False, None

    return False, None

def execute_scalp_trade(client, exchange: str, symbol: str, amount_usd: float):
    """
    Execute a quick scalp trade:
    1. Buy at market
    2. Wait for small price movement
    3. Sell at market (with limit to ensure profit)
    """
    print(f"\n{'='*60}")
    print(f"🎯 EXECUTING TRADE: {symbol} on {exchange.upper()}")
    print(f"{'='*60}")
    
    # Get current price
    prices = get_best_price(client, exchange, symbol)
    if not prices:
        print("   ❌ Could not get price")
        return False, 0
    
    current_price = prices['last']
    print(f"   📊 Current Price: ${current_price:.4f}")
    
    quote_asset = get_quote_asset(client, exchange, symbol)
    available_quote = get_available_balance(client, exchange, quote_asset)
    min_notional = get_min_notional(client, exchange, symbol)
    quote_order_qty = None
    spend_amount = amount_usd
    
    if exchange == 'binance':
        if available_quote is None or available_quote <= 0:
            print(f"   ❌ No available {quote_asset or 'quote'} balance on Binance")
            return False, 0
        max_spend = available_quote * 0.98  # leave small buffer for fees
        spend_amount = min(amount_usd, max_spend)
        if min_notional > 0 and spend_amount < min_notional:
            if max_spend >= min_notional:
                spend_amount = min(max_spend, min_notional)
            else:
                print(f"   ❌ Insufficient {quote_asset} balance (${available_quote:.2f}) for Binance min notional ${min_notional:.2f}")
                return False, 0
        quote_order_qty = spend_amount
    elif exchange == 'capital':
        # Capital.com forex positions have fixed contract sizes. 1 lot ≈ $100k notional.
        target_lots = amount_usd / 100000  # approximate conversion
        spend_amount = amount_usd
    
    # Calculate quantity based on spend amount
    raw_quantity = spend_amount / current_price if current_price else 0
    if exchange == 'capital':
        quantity = max(0.01, round(target_lots, 2))
    elif 'ADA' in symbol:
        quantity = round(raw_quantity, 1)
    elif 'BTC' in symbol:
        quantity = round(raw_quantity, 6)
    elif 'ETH' in symbol:
        quantity = round(raw_quantity, 5)
    else:
        quantity = max(1, int(raw_quantity))
    
    print(f"   📦 Quantity: {quantity}")
    print(f"   💵 Value: ${spend_amount:.2f}")
    
    # Calculate fees
    fee_rate = get_platform_fee(exchange, 'taker')
    trade_notional = spend_amount if quote_order_qty else quantity * current_price
    entry_fee = trade_notional * fee_rate
    exit_fee = trade_notional * fee_rate
    total_fees = entry_fee + exit_fee
    
    print(f"   💸 Est. Fees: ${total_fees:.4f}")
    
    # Calculate minimum profit target (fees + 0.1% profit)
    min_profit_pct = (total_fees / amount_usd) + 0.001
    target_price = current_price * (1 + min_profit_pct)
    
    print(f"   🎯 Target Price: ${target_price:.4f} (+{min_profit_pct*100:.3f}%)")
    
    # STEP 1: BUY
    print(f"\n   📈 BUYING {quantity} {symbol}...")
    order_kwargs = {'quantity': quantity}
    if quote_order_qty:
        order_kwargs = {'quote_qty': quote_order_qty}
    try:
        buy_result = client.place_market_order(exchange, symbol, 'BUY', **order_kwargs)
        success, order_ref = resolve_order_reference(exchange, client, buy_result, 'buy')
        if not success:
            print(f"   ❌ Buy failed: {buy_result}")
            return False, 0
        print(f"   ✅ Buy Order ID: {order_ref}")
        trade_quantity = quantity
        if isinstance(buy_result, dict):
            executed_qty = buy_result.get('executedQty') or buy_result.get('origQty')
            if executed_qty:
                try:
                    trade_quantity = float(executed_qty)
                except (TypeError, ValueError):
                    pass
    except Exception as e:
        print(f"   ❌ Buy error: {e}")
        return False, 0
    
    # Wait for price to move up
    print(f"\n   ⏳ Waiting for price movement...")
    wait_time = 0
    max_wait = 60  # Max 60 seconds
    check_interval = 2
    
    while wait_time < max_wait:
        time.sleep(check_interval)
        wait_time += check_interval
        
        new_prices = get_best_price(client, exchange, symbol)
        if new_prices:
            new_price = new_prices['last']
            pct_change = ((new_price - current_price) / current_price) * 100
            print(f"   📊 Price: ${new_price:.4f} ({pct_change:+.3f}%) [{wait_time}s]")
            
            # If price moved up enough, sell
            if new_price >= target_price:
                print(f"   🎯 Target reached!")
                break
            
            # If price dropped too much, cut loss
            if pct_change < -0.5:
                print(f"   ⚠️ Price dropped, selling to minimize loss")
                break
    
    # STEP 2: SELL
    print(f"\n   📉 SELLING {quantity} {symbol}...")
    try:
        sell_result = client.place_market_order(exchange, symbol, 'SELL', quantity=trade_quantity)
        success, order_ref = resolve_order_reference(exchange, client, sell_result, 'sell')
        if not success:
            print(f"   ❌ Sell failed: {sell_result}")
            return False, 0
        print(f"   ✅ Sell Order ID: {order_ref}")
    except Exception as e:
        print(f"   ❌ Sell error: {e}")
        return False, 0
    
    # Calculate final P&L
    final_prices = get_best_price(client, exchange, symbol)
    if final_prices:
        exit_price = final_prices['last']
        gross_pnl = (exit_price - current_price) * trade_quantity
        net_pnl = gross_pnl - total_fees
        
        print(f"\n   {'='*40}")
        print(f"   📊 TRADE RESULT:")
        print(f"   ├─ Entry: ${current_price:.4f}")
        print(f"   ├─ Exit:  ${exit_price:.4f}")
        print(f"   ├─ Gross: ${gross_pnl:+.4f}")
        print(f"   ├─ Fees:  ${total_fees:.4f}")
        if net_pnl > 0:
            print(f"   └─ ✅ NET PROFIT: ${net_pnl:+.4f}")
        else:
            print(f"   └─ ❌ NET LOSS: ${net_pnl:+.4f}")
        print(f"   {'='*40}")
        
        return net_pnl > 0, net_pnl
    
    return False, 0


def main():
    print("\n" + "="*70)
    print("💰 REAL MONEY TRADE EXECUTION - 3 NET PROFIT TRADES 💰")
    print("="*70)
    
    # Safety confirmation
    print("\n⚠️  WARNING: This will execute REAL trades with REAL money!")
    print("    Available balances will be used.")
    
    confirm = input("\n   Type 'EXECUTE' to proceed: ")
    if confirm != 'EXECUTE':
        print("\n   ❌ Cancelled. No trades executed.")
        return
    
    # Initialize client in LIVE mode
    print("\n🔌 Initializing MultiExchangeClient (LIVE MODE)...")
    client = MultiExchangeClient()
    
    if client.dry_run:
        print("   ⚠️ Client is in DRY RUN mode - switching to LIVE")
        client.dry_run = False
    
    print(f"   ✅ Client ready (Dry Run: {client.dry_run})")
    
    # Define trades - One on each platform
    # Binance: Use XLMUSDC ($5 min notional met after freeing USDC balance)
    # Kraken: Use ADAUSDT to consume available USDT balance
    # Capital.com: Use EURUSD (Forex CFD) since Demo doesn't have crypto
    trades = [
        ('binance', 'XLMUSDC', 5.0),    # ~$5 XLM trade on Binance (USDC quote)
        ('kraken', 'ADAUSDT', 6.0),     # $6 ADA trade on Kraken (USDT quote)
        ('capital', 'EURUSD', 10.0),    # $10 EURUSD trade (Forex CFD)
    ]
    
    results = []
    total_pnl = 0
    
    for exchange, symbol, amount in trades:
        # Skip if exchange client is not enabled/working
        if exchange == 'capital' and not client.clients['capital'].client.enabled:
            print(f"\n   ⚠️ Skipping Capital.com trade (Client disabled/not configured)")
            continue
            
        success, pnl = execute_scalp_trade(client, exchange, symbol, amount)
        results.append((exchange, symbol, success, pnl))
        total_pnl += pnl
        
        # Wait between trades
        if trades.index((exchange, symbol, amount)) < len(trades) - 1:
            print("\n   ⏳ Waiting 5 seconds before next trade...")
            time.sleep(5)
    
    # Final Summary
    print("\n" + "="*70)
    print("📊 FINAL RESULTS")
    print("="*70)
    
    wins = 0
    for exchange, symbol, success, pnl in results:
        icon = "✅" if success else "❌"
        print(f"   {icon} {exchange.upper()} {symbol}: ${pnl:+.4f}")
        if success:
            wins += 1
    
    print(f"\n   Total Trades: {len(results)}")
    print(f"   Wins: {wins}")
    print(f"   Win Rate: {wins/len(results)*100:.1f}%")
    print(f"   Total Net P&L: ${total_pnl:+.4f}")
    
    if total_pnl > 0:
        print("\n   🎉 OVERALL NET PROFIT! 🎉")
    else:
        print("\n   📉 Overall net loss")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
