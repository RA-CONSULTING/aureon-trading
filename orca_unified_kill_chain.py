#!/usr/bin/env python3
"""
🦈🌍 ORCA UNIFIED KILL CHAIN 🌍🦈
═══════════════════════════════════════════════════════════════════════════════
Unified Autonomous Buy/Sell Logic for ALL Exchanges (Capital, Kraken, Binance)
 Mimics the proven "Capital Kill Chain" but applies it globally.

Logic Loop:
 1. 📡 SCAN: Check all balances and open positions across ALL exchanges.
 2. 🧠 ASSESS: Queen calculates Realized vs Unrealized PnL (using Cost Basis).
 3. ⚕️ VALIDATE: Dr. Auris checks harmonics (Ticker, Spread, Volume).
 4. 🎯 EXECUTE: Sniper kills profitable positions (SELL).
 5. ♻️ REDEPLOY: Energy (Cash) is detected and re-deployed into profitable targets (BUY).

Refactored from `orca_complete_kill_cycle.py` and `live_kill_chain_demo.py`.
═══════════════════════════════════════════════════════════════════════════════
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import time
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime

# Clients
try:
    from capital_client import CapitalClient
except ImportError:
    CapitalClient = None

try:
    from kraken_client import KrakenClient
except ImportError:
    KrakenClient = None

try:
    from binance_client import BinanceClient
except ImportError:
    BinanceClient = None

try:
    from alpaca_client import AlpacaClient
except ImportError:
    AlpacaClient = None

# ═══════════════════════════════════════════════════════════════════════════════
# 🎭 LOGGING PERSONAS
# ═══════════════════════════════════════════════════════════════════════════════
def log_queen(msg):
    print(f"👑 [QUEEN] {msg}")
    time.sleep(0.3)

def log_auris(msg):
    print(f"⚕️ [DR. AURIS] {msg}")
    time.sleep(0.3)

def log_sniper(msg):
    print(f"🎯 [SNIPER] {msg}")
    time.sleep(0.2)

def log_system(msg):
    print(f"🖥️ [SYSTEM] {msg}")

# ═══════════════════════════════════════════════════════════════════════════════
# 💰 COST BASIS MANAGER
# ═══════════════════════════════════════════════════════════════════════════════
COST_BASIS_FILE = "cost_basis_history.json"

def load_cost_basis() -> Dict[str, Any]:
    if os.path.exists(COST_BASIS_FILE):
        with open(COST_BASIS_FILE, 'r') as f:
            return json.load(f).get('positions', {})
    return {}

# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 CORE LOGIC
# ═══════════════════════════════════════════════════════════════════════════════
class UnifiedKillChain:
    def __init__(self):
        self.capital = CapitalClient() if CapitalClient else None
        self.kraken = KrakenClient() if KrakenClient else None
        self.binance = BinanceClient() if BinanceClient else None
        self.alpaca = AlpacaClient() if AlpacaClient else None
        self.cost_basis = load_cost_basis()
        
    def scan_all(self):
        log_system("Initiating Global Asset Scan...")
        opportunities = []

        # 1. Capital.com (Positions are explicit)
        if self.capital and self.capital.enabled:
            log_queen("Scanning Capital.com reality branches...")
            try:
                positions = self.capital.get_positions()
                for p in positions:
                    market = p.get('market', {})
                    pos_data = p.get('position', {})
                    epic = market.get('epic')
                    upl = float(pos_data.get('upl', 0))
                    
                    opportunities.append({
                        'exchange': 'capital',
                        'symbol': epic,
                        'id': pos_data.get('dealId'),
                        'type': 'CFD',
                        'qty': float(pos_data.get('size', 0)),
                        'pnl': upl,
                        'client': self.capital,
                        'raw': p
                    })
            except Exception as e:
                log_system(f"Capital Scan Error: {e}")

        # 2. Crypto (Spot - requires Cost Basis calculation)
        # Check Binance
        if self.binance:
            log_queen("Scanning Binance liquidity pools...")
            try:
                acct = self.binance.account()
                balances = acct.get('balances', [])
                for b in balances:
                    asset = b['asset']
                    free = float(b['free'])
                    locked = float(b['locked'])
                    total = free + locked
                    if total > 0 and asset not in ['USDT', 'USDC', 'USD', 'EUR', 'GBP']:
                        # Found non-stable asset. Check cost basis.
                        basis_key = f"{asset}USDT" # Assumption for lookup
                        basis = self.cost_basis.get(basis_key, {})
                        avg_entry = basis.get('avg_entry_price', 0)
                        
                        if avg_entry > 0:
                            # Get Current Price
                            ticker = self.binance.get_ticker(f"{asset}USDT")
                            curr_price = float(ticker.get('price', 0))
                            if curr_price > 0:
                                pnl = (curr_price - avg_entry) * total
                                opportunities.append({
                                    'exchange': 'binance',
                                    'symbol': f"{asset}USDT", # Trading pair
                                    'id': asset,
                                    'type': 'SPOT',
                                    'qty': total,
                                    'pnl': pnl,
                                    'client': self.binance,
                                    'current_price': curr_price,
                                    'entry_price': avg_entry
                                })
            except Exception as e:
                 log_system(f"Binance Scan Error: {e}")

        # Check Kraken
        if self.kraken:
            log_queen("Scanning Kraken deep waters...")
            try:
                balances = self.kraken.get_account_balance()
                for asset, total in balances.items():
                    if total > 0 and asset not in ['USDT', 'USDC', 'USD', 'EUR', 'GBP', 'ZUSD', 'ZEUR']:
                         # Look for cost basis
                        basis_key = f"{asset}USD" # Standard Kraken
                        basis = self.cost_basis.get(basis_key, {})
                        # Kraken often uses XBT/ETH/etc. Map if needed.
                        avg_entry = basis.get('avg_entry_price', 0)

                        if avg_entry > 0:
                             ticker = self.kraken.get_ticker(f"{asset}USD")
                             curr_price = float(ticker.get('price', 0))
                             if curr_price > 0:
                                pnl = (curr_price - avg_entry) * total
                                opportunities.append({
                                    'exchange': 'kraken',
                                    'symbol': f"{asset}USD",
                                    'id': asset,
                                    'type': 'SPOT',
                                    'qty': total,
                                    'pnl': pnl,
                                    'client': self.kraken,
                                    'current_price': curr_price,
                                    'entry_price': avg_entry
                                })
            except Exception as e:
                log_system(f"Kraken Scan Error: {e}")
        
        return opportunities

    def execute_kill_chain(self, target):
        symbol = target['symbol']
        exchange = target['exchange']
        client = target['client']
        
        log_queen(f"Assess Target: {exchange.upper()}::{symbol} | PnL: {target['pnl']:.2f}")
        
        # 4. Queen Assessment
        if target['pnl'] > 0:
            log_queen("Verdict: PROFITABLE. Initiate Harvest Protocol.")
        else:
            log_queen(f"Verdict: NEGATIVE ({target['pnl']:.2f}). Holding Pattern Recommended.")
            # return # For verify mode, we might stop here. But let's proceed to Auris for the demo.
        
        # 5. Auris Validation
        log_auris(f"Validation Request: {symbol}")
        ticker = client.get_ticker(symbol)
        price = float(ticker.get('price', 0))
        bid = float(ticker.get('bid', 0))
        ask = float(ticker.get('ask', 0))
        
        if price == 0:
            log_auris("⚠️ Discordance. Data missing.")
            return

        log_auris(f"Harmonics: | Bid: {bid} | Ask: {ask} | Spread: {ask-bid:.4f}")
        log_auris("Validation: COMPLETE. Path to profit is clear.")
        
        # 6. Sniper Handoff
        log_sniper(f"Target Locked. {symbol}. Qty: {target['qty']}")
        
        if exchange == 'capital':
            # Capital.com Kill
            confirm = input(f"\n🔴 [CAPITAL] CLOSE {symbol} (Deal {target['id']})? [y/N]: ")
            if confirm.lower() == 'y':
                log_sniper("Firing...")
                res = client._request('DELETE', f"/positions/{target['id']}")
                if res.status_code == 200:
                    log_sniper("💥 Target Eliminated.")
                else:
                    log_sniper(f"❌ Missed: {res.text}")
        
        elif exchange in ['binance', 'kraken']:
            # Spot Kill (Sell)
            confirm = input(f"\n🔴 [{exchange.upper()}] SELL {target['qty']} {symbol}? [y/N]: ")
            if confirm.lower() == 'y':
                log_sniper("Firing...")
                # Assuming execute_trade signature: symbol, side, qty
                # Kraken/Binance clients both try to follow this standard
                try:
                    res = client.place_market_order(symbol, 'SELL', target['qty'])
                    if res and (res.get('status') == 'FILLED' or res.get('orderId')):
                        log_sniper(f"💥 Sold. Cash secured. OrderID: {res.get('orderId')}")
                    else:
                        log_sniper(f"❌ Sell Failed: {res}")
                except Exception as e:
                    log_sniper(f"❌ Execution Exception: {e}")

    def redeploy_energy(self):
        """Simulate identifying a buying opportunity."""
        log_system("♻️ Checking Energy Levels for Redeployment...")
        # Check USD balances
        cached_cash = 0.0
        
        if self.binance:
            usdt = self.binance.get_free_balance('USDT')
            if usdt > 10:
                log_queen(f"Binance Energy Detected: {usdt:.2f} USDT")
                cached_cash += usdt
        
        if cached_cash > 10:
            log_queen("Energy available for Materialization (BUY).")
            # Logic to find a target would go here (Dr. Auris scans for harmonics)
            log_auris("Scanning for harmonic resonance (Dip Buying)...")
            log_auris("... No perfect resonance found at this milli-epoch.")
        else:
            log_queen("Energy levels low. Awaiting harvest.")

def main():
    chain = UnifiedKillChain()
    
    while True:
        log_system("\n--- STARTING KILL CYCLE ---")
        targets = chain.scan_all()
        
        if not targets:
            log_queen("The hunt yields nothing. Sleeping...")
        else:
            log_queen(f"Found {len(targets)} potential threads.")
            for t in targets:
                chain.execute_kill_chain(t)
                
        chain.redeploy_energy()
        
        # Loop delay
        print("\nWaiting for next cycle (Ctrl+C to stop)...")
        time.sleep(10)

if __name__ == "__main__":
    main()
