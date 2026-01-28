#!/usr/bin/env python3
"""
💰👁️ REAL PORTFOLIO TRACKER - NO PHANTOM NUMBERS! 👁️💰
========================================================

This module tracks ACTUAL balances across all exchanges.
Queen Sero and Orca Intelligence use this to see THE TRUTH.

No more phantom profits. No more fake numbers.
Just cold, hard REALITY.

"The truth shall set you free" - But first it will piss you off.

Gary Leckey | January 2026 | REALITY CHECK SYSTEM
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import os
import sys
import json
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# UTF-8 fix for Windows
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

logger = logging.getLogger(__name__)


@dataclass
class ExchangeBalance:
    """Real balance from a single exchange."""
    exchange: str
    total_usd: float
    cash_usd: float
    positions_usd: float
    timestamp: float
    raw_balances: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass 
class RealPortfolioSnapshot:
    """Complete snapshot of ACTUAL portfolio value."""
    timestamp: float
    total_usd: float
    
    # Per-exchange breakdown
    alpaca_usd: float = 0.0
    kraken_usd: float = 0.0
    binance_usd: float = 0.0
    capital_usd: float = 0.0
    
    # Historical tracking
    starting_capital: float = 78.51  # ACTUAL starting capital
    
    # 💰 P&L BREAKDOWN (The Truth) 💰
    cumulative_net_pnl: float = 0.0   # Total Equity - Starting Capital
    floating_pnl: float = 0.0         # Unrealized (Open Positions)
    lifetime_realized_pnl: float = 0.0 # Cumulative - Floating (Banked)
    
    realized_pnl: float = 0.0  # DEPRECATED: Kept for backward compat (Same as cumulative_net_pnl)
    unrealized_pnl: float = 0.0 # DEPRECATED: Kept for compat (Same as floating_pnl)
    
    total_fees_paid: float = 0.0
    total_trades: int = 0
    
    # Win/Loss tracking
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # Queen's dream progress
    dream_target: float = 1_000_000_000.0  # $1 BILLION
    dream_progress_pct: float = 0.0
    
    # Treasury Tracking (Avalanche Harvester)
    treasury_usd: float = 0.0
    harvest_reserve_breakdown: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'total_usd': round(self.total_usd, 2),
            'alpaca_usd': round(self.alpaca_usd, 2),
            'kraken_usd': round(self.kraken_usd, 2),
            'binance_usd': round(self.binance_usd, 2),
            'capital_usd': round(self.capital_usd, 2),
            'treasury_usd': round(self.treasury_usd, 2),
            'harvest_reserves': self.harvest_reserve_breakdown,
            'starting_capital': self.starting_capital,
            'realized_pnl': round(self.realized_pnl, 2),
            'unrealized_pnl': round(self.unrealized_pnl, 2),
            'total_pnl': round(self.realized_pnl + self.unrealized_pnl, 2),
            'total_fees_paid': round(self.total_fees_paid, 2),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate * 100, 1),
            'dream_progress_pct': self.dream_progress_pct,
            'is_profitable': (self.realized_pnl + self.unrealized_pnl) > 0,
            'net_change_pct': round(((self.total_usd - self.starting_capital) / self.starting_capital) * 100, 2) if self.starting_capital > 0 else 0
        }


class RealPortfolioTracker:
    """
    💰👁️ THE TRUTH TRACKER 👁️💰
    
    Queen Sero and Orca can ALWAYS see the REAL portfolio state.
    No phantom numbers. No fake profits. JUST TRUTH.
    """
    
    # Persistence file
    STATE_FILE = "real_portfolio_state.json"
    HISTORY_FILE = "real_portfolio_history.json"
    
    def __init__(self, starting_capital: float = 78.51):
        """Initialize with REAL starting capital."""
        self.starting_capital = starting_capital
        self.last_snapshot: Optional[RealPortfolioSnapshot] = None
        self.history: List[Dict] = []
        self.max_history = 1000
        
        # Exchange clients (lazy loaded)
        self._alpaca_client = None
        self._kraken_client = None
        self._binance_client = None
        self._capital_client = None
        
        # Load previous state if exists
        self._load_state()
        
        logger.info("💰👁️ Real Portfolio Tracker initialized")
        logger.info(f"   Starting Capital: ${self.starting_capital:.2f}")
    
    def _load_state(self) -> None:
        """Load previous state from disk."""
        try:
            state_path = Path(self.STATE_FILE)
            if state_path.exists():
                with open(state_path, 'r') as f:
                    data = json.load(f)
                    self.starting_capital = data.get('starting_capital', self.starting_capital)
                    self.history = data.get('history', [])[-self.max_history:]
                    logger.info(f"📂 Loaded portfolio state: {len(self.history)} snapshots")
        except Exception as e:
            logger.warning(f"⚠️ Could not load portfolio state: {e}")
    
    def _save_state(self) -> None:
        """Save state to disk."""
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump({
                    'starting_capital': self.starting_capital,
                    'last_update': time.time(),
                    'history': self.history[-self.max_history:]
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ Could not save portfolio state: {e}")
    
    def _get_alpaca_balance(self) -> ExchangeBalance:
        """Get REAL Alpaca balance."""
        try:
            if self._alpaca_client is None:
                from alpaca_client import AlpacaClient
                self._alpaca_client = AlpacaClient()
            
            acc = self._alpaca_client.get_account()
            cash = float(acc.get('cash', 0))
            equity = float(acc.get('equity', 0))
            
            return ExchangeBalance(
                exchange='alpaca',
                total_usd=equity,
                cash_usd=cash,
                positions_usd=equity - cash,
                timestamp=time.time(),
                raw_balances={'cash': cash, 'equity': equity}
            )
        except Exception as e:
            return ExchangeBalance(
                exchange='alpaca',
                total_usd=0.0,
                cash_usd=0.0,
                positions_usd=0.0,
                timestamp=time.time(),
                error=str(e)
            )
    
    def _get_kraken_balance(self) -> ExchangeBalance:
        """Get REAL Kraken balance."""
        try:
            if self._kraken_client is None:
                from kraken_client import KrakenClient
                self._kraken_client = KrakenClient()
            
            balances = self._kraken_client.get_balance()
            
            # Estimate USD value (simplified - stablecoins = 1:1)
            total_usd = 0.0
            raw = {}
            stables = ['USD', 'USDT', 'USDC', 'ZUSD', 'TUSD', 'DAI']
            
            for asset, amount in balances.items():
                amt = float(amount)
                if amt > 0.0001:
                    raw[asset] = amt
                    # Check if it's a stablecoin
                    if any(s in asset.upper() for s in stables):
                        total_usd += amt
            
            return ExchangeBalance(
                exchange='kraken',
                total_usd=total_usd,
                cash_usd=total_usd,
                positions_usd=0.0,
                timestamp=time.time(),
                raw_balances=raw
            )
        except Exception as e:
            return ExchangeBalance(
                exchange='kraken',
                total_usd=0.0,
                cash_usd=0.0,
                positions_usd=0.0,
                timestamp=time.time(),
                error=str(e)
            )
    
    def _get_binance_balance(self) -> ExchangeBalance:
        """Get REAL Binance balance."""
        try:
            if self._binance_client is None:
                from binance_client import BinanceClient
                self._binance_client = BinanceClient()
            
            balances = self._binance_client.get_balance()
            
            total_usd = 0.0
            raw = {}
            stables = ['USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FDUSD']
            
            for asset, data in balances.items():
                free = float(data.get('free', 0))
                locked = float(data.get('locked', 0))
                total = free + locked
                if total > 0.0001:
                    raw[asset] = total
                    if asset.upper() in stables:
                        total_usd += total
            
            return ExchangeBalance(
                exchange='binance',
                total_usd=total_usd,
                cash_usd=total_usd,
                positions_usd=0.0,
                timestamp=time.time(),
                raw_balances=raw
            )
        except Exception as e:
            return ExchangeBalance(
                exchange='binance',
                total_usd=0.0,
                cash_usd=0.0,
                positions_usd=0.0,
                timestamp=time.time(),
                error=str(e)
            )
    
    def _get_capital_balance(self) -> ExchangeBalance:
        """Get REAL Capital.com balance."""
        try:
            if self._capital_client is None:
                from capital_client import CapitalClient
                self._capital_client = CapitalClient()
            
            acc = self._capital_client.get_accounts()
            if acc and len(acc) > 0:
                balance = float(acc[0].get('balance', {}).get('balance', 0))
                return ExchangeBalance(
                    exchange='capital',
                    total_usd=balance,
                    cash_usd=balance,
                    positions_usd=0.0,
                    timestamp=time.time()
                )
            return ExchangeBalance(
                exchange='capital',
                total_usd=0.0,
                cash_usd=0.0,
                positions_usd=0.0,
                timestamp=time.time()
            )
        except Exception as e:
            return ExchangeBalance(
                exchange='capital',
                total_usd=0.0,
                cash_usd=0.0,
                positions_usd=0.0,
                timestamp=time.time(),
                error=str(e)
            )
    
    def _get_trade_stats(self) -> Dict:
        """Get trade statistics from cost basis history."""
        try:
            with open('cost_basis_history.json', 'r') as f:
                data = json.load(f)
            
            positions = data.get('positions', {})
            total_trades = 0
            total_fees = 0.0
            
            for symbol, pos in positions.items():
                total_trades += int(pos.get('trade_count', 0))
                total_fees += float(pos.get('total_fees', 0))
            
            return {
                'total_trades': total_trades,
                'total_fees': total_fees,
                'winning_trades': 0,  # Would need closed trade data
                'losing_trades': 0
            }
        except Exception:
            return {
                'total_trades': 0,
                'total_fees': 0.0,
                'winning_trades': 0,
                'losing_trades': 0
            }
    
    def _get_treasury_state(self) -> Dict:
        """Get Avalanche Treasury state."""
        try:
            treasury_file = Path("state/avalanche_treasury.json")
            if treasury_file.exists():
                with open(treasury_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Could not load treasury state: {e}")
        
        return {
            'total_usd': 0.0,
            'reserves': {}
        }

    def _load_live_profit_source(self) -> Optional[Dict]:
        """
        Load authoritative live profit state from quick_profit_check.py.
        This provides accurately valued positions (including crypto assets).
        """
        try:
            path = Path("live_profit_state.json")
            if path.exists() and time.time() - path.stat().st_mtime < 300: # 5 min fresh
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def get_real_portfolio(self) -> RealPortfolioSnapshot:
        """
        Get REAL portfolio snapshot from ALL exchanges.
        
        This is the TRUTH - what Queen and Orca should see.
        """
        # Get balances from all exchanges (basic checks)
        alpaca = self._get_alpaca_balance()
        kraken = self._get_kraken_balance()
        binance = self._get_binance_balance()
        capital = self._get_capital_balance()
        
        # 1. Calculate Base Equity (Cash + value)
        # Note: Internal _get methods often miss specific crypto position values
        # So we prefer live_profit_state.json if available for TOTAL VALUE
        
        live_state = self._load_live_profit_source()
        
        if live_state and 'totals' in live_state:
            # TRUST THE LIVE STATE (It has better pricing)
            total_usd = float(live_state['totals']['total_value_usd'])
            floating_pnl = float(live_state['totals']['total_pnl_usd'])
            
            # Override exchange breakdowns if possible (optional, keeping simple for now)
            # Just ensure total matches reality
        else:
            # Fallback to internal check (might undervalue)
            total_usd = (
                alpaca.total_usd + 
                kraken.total_usd + 
                binance.total_usd + 
                capital.total_usd
            )
            # Estimate floating from alpaca (others assume 0 in current impl)
            floating_pnl = alpaca.positions_usd - (alpaca.total_usd - alpaca.cash_usd) # Rough approx
            # Actually, alpaca.positions_usd is Value. PnL is harder to derive without cost basis here.
            # We will default to 0 if live_state missing.
            floating_pnl = 0.0

        # Get trade stats
        trade_stats = self._get_trade_stats()
        
        # Get treasury state
        treasury = self._get_treasury_state()
        treasury_usd = float(treasury.get('total_usd', 0.0))
        
        # 2. Calculate P&L Metaphysics
        cumulative_net_pnl = total_usd - self.starting_capital
        lifetime_realized_pnl = cumulative_net_pnl - floating_pnl
        
        # Create snapshot
        snapshot = RealPortfolioSnapshot(
            timestamp=time.time(),
            total_usd=total_usd,
            alpaca_usd=alpaca.total_usd,
            kraken_usd=kraken.total_usd, # Note: This might be cash-only if live_state used
            binance_usd=binance.total_usd,
            capital_usd=capital.total_usd,
            
            starting_capital=self.starting_capital,
            
            # The TRUTH
            cumulative_net_pnl=cumulative_net_pnl,
            floating_pnl=floating_pnl,
            lifetime_realized_pnl=lifetime_realized_pnl,
            
            # Legacy Compat
            realized_pnl=cumulative_net_pnl, 
            unrealized_pnl=floating_pnl,
            
            total_fees_paid=trade_stats['total_fees'],
            total_trades=trade_stats['total_trades'],
            winning_trades=trade_stats['winning_trades'],
            losing_trades=trade_stats['losing_trades'], 
            dream_progress_pct=(total_usd / 1_000_000_000.0) * 100 if total_usd > 0 else 0,
            treasury_usd=treasury_usd,
            harvest_reserve_breakdown=treasury.get('reserves', {})
        )
        
        # Update history
        self.last_snapshot = snapshot
        try:
            self.history.append(snapshot.__dict__) # Serialize
        except:
             # Fallback if __dict__ fails (dataclass normally supports it, but just in case)
             pass
             
        self._save_state()
        
        return snapshot
    
    def get_quick_summary(self) -> Dict:
        """Get a quick summary for Queen/Orca display."""
        snapshot = self.get_real_portfolio()
        
        # Determine status
        if snapshot.cumulative_net_pnl > 0:
            status = "📈 PROFITABLE"
            status_emoji = "💰"
        elif snapshot.cumulative_net_pnl < -10:
            status = "📉 LOSING"
            status_emoji = "🔴"
        else:
            status = "📊 BREAK-EVEN"
            status_emoji = "🟡"
        
        return {
            'status': status,
            'status_emoji': status_emoji,
            'total_usd': f"${snapshot.total_usd:.2f}",
            'starting_capital': f"${snapshot.starting_capital:.2f}",
            
            # The Three PnLs
            'cumulative_net': f"${snapshot.cumulative_net_pnl:+.2f}",
            'floating': f"${snapshot.floating_pnl:+.2f}",
            'lifetime_realized': f"${snapshot.lifetime_realized_pnl:+.2f}",
            
            'pnl_pct': f"{(snapshot.cumulative_net_pnl / snapshot.starting_capital * 100):+.1f}%",
            'total_trades': snapshot.total_trades,
            'dream_progress': f"{snapshot.dream_progress_pct:.10f}%",
            'treasury': f"${snapshot.treasury_usd:.2f}",
            'exchanges': {
                'alpaca': f"${snapshot.alpaca_usd:.2f}",
                'kraken': f"${snapshot.kraken_usd:.2f}",
                'binance': f"${snapshot.binance_usd:.2f}",
                'capital': f"${snapshot.capital_usd:.2f}"
            },
            'timestamp': datetime.fromtimestamp(snapshot.timestamp).isoformat()
        }
    
    def format_for_queen(self) -> str:
        """Format portfolio for Queen's display."""
        summary = self.get_quick_summary()
        
        lines = [
            "═══════════════════════════════════════════════════════",
            f"     👑💰 QUEEN'S REAL PORTFOLIO STATUS 💰👑",
            "═══════════════════════════════════════════════════════",
            f"  Status: {summary['status_emoji']} {summary['status']}",
            f"  ",
            f"  💵 TOTAL VALUE: {summary['total_usd']}",
            f"  💎 TREASURY: {summary['treasury']}",
            f"  📊 Started With: {summary['starting_capital']}",
            f"  ",
            f"  📈 P&L BREAKDOWN:",
            f"     🌊 Floating (Open):   {summary['floating']}",
            f"     💰 Realized (Banked): {summary['lifetime_realized']}",
            f"     🏆 Cumulative Net:    {summary['cumulative_net']} ({summary['pnl_pct']})",
            f"  ",
            f"  🏦 BY EXCHANGE:",
            f"     🦙 Alpaca:  {summary['exchanges']['alpaca']}",
            f"     🐙 Kraken:  {summary['exchanges']['kraken']}",
            f"     🟡 Binance: {summary['exchanges']['binance']}",
            f"     💼 Capital: {summary['exchanges']['capital']}",
            f"  ",
            f"  📊 Total Trades: {summary['total_trades']}",
            f"  🎯 Dream Progress: {summary['dream_progress']}",
            "═══════════════════════════════════════════════════════"
        ]
        
        return "\n".join(lines)
    
    def format_for_orca(self) -> str:
        """Format portfolio for Orca's hunting display."""
        summary = self.get_quick_summary()
        
        lines = [
            "🦈═══════════════════════════════════════════════════🦈",
            f"        ORCA HUNTING RESOURCES",
            "🦈═══════════════════════════════════════════════════🦈",
            f"  🎯 Available Capital: {summary['total_usd']}",
            f"  📊 Hunt Status: {summary['status']}",
            f"  📈 Season P&L: {summary['pnl']}",
            f"  🔪 Kills (Trades): {summary['total_trades']}",
            "🦈═══════════════════════════════════════════════════🦈"
        ]
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 🌐 SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_tracker_instance: Optional[RealPortfolioTracker] = None


def get_real_portfolio_tracker() -> RealPortfolioTracker:
    """Get the singleton portfolio tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = RealPortfolioTracker()
    return _tracker_instance


def get_real_balance() -> Dict:
    """Quick function to get real balance."""
    return get_real_portfolio_tracker().get_quick_summary()


def show_real_portfolio():
    """Print real portfolio to console."""
    tracker = get_real_portfolio_tracker()
    print(tracker.format_for_queen())


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST / CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Real Portfolio Tracker")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--orca", action="store_true", help="Orca format")
    args = parser.parse_args()
    
    tracker = get_real_portfolio_tracker()
    
    if args.json:
        snapshot = tracker.get_real_portfolio()
        print(json.dumps(snapshot.to_dict(), indent=2))
    elif args.orca:
        print(tracker.format_for_orca())
    else:
        print(tracker.format_for_queen())
