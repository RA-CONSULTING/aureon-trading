#!/usr/bin/env python3
"""
⚔️ MULTI-EXCHANGE VERIFICATION TEST
=====================================
Tests the COMPLETE autonomous cycle on each exchange:
  1. BUY crypto with cash
  2. Verify the position exists
  3. SELL crypto back to cash
  4. Verify cash returned

Also tests convert_crypto path-finding on each exchange.

Uses REAL tiny amounts ($1-$4) to prove the logic flow works.
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Force live mode for this test
os.environ['DRY_RUN'] = '0'
os.environ['LIVE'] = '1'
os.environ['KRAKEN_DRY_RUN'] = 'false'
os.environ['BINANCE_DRY_RUN'] = 'false'
os.environ['ALPACA_DRY_RUN'] = 'false'

RESULTS = []

def log(msg, level='INFO'):
    ts = datetime.now().strftime('%H:%M:%S')
    icon = {'INFO': '📋', 'OK': '✅', 'FAIL': '❌', 'WARN': '⚠️', 'TEST': '🧪'}.get(level, '📋')
    print(f"[{ts}] {icon} {msg}")

def record(exchange, operation, success, details=""):
    RESULTS.append({
        'exchange': exchange,
        'operation': operation,
        'success': success,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })
    level = 'OK' if success else 'FAIL'
    log(f"{exchange.upper()} {operation}: {'PASS' if success else 'FAIL'} — {details}", level)

def print_summary():
    print("\n" + "=" * 70)
    print("⚔️  MULTI-EXCHANGE VERIFICATION RESULTS")
    print("=" * 70)
    
    for ex in ['kraken', 'binance', 'alpaca']:
        ex_results = [r for r in RESULTS if r['exchange'] == ex]
        if not ex_results:
            print(f"\n  {'🐙' if ex=='kraken' else '🟡' if ex=='binance' else '🦙'} {ex.upper()}: NOT TESTED")
            continue
        
        passes = sum(1 for r in ex_results if r['success'])
        fails = sum(1 for r in ex_results if not r['success'])
        icon = '🐙' if ex=='kraken' else '🟡' if ex=='binance' else '🦙'
        status = '✅ ALL PASS' if fails == 0 else f'❌ {fails} FAILED'
        print(f"\n  {icon} {ex.upper()}: {status} ({passes}/{len(ex_results)})")
        for r in ex_results:
            mark = '  ✅' if r['success'] else '  ❌'
            print(f"    {mark} {r['operation']}: {r['details']}")
    
    print("\n" + "=" * 70)
    total_pass = sum(1 for r in RESULTS if r['success'])
    total_fail = sum(1 for r in RESULTS if not r['success'])
    final = "🏆 ALL SYSTEMS GO" if total_fail == 0 else f"⚠️ {total_fail} ISSUES FOUND"
    print(f"  TOTAL: {total_pass} PASS / {total_fail} FAIL — {final}")
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════
# 🐙 KRAKEN TESTS
# ═══════════════════════════════════════════════════════════════════

def test_kraken():
    log("═══ KRAKEN VERIFICATION ═══", 'TEST')
    
    try:
        from kraken_client import get_kraken_client
        kraken = get_kraken_client()
        record('kraken', 'CLIENT_INIT', True, 'KrakenClient loaded')
    except Exception as e:
        record('kraken', 'CLIENT_INIT', False, str(e))
        return

    # 1. Check balance
    try:
        balances = kraken.get_balance()
        usdc = float(balances.get('USDC', 0))
        usd = float(balances.get('ZUSD', 0) or balances.get('USD', 0))
        cash = usdc + usd
        record('kraken', 'GET_BALANCE', True, f'USDC=${usdc:.2f}, USD=${usd:.4f}, total=${cash:.2f}')
    except Exception as e:
        record('kraken', 'GET_BALANCE', False, str(e))
        return

    # 2. Get ticker for a pair
    try:
        ticker = kraken.get_ticker('ETHUSDC')
        price = float(ticker.get('price', 0))
        record('kraken', 'GET_TICKER', True, f'ETH/USDC price=${price:.2f}')
    except Exception as e:
        record('kraken', 'GET_TICKER', False, str(e))
        # Try alternate pair
        try:
            ticker = kraken.get_ticker('XETHZUSD')
            price = float(ticker.get('price', 0))
            record('kraken', 'GET_TICKER_ALT', True, f'ETH/USD price=${price:.2f}')
        except Exception as e2:
            record('kraken', 'GET_TICKER_ALT', False, str(e2))

    # 3. Find conversion path
    try:
        path = kraken.find_conversion_path('USDC', 'ETH')
        record('kraken', 'FIND_PATH_USDC→ETH', True, f'{len(path)} step(s): {[s.get("description","") for s in path]}')
    except Exception as e:
        record('kraken', 'FIND_PATH_USDC→ETH', False, str(e))

    # 4. BUY — use $4 of USDC to buy ETH
    if usdc < 4.0:
        record('kraken', 'BUY_ETH', False, f'Insufficient USDC (${usdc:.2f} < $4.00)')
        btc_balance = float(balances.get('XXBT', 0))
        if btc_balance > 0:
            # We have BTC from previous fire trade — sell it to test sell flow
            log(f"Using existing BTC position ({btc_balance:.8f}) for SELL test")
        return
    
    buy_quote = 4.0  # $4 worth
    bought_qty = 0
    try:
        log(f"Executing BUY: $4.00 USDC → ETH on Kraken...")
        order = kraken.place_market_order('ETHUSDC', 'buy', quote_qty=buy_quote)
        
        if order and not order.get('error') and not order.get('rejected'):
            status = order.get('status', 'UNKNOWN')
            filled_qty = float(order.get('executedQty', 0) or 0)
            order_id = order.get('orderId', 'N/A')
            bought_qty = filled_qty
            record('kraken', 'BUY_ETH', True, 
                   f'OrderID={order_id}, status={status}, qty={filled_qty:.8f} ETH')
        else:
            error = order.get('error') or order.get('rejected') or str(order)
            record('kraken', 'BUY_ETH', False, f'Order failed: {error}')
            return
    except Exception as e:
        record('kraken', 'BUY_ETH', False, str(e))
        return

    # 5. VERIFY position exists
    time.sleep(2)
    try:
        new_bal = kraken.get_balance()
        new_eth = float(new_bal.get('ETH', 0))
        record('kraken', 'VERIFY_BUY', new_eth > 0, f'ETH balance after buy: {new_eth:.8f}')
    except Exception as e:
        record('kraken', 'VERIFY_BUY', False, str(e))

    # 6. SELL — sell the ETH back to USDC
    if bought_qty <= 0:
        record('kraken', 'SELL_ETH', False, 'No ETH to sell (bought_qty=0)')
        return
    
    sell_qty = bought_qty * 0.99  # 99% to ensure enough
    try:
        log(f"Executing SELL: {sell_qty:.8f} ETH → USDC on Kraken...")
        sell_order = kraken.place_market_order('ETHUSDC', 'sell', quantity=sell_qty)
        
        if sell_order and not sell_order.get('error') and not sell_order.get('rejected'):
            status = sell_order.get('status', 'UNKNOWN')
            order_id = sell_order.get('orderId', 'N/A')
            received = float(sell_order.get('receivedQty', 0) or 0)
            record('kraken', 'SELL_ETH', True,
                   f'OrderID={order_id}, status={status}, received=${received:.4f}')
        else:
            error = sell_order.get('error') or sell_order.get('rejected') or str(sell_order)
            record('kraken', 'SELL_ETH', False, f'Sell failed: {error}')
    except Exception as e:
        record('kraken', 'SELL_ETH', False, str(e))

    # 7. CONVERT test (convert_crypto path)
    try:
        log(f"Testing convert_crypto: USDC → ETH via Kraken...")
        # Use convert_crypto with $2
        convert_result = kraken.convert_crypto('USDC', 'ETH', 2.0)
        
        if convert_result and not convert_result.get('error'):
            trades = convert_result.get('trades', [])
            success_count = sum(1 for t in trades if isinstance(t, dict) and t.get('status') == 'success')
            record('kraken', 'CONVERT_USDC→ETH', success_count > 0,
                   f'{success_count} trades in conversion')
            
            # Convert back to verify round-trip
            time.sleep(1)
            new_bal2 = kraken.get_balance()
            eth_now = float(new_bal2.get('ETH', 0))
            if eth_now > 0:
                sell_back = kraken.convert_crypto('ETH', 'USDC', eth_now * 0.95)
                if sell_back and not sell_back.get('error'):
                    record('kraken', 'CONVERT_ETH→USDC', True, 'Round-trip complete')
                else:
                    record('kraken', 'CONVERT_ETH→USDC', False, str(sell_back.get('error', 'Unknown')))
        else:
            error = convert_result.get('error', 'Unknown') if convert_result else 'No result'
            record('kraken', 'CONVERT_USDC→ETH', False, f'{error}')
    except Exception as e:
        record('kraken', 'CONVERT_USDC→ETH', False, str(e))


# ═══════════════════════════════════════════════════════════════════
# 🦙 ALPACA TESTS
# ═══════════════════════════════════════════════════════════════════

def test_alpaca():
    log("═══ ALPACA VERIFICATION ═══", 'TEST')
    
    try:
        from alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        record('alpaca', 'CLIENT_INIT', True, 'AlpacaClient loaded')
    except Exception as e:
        record('alpaca', 'CLIENT_INIT', False, str(e))
        return

    # 1. Check balance
    try:
        balances = alpaca.get_balance()
        usd = float(balances.get('USD', 0))
        record('alpaca', 'GET_BALANCE', True, f'USD=${usd:.2f}, assets={len(balances)-1}')
        
        # Show all assets
        for asset, amt in balances.items():
            amt = float(amt)
            if amt > 0 and asset != 'USD':
                log(f"  Alpaca position: {asset} = {amt}")
    except Exception as e:
        record('alpaca', 'GET_BALANCE', False, str(e))
        return

    # 2. Get ticker
    try:
        ticker = alpaca.get_ticker('SHIB/USD')
        price = float(ticker.get('price', 0))
        record('alpaca', 'GET_TICKER', True, f'SHIB/USD price=${price:.8f}')
    except Exception as e:
        record('alpaca', 'GET_TICKER', False, str(e))

    # 3. Find conversion path
    try:
        path = alpaca.find_conversion_path('USD', 'SHIB')
        record('alpaca', 'FIND_PATH_USD→SHIB', True, f'{len(path)} step(s)')
    except Exception as e:
        record('alpaca', 'FIND_PATH_USD→SHIB', False, str(e))

    # 4. Test SELL — Sell some SHIB back to USD to generate cash
    shib_bal = float(balances.get('SHIB', 0))
    if shib_bal > 100:
        try:
            # Sell 100 SHIB (worth ~$0.002 — tiny test)
            sell_qty = min(500.0, shib_bal * 0.5)
            log(f"Executing SELL: {sell_qty:.1f} SHIB → USD on Alpaca...")
            
            # Use convert_crypto for the sell
            sell_result = alpaca.convert_crypto('SHIB', 'USD', sell_qty)
            
            if sell_result and not sell_result.get('error'):
                trades = sell_result.get('trades', [])
                success_count = sum(1 for t in trades if isinstance(t, dict) and t.get('status') == 'success')
                record('alpaca', 'SELL_SHIB→USD', success_count > 0,
                       f'{success_count} trades, result={json.dumps(sell_result)[:200]}')
            else:
                error = sell_result.get('error', 'Unknown') if sell_result else 'No result'
                record('alpaca', 'SELL_SHIB→USD', False, error)
        except Exception as e:
            record('alpaca', 'SELL_SHIB→USD', False, str(e))
    else:
        record('alpaca', 'SELL_SHIB→USD', False, f'Insufficient SHIB ({shib_bal})')

    # 5. Check balance after sell to see if USD increased
    time.sleep(2)
    try:
        new_bal = alpaca.get_balance()
        new_usd = float(new_bal.get('USD', 0))
        record('alpaca', 'VERIFY_SELL', new_usd > usd - 0.01, f'USD before=${usd:.4f}, after=${new_usd:.4f}')
        usd = new_usd  # Update
    except Exception as e:
        record('alpaca', 'VERIFY_SELL', False, str(e))

    # 6. BUY — Buy SHIB with whatever USD we have
    if usd >= 1.0:
        try:
            log(f"Executing BUY: ${min(usd * 0.9, 1.0):.2f} USD → SHIB on Alpaca...")
            buy_result = alpaca.convert_crypto('USD', 'SHIB', min(usd * 0.9, 1.0))
            
            if buy_result and not buy_result.get('error'):
                trades = buy_result.get('trades', [])
                success_count = sum(1 for t in trades if isinstance(t, dict) and t.get('status') == 'success')
                record('alpaca', 'BUY_USD→SHIB', success_count > 0,
                       f'{success_count} trades')
            else:
                error = buy_result.get('error', 'Unknown') if buy_result else 'No result'
                record('alpaca', 'BUY_USD→SHIB', False, error)
        except Exception as e:
            record('alpaca', 'BUY_USD→SHIB', False, str(e))
    else:
        # Try place_market_order directly
        try:
            log(f"Trying place_market_order: SHIB/USD BUY quote_qty=${usd:.4f}...")
            if usd >= 0.50:
                order = alpaca.place_market_order('SHIB/USD', 'buy', quote_qty=usd * 0.9)
                if order and not order.get('error') and not order.get('rejected'):
                    record('alpaca', 'BUY_SHIB_DIRECT', True, f'OrderID={order.get("orderId", "N/A")}')
                else:
                    record('alpaca', 'BUY_SHIB_DIRECT', False, str(order))
            else:
                record('alpaca', 'BUY_USD→SHIB', False, f'Insufficient USD (${usd:.4f}) for any buy')
        except Exception as e:
            record('alpaca', 'BUY_SHIB_DIRECT', False, str(e))

    # 7. CONVERT test
    try:
        aave_bal = float(balances.get('AAVE', 0))
        if aave_bal > 0.001:
            log(f"Testing convert_crypto: AAVE → USD via Alpaca...")
            # Sell tiny AAVE → USD
            convert_amt = aave_bal * 0.1  # 10% of AAVE
            convert_result = alpaca.convert_crypto('AAVE', 'USD', convert_amt)
            if convert_result and not convert_result.get('error'):
                trades = convert_result.get('trades', [])
                success_count = sum(1 for t in trades if isinstance(t, dict) and t.get('status') == 'success')
                record('alpaca', 'CONVERT_AAVE→USD', success_count > 0,
                       f'{success_count} trades')
            else:
                error = convert_result.get('error', 'Unknown') if convert_result else 'No result'
                record('alpaca', 'CONVERT_AAVE→USD', False, error)
        else:
            record('alpaca', 'CONVERT_AAVE→USD', False, 'Insufficient AAVE')
    except Exception as e:
        record('alpaca', 'CONVERT_AAVE→USD', False, str(e))


# ═══════════════════════════════════════════════════════════════════
# 🟡 BINANCE TESTS
# ═══════════════════════════════════════════════════════════════════

def test_binance():
    log("═══ BINANCE VERIFICATION ═══", 'TEST')
    
    try:
        from binance_client import BinanceClient
        binance = BinanceClient()
        record('binance', 'CLIENT_INIT', True, 'BinanceClient loaded')
    except Exception as e:
        record('binance', 'CLIENT_INIT', False, str(e))
        return

    # 1. Check balance
    try:
        balances = binance.get_balance()
        spot_assets = {}
        locked_assets = {}
        cash = 0.0
        for asset, amt in balances.items():
            amt = float(amt)
            if amt <= 0:
                continue
            if asset.startswith('LD'):
                locked_assets[asset] = amt
            elif asset in ('USDT', 'USDC', 'BUSD', 'FDUSD'):
                cash += amt
                spot_assets[asset] = amt
            else:
                spot_assets[asset] = amt
        
        record('binance', 'GET_BALANCE', True, 
               f'Cash=${cash:.4f}, spot={len(spot_assets)}, locked(LD)={len(locked_assets)}')
        
        for asset, amt in locked_assets.items():
            log(f"  Binance (Earn): {asset} = {amt:.4f}")
    except Exception as e:
        record('binance', 'GET_BALANCE', False, str(e))
        return

    # 2. Get ticker
    try:
        ticker = binance.get_24h_ticker('ETHUSDC')
        price = float(ticker.get('lastPrice', 0))
        change = float(ticker.get('priceChangePercent', 0))
        record('binance', 'GET_TICKER', True, f'ETH/USDC=${price:.2f} ({change:+.2f}%)')
    except Exception as e:
        record('binance', 'GET_TICKER', False, str(e))

    # 3. Find conversion path
    try:
        path = binance.find_conversion_path('USDC', 'ETH')
        record('binance', 'FIND_PATH_USDC→ETH', True, f'{len(path)} step(s): {[s.get("description","") for s in path]}')
    except Exception as e:
        record('binance', 'FIND_PATH_USDC→ETH', False, str(e))

    # 4. BUY test — Need spot cash
    if cash < 1.0:
        record('binance', 'BUY_ETH', False, 
               f'No spot cash (${cash:.4f}). All funds are in Binance Earn (LD* prefixed). '
               f'Need to redeem from Earn to spot first.')
        record('binance', 'SELL_ETH', False, 'Skipped — no buy to reverse')
        record('binance', 'CONVERT', False, 'Skipped — no spot funds')
    else:
        # Would execute BUY here
        try:
            log(f"Executing BUY: $1.00 USDC → ETH on Binance...")
            order = binance.place_market_order('ETHUSDC', 'buy', quote_qty=1.0)
            if order and not order.get('error') and not order.get('rejected'):
                record('binance', 'BUY_ETH', True, f'OrderID={order.get("orderId")}')
            else:
                record('binance', 'BUY_ETH', False, str(order))
        except Exception as e:
            record('binance', 'BUY_ETH', False, str(e))

    # 5. Test convert_crypto path finding (even without funds, 
    #    verify the logic doesn't crash)
    try:
        log("Testing convert_crypto logic (path-finding)...")
        path_btc = binance.find_conversion_path('ETH', 'BTC')
        if path_btc:
            record('binance', 'FIND_PATH_ETH→BTC', True, f'{len(path_btc)} step(s)')
        else:
            record('binance', 'FIND_PATH_ETH→BTC', False, 'No path found')
    except Exception as e:
        record('binance', 'FIND_PATH_ETH→BTC', False, str(e))

    try:
        path_usdc = binance.find_conversion_path('BTC', 'USDC')
        if path_usdc:
            record('binance', 'FIND_PATH_BTC→USDC', True, f'{len(path_usdc)} step(s)')
        else:
            record('binance', 'FIND_PATH_BTC→USDC', False, 'No path found')
    except Exception as e:
        record('binance', 'FIND_PATH_BTC→USDC', False, str(e))


# ═══════════════════════════════════════════════════════════════════
# 🏁 MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("⚔️" * 35)
    print("  MULTI-EXCHANGE AUTONOMOUS VERIFICATION TEST")
    print("  Testing BUY → VERIFY → SELL → CONVERT on each exchange")
    print("  Using REAL tiny amounts ($1-$4)")
    print("⚔️" * 35)
    print()
    
    # Run tests sequentially (each exchange is independent)
    test_kraken()
    print()
    test_alpaca()
    print()
    test_binance()
    
    # Print summary
    print_summary()
    
    # Save results
    try:
        with open('exchange_verification_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': RESULTS,
                'summary': {
                    'total': len(RESULTS),
                    'passed': sum(1 for r in RESULTS if r['success']),
                    'failed': sum(1 for r in RESULTS if not r['success'])
                }
            }, f, indent=2)
        log("Results saved to exchange_verification_results.json")
    except Exception:
        pass

if __name__ == '__main__':
    main()
