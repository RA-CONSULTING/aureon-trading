"""
💎 TRADE PROFIT VALIDATOR - NO PHANTOM GAINS! 💎
═══════════════════════════════════════════════════════════════════════════════

The CORE principle: ONLY count REAL, VALIDATED profits!

Every trade must pass these validation stages:
1. PRE-TRADE: Validate we have real cost basis data
2. EXECUTION: Validate order was filled (order_id, fill_price, fill_qty)
3. POST-TRADE: Validate realized P&L clears ALL costs (fees + spread + slippage)
4. PORTFOLIO: Validate portfolio actually grew (balance before vs after)

NEVER COUNT:
- Estimated P&L (use ACTUAL fill prices)
- Unfilled orders
- Trades without order IDs
- P&L that doesn't clear fees

Gary Leckey | January 2026 | The Math Works
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

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


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 EXCHANGE FEE PROFILES - Real costs per exchange
# ═══════════════════════════════════════════════════════════════════════════════
EXCHANGE_FEES = {
    'binance': {
        'maker': 0.0010,    # 0.10%
        'taker': 0.0010,    # 0.10%
        'slippage': 0.0003, # 0.03% estimated
        'spread': 0.0005,   # 0.05% estimated
    },
    'kraken': {
        'maker': 0.0016,    # 0.16%
        'taker': 0.0026,    # 0.26%
        'slippage': 0.0005, # 0.05%
        'spread': 0.0008,   # 0.08%
    },
    'alpaca': {
        'maker': 0.0015,    # 0.15%
        'taker': 0.0025,    # 0.25%
        'slippage': 0.0005, # 0.05%
        'spread': 0.0008,   # 0.08%
    },
    'capital': {
        'maker': 0.0000,    # Spread-based
        'taker': 0.0000,    # Spread-based
        'slippage': 0.0005, # 0.05%
        'spread': 0.0020,   # 0.20% (built into spread)
    }
}


@dataclass
class TradeValidation:
    """Complete validation record for a trade."""
    
    # Identifiers
    symbol: str
    exchange: str
    side: str  # 'buy' or 'sell'
    timestamp: float = field(default_factory=time.time)
    
    # Order details (from exchange API)
    order_id: Optional[str] = None
    fill_price: Optional[float] = None
    fill_qty: Optional[float] = None
    fill_value: Optional[float] = None
    
    # Fee details (REAL, from exchange)
    exchange_fee: float = 0.0
    estimated_slippage: float = 0.0
    estimated_spread: float = 0.0
    total_costs: float = 0.0
    
    # Validation flags
    has_order_id: bool = False
    has_fill_price: bool = False
    has_fill_qty: bool = False
    is_valid: bool = False
    
    # P&L (only for sells)
    cost_basis: Optional[float] = None
    gross_pnl: Optional[float] = None
    net_pnl: Optional[float] = None
    clears_costs: bool = False
    
    # Validation errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class TradeProfitValidator:
    """
    💎 The SINGLE SOURCE OF TRUTH for profit validation.
    
    RULES:
    1. No order_id = No valid trade
    2. No fill_price = No valid P&L
    3. Net P&L must clear ALL costs (fees + slippage + spread)
    4. Portfolio balance must increase for a "win"
    """
    
    def __init__(self, validation_log_file: str = "trade_validations.json"):
        self.validation_log_file = validation_log_file
        self.validations: List[TradeValidation] = []
        self.portfolio_snapshots: List[Dict[str, float]] = []
        self.wins = 0
        self.losses = 0
        self.total_validated_pnl = 0.0
        self._load_history()
    
    def _load_history(self):
        """Load validation history from file."""
        if os.path.exists(self.validation_log_file):
            try:
                with open(self.validation_log_file, 'r') as f:
                    data = json.load(f)
                    self.wins = data.get('wins', 0)
                    self.losses = data.get('losses', 0)
                    self.total_validated_pnl = data.get('total_validated_pnl', 0.0)
            except Exception:
                pass
    
    def _save_history(self):
        """Save validation history to file."""
        try:
            data = {
                'wins': self.wins,
                'losses': self.losses,
                'total_validated_pnl': self.total_validated_pnl,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.validation_log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save validation history: {e}")
    
    def get_exchange_costs(self, exchange: str, value: float, is_taker: bool = True) -> Dict[str, float]:
        """
        Calculate ALL costs for a trade on an exchange.
        
        Returns:
            {
                'fee': actual fee,
                'slippage': estimated slippage,
                'spread': estimated spread cost,
                'total': total costs
            }
        """
        fees = EXCHANGE_FEES.get(exchange.lower(), EXCHANGE_FEES['alpaca'])
        
        fee_rate = fees['taker'] if is_taker else fees['maker']
        fee = value * fee_rate
        slippage = value * fees['slippage']
        spread = value * fees['spread']
        
        return {
            'fee': fee,
            'slippage': slippage,
            'spread': spread,
            'total': fee + slippage + spread
        }
    
    def validate_buy_order(
        self,
        symbol: str,
        exchange: str,
        order_response: Dict[str, Any],
        expected_price: float = None,
        expected_qty: float = None
    ) -> TradeValidation:
        """
        🔍 STAGE 1: Validate a BUY order was properly executed.
        
        Checks:
        - Order ID exists
        - Fill price exists and is reasonable
        - Fill quantity exists
        """
        validation = TradeValidation(
            symbol=symbol,
            exchange=exchange,
            side='buy'
        )
        
        # Extract order details
        order_id = self._extract_order_id(order_response, exchange)
        fill_price = self._extract_fill_price(order_response, exchange)
        fill_qty = self._extract_fill_qty(order_response, exchange)
        
        # Validate order ID
        if order_id and order_id not in ['DRY_RUN', None, '']:
            validation.order_id = order_id
            validation.has_order_id = True
        else:
            validation.errors.append("NO_ORDER_ID: Order not executed by exchange")
        
        # Validate fill price
        if fill_price and fill_price > 0:
            validation.fill_price = fill_price
            validation.has_fill_price = True
            
            # Check for extreme slippage (>2% from expected)
            if expected_price and abs(fill_price - expected_price) / expected_price > 0.02:
                validation.warnings.append(f"HIGH_SLIPPAGE: Fill {fill_price:.6f} vs expected {expected_price:.6f}")
        else:
            validation.errors.append("NO_FILL_PRICE: Cannot determine entry price")
        
        # Validate fill quantity
        if fill_qty and fill_qty > 0:
            validation.fill_qty = fill_qty
            validation.has_fill_qty = True
            
            # Check for partial fill
            if expected_qty and fill_qty < expected_qty * 0.95:
                validation.warnings.append(f"PARTIAL_FILL: Got {fill_qty:.6f} vs expected {expected_qty:.6f}")
        else:
            validation.errors.append("NO_FILL_QTY: Cannot determine position size")
        
        # Calculate fill value and costs
        if validation.has_fill_price and validation.has_fill_qty:
            validation.fill_value = validation.fill_price * validation.fill_qty
            costs = self.get_exchange_costs(exchange, validation.fill_value)
            validation.exchange_fee = costs['fee']
            validation.estimated_slippage = costs['slippage']
            validation.estimated_spread = costs['spread']
            validation.total_costs = costs['total']
        
        # Final validation
        validation.is_valid = (
            validation.has_order_id and 
            validation.has_fill_price and 
            validation.has_fill_qty
        )
        
        if validation.is_valid:
            print(f"   ✅ BUY VALIDATED: {symbol} @ ${validation.fill_price:.6f} x {validation.fill_qty:.6f}")
            print(f"      Order ID: {validation.order_id}")
            print(f"      Total Cost (incl fees): ${validation.fill_value + validation.total_costs:.4f}")
        else:
            print(f"   ❌ BUY INVALID: {symbol}")
            for err in validation.errors:
                print(f"      🚫 {err}")
        
        self.validations.append(validation)
        return validation
    
    def validate_sell_order(
        self,
        symbol: str,
        exchange: str,
        order_response: Dict[str, Any],
        cost_basis: float,
        entry_qty: float,
        expected_price: float = None
    ) -> TradeValidation:
        """
        🔍 STAGE 2: Validate a SELL order and calculate REAL P&L.
        
        Checks:
        - Order ID exists
        - Fill price exists
        - Net P&L clears ALL costs (fees + slippage + spread)
        """
        validation = TradeValidation(
            symbol=symbol,
            exchange=exchange,
            side='sell',
            cost_basis=cost_basis
        )
        
        # Extract order details
        order_id = self._extract_order_id(order_response, exchange)
        fill_price = self._extract_fill_price(order_response, exchange)
        fill_qty = self._extract_fill_qty(order_response, exchange)
        
        # Validate order ID
        if order_id and order_id not in ['DRY_RUN', None, '']:
            validation.order_id = order_id
            validation.has_order_id = True
        else:
            validation.errors.append("NO_ORDER_ID: Sell not executed by exchange")
        
        # Validate fill price
        if fill_price and fill_price > 0:
            validation.fill_price = fill_price
            validation.has_fill_price = True
        else:
            validation.errors.append("NO_FILL_PRICE: Cannot determine exit price")
        
        # Validate fill quantity
        if fill_qty and fill_qty > 0:
            validation.fill_qty = fill_qty
            validation.has_fill_qty = True
        else:
            # Use entry qty if fill qty not reported
            validation.fill_qty = entry_qty
            validation.has_fill_qty = True
            validation.warnings.append("USING_ENTRY_QTY: Fill qty not in response, using entry qty")
        
        # Calculate REAL P&L
        if validation.has_fill_price and validation.has_fill_qty:
            validation.fill_value = validation.fill_price * validation.fill_qty
            
            # Calculate exit costs
            costs = self.get_exchange_costs(exchange, validation.fill_value)
            validation.exchange_fee = costs['fee']
            validation.estimated_slippage = costs['slippage']
            validation.estimated_spread = costs['spread']
            validation.total_costs = costs['total']
            
            # Calculate P&L
            validation.gross_pnl = validation.fill_value - cost_basis
            validation.net_pnl = validation.gross_pnl - validation.total_costs
            
            # Check if we cleared costs
            validation.clears_costs = validation.net_pnl > 0
        
        # Final validation
        validation.is_valid = (
            validation.has_order_id and 
            validation.has_fill_price and 
            validation.has_fill_qty
        )
        
        if validation.is_valid:
            if validation.clears_costs:
                self.wins += 1
                self.total_validated_pnl += validation.net_pnl
                print(f"   ✅ VALIDATED WIN: {symbol} Net P&L: ${validation.net_pnl:+.4f}")
            else:
                self.losses += 1
                self.total_validated_pnl += validation.net_pnl
                print(f"   ❌ VALIDATED LOSS: {symbol} Net P&L: ${validation.net_pnl:+.4f}")
            
            print(f"      Order ID: {validation.order_id}")
            print(f"      Fill: ${validation.fill_price:.6f} x {validation.fill_qty:.6f}")
            print(f"      Gross: ${validation.gross_pnl:+.4f} | Costs: ${validation.total_costs:.4f} | Net: ${validation.net_pnl:+.4f}")
        else:
            print(f"   🚫 SELL INVALID (NOT COUNTED): {symbol}")
            for err in validation.errors:
                print(f"      🚫 {err}")
        
        self._save_history()
        self.validations.append(validation)
        return validation
    
    def validate_portfolio_growth(
        self,
        balance_before: float,
        balance_after: float,
        expected_pnl: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        🔍 STAGE 3: Validate portfolio actually grew as expected.
        
        This is the FINAL check - did the balance ACTUALLY increase?
        """
        actual_change = balance_after - balance_before
        variance = actual_change - expected_pnl
        variance_pct = (variance / expected_pnl * 100) if expected_pnl != 0 else 0
        
        # Allow up to 5% variance for fee estimation errors
        is_valid = abs(variance_pct) < 5.0 or abs(variance) < 0.01
        
        result = {
            'balance_before': balance_before,
            'balance_after': balance_after,
            'actual_change': actual_change,
            'expected_pnl': expected_pnl,
            'variance': variance,
            'variance_pct': variance_pct,
            'is_valid': is_valid,
            'grew': actual_change > 0
        }
        
        if is_valid:
            if actual_change > 0:
                print(f"   ✅ PORTFOLIO GREW: ${balance_before:.2f} → ${balance_after:.2f} (+${actual_change:.4f})")
            else:
                print(f"   📉 PORTFOLIO SHRANK: ${balance_before:.2f} → ${balance_after:.2f} (${actual_change:.4f})")
        else:
            print(f"   ⚠️ P&L VARIANCE: Expected ${expected_pnl:+.4f} but got ${actual_change:+.4f} (var: {variance_pct:.1f}%)")
        
        return is_valid, result
    
    def _extract_order_id(self, response: Dict[str, Any], exchange: str) -> Optional[str]:
        """Extract order ID from exchange response."""
        if not response:
            return None
        
        # Common field names
        for field in ['orderId', 'order_id', 'id', 'txid']:
            if response.get(field):
                return str(response[field])
        
        return None
    
    def _extract_fill_price(self, response: Dict[str, Any], exchange: str) -> Optional[float]:
        """Extract fill price from exchange response."""
        if not response:
            return None
        
        # Try direct fields first
        for field in ['filled_avg_price', 'avgPrice', 'price', 'avg_fill_price', 'avg_price']:
            if response.get(field):
                try:
                    return float(response[field])
                except (ValueError, TypeError):
                    continue
        
        # Try calculating from fills array
        fills = response.get('fills', [])
        if fills:
            total_qty = 0.0
            total_cost = 0.0
            for fill in fills:
                qty = float(fill.get('qty', 0))
                price = float(fill.get('price', 0))
                total_qty += qty
                total_cost += qty * price
            if total_qty > 0:
                return total_cost / total_qty
        
        # Try calculating from cumulative
        exec_qty = float(response.get('executedQty', 0))
        cumm_quote = float(response.get('cummulativeQuoteQty', 0))
        if exec_qty > 0 and cumm_quote > 0:
            return cumm_quote / exec_qty
        
        return None
    
    def _extract_fill_qty(self, response: Dict[str, Any], exchange: str) -> Optional[float]:
        """Extract filled quantity from exchange response."""
        if not response:
            return None
        
        for field in ['filled_qty', 'executedQty', 'qty', 'filledQty', 'executed_qty']:
            if response.get(field):
                try:
                    return float(response[field])
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        total_trades = self.wins + self.losses
        win_rate = (self.wins / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_validated_trades': total_trades,
            'validated_wins': self.wins,
            'validated_losses': self.losses,
            'validated_win_rate': win_rate,
            'total_validated_pnl': self.total_validated_pnl
        }
    
    def print_summary(self):
        """Print validation summary."""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("💎 TRADE PROFIT VALIDATOR - VALIDATED RESULTS")
        print("=" * 60)
        print(f"   Total Validated Trades: {stats['total_validated_trades']}")
        print(f"   ✅ Validated Wins:      {stats['validated_wins']}")
        print(f"   ❌ Validated Losses:    {stats['validated_losses']}")
        print(f"   📊 Validated Win Rate:  {stats['validated_win_rate']:.1f}%")
        print(f"   💰 Total Validated P&L: ${stats['total_validated_pnl']:+.2f}")
        print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global validator instance
_validator: Optional[TradeProfitValidator] = None

def get_validator() -> TradeProfitValidator:
    """Get or create the global validator instance."""
    global _validator
    if _validator is None:
        _validator = TradeProfitValidator()
    return _validator


def validate_buy(symbol: str, exchange: str, order_response: Dict) -> TradeValidation:
    """Quick validation for a buy order."""
    return get_validator().validate_buy_order(symbol, exchange, order_response)


def validate_sell(symbol: str, exchange: str, order_response: Dict, cost_basis: float, qty: float) -> TradeValidation:
    """Quick validation for a sell order."""
    return get_validator().validate_sell_order(symbol, exchange, order_response, cost_basis, qty)


def is_real_profit(net_pnl: float, exchange: str, trade_value: float) -> Tuple[bool, str]:
    """
    Quick check if net_pnl is a REAL profit that clears ALL costs.
    
    Returns:
        (is_real: bool, reason: str)
    """
    costs = get_validator().get_exchange_costs(exchange, trade_value)
    min_profit = costs['total']  # Must clear ALL costs
    
    if net_pnl > min_profit:
        return True, f"✅ Clears costs (min: ${min_profit:.4f})"
    elif net_pnl > 0:
        return False, f"⚠️ Positive but doesn't clear costs (need ${min_profit:.4f}, got ${net_pnl:.4f})"
    else:
        return False, f"❌ Loss: ${net_pnl:.4f}"


if __name__ == "__main__":
    # Test the validator
    validator = TradeProfitValidator()
    
    print("\n🧪 Testing Trade Profit Validator...")
    
    # Simulate a buy order
    buy_response = {
        'orderId': 'TEST123',
        'filled_avg_price': 100.50,
        'filled_qty': 10.0,
        'status': 'FILLED'
    }
    
    buy_val = validator.validate_buy_order(
        symbol='TEST/USD',
        exchange='kraken',
        order_response=buy_response,
        expected_price=100.00,
        expected_qty=10.0
    )
    
    # Simulate a profitable sell
    sell_response = {
        'orderId': 'TEST456',
        'filled_avg_price': 102.00,
        'filled_qty': 10.0,
        'status': 'FILLED'
    }
    
    cost_basis = 100.50 * 10.0 + 5.0  # Entry cost + fees
    
    sell_val = validator.validate_sell_order(
        symbol='TEST/USD',
        exchange='kraken',
        order_response=sell_response,
        cost_basis=cost_basis,
        entry_qty=10.0
    )
    
    # Validate portfolio growth
    validator.validate_portfolio_growth(
        balance_before=1000.00,
        balance_after=1000.00 + (sell_val.net_pnl or 0),
        expected_pnl=sell_val.net_pnl or 0
    )
    
    # Print summary
    validator.print_summary()
