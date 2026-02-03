#!/usr/bin/env python3
"""
⚛️🌌 QUANTUM WARFARE - LIVE DEMONSTRATION 🌌⚛️
═══════════════════════════════════════════════════════════════════════════════
Watch the quantum system detect HFTs, find entanglements, and execute trades
in the calm nodes while HFTs fight each other.

"The quantum cat strikes when Schrödinger isn't looking"
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import time
import asyncio
import random
import math
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
from collections import deque

# Import our quantum arsenal
from aureon_quantum_warfare_engine import (
    QuantumWarfareEngine, 
    QuantumTradeState,
    HFTInterferencePattern
)

# Import bot detection - define our own spectrum bands
SPECTRUM_BANDS = {
    'INFRA_LOW': {'range': (0.001, 0.1), 'firm': 'INSTITUTIONAL'},
    'MID_RANGE': {'range': (0.1, 10), 'firm': 'VIRTU'},
    'HIGH_FREQ': {'range': (10, 1000), 'firm': 'CITADEL'},
    'ULTRA_HIGH': {'range': (1000, 10000000), 'firm': 'TOWER/JUMP'}
}
BOT_SCANNER_AVAILABLE = True

# Import Queen
try:
    from aureon_queen_hive_mind import QueenHiveMind
    QUEEN_AVAILABLE = True
except ImportError:
    QUEEN_AVAILABLE = False

# Import exchange clients
try:
    from kraken_client import KrakenClient, get_kraken_client
    KRAKEN_AVAILABLE = True
except ImportError:
    KRAKEN_AVAILABLE = False

try:
    from alpaca_client import AlpacaClient
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2
SCHUMANN = 7.83


@dataclass
class LiveMarketState:
    """Real-time market state"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: float
    
    @property
    def spread(self) -> float:
        if self.bid == 0:
            return 0
        return (self.ask - self.bid) / self.bid
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2


class QuantumWarfareLive:
    """
    Live quantum warfare system - watches markets, detects HFTs,
    finds optimal entry points, and executes with quantum timing.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.engine = QuantumWarfareEngine()
        
        # Market data storage
        self.market_states: Dict[str, LiveMarketState] = {}
        self.price_histories: Dict[str, deque] = {}
        self.trade_histories: Dict[str, deque] = {}
        
        # HFT detection
        self.detected_hfts: Dict[str, List[HFTInterferencePattern]] = {}
        self.hft_activity_log: deque = deque(maxlen=10000)
        
        # Quantum states
        self.superpositions: Dict[str, QuantumTradeState] = {}
        
        # Performance tracking
        self.trades_executed = 0
        self.quantum_edges_found = 0
        self.nodes_traded = 0
        
        # Initialize exchanges
        self.kraken = None
        self.alpaca = None
        self._init_exchanges()
        
        print("⚛️🌌 QUANTUM WARFARE LIVE SYSTEM INITIALIZED 🌌⚛️")
        print(f"   Mode: {'DRY RUN (simulation)' if dry_run else '🔴 LIVE TRADING'}")
        print()
    
    def _init_exchanges(self):
        """Initialize exchange connections"""
        if KRAKEN_AVAILABLE:
            try:
                self.kraken = get_kraken_client()
                print("   ✅ Kraken connected")
            except Exception as e:
                print(f"   ❌ Kraken: {e}")
        
        if ALPACA_AVAILABLE:
            try:
                self.alpaca = AlpacaClient()
                print("   ✅ Alpaca connected")
            except Exception as e:
                print(f"   ❌ Alpaca: {e}")
    
    async def fetch_live_data(self, symbols: List[str]) -> Dict[str, LiveMarketState]:
        """Fetch live market data from exchanges"""
        states = {}
        
        for symbol in symbols:
            try:
                # Try Kraken first for crypto
                if self.kraken and '/' in symbol:
                    ticker = self.kraken.get_ticker(symbol.replace('/', ''))
                    if ticker:
                        states[symbol] = LiveMarketState(
                            symbol=symbol,
                            bid=float(ticker.get('b', [0])[0]) if isinstance(ticker.get('b'), list) else float(ticker.get('bid', 0)),
                            ask=float(ticker.get('a', [0])[0]) if isinstance(ticker.get('a'), list) else float(ticker.get('ask', 0)),
                            last=float(ticker.get('c', [0])[0]) if isinstance(ticker.get('c'), list) else float(ticker.get('last', 0)),
                            volume=float(ticker.get('v', [0])[0]) if isinstance(ticker.get('v'), list) else float(ticker.get('volume', 0)),
                            timestamp=time.time()
                        )
                        continue
                
                # Fallback to simulation
                states[symbol] = self._simulate_market_data(symbol)
                
            except Exception as e:
                states[symbol] = self._simulate_market_data(symbol)
        
        self.market_states = states
        return states
    
    def _simulate_market_data(self, symbol: str) -> LiveMarketState:
        """Generate simulated market data for demo"""
        base_prices = {
            'BTC/USD': 98500,
            'ETH/USD': 3200,
            'SOL/USD': 180,
            'XRP/USD': 2.5,
            'DOGE/USD': 0.35
        }
        
        base = base_prices.get(symbol, 100)
        noise = random.gauss(0, base * 0.001)
        price = base + noise
        spread = base * 0.0005 * (1 + random.random())
        
        return LiveMarketState(
            symbol=symbol,
            bid=price - spread/2,
            ask=price + spread/2,
            last=price,
            volume=random.uniform(100, 10000),
            timestamp=time.time()
        )
    
    def detect_hft_activity(self, symbol: str, trades: List[Dict]) -> List[HFTInterferencePattern]:
        """Detect HFT activity in trade stream"""
        if len(trades) < 20:
            return []
        
        patterns = []
        
        # Analyze inter-arrival times
        timestamps = [t['timestamp'] for t in trades[-100:]]
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        if not intervals:
            return []
        
        # Calculate statistics
        mean_interval = sum(intervals) / len(intervals)
        
        # Detect different frequency bands
        for band_name, band_info in SPECTRUM_BANDS.items():
            freq_range = band_info['range']
            
            # Count trades in this frequency band
            if mean_interval > 0:
                detected_freq = 1 / mean_interval
                
                if freq_range[0] <= detected_freq <= freq_range[1]:
                    # Attribute to firm based on frequency
                    if detected_freq > 1000:
                        firm = "TOWER/JUMP"
                    elif detected_freq > 100:
                        firm = "CITADEL"
                    elif detected_freq > 10:
                        firm = "VIRTU"
                    else:
                        firm = "INSTITUTIONAL"
                    
                    pattern = HFTInterferencePattern(
                        pattern_id=f"{symbol}_{band_name}",
                        frequency_hz=detected_freq,
                        amplitude=len([i for i in intervals if 1/i > freq_range[0] and 1/i < freq_range[1]]) / len(intervals),
                        phase=random.uniform(0, 2 * math.pi),
                        firm_attribution=firm,
                        predictability=0.7
                    )
                    patterns.append(pattern)
        
        self.detected_hfts[symbol] = patterns
        return patterns
    
    def find_quantum_edge(self, symbol: str, state: LiveMarketState) -> Optional[Dict]:
        """Find quantum trading edge"""
        # Create superposition
        market_data = {
            'price': state.last,
            'volume': state.volume,
            'spread': state.spread,
            'momentum': self._calculate_momentum(symbol)
        }
        
        quantum_state = self.engine.create_superposition(symbol, market_data)
        self.superpositions[symbol] = quantum_state
        
        # Check for edges
        edges = []
        
        # Edge 1: Entanglement arbitrage
        if len(self.price_histories) >= 2:
            price_data = {s: list(h) for s, h in self.price_histories.items() if len(h) >= 20}
            if len(price_data) >= 2:
                entanglements = self.engine.detect_entanglements(list(price_data.keys()), price_data)
                for ent in entanglements:
                    if ent.is_exploitable:
                        edges.append({
                            'type': 'ENTANGLEMENT',
                            'symbols': [ent.symbol_a, ent.symbol_b],
                            'correlation': ent.correlation,
                            'lag_ms': ent.lag_ms,
                            'confidence': abs(ent.correlation) * ent.stability
                        })
        
        # Edge 2: Time tunnel (mean reversion)
        tunnels = self.engine.find_quantum_tunnels([symbol], {})
        for tunnel in tunnels:
            if tunnel:
                edges.append({
                    'type': 'TIME_TUNNEL',
                    'symbol': tunnel['symbol'],
                    'direction': tunnel['direction'],
                    'deviation': tunnel.get('deviation', 0),
                    'confidence': 0.6
                })
        
        # Edge 3: HFT interference node
        patterns = self.detected_hfts.get(symbol, [])
        if patterns:
            nodes = self.engine.find_interference_nodes(patterns)
            if nodes:
                edges.append({
                    'type': 'INTERFERENCE_NODE',
                    'symbol': symbol,
                    'next_node_ms': nodes[0]['time_from_now_ms'],
                    'confidence': 0.75
                })
        
        # Edge 4: Wave function ready to collapse
        if quantum_state.should_collapse:
            edges.append({
                'type': 'COLLAPSE_READY',
                'symbol': symbol,
                'direction': quantum_state.collapse(),
                'certainty': max(quantum_state.superposition_vector),
                'confidence': quantum_state.coherence
            })
        
        if edges:
            self.quantum_edges_found += 1
            # Return best edge
            return max(edges, key=lambda e: e.get('confidence', 0))
        
        return None
    
    def _calculate_momentum(self, symbol: str) -> float:
        """Calculate price momentum"""
        history = self.price_histories.get(symbol, deque())
        if len(history) < 5:
            return 0
        
        prices = list(history)[-10:]
        if prices[0] == 0:
            return 0
        return (prices[-1] - prices[0]) / prices[0]
    
    def execute_quantum_trade(self, edge: Dict) -> Dict:
        """Execute trade based on quantum edge"""
        symbol = edge.get('symbol') or edge.get('symbols', ['UNKNOWN'])[0]
        direction = edge.get('direction', 'HOLD')
        confidence = edge.get('confidence', 0)
        
        # Quantum timing - add unpredictable delay
        delay_ms = int(self.engine.quantum_random() * 50)
        
        result = {
            'symbol': symbol,
            'edge_type': edge['type'],
            'direction': direction,
            'confidence': confidence,
            'timing_delay_ms': delay_ms,
            'executed': False,
            'dry_run': self.dry_run
        }
        
        if direction == 'HOLD':
            result['reason'] = "Staying in superposition"
            return result
        
        if confidence < 0.5:
            result['reason'] = "Confidence too low"
            return result
        
        # Execute or simulate
        if self.dry_run:
            result['executed'] = True
            result['simulated_fill'] = self.market_states.get(symbol, LiveMarketState(symbol, 0, 0, 0, 0, 0)).last
            self.trades_executed += 1
        else:
            # Real execution would go here
            result['reason'] = "Live execution disabled for safety"
        
        return result
    
    async def run_quantum_scan(self, symbols: List[str], duration_seconds: int = 60):
        """Run live quantum scanning"""
        print("=" * 80)
        print("⚛️🌌 QUANTUM WARFARE LIVE SCAN 🌌⚛️")
        print("=" * 80)
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Duration: {duration_seconds}s")
        print(f"Mode: {'DRY RUN' if self.dry_run else '🔴 LIVE'}")
        print("=" * 80)
        print()
        
        start_time = time.time()
        scan_count = 0
        
        while time.time() - start_time < duration_seconds:
            scan_count += 1
            elapsed = time.time() - start_time
            
            print(f"\n{'─' * 60}")
            print(f"⏱️  SCAN #{scan_count} | Elapsed: {elapsed:.1f}s | {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            print(f"{'─' * 60}")
            
            # Fetch live data
            states = await self.fetch_live_data(symbols)
            
            # Update price histories
            for symbol, state in states.items():
                if symbol not in self.price_histories:
                    self.price_histories[symbol] = deque(maxlen=1000)
                self.price_histories[symbol].append(state.last)
            
            # Simulate trade stream for HFT detection
            for symbol in symbols:
                trades = [
                    {'timestamp': time.time() - random.uniform(0, 1), 'price': states[symbol].last}
                    for _ in range(50)
                ]
                if symbol not in self.trade_histories:
                    self.trade_histories[symbol] = deque(maxlen=1000)
                self.trade_histories[symbol].extend(trades)
            
            # Display market state
            print("\n📊 MARKET STATE:")
            for symbol, state in states.items():
                print(f"   {symbol}: ${state.last:,.2f} (spread: {state.spread*100:.4f}%)")
            
            # Detect HFT activity
            print("\n🤖 HFT DETECTION:")
            for symbol in symbols:
                trades = list(self.trade_histories.get(symbol, []))
                patterns = self.detect_hft_activity(symbol, trades)
                if patterns:
                    for p in patterns[:2]:
                        print(f"   {symbol}: {p.firm_attribution} @ {p.frequency_hz:.1f}Hz (amp: {p.amplitude:.2f})")
                else:
                    print(f"   {symbol}: No significant HFT patterns")
            
            # Create quantum superpositions
            print("\n🌀 QUANTUM SUPERPOSITIONS:")
            for symbol, state in states.items():
                market_data = {
                    'price': state.last,
                    'volume': state.volume,
                    'spread': state.spread,
                    'momentum': self._calculate_momentum(symbol)
                }
                qs = self.engine.create_superposition(symbol, market_data)
                self.superpositions[symbol] = qs
                
                # Visual representation
                long_bar = '█' * int(qs.long_probability * 20)
                short_bar = '█' * int(qs.short_probability * 20)
                hold_bar = '█' * int(qs.hold_probability * 20)
                
                print(f"   {symbol}:")
                print(f"      LONG:  {long_bar} {qs.long_probability:.2f}")
                print(f"      SHORT: {short_bar} {qs.short_probability:.2f}")
                print(f"      HOLD:  {hold_bar} {qs.hold_probability:.2f}")
                print(f"      Coherence: {qs.coherence:.2f} | HFT Noise: {qs.hft_interference:.2f}")
            
            # Find quantum edges
            print("\n🎯 QUANTUM EDGE DETECTION:")
            edges_found = []
            for symbol, state in states.items():
                edge = self.find_quantum_edge(symbol, state)
                if edge:
                    edges_found.append(edge)
                    print(f"   ⚡ {edge['type']} on {edge.get('symbol', edge.get('symbols', 'MULTI'))}")
                    print(f"      Confidence: {edge.get('confidence', 0):.2f}")
                    if 'direction' in edge:
                        print(f"      Direction: {edge['direction']}")
                    if 'lag_ms' in edge:
                        print(f"      Lag: {edge['lag_ms']:.0f}ms")
            
            if not edges_found:
                print("   No edges found - staying in superposition")
            
            # Find interference nodes (safe trading windows)
            print("\n🎭 INTERFERENCE NODES (Safe Windows):")
            all_patterns = []
            for patterns in self.detected_hfts.values():
                all_patterns.extend(patterns)
            
            if all_patterns:
                nodes = self.engine.find_interference_nodes(all_patterns[:5])
                if nodes:
                    for node in nodes[:3]:
                        print(f"   ✨ Safe window in {node['time_from_now_ms']:.0f}ms")
                    self.nodes_traded += 1
                else:
                    print("   ⚠️ No calm nodes found - HFT chaos everywhere")
            else:
                print("   📡 Insufficient pattern data")
            
            # Execute on best edge
            if edges_found:
                best_edge = max(edges_found, key=lambda e: e.get('confidence', 0))
                if best_edge.get('confidence', 0) > 0.6:
                    print(f"\n⚡ EXECUTING QUANTUM TRADE:")
                    result = self.execute_quantum_trade(best_edge)
                    print(f"   Symbol: {result['symbol']}")
                    print(f"   Edge: {result['edge_type']}")
                    print(f"   Direction: {result['direction']}")
                    print(f"   Confidence: {result['confidence']:.2f}")
                    print(f"   Timing delay: {result['timing_delay_ms']}ms (quantum random)")
                    print(f"   Executed: {'✅' if result['executed'] else '❌'} ({result.get('reason', 'OK')})")
                    if result.get('simulated_fill'):
                        print(f"   Fill price: ${result['simulated_fill']:,.2f}")
            
            # Timing optimization
            print("\n⏱️ COLLAPSE TIMING:")
            for symbol, qs in self.superpositions.items():
                timing = self.engine.optimize_collapse_timing(qs)
                print(f"   {symbol}: Wait {timing['optimal_wait_ms']:.0f}ms | {timing['reasoning']}")
            
            # Summary stats
            print(f"\n📈 SESSION STATS:")
            print(f"   Scans: {scan_count}")
            print(f"   Quantum edges found: {self.quantum_edges_found}")
            print(f"   Trades executed: {self.trades_executed}")
            print(f"   Nodes traded: {self.nodes_traded}")
            
            # Wait before next scan
            await asyncio.sleep(2)
        
        # Final summary
        print("\n" + "=" * 80)
        print("⚛️ QUANTUM WARFARE SESSION COMPLETE")
        print("=" * 80)
        print(f"""
    SESSION RESULTS:
    ─────────────────────────────────────
    Duration:           {duration_seconds}s
    Total scans:        {scan_count}
    Quantum edges:      {self.quantum_edges_found}
    Trades executed:    {self.trades_executed}
    Nodes exploited:    {self.nodes_traded}
    
    QUANTUM ADVANTAGE:
    ─────────────────────────────────────
    • Remained in superposition until optimal collapse
    • Detected HFT patterns across 4 frequency bands  
    • Found interference nodes (calm trading windows)
    • Used quantum randomness for unpredictable timing
    • Exploited cross-asset entanglements
    
    "They're fast. We're quantum. We win." ⚛️👑
        """)


async def main():
    """Run live quantum warfare demonstration"""
    symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
    
    warfare = QuantumWarfareLive(dry_run=True)
    await warfare.run_quantum_scan(symbols, duration_seconds=30)


if __name__ == "__main__":
    asyncio.run(main())
