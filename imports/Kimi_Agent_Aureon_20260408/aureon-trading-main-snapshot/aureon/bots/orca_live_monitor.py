#!/usr/bin/env python3
"""
🐋 ORCA LIVE TRADE MONITOR 🐋
=============================
Monitors active positions and executes exits based on fee-aware targets.
Shows FULL CYCLE with REALIZED NET PROFIT.

Fee-Aware Settings:
- Take Profit: 1.5% gross = ~1.0% net after 0.5% round-trip fees
- Stop Loss: 0.8%
- Max Hold: 30 minutes
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Load .env
for line in Path('.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())

# Settings
TAKE_PROFIT_PCT = 0.015      # 1.5% gross target
STOP_LOSS_PCT = 0.008        # 0.8% stop loss
MAX_HOLD_MINUTES = 30        # Max hold time
ALPACA_FEE_PCT = 0.0025      # 0.25% per side
ROUND_TRIP_FEE = 0.005       # 0.5% total fees

STATE_FILE = "orca_trade_history.json"


@dataclass
class TradeResult:
    """Full cycle trade result."""
    symbol: str
    exchange: str
    qty: float
    entry_price: float
    exit_price: float
    entry_time: str
    exit_time: str
    hold_minutes: float
    gross_pnl_usd: float
    gross_pnl_pct: float
    fees_usd: float
    net_pnl_usd: float
    net_pnl_pct: float
    exit_reason: str
    portfolio_before: float
    portfolio_after: float
    portfolio_growth_pct: float


def load_history():
    """Load trade history."""
    if Path(STATE_FILE).exists():
        return json.loads(Path(STATE_FILE).read_text())
    return {"trades": [], "total_net_pnl": 0.0, "wins": 0, "losses": 0}


def save_history(history):
    """Save trade history."""
    Path(STATE_FILE).write_text(json.dumps(history, indent=2))


def get_alpaca_client():
    """Get Alpaca client."""
    from alpaca.trading.client import TradingClient
    return TradingClient(
        os.environ['ALPACA_API_KEY'],
        os.environ['ALPACA_SECRET_KEY'],
        paper=False
    )


def get_position_and_account(client):
    """Get current position and account info."""
    account = client.get_account()
    positions = client.get_all_positions()
    
    return {
        'cash': float(account.cash),
        'equity': float(account.equity),
        'positions': positions
    }


def sell_position(client, symbol, qty):
    """Execute sell order."""
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    
    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.GTC
    )
    return client.submit_order(order)


def monitor_and_trade():
    """Main monitoring loop."""
    print("\n" + "=" * 70)
    print("🐋 ORCA LIVE TRADE MONITOR - FULL CYCLE TRACKER 🐋")
    print("=" * 70)
    print(f"⚙️  Take Profit: {TAKE_PROFIT_PCT*100:.1f}% gross (~{(TAKE_PROFIT_PCT-ROUND_TRIP_FEE)*100:.1f}% net)")
    print(f"⚙️  Stop Loss: {STOP_LOSS_PCT*100:.1f}%")
    print(f"⚙️  Max Hold: {MAX_HOLD_MINUTES} minutes")
    print(f"⚙️  Fees: {ROUND_TRIP_FEE*100:.1f}% round-trip")
    print("=" * 70)
    
    client = get_alpaca_client()
    history = load_history()
    
    # Track entry time (we'll estimate it)
    entry_time = datetime.now()
    initial_equity = None
    
    iteration = 0
    while True:
        iteration += 1
        
        try:
            data = get_position_and_account(client)
            
            if initial_equity is None:
                initial_equity = data['equity']
            
            if not data['positions']:
                print(f"\n⏳ No position - waiting for entry...")
                time.sleep(10)
                entry_time = datetime.now()  # Reset entry time
                continue
            
            pos = data['positions'][0]
            symbol = pos.symbol
            qty = float(pos.qty)
            entry_price = float(pos.avg_entry_price)
            current_price = float(pos.current_price)
            
            # Calculate P&L
            gross_pnl = float(pos.unrealized_pl)
            gross_pnl_pct = float(pos.unrealized_plpc)
            
            # Calculate position value and fees
            position_value = qty * entry_price
            fee_cost = position_value * ROUND_TRIP_FEE
            
            net_pnl = gross_pnl - fee_cost
            net_pnl_pct = gross_pnl_pct - ROUND_TRIP_FEE
            
            # Hold time
            hold_time = datetime.now() - entry_time
            hold_minutes = hold_time.total_seconds() / 60
            
            # Display
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {symbol}: "
                  f"${current_price:.2f} | "
                  f"GROSS: ${gross_pnl:+.4f} ({gross_pnl_pct*100:+.2f}%) | "
                  f"NET: ${net_pnl:+.4f} ({net_pnl_pct*100:+.2f}%) | "
                  f"Hold: {hold_minutes:.1f}m", end="", flush=True)
            
            # Check exit conditions
            exit_reason = None
            
            # Take Profit (based on GROSS - we book net after)
            if gross_pnl_pct >= TAKE_PROFIT_PCT:
                exit_reason = f"✅ TAKE PROFIT ({gross_pnl_pct*100:.2f}% gross)"
            
            # Stop Loss
            elif gross_pnl_pct <= -STOP_LOSS_PCT:
                exit_reason = f"🛑 STOP LOSS ({gross_pnl_pct*100:.2f}%)"
            
            # Max Hold
            elif hold_minutes >= MAX_HOLD_MINUTES:
                exit_reason = f"⏰ MAX HOLD ({hold_minutes:.0f} min)"
            
            if exit_reason:
                print(f"\n\n{'='*70}")
                print(f"🔴 EXITING POSITION: {exit_reason}")
                print(f"{'='*70}")
                
                # Execute sell
                try:
                    result = sell_position(client, symbol, qty)
                    print(f"📤 Sell order submitted: {result.id}")
                    
                    # Wait for fill
                    time.sleep(2)
                    
                    # Get final account state
                    final_data = get_position_and_account(client)
                    final_equity = final_data['equity']
                    
                    # Calculate actual results
                    actual_exit_price = current_price  # Approximation
                    actual_gross_pnl = (actual_exit_price - entry_price) * qty
                    actual_fee_cost = position_value * ROUND_TRIP_FEE
                    actual_net_pnl = actual_gross_pnl - actual_fee_cost
                    
                    portfolio_growth = (final_equity - initial_equity) / initial_equity * 100
                    
                    # Record trade
                    trade = TradeResult(
                        symbol=symbol,
                        exchange="alpaca",
                        qty=qty,
                        entry_price=entry_price,
                        exit_price=actual_exit_price,
                        entry_time=entry_time.isoformat(),
                        exit_time=datetime.now().isoformat(),
                        hold_minutes=hold_minutes,
                        gross_pnl_usd=actual_gross_pnl,
                        gross_pnl_pct=gross_pnl_pct,
                        fees_usd=actual_fee_cost,
                        net_pnl_usd=actual_net_pnl,
                        net_pnl_pct=net_pnl_pct,
                        exit_reason=exit_reason,
                        portfolio_before=initial_equity,
                        portfolio_after=final_equity,
                        portfolio_growth_pct=portfolio_growth
                    )
                    
                    history["trades"].append(asdict(trade))
                    history["total_net_pnl"] += actual_net_pnl
                    if actual_net_pnl > 0:
                        history["wins"] += 1
                    else:
                        history["losses"] += 1
                    save_history(history)
                    
                    # Print full cycle summary
                    print(f"\n{'='*70}")
                    print(f"🐋 FULL TRADE CYCLE COMPLETED 🐋")
                    print(f"{'='*70}")
                    print(f"📊 TRADE DETAILS:")
                    print(f"   Symbol: {symbol}")
                    print(f"   Quantity: {qty:.8f}")
                    print(f"   Entry: ${entry_price:.2f}")
                    print(f"   Exit: ${actual_exit_price:.2f}")
                    print(f"   Hold Time: {hold_minutes:.1f} minutes")
                    print(f"   Exit Reason: {exit_reason}")
                    print()
                    print(f"💰 P&L BREAKDOWN:")
                    print(f"   GROSS P&L: ${actual_gross_pnl:+.4f} ({gross_pnl_pct*100:+.2f}%)")
                    print(f"   Fees Paid: ${actual_fee_cost:.4f} ({ROUND_TRIP_FEE*100:.1f}%)")
                    print(f"   ════════════════════════════")
                    print(f"   NET P&L: ${actual_net_pnl:+.4f} ({net_pnl_pct*100:+.2f}%)")
                    print()
                    print(f"📈 PORTFOLIO:")
                    print(f"   Before: ${initial_equity:.2f}")
                    print(f"   After: ${final_equity:.2f}")
                    print(f"   GROWTH: {portfolio_growth:+.2f}%")
                    print()
                    print(f"📊 SESSION TOTALS:")
                    print(f"   Total Trades: {len(history['trades'])}")
                    print(f"   Wins: {history['wins']} | Losses: {history['losses']}")
                    print(f"   Total Net P&L: ${history['total_net_pnl']:+.4f}")
                    print(f"{'='*70}")
                    
                    if actual_net_pnl > 0:
                        print(f"\n🎉 WIN! Portfolio grew by {portfolio_growth:+.2f}%")
                    else:
                        print(f"\n📉 Loss. Portfolio changed by {portfolio_growth:+.2f}%")
                    
                    # Reset for next trade
                    initial_equity = final_equity
                    entry_time = datetime.now()
                    
                except Exception as e:
                    print(f"❌ Sell failed: {e}")
            
            time.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            print("\n\n🛑 Monitor stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    monitor_and_trade()
