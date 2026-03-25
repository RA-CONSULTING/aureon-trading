#!/usr/bin/env python3
"""
🌍⚡ GLOBAL FINANCIAL ECOSYSTEM DATA FEED ⚡🌍
═══════════════════════════════════════════════════════════════

Aggregates the ENTIRE Earth's financial ecosystem into probability signals:

📊 ASSET CLASSES:
├─ 🪙 Crypto (Binance, Kraken, Alpaca)
├─ 💱 Forex (EUR/USD, GBP/USD, JPY/USD, etc.)
├─ 📈 Stocks/Indices (S&P 500, NASDAQ, DOW, DAX, FTSE, Nikkei)
├─ 🏆 Commodities (Gold, Silver, Oil, Natural Gas)
├─ 📄 Bonds (10Y Treasury Yields, German Bund)
└─ 💵 DXY (US Dollar Index)

📡 MACRO INDICATORS:
├─ 😱 Fear & Greed Index (Crypto + Traditional)
├─ 📉 VIX (Volatility Index)
├─ 💵 Interest Rates (Fed, ECB, BOE, BOJ)
├─ 📊 Economic Calendar Events
└─ 🌐 Global Market Correlations

🔗 FEEDS INTO:
├─ hnc_probability_matrix.py (2-Hour Trading Window)
├─ aureon_unified_ecosystem.py (Trading Decisions)
└─ cost_basis_tracker.py (Position Management)

Gary Leckey & GitHub Copilot | December 2025
"From Prime to Probability - The Entire Earth's Pulse"
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
import time
import math
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
import logging

try:
    from aureon_thought_bus import ThoughtBus, Thought
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    ThoughtBus = None
    Thought = None
    THOUGHT_BUS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 📊 DATA SOURCES - FREE APIs
# ═══════════════════════════════════════════════════════════════

DATA_SOURCES = {
    # Fear & Greed
    'FEAR_GREED_CRYPTO': 'https://api.alternative.me/fng/?limit=1',
    
    # CoinGecko - Global Crypto Market
    'COINGECKO_GLOBAL': 'https://api.coingecko.com/api/v3/global',
    'COINGECKO_FEAR_GREED': 'https://api.coingecko.com/api/v3/global',
    
    # Forex Rates (exchangerate-api free tier)
    'FOREX_RATES': 'https://open.er-api.com/v6/latest/USD',
    
    # Yahoo Finance (via public endpoint)
    'YAHOO_QUOTE': 'https://query1.finance.yahoo.com/v7/finance/quote?symbols=',
    
    # DXY, VIX, S&P500, Gold, Oil via Yahoo (UUP is a DXY proxy fallback)
    'MACRO_SYMBOLS': '^DXY,UUP,^VIX,^GSPC,^DJI,^IXIC,GC=F,CL=F,^TNX,^FVX',
    
    # Economic Calendar (investing.com scrape fallback)
    'ECON_CALENDAR': 'https://www.investing.com/economic-calendar/',
}

# Asset correlation matrix (static, learned from historical data)
CORRELATION_MATRIX = {
    # BTC correlations
    ('BTC', 'ETH'): 0.92,
    ('BTC', 'SPX'): 0.65,
    ('BTC', 'GOLD'): 0.30,
    ('BTC', 'DXY'): -0.55,
    ('BTC', 'VIX'): -0.45,
    
    # ETH correlations
    ('ETH', 'SOL'): 0.88,
    ('ETH', 'SPX'): 0.60,
    
    # Traditional correlations
    ('GOLD', 'DXY'): -0.75,
    ('OIL', 'DXY'): -0.40,
    ('SPX', 'VIX'): -0.80,
    ('BONDS', 'SPX'): -0.35,
}


@dataclass
class MacroSnapshot:
    """Snapshot of global macro conditions."""
    timestamp: datetime
    
    # Fear & Greed
    crypto_fear_greed: int = 50  # 0-100
    crypto_fg_classification: str = "Neutral"
    
    # Volatility
    vix: float = 20.0
    vix_change: float = 0.0
    
    # Dollar Strength
    dxy: float = 100.0
    dxy_change: float = 0.0
    
    # Interest Rates
    us_10y_yield: float = 4.5
    us_2y_yield: float = 4.3
    yield_curve_inversion: bool = False  # 2Y > 10Y = recession signal
    
    # Indices
    spx: float = 5000.0
    spx_change: float = 0.0
    dow: float = 40000.0
    nasdaq: float = 16000.0
    
    # Commodities
    gold: float = 2000.0
    gold_change: float = 0.0
    oil: float = 75.0
    oil_change: float = 0.0
    
    # Global Crypto Market
    total_crypto_mcap: float = 2.5e12
    btc_dominance: float = 50.0
    
    # Forex
    eur_usd: float = 1.08
    gbp_usd: float = 1.27
    usd_jpy: float = 150.0
    
    # Computed Signals
    risk_on_off: str = "NEUTRAL"  # RISK_ON, RISK_OFF, NEUTRAL
    market_regime: str = "NORMAL"  # NORMAL, FEAR, GREED, PANIC, EUPHORIA
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'crypto_fear_greed': self.crypto_fear_greed,
            'crypto_fg_classification': self.crypto_fg_classification,
            'vix': self.vix,
            'vix_change': self.vix_change,
            'dxy': self.dxy,
            'dxy_change': self.dxy_change,
            'us_10y_yield': self.us_10y_yield,
            'us_2y_yield': self.us_2y_yield,
            'yield_curve_inversion': self.yield_curve_inversion,
            'spx': self.spx,
            'spx_change': self.spx_change,
            'dow': self.dow,
            'nasdaq': self.nasdaq,
            'gold': self.gold,
            'gold_change': self.gold_change,
            'oil': self.oil,
            'oil_change': self.oil_change,
            'total_crypto_mcap': self.total_crypto_mcap,
            'btc_dominance': self.btc_dominance,
            'eur_usd': self.eur_usd,
            'gbp_usd': self.gbp_usd,
            'usd_jpy': self.usd_jpy,
            'risk_on_off': self.risk_on_off,
            'market_regime': self.market_regime,
        }


@dataclass 
class EconomicEvent:
    """Scheduled economic event."""
    timestamp: datetime
    currency: str
    event_name: str
    impact: str  # HIGH, MEDIUM, LOW
    previous: Optional[str] = None
    forecast: Optional[str] = None
    actual: Optional[str] = None


class GlobalFinancialFeed:
    """
    Aggregates Earth's entire financial ecosystem into probability signals.
    """
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 60  # seconds
        self.history: deque = deque(maxlen=100)
        self.last_snapshot: Optional[MacroSnapshot] = None
        self.economic_calendar: List[EconomicEvent] = []
        
        # Data file for persistence
        self.data_file = "global_financial_state.json"
        
        # Thought Bus for broadcasting checks
        self.bus = None
        if THOUGHT_BUS_AVAILABLE:
            try:
                self.bus = ThoughtBus(persist_path="thoughts.jsonl")
            except Exception:
                pass
                
        self.last_broadcast = 0.0
        self._load_state()
        
    def _load_state(self):
        """Load cached state from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # Restore last snapshot from cache
                    if data.get('last_snapshot'):
                        self.cache = data
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save state to file for persistence."""
        try:
            state = {
                'updated': datetime.now().isoformat(),
                'last_snapshot': self.last_snapshot.to_dict() if self.last_snapshot else None,
            }
            with open(self.data_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")
    
    def _fetch_json(self, url: str, timeout: int = 5) -> Optional[Dict]:
        """Fetch JSON from URL with caching."""
        cache_key = url
        cache_entry = self.cache.get(cache_key)
        
        # Check cache
        if cache_entry:
            age = time.time() - cache_entry.get('time', 0)
            if age < self.cache_ttl:
                return cache_entry.get('data')
        
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Aureon-Trading/1.0')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode())
                self.cache[cache_key] = {'data': data, 'time': time.time()}
                return data
        except Exception as e:
            logger.debug(f"Fetch failed for {url}: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # 📡 DATA FETCHERS
    # ═══════════════════════════════════════════════════════════════
    
    def fetch_crypto_fear_greed(self) -> Dict[str, Any]:
        """Fetch Crypto Fear & Greed Index from alternative.me."""
        data = self._fetch_json(DATA_SOURCES['FEAR_GREED_CRYPTO'])
        if data and data.get('data'):
            fng = data['data'][0]
            return {
                'value': int(fng.get('value', 50)),
                'classification': fng.get('value_classification', 'Neutral'),
                'timestamp': fng.get('timestamp'),
            }
        return {'value': 50, 'classification': 'Neutral'}
    
    def fetch_global_crypto_market(self) -> Dict[str, Any]:
        """Fetch global crypto market data from CoinGecko."""
        data = self._fetch_json(DATA_SOURCES['COINGECKO_GLOBAL'])
        if data and data.get('data'):
            d = data['data']
            return {
                'total_mcap': d.get('total_market_cap', {}).get('usd', 0),
                'total_volume': d.get('total_volume', {}).get('usd', 0),
                'btc_dominance': d.get('market_cap_percentage', {}).get('btc', 50),
                'eth_dominance': d.get('market_cap_percentage', {}).get('eth', 15),
                'mcap_change_24h': d.get('market_cap_change_percentage_24h_usd', 0),
            }
        return {}
    
    def fetch_forex_rates(self) -> Dict[str, float]:
        """Fetch forex rates (USD base)."""
        data = self._fetch_json(DATA_SOURCES['FOREX_RATES'])
        if data and data.get('rates'):
            rates = data['rates']
            return {
                'eur_usd': 1.0 / rates.get('EUR', 1.08),
                'gbp_usd': 1.0 / rates.get('GBP', 1.27),
                'usd_jpy': rates.get('JPY', 150.0),
                'usd_chf': rates.get('CHF', 0.88),
                'aud_usd': 1.0 / rates.get('AUD', 1.53),
                'usd_cad': rates.get('CAD', 1.36),
            }
        return {}
    
    def fetch_yahoo_quotes(self, symbols: str) -> Dict[str, Dict]:
        """Fetch quotes from Yahoo Finance."""
        url = DATA_SOURCES['YAHOO_QUOTE'] + symbols
        data = self._fetch_json(url, timeout=10)
        
        results = {}
        if data and data.get('quoteResponse', {}).get('result'):
            for quote in data['quoteResponse']['result']:
                sym = quote.get('symbol', '')
                results[sym] = {
                    'price': quote.get('regularMarketPrice', 0),
                    'change': quote.get('regularMarketChange', 0),
                    'change_pct': quote.get('regularMarketChangePercent', 0),
                    'volume': quote.get('regularMarketVolume', 0),
                    'market_state': quote.get('marketState', 'CLOSED'),
                }
        return results
    
    def fetch_macro_indicators(self) -> Dict[str, Any]:
        """Fetch all major macro indicators."""
        symbols = DATA_SOURCES['MACRO_SYMBOLS']
        quotes = self.fetch_yahoo_quotes(symbols)
        
        dxy_quote = quotes.get('^DXY') or quotes.get('UUP') or {}
        return {
            'vix': quotes.get('^VIX', {}).get('price', 20.0),
            'vix_change': quotes.get('^VIX', {}).get('change_pct', 0),

            'dxy': dxy_quote.get('price', 100.0),
            'dxy_change': dxy_quote.get('change_pct', 0),
            
            'spx': quotes.get('^GSPC', {}).get('price', 5000),
            'spx_change': quotes.get('^GSPC', {}).get('change_pct', 0),
            
            'dow': quotes.get('^DJI', {}).get('price', 40000),
            'nasdaq': quotes.get('^IXIC', {}).get('price', 16000),
            
            'gold': quotes.get('GC=F', {}).get('price', 2000),
            'gold_change': quotes.get('GC=F', {}).get('change_pct', 0),
            
            'oil': quotes.get('CL=F', {}).get('price', 75),
            'oil_change': quotes.get('CL=F', {}).get('change_pct', 0),
            
            'us_10y': quotes.get('^TNX', {}).get('price', 4.5),
            'us_5y': quotes.get('^FVX', {}).get('price', 4.3),
        }
    
    # ═══════════════════════════════════════════════════════════════
    # 🧠 ANALYSIS & SIGNALS
    # ═══════════════════════════════════════════════════════════════
    
    def compute_risk_sentiment(self, snapshot: MacroSnapshot) -> str:
        """
        Compute overall market risk sentiment.
        
        RISK_ON: Markets bullish, low volatility, greed
        RISK_OFF: Markets bearish, high volatility, fear
        NEUTRAL: Mixed signals
        """
        score = 0
        
        # Fear & Greed (0-100, 50 = neutral)
        if snapshot.crypto_fear_greed > 65:
            score += 2  # Greed = Risk On
        elif snapshot.crypto_fear_greed < 35:
            score -= 2  # Fear = Risk Off
        
        # VIX (20 = neutral, <15 = calm, >30 = fear)
        if snapshot.vix < 15:
            score += 2
        elif snapshot.vix > 25:
            score -= 1
        elif snapshot.vix > 35:
            score -= 3
        
        # DXY (stronger dollar = risk off for crypto/stocks)
        if snapshot.dxy_change > 0.5:
            score -= 1
        elif snapshot.dxy_change < -0.5:
            score += 1
        
        # S&P Change
        if snapshot.spx_change > 1.0:
            score += 2
        elif snapshot.spx_change < -1.0:
            score -= 2
        
        # Gold (safe haven move = risk off)
        if snapshot.gold_change > 1.5:
            score -= 1  # Flight to safety
        
        # Yield curve inversion = recession signal
        if snapshot.yield_curve_inversion:
            score -= 2
        
        if score >= 3:
            return "RISK_ON"
        elif score <= -3:
            return "RISK_OFF"
        return "NEUTRAL"
    
    def compute_market_regime(self, snapshot: MacroSnapshot) -> str:
        """
        Determine current market regime.
        
        PANIC: Extreme fear, high VIX, sharp declines
        FEAR: Elevated fear, rising VIX
        NORMAL: Balanced sentiment
        GREED: Elevated greed, low VIX
        EUPHORIA: Extreme greed, complacency
        """
        fg = snapshot.crypto_fear_greed
        vix = snapshot.vix
        
        if fg < 20 and vix > 35:
            return "PANIC"
        elif fg < 35 and vix > 25:
            return "FEAR"
        elif fg > 80 and vix < 15:
            return "EUPHORIA"
        elif fg > 65:
            return "GREED"
        return "NORMAL"
    
    def compute_correlation_impact(self, asset: str, snapshot: MacroSnapshot) -> float:
        """
        Compute correlation-adjusted impact for an asset.
        
        Returns: Multiplier (-1.0 to +1.0) based on correlated assets' movements
        """
        impact = 0.0
        count = 0
        
        # Map snapshot values to simple direction signals
        signals = {
            'SPX': 1 if snapshot.spx_change > 0 else -1,
            'DXY': 1 if snapshot.dxy_change > 0 else -1,
            'GOLD': 1 if snapshot.gold_change > 0 else -1,
            'VIX': 1 if snapshot.vix > 25 else -1 if snapshot.vix < 15 else 0,
        }
        
        # Check correlations
        for (a1, a2), corr in CORRELATION_MATRIX.items():
            if a1 == asset and a2 in signals:
                impact += corr * signals[a2]
                count += 1
            elif a2 == asset and a1 in signals:
                impact += corr * signals[a1]
                count += 1
        
        if count > 0:
            impact /= count
        
        return max(-1.0, min(1.0, impact))
    
    # ═══════════════════════════════════════════════════════════════
    # 🎯 PROBABILITY SIGNALS FOR TRADING
    # ═══════════════════════════════════════════════════════════════
    
    def get_probability_adjustment(self, symbol: str, base_probability: float) -> Tuple[float, Dict]:
        """
        Adjust trading probability based on global macro conditions.
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDC, ETHUSDC)
            base_probability: Base probability from technical analysis (0-1)
            
        Returns:
            (adjusted_probability, reasoning_dict)
        """
        snapshot = self.get_snapshot()
        
        adjustments = []
        total_adjustment = 0.0
        
        # 1. Fear & Greed Impact
        fg = snapshot.crypto_fear_greed
        if fg < 25:  # Extreme fear = contrarian BUY
            adj = 0.10
            adjustments.append(f"Extreme Fear ({fg}) = +10% (contrarian)")
        elif fg > 75:  # Extreme greed = cautious
            adj = -0.05
            adjustments.append(f"Extreme Greed ({fg}) = -5% (caution)")
        else:
            adj = (fg - 50) / 500  # Small linear adjustment
            adjustments.append(f"Fear/Greed ({fg}) = {adj*100:+.1f}%")
        total_adjustment += adj
        
        # 2. VIX Impact
        vix = snapshot.vix
        if vix > 35:
            adj = -0.15  # High volatility = reduce exposure
            adjustments.append(f"High VIX ({vix:.1f}) = -15%")
        elif vix > 25:
            adj = -0.05
            adjustments.append(f"Elevated VIX ({vix:.1f}) = -5%")
        elif vix < 15:
            adj = 0.05
            adjustments.append(f"Low VIX ({vix:.1f}) = +5% (calm)")
        else:
            adj = 0
        total_adjustment += adj
        
        # 3. Dollar Strength (inverse for crypto)
        if 'USD' in symbol or 'BTC' in symbol or 'ETH' in symbol:
            dxy_impact = -snapshot.dxy_change / 100  # Inverse
            total_adjustment += dxy_impact
            adjustments.append(f"DXY impact: {dxy_impact*100:+.2f}%")
        
        # 4. Market Regime
        regime = snapshot.market_regime
        regime_adj = {
            'PANIC': 0.15,     # Buy the fear
            'FEAR': 0.05,
            'NORMAL': 0,
            'GREED': -0.03,
            'EUPHORIA': -0.10  # Reduce exposure
        }.get(regime, 0)
        total_adjustment += regime_adj
        adjustments.append(f"Regime ({regime}) = {regime_adj*100:+.1f}%")
        
        # 5. Risk Sentiment
        risk = snapshot.risk_on_off
        if risk == "RISK_ON":
            adj = 0.05
        elif risk == "RISK_OFF":
            adj = -0.08
        else:
            adj = 0
        total_adjustment += adj
        adjustments.append(f"Risk ({risk}) = {adj*100:+.1f}%")
        
        # Apply adjustment with bounds
        adjusted = base_probability + total_adjustment
        adjusted = max(0.05, min(0.95, adjusted))
        
        return adjusted, {
            'base_probability': base_probability,
            'total_adjustment': total_adjustment,
            'adjusted_probability': adjusted,
            'adjustments': adjustments,
            'snapshot': snapshot.to_dict(),
        }
    
    def _broadcast_to_hive(self, snapshot: MacroSnapshot):
        """Broadcast macro snapshot to the Thought Bus."""
        if not self.bus or not THOUGHT_BUS_AVAILABLE:
            return
            
        now = time.time()
        # Rate limit broadcasts (don't spam every call)
        if now - self.last_broadcast < 10.0:  # 10s throttle
            return
            
        try:
            payload = snapshot.to_dict()
            # Enriched payload for easier consumption
            payload['source'] = 'global_financial_feed'
            payload['type'] = 'macro_snapshot'
            payload['risk_sentiment'] = snapshot.risk_on_off
            
            thought = Thought(
                topic="market.macro.global",
                payload=payload,
                source="global_financial_feed"
            )
            self.bus.publish(thought)
            self.last_broadcast = now
            logger.info(f"🌍 Broadcasted global macro snapshot (Risk: {snapshot.risk_on_off})")
        except Exception as e:
            logger.warning(f"Failed to broadcast macro snapshot: {e}")

    def get_snapshot(self) -> MacroSnapshot:
        """
        Get current global macro snapshot.
        Fetches fresh data or returns cached version.
        """
        # Check cache freshness
        if self.last_snapshot:
            age = (datetime.now() - self.last_snapshot.timestamp).total_seconds()
            if age < self.cache_ttl:
                # Still try to broadcast if it's been a while (e.g. called from another loop)
                self._broadcast_to_hive(self.last_snapshot)
                return self.last_snapshot
        
        print("\n🌍 Fetching Global Financial Data...")
        
        # Fetch all data sources
        fng = self.fetch_crypto_fear_greed()
        crypto_global = self.fetch_global_crypto_market()
        forex = self.fetch_forex_rates()
        macro = self.fetch_macro_indicators()
        
        # Build snapshot
        snapshot = MacroSnapshot(
            timestamp=datetime.now(),
            
            # Fear & Greed
            crypto_fear_greed=fng.get('value', 50),
            crypto_fg_classification=fng.get('classification', 'Neutral'),
            
            # Volatility
            vix=macro.get('vix', 20.0),
            vix_change=macro.get('vix_change', 0),
            
            # Dollar (use proxy if needed)
            dxy=macro.get('dxy', 100.0),
            dxy_change=macro.get('dxy_change', 0.0),
            
            # Yields
            us_10y_yield=macro.get('us_10y', 4.5),
            us_2y_yield=macro.get('us_5y', 4.3),  # Using 5Y as proxy
            yield_curve_inversion=macro.get('us_5y', 4.3) > macro.get('us_10y', 4.5),
            
            # Indices
            spx=macro.get('spx', 5000),
            spx_change=macro.get('spx_change', 0),
            dow=macro.get('dow', 40000),
            nasdaq=macro.get('nasdaq', 16000),
            
            # Commodities
            gold=macro.get('gold', 2000),
            gold_change=macro.get('gold_change', 0),
            oil=macro.get('oil', 75),
            oil_change=macro.get('oil_change', 0),
            
            # Crypto
            total_crypto_mcap=crypto_global.get('total_mcap', 2.5e12),
            btc_dominance=crypto_global.get('btc_dominance', 50),
            
            # Forex
            eur_usd=forex.get('eur_usd', 1.08),
            gbp_usd=forex.get('gbp_usd', 1.27),
            usd_jpy=forex.get('usd_jpy', 150),
        )
        
        # Compute derived signals
        snapshot.risk_on_off = self.compute_risk_sentiment(snapshot)
        snapshot.market_regime = self.compute_market_regime(snapshot)
        
        # Store and persist
        self.last_snapshot = snapshot
        self.history.append(snapshot)
        self._save_state()
        
        # Broadcast to Thought Bus (The Queen is listening)
        self._broadcast_to_hive(snapshot)

        # Feed into Autonomy Hub (The Big Wheel)
        try:
            from aureon_autonomy_hub import get_autonomy_hub
            hub = get_autonomy_hub()
            hub.data_bridge.ingest_macro_snapshot(snapshot.to_dict())
        except Exception:
            pass  # Hub not available yet

        # Log summary
        print(f"   😱 Fear/Greed: {snapshot.crypto_fear_greed} ({snapshot.crypto_fg_classification})")
        print(f"   📊 VIX: {snapshot.vix:.1f} | S&P: {snapshot.spx:.0f} ({snapshot.spx_change:+.2f}%)")
        print(f"   🏆 Gold: ${snapshot.gold:.0f} | Oil: ${snapshot.oil:.1f}")
        print(f"   💵 EUR/USD: {snapshot.eur_usd:.4f} | GBP/USD: {snapshot.gbp_usd:.4f}")
        print(f"   📄 10Y Yield: {snapshot.us_10y_yield:.2f}%")
        print(f"   🎯 Regime: {snapshot.market_regime} | Risk: {snapshot.risk_on_off}")
        
        return snapshot
    
    def get_trading_signal(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive trading signal for a symbol.
        
        Returns:
            {
                'symbol': str,
                'macro_bias': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
                'macro_strength': 0-100,
                'adjustments': list,
                'snapshot': dict,
            }
        """
        snapshot = self.get_snapshot()
        
        # Determine macro bias
        score = 0
        
        # Fear/Greed contribution
        score += (snapshot.crypto_fear_greed - 50) / 5  # -10 to +10
        
        # VIX contribution (inverse)
        vix_score = (20 - snapshot.vix) / 2  # Positive when VIX low
        score += max(-5, min(5, vix_score))
        
        # S&P contribution
        score += snapshot.spx_change * 2  # Direct correlation
        
        # Risk sentiment
        if snapshot.risk_on_off == "RISK_ON":
            score += 5
        elif snapshot.risk_on_off == "RISK_OFF":
            score -= 5
        
        # Normalize to 0-100
        strength = int(50 + score)
        strength = max(0, min(100, strength))
        
        if strength > 60:
            bias = "BULLISH"
        elif strength < 40:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        return {
            'symbol': symbol,
            'macro_bias': bias,
            'macro_strength': strength,
            'fear_greed': snapshot.crypto_fear_greed,
            'vix': snapshot.vix,
            'market_regime': snapshot.market_regime,
            'risk_sentiment': snapshot.risk_on_off,
            'timestamp': snapshot.timestamp.isoformat(),
        }
    
    def print_dashboard(self):
        """Print a visual dashboard of global financial state."""
        snapshot = self.get_snapshot()
        
        fg = snapshot.crypto_fear_greed
        fg_bar = "█" * (fg // 5) + "░" * (20 - fg // 5)
        
        print("\n" + "═" * 70)
        print("🌍⚡ GLOBAL FINANCIAL ECOSYSTEM DASHBOARD ⚡🌍")
        print("═" * 70)
        print(f"""
┌────────────────────────────────────────────────────────────────────┐
│  😱 FEAR & GREED INDEX                                             │
│  [{fg_bar}] {fg}/100 ({snapshot.crypto_fg_classification})
│                                                                    │
│  📊 VOLATILITY (VIX)                                               │
│  {snapshot.vix:.1f} {'🔴 HIGH' if snapshot.vix > 25 else '🟢 LOW' if snapshot.vix < 15 else '🟡 NORMAL'}
│                                                                    │
│  📈 MARKETS                                                        │
│  S&P 500:  ${snapshot.spx:,.0f} ({snapshot.spx_change:+.2f}%)
│  NASDAQ:   ${snapshot.nasdaq:,.0f}
│  DOW:      ${snapshot.dow:,.0f}
│                                                                    │
│  🏆 COMMODITIES                                                    │
│  Gold:     ${snapshot.gold:,.0f} ({snapshot.gold_change:+.2f}%)
│  Oil:      ${snapshot.oil:.2f} ({snapshot.oil_change:+.2f}%)
│                                                                    │
│  💱 FOREX                                                          │
│  EUR/USD:  {snapshot.eur_usd:.4f}
│  GBP/USD:  {snapshot.gbp_usd:.4f}
│  USD/JPY:  {snapshot.usd_jpy:.2f}
│                                                                    │
│  📄 BONDS                                                          │
│  10Y Yield: {snapshot.us_10y_yield:.2f}%
│  Curve:     {'⚠️ INVERTED' if snapshot.yield_curve_inversion else '✅ NORMAL'}
│                                                                    │
│  🪙 CRYPTO MARKET                                                  │
│  Total MCap: ${snapshot.total_crypto_mcap/1e12:.2f}T
│  BTC Dom:    {snapshot.btc_dominance:.1f}%
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  🎯 SIGNALS                                                        │
│  Market Regime: {snapshot.market_regime:<15}
│  Risk Sentiment: {snapshot.risk_on_off:<15}
└────────────────────────────────────────────────────────────────────┘
""")
        print("═" * 70)


# ═══════════════════════════════════════════════════════════════
# 🔗 INTEGRATION WITH PROBABILITY MATRIX
# ═══════════════════════════════════════════════════════════════

def integrate_with_probability_matrix():
    """
    Hook to integrate global financial feed with HNC Probability Matrix.
    """
    try:
        from hnc_probability_matrix import HNCProbabilityIntegration
        
        feed = GlobalFinancialFeed()
        integration = HNCProbabilityIntegration()
        
        # Get macro snapshot
        snapshot = feed.get_snapshot()
        
        # Feed macro data into probability calculation
        macro_bias = {
            'fear_greed': snapshot.crypto_fear_greed,
            'vix': snapshot.vix,
            'risk_on_off': snapshot.risk_on_off,
            'market_regime': snapshot.market_regime,
        }
        
        return feed, macro_bias
        
    except ImportError:
        logger.warning("HNC Probability Matrix not available")
        return GlobalFinancialFeed(), {}


# ═══════════════════════════════════════════════════════════════
# 🧪 TEST / DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🌍⚡ GLOBAL FINANCIAL ECOSYSTEM FEED ⚡🌍")
    print("=" * 70)
    
    feed = GlobalFinancialFeed()
    
    # Print dashboard
    feed.print_dashboard()
    
    # Test probability adjustment
    print("\n📊 PROBABILITY ADJUSTMENT TEST:")
    test_symbols = ['BTCUSDC', 'ETHUSDC', 'SOLUSDC']
    
    for symbol in test_symbols:
        base_prob = 0.60  # Assume 60% base probability from technicals
        adjusted, reasoning = feed.get_probability_adjustment(symbol, base_prob)
        
        print(f"\n   {symbol}:")
        print(f"   Base: {base_prob*100:.0f}% → Adjusted: {adjusted*100:.1f}%")
        for adj in reasoning['adjustments']:
            print(f"      • {adj}")
    
    print("\n" + "=" * 70)
    print("✅ Global Financial Feed Ready")
    print("   Feeds into: hnc_probability_matrix.py")
    print("   Used by: aureon_unified_ecosystem.py")
    print("=" * 70)
