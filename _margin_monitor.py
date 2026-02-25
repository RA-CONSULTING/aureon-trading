#!/usr/bin/env python3
"""
MARGIN POSITION MONITOR — No Stop Loss, Hold Until Profit
==========================================================
Monitors open margin positions and closes them ONLY when:
1. Price is above breakeven (entry + all fees)
2. Net P&L is confirmed positive
3. Profit is locked in

Philosophy: NO STOP LOSS. We hold with patience until profitable.
Only exception: margin liquidation risk (<110% margin level).
"""
import os, sys, time, json, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('margin_monitor')

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════
CHECK_INTERVAL = 30       # Seconds between price checks
MIN_PROFIT_USD = 0.001    # Minimum net profit in USD to trigger close
MIN_PROFIT_PCT = 0.10     # Minimum % above breakeven to close (0.10%)
LIQUIDATION_WARN = 120    # Margin level % warning threshold
LIQUIDATION_FORCE = 110   # Margin level % force-close threshold

def main():
    from kraken_client import KrakenClient
    client = KrakenClient()
    
    assert not client.dry_run, "ERROR: Client is in dry-run mode!"
    
    print("=" * 70)
    print("  MARGIN POSITION MONITOR")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Check interval: {CHECK_INTERVAL}s")
    print(f"  Min profit to close: ${MIN_PROFIT_USD} or {MIN_PROFIT_PCT}%")
    print(f"  Stop loss: NONE (patience mode)")
    print("=" * 70)
    
    closed_positions = []
    cycle = 0
    
    while True:
        cycle += 1
        try:
            # Get open margin positions
            positions = client.get_open_margin_positions()
            
            if not positions:
                if closed_positions:
                    print(f"\n{'=' * 70}")
                    print(f"  ALL MARGIN POSITIONS CLOSED WITH PROFIT!")
                    print(f"  Closed {len(closed_positions)} positions:")
                    total_profit = 0
                    for cp in closed_positions:
                        print(f"    {cp['pair']}: ${cp['pnl']:+.4f}")
                        total_profit += cp['pnl']
                    print(f"  Total profit: ${total_profit:+.4f}")
                    print(f"{'=' * 70}")
                else:
                    print(f"\n  No open margin positions found. Nothing to monitor.")
                break
            
            # Get margin account health
            tb = client.get_trade_balance()
            margin_level = float(tb.get('margin_level', 0) or 0)
            free_margin = float(tb.get('free_margin', 0) or 0)
            
            # Get current ETH price
            ticker = client.get_ticker('ETHUSD')
            current_bid = float(ticker.get('bid', 0))
            current_ask = float(ticker.get('ask', 0))
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            print(f"\n[{timestamp}] Cycle {cycle} | ETH: ${current_bid:,.2f} | Margin Level: {margin_level:.0f}% | Free: ${free_margin:.2f}")
            print(f"  {'─' * 60}")
            
            # Check liquidation risk FIRST
            if margin_level > 0 and margin_level < LIQUIDATION_FORCE:
                print(f"  CRITICAL: Margin level {margin_level:.1f}% < {LIQUIDATION_FORCE}%!")
                print(f"  Force closing ALL positions to prevent liquidation!")
                for pos in positions:
                    _force_close(client, pos, "LIQUIDATION_RISK")
                continue
            elif margin_level > 0 and margin_level < LIQUIDATION_WARN:
                print(f"  WARNING: Margin level {margin_level:.1f}% approaching danger zone")
            
            # Monitor each position
            for i, pos in enumerate(positions):
                pair = pos.get('pair', '?')
                pos_type = pos.get('type', '?')  # buy = long, sell = short
                volume = float(pos.get('volume', 0))
                volume_closed = float(pos.get('volume_closed', 0))
                remaining = volume - volume_closed
                cost = float(pos.get('cost', 0))
                fee = float(pos.get('fee', 0))
                leverage = pos.get('leverage', '1')
                unrealized = float(pos.get('unrealized_pnl', 0) or 0)
                margin_used = float(pos.get('margin', 0))
                rollover = float(pos.get('rollovertm', 0) or 0)
                
                # Calculate entry price and breakeven
                entry_price = cost / volume if volume > 0 else 0
                exit_fee_est = fee  # Roughly same fee to close
                total_fees = fee + exit_fee_est
                breakeven = entry_price + (total_fees / remaining) if remaining > 0 else entry_price
                
                # Current P&L (accounting for fees)
                gross_pnl = (current_bid - entry_price) * remaining
                net_pnl = gross_pnl - total_fees
                pnl_pct = (net_pnl / cost * 100) if cost > 0 else 0
                
                # Distance to breakeven
                to_breakeven = current_bid - breakeven
                to_breakeven_pct = (to_breakeven / breakeven * 100) if breakeven > 0 else 0
                
                # Status indicator
                if net_pnl > MIN_PROFIT_USD:
                    status = "PROFITABLE"
                    icon = "+"
                elif current_bid >= entry_price:
                    status = "ABOVE ENTRY (fees not covered)"
                    icon = "~"
                else:
                    underwater_pct = abs((current_bid / entry_price - 1) * 100)
                    status = f"UNDERWATER (-{underwater_pct:.2f}%)"
                    icon = "-"
                
                print(f"  [{i}] {pair} LONG {remaining:.6f} ETH (lev={leverage}x)")
                print(f"      Entry: ${entry_price:,.2f} | Breakeven: ${breakeven:,.2f} | Current: ${current_bid:,.2f}")
                print(f"      Gross PnL: ${gross_pnl:+.4f} | Fees: ${total_fees:.4f} | Net PnL: ${net_pnl:+.4f} ({pnl_pct:+.3f}%)")
                print(f"      To breakeven: ${to_breakeven:+.2f} ({to_breakeven_pct:+.3f}%)")
                print(f"      Status: [{icon}] {status}")
                
                # ════════════════════════════════════════════════════════
                #  CLOSE DECISION: Only when NET PROFIT is confirmed
                # ════════════════════════════════════════════════════════
                should_close = False
                close_reason = ""
                
                if net_pnl >= MIN_PROFIT_USD and to_breakeven_pct >= MIN_PROFIT_PCT:
                    should_close = True
                    close_reason = f"PROFIT_TARGET (net=${net_pnl:+.4f}, {to_breakeven_pct:+.3f}% above breakeven)"
                
                if should_close:
                    print(f"      >>> CLOSING: {close_reason}")
                    try:
                        close_order = client.close_margin_position(
                            symbol='ETHUSD',
                            side='sell',   # sell to close LONG
                            volume=remaining,
                            leverage=int(leverage) if str(leverage).isdigit() else None
                        )
                        close_txid = close_order.get('orderId') or close_order.get('txid', 'UNKNOWN')
                        close_status = close_order.get('status', 'UNKNOWN')
                        print(f"      >>> CLOSED! Order ID: {close_txid} | Status: {close_status}")
                        print(f"      >>> Net Profit: ${net_pnl:+.4f}")
                        closed_positions.append({
                            'pair': pair,
                            'entry_price': entry_price,
                            'exit_price': current_bid,
                            'volume': remaining,
                            'pnl': net_pnl,
                            'order_id': str(close_txid),
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as e:
                        print(f"      >>> CLOSE FAILED: {e}")
                else:
                    if net_pnl < 0:
                        needed = breakeven - current_bid
                        print(f"      HOLDING — Need ETH +${needed:.2f} to breakeven. Patience.")
                    else:
                        print(f"      HOLDING — Profitable but below {MIN_PROFIT_PCT}% threshold. Patience.")
            
            # Sleep until next check
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print(f"\n  Monitor stopped by user. Positions remain open.")
            break
        except Exception as e:
            logger.error(f"Monitor error: {e}", exc_info=True)
            time.sleep(CHECK_INTERVAL)
    
    # Save results
    if closed_positions:
        results = {
            'timestamp': datetime.now().isoformat(),
            'positions_closed': closed_positions,
            'total_profit': sum(cp['pnl'] for cp in closed_positions)
        }
        with open('_margin_monitor_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to _margin_monitor_results.json")


def _force_close(client, pos, reason):
    """Emergency close a margin position."""
    volume = float(pos.get('volume', 0)) - float(pos.get('volume_closed', 0))
    leverage = pos.get('leverage', None)
    try:
        close_order = client.close_margin_position(
            symbol='ETHUSD',
            side='sell',
            volume=volume,
            leverage=int(leverage) if leverage and str(leverage).isdigit() else None
        )
        print(f"  Force closed: {close_order.get('orderId', '?')} reason={reason}")
    except Exception as e:
        print(f"  Force close failed: {e}")


if __name__ == '__main__':
    main()
