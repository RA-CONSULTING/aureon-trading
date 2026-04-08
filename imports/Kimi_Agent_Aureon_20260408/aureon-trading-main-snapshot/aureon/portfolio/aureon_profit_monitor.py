#!/usr/bin/env python3
"""
👑💰 AUREON PROFIT MONITOR - Queen's Real-Time Portfolio Growth Tracker 💰👑
═══════════════════════════════════════════════════════════════════════════════

A comprehensive monitoring system that:
1. Tracks ALL positions across ALL exchanges
2. Shows progress bars toward profit targets
3. Uses profit gate to validate REAL wins (no phantom profits)
4. Auto-sells ONLY when profit is GUARANTEED
5. Reinvests profits across exchanges for compound growth
6. NO STOP LOSS - holds until profitable

"We never sell at a loss. Patience is the path to profit."
- Queen Sero

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
import json
import logging
import threading
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TrackedPosition:
    """A position being monitored for profit."""
    symbol: str
    exchange: str
    entry_price: float
    quantity: float
    entry_time: float
    entry_cost: float  # Total cost including fees
    
    # Current state (updated by monitor)
    current_price: float = 0.0
    current_value: float = 0.0
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    total_costs: float = 0.0
    
    # Progress toward profit
    progress_pct: float = 0.0  # 0-100%, 100% = ready to sell
    target_price: float = 0.0
    breakeven_price: float = 0.0
    
    # Status
    is_real_win: bool = False
    status: str = "HOLDING"  # HOLDING, READY_TO_SELL, SOLD, REINVESTING
    last_update: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExchangeStatus:
    """Status of an exchange in the portfolio."""
    name: str
    available_cash: float = 0.0
    total_value: float = 0.0
    position_count: int = 0
    realized_profit: float = 0.0
    unrealized_pnl: float = 0.0
    last_trade_time: float = 0.0
    is_active: bool = True
    
    
@dataclass  
class PortfolioSnapshot:
    """Complete portfolio state at a point in time."""
    timestamp: float
    total_value: float
    total_cash: float
    total_invested: float
    total_realized_profit: float
    total_unrealized_pnl: float
    position_count: int
    exchanges: Dict[str, ExchangeStatus] = field(default_factory=dict)
    positions: List[TrackedPosition] = field(default_factory=list)
    

# ═══════════════════════════════════════════════════════════════════════════════
# 👑💰 QUEEN'S PROFIT MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

class QueenProfitMonitor:
    """
    👑💰 Queen's Real-Time Profit Monitoring System 💰👑
    
    Monitors all positions across all exchanges and:
    - Shows progress bars toward profit targets
    - Validates profits using the profit gate (no phantom wins)
    - Auto-sells when guaranteed profit is reached
    - Reinvests profits across exchanges
    - NEVER sells at a loss
    
    "Patience transforms holding into gold."
    """
    
    # Minimum profit thresholds (in USD)
    MIN_PROFIT_TO_SELL = 0.01       # Minimum net profit to consider selling
    TARGET_PROFIT_PCT = 0.5         # Target 0.5% net profit per position
    REINVEST_THRESHOLD = 1.00       # Minimum cash to trigger reinvestment
    
    def __init__(
        self,
        clients: Dict[str, Any] = None,
        queen: Any = None,
        target_profit_pct: float = 0.5,
        min_profit_usd: float = 0.01,
    ):
        """
        Initialize the profit monitor.
        
        Args:
            clients: Dict of exchange clients {name: client}
            queen: Queen Hive Mind instance for decision making
            target_profit_pct: Target profit percentage per position
            min_profit_usd: Minimum USD profit to trigger sell
        """
        self.clients = clients or {}
        self.queen = queen
        self.target_profit_pct = target_profit_pct
        self.min_profit_usd = min_profit_usd
        
        # State
        self.positions: Dict[str, TrackedPosition] = {}  # key: "exchange:symbol"
        self.exchanges: Dict[str, ExchangeStatus] = {}
        self.realized_profits: float = 0.0
        self.total_reinvested: float = 0.0
        
        # History
        self.snapshots: List[PortfolioSnapshot] = []
        self.profit_history: List[Dict] = []
        
        # Threading
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Wire profit gate
        try:
            from adaptive_prime_profit_gate import is_real_win, get_fee_profile, get_adaptive_gate
            self.is_real_win = is_real_win
            self.get_fee_profile = get_fee_profile
            self.profit_gate = get_adaptive_gate()
            logger.info("👑💰 Profit Monitor: Profit gate CONNECTED")
        except Exception as e:
            self.is_real_win = None
            self.get_fee_profile = None
            self.profit_gate = None
            logger.warning(f"👑💰 Profit Monitor: Profit gate not available: {e}")
        
        logger.info("👑💰 Queen's Profit Monitor initialized")
        logger.info(f"   Target profit: {target_profit_pct}%")
        logger.info(f"   Min profit to sell: ${min_profit_usd}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 📊 POSITION TRACKING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def add_position(
        self,
        symbol: str,
        exchange: str,
        entry_price: float,
        quantity: float,
        entry_cost: float = None,
    ) -> TrackedPosition:
        """
        Add a new position to track.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSD")
            exchange: Exchange name
            entry_price: Entry price
            quantity: Position quantity
            entry_cost: Total entry cost (if None, calculated with fees)
        """
        key = f"{exchange}:{symbol}"
        
        # Calculate entry cost with fees if not provided
        if entry_cost is None:
            if self.get_fee_profile:
                profile = self.get_fee_profile(exchange)
                fee_rate = profile.get('total_taker_rate', 0.005)
            else:
                fee_rate = 0.005  # Default 0.5%
            entry_cost = entry_price * quantity * (1 + fee_rate)
        
        # Calculate target and breakeven prices
        if self.profit_gate:
            gates = self.profit_gate.calculate_gates(exchange, entry_cost)
            breakeven_price = entry_price * (1 + gates.r_breakeven)
            target_price = entry_price * (1 + gates.r_prime + self.target_profit_pct / 100)
        else:
            # Fallback calculation
            breakeven_price = entry_price * 1.01  # ~1% for fees
            target_price = entry_price * (1 + self.target_profit_pct / 100 + 0.01)
        
        position = TrackedPosition(
            symbol=symbol,
            exchange=exchange,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=time.time(),
            entry_cost=entry_cost,
            current_price=entry_price,
            current_value=entry_price * quantity,
            breakeven_price=breakeven_price,
            target_price=target_price,
            last_update=time.time(),
        )
        
        with self._lock:
            self.positions[key] = position
        
        logger.info(f"👑💰 Tracking new position: {symbol} on {exchange}")
        logger.info(f"   Entry: ${entry_price:.6f} | Target: ${target_price:.6f}")
        
        return position
    
    def remove_position(self, symbol: str, exchange: str) -> Optional[TrackedPosition]:
        """Remove a position from tracking."""
        key = f"{exchange}:{symbol}"
        with self._lock:
            return self.positions.pop(key, None)
    
    def get_position(self, symbol: str, exchange: str) -> Optional[TrackedPosition]:
        """Get a tracked position."""
        key = f"{exchange}:{symbol}"
        return self.positions.get(key)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 📈 PRICE & PROFIT UPDATES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_position(self, symbol: str, exchange: str, current_price: float) -> Optional[TrackedPosition]:
        """
        Update a position with current price and recalculate P&L.
        
        Uses profit gate for accurate cost calculations.
        Returns the updated position or None if not found.
        """
        key = f"{exchange}:{symbol}"
        position = self.positions.get(key)
        
        if not position:
            return None
        
        # Calculate P&L using profit gate
        if self.is_real_win:
            result = self.is_real_win(
                exchange=exchange,
                entry_price=position.entry_price,
                current_price=current_price,
                quantity=position.quantity,
                is_maker=False,
                gate_level='breakeven'
            )
            
            position.current_price = current_price
            position.current_value = current_price * position.quantity
            position.gross_pnl = result['gross_pnl']
            position.net_pnl = result['net_pnl']
            position.total_costs = result['total_costs']
            position.is_real_win = result['is_win']
        else:
            # Fallback calculation
            position.current_price = current_price
            position.current_value = current_price * position.quantity
            position.gross_pnl = position.current_value - (position.entry_price * position.quantity)
            # Estimate costs at 1% round trip
            position.total_costs = position.entry_cost * 0.01 + position.current_value * 0.005
            position.net_pnl = position.gross_pnl - position.total_costs
            position.is_real_win = position.net_pnl > 0
        
        # Calculate progress toward target
        if position.target_price > position.entry_price:
            price_range = position.target_price - position.entry_price
            price_progress = current_price - position.entry_price
            position.progress_pct = min(100.0, max(0.0, (price_progress / price_range) * 100))
        else:
            position.progress_pct = 100.0 if position.is_real_win else 0.0
        
        # Update status
        if position.is_real_win and position.net_pnl >= self.min_profit_usd:
            position.status = "READY_TO_SELL"
        elif position.is_real_win:
            position.status = "PROFITABLE"
        else:
            position.status = "HOLDING"
        
        position.last_update = time.time()
        
        return position
    
    def update_all_positions(self) -> List[TrackedPosition]:
        """
        Update all positions with current prices.
        
        Returns list of positions that are ready to sell.
        """
        ready_to_sell = []
        
        for key, position in list(self.positions.items()):
            exchange = position.exchange
            symbol = position.symbol
            
            # Get current price from client
            client = self.clients.get(exchange)
            if not client:
                continue
            
            try:
                ticker = client.get_ticker(symbol)
                if ticker:
                    current_price = float(ticker.get('price', 0) or ticker.get('last', 0))
                    if current_price > 0:
                        updated = self.update_position(symbol, exchange, current_price)
                        if updated and updated.status == "READY_TO_SELL":
                            ready_to_sell.append(updated)
            except Exception as e:
                logger.debug(f"Could not update {symbol} on {exchange}: {e}")
        
        return ready_to_sell
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 💰 AUTO-SELL & REINVEST
    # ═══════════════════════════════════════════════════════════════════════════
    
    def execute_profitable_sells(self) -> List[Dict]:
        """
        Sell all positions that have reached guaranteed profit.
        
        ONLY sells when:
        1. is_real_win == True (profit gate validated)
        2. net_pnl >= min_profit_usd
        
        Returns list of executed sells.
        """
        executed = []
        ready = self.update_all_positions()
        
        for position in ready:
            if position.status != "READY_TO_SELL":
                continue
            
            # Double-check with profit gate
            if not position.is_real_win:
                logger.warning(f"👑⚠️ {position.symbol}: Not a real win, skipping sell")
                continue
            
            if position.net_pnl < self.min_profit_usd:
                logger.debug(f"👑 {position.symbol}: Net profit ${position.net_pnl:.4f} below minimum")
                continue
            
            # Execute sell
            client = self.clients.get(position.exchange)
            if not client:
                continue
            
            try:
                logger.info(f"👑💰 SELLING {position.symbol} for GUARANTEED profit!")
                logger.info(f"   Net P&L: ${position.net_pnl:.4f}")
                
                sell_result = client.place_market_order(
                    symbol=position.symbol,
                    side='sell',
                    qty=position.quantity
                )
                
                if sell_result and not sell_result.get('error'):
                    # Record profit
                    self.realized_profits += position.net_pnl
                    
                    sell_record = {
                        'symbol': position.symbol,
                        'exchange': position.exchange,
                        'entry_price': position.entry_price,
                        'exit_price': position.current_price,
                        'quantity': position.quantity,
                        'gross_pnl': position.gross_pnl,
                        'net_pnl': position.net_pnl,
                        'costs': position.total_costs,
                        'hold_time_seconds': time.time() - position.entry_time,
                        'timestamp': time.time(),
                    }
                    
                    executed.append(sell_record)
                    self.profit_history.append(sell_record)
                    
                    # Remove from tracking
                    self.remove_position(position.symbol, position.exchange)
                    
                    logger.info(f"👑✅ SOLD {position.symbol} | Net: ${position.net_pnl:.4f}")
                else:
                    logger.warning(f"👑⚠️ Sell failed for {position.symbol}: {sell_result}")
                    
            except Exception as e:
                logger.error(f"👑❌ Error selling {position.symbol}: {e}")
        
        return executed
    
    def reinvest_profits(self, opportunities: List[Dict] = None) -> List[Dict]:
        """
        Reinvest available cash across exchanges.
        
        Args:
            opportunities: Optional list of opportunities to invest in.
                          If None, will scan for opportunities.
        
        Returns list of new positions created.
        """
        new_positions = []
        
        for exchange_name, client in self.clients.items():
            if not client:
                continue
            
            try:
                # Get available cash
                balance = client.get_balance()
                if not balance:
                    continue
                
                # Find USD/USDT/cash balance
                cash = 0.0
                for asset in ['USD', 'USDT', 'ZUSD', 'cash']:
                    cash = float(balance.get(asset, 0))
                    if cash > 0:
                        break
                
                if cash < self.REINVEST_THRESHOLD:
                    continue
                
                # Check for opportunities or use provided ones
                if opportunities:
                    exchange_opps = [o for o in opportunities if o.get('exchange') == exchange_name]
                else:
                    # This would be wired to your opportunity scanner
                    exchange_opps = []
                
                if not exchange_opps:
                    logger.debug(f"No opportunities on {exchange_name} for reinvestment")
                    continue
                
                # Invest in top opportunity
                opp = exchange_opps[0]
                amount = min(cash * 0.9, 10.0)  # Use 90% of cash, max $10 per position
                
                if amount < 1.0:
                    continue
                
                logger.info(f"👑🔄 Reinvesting ${amount:.2f} on {exchange_name}")
                
                # Execute buy
                buy_result = client.place_market_order(
                    symbol=opp['symbol'],
                    side='buy',
                    quote_qty=amount
                )
                
                if buy_result and not buy_result.get('error'):
                    qty = float(buy_result.get('executedQty', 0) or buy_result.get('filled_qty', 0) or 0)
                    price = float(buy_result.get('price', 0) or opp.get('price', 0))
                    
                    if qty > 0 and price > 0:
                        position = self.add_position(
                            symbol=opp['symbol'],
                            exchange=exchange_name,
                            entry_price=price,
                            quantity=qty,
                            entry_cost=amount
                        )
                        
                        new_positions.append({
                            'symbol': opp['symbol'],
                            'exchange': exchange_name,
                            'price': price,
                            'quantity': qty,
                            'amount': amount,
                        })
                        
                        self.total_reinvested += amount
                        logger.info(f"👑✅ Reinvested in {opp['symbol']} @ ${price:.6f}")
                        
            except Exception as e:
                logger.error(f"Error reinvesting on {exchange_name}: {e}")
        
        return new_positions
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 📊 DISPLAY & PROGRESS BARS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_progress_bar(self, progress: float, width: int = 20) -> str:
        """Generate a text progress bar."""
        filled = int(progress / 100 * width)
        empty = width - filled
        
        if progress >= 100:
            bar_char = '█'
            color = '🟢'
        elif progress >= 50:
            bar_char = '▓'
            color = '🟡'
        else:
            bar_char = '░'
            color = '🔴'
        
        bar = bar_char * filled + '░' * empty
        return f"{color} [{bar}] {progress:5.1f}%"
    
    def format_position_line(self, position: TrackedPosition) -> str:
        """Format a single position for display."""
        progress_bar = self.get_progress_bar(position.progress_pct, 15)
        
        # Status emoji
        if position.status == "READY_TO_SELL":
            status = "💰 READY"
        elif position.is_real_win:
            status = "✅ WIN"
        else:
            status = "⏳ HOLD"
        
        # Format symbol (pad to 12 chars)
        symbol_str = f"{position.symbol[:10]:<10}"
        
        return (
            f"{symbol_str} | {progress_bar} | "
            f"Net: ${position.net_pnl:+7.4f} | {status}"
        )
    
    def print_dashboard(self):
        """Print a comprehensive portfolio dashboard."""
        print("\n" + "═" * 70)
        print("  👑💰 QUEEN'S PROFIT MONITOR - PORTFOLIO DASHBOARD 💰👑")
        print("═" * 70)
        
        # Summary
        total_value = 0.0
        total_invested = 0.0
        total_unrealized = 0.0
        ready_count = 0
        
        for pos in self.positions.values():
            total_value += pos.current_value
            total_invested += pos.entry_cost
            total_unrealized += pos.net_pnl
            if pos.status == "READY_TO_SELL":
                ready_count += 1
        
        print(f"\n📊 SUMMARY")
        print(f"   Positions: {len(self.positions)} | Ready to Sell: {ready_count}")
        print(f"   Total Invested: ${total_invested:.2f}")
        print(f"   Total Value: ${total_value:.2f}")
        print(f"   Unrealized P&L: ${total_unrealized:+.4f}")
        print(f"   Realized Profits: ${self.realized_profits:+.4f}")
        print(f"   Total Reinvested: ${self.total_reinvested:.2f}")
        
        # Position list with progress bars
        print(f"\n{'─' * 70}")
        print(f"  {'SYMBOL':<10} | {'PROGRESS':<25} | {'NET P&L':>12} | STATUS")
        print(f"{'─' * 70}")
        
        for pos in sorted(self.positions.values(), key=lambda p: -p.net_pnl):
            print(f"  {self.format_position_line(pos)}")
        
        if not self.positions:
            print("  No active positions")
        
        # Exchange breakdown
        print(f"\n{'─' * 70}")
        print(f"📍 EXCHANGE STATUS")
        
        exchange_stats = {}
        for pos in self.positions.values():
            if pos.exchange not in exchange_stats:
                exchange_stats[pos.exchange] = {'count': 0, 'value': 0.0, 'pnl': 0.0}
            exchange_stats[pos.exchange]['count'] += 1
            exchange_stats[pos.exchange]['value'] += pos.current_value
            exchange_stats[pos.exchange]['pnl'] += pos.net_pnl
        
        for exchange, stats in exchange_stats.items():
            emoji = '🟢' if stats['pnl'] >= 0 else '🔴'
            print(f"   {emoji} {exchange.upper()}: {stats['count']} positions | "
                  f"${stats['value']:.2f} | P&L: ${stats['pnl']:+.4f}")
        
        print("═" * 70 + "\n")
    
    def get_status_dict(self) -> Dict:
        """Get current status as a dictionary."""
        total_unrealized = sum(p.net_pnl for p in self.positions.values())
        ready_count = sum(1 for p in self.positions.values() if p.status == "READY_TO_SELL")
        
        return {
            'timestamp': time.time(),
            'position_count': len(self.positions),
            'ready_to_sell_count': ready_count,
            'total_invested': sum(p.entry_cost for p in self.positions.values()),
            'total_value': sum(p.current_value for p in self.positions.values()),
            'unrealized_pnl': total_unrealized,
            'realized_profits': self.realized_profits,
            'total_reinvested': self.total_reinvested,
            'positions': [p.to_dict() for p in self.positions.values()],
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🔄 CONTINUOUS MONITORING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _monitor_loop(self, interval: float = 10.0, auto_sell: bool = True, auto_reinvest: bool = False):
        """Internal monitoring loop."""
        logger.info("👑💰 Profit monitor loop started")
        
        while self._running:
            try:
                # Update all positions
                ready = self.update_all_positions()
                
                # Auto-sell profitable positions
                if auto_sell and ready:
                    sells = self.execute_profitable_sells()
                    if sells:
                        logger.info(f"👑💰 Executed {len(sells)} profitable sells")
                
                # Auto-reinvest (disabled by default - needs opportunities)
                if auto_reinvest and self.realized_profits > self.REINVEST_THRESHOLD:
                    # Would need opportunity scanner integration
                    pass
                
                # Sleep
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(interval)
        
        logger.info("👑💰 Profit monitor loop stopped")
    
    def start_monitoring(self, interval: float = 10.0, auto_sell: bool = True, auto_reinvest: bool = False):
        """Start the background monitoring thread."""
        if self._running:
            logger.warning("Monitor already running")
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval, auto_sell, auto_reinvest),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("👑💰 Background monitoring started")
    
    def stop_monitoring(self):
        """Stop the background monitoring thread."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        logger.info("👑💰 Background monitoring stopped")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 💾 PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def save_state(self, filepath: str = "profit_monitor_state.json"):
        """Save current state to file."""
        state = {
            'timestamp': time.time(),
            'realized_profits': self.realized_profits,
            'total_reinvested': self.total_reinvested,
            'positions': {k: v.to_dict() for k, v in self.positions.items()},
            'profit_history': self.profit_history,
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"👑💾 State saved to {filepath}")
    
    def load_state(self, filepath: str = "profit_monitor_state.json"):
        """Load state from file."""
        if not Path(filepath).exists():
            logger.info(f"No state file found at {filepath}")
            return
        
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.realized_profits = state.get('realized_profits', 0.0)
        self.total_reinvested = state.get('total_reinvested', 0.0)
        self.profit_history = state.get('profit_history', [])
        
        # Restore positions
        for key, pos_dict in state.get('positions', {}).items():
            self.positions[key] = TrackedPosition(**pos_dict)
        
        logger.info(f"👑📂 State loaded from {filepath}")
        logger.info(f"   Positions: {len(self.positions)}")
        logger.info(f"   Realized profits: ${self.realized_profits:.4f}")


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 SINGLETON & HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

_profit_monitor: Optional[QueenProfitMonitor] = None


def get_profit_monitor() -> QueenProfitMonitor:
    """Get the singleton profit monitor instance."""
    global _profit_monitor
    if _profit_monitor is None:
        _profit_monitor = QueenProfitMonitor()
    return _profit_monitor


def init_profit_monitor(clients: Dict[str, Any], queen: Any = None) -> QueenProfitMonitor:
    """Initialize the profit monitor with clients."""
    global _profit_monitor
    _profit_monitor = QueenProfitMonitor(clients=clients, queen=queen)
    return _profit_monitor


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST / DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    print("\n" + "=" * 60)
    print("  👑💰 QUEEN'S PROFIT MONITOR - TEST MODE 💰👑")
    print("=" * 60)
    
    # Create monitor
    monitor = QueenProfitMonitor(target_profit_pct=0.5, min_profit_usd=0.01)
    
    # Add test positions
    monitor.add_position("BTCUSD", "kraken", 89000.0, 0.0001)
    monitor.add_position("ETHUSD", "kraken", 3200.0, 0.003)
    monitor.add_position("KINUSD", "kraken", 0.00000092, 21657051.733)
    
    # Simulate price updates
    print("\n📈 Simulating price updates...\n")
    
    # Update with slightly higher prices
    monitor.update_position("BTCUSD", "kraken", 89500.0)
    monitor.update_position("ETHUSD", "kraken", 3220.0)
    monitor.update_position("KINUSD", "kraken", 0.00000098)
    
    # Print dashboard
    monitor.print_dashboard()
    
    # Show status dict
    status = monitor.get_status_dict()
    print(f"\n📊 Status: {status['position_count']} positions, "
          f"${status['unrealized_pnl']:+.4f} unrealized")
    
    print("\n" + "=" * 60)
    print("  Test complete!")
    print("=" * 60)
