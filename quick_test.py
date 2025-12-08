#!/usr/bin/env python3
"""
🔧 QUICK TEST - Verify all systems working
"""
import os
import sys

print("Testing imports and system readiness...\n")

# Test 1: Binance
try:
    from binance.client import Client
    print("✅ python-binance installed")
except ImportError:
    print("❌ python-binance NOT installed")
    sys.exit(1)

# Test 2: Krakenex  
try:
    import krakenex
    print("✅ krakenex installed")
except ImportError:
    print("❌ krakenex NOT installed")
    sys.exit(1)

# Test 3: Load env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv installed")
except ImportError:
    print("❌ python-dotenv NOT installed")
    sys.exit(1)

# Test 4: Check API keys
binance_key = os.getenv('BINANCE_API_KEY')
if binance_key:
    print(f"✅ BINANCE_API_KEY configured")
else:
    print("❌ BINANCE_API_KEY missing from .env")
    sys.exit(1)

# Test 5: Try Binance connection
try:
    binance_secret = os.getenv('BINANCE_API_SECRET')
    client = Client(binance_key, binance_secret)
    account = client.get_account()
    print("✅ Binance connection successful")
    
    # Show balances
    balances = account['balances']
    usdt = next((b for b in balances if b['asset'] == 'USDT'), None)
    usdc = next((b for b in balances if b['asset'] == 'USDC'), None)
    
    if usdt or usdc:
        if usdt:
            free = float(usdt['free'])
            print(f"   💰 USDT: ${free:.2f} available")
        if usdc:
            free = float(usdc['free'])
            print(f"   💰 USDC: ${free:.2f} available")
    else:
        print("   ⚠️  No USDT/USDC balance found")
        
except Exception as e:
    print(f"❌ Binance connection failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ ALL SYSTEMS OPERATIONAL")
print("="*50)
print("\nReady to run: python3 aureon_unified_ecosystem.py\n")
