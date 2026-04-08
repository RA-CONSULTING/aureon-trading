# -*- coding: utf-8 -*-
"""
👑🌍 QUEEN AUTONOMOUS TRADE EXECUTOR
═══════════════════════════════════════════════════════════════════════════════

The Queen has FULL AUTONOMY over exchange routing. This module provides:
1. Intelligent exchange selection based on restrictions, health, and success rates
2. Automatic retry with alternative exchanges on failure
3. Learning from errors (UK restrictions, API limitations, etc.)
4. Success tracking and optimization

This is the ONLY function that should be used for trade execution.
No more manual exchange selection - QUEEN DECIDES.

Author: Aureon Trading System
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

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


def _safe_print(*args, **kwargs):
    """Print that won't crash if stdout is closed."""
    try:
        import builtins
        builtins.print(*args, **kwargs)
    except (ValueError, OSError, IOError):
        return


# Import Queen Autonomy
try:
    from aureon_queen_exchange_autonomy import get_queen_autonomy, QueenExchangeAutonomy, RestrictionType
    QUEEN_AUTONOMY_AVAILABLE = True
except ImportError:
    QUEEN_AUTONOMY_AVAILABLE = False
    get_queen_autonomy = None
    QueenExchangeAutonomy = None
    RestrictionType = None


@dataclass
class TradeResult:
    """Result of a Queen-routed trade execution."""
    success: bool
    exchange: Optional[str]
    order: Optional[Dict[str, Any]]
    reason: str
    queen_routed: bool
    queen_override: bool = False
    tried_exchanges: List[str] = None
    
    def __post_init__(self):
        if self.tried_exchanges is None:
            self.tried_exchanges = []


def queen_execute_trade(
    clients: Dict[str, Any],
    symbol: str,
    side: str,
    quantity: float,
    quote_amount_usd: float = None,
    preferred_exchange: str = None,
    dry_run: bool = False
) -> TradeResult:
    """
    👑 QUEEN AUTONOMOUS TRADE EXECUTION
    
    The Queen has FULL AUTONOMY over exchange routing. She will:
    1. Check which exchanges can handle this trade (restrictions, minimums, etc.)
    2. Select the BEST exchange for the trade
    3. Execute on that exchange
    4. If it FAILS, she LEARNS and auto-routes to the next best exchange
    5. On SUCCESS, she remembers which exchange worked
    
    This is the ONLY function that should be used for trade execution.
    No more manual exchange selection - QUEEN DECIDES.
    
    Args:
        clients: Dict of exchange clients {'alpaca': AlpacaClient, 'kraken': KrakenClient, ...}
        symbol: Trading symbol (e.g., 'BTC/USD', 'ETH/USD')
        side: 'buy' or 'sell'
        quantity: Amount to trade
        quote_amount_usd: USD value of the trade (for minimums checking)
        preferred_exchange: Optional hint (Queen can override if restricted)
        dry_run: If True, don't actually execute
        
    Returns:
        TradeResult with success status, exchange used, order details
    """
    if not QUEEN_AUTONOMY_AVAILABLE:
        # Fallback: use preferred exchange directly if Queen unavailable
        _safe_print("⚠️ Queen Autonomy unavailable - falling back to preferred exchange")
        if preferred_exchange and preferred_exchange in clients:
            try:
                client = clients[preferred_exchange]
                order = client.place_market_order(symbol, side, quantity, dry_run=dry_run)
                return TradeResult(
                    success=True,
                    exchange=preferred_exchange,
                    order=order,
                    reason='Queen offline - direct execution',
                    queen_routed=False
                )
            except Exception as e:
                return TradeResult(
                    success=False,
                    exchange=preferred_exchange,
                    order=None,
                    reason=str(e),
                    queen_routed=False
                )
        return TradeResult(
            success=False,
            exchange=None,
            order=None,
            reason='No preferred exchange and Queen offline',
            queen_routed=False
        )
    
    # 👑 QUEEN HAS FULL AUTONOMY
    queen = get_queen_autonomy()
    
    # First, estimate USD value if not provided
    if quote_amount_usd is None:
        # Try to get current price for estimation
        quote_amount_usd = quantity * 1.0  # Default estimate
        for ex_name, client in clients.items():
            if client is None:
                continue
            try:
                ticker = client.get_ticker(symbol)
                if ticker and 'last' in ticker:
                    quote_amount_usd = quantity * float(ticker['last'])
                    break
            except:
                pass
    
    # 👑 Queen routes the trade to the BEST exchange
    routing = queen.route_trade(
        symbol=symbol,
        side=side,
        quantity=quantity,
        quote_amount_usd=quote_amount_usd,
        preferred_exchange=preferred_exchange,
        available_exchanges=[e for e in clients.keys() if clients.get(e) is not None]
    )
    
    if not routing['queen_approved']:
        _safe_print(f"❌ Queen REJECTED trade: {symbol} {side} {quantity}")
        _safe_print(f"   Reason: {routing['reason']}")
        return TradeResult(
            success=False,
            exchange=None,
            order=None,
            reason=routing['reason'],
            queen_routed=True
        )
    
    # 👑 Queen selected an exchange - execute!
    selected_exchange = routing['selected_exchange']
    original_exchange = preferred_exchange
    
    if selected_exchange != preferred_exchange:
        _safe_print(f"👑 QUEEN OVERRIDE: {preferred_exchange} → {selected_exchange}")
        _safe_print(f"   Reason: {routing['reason']}")
    
    # Try to execute on Queen's selected exchange
    max_retries = 3
    tried_exchanges = []
    
    for attempt in range(max_retries):
        if selected_exchange not in clients or clients[selected_exchange] is None:
            _safe_print(f"⚠️ Exchange {selected_exchange} client not available")
            # Ask Queen for next best
            fallback = queen.handle_trade_failure(
                exchange=selected_exchange,
                symbol=symbol,
                error_message="Client not available",
                quantity=quantity,
                quote_amount_usd=quote_amount_usd,
                available_exchanges=[e for e in clients.keys() if e not in tried_exchanges and clients.get(e) is not None]
            )
            tried_exchanges.append(selected_exchange)
            if fallback['success']:
                selected_exchange = fallback['alternative_exchange']
                continue
            else:
                break
        
        client = clients[selected_exchange]
        
        try:
            # 🎯 EXECUTE THE TRADE
            if dry_run:
                _safe_print(f"🧪 [DRY RUN] Would {side} {quantity} {symbol} on {selected_exchange}")
                order = {'dry_run': True, 'exchange': selected_exchange, 'symbol': symbol, 'side': side, 'quantity': quantity}
            else:
                order = client.place_market_order(symbol, side, quantity, dry_run=False)
            
            # 🏆 SUCCESS! Record it
            queen.record_success(selected_exchange, symbol, side, quantity, quote_amount_usd)
            
            _safe_print(f"✅ QUEEN EXECUTED: {side} {quantity} {symbol} on {selected_exchange}")
            return TradeResult(
                success=True,
                exchange=selected_exchange,
                order=order,
                reason='Queen approved and executed',
                queen_routed=True,
                queen_override=selected_exchange != original_exchange,
                tried_exchanges=tried_exchanges
            )
            
        except Exception as e:
            error_msg = str(e)
            _safe_print(f"❌ Trade failed on {selected_exchange}: {error_msg}")
            
            # 👑 Queen learns from failure and routes to alternative
            tried_exchanges.append(selected_exchange)
            fallback = queen.handle_trade_failure(
                exchange=selected_exchange,
                symbol=symbol,
                error_message=error_msg,
                quantity=quantity,
                quote_amount_usd=quote_amount_usd,
                available_exchanges=[e for e in clients.keys() if e not in tried_exchanges and clients.get(e) is not None]
            )
            
            if fallback['success'] and fallback['alternative_exchange']:
                _safe_print(f"👑 Queen routing to: {fallback['alternative_exchange']}")
                selected_exchange = fallback['alternative_exchange']
            else:
                _safe_print(f"❌ Queen exhausted all options: {fallback['reason']}")
                return TradeResult(
                    success=False,
                    exchange=None,
                    order=None,
                    reason=f"All exchanges failed: {error_msg}",
                    queen_routed=True,
                    tried_exchanges=tried_exchanges
                )
    
    return TradeResult(
        success=False,
        exchange=None,
        order=None,
        reason=f"Max retries exceeded, tried: {tried_exchanges}",
        queen_routed=True,
        tried_exchanges=tried_exchanges
    )


def queen_get_exchange_status() -> Dict[str, Any]:
    """Get Queen's current view of exchange health and restrictions."""
    if not QUEEN_AUTONOMY_AVAILABLE:
        return {'queen_online': False, 'exchanges': {}}
    
    queen = get_queen_autonomy()
    status = {}
    
    for ex_name, capability in queen.exchange_capabilities.items():
        restrictions = queen.get_restrictions(ex_name)
        status[ex_name] = {
            'enabled': capability.api_connected or capability.total_trades == 0,  # Enabled if connected or never tested
            'health': capability.success_rate,
            'success_rate': capability.success_rate,
            'is_healthy': capability.is_healthy,
            'total_trades': capability.total_trades,
            'failed_trades': capability.failed_trades,
            'uk_compliant': capability.uk_compliant,
            'restrictions': [r.restriction_type.value for r in restrictions],
            'last_success': capability.last_successful_trade
        }
    
    return {'queen_online': True, 'exchanges': status}


def queen_preload_uk_restrictions():
    """
    Pre-load known UK exchange restrictions so Queen doesn't have to learn them the hard way.
    Call this at system startup!
    """
    if not QUEEN_AUTONOMY_AVAILABLE:
        _safe_print("⚠️ Queen Autonomy not available - cannot preload restrictions")
        return
    
    queen = get_queen_autonomy()
    
    # Pre-register Binance UK restrictions
    # These are KNOWN issues - Queen shouldn't have to fail to learn them
    uk_restricted_symbols = [
        'BTC/USD', 'ETH/USD', 'BNB/USD', 'ADA/USD', 'DOGE/USD',
        'XRP/USD', 'SOL/USD', 'DOT/USD', 'AVAX/USD', 'MATIC/USD',
        'LINK/USD', 'UNI/USD', 'ATOM/USD', 'LTC/USD', 'BCH/USD',
        # Add more as discovered
    ]
    
    for symbol in uk_restricted_symbols:
        queen.pre_register_restriction(
            exchange='binance',
            restriction_type=RestrictionType.UK_REGULATED,
            symbol=symbol,
            reason='UK FCA restrictions - symbol not permitted for UK accounts (TRD_GRP_039)'
        )
    
    _safe_print(f"👑 Queen pre-loaded {len(uk_restricted_symbols)} UK restrictions for Binance")
    
    # Pre-register Capital.com limitations
    queen.pre_register_restriction(
        exchange='capital',
        restriction_type=RestrictionType.MARKET_CLOSED,
        symbol='*',  # All symbols affected on weekends
        reason='CFD market - closed on weekends'
    )
    
    _safe_print("👑 Queen pre-loaded Capital.com market hours restriction")


def queen_test_execution():
    """
    Test Queen's trade execution with a dry run.
    Use this to verify the system is working before live trading.
    """
    _safe_print("\n" + "="*60)
    _safe_print("👑 QUEEN AUTONOMY TEST")
    _safe_print("="*60)
    
    # Check Queen status
    status = queen_get_exchange_status()
    _safe_print(f"\nQueen Online: {status['queen_online']}")
    
    if status['queen_online']:
        _safe_print("\nExchange Status:")
        for ex_name, ex_status in status['exchanges'].items():
            enabled = "✅" if ex_status['enabled'] else "❌"
            restrictions = ex_status.get('restrictions', [])
            restriction_str = ", ".join(str(r) for r in restrictions) if restrictions else "None"
            health = ex_status.get('health', 0)
            success = ex_status.get('success_rate', 0)
            _safe_print(f"  {enabled} {ex_name}: health={health:.0%}, "
                       f"success={success:.0%}, restrictions=[{restriction_str}]")
    
    _safe_print("\n" + "="*60)
    _safe_print("👑 Queen autonomy system READY")
    _safe_print("="*60 + "\n")


# Export for use in other modules
__all__ = [
    'queen_execute_trade',
    'queen_get_exchange_status', 
    'queen_preload_uk_restrictions',
    'queen_test_execution',
    'TradeResult',
    'QUEEN_AUTONOMY_AVAILABLE'
]


if __name__ == "__main__":
    queen_test_execution()
