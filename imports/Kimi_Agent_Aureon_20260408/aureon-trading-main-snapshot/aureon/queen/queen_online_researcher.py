#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║      👑🌐 QUEEN'S ONLINE RESEARCHER - Self-Enhancement Engine 🌐👑              ║
║                                                                                ║
║     "I search, I learn, I evolve, I profit."                                   ║
║                                                                                ║
║     Gives the Queen ability to:                                                ║
║     1. Search online for trading strategies and code patterns                  ║
║     2. Fetch documentation from APIs and libraries                             ║
║     3. Research market data sources and techniques                             ║
║     4. Generate enhanced code based on findings                                ║
║     5. Apply improvements and track revenue impact                             ║
║                                                                                ║
║     THE QUEEN CAN ENHANCE HERSELF BY LEARNING FROM THE INTERNET!               ║
║                                                                                ║
║     Gary Leckey | January 2026 | "Let her learn and grow"                      ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import logging
import asyncio
import aiohttp
import ssl
import certifi
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ResearchTopic(Enum):
    """Topics the Queen can research online"""
    TRADING_STRATEGY = "trading_strategy"
    CRYPTO_PATTERNS = "crypto_patterns"
    MOMENTUM_INDICATORS = "momentum_indicators"
    RISK_MANAGEMENT = "risk_management"
    API_DOCUMENTATION = "api_documentation"
    CODE_OPTIMIZATION = "code_optimization"
    MARKET_ANALYSIS = "market_analysis"


@dataclass
class ResearchFinding:
    """A piece of knowledge the Queen discovered"""
    topic: str
    source: str
    title: str
    content: str
    code_snippet: Optional[str] = None
    relevance_score: float = 0.5
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    applied: bool = False
    revenue_impact: float = 0.0


@dataclass
class CodeEnhancement:
    """A code improvement the Queen generated"""
    name: str
    description: str
    original_code: Optional[str]
    enhanced_code: str
    source_research: List[str]  # Research findings that inspired this
    expected_improvement: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    applied: bool = False
    measured_revenue: float = 0.0


class QueenOnlineResearcher:
    """
    👑🌐 The Queen's Internet Research Capability
    
    The Queen can:
    - Search online for trading knowledge
    - Fetch API documentation
    - Learn from code repositories
    - Generate enhanced strategies
    - Track revenue from improvements
    """
    
    def __init__(self, repo_path: str = None):
        self.repo_path = Path(repo_path or os.getcwd())
        self.research_dir = self.repo_path / "queen_research"
        self.research_dir.mkdir(exist_ok=True, parents=True)
        
        # Knowledge base
        self.findings: List[ResearchFinding] = []
        self.enhancements: List[CodeEnhancement] = []
        self.total_revenue_generated: float = 0.0
        
        # API sources the Queen can query
        self.knowledge_sources = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'binance_api': 'https://api.binance.com/api/v3',
            'kraken_api': 'https://api.kraken.com/0/public',
            'github_raw': 'https://raw.githubusercontent.com',
            'pypi': 'https://pypi.org/pypi',
        }
        
        # Pre-loaded trading knowledge patterns the Queen knows to search for
        self.trading_patterns = [
            "momentum_crossover",
            "mean_reversion",
            "breakout_detection",
            "volume_surge",
            "trend_following",
            "arbitrage_detection",
            "whale_tracking",
            "sentiment_analysis"
        ]
        
        # Load previous research
        self._load_research_history()
        
        logger.info("👑🌐 Queen's Online Researcher is ONLINE!")
        logger.info(f"   📚 Research dir: {self.research_dir}")
        logger.info(f"   🔍 Knowledge sources: {len(self.knowledge_sources)}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🌐 ONLINE RESEARCH CAPABILITIES
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def research_trading_strategies(self) -> List[ResearchFinding]:
        """
        👑🔍 Search online for trading strategy improvements.
        
        Returns list of research findings with code patterns.
        """
        logger.info("👑🔍 Queen researching trading strategies online...")
        findings = []
        
        # Research from multiple sources
        try:
            # 1. Fetch market data patterns from CoinGecko
            market_patterns = await self._research_market_patterns()
            findings.extend(market_patterns)
            
            # 2. Analyze Binance trading pairs for opportunities
            binance_insights = await self._research_binance_patterns()
            findings.extend(binance_insights)
            
            # 3. Check Kraken for market conditions
            kraken_insights = await self._research_kraken_patterns()
            findings.extend(kraken_insights)
            
            # 4. Generate code patterns from findings
            code_patterns = self._generate_code_from_research(findings)
            findings.extend(code_patterns)
            
        except Exception as e:
            logger.error(f"👑⚠️ Research error: {e}")
        
        # Store findings
        self.findings.extend(findings)
        self._save_research_history()
        
        logger.info(f"👑📚 Queen found {len(findings)} new insights!")
        return findings
    
    async def _research_market_patterns(self) -> List[ResearchFinding]:
        """Research market patterns from CoinGecko"""
        findings = []
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get trending coins
                url = f"{self.knowledge_sources['coingecko']}/search/trending"
                async with session.get(url, ssl=ssl_context, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        coins = data.get('coins', [])[:5]
                        
                        # Generate insight
                        trending_symbols = [c.get('item', {}).get('symbol', '') for c in coins]
                        findings.append(ResearchFinding(
                            topic="trending_coins",
                            source="coingecko",
                            title="Trending Coins Pattern",
                            content=f"Currently trending: {', '.join(trending_symbols)}",
                            code_snippet=self._generate_trending_code(trending_symbols),
                            relevance_score=0.7
                        ))
                        logger.info(f"👑📊 Trending coins: {trending_symbols}")
                
                # Get global market data
                url = f"{self.knowledge_sources['coingecko']}/global"
                async with session.get(url, ssl=ssl_context, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        market_data = data.get('data', {})
                        
                        btc_dom = market_data.get('market_cap_percentage', {}).get('btc', 0)
                        market_cap_change = market_data.get('market_cap_change_percentage_24h_usd', 0)
                        
                        findings.append(ResearchFinding(
                            topic="market_sentiment",
                            source="coingecko",
                            title="Global Market Sentiment",
                            content=f"BTC Dominance: {btc_dom:.1f}%, 24h Change: {market_cap_change:.2f}%",
                            code_snippet=self._generate_sentiment_code(btc_dom, market_cap_change),
                            relevance_score=0.8
                        ))
                        
        except Exception as e:
            logger.warning(f"👑⚠️ CoinGecko research error: {e}")
        
        return findings
    
    async def _research_binance_patterns(self) -> List[ResearchFinding]:
        """Research trading patterns from Binance"""
        findings = []
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get top volume pairs
                url = f"{self.knowledge_sources['binance_api']}/ticker/24hr"
                async with session.get(url, ssl=ssl_context, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Filter USDT pairs and sort by volume
                        usdt_pairs = [d for d in data if d.get('symbol', '').endswith('USDT')]
                        sorted_by_volume = sorted(
                            usdt_pairs,
                            key=lambda x: float(x.get('quoteVolume', 0)),
                            reverse=True
                        )[:10]
                        
                        # Find biggest gainers
                        gainers = sorted(
                            usdt_pairs,
                            key=lambda x: float(x.get('priceChangePercent', 0)),
                            reverse=True
                        )[:5]
                        
                        gainer_symbols = [g['symbol'].replace('USDT', '') for g in gainers]
                        gainer_changes = [float(g['priceChangePercent']) for g in gainers]
                        
                        findings.append(ResearchFinding(
                            topic="momentum_leaders",
                            source="binance",
                            title="Top Momentum Leaders",
                            content=f"Top gainers: {dict(zip(gainer_symbols, gainer_changes))}",
                            code_snippet=self._generate_momentum_code(gainer_symbols, gainer_changes),
                            relevance_score=0.85
                        ))
                        
                        # Find volume spikes
                        high_volume = [p for p in sorted_by_volume[:20] 
                                      if float(p.get('priceChangePercent', 0)) > 5]
                        
                        if high_volume:
                            findings.append(ResearchFinding(
                                topic="volume_spike",
                                source="binance",
                                title="Volume Spike Detection",
                                content=f"High volume + price increase detected in {len(high_volume)} pairs",
                                code_snippet=self._generate_volume_spike_code(),
                                relevance_score=0.9
                            ))
                        
        except Exception as e:
            logger.warning(f"👑⚠️ Binance research error: {e}")
        
        return findings
    
    async def _research_kraken_patterns(self) -> List[ResearchFinding]:
        """Research from Kraken market data"""
        findings = []
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get ticker info
                url = f"{self.knowledge_sources['kraken_api']}/Ticker?pair=XBTUSD,ETHUSD,SOLUSD"
                async with session.get(url, ssl=ssl_context, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data.get('result', {})
                        
                        # Analyze volatility
                        volatility_insights = []
                        for pair, info in result.items():
                            high = float(info.get('h', [0, 0])[1])  # 24h high
                            low = float(info.get('l', [0, 0])[1])   # 24h low
                            if low > 0:
                                volatility = ((high - low) / low) * 100
                                volatility_insights.append(f"{pair}: {volatility:.2f}%")
                        
                        if volatility_insights:
                            findings.append(ResearchFinding(
                                topic="volatility_analysis",
                                source="kraken",
                                title="Volatility Patterns",
                                content=f"24h volatility: {', '.join(volatility_insights)}",
                                code_snippet=self._generate_volatility_code(),
                                relevance_score=0.75
                            ))
                        
        except Exception as e:
            logger.warning(f"👑⚠️ Kraken research error: {e}")
        
        return findings
    
    def _generate_code_from_research(self, findings: List[ResearchFinding]) -> List[ResearchFinding]:
        """Generate actionable code patterns from research findings"""
        code_findings = []
        
        # Synthesize findings into trading rules
        momentum_findings = [f for f in findings if 'momentum' in f.topic.lower()]
        volume_findings = [f for f in findings if 'volume' in f.topic.lower()]
        
        if momentum_findings and volume_findings:
            # Combined momentum + volume strategy
            code_findings.append(ResearchFinding(
                topic="combined_strategy",
                source="queen_synthesis",
                title="Queen's Synthesized Strategy",
                content="Combined momentum + volume detection for optimal entry",
                code_snippet=self._generate_combined_strategy_code(),
                relevance_score=0.95
            ))
        
        return code_findings
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 💡 CODE GENERATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _generate_trending_code(self, symbols: List[str]) -> str:
        """Generate code to prioritize trending coins"""
        return f'''
# 👑 Queen's Trending Coin Boost (Auto-generated from research)
QUEEN_TRENDING_BOOST = {{
    {", ".join([f"'{s}': 1.25" for s in symbols])}  # +25% score boost
}}

def apply_trending_boost(symbol: str, base_score: float) -> float:
    """Apply boost to trending coins discovered by Queen's research."""
    boost = QUEEN_TRENDING_BOOST.get(symbol.upper(), 1.0)
    return base_score * boost
'''
    
    def _generate_sentiment_code(self, btc_dom: float, market_change: float) -> str:
        """Generate code for market sentiment trading"""
        sentiment = "bullish" if market_change > 0 else "bearish"
        return f'''
# 👑 Queen's Market Sentiment Analysis (Auto-generated)
QUEEN_MARKET_SENTIMENT = {{
    'btc_dominance': {btc_dom:.2f},
    'market_24h_change': {market_change:.2f},
    'sentiment': '{sentiment}',
    'alt_season': {btc_dom < 45}  # Alt season when BTC dom < 45%
}}

def get_sentiment_multiplier() -> float:
    """Get trading aggressiveness based on market sentiment."""
    if QUEEN_MARKET_SENTIMENT['sentiment'] == 'bullish':
        return 1.2 if QUEEN_MARKET_SENTIMENT['alt_season'] else 1.1
    return 0.8  # More conservative in bearish markets
'''
    
    def _generate_momentum_code(self, symbols: List[str], changes: List[float]) -> str:
        """Generate momentum tracking code"""
        pairs = dict(zip(symbols, changes))
        return f'''
# 👑 Queen's Momentum Leaders (Auto-generated from live research)
QUEEN_MOMENTUM_LEADERS = {json.dumps(pairs, indent=4)}

def is_momentum_leader(symbol: str) -> Tuple[bool, float]:
    """Check if symbol is a current momentum leader."""
    change = QUEEN_MOMENTUM_LEADERS.get(symbol.upper(), 0)
    return change > 5.0, change  # Leader if >5% gain
    
def get_momentum_priority(symbols: List[str]) -> List[str]:
    """Sort symbols by momentum priority."""
    return sorted(
        symbols,
        key=lambda s: QUEEN_MOMENTUM_LEADERS.get(s.upper(), 0),
        reverse=True
    )
'''
    
    def _generate_volume_spike_code(self) -> str:
        """Generate volume spike detection code"""
        return '''
# 👑 Queen's Volume Spike Detector (Auto-generated)
class QueenVolumeSpikeDetector:
    """Detect volume spikes that often precede price movements."""
    
    def __init__(self, spike_threshold: float = 2.0):
        self.threshold = spike_threshold  # 2x normal volume
        self.volume_history = {}
    
    def check_spike(self, symbol: str, current_volume: float) -> Tuple[bool, float]:
        """Check if current volume is a spike."""
        history = self.volume_history.get(symbol, [])
        
        if len(history) < 5:
            # Not enough history
            self.volume_history.setdefault(symbol, []).append(current_volume)
            return False, 1.0
        
        avg_volume = sum(history[-10:]) / len(history[-10:])
        spike_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Update history
        self.volume_history[symbol].append(current_volume)
        if len(self.volume_history[symbol]) > 20:
            self.volume_history[symbol] = self.volume_history[symbol][-20:]
        
        return spike_ratio > self.threshold, spike_ratio

# Singleton
_queen_volume_detector = QueenVolumeSpikeDetector()

def queen_check_volume_spike(symbol: str, volume: float) -> Tuple[bool, float]:
    """Queen's volume spike check."""
    return _queen_volume_detector.check_spike(symbol, volume)
'''
    
    def _generate_volatility_code(self) -> str:
        """Generate volatility-based trading code"""
        return '''
# 👑 Queen's Volatility Analyzer (Auto-generated)
def queen_calculate_volatility_score(high: float, low: float, current: float) -> float:
    """
    Calculate volatility score for position sizing.
    
    Returns:
        Score 0-1 where higher = more volatile = smaller positions
    """
    if low <= 0:
        return 0.5
    
    range_pct = ((high - low) / low) * 100
    
    # Map to score (0-1)
    # < 2% = low volatility = score 0.2 (larger positions OK)
    # 2-5% = medium = score 0.5
    # > 5% = high = score 0.8 (smaller positions)
    if range_pct < 2:
        return 0.2
    elif range_pct < 5:
        return 0.5
    elif range_pct < 10:
        return 0.7
    return 0.9

def queen_adjust_position_for_volatility(base_amount: float, volatility_score: float) -> float:
    """Reduce position size in high volatility."""
    adjustment = 1.0 - (volatility_score * 0.5)  # Max 50% reduction
    return base_amount * max(0.3, adjustment)
'''
    
    def _generate_combined_strategy_code(self) -> str:
        """Generate combined strategy from multiple research sources"""
        return '''
# 👑 Queen's Synthesized Strategy (Auto-generated from combined research)
class QueenEnhancedStrategy:
    """
    Combined momentum + volume + sentiment strategy.
    Generated by Queen's Online Researcher.
    """
    
    def __init__(self):
        self.name = "queen_synthesized_v1"
        self.momentum_weight = 0.4
        self.volume_weight = 0.3
        self.sentiment_weight = 0.3
    
    def evaluate_opportunity(
        self,
        symbol: str,
        price_change_24h: float,
        volume_ratio: float,
        market_sentiment: str
    ) -> Tuple[float, str]:
        """
        Evaluate a trading opportunity using Queen's synthesized strategy.
        
        Returns:
            (score 0-1, reasoning)
        """
        reasons = []
        
        # Momentum score (0-1)
        momentum_score = min(1.0, max(0, price_change_24h / 10))  # Normalize to 10%
        if price_change_24h > 5:
            reasons.append(f"Strong momentum +{price_change_24h:.1f}%")
        
        # Volume score (0-1)
        volume_score = min(1.0, volume_ratio / 3)  # 3x volume = max score
        if volume_ratio > 2:
            reasons.append(f"Volume spike {volume_ratio:.1f}x")
        
        # Sentiment score (0-1)
        sentiment_score = 0.7 if market_sentiment == 'bullish' else 0.3
        reasons.append(f"Market {market_sentiment}")
        
        # Combined score
        total_score = (
            momentum_score * self.momentum_weight +
            volume_score * self.volume_weight +
            sentiment_score * self.sentiment_weight
        )
        
        return total_score, " | ".join(reasons)

# Singleton
_queen_strategy = QueenEnhancedStrategy()

def queen_evaluate_trade(symbol: str, price_change: float, volume_ratio: float, sentiment: str):
    """Quick access to Queen's synthesized evaluation."""
    return _queen_strategy.evaluate_opportunity(symbol, price_change, volume_ratio, sentiment)
'''
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🏗️ CODE ENHANCEMENT & APPLICATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def generate_enhancement_from_research(self) -> Optional[CodeEnhancement]:
        """
        👑🏗️ Generate a code enhancement based on recent research.
        
        Returns a CodeEnhancement ready to be applied.
        """
        if not self.findings:
            logger.info("👑📚 No research findings to generate enhancements from")
            return None
        
        # Get most relevant recent findings
        recent = sorted(
            [f for f in self.findings if not f.applied],
            key=lambda x: x.relevance_score,
            reverse=True
        )[:5]
        
        if not recent:
            return None
        
        # Combine code snippets into enhancement
        combined_code = f'''#!/usr/bin/env python3
"""
👑🌐 QUEEN AUTO-GENERATED ENHANCEMENT
═══════════════════════════════════════════════════════════════
Generated: {datetime.now().isoformat()}
Based on: {len(recent)} research findings
Sources: {", ".join(set(f.source for f in recent))}

This code was generated by Queen Sero based on her online research.
She analyzed market data, detected patterns, and synthesized this strategy.
"""

from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

'''
        for finding in recent:
            if finding.code_snippet:
                combined_code += f"\n# From: {finding.source} - {finding.title}\n"
                combined_code += finding.code_snippet
                combined_code += "\n"
        
        # Add integration code
        combined_code += '''

# ═══════════════════════════════════════════════════════════════════════════
# 👑 QUEEN'S MASTER EVALUATOR
# ═══════════════════════════════════════════════════════════════════════════

def queen_research_score(
    symbol: str,
    price: float,
    volume: float,
    price_change_24h: float = 0,
    high_24h: float = 0,
    low_24h: float = 0
) -> Tuple[float, List[str]]:
    """
    👑 Queen's master scoring function using all research-generated insights.
    
    Returns:
        (score 0-100, list of reasons)
    """
    score = 50.0  # Base score
    reasons = []
    
    # Apply trending boost if available
    if 'QUEEN_TRENDING_BOOST' in globals():
        boost = QUEEN_TRENDING_BOOST.get(symbol.upper(), 1.0)
        if boost > 1.0:
            score += 10
            reasons.append(f"Trending +{(boost-1)*100:.0f}%")
    
    # Apply momentum leader boost
    if 'QUEEN_MOMENTUM_LEADERS' in globals():
        momentum = QUEEN_MOMENTUM_LEADERS.get(symbol.upper(), 0)
        if momentum > 5:
            score += 15
            reasons.append(f"Momentum leader +{momentum:.1f}%")
    
    # Apply market sentiment
    if 'QUEEN_MARKET_SENTIMENT' in globals():
        if QUEEN_MARKET_SENTIMENT.get('sentiment') == 'bullish':
            score += 5
            reasons.append("Bullish market")
    
    # Apply volatility adjustment
    if high_24h > 0 and low_24h > 0:
        vol_score = queen_calculate_volatility_score(high_24h, low_24h, price)
        if vol_score < 0.5:
            score += 5
            reasons.append("Low volatility (safe)")
        elif vol_score > 0.7:
            score -= 10
            reasons.append("High volatility (risky)")
    
    return min(100, max(0, score)), reasons


# Mark as Queen-generated
QUEEN_GENERATED = True
QUEEN_RESEARCH_VERSION = "1.0"
'''
        
        enhancement = CodeEnhancement(
            name="queen_research_enhancement",
            description=f"Auto-generated from {len(recent)} research findings",
            original_code=None,
            enhanced_code=combined_code,
            source_research=[f.title for f in recent],
            expected_improvement="Better trade selection based on live market research"
        )
        
        self.enhancements.append(enhancement)
        
        # Mark findings as applied
        for f in recent:
            f.applied = True
        
        self._save_research_history()
        
        logger.info(f"👑🏗️ Generated enhancement: {enhancement.name}")
        return enhancement
    
    def apply_enhancement(self, enhancement: CodeEnhancement, architect) -> Dict[str, Any]:
        """
        👑 Apply a code enhancement using the Code Architect.
        
        Args:
            enhancement: The enhancement to apply
            architect: QueenCodeArchitect instance
            
        Returns:
            Result dict with status and file path
        """
        if not architect:
            return {'status': 'error', 'reason': 'Code Architect not available'}
        
        # Write enhancement file
        filename = f"queen_strategies/{enhancement.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        
        success = architect.write_file(filename, enhancement.enhanced_code)
        
        if success:
            enhancement.applied = True
            self._save_research_history()
            
            logger.info(f"👑✅ Enhancement applied: {filename}")
            return {
                'status': 'success',
                'file': filename,
                'enhancement': enhancement.name
            }
        
        return {'status': 'error', 'reason': 'Failed to write file'}
    
    def track_revenue_impact(self, enhancement_name: str, revenue: float):
        """
        👑💰 Track revenue generated by an enhancement.
        """
        for e in self.enhancements:
            if e.name == enhancement_name:
                e.measured_revenue += revenue
                self.total_revenue_generated += revenue
                self._save_research_history()
                logger.info(f"👑💰 {enhancement_name} generated ${revenue:.4f} (total: ${e.measured_revenue:.4f})")
                return
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 💾 PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _save_research_history(self):
        """Save research history to disk"""
        history = {
            'findings': [
                {
                    'topic': f.topic,
                    'source': f.source,
                    'title': f.title,
                    'content': f.content,
                    'relevance_score': f.relevance_score,
                    'discovered_at': f.discovered_at,
                    'applied': f.applied
                }
                for f in self.findings[-100:]  # Keep last 100
            ],
            'enhancements': [
                {
                    'name': e.name,
                    'description': e.description,
                    'source_research': e.source_research,
                    'generated_at': e.generated_at,
                    'applied': e.applied,
                    'measured_revenue': e.measured_revenue
                }
                for e in self.enhancements[-50:]  # Keep last 50
            ],
            'total_revenue': self.total_revenue_generated,
            'last_updated': datetime.now().isoformat()
        }
        
        history_file = self.research_dir / "research_history.json"
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _load_research_history(self):
        """Load previous research history"""
        history_file = self.research_dir / "research_history.json"
        if history_file.exists():
            try:
                with open(history_file) as f:
                    history = json.load(f)
                
                self.total_revenue_generated = history.get('total_revenue', 0.0)
                logger.info(f"👑📚 Loaded research history: ${self.total_revenue_generated:.4f} total revenue")
                
            except Exception as e:
                logger.warning(f"Could not load research history: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get researcher statistics"""
        return {
            'total_findings': len(self.findings),
            'applied_findings': sum(1 for f in self.findings if f.applied),
            'total_enhancements': len(self.enhancements),
            'applied_enhancements': sum(1 for e in self.enhancements if e.applied),
            'total_revenue_generated': self.total_revenue_generated,
            'knowledge_sources': list(self.knowledge_sources.keys())
        }


# Singleton
_researcher_instance = None

def get_online_researcher() -> QueenOnlineResearcher:
    global _researcher_instance
    if _researcher_instance is None:
        _researcher_instance = QueenOnlineResearcher()
    return _researcher_instance


async def queen_research_and_enhance():
    """
    👑🌐🏗️ Full research → enhance → apply cycle.
    
    The Queen:
    1. Researches online for trading insights
    2. Generates code enhancements
    3. Applies them to the codebase
    """
    from queen_code_architect import get_code_architect
    
    researcher = get_online_researcher()
    architect = get_code_architect()
    
    print("\n" + "=" * 70)
    print("👑🌐 QUEEN'S ONLINE RESEARCH & SELF-ENHANCEMENT")
    print("=" * 70)
    
    # Step 1: Research
    print("\n1️⃣ Researching online for trading insights...")
    findings = await researcher.research_trading_strategies()
    print(f"   📚 Found {len(findings)} insights")
    
    for f in findings[:5]:
        print(f"   • {f.source}: {f.title} (relevance: {f.relevance_score:.0%})")
    
    # Step 2: Generate enhancement
    print("\n2️⃣ Generating code enhancement from research...")
    enhancement = researcher.generate_enhancement_from_research()
    
    if enhancement:
        print(f"   🏗️ Generated: {enhancement.name}")
        print(f"   📝 Based on: {', '.join(enhancement.source_research[:3])}")
        
        # Step 3: Apply
        print("\n3️⃣ Applying enhancement to codebase...")
        result = researcher.apply_enhancement(enhancement, architect)
        
        if result['status'] == 'success':
            print(f"   ✅ Applied: {result['file']}")
        else:
            print(f"   ⚠️ Failed: {result.get('reason')}")
    else:
        print("   ℹ️ No new enhancements to generate")
    
    # Stats
    stats = researcher.get_stats()
    print(f"\n📊 RESEARCH STATS:")
    print(f"   Total findings: {stats['total_findings']}")
    print(f"   Applied: {stats['applied_findings']}")
    print(f"   Enhancements: {stats['total_enhancements']}")
    print(f"   Revenue generated: ${stats['total_revenue_generated']:.4f}")
    
    print("\n" + "=" * 70)
    print("👑 'I search, I learn, I evolve, I profit.'")
    print("=" * 70 + "\n")
    
    return {
        'findings': len(findings),
        'enhancement': enhancement.name if enhancement else None,
        'stats': stats
    }


if __name__ == "__main__":
    print("👑🌐 Queen's Online Researcher - Test Mode")
    result = asyncio.run(queen_research_and_enhance())
    print(f"\nResult: {result}")
