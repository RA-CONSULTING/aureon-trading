#!/usr/bin/env python3
"""
Lightweight CLI to inspect EnhancementLayer modifiers + a quick fused probability proxy
for a given symbol/exchange using public tickers (Binance/Kraken).

Usage examples:
  python scripts/enhancement_cli.py --symbol BTCUSDT --exchange binance
  python scripts/enhancement_cli.py --symbol XBTUSD --exchange kraken

Outputs:
  - Price, 24h change %, volume
  - Enhancement modifier + emotional state/phase/band/chakra
  - Simple fused probability + action bucket (proxy, not production router)

This avoids needing full aureon_unified_ecosystem; uses public REST.
"""

import argparse
import sys
import math
from typing import Optional, Tuple, List

import requests

# Ensure local imports work when run from repository root
sys.path.append('.')

try:
    from aureon_enhancements import EnhancementLayer, get_emotional_color
except Exception as exc:  # pragma: no cover - optional deps
    print(f"⚠️  EnhancementLayer not available: {exc}")
    EnhancementLayer = None  # type: ignore
    get_emotional_color = lambda x: ''  # type: ignore


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def synth_waveform(freq: float, samples: int = 32, sample_rate: int = 8000) -> List[float]:
    """Generate a short sine waveform preview for readability (not for audio)."""
    if freq <= 0 or samples <= 0:
        return []
    out: List[float] = []
    for n in range(samples):
        t = n / sample_rate
        out.append(math.sin(2 * math.pi * freq * t))
    return out


def sparkline(values: List[float]) -> str:
    """Render a tiny sparkline for quick visual read."""
    if not values:
        return ""
    blocks = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    span = hi - lo if hi != lo else 1.0
    scaled = [int((v - lo) / span * (len(blocks) - 1)) for v in values]
    return ''.join(blocks[i] for i in scaled)


def fetch_binance(symbol: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    url = 'https://api.binance.com/api/v3/ticker/24hr'
    try:
        resp = requests.get(url, params={'symbol': symbol}, timeout=5)
        data = resp.json()
        if 'lastPrice' not in data:
            return None, None, None
        price = float(data.get('lastPrice', 0))
        change_pct = float(data.get('priceChangePercent', 0))
        volume = float(data.get('quoteVolume', 0))
        return price, change_pct, volume
    except Exception:
        return None, None, None


def fetch_kraken(symbol: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    # Kraken expects pairs like XBTUSD, ETHUSD, SOLUSD
    pair = symbol.upper()
    url = 'https://api.kraken.com/0/public/Ticker'
    try:
        resp = requests.get(url, params={'pair': pair}, timeout=5)
        data = resp.json()
        if data.get('error'):
            return None, None, None
        result = data.get('result') or {}
        if not result:
            return None, None, None
        first = next(iter(result.values()))
        last = float(first.get('c', [0])[0])
        open_price = float(first.get('o', last)) or last
        change_pct = ((last - open_price) / open_price * 100) if open_price else 0.0
        volume = float(first.get('v', [0, 0])[1])
        return last, change_pct, volume
    except Exception:
        return None, None, None


def action_bucket(p: float) -> str:
    if p >= 0.70:
        return 'STRONG_BUY'
    if p >= 0.60:
        return 'BUY'
    if p >= 0.55:
        return 'SLIGHT_BUY'
    if p >= 0.45:
        return 'HOLD'
    if p >= 0.40:
        return 'SLIGHT_SELL'
    if p >= 0.30:
        return 'SELL'
    return 'STRONG_SELL'


def main():
    parser = argparse.ArgumentParser(description="Enhancement modifier + fused-prob proxy")
    parser.add_argument('--symbol', default='BTCUSDT', help='Symbol (e.g., BTCUSDT or XBTUSD)')
    parser.add_argument('--exchange', default='binance', choices=['binance', 'kraken'], help='Exchange to query')
    parser.add_argument('--waveform', action='store_true', help='Show a short waveform preview at the emotional frequency')
    parser.add_argument('--samples', type=int, default=32, help='Number of samples for waveform preview (default 32)')
    args = parser.parse_args()

    exchange = args.exchange.lower()
    symbol = args.symbol.upper()

    if exchange == 'binance':
        price, change_pct, volume = fetch_binance(symbol)
    else:
        price, change_pct, volume = fetch_kraken(symbol)

    if price is None:
        print(f"🚫 Could not fetch ticker for {symbol} on {exchange}")
        sys.exit(1)

    change_pct = change_pct or 0.0
    volume = volume or 0.0

    # Proxy lambda and coherence from price action
    lambda_value = clamp(change_pct / 100.0, -1.0, 1.0)
    coherence = clamp(abs(change_pct) / 10.0, 0.0, 1.0)  # heuristic: larger move → higher coherence
    volatility = abs(change_pct) / 100.0

    enh_modifier = 1.0
    enh_state = 'Neutral'
    enh_phase = 'LOVE'
    enh_band = None
    enh_chakra = None
    enh_freq = None
    color = ''

    if EnhancementLayer:
        try:
            layer = EnhancementLayer()
            result = layer.get_unified_modifier(
                lambda_value=lambda_value,
                coherence=coherence,
                price=price,
                volume=volume,
                volatility=volatility,
                exchange=exchange.upper(),
            )
            enh_modifier = result.trading_modifier
            enh_state = result.emotional_state
            enh_phase = result.cycle_phase
            enh_band = result.emotion_band
            enh_chakra = result.chakra_alignment
            enh_freq = result.emotional_frequency
            color = get_emotional_color(result.emotional_state)
        except Exception as exc:  # pragma: no cover
            print(f"⚠️  Enhancement calc failed: {exc}")

    # Simple fused probability proxy
    base_prob = 0.5 + (change_pct / 100.0) * 0.5  # map -100..+100% to 0..1 with center 0.5
    base_prob = clamp(base_prob, 0.0, 1.0)
    fused_prob = clamp(base_prob * enh_modifier, 0.0, 1.0)
    action = action_bucket(fused_prob)

    print(f"\n📈 {exchange.upper()} {symbol}")
    print(f"   Price: {price:.6f} | 24h Δ: {change_pct:+.2f}% | Vol: {volume:.2f}")
    print(f"   λ: {lambda_value:+.3f} | Coherence: {coherence:.3f} | Volatility: {volatility:.3f}")

    print(f"\n✨ Enhancement Layer")
    print(f"   Modifier: {enh_modifier:.3f}x | State: {enh_state} | Phase: {enh_phase} {color}")
    if enh_band:
        print(f"   Emotion band: {enh_band}")
    if enh_chakra:
        print(f"   Chakra alignment: {enh_chakra}")
    if args.waveform and enh_freq:
        wf = synth_waveform(enh_freq, samples=args.samples)
        print(f"   Waveform @ {enh_freq:.1f}Hz (first {len(wf)} samples):")
        print(f"     {sparkline(wf)}")
        if wf:
            # Show numeric preview for clarity
            preview = ', '.join(f"{v:+.2f}" for v in wf[:8])
            print(f"     samples: {preview} ...")

    print(f"\n🧠 Fused Prob (proxy)")
    print(f"   Base: {base_prob:.3f} | Fused: {fused_prob:.3f} | Action: {action}")
    print()


if __name__ == '__main__':
    main()
