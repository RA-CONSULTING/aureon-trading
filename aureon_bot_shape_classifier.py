"""
Bot Shape Classifier

Uses incoming market price streams and orderbook analyses to compute short-time
spectrograms, extract spectral features, and classify observed bot/whale shapes
(e.g., grid, spiral, oscillator, taper, accumulation/distribution).

Publishes:
- topic: `whale.sonar.spectrogram` payload: {symbol, detected_at, peaks, centroid, bandwidth}
- topic: `whale.shape.detected` payload: {symbol, detected_at, shape: {subtype, score, reason}, spectrogram_summary}
"""
from __future__ import annotations

import logging
import math
import time
from collections import defaultdict, deque
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import numpy as np

from aureon_thought_bus import get_thought_bus, Thought

try:
    from whale_metrics import whale_shape_detected_total
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    whale_shape_detected_total = None

# ════════════════════════════════════════════════════════════════════════════════
# 🐦 CHIRP BUS INTEGRATION - Emit strong bot patterns to Orca!
# ════════════════════════════════════════════════════════════════════════════════
CHIRP_BUS_AVAILABLE = False
get_chirp_bus = None
try:
    from aureon_chirp_bus import get_chirp_bus
    CHIRP_BUS_AVAILABLE = True
except ImportError:
    CHIRP_BUS_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════════════════
# 🌐 GLOBAL MARKET INTEGRATION
# ════════════════════════════════════════════════════════════════════════════════
try:
    from kraken_client import KrakenClient
    KRAKEN_AVAILABLE = True
except ImportError:
    KRAKEN_AVAILABLE = False
    KrakenClient = None

try:
    from binance_ws_client import BinanceWebSocketClient
    BINANCE_WS_AVAILABLE = True
except ImportError:
    BINANCE_WS_AVAILABLE = False
    BinanceWebSocketClient = None

try:
    from capital_client import CapitalClient
    CAPITAL_AVAILABLE = True
except ImportError:
    CAPITAL_AVAILABLE = False
    CapitalClient = None

logger = logging.getLogger(__name__)


class BotShapeClassifier:
    def __init__(self, sample_window: int = 128, hop: int = 32):
        self.thought_bus = get_thought_bus()
        # price history per symbol: deque of (ts, price)
        self.price_hist: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1024))
        self.sample_window = int(sample_window)
        self.hop = int(hop)
        
        # 🌐 GLOBAL MARKET CLIENTS
        self.kraken_client: Optional[Any] = None
        self.binance_ws: Optional[Any] = None
        self.capital_client: Optional[Any] = None
        
        # Initialize market connections
        self._init_market_connections()
        
        # 🐦 CHIRP BUS - Emit strong bot patterns to Orca
        self.chirp_bus = None
        if CHIRP_BUS_AVAILABLE and get_chirp_bus:
            try:
                self.chirp_bus = get_chirp_bus()
                logger.info("🐦 Bot Shape Classifier → Orca CHIRP BUS connected")
            except Exception as e:
                logger.debug(f"Chirp bus init failed: {e}")

        # subscribe to market price updates and orderbook analyses
        try:
            self.thought_bus.subscribe('market.*', self._on_market)
        except Exception:
            logger.debug('BotShapeClassifier: failed to subscribe to market.*')
        try:
            self.thought_bus.subscribe('whale.orderbook.analyzed', self._on_orderbook)
        except Exception:
            logger.debug('BotShapeClassifier: failed to subscribe to whale.orderbook.analyzed')

    def _on_market(self, thought: Thought) -> None:
        payload = thought.payload or {}
        symbol = payload.get('symbol') or payload.get('s')
        price = payload.get('price') or payload.get('c') or payload.get('close')
        ts = payload.get('ts') or thought.ts or time.time()
        try:
            if not symbol or price is None:
                return
            price = float(price)
            self.price_hist[symbol].append((ts, price))
        except Exception:
            return

    def _on_orderbook(self, thought: Thought) -> None:
        payload = thought.payload or {}
        symbol = payload.get('symbol')
        exchange = payload.get('exchange') or payload.get('exch')
        if not symbol:
            return
        # If we have enough price history, compute spectrogram and classify
        ph = list(self.price_hist.get(symbol, []))
        if len(ph) < self.sample_window:
            # not enough data -> try to fetch from external cache (best-effort)
            logger.debug('Not enough price history for %s (have=%d need=%d)', symbol, len(ph), self.sample_window)
            return

        timestamps, prices = zip(*ph[-self.sample_window:])
        prices = np.array(prices)

        # Integrate harmonic analyzer (if available) for frequency/coherence/phase features
        harmonic_info = {}
        try:
            from aureon_probability_nexus import HarmonicAnalyzer
            ha = HarmonicAnalyzer()
            # HarmonicAnalyzer expects a price list; pass the last 100 prices if available
            freq, coh, ph = ha.analyze(list(prices[-100:]))
            harmonic_info = {'frequency': float(freq), 'coherence': float(coh), 'phase': float(ph)}
        except Exception:
            harmonic_info = {}

        # Work with log returns to emphasize micro-movements
        returns = np.diff(np.log(prices + 1e-12))
        if len(returns) < 8:
            return

        # Build spectrogram via short-time FFT
        S = self._stft(returns, n_fft=self.sample_window//2, hop=self.hop)
        # magnitude spectrogram
        mag = np.abs(S)
        # Normalize per-column
        mag_norm = mag / (np.max(mag, axis=0, keepdims=True) + 1e-9)

        # Spectral features
        centroid = self._spectral_centroid(mag)
        bandwidth = self._spectral_bandwidth(mag, centroid)
        peaks = self._dominant_peaks(mag, top_n=3)
        flatness = self._spectral_flatness(mag)
        energy = float(np.sum(mag))

        spectro_summary = {
            'shape_frames': mag.shape[1],
            'centroid': float(centroid),
            'bandwidth': float(bandwidth),
            'flatness': float(flatness),
            'energy': float(energy),
            'peaks': peaks,
            'harmonic': harmonic_info,
        }

        # Heuristic classification
        layering = float(payload.get('layering_score', 0.0) or 0.0)
        bids_depth = float(payload.get('bids_depth', 0.0) or 0.0)
        asks_depth = float(payload.get('asks_depth', 0.0) or 0.0)

        subtype, score, reason = self._classify_shape(spectro_summary, layering, bids_depth, asks_depth)

        detected = {
            'symbol': symbol,
            'exchange': exchange,
            'detected_at': time.time(),
            'shape': {'subtype': subtype, 'score': float(score), 'reason': reason},
            'spectrogram': spectro_summary,
        }
        
        # Emit strong patterns to Orca for trading signals
        self.emit_shape_to_orca(symbol, detected['shape'], exchange, spectro_summary)

        # Publish both a spectrogram thought (compact) and a shape classification
        s_th = Thought(source='bot_shape_classifier', topic='whale.sonar.spectrogram', payload={'symbol': symbol, 'spectrogram': spectro_summary})
        try:
            self.thought_bus.publish(s_th)
        except Exception:
            logger.debug('Failed to publish whale.sonar.spectrogram')

        # A-Z-Z-A echo signature (simple mirrored peaks) to model echolocation-like ping
        try:
            peak_bins = [p['bin'] for p in peaks]
            echo_sig = peak_bins + peak_bins[::-1]
            echo_payload = {'symbol': symbol, 'echo_signature': echo_sig, 'detected_at': time.time()}
            e_th = Thought(source='bot_shape_classifier', topic='whale.sonar.echo', payload=echo_payload)
            self.thought_bus.publish(e_th)
        except Exception:
            logger.debug('Failed to publish whale.sonar.echo')

        th = Thought(source='bot_shape_classifier', topic='whale.shape.detected', payload=detected)
        try:
            self.thought_bus.publish(th)
            # Emit metrics
            if METRICS_AVAILABLE and whale_shape_detected_total:
                whale_shape_detected_total.inc(subtype=subtype, symbol=symbol, exchange=exchange or 'unknown')
        except Exception:
            logger.debug('Failed to publish whale.shape.detected')

    # ----------------- signal processing helpers -----------------
    def _stft(self, x: np.ndarray, n_fft: int = 32, hop: int = 8) -> np.ndarray:
        n = len(x)
        if n < n_fft:
            n_fft = max(8, n//2)
        frames = []
        for start in range(0, n - n_fft + 1, hop):
            win = x[start:start+n_fft] * np.hanning(n_fft)
            fft = np.fft.rfft(win)
            frames.append(fft)
        if not frames:
            return np.zeros((n_fft//2+1, 0), dtype=np.complex64)
        return np.column_stack(frames)

    def _spectral_centroid(self, mag: np.ndarray) -> float:
        freqs = np.arange(mag.shape[0])
        power = np.mean(mag, axis=1)
        num = np.sum(freqs * power)
        den = np.sum(power) + 1e-12
        return float(num / den)

    def _spectral_bandwidth(self, mag: np.ndarray, centroid: float) -> float:
        freqs = np.arange(mag.shape[0])
        power = np.mean(mag, axis=1)
        num = np.sum(((freqs - centroid) ** 2) * power)
        den = np.sum(power) + 1e-12
        return float(math.sqrt(num / den))

    def _dominant_peaks(self, mag: np.ndarray, top_n: int = 3) -> List[Dict[str, float]]:
        mean_spec = np.mean(mag, axis=1)
        idx = np.argsort(mean_spec)[::-1][:top_n]
        return [{'bin': int(i), 'power': float(mean_spec[i])} for i in idx]

    def _spectral_flatness(self, mag: np.ndarray) -> float:
        mean_spec = np.mean(mag, axis=1) + 1e-12
        geo = float(np.exp(np.mean(np.log(mean_spec))))
        arith = float(np.mean(mean_spec))
        return float(geo / (arith + 1e-12))

    # ----------------- classification heuristics -----------------
    def _classify_shape(self, spectro: Dict[str, Any], layering: float, bids_depth: float, asks_depth: float):
        centroid = spectro['centroid']
        flatness = spectro['flatness']
        energy = spectro['energy']
        peaks = spectro['peaks']

        # Heuristic rules:
        # - Grid: high layering or low flatness with multiple evenly strong peaks
        # - Oscillator: dominant single peak, low bandwidth
        # - Spiral: shifting centroid across frames (not trivially detectable here) -> use bandwidth>threshold
        # - Taper: energy low and flatness increasing
        # - Accumulation/Distribution: inferred from wall side/imbalance (bids_depth vs asks_depth)

        # grid
        if layering > 0.6 or (len(peaks) >= 2 and flatness < 0.5 and peaks[1]['power'] > 0.4 * peaks[0]['power']):
            return 'grid', min(0.99, 0.4 + 0.6 * layering + (1.0 - flatness) * 0.2), 'layering_or_multi_peak'

        # oscillator
        if spectro['bandwidth'] < 2.0 and peaks and peaks[0]['power'] > 0.5 * max(0.01, sum(p['power'] for p in peaks)):
            return 'oscillator', min(0.99, 0.5 + (1.0 - spectro['bandwidth']/10.0)), 'dominant_peak_low_bandwidth'

        # spiral (bandwidth high but centroid moderate)
        if spectro['bandwidth'] > 4.0 and spectro['centroid'] > 2.0:
            return 'spiral', min(0.95, 0.4 + 0.12 * spectro['bandwidth']), 'wideband_centroid'

        # taper
        if energy < 1e-3 or spectro['flatness'] > 0.85:
            return 'taper', 0.6, 'low_energy_or_flat'

        # accumulation / distribution
        if bids_depth > asks_depth * 1.5:
            return 'accumulation', min(0.99, 0.5 + min(0.5, bids_depth / (asks_depth + 1e-9) / 10.0)), 'bid_depth_imbalance'
        if asks_depth > bids_depth * 1.5:
            return 'distribution', min(0.99, 0.5 + min(0.5, asks_depth / (bids_depth + 1e-9) / 10.0)), 'ask_depth_imbalance'

        # default neutral
        return 'neutral', 0.4, 'no_strong_signal'


# Default singleton
default_bot_shape_classifier: Optional[BotShapeClassifier] = None
try:
    default_bot_shape_classifier = BotShapeClassifier()
except Exception:
    default_bot_shape_classifier = None


if __name__ == '__main__':
    # quick CLI test: ingest sample generated price data and a fake orderbook
    import argparse
    import math

    ap = argparse.ArgumentParser()
    ap.add_argument('symbol', nargs='?', default='TESTCOIN/USD')
    args = ap.parse_args()

    from aureon_thought_bus import get_thought_bus, Thought
    tb = get_thought_bus()

    # publish synthetic market ticks (sine + noise)
    symbol = args.symbol
    for t in range(256):
        price = 100.0 + math.sin(t/4.0) * 0.5 + (0.01 * (t % 5))
        th = Thought(source='cli', topic='market.snapshot', payload={'symbol': symbol, 'price': price, 'ts': time.time()})
        tb.publish(th)
        time.sleep(0.01)

    # publish a fake orderbook analyzed event
    analysis = {'symbol': symbol, 'detected_at': time.time(), 'walls': [{'price':100.0,'size':2000.0,'notional_usd':200000.0,'side':'bid'}], 'layering_score':0.2, 'bids_depth':200000.0, 'asks_depth':50000.0}
    tb.publish(Thought(source='cli', topic='whale.orderbook.analyzed', payload=analysis))
