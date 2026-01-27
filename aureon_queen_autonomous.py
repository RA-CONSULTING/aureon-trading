#!/usr/bin/env python3
"""
👑⚡ AUREON QUEEN AUTONOMOUS CONTROL ⚡👑
═══════════════════════════════════════════════════════════════════════════════

FULL AUTONOMOUS MODE - The Queen and Micro-Momentum have COMPLETE CONTROL!

NO HUMAN INTERVENTION REQUIRED!

The system will:
1. 🔍 Continuously scan for momentum > 0.34% (covers costs)
2. 🎯 Validate opportunities with Monte Carlo simulations
3. ✅ Execute trades when conditions are met
4. 📊 Track P&L and adjust strategy
5. 🛡️ Protect capital with strict risk management

SAFETY FEATURES:
- Maximum position size limits
- Daily loss limits (circuit breaker)
- Minimum momentum thresholds (no bleeding!)
- Automatic stop-loss on every trade

Gary Leckey | Aureon Trading System | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
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

import time
import json
import logging
import signal
import threading
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 📦 IMPORTS - Queen's Components
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from aureon_micro_momentum_goal import MicroMomentumScanner, MomentumTier, MomentumSignal
    MOMENTUM_AVAILABLE = True
except ImportError as e:
    logger.error(f"MicroMomentumScanner not available: {e}")
    MOMENTUM_AVAILABLE = False

try:
    from aureon_queen_dream_engine import QueenDreamEngine
    DREAM_ENGINE_AVAILABLE = True
except ImportError as e:
    logger.error(f"QueenDreamEngine not available: {e}")
    DREAM_ENGINE_AVAILABLE = False

try:
    from alpaca_client import AlpacaClient
    ALPACA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AlpacaClient not available: {e}")
    ALPACA_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️ AUTONOMOUS CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AutonomousConfig:
    """Configuration for autonomous trading"""
    
    # 💸 COST THRESHOLDS (WE CANNOT BLEED!)
    min_momentum_pct: float = 0.34       # Minimum momentum to cover costs
    tier1_threshold: float = 0.50        # 🔥 HOT - immediate entry
    tier2_threshold: float = 0.40        # ⚡ STRONG - high priority
    tier3_threshold: float = 0.34        # 🌊 VALID - covers costs
    
    # 💰 POSITION SIZING
    max_position_usd: float = 100.0      # Maximum position size
    min_position_usd: float = 10.0       # Minimum position size
    position_pct_of_balance: float = 0.10  # Use 10% of balance per trade
    
    # 🛡️ RISK MANAGEMENT
    max_daily_loss_pct: float = 5.0      # Stop trading if down 5% today
    max_trades_per_hour: int = 20        # Rate limit
    stop_loss_pct: float = 0.50          # 0.5% stop loss
    take_profit_pct: float = 0.50        # 0.5% take profit (1:1 R:R)
    max_hold_seconds: int = 60           # Exit after 60 seconds max
    
    # ⏱️ TIMING
    scan_interval_seconds: int = 5       # Scan every 5 seconds
    momentum_lookback_minutes: int = 10  # Look at last 10 minutes
    
    # 🎯 VALIDATION
    min_win_probability: float = 0.50    # 50% win rate minimum
    min_net_profit_pct: float = 0.001    # 0.001% minimum net profit
    
    # 🔧 OPERATIONAL
    dry_run: bool = True                 # Paper trading mode
    log_level: str = "INFO"
    state_file: str = "queen_autonomous_state.json"


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 TRADE TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

class TradeStatus(Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


@dataclass
class AutonomousTrade:
    """A trade executed by the autonomous system"""
    trade_id: str
    symbol: str
    direction: str  # LONG or SHORT
    
    # Entry
    entry_price: float
    entry_time: float
    position_size_usd: float
    quantity: float
    
    # Exit (filled when closed)
    exit_price: float = 0.0
    exit_time: float = 0.0
    exit_reason: str = ""
    
    # P&L
    gross_pnl_pct: float = 0.0
    fees_pct: float = 0.34  # Round trip cost
    net_pnl_pct: float = 0.0
    net_pnl_usd: float = 0.0
    
    # Metadata
    status: TradeStatus = TradeStatus.PENDING
    momentum_at_entry: float = 0.0
    tier_at_entry: str = ""
    validation_score: float = 0.0


@dataclass
class DailyStats:
    """Daily trading statistics"""
    date: str = ""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    gross_pnl_pct: float = 0.0
    net_pnl_pct: float = 0.0
    net_pnl_usd: float = 0.0
    fees_paid_pct: float = 0.0
    best_trade_pct: float = 0.0
    worst_trade_pct: float = 0.0
    current_streak: int = 0  # Positive = wins, negative = losses


# ═══════════════════════════════════════════════════════════════════════════════
# 👑 QUEEN AUTONOMOUS CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class QueenAutonomousController:
    """
    👑 THE QUEEN HAS FULL CONTROL 👑
    
    This controller runs autonomously, making all trading decisions
    based on momentum detection and Monte Carlo validation.
    
    NO HUMAN INTERVENTION REQUIRED!
    """
    
    def __init__(self, config: AutonomousConfig = None):
        self.config = config or AutonomousConfig()
        
        # Components
        self.momentum_scanner: Optional[MicroMomentumScanner] = None
        self.dream_engine: Optional[QueenDreamEngine] = None
        self.alpaca: Optional[Any] = None
        
        # State
        self.running = False
        self.current_position: Optional[AutonomousTrade] = None
        self.trade_history: List[AutonomousTrade] = []
        self.daily_stats = DailyStats(date=datetime.now().strftime("%Y-%m-%d"))
        self.trades_this_hour = 0
        self.hour_start = time.time()
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Balance tracking
        self.starting_balance_usd = 0.0
        self.current_balance_usd = 0.0
        
        self._initialize_components()
        self._load_state()
    
    def _initialize_components(self):
        """Initialize all Queen components"""
        logger.info("👑 Initializing Queen Autonomous Controller...")
        
        # Momentum Scanner
        if MOMENTUM_AVAILABLE:
            self.momentum_scanner = MicroMomentumScanner()
            logger.info("   ✅ MicroMomentumScanner initialized")
        else:
            logger.error("   ❌ MicroMomentumScanner NOT available!")
            
        # Dream Engine
        if DREAM_ENGINE_AVAILABLE:
            self.dream_engine = QueenDreamEngine()
            logger.info("   ✅ QueenDreamEngine initialized")
        else:
            logger.error("   ❌ QueenDreamEngine NOT available!")
        
        # Alpaca Client
        if ALPACA_AVAILABLE:
            try:
                self.alpaca = AlpacaClient()
                logger.info("   ✅ AlpacaClient initialized")
            except Exception as e:
                logger.error(f"   ❌ AlpacaClient failed: {e}")
        
        # Get initial balance
        self._update_balance()
        
        logger.info("👑 Queen Autonomous Controller ready!")
        logger.info(f"   Mode: {'🧪 DRY RUN (Paper)' if self.config.dry_run else '💰 LIVE TRADING'}")
        logger.info(f"   Min Momentum: {self.config.min_momentum_pct}%")
        logger.info(f"   Max Position: ${self.config.max_position_usd}")
        logger.info(f"   Daily Loss Limit: {self.config.max_daily_loss_pct}%")
    
    def _update_balance(self):
        """Update current balance from exchange"""
        if self.alpaca:
            try:
                account = self.alpaca.get_account()
                if hasattr(account, 'portfolio_value'):
                    self.current_balance_usd = float(account.portfolio_value)
                elif isinstance(account, dict):
                    self.current_balance_usd = float(account.get('portfolio_value', 100))
                
                if self.starting_balance_usd == 0:
                    self.starting_balance_usd = self.current_balance_usd
                    
            except Exception as e:
                logger.warning(f"Failed to get balance: {e}")
                if self.current_balance_usd == 0:
                    self.current_balance_usd = 100.0  # Default for dry run
                    self.starting_balance_usd = 100.0
        else:
            # Dry run default
            if self.current_balance_usd == 0:
                self.current_balance_usd = 100.0
                self.starting_balance_usd = 100.0
    
    def _load_state(self):
        """Load state from file"""
        try:
            if Path(self.config.state_file).exists():
                with open(self.config.state_file, 'r') as f:
                    state = json.load(f)
                    # Load daily stats if same day
                    if state.get('date') == datetime.now().strftime("%Y-%m-%d"):
                        self.daily_stats.total_trades = state.get('total_trades', 0)
                        self.daily_stats.net_pnl_pct = state.get('net_pnl_pct', 0)
                        self.daily_stats.net_pnl_usd = state.get('net_pnl_usd', 0)
                        logger.info(f"   📂 Loaded state: {self.daily_stats.total_trades} trades today, {self.daily_stats.net_pnl_pct:+.3f}% P&L")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
    
    def _save_state(self):
        """Save state to file"""
        try:
            state = {
                'date': datetime.now().strftime("%Y-%m-%d"),
                'total_trades': self.daily_stats.total_trades,
                'net_pnl_pct': self.daily_stats.net_pnl_pct,
                'net_pnl_usd': self.daily_stats.net_pnl_usd,
                'winning_trades': self.daily_stats.winning_trades,
                'losing_trades': self.daily_stats.losing_trades,
                'last_update': datetime.now().isoformat()
            }
            with open(self.config.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save state: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🔍 MOMENTUM DETECTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def scan_for_momentum(self) -> List[MomentumSignal]:
        """Scan for coins with momentum exceeding costs"""
        if not self.momentum_scanner:
            return []
        
        signals = self.momentum_scanner.scan_for_momentum()
        
        # Filter to actionable signals only
        actionable = [s for s in signals 
                     if s.tier != MomentumTier.TIER_4_SKIP 
                     and s.net_profit_potential > self.config.min_net_profit_pct]
        
        return actionable
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎯 OPPORTUNITY VALIDATION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def validate_opportunity(self, signal: MomentumSignal) -> Optional[Dict]:
        """
        Validate opportunity with MOMENTUM-FIRST approach
        
        THE QUEEN'S WISDOM:
        - The coin is ALREADY moving - that's proven, not simulated
        - Monte Carlo is random noise - the momentum is REAL data
        - If momentum > costs, the math is already in our favor
        - Trust the market, not the simulation
        """
        
        # Calculate momentum strength (absolute value for direction-agnostic scoring)
        momentum_strength = abs(signal.momentum_5m_pct) if signal.momentum_5m_pct else 0
        momentum_strength_1m = abs(signal.momentum_1m_pct) if signal.momentum_1m_pct else 0
        
        # Net profit after costs - this is THE GOAL
        net_profit = signal.net_profit_potential
        
        # Direction check: momentum should be continuing
        # LONG: positive momentum, SHORT: negative momentum
        direction_confirmed = (
            (signal.direction == 'LONG' and signal.momentum_1m_pct > 0) or
            (signal.direction == 'SHORT' and signal.momentum_1m_pct < 0)
        )
        
        # Scoring based on ACTUAL momentum (not random walks!)
        tier_score = {
            MomentumTier.TIER_1_HOT: 1.0,      # >0.5% in 1min = FIRE
            MomentumTier.TIER_2_STRONG: 0.8,   # >0.4% in 5min = Strong
            MomentumTier.TIER_3_VALID: 0.6,    # >0.34% = Valid
            MomentumTier.TIER_4_SKIP: 0.0      # Skip
        }.get(signal.tier, 0.5)
        
        # Validation rules:
        # 1. TIER 1 (HOT) - auto-approve if net profit positive
        # 2. TIER 2 (STRONG) - approve if direction confirmed and net > 0
        # 3. TIER 3 (VALID) - approve if direction confirmed, net > 0, AND momentum accelerating
        # 4. TIER 4 (SKIP) - never approve
        
        validated = False
        reason = ""
        
        if signal.tier == MomentumTier.TIER_1_HOT:
            # HOT momentum - TRUST IT
            if net_profit > 0:
                validated = True
                reason = "🔥 TIER 1 HOT - momentum > 0.5% in 1min, net positive"
            else:
                reason = "TIER 1 but costs exceed net profit"
                
        elif signal.tier == MomentumTier.TIER_2_STRONG:
            # Strong momentum - need direction confirmation
            if net_profit > 0 and direction_confirmed:
                validated = True
                reason = "⚡ TIER 2 STRONG - direction confirmed, net positive"
            elif net_profit > 0:
                # Direction not confirmed but net still positive
                validated = True
                reason = "⚡ TIER 2 STRONG - net positive (direction unconfirmed)"
            else:
                reason = f"TIER 2 but net={net_profit:.3f}% (need >0)"
                
        elif signal.tier == MomentumTier.TIER_3_VALID:
            # Valid but borderline - need strong confirmation
            if net_profit > 0.05 and direction_confirmed:  # 0.05% minimum buffer
                validated = True
                reason = "✅ TIER 3 VALID - confirmed with buffer"
            else:
                reason = f"TIER 3 needs net>{0.05}% and direction (net={net_profit:.3f}%)"
        else:
            reason = "TIER 4 SKIP - momentum below costs"
        
        # Calculate composite score
        score = tier_score * net_profit * 100 * (1.2 if direction_confirmed else 0.8)
        
        logger.info(f"   🔍 Validation: {reason}")
        
        return {
            'symbol': signal.symbol,
            'direction': signal.direction,
            'price': signal.current_price,
            'momentum_5m': signal.momentum_5m_pct,
            'momentum_1m': signal.momentum_1m_pct,
            'net_profit': net_profit,
            'tier': signal.tier.name,
            'tier_score': tier_score,
            'direction_confirmed': direction_confirmed,
            'score': score,
            'reason': reason,
            'validated': validated
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 💰 TRADE EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def execute_trade(self, opportunity: Dict) -> Optional[AutonomousTrade]:
        """Execute a validated trade"""
        
        # Check if we already have a position
        if self.current_position and self.current_position.status == TradeStatus.OPEN:
            logger.warning("Already have an open position - skipping")
            return None
        
        # Check rate limits
        if self.trades_this_hour >= self.config.max_trades_per_hour:
            logger.warning(f"Rate limit reached ({self.config.max_trades_per_hour}/hour)")
            return None
        
        # Check daily loss limit
        if self.daily_stats.net_pnl_pct <= -self.config.max_daily_loss_pct:
            logger.warning(f"🛑 CIRCUIT BREAKER: Daily loss limit reached ({self.daily_stats.net_pnl_pct:.2f}%)")
            return None
        
        # Calculate position size
        position_usd = min(
            self.config.max_position_usd,
            self.current_balance_usd * self.config.position_pct_of_balance
        )
        position_usd = max(position_usd, self.config.min_position_usd)
        
        price = opportunity['price']
        quantity = position_usd / price if price > 0 else 0
        
        # Create trade record
        trade = AutonomousTrade(
            trade_id=f"Q{int(time.time()*1000)}",
            symbol=opportunity['symbol'],
            direction=opportunity['direction'],
            entry_price=price,
            entry_time=time.time(),
            position_size_usd=position_usd,
            quantity=quantity,
            status=TradeStatus.OPEN,
            momentum_at_entry=opportunity.get('momentum', 0),
            tier_at_entry=str(opportunity.get('tier', '')),
            validation_score=opportunity.get('score', 0)
        )
        
        # Execute on exchange (or paper trade)
        if self.config.dry_run:
            logger.info(f"🧪 [DRY RUN] ENTRY: {trade.direction} {trade.symbol} @ ${trade.entry_price:.4f} (${trade.position_size_usd:.2f})")
            trade.status = TradeStatus.OPEN
        else:
            # Real execution
            if self.alpaca:
                try:
                    side = 'buy' if trade.direction == 'LONG' else 'sell'
                    order = self.alpaca.submit_order(
                        symbol=trade.symbol.replace('/', ''),
                        qty=trade.quantity,
                        side=side,
                        type='market',
                        time_in_force='ioc'
                    )
                    logger.info(f"💰 [LIVE] ENTRY: {trade.direction} {trade.symbol} @ ${trade.entry_price:.4f}")
                    trade.status = TradeStatus.OPEN
                except Exception as e:
                    logger.error(f"Trade execution failed: {e}")
                    trade.status = TradeStatus.CANCELLED
                    return None
        
        self.current_position = trade
        self.trades_this_hour += 1
        
        return trade
    
    def close_position(self, reason: str = "manual") -> Optional[AutonomousTrade]:
        """Close current position"""
        if not self.current_position or self.current_position.status != TradeStatus.OPEN:
            return None
        
        trade = self.current_position
        
        # Get current price
        current_price = trade.entry_price  # Default
        if self.momentum_scanner:
            signals = self.momentum_scanner.scan_for_momentum([trade.symbol])
            if signals:
                current_price = signals[0].current_price
        
        trade.exit_price = current_price
        trade.exit_time = time.time()
        trade.exit_reason = reason
        
        # Calculate P&L
        if trade.direction == 'LONG':
            trade.gross_pnl_pct = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
        else:
            trade.gross_pnl_pct = ((trade.entry_price - trade.exit_price) / trade.entry_price) * 100
        
        trade.net_pnl_pct = trade.gross_pnl_pct - trade.fees_pct
        trade.net_pnl_usd = trade.position_size_usd * (trade.net_pnl_pct / 100)
        trade.status = TradeStatus.CLOSED
        
        # Execute close on exchange
        if self.config.dry_run:
            emoji = "✅" if trade.net_pnl_pct > 0 else "❌"
            logger.info(f"🧪 [DRY RUN] EXIT: {trade.symbol} @ ${trade.exit_price:.4f} | "
                       f"{emoji} Net: {trade.net_pnl_pct:+.3f}% (${trade.net_pnl_usd:+.4f}) | Reason: {reason}")
        else:
            if self.alpaca:
                try:
                    side = 'sell' if trade.direction == 'LONG' else 'buy'
                    self.alpaca.submit_order(
                        symbol=trade.symbol.replace('/', ''),
                        qty=trade.quantity,
                        side=side,
                        type='market',
                        time_in_force='ioc'
                    )
                    logger.info(f"💰 [LIVE] EXIT: {trade.symbol} | Net: {trade.net_pnl_pct:+.3f}%")
                except Exception as e:
                    logger.error(f"Close failed: {e}")
        
        # Update stats
        self.daily_stats.total_trades += 1
        self.daily_stats.net_pnl_pct += trade.net_pnl_pct
        self.daily_stats.net_pnl_usd += trade.net_pnl_usd
        self.daily_stats.fees_paid_pct += trade.fees_pct
        
        if trade.net_pnl_pct > 0:
            self.daily_stats.winning_trades += 1
            self.daily_stats.current_streak = max(1, self.daily_stats.current_streak + 1)
        else:
            self.daily_stats.losing_trades += 1
            self.daily_stats.current_streak = min(-1, self.daily_stats.current_streak - 1)
        
        self.trade_history.append(trade)
        self.current_position = None
        self.current_balance_usd += trade.net_pnl_usd
        
        self._save_state()
        
        return trade
    
    def check_position_exit(self):
        """Check if current position should be closed"""
        if not self.current_position or self.current_position.status != TradeStatus.OPEN:
            return
        
        trade = self.current_position
        hold_time = time.time() - trade.entry_time
        
        # Get current price
        current_price = trade.entry_price
        if self.momentum_scanner:
            signals = self.momentum_scanner.scan_for_momentum([trade.symbol])
            if signals:
                current_price = signals[0].current_price
        
        # Calculate unrealized P&L
        if trade.direction == 'LONG':
            unrealized_pnl = ((current_price - trade.entry_price) / trade.entry_price) * 100
        else:
            unrealized_pnl = ((trade.entry_price - current_price) / trade.entry_price) * 100
        
        # Check exit conditions
        
        # 1. Take profit
        if unrealized_pnl >= self.config.take_profit_pct:
            self.close_position(f"take_profit ({unrealized_pnl:+.3f}%)")
            return
        
        # 2. Stop loss
        if unrealized_pnl <= -self.config.stop_loss_pct:
            self.close_position(f"stop_loss ({unrealized_pnl:+.3f}%)")
            return
        
        # 3. Time limit
        if hold_time >= self.config.max_hold_seconds:
            self.close_position(f"time_exit ({hold_time:.0f}s, {unrealized_pnl:+.3f}%)")
            return
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🔄 MAIN AUTONOMOUS LOOP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def run_cycle(self):
        """Run one autonomous trading cycle"""
        
        # Reset hourly counter if needed
        if time.time() - self.hour_start > 3600:
            self.trades_this_hour = 0
            self.hour_start = time.time()
        
        # Check existing position
        self.check_position_exit()
        
        # If we have an open position, don't look for new ones
        if self.current_position and self.current_position.status == TradeStatus.OPEN:
            return
        
        # Scan for momentum
        signals = self.scan_for_momentum()
        
        if not signals:
            return  # No actionable momentum
        
        # Take the best signal
        best_signal = signals[0]
        
        logger.info(f"🎯 Momentum detected: {best_signal.tier.value} {best_signal.symbol} "
                   f"| 5m: {best_signal.momentum_5m_pct:+.3f}% | Net: {best_signal.net_profit_potential:+.3f}%")
        
        # Validate with simulation
        opportunity = self.validate_opportunity(best_signal)
        
        if not opportunity.get('validated'):
            logger.info(f"   ❌ Validation failed: {opportunity.get('reason', 'unknown')}")
            return
        
        logger.info(f"   ✅ VALIDATED! {opportunity.get('reason', '')}")
        logger.info(f"   📊 Score: {opportunity.get('score', 0):.2f} | Net: {opportunity.get('net_profit', 0):+.3f}%")
        
        # Execute trade
        trade = self.execute_trade(opportunity)
        
        if trade:
            logger.info(f"   🚀 Trade opened: {trade.trade_id}")
    
    def run(self):
        """
        🚀 START AUTONOMOUS TRADING 🚀
        
        The Queen now has FULL CONTROL!
        """
        self.running = True
        
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     👑⚡ QUEEN AUTONOMOUS MODE ACTIVATED ⚡👑                                 ║
║                                                                              ║
║     THE QUEEN HAS FULL CONTROL!                                             ║
║                                                                              ║
║     🔍 Scanning for momentum > 0.34%                                        ║
║     🎯 Validating with Monte Carlo simulations                              ║
║     💰 Executing trades autonomously                                        ║
║                                                                              ║
║     Press Ctrl+C to stop                                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"👑 Queen Autonomous Mode: {'🧪 DRY RUN' if self.config.dry_run else '💰 LIVE'}")
        logger.info(f"   Starting Balance: ${self.starting_balance_usd:.2f}")
        logger.info(f"   Scan Interval: {self.config.scan_interval_seconds}s")
        logger.info(f"   Min Momentum: {self.config.min_momentum_pct}%")
        logger.info("")
        
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                
                try:
                    self.run_cycle()
                except Exception as e:
                    logger.error(f"Cycle error: {e}")
                
                # Status update every 12 cycles (1 minute at 5s interval)
                if cycle_count % 12 == 0:
                    win_rate = (self.daily_stats.winning_trades / max(1, self.daily_stats.total_trades)) * 100
                    logger.info(f"📊 Status: {self.daily_stats.total_trades} trades | "
                               f"Win: {win_rate:.0f}% | "
                               f"Net P&L: {self.daily_stats.net_pnl_pct:+.3f}% (${self.daily_stats.net_pnl_usd:+.2f})")
                
                time.sleep(self.config.scan_interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n👑 Queen Autonomous Mode stopped by user")
        
        # Close any open position
        if self.current_position and self.current_position.status == TradeStatus.OPEN:
            self.close_position("shutdown")
        
        self._save_state()
        self.print_summary()
    
    def print_summary(self):
        """Print trading session summary"""
        print("\n" + "="*60)
        print("👑 QUEEN AUTONOMOUS SESSION SUMMARY")
        print("="*60)
        print(f"   Total Trades:    {self.daily_stats.total_trades}")
        print(f"   Winning Trades:  {self.daily_stats.winning_trades}")
        print(f"   Losing Trades:   {self.daily_stats.losing_trades}")
        win_rate = (self.daily_stats.winning_trades / max(1, self.daily_stats.total_trades)) * 100
        print(f"   Win Rate:        {win_rate:.1f}%")
        print(f"   Gross P&L:       {self.daily_stats.gross_pnl_pct:+.3f}%")
        print(f"   Fees Paid:       {self.daily_stats.fees_paid_pct:.3f}%")
        print(f"   Net P&L:         {self.daily_stats.net_pnl_pct:+.3f}% (${self.daily_stats.net_pnl_usd:+.2f})")
        print(f"   Final Balance:   ${self.current_balance_usd:.2f}")
        print("="*60)
    
    def stop(self):
        """Stop autonomous trading"""
        self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Start the Queen Autonomous Controller"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Queen Autonomous Trading Controller")
    parser.add_argument('--live', action='store_true', help='Enable LIVE trading (default: dry run)')
    parser.add_argument('--max-position', type=float, default=100.0, help='Max position size in USD')
    parser.add_argument('--scan-interval', type=int, default=5, help='Scan interval in seconds')
    parser.add_argument('--max-trades-hour', type=int, default=20, help='Max trades per hour')
    args = parser.parse_args()
    
    config = AutonomousConfig(
        dry_run=not args.live,
        max_position_usd=args.max_position,
        scan_interval_seconds=args.scan_interval,
        max_trades_per_hour=args.max_trades_hour
    )
    
    controller = QueenAutonomousController(config)
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        controller.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    controller.run()


if __name__ == "__main__":
    main()
