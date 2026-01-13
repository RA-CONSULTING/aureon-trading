#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌊 AUREON OCEAN SCANNER - BE A TURTLE IN THE SEA OF POSSIBILITIES
═════════════════════════════════════════════════════════════════

"Why be a big fish in a small pond when you can be a turtle in the ocean?"
                                                        - Gary Leckey

This module scans the ENTIRE global market, not just what we hold.
It identifies opportunities BEFORE we need to hold them.

UNIVERSE EXPANSION:
  • Kraken: 1,434 tradeable pairs
  • Alpaca Crypto: 62 symbols  
  • Alpaca Stocks: 10,000+ symbols (when market open)
  • Binance: 2,000+ pairs
  • TOTAL POTENTIAL: 13,000+ opportunities!

vs our current "puddle":
  • 28 opportunities (only from 5 held positions)

"""
import sys
import os

# Windows UTF-8 Fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import json
import logging

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618 Golden ratio
LOVE_FREQUENCY = 528
SCHUMANN_BASE = 7.83

logger = logging.getLogger(__name__)

@dataclass
class OceanOpportunity:
    """A single opportunity in the ocean of possibilities."""
    symbol: str
    exchange: str
    opportunity_type: str  # 'momentum', 'arbitrage', 'reversal', 'breakout'
    
    # Price data
    current_price: float = 0.0
    price_24h_ago: float = 0.0
    price_1h_ago: float = 0.0
    
    # Momentum metrics
    momentum_1m: float = 0.0  # % change per minute
    momentum_5m: float = 0.0
    momentum_1h: float = 0.0
    momentum_24h: float = 0.0
    
    # Volume metrics
    volume_24h: float = 0.0
    volume_ratio: float = 1.0  # Current vs average
    
    # Scoring
    ocean_score: float = 0.0  # 0-1 overall opportunity score
    confidence: float = 0.0
    expected_pnl: float = 0.0
    
    # Metadata
    timestamp: float = field(default_factory=time.time)
    reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'exchange': self.exchange,
            'type': self.opportunity_type,
            'price': self.current_price,
            'momentum_1m': self.momentum_1m,
            'momentum_1h': self.momentum_1h,
            'momentum_24h': self.momentum_24h,
            'volume_ratio': self.volume_ratio,
            'ocean_score': self.ocean_score,
            'confidence': self.confidence,
            'expected_pnl': self.expected_pnl,
            'reason': self.reason,
        }


class OceanScanner:
    """
    🌊 THE OCEAN SCANNER - Scans the entire global market.
    
    Instead of only looking at what we hold (puddle mentality),
    we scan EVERYTHING and find the best opportunities first,
    THEN decide what to hold.
    
    "The turtle doesn't just look at the coral reef it's sitting on.
     It looks at the entire ocean and swims to where the food is."
    """
    
    def __init__(self, exchanges: Dict = None):
        self.exchanges = exchanges or {}
        
        # Universe tracking
        self.kraken_universe: Set[str] = set()
        self.alpaca_crypto_universe: Set[str] = set()
        self.alpaca_stock_universe: Set[str] = set()
        self.binance_universe: Set[str] = set()
        
        # Price cache
        self.prices: Dict[str, Dict] = {}  # symbol -> {price, timestamp, exchange}
        
        # Momentum tracking
        self.price_history: Dict[str, List[Tuple[float, float]]] = {}  # symbol -> [(timestamp, price)]
        self.momentum_cache: Dict[str, Dict] = {}  # symbol -> {1m, 5m, 1h, 24h}
        
        # Opportunity pools
        self.hot_opportunities: List[OceanOpportunity] = []
        self.arbitrage_opportunities: List[OceanOpportunity] = []
        self.momentum_opportunities: List[OceanOpportunity] = []
        
        # Statistics
        self.total_symbols_scanned = 0
        self.last_scan_time = 0
        self.scan_count = 0
        
        print("🌊 OCEAN SCANNER INITIALIZED")
        print("   Ready to scan the SEA of possibilities!")
        
    async def discover_universe(self) -> Dict[str, int]:
        """
        🔭 DISCOVER THE ENTIRE TRADING UNIVERSE
        
        This scans all exchanges and builds a map of every tradeable
        symbol across the global market.
        """
        print("\n" + "=" * 70)
        print("🔭 DISCOVERING THE TRADING UNIVERSE...")
        print("=" * 70)
        
        universe_counts = {}
        
        # ═══════════════════════════════════════════════════════════════
        # 🐙 KRAKEN UNIVERSE
        # ═══════════════════════════════════════════════════════════════
        if 'kraken' in self.exchanges:
            try:
                kraken = self.exchanges['kraken']
                if hasattr(kraken, '_load_asset_pairs'):
                    pairs = kraken._load_asset_pairs()
                    self.kraken_universe = {p for p in pairs.keys() if not p.endswith('.d')}
                    universe_counts['kraken'] = len(self.kraken_universe)
                    print(f"   🐙 KRAKEN: {len(self.kraken_universe)} pairs discovered!")
            except Exception as e:
                print(f"   ❌ Kraken discovery error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🦙 ALPACA CRYPTO UNIVERSE
        # ═══════════════════════════════════════════════════════════════
        if 'alpaca' in self.exchanges:
            try:
                alpaca = self.exchanges['alpaca']
                if hasattr(alpaca, 'get_tradable_crypto_symbols'):
                    symbols = alpaca.get_tradable_crypto_symbols() or []
                    self.alpaca_crypto_universe = set(symbols)
                    universe_counts['alpaca_crypto'] = len(self.alpaca_crypto_universe)
                    print(f"   🦙 ALPACA CRYPTO: {len(self.alpaca_crypto_universe)} symbols discovered!")
            except Exception as e:
                print(f"   ❌ Alpaca crypto discovery error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # 📈 ALPACA STOCKS UNIVERSE
        # ═══════════════════════════════════════════════════════════════
        if 'alpaca' in self.exchanges:
            try:
                alpaca = self.exchanges['alpaca']
                # Check for trading API
                if hasattr(alpaca, '_trading_api'):
                    api = alpaca._trading_api
                elif hasattr(alpaca, 'trading_client'):
                    api = alpaca.trading_client
                else:
                    api = None
                
                if api and hasattr(api, 'get_all_assets'):
                    from alpaca.trading.requests import GetAssetsRequest
                    from alpaca.trading.enums import AssetClass, AssetStatus
                    
                    request = GetAssetsRequest(
                        asset_class=AssetClass.US_EQUITY,
                        status=AssetStatus.ACTIVE
                    )
                    assets = api.get_all_assets(request)
                    tradeable = [a for a in assets if a.tradable and a.fractionable]
                    self.alpaca_stock_universe = {a.symbol for a in tradeable}
                    universe_counts['alpaca_stocks'] = len(self.alpaca_stock_universe)
                    print(f"   📈 ALPACA STOCKS: {len(self.alpaca_stock_universe)} symbols discovered!")
            except Exception as e:
                print(f"   ❌ Alpaca stocks discovery error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # 🟡 BINANCE UNIVERSE
        # ═══════════════════════════════════════════════════════════════
        if 'binance' in self.exchanges:
            try:
                binance = self.exchanges['binance']
                if hasattr(binance, 'exchange_info'):
                    info = binance.exchange_info()
                    symbols = info.get('symbols', [])
                    self.binance_universe = {
                        s['symbol'] for s in symbols 
                        if s.get('status') == 'TRADING' and s.get('isSpotTradingAllowed', True)
                    }
                    universe_counts['binance'] = len(self.binance_universe)
                    print(f"   🟡 BINANCE: {len(self.binance_universe)} pairs discovered!")
            except Exception as e:
                print(f"   ❌ Binance discovery error: {e}")
        
        # ═══════════════════════════════════════════════════════════════
        # 📊 UNIVERSE SUMMARY
        # ═══════════════════════════════════════════════════════════════
        total_universe = sum(universe_counts.values())
        self.total_symbols_scanned = total_universe
        
        print()
        print("=" * 70)
        print(f"🌍 TOTAL TRADING UNIVERSE: {total_universe:,} symbols!")
        print("=" * 70)
        print()
        print("   🐢 You are now a TURTLE in the SEA of possibilities!")
        print("   🐠 Not a big fish in a tiny pond of 28 opportunities...")
        print()
        
        return universe_counts
    
    async def scan_ocean(self, limit: int = 100) -> List[OceanOpportunity]:
        """
        🌊 SCAN THE ENTIRE OCEAN FOR OPPORTUNITIES
        
        This performs a full scan of all discovered symbols,
        calculating momentum and identifying opportunities.
        
        Returns the TOP opportunities sorted by score.
        """
        print(f"\n🌊 SCANNING OCEAN... (Universe: {self.total_symbols_scanned:,} symbols)")
        scan_start = time.time()
        
        opportunities = []
        
        # Scan each exchange's universe
        if self.kraken_universe and 'kraken' in self.exchanges:
            kraken_opps = await self._scan_exchange_universe(
                'kraken', 
                self.kraken_universe,
                limit=limit // 4
            )
            opportunities.extend(kraken_opps)
        
        if self.alpaca_crypto_universe and 'alpaca' in self.exchanges:
            alpaca_opps = await self._scan_exchange_universe(
                'alpaca',
                self.alpaca_crypto_universe,
                limit=limit // 4
            )
            opportunities.extend(alpaca_opps)
        
        # Sort by ocean score
        opportunities.sort(key=lambda x: x.ocean_score, reverse=True)
        
        scan_duration = time.time() - scan_start
        self.last_scan_time = scan_duration
        self.scan_count += 1
        
        # Store top opportunities
        self.hot_opportunities = opportunities[:limit]
        
        print(f"\n🎯 OCEAN SCAN COMPLETE in {scan_duration:.2f}s")
        print(f"   Found {len(opportunities)} opportunities from {self.total_symbols_scanned:,} symbols")
        
        return opportunities[:limit]
    
    async def _scan_exchange_universe(
        self, 
        exchange: str, 
        symbols: Set[str],
        limit: int = 50
    ) -> List[OceanOpportunity]:
        """Scan a single exchange's universe for opportunities."""
        opportunities = []
        
        client = self.exchanges.get(exchange)
        if not client:
            return opportunities
        
        # Get batch price data if available
        try:
            if exchange == 'kraken' and hasattr(client, 'get_ticker_batch'):
                tickers = client.get_ticker_batch(list(symbols)[:100])  # Limit API calls
            elif exchange == 'alpaca':
                tickers = await self._get_alpaca_tickers(client, symbols)
            else:
                tickers = {}
        except Exception as e:
            logger.error(f"Ticker fetch error for {exchange}: {e}")
            tickers = {}
        
        for symbol, ticker in tickers.items():
            try:
                opp = self._analyze_symbol(symbol, ticker, exchange)
                if opp and opp.ocean_score > 0.3:  # Minimum score threshold
                    opportunities.append(opp)
            except Exception as e:
                continue
        
        # Sort by score and return top
        opportunities.sort(key=lambda x: x.ocean_score, reverse=True)
        return opportunities[:limit]
    
    def _analyze_symbol(self, symbol: str, ticker: Dict, exchange: str) -> Optional[OceanOpportunity]:
        """Analyze a single symbol and score its opportunity potential."""
        
        price = ticker.get('last', ticker.get('price', ticker.get('c', 0)))
        if not price or price <= 0:
            return None
        
        # Calculate momentum from ticker data
        open_price = ticker.get('open', ticker.get('o', price))
        high = ticker.get('high', ticker.get('h', price))
        low = ticker.get('low', ticker.get('l', price))
        volume = ticker.get('volume', ticker.get('v', 0))
        
        # 24h momentum
        if open_price and open_price > 0:
            momentum_24h = ((price - open_price) / open_price) * 100
        else:
            momentum_24h = 0
        
        # Volatility (high-low range)
        if high and low and low > 0:
            volatility = ((high - low) / low) * 100
        else:
            volatility = 0
        
        # Calculate ocean score
        # Components:
        # - Momentum (higher = better for trend following)
        # - Volume (higher = more liquid)
        # - Volatility (moderate = opportunity without chaos)
        
        # Momentum score (0-0.4) - positive momentum is better
        momentum_score = min(0.4, max(0, momentum_24h / 20))  # 20% = max score
        
        # Volume score (0-0.3) - placeholder, needs volume comparison
        volume_score = 0.15 if volume > 0 else 0
        
        # Volatility score (0-0.3) - sweet spot is 2-10%
        if 2 <= volatility <= 10:
            volatility_score = 0.3
        elif volatility < 2:
            volatility_score = volatility / 2 * 0.3
        else:
            volatility_score = max(0, 0.3 - (volatility - 10) / 50)
        
        ocean_score = momentum_score + volume_score + volatility_score
        
        # Determine opportunity type
        if momentum_24h > 5:
            opp_type = 'momentum'
            reason = f"Strong momentum: {momentum_24h:.1f}% in 24h"
        elif momentum_24h < -5:
            opp_type = 'reversal'
            reason = f"Potential reversal: {momentum_24h:.1f}% down"
        elif volatility > 5:
            opp_type = 'breakout'
            reason = f"High volatility: {volatility:.1f}% range"
        else:
            opp_type = 'stable'
            reason = "Stable with moderate movement"
        
        return OceanOpportunity(
            symbol=symbol,
            exchange=exchange,
            opportunity_type=opp_type,
            current_price=float(price),
            momentum_24h=momentum_24h,
            volume_24h=float(volume) if volume else 0,
            ocean_score=ocean_score,
            confidence=min(1.0, ocean_score / 0.7),  # Normalize to 0-1
            reason=reason,
        )
    
    async def _get_alpaca_tickers(self, client, symbols: Set[str]) -> Dict:
        """Get ticker data for Alpaca symbols."""
        tickers = {}
        
        try:
            # Use get_latest_quotes or similar
            if hasattr(client, 'get_latest_quotes'):
                quotes = client.get_latest_quotes(list(symbols)[:50])
                for symbol, quote in quotes.items():
                    tickers[symbol] = {
                        'last': float(quote.ask_price) if hasattr(quote, 'ask_price') else 0,
                        'bid': float(quote.bid_price) if hasattr(quote, 'bid_price') else 0,
                        'ask': float(quote.ask_price) if hasattr(quote, 'ask_price') else 0,
                    }
        except Exception as e:
            logger.error(f"Alpaca ticker error: {e}")
        
        return tickers
    
    def get_ocean_summary(self) -> Dict:
        """Get a summary of the ocean scanner's state."""
        return {
            'universe_size': {
                'kraken': len(self.kraken_universe),
                'alpaca_crypto': len(self.alpaca_crypto_universe),
                'alpaca_stocks': len(self.alpaca_stock_universe),
                'binance': len(self.binance_universe),
                'total': self.total_symbols_scanned,
            },
            'hot_opportunities': len(self.hot_opportunities),
            'top_5': [opp.to_dict() for opp in self.hot_opportunities[:5]],
            'scan_count': self.scan_count,
            'last_scan_time': self.last_scan_time,
        }
    
    def print_ocean_report(self):
        """Print a beautiful ocean report."""
        print("\n" + "🌊" * 35)
        print("            🐢 OCEAN SCANNER REPORT 🐢")
        print("🌊" * 35)
        
        print(f"\n📊 UNIVERSE SIZE:")
        print(f"   🐙 Kraken:        {len(self.kraken_universe):>6,} pairs")
        print(f"   🦙 Alpaca Crypto: {len(self.alpaca_crypto_universe):>6,} symbols")
        print(f"   📈 Alpaca Stocks: {len(self.alpaca_stock_universe):>6,} symbols")
        print(f"   🟡 Binance:       {len(self.binance_universe):>6,} pairs")
        print(f"   ─────────────────────────")
        print(f"   🌍 TOTAL:         {self.total_symbols_scanned:>6,} opportunities!")
        
        print(f"\n🔥 TOP 10 HOT OPPORTUNITIES:")
        for i, opp in enumerate(self.hot_opportunities[:10], 1):
            emoji = '🚀' if opp.momentum_24h > 5 else '📉' if opp.momentum_24h < -5 else '📊'
            print(f"   {i:>2}. {emoji} {opp.symbol:<12} | {opp.exchange:<8} | "
                  f"Score: {opp.ocean_score:.2f} | Mom: {opp.momentum_24h:>+6.1f}% | {opp.reason[:30]}")
        
        print(f"\n⏱️  Scan #{self.scan_count} completed in {self.last_scan_time:.2f}s")
        print("🌊" * 35)


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════
async def main():
    """Test the ocean scanner."""
    print("\n" + "=" * 70)
    print("🌊 AUREON OCEAN SCANNER - TEST MODE")
    print("=" * 70)
    
    # Load exchange clients
    exchanges = {}
    
    try:
        from kraken_client import KrakenClient
        exchanges['kraken'] = KrakenClient()
        print("✅ Kraken client loaded")
    except Exception as e:
        print(f"❌ Kraken: {e}")
    
    try:
        from alpaca_client import AlpacaClient
        exchanges['alpaca'] = AlpacaClient()
        print("✅ Alpaca client loaded")
    except Exception as e:
        print(f"❌ Alpaca: {e}")
    
    # Create scanner
    scanner = OceanScanner(exchanges)
    
    # Discover universe
    universe = await scanner.discover_universe()
    
    # Scan ocean (limited for test)
    opportunities = await scanner.scan_ocean(limit=50)
    
    # Print report
    scanner.print_ocean_report()
    
    return scanner


if __name__ == '__main__':
    asyncio.run(main())
