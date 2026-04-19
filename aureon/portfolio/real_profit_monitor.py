#!/usr/bin/env python3
"""
🎯 REAL PROFIT MONITOR
═══════════════════════════════════════════════════════════════════════

Monitors margin trades and shows ACTUAL profit after ALL fees.
- Gross profit (what the price did)
- All fees deducted (entry + exit + rollover)
- Real net profit (what you actually keep)
- True breakeven price (accounting for ALL costs)
- 4-hour rollover fee accumulation in real-time

Usage:
    python real_profit_monitor.py
"""

import json
import time
import math
from datetime import datetime, timedelta
from pathlib import Path

# Fee rates from Kraken
KRAKEN_OPEN_FEE = 0.00376      # 0.376%
KRAKEN_CLOSE_FEE = 0.0035      # 0.35%
KRAKEN_ROLLOVER_RATE = 0.0001  # 0.01% per 4 hours
KRAKEN_ROLLOVER_INTERVAL = 4 * 3600  # 4 hours in seconds


class RealProfitMonitor:
    """Monitor real profit on margin trades."""

    def __init__(self):
        self.root_dir = Path(__file__).parent

    def calculate_real_profit(self, trade, current_price=None):
        """
        Calculate REAL profit accounting for ALL fees.

        Returns dict with:
            - gross_pnl: Price movement profit (before fees)
            - all_fees: Total fees paid
            - net_pnl: REAL profit after fees
            - breakeven_price: Price needed to break even
            - rollover_accumulation: Rollover fees so far
        """

        if current_price is None:
            current_price = trade.get('current_price', trade.get('exit_price'))

        entry_price = trade.get('entry_price', 0)
        exit_price = trade.get('exit_price', current_price)
        volume = trade.get('volume', 0)
        side = trade.get('side', 'buy').lower()
        entry_time = trade.get('entry_time')
        leverage = trade.get('leverage', 1)

        # Parse entry time
        if entry_time is None:
            entry_ts = time.time()
        elif isinstance(entry_time, str):
            try:
                entry_dt = datetime.fromisoformat(entry_time)
                entry_ts = entry_dt.timestamp()
            except:
                entry_ts = time.time()
        else:
            entry_ts = float(entry_time) if entry_time else time.time()

        # 1. GROSS PROFIT (before fees)
        if side == 'buy':
            gross_pnl = (current_price - entry_price) * volume
        else:
            gross_pnl = (entry_price - current_price) * volume

        # 2. ENTRY FEE
        entry_cost = entry_price * volume
        entry_fee = entry_cost * KRAKEN_OPEN_FEE

        # 3. EXIT FEE (estimated on current price if still open)
        exit_cost = current_price * volume
        exit_fee = exit_cost * KRAKEN_CLOSE_FEE

        # 4. ROLLOVER FEES (every 4 hours held)
        hold_time = time.time() - entry_ts
        rollover_periods = math.ceil(hold_time / KRAKEN_ROLLOVER_INTERVAL) if hold_time > 0 else 0
        rollover_fees = rollover_periods * entry_cost * KRAKEN_ROLLOVER_RATE

        # 5. TOTAL FEES
        total_fees = entry_fee + exit_fee + rollover_fees

        # 6. REAL PROFIT (after all fees)
        net_pnl = gross_pnl - total_fees

        # 7. BREAKEVEN PRICE
        # breakeven = entry_price + (total_fees + profit_target) / volume
        # simplified: what price do we need to break even?
        fee_per_unit = total_fees / volume if volume > 0 else 0

        if side == 'buy':
            breakeven_price = entry_price + fee_per_unit
        else:
            breakeven_price = entry_price - fee_per_unit

        # 8. FEES BREAKDOWN
        fees_breakdown = {
            'entry_fee': entry_fee,
            'exit_fee': exit_fee,
            'rollover_fees': rollover_fees,
            'total': total_fees
        }

        # 9. HOLD TIME
        hold_minutes = hold_time / 60
        hold_hours = hold_time / 3600

        return {
            'entry_price': entry_price,
            'current_price': current_price,
            'exit_price': exit_price,
            'volume': volume,
            'entry_cost': entry_cost,
            'gross_pnl': gross_pnl,
            'fees': fees_breakdown,
            'net_pnl': net_pnl,
            'breakeven_price': breakeven_price,
            'hold_time_minutes': hold_minutes,
            'hold_time_hours': hold_hours,
            'rollover_periods': rollover_periods,
            'is_profitable': net_pnl > 0,
            'fee_burden_pct': (total_fees / entry_cost * 100) if entry_cost > 0 else 0,
            'leverage': leverage
        }

    def format_trade_report(self, trade, analysis):
        """Format a trade analysis report."""

        pair = trade.get('pair', 'UNKNOWN')
        side = trade.get('side', 'buy').upper()
        entry_time = trade.get('entry_time', 'Unknown')

        report = f"""
╔════════════════════════════════════════════════════════════════╗
║  {pair} - {side} POSITION ANALYSIS
╠════════════════════════════════════════════════════════════════╣

📊 POSITION
  Entry Price:    ${analysis['entry_price']:.4f}
  Current Price:  ${analysis['current_price']:.4f}
  Volume:         {analysis['volume']:.8f} {pair.replace('USD', '')}
  Leverage:       {analysis['leverage']}x
  Entry Time:     {entry_time}
  Hold Time:      {analysis['hold_time_minutes']:.1f}m ({analysis['hold_time_hours']:.2f}h)

💰 PROFIT ANALYSIS
  Gross P&L:      ${analysis['gross_pnl']:+.2f}  ← Price movement only

  FEES BREAKDOWN:
    Entry Fee:    ${analysis['fees']['entry_fee']:+.2f}  (0.376%)
    Exit Fee:     ${analysis['fees']['exit_fee']:+.2f}  (0.35%)
    Rollover Fee: ${analysis['fees']['rollover_fees']:+.2f}  ({analysis['rollover_periods']} × 4h periods)
    ─────────────────────────
    Total Fees:   ${analysis['fees']['total']:+.2f}  ({analysis['fee_burden_pct']:.2f}% of entry)

  NET P&L:        ${analysis['net_pnl']:+.2f}  ← REAL PROFIT (after all fees)

  Status:         {'✅ TRUE PROFIT' if analysis['is_profitable'] else '❌ LOSS'}

🎯 BREAKEVEN ANALYSIS
  Breakeven Price: ${analysis['breakeven_price']:.4f}
  Distance:       ${abs(analysis['current_price'] - analysis['breakeven_price']):.4f}

  {'✅ ABOVE breakeven' if analysis['is_profitable'] else '❌ BELOW breakeven'}

╚════════════════════════════════════════════════════════════════╝
"""
        return report

    def monitor_active_trades(self):
        """Monitor active margin trades."""

        state_file = self.root_dir / 'kraken_margin_army_state.json'

        if not state_file.exists():
            print("❌ No margin state file found")
            return

        try:
            with open(state_file) as f:
                state = json.load(f)

            active_trade = state.get('active_trade')

            if not active_trade:
                print("ℹ️  No active margin trade currently")
                return

            print("\n" + "="*70)
            print("🔍 ACTIVE MARGIN TRADE - REAL PROFIT MONITOR")
            print("="*70)

            # For active trades, we need to fetch current price from Kraken
            try:
                from aureon.exchanges.kraken_client import KrakenClient
                kraken = KrakenClient()
                pair = active_trade.get('pair', 'UNKNOWN')
                ticker = kraken.get_ticker(pair)
                if ticker:
                    current_price = float(ticker.get('price', 0))
                else:
                    current_price = active_trade.get('entry_price')
            except:
                current_price = active_trade.get('entry_price')

            analysis = self.calculate_real_profit(active_trade, current_price=current_price)
            report = self.format_trade_report(active_trade, analysis)
            print(report)

        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()

    def monitor_recent_trades(self, count=5):
        """Monitor recent completed trades."""

        state_file = self.root_dir / 'kraken_margin_army_state.json'

        if not state_file.exists():
            print("❌ No margin state file found")
            return

        try:
            with open(state_file) as f:
                state = json.load(f)

            completed = state.get('completed_trades', [])

            if not completed:
                print("ℹ️  No completed trades")
                return

            print("\n" + "="*70)
            print(f"🔍 LAST {min(count, len(completed))} COMPLETED TRADES - REAL PROFIT CHECK")
            print("="*70)

            for i, trade in enumerate(completed[-count:], 1):
                pair = trade.get('pair', 'UNKNOWN')

                # Use exit price for completed trades
                analysis = self.calculate_real_profit(
                    trade,
                    current_price=trade.get('exit_price', trade.get('current_price'))
                )

                # Compact view for history
                status = '✅' if analysis['is_profitable'] else '❌'

                print(f"\n{i}. {pair} - {trade.get('side').upper()}")
                print(f"   {status} Gross: ${analysis['gross_pnl']:+.2f} | "
                      f"Fees: ${analysis['fees']['total']:+.2f} | "
                      f"NET: ${analysis['net_pnl']:+.2f}")
                print(f"   Hold: {analysis['hold_time_minutes']:.1f}m | "
                      f"Fee Burden: {analysis['fee_burden_pct']:.2f}%")

        except Exception as e:
            print(f"Error: {e}")

    def monitor_continuous(self, interval=10):
        """Continuously monitor active trades."""

        print("\n" + "="*70)
        print("🔄 CONTINUOUS REAL PROFIT MONITOR (Press Ctrl+C to stop)")
        print("="*70)

        try:
            while True:
                # Clear screen (works on most terminals)
                print("\033[2J\033[H")

                print(f"\n📊 REAL PROFIT MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*70)

                self.monitor_active_trades()

                print(f"\nNext refresh in {interval}s... (Ctrl+C to stop)\n")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor real profit on margin trades")
    parser.add_argument('--active', action='store_true', help='Show active trade only')
    parser.add_argument('--recent', type=int, default=5, help='Show recent N trades')
    parser.add_argument('--continuous', type=int, default=10, help='Continuous monitor (refresh every N seconds)')
    parser.add_argument('--all', action='store_true', help='Show all completed trades')

    args = parser.parse_args()

    monitor = RealProfitMonitor()

    if args.continuous:
        monitor.monitor_continuous(interval=args.continuous)
    elif args.active:
        monitor.monitor_active_trades()
    elif args.all:
        # Count all trades
        state_file = Path(__file__).parent / 'kraken_margin_army_state.json'
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            monitor.monitor_recent_trades(count=len(state.get('completed_trades', [])))
    else:
        monitor.monitor_recent_trades(count=args.recent)


if __name__ == '__main__':
    main()
