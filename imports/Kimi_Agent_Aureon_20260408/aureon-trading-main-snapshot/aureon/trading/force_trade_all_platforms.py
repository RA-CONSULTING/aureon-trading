#!/usr/bin/env python3
"""
🔥🔥🔥 FORCE TRADE ALL PLATFORMS - VERIFY ALL SYSTEMS CONNECTED 🔥🔥🔥
═══════════════════════════════════════════════════════════════════════════════

FORCES A SMALL TEST TRADE ON EVERY EXCHANGE TO VERIFY:
1. API connectivity is real (not phantom)
2. Trading is enabled (not dry run)
3. All systems are talking to each other
4. No spoofing or ghost processes

Gary Leckey | January 2026 | FORCE THE ISSUE
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

# FORCE LIVE MODE
os.environ['LIVE'] = '1'
os.environ['KRAKEN_DRY_RUN'] = 'false'
os.environ['BINANCE_DRY_RUN'] = 'false'
os.environ['ALPACA_DRY_RUN'] = 'false'
os.environ['CAPITAL_DEMO'] = 'false'

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not installed")

import time
import json
from datetime import datetime

from queen_force_trade_governance import evaluate_queen_force_trade_authority

print("\n" + "=" * 70)
print("🔥🔥🔥 FORCE TRADE ALL PLATFORMS - LIVE VERIFICATION 🔥🔥🔥")
print("=" * 70)
print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   LIVE Mode: {os.getenv('LIVE', '0')}")
print("=" * 70 + "\n")

decision = evaluate_queen_force_trade_authority()
print(f"👑 Queen Governance: {decision.reason}")
if decision.missing_requirements:
    print("   Missing requirements:")
    for requirement in decision.missing_requirements:
        print(f"   - {requirement}")
if not decision.allowed:
    print("🛑 Aborting platform force-trade verification: only the unified Queen may force trades.")
    sys.exit(1)

# Results tracking
results = {
    'kraken': {'status': 'PENDING', 'trade': None, 'error': None},
    'binance': {'status': 'PENDING', 'trade': None, 'error': None},
    'alpaca': {'status': 'PENDING', 'trade': None, 'error': None},
    'capital': {'status': 'PENDING', 'trade': None, 'error': None},
}

# ════════════════════════════════════════════════════════════════════════════
# 🐙 KRAKEN - Force Trade
# ════════════════════════════════════════════════════════════════════════════
print("\n🐙 KRAKEN: Testing trade execution...")
try:
    from kraken_client import KrakenClient, get_kraken_client
    
    kraken = get_kraken_client()
    print(f"   Dry Run Mode: {kraken.dry_run}")
    
    # Get balance first
    balance = kraken.get_balance()
    print(f"   Balance: {json.dumps(balance, indent=2)[:200]}...")
    
    # Find a small tradeable amount (Kraken uses ZUSD for USD)
    usd_balance = float(balance.get('ZUSD', balance.get('USD', balance.get('ZUSD.F', 0))))
    print(f"   USD Balance: ${usd_balance:.2f}")
    
    if usd_balance >= 10.0:
        # Try to buy minimum BTC
        try:
            # Get BTC price
            price_info = kraken.best_price('XXBTZUSD')
            btc_price = float(price_info.get('price', 100000))
            print(f"   BTC Price: ${btc_price:.2f}")
            
            # Calculate minimum order (Kraken min is usually 0.0001 BTC)
            min_btc = 0.0001
            min_cost = min_btc * btc_price
            
            if usd_balance >= min_cost * 1.01:  # Include fee buffer
                print(f"   🔥 Attempting LIVE BUY {min_btc} BTC (~${min_cost:.2f})...")
                
                # Execute market buy using correct method
                order = kraken.place_market_order(
                    symbol='XXBTZUSD',
                    side='buy',
                    quantity=min_btc
                )
                print(f"   ✅ KRAKEN ORDER: {order}")
                results['kraken'] = {'status': 'SUCCESS', 'trade': order, 'error': None}
            else:
                print(f"   ⚠️ Insufficient balance for min trade (need ${min_cost:.2f})")
                results['kraken'] = {'status': 'INSUFFICIENT_FUNDS', 'trade': None, 'error': f'Need ${min_cost:.2f}'}
        except Exception as e:
            print(f"   ❌ Trade error: {e}")
            results['kraken'] = {'status': 'TRADE_ERROR', 'trade': None, 'error': str(e)}
    else:
        print(f"   ⚠️ Insufficient USD balance (need $10+, have ${usd_balance:.2f})")
        results['kraken'] = {'status': 'NO_BALANCE', 'trade': None, 'error': f'Need $10+, have ${usd_balance:.2f}'}
        
except Exception as e:
    print(f"   ❌ Kraken error: {e}")
    results['kraken'] = {'status': 'CONNECTION_ERROR', 'trade': None, 'error': str(e)}

# ════════════════════════════════════════════════════════════════════════════
# 🟡 BINANCE - Force Trade
# ════════════════════════════════════════════════════════════════════════════
print("\n🟡 BINANCE: Testing trade execution...")
try:
    from binance_client import get_binance_client

    binance = get_binance_client()
    print(f"   Dry Run Mode: {binance.dry_run}")
    
    # Get balance
    balance = binance.get_balance()
    print(f"   Balance: {json.dumps(balance, indent=2)[:200]}...")
    
    usdt_balance = float(balance.get('USDT', 0))
    gbp_balance = float(balance.get('GBP', 0))
    print(f"   USDT Balance: ${usdt_balance:.2f}")
    print(f"   GBP Balance: £{gbp_balance:.2f}")
    
    if usdt_balance >= 10.0:  # Binance min is usually ~$10
        try:
            # Get BTC price
            price_info = binance.best_price('BTCUSDT')
            btc_price = float(price_info.get('price', 100000))
            print(f"   BTC Price: ${btc_price:.2f}")
            
            # Calculate minimum order
            min_btc = 0.0001
            min_cost = min_btc * btc_price
            
            if usdt_balance >= min_cost * 1.01:
                print(f"   🔥 Attempting LIVE BUY {min_btc} BTC (~${min_cost:.2f})...")
                
                order = binance.place_market_order(
                    symbol='BTCUSDT',
                    side='BUY',
                    quantity=min_btc
                )
                print(f"   ✅ BINANCE ORDER: {order}")
                results['binance'] = {'status': 'SUCCESS', 'trade': order, 'error': None}
            else:
                print(f"   ⚠️ Insufficient for min trade")
                results['binance'] = {'status': 'INSUFFICIENT_FUNDS', 'trade': None, 'error': f'Need ${min_cost:.2f}'}
        except Exception as e:
            print(f"   ❌ Trade error: {e}")
            results['binance'] = {'status': 'TRADE_ERROR', 'trade': None, 'error': str(e)}
    elif gbp_balance >= 10.0:
        try:
            # Try GBP pairs for UK users
            print(f"   🔥 Attempting LIVE BUY with GBP...")
            price_info = binance.best_price('BTCGBP')
            btc_price = float(price_info.get('price', 80000))
            min_btc = 0.0001
            min_cost = min_btc * btc_price
            
            if gbp_balance >= min_cost * 1.01:
                order = binance.place_market_order(
                    symbol='BTCGBP',
                    side='BUY',
                    quantity=min_btc
                )
                print(f"   ✅ BINANCE ORDER (GBP): {order}")
                results['binance'] = {'status': 'SUCCESS', 'trade': order, 'error': None}
            else:
                results['binance'] = {'status': 'INSUFFICIENT_FUNDS', 'trade': None, 'error': f'Need £{min_cost:.2f}'}
        except Exception as e:
            print(f"   ❌ Trade error: {e}")
            results['binance'] = {'status': 'TRADE_ERROR', 'trade': None, 'error': str(e)}
    else:
        print(f"   ⚠️ No USDT/GBP balance to trade (need $10+)")
        results['binance'] = {'status': 'NO_BALANCE', 'trade': None, 'error': 'No USDT or GBP'}
        
except Exception as e:
    print(f"   ❌ Binance error: {e}")
    results['binance'] = {'status': 'CONNECTION_ERROR', 'trade': None, 'error': str(e)}

# ════════════════════════════════════════════════════════════════════════════
# 🦙 ALPACA - Force Trade
# ════════════════════════════════════════════════════════════════════════════
print("\n🦙 ALPACA: Testing trade execution...")
try:
    from alpaca_client import AlpacaClient
    
    alpaca = AlpacaClient()
    print(f"   Paper Trading: {alpaca.paper}")
    
    # Get account
    account = alpaca.get_account()
    cash = float(account.get('cash', 0))
    buying_power = float(account.get('buying_power', 0))
    print(f"   Cash: ${cash:.2f}")
    print(f"   Buying Power: ${buying_power:.2f}")
    
    if buying_power >= 5.0:
        try:
            # Buy $5 worth of BTC/USD (minimum viable trade)
            print(f"   🔥 Attempting LIVE BUY $5 of BTC/USD...")
            
            order = alpaca.place_order(
                symbol='BTC/USD',
                qty=None,  # Use notional instead
                side='buy',
                type='market',
                time_in_force='gtc',
                notional=5.0  # $5 worth
            )
            print(f"   ✅ ALPACA ORDER: {order}")
            results['alpaca'] = {'status': 'SUCCESS', 'trade': order, 'error': None}
        except Exception as e:
            # If crypto fails, try a fractional stock
            try:
                print(f"   Crypto failed ({e}), trying fractional AAPL...")
                order = alpaca.place_order(
                    symbol='AAPL',
                    qty=0.01,  # Fractional share
                    side='buy',
                    type='market',
                    time_in_force='day'
                )
                print(f"   ✅ ALPACA ORDER (stock): {order}")
                results['alpaca'] = {'status': 'SUCCESS', 'trade': order, 'error': None}
            except Exception as e2:
                print(f"   ❌ Trade error: {e2}")
                results['alpaca'] = {'status': 'TRADE_ERROR', 'trade': None, 'error': str(e2)}
    else:
        print(f"   ⚠️ Insufficient buying power (need $5+, have ${buying_power:.2f})")
        results['alpaca'] = {'status': 'NO_BALANCE', 'trade': None, 'error': f'Need $5+, have ${buying_power:.2f}'}
        
except Exception as e:
    print(f"   ❌ Alpaca error: {e}")
    results['alpaca'] = {'status': 'CONNECTION_ERROR', 'trade': None, 'error': str(e)}

# ════════════════════════════════════════════════════════════════════════════
# 💼 CAPITAL.COM - Force Trade (CFDs only - no crypto)
# ════════════════════════════════════════════════════════════════════════════
print("\n💼 CAPITAL.COM: Testing trade execution...")
try:
    from capital_client import CapitalClient
    
    capital = CapitalClient()
    print(f"   Enabled: {capital.enabled}")
    print(f"   Demo Mode: {capital.demo_mode}")
    
    if not capital.enabled:
        print(f"   ⚠️ Capital client disabled (check credentials)")
        results['capital'] = {'status': 'DISABLED', 'trade': None, 'error': 'Client disabled'}
    else:
        # Get account balance
        balance = capital.get_account_balance()
        print(f"   Balance: {balance}")
        
        total_balance = sum(balance.values())
        if total_balance >= 10.0:
            try:
                # Capital.com is CFDs - try EURUSD (forex) or US500 (index)
                print(f"   🔥 Attempting LIVE BUY 0.1 lot EURUSD CFD...")
                
                # Use small CFD position
                order = capital.place_market_order(
                    symbol='EURUSD',  # Forex pair
                    side='BUY',
                    quantity=0.1  # 0.1 lot = 10000 units
                )
                
                if order.get('error'):
                    # Try US500 index instead
                    print(f"   EURUSD failed, trying US500 index CFD...")
                    order = capital.place_market_order(
                        symbol='US500',
                        side='BUY',
                        quantity=0.01  # Micro lot
                    )
                
                if order.get('error'):
                    print(f"   ❌ Trade error: {order}")
                    results['capital'] = {'status': 'TRADE_ERROR', 'trade': None, 'error': str(order)}
                else:
                    print(f"   ✅ CAPITAL ORDER: {order}")
                    results['capital'] = {'status': 'SUCCESS', 'trade': order, 'error': None}
            except Exception as e:
                print(f"   ❌ Trade error: {e}")
                results['capital'] = {'status': 'TRADE_ERROR', 'trade': None, 'error': str(e)}
        else:
            print(f"   ⚠️ Insufficient balance (need £10+)")
            results['capital'] = {'status': 'NO_BALANCE', 'trade': None, 'error': 'Insufficient funds'}
        
except ImportError as e:
    print(f"   ⚠️ Capital client import error: {e}")
    results['capital'] = {'status': 'NOT_AVAILABLE', 'trade': None, 'error': str(e)}
except Exception as e:
    print(f"   ❌ Capital error: {e}")
    results['capital'] = {'status': 'CONNECTION_ERROR', 'trade': None, 'error': str(e)}

# ════════════════════════════════════════════════════════════════════════════
# 📊 FINAL RESULTS
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("📊 FORCE TRADE RESULTS - ALL PLATFORMS")
print("=" * 70)

success_count = 0
for platform, result in results.items():
    emoji = "✅" if result['status'] == 'SUCCESS' else "❌"
    if result['status'] == 'SUCCESS':
        success_count += 1
    print(f"   {emoji} {platform.upper()}: {result['status']}")
    if result['error']:
        print(f"      Error: {result['error']}")
    if result['trade']:
        print(f"      Trade: {str(result['trade'])[:100]}...")

print("\n" + "=" * 70)
print(f"🎯 SUMMARY: {success_count}/4 platforms executed trades successfully")
if success_count == 4:
    print("🔥🔥🔥 ALL SYSTEMS OPERATIONAL - NO PHANTOM PROCESSES! 🔥🔥🔥")
elif success_count > 0:
    print("⚠️ PARTIAL SUCCESS - Check failed platforms")
else:
    print("❌ NO TRADES EXECUTED - CHECK API KEYS AND BALANCES!")
print("=" * 70)

# Save results
with open('force_trade_results.json', 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'live_mode': os.getenv('LIVE', '0'),
        'results': results
    }, f, indent=2, default=str)
print(f"\n📁 Results saved to force_trade_results.json")
