#!/usr/bin/env python3
"""
HNC Live Connector
------------------
Periodically reads the websocket price cache (ws_cache/ws_prices.json) and feeds
price ticks into the `HncSurgeDetector`. When a surge is detected, publishes an
`intelligence.surge.hnc` event via the global `RealDataFeedHub`.

Usage:
    python aureon_hnc_live_connector.py --symbols BTC,ETH,SOL --interval 0.5

"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import time
import json
import argparse
import logging
from pathlib import Path
from typing import List

from aureon_hnc_surge_detector import HncSurgeDetector, SurgeWindow
from aureon_real_data_feed_hub import get_feed_hub

# Integrations: ThoughtBus for pub/sub and QGITA for Lighthouse validation
try:
    from aureon_thought_bus import get_thought_bus, Thought
    THOUGHT_BUS_OK = True
except Exception:
    get_thought_bus = None
    Thought = None
    THOUGHT_BUS_OK = False

try:
    from aureon_qgita_framework import QGITAMarketAnalyzer
    QGITA_OK = True
except Exception:
    QGITAMarketAnalyzer = None
    QGITA_OK = False

logger = logging.getLogger(__name__)

DEFAULT_WS_CACHE = Path(os.getenv('WS_PRICE_CACHE_PATH', 'ws_cache/ws_prices.json'))


class HncLiveConnector:
    def __init__(self, symbols: List[str], ws_cache_path: Path = DEFAULT_WS_CACHE, poll_interval: float = 0.5):
        self.symbols = symbols
        self.ws_cache_path = Path(ws_cache_path)
        self.poll_interval = poll_interval
        # Adjust detector sample_rate to match poll interval (samples per second)
        sample_rate = max(1, int(round(1.0 / self.poll_interval)))
        # Use an analysis window of 10-60 seconds depending on sample rate
        analysis_window_secs = 20
        analysis_window_size = max(32, min(2048, sample_rate * analysis_window_secs))
        self.detector = HncSurgeDetector(sample_rate=sample_rate, analysis_window_size=analysis_window_size)
        self._last_read_ts = 0.0
        self.hub = get_feed_hub()

        # Wire ThoughtBus if available (for cross-system subscriptions)
        try:
            if THOUGHT_BUS_OK:
                self.thought_bus = get_thought_bus()
                logger.info("ThoughtBus: connected for HNC events")
            else:
                self.thought_bus = None
        except Exception:
            self.thought_bus = None

        # Initialize QGITA market analyzer for Lighthouse validation
        if QGITA_OK and QGITAMarketAnalyzer is not None:
            try:
                self.qgita = QGITAMarketAnalyzer()
                logger.info("QGITA: Analyzer initialized for Lighthouse validation")
            except Exception:
                self.qgita = None
        else:
            self.qgita = None

        # Optional: lazy reference to BotShapeScanner (do not auto-start WS)
        try:
            from aureon_bot_shape_scanner import BotShapeScanner
            self.bot_shape_scanner = BotShapeScanner(self.symbols)
            logger.info("BotShapeScanner: available (not auto-started)")
        except Exception:
            self.bot_shape_scanner = None

        logger.info(f"HNC Live Connector initialized (symbols={self.symbols}, cache={self.ws_cache_path}, sample_rate={sample_rate}, window={analysis_window_size})")

        # Subscribe to RealDataFeedHub market topics for live ticks (if available)
        try:
            if hasattr(self.hub, 'subscribe'):
                # Subscribe to common market topic patterns. Callbacks receive (topic, data)
                self.hub.subscribe('market.ticker', self._hub_event_handler)
                self.hub.subscribe('market.ticker.*', self._hub_event_handler)
                self.hub.subscribe('market.price.*', self._hub_event_handler)
                logger.info('Subscribed to RealDataFeedHub market topics for live ticks')
        except Exception as e:
            logger.debug(f'Failed to subscribe to hub market topics: {e}')

    def _load_prices_from_cache(self):
        """Load prices and normalize to symbol->price mapping (e.g., 'BTC/USD')."""
        if not self.ws_cache_path.exists():
            return {}
        try:
            payload = json.loads(self.ws_cache_path.read_text(encoding='utf-8'))
        except Exception as e:
            logger.debug(f"Failed to read ws cache: {e}")
            return {}

        normalized = {}
        # 1) If payload has 'prices' (binance style), map BASE -> BASE/USD
        prices = payload.get('prices', {}) or {}
        for base, price in prices.items():
            try:
                normalized[f"{base}/USD"] = float(price)
            except Exception:
                continue

        # 2) If payload has 'ticker_cache' (coingecko style), map PAIR -> price
        ticker_cache = payload.get('ticker_cache', {}) or {}
        for pair, entry in ticker_cache.items():
            try:
                normalized[pair.upper()] = float(entry.get('price', 0) or 0)
            except Exception:
                continue

        return normalized

    def _map_base_to_symbol(self, base: str) -> str:
        """Map cache base like 'BTC' to symbol 'BTC/USD'"""
        return f"{base}/USD"

    def _publish_surge(self, surge: SurgeWindow):
        data = {
            'symbol': surge.symbol,
            'start_time': surge.start_time,
            'end_time': surge.end_time,
            'peak_time': surge.peak_time,
            'intensity': surge.intensity,
            'primary_harmonic': surge.primary_harmonic,
            'contributing_count': len(surge.contributing_events),
            'detected_at': time.time()
        }
        # Publish to real feed hub
        try:
            self.hub._publish_to_bus('intelligence.surge.hnc', data)
            logger.info(f"Published HNC surge: {surge.symbol} intensity={surge.intensity:.2f}")
        except Exception as e:
            logger.warning(f"Failed to publish surge to hub: {e}")

        # Also emit a Thought for cross-system listeners (scanners, Queen, UI)
        try:
            if self.thought_bus is not None and Thought is not None:
                thought = Thought(source='hnc', topic='intelligence.surge.hnc', payload=data)
                self.thought_bus.publish(thought)
                logger.info(f"ThoughtBus: emitted hnc surge thought for {surge.symbol}")
        except Exception as e:
            logger.debug(f"ThoughtBus emit failed: {e}")

        # Attempt QGITA validation via FTCP -> Lighthouse pipeline
        try:
            if self.qgita is not None:
                buf = self.detector.price_history.get(surge.symbol, None)
                if buf and len(buf) >= 20:
                    import numpy as _np
                    values = _np.array(list(buf))
                    # Create synthetic times based on sample_rate
                    dt = 1.0 / max(1, self.detector.sample_rate)
                    n = len(values)
                    times = _np.array([time.time() - (n - i) * dt for i in range(n)])

                    # Stage 1: detect FTCPs
                    ftcps = self.qgita.ftcp_detector.detect_ftcps(times, values)
                    if ftcps:
                        strongest = self.qgita.ftcp_detector.get_strongest_ftcp(ftcps)
                        if strongest:
                            # Stage 2: Lighthouse validation
                            lhe = self.qgita.lighthouse.validate_ftcp(strongest, values)
                            if lhe:
                                lhe_payload = {
                                    'symbol': surge.symbol,
                                    'lighthouse_intensity': lhe.lighthouse_intensity,
                                    'confidence': lhe.confidence,
                                    'event_type': lhe.event_type.value,
                                    'timestamp': lhe.timestamp
                                }
                                # Publish validated Lighthouse event
                                try:
                                    self.hub._publish_to_bus('intelligence.lighthouse.event', lhe_payload)
                                    logger.info(f"Published Lighthouse event for {surge.symbol}: L={lhe.lighthouse_intensity:.3f}")
                                except Exception:
                                    logger.debug("Failed to publish Lighthouse event to hub")

                                # ThoughtBus emit
                                if self.thought_bus is not None and Thought is not None:
                                    thought = Thought(source='hnc', topic='intelligence.lighthouse.hnc', payload=lhe_payload)
                                    self.thought_bus.publish(thought)

                                # Optional: ping BotShapeScanner to perform immediate micro scan
                                if self.bot_shape_scanner is not None:
                                    try:
                                        # call a lightweight probe (do not start full WS)
                                        # BotShapeScanner provides analysis methods; call internal scan method if present
                                        if hasattr(self.bot_shape_scanner, '_compute_full_spectrum_fingerprint'):
                                            fingerprint = self.bot_shape_scanner._compute_full_spectrum_fingerprint(surge.symbol)
                                            if fingerprint:
                                                fp_payload = {'symbol': surge.symbol, 'fingerprint': repr(fingerprint), 'ts': time.time()}
                                                self.hub._publish_to_bus('intelligence.botshape.snapshot', fp_payload)
                                    except Exception:
                                        logger.debug('BotShapeScanner probe failed')
        except Exception as e:
            logger.debug(f"QGITA validation error: {e}")

    def run_once(self):
        prices = self._load_prices_from_cache()
        if not prices:
            logger.debug("No prices in cache")
            return

        # For each requested symbol, get the base price and feed into detector
        for base in prices.keys():
            symbol = self._map_base_to_symbol(base)
            if symbol not in self.symbols:
                continue
            price = prices.get(base)
            if price is None:
                continue
            self.detector.add_price_tick(symbol, float(price))

            surge = self.detector.detect_surge(symbol)
            if surge:
                print(f"🔔 HNC Surge detected for {symbol}: intensity={surge.intensity:.2f} (peak: {surge.peak_time})")
                self._publish_surge(surge)

    def run_forever(self):
        print("🌊 HNC Live Connector running. Press Ctrl-C to stop.")
        try:
            while True:
                self.run_once()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("Stopping HNC Live Connector")

    # ----- Hub event handler for direct feed subscription -----
    def _hub_event_handler(self, topic: str, data: dict):
        """Handle events published on RealDataFeedHub and extract price ticks."""
        try:
            if not isinstance(data, dict):
                return

            # Common fields used by various producers
            symbol = data.get('symbol') or data.get('s') or data.get('pair')
            price = data.get('price') or data.get('lastPrice') or data.get('last') or data.get('p')

            if not symbol or price is None:
                return

            # Normalize symbol to form 'BTC/USD'
            if isinstance(symbol, str) and '/' not in symbol:
                symbol = f"{symbol.upper()}/USD"
            else:
                symbol = symbol.upper()

            if symbol not in self.symbols:
                return

            # Feed into detector
            self.detector.add_price_tick(symbol, float(price))
            surge = self.detector.detect_surge(symbol)
            if surge:
                print(f"🔔 HNC Surge detected (live hub): {symbol} intensity={surge.intensity:.2f}")
                self._publish_surge(surge)
        except Exception as e:
            logger.debug(f"Hub event handler error: {e}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--symbols', default=os.getenv('HNC_SYMBOLS', 'BTC/USD,ETH/USD,SOL/USD'), help='Comma-separated symbols to watch (format BASE/USD)')
    p.add_argument('--interval', type=float, default=float(os.getenv('HNC_POLL_INTERVAL', '0.5')), help='Poll interval (s)')
    p.add_argument('--ws-cache', default=os.getenv('WS_PRICE_CACHE_PATH', 'ws_cache/ws_prices.json'), help='Path to WS price cache JSON')
    return p.parse_args()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s | %(message)s')
    args = parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(',')]
    connector = HncLiveConnector(symbols=symbols, ws_cache_path=Path(args.ws_cache), poll_interval=args.interval)
    connector.run_forever()
