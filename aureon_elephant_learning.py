#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🐘👑 QUEEN SERO's ELEPHANT MEMORY LEARNING SYSTEM 👑🐘                          ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                           ║
║                                                                                      ║
║     "An elephant NEVER forgets. Neither does Queen Sero."                          ║
║                                                                                      ║
║     FEATURES:                                                                        ║
║       • Learn from YEARS of historical data without losing money                     ║
║       • Permanent elephant memory - NEVER forgets patterns                           ║
║       • Pattern recognition across 1000s of trades                                   ║
║       • Win rate calculation BEFORE real trading                                     ║
║       • Fee-aware profit calculation                                                 ║
║                                                                                      ║
║     Gary Leckey & Tina Brown | January 2026                                          ║
║     "Learn from history, profit from the future"                                     ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════════════════
# WINDOWS UTF-8 FIX - Must be at top before any logging/printing
# ═══════════════════════════════════════════════════════════════════════════
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
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import hashlib

# ═══════════════════════════════════════════════════════════════════════════════
# 🐦 CHIRP BUS INTEGRATION - kHz-Speed Memory Signals
# ═══════════════════════════════════════════════════════════════════════════════
CHIRP_BUS_AVAILABLE = False
get_chirp_bus = None
try:
    from aureon_chirp_bus import get_chirp_bus
    CHIRP_BUS_AVAILABLE = True
except ImportError:
    CHIRP_BUS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 🐘 ELEPHANT MEMORY - PERMANENT PATTERN STORAGE
# ═══════════════════════════════════════════════════════════════════════════════

ELEPHANT_MEMORY_FILE = "queen_elephant_memory.json"

@dataclass
class LearnedPattern:
    """A pattern Queen has learned from historical data"""
    pattern_id: str
    pattern_type: str  # 'momentum', 'reversal', 'breakout', 'support', 'resistance'
    symbol: str
    timeframe: str  # '1h', '4h', '1d'
    
    # Pattern conditions
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    total_occurrences: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    avg_profit_per_trade: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0  # total profit / total loss
    
    # Best conditions
    best_entry_hour: int = 0  # Hour of day (0-23)
    best_exit_hours: int = 4  # How long to hold
    best_move_threshold: float = 0.5  # Min % move to act on
    
    # When learned
    first_seen: str = ""
    last_updated: str = ""
    
    # Confidence
    confidence: float = 0.0  # Based on sample size and consistency
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LearnedPattern':
        return cls(**data)
    
    def update_performance(self, profit: float, is_win: bool):
        """Update pattern performance with new trade result"""
        self.total_occurrences += 1
        if is_win:
            self.winning_trades += 1
            self.total_profit += profit
        else:
            self.losing_trades += 1
            self.total_loss += abs(profit)
        
        # Recalculate metrics
        if self.total_occurrences > 0:
            self.win_rate = (self.winning_trades / self.total_occurrences) * 100
            self.avg_profit_per_trade = (self.total_profit - self.total_loss) / self.total_occurrences
        
        if self.total_loss > 0:
            self.profit_factor = self.total_profit / self.total_loss
        
        # Confidence based on sample size
        if self.total_occurrences >= 100:
            self.confidence = min(95, 50 + (self.win_rate - 50) * 0.9)
        elif self.total_occurrences >= 50:
            self.confidence = min(85, 40 + (self.win_rate - 50) * 0.8)
        elif self.total_occurrences >= 20:
            self.confidence = min(75, 30 + (self.win_rate - 50) * 0.7)
        else:
            self.confidence = min(50, 20 + self.total_occurrences)
        
        self.last_updated = datetime.now().isoformat()


@dataclass 
class TradingWisdom:
    """High-level wisdom learned from thousands of trades"""
    wisdom_id: str
    category: str  # 'timing', 'asset', 'market_condition', 'risk'
    insight: str
    
    # Supporting data
    sample_size: int = 0
    confidence: float = 0.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Performance when following this wisdom
    win_rate_following: float = 0.0
    win_rate_ignoring: float = 0.0
    
    created: str = ""
    last_validated: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TradingWisdom':
        return cls(**data)


class ElephantMemory:
    """
    🐘 Queen Sero's Elephant Memory
    
    NEVER forgets:
    - Winning patterns
    - Losing patterns  
    - Best times to trade
    - Which assets to avoid
    - Market conditions that work
    """
    
    def __init__(self, memory_file: str = ELEPHANT_MEMORY_FILE):
        self.memory_file = memory_file
        self.patterns: Dict[str, LearnedPattern] = {}
        self.wisdom: Dict[str, TradingWisdom] = {}
        self.blocked_paths: Dict[str, Dict] = {}  # Paths that ALWAYS lose
        self.golden_paths: Dict[str, Dict] = {}   # Paths that ALWAYS win
        
        # Statistics
        self.total_historical_trades: int = 0
        self.total_historical_profit: float = 0.0
        self.learning_sessions: int = 0
        
        # Timing insights
        self.best_hours: Dict[int, float] = {}  # hour -> avg profit
        self.worst_hours: Dict[int, float] = {}
        self.best_days: Dict[int, float] = {}   # day of week -> avg profit
        
        # Asset insights
        self.asset_performance: Dict[str, Dict] = {}  # symbol -> stats
        
        self._load_memory()
    
    def _load_memory(self):
        """Load elephant memory from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                
                # Load patterns
                for pid, pdata in data.get('patterns', {}).items():
                    self.patterns[pid] = LearnedPattern.from_dict(pdata)
                
                # Load wisdom
                for wid, wdata in data.get('wisdom', {}).items():
                    self.wisdom[wid] = TradingWisdom.from_dict(wdata)
                
                # Load paths
                # 🔓 FULL AUTONOMOUS MODE: Never load blocked paths - Queen has full access!
                self.blocked_paths = {}  # Always empty - no blocking!
                self.golden_paths = data.get('golden_paths', {})
                
                # Load stats
                self.total_historical_trades = data.get('total_historical_trades', 0)
                self.total_historical_profit = data.get('total_historical_profit', 0.0)
                self.learning_sessions = data.get('learning_sessions', 0)
                
                # Load insights
                self.best_hours = {int(k): v for k, v in data.get('best_hours', {}).items()}
                self.worst_hours = {int(k): v for k, v in data.get('worst_hours', {}).items()}
                self.best_days = {int(k): v for k, v in data.get('best_days', {}).items()}
                self.asset_performance = data.get('asset_performance', {})
                
                logger.info(f"🐘 Elephant Memory loaded: {len(self.patterns)} patterns, {len(self.wisdom)} wisdoms")
                logger.info(f"   📊 Historical trades: {self.total_historical_trades:,}")
                logger.info(f"   💰 Historical profit: ${self.total_historical_profit:,.2f}")
                logger.info(f"   🚫 Blocked paths: {len(self.blocked_paths)}")
                logger.info(f"   ⭐ Golden paths: {len(self.golden_paths)}")
                
            except Exception as e:
                logger.warning(f"Failed to load elephant memory: {e}")
    
    def _save_memory(self):
        """Save elephant memory to disk - NEVER FORGET!"""
        data = {
            'patterns': {pid: p.to_dict() for pid, p in self.patterns.items()},
            'wisdom': {wid: w.to_dict() for wid, w in self.wisdom.items()},
            'blocked_paths': {},  # 🔓 ALWAYS EMPTY - Full autonomous mode!
            'golden_paths': self.golden_paths,
            'total_historical_trades': self.total_historical_trades,
            'total_historical_profit': self.total_historical_profit,
            'learning_sessions': self.learning_sessions,
            'best_hours': self.best_hours,
            'worst_hours': self.worst_hours,
            'best_days': self.best_days,
            'asset_performance': self.asset_performance,
            'last_saved': datetime.now().isoformat()
        }
        
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"🐘 Elephant Memory saved: {len(self.patterns)} patterns")
    
    def remember_pattern(self, pattern: LearnedPattern):
        """Remember a new pattern FOREVER"""
        self.patterns[pattern.pattern_id] = pattern
        self._save_memory()
        
        # 🐦 CHIRP EMISSION - kHz-Speed Memory Signals
        # Emit pattern learning chirps for system-wide awareness
        if CHIRP_BUS_AVAILABLE and get_chirp_bus:
            try:
                chirp_bus = get_chirp_bus()
                
                chirp_bus.emit_signal(
                    signal_type='ELEPHANT_PATTERN_LEARNED',
                    symbol=pattern.symbol,
                    coherence=pattern.confidence,
                    confidence=pattern.win_rate,
                    frequency=396.0,  # Liberation frequency
                    amplitude=pattern.confidence
                )
                
            except Exception as e:
                # Chirp emission failure - non-critical, continue
                pass
    
    def remember_wisdom(self, wisdom: TradingWisdom):
        """Remember wisdom FOREVER"""
        self.wisdom[wisdom.wisdom_id] = wisdom
        self._save_memory()
        
        # 🐦 CHIRP EMISSION - kHz-Speed Memory Signals
        # Emit wisdom learning chirps for system-wide awareness
        if CHIRP_BUS_AVAILABLE and get_chirp_bus:
            try:
                chirp_bus = get_chirp_bus()
                
                chirp_bus.emit_signal(
                    signal_type='ELEPHANT_WISDOM_LEARNED',
                    symbol='SYSTEM',  # Wisdom applies system-wide
                    coherence=wisdom.confidence,
                    confidence=wisdom.confidence,
                    frequency=528.0,  # Love frequency for wisdom
                    amplitude=wisdom.confidence
                )
                
            except Exception as e:
                # Chirp emission failure - non-critical, continue
                pass
    
    def block_path_forever(self, from_asset: str, to_asset: str, reason: str, 
                           loss_count: int, total_loss: float):
        """Block a trading path FOREVER
        
        🔓 FULL AUTONOMOUS MODE: DO NOT BLOCK - Just log for learning!
        Queen Sero needs all paths available to explore and learn!
        """
        path_key = f"{from_asset}→{to_asset}"
        # 🔓 DISABLED: Don't actually block, just log
        logger.info(f"🐘📝 NOTED (not blocked): {path_key} - {reason} (losses: {loss_count}, total: ${total_loss:.2f})")
        # Original blocking code disabled:
        # self.blocked_paths[path_key] = {...}
        # self._save_memory()
    
    def mark_golden_path(self, from_asset: str, to_asset: str, 
                         win_count: int, total_profit: float, win_rate: float):
        """Mark a consistently winning path"""
        path_key = f"{from_asset}→{to_asset}"
        self.golden_paths[path_key] = {
            'from': from_asset,
            'to': to_asset,
            'win_count': win_count,
            'total_profit': total_profit,
            'win_rate': win_rate,
            'discovered_at': datetime.now().isoformat()
        }
        self._save_memory()
        logger.info(f"🐘⭐ GOLDEN PATH DISCOVERED: {path_key} - {win_rate:.1f}% win rate!")
    
    def is_path_blocked(self, from_asset: str, to_asset: str) -> Tuple[bool, Optional[str]]:
        """Check if a path is permanently blocked
        
        🔓 FULL AUTONOMOUS MODE: NEVER BLOCK ANY PATH!
        Queen Sero must be free to explore ALL possibilities!
        """
        # 🔓 DISABLED FOR FULL AUTONOMOUS TRADING - Let Queen try everything!
        return False, None
    
    def is_golden_path(self, from_asset: str, to_asset: str) -> Tuple[bool, float]:
        """Check if a path is a golden winner"""
        path_key = f"{from_asset}→{to_asset}"
        if path_key in self.golden_paths:
            return True, self.golden_paths[path_key].get('win_rate', 0)
        return False, 0.0
    
    def get_best_trading_hours(self) -> List[int]:
        """Get the best hours to trade based on personal history AND ingrested wisdom"""
        # 1. Gather Personal Experience (Self-Learning)
        personal_best = []
        if self.best_hours:
            sorted_hours = sorted(self.best_hours.items(), key=lambda x: x[1], reverse=True)
            personal_best = [h for h, _ in sorted_hours[:6]] # Top 6 from experience
            
        # 2. Gather Historical Wisdom (Ingested Knowledge)
        wisdom_best = []
        for wid, w in self.wisdom.items():
            if wid.startswith('coinbase_golden_hour_'):
                try:
                    hour = int(wid.split('_')[-1])
                    wisdom_best.append(hour)
                except ValueError:
                    pass
                    
        # 3. Merge & Prioritize
        # If we have NO personal experience, trust Wisdom 100%
        if not personal_best:
            if not wisdom_best:
                return list(range(24)) # Absolute zero knowledge
            return list(set(wisdom_best)) # Return unique wisdom hours
            
        # If we have both, combine them (Union of top personal + all wisdom)
        combined = list(set(personal_best + wisdom_best))
        return combined

    def get_worst_trading_hours(self) -> List[int]:
        """Get hours to AVOID based on history and wisdom"""
        avoid = []
        # Wisdom avoids (e.g. "coinbase_avoid_hour_X")
        for wid, w in self.wisdom.items():
            if wid.startswith('coinbase_avoid_hour_'):
                try:
                    hour = int(wid.split('_')[-1])
                    avoid.append(hour)
                except ValueError:
                    pass
        return list(set(avoid))
    
    def get_asset_score(self, symbol: str) -> float:
        """Get historical performance score for an asset (0-100)"""
        # 1. Base Score from Personal Stats
        if symbol in self.asset_performance:
            stats = self.asset_performance[symbol]
            win_rate = stats.get('win_rate', 50)
            profit_factor = stats.get('profit_factor', 1.0)
            sample_size = stats.get('trades', 0)
            
            # Score based on win rate and profit factor
            base_score = (win_rate + (profit_factor - 1) * 20) / 2
            
            # Confidence adjustment based on sample size
            if sample_size < 10:
                confidence = 0.3
            elif sample_size < 50:
                confidence = 0.6
            elif sample_size < 100:
                confidence = 0.8
            else:
                confidence = 1.0
            
            final_score = 50 + (base_score - 50) * confidence
        else:
            final_score = 50.0  # Neutral if unknown
            
        # 2. Apply Wisdom Modifiers (Macro Context)
        current_date = datetime.now()
        
        # September Effect (Bearish) - Slight penalty
        if current_date.month == 9:
            sept_wisdom = self.wisdom.get('wiki_september_effect')
            if sept_wisdom:
                final_score *= 0.9 
                
        # Weekend Effect (Sunday Dump) - Slight penalty for buys
        if current_date.weekday() == 6: # Sunday
            sunday_wisdom = self.wisdom.get('wiki_sunday_dump')
            if sunday_wisdom:
                final_score *= 0.95
                
        # Bitcoin Halving Boost (Post-Halving Bull Run assumption)
        halving_wisdom = self.wisdom.get('wiki_bitcoin_halving_cycle')
        if halving_wisdom and symbol.startswith('BTC'):
             # Slight permanent boost for BTC if Aware of Halving Cycle
             final_score *= 1.02
             
        return min(100.0, max(0.0, final_score))
    
    def get_pattern_signals(self, symbol: str, current_price: float, 
                           price_change_1h: float, volume_change: float) -> List[Dict]:
        """Get signals from learned patterns"""
        signals = []
        
        for pattern in self.patterns.values():
            if pattern.symbol != symbol and pattern.symbol != '*':
                continue
            
            if pattern.win_rate < 55 or pattern.confidence < 50:
                continue
            
            # Check if current conditions match pattern
            conditions = pattern.conditions
            
            # Momentum pattern
            if pattern.pattern_type == 'momentum':
                min_change = conditions.get('min_change_1h', 0.5)
                if price_change_1h >= min_change:
                    signals.append({
                        'pattern_id': pattern.pattern_id,
                        'type': 'momentum',
                        'action': 'BUY',
                        'confidence': pattern.confidence,
                        'win_rate': pattern.win_rate,
                        'avg_profit': pattern.avg_profit_per_trade,
                        'reason': f"Momentum pattern ({pattern.win_rate:.1f}% win rate)"
                    })
            
            # Reversal pattern
            elif pattern.pattern_type == 'reversal':
                max_drop = conditions.get('max_drop_1h', -2.0)
                if price_change_1h <= max_drop:
                    signals.append({
                        'pattern_id': pattern.pattern_id,
                        'type': 'reversal',
                        'action': 'BUY',
                        'confidence': pattern.confidence,
                        'win_rate': pattern.win_rate,
                        'avg_profit': pattern.avg_profit_per_trade,
                        'reason': f"Reversal pattern ({pattern.win_rate:.1f}% win rate)"
                    })
            
            # Volume breakout
            elif pattern.pattern_type == 'volume_breakout':
                min_volume = conditions.get('min_volume_change', 200)
                if volume_change >= min_volume:
                    signals.append({
                        'pattern_id': pattern.pattern_id,
                        'type': 'volume_breakout',
                        'action': 'BUY',
                        'confidence': pattern.confidence,
                        'win_rate': pattern.win_rate,
                        'avg_profit': pattern.avg_profit_per_trade,
                        'reason': f"Volume breakout ({pattern.win_rate:.1f}% win rate)"
                    })
        
        return signals
    
    def summarize(self) -> str:
        """Get a summary of elephant memory"""
        lines = [
            "🐘 QUEEN'S ELEPHANT MEMORY SUMMARY 🐘",
            "=" * 50,
            f"📊 Learning sessions: {self.learning_sessions}",
            f"📈 Historical trades analyzed: {self.total_historical_trades:,}",
            f"💰 Historical profit (sim): ${self.total_historical_profit:,.2f}",
            f"",
            f"🧠 Patterns learned: {len(self.patterns)}",
            f"💡 Wisdom collected: {len(self.wisdom)}",
            f"🚫 Blocked paths: {len(self.blocked_paths)}",
            f"⭐ Golden paths: {len(self.golden_paths)}",
            f"📊 Assets tracked: {len(self.asset_performance)}",
            ""
        ]
        
        # Best patterns
        if self.patterns:
            best = sorted(self.patterns.values(), 
                         key=lambda p: p.win_rate * p.confidence, 
                         reverse=True)[:5]
            lines.append("🏆 TOP 5 PATTERNS:")
            for p in best:
                lines.append(f"   • {p.pattern_type}: {p.win_rate:.1f}% win ({p.total_occurrences} trades)")
        
        # Golden paths
        if self.golden_paths:
            lines.append("")
            lines.append("⭐ GOLDEN PATHS (HIGH WIN RATE):")
            for path, data in list(self.golden_paths.items())[:5]:
                lines.append(f"   • {path}: {data['win_rate']:.1f}% win, ${data['total_profit']:.2f} profit")
        
        # Blocked paths
        if self.blocked_paths:
            lines.append("")
            lines.append("🚫 BLOCKED PATHS (ALWAYS LOSE):")
            for path, data in list(self.blocked_paths.items())[:5]:
                lines.append(f"   • {path}: {data['reason']}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 HISTORICAL DATA LEARNER
# ═══════════════════════════════════════════════════════════════════════════════

class HistoricalLearner:
    """
    Learn from historical data and store in elephant memory
    """
    
    # Public APIs for historical data
    BINANCE_URL = "https://api.binance.com"
    COINGECKO_URL = "https://api.coingecko.com/api/v3"
    
    # Trading fee assumption
    TRADING_FEE = 0.001  # 0.1% per trade
    
    def __init__(self, elephant_memory: ElephantMemory):
        self.memory = elephant_memory
        self.session = requests.Session()
        self.cache_file = "historical_candles_cache.json"
        self.cached_data: Dict[str, List] = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cached historical data"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_cache(self):
        """Save historical data to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cached_data, f)
    
    def fetch_binance_history(self, symbol: str, interval: str = '1h', 
                              days: int = 30) -> List[Dict]:
        """
        Fetch historical candles from Binance (PUBLIC API)
        """
        cache_key = f"binance_{symbol}_{interval}_{days}d"
        
        # Check cache first
        if cache_key in self.cached_data:
            logger.info(f"📦 Using cached data for {symbol}")
            return self.cached_data[cache_key]
        
        try:
            # Calculate time range
            end_time = int(time.time() * 1000)
            start_time = end_time - (days * 24 * 60 * 60 * 1000)
            
            url = f"{self.BINANCE_URL}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': start_time,
                'endTime': end_time,
                'limit': 1000
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            candles = []
            for k in response.json():
                candles.append({
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'symbol': symbol
                })
            
            # Cache it
            self.cached_data[cache_key] = candles
            self._save_cache()
            
            logger.info(f"📊 Fetched {len(candles)} candles for {symbol}")
            return candles
            
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
            return []
    
    def analyze_patterns(self, candles: List[Dict]) -> Dict[str, LearnedPattern]:
        """
        Analyze historical candles for patterns
        """
        if len(candles) < 100:
            return {}
        
        patterns = {}
        symbol = candles[0]['symbol'] if candles else 'UNKNOWN'
        
        # Track simulated trades
        trades = []
        
        # Strategy 1: Momentum (buy after 1%+ rise)
        momentum_wins = 0
        momentum_losses = 0
        momentum_profit = 0.0
        momentum_loss = 0.0
        
        for i in range(24, len(candles) - 4):
            prev_close = candles[i-1]['close']
            curr_close = candles[i]['close']
            change = ((curr_close - prev_close) / prev_close) * 100
            
            if change >= 1.0:  # 1%+ rise
                # Simulate buying and holding for 4 hours
                entry_price = curr_close
                exit_price = candles[i + 4]['close']
                
                # Calculate profit after fees
                gross_profit_pct = ((exit_price - entry_price) / entry_price) * 100
                net_profit_pct = gross_profit_pct - (self.TRADING_FEE * 2 * 100)  # Buy + sell fee
                
                if net_profit_pct > 0:
                    momentum_wins += 1
                    momentum_profit += net_profit_pct
                else:
                    momentum_losses += 1
                    momentum_loss += abs(net_profit_pct)
                
                trades.append({
                    'type': 'momentum',
                    'entry': entry_price,
                    'exit': exit_price,
                    'profit_pct': net_profit_pct
                })
        
        # Create momentum pattern
        if momentum_wins + momentum_losses > 20:
            total = momentum_wins + momentum_losses
            pattern = LearnedPattern(
                pattern_id=f"momentum_{symbol}_1h",
                pattern_type='momentum',
                symbol=symbol,
                timeframe='1h',
                conditions={'min_change_1h': 1.0, 'hold_hours': 4},
                total_occurrences=total,
                winning_trades=momentum_wins,
                losing_trades=momentum_losses,
                total_profit=momentum_profit,
                total_loss=momentum_loss,
                win_rate=(momentum_wins / total) * 100 if total > 0 else 0,
                avg_profit_per_trade=(momentum_profit - momentum_loss) / total if total > 0 else 0,
                profit_factor=momentum_profit / momentum_loss if momentum_loss > 0 else 0,
                first_seen=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                confidence=min(90, 50 + total / 2)
            )
            patterns[pattern.pattern_id] = pattern
        
        # Strategy 2: Reversal (buy after 2%+ drop)
        reversal_wins = 0
        reversal_losses = 0
        reversal_profit = 0.0
        reversal_loss = 0.0
        
        for i in range(24, len(candles) - 4):
            prev_close = candles[i-1]['close']
            curr_close = candles[i]['close']
            change = ((curr_close - prev_close) / prev_close) * 100
            
            if change <= -2.0:  # 2%+ drop
                entry_price = curr_close
                exit_price = candles[i + 4]['close']
                
                gross_profit_pct = ((exit_price - entry_price) / entry_price) * 100
                net_profit_pct = gross_profit_pct - (self.TRADING_FEE * 2 * 100)
                
                if net_profit_pct > 0:
                    reversal_wins += 1
                    reversal_profit += net_profit_pct
                else:
                    reversal_losses += 1
                    reversal_loss += abs(net_profit_pct)
        
        # Create reversal pattern
        if reversal_wins + reversal_losses > 20:
            total = reversal_wins + reversal_losses
            pattern = LearnedPattern(
                pattern_id=f"reversal_{symbol}_1h",
                pattern_type='reversal',
                symbol=symbol,
                timeframe='1h',
                conditions={'max_drop_1h': -2.0, 'hold_hours': 4},
                total_occurrences=total,
                winning_trades=reversal_wins,
                losing_trades=reversal_losses,
                total_profit=reversal_profit,
                total_loss=reversal_loss,
                win_rate=(reversal_wins / total) * 100 if total > 0 else 0,
                avg_profit_per_trade=(reversal_profit - reversal_loss) / total if total > 0 else 0,
                profit_factor=reversal_profit / reversal_loss if reversal_loss > 0 else 0,
                first_seen=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                confidence=min(90, 50 + total / 2)
            )
            patterns[pattern.pattern_id] = pattern
        
        # Strategy 3: Volume breakout
        volume_wins = 0
        volume_losses = 0
        volume_profit = 0.0
        volume_loss = 0.0
        
        for i in range(24, len(candles) - 4):
            avg_volume = sum(c['volume'] for c in candles[i-24:i]) / 24
            curr_volume = candles[i]['volume']
            
            if curr_volume > avg_volume * 3:  # 3x average volume
                entry_price = candles[i]['close']
                exit_price = candles[i + 4]['close']
                
                gross_profit_pct = ((exit_price - entry_price) / entry_price) * 100
                net_profit_pct = gross_profit_pct - (self.TRADING_FEE * 2 * 100)
                
                if net_profit_pct > 0:
                    volume_wins += 1
                    volume_profit += net_profit_pct
                else:
                    volume_losses += 1
                    volume_loss += abs(net_profit_pct)
        
        # Create volume pattern
        if volume_wins + volume_losses > 10:
            total = volume_wins + volume_losses
            pattern = LearnedPattern(
                pattern_id=f"volume_{symbol}_1h",
                pattern_type='volume_breakout',
                symbol=symbol,
                timeframe='1h',
                conditions={'min_volume_change': 300, 'hold_hours': 4},
                total_occurrences=total,
                winning_trades=volume_wins,
                losing_trades=volume_losses,
                total_profit=volume_profit,
                total_loss=volume_loss,
                win_rate=(volume_wins / total) * 100 if total > 0 else 0,
                avg_profit_per_trade=(volume_profit - volume_loss) / total if total > 0 else 0,
                profit_factor=volume_profit / volume_loss if volume_loss > 0 else 0,
                first_seen=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                confidence=min(80, 40 + total)
            )
            patterns[pattern.pattern_id] = pattern
        
        # Analyze best hours
        hourly_profits = defaultdict(list)
        for i, candle in enumerate(candles[:-1]):
            ts = datetime.fromtimestamp(candle['timestamp'] / 1000)
            hour = ts.hour
            
            next_close = candles[i + 1]['close']
            change = ((next_close - candle['close']) / candle['close']) * 100
            hourly_profits[hour].append(change)
        
        # Update elephant memory with hour insights
        for hour, profits in hourly_profits.items():
            avg_profit = sum(profits) / len(profits) if profits else 0
            if avg_profit > 0.1:
                self.memory.best_hours[hour] = avg_profit
            elif avg_profit < -0.1:
                self.memory.worst_hours[hour] = avg_profit
        
        return patterns
    
    def learn_from_symbol(self, symbol: str, days: int = 90) -> Dict:
        """Learn everything from a symbol's history"""
        logger.info(f"🐘📚 Learning from {symbol} ({days} days)...")
        
        # Fetch data
        candles = self.fetch_binance_history(symbol, '1h', days)
        
        if not candles:
            return {'success': False, 'reason': 'No data available'}
        
        # Analyze patterns
        patterns = self.analyze_patterns(candles)
        
        # Store in elephant memory
        for pattern in patterns.values():
            self.memory.remember_pattern(pattern)
        
        # Update asset performance
        total_trades = sum(p.total_occurrences for p in patterns.values())
        total_wins = sum(p.winning_trades for p in patterns.values())
        total_profit = sum(p.total_profit - p.total_loss for p in patterns.values())
        
        self.memory.asset_performance[symbol] = {
            'trades': total_trades,
            'wins': total_wins,
            'win_rate': (total_wins / total_trades * 100) if total_trades > 0 else 50,
            'total_profit': total_profit,
            'profit_factor': sum(p.profit_factor for p in patterns.values()) / len(patterns) if patterns else 1.0,
            'last_analyzed': datetime.now().isoformat()
        }
        
        # Update stats
        self.memory.total_historical_trades += total_trades
        self.memory.total_historical_profit += total_profit
        self.memory.learning_sessions += 1
        self.memory._save_memory()
        
        return {
            'success': True,
            'symbol': symbol,
            'candles_analyzed': len(candles),
            'patterns_found': len(patterns),
            'total_trades': total_trades,
            'win_rate': (total_wins / total_trades * 100) if total_trades > 0 else 0,
            'profit': total_profit
        }
    
    def learn_all_major_pairs(self, days: int = 30):
        """Learn from all major trading pairs"""
        major_pairs = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
            'SOLUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'MATICUSDT',
            'LTCUSDT', 'ATOMUSDT', 'UNIUSDT', 'NEARUSDT', 'APTUSDT'
        ]
        
        results = []
        for symbol in major_pairs:
            try:
                result = self.learn_from_symbol(symbol, days)
                results.append(result)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.warning(f"Failed to learn {symbol}: {e}")
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# 👑 QUEEN INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

class QueenElephantBrain:
    """
    Queen Sero's brain enhanced with elephant memory
    """
    
    def __init__(self):
        self.elephant = ElephantMemory()
        self.learner = HistoricalLearner(self.elephant)
        
        logger.info("🐘👑 Queen's Elephant Brain initialized!")
        logger.info(f"   📊 Patterns in memory: {len(self.elephant.patterns)}")
        logger.info(f"   🚫 Blocked paths: {len(self.elephant.blocked_paths)}")
        logger.info(f"   ⭐ Golden paths: {len(self.elephant.golden_paths)}")
    
    def should_trade(self, from_asset: str, to_asset: str, 
                     price_change: float, volume_change: float) -> Dict:
        """
        Use elephant memory to decide if a trade is good
        """
        # Check if path is blocked
        is_blocked, reason = self.elephant.is_path_blocked(from_asset, to_asset)
        if is_blocked:
            return {
                'should_trade': False,
                'confidence': 100,
                'reason': f"🐘🚫 ELEPHANT NEVER FORGETS: {reason}"
            }
        
        # Check if path is golden
        is_golden, win_rate = self.elephant.is_golden_path(from_asset, to_asset)
        if is_golden and win_rate > 70:
            return {
                'should_trade': True,
                'confidence': win_rate,
                'reason': f"🐘⭐ GOLDEN PATH: {win_rate:.1f}% historical win rate!"
            }
        
        # Check hour
        current_hour = datetime.now().hour
        if current_hour in self.elephant.worst_hours:
            return {
                'should_trade': False,
                'confidence': 70,
                'reason': f"🐘⏰ BAD HOUR: Hour {current_hour} historically loses money"
            }
        
        # Get pattern signals
        signals = self.elephant.get_pattern_signals(
            f"{from_asset}{to_asset}",
            0,  # Would need real price
            price_change,
            volume_change
        )
        
        if signals:
            best_signal = max(signals, key=lambda s: s['confidence'])
            return {
                'should_trade': best_signal['win_rate'] > 55,
                'confidence': best_signal['confidence'],
                'reason': f"🐘📊 PATTERN: {best_signal['reason']}",
                'expected_profit': best_signal['avg_profit']
            }
        
        # Check asset score
        asset_score = self.elephant.get_asset_score(to_asset)
        if asset_score < 40:
            return {
                'should_trade': False,
                'confidence': 60,
                'reason': f"🐘📉 WEAK ASSET: {to_asset} scores {asset_score:.1f}/100"
            }
        
        # Default: no strong signal
        return {
            'should_trade': False,
            'confidence': 50,
            'reason': "🐘🤔 NO STRONG PATTERN - waiting for better setup"
        }
    
    def learn_before_trading(self, days: int = 30):
        """Learn from history before starting to trade"""
        logger.info("🐘📚 ELEPHANT LEARNING SESSION STARTING...")
        logger.info(f"   📅 Analyzing {days} days of historical data")
        
        results = self.learner.learn_all_major_pairs(days)
        
        # Summary
        total_patterns = sum(r.get('patterns_found', 0) for r in results if r.get('success'))
        total_trades = sum(r.get('total_trades', 0) for r in results if r.get('success'))
        avg_win_rate = sum(r.get('win_rate', 0) for r in results if r.get('success')) / len(results)
        
        logger.info(f"🐘✅ LEARNING COMPLETE!")
        logger.info(f"   📊 Patterns learned: {total_patterns}")
        logger.info(f"   📈 Trades analyzed: {total_trades}")
        logger.info(f"   🎯 Average win rate: {avg_win_rate:.1f}%")
        
        return {
            'patterns_learned': total_patterns,
            'trades_analyzed': total_trades,
            'avg_win_rate': avg_win_rate
        }
    
    def record_trade_result(self, from_asset: str, to_asset: str, 
                           profit: float, was_profitable: bool):
        """Record a real trade result in elephant memory"""
        path_key = f"{from_asset}→{to_asset}"
        
        # Update or create path stats
        if path_key not in self.elephant.asset_performance:
            self.elephant.asset_performance[path_key] = {
                'trades': 0, 'wins': 0, 'losses': 0,
                'total_profit': 0, 'total_loss': 0
            }
        
        stats = self.elephant.asset_performance[path_key]
        stats['trades'] += 1
        
        if was_profitable:
            stats['wins'] += 1
            stats['total_profit'] += profit
        else:
            stats['losses'] += 1
            stats['total_loss'] += abs(profit)
        
        stats['win_rate'] = (stats['wins'] / stats['trades']) * 100
        
        # Auto-block consistently losing paths
        if stats['trades'] >= 5 and stats['win_rate'] < 30:
            self.elephant.block_path_forever(
                from_asset, to_asset,
                f"Only {stats['win_rate']:.1f}% win rate after {stats['trades']} trades",
                stats['losses'],
                stats['total_loss']
            )
        
        # Auto-mark golden paths
        if stats['trades'] >= 10 and stats['win_rate'] > 70:
            self.elephant.mark_golden_path(
                from_asset, to_asset,
                stats['wins'],
                stats['total_profit'],
                stats['win_rate']
            )
        
        self.elephant._save_memory()

    def record_trade_outcome(self, outcome: Any):
        """Convenience method to accept WinOutcome dict or dataclass and record it."""
        try:
            if isinstance(outcome, dict):
                from_asset = outcome.get('from_asset') or outcome.get('from') or ''
                to_asset = outcome.get('to_asset') or outcome.get('to') or ''
                profit = outcome.get('net_profit_usd') or outcome.get('pnl') or outcome.get('profit_usd') or 0.0
                is_win = bool(outcome.get('is_win') or (profit is not None and float(profit) >= 0.01))
            else:
                # Dataclass-like object
                from_asset = getattr(outcome, 'from_asset', '')
                to_asset = getattr(outcome, 'to_asset', '')
                profit = getattr(outcome, 'net_profit_usd', None) or getattr(outcome, 'pnl', None) or 0.0
                is_win = bool(getattr(outcome, 'is_win', (profit is not None and float(profit) >= 0.01)))

            # Fall back if empty
            if not from_asset or not to_asset:
                return False

            self.record_trade_result(from_asset, to_asset, float(profit), is_win)
            return True
        except Exception:
            logger.exception('Failed to record trade outcome in Elephant Memory')
            return False

# ═══════════════════════════════════════════════════════════════════════════════
# 🏃 MAIN - Test the elephant learning
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("🐘👑 QUEEN SERO's ELEPHANT MEMORY LEARNING SYSTEM 👑🐘")
    print("=" * 70)
    print()
    print('"An elephant NEVER forgets. Neither does Queen Sero."')
    print()
    
    # Initialize
    brain = QueenElephantBrain()
    
    # Show current memory
    print()
    print(brain.elephant.summarize())
    print()
    
    # Learn from history
    print("=" * 70)
    print("📚 LEARNING FROM HISTORICAL DATA...")
    print("=" * 70)
    
    # Learn from top pairs
    results = brain.learn_before_trading(days=30)
    
    print()
    print("=" * 70)
    print("🐘 LEARNING COMPLETE!")
    print("=" * 70)
    print(f"   📊 Patterns learned: {results['patterns_learned']}")
    print(f"   📈 Trades analyzed: {results['trades_analyzed']}")
    print(f"   🎯 Average win rate: {results['avg_win_rate']:.1f}%")
    print()
    
    # Show updated memory
    print(brain.elephant.summarize())
    
    # Test a trade decision
    print()
    print("=" * 70)
    print("🧪 TESTING TRADE DECISIONS...")
    print("=" * 70)
    
    # Test cases
    test_trades = [
        ('USDT', 'BTC', 1.5, 200),   # Momentum + volume
        ('BTC', 'ETH', -2.5, 50),    # Reversal pattern
        ('USDT', 'DOGE', 0.1, 10),   # No pattern
    ]
    
    for from_a, to_a, price_chg, vol_chg in test_trades:
        result = brain.should_trade(from_a, to_a, price_chg, vol_chg)
        print(f"\n{from_a}→{to_a} (price:{price_chg:+.1f}%, vol:{vol_chg}%):")
        print(f"   Trade: {'✅ YES' if result['should_trade'] else '❌ NO'}")
        print(f"   Confidence: {result['confidence']:.1f}%")
        print(f"   Reason: {result['reason']}")


if __name__ == "__main__":
    main()
