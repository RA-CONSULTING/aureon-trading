# -*- coding: utf-8 -*-
"""
Comprehensive dashboard portfolio test.
Simulates exactly what refresh_portfolio() does.
"""
import json
import os
import asyncio
from pathlib import Path

async def fetch_live_prices(symbols):
    """Mimic _fetch_live_prices_for_symbols"""
    import requests
    
    gecko_map = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana',
        'ADA': 'cardano', 'DOT': 'polkadot', 'MATIC': 'matic-network',
        'AVAX': 'avalanche-2', 'ARB': 'arbitrum', 'OP': 'optimism',
        'DOGE': 'dogecoin', 'XRP': 'ripple', 'LTC': 'litecoin',
        'BNB': 'binancecoin', 'FUN': 'funtoken'
    }
    
    prices = {}
    
    # Extract unique base assets
    bases = set()
    for sym in symbols:
        # Try to find the base (first 1-5 chars)
        for length in range(min(5, len(sym)), 0, -1):
            potential = sym[:length]
            if potential in gecko_map:
                bases.add(potential)
                break
    
    if bases:
        try:
            ids = ','.join([gecko_map[b] for b in bases])
            resp = requests.get(
                f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd",
                timeout=5
            )
            if resp.status_code == 200:
                gecko_prices = resp.json()
                # Map back to symbols
                for sym in symbols:
                    for length in range(min(5, len(sym)), 0, -1):
                        potential = sym[:length]
                        if potential in gecko_map and gecko_map[potential] in gecko_prices:
                            prices[sym] = gecko_prices[gecko_map[potential]].get('usd', 0)
                            break
        except Exception as e:
            print(f"Error fetching prices: {e}")
    
    return prices

async def test_refresh_portfolio():
    """Test what refresh_portfolio() should return"""
    print("=" * 70)
    print("SIMULATING refresh_portfolio() from aureon_pro_dashboard.py")
    print("=" * 70)
    
    # Load cost_basis_history
    cb_path = Path('/workspaces/aureon-trading/cost_basis_history.json')
    if not cb_path.exists():
        print("❌ cost_basis_history.json not found!")
        return
    
    with open(cb_path, 'r') as f:
        cost_basis_data = json.load(f)
    
    fallback_pos = cost_basis_data.get('positions', {})
    print(f"\n✅ Loaded {len(fallback_pos)} positions from cost_basis_history.json")
    
    # Sort by total_cost (highest value positions first)
    sorted_positions = sorted(
        [(k, v) for k, v in fallback_pos.items() 
         if isinstance(v, dict) and v.get('total_cost', 0) > 0.01],
        key=lambda x: x[1].get('total_cost', 0),
        reverse=True
    )[:20]  # Top 20 by value
    
    print(f"📊 Top 20 positions by value: {len(sorted_positions)}")
    
    # Fetch live prices
    symbols_to_price = [sym for sym, _ in sorted_positions]
    print(f"\n💰 Fetching live prices for {len(symbols_to_price)} symbols...")
    print(f"   Symbols: {symbols_to_price[:5]} ... (and {len(symbols_to_price)-5} more)")
    
    live_prices = await fetch_live_prices(symbols_to_price)
    print(f"✅ Fetched prices for {len(live_prices)} symbols")
    
    # Build positions array
    positions = []
    total_value = 0.0
    total_cost = 0.0
    winners = 0
    losers = 0
    
    for symbol, pos_data in sorted_positions:
        qty = float(pos_data.get('total_quantity', 0) or 0)
        avg_entry = float(pos_data.get('avg_entry_price', 0) or 0)
        cost_basis = float(pos_data.get('total_cost', 0) or qty * avg_entry)
        exchange = pos_data.get('exchange', 'unknown')
        
        # Use LIVE price if available, else fall back to entry price
        current_price = live_prices.get(symbol, avg_entry)
        current_value = qty * current_price
        pnl = current_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        positions.append({
            'symbol': symbol,
            'quantity': qty,
            'avgCost': avg_entry,
            'currentPrice': current_price,
            'currentValue': current_value,
            'unrealizedPnl': pnl,
            'pnlPercent': pnl_pct,
            'exchange': exchange
        })
        
        total_value += current_value
        total_cost += cost_basis
        
        if pnl_pct > 0:
            winners += 1
        else:
            losers += 1
    
    # Calculate portfolio metrics
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    win_rate = (winners / len(positions) * 100) if positions else 0
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 PORTFOLIO SUMMARY")
    print("=" * 70)
    print(f"Total Positions: {len(positions)}")
    print(f"Total Cost Basis: ${total_cost:,.2f}")
    print(f"Total Current Value: ${total_value:,.2f}")
    print(f"Total Unrealized P&L: ${total_pnl:,.2f} ({total_pnl_pct:+.2f}%)")
    print(f"\nWin Rate: {winners}/{len(positions)} = {win_rate:.1f}%")
    print(f"Winners: {winners} ✅")
    print(f"Losers: {losers} ❌")
    
    # Show top 5 positions
    print("\n" + "=" * 70)
    print("🏆 TOP 5 POSITIONS BY VALUE")
    print("=" * 70)
    for i, pos in enumerate(positions[:5], 1):
        status = "✅" if pos['pnlPercent'] > 0 else "❌"
        print(f"{i}. {pos['symbol']:12} | {pos['quantity']:8.4f} @ ${pos['avgCost']:10.2f} → ${pos['currentPrice']:10.2f}")
        print(f"   Value: ${pos['currentValue']:12,.2f} | P&L: ${pos['unrealizedPnl']:+10,.2f} ({pos['pnlPercent']:+6.2f}%) {status}")
    
    # This is what would be returned as self.portfolio
    portfolio = {
        'positions': positions,
        'totalValue': total_value,
        'totalCost': total_cost,
        'unrealizedPnl': total_pnl,
        'unrealizedPnlPercent': total_pnl_pct,
        'winRate': win_rate,
        'cash': 0  # Not tracked in cost_basis
    }
    
    print("\n" + "=" * 70)
    print("✅ DASHBOARD SHOULD DISPLAY:")
    print("=" * 70)
    print(f"Win Rate: {win_rate:.0f}% (not 5%!)")
    print(f"Portfolio P&L: {total_pnl_pct:+.2f}%")
    print(f"Total Value: ${total_value:,.2f}")
    print(f"Positions: {len(positions)}")
    
    return portfolio

# Run the test
if __name__ == "__main__":
    portfolio = asyncio.run(test_refresh_portfolio())
