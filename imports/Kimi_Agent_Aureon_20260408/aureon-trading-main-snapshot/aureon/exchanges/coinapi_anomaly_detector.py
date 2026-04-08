#!/usr/bin/env python3
"""
🌍⚡ COINAPI ANOMALY DETECTOR - DATA TRUTH ENGINE ⚡🌍
═══════════════════════════════════════════════════════════════

Cross-validates market data from CoinAPI with our internal feeds.
Detects anomalies, discrepancies, and hidden signals in the data.
Uses anomalies to refine our own algorithms and discover the "real story".

CoinAPI provides aggregated data from 300+ exchanges:
- OHLCV data (trades, quotes, order books)
- Real-time and historical market data
- Exchange metadata and status

We use this to:
1. Detect price manipulation or wash trading
2. Find arbitrage opportunities across exchanges
3. Identify data feed latencies and frontrunning
4. Validate our own data quality
5. Discover hidden liquidity patterns

Gary Leckey & GitHub Copilot | November 2025
"The Truth is in the Anomalies"
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import time
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import statistics

# ═══════════════════════════════════════════════════════════════
# COINAPI CONFIGURATION
# ═══════════════════════════════════════════════════════════════

COINAPI_BASE_URL = "https://rest.coinapi.io/v1"
COINAPI_API_KEY = os.getenv('COINAPI_KEY', '')  # Set in .env

# Anomaly detection thresholds
ANOMALY_THRESHOLDS = {
    'PRICE_SPREAD': 0.02,        # 2% price difference is anomalous
    'VOLUME_SPIKE': 3.0,         # 3x average volume
    'LATENCY_MS': 500,           # 500ms latency is suspicious
    'ORDERBOOK_IMBALANCE': 0.7,  # 70/30 bid/ask ratio
    'WASH_TRADE_RATIO': 0.15,    # 15% wash trading indicator
    'FRONTRUN_WINDOW_MS': 100,   # 100ms frontrunning window
}

# Prime-based confidence scoring
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]


class AnomalyType(Enum):
    """Types of market data anomalies"""
    PRICE_MANIPULATION = "💰 Price Manipulation"
    WASH_TRADING = "🔄 Wash Trading"
    LATENCY_ARBITRAGE = "⚡ Latency Arbitrage"
    ORDERBOOK_SPOOFING = "📊 Orderbook Spoofing"
    VOLUME_INFLATION = "📈 Volume Inflation"
    EXCHANGE_OUTAGE = "🚨 Exchange Outage"
    FRONTRUNNING = "🎯 Frontrunning Detected"
    LIQUIDITY_DRAIN = "💧 Liquidity Drain"
    CROSS_EXCHANGE_SPREAD = "🌐 Cross-Exchange Spread"


@dataclass
class MarketAnomaly:
    """Detected market anomaly"""
    anomaly_type: AnomalyType
    symbol: str
    exchange: str
    timestamp: datetime
    severity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    description: str
    evidence: Dict[str, Any]
    recommendation: str
    
    # Refinement data
    expected_value: float = 0.0
    actual_value: float = 0.0
    deviation_pct: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'type': self.anomaly_type.value,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'confidence': self.confidence,
            'description': self.description,
            'evidence': self.evidence,
            'recommendation': self.recommendation,
            'expected': self.expected_value,
            'actual': self.actual_value,
            'deviation': self.deviation_pct,
        }


@dataclass
class ExchangeDataPoint:
    """Single data point from an exchange via CoinAPI"""
    exchange_id: str
    symbol: str
    price: float
    volume_24h: float
    bid: float
    ask: float
    timestamp: datetime
    latency_ms: float = 0.0
    
    def spread_pct(self) -> float:
        """Calculate bid-ask spread percentage"""
        if self.bid <= 0:
            return 0.0
        return ((self.ask - self.bid) / self.bid) * 100


class CoinAPIClient:
    """
    CoinAPI REST client for fetching multi-exchange data.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or COINAPI_API_KEY
        self.base_url = COINAPI_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'X-CoinAPI-Key': self.api_key,
            'Accept': 'application/json',
        })
        self.last_status_code: Optional[int] = None
        self.last_error_text: Optional[str] = None
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Cache
        self.exchange_cache = {}
        self.symbol_cache = {}
        
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling"""
        if not self.api_key:
            return None
        
        self._rate_limit()
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            self.last_status_code = int(getattr(response, "status_code", 0) or 0)
            
            if response.status_code == 200:
                self.last_error_text = None
                return response.json()
            elif response.status_code == 429:
                self.last_error_text = str(getattr(response, "text", "") or "")
                print("⚠️  CoinAPI rate limit hit")
                return None
            else:
                self.last_error_text = str(getattr(response, "text", "") or "")
                snippet = self.last_error_text[:200].replace("\n", " ")
                print(f"⚠️  CoinAPI error: {response.status_code} ({snippet})")
                return None
        except Exception as e:
            self.last_status_code = None
            self.last_error_text = str(e)
            print(f"⚠️  CoinAPI request failed: {e}")
            return None
    
    def get_exchanges(self) -> List[Dict]:
        """Get list of all exchanges"""
        if 'exchanges' in self.exchange_cache:
            return self.exchange_cache['exchanges']
        
        data = self._request('exchanges')
        if data:
            self.exchange_cache['exchanges'] = data
            return data
        return []
    
    def get_current_rate(self, asset_id_base: str, asset_id_quote: str) -> Optional[Dict]:
        """Get current exchange rate"""
        endpoint = f"exchangerate/{asset_id_base}/{asset_id_quote}"
        return self._request(endpoint)
    
    def get_ohlcv_latest(self, symbol_id: str, period: str = "1MIN", limit: int = 100) -> List[Dict]:
        """Get latest OHLCV data"""
        endpoint = f"ohlcv/{symbol_id}/latest"
        params = {'period_id': period, 'limit': limit}
        data = self._request(endpoint, params)
        return data if data else []

    def get_ohlcv_history(
        self,
        symbol_id: str,
        period: str = "1MIN",
        time_start: str | None = None,
        time_end: str | None = None,
        limit: int = 10000,
    ) -> List[Dict]:
        """Get historical OHLCV data (CoinAPI /ohlcv/{symbol_id}/history)."""
        endpoint = f"ohlcv/{symbol_id}/history"
        params: Dict[str, Any] = {'period_id': period, 'limit': limit}
        if time_start:
            params['time_start'] = time_start
        if time_end:
            params['time_end'] = time_end
        data = self._request(endpoint, params)
        return data if data else []
    
    def get_quotes_current(self, symbol_id: str = None) -> List[Dict]:
        """Get current quotes (bid/ask)"""
        endpoint = "quotes/current"
        params = {'filter_symbol_id': symbol_id} if symbol_id else {}
        data = self._request(endpoint, params)
        return data if data else []
    
    def get_orderbook_current(self, symbol_id: str, limit_levels: int = 20) -> Optional[Dict]:
        """Get current orderbook"""
        endpoint = f"orderbooks/{symbol_id}/current"
        params = {'limit_levels': limit_levels}
        return self._request(endpoint, params)
    
    def get_trades_latest(self, symbol_id: str, limit: int = 100) -> List[Dict]:
        """Get latest trades"""
        endpoint = f"trades/{symbol_id}/latest"
        params = {'limit': limit}
        data = self._request(endpoint, params)
        return data if data else []

    def get_trades_history(
        self,
        symbol_id: str,
        time_start: str | None = None,
        time_end: str | None = None,
        limit: int = 10000,
    ) -> List[Dict]:
        """Get historical trades (CoinAPI /trades/{symbol_id}/history)."""
        endpoint = f"trades/{symbol_id}/history"
        params: Dict[str, Any] = {'limit': limit}
        if time_start:
            params['time_start'] = time_start
        if time_end:
            params['time_end'] = time_end
        data = self._request(endpoint, params)
        return data if data else []

    def get_assets(self) -> List[Dict]:
        """Get the full CoinAPI assets registry."""
        data = self._request("assets")
        return data if data else []

    def get_symbols(self) -> List[Dict]:
        """Get the full CoinAPI symbols registry."""
        data = self._request("symbols")
        return data if data else []


class AnomalyDetector:
    """
    Detects anomalies in CoinAPI data and uses them to refine algorithms.
    """
    
    def __init__(self, coinapi_client: CoinAPIClient):
        self.client = coinapi_client
        
        # Anomaly storage
        self.detected_anomalies: deque = deque(maxlen=1000)
        self.anomaly_history: Dict[str, List[MarketAnomaly]] = {}
        
        # Statistical baselines
        self.price_baselines: Dict[str, deque] = {}
        self.volume_baselines: Dict[str, deque] = {}
        self.spread_baselines: Dict[str, deque] = {}
        
        # Cross-exchange tracking
        self.multi_exchange_cache: Dict[str, List[ExchangeDataPoint]] = {}
        
        # Algorithm refinement metrics
        self.refinement_log: List[Dict] = []
        
    def fetch_multi_exchange_data(self, base_asset: str, quote_asset: str) -> List[ExchangeDataPoint]:
        """
        Fetch price data from multiple exchanges for the same pair.
        This is where we find discrepancies and the "real story".
        """
        data_points = []
        
        # Try to get quotes for this pair across exchanges
        symbol_filter = f"*_{base_asset}_{quote_asset}"
        quotes = self.client.get_quotes_current(symbol_filter)
        
        for quote in quotes:
            try:
                exchange_id = quote.get('symbol_id', '').split('_')[0]
                price = float(quote.get('ask', 0))
                bid = float(quote.get('bid', 0))
                ask = float(quote.get('ask', 0))
                timestamp = datetime.fromisoformat(quote.get('time_exchange', '').replace('Z', '+00:00'))
                
                if price > 0 and bid > 0 and ask > 0:
                    data_points.append(ExchangeDataPoint(
                        exchange_id=exchange_id,
                        symbol=f"{base_asset}/{quote_asset}",
                        price=price,
                        volume_24h=0,  # Would need separate query
                        bid=bid,
                        ask=ask,
                        timestamp=timestamp,
                    ))
            except:
                continue
        
        # Cache for later analysis
        key = f"{base_asset}_{quote_asset}"
        self.multi_exchange_cache[key] = data_points
        
        return data_points
    
    def detect_price_manipulation(self, data_points: List[ExchangeDataPoint]) -> List[MarketAnomaly]:
        """
        Detect price manipulation by comparing prices across exchanges.
        Large discrepancies indicate manipulation or wash trading.
        """
        if len(data_points) < 2:
            return []
        
        anomalies = []
        prices = [dp.price for dp in data_points]
        mean_price = statistics.mean(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else 0
        
        for dp in data_points:
            deviation = abs(dp.price - mean_price) / mean_price if mean_price > 0 else 0
            
            if deviation > ANOMALY_THRESHOLDS['PRICE_SPREAD']:
                severity = min(1.0, deviation / (ANOMALY_THRESHOLDS['PRICE_SPREAD'] * 2))
                confidence = 0.7 + (0.3 * min(1.0, len(data_points) / 10))
                
                anomaly = MarketAnomaly(
                    anomaly_type=AnomalyType.PRICE_MANIPULATION,
                    symbol=dp.symbol,
                    exchange=dp.exchange_id,
                    timestamp=dp.timestamp,
                    severity=severity,
                    confidence=confidence,
                    description=f"Price {deviation:.1%} away from cross-exchange mean",
                    evidence={
                        'exchange_price': dp.price,
                        'mean_price': mean_price,
                        'std_dev': std_price,
                        'num_exchanges': len(data_points),
                    },
                    recommendation="AVOID" if severity > 0.5 else "CAUTION",
                    expected_value=mean_price,
                    actual_value=dp.price,
                    deviation_pct=deviation * 100,
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    def detect_orderbook_spoofing(self, symbol_id: str) -> Optional[MarketAnomaly]:
        """
        Detect orderbook spoofing by analyzing bid/ask imbalance.
        """
        orderbook = self.client.get_orderbook_current(symbol_id)
        if not orderbook:
            return None
        
        try:
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                return None
            
            # Calculate total volume on each side
            bid_volume = sum(float(b.get('size', 0)) for b in bids[:10])
            ask_volume = sum(float(a.get('size', 0)) for a in asks[:10])
            total_volume = bid_volume + ask_volume
            
            if total_volume == 0:
                return None
            
            bid_ratio = bid_volume / total_volume
            
            # Check for extreme imbalance (spoofing indicator)
            if bid_ratio > ANOMALY_THRESHOLDS['ORDERBOOK_IMBALANCE'] or bid_ratio < (1 - ANOMALY_THRESHOLDS['ORDERBOOK_IMBALANCE']):
                severity = abs(bid_ratio - 0.5) * 2  # Scale to 0-1
                
                return MarketAnomaly(
                    anomaly_type=AnomalyType.ORDERBOOK_SPOOFING,
                    symbol=symbol_id,
                    exchange=symbol_id.split('_')[0],
                    timestamp=datetime.now(),
                    severity=severity,
                    confidence=0.75,
                    description=f"Orderbook imbalance: {bid_ratio:.0%} bids vs {1-bid_ratio:.0%} asks",
                    evidence={
                        'bid_volume': bid_volume,
                        'ask_volume': ask_volume,
                        'bid_ratio': bid_ratio,
                        'top_bid': bids[0] if bids else None,
                        'top_ask': asks[0] if asks else None,
                    },
                    recommendation="WAIT" if severity > 0.6 else "CAUTION",
                    expected_value=0.5,
                    actual_value=bid_ratio,
                    deviation_pct=(bid_ratio - 0.5) * 200,
                )
        except:
            return None
    
    def detect_wash_trading(self, symbol_id: str) -> Optional[MarketAnomaly]:
        """
        Detect wash trading by analyzing trade patterns.
        Circular trades at similar prices indicate wash trading.
        """
        trades = self.client.get_trades_latest(symbol_id, limit=100)
        if len(trades) < 10:
            return None
        
        try:
            # Look for repeated prices and volumes
            prices = [float(t.get('price', 0)) for t in trades]
            volumes = [float(t.get('size', 0)) for t in trades]
            
            # Count price repetitions
            price_counts = {}
            for p in prices:
                rounded = round(p, 8)
                price_counts[rounded] = price_counts.get(rounded, 0) + 1
            
            max_repetitions = max(price_counts.values())
            repetition_ratio = max_repetitions / len(prices)
            
            if repetition_ratio > ANOMALY_THRESHOLDS['WASH_TRADE_RATIO']:
                return MarketAnomaly(
                    anomaly_type=AnomalyType.WASH_TRADING,
                    symbol=symbol_id,
                    exchange=symbol_id.split('_')[0],
                    timestamp=datetime.now(),
                    severity=repetition_ratio,
                    confidence=0.65,
                    description=f"{repetition_ratio:.0%} of trades at identical prices",
                    evidence={
                        'max_repetitions': max_repetitions,
                        'total_trades': len(trades),
                        'repetition_ratio': repetition_ratio,
                        'unique_prices': len(price_counts),
                    },
                    recommendation="AVOID",
                    expected_value=0.1,
                    actual_value=repetition_ratio,
                    deviation_pct=(repetition_ratio - 0.1) * 100,
                )
        except:
            return None
    
    def detect_cross_exchange_arbitrage(self, data_points: List[ExchangeDataPoint]) -> List[MarketAnomaly]:
        """
        Detect arbitrage opportunities from price discrepancies.
        These reveal the "real" price vs manipulated prices.
        """
        if len(data_points) < 2:
            return []
        
        anomalies = []
        
        # Find min and max prices
        sorted_points = sorted(data_points, key=lambda x: x.price)
        min_dp = sorted_points[0]
        max_dp = sorted_points[-1]
        
        spread_pct = (max_dp.price - min_dp.price) / min_dp.price if min_dp.price > 0 else 0
        
        if spread_pct > ANOMALY_THRESHOLDS['PRICE_SPREAD']:
            # This is an arbitrage opportunity
            anomaly = MarketAnomaly(
                anomaly_type=AnomalyType.CROSS_EXCHANGE_SPREAD,
                symbol=min_dp.symbol,
                exchange=f"{min_dp.exchange_id}→{max_dp.exchange_id}",
                timestamp=datetime.now(),
                severity=min(1.0, spread_pct / 0.05),
                confidence=0.9,
                description=f"{spread_pct:.2%} arbitrage spread between exchanges",
                evidence={
                    'buy_exchange': min_dp.exchange_id,
                    'buy_price': min_dp.price,
                    'sell_exchange': max_dp.exchange_id,
                    'sell_price': max_dp.price,
                    'profit_pct': spread_pct * 100,
                },
                recommendation="ARBITRAGE OPPORTUNITY",
                expected_value=min_dp.price,
                actual_value=max_dp.price,
                deviation_pct=spread_pct * 100,
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def refine_algorithm(self, anomaly: MarketAnomaly) -> Dict[str, Any]:
        """
        Use detected anomaly to refine our trading algorithms.
        Returns refinement recommendations.
        """
        refinement = {
            'timestamp': datetime.now().isoformat(),
            'anomaly_type': anomaly.anomaly_type.value,
            'symbol': anomaly.symbol,
            'adjustment': {},
        }
        
        if anomaly.anomaly_type == AnomalyType.PRICE_MANIPULATION:
            # Increase coherence threshold for this symbol
            refinement['adjustment'] = {
                'coherence_threshold': '+0.1',
                'position_size': '×0.5',
                'reason': 'Price manipulation detected - require higher confidence',
            }
        
        elif anomaly.anomaly_type == AnomalyType.WASH_TRADING:
            # Blacklist symbol temporarily
            refinement['adjustment'] = {
                'blacklist_duration': '1h',
                'position_size': '×0.0',
                'reason': 'Wash trading detected - avoid completely',
            }
        
        elif anomaly.anomaly_type == AnomalyType.ORDERBOOK_SPOOFING:
            # Wait for orderbook to stabilize
            refinement['adjustment'] = {
                'entry_delay': '+60s',
                'position_size': '×0.7',
                'reason': 'Orderbook spoofing - wait for real liquidity',
            }
        
        elif anomaly.anomaly_type == AnomalyType.CROSS_EXCHANGE_SPREAD:
            # Use mean price instead of single exchange
            refinement['adjustment'] = {
                'price_source': 'multi_exchange_mean',
                'position_size': '×1.2',
                'reason': 'Arbitrage opportunity - use aggregated price',
            }
        
        elif anomaly.anomaly_type == AnomalyType.LATENCY_ARBITRAGE:
            # Adjust for latency
            refinement['adjustment'] = {
                'latency_compensation': f'+{anomaly.evidence.get("latency_ms", 0)}ms',
                'position_size': '×0.8',
                'reason': 'High latency detected - adjust timing',
            }
        
        # Log refinement
        self.refinement_log.append(refinement)
        
        return refinement
    
    def analyze_symbol(self, base_asset: str, quote_asset: str) -> Dict[str, Any]:
        """
        Complete anomaly analysis for a symbol.
        Returns all detected anomalies and refinement recommendations.
        """
        print(f"\n🔍 Analyzing {base_asset}/{quote_asset} across exchanges...")
        
        # Fetch multi-exchange data
        data_points = self.fetch_multi_exchange_data(base_asset, quote_asset)
        
        if not data_points:
            print("   ⚠️  No data available")
            return {'anomalies': [], 'refinements': []}
        
        print(f"   📊 Found data from {len(data_points)} exchanges")
        
        all_anomalies = []
        all_refinements = []
        
        # Detect price manipulation
        price_anomalies = self.detect_price_manipulation(data_points)
        all_anomalies.extend(price_anomalies)
        
        # Detect arbitrage opportunities
        arb_anomalies = self.detect_cross_exchange_arbitrage(data_points)
        all_anomalies.extend(arb_anomalies)
        
        # Store anomalies
        for anomaly in all_anomalies:
            self.detected_anomalies.append(anomaly)
            
            # Refine algorithm based on anomaly
            refinement = self.refine_algorithm(anomaly)
            all_refinements.append(refinement)
        
        return {
            'symbol': f"{base_asset}/{quote_asset}",
            'exchanges_analyzed': len(data_points),
            'anomalies': [a.to_dict() for a in all_anomalies],
            'refinements': all_refinements,
            'mean_price': statistics.mean([dp.price for dp in data_points]) if data_points else 0,
            'price_std': statistics.stdev([dp.price for dp in data_points]) if len(data_points) > 1 else 0,
        }
    
    def print_anomaly_report(self, analysis: Dict):
        """Print formatted anomaly report"""
        print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌍⚡ COINAPI ANOMALY REPORT: {analysis['symbol']:20s}            ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Exchanges Analyzed: {analysis['exchanges_analyzed']:2d}                                               ║
║  Mean Price: ${analysis['mean_price']:.6f}                                           ║
║  Price StdDev: ${analysis['price_std']:.6f}                                         ║
╠══════════════════════════════════════════════════════════════════════════╣""")
        
        if analysis['anomalies']:
            print("║  DETECTED ANOMALIES:                                                     ║")
            print("╠══════════════════════════════════════════════════════════════════════════╣")
            
            for i, anom in enumerate(analysis['anomalies'][:5], 1):
                severity_bar = "█" * int(anom['severity'] * 10) + "░" * (10 - int(anom['severity'] * 10))
                print(f"║  {i}. {anom['type']:30s}                                  ║")
                print(f"║     Severity: {severity_bar} {anom['severity']:.0%}                               ║")
                print(f"║     {anom['description'][:68]:68s} ║")
                print(f"║     → {anom['recommendation']:64s} ║")
                print("╠══════════════════════════════════════════════════════════════════════════╣")
        else:
            print("║  ✅ No anomalies detected - data looks clean                             ║")
            print("╠══════════════════════════════════════════════════════════════════════════╣")
        
        if analysis['refinements']:
            print("║  ALGORITHM REFINEMENTS:                                                  ║")
            print("╠══════════════════════════════════════════════════════════════════════════╣")
            
            for i, ref in enumerate(analysis['refinements'][:3], 1):
                adj = ref['adjustment']
                print(f"║  {i}. {adj.get('reason', 'No reason')[:68]:68s} ║")
                for key, value in adj.items():
                    if key != 'reason':
                        print(f"║     • {key}: {str(value)[:58]:58s} ║")
                print("╠══════════════════════════════════════════════════════════════════════════╣")
        
        print("╚══════════════════════════════════════════════════════════════════════════╝")


# ═══════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════

def demo_anomaly_detection():
    """Demonstrate the anomaly detection system"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌍⚡ COINAPI ANOMALY DETECTOR DEMONSTRATION ⚡🌍                        ║
║  Cross-Exchange Analysis & Algorithm Refinement                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    api_key = os.getenv('COINAPI_KEY')
    if not api_key:
        print("""
⚠️  No CoinAPI key found!
   
To use this feature:
1. Get free API key from https://www.coinapi.io/
2. Add to .env file: COINAPI_KEY=your-key-here
3. Free tier: 100 requests/day

For now, showing demo with simulated data...
""")
        # Simulate some data for demo
        return demo_with_simulated_data()
    
    # Real API test
    client = CoinAPIClient(api_key)
    detector = AnomalyDetector(client)
    
    # Analyze popular pairs
    test_pairs = [
        ('BTC', 'USD'),
        ('ETH', 'USD'),
        ('BNB', 'USD'),
    ]
    
    for base, quote in test_pairs:
        try:
            analysis = detector.analyze_symbol(base, quote)
            detector.print_anomaly_report(analysis)
            time.sleep(1)
        except Exception as e:
            print(f"   ⚠️  Analysis failed for {base}/{quote}: {e}")
    
    print("\n✨ Anomaly Detection Complete!")
    print(f"📊 Total Anomalies Detected: {len(detector.detected_anomalies)}")
    print(f"🔧 Algorithm Refinements Made: {len(detector.refinement_log)}")


def demo_with_simulated_data():
    """Demo with simulated data when no API key"""
    print("\n🎭 Running with simulated data...\n")
    
    # Simulate anomalies
    simulated_analysis = {
        'symbol': 'BTC/USD',
        'exchanges_analyzed': 5,
        'mean_price': 69420.50,
        'price_std': 350.25,
        'anomalies': [
            {
                'type': '💰 Price Manipulation',
                'severity': 0.75,
                'description': 'Price 4.2% away from cross-exchange mean',
                'recommendation': 'AVOID',
                'exchange': 'EXCHANGE_X',
            },
            {
                'type': '🌐 Cross-Exchange Spread',
                'severity': 0.45,
                'description': '2.8% arbitrage spread between exchanges',
                'recommendation': 'ARBITRAGE OPPORTUNITY',
                'exchange': 'BINANCE→KRAKEN',
            },
        ],
        'refinements': [
            {
                'adjustment': {
                    'coherence_threshold': '+0.1',
                    'position_size': '×0.5',
                    'reason': 'Price manipulation detected - require higher confidence',
                }
            },
            {
                'adjustment': {
                    'price_source': 'multi_exchange_mean',
                    'position_size': '×1.2',
                    'reason': 'Arbitrage opportunity - use aggregated price',
                }
            },
        ],
    }
    
    # Create detector just for printing
    client = CoinAPIClient('')
    detector = AnomalyDetector(client)
    detector.print_anomaly_report(simulated_analysis)
    
    print("\n✨ Simulated Demo Complete!")


if __name__ == "__main__":
    demo_anomaly_detection()
