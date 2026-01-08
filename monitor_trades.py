#!/usr/bin/env python3
"""
🔍 LIVE TRADE MONITOR - Watch Micro Profit Labyrinth
"""
import json
import time
import os
from datetime import datetime

def monitor_trades():
    """Watch trades in real-time"""
    last_count = 0
    
    while True:
        try:
            # Read pending validations
            if os.path.exists('7day_pending_validations.json'):
                with open('7day_pending_validations.json', 'r') as f:
                    trades = json.load(f)
                
                current_count = len(trades)
                
                print(f"\n{'='*70}")
                print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*70}")
                print(f"📊 Total Trades: {current_count}")
                
                # Show last 5 trades
                if trades:
                    print(f"\n📈 RECENT TRADES (Last 5):")
                    print(f"{'-'*70}")
                    
                    for trade in trades[-5:]:
                        symbol = trade.get('symbol', 'UNKNOWN')
                        entry = trade.get('entry_price', 0)
                        exit_p = trade.get('exit_price', 0)
                        entry_t = trade.get('entry_time', '')[:19]
                        exit_t = trade.get('exit_time', '')[:19]
                        
                        # Calculate P&L
                        actual_edge = trade.get('actual_edge', 0)
                        status = trade.get('status', 'unknown')
                        
                        if actual_edge > 0:
                            emoji = '✅'
                        elif actual_edge < 0:
                            emoji = '❌'
                        else:
                            emoji = '⚪'
                        
                        print(f"{emoji} {symbol:15} | Entry: {entry:.8f} → Exit: {exit_p:.8f}")
                        print(f"   PnL: ${actual_edge:+.4f} | Status: {status}")
                        print(f"   Time: {entry_t} → {exit_t}")
                        print()
                    
                    # Calculate totals
                    total_pnl = sum(t.get('actual_edge', 0) for t in trades)
                    wins = sum(1 for t in trades if t.get('actual_edge', 0) > 0)
                    losses = sum(1 for t in trades if t.get('actual_edge', 0) < 0)
                    
                    print(f"{'-'*70}")
                    print(f"💰 TOTALS: ${total_pnl:+.2f} | Wins: {wins} | Losses: {losses} | Win%: {wins/(wins+losses)*100 if (wins+losses) > 0 else 0:.0f}%")
                
                # Check for new trades
                if current_count > last_count:
                    new_trades = current_count - last_count
                    print(f"\n🆕 {new_trades} NEW TRADE(S) SINCE LAST CHECK!")
                    last_count = current_count
            
            # Wait 5 seconds before next check
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("🔍 LIVE TRADE MONITOR - Starting...")
    print("Press Ctrl+C to stop\n")
    monitor_trades()
