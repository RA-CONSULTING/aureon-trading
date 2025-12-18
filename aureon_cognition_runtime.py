from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from aureon_thought_bus import ThoughtBus, Thought

Json = Dict[str, Any]


class MinerModule:
    """
    Listens to market snapshots and emits miner.signal thoughts.
    Replace compute_signal() with your real miner cognition.
    """
    def __init__(self, bus: ThoughtBus):
        self.bus = bus
        self.bus.subscribe("market.snapshot", self.on_market_snapshot)

    def on_market_snapshot(self, t: Thought) -> None:
        snap = t.payload
        universe: List[str] = snap.get("universe", [])
        by_symbol: Json = snap.get("market_by_symbol", {})

        candidates = []
        for sym in universe:
            s = self.compute_signal(sym, by_symbol.get(sym, {}))
            if s is not None:
                candidates.append(s)

        self.bus.publish(Thought(
            source="miner",
            topic="miner.signal_batch",
            trace_id=t.trace_id,
            parent_id=t.id,
            payload={"candidates": candidates},
        ))

    def compute_signal(self, symbol: str, market: Json) -> Optional[Json]:
        # TODO: swap for your miner brain
        momentum = float(market.get("momentum", 0.0))
        gamma = float(market.get("gamma", 0.0))

        if gamma < 0.20:
            return None

        casc = momentum * 10.0
        return {
            "symbol": symbol,
            "side": "buy" if casc > 0 else "sell",
            "strength": casc,
            "gamma": gamma,
            "expected_edge": casc * gamma,
            "min_hold_seconds": 50 * 60,
        }


class RiskModule:
    """
    Risk-aware signal filter with capital and position limits.
    
    🔒 CAPITAL AWARE: Now checks available capital before approving signals.
    This prevents flooding the execution system with orders that will fail.
    """
    def __init__(self, bus: ThoughtBus, max_positions: int = 3, 
                 get_open_positions_count=None, get_available_capital=None,
                 min_order_size: float = 6.0):
        self.bus = bus
        self.max_positions = max_positions
        self.min_order_size = min_order_size
        self.get_open_positions_count = get_open_positions_count or (lambda: 0)
        self.get_available_capital = get_available_capital or (lambda: float('inf'))
        self.bus.subscribe("miner.signal_batch", self.on_signals)

    def on_signals(self, t: Thought) -> None:
        candidates = t.payload.get("candidates", [])
        approved = []
        rejected = []

        # Get real position count from ecosystem
        open_positions = self.get_open_positions_count()
        
        # 🔒 Get available capital - critical for preventing spam orders
        available_capital = self.get_available_capital()
        
        # 🛑 If capital is too low for even one trade, reject all buy signals early
        if available_capital < self.min_order_size:
            for c in candidates:
                if c.get("side", "buy").lower() == "buy":
                    rejected.append({**c, "reason": "insufficient_capital"})
                else:
                    # Allow sell signals even with low capital
                    approved.append(c)
            
            # Publish and return early
            self.bus.publish(Thought(
                source="risk",
                topic="risk.approved_intents",
                trace_id=t.trace_id,
                parent_id=t.id,
                payload={"approved": approved, "rejected": rejected},
            ))
            return

        for c in sorted(candidates, key=lambda x: x.get("expected_edge", 0.0), reverse=True):
            if self.max_positions and self.max_positions > 0 and open_positions >= self.max_positions:
                rejected.append({**c, "reason": "max_positions"})
                continue
            if c.get("expected_edge", 0.0) <= 0:
                rejected.append({**c, "reason": "non_positive_edge"})
                continue

            approved.append(c)
            open_positions += 1

        self.bus.publish(Thought(
            source="risk",
            topic="risk.approved_intents",
            trace_id=t.trace_id,
            parent_id=t.id,
            payload={"approved": approved, "rejected": rejected},
        ))


class ExecutionModule:
    def __init__(self, bus: ThoughtBus, place_order_fn):
        self.bus = bus
        self.place_order_fn = place_order_fn
        self.bus.subscribe("risk.approved_intents", self.on_approved)

    def on_approved(self, t: Thought) -> None:
        for intent in t.payload.get("approved", []):
            symbol = intent["symbol"]
            side = intent["side"]
            qty = float(intent.get("qty", 0.01))

            order_result = self.place_order_fn(symbol=symbol, side=side, qty=qty)

            self.bus.publish(Thought(
                source="execution",
                topic="execution.order_result",
                trace_id=t.trace_id,
                parent_id=t.id,
                payload={"intent": intent, "order_result": order_result},
            ))


class AureonRuntime:
    def __init__(self, persist_path: Optional[str] = "logs/aureon_thoughts.jsonl"):
        self.bus = ThoughtBus(persist_path=persist_path)
        self.miner = MinerModule(self.bus)
        self.risk = RiskModule(self.bus)
        self.exec = ExecutionModule(self.bus, place_order_fn=self.fake_place_order)

    def fake_place_order(self, symbol: str, side: str, qty: float) -> Json:
        # Replace with your ccxt order call
        return {"ok": True, "symbol": symbol, "side": side, "qty": qty, "ts": time.time()}

    def tick(self, universe: List[str], market_by_symbol: Json) -> None:
        self.bus.publish(Thought(
            source="runtime",
            topic="market.snapshot",
            payload={"universe": universe, "market_by_symbol": market_by_symbol},
        ))

    def recent_thoughts(self, topic_prefix: str = "", limit: int = 50) -> List[Json]:
        return self.bus.recall(topic_prefix=topic_prefix or None, limit=limit)
