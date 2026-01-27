#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦈🔪 ORCA KILL EXECUTION - HUNT → KILL → PROFIT 🔪🦈
═══════════════════════════════════════════════════════════════════════════════

"The Orca doesn't just find prey - it KILLS and FEEDS."

This module handles the actual execution:
  1. HUNT  → Find the target (done by global scanner)
  2. KILL  → Execute the trade (BUY or SELL)
  3. WATCH → Monitor for profit target
  4. FEAST → Close position and realize profit

EXCHANGES SUPPORTED:
  🐙 KRAKEN: Full trading (TUSD/USD available)
  🦙 ALPACA: Full trading (USD available)

Gary Leckey | Orca Kills Now | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Position tracking file
POSITION_FILE = "orca_active_positions.json"


@dataclass
class OrcaPosition:
    """An active position held by the Orca."""
    id: str
    symbol: str
    exchange: str
    side: str  # 'long' or 'short'
    
    # Entry details
    entry_price: float
    entry_qty: float
    entry_cost: float  # Total cost including fees
    entry_time: float
    entry_order_id: str
    
    # Target/Stop
    take_profit_pct: float = 5.0   # Default 5% profit target
    stop_loss_pct: float = -3.0    # Default -3% stop loss
    
    # Current state
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    # Exit details (when closed)
    exit_price: float = 0.0
    exit_qty: float = 0.0
    exit_cost: float = 0.0
    exit_time: float = 0.0
    exit_order_id: str = ""
    exit_reason: str = ""
    
    # Final P&L
    realized_pnl: float = 0.0
    status: str = "open"  # 'open', 'closed', 'stopped'
    
    def update_pnl(self, current_price: float):
        """Update unrealized P&L."""
        self.current_price = current_price
        if self.side == 'long':
            self.unrealized_pnl = (current_price - self.entry_price) * self.entry_qty
            self.unrealized_pnl_pct = ((current_price / self.entry_price) - 1) * 100
        else:  # short
            self.unrealized_pnl = (self.entry_price - current_price) * self.entry_qty
            self.unrealized_pnl_pct = ((self.entry_price / current_price) - 1) * 100
    
    def should_take_profit(self) -> bool:
        """Check if we hit profit target."""
        return self.unrealized_pnl_pct >= self.take_profit_pct
    
    def should_stop_loss(self) -> bool:
        """Check if we hit stop loss."""
        return self.unrealized_pnl_pct <= self.stop_loss_pct
    
    def to_dict(self) -> Dict:
        return asdict(self)


class OrcaKillExecutor:
    """
    🦈🔪 THE ORCA KILL EXECUTOR
    
    Takes hunt results and executes actual trades:
    - BUY to open long positions
    - SELL to close positions
    - Monitors for profit/stop
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.positions: Dict[str, OrcaPosition] = {}
        self.kraken = None
        self.alpaca = None
        
        self._init_exchanges()
        self._load_positions()
        
    def _init_exchanges(self):
        """Initialize exchange connections."""
        # Kraken - ALWAYS get real balance, only use dry_run for orders
        try:
            from kraken_client import get_kraken_client
            self.kraken = get_kraken_client()
            if self.kraken:
                # Store original dry_run state
                original_dry_run = getattr(self.kraken, 'dry_run', False)
                # Temporarily disable dry_run to get REAL balance
                self.kraken.dry_run = False
                balance = self.kraken.get_account_balance()
                # Restore dry_run for order execution
                self.kraken.dry_run = self.dry_run
                
                # Check multiple stablecoins
                tusd = float(balance.get('TUSD', 0))
                usd = float(balance.get('USD', 0))
                usdc = float(balance.get('USDC', 0))
                usdt = float(balance.get('USDT', 0))
                total_stable = tusd + usd + usdc + usdt
                
                self.kraken_balance = balance  # Store full balance
                logger.info(f"🐙 Kraken connected: ${tusd:.2f} TUSD, ${usd:.2f} USD, ${usdc:.2f} USDC, ${usdt:.2f} USDT")
                logger.info(f"   Total stable: ${total_stable:.2f} (dry_run orders: {self.dry_run})")
        except Exception as e:
            logger.error(f"Kraken init error: {e}")
            self.kraken_balance = {}
            
        # Alpaca
        try:
            from alpaca_client import AlpacaClient
            self.alpaca = AlpacaClient()
            acct = self.alpaca.get_account()
            cash = float(acct.get('cash', 0))
            logger.info(f"🦙 Alpaca connected: ${cash:.2f} USD")
        except Exception as e:
            logger.error(f"Alpaca init error: {e}")
    
    def _load_positions(self):
        """Load active positions from file."""
        try:
            if os.path.exists(POSITION_FILE):
                with open(POSITION_FILE, 'r') as f:
                    data = json.load(f)
                    for pos_id, pos_data in data.items():
                        self.positions[pos_id] = OrcaPosition(**pos_data)
                logger.info(f"📂 Loaded {len(self.positions)} active positions")
        except Exception as e:
            logger.error(f"Failed to load positions: {e}")
    
    def _save_positions(self):
        """Save active positions to file."""
        try:
            data = {pos_id: pos.to_dict() for pos_id, pos in self.positions.items()}
            with open(POSITION_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save positions: {e}")
    
    def get_balance(self, exchange: str) -> Tuple[str, float]:
        """Get available balance on exchange."""
        if exchange == 'kraken' and self.kraken:
            # Use cached balance if available, otherwise fetch fresh (with dry_run disabled)
            if hasattr(self, 'kraken_balance') and self.kraken_balance:
                balance = self.kraken_balance
            else:
                # Temporarily disable dry_run to get REAL balance
                original_dry_run = getattr(self.kraken, 'dry_run', False)
                self.kraken.dry_run = False
                balance = self.kraken.get_account_balance()
                self.kraken.dry_run = original_dry_run
                self.kraken_balance = balance
            
            # Check for TUSD (primary), then USD, then USDC, then USDT
            for asset in ['TUSD', 'USD', 'ZUSD', 'USDC', 'USDT']:
                amt = float(balance.get(asset, 0))
                if amt > 0.5:  # At least $0.50
                    return asset, amt
            return 'TUSD', 0.0
        elif exchange == 'alpaca' and self.alpaca:
            acct = self.alpaca.get_account()
            return 'USD', float(acct.get('cash', 0))
        return 'USD', 0.0
    
    def get_price(self, symbol: str, exchange: str) -> float:
        """Get current price for symbol."""
        try:
            if exchange == 'kraken' and self.kraken:
                # Normalize symbol (ME/USD -> MEUSD)
                kraken_sym = symbol.replace('/', '')
                price_info = self.kraken.best_price(kraken_sym)
                return float(price_info.get('price', 0))
            elif exchange == 'alpaca' and self.alpaca:
                quote = self.alpaca.get_crypto_quote(symbol.replace('/', ''))
                return float(quote.get('ap', 0) or quote.get('ask', 0))
        except Exception as e:
            logger.error(f"Price fetch error for {symbol}: {e}")
        return 0.0
    
    def execute_kill(self, symbol: str, exchange: str, side: str, 
                     amount_usd: Optional[float] = None,
                     take_profit_pct: float = 5.0,
                     stop_loss_pct: float = -3.0) -> Optional[OrcaPosition]:
        """
        🔪 EXECUTE THE KILL
        
        Args:
            symbol: Trading pair (e.g., "ME/USD")
            exchange: Exchange to trade on ('kraken' or 'alpaca')
            side: 'buy' for long, 'sell' for short
            amount_usd: Amount in USD to trade (default: 90% of balance)
            take_profit_pct: Profit target %
            stop_loss_pct: Stop loss %
        
        Returns:
            OrcaPosition if successful, None if failed
        """
        print(f"\n🦈🔪 ORCA KILL EXECUTION")
        print("=" * 60)
        print(f"   Symbol:   {symbol}")
        print(f"   Exchange: {exchange}")
        print(f"   Side:     {side.upper()}")
        print(f"   TP:       +{take_profit_pct}%")
        print(f"   SL:       {stop_loss_pct}%")
        print(f"   DRY-RUN:  {self.dry_run}")
        print("=" * 60)
        
        # Get balance
        quote_asset, balance = self.get_balance(exchange)
        print(f"\n💰 Available: ${balance:.2f} {quote_asset}")
        
        if balance < 1.0:
            print(f"❌ Insufficient balance on {exchange}")
            return None
        
        # Calculate trade size (90% of balance or specified amount)
        trade_amount = amount_usd or (balance * 0.9)
        trade_amount = min(trade_amount, balance * 0.95)  # Keep 5% buffer
        print(f"📊 Trade amount: ${trade_amount:.2f}")
        
        # Get current price
        price = self.get_price(symbol, exchange)
        if price <= 0:
            print(f"❌ Could not get price for {symbol}")
            return None
        print(f"💵 Current price: ${price:.6f}")
        
        # Calculate quantity
        qty = trade_amount / price
        print(f"📦 Quantity: {qty:.6f} {symbol.split('/')[0]}")
        
        # Execute order
        print(f"\n🔪 EXECUTING {side.upper()} ORDER...")
        
        order_result = None
        if exchange == 'kraken' and self.kraken:
            try:
                # Kraken needs the pair without slash
                kraken_pair = symbol.replace('/', '')
                
                # If we have TUSD, we need to trade METUSD pair or convert first
                if quote_asset == 'TUSD':
                    # Check if direct TUSD pair exists
                    tusd_pair = symbol.split('/')[0] + 'TUSD'
                    try:
                        self.kraken.best_price(tusd_pair)
                        kraken_pair = tusd_pair
                        print(f"   Using TUSD pair: {kraken_pair}")
                    except:
                        # No TUSD pair, need to convert TUSD->USD first
                        print(f"   ⚠️ No {tusd_pair} pair, using USD pair")
                
                order_result = self.kraken.place_market_order(
                    symbol=kraken_pair,
                    side=side,
                    quote_qty=trade_amount
                )
            except Exception as e:
                print(f"❌ Kraken order failed: {e}")
                return None
                
        elif exchange == 'alpaca' and self.alpaca:
            try:
                # Alpaca crypto trading
                order_result = self.alpaca.submit_order(
                    symbol=symbol.replace('/', ''),
                    qty=None,  # Use notional
                    side=side,
                    type='market',
                    time_in_force='gtc',
                    notional=trade_amount
                )
            except Exception as e:
                print(f"❌ Alpaca order failed: {e}")
                return None
        
        if not order_result:
            print(f"❌ Order execution failed")
            return None
        
        # Check for errors
        if 'error' in order_result:
            print(f"❌ Order error: {order_result}")
            return None
        
        # Parse order result
        order_id = order_result.get('orderId', order_result.get('id', str(time.time())))
        exec_price = float(order_result.get('price', price))
        exec_qty = float(order_result.get('executedQty', qty))
        exec_cost = float(order_result.get('cummulativeQuoteQty', trade_amount))
        
        print(f"\n✅ ORDER FILLED!")
        print(f"   Order ID: {order_id}")
        print(f"   Price:    ${exec_price:.6f}")
        print(f"   Quantity: {exec_qty:.6f}")
        print(f"   Cost:     ${exec_cost:.2f}")
        
        # Create position
        pos_id = f"{exchange}_{symbol.replace('/', '')}_{int(time.time())}"
        position = OrcaPosition(
            id=pos_id,
            symbol=symbol,
            exchange=exchange,
            side='long' if side == 'buy' else 'short',
            entry_price=exec_price,
            entry_qty=exec_qty,
            entry_cost=exec_cost,
            entry_time=time.time(),
            entry_order_id=order_id,
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct,
            current_price=exec_price,
            status='open'
        )
        
        # Save position
        self.positions[pos_id] = position
        self._save_positions()
        
        print(f"\n📍 Position opened: {pos_id}")
        print(f"   Target: +{take_profit_pct}% (${exec_price * (1 + take_profit_pct/100):.6f})")
        print(f"   Stop:   {stop_loss_pct}% (${exec_price * (1 + stop_loss_pct/100):.6f})")
        
        return position
    
    def close_position(self, position: OrcaPosition, reason: str = "manual") -> bool:
        """
        Close an open position.
        """
        if position.status != 'open':
            print(f"⚠️ Position {position.id} already {position.status}")
            return False
        
        print(f"\n🔪 CLOSING POSITION: {position.symbol}")
        print(f"   Side: {position.side}")
        print(f"   Entry: ${position.entry_price:.6f}")
        print(f"   Current PnL: {position.unrealized_pnl_pct:+.2f}%")
        print(f"   Reason: {reason}")
        
        # Determine close side
        close_side = 'sell' if position.side == 'long' else 'buy'
        
        # Execute close order
        order_result = None
        if position.exchange == 'kraken' and self.kraken:
            try:
                kraken_pair = position.symbol.replace('/', '')
                order_result = self.kraken.place_market_order(
                    symbol=kraken_pair,
                    side=close_side,
                    quantity=position.entry_qty
                )
            except Exception as e:
                print(f"❌ Close order failed: {e}")
                return False
                
        elif position.exchange == 'alpaca' and self.alpaca:
            try:
                order_result = self.alpaca.submit_order(
                    symbol=position.symbol.replace('/', ''),
                    qty=position.entry_qty,
                    side=close_side,
                    type='market',
                    time_in_force='gtc'
                )
            except Exception as e:
                print(f"❌ Close order failed: {e}")
                return False
        
        if not order_result or 'error' in order_result:
            print(f"❌ Close failed: {order_result}")
            return False
        
        # Update position with exit details
        exit_price = float(order_result.get('price', position.current_price))
        exit_qty = float(order_result.get('executedQty', position.entry_qty))
        exit_cost = float(order_result.get('cummulativeQuoteQty', 0))
        
        position.exit_price = exit_price
        position.exit_qty = exit_qty
        position.exit_cost = exit_cost
        position.exit_time = time.time()
        position.exit_order_id = order_result.get('orderId', '')
        position.exit_reason = reason
        
        # Calculate realized P&L
        if position.side == 'long':
            position.realized_pnl = exit_cost - position.entry_cost
        else:
            position.realized_pnl = position.entry_cost - exit_cost
        
        position.status = 'closed'
        self._save_positions()
        
        pnl_emoji = "🟢" if position.realized_pnl > 0 else "🔴"
        print(f"\n{pnl_emoji} POSITION CLOSED!")
        print(f"   Exit Price: ${exit_price:.6f}")
        print(f"   Realized P&L: ${position.realized_pnl:.4f}")
        
        return True
    
    def monitor_positions(self) -> List[OrcaPosition]:
        """
        Monitor all open positions and close if hit TP/SL.
        Returns list of positions that were closed.
        """
        closed = []
        
        for pos_id, position in list(self.positions.items()):
            if position.status != 'open':
                continue
            
            # Update current price
            price = self.get_price(position.symbol, position.exchange)
            if price <= 0:
                continue
            
            position.update_pnl(price)
            
            # Check take profit
            if position.should_take_profit():
                print(f"\n🎯 TAKE PROFIT HIT: {position.symbol} +{position.unrealized_pnl_pct:.2f}%")
                if self.close_position(position, reason="take_profit"):
                    closed.append(position)
                continue
            
            # Check stop loss
            if position.should_stop_loss():
                print(f"\n🛑 STOP LOSS HIT: {position.symbol} {position.unrealized_pnl_pct:.2f}%")
                if self.close_position(position, reason="stop_loss"):
                    closed.append(position)
                continue
            
            # Print status
            pnl_emoji = "🟢" if position.unrealized_pnl >= 0 else "🔴"
            print(f"{pnl_emoji} {position.symbol}: ${price:.6f} ({position.unrealized_pnl_pct:+.2f}%)")
        
        return closed
    
    def get_open_positions(self) -> List[OrcaPosition]:
        """Get all open positions."""
        return [p for p in self.positions.values() if p.status == 'open']
    
    def status(self):
        """Print current status."""
        print("\n" + "=" * 60)
        print("🦈 ORCA KILL EXECUTOR STATUS")
        print("=" * 60)
        
        # Exchange balances
        kraken_asset, kraken_bal = self.get_balance('kraken')
        alpaca_asset, alpaca_bal = self.get_balance('alpaca')
        print(f"\n💰 BALANCES:")
        print(f"   🐙 Kraken: ${kraken_bal:.2f} {kraken_asset}")
        print(f"   🦙 Alpaca: ${alpaca_bal:.2f} {alpaca_asset}")
        
        # Open positions
        open_pos = self.get_open_positions()
        print(f"\n📍 OPEN POSITIONS: {len(open_pos)}")
        
        total_pnl = 0.0
        for pos in open_pos:
            price = self.get_price(pos.symbol, pos.exchange)
            if price > 0:
                pos.update_pnl(price)
            pnl_emoji = "🟢" if pos.unrealized_pnl >= 0 else "🔴"
            print(f"   {pnl_emoji} {pos.symbol} ({pos.exchange})")
            print(f"      Entry: ${pos.entry_price:.6f}")
            print(f"      Current: ${pos.current_price:.6f}")
            print(f"      P&L: {pos.unrealized_pnl_pct:+.2f}% (${pos.unrealized_pnl:+.4f})")
            total_pnl += pos.unrealized_pnl
        
        if open_pos:
            print(f"\n   💵 Total Unrealized: ${total_pnl:+.4f}")
        
        # Closed positions (recent)
        closed_pos = [p for p in self.positions.values() if p.status == 'closed']
        if closed_pos:
            print(f"\n📊 RECENT CLOSED: {len(closed_pos)}")
            for pos in closed_pos[-5:]:  # Last 5
                pnl_emoji = "🟢" if pos.realized_pnl > 0 else "🔴"
                print(f"   {pnl_emoji} {pos.symbol}: ${pos.realized_pnl:+.4f} ({pos.exit_reason})")
        
        print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# 🦈 QUICK KILL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def orca_execute_kill(symbol: str, exchange: str, side: str, 
                      amount_usd: float = None, dry_run: bool = True):
    """🔪 Execute a kill (trade)."""
    executor = OrcaKillExecutor(dry_run=dry_run)
    return executor.execute_kill(symbol, exchange, side, amount_usd)

def orca_hunt_and_kill(dry_run: bool = True):
    """🦈 Run full hunt cycle and execute best kill."""
    from aureon_live_momentum_hunter import LiveMomentumHunter
    
    # Hunt
    hunter = LiveMomentumHunter(dry_run=dry_run)
    results = hunter.hunt()
    
    if not results:
        print("\n⏳ No kills found - Orca is patient")
        return None
    
    # Execute best kill
    best = results[0]
    executor = OrcaKillExecutor(dry_run=dry_run)
    
    # Determine exchange - check which one has the symbol
    # For now, check if it came from global scan (likely Kraken)
    exchange = 'alpaca'
    if best.nexus_factors.get('extreme_momentum'):
        # Came from global scanner, likely Kraken
        exchange = 'kraken'
    
    position = executor.execute_kill(
        symbol=best.symbol,
        exchange=exchange,
        side=best.side,
        take_profit_pct=5.0,
        stop_loss_pct=-3.0
    )
    
    return position

def orca_monitor():
    """👀 Monitor open positions."""
    executor = OrcaKillExecutor(dry_run=False)  # Always real for monitoring
    return executor.monitor_positions()

def orca_status():
    """📊 Show executor status."""
    executor = OrcaKillExecutor(dry_run=False)
    executor.status()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'status':
            orca_status()
        elif cmd == 'monitor':
            orca_monitor()
        elif cmd == 'hunt':
            # Dry run hunt and kill
            orca_hunt_and_kill(dry_run=True)
        elif cmd == 'hunt-live':
            # LIVE hunt and kill
            print("⚠️ LIVE MODE - Real trades will be executed!")
            confirm = input("Type 'KILL' to confirm: ")
            if confirm == 'KILL':
                orca_hunt_and_kill(dry_run=False)
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python orca_kill_executor.py [status|monitor|hunt|hunt-live]")
    else:
        # Default: show status
        orca_status()
