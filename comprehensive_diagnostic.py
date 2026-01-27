#!/usr/bin/env python3
"""
🔧 COMPREHENSIVE SYSTEM DIAGNOSTIC
Tests all components step by step to find the issue
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import traceback
from pathlib import Path

sys.path.insert(0, '/workspaces/aureon-trading')

issues: list[str] = []
warnings_list: list[str] = []

def step(n, title):
    print(f"\n{n}️⃣ {title}")
    print("   " + "-"*60)

def success(msg):
    print(f"   ✅ {msg}")

def error(msg):
    issues.append(msg)
    print(f"   ❌ {msg}")

def warning(msg):
    warnings_list.append(msg)
    print(f"   ⚠️  {msg}")

print("\n" + "="*70)
print("🔧 COMPREHENSIVE SYSTEM DIAGNOSTIC")
print("="*70)

# Step 1: Environment
step(1, "Environment Check")
try:
    from dotenv import load_dotenv

    repo_dir = Path(__file__).resolve().parent
    dotenv_path = repo_dir / ".env"
    loaded = load_dotenv(dotenv_path=dotenv_path)
    if loaded:
        success(f"Loaded .env from {dotenv_path}")
    else:
        warning("No .env file found (falling back to environment)")

    def has_real_value(value: str | None) -> bool:
        if not value:
            return False
        placeholder_prefixes = ["YOUR_", "changeme", "example", "sample"]
        lower_value = value.lower()
        return not any(value.startswith(prefix) or lower_value.startswith(prefix) for prefix in placeholder_prefixes)

    binance_key = os.getenv("BINANCE_API_KEY")
    binance_secret = os.getenv("BINANCE_API_SECRET")
    kraken_key = os.getenv("KRAKEN_API_KEY")
    kraken_secret = os.getenv("KRAKEN_API_SECRET")

    binance_keys_ready = has_real_value(binance_key) and has_real_value(binance_secret)
    kraken_keys_ready = has_real_value(kraken_key) and has_real_value(kraken_secret)

    if binance_keys_ready:
        success(f"Binance API key: {binance_key[:10]}...")
    else:
        error("Missing or placeholder Binance API keys")

    if kraken_keys_ready:
        success(f"Kraken API key: {kraken_key[:10]}...")
    else:
        warning("Missing or placeholder Kraken API keys (optional)")
except Exception as e:
    error(f"dotenv: {e}")

binance_client_available = False
kraken_available = False

# Step 2: Core Imports
step(2, "Core Library Imports")
try:
    from binance.client import Client

    binance_client_available = True
    success("binance.client")
except ImportError as e:
    error(f"binance.client: {e}")

try:
    import krakenex

    kraken_available = True
    success("krakenex")
except ImportError as e:
    warning(f"krakenex: {e}")

try:
    import requests

    success("requests")
except ImportError as e:
    error(f"requests: {e}")

# Step 3: Exchange Clients
step(3, "Exchange Client Imports")
try:
    from binance_client import BinanceClient

    success("binance_client.BinanceClient")
except Exception as e:
    error(f"binance_client: {e}")
    traceback.print_exc()

try:
    from kraken_client import KrakenClient

    success("kraken_client.KrakenClient")
except Exception as e:
    warning(f"kraken_client: {e}")
    traceback.print_exc()

try:
    from alpaca_client import AlpacaClient

    success("alpaca_client.AlpacaClient")
except Exception as e:
    warning(f"alpaca_client: {e}")
    traceback.print_exc()

try:
    from capital_client import CapitalClient

    success("capital_client.CapitalClient")
except Exception as e:
    warning(f"capital_client: {e}")
    traceback.print_exc()

# Step 4: Unified Client
step(4, "Unified Exchange Client")
try:
    from unified_exchange_client import UnifiedExchangeClient, MultiExchangeClient

    success("unified_exchange_client.UnifiedExchangeClient")
    success("unified_exchange_client.MultiExchangeClient")
except Exception as e:
    error(f"unified_exchange_client: {e}")
    traceback.print_exc()

# Step 5: Multi-exchange Orchestrator
step(5, "Multi-Exchange Orchestrator")
try:
    from aureon_unified_ecosystem import MultiExchangeOrchestrator

    success("MultiExchangeOrchestrator imported")
except Exception as e:
    error(f"MultiExchangeOrchestrator: {e}")
    traceback.print_exc()

# Step 6: Main Ecosystem Import
step(6, "Main Ecosystem Import")
try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem

    success("AureonKrakenEcosystem imported")
except Exception as e:
    error(f"AureonKrakenEcosystem: {e}")
    print("\nFull traceback:")
    traceback.print_exc()

# Step 7: Binance Connection
step(7, "Binance API Connection")
if not binance_keys_ready:
    warning("Skipping Binance connection: API keys missing or placeholder")
elif not binance_client_available:
    warning("Skipping Binance connection: python-binance not installed")
else:
    try:
        client = Client(binance_key, binance_secret)
        account = client.get_account()
        success(f"Binance connected, account: {account.get('accountType', 'unknown')}")

        balances = account.get("balances", [])
        usdc = next((b for b in balances if b["asset"] in ["USDC", "USDT"]), None)

        if usdc:
            free = float(usdc.get("free", 0))
            locked = float(usdc.get("locked", 0))
            success(f"USDC/USDT Balance: ${free:.2f} free, ${locked:.2f} locked")

            if free < 5:
                warning(f"Low balance (${free:.2f}), minimum $5 recommended")
        else:
            warning("No USDC/USDT found")

    except Exception as e:
        warning(f"Binance connection: {e}")
        traceback.print_exc()

# Step 8: Ecosystem Initialization
step(8, "Ecosystem Initialization")
try:
    ecosystem = AureonKrakenEcosystem(initial_balance=100.0, dry_run=True)

    success(f"Ecosystem initialized (dry_run={ecosystem.dry_run})")
    success(f"Initial equity: £{ecosystem.total_equity_gbp:.2f}")
except Exception as e:
    warning(f"Ecosystem init: {e}")
    print("\nFull traceback:")
    traceback.print_exc()

# Step 9: State File
step(9, "State File")
if os.path.exists("aureon_kraken_state.json"):
    with open("aureon_kraken_state.json") as f:
        state = json.load(f)
    success(f"State file exists (iteration {state.get('iteration', 0)})")
else:
    warning("State file not found (will be created on first run)")

print("\n" + "=" * 70)
if issues:
    print(f"⚠️  DIAGNOSTIC COMPLETED WITH {len(issues)} ISSUE(S)")
else:
    print("✅ ALL DIAGNOSTICS PASSED - SYSTEM READY")
print("=" * 70)

if issues:
    print("\nOutstanding issues:")
    for i, msg in enumerate(issues, start=1):
        print(f"   {i}. {msg}")

if warnings_list:
    print("\nWarnings:")
    for i, msg in enumerate(warnings_list, start=1):
        print(f"   {i}. {msg}")

print("\n📝 Next Steps:")
print("   1. Run: python3 aureon_unified_ecosystem.py")
print("   2. Or test with: python3 run_ecosystem_debug.py")
print("\n")
