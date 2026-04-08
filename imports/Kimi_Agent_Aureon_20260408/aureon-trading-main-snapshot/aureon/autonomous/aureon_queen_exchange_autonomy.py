#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                       ║
║     👑🌍 QUEEN EXCHANGE AUTONOMY SYSTEM 🌍👑                                          ║
║                                                                                       ║
║     The Queen has FULL AUTONOMY over exchange routing and restriction handling.       ║
║     She learns from failures and NEVER repeats the same mistake.                      ║
║                                                                                       ║
║     🇬🇧 UK RESTRICTIONS? Route to Kraken/Alpaca instead.                              ║
║     🔒 API Key Limited? Use alternative paths.                                        ║
║     ⏰ Market Closed? Queue for next open window.                                     ║
║                                                                                       ║
║     THE QUEEN ADAPTS. THE QUEEN LEARNS. THE QUEEN WINS.                               ║
║                                                                                       ║
║     Gary Leckey & Tina Brown | January 2026 | Queen's Full Autonomy                   ║
║                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum, auto

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# EXCHANGE RESTRICTION TYPES
# ═══════════════════════════════════════════════════════════════════════════

class RestrictionType(Enum):
    """Types of exchange restrictions the Queen can detect and handle."""
    UK_REGULATED = auto()           # 🇬🇧 FCA restrictions (Binance UK)
    API_KEY_LIMITED = auto()        # 🔑 API key has restricted permissions
    SYMBOL_NOT_PERMITTED = auto()   # 🚫 Specific symbol not tradeable
    INSUFFICIENT_FUNDS = auto()     # 💰 Not enough balance
    MARKET_CLOSED = auto()          # ⏰ Market hours restriction
    RATE_LIMITED = auto()           # ⏱️ Too many requests
    MIN_NOTIONAL = auto()           # 📉 Below minimum order value
    MIN_QUANTITY = auto()           # 📊 Below minimum order quantity
    CANCEL_ONLY = auto()            # 🛑 Market in cancel-only mode (delisting)
    IP_RESTRICTED = auto()          # 🌐 IP not whitelisted
    MAINTENANCE = auto()            # 🔧 Exchange under maintenance
    UNKNOWN = auto()                # ❓ Unknown restriction


@dataclass
class ExchangeRestriction:
    """Record of a detected exchange restriction."""
    exchange: str
    restriction_type: RestrictionType
    symbol: Optional[str] = None
    error_message: str = ""
    detected_at: float = field(default_factory=time.time)
    expiry_at: Optional[float] = None  # When this restriction should be rechecked
    permanent: bool = False  # Is this a permanent restriction?
    
    def is_expired(self) -> bool:
        if self.permanent:
            return False
        if self.expiry_at is None:
            return False
        return time.time() > self.expiry_at
    
    def to_dict(self) -> Dict:
        return {
            'exchange': self.exchange,
            'restriction_type': self.restriction_type.name,
            'symbol': self.symbol,
            'error_message': self.error_message,
            'detected_at': self.detected_at,
            'expiry_at': self.expiry_at,
            'permanent': self.permanent
        }


@dataclass
class ExchangeCapability:
    """What each exchange CAN do (Queen's knowledge)."""
    exchange: str
    supports_crypto: bool = True
    supports_stocks: bool = False
    supports_cfd: bool = False
    supports_forex: bool = False
    supports_fractional: bool = False
    min_order_usd: float = 5.0
    uk_compliant: bool = True
    api_connected: bool = False
    last_successful_trade: Optional[float] = None
    total_trades: int = 0
    failed_trades: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.total_trades - self.failed_trades) / self.total_trades
    
    @property
    def is_healthy(self) -> bool:
        """Is this exchange healthy enough to use?"""
        if not self.api_connected:
            return False
        if self.success_rate < 0.5 and self.total_trades > 5:
            return False
        return True


# ═══════════════════════════════════════════════════════════════════════════
# QUEEN'S EXCHANGE AUTONOMY BRAIN
# ═══════════════════════════════════════════════════════════════════════════

class QueenExchangeAutonomy:
    """
    👑 The Queen's Full Exchange Autonomy System 👑
    
    She has complete control over:
    - Which exchange to use for each trade
    - How to route around restrictions
    - Learning from failures
    - Never repeating mistakes
    """
    
    # 🇬🇧 UK RESTRICTED TOKENS (Binance FCA compliance)
    UK_RESTRICTED_TOKENS: Set[str] = {
        # Leveraged tokens (banned for UK retail)
        "BTCDOWN", "BTCUP", "ETHDOWN", "ETHUP", "BNBDOWN", "BNBUP",
        "XRPDOWN", "XRPUP", "DOTDOWN", "DOTUP", "EOSDOWN", "EOSUP",
        "TRXDOWN", "TRXUP", "LINKDOWN", "LINKUP", "ADAUP", "ADADOWN",
        # Stock tokens (delisted for UK)
        "TSLA", "COIN", "AAPL", "MSFT", "GOOGL", "AMZN", "MSTR",
        # Deprecated stablecoins
        "BUSD",
    }
    
    # Known API permission groups that have restrictions
    RESTRICTED_API_GROUPS: Set[str] = {
        "TRD_GRP_039",  # Limited trading group (Binance UK)
    }
    
    def __init__(self, state_file: str = "queen_exchange_autonomy.json"):
        self.state_file = Path(state_file)
        
        # Exchange capabilities (Queen's knowledge)
        self.capabilities: Dict[str, ExchangeCapability] = {
            'kraken': ExchangeCapability(
                exchange='kraken',
                supports_crypto=True,
                supports_stocks=False,
                supports_cfd=False,
                supports_forex=False,
                supports_fractional=False,
                min_order_usd=5.0,
                uk_compliant=True,
            ),
            'binance': ExchangeCapability(
                exchange='binance',
                supports_crypto=True,
                supports_stocks=False,
                supports_cfd=False,
                supports_forex=False,
                supports_fractional=False,
                min_order_usd=5.0,
                uk_compliant=False,  # 🇬🇧 Has UK restrictions!
            ),
            'alpaca': ExchangeCapability(
                exchange='alpaca',
                supports_crypto=True,
                supports_stocks=True,
                supports_cfd=False,
                supports_forex=False,
                supports_fractional=True,
                min_order_usd=1.0,
                uk_compliant=True,
            ),
            'capital': ExchangeCapability(
                exchange='capital',
                supports_crypto=False,  # CFDs only, not direct crypto
                supports_stocks=True,
                supports_cfd=True,
                supports_forex=True,
                supports_fractional=True,
                min_order_usd=0.0,
                uk_compliant=True,
            ),
        }
        
        # Alias for compatibility
        self.exchange_capabilities = self.capabilities
        
        # Active restrictions (learned from failures)
        self.restrictions: List[ExchangeRestriction] = []
        
        # Blocked symbol-exchange pairs (permanent bans from failures)
        self.blocked_pairs: Set[Tuple[str, str]] = set()  # (symbol, exchange)
        
        # Exchange priority order (Queen decides)
        self.exchange_priority: List[str] = ['kraken', 'alpaca', 'binance', 'capital']
        
        # Load saved state
        self._load_state()
        
        logger.info("👑 Queen Exchange Autonomy System initialized")
        logger.info(f"   Restrictions loaded: {len(self.restrictions)}")
        logger.info(f"   Blocked pairs: {len(self.blocked_pairs)}")
    
    def _load_state(self):
        """Load saved autonomy state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                # Load blocked pairs
                self.blocked_pairs = set(
                    tuple(p) for p in data.get('blocked_pairs', [])
                )
                
                # Load restrictions
                for r in data.get('restrictions', []):
                    try:
                        restriction = ExchangeRestriction(
                            exchange=r['exchange'],
                            restriction_type=RestrictionType[r['restriction_type']],
                            symbol=r.get('symbol'),
                            error_message=r.get('error_message', ''),
                            detected_at=r.get('detected_at', time.time()),
                            expiry_at=r.get('expiry_at'),
                            permanent=r.get('permanent', False)
                        )
                        if not restriction.is_expired():
                            self.restrictions.append(restriction)
                    except Exception:
                        continue
                
                # Load exchange stats
                for ex_name, stats in data.get('exchange_stats', {}).items():
                    if ex_name in self.capabilities:
                        cap = self.capabilities[ex_name]
                        cap.api_connected = stats.get('api_connected', False)
                        cap.total_trades = stats.get('total_trades', 0)
                        cap.failed_trades = stats.get('failed_trades', 0)
                        cap.last_successful_trade = stats.get('last_successful_trade')
                
            except Exception as e:
                logger.warning(f"Could not load autonomy state: {e}")
    
    def _save_state(self):
        """Save autonomy state for persistence."""
        try:
            # Clean expired restrictions
            self.restrictions = [r for r in self.restrictions if not r.is_expired()]
            
            data = {
                'blocked_pairs': list(self.blocked_pairs),
                'restrictions': [r.to_dict() for r in self.restrictions],
                'exchange_stats': {
                    name: {
                        'api_connected': cap.api_connected,
                        'total_trades': cap.total_trades,
                        'failed_trades': cap.failed_trades,
                        'last_successful_trade': cap.last_successful_trade,
                        'success_rate': cap.success_rate,
                    }
                    for name, cap in self.capabilities.items()
                },
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save autonomy state: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # ERROR DETECTION & LEARNING
    # ═══════════════════════════════════════════════════════════════════════
    
    def detect_restriction_from_error(self, exchange: str, error: str, symbol: Optional[str] = None) -> Optional[ExchangeRestriction]:
        """
        👑 The Queen analyzes errors and learns what restrictions exist.
        
        She NEVER makes the same mistake twice.
        """
        error_lower = error.lower()
        
        # Detect restriction type from error message
        restriction_type = RestrictionType.UNKNOWN
        permanent = False
        expiry_hours = 1  # Default: retry in 1 hour
        
        # 🇬🇧 UK / FCA Restrictions
        if 'not permitted for this account' in error_lower:
            restriction_type = RestrictionType.API_KEY_LIMITED
            permanent = True  # Needs API key regeneration
            logger.warning(f"👑 Queen detected: {exchange} API key has restricted permissions (TRD_GRP_039)")
        
        elif 'uk' in error_lower and 'restrict' in error_lower:
            restriction_type = RestrictionType.UK_REGULATED
            permanent = True
            
        # 💰 Insufficient Funds
        elif 'insufficient' in error_lower and ('fund' in error_lower or 'balance' in error_lower):
            restriction_type = RestrictionType.INSUFFICIENT_FUNDS
            expiry_hours = 24  # Retry tomorrow
            
        # 📉 Minimum Notional
        elif 'minnotional' in error_lower or 'min_notional' in error_lower:
            restriction_type = RestrictionType.MIN_NOTIONAL
            permanent = True  # Symbol always has this limit
            
        # 📊 Minimum Quantity
        elif 'volume_minimum' in error_lower or 'ordermin' in error_lower or 'min qty' in error_lower:
            restriction_type = RestrictionType.MIN_QUANTITY
            permanent = True
            
        # ⏰ Market Closed
        elif 'closed' in error_lower or 'market hours' in error_lower or 'timetable' in error_lower:
            restriction_type = RestrictionType.MARKET_CLOSED
            expiry_hours = 12  # Markets reopen
            
        # 🛑 Cancel Only Mode (delisting)
        elif 'cancel_only' in error_lower or 'cancel only' in error_lower:
            restriction_type = RestrictionType.CANCEL_ONLY
            permanent = True  # Token being delisted
            
        # ⏱️ Rate Limited
        elif 'rate' in error_lower and 'limit' in error_lower:
            restriction_type = RestrictionType.RATE_LIMITED
            expiry_hours = 0.1  # 6 minutes
            
        # 🌐 IP Restricted
        elif 'ip' in error_lower and ('restrict' in error_lower or 'whitelist' in error_lower):
            restriction_type = RestrictionType.IP_RESTRICTED
            permanent = True
            
        # 🔧 Maintenance
        elif 'maintenance' in error_lower or 'service' in error_lower and 'unavailable' in error_lower:
            restriction_type = RestrictionType.MAINTENANCE
            expiry_hours = 2
        
        if restriction_type == RestrictionType.UNKNOWN:
            return None
        
        # Create restriction record
        restriction = ExchangeRestriction(
            exchange=exchange,
            restriction_type=restriction_type,
            symbol=symbol,
            error_message=error[:200],
            permanent=permanent,
            expiry_at=None if permanent else time.time() + (expiry_hours * 3600)
        )
        
        # Add to restrictions list
        self.restrictions.append(restriction)
        
        # Block symbol-exchange pair if permanent
        if permanent and symbol:
            self.blocked_pairs.add((symbol, exchange))
            logger.info(f"👑 Queen BLOCKED: {symbol} on {exchange} (permanent)")
        
        # Update exchange stats
        if exchange in self.capabilities:
            self.capabilities[exchange].failed_trades += 1
        
        # Save state
        self._save_state()
        
        return restriction
    
    def record_success(self, exchange: str, symbol: str, side: str = None, quantity: float = None, quote_amount_usd: float = None):
        """Record a successful trade - Queen learns what WORKS."""
        if exchange in self.capabilities:
            cap = self.capabilities[exchange]
            cap.total_trades += 1
            cap.last_successful_trade = time.time()
            cap.api_connected = True
            self._save_state()
    
    def record_failure(self, exchange: str, symbol: str, error: str):
        """Record a failed trade - Queen learns and adapts."""
        if exchange in self.capabilities:
            self.capabilities[exchange].total_trades += 1
        
        # Detect and record the restriction
        self.detect_restriction_from_error(exchange, error, symbol)
    
    def get_restrictions(self, exchange: str) -> List[ExchangeRestriction]:
        """Get all active restrictions for an exchange."""
        return [r for r in self.restrictions 
                if r.exchange == exchange and not r.is_expired()]
    
    def pre_register_restriction(
        self,
        exchange: str,
        restriction_type: RestrictionType,
        symbol: str = None,
        reason: str = ""
    ):
        """
        👑 Pre-register a KNOWN restriction so the Queen doesn't have to learn it the hard way.
        
        Use this at startup to load known restrictions like UK regulations.
        """
        # Check if restriction already exists
        for r in self.restrictions:
            if (r.exchange == exchange and 
                r.restriction_type == restriction_type and
                r.symbol == symbol):
                return  # Already registered
        
        # Create new restriction
        restriction = ExchangeRestriction(
            exchange=exchange,
            restriction_type=restriction_type,
            symbol=symbol,
            error_message=reason,
            permanent=True,  # Pre-registered restrictions are permanent
            expiry_at=None
        )
        
        self.restrictions.append(restriction)
        
        # Block symbol-exchange pair if symbol-specific
        if symbol and symbol != '*':
            self.blocked_pairs.add((symbol, exchange))
        
        logger.debug(f"👑 Pre-registered restriction: {exchange} {restriction_type.value} {symbol}")
        
        self._save_state()
    
    # ═══════════════════════════════════════════════════════════════════════
    # INTELLIGENT ROUTING DECISIONS
    # ═══════════════════════════════════════════════════════════════════════
    
    def is_symbol_blocked(self, symbol: str, exchange: str) -> bool:
        """Check if a symbol-exchange pair is blocked."""
        return (symbol, exchange) in self.blocked_pairs
    
    def is_exchange_restricted(self, exchange: str, restriction_type: Optional[RestrictionType] = None) -> bool:
        """Check if an exchange has active restrictions."""
        for r in self.restrictions:
            if r.exchange == exchange and not r.is_expired():
                if restriction_type is None or r.restriction_type == restriction_type:
                    return True
        return False
    
    def get_best_exchange_for_trade(
        self,
        symbol: str,
        side: str,
        asset_type: str = 'crypto',
        required_amount_usd: float = 10.0
    ) -> Optional[str]:
        """
        👑 The Queen decides the BEST exchange for this trade.
        
        She considers:
        - Known restrictions
        - Past failures
        - Exchange capabilities
        - Asset type requirements
        """
        candidates = []
        
        for exchange in self.exchange_priority:
            cap = self.capabilities.get(exchange)
            if not cap:
                continue
            
            # Check basic capability
            if asset_type == 'crypto' and not cap.supports_crypto:
                continue
            if asset_type == 'stock' and not cap.supports_stocks:
                continue
            if asset_type == 'cfd' and not cap.supports_cfd:
                continue
            
            # Check if symbol is blocked on this exchange
            if self.is_symbol_blocked(symbol, exchange):
                logger.debug(f"👑 Skipping {exchange} for {symbol}: blocked pair")
                continue
            
            # Check for active restrictions
            if self.is_exchange_restricted(exchange, RestrictionType.API_KEY_LIMITED):
                logger.debug(f"👑 Skipping {exchange}: API key limited")
                continue
            
            if self.is_exchange_restricted(exchange, RestrictionType.MAINTENANCE):
                logger.debug(f"👑 Skipping {exchange}: under maintenance")
                continue
            
            # Check minimum order
            if required_amount_usd < cap.min_order_usd:
                logger.debug(f"👑 Skipping {exchange}: min order ${cap.min_order_usd}")
                continue
            
            # Check UK compliance
            if not cap.uk_compliant and self._is_uk_restricted_symbol(symbol):
                logger.debug(f"👑 Skipping {exchange} for {symbol}: UK restricted")
                continue
            
            # Score this exchange
            score = 100  # Base score
            
            # Prefer healthy exchanges
            if cap.is_healthy:
                score += 50
            
            # Prefer exchanges with recent successful trades
            if cap.last_successful_trade:
                hours_since = (time.time() - cap.last_successful_trade) / 3600
                if hours_since < 1:
                    score += 30
                elif hours_since < 24:
                    score += 10
            
            # Penalize exchanges with failures
            score -= cap.failed_trades * 5
            
            # Boost UK-compliant exchanges
            if cap.uk_compliant:
                score += 20
            
            candidates.append((exchange, score))
        
        if not candidates:
            logger.warning(f"👑 Queen: NO viable exchange found for {symbol}")
            return None
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: -x[1])
        
        best = candidates[0][0]
        logger.info(f"👑 Queen selected {best.upper()} for {symbol} (score: {candidates[0][1]})")
        
        return best
    
    def get_alternative_exchanges(self, failed_exchange: str, symbol: str) -> List[str]:
        """
        👑 When one exchange fails, the Queen finds alternatives.
        
        NEVER give up - always find another way!
        """
        alternatives = []
        
        for exchange in self.exchange_priority:
            if exchange == failed_exchange:
                continue
            
            cap = self.capabilities.get(exchange)
            if not cap or not cap.supports_crypto:
                continue
            
            if self.is_symbol_blocked(symbol, exchange):
                continue
            
            if self.is_exchange_restricted(exchange, RestrictionType.API_KEY_LIMITED):
                continue
            
            alternatives.append(exchange)
        
        logger.info(f"👑 Queen alternatives for {symbol} (not {failed_exchange}): {alternatives}")
        return alternatives
    
    def _is_uk_restricted_symbol(self, symbol: str) -> bool:
        """Check if symbol is UK restricted."""
        symbol_upper = symbol.upper()
        for token in self.UK_RESTRICTED_TOKENS:
            if token in symbol_upper:
                return True
        return False
    
    # ═══════════════════════════════════════════════════════════════════════
    # AUTONOMOUS ROUTING (FULL QUEEN CONTROL)
    # ═══════════════════════════════════════════════════════════════════════
    
    def route_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        quote_amount_usd: float,
        preferred_exchange: Optional[str] = None,
        available_exchanges: List[str] = None
    ) -> Dict[str, Any]:
        """
        👑 THE QUEEN ROUTES THE TRADE.
        
        She has FULL AUTONOMY to:
        1. Choose the best exchange
        2. Route around failures
        3. Try alternatives if first choice fails
        
        Returns routing decision with exchange and reasoning.
        """
        routing = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'quote_amount_usd': quote_amount_usd,
            'selected_exchange': None,
            'alternatives': [],
            'reason': '',  # Single reason for executor
            'reasoning': [],
            'restrictions_detected': [],
            'queen_approved': False
        }
        
        # Filter by available exchanges if provided
        valid_exchanges = available_exchanges if available_exchanges else list(self.capabilities.keys())
        
        # Step 1: Check if preferred exchange works
        if preferred_exchange and preferred_exchange in valid_exchanges:
            if self.is_symbol_blocked(symbol, preferred_exchange):
                routing['reasoning'].append(f"❌ {preferred_exchange}: Symbol blocked (past failures)")
                routing['reason'] = f"{preferred_exchange} blocked for {symbol}"
            elif self.is_exchange_restricted(preferred_exchange, RestrictionType.API_KEY_LIMITED):
                routing['reasoning'].append(f"❌ {preferred_exchange}: API key has restricted permissions")
                routing['restrictions_detected'].append('API_KEY_LIMITED')
                routing['reason'] = f"{preferred_exchange} has API restrictions"
            else:
                routing['selected_exchange'] = preferred_exchange
                routing['reasoning'].append(f"✅ Using preferred exchange: {preferred_exchange}")
                routing['reason'] = f"Using preferred: {preferred_exchange}"
        
        # Step 2: If no preferred or preferred failed, Queen decides
        if not routing['selected_exchange']:
            # Check each exchange in priority order
            for exchange in self.exchange_priority:
                if exchange not in valid_exchanges:
                    continue
                    
                if self.is_symbol_blocked(symbol, exchange):
                    continue
                    
                if self.is_exchange_restricted(exchange, RestrictionType.API_KEY_LIMITED):
                    continue
                
                cap = self.capabilities.get(exchange)
                if cap and cap.supports_crypto:
                    routing['selected_exchange'] = exchange
                    routing['reasoning'].append(f"✅ Queen selected: {exchange}")
                    routing['reason'] = f"Queen selected {exchange}"
                    break
        
        # Step 3: Find alternatives
        if routing['selected_exchange']:
            routing['alternatives'] = [
                ex for ex in self.get_alternative_exchanges(routing['selected_exchange'], symbol)
                if ex in valid_exchanges
            ]
        
        # Step 4: Queen approval
        if routing['selected_exchange']:
            routing['queen_approved'] = True
            routing['reasoning'].append("👑 Queen APPROVED this route")
        else:
            routing['reasoning'].append("👑 Queen REJECTED - No viable exchange found")
            routing['reasoning'].append("💡 Consider: Adding funds, regenerating API keys, or waiting for markets")
            routing['reason'] = "No viable exchange found"
        
        return routing
    
    def handle_trade_failure(
        self,
        exchange: str,
        symbol: str,
        error_message: str,
        quantity: float,
        quote_amount_usd: float,
        available_exchanges: List[str] = None
    ) -> Dict[str, Any]:
        """
        👑 When a trade fails, the Queen handles it.
        
        She:
        1. Records the failure (learns)
        2. Finds an alternative exchange
        3. Returns a new routing for retry
        
        Returns dict with 'success', 'alternative_exchange', 'reason'
        """
        # Record the failure
        self.record_failure(exchange, symbol, error_message)
        
        # Detect restriction type
        restriction = self.detect_restriction_from_error(exchange, error_message, symbol)
        
        logger.warning(f"👑 Queen handling failure on {exchange}: {error_message[:100]}")
        
        if restriction:
            logger.info(f"👑 Restriction detected: {restriction.restriction_type.name}")
        
        # Find alternatives
        alternatives = self.get_alternative_exchanges(exchange, symbol)
        
        # Filter by available exchanges if provided
        if available_exchanges:
            alternatives = [a for a in alternatives if a in available_exchanges]
        
        if not alternatives:
            logger.error(f"👑 Queen: No alternatives for {symbol} after {exchange} failed")
            return {
                'success': False,
                'alternative_exchange': None,
                'reason': f"No alternatives available for {symbol}",
                'restriction_detected': restriction.restriction_type.value if restriction else None
            }
        
        best_alternative = alternatives[0]
        
        logger.info(f"👑 Queen routing from {exchange} → {best_alternative}")
        
        return {
            'success': True,
            'alternative_exchange': best_alternative,
            'reason': f"Routed to {best_alternative} after {exchange} failed",
            'restriction_detected': restriction.restriction_type.value if restriction else None,
            'all_alternatives': alternatives
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # STATUS & REPORTING
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict[str, Any]:
        """Get Queen's exchange autonomy status."""
        return {
            'active_restrictions': len([r for r in self.restrictions if not r.is_expired()]),
            'blocked_pairs': len(self.blocked_pairs),
            'exchange_health': {
                name: {
                    'healthy': cap.is_healthy,
                    'success_rate': f"{cap.success_rate * 100:.1f}%",
                    'total_trades': cap.total_trades,
                    'uk_compliant': cap.uk_compliant,
                }
                for name, cap in self.capabilities.items()
            },
            'restrictions_by_type': {},
            'blocked_exchanges': [
                ex for ex, cap in self.capabilities.items()
                if self.is_exchange_restricted(ex, RestrictionType.API_KEY_LIMITED)
            ]
        }
    
    def print_status(self):
        """Print Queen's exchange autonomy status."""
        print("\n" + "=" * 60)
        print("👑 QUEEN EXCHANGE AUTONOMY STATUS 👑")
        print("=" * 60)
        
        status = self.get_status()
        
        print(f"\n📊 Active Restrictions: {status['active_restrictions']}")
        print(f"🚫 Blocked Pairs: {status['blocked_pairs']}")
        
        print("\n🏦 Exchange Health:")
        for ex, health in status['exchange_health'].items():
            emoji = "✅" if health['healthy'] else "❌"
            uk = "🇬🇧" if health['uk_compliant'] else "⚠️"
            print(f"   {emoji} {ex.upper()}: {health['success_rate']} ({health['total_trades']} trades) {uk}")
        
        if status['blocked_exchanges']:
            print(f"\n⛔ BLOCKED EXCHANGES: {', '.join(status['blocked_exchanges'])}")
            print("   💡 These exchanges have API key restrictions - regenerate keys!")
        
        print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════

_queen_autonomy: Optional[QueenExchangeAutonomy] = None

def get_queen_autonomy() -> QueenExchangeAutonomy:
    """Get the global Queen Exchange Autonomy instance."""
    global _queen_autonomy
    if _queen_autonomy is None:
        _queen_autonomy = QueenExchangeAutonomy()
    return _queen_autonomy


# ═══════════════════════════════════════════════════════════════════════════
# MAIN - TEST
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("👑 Testing Queen Exchange Autonomy System...")
    
    queen = get_queen_autonomy()
    
    # Print current status
    queen.print_status()
    
    # Simulate detecting Binance restriction
    print("\n🔍 Simulating Binance API restriction detection...")
    queen.detect_restriction_from_error(
        'binance',
        'This symbol is not permitted for this account.',
        'BTCUSDT'
    )
    
    # Test routing
    print("\n🔄 Testing trade routing...")
    routing = queen.route_trade(
        symbol='BTC/USD',
        side='buy',
        quantity=0.001,
        quote_amount_usd=100.0,
        preferred_exchange='binance'
    )
    
    print(f"   Selected: {routing['selected_exchange']}")
    print(f"   Alternatives: {routing['alternatives']}")
    print(f"   Reasoning: {routing['reasoning']}")
    
    # Print final status
    queen.print_status()
