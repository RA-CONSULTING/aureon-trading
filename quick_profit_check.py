#!/usr/bin/env python
"""Quick live position and profit monitor."""
import sys
import json
import time
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
sys.path.insert(0, '/workspaces/aureon-trading')

from alpaca_client import AlpacaClient
from kraken_client import KrakenClient, get_kraken_client  
from binance_client import BinanceClient, get_binance_client

# Try to import Thought Bus for Queen integration
try:
    from aureon_thought_bus import ThoughtBus, THOUGHT_BUS_AVAILABLE
except:
    THOUGHT_BUS_AVAILABLE = False

PROFIT_STATE_FILE = "live_profit_state.json"
BALANCE_SNAPSHOT_FILE = "_pre_trade_balance_snapshot.json"

def load_cost_basis():
    """Load cost basis history."""
    if Path('cost_basis_history.json').exists():
        with open('cost_basis_history.json') as f:
            data = json.load(f)
            return data.get('positions', {})
    return {}

def get_current_price(exchange, symbol):
    """Get current price for a symbol."""
    try:
        if exchange == 'kraken':
            client = get_kraken_client()
            ticker = client.get_ticker(symbol + 'USD')
            return float(ticker.get('last', 0))
        elif exchange == 'binance':
            client = get_binance_client()
            ticker = client.get_ticker_price(symbol + 'USDT')
            return float(ticker.get('price', 0))
    except:
        return 0


def save_balance_snapshot() -> Dict[str, Any]:
    """
    Save a complete balance snapshot across ALL 3 exchanges.
    Uses atomic write (tmp + rename) to prevent corruption.
    Called before any trade cycle begins and after each cycle ends.
    """
    snapshot = {
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "exchanges": {}
    }
    total_usd = 0.0

    # ── Kraken ──
    try:
        kraken = get_kraken_client()
        balances = kraken.get_balance()
        kraken_bal = {}
        if balances:
            for asset, amount in balances.items():
                if amount > 0.0:
                    kraken_bal[asset] = amount
        snapshot["exchanges"]["kraken"] = {"balances": kraken_bal}
    except Exception as e:
        snapshot["exchanges"]["kraken"] = {"error": str(e)}

    # ── Alpaca ──
    try:
        alpaca = AlpacaClient()
        account = alpaca.get_account()
        positions = alpaca.get_positions()
        alpaca_bal = {
            "cash": float(account.get("cash", 0)),
            "portfolio_value": float(account.get("portfolio_value", 0)),
        }
        if positions:
            for pos in positions:
                alpaca_bal[pos["symbol"]] = {
                    "qty": float(pos["qty"]),
                    "market_value": float(pos["market_value"]),
                    "avg_entry_price": float(pos["avg_entry_price"]),
                    "current_price": float(pos["current_price"]),
                }
        snapshot["exchanges"]["alpaca"] = {"balances": alpaca_bal}
        total_usd += alpaca_bal["portfolio_value"]
    except Exception as e:
        snapshot["exchanges"]["alpaca"] = {"error": str(e)}

    # ── Binance (was MISSING — this is the key fix) ──
    try:
        binance = get_binance_client()
        balances = binance.get_balance() if binance else {}
        binance_bal = {}
        if balances:
            for asset, amount in balances.items():
                if amount > 0.0:
                    binance_bal[asset] = amount
        snapshot["exchanges"]["binance"] = {"balances": binance_bal}
    except Exception as e:
        snapshot["exchanges"]["binance"] = {"error": str(e)}

    snapshot["total_estimated_usd"] = total_usd  # Rough — Kraken/Binance need pricing

    # Atomic write: temp file → rename
    try:
        fd, tmp_path = tempfile.mkstemp(dir=".", suffix=".tmp", prefix="_snap_")
        with os.fdopen(fd, 'w') as f:
            json.dump(snapshot, f, indent=2)
        os.replace(tmp_path, BALANCE_SNAPSHOT_FILE)
    except Exception as e:
        print(f"⚠️ Failed to write balance snapshot: {e}")

    return snapshot


def get_portfolio_snapshot() -> Dict[str, Any]:
    """
    Get a structured snapshot of the entire portfolio across all exchanges.
    Returns dict with exchange data that Queen/Orca can consume.
    """
    snapshot = {
        "timestamp": time.time(),
        "exchanges": {},
        "totals": {
            "total_value_usd": 0,
            "total_pnl_usd": 0,
            "positions_count": 0,
            "profitable_count": 0
        }
    }
    
    cost_basis = load_cost_basis()
    
    # Alpaca
    try:
        alpaca = AlpacaClient()
        positions = alpaca.get_positions()
        
        alpaca_data = {
            "positions": [],
            "total_value": 0,
            "total_pnl": 0,
            "count": len(positions) if positions else 0
        }
        
        if positions:
            for pos in positions:
                pnl = float(pos['unrealized_pl'])
                value = float(pos['market_value'])
                
                alpaca_data["positions"].append({
                    "symbol": pos['symbol'],
                    "qty": float(pos['qty']),
                    "entry_price": float(pos['avg_entry_price']),
                    "current_price": float(pos['current_price']),
                    "value": value,
                    "pnl": pnl,
                    "pnl_pct": float(pos['unrealized_plpc']) * 100
                })
                
                alpaca_data["total_value"] += value
                alpaca_data["total_pnl"] += pnl
                
                if pnl > 0:
                    snapshot["totals"]["profitable_count"] += 1
        
        snapshot["exchanges"]["alpaca"] = alpaca_data
        snapshot["totals"]["total_value_usd"] += alpaca_data["total_value"]
        snapshot["totals"]["total_pnl_usd"] += alpaca_data["total_pnl"]
        snapshot["totals"]["positions_count"] += alpaca_data["count"]
        
    except Exception as e:
        snapshot["exchanges"]["alpaca"] = {"error": str(e)}
    
    # Kraken
    try:
        kraken = get_kraken_client()
        balances = kraken.get_balance()
        ledgers = kraken.get_ledgers()
        
        kraken_data = {
            "positions": [],
            "total_value_usd": 0,
            "total_pnl_usd": 0,
            "count": 0,
            "profitable_count": 0
        }
        
        if balances:
            # Fetch all tickers once
            all_tickers = kraken.get_24h_tickers()
            price_lookup = {}
            for ticker in all_tickers:
                symbol = ticker['symbol']
                price = float(ticker.get('lastPrice', 0))
                for quote in ['USD', 'EUR', 'GBP', 'USDT', 'USDC']:
                    if symbol.endswith(quote):
                        base = symbol[:-len(quote)]
                        if base not in price_lookup or quote == 'USD':
                            price_lookup[base] = {'price': price, 'quote': quote}
                        break
            
            # Process ledgers for cost basis
            trades_by_ref = {}
            if ledgers and 'ledger' in ledgers:
                for ledger_id, entry in ledgers['ledger'].items():
                    if entry['type'] == 'trade':
                        refid = entry['refid']
                        if refid not in trades_by_ref:
                            trades_by_ref[refid] = []
                        trades_by_ref[refid].append(entry)
            
            kraken_cost_basis = {}
            for refid, entries in trades_by_ref.items():
                if len(entries) == 2:
                    entry1, entry2 = entries
                    asset_entry = None
                    currency_entry = None
                    
                    if entry1['asset'].startswith('Z'):
                        currency_entry = entry1
                        asset_entry = entry2
                    elif entry2['asset'].startswith('Z'):
                        currency_entry = entry2
                        asset_entry = entry1
                    elif entry1['asset'] in ['XXBT', 'XETH'] and entry2['asset'] not in ['XXBT', 'XETH']:
                        currency_entry = entry1
                        asset_entry = entry2
                    elif entry2['asset'] in ['XXBT', 'XETH'] and entry1['asset'] not in ['XXBT', 'XETH']:
                        currency_entry = entry2
                        asset_entry = entry1
                    else:
                        if abs(float(entry1['amount'])) > abs(float(entry2['amount'])):
                            currency_entry = entry1
                            asset_entry = entry2
                        else:
                            currency_entry = entry2
                            asset_entry = entry1
                    
                    if asset_entry and currency_entry:
                        asset = asset_entry['asset']
                        if asset.startswith('X') and len(asset) > 4:
                            asset = asset[1:]
                        if asset.startswith('Z') and len(asset) > 4:
                            asset = asset[1:]
                        if asset.endswith('.d'):
                            asset = asset[:-2]
                        
                        amount_bought = abs(float(asset_entry['amount']))
                        cost = abs(float(currency_entry['amount']))
                        
                        if amount_bought > 0:
                            if asset not in kraken_cost_basis:
                                kraken_cost_basis[asset] = {'total_cost': 0, 'total_amount': 0}
                            kraken_cost_basis[asset]['total_cost'] += cost
                            kraken_cost_basis[asset]['total_amount'] += amount_bought
            
            for symbol, balance in balances.items():
                if balance > 0.001:  # Skip dust
                    lookup_symbol = symbol
                    if symbol.startswith('X') and len(symbol) > 4:
                        lookup_symbol = symbol[1:]
                    if symbol.startswith('Z') and len(symbol) > 4:
                        lookup_symbol = symbol[1:]
                    if symbol.endswith('.d'):
                        lookup_symbol = symbol[:-2]
                    
                    price_data = price_lookup.get(lookup_symbol)
                    cost_data = kraken_cost_basis.get(lookup_symbol)
                    
                    if price_data and price_data['price'] > 0:
                        current_price = price_data['price']
                        value = balance * current_price
                        
                        entry_price = 0
                        pnl = 0
                        is_free = False
                        
                        if cost_data and cost_data['total_amount'] > 0:
                            entry_price = cost_data['total_cost'] / cost_data['total_amount']
                            pnl = balance * (current_price - entry_price)
                        else:
                            is_free = True
                            pnl = value  # All value is profit for airdrops
                        
                        kraken_data["positions"].append({
                            "symbol": symbol,
                            "qty": balance,
                            "entry_price": entry_price,
                            "current_price": current_price,
                            "value_usd": value,
                            "pnl_usd": pnl,
                            "is_airdrop": is_free,
                            "quote": price_data['quote']
                        })
                        
                        kraken_data["total_value_usd"] += value
                        kraken_data["total_pnl_usd"] += pnl
                        kraken_data["count"] += 1
                        
                        if pnl > 0:
                            kraken_data["profitable_count"] += 1
        
        snapshot["exchanges"]["kraken"] = kraken_data
        snapshot["totals"]["total_value_usd"] += kraken_data["total_value_usd"]
        snapshot["totals"]["total_pnl_usd"] += kraken_data["total_pnl_usd"]
        snapshot["totals"]["positions_count"] += kraken_data["count"]
        snapshot["totals"]["profitable_count"] += kraken_data["profitable_count"]
        
    except Exception as e:
        snapshot["exchanges"]["kraken"] = {"error": str(e)}
    
    # Binance
    try:
        binance = get_binance_client()
        balances = binance.get_balance()
        
        binance_data = {
            "positions": [],
            "total_value": 0,
            "total_pnl": 0,
            "count": 0,
            "profitable_count": 0
        }
        
        if balances:
            for asset, balance in balances.items():  # Process ALL positions (was [:20])
                if balance > 0:
                    ticker_pair = f"{asset}USDC"
                    cost_data = cost_basis.get(ticker_pair) or cost_basis.get(f"binance:{ticker_pair}")
                    
                    entry_price = 0
                    if cost_data and cost_data.get('exchange') == 'binance':
                        entry_price = cost_data.get('avg_entry_price', 0)
                    
                    try:
                        ticker = binance.get_ticker(ticker_pair)
                        current_price = float(ticker.get('last', 0))
                        
                        if current_price > 0:
                            value = balance * current_price
                            pnl = balance * (current_price - entry_price) if entry_price > 0 else 0
                            
                            binance_data["positions"].append({
                                "symbol": asset,
                                "qty": balance,
                                "entry_price": entry_price,
                                "current_price": current_price,
                                "value": value,
                                "pnl": pnl,
                                "pnl_pct": ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
                            })
                            
                            binance_data["total_value"] += value
                            binance_data["total_pnl"] += pnl
                            binance_data["count"] += 1
                            
                            if pnl > 0:
                                binance_data["profitable_count"] += 1
                    except:
                        pass  # Skip assets with no USDC pair
        
        snapshot["exchanges"]["binance"] = binance_data
        snapshot["totals"]["total_value_usd"] += binance_data["total_value"]
        snapshot["totals"]["total_pnl_usd"] += binance_data["total_pnl"]
        snapshot["totals"]["positions_count"] += binance_data["count"]
        snapshot["totals"]["profitable_count"] += binance_data["profitable_count"]
        
    except Exception as e:
        snapshot["exchanges"]["binance"] = {"error": str(e)}
    
    return snapshot

def save_profit_state(snapshot: Dict[str, Any]):
    """Save portfolio snapshot to file for Queen/Orca access."""
    try:
        with open(PROFIT_STATE_FILE, 'w') as f:
            json.dump(snapshot, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save profit state: {e}")

def publish_to_thought_bus(snapshot: Dict[str, Any]):
    """Publish portfolio data to Thought Bus for Queen awareness."""
    if not THOUGHT_BUS_AVAILABLE:
        return
    
    try:
        bus = ThoughtBus()
        bus.emit("portfolio_snapshot", {
            "total_value_usd": snapshot["totals"]["total_value_usd"],
            "total_pnl_usd": snapshot["totals"]["total_pnl_usd"],
            "positions_count": snapshot["totals"]["positions_count"],
            "profitable_count": snapshot["totals"]["profitable_count"],
            "timestamp": snapshot["timestamp"],
            "exchanges": {
                "alpaca": snapshot["exchanges"].get("alpaca", {}).get("total_value", 0),
                "kraken": snapshot["exchanges"].get("kraken", {}).get("total_value_usd", 0),
                "binance": snapshot["exchanges"].get("binance", {}).get("total_value", 0)
            }
        })
    except Exception as e:
        print(f"⚠️ Failed to publish to Thought Bus: {e}")

def main():
    print("\n💰 LIVE POSITION & PROFIT MONITOR\n")
    print("=" * 80)
    
    # Save raw balance snapshot FIRST (all 3 exchanges, atomic write)
    print("📸 Taking pre-trade balance snapshot (all exchanges)...")
    save_balance_snapshot()
    
    # Get structured snapshot
    snapshot = get_portfolio_snapshot()
    
    # Save state for Queen/Orca
    save_profit_state(snapshot)
    publish_to_thought_bus(snapshot)
    
    # Load cost basis for display
    cost_basis = load_cost_basis()
    
    # Alpaca - shows unrealized P&L
    print("\n🦙 ALPACA:")
    try:
        alpaca = AlpacaClient()
        positions = alpaca.get_positions()
        
        if not positions:
            print("   No open positions")
        else:
            total_value = 0
            total_pnl = 0
            
            for pos in positions:
                symbol = pos['symbol']
                qty = float(pos['qty'])
                entry = float(pos['avg_entry_price'])
                current = float(pos['current_price'])
                value = float(pos['market_value'])
                pnl = float(pos['unrealized_pl'])
                pnl_pct = float(pos['unrealized_plpc']) * 100
                
                total_value += value
                total_pnl += pnl
                
                status = "🟢" if pnl > 0 else "🔴"
                print(f"\n   {status} {symbol:10s}")
                print(f"      Entry:   ${entry:10.6f}")
                print(f"      Current: ${current:10.6f}")
                print(f"      Qty:     {qty:10.4f}")
                print(f"      Value:   ${value:10.2f}")
                print(f"      P&L:     ${pnl:+10.2f} ({pnl_pct:+.2f}%)")
                
                # Distance to profit targets
                if pnl_pct < 0.5:
                    print(f"      ⏳ {0.5 - pnl_pct:.2f}% to 0.5% target")
                elif pnl_pct < 1.0:
                    print(f"      🎯 {1.0 - pnl_pct:.2f}% to 1.0% target")  
                else:
                    print(f"      ✅ PROFITABLE! Hit target!")
            
            print(f"\n   TOTAL: ${total_value:.2f} | P&L: ${total_pnl:+.2f} ({total_pnl/total_value*100:+.2f}%)")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Kraken - show balance with P&L calculated from ledger history
    print("\n\n🐙 KRAKEN:")
    try:
        kraken = get_kraken_client()
        balances = kraken.get_balance()
        ledgers = kraken.get_ledgers()

        if not balances:
            print("   No positions")
        else:
            # 🚀 OPTIMIZATION: Fetch all market prices in ONE batch call
            print("   Fetching market data...")
            all_tickers = kraken.get_24h_tickers()
            price_lookup = {}
            
            # Build lookup table: asset -> {price, quote_currency}
            for ticker in all_tickers:
                symbol = ticker['symbol']
                price = float(ticker.get('lastPrice', 0))
                
                # Extract base and quote (e.g., "SOLUSD" -> SOL, USD)
                for quote in ['USD', 'EUR', 'GBP', 'USDT', 'USDC']:
                    if symbol.endswith(quote):
                        base = symbol[:-len(quote)]
                        if base not in price_lookup or quote == 'USD':  # Prefer USD
                            price_lookup[base] = {'price': price, 'quote': quote}
                        break
            
            # Process ledgers to find cost basis
            trades_by_ref = {}
            if ledgers and 'ledger' in ledgers:
                for ledger_id, entry in ledgers['ledger'].items():
                    if entry['type'] == 'trade':
                        refid = entry['refid']
                        if refid not in trades_by_ref:
                            trades_by_ref[refid] = []
                        trades_by_ref[refid].append(entry)

            kraken_cost_basis = {}
            for refid, entries in trades_by_ref.items():
                if len(entries) == 2:
                    # Identify asset and currency entries
                    entry1, entry2 = entries
                    asset_entry = None
                    currency_entry = None

                    # Currency assets start with Z (ZUSD, ZEUR) or X (XXBT, XETH for majors)
                    # Non-currency assets are the altcoins
                    if entry1['asset'].startswith('Z'):
                        currency_entry = entry1
                        asset_entry = entry2
                    elif entry2['asset'].startswith('Z'):
                        currency_entry = entry2
                        asset_entry = entry1
                    elif entry1['asset'] in ['XXBT', 'XETH'] and entry2['asset'] not in ['XXBT', 'XETH']:
                        currency_entry = entry1
                        asset_entry = entry2
                    elif entry2['asset'] in ['XXBT', 'XETH'] and entry1['asset'] not in ['XXBT', 'XETH']:
                        currency_entry = entry2
                        asset_entry = entry1
                    else:
                        # Both are X-prefixed, pick the one with larger amount as currency
                        if abs(float(entry1['amount'])) > abs(float(entry2['amount'])):
                            currency_entry = entry1
                            asset_entry = entry2
                        else:
                            currency_entry = entry2
                            asset_entry = entry1

                    if asset_entry and currency_entry:
                        asset = asset_entry['asset']
                        
                        # Normalize asset names (remove X/Z prefixes)
                        if asset.startswith('X') and len(asset) > 4:
                            asset = asset[1:]
                        if asset.startswith('Z') and len(asset) > 4:
                            asset = asset[1:]
                        if asset.endswith('.d'):
                            asset = asset[:-2]

                        amount_bought = abs(float(asset_entry['amount']))
                        cost = abs(float(currency_entry['amount']))
                        
                        if amount_bought > 0:  # Only count buys
                            if asset not in kraken_cost_basis:
                                kraken_cost_basis[asset] = {'total_cost': 0, 'total_amount': 0}
                            
                            kraken_cost_basis[asset]['total_cost'] += cost
                            kraken_cost_basis[asset]['total_amount'] += amount_bought

            profitable_count = 0
            total_assets = sum(1 for b in balances.values() if b > 0)
            total_value_usd = 0
            total_pnl_usd = 0

            for symbol, balance in balances.items():
                if balance > 0:
                    # Normalize symbol for lookups
                    lookup_symbol = symbol
                    if symbol.startswith('X') and len(symbol) > 4:
                        lookup_symbol = symbol[1:]
                    if symbol.startswith('Z') and len(symbol) > 4:
                        lookup_symbol = symbol[1:]
                    if symbol.endswith('.d'):
                        lookup_symbol = symbol[:-2]

                    # Try to find price in our lookup table
                    price_data = price_lookup.get(lookup_symbol)
                    cost_data = kraken_cost_basis.get(lookup_symbol)
                    
                    if price_data and price_data['price'] > 0:
                        current_price = price_data['price']
                        quote = price_data['quote']
                        value = balance * current_price
                        
                        if cost_data and cost_data['total_amount'] > 0:
                            avg_entry_price = cost_data['total_cost'] / cost_data['total_amount']
                            pnl = balance * (current_price - avg_entry_price)
                            pnl_pct = ((current_price - avg_entry_price) / avg_entry_price) * 100 if avg_entry_price > 0 else 0
                            
                            status = "🟢" if pnl > 0 else "🔴"
                            print(f"   {status} {symbol:12s} | Bal: {balance:10.6f} | Entry: {avg_entry_price:.6f} {quote} | Current: {current_price:.6f} {quote}")
                            print(f"        Value: {value:.2f} {quote} | P&L: {pnl:+.2f} {quote} ({pnl_pct:+.2f}%)")
                            
                            if pnl > 0:
                                profitable_count += 1
                            
                            total_value_usd += value
                            total_pnl_usd += pnl
                        else:
                            # No cost basis = likely airdrop/staking
                            print(f"   🎁 {symbol:12s} | Bal: {balance:10.6f} | Current: {current_price:.6f} {quote}")
                            print(f"        Value: {value:.2f} {quote} | FREE (airdrop/staking)")
                            profitable_count += 1
                            total_value_usd += value
                    else:
                        # No price data available
                        if balance < 0.001:
                            continue  # Skip dust
                        print(f"   ⚪ {symbol:12s} | Balance: {balance:.6f}")

            print(f"\n   Total: {total_assets} assets | {profitable_count} profitable | Est. Value: ${total_value_usd:.2f}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Binance - show balance with P&L if cost basis available
    print("\n\n🟡 BINANCE:")
    try:
        binance = get_binance_client()
        balances = binance.get_balance()
        
        if not balances:
            print("   No balances")
        else:
            count = 0
            profitable_count = 0
            
            for asset, balance in balances.items():  # Process ALL positions (was [:10])
                if balance > 0:
                    # Check cost basis - try both key formats
                    ticker_pair = f"{asset}USDC"
                    cost_data = cost_basis.get(ticker_pair) or cost_basis.get(f"binance:{ticker_pair}")
                    
                    if cost_data and cost_data.get('exchange') == 'binance':
                        entry_price = cost_data.get('avg_entry_price', 0)
                        
                        # Get current price using USDC pairs
                        try:
                            ticker = binance.get_ticker(ticker_pair)
                            current_price = float(ticker.get('last', 0))
                            
                            if entry_price > 0 and current_price > 0:
                                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                                value = balance * current_price
                                pnl = balance * (current_price - entry_price)
                                
                                status = "🟢" if pnl > 0 else "🔴"
                                print(f"   {status} {asset:12s} | Bal: {balance:10.6f} | Entry: €{entry_price:.6f} | Current: €{current_price:.6f}")
                                print(f"        Value: €{value:.2f} | P&L: €{pnl:+.2f} ({pnl_pct:+.2f}%)")
                                
                                if pnl > 0:
                                    profitable_count += 1
                            else:
                                print(f"   ⚪ {asset:12s} | Balance: {balance:.6f}")
                        except:
                            print(f"   ⚪ {asset:12s} | Balance: {balance:.6f}")
                    else:
                        print(f"   ⚪ {asset:12s} | Balance: {balance:.6f}")
                    
                    count += 1
            
            print(f"\n   Total: {count} assets | {profitable_count} profitable")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 80 + "\n")
    
    # Queen/Orca integration confirmation
    print(f"📊 Portfolio state saved to: {PROFIT_STATE_FILE}")
    if THOUGHT_BUS_AVAILABLE:
        print("🧠 Portfolio data published to Thought Bus → Queen can see it")
    else:
        print("💭 Thought Bus not available (Queen can still read state file)")

if __name__ == "__main__":
    main()
