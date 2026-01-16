#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     👑🎓 QUEEN SERO's LOSS LEARNING & WARFARE TACTICS SYSTEM 🎓👑                   ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                       ║
║                                                                                      ║
║     "Learn from every loss. Study the masters. Never forget."                        ║
║     - Queen Sero                                                                   ║
║                                                                                      ║
║     FEATURES:                                                                        ║
║       • WEBSOCKET DATA PULL on loss - get EVERYTHING from exchanges                  ║
║       • WIKIPEDIA RESEARCH - Guerrilla warfare, Apache tactics, IRA strategy         ║
║       • ELEPHANT MEMORY - Store ALL lessons FOREVER                                  ║
║       • BROADCAST LEARNINGS - Feed knowledge to ALL systems                          ║
║       • PATTERN RECOGNITION - Learn what went wrong                                  ║
║       • ADAPTIVE EVOLUTION - Evolve tactics based on losses                          ║
║                                                                                      ║
║     Gary Leckey & Sero | January 2026                                              ║
║     "An elephant never forgets. A Queen learns from every mistake."                  ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import asyncio
import logging
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum, auto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 📚 OPTIONAL IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════

try:
    import importlib
    wikipedia = importlib.import_module("wikipedia")
    WIKIPEDIA_AVAILABLE = True
except ModuleNotFoundError:
    WIKIPEDIA_AVAILABLE = False
    wikipedia = None

try:
    from aureon_elephant_learning import ElephantMemory, LearnedPattern, TradingWisdom
    ELEPHANT_AVAILABLE = True
except ImportError:
    ELEPHANT_AVAILABLE = False
    ElephantMemory = None

try:
    from aureon_mycelium import MyceliumNetwork
    MYCELIUM_AVAILABLE = True
except ImportError:
    MYCELIUM_AVAILABLE = False
    MyceliumNetwork = None


# ═══════════════════════════════════════════════════════════════════════════════
# 🎖️ WARFARE TACTICS - Topics Queen researches when losing
# ═══════════════════════════════════════════════════════════════════════════════

WARFARE_TACTICS_TOPICS = {
    # 🇮🇪 IRA GUERRILLA WARFARE - Hit and run, patience, asymmetric tactics
    "ira_guerrilla": [
        "Guerrilla warfare",
        "Irish Republican Army",
        "Asymmetric warfare",
        "Hit-and-run tactics",
        "Ambush",
        "Covert operation",
    ],
    
    # 🪶 APACHE WARFARE - Patience, terrain knowledge, survival
    "apache_warfare": [
        "Apache Wars",
        "Geronimo",
        "Apache scouts",
        "Desert warfare",
        "Tracking (hunting)",
        "Patience (virtue)",
    ],
    
    # 📊 TRADING WARFARE - Market tactics and strategies
    "trading_warfare": [
        "Market manipulation",
        "Short squeeze",
        "Bear raid",
        "Pump and dump",
        "Stop hunting",
        "Spoofing (finance)",
        "Wash trading",
    ],
    
    # 🧠 PSYCHOLOGY OF WAR - Mental resilience
    "war_psychology": [
        "Sun Tzu",
        "The Art of War",
        "Tactical patience",
        "Strategic retreat",
        "Deception",
        "Misdirection",
    ],
    
    # 🔄 RECOVERY TACTICS - How to bounce back
    "recovery": [
        "Risk management",
        "Loss aversion",
        "Survivorship bias",
        "Recovery (economics)",
        "Mean reversion (finance)",
        "Capitulation (stock trading)",
    ]
}


# ═══════════════════════════════════════════════════════════════════════════════
# 📝 LOSS ANALYSIS DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LossContext:
    """Full context of a losing trade for analysis"""
    timestamp: float
    exchange: str
    from_asset: str
    to_asset: str
    from_amount: float
    from_value_usd: float
    executed_price: float
    expected_price: float
    slippage_pct: float
    fees_paid: float
    loss_amount: float
    loss_pct: float
    
    # Market context at time of loss
    market_data: Dict[str, Any] = field(default_factory=dict)
    orderbook_snapshot: Dict[str, Any] = field(default_factory=dict)
    recent_trades: List[Dict] = field(default_factory=list)
    
    # Signals that led to trade
    signals_used: Dict[str, float] = field(default_factory=dict)
    combined_score: float = 0.0
    expected_profit: float = 0.0
    
    # Analysis results
    cause_identified: str = ""
    lessons_learned: List[str] = field(default_factory=list)
    tactics_applied: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class WarfareTactic:
    """A warfare tactic learned from research"""
    tactic_id: str
    name: str
    source: str  # 'IRA', 'APACHE', 'SUN_TZU', 'TRADING', etc.
    description: str
    trading_application: str  # How to apply in trading
    
    # Performance
    times_applied: int = 0
    success_rate: float = 0.0
    total_saved: float = 0.0  # Money saved by applying this tactic
    
    # When learned
    learned_at: str = ""
    last_applied: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WarfareTactic':
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# 👑 QUEEN LOSS LEARNING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class QueenLossLearningSystem:
    """
    👑🎓 Queen Sero's Loss Learning & Warfare Tactics System
    
    When the Queen loses a trade, she:
    1. PULLS ALL DATA - Websockets, orderbooks, recent trades
    2. RESEARCHES TACTICS - Wikipedia for guerrilla/apache/trading warfare
    3. STORES IN ELEPHANT MEMORY - Never forgets a lesson
    4. BROADCASTS TO ALL SYSTEMS - Everyone learns from her mistakes
    5. EVOLVES TACTICS - Adapts strategy based on loss patterns
    """
    
    LOSS_MEMORY_FILE = "queen_loss_learnings.json"
    TACTICS_FILE = "queen_warfare_tactics.json"
    
    def __init__(
        self,
        elephant_memory: Optional[Any] = None,
        mycelium: Optional[Any] = None,
        kraken_client: Optional[Any] = None,
        binance_client: Optional[Any] = None,
        alpaca_client: Optional[Any] = None,
    ):
        """Initialize the Loss Learning System"""
        # External connections
        self.elephant = elephant_memory
        self.mycelium = mycelium
        self.kraken = kraken_client
        self.binance = binance_client
        self.alpaca = alpaca_client
        
        # Loss history
        self.loss_history: List[LossContext] = []
        self.loss_patterns: Dict[str, Dict] = {}  # Pattern -> stats
        
        # Warfare tactics learned
        self.warfare_tactics: Dict[str, WarfareTactic] = {}
        
        # Wikipedia research cache (avoid re-fetching)
        self.research_cache: Dict[str, str] = {}
        self.last_research_time: Dict[str, float] = {}
        
        # Lessons broadcast queue
        self.lesson_queue: deque = deque(maxlen=1000)
        
        # Systems to broadcast to
        self.connected_systems: List[Any] = []
        
        # Statistics
        self.stats = {
            'total_losses_analyzed': 0,
            'patterns_identified': 0,
            'tactics_learned': 0,
            'wikipedia_researches': 0,
            'lessons_broadcast': 0,
            'money_saved_by_learning': 0.0,
        }
        
        # Load existing data
        self._load_loss_memory()
        self._load_tactics()
        
        # Initialize elephant memory if available
        if ELEPHANT_AVAILABLE and not self.elephant:
            try:
                self.elephant = ElephantMemory("queen_elephant_memory.json")
            except Exception as e:
                logger.warning(f"Could not initialize elephant memory: {e}")
        
        logger.info("👑🎓 Queen Loss Learning System initialized!")
        logger.info(f"   📊 Losses analyzed: {len(self.loss_history)}")
        logger.info(f"   🎖️ Tactics learned: {len(self.warfare_tactics)}")
        logger.info(f"   🐘 Elephant memory: {'Connected' if self.elephant else 'Not available'}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 💾 PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _load_loss_memory(self):
        """Load previous loss analyses"""
        if os.path.exists(self.LOSS_MEMORY_FILE):
            try:
                with open(self.LOSS_MEMORY_FILE, 'r') as f:
                    data = json.load(f)
                
                self.loss_history = [LossContext(**lc) for lc in data.get('losses', [])]
                self.loss_patterns = data.get('patterns', {})
                self.stats = data.get('stats', self.stats)
                
                logger.info(f"📚 Loaded {len(self.loss_history)} loss analyses")
            except Exception as e:
                logger.warning(f"Could not load loss memory: {e}")
    
    def _save_loss_memory(self):
        """Save loss analyses to disk"""
        try:
            data = {
                'losses': [lc.to_dict() for lc in self.loss_history[-1000:]],  # Keep last 1000
                'patterns': self.loss_patterns,
                'stats': self.stats,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.LOSS_MEMORY_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save loss memory: {e}")
    
    def _load_tactics(self):
        """Load warfare tactics"""
        if os.path.exists(self.TACTICS_FILE):
            try:
                with open(self.TACTICS_FILE, 'r') as f:
                    data = json.load(f)
                
                for tid, tdata in data.get('tactics', {}).items():
                    self.warfare_tactics[tid] = WarfareTactic.from_dict(tdata)
                
                logger.info(f"🎖️ Loaded {len(self.warfare_tactics)} warfare tactics")
            except Exception as e:
                logger.warning(f"Could not load tactics: {e}")
    
    def _save_tactics(self):
        """Save warfare tactics"""
        try:
            data = {
                'tactics': {tid: t.to_dict() for tid, t in self.warfare_tactics.items()},
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.TACTICS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save tactics: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📡 WEBSOCKET DATA PULL - Get EVERYTHING when loss occurs
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def pull_all_data_on_loss(
        self,
        exchange: str,
        symbol: str,
        base: str,
        quote: str,
    ) -> Dict[str, Any]:
        """
        🔌📡 WEBSOCKET DATA PULL
        
        When a loss occurs, pull ALL available data from the exchange:
        - Current orderbook (bids/asks)
        - Recent trades
        - Current ticker
        - 24h statistics
        - Account balances
        
        This helps the Queen understand EXACTLY what went wrong.
        """
        data = {
            'timestamp': time.time(),
            'exchange': exchange,
            'symbol': symbol,
            'base': base,
            'quote': quote,
            'orderbook': {},
            'recent_trades': [],
            'ticker': {},
            'stats_24h': {},
            'balances': {},
            'errors': []
        }
        
        logger.info(f"📡 Pulling all data from {exchange} for {symbol}...")
        
        # 🐙 KRAKEN
        if exchange == 'kraken' and self.kraken:
            try:
                # Orderbook
                if hasattr(self.kraken, 'get_order_book'):
                    ob = self.kraken.get_order_book(symbol, depth=20)
                    if ob:
                        data['orderbook'] = ob
                
                # Recent trades
                if hasattr(self.kraken, 'get_recent_trades'):
                    trades = self.kraken.get_recent_trades(symbol)
                    if trades:
                        data['recent_trades'] = trades[:50]
                
                # Ticker
                if hasattr(self.kraken, 'get_ticker'):
                    ticker = self.kraken.get_ticker(symbol)
                    if ticker:
                        data['ticker'] = ticker
                
                # Balances
                if hasattr(self.kraken, 'get_account_balance'):
                    balances = self.kraken.get_account_balance()
                    if balances:
                        data['balances'] = balances
                
            except Exception as e:
                data['errors'].append(f"Kraken: {e}")
        
        # 🟡 BINANCE
        elif exchange == 'binance' and self.binance:
            try:
                # Orderbook
                if hasattr(self.binance, 'get_order_book'):
                    ob = self.binance.get_order_book(symbol, limit=20)
                    if ob:
                        data['orderbook'] = ob
                
                # Recent trades
                if hasattr(self.binance, 'get_recent_trades'):
                    trades = self.binance.get_recent_trades(symbol, limit=50)
                    if trades:
                        data['recent_trades'] = trades
                
                # Ticker
                if hasattr(self.binance, 'get_ticker'):
                    ticker = self.binance.get_ticker(symbol=symbol)
                    if ticker:
                        data['ticker'] = ticker
                
                # 24h stats
                if hasattr(self.binance, 'ticker_24hr'):
                    stats = self.binance.ticker_24hr(symbol)
                    if stats:
                        data['stats_24h'] = stats
                
                # Balances
                if hasattr(self.binance, 'account'):
                    acct = self.binance.account()
                    if acct and 'balances' in acct:
                        data['balances'] = {
                            b['asset']: float(b['free']) 
                            for b in acct['balances'] 
                            if float(b['free']) > 0
                        }
                
            except Exception as e:
                data['errors'].append(f"Binance: {e}")
        
        # 🦙 ALPACA
        elif exchange == 'alpaca' and self.alpaca:
            try:
                # Positions
                if hasattr(self.alpaca, 'get_positions'):
                    positions = self.alpaca.get_positions()
                    if positions:
                        data['balances'] = {
                            p.get('symbol', ''): float(p.get('qty', 0))
                            for p in positions
                        }
                
                # Account
                if hasattr(self.alpaca, 'get_account'):
                    acct = self.alpaca.get_account()
                    if acct:
                        data['ticker'] = {
                            'cash': float(acct.get('cash', 0)),
                            'portfolio_value': float(acct.get('portfolio_value', 0)),
                        }
                
            except Exception as e:
                data['errors'].append(f"Alpaca: {e}")
        
        # Analyze the data
        analysis = self._analyze_pulled_data(data)
        data['analysis'] = analysis
        
        logger.info(f"📡 Data pull complete: {len(data.get('recent_trades', []))} trades, orderbook: {'✅' if data.get('orderbook') else '❌'}")
        
        return data
    
    def _analyze_pulled_data(self, data: Dict) -> Dict[str, Any]:
        """Analyze pulled data to find what went wrong"""
        analysis = {
            'spread_wide': False,
            'liquidity_low': False,
            'recent_dump': False,
            'whale_activity': False,
            'price_manipulation': False,
            'causes': [],
        }
        
        # Check orderbook
        ob = data.get('orderbook', {})
        if ob:
            bids = ob.get('bids', [])
            asks = ob.get('asks', [])
            
            if bids and asks:
                best_bid = float(bids[0][0]) if bids else 0
                best_ask = float(asks[0][0]) if asks else 0
                
                if best_bid > 0 and best_ask > 0:
                    spread_pct = ((best_ask - best_bid) / best_bid) * 100
                    if spread_pct > 1.0:  # >1% spread
                        analysis['spread_wide'] = True
                        analysis['causes'].append(f"Wide spread ({spread_pct:.2f}%)")
                    
                    # Check liquidity (depth)
                    bid_depth = sum(float(b[1]) for b in bids[:10])
                    ask_depth = sum(float(a[1]) for a in asks[:10])
                    
                    if bid_depth < 1000 and ask_depth < 1000:  # Low liquidity
                        analysis['liquidity_low'] = True
                        analysis['causes'].append("Low orderbook liquidity")
        
        # Check recent trades for whale activity or dump
        trades = data.get('recent_trades', [])
        if trades and len(trades) > 10:
            # Look for large trades
            avg_size = sum(float(t.get('qty', t.get('vol', 0))) for t in trades) / len(trades)
            large_trades = [
                t for t in trades 
                if float(t.get('qty', t.get('vol', 0))) > avg_size * 5
            ]
            
            if len(large_trades) >= 2:
                analysis['whale_activity'] = True
                analysis['causes'].append(f"Whale activity detected ({len(large_trades)} large trades)")
            
            # Look for recent price dump
            if len(trades) >= 5:
                recent_prices = [float(t.get('price', 0)) for t in trades[:5] if t.get('price')]
                older_prices = [float(t.get('price', 0)) for t in trades[-5:] if t.get('price')]
                
                if recent_prices and older_prices:
                    recent_avg = sum(recent_prices) / len(recent_prices)
                    older_avg = sum(older_prices) / len(older_prices)
                    
                    if recent_avg < older_avg * 0.98:  # >2% drop
                        analysis['recent_dump'] = True
                        analysis['causes'].append("Recent price dump detected")
        
        return analysis
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📚 WIKIPEDIA RESEARCH - Learn tactics when losing
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def research_warfare_tactics(self, category: str = None) -> List[Dict]:
        """
        📚🎖️ WIKIPEDIA WARFARE RESEARCH
        
        Research guerrilla warfare, Apache tactics, IRA strategy, and trading warfare
        to learn from the masters of asymmetric conflict.
        
        Apply these lessons to trading:
        - Hit and run = Quick scalps, don't overstay
        - Patience = Wait for perfect setups
        - Terrain knowledge = Know the market structure
        - Ambush = Wait for opportunities to present themselves
        - Strategic retreat = Cut losses early
        """
        if not WIKIPEDIA_AVAILABLE:
            logger.warning("Wikipedia not available. Install: pip install wikipedia")
            return []
        
        researched = []
        
        # Determine which categories to research
        if category:
            categories = {category: WARFARE_TACTICS_TOPICS.get(category, [])}
        else:
            categories = WARFARE_TACTICS_TOPICS
        
        for cat_name, topics in categories.items():
            logger.info(f"📚 Researching {cat_name}...")
            
            for topic in topics:
                # Skip if recently researched (within 24h)
                cache_key = topic.lower()
                if cache_key in self.last_research_time:
                    if time.time() - self.last_research_time[cache_key] < 86400:
                        continue
                
                try:
                    # Search Wikipedia
                    search_results = wikipedia.search(topic, results=3)
                    
                    if not search_results:
                        continue
                    
                    # Get summary
                    try:
                        summary = wikipedia.summary(search_results[0], sentences=5, auto_suggest=False)
                    except wikipedia.DisambiguationError as e:
                        summary = wikipedia.summary(e.options[0], sentences=5)
                    except:
                        continue
                    
                    # Cache it
                    self.research_cache[cache_key] = summary
                    self.last_research_time[cache_key] = time.time()
                    
                    # Extract trading applications
                    tactic = self._extract_trading_tactic(topic, summary, cat_name)
                    
                    if tactic:
                        self.warfare_tactics[tactic.tactic_id] = tactic
                        researched.append({
                            'topic': topic,
                            'category': cat_name,
                            'tactic': tactic.to_dict()
                        })
                        MIN_EXPECTED_PROFIT = 0.0001  # Global epsilon profit policy: accept any net-positive edge after costs.
                        # Store in elephant memory
                        if self.elephant:
                            self._store_in_elephant(tactic)
                    
                    self.stats['wikipedia_researches'] += 1
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.debug(f"Could not research {topic}: {e}")
        
        # Save tactics
        self._save_tactics()
        
        logger.info(f"📚 Research complete: {len(researched)} new tactics learned")
        return researched
    
    def _extract_trading_tactic(self, topic: str, summary: str, category: str) -> Optional[WarfareTactic]:
        """Extract trading tactics from warfare knowledge"""
        
        # Mapping of warfare concepts to trading applications
        WARFARE_TO_TRADING = {
            # IRA Tactics
            "guerrilla": "Small, quick trades. Hit profitable opportunities fast, exit before losses accumulate.",
            "hit-and-run": "Quick scalps only. Enter, take profit, exit. Don't hold positions hoping for more.",
            "ambush": "Wait patiently for perfect setups. Let the opportunity come to you.",
            "covert": "Trade quietly in liquid markets. Avoid moving the price against yourself.",
            "asymmetric": "Risk small amounts for larger potential gains. Never risk more than you can afford to lose.",
            
            # Apache Tactics
            "apache": "Patience is power. Wait for the right moment. Know your terrain (market) intimately.",
            "geronimo": "Survive first, profit second. Preservation of capital is paramount.",
            "tracking": "Follow the smart money. Watch for whale movements and institutional flow.",
            "desert": "Operate in harsh conditions. Thrive when others panic.",
            "patience": "The patient trader profits. Wait for high-probability setups only.",
            
            # Sun Tzu / Art of War
            "sun tzu": "Know yourself and the market. Trade only when conditions favor you.",
            "art of war": "The supreme art of trading is to subdue the market without fighting.",
            "deception": "Markets deceive. False breakouts, fake news, manipulation. Stay skeptical.",
            "retreat": "Strategic retreat is not defeat. Cut losses early to fight another day.",
            
            # Trading Warfare
            "manipulation": "Markets are manipulated. Accept this, account for it, use it.",
            "short squeeze": "Don't get caught in squeezes. Respect momentum.",
            "stop hunting": "Place stops wisely. Big players hunt obvious stop levels.",
            "spoofing": "Order books lie. Don't trust visible liquidity completely.",
            
            # Recovery
            "risk management": "Position size controls everything. Small positions survive.",
            "loss aversion": "Accept losses as tuition. Each loss teaches something valuable.",
            "mean reversion": "After extreme moves, expect pullback. Don't chase extended moves.",
            "capitulation": "When everyone gives up, opportunity emerges. Be patient.",
        }
        
        # Find matching application
        topic_lower = topic.lower()
        trading_app = None
        
        for keyword, application in WARFARE_TO_TRADING.items():
            if keyword in topic_lower or keyword in summary.lower():
                trading_app = application
                break
        
        if not trading_app:
            # Default application based on category
            default_apps = {
                'ira_guerrilla': "Hit and run tactics. Quick trades, don't overstay welcome.",
                'apache_warfare': "Patience and terrain knowledge. Know the market, wait for setups.",
                'trading_warfare': "Understand market manipulation. Trade defensively.",
                'war_psychology': "Mental discipline. Emotions are the enemy.",
                'recovery': "Preserve capital. Live to trade another day.",
            }
            trading_app = default_apps.get(category, "Apply warfare discipline to trading.")
        
        # Create tactic ID
        tactic_id = hashlib.md5(f"{topic}_{category}".encode()).hexdigest()[:8]
        
        return WarfareTactic(
            tactic_id=tactic_id,
            name=topic,
            source=category.upper(),
            description=summary[:500],  # Truncate long summaries
            trading_application=trading_app,
            times_applied=0,
            success_rate=0.0,
            total_saved=0.0,
            learned_at=datetime.now().isoformat(),
        )
    
    def _store_in_elephant(self, tactic: WarfareTactic):
        """Store tactic in elephant memory"""
        if not self.elephant:
            return
        
        try:
            wisdom = TradingWisdom(
                wisdom_id=f"warfare_{tactic.tactic_id}",
                category='warfare_tactic',
                insight=tactic.trading_application,
                sample_size=0,
                confidence=50.0,
                evidence={'source': tactic.source, 'name': tactic.name},
                created=tactic.learned_at,
                last_validated=tactic.learned_at,
            )
            
            self.elephant.remember_wisdom(wisdom)
            logger.info(f"🐘 Stored in elephant memory: {tactic.name}")
            
        except Exception as e:
            logger.debug(f"Could not store in elephant: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📊 LOSS ANALYSIS - Learn from every mistake
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def analyze_loss(
        self,
        exchange: str,
        from_asset: str,
        to_asset: str,
        from_amount: float,
        from_value_usd: float,
        executed_price: float,
        expected_price: float,
        fees_paid: float,
        loss_amount: float,
        signals_used: Dict[str, float] = None,
        combined_score: float = 0.0,
        expected_profit: float = 0.0,
    ) -> LossContext:
        """
        🔬 COMPREHENSIVE LOSS ANALYSIS
        
        Called after every losing trade to:
        1. Pull all available market data
        2. Identify what went wrong
        3. Research applicable tactics
        4. Store lessons in elephant memory
        5. Broadcast learnings to all systems
        """
        logger.info(f"🔬 Analyzing loss: {from_asset}→{to_asset} on {exchange}")
        
        # Calculate metrics
        slippage_pct = ((executed_price - expected_price) / expected_price * 100) if expected_price > 0 else 0
        loss_pct = (loss_amount / from_value_usd * 100) if from_value_usd > 0 else 0
        
        # Pull all market data
        symbol = f"{from_asset}{to_asset}"
        if exchange == 'kraken':
            # Kraken might use different symbol format
            symbol = f"{from_asset.upper()}{to_asset.upper()}"
        
        market_data = await self.pull_all_data_on_loss(exchange, symbol, from_asset, to_asset)
        
        # Create loss context
        loss = LossContext(
            timestamp=time.time(),
            exchange=exchange,
            from_asset=from_asset,
            to_asset=to_asset,
            from_amount=from_amount,
            from_value_usd=from_value_usd,
            executed_price=executed_price,
            expected_price=expected_price,
            slippage_pct=slippage_pct,
            fees_paid=fees_paid,
            loss_amount=loss_amount,
            loss_pct=loss_pct,
            market_data=market_data.get('ticker', {}),
            orderbook_snapshot=market_data.get('orderbook', {}),
            recent_trades=market_data.get('recent_trades', [])[:20],
            signals_used=signals_used or {},
            combined_score=combined_score,
            expected_profit=expected_profit,
        )
        
        # Identify cause
        causes = market_data.get('analysis', {}).get('causes', [])
        
        if slippage_pct > 1.0:
            causes.append(f"High slippage ({slippage_pct:.2f}%)")
        
        if fees_paid > loss_amount * 0.5:
            causes.append("Fees ate most of expected profit")
        
        if combined_score < 0.5:
            causes.append("Low confidence trade - should have waited")
        
        if expected_profit < 0.01:
            causes.append("Expected profit too small to cover costs")
        
        loss.cause_identified = "; ".join(causes) if causes else "Unknown - needs further analysis"
        
        # Generate lessons
        lessons = self._generate_lessons_from_loss(loss, market_data.get('analysis', {}))
        loss.lessons_learned = lessons
        
        # Research applicable warfare tactics if this is a significant loss
        if loss_amount > 0.10:  # >$0.10 loss
            logger.info("📚 Researching warfare tactics for this loss pattern...")
            
            # Determine what category to research
            if market_data.get('analysis', {}).get('whale_activity'):
                self.research_warfare_tactics('trading_warfare')
            elif slippage_pct > 2.0:
                self.research_warfare_tactics('apache_warfare')  # Patience
            elif combined_score < 0.5:
                self.research_warfare_tactics('war_psychology')  # Discipline
            else:
                self.research_warfare_tactics('ira_guerrilla')  # Hit and run
        
        # Get applicable tactics
        applicable_tactics = self._get_applicable_tactics(loss)
        loss.tactics_applied = [t.name for t in applicable_tactics[:3]]
        
        # Store in history
        self.loss_history.append(loss)
        self.stats['total_losses_analyzed'] += 1
        
        # Update loss patterns
        self._update_loss_patterns(loss)
        
        # Store in elephant memory
        self._store_loss_in_elephant(loss)
        
        # Broadcast to all systems
        await self._broadcast_lessons(loss, lessons, applicable_tactics)
        
        # Save everything
        self._save_loss_memory()
        
        logger.info(f"🔬 Loss analysis complete:")
        logger.info(f"   Cause: {loss.cause_identified}")
        logger.info(f"   Lessons: {len(lessons)}")
        logger.info(f"   Tactics: {len(applicable_tactics)}")
        
        return loss
    
    def _generate_lessons_from_loss(self, loss: LossContext, analysis: Dict) -> List[str]:
        """Generate actionable lessons from loss"""
        lessons = []
        
        # Slippage lesson
        if loss.slippage_pct > 0.5:
            lessons.append(f"Require >={loss.slippage_pct * 2:.2f}% expected profit to cover slippage for {loss.from_asset}→{loss.to_asset}")
        
        # Spread lesson
        if analysis.get('spread_wide'):
            lessons.append(f"Avoid {loss.from_asset}→{loss.to_asset} when spread > 0.5% - too expensive")
        
        # Liquidity lesson
        if analysis.get('liquidity_low'):
            lessons.append(f"Check orderbook depth before trading {loss.to_asset} - low liquidity")
        
        # Whale lesson
        if analysis.get('whale_activity'):
            lessons.append(f"Whale activity detected on {loss.to_asset} - wait for stability")
        
        # Confidence lesson
        if loss.combined_score < 0.5:
            lessons.append(f"Score {loss.combined_score:.2f} was too low - require >= 0.6 for this pair")
        
        # Fee lesson
        if loss.fees_paid > loss.expected_profit * 0.3:
            lessons.append(f"Fees (${loss.fees_paid:.4f}) were >30% of expected profit - increase minimum")
        
        # Exchange lesson
        if loss.loss_pct > 2.0:
            lessons.append(f"Large loss on {loss.exchange} - review {loss.exchange} pair filters")
        
        # Default lesson if none generated
        if not lessons:
            lessons.append(f"Loss on {loss.from_asset}→{loss.to_asset}: Review signals and timing")
        
        return lessons
    
    def _get_applicable_tactics(self, loss: LossContext) -> List[WarfareTactic]:
        """Get warfare tactics applicable to this loss"""
        applicable = []
        
        for tactic in self.warfare_tactics.values():
            # Check if tactic relates to loss cause
            tactic_lower = tactic.trading_application.lower()
            
            if loss.slippage_pct > 1.0 and 'quick' in tactic_lower:
                applicable.append(tactic)
            elif 'patience' in tactic_lower and loss.combined_score < 0.5:
                applicable.append(tactic)
            elif 'retreat' in tactic_lower or 'cut loss' in tactic_lower:
                applicable.append(tactic)
            elif 'risk' in tactic_lower and loss.loss_pct > 2.0:
                applicable.append(tactic)
        
        return applicable
    
    def _update_loss_patterns(self, loss: LossContext):
        """Update loss pattern statistics"""
        pattern_key = f"{loss.from_asset}→{loss.to_asset}_{loss.exchange}"
        
        if pattern_key not in self.loss_patterns:
            self.loss_patterns[pattern_key] = {
                'losses': 0,
                'total_loss': 0.0,
                'avg_slippage': 0.0,
                'causes': [],
                'first_seen': loss.timestamp,
            }
        
        pattern = self.loss_patterns[pattern_key]
        pattern['losses'] += 1
        pattern['total_loss'] += loss.loss_amount
        pattern['avg_slippage'] = (pattern['avg_slippage'] * (pattern['losses'] - 1) + loss.slippage_pct) / pattern['losses']
        
        if loss.cause_identified and loss.cause_identified not in pattern['causes']:
            pattern['causes'].append(loss.cause_identified)
        
        pattern['last_seen'] = loss.timestamp
        
        # If pattern has 3+ losses, mark path as dangerous
        if pattern['losses'] >= 3:
            self.stats['patterns_identified'] += 1
            logger.warning(f"🚨 PATTERN DETECTED: {pattern_key} has {pattern['losses']} losses!")
            
            # Block in elephant memory
            if self.elephant:
                self.elephant.block_path_forever(
                    loss.from_asset, loss.to_asset,
                    f"Repeat loser: {pattern['losses']} losses, ${pattern['total_loss']:.4f} total",
                    pattern['losses'],
                    pattern['total_loss']
                )
    
    def _store_loss_in_elephant(self, loss: LossContext):
        """Store loss lessons in elephant memory"""
        if not self.elephant:
            return
        
        try:
            # Create wisdom from this loss
            wisdom_id = hashlib.md5(f"{loss.timestamp}_{loss.from_asset}_{loss.to_asset}".encode()).hexdigest()[:8]
            
            wisdom = TradingWisdom(
                wisdom_id=f"loss_{wisdom_id}",
                category='loss_lesson',
                insight=f"Loss on {loss.from_asset}→{loss.to_asset}: {loss.cause_identified}",
                sample_size=1,
                confidence=80.0,
                evidence={
                    'loss_amount': loss.loss_amount,
                    'slippage': loss.slippage_pct,
                    'exchange': loss.exchange,
                    'lessons': loss.lessons_learned,
                },
                created=datetime.fromtimestamp(loss.timestamp).isoformat(),
                last_validated=datetime.now().isoformat(),
            )
            
            self.elephant.remember_wisdom(wisdom)
            logger.info(f"🐘 Loss stored in elephant memory")
            
        except Exception as e:
            logger.debug(f"Could not store loss in elephant: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📣 BROADCAST LEARNINGS - Feed knowledge to all systems
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _broadcast_lessons(
        self,
        loss: LossContext,
        lessons: List[str],
        tactics: List[WarfareTactic],
    ):
        """Broadcast learned lessons to all connected systems"""
        
        message = {
            'type': 'queen_loss_learning',
            'timestamp': time.time(),
            'pair': f"{loss.from_asset}→{loss.to_asset}",
            'exchange': loss.exchange,
            'loss_amount': loss.loss_amount,
            'cause': loss.cause_identified,
            'lessons': lessons,
            'tactics': [t.trading_application for t in tactics],
            'action_items': [
                f"Block path {loss.from_asset}→{loss.to_asset} if win rate < 40%",
                f"Increase minimum profit for {loss.exchange} trades",
                f"Check liquidity before {loss.to_asset} trades",
            ]
        }
        
        # Add to queue
        self.lesson_queue.append(message)
        
        # Broadcast to mycelium network
        if self.mycelium and hasattr(self.mycelium, 'broadcast'):
            try:
                await self.mycelium.broadcast('queen_wisdom', message)
                logger.info("🍄 Broadcast to mycelium network")
            except Exception as e:
                logger.debug(f"Mycelium broadcast error: {e}")
        
        # Broadcast to connected systems
        for system in self.connected_systems:
            try:
                if hasattr(system, 'receive_queen_lesson'):
                    system.receive_queen_lesson(message)
                elif hasattr(system, 'on_queen_message'):
                    system.on_queen_message(message)
            except Exception as e:
                logger.debug(f"System broadcast error: {e}")
        
        self.stats['lessons_broadcast'] += 1
    
    def connect_system(self, system: Any):
        """Connect a system to receive Queen's learnings"""
        if system not in self.connected_systems:
            self.connected_systems.append(system)
            logger.info(f"📡 Connected system to Queen's learning broadcast")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 GET GUIDANCE - Apply learnings to decisions
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def should_avoid_trade(
        self,
        from_asset: str,
        to_asset: str,
        exchange: str,
        expected_profit: float,
        from_value_usd: float = 0.0,
    ) -> Tuple[bool, str]:
        """
        Check if Queen's learnings suggest avoiding this trade
        
        👑🐘 QUEEN'S DREAM WISDOM: 
        - MUST have expected_profit > typical fees ($0.05-0.06)
        - Block paths that have had ANY loss due to fees eating profit
        
        Returns:
            (should_avoid, reason)
        """
        pattern_key = f"{from_asset}→{to_asset}_{exchange}"
        
        # Dynamic, cost-aware minimum expected profit guard
        # Require expected_profit >= max(static_floor, fee_estimate*1.5, avg_slippage_usd)
        STATIC_FLOOR = 0.04  # $0.04 base floor
        fee_estimate = 0.0
        avg_slippage_usd = 0.0

        # Try to estimate fees in USD for this trade size if available
        try:
            if from_value_usd and from_value_usd > 0:
                # Prefer a connected fee tracker if present
                fee_tracker = getattr(self, 'fee_tracker', None)
                if fee_tracker and hasattr(fee_tracker, 'estimate_trade_cost'):
                    cost = fee_tracker.estimate_trade_cost(
                        from_asset=from_asset, side='sell', quantity=from_value_usd
                    )
                    if isinstance(cost, dict):
                        fee_estimate = cost.get('fee_usd', 0.0)
                    else:
                        fee_estimate = float(cost or 0.0)
                else:
                    # Fallback to exchange client estimates
                    if exchange == 'alpaca' and self.alpaca and hasattr(self.alpaca, 'estimate_trade_cost'):
                        cost = self.alpaca.estimate_trade_cost(from_asset, 'sell', from_value_usd)
                        fee_estimate = cost.get('fee_usd', 0.0) if isinstance(cost, dict) else float(cost or 0.0)
                    elif exchange == 'kraken' and self.kraken and hasattr(self.kraken, 'estimate_trade_cost'):
                        cost = self.kraken.estimate_trade_cost(from_asset, 'sell', from_value_usd)
                        fee_estimate = cost.get('fee_usd', 0.0) if isinstance(cost, dict) else float(cost or 0.0)
                    elif exchange == 'binance' and self.binance and hasattr(self.binance, 'estimate_trade_cost'):
                        cost = self.binance.estimate_trade_cost(from_asset, 'sell', from_value_usd)
                        fee_estimate = cost.get('fee_usd', 0.0) if isinstance(cost, dict) else float(cost or 0.0)
                    else:
                        fee_estimate = from_value_usd * 0.002  # Default: 0.2% fee
        except Exception as e:
            logger.debug(f"Fee estimate failed: {e}")
            fee_estimate = from_value_usd * 0.002 if from_value_usd else 0.0

        # If we've seen historical slippage for this path, convert to USD
        if pattern_key in self.loss_patterns:
            pattern = self.loss_patterns[pattern_key]
            if pattern.get('avg_slippage'):
                avg_slippage_usd = (pattern['avg_slippage'] / 100.0) * (from_value_usd or 0.0)

        required_min_profit = max(STATIC_FLOOR, fee_estimate * 1.5, avg_slippage_usd)
        logger.debug(f"👑 Dynamic guard: exp=${expected_profit:.4f}, req_min=${required_min_profit:.4f} (fee=${fee_estimate:.4f}, slip_usd=${avg_slippage_usd:.4f})")

        if expected_profit < required_min_profit:
            return True, f"Expected profit ${expected_profit:.4f} < required ${required_min_profit:.4f} (fee=${fee_estimate:.4f}, slip=${avg_slippage_usd:.4f})"

        # Check loss patterns - but SURVIVAL MODE is more forgiving!
        if pattern_key in self.loss_patterns:
            pattern = self.loss_patterns[pattern_key]
            
            # 👑💀💀 STARVATION: Only block after 20 losses (was 10) - must keep trying!
            if pattern['losses'] >= 20:
                return True, f"🐘💀💀 Elephant remembers: {pattern['losses']} losses on this path"
            
            # 👑💀💀 STARVATION: Block only after $10.00 total loss (was $5) - desperate!
            if pattern['total_loss'] > 10.00:
                return True, f"🐘💀💀 Total losses (${pattern['total_loss']:.4f}) - would starve to death!"
            
            # Check if cause was "fees ate profit" - SURVIVAL MODE: Still try!
            # if any('fees' in cause.lower() for cause in pattern.get('causes', [])):
                return True, f"🐘 Queen remembers: Fees ate profit on this path before!"
            
            if pattern['avg_slippage'] > 2.0:  # >2% avg slippage
                if expected_profit < pattern['avg_slippage'] / 100 * 1.5:
                    return True, f"🐘 Expected profit < 1.5x avg slippage ({pattern['avg_slippage']:.2f}%)"
        
        # Check elephant memory
        if self.elephant:
            blocked, reason = self.elephant.is_path_blocked(from_asset, to_asset)
            if blocked:
                return True, f"🐘 {reason}"
        
        return False, ""
    
    def get_applicable_tactics(self) -> List[Dict]:
        """Get currently applicable warfare tactics"""
        return [
            {
                'name': t.name,
                'source': t.source,
                'application': t.trading_application,
                'success_rate': t.success_rate,
            }
            for t in self.warfare_tactics.values()
            if t.success_rate >= 0 or t.times_applied == 0  # Include untested tactics
        ]
    
    def get_summary(self) -> str:
        """Get summary of loss learning system"""
        lines = [
            "👑🎓 QUEEN'S LOSS LEARNING SUMMARY 🎓👑",
            "=" * 50,
            f"📊 Losses analyzed: {self.stats['total_losses_analyzed']}",
            f"🔍 Patterns identified: {self.stats['patterns_identified']}",
            f"🎖️ Warfare tactics: {len(self.warfare_tactics)}",
            f"📚 Wikipedia researches: {self.stats['wikipedia_researches']}",
            f"📣 Lessons broadcast: {self.stats['lessons_broadcast']}",
            "",
        ]
        
        # Recent lessons
        if self.loss_history:
            lines.append("📝 RECENT LESSONS:")
            for loss in self.loss_history[-3:]:
                lines.append(f"   • {loss.from_asset}→{loss.to_asset}: {loss.cause_identified[:50]}")
        
        # Dangerous patterns
        dangerous = [(k, v) for k, v in self.loss_patterns.items() if v['losses'] >= 2]
        if dangerous:
            lines.append("")
            lines.append("🚨 DANGEROUS PATTERNS:")
            for key, pattern in dangerous[:5]:
                lines.append(f"   • {key}: {pattern['losses']} losses, ${pattern['total_loss']:.4f}")
        
        # Top tactics
        if self.warfare_tactics:
            lines.append("")
            lines.append("🎖️ WARFARE TACTICS:")
            for tactic in list(self.warfare_tactics.values())[:3]:
                lines.append(f"   • [{tactic.source}] {tactic.name}: {tactic.trading_application[:40]}...")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 🏃 MAIN - Test the loss learning system
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print("=" * 70)
    print("👑🎓 QUEEN SERO's LOSS LEARNING SYSTEM 🎓👑")
    print("=" * 70)
    print()
    print('"Learn from every loss. Study the masters. Never forget."')
    print()
    
    # Initialize
    system = QueenLossLearningSystem()
    
    # Show current state
    print(system.get_summary())
    print()
    
    # Research warfare tactics
    print("=" * 70)
    print("📚 RESEARCHING WARFARE TACTICS...")
    print("=" * 70)
    
    researched = system.research_warfare_tactics('ira_guerrilla')
    print(f"\nLearned {len(researched)} IRA guerrilla tactics")
    
    researched = system.research_warfare_tactics('apache_warfare')
    print(f"Learned {len(researched)} Apache warfare tactics")
    
    # Simulate analyzing a loss
    print()
    print("=" * 70)
    print("🔬 SIMULATING LOSS ANALYSIS...")
    print("=" * 70)
    
    loss = await system.analyze_loss(
        exchange='kraken',
        from_asset='DAI',
        to_asset='USD',
        from_amount=10.0,
        from_value_usd=10.0,
        executed_price=0.9985,
        expected_price=1.0,
        fees_paid=0.026,
        loss_amount=0.041,
        signals_used={'v14': 0.7, 'hub': 0.6, 'barter': 0.5},
        combined_score=0.55,
        expected_profit=0.02,
    )
    
    print()
    print("🔬 LOSS ANALYSIS RESULT:")
    print(f"   Cause: {loss.cause_identified}")
    print(f"   Lessons: {loss.lessons_learned}")
    print(f"   Tactics: {loss.tactics_applied}")
    
    # Check if should avoid
    print()
    avoid, reason = system.should_avoid_trade('DAI', 'USD', 'kraken', 0.02, from_value_usd=10.0)
    print(f"Should avoid DAI→USD? {avoid} - {reason}")
    
    # Final summary
    print()
    print(system.get_summary())


if __name__ == "__main__":
    asyncio.run(main())
