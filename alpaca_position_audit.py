#!/usr/bin/env python3
"""
🔍 ALPACA POSITION TRUTH AUDITOR
Verifies that Alpaca API isn't lying about positions and we're not phantom bleeding.
"""
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import json
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, QueryOrderStatus

def main():
    api_key = os.environ.get('ALPACA_API_KEY') or os.environ.get('APCA_API_KEY_ID')
    api_secret = os.environ.get('ALPACA_API_SECRET') or os.environ.get('APCA_API_SECRET_KEY')

    if not api_key or not api_secret:
        print("❌ ERROR: No Alpaca API credentials found!")
        return

    print('=' * 80)
    print('🔍 ALPACA API POSITION AUDIT - TRUTH CHECK')
    print('=' * 80)
    print(f'   Timestamp: {datetime.now().isoformat()}')

    client = TradingClient(api_key, api_secret, paper=True)
    
    # Get account info
    account = client.get_account()

    print(f'\n💰 ACCOUNT STATUS (What Alpaca Claims):')
    print(f'   Portfolio Value: ${float(account.portfolio_value):,.2f}')
    print(f'   Cash: ${float(account.cash):,.2f}')
    print(f'   Buying Power: ${float(account.buying_power):,.2f}')
    print(f'   Equity: ${float(account.equity):,.2f}')
    print(f'   Last Equity (prev day): ${float(account.last_equity):,.2f}')
    
    day_pnl = float(account.equity) - float(account.last_equity)
    day_pnl_pct = (day_pnl / float(account.last_equity)) * 100 if float(account.last_equity) > 0 else 0
    day_emoji = '✅' if day_pnl >= 0 else '❌'
    print(f'   Day P&L: ${day_pnl:,.4f} ({day_pnl_pct:+.2f}%) {day_emoji}')

    # Get all positions
    positions = client.get_all_positions()
    print(f'\n📊 POSITIONS (What Alpaca Says We Hold):')
    print('-' * 80)

    total_market_value = 0.0
    total_cost_basis = 0.0
    total_unrealized_pl = 0.0

    if not positions:
        print('   📭 No positions reported by Alpaca API')
    else:
        for pos in positions:
            symbol = pos.symbol
            qty = float(pos.qty)
            avg_entry = float(pos.avg_entry_price)
            current_price = float(pos.current_price)
            market_value = float(pos.market_value)
            cost_basis = float(pos.cost_basis)
            unrealized_pl = float(pos.unrealized_pl)
            unrealized_plpc = float(pos.unrealized_plpc) * 100
            
            total_market_value += market_value
            total_cost_basis += cost_basis
            total_unrealized_pl += unrealized_pl
            
            status = '✅ PROFIT' if unrealized_pl >= 0 else '❌ LOSS'
            
            # Calculate our own PnL to verify
            our_calc_value = qty * current_price
            our_calc_cost = qty * avg_entry
            our_calc_pl = our_calc_value - our_calc_cost
            
            # Check if Alpaca's math matches ours
            value_match = abs(market_value - our_calc_value) < 0.01
            pl_match = abs(unrealized_pl - our_calc_pl) < 0.01
            
            verify_emoji = '✅' if (value_match and pl_match) else '⚠️'
            
            print(f'   {symbol}:')
            print(f'      Qty: {qty}')
            print(f'      Avg Entry: ${avg_entry:.6f}')
            print(f'      Current Price: ${current_price:.6f}')
            print(f'      Market Value: ${market_value:.2f} (our calc: ${our_calc_value:.2f}) {verify_emoji}')
            print(f'      Cost Basis: ${cost_basis:.2f} (our calc: ${our_calc_cost:.2f})')
            print(f'      Unrealized P&L: ${unrealized_pl:.4f} ({unrealized_plpc:+.2f}%) {status}')
            print(f'      Our P&L calc: ${our_calc_pl:.4f}')
            print()

    print('-' * 80)
    print(f'📈 TOTALS:')
    print(f'   Total Market Value: ${total_market_value:.2f}')
    print(f'   Total Cost Basis: ${total_cost_basis:.2f}')
    print(f'   Total Unrealized P&L: ${total_unrealized_pl:.4f}')

    # CRITICAL: Math verification
    print(f'\n🔬 MATH VERIFICATION (Catching Lies):')
    expected_portfolio = float(account.cash) + total_market_value
    alpaca_portfolio = float(account.portfolio_value)
    print(f'   Our Math: Cash (${float(account.cash):.2f}) + Positions (${total_market_value:.2f}) = ${expected_portfolio:.2f}')
    print(f'   Alpaca Says: Portfolio = ${alpaca_portfolio:.2f}')
    discrepancy = abs(expected_portfolio - alpaca_portfolio)
    
    if discrepancy < 0.01:
        print(f'   ✅ MATCH - Alpaca is NOT lying about portfolio value')
    else:
        print(f'   🚨 DISCREPANCY DETECTED: ${discrepancy:.4f}')
        print(f'   ⚠️ POTENTIAL PHANTOM BLEEDING!')

    # Trade history analysis
    print(f'\n📜 RECENT TRADE HISTORY (Checking For Hidden Losses):')
    req = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=50)
    orders = client.get_orders(req)
    
    total_buy_value = 0.0
    total_sell_value = 0.0
    trade_count = 0
    
    print(f'   Last {min(len(orders), 20)} closed orders:')
    for order in orders[:20]:
        side_emoji = '🟢 BUY' if order.side == OrderSide.BUY else '🔴 SELL'
        filled_qty = float(order.filled_qty) if order.filled_qty else 0
        filled_price = float(order.filled_avg_price) if order.filled_avg_price else 0
        total_value = filled_qty * filled_price
        
        if order.side == OrderSide.BUY:
            total_buy_value += total_value
        else:
            total_sell_value += total_value
            
        trade_count += 1
        
        # Format timestamp
        filled_at = order.filled_at.strftime('%m/%d %H:%M') if order.filled_at else 'N/A'
        
        print(f'      {filled_at} | {side_emoji} {order.symbol}: {filled_qty:.6f} @ ${filled_price:.4f} = ${total_value:.2f}')

    print(f'\n💸 TRADE FLOW ANALYSIS:')
    print(f'   Total Bought: ${total_buy_value:.2f}')
    print(f'   Total Sold: ${total_sell_value:.2f}')
    net_flow = total_sell_value - total_buy_value
    print(f'   Net Flow: ${net_flow:.2f}')
    
    # Compare to what we have now
    print(f'\n🔎 ACCOUNT RECONCILIATION:')
    print(f'   Current Cash: ${float(account.cash):.2f}')
    print(f'   Current Positions Value: ${total_market_value:.2f}')
    print(f'   Current Total: ${expected_portfolio:.2f}')
    
    # Load local state to compare
    try:
        with open('active_position.json', 'r') as f:
            local_state = json.load(f)
            print(f'\n📁 LOCAL STATE FILE (active_position.json):')
            print(f'   {json.dumps(local_state, indent=6)[:500]}...')
    except Exception as e:
        print(f'\n📁 LOCAL STATE: Could not load active_position.json: {e}')

    # Check fee tracker
    try:
        with open('alpaca_fee_tracker_state.json', 'r') as f:
            fee_state = json.load(f)
            print(f'\n💵 FEE TRACKER STATE:')
            print(f'   Total Fees Paid: ${fee_state.get("total_fees_paid", 0):.4f}')
            print(f'   Total Trades: {fee_state.get("total_trades", 0)}')
            print(f'   Last Updated: {fee_state.get("last_updated", "N/A")}')
    except Exception as e:
        print(f'\n💵 FEE TRACKER: Could not load: {e}')

    print('\n' + '=' * 80)
    print('🔍 AUDIT COMPLETE')
    print('=' * 80)
    
    # Final verdict
    if discrepancy < 0.01:
        print('✅ NO PHANTOM BLEEDING DETECTED - Alpaca is telling the truth')
        print(f'   Your portfolio is ${alpaca_portfolio:.2f}')
        if total_unrealized_pl >= 0:
            print(f'   📈 You are UP ${total_unrealized_pl:.4f} on current positions')
        else:
            print(f'   📉 You are DOWN ${abs(total_unrealized_pl):.4f} on current positions')
    else:
        print('🚨 POTENTIAL ISSUES DETECTED - Investigate further!')
        print(f'   Discrepancy: ${discrepancy:.4f}')

if __name__ == '__main__':
    main()
