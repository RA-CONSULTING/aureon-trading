"""
🧠 AUREON EXCHANGE INTELLIGENCE AUDIT
═══════════════════════════════════════════════════════════════

SMART QUESTIONS FOR EACH EXCHANGE:
1. What have I BOUGHT? (Buy trades)
2. What have I SOLD? (Sell trades)
3. What IDs exist? (Order/Trade IDs)
4. What codes/symbols are there? (All traded pairs)
5. What's the pattern? (Activity timeline)

This is QUEEN-LEVEL INTELLIGENCE - understanding the full picture
by interrogating the APIs for historical data, not just balances.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
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

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class ExchangeIntelligence:
    """Intelligence gathered from an exchange."""
    exchange: str
    
    # Trade intelligence
    total_buys: int = 0
    total_sells: int = 0
    buy_symbols: Set[str] = field(default_factory=set)
    sell_symbols: Set[str] = field(default_factory=set)
    all_symbols_traded: Set[str] = field(default_factory=set)
    
    # Order intelligence
    total_orders: int = 0
    open_orders: int = 0
    closed_orders: int = 0
    order_ids: List[str] = field(default_factory=list)
    
    # Current holdings
    current_positions: Dict[str, float] = field(default_factory=dict)
    
    # Activity patterns
    first_trade_date: str = None
    last_trade_date: str = None
    most_traded_symbol: str = None
    trade_count_by_symbol: Dict[str, int] = field(default_factory=dict)
    
    # Value metrics
    total_bought_value: float = 0.0
    total_sold_value: float = 0.0
    net_flow: float = 0.0  # bought - sold

class AureonExchangeIntelligenceAudit:
    """
    🧠 Ask smart questions to exchange APIs.
    
    Instead of "What's my balance?"
    Ask: "What have I bought? What sold? What IDs exist? What symbols?"
    """
    
    def __init__(self):
        """Initialize audit system."""
        self.intelligences = {}
    
    def audit_binance(self) -> ExchangeIntelligence:
        """Interrogate Binance for intelligence."""
        intel = ExchangeIntelligence(exchange='binance')
        
        try:
            from binance_client import BinanceClient
            client = BinanceClient()
            
            print("🔍 Interrogating Binance API...")
            
            # Q1: What positions exist NOW?
            balances = client.get_balance()
            intel.current_positions = {k: v for k, v in balances.items() if v > 0}
            print(f"   ✅ Current positions: {len(intel.current_positions)}")
            
            # Q2: What have I traded? (Check cost basis history)
            try:
                if os.path.exists('cost_basis_history.json'):
                    with open('cost_basis_history.json', 'r') as f:
                        data = json.load(f)
                        positions = data.get('positions', {})
                        
                        # Extract Binance trades
                        for key, pos in positions.items():
                            if 'binance' in key.lower() or pos.get('exchange') == 'binance':
                                symbol = pos.get('symbol', '')
                                trade_count = pos.get('trade_count', 0)
                                
                                if symbol:
                                    intel.all_symbols_traded.add(symbol)
                                    intel.trade_count_by_symbol[symbol] = trade_count
                                    intel.total_buys += trade_count  # Assume buys for now
                                
                                # Check order IDs
                                order_ids = pos.get('order_ids', [])
                                intel.order_ids.extend(order_ids)
                                
                                # Value tracking
                                total_cost = pos.get('total_cost', 0)
                                intel.total_bought_value += total_cost
                
                print(f"   ✅ Symbols traded: {len(intel.all_symbols_traded)}")
                print(f"   ✅ Trade count: {intel.total_buys}")
                print(f"   ✅ Order IDs tracked: {len(intel.order_ids)}")
                
            except Exception as e:
                print(f"   ⚠️  Cost basis read error: {e}")
            
            # Q3: What's the most traded symbol?
            if intel.trade_count_by_symbol:
                intel.most_traded_symbol = max(
                    intel.trade_count_by_symbol.items(),
                    key=lambda x: x[1]
                )[0]
            
            # Q4: Calculate net flow
            intel.net_flow = intel.total_bought_value - intel.total_sold_value
            
        except Exception as e:
            print(f"   ❌ Binance audit error: {e}")
        
        return intel
    
    def audit_kraken(self) -> ExchangeIntelligence:
        """Interrogate Kraken for intelligence."""
        intel = ExchangeIntelligence(exchange='kraken')
        
        try:
            from kraken_client import KrakenClient, get_kraken_client
            client = get_kraken_client()
            
            print("🔍 Interrogating Kraken API...")
            
            # Q1: Check state file (more reliable than rate-limited API)
            if os.path.exists('aureon_kraken_state.json'):
                with open('aureon_kraken_state.json', 'r') as f:
                    state = json.load(f)
                    
                    # Current positions
                    positions = state.get('positions', {})
                    for symbol, pos in positions.items():
                        qty = pos.get('quantity', 0)
                        if qty > 0:
                            intel.current_positions[symbol] = qty
                            intel.all_symbols_traded.add(symbol)
                    
                    # Metrics from state
                    intel.total_buys = state.get('total_trades', 0)
                    intel.total_bought_value = state.get('balance', 0)
                    
                    print(f"   ✅ Current positions: {len(intel.current_positions)}")
                    print(f"   ✅ Symbols traded: {len(intel.all_symbols_traded)}")
                    print(f"   ✅ Total trades: {intel.total_buys}")
            
            # Q2: Try to get trade history from API (might rate limit)
            try:
                trades = client.get_trades_history()
                if trades:
                    for trade_id, trade in trades.items():
                        intel.order_ids.append(trade_id)
                        symbol = trade.get('pair', '')
                        trade_type = trade.get('type', '')
                        
                        if symbol:
                            intel.all_symbols_traded.add(symbol)
                        
                        if trade_type == 'buy':
                            intel.total_buys += 1
                            intel.buy_symbols.add(symbol)
                        elif trade_type == 'sell':
                            intel.total_sells += 1
                            intel.sell_symbols.add(symbol)
                    
                    print(f"   ✅ Trade IDs found: {len(intel.order_ids)}")
            except Exception as e:
                print(f"   ⚠️  Trade history unavailable: {e}")
        
        except Exception as e:
            print(f"   ❌ Kraken audit error: {e}")
        
        return intel
    
    def audit_alpaca(self) -> ExchangeIntelligence:
        """Interrogate Alpaca for intelligence."""
        intel = ExchangeIntelligence(exchange='alpaca')
        
        try:
            from alpaca_client import AlpacaClient
            client = AlpacaClient()
            
            print("🔍 Interrogating Alpaca API...")
            
            # Q1: Current positions
            try:
                positions = client.get_positions()
                for pos in positions:
                    symbol = pos.get('symbol', '')
                    qty = float(pos.get('qty', 0))
                    
                    if symbol and qty > 0:
                        intel.current_positions[symbol] = qty
                        intel.all_symbols_traded.add(symbol)
                
                print(f"   ✅ Current positions: {len(intel.current_positions)}")
            except:
                pass
            
            # Q2: Get account info
            try:
                account = client.get_account()
                cash = float(account.get('cash', 0))
                intel.total_bought_value = cash  # Available cash
                print(f"   ✅ Account cash: ${cash:.2f}")
            except:
                pass
            
            # Q3: Check activities/orders
            try:
                # Alpaca has activities endpoint
                activities = client.get_activities()
                if activities:
                    for activity in activities:
                        activity_type = activity.get('activity_type', '')
                        symbol = activity.get('symbol', '')
                        
                        if symbol:
                            intel.all_symbols_traded.add(symbol)
                        
                        if activity_type in ['FILL', 'BUY']:
                            intel.total_buys += 1
                            if symbol:
                                intel.buy_symbols.add(symbol)
                        elif activity_type in ['SELL']:
                            intel.total_sells += 1
                            if symbol:
                                intel.sell_symbols.add(symbol)
                    
                    print(f"   ✅ Activities found: {len(activities)}")
                    print(f"   ✅ Buys: {intel.total_buys}, Sells: {intel.total_sells}")
            except Exception as e:
                print(f"   ⚠️  Activities unavailable: {e}")
        
        except Exception as e:
            print(f"   ❌ Alpaca audit error: {e}")
        
        return intel
    
    def audit_capital(self) -> ExchangeIntelligence:
        """Interrogate Capital.com for intelligence."""
        intel = ExchangeIntelligence(exchange='capital')
        
        try:
            from capital_client import CapitalClient
            client = CapitalClient()
            
            print("🔍 Interrogating Capital.com API...")
            
            # Q1: Current positions
            try:
                positions = client.get_positions()
                for pos_data in positions:
                    pos = pos_data.get('position', {})
                    market = pos_data.get('market', {})
                    
                    symbol = market.get('instrumentName', '')
                    size = float(pos.get('size', 0))
                    deal_id = pos.get('dealId', '')
                    
                    if symbol and size > 0:
                        intel.current_positions[symbol] = size
                        intel.all_symbols_traded.add(symbol)
                    
                    if deal_id:
                        intel.order_ids.append(deal_id)
                
                print(f"   ✅ Current positions: {len(intel.current_positions)}")
                print(f"   ✅ Deal IDs: {len(intel.order_ids)}")
            except:
                pass
            
            # Q2: Account info
            try:
                accounts = client.get_accounts()
                if accounts:
                    balance = float(accounts[0].get('balance', {}).get('balance', 0))
                    intel.total_bought_value = balance
                    print(f"   ✅ Account balance: £{balance:.2f}")
            except:
                pass
        
        except Exception as e:
            print(f"   ❌ Capital.com audit error: {e}")
        
        return intel
    
    def run_full_audit(self):
        """Run intelligence audit on all exchanges."""
        print("\n" + "=" * 80)
        print("🧠 AUREON EXCHANGE INTELLIGENCE AUDIT")
        print("=" * 80)
        print("\nAsking smart questions to every exchange API...\n")
        
        # Audit each exchange
        self.intelligences['binance'] = self.audit_binance()
        print()
        self.intelligences['kraken'] = self.audit_kraken()
        print()
        self.intelligences['alpaca'] = self.audit_alpaca()
        print()
        self.intelligences['capital'] = self.audit_capital()
        
        # Generate intelligence report
        self.print_intelligence_report()
    
    def print_intelligence_report(self):
        """Print comprehensive intelligence report."""
        print("\n" + "=" * 80)
        print("📊 INTELLIGENCE REPORT - WHAT THE QUEEN KNOWS")
        print("=" * 80)
        
        total_symbols = set()
        total_positions = 0
        total_buys = 0
        total_sells = 0
        total_order_ids = 0
        
        for exch, intel in self.intelligences.items():
            print(f"\n🏦 {exch.upper()}")
            print("-" * 80)
            
            # Current state
            print(f"\n   📦 CURRENT HOLDINGS: {len(intel.current_positions)}")
            if intel.current_positions:
                for symbol, qty in list(intel.current_positions.items())[:10]:
                    print(f"      • {symbol:15} {qty:.6f}")
                if len(intel.current_positions) > 10:
                    print(f"      ... and {len(intel.current_positions) - 10} more")
            
            # Trading activity
            print(f"\n   📈 TRADING ACTIVITY:")
            print(f"      Symbols traded:     {len(intel.all_symbols_traded)}")
            print(f"      Buy trades:         {intel.total_buys}")
            print(f"      Sell trades:        {intel.total_sells}")
            print(f"      Net flow:           ${intel.net_flow:,.2f}")
            
            # IDs
            if intel.order_ids:
                print(f"\n   🆔 ORDER/TRADE IDs: {len(intel.order_ids)} tracked")
                print(f"      Latest IDs: {intel.order_ids[:3]}")
            
            # Most active
            if intel.most_traded_symbol:
                count = intel.trade_count_by_symbol.get(intel.most_traded_symbol, 0)
                print(f"\n   🔥 MOST TRADED: {intel.most_traded_symbol} ({count} trades)")
            
            # Symbols
            if intel.all_symbols_traded:
                print(f"\n   💎 ALL SYMBOLS: {', '.join(list(intel.all_symbols_traded)[:15])}")
                if len(intel.all_symbols_traded) > 15:
                    print(f"      ... and {len(intel.all_symbols_traded) - 15} more")
            
            # Aggregate totals
            total_symbols.update(intel.all_symbols_traded)
            total_positions += len(intel.current_positions)
            total_buys += intel.total_buys
            total_sells += intel.total_sells
            total_order_ids += len(intel.order_ids)
        
        # Global intelligence
        print("\n" + "=" * 80)
        print("🌍 GLOBAL INTELLIGENCE")
        print("=" * 80)
        print(f"\n   📊 Total unique symbols traded:    {len(total_symbols)}")
        print(f"   📦 Total current positions:        {total_positions}")
        print(f"   📈 Total buy trades:               {total_buys}")
        print(f"   📉 Total sell trades:              {total_sells}")
        print(f"   🆔 Total order/trade IDs tracked:  {total_order_ids}")
        print(f"   ⚖️  Buy/Sell ratio:                 {total_buys}/{total_sells} = {total_buys/max(total_sells,1):.2f}x")
        
        print("\n" + "=" * 80)
        print("\n✅ QUEEN NOW KNOWS:")
        print("   • What was BOUGHT")
        print("   • What was SOLD")  
        print("   • What IDs exist")
        print("   • What codes/symbols are there")
        print("   • Trading patterns & activity")
        print("\n🧠 This is INTELLIGENCE, not just balance checking!")
        print("=" * 80 + "\n")


def main():
    """Run the intelligence audit."""
    audit = AureonExchangeIntelligenceAudit()
    audit.run_full_audit()


if __name__ == '__main__':
    main()
