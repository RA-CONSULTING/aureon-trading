"""Human-time trade cognition and forecast verification.

This module gives the trading loop a small, explicit contract:
what the system believed at entry time, when it expected that belief to
resolve, and how live ticker movement later matched or missed the forecast.
It does not place orders or close trades; it only records and verifies intent.
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Mapping, Optional


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value or 0.0)))


def _finite(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        if math.isfinite(number):
            return number
    except (TypeError, ValueError):
        pass
    return default


@dataclass(frozen=True)
class HumanTimeContext:
    epoch: float
    iso: str
    date: str
    time: str
    weekday: str
    minute_of_day: int
    timezone: str

    @classmethod
    def now(cls, epoch: Optional[float] = None) -> "HumanTimeContext":
        ts = time.time() if epoch is None else float(epoch)
        dt = datetime.fromtimestamp(ts).astimezone()
        return cls(
            epoch=ts,
            iso=dt.isoformat(timespec="seconds"),
            date=dt.date().isoformat(),
            time=dt.strftime("%H:%M:%S"),
            weekday=dt.strftime("%A"),
            minute_of_day=dt.hour * 60 + dt.minute,
            timezone=dt.tzname() or "",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": round(self.epoch, 3),
            "iso": self.iso,
            "date": self.date,
            "time": self.time,
            "weekday": self.weekday,
            "minute_of_day": self.minute_of_day,
            "timezone": self.timezone,
        }


@dataclass
class TradeCognitionPlan:
    plan_id: str
    pair: str
    side: str
    ticker_symbol: str
    entry_price: float
    target_price: float
    target_move_pct: float
    required_move_pct: float
    profit_target_usd: float
    eta_seconds: float
    confidence: float
    probability: float
    opened_at: HumanTimeContext
    expected_by: HumanTimeContext
    reason: str = ""
    sources: Dict[str, Any] = field(default_factory=dict)
    last_verification: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "pair": self.pair,
            "side": self.side,
            "ticker_symbol": self.ticker_symbol,
            "entry_price": self.entry_price,
            "target_price": self.target_price,
            "target_move_pct": self.target_move_pct,
            "required_move_pct": self.required_move_pct,
            "profit_target_usd": self.profit_target_usd,
            "eta_seconds": round(self.eta_seconds, 3),
            "eta_minutes": round(self.eta_seconds / 60.0, 3),
            "confidence": round(self.confidence, 6),
            "probability": round(self.probability, 6),
            "opened_at": self.opened_at.to_dict(),
            "expected_by": self.expected_by.to_dict(),
            "reason": self.reason,
            "sources": dict(self.sources),
            "last_verification": dict(self.last_verification),
        }


class TemporalTradeCognition:
    """Create and verify timestamped trade forecasts."""

    def __init__(self, default_horizon_seconds: float = 180.0):
        self.default_horizon_seconds = max(30.0, float(default_horizon_seconds or 180.0))

    def plan_trade(
        self,
        *,
        pair: str,
        side: str,
        ticker_symbol: str,
        entry_price: float,
        target_price: float,
        required_move_pct: float,
        profit_target_usd: float,
        eta_minutes: Optional[float] = None,
        confidence: float = 0.5,
        probability: Optional[float] = None,
        reason: str = "",
        sources: Optional[Mapping[str, Any]] = None,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        opened = HumanTimeContext.now(now)
        eta_seconds = self._normalise_eta_seconds(eta_minutes, required_move_pct)
        expected = HumanTimeContext.now(opened.epoch + eta_seconds)
        target_move_pct = self._target_move_pct(side, entry_price, target_price)
        confidence = _clamp(confidence)
        probability_value = (
            _clamp(probability)
            if probability is not None
            else _clamp(0.35 + confidence * 0.55)
        )
        plan_id = self._plan_id(pair, side, opened.epoch, entry_price, target_price)
        plan = TradeCognitionPlan(
            plan_id=plan_id,
            pair=pair,
            side=side,
            ticker_symbol=ticker_symbol,
            entry_price=float(entry_price or 0.0),
            target_price=float(target_price or 0.0),
            target_move_pct=target_move_pct,
            required_move_pct=max(0.0, float(required_move_pct or 0.0)),
            profit_target_usd=max(0.0, float(profit_target_usd or 0.0)),
            eta_seconds=eta_seconds,
            confidence=confidence,
            probability=probability_value,
            opened_at=opened,
            expected_by=expected,
            reason=reason,
            sources=dict(sources or {}),
        )
        return plan.to_dict()

    def verify(
        self,
        plan: Mapping[str, Any],
        *,
        current_price: float,
        validated_net_pnl: float = 0.0,
        now: Optional[float] = None,
    ) -> Dict[str, Any]:
        opened = self._epoch_from_section(plan.get("opened_at"))
        expected = self._epoch_from_section(plan.get("expected_by"))
        current_ts = time.time() if now is None else float(now)
        entry = _finite(plan.get("entry_price"))
        target = _finite(plan.get("target_price"))
        side = str(plan.get("side", "buy")).lower()
        target_profit = _finite(plan.get("profit_target_usd"))
        price = _finite(current_price)

        elapsed = max(0.0, current_ts - opened)
        eta = max(1.0, expected - opened)
        time_fraction = _clamp(elapsed / eta)
        direction_move_pct = self._target_move_pct(side, entry, price)
        total_needed_pct = max(abs(self._target_move_pct(side, entry, target)), 1e-9)
        progress = _clamp(direction_move_pct / total_needed_pct)
        due = current_ts >= expected
        target_hit = (
            validated_net_pnl >= target_profit
            if target_profit > 0
            else progress >= 1.0
        )

        if target_hit and not due:
            status = "hit_early"
        elif target_hit:
            status = "hit"
        elif due:
            status = "missed_eta"
        elif progress + 0.15 >= time_fraction:
            status = "on_track"
        else:
            status = "lagging"

        verified_at = HumanTimeContext.now(current_ts)
        return {
            "plan_id": plan.get("plan_id", ""),
            "pair": plan.get("pair", ""),
            "side": side,
            "status": status,
            "verified_at": verified_at.to_dict(),
            "due": due,
            "target_hit": bool(target_hit),
            "elapsed_seconds": round(elapsed, 3),
            "eta_seconds": round(eta, 3),
            "seconds_to_eta": round(expected - current_ts, 3),
            "time_progress": round(time_fraction, 6),
            "price_progress": round(progress, 6),
            "entry_price": entry,
            "current_price": price,
            "target_price": target,
            "direction_move_pct": round(direction_move_pct, 6),
            "validated_net_pnl": round(float(validated_net_pnl or 0.0), 6),
            "target_profit_usd": target_profit,
        }

    def with_verification(self, plan: Mapping[str, Any], verification: Mapping[str, Any]) -> Dict[str, Any]:
        updated = dict(plan)
        updated["last_verification"] = dict(verification)
        return updated

    def _normalise_eta_seconds(self, eta_minutes: Optional[float], required_move_pct: float) -> float:
        eta_min = _finite(eta_minutes, 0.0)
        if eta_min > 0 and eta_min < 999:
            return max(30.0, min(24.0 * 3600.0, eta_min * 60.0))
        required = max(0.0, float(required_move_pct or 0.0))
        if required > 0:
            return max(60.0, min(30.0 * 60.0, required * 180.0))
        return self.default_horizon_seconds

    @staticmethod
    def _target_move_pct(side: str, entry_price: float, target_price: float) -> float:
        entry = float(entry_price or 0.0)
        target = float(target_price or 0.0)
        if entry <= 0 or target <= 0:
            return 0.0
        if str(side).lower() == "sell":
            return (entry - target) / entry * 100.0
        return (target - entry) / entry * 100.0

    @staticmethod
    def _epoch_from_section(section: Any) -> float:
        if isinstance(section, Mapping):
            return _finite(section.get("epoch"), time.time())
        return time.time()

    @staticmethod
    def _plan_id(pair: str, side: str, epoch: float, entry_price: float, target_price: float) -> str:
        raw = f"{pair}|{side}|{epoch:.3f}|{entry_price:.10f}|{target_price:.10f}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
