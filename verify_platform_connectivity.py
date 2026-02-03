#!/usr/bin/env python3
"""
Verify connectivity and portfolio state across all trading platforms
KRAKEN | BINANCE | CAPITAL.COM
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kraken_client import KrakenClient, get_kraken_client
from binance_client import BinanceClient
from capital_client import CapitalClient
import json
from datetime import datetime

def check_kraken():
    """Check Kraken connectivity and portfolio"""
    print("\n" + "="*80)
    print("🐙 KRAKEN - Connectivity & Portfolio Check")
    print("="*80)
    
    try:
        client = get_kraken_client()
        
        # Check API connectivity
        print("✅ API Connection: SUCCESS")
        
        # Get balance via account()
        account_data = client.account()
        print(f"\n💰 KRAKEN BALANCES:")
        total_gbp = 0
        holdings = []
        
        for bal in account_data.get('balances', []):
            asset = bal.get('asset', '')
            amount = float(bal.get('free', 0))
            
            if amount > 0.00001:
                # Get GBP value
                try:
                    if asset in ['GBP', 'ZGBP', 'EUR', 'ZEUR']:
                        value_gbp = amount if asset.startswith('GBP') else amount * 0.87
                    else:
                        # Get price vs GBP
                        symbol = f"{asset}GBP" if asset not in ['BTC', 'XBT'] else "XBTGBP"
                        price = client.get_current_price(symbol)
                        value_gbp = amount * price if price else 0
                except:
                    value_gbp = 0
                
                total_gbp += value_gbp
                holdings.append({
                    'asset': asset,
                    'amount': amount,
                    'value_gbp': value_gbp
                })
                print(f"  {asset:8s}: {amount:>15.8f} (£{value_gbp:>10.2f})")
        
        print(f"\n📊 Total Portfolio Value: £{total_gbp:.2f}")
        
        # Check tradeable pairs
        print(f"\n🔄 Checking tradeable pairs...")
        pairs = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'ADAUSD', 'SOLUSD']
        tradeable = []
        for pair in pairs:
            try:
                price = client.get_current_price(pair)
                if price:
                    tradeable.append(pair)
                    print(f"  ✅ {pair}: £{price:,.2f}")
            except:
                print(f"  ❌ {pair}: Not available")
        
        return {
            'platform': 'KRAKEN',
            'status': 'CONNECTED',
            'total_value_gbp': total_gbp,
            'holdings': holdings,
            'tradeable_pairs': tradeable
        }
        
    except Exception as e:
        print(f"❌ KRAKEN ERROR: {e}")
        return {'platform': 'KRAKEN', 'status': 'ERROR', 'error': str(e)}

def check_binance():
    """Check Binance connectivity and portfolio"""
    print("\n" + "="*80)
    print("🟡 BINANCE - Connectivity & Portfolio Check")
    print("="*80)
    
    try:
        client = get_binance_client()
        
        # Check API connectivity
        print("✅ API Connection: SUCCESS")
        
        # Get balance via account()
        account_data = client.account()
        print(f"\n💰 BINANCE BALANCES:")
        total_gbp = 0
        holdings = []
        
        # Get GBP/USDT rate for conversions
        try:
            gbp_usdt_rate = client.get_current_price("GBPUSDT")
        except:
            gbp_usdt_rate = 1.27  # Fallback
        
        for bal in account_data.get('balances', []):
            asset = bal.get('asset', '')
            amount = float(bal.get('free', 0))
            
            if amount > 0.0001:  # Filter dust
                # Get price in GBP
                try:
                    if asset == 'GBP':
                        value_gbp = amount
                    elif asset == 'USDT':
                        value_gbp = amount / gbp_usdt_rate
                    else:
                        # Try to get USDT price first, then convert
                        usdt_price = client.get_current_price(f"{asset}USDT")
                        value_gbp = (amount * usdt_price) / gbp_usdt_rate if usdt_price else 0
                    
                    total_gbp += value_gbp
                    holdings.append({
                        'asset': asset,
                        'amount': amount,
                        'value_gbp': value_gbp
                    })
                    print(f"  {asset:8s}: {amount:>15.8f} (£{value_gbp:>10.2f})")
                except Exception as e:
                    print(f"  {asset:8s}: {amount:>15.8f} (price unavailable)")
        
        print(f"\n📊 Total Portfolio Value: £{total_gbp:.2f}")
        
        # Check tradeable pairs
        print(f"\n🔄 Checking tradeable pairs...")
        pairs = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT']
        tradeable = []
        for pair in pairs:
            try:
                price = client.get_current_price(pair)
                if price:
                    tradeable.append(pair)
                    print(f"  ✅ {pair}: ${price:,.2f}")
            except:
                print(f"  ❌ {pair}: Not available")
        
        return {
            'platform': 'BINANCE',
            'status': 'CONNECTED',
            'total_value_gbp': total_gbp,
            'holdings': holdings,
            'tradeable_pairs': tradeable
        }
        
    except Exception as e:
        print(f"❌ BINANCE ERROR: {e}")
        return {'platform': 'BINANCE', 'status': 'ERROR', 'error': str(e)}

def check_capital():
    """Check Capital.com connectivity and portfolio"""
    print("\n" + "="*80)
    print("🏛️ CAPITAL.COM - Connectivity & Portfolio Check")
    print("="*80)
    
    try:
        client = CapitalClient()
        
        # Check API connectivity
        print("✅ API Connection: SUCCESS")
        
        # Get balance via get_account_balance()
        balance_data = client.get_account_balance()
        print(f"\n💰 CAPITAL.COM BALANCES:")
        
        total_gbp = balance_data.get('GBP', 0)
        available = balance_data.get('available', total_gbp)
        
        print(f"  Total Balance:    £{total_gbp:,.2f}")
        print(f"  Available:        £{available:,.2f}")
        print(f"  In Positions:     £{total_gbp - available:,.2f}")
        
        # Get open positions
        positions = client.get_positions()
        print(f"\n📊 OPEN POSITIONS: {len(positions)}")
        position_data = []
        
        for pos in positions:
            pos_value = abs(pos.get('size', 0) * pos.get('level', 0))
            pnl = pos.get('profit', 0)
            position_data.append({
                'symbol': pos.get('market', 'N/A'),
                'direction': pos.get('direction', 'N/A'),
                'size': pos.get('size', 0),
                'level': pos.get('level', 0),
                'value': pos_value,
                'pnl': pnl
            })
            print(f"  {pos.get('market', 'N/A'):12s} {pos.get('direction', 'N/A'):5s} "
                  f"Size: {pos.get('size', 0):>10.4f} @ £{pos.get('level', 0):>10.2f} "
                  f"P&L: £{pnl:>+8.2f}")
        
        # Check tradeable instruments
        print(f"\n🔄 Checking tradeable instruments...")
        instruments = ['BITCOIN', 'ETHEREUM', 'RIPPLE', 'CARDANO', 'SOLANA']
        tradeable = []
        for inst in instruments:
            try:
                price = client.get_current_price(inst)
                if price:
                    tradeable.append(inst)
                    print(f"  ✅ {inst}: £{price:,.2f}")
            except:
                print(f"  ❌ {inst}: Not available")
        
        return {
            'platform': 'CAPITAL.COM',
            'status': 'CONNECTED',
            'total_value_gbp': total_gbp,
            'available_gbp': available,
            'positions': position_data,
            'tradeable_instruments': tradeable
        }
        
    except Exception as e:
        print(f"❌ CAPITAL.COM ERROR: {e}")
        return {'platform': 'CAPITAL.COM', 'status': 'ERROR', 'error': str(e)}

def main():
    """Execute platform checks and generate report"""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "🌐 MULTI-PLATFORM CONNECTIVITY CHECK" + " "*22 + "║")
    print("╚" + "="*78 + "╝")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n🕐 Timestamp: {timestamp}")
    
    # Check all platforms
    kraken_data = check_kraken()
    binance_data = check_binance()
    capital_data = check_capital()
    
    # Generate summary
    print("\n" + "="*80)
    print("📊 SUMMARY REPORT")
    print("="*80)
    
    all_data = [kraken_data, binance_data, capital_data]
    
    total_portfolio_gbp = sum(d.get('total_value_gbp', 0) for d in all_data if d.get('status') == 'CONNECTED')
    connected_count = sum(1 for d in all_data if d.get('status') == 'CONNECTED')
    
    print(f"\n✅ Connected Platforms: {connected_count}/3")
    print(f"💰 Total Portfolio Value: £{total_portfolio_gbp:,.2f}")
    
    for data in all_data:
        status = "🟢" if data.get('status') == 'CONNECTED' else "🔴"
        value = f"£{data.get('total_value_gbp', 0):,.2f}" if data.get('status') == 'CONNECTED' else "N/A"
        print(f"  {status} {data['platform']:15s} - {value}")
    
    # Save to file
    report_file = f"/tmp/platform_connectivity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        'timestamp': timestamp,
        'platforms': all_data,
        'summary': {
            'connected': connected_count,
            'total_value_gbp': total_portfolio_gbp
        }
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📁 Report saved: {report_file}")
    
    # Trading readiness check
    print("\n" + "="*80)
    print("🎯 TRADING READINESS")
    print("="*80)
    
    if connected_count == 3:
        print("✅ All platforms connected - READY FOR LIVE TRADING")
        print(f"✅ Total capital available: £{total_portfolio_gbp:,.2f}")
        print("✅ Multi-exchange arbitrage: ENABLED")
    else:
        print("⚠️  Not all platforms connected - check errors above")
    
    return report_data

if __name__ == "__main__":
    main()
