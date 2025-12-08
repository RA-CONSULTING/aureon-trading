#!/usr/bin/env python3
"""
🔧 COMPREHENSIVE SYSTEM DIAGNOSTIC
Tests all components step by step to find the issue
"""
import os
import sys
import json
import traceback

sys.path.insert(0, '/workspaces/aureon-trading')

def step(n, title):
    print(f"\n{n}️⃣ {title}")
    print("   " + "-"*60)

def success(msg):
    print(f"   ✅ {msg}")

def error(msg):
    print(f"   ❌ {msg}")

def warning(msg):
    print(f"   ⚠️  {msg}")

print("\n" + "="*70)
print("🔧 COMPREHENSIVE SYSTEM DIAGNOSTIC")
print("="*70)

# Step 1: Environment
step(1, "Environment Check")
try:
    from dotenv import load_dotenv
    load_dotenv()
    success("dotenv loaded")
    
    binance_key = os.getenv('BINANCE_API_KEY')
    binance_secret = os.getenv('BINANCE_API_SECRET')
    
    if binance_key and binance_secret:
        success(f"Binance API key: {binance_key[:10]}...")
    else:
        error("Missing Binance API keys")
        sys.exit(1)
except Exception as e:
    error(f"dotenv: {e}")
    sys.exit(1)

# Step 2: Core Imports
step(2, "Core Library Imports")
try:
    from binance.client import Client
    success("binance.client")
except ImportError as e:
    error(f"binance.client: {e}")
    sys.exit(1)

try:
    import krakenex
    success("krakenex")
except ImportError as e:
    error(f"krakenex: {e}")
    sys.exit(1)

try:
    import requests
    success("requests")
except ImportError as e:
    error(f"requests: {e}")
    sys.exit(1)

# Step 3: Exchange Clients
step(3, "Exchange Client Imports")
try:
    from binance_client import BinanceClient
    success("binance_client.BinanceClient")
except Exception as e:
    error(f"binance_client: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from kraken_client import KrakenClient
    success("kraken_client.KrakenClient")
except Exception as e:
    error(f"kraken_client: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from alpaca_client import AlpacaClient
    success("alpaca_client.AlpacaClient")
except Exception as e:
    error(f"alpaca_client: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from capital_client import CapitalClient
    success("capital_client.CapitalClient")
except Exception as e:
    error(f"capital_client: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 4: Unified Client
step(4, "Unified Exchange Client")
try:
    from unified_exchange_client import UnifiedExchangeClient, MultiExchangeClient
    success("unified_exchange_client.UnifiedExchangeClient")
    success("unified_exchange_client.MultiExchangeClient")
except Exception as e:
    error(f"unified_exchange_client: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 5: Multi-exchange Orchestrator
step(5, "Multi-Exchange Orchestrator")
try:
    from aureon_unified_ecosystem import MultiExchangeOrchestrator
    success("MultiExchangeOrchestrator imported")
except Exception as e:
    error(f"MultiExchangeOrchestrator: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 6: Main Ecosystem Import
step(6, "Main Ecosystem Import")
try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem
    success("AureonKrakenEcosystem imported")
except Exception as e:
    error(f"AureonKrakenEcosystem: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

# Step 7: Binance Connection
step(7, "Binance API Connection")
try:
    client = Client(binance_key, binance_secret)
    account = client.get_account()
    success(f"Binance connected, account: {account.get('accountType', 'unknown')}")
    
    # Check balances
    balances = account.get('balances', [])
    usdc = next((b for b in balances if b['asset'] in ['USDC', 'USDT']), None)
    
    if usdc:
        free = float(usdc.get('free', 0))
        locked = float(usdc.get('locked', 0))
        success(f"USDC/USDT Balance: ${free:.2f} free, ${locked:.2f} locked")
        
        if free < 5:
            warning(f"Low balance (${free:.2f}), minimum $5 recommended")
    else:
        warning("No USDC/USDT found")
        
except Exception as e:
    error(f"Binance connection: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 8: Ecosystem Initialization
step(8, "Ecosystem Initialization")
try:
    ecosystem = AureonKrakenEcosystem(initial_balance=100.0, dry_run=True)
    success(f"Ecosystem initialized (dry_run={ecosystem.dry_run})")
    success(f"Initial equity: £{ecosystem.total_equity_gbp:.2f}")
except Exception as e:
    error(f"Ecosystem init: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

# Step 9: State File
step(9, "State File")
if os.path.exists('aureon_kraken_state.json'):
    with open('aureon_kraken_state.json') as f:
        state = json.load(f)
    success(f"State file exists (iteration {state.get('iteration', 0)})")
else:
    warning("State file not found (will be created on first run)")

print("\n" + "="*70)
print("✅ ALL DIAGNOSTICS PASSED - SYSTEM READY")
print("="*70)

print("\n📝 Next Steps:")
print("   1. Run: python3 aureon_unified_ecosystem.py")
print("   2. Or test with: python3 run_ecosystem_debug.py")
print("\n")
