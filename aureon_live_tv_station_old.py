#!/usr/bin/env python3
"""
📺🌊 AUREON LIVE TV STATION - 30s DELAYED MARKET STREAM 🌊📺

Purpose:
- Consume REAL Binance WebSocket cache data (ws_cache/ws_prices.json)
- Compute metrics (price, change %, momentum, volatility)
- Queen ↔ Auris ping-pong validation on live metrics
- Convert metrics to harmonic Hz, then back to human text
- Broadcast a 30-second delayed stream (TV-style) while validating predictions

⚠️ REAL DATA ONLY. NO SIMULATIONS. NO RANDOMS.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
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

import json
import time
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Deque, Tuple
from collections import deque
from datetime import datetime

from metatrons_cube_knowledge_exchange import QueenAurisPingPong
from aureon_truth_prediction_engine import (
    TruthPredictionEngine,
    TruthPrediction,
    MarketSnapshot
)

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2
SCHUMANN_BASE = 7.83
LOVE_FREQUENCY = 528.0
MAX_HZ = 963.0

WS_CACHE_PATH = Path(os.getenv("WS_PRICE_CACHE_PATH", "ws_cache/ws_prices.json"))
STREAM_DELAY_SECONDS = 30.0
PINGPONG_INTERVAL = 10.0
PREDICTION_HORIZON_SECONDS = 30.0
MIN_HISTORY_SECONDS = 30.0
LOG_PATH = Path("live_tv_stream.jsonl")


@dataclass
class PriceSnapshot:
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    timestamp: float


@dataclass
class PredictionRecord:
    symbol: str
    start_time: float
    start_price: float
    predicted_price: float
    predicted_change_pct: float
    horizon_seconds: float
    validated: bool = False
    actual_price: float = 0.0
    actual_change_pct: float = 0.0
    correct_direction: Optional[bool] = None


def _read_ws_cache() -> Optional[Dict]:
    if not WS_CACHE_PATH.exists():
        return None
    try:
        return json.loads(WS_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_snapshots(payload: Dict) -> List[PriceSnapshot]:
    tickers = payload.get("ticker_cache", {}) if isinstance(payload, dict) else {}
    generated_at = float(payload.get("generated_at", time.time()))
    snapshots: List[PriceSnapshot] = []

    for key, t in tickers.items():
        if not isinstance(t, dict):
            continue
        base = t.get("base")
        if not base:
            continue
        try:
            price = float(t.get("price", 0) or 0)
            if price <= 0:
                continue
            change = float(t.get("change24h", 0) or 0)
            volume = float(t.get("volume", 0) or 0)
            snapshots.append(PriceSnapshot(
                symbol=str(base).upper(),
                price=price,
                change_24h=change,
                volume_24h=volume,
                timestamp=generated_at
            ))
        except Exception:
            continue

    return snapshots


def _momentum_from_history(history: Deque[Tuple[float, float]]) -> float:
    if len(history) < 2:
        return 0.0
    t0, p0 = history[0]
    t1, p1 = history[-1]
    if p0 <= 0 or t1 <= t0:
        return 0.0
    return (p1 - p0) / p0 * 100


def _volatility_from_history(history: Deque[Tuple[float, float]]) -> float:
    if len(history) < 3:
        return 0.0
    prices = [p for _, p in history]
    mean = sum(prices) / len(prices)
    if mean <= 0:
        return 0.0
    var = sum((p - mean) ** 2 for p in prices) / len(prices)
    return math.sqrt(var) / mean * 100


def _price_to_hz(momentum_pct: float, volatility_pct: float) -> float:
    strength = min(1.0, (abs(momentum_pct) + volatility_pct) / 10.0)
    hz = SCHUMANN_BASE + (MAX_HZ - SCHUMANN_BASE) * strength
    # Blend with LOVE_FREQUENCY for harmonic center
    return (hz + LOVE_FREQUENCY) / 2


def _format_hz_label(hz: float) -> str:
    if hz < 10:
        return "Schumann"
    if hz < 100:
        return "Alpha"
    if hz < 300:
        return "Beta"
    if hz < 700:
        return "Gamma"
    return "Solfeggio"


def _log_event(event: Dict) -> None:
    try:
        LOG_PATH.write_text("", encoding="utf-8") if not LOG_PATH.exists() else None
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main() -> int:
    pingpong = QueenAurisPingPong()
    history: Dict[str, Deque[Tuple[float, float]]] = {}
    predictions: List[PredictionRecord] = []
    delayed_buffer: Deque[Dict] = deque()

    last_pingpong = 0.0
    last_seen_cache = 0.0

    print("📺 AUREON LIVE TV STATION STARTED")
    print(f"   Cache: {WS_CACHE_PATH}")
    print(f"   Delay: {STREAM_DELAY_SECONDS}s | Prediction horizon: {PREDICTION_HORIZON_SECONDS}s")
    print("   REAL DATA ONLY - waiting for Binance WS cache...")

    while True:
        payload = _read_ws_cache()
        if not payload:
            time.sleep(1.0)
            continue

        generated_at = float(payload.get("generated_at", time.time()))
        if generated_at == last_seen_cache:
            time.sleep(0.5)
            continue
        last_seen_cache = generated_at

        snapshots = _extract_snapshots(payload)
        now = time.time()

        for snap in snapshots:
            hist = history.setdefault(snap.symbol, deque(maxlen=180))
            hist.append((snap.timestamp, snap.price))

            # Build prediction if we have enough history
            duration = hist[-1][0] - hist[0][0] if len(hist) >= 2 else 0
            if duration >= MIN_HISTORY_SECONDS:
                t0, p0 = hist[0]
                t1, p1 = hist[-1]
                slope = (p1 - p0) / max(1.0, (t1 - t0))
                predicted_price = p1 + slope * PREDICTION_HORIZON_SECONDS
                predicted_change_pct = ((predicted_price - p1) / p1 * 100) if p1 > 0 else 0
                predictions.append(PredictionRecord(
                    symbol=snap.symbol,
                    start_time=now,
                    start_price=p1,
                    predicted_price=predicted_price,
                    predicted_change_pct=predicted_change_pct,
                    horizon_seconds=PREDICTION_HORIZON_SECONDS
                ))

        # Validate predictions if horizon elapsed
        for pred in predictions:
            if pred.validated:
                continue
            if now - pred.start_time < pred.horizon_seconds:
                continue
            # Find latest price
            hist = history.get(pred.symbol)
            if not hist:
                continue
            _, current_price = hist[-1]
            pred.actual_price = current_price
            pred.actual_change_pct = ((current_price - pred.start_price) / pred.start_price * 100) if pred.start_price > 0 else 0
            pred.correct_direction = (pred.predicted_change_pct >= 0) == (pred.actual_change_pct >= 0)
            pred.validated = True

            _log_event({
                "type": "prediction_validation",
                "timestamp": now,
                "symbol": pred.symbol,
                "predicted_change_pct": pred.predicted_change_pct,
                "actual_change_pct": pred.actual_change_pct,
                "correct_direction": pred.correct_direction
            })

        # Push to delayed buffer for TV output
        for snap in snapshots:
            hist = history.get(snap.symbol)
            if not hist:
                continue
            momentum = _momentum_from_history(hist)
            volatility = _volatility_from_history(hist)
            hz = _price_to_hz(momentum, volatility)
            delayed_buffer.append({
                "timestamp": snap.timestamp,
                "symbol": snap.symbol,
                "price": snap.price,
                "change_24h": snap.change_24h,
                "momentum": momentum,
                "volatility": volatility,
                "hz": hz,
                "hz_label": _format_hz_label(hz),
            })

        # Queen ↔ Auris ping-pong (live analytics)
        if now - last_pingpong >= PINGPONG_INTERVAL and snapshots:
            last_pingpong = now
            top = max(snapshots, key=lambda s: s.volume_24h)
            hist = history.get(top.symbol, deque())
            momentum = _momentum_from_history(hist)
            volatility = _volatility_from_history(hist)
            hz = _price_to_hz(momentum, volatility)
            message = (
                f"LIVE METRICS | {top.symbol} price={top.price:.6f} change24h={top.change_24h:+.2f}% "
                f"momentum30s={momentum:+.3f}% vol30s={volatility:.3f}% hz={hz:.2f}"
            )
            thoughts = pingpong.queen_speaks(message, target_sphere=0)
            pingpong.auris_validates(thoughts)
            truth = pingpong.check_geometric_truth()
            if truth:
                _log_event({
                    "type": "geometric_truth",
                    "timestamp": now,
                    "confidence": truth.confidence,
                    "truth": truth.truth
                })

        # Emit delayed TV stream (30s)
        while delayed_buffer and (now - delayed_buffer[0]["timestamp"]) >= STREAM_DELAY_SECONDS:
            item = delayed_buffer.popleft()
            line = (
                f"📺 DELAYED {STREAM_DELAY_SECONDS:.0f}s | {item['symbol']} | "
                f"${item['price']:.6f} | 24h {item['change_24h']:+.2f}% | "
                f"mom30s {item['momentum']:+.3f}% | vol30s {item['volatility']:.3f}% | "
                f"{item['hz_label']} {item['hz']:.2f} Hz"
            )
            print(line)
            _log_event({
                "type": "delayed_stream",
                "timestamp": now,
                **item
            })

        time.sleep(0.5)


if __name__ == "__main__":
    main()
