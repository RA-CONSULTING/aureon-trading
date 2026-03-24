# -*- coding: utf-8 -*-
"""
Test script to validate Aurora Pro Dashboard data output.
Run this to see exactly what the dashboard is returning and why win rate shows 5%.
"""
import json
import os
import sys
from pathlib import Path

def check_cost_basis():
    """Check if cost_basis_history.json has valid position data."""
    path = Path("/workspaces/aureon-trading/cost_basis_history.json")
    if not path.exists():
        print("❌ cost_basis_history.json NOT FOUND")
        return 0
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        positions = data if isinstance(data, dict) else {}
        count = len(positions)
        print(f"\n✅ cost_basis_history.json found with {count} positions")
        
        if count > 0:
            sample_symbols = list(positions.keys())[:5]
            for symbol in sample_symbols:
                pos = positions[symbol]
                qty = pos.get('total_quantity', 0)
                avg_cost = pos.get('avg_entry_price', 0)
                total = pos.get('total_cost', 0)
                print(f"   📍 {symbol}: {qty} @ ${avg_cost:.2f} = ${total:,.2f}")
        
        return count
    except Exception as e:
        print(f"❌ Error reading cost_basis_history.json: {e}")
        return 0

def check_active_position():
    """Check if active_position.json has current position data."""
    path = Path("/workspaces/aureon-trading/active_position.json")
    if not path.exists():
        print("❌ active_position.json NOT FOUND")
        return 0
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        positions = data if isinstance(data, dict) else {}
        count = len(positions)
        print(f"\n✅ active_position.json found with {count} positions")
        
        if count > 0:
            sample_symbols = list(positions.keys())[:3]
            for symbol in sample_symbols:
                pos = positions[symbol]
                qty = pos.get('quantity', 0)
                entry = pos.get('entry_price', 0)
                current = pos.get('current_price', 0)
                pnl_pct = ((current - entry) / entry * 100) if entry > 0 else 0
                print(f"   📍 {symbol}: {qty} @ ${entry:.2f} → ${current:.2f} | PnL: {pnl_pct:.2f}%")
        
        return count
    except Exception as e:
        print(f"❌ Error reading active_position.json: {e}")
        return 0

def check_dashboard_snapshot():
    """Check if dashboard_snapshot.json has fallback data."""
    path = Path("/workspaces/aureon-trading/dashboard_snapshot.json")
    if not path.exists():
        print("❌ dashboard_snapshot.json NOT FOUND")
        return 0
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        positions = data.get('positions', [])
        count = len(positions)
        print(f"\n✅ dashboard_snapshot.json found with {count} positions")
        
        if count > 0:
            for pos in positions[:3]:
                symbol = pos.get('symbol', 'UNKNOWN')
                qty = pos.get('quantity', 0)
                pnl = pos.get('pnlPercent', 0)
                print(f"   📍 {symbol}: {qty} units | PnL%: {pnl:.2f}%")
        
        return count
    except Exception as e:
        print(f"❌ Error reading dashboard_snapshot.json: {e}")
        return 0

def analyze_win_rates():
    """Analyze which positions are winners vs losers."""
    print("\n" + "="*60)
    print("🎯 WIN RATE ANALYSIS")
    print("="*60)
    
    # Check cost_basis
    print("\n📊 Analyzing cost_basis_history.json...")
    path = Path("/workspaces/aureon-trading/cost_basis_history.json")
    if path.exists():
        try:
            with open(path, 'r') as f:
                positions = json.load(f)
            
            # Try to fetch live prices
            try:
                import requests
                symbols = list(positions.keys())[:10]
                
                # Try CoinGecko
                gecko_map = {
                    'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
                    'ADA': 'cardano', 'DOT': 'polkadot', 'MATIC': 'matic-network',
                    'AVAX': 'avalanche-2', 'ARB': 'arbitrum', 'OP': 'optimism',
                    'DOGE': 'dogecoin', 'XRP': 'ripple', 'LTC': 'litecoin'
                }
                
                ids = ','.join([gecko_map.get(s, s.lower()) for s in symbols if s in gecko_map])
                if ids:
                    resp = requests.get(
                        f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd",
                        timeout=5
                    )
                    if resp.status_code == 200:
                        prices = resp.json()
                        
                        winners = 0
                        losers = 0
                        for symbol in symbols:
                            if symbol not in positions:
                                continue
                            
                            pos = positions[symbol]
                            avg_cost = float(pos.get('avg_entry_price', 0) or 0)
                            
                            # Map to CoinGecko ID
                            gecko_id = gecko_map.get(symbol, symbol.lower())
                            if gecko_id in prices and 'usd' in prices[gecko_id]:
                                current = prices[gecko_id]['usd']
                                pnl_pct = ((current - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
                                
                                if pnl_pct > 0:
                                    winners += 1
                                    result = "✅ WIN"
                                else:
                                    losers += 1
                                    result = "❌ LOSS"
                                
                                print(f"   {result} | {symbol}: ${avg_cost:.2f} → ${current:.2f} | {pnl_pct:+.2f}%")
                
                if winners + losers > 0:
                    win_rate = (winners / (winners + losers)) * 100
                    print(f"\n   📈 Win Rate: {winners}/{winners + losers} = {win_rate:.1f}%")
                else:
                    print("\n   ⚠️  Could not fetch live prices to calculate win rate")
            
            except Exception as e:
                print(f"   ⚠️  Could not fetch live prices: {e}")
        
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    print("\n" + "="*60)
    print("🔍 AURORA PRO DASHBOARD DATA VALIDATION")
    print("="*60)
    
    cost_basis_count = check_cost_basis()
    active_count = check_active_position()
    snapshot_count = check_dashboard_snapshot()
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    print(f"cost_basis_history.json:  {cost_basis_count} positions")
    print(f"active_position.json:     {active_count} positions")
    print(f"dashboard_snapshot.json:  {snapshot_count} positions")
    
    if cost_basis_count == 0 and active_count == 0 and snapshot_count == 0:
        print("\n⚠️  WARNING: No position data found in any source!")
        print("   This explains why dashboard shows '--' and win rate is invalid")
    elif snapshot_count > 0 and cost_basis_count == 0:
        print("\n⚠️  WARNING: Only snapshot fallback has data!")
        print("   cost_basis_history.json is empty - live API likely not working")
    
    analyze_win_rates()
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
