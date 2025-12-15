from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from typing import List

from .config_manager import TradingConfig


@dataclass
class Position:
    symbol: str
    size: float
    entry_price: float


@dataclass
class RuntimeState:
    running: bool = False
    pnl: float = 0.0
    positions: List[Position] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)


class TradingService:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.state = RuntimeState()
        self._worker: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._current_price = 100.0

    def start(self) -> None:
        if self.state.running:
            self.state.logs.append("Trading already running.")
            return
        self.state.running = True
        self.state.logs.append(
            f"Trading service started in {self.config.mode} mode for {self.config.base_asset}/{self.config.quote_asset}."
        )
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        if not self.state.running:
            return
        self.state.logs.append("Stopping trading service...")
        self._stop_event.set()
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2)
        self.state.running = False
        self.state.logs.append("Trading stopped.")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            jitter = random.uniform(-0.8, 1.5)
            self._current_price = max(1.0, self._current_price + jitter)

            # Mark-to-market for open positions
            if self.state.positions:
                pos = self.state.positions[0]
                unrealized = (self._current_price - pos.entry_price) * pos.size * 0.01
                self.state.pnl = round(unrealized, 2)

            # Occasionally open or adjust a position
            if random.random() > 0.75:
                if self.config.trade_size <= 0:
                    self.state.logs.append("Trade size must be positive; adjust config to resume trading.")
                else:
                    position = Position(
                        symbol=f"{self.config.base_asset}/{self.config.quote_asset}",
                        size=self.config.trade_size,
                        entry_price=round(self._current_price, 2),
                    )
                    self.state.positions = [position]
                    self.state.logs.append(
                        f"Opened {position.size} {position.symbol} @ {position.entry_price}"
                    )

            if random.random() > 0.9 and self.state.positions:
                closed = self.state.positions.pop()
                realized = (self._current_price - closed.entry_price) * closed.size * 0.01
                self.state.pnl = round(realized, 2)
                self.state.logs.append(
                    f"Closed {closed.size} {closed.symbol} at {self._current_price:.2f} | P&L: {self.state.pnl}"
                )

            time.sleep(1)


__all__ = ["TradingService", "RuntimeState", "Position"]
