# ⚡ UNIFIED TRADE EXECUTOR - Execution Hub
# Stage 3: Queen → Trade Executor → Multi-Exchange Orchestration
import time
import logging
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class TradeGatingConfig:
    """Safety guardrails for trade execution"""
    min_score: float = 0.618
    min_coherence: float = 0.618
    min_lambda: float = 0.618
    max_position_pct: float = 0.05
    max_daily_trades: int = 50
    max_daily_loss_pct: float = 0.05
    allowed_exchanges: list = None
    
    def __post_init__(self):
        if self.allowed_exchanges is None:
            self.allowed_exchanges = ["kraken", "binance", "alpaca", "capital"]

@dataclass
class ExecutionRequest:
    """Standardized trade request"""
    symbol: str
    side: str
    quantity: float
    price: float
    confidence: float
    coherence: float
    lambda_val: float
    timestamp: float = None
    exchange: str = "unknown"
    source: str = "unknown"
    trace_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class ExecutionResult:
    """Execution outcome"""
    success: bool
    symbol: str
    side: str
    executed_qty: float
    executed_price: float
    pnl: float
    error: Optional[str] = None
    order_id: Optional[str] = None
    timestamp: float = None
    exchange: str = "unknown"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class UnifiedTradeExecutor:
    """Central execution hub"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.config = TradeGatingConfig()
        self.stats = {
            "requests": 0,
            "approved": 0,
            "rejected": 0,
            "pnl": 0.0,
            "confirmed_fills": 0,
            "ghost_orders": 0,
            "validation_failures": 0,
        }
        self._submitted_orders: Dict[str, Dict[str, Any]] = {}
        self._confirmation_window_s = 90
        
    def initialize(self):
        logger.info(f"⚡ Executor: {'🧪 DRY-RUN' if self.dry_run else '💰 LIVE'}")
        
    def apply_gating_rules(self, request: ExecutionRequest) -> Tuple[bool, str]:
        if request.confidence < self.config.min_score:
            return False, "Low confidence"
        if request.coherence < self.config.min_coherence:
            return False, "Low coherence"
        if request.lambda_val < self.config.min_lambda:
            return False, "Low lambda"
        if request.quantity <= 0:
            return False, "Invalid quantity"
        if request.price <= 0:
            return False, "Invalid price"
        if request.exchange and request.exchange not in self.config.allowed_exchanges:
            return False, "Exchange not allowed"
        return True, "✅"

    def _new_order_id(self, request: ExecutionRequest) -> str:
        ts = int(time.time() * 1000)
        return f"{request.exchange}:{request.symbol}:{request.side}:{ts}"

    def record_fill_confirmation(self, order_id: str, exchange: str, filled_qty: float, filled_price: float) -> bool:
        """Attach an exchange-side confirmation to an order and validate fill integrity."""
        order = self._submitted_orders.get(order_id)
        if not order:
            self.stats["validation_failures"] += 1
            return False

        if filled_qty <= 0 or filled_price <= 0:
            self.stats["validation_failures"] += 1
            return False

        if order.get("exchange") != exchange:
            self.stats["validation_failures"] += 1
            return False

        order["confirmed"] = True
        order["filled_qty"] = filled_qty
        order["filled_price"] = filled_price
        order["confirmed_at"] = time.time()
        self.stats["confirmed_fills"] += 1
        return True

    def sweep_for_ghost_orders(self, now: Optional[float] = None) -> int:
        """Flag approved orders that never received exchange confirmation."""
        now = now or time.time()
        ghost_count = 0
        for order in self._submitted_orders.values():
            if order.get("approved") and not order.get("confirmed"):
                age = now - order.get("submitted_at", now)
                if age > self._confirmation_window_s and not order.get("ghost"):
                    order["ghost"] = True
                    self.stats["ghost_orders"] += 1
                    ghost_count += 1
        return ghost_count

    def build_request_from_opportunity(self, opportunity: Dict[str, Any], side: str = "buy") -> ExecutionRequest:
        """Translate Ocean Scanner output into a validated execution request."""
        price = float(opportunity.get("price") or 0.0)
        confidence = float(opportunity.get("confidence") or 0.0)
        coherence = float(opportunity.get("ocean_score") or confidence)
        quantity = float(opportunity.get("quantity") or 0.0)
        if quantity <= 0 and price > 0:
            # Conservative fallback to avoid oversizing while still allowing the Queen
            # to take opportunities outside the current portfolio holdings.
            quantity = round(25.0 / price, 8)

        return ExecutionRequest(
            symbol=str(opportunity.get("symbol") or "UNKNOWN"),
            side=side,
            quantity=quantity,
            price=price,
            confidence=confidence,
            coherence=coherence,
            lambda_val=float(opportunity.get("lambda") or coherence),
            exchange=str(opportunity.get("exchange") or "unknown"),
            source=str(opportunity.get("source") or "ocean_scanner"),
            trace_id=opportunity.get("trace_id"),
        )
    
    def execute_trade(self, request: ExecutionRequest) -> ExecutionResult:
        self.stats["requests"] += 1
        approved, reason = self.apply_gating_rules(request)
        order_id = self._new_order_id(request)

        self._submitted_orders[order_id] = {
            "order_id": order_id,
            "symbol": request.symbol,
            "side": request.side,
            "exchange": request.exchange,
            "submitted_at": time.time(),
            "approved": approved,
            "reason": reason,
            "requested_qty": request.quantity,
            "requested_price": request.price,
            "trace_id": request.trace_id,
            "confirmed": False,
            "ghost": False,
        }

        if approved:
            self.stats["approved"] += 1
        else:
            self.stats["rejected"] += 1

        return ExecutionResult(
            success=approved,
            symbol=request.symbol,
            side=request.side,
            executed_qty=request.quantity if approved else 0.0,
            executed_price=request.price if approved else 0.0,
            pnl=0.0,
            error=None if approved else reason,
            order_id=order_id,
            exchange=request.exchange,
        )
    
    def get_statistics(self) -> Dict:
        return self.stats

class QueenExecutorBridge:
    def __init__(self, executor):
        self.executor = executor

    def wire_queen_to_executor(self):
        logger.info("🔌 Bridge wired")

    def process_ocean_opportunity(self, opportunity: Dict[str, Any], side: str = "buy") -> ExecutionResult:
        """Simple bridge method that wires scanner opportunities into the executor."""
        request = self.executor.build_request_from_opportunity(opportunity, side=side)
        return self.executor.execute_trade(request)
