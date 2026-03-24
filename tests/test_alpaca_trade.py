#!/usr/bin/env python3
"""
🦙 ALPACA BATTLEFIELD TEST SCRIPT 🦙

Test trading on Alpaca - swap ETH for something else!

Usage:
    python test_alpaca_trade.py

Make sure you have in your .env:
    ALPACA_API_KEY=your_key
    ALPACA_SECRET_KEY=your_secret
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from alpaca_client import AlpacaClient

def main():
    print("\n🦙 ═══════════════════════════════════════════════════════════")
    print("   ALPACA BATTLEFIELD TEST - Let's see what we've got!")
    print("   ═══════════════════════════════════════════════════════════\n")
    
    # Check keys
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ ALPACA API KEYS NOT FOUND!")
        print("\n   Add these to your .env file:")
        print("   ALPACA_API_KEY=your_key")
        print("   ALPACA_SECRET_KEY=your_secret")
        return
    
    # Don't print credential material (even partially) to stdout.
    print("✅ API Key: [set]")
    print("✅ Secret: [set]")
    
    client = AlpacaClient()
    
    # 1. Account Status
    print("\n📊 ACCOUNT STATUS:")
    print("─" * 50)
    account = client.get_account()
    if not account:
        print("❌ Could not connect to Alpaca")
        return
    
    cash = float(account.get('cash', 0))
    buying_power = float(account.get('buying_power', 0))
    portfolio_value = float(account.get('portfolio_value', 0))
    status = account.get('status', 'unknown')
    crypto_status = account.get('crypto_status', 'N/A')
    trading_blocked = account.get('trading_blocked', False)
    
    print(f"   💵 Cash: ${cash:.2f}")
    print(f"   💰 Buying Power: ${buying_power:.2f}")
    print(f"   📈 Portfolio Value: ${portfolio_value:.2f}")
    print(f"   📋 Status: {status}")
    print(f"   🪙 Crypto Status: {crypto_status}")
    print(f"   🚫 Trading Blocked: {trading_blocked}")
    
    if trading_blocked:
        print("\n❌ TRADING IS BLOCKED ON THIS ACCOUNT!")
        return
    
    # 2. Current Positions
    print("\n📦 CURRENT POSITIONS:")
    print("─" * 50)
    positions = client.get_positions()
    
    eth_position = None
    if positions:
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            qty = float(pos.get('qty', 0))
            current_price = float(pos.get('current_price', 0))
            market_value = float(pos.get('market_value', 0))
            unrealized_pl = float(pos.get('unrealized_pl', 0))
            cost_basis = float(pos.get('cost_basis', 0))
            
            pl_pct = (unrealized_pl / cost_basis * 100) if cost_basis > 0 else 0
            
            print(f"   {symbol}:")
            print(f"      Qty: {qty:.6f}")
            print(f"      Price: ${current_price:.2f}")
            print(f"      Value: ${market_value:.2f}")
            print(f"      P/L: ${unrealized_pl:.2f} ({pl_pct:+.2f}%)")
            
            if 'ETH' in symbol.upper():
                eth_position = pos
    else:
        print("   No positions found")
    
    # 3. Available Crypto
    print("\n🪙 TRADABLE CRYPTO PAIRS:")
    print("─" * 50)
    cryptos = client.get_tradable_crypto_symbols('USD')
    print(f"   Found {len(cryptos)} pairs:")
    for c in cryptos[:15]:
        print(f"      • {c}")
    if len(cryptos) > 15:
        print(f"      ... and {len(cryptos) - 15} more")
    
    # 4. Suggest a trade
    print("\n🎯 TRADE SUGGESTION:")
    print("─" * 50)
    
    if eth_position:
        eth_qty = float(eth_position.get('qty', 0))
        eth_value = float(eth_position.get('market_value', 0))
        print(f"   You have ETH: {eth_qty:.6f} (${eth_value:.2f})")
        
        # Get quotes for potential swaps
        swap_targets = ['BTC/USD', 'SOL/USD', 'DOGE/USD', 'AVAX/USD']
        print(f"\n   Potential swap targets:")
        
        quotes = client.get_latest_crypto_quotes(swap_targets)
        for symbol in swap_targets:
            if symbol in quotes:
                quote = quotes[symbol]
                bid = float(quote.get('bp', 0))
                ask = float(quote.get('ap', 0))
                print(f"      {symbol}: Bid ${bid:.4f} / Ask ${ask:.4f}")
        
        print(f"\n   💡 To swap ETH to BTC, you would:")
        print(f"      1. Sell {eth_qty:.6f} ETH/USD")
        print(f"      2. Buy ${eth_value:.2f} worth of BTC/USD")
        
        # Interactive?
        print("\n   ⚠️  This script is READ-ONLY for safety.")
        print("   The main ecosystem will trade automatically when running!")
        
    elif cash > 10:
        print(f"   You have ${cash:.2f} cash available")
        print(f"   The ecosystem will deploy scouts automatically!")
    else:
        print("   No ETH position and low cash. Add funds to Alpaca!")
    
    print("\n🦙 ═══════════════════════════════════════════════════════════")
    print("   Alpaca battlefield READY! Run the main ecosystem to trade.")
    print("   ═══════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    main()
