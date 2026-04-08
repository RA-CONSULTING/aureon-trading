#!/usr/bin/env python3
"""
👑💰 QUEEN'S LIVE PROFIT DASHBOARD 💰👑
═══════════════════════════════════════════════════════════════════════════════

Live monitoring dashboard showing:
- All positions with progress bars toward profit
- Real-time P&L using profit gate validation
- Auto-sell when guaranteed profit
- Cross-exchange portfolio view
- NO PHANTOM PROFITS - only validated net gains

Run: python queen_profit_dashboard.py [--auto-sell]

Gary Leckey & GitHub Copilot | 2026
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
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import time
import argparse
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 PROGRESS BAR HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def progress_bar(value: float, max_value: float = 100, width: int = 25) -> str:
    """Generate a pretty progress bar."""
    if max_value <= 0:
        pct = 0
    else:
        pct = min(100, max(0, (value / max_value) * 100))
    
    filled = int(pct / 100 * width)
    empty = width - filled
    
    if pct >= 100:
        bar = '█' * width
        color = '\033[92m'  # Green
    elif pct >= 50:
        bar = '▓' * filled + '░' * empty
        color = '\033[93m'  # Yellow
    else:
        bar = '░' * filled + '░' * empty
        color = '\033[91m'  # Red
    
    reset = '\033[0m'
    return f"{color}[{bar}]{reset} {pct:5.1f}%"


def format_money(value: float, show_sign: bool = True) -> str:
    """Format currency with color."""
    if value >= 0:
        color = '\033[92m'  # Green
        sign = '+' if show_sign else ''
    else:
        color = '\033[91m'  # Red
        sign = ''
    reset = '\033[0m'
    return f"{color}{sign}${value:.4f}{reset}"


def format_price(price: float) -> str:
    """Format price with appropriate precision."""
    if price < 0.001:
        return f"${price:.10f}"
    elif price < 1:
        return f"${price:.6f}"
    else:
        return f"${price:.4f}"


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


# ═══════════════════════════════════════════════════════════════════════════════
# 👑💰 MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def run_dashboard(auto_sell: bool = False, refresh_interval: float = 5.0):
    """Run the live profit dashboard."""
    
    print("\n" + "=" * 70)
    print("  👑💰 QUEEN'S LIVE PROFIT DASHBOARD 💰👑")
    print("=" * 70)
    print("\n⏳ Initializing clients and profit gate...\n")
    
    # Import clients and profit gate
    try:
        from kraken_client import KrakenClient, get_kraken_client
        kraken = get_kraken_client()
        print("✅ Kraken client connected")
    except Exception as e:
        print(f"❌ Kraken client failed: {e}")
        kraken = None
    
    try:
        from alpaca_client import AlpacaClient
        alpaca = AlpacaClient()
        print("✅ Alpaca client connected")
    except Exception as e:
        print(f"⚠️ Alpaca client not available: {e}")
        alpaca = None
    
    # Load profit gate
    try:
        from adaptive_prime_profit_gate import is_real_win, get_fee_profile
        print("✅ Profit gate CONNECTED (no phantom profits!)")
    except Exception as e:
        print(f"❌ Profit gate not available: {e}")
        is_real_win = None
        get_fee_profile = None
    
    # Track positions and their entry info
    # Structure: {symbol: {qty, entry_price, entry_cost, exchange}}
    tracked_positions = {}
    
    # Realized profits tracking
    realized_profits = 0.0
    sells_executed = []
    start_time = time.time()
    
    # Keep track of positions we've bought
    active_position_file = 'active_position.json'
    
    print("\n" + "-" * 70)
    print("  Starting live monitoring... (Ctrl+C to exit)")
    print("-" * 70)
    time.sleep(2)
    
    while True:
        try:
            # Clear and redraw
            clear_screen()
            
            now = datetime.now()
            elapsed = timedelta(seconds=int(time.time() - start_time))
            
            print("═" * 70)
            print(f"  👑💰 QUEEN'S PROFIT DASHBOARD | {now.strftime('%H:%M:%S')} | Running: {elapsed}")
            print("═" * 70)
            
            # ═══════════════════════════════════════════════════════════════
            # KRAKEN POSITIONS
            # ═══════════════════════════════════════════════════════════════
            
            if kraken:
                print(f"\n📍 KRAKEN POSITIONS")
                print(f"{'─' * 70}")
                print(f"  {'SYMBOL':<12} {'PROGRESS':<30} {'NET P&L':>12} {'STATUS':>10}")
                print(f"{'─' * 70}")
                
                # Get balances
                balance = kraken.get_balance()
                
                total_value = 0.0
                total_cost = 0.0
                total_pnl = 0.0
                ready_count = 0
                holding_count = 0
                
                for asset, qty in sorted(balance.items()):
                    qty = float(qty)
                    
                    # Skip cash/stables and tiny amounts
                    if asset in ['USD', 'GBP', 'ZUSD', 'ZGBP', 'EUR', 'ZEUR', 'USDT', 'USDC', 'DAI', 'TUSD']:
                        continue
                    if qty < 0.000001:
                        continue
                    
                    # Get current price
                    symbol = asset + 'USD'
                    try:
                        ticker = kraken.get_ticker(symbol)
                        current_price = float(ticker.get('price', 0))
                    except:
                        continue
                    
                    if current_price <= 0:
                        continue
                    
                    current_value = qty * current_price
                    
                    # Skip tiny positions
                    if current_value < 0.10:
                        continue
                    
                    # Get entry price from tracked positions or estimate
                    key = f"kraken:{symbol}"
                    if key in tracked_positions:
                        entry_price = tracked_positions[key].get('entry_price', current_price)
                        entry_cost = tracked_positions[key].get('entry_cost', current_value)
                    else:
                        # Use current as entry (conservative)
                        entry_price = current_price
                        entry_cost = current_value
                    
                    # Calculate P&L using profit gate
                    if is_real_win:
                        result = is_real_win(
                            exchange='kraken',
                            entry_price=entry_price,
                            current_price=current_price,
                            quantity=qty,
                            is_maker=False,
                            gate_level='breakeven'
                        )
                        net_pnl = result['net_pnl']
                        gross_pnl = result['gross_pnl']
                        costs = result['total_costs']
                        is_win = result['is_win']
                    else:
                        gross_pnl = current_value - entry_cost
                        costs = current_value * 0.01  # Estimate 1% costs
                        net_pnl = gross_pnl - costs
                        is_win = net_pnl > 0
                    
                    # Calculate progress to profit target
                    # Target: 0.5% net profit
                    target_profit = entry_cost * 0.005
                    if target_profit > 0:
                        progress = (net_pnl / target_profit) * 100
                    else:
                        progress = 100 if is_win else 0
                    
                    # Determine status
                    if is_win and net_pnl >= 0.01:
                        status = "💰 READY"
                        ready_count += 1
                    elif is_win:
                        status = "✅ WIN"
                    else:
                        status = "⏳ HOLD"
                        holding_count += 1
                    
                    # Display
                    bar = progress_bar(progress, 100, 20)
                    pnl_str = format_money(net_pnl)
                    print(f"  {symbol:<12} {bar} {pnl_str:>12} {status:>10}")
                    
                    total_value += current_value
                    total_cost += entry_cost
                    total_pnl += net_pnl
                    
                    # Auto-sell if enabled and ready
                    if auto_sell and is_win and net_pnl >= 0.01:
                        print(f"\n  🔔 AUTO-SELL TRIGGERED: {symbol}")
                        try:
                            # Execute sell
                            result = kraken.place_market_order(
                                symbol=symbol,
                                side='sell',
                                qty=qty
                            )
                            if result and not result.get('error'):
                                realized_profits += net_pnl
                                sells_executed.append({
                                    'symbol': symbol,
                                    'qty': qty,
                                    'net_pnl': net_pnl,
                                    'time': now.strftime('%H:%M:%S')
                                })
                                print(f"  ✅ SOLD {symbol} for ${net_pnl:.4f} profit!")
                        except Exception as e:
                            print(f"  ❌ Sell failed: {e}")
                
                # Cash balances
                cash_usd = float(balance.get('USD', 0))
                cash_gbp = float(balance.get('ZGBP', balance.get('GBP', 0)))
                
                print(f"{'─' * 70}")
                print(f"  📊 SUMMARY: {holding_count} holding | {ready_count} ready | "
                      f"Net P&L: {format_money(total_pnl)}")
                print(f"  💵 Cash: ${cash_usd:.2f} USD | £{cash_gbp:.2f} GBP")
            
            # ═══════════════════════════════════════════════════════════════
            # ALPACA POSITIONS (if available)
            # ═══════════════════════════════════════════════════════════════
            
            if alpaca:
                try:
                    positions = alpaca.get_positions() if hasattr(alpaca, 'get_positions') else []
                    if positions:
                        print(f"\n📍 ALPACA POSITIONS")
                        print(f"{'─' * 70}")
                        for pos in positions:
                            symbol = pos.get('symbol', 'UNK')
                            qty = float(pos.get('qty', 0))
                            unrealized_pl = float(pos.get('unrealized_pl', 0))
                            status = "✅ WIN" if unrealized_pl > 0 else "⏳ HOLD"
                            print(f"  {symbol:<12} {format_money(unrealized_pl):>20} {status}")
                except Exception as e:
                    pass  # Alpaca not configured
            
            # ═══════════════════════════════════════════════════════════════
            # SESSION STATS
            # ═══════════════════════════════════════════════════════════════
            
            print(f"\n{'═' * 70}")
            print(f"  📈 SESSION STATISTICS")
            print(f"{'─' * 70}")
            print(f"  Runtime: {elapsed}")
            print(f"  Realized Profits: {format_money(realized_profits)}")
            print(f"  Sells Executed: {len(sells_executed)}")
            
            if sells_executed:
                print(f"\n  📜 RECENT SELLS:")
                for sale in sells_executed[-5:]:
                    print(f"     [{sale['time']}] {sale['symbol']}: {format_money(sale['net_pnl'])}")
            
            # ═══════════════════════════════════════════════════════════════
            # CONTROLS
            # ═══════════════════════════════════════════════════════════════
            
            print(f"\n{'═' * 70}")
            mode = "🔴 AUTO-SELL ENABLED" if auto_sell else "🔵 MONITORING ONLY"
            print(f"  {mode} | Refresh: {refresh_interval}s | Press Ctrl+C to exit")
            print(f"{'═' * 70}")
            
            # Sleep
            time.sleep(refresh_interval)
            
        except KeyboardInterrupt:
            print("\n\n👑 Dashboard stopped by user")
            print(f"📊 Session Summary:")
            print(f"   Runtime: {elapsed}")
            print(f"   Realized Profits: ${realized_profits:.4f}")
            print(f"   Sells: {len(sells_executed)}")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Queen's Live Profit Dashboard")
    parser.add_argument('--auto-sell', action='store_true', 
                        help='Enable auto-sell when positions hit profit target')
    parser.add_argument('--refresh', type=float, default=5.0,
                        help='Refresh interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    run_dashboard(
        auto_sell=args.auto_sell,
        refresh_interval=args.refresh
    )
