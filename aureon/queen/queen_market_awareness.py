#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👑🌍 QUEEN MARKET AWARENESS - MARKET-WIDE CONTEXT INTELLIGENCE
==============================================================

Gives the Queen understanding of:
1. 📊 Market-Wide Context - Is the WHOLE market down?
2. 📈 BTC Correlation - Are your coins tracking Bitcoin?
3. 🛡️ Hold Until Recovery - When to wait vs when to act
4. 📝 Paper vs Realized - Communicate what losses REALLY mean
5. 🔴🟢 Real-Time Tracking - Monitor market LIVE using open source feeds

This module makes the Queen SMART about market conditions,
not just individual positions.

Gary Leckey | February 2026
"""

import os
import json
import time
import logging
import requests
import asyncio
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from collections import deque
from dotenv import load_dotenv

load_dotenv('/workspaces/aureon-trading/.env', override=True)

logger = logging.getLogger(__name__)

# Import Open Source Data Engine for real-time tracking
# Note: Deferred import to avoid circular dependencies
OPEN_SOURCE_ENGINE_AVAILABLE = False
OpenSourceDataEngine = None
get_data_engine = None
MarketData = None
SentimentData = None
WhaleAlert = None

def _load_data_engine():
    """Lazy load the data engine to avoid circular imports"""
    global OPEN_SOURCE_ENGINE_AVAILABLE, OpenSourceDataEngine, get_data_engine
    global MarketData, SentimentData, WhaleAlert
    
    if OPEN_SOURCE_ENGINE_AVAILABLE:
        return True
    
    try:
        from queen_open_source_data_engine import (
            OpenSourceDataEngine as OSE, 
            get_data_engine as get_engine,
            MarketData as MD,
            SentimentData as SD,
            WhaleAlert as WA
        )
        OpenSourceDataEngine = OSE
        get_data_engine = get_engine
        MarketData = MD
        SentimentData = SD
        WhaleAlert = WA
        OPEN_SOURCE_ENGINE_AVAILABLE = True
        logger.info("🌐 Open Source Data Engine loaded successfully")
        return True
    except ImportError as e:
        logger.warning(f"⚠️ Open Source Data Engine not available: {e}")
        return False

# ============================================================================
# MARKET STATE DATA STRUCTURES
# ============================================================================

@dataclass
class MarketCondition:
    """Overall market condition assessment"""
    timestamp: datetime
    
    # BTC as market proxy
    btc_price: float = 0.0
    btc_24h_change: float = 0.0
    btc_7d_change: float = 0.0
    btc_30d_change: float = 0.0
    
    # Market state
    market_state: str = "UNKNOWN"  # BULL, BEAR, SIDEWAYS, CRASH, RECOVERY
    market_severity: float = 0.0   # -1.0 (crash) to +1.0 (moon)
    
    # Your portfolio context
    portfolio_vs_btc: float = 0.0  # How your portfolio compares to BTC
    correlation_to_btc: float = 0.0  # How correlated your coins are
    
    # Recommendations
    should_hold: bool = True
    recovery_outlook: str = ""
    queen_message: str = ""

@dataclass
class PositionContext:
    """Context for a single position relative to market"""
    asset: str
    qty_held: float
    cost_basis: float
    current_value: float
    
    # P&L
    paper_pnl: float = 0.0
    paper_pnl_pct: float = 0.0
    realized_pnl: float = 0.0
    
    # Market context
    drop_vs_btc: float = 0.0  # How much worse/better than BTC
    is_tracking_btc: bool = False  # Correlated to market?
    
    # Assessment
    loss_reason: str = ""  # "MARKET_WIDE", "COIN_SPECIFIC", "BOTH"
    recovery_probability: str = ""  # "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    queen_advice: str = ""

# ============================================================================
# MARKET AWARENESS ENGINE
# ============================================================================

class QueenMarketAwareness:
    """
    👑🌍 THE QUEEN'S MARKET AWARENESS ENGINE
    
    Gives the Queen understanding of:
    - Is the whole market down or just my coins?
    - Should I hold and wait for recovery?
    - What are paper losses vs realized losses?
    - REAL-TIME market tracking using open source feeds
    """
    
    def __init__(self):
        self.state_file = '/workspaces/aureon-trading/queen_market_state.json'
        self.last_update = None
        self.update_interval = 300  # 5 minutes
        self.market_condition: Optional[MarketCondition] = None
        
        # Historical BTC prices for reference
        self.btc_reference_prices = {
            'jan_2026_high': 108000,  # BTC high in Jan 2026
            'jan_27_2026': 102000,    # When most positions were bought
            'feb_3_2026': 78000,      # Current approximate
        }
        
        # 🌐 REAL-TIME DATA ENGINE - Open Source Feeds
        self.data_engine = None
        self.data_engine_thread = None
        self.live_tracking = False
        
        # Real-time market state
        self.live_prices: Dict[str, float] = {}
        self.live_sentiment: Optional[Dict] = None
        self.whale_alerts: deque = deque(maxlen=50)
        self.market_alerts: deque = deque(maxlen=100)  # Significant events
        
        # Tracking thresholds
        self.whale_threshold_usd = 100000  # $100K+ = whale
        self.significant_move_pct = 5.0  # 5%+ = significant
        
        # 🌊 OCEAN SCANNER - Full market opportunity scanning
        self.ocean_scanner = None
        self.ocean_last_scan = None
        self.ocean_scan_interval = 60  # Scan every 60 seconds
        self.ocean_opportunities: List[Dict] = []
        
        # ☀️🌍 SOLAR SYSTEM AWARENESS - Cosmic counter-intelligence
        self.solar_awareness = None
        
        # ⚔️ WARRIOR PATH - IRA/Apache/Sun Tzu/Ghost Dance tactical systems
        self.warrior_path = None
        
        logger.info("👑🌍 Queen Market Awareness initialized")
        
        # Try to wire open source data engine
        self._wire_data_engine()
        
        # Try to wire ocean scanner
        self._wire_ocean_scanner()
        
        # Try to wire solar system awareness
        self._wire_solar_awareness()
        
        # Try to wire warrior path tactical systems
        self._wire_warrior_path()
    
    def _wire_data_engine(self):
        """Wire the Open Source Data Engine for real-time tracking"""
        # Lazy load the data engine
        if not _load_data_engine():
            logger.warning("⚠️ Could not load data engine")
            return
        
        try:
            self.data_engine = get_data_engine()
            logger.info("🌐 Open Source Data Engine WIRED!")
            logger.info("   📊 CoinGecko - Prices, Market Cap")
            logger.info("   😱 Fear & Greed Index - Sentiment")
            logger.info("   🐋 Whale Detection - Large trades")
            logger.info("   📰 News Sentiment - Headlines")
            logger.info("   🗣️ Social Volume - Reddit/Twitter")
            logger.info("   📈 Order Books - Buy/Sell pressure")
        except Exception as e:
            logger.warning(f"⚠️ Could not wire data engine: {e}")
    
    def _wire_ocean_scanner(self):
        """Wire the Ocean Scanner for full market opportunity scanning"""
        try:
            from aureon_ocean_scanner import OceanScanner
            
            # Load exchange clients
            exchanges = {}
            
            try:
                from kraken_client import get_kraken_client
                exchanges['kraken'] = get_kraken_client()
            except Exception:
                pass
            
            try:
                from alpaca_client import AlpacaClient
                exchanges['alpaca'] = AlpacaClient()
            except Exception:
                pass
            
            try:
                from binance_client import BinanceClient
                exchanges['binance'] = BinanceClient()
            except Exception:
                pass
            
            self.ocean_scanner = OceanScanner(exchanges)
            logger.info("🌊 Ocean Scanner WIRED!")
            logger.info("   🐢 Queen is now a TURTLE in the sea of possibilities!")
            logger.info("   🔭 Universe discovery: READY")
            logger.info("   🎯 Opportunity scanning: READY")
            
        except ImportError as e:
            logger.warning(f"⚠️ Ocean Scanner not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Could not wire ocean scanner: {e}")
    
    async def scan_ocean_opportunities(self, limit: int = 50) -> List[Dict]:
        """
        🌊 SCAN THE OCEAN FOR OPPORTUNITIES
        
        Uses the Ocean Scanner to find the best opportunities
        across ALL exchanges and ALL symbols.
        """
        if not self.ocean_scanner:
            logger.warning("Ocean scanner not available")
            return []
        
        try:
            # Discover universe if not done
            if self.ocean_scanner.total_symbols_scanned == 0:
                logger.info("🔭 Discovering trading universe...")
                await self.ocean_scanner.discover_universe()
            
            # Scan ocean
            opportunities = await self.ocean_scanner.scan_ocean(limit=limit)
            
            # Store results
            self.ocean_opportunities = [opp.to_dict() for opp in opportunities]
            self.ocean_last_scan = time.time()
            
            return self.ocean_opportunities
            
        except Exception as e:
            logger.error(f"Ocean scan failed: {e}")
            return []
    
    def get_ocean_summary(self) -> Dict:
        """Get summary of ocean scanner state"""
        if not self.ocean_scanner:
            return {'error': 'Ocean scanner not available'}
        
        return self.ocean_scanner.get_ocean_summary()
    
    def get_ocean_report(self) -> str:
        """
        🌊 QUEEN'S OCEAN OPPORTUNITY REPORT
        
        Shows the best opportunities the Queen found across the entire market.
        """
        if not self.ocean_scanner:
            return "⚠️ Ocean Scanner not available - cannot see the full market"
        
        summary = self.ocean_scanner.get_ocean_summary()
        universe = summary.get('universe_size', {})
        top_opps = summary.get('top_5', [])
        
        report = f"""
🌊🐢 QUEEN'S OCEAN REPORT - BE A TURTLE, NOT A FISH!
=====================================================
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔭 Last Scan: {self.ocean_last_scan and datetime.fromtimestamp(self.ocean_last_scan).strftime('%H:%M:%S') or 'Never'}

🌍 TRADING UNIVERSE:
   🐙 Kraken:        {universe.get('kraken', 0):>6,} pairs
   🦙 Alpaca Crypto: {universe.get('alpaca_crypto', 0):>6,} symbols
   📈 Alpaca Stocks: {universe.get('alpaca_stocks', 0):>6,} symbols
   🟡 Binance:       {universe.get('binance', 0):>6,} pairs
   ─────────────────────────
   🌊 TOTAL OCEAN:   {universe.get('total', 0):>6,} opportunities!

🔥 TOP 5 HOT OPPORTUNITIES:
"""
        if top_opps:
            for i, opp in enumerate(top_opps[:5], 1):
                mom = opp.get('momentum_24h', 0)
                emoji = '🚀' if mom > 5 else '📉' if mom < -5 else '📊'
                report += f"   {i}. {emoji} {opp.get('symbol', '?'):<12} | Score: {opp.get('ocean_score', 0):.2f} | Mom: {mom:>+6.1f}% | {opp.get('reason', '')[:30]}\n"
        else:
            report += "   (No opportunities scanned yet - run scan_ocean_opportunities())\n"
        
        # Compare to our puddle
        report += f"""
🐟 YOUR CURRENT PUDDLE:
   Held positions: ~17 coins
   Universe access: {universe.get('total', 0):,} opportunities!
   
👑 QUEEN'S WISDOM:
   "Why be a big fish in a small pond when you can be a TURTLE in the ocean?"
   The Queen now sees {universe.get('total', 0):,}x more opportunities!
"""
        return report
    
    def _wire_solar_awareness(self):
        """Wire the Solar System Awareness for cosmic counter-intelligence"""
        try:
            from queen_solar_system_awareness import QueenSolarSystemAwareness
            
            self.solar_awareness = QueenSolarSystemAwareness()
            logger.info("☀️🌍 Solar System Awareness WIRED!")
            logger.info("   🌞 CME Tracking: READY")
            logger.info("   🌍 Schumann Resonance: READY")
            logger.info("   ⚡ Ionosphere Monitoring: READY")
            logger.info("   🎯 Counter-Phase Engine: READY")
            logger.info("   👑 Cosmic Veto System: READY")
            
        except ImportError as e:
            logger.warning(f"⚠️ Solar System Awareness not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Could not wire solar awareness: {e}")
    
    async def get_cosmic_state(self) -> Dict:
        """Get full cosmic intelligence state"""
        if not self.solar_awareness:
            return {'error': 'Solar awareness not available'}
        
        return await self.solar_awareness.get_full_cosmic_state()
    
    def get_cosmic_report(self) -> str:
        """Get Queen's Cosmic Intelligence Report"""
        if not self.solar_awareness:
            return "⚠️ Solar System Awareness not available"
        
        return self.solar_awareness.get_cosmic_report()
    
    async def cosmic_veto(self, trade: Dict) -> Tuple[bool, str]:
        """Check if cosmic conditions veto a trade"""
        if not self.solar_awareness:
            return False, "Solar awareness not available - no veto"
        
        return await self.solar_awareness.queen_cosmic_veto(trade)
    
    def get_counter_phase(self) -> Dict:
        """Get current counter-phase positioning"""
        if not self.solar_awareness:
            return {'error': 'Solar awareness not available'}
        
        return self.solar_awareness.calculate_counter_phase()
    
    # ═══════════════════════════════════════════════════════════════════════
    # ⚔️ WARRIOR PATH - IRA/APACHE/SUN TZU/GHOST DANCE TACTICAL SYSTEMS
    # ═══════════════════════════════════════════════════════════════════════
    
    def _wire_warrior_path(self):
        """Wire the Warrior Path for all tactical systems"""
        try:
            from queen_warrior_path import QueenWarriorPath
            
            self.warrior_path = QueenWarriorPath()
            logger.info("⚔️🦅 Warrior Path WIRED!")
            logger.info("   🇮🇪 IRA Tactics: Hit-and-Run, Cell Structure, Blend In")
            logger.info("   🦅 Apache Tactics: Patience, Terrain Mastery, Survival")
            logger.info("   ☯️ Sun Tzu: Win Without Fighting, Attack Weakness")
            logger.info("   🌌 Ghost Dance: 741Hz Warrior, 852Hz Scout, 528Hz Medicine")
            logger.info("   📜 Historical Patterns: 1929, 2008, 2020")
            logger.info("   🐺 Animal Scanners: Wolf, Lion, Hummingbird, Ants")
            logger.info("   🎵 Harmonic Counter-Phase: 180° Opposition")
            
        except ImportError as e:
            logger.warning(f"⚠️ Warrior Path not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Could not wire warrior path: {e}")
    
    def get_tactical_assessment(self, symbol: str = "", price: float = 0.0,
                                 price_change_pct: float = 0.0, volume: float = 0.0,
                                 market_context: Optional[Dict] = None) -> Dict:
        """
        Get full tactical assessment from all warfare systems.
        
        Returns IRA/Apache/Sun Tzu/Ghost Dance combined assessment.
        """
        if not self.warrior_path:
            return {'error': 'Warrior path not available'}
        
        assessment = self.warrior_path.assess_tactical_situation(
            symbol=symbol,
            price=price,
            price_change_pct=price_change_pct,
            volume=volume,
            market_context=market_context
        )
        
        return assessment.to_dict()
    
    def invoke_ancestors(self, ceremony_type: str = "battle") -> Dict:
        """
        🌌 INVOKE ANCESTRAL SPIRITS
        
        Ceremony types:
        - "battle": Warrior and Scout spirits (741Hz)
        - "healing": Medicine and Grandmother spirits (528Hz)
        - "vision": Scout and Chief spirits (852Hz)
        - "harvest": Grandmother and Earth spirits (417Hz)
        """
        if not self.warrior_path:
            return {'error': 'Warrior path not available'}
        
        return self.warrior_path.invoke_ancestors(ceremony_type)
    
    def get_warrior_report(self) -> str:
        """Get full Warrior Path status report"""
        if not self.warrior_path:
            return "⚠️ Warrior Path not available"
        
        return self.warrior_path.get_warrior_report()
    
    def get_battle_readiness(self) -> float:
        """Get current battle readiness score (0-1)"""
        if not self.warrior_path:
            return 0.0
        
        assessment = self.warrior_path.assess_tactical_situation()
        return assessment.battle_readiness
    
    def can_win_without_fighting(self, context: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        ☯️ SUN TZU'S HIGHEST ART - Can we profit without direct confrontation?
        
        Returns (can_win, reason)
        """
        if not self.warrior_path:
            return False, "Warrior path not available"
        
        ctx = context or {}
        assessment = self.warrior_path.assess_tactical_situation(market_context=ctx)
        
        if assessment.sun_tzu_can_win_without_fight:
            return True, "VETO - Win without fighting (information edge or passive income)"
        
        return False, assessment.sun_tzu_enemy_weakness

    async def _data_callback(self, event_type: str, data):
        """Handle real-time data events from open source feeds"""
        try:
            if event_type == 'market_data':
                # Update live prices
                self.live_prices[data.symbol] = data.price
                
                # Check for significant moves
                if abs(data.change_24h or 0) >= self.significant_move_pct:
                    alert = {
                        'type': 'SIGNIFICANT_MOVE',
                        'symbol': data.symbol,
                        'change': data.change_24h,
                        'price': data.price,
                        'timestamp': time.time(),
                        'message': f"🚨 {data.symbol} moved {data.change_24h:+.1f}% in 24h!"
                    }
                    self.market_alerts.append(alert)
                    logger.info(alert['message'])
            
            elif event_type == 'whale_alert':
                self.whale_alerts.append(data)
                logger.info(f"🐋 WHALE: {data.symbol} ${data.value_usd:,.0f} ({data.side.upper()})")
            
            elif event_type == 'sentiment_update':
                self.live_sentiment = data
                
                # Alert on extreme sentiment
                if data and hasattr(data, 'fear_greed_index'):
                    if data.fear_greed_index <= 20:
                        self.market_alerts.append({
                            'type': 'EXTREME_FEAR',
                            'value': data.fear_greed_index,
                            'timestamp': time.time(),
                            'message': f"😱 EXTREME FEAR! Index at {data.fear_greed_index} - Could be buying opportunity!"
                        })
                    elif data.fear_greed_index >= 80:
                        self.market_alerts.append({
                            'type': 'EXTREME_GREED',
                            'value': data.fear_greed_index,
                            'timestamp': time.time(),
                            'message': f"🤑 EXTREME GREED! Index at {data.fear_greed_index} - Be cautious!"
                        })
                        
        except Exception as e:
            logger.warning(f"Data callback error: {e}")
    
    def start_live_tracking(self):
        """
        🔴 START REAL-TIME MARKET TRACKING
        
        Queen monitors:
        - Live prices from multiple exchanges
        - Whale movements ($100K+ trades)
        - Fear & Greed changes
        - News sentiment shifts
        - Social volume spikes
        - Order book imbalances
        """
        # Ensure data engine is loaded
        if not _load_data_engine():
            logger.warning("⚠️ Cannot start live tracking - data engine not available")
            return False
        
        if not self.data_engine:
            self._wire_data_engine()
        
        if not self.data_engine:
            logger.warning("⚠️ Cannot start live tracking - data engine not wired")
            return False
        
        if self.live_tracking:
            logger.info("👑 Live tracking already running")
            return True
        
        try:
            # Set up callback
            self.data_engine.callback = self._data_callback
            
            # Start in background
            self.data_engine_thread = self.data_engine.start_background()
            self.live_tracking = True
            
            logger.info("🔴 LIVE TRACKING STARTED!")
            logger.info("   👁️ Queen is now watching the market in REAL-TIME")
            logger.info("   🐋 Whale alerts: ACTIVE")
            logger.info("   📊 Price tracking: ACTIVE")
            logger.info("   😱 Sentiment monitoring: ACTIVE")
            
            return True
        except Exception as e:
            logger.error(f"Failed to start live tracking: {e}")
            return False
    
    def stop_live_tracking(self):
        """Stop real-time tracking"""
        if self.data_engine:
            self.data_engine.stop()
        self.live_tracking = False
        logger.info("🛑 Live tracking stopped")
    
    def get_live_market_summary(self) -> Dict:
        """
        📊 GET REAL-TIME MARKET SUMMARY
        
        Returns live data from all open source feeds
        """
        if not self.data_engine:
            return {'error': 'Data engine not available'}
        
        try:
            # Get all data from engine
            market_data = self.data_engine.get_market_data()
            sentiment = self.data_engine.get_sentiment()
            whale_alerts = self.data_engine.get_whale_alerts(10)
            trending = self.data_engine.get_trending()
            intelligence = self.data_engine.get_market_intelligence()
            news = self.data_engine.get_news(5)
            social = self.data_engine.get_social_sentiment()
            order_books = self.data_engine.get_order_books()
            stats = self.data_engine.get_stats()
            
            # Calculate market mood
            fear_greed = sentiment.get('fear_greed_index', 50) if sentiment else 50
            if fear_greed <= 25:
                mood = "😱 EXTREME FEAR"
            elif fear_greed <= 45:
                mood = "😰 FEAR"
            elif fear_greed <= 55:
                mood = "😐 NEUTRAL"
            elif fear_greed <= 75:
                mood = "😊 GREED"
            else:
                mood = "🤑 EXTREME GREED"
            
            # BTC dominance indicator
            btc_data = market_data.get('BTC/USD', {})
            btc_change = btc_data.get('change_24h', 0) if btc_data else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'live_tracking': self.live_tracking,
                'mood': mood,
                'fear_greed': {
                    'index': fear_greed,
                    'label': sentiment.get('fear_greed_label', 'Unknown') if sentiment else 'Unknown'
                },
                'btc': {
                    'price': btc_data.get('price', 0) if btc_data else 0,
                    'change_24h': btc_change,
                    'volume': btc_data.get('volume_24h', 0) if btc_data else 0
                },
                'whale_activity': {
                    'recent_count': len(whale_alerts),
                    'alerts': whale_alerts[:5]
                },
                'trending_coins': trending[:5] if trending else [],
                'news_sentiment': news.get('sentiment_score', 0) if news else 0,
                'social_buzz': social,
                'order_book_bias': intelligence.get('order_book_bias', 'neutral'),
                'data_health': stats,
                'market_alerts': list(self.market_alerts)[-10:],
                'ocean': self.get_ocean_summary() if self.ocean_scanner else None,
                'cosmic': self.get_counter_phase() if self.solar_awareness else None
            }
        except Exception as e:
            logger.error(f"Error getting live summary: {e}")
            return {'error': str(e)}
    
    def get_queen_live_report(self) -> str:
        """
        👑📊 QUEEN'S LIVE MARKET REPORT
        
        Human-readable summary of what Queen sees RIGHT NOW
        """
        summary = self.get_live_market_summary()
        
        if 'error' in summary:
            return f"⚠️ Cannot generate live report: {summary['error']}"
        
        # Build report
        mood = summary.get('mood', '😐 NEUTRAL')
        fg = summary.get('fear_greed', {})
        btc = summary.get('btc', {})
        whales = summary.get('whale_activity', {})
        trending = summary.get('trending_coins', [])
        alerts = summary.get('market_alerts', [])
        
        # Get trending names
        trending_names = []
        for coin in trending[:3]:
            if isinstance(coin, dict) and 'item' in coin:
                trending_names.append(coin['item'].get('name', '?'))
            elif isinstance(coin, dict):
                trending_names.append(coin.get('name', coin.get('id', '?')))
        
        report = f"""
👑🔴 QUEEN'S LIVE MARKET REPORT
================================
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔴 Live Tracking: {'ACTIVE' if summary.get('live_tracking') else 'INACTIVE'}

🎭 MARKET MOOD: {mood}
   Fear & Greed Index: {fg.get('index', '?')}/100 ({fg.get('label', '?')})

₿ BITCOIN:
   Price: ${btc.get('price', 0):,.0f}
   24h Change: {btc.get('change_24h', 0):+.1f}%

🐋 WHALE ACTIVITY:
   Recent whale trades: {whales.get('recent_count', 0)}
   {'   ⚠️ Whales are ACTIVE!' if whales.get('recent_count', 0) > 5 else '   ✅ Normal activity'}

🔥 TRENDING:
   {', '.join(trending_names) if trending_names else 'No data'}

📰 NEWS SENTIMENT: {summary.get('news_sentiment', 0):+.2f}

📈 ORDER BOOK BIAS: {summary.get('order_book_bias', 'neutral').upper()}
"""
        
        # Add recent alerts
        if alerts:
            report += "\n🚨 RECENT ALERTS:\n"
            for alert in alerts[-5:]:
                report += f"   • {alert.get('message', str(alert))}\n"
        
        # Add Queen's take
        fg_index = fg.get('index', 50)
        btc_change = btc.get('change_24h', 0)
        
        report += "\n👑 QUEEN'S TAKE:\n"
        
        if fg_index <= 25:
            report += "   🔵 Extreme fear = potential BUYING opportunity\n"
            report += "   📊 Markets oversold - watch for reversal signals\n"
        elif fg_index >= 75:
            report += "   🔴 Extreme greed = be CAUTIOUS\n"
            report += "   📊 Markets may be overbought - take profits?\n"
        else:
            report += "   ⚪ Market sentiment is balanced\n"
        
        if btc_change <= -5:
            report += f"   📉 BTC down {abs(btc_change):.1f}% - HOLD positions, don't panic sell\n"
        elif btc_change >= 5:
            report += f"   📈 BTC up {btc_change:.1f}% - Market recovering!\n"
        
        # Add ocean scanner summary if available
        ocean = summary.get('ocean')
        if ocean and not ocean.get('error'):
            universe = ocean.get('universe_size', {})
            total = universe.get('total', 0)
            top_opps = ocean.get('top_5', [])
            report += f"""
🌊 OCEAN SCANNER (Full Market View):
   🌍 Universe: {total:,} tradeable opportunities
   🔥 Hot Opportunities: {ocean.get('hot_opportunities', 0)}
"""
            if top_opps:
                report += "   🎯 Top 3:\n"
                for opp in top_opps[:3]:
                    mom = opp.get('momentum_24h', 0)
                    emoji = '🚀' if mom > 5 else '📉' if mom < -5 else '📊'
                    report += f"      {emoji} {opp.get('symbol', '?')}: Score {opp.get('ocean_score', 0):.2f}, Mom {mom:+.1f}%\n"
        
        # Add cosmic/solar system awareness if available
        cosmic = summary.get('cosmic')
        if cosmic and not cosmic.get('error'):
            phase_diff = cosmic.get('phase_difference', 0)
            alignment = cosmic.get('alignment_quality', 0)
            action = cosmic.get('recommended_action', 'OBSERVE')
            
            # Determine cosmic status indicator
            if alignment > 0.7:
                cosmic_emoji = "🟢"
                cosmic_status = "OPTIMAL"
            elif alignment > 0.4:
                cosmic_emoji = "🟡"
                cosmic_status = "FAVORABLE"
            else:
                cosmic_emoji = "🔴"
                cosmic_status = "MISALIGNED"
            
            report += f"""
☀️🌍 COSMIC COUNTER-INTELLIGENCE:
   {cosmic_emoji} Phase: {phase_diff:.1f}° counter ({cosmic_status})
   🎯 Alignment Quality: {alignment:.1%}
   📊 Recommended: {action}
   💡 {cosmic.get('reasoning', '')}
"""
        
        return report
    
    def _fetch_btc_data(self) -> Dict:
        """Fetch current BTC data from multiple sources"""
        try:
            # Try Binance first
            resp = requests.get('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT', timeout=5)
            data = resp.json()
            
            btc_price = float(data.get('lastPrice', 0))
            btc_24h_change = float(data.get('priceChangePercent', 0))
            
            # Calculate 7d and 30d from reference prices
            jan_high = self.btc_reference_prices['jan_2026_high']
            btc_from_high = ((btc_price - jan_high) / jan_high) * 100
            
            return {
                'price': btc_price,
                'change_24h': btc_24h_change,
                'change_from_jan_high': btc_from_high,
                'source': 'binance'
            }
        except Exception as e:
            logger.warning(f"Failed to fetch BTC data: {e}")
            return {'price': 78000, 'change_24h': 0, 'change_from_jan_high': -28, 'source': 'fallback'}
    
    def _determine_market_state(self, btc_change: float) -> Tuple[str, float]:
        """Determine overall market state based on BTC movement"""
        if btc_change <= -30:
            return "CRASH", -1.0
        elif btc_change <= -20:
            return "BEAR", -0.7
        elif btc_change <= -10:
            return "CORRECTION", -0.4
        elif btc_change <= -5:
            return "DIP", -0.2
        elif btc_change < 5:
            return "SIDEWAYS", 0.0
        elif btc_change < 15:
            return "RECOVERY", 0.3
        elif btc_change < 30:
            return "BULL", 0.6
        else:
            return "MOON", 1.0
    
    def assess_market(self) -> MarketCondition:
        """
        👑 Assess overall market conditions
        
        Returns MarketCondition with full context
        """
        now = datetime.now()
        
        # Fetch BTC data
        btc_data = self._fetch_btc_data()
        btc_price = btc_data['price']
        btc_24h = btc_data['change_24h']
        btc_from_high = btc_data['change_from_jan_high']
        
        # Determine market state
        market_state, severity = self._determine_market_state(btc_from_high)
        
        # Build condition
        condition = MarketCondition(
            timestamp=now,
            btc_price=btc_price,
            btc_24h_change=btc_24h,
            btc_30d_change=btc_from_high,
        )
        
        condition.market_state = market_state
        condition.market_severity = severity
        
        # Should hold in down market?
        condition.should_hold = market_state in ("CRASH", "BEAR", "CORRECTION", "DIP")
        
        # Recovery outlook
        if market_state == "CRASH":
            condition.recovery_outlook = "🔴 CRASH: Recovery could take months. HOLD tight."
        elif market_state == "BEAR":
            condition.recovery_outlook = "🟠 BEAR MARKET: Recovery likely in weeks-months. HOLD."
        elif market_state == "CORRECTION":
            condition.recovery_outlook = "🟡 CORRECTION: Normal pullback. Recovery likely in days-weeks."
        elif market_state == "DIP":
            condition.recovery_outlook = "🟢 DIP: Small pullback. Recovery likely soon."
        else:
            condition.recovery_outlook = f"📈 Market is {market_state}. Good conditions."
        
        # Queen's message
        if condition.should_hold:
            condition.queen_message = f"""
👑 QUEEN'S MARKET ASSESSMENT:

📊 MARKET STATUS: {market_state}
   BTC: ${btc_price:,.0f} ({btc_from_high:+.1f}% from Jan high)

🌍 THE WHOLE MARKET IS DOWN
   This is NOT just your coins - EVERYONE is down.
   BTC dropped {abs(btc_from_high):.0f}% from January highs.

📝 YOUR LOSSES ARE PAPER LOSSES
   You haven't sold, so you haven't lost anything.
   Paper losses become real ONLY if you sell.

🛡️ MY ADVICE: HOLD
   {condition.recovery_outlook}
   
   When BTC recovers, your altcoins will likely recover even faster.
   Small-caps typically bounce 2-3x harder than BTC.

💎 DIAMOND HANDS MODE ACTIVE
   I will NOT sell your positions at a loss.
   We wait for recovery.
"""
        else:
            condition.queen_message = f"""
👑 QUEEN'S MARKET ASSESSMENT:

📊 MARKET STATUS: {market_state}
   BTC: ${btc_price:,.0f} ({btc_24h:+.1f}% 24h)

📈 Market conditions are favorable.
   Normal trading operations can proceed.
"""
        
        self.market_condition = condition
        self._save_state()
        
        return condition
    
    def assess_position(self, asset: str, qty: float, cost_basis: float, 
                       current_value: float, realized_pnl: float = 0) -> PositionContext:
        """
        👑 Assess a single position in market context
        
        Returns PositionContext with full analysis
        """
        # Ensure we have market data
        if not self.market_condition:
            self.assess_market()
        
        market = self.market_condition
        
        # Calculate P&L
        paper_pnl = current_value - cost_basis
        paper_pnl_pct = (paper_pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        # Compare to BTC
        btc_drop = market.btc_30d_change if market else -23
        drop_vs_btc = paper_pnl_pct - btc_drop
        
        # Is this coin tracking BTC or doing its own thing?
        # If within 15% of BTC's move, it's correlated
        is_tracking = abs(drop_vs_btc) < 15
        
        # Determine loss reason
        if paper_pnl >= 0:
            loss_reason = "NONE"
        elif is_tracking:
            loss_reason = "MARKET_WIDE"
        elif paper_pnl_pct < btc_drop - 15:
            loss_reason = "COIN_SPECIFIC"  # Doing worse than market
        else:
            loss_reason = "BOTH"
        
        # Recovery probability
        if loss_reason == "MARKET_WIDE":
            recovery_prob = "HIGH"  # Will recover with market
        elif loss_reason == "COIN_SPECIFIC":
            recovery_prob = "MEDIUM"  # Depends on the project
        elif loss_reason == "BOTH":
            recovery_prob = "MEDIUM"
        else:
            recovery_prob = "N/A"  # Not at a loss
        
        # Queen's advice
        if paper_pnl >= 0:
            advice = f"✅ {asset} is at profit. Consider taking gains if target met."
        elif loss_reason == "MARKET_WIDE":
            advice = f"🌍 {asset} is down with the market ({paper_pnl_pct:+.1f}% vs BTC {btc_drop:+.1f}%). HOLD - will recover with market."
        elif loss_reason == "COIN_SPECIFIC":
            advice = f"⚠️ {asset} is underperforming market ({paper_pnl_pct:+.1f}% vs BTC {btc_drop:+.1f}%). Evaluate project fundamentals."
        else:
            advice = f"🔍 {asset} mixed signals. HOLD for now, monitor closely."
        
        return PositionContext(
            asset=asset,
            qty_held=qty,
            cost_basis=cost_basis,
            current_value=current_value,
            paper_pnl=paper_pnl,
            paper_pnl_pct=paper_pnl_pct,
            realized_pnl=realized_pnl,
            drop_vs_btc=drop_vs_btc,
            is_tracking_btc=is_tracking,
            loss_reason=loss_reason,
            recovery_probability=recovery_prob,
            queen_advice=advice
        )
    
    def get_portfolio_context(self, positions: List[Dict]) -> Dict:
        """
        👑 Get full portfolio context with market awareness
        
        Args:
            positions: List of {asset, qty, cost_basis, current_value}
        
        Returns:
            Full portfolio analysis with market context
        """
        # Assess market first
        market = self.assess_market()
        
        # Analyze each position
        position_contexts = []
        total_cost = 0
        total_value = 0
        total_paper_pnl = 0
        
        for pos in positions:
            ctx = self.assess_position(
                asset=pos.get('asset', 'UNKNOWN'),
                qty=pos.get('qty', 0),
                cost_basis=pos.get('cost_basis', 0),
                current_value=pos.get('current_value', 0),
                realized_pnl=pos.get('realized_pnl', 0)
            )
            position_contexts.append(ctx)
            total_cost += ctx.cost_basis
            total_value += ctx.current_value
            total_paper_pnl += ctx.paper_pnl
        
        # Portfolio vs BTC
        portfolio_pnl_pct = (total_paper_pnl / total_cost * 100) if total_cost > 0 else 0
        portfolio_vs_btc = portfolio_pnl_pct - market.btc_30d_change
        
        # Count by loss reason
        market_losses = sum(1 for p in position_contexts if p.loss_reason == "MARKET_WIDE")
        coin_losses = sum(1 for p in position_contexts if p.loss_reason == "COIN_SPECIFIC")
        profitable = sum(1 for p in position_contexts if p.paper_pnl >= 0)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'market': {
                'state': market.market_state,
                'severity': market.market_severity,
                'btc_price': market.btc_price,
                'btc_change': market.btc_30d_change,
                'should_hold': market.should_hold,
                'outlook': market.recovery_outlook,
                'queen_message': market.queen_message
            },
            'portfolio': {
                'total_cost_basis': total_cost,
                'total_current_value': total_value,
                'total_paper_pnl': total_paper_pnl,
                'paper_pnl_pct': portfolio_pnl_pct,
                'vs_btc': portfolio_vs_btc,
                'positions': len(position_contexts),
                'profitable': profitable,
                'market_losses': market_losses,
                'coin_specific_losses': coin_losses
            },
            'positions': [asdict(p) for p in position_contexts],
            'queen_summary': self._generate_summary(market, position_contexts, total_paper_pnl, portfolio_vs_btc)
        }
    
    def _generate_summary(self, market: MarketCondition, positions: List[PositionContext],
                         total_paper_pnl: float, portfolio_vs_btc: float) -> str:
        """Generate Queen's summary message"""
        
        market_losses = sum(1 for p in positions if p.loss_reason == "MARKET_WIDE")
        coin_losses = sum(1 for p in positions if p.loss_reason == "COIN_SPECIFIC")
        profitable = sum(1 for p in positions if p.paper_pnl >= 0)
        
        if total_paper_pnl >= 0:
            return f"""
👑 QUEEN'S PORTFOLIO SUMMARY:

✅ PORTFOLIO IS IN PROFIT
   Total Paper P&L: ${total_paper_pnl:+.2f}
   
Keep up the good work! 💎
"""
        
        return f"""
👑 QUEEN'S PORTFOLIO SUMMARY:

📊 MARKET STATUS: {market.market_state}
   BTC is down {abs(market.btc_30d_change):.0f}% from January highs.

📝 YOUR PAPER LOSSES: ${total_paper_pnl:.2f}
   These are NOT real losses until you sell.
   
🔍 LOSS BREAKDOWN:
   🌍 {market_losses} positions down WITH the market (will recover)
   ⚠️ {coin_losses} positions underperforming market (monitor)
   ✅ {profitable} positions in profit

📈 YOUR PERFORMANCE vs BTC: {portfolio_vs_btc:+.1f}%
   {"You're doing BETTER than Bitcoin! 👑" if portfolio_vs_btc > 0 else "Slightly behind BTC - normal for altcoins in down markets."}

🛡️ QUEEN'S STRATEGY: {"HOLD" if market.should_hold else "NORMAL TRADING"}
   {market.recovery_outlook}

💎 REMEMBER:
   - Paper losses are NOT real losses
   - The market is cyclical - it WILL recover
   - When BTC pumps, altcoins pump HARDER
   - Diamond hands win long-term

I am protecting your positions and will NOT sell at a loss. 👑
"""
    
    def _save_state(self):
        """Save market state to file"""
        try:
            if self.market_condition:
                data = {
                    'timestamp': self.market_condition.timestamp.isoformat(),
                    'btc_price': self.market_condition.btc_price,
                    'btc_30d_change': self.market_condition.btc_30d_change,
                    'market_state': self.market_condition.market_state,
                    'severity': self.market_condition.market_severity,
                    'should_hold': self.market_condition.should_hold,
                    'outlook': self.market_condition.recovery_outlook
                }
                with open(self.state_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save market state: {e}")
    
    def load_state(self) -> Optional[MarketCondition]:
        """Load market state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file) as f:
                    data = json.load(f)
                # Recreate MarketCondition
                condition = MarketCondition(
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    btc_price=data.get('btc_price', 0),
                    btc_30d_change=data.get('btc_30d_change', 0),
                    market_state=data.get('market_state', 'UNKNOWN'),
                    market_severity=data.get('severity', 0),
                    should_hold=data.get('should_hold', True),
                    recovery_outlook=data.get('outlook', '')
                )
                self.market_condition = condition
                return condition
        except Exception as e:
            logger.warning(f"Failed to load market state: {e}")
        return None


# ============================================================================
# STANDALONE TEST
# ============================================================================

def main():
    """Test the market awareness system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Queen Market Awareness')
    parser.add_argument('--live', action='store_true', help='Start live tracking')
    parser.add_argument('--report', action='store_true', help='Show live report')
    args = parser.parse_args()
    
    print("=" * 80)
    print("👑🌍 QUEEN MARKET AWARENESS TEST")
    print("=" * 80)
    
    awareness = QueenMarketAwareness()
    
    # If live tracking requested
    if args.live:
        print("\n🔴 STARTING LIVE MARKET TRACKING...")
        print("Press Ctrl+C to stop\n")
        
        awareness.start_live_tracking()
        
        try:
            while True:
                time.sleep(30)  # Print report every 30 seconds
                print("\n" + "=" * 80)
                print(awareness.get_queen_live_report())
                print("=" * 80)
        except KeyboardInterrupt:
            awareness.stop_live_tracking()
            print("\n👑 Live tracking stopped")
        return
    
    # If just report requested
    if args.report:
        print("\n📊 Getting live market data...")
        summary = awareness.get_live_market_summary()
        print(awareness.get_queen_live_report())
        return
    
    # Standard market assessment
    market = awareness.assess_market()
    print(market.queen_message)
    
    # Test with sample positions (from unified_pnl_state.json)
    try:
        with open('/workspaces/aureon-trading/unified_pnl_state.json') as f:
            pnl_data = json.load(f)
        
        positions = []
        for p in pnl_data.get('positions', []):
            positions.append({
                'asset': p['asset'],
                'qty': p['qty_held'],
                'cost_basis': p['cost_basis'],
                'current_value': p['current_value'],
                'realized_pnl': p.get('realized_pnl', 0)
            })
        
        # Get full context
        context = awareness.get_portfolio_context(positions)
        
        print("\n" + "=" * 80)
        print("📊 POSITION-BY-POSITION ANALYSIS")
        print("=" * 80)
        
        for pos in context['positions']:
            status = "🟢" if pos['paper_pnl'] >= 0 else "🔴"
            reason = pos['loss_reason']
            prob = pos['recovery_probability']
            print(f"\n{status} {pos['asset']}:")
            print(f"   Paper P&L: ${pos['paper_pnl']:+.2f} ({pos['paper_pnl_pct']:+.1f}%)")
            print(f"   vs BTC: {pos['drop_vs_btc']:+.1f}%")
            print(f"   Loss Reason: {reason}")
            print(f"   Recovery: {prob}")
            print(f"   Advice: {pos['queen_advice']}")
        
        print("\n" + "=" * 80)
        print(context['queen_summary'])
        print("=" * 80)
        
    except FileNotFoundError:
        print("No unified_pnl_state.json found - run unified_pnl_tracker.py first")
    
    # Show available open source data sources
    print("\n" + "=" * 80)
    print("🌐 OPEN SOURCE DATA SOURCES AVAILABLE:")
    print("=" * 80)
    print("""
📊 PRICE DATA (FREE):
   • CoinGecko API - Prices, Market Cap, Volume
   • Binance Public WebSocket - Live trades
   • Kraken Public WebSocket - Live trades
   • Coinbase Public WebSocket - Live trades

😱 SENTIMENT DATA (FREE):
   • Fear & Greed Index (alternative.me)
   • News Sentiment (CryptoCompare)
   • Reddit Social Volume (r/cryptocurrency, r/bitcoin)

🐋 WHALE TRACKING (FREE):
   • Large trade detection (>$100K)
   • Order book imbalance analysis
   • Spoofing/manipulation detection

🔗 BLOCKCHAIN DATA (FREE):
   • Mempool.space - Bitcoin network stats
   • BlockCypher - BTC/ETH blockchain data
   • DeFi Llama - TVL data

📈 To start LIVE tracking, run:
   python queen_market_awareness.py --live
""")

if __name__ == '__main__':
    main()
