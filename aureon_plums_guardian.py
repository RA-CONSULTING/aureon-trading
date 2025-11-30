"""
🇬🇧💎 AUREON PLUMS GUARDIAN 💎🇬🇧
Big Plums Safety System - Extracted from TSX Intelligence

This module implements:
1. ATR-based Volatility Stops (2x ATR from TechnologyRoadmap.tsx)
2. Max Portfolio Drawdown Circuit Breaker (15% from TechnologyRoadmap.tsx)
3. Max Position Hold Time (72 hours from TechnologyRoadmap.tsx)
4. Max Daily Loss Limiter (from RiskManagementDashboard.tsx)
5. Emergency Kill Switch (from TechnologyRoadmap.tsx)
6. Dynamic Leverage Adjustment (1x-5x from TechnologyRoadmap.tsx)
7. UK Trading Compliance Checks

DISCOVERED FROM: TechnologyRoadmap.tsx, RiskManagementDashboard.tsx, AurisNodesVisualization.tsx
"""

import time
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class GuardianLimits:
    """Risk limits from TSX discovery"""
    max_drawdown_pct: float = 0.15  # 15% from TechnologyRoadmap.tsx
    max_position_hold_hours: float = 72.0  # 72 hours from TechnologyRoadmap.tsx
    max_daily_loss_usd: float = 50.0  # Dynamic based on capital
    atr_stop_multiplier: float = 2.0  # 2x ATR from TechnologyRoadmap.tsx
    min_leverage: float = 1.0  # From TechnologyRoadmap.tsx
    max_leverage: float = 5.0  # From TechnologyRoadmap.tsx
    
    # UK-specific
    max_position_pct: float = 0.80  # 80% max per position (BIG PLUMS!)
    min_liquidity_usd: float = 50000  # Minimum 24h volume


class ATRCalculator:
    """Calculate Average True Range for volatility-adjusted stops"""
    
    def __init__(self, period: int = 14):
        self.period = period
        self.tr_history: List[float] = []
    
    def calculate_tr(self, high: float, low: float, prev_close: float) -> float:
        """True Range = max(H-L, |H-Prev_Close|, |L-Prev_Close|)"""
        range1 = high - low
        range2 = abs(high - prev_close)
        range3 = abs(low - prev_close)
        return max(range1, range2, range3)
    
    def update(self, high: float, low: float, prev_close: float) -> float:
        """Update ATR with new candle data"""
        tr = self.calculate_tr(high, low, prev_close)
        self.tr_history.append(tr)
        
        # Keep only last 'period' values
        if len(self.tr_history) > self.period:
            self.tr_history.pop(0)
        
        # ATR = average of true ranges
        atr = sum(self.tr_history) / len(self.tr_history)
        return atr
    
    def get_stop_distance(self, atr: float, multiplier: float = 2.0) -> float:
        """Get stop loss distance based on ATR"""
        return atr * multiplier


class PortfolioDrawdownMonitor:
    """15% max drawdown circuit breaker from TechnologyRoadmap.tsx"""
    
    def __init__(self, max_drawdown_pct: float = 0.15):
        self.max_drawdown_pct = max_drawdown_pct
        self.peak_value: float = 0.0
        self.circuit_breaker_active: bool = False
        self.breaker_triggered_at: Optional[float] = None
    
    def update(self, current_value: float) -> Tuple[bool, float]:
        """
        Update portfolio value and check for circuit breaker
        
        Returns:
            (is_breaker_active, current_drawdown_pct)
        """
        # Track peak
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        # Calculate drawdown
        if self.peak_value > 0:
            drawdown = (self.peak_value - current_value) / self.peak_value
        else:
            drawdown = 0.0
        
        # Check circuit breaker
        if drawdown >= self.max_drawdown_pct and not self.circuit_breaker_active:
            self.circuit_breaker_active = True
            self.breaker_triggered_at = time.time()
            logger.warning(
                f"🚨 CIRCUIT BREAKER TRIGGERED! Drawdown: {drawdown*100:.1f}% "
                f"(max: {self.max_drawdown_pct*100:.1f}%)"
            )
        
        return self.circuit_breaker_active, drawdown
    
    def reset_breaker(self):
        """Manually reset circuit breaker"""
        self.circuit_breaker_active = False
        self.breaker_triggered_at = None
        logger.info("✅ Circuit breaker RESET")


class MaxHoldTimeMonitor:
    """72-hour max position hold time from TechnologyRoadmap.tsx"""
    
    def __init__(self, max_hours: float = 72.0):
        self.max_hours = max_hours
        self.position_entries: Dict[str, float] = {}  # symbol -> entry_timestamp
    
    def record_entry(self, symbol: str):
        """Record position entry time"""
        self.position_entries[symbol] = time.time()
        logger.info(f"⏰ Started timer for {symbol} (max: {self.max_hours}h)")
    
    def check_expired(self, symbol: str) -> Tuple[bool, float]:
        """
        Check if position has exceeded max hold time
        
        Returns:
            (is_expired, hours_held)
        """
        if symbol not in self.position_entries:
            return False, 0.0
        
        entry_time = self.position_entries[symbol]
        hours_held = (time.time() - entry_time) / 3600
        is_expired = hours_held >= self.max_hours
        
        if is_expired:
            logger.warning(
                f"⏰ {symbol} EXCEEDED MAX HOLD TIME: {hours_held:.1f}h "
                f"(max: {self.max_hours}h)"
            )
        
        return is_expired, hours_held
    
    def remove_position(self, symbol: str):
        """Remove position from tracking"""
        if symbol in self.position_entries:
            del self.position_entries[symbol]


class DailyLossLimiter:
    """Max daily loss from RiskManagementDashboard.tsx"""
    
    def __init__(self, max_loss_usd: float):
        self.max_loss_usd = max_loss_usd
        self.daily_pnl: float = 0.0
        self.last_reset: datetime = datetime.now()
        self.loss_limit_hit: bool = False
    
    def record_trade(self, pnl: float):
        """Record trade P&L"""
        # Reset if new day
        now = datetime.now()
        if now.date() != self.last_reset.date():
            self.reset_daily()
        
        self.daily_pnl += pnl
        
        # Check if loss limit hit
        if self.daily_pnl <= -self.max_loss_usd and not self.loss_limit_hit:
            self.loss_limit_hit = True
            logger.warning(
                f"🚨 DAILY LOSS LIMIT HIT: ${self.daily_pnl:.2f} "
                f"(max: ${self.max_loss_usd:.2f})"
            )
    
    def can_trade(self) -> Tuple[bool, float]:
        """Check if can still trade today"""
        return not self.loss_limit_hit, self.daily_pnl
    
    def reset_daily(self):
        """Reset daily tracking"""
        self.daily_pnl = 0.0
        self.loss_limit_hit = False
        self.last_reset = datetime.now()
        logger.info("🔄 Daily loss limiter RESET")


class DynamicLeverageAdjuster:
    """1x-5x dynamic leverage from TechnologyRoadmap.tsx"""
    
    def __init__(self, min_lev: float = 1.0, max_lev: float = 5.0):
        self.min_lev = min_lev
        self.max_lev = max_lev
    
    def calculate_leverage(self, volatility: float, confidence: float) -> float:
        """
        Calculate leverage based on volatility and signal confidence
        
        Args:
            volatility: Market volatility (0.0 - 1.0, normalized)
            confidence: Signal confidence/coherence (0.0 - 1.0)
        
        Returns:
            Leverage multiplier (1.0 - 5.0)
        """
        # Low volatility + high confidence = higher leverage
        # High volatility + low confidence = lower leverage
        
        # Inverse volatility factor (high vol = low factor)
        vol_factor = 1.0 - min(volatility, 1.0)
        
        # Combined score
        score = (vol_factor + confidence) / 2.0
        
        # Map score to leverage range
        leverage = self.min_lev + (score * (self.max_lev - self.min_lev))
        
        return max(self.min_lev, min(leverage, self.max_lev))


class UKComplianceChecker:
    """🇬🇧 UK Binance Trading Compliance"""
    
    def __init__(self):
        # UK-restricted pairs (update based on Binance UK restrictions)
        self.restricted_quotes = ['USDC']  # USDC pairs often restricted
        self.allowed_quotes = ['USDT', 'BTC', 'ETH', 'BNB', 'EUR', 'GBP']
    
    def is_pair_allowed(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if pair is allowed for UK trading
        
        Returns:
            (is_allowed, reason)
        """
        # Check quote currency
        for quote in self.restricted_quotes:
            if symbol.endswith(quote):
                return False, f"UK restricts {quote} pairs"
        
        # Check if uses allowed quote
        for quote in self.allowed_quotes:
            if symbol.endswith(quote):
                return True, f"Allowed: {quote} pair"
        
        return False, "Unknown quote currency"


class PlumsGuardian:
    """
    🇬🇧💎 MAIN BIG PLUMS GUARDIAN 💎🇬🇧
    
    Unified risk management system extracted from TSX files
    """
    
    def __init__(self, initial_capital: float, limits: Optional[GuardianLimits] = None):
        self.limits = limits or GuardianLimits()
        self.initial_capital = initial_capital
        
        # Initialize all sub-systems
        self.drawdown_monitor = PortfolioDrawdownMonitor(self.limits.max_drawdown_pct)
        self.hold_time_monitor = MaxHoldTimeMonitor(self.limits.max_position_hold_hours)
        self.daily_loss_limiter = DailyLossLimiter(self.limits.max_daily_loss_usd)
        self.leverage_adjuster = DynamicLeverageAdjuster(
            self.limits.min_leverage, 
            self.limits.max_leverage
        )
        self.uk_compliance = UKComplianceChecker()
        self.atr_calculators: Dict[str, ATRCalculator] = {}  # symbol -> ATRCalculator
        
        # Emergency kill switch
        self.kill_switch_active: bool = False
        
        logger.info(
            f"🇬🇧💎 PLUMS GUARDIAN INITIALIZED 💎🇬🇧\n"
            f"  Max Drawdown: {self.limits.max_drawdown_pct*100:.0f}%\n"
            f"  Max Hold Time: {self.limits.max_position_hold_hours:.0f}h\n"
            f"  Max Daily Loss: ${self.limits.max_daily_loss_usd:.2f}\n"
            f"  ATR Stop Multiplier: {self.limits.atr_stop_multiplier}x\n"
            f"  Leverage Range: {self.limits.min_leverage}x - {self.limits.max_leverage}x"
        )
    
    def check_can_enter(self, symbol: str, portfolio_value: float) -> Tuple[bool, str]:
        """
        Check if new position entry is allowed
        
        Returns:
            (can_enter, reason)
        """
        # Emergency kill switch
        if self.kill_switch_active:
            return False, "🚨 KILL SWITCH ACTIVE"
        
        # Circuit breaker
        is_breaker_active, drawdown = self.drawdown_monitor.update(portfolio_value)
        if is_breaker_active:
            return False, f"🚨 Circuit breaker active (DD: {drawdown*100:.1f}%)"
        
        # Daily loss limit
        can_trade, daily_pnl = self.daily_loss_limiter.can_trade()
        if not can_trade:
            return False, f"🚨 Daily loss limit hit (${daily_pnl:.2f})"
        
        # UK compliance
        is_allowed, reason = self.uk_compliance.is_pair_allowed(symbol)
        if not is_allowed:
            return False, f"🇬🇧 {reason}"
        
        return True, "✅ All checks passed"
    
    def calculate_position_size(
        self, 
        symbol: str,
        balance: float, 
        volatility: float, 
        confidence: float
    ) -> float:
        """
        Calculate position size with all safety checks
        
        Args:
            symbol: Trading pair
            balance: Available balance
            volatility: Normalized volatility (0-1)
            confidence: Signal confidence (0-1)
        
        Returns:
            Position size in USD
        """
        # Base size from config
        base_size = balance * self.limits.max_position_pct
        
        # Apply dynamic leverage
        leverage = self.leverage_adjuster.calculate_leverage(volatility, confidence)
        
        # Final size
        size = base_size * leverage
        
        logger.info(
            f"💎 {symbol} SIZE: Base=${base_size:.2f} × {leverage:.2f}x = ${size:.2f}"
        )
        
        return size
    
    def get_atr_stop(
        self, 
        symbol: str, 
        entry_price: float,
        high: float, 
        low: float, 
        prev_close: float
    ) -> float:
        """
        Calculate ATR-based stop loss
        
        Returns:
            Stop loss price
        """
        # Get or create ATR calculator
        if symbol not in self.atr_calculators:
            self.atr_calculators[symbol] = ATRCalculator()
        
        atr_calc = self.atr_calculators[symbol]
        atr = atr_calc.update(high, low, prev_close)
        stop_distance = atr_calc.get_stop_distance(atr, self.limits.atr_stop_multiplier)
        
        # Stop loss = entry - (ATR * multiplier)
        stop_price = entry_price - stop_distance
        
        logger.info(
            f"📊 {symbol} ATR STOP: ATR={atr:.6f} × {self.limits.atr_stop_multiplier} "
            f"= Stop @ ${stop_price:.6f}"
        )
        
        return stop_price
    
    def record_entry(self, symbol: str):
        """Record position entry for hold time tracking"""
        self.hold_time_monitor.record_entry(symbol)
    
    def check_exit(self, symbol: str) -> Tuple[bool, str]:
        """
        Check if position should be exited
        
        Returns:
            (should_exit, reason)
        """
        # Check hold time
        is_expired, hours_held = self.hold_time_monitor.check_expired(symbol)
        if is_expired:
            return True, f"⏰ Max hold time exceeded ({hours_held:.1f}h)"
        
        return False, ""
    
    def record_exit(self, symbol: str, pnl: float):
        """Record position exit"""
        self.hold_time_monitor.remove_position(symbol)
        self.daily_loss_limiter.record_trade(pnl)
        
        logger.info(f"📊 {symbol} EXIT: P&L=${pnl:.2f} | Daily: ${self.daily_loss_limiter.daily_pnl:.2f}")
    
    def activate_kill_switch(self):
        """🚨 EMERGENCY KILL SWITCH"""
        self.kill_switch_active = True
        logger.warning("🚨🚨🚨 EMERGENCY KILL SWITCH ACTIVATED! 🚨🚨🚨")
    
    def deactivate_kill_switch(self):
        """Reset kill switch"""
        self.kill_switch_active = False
        logger.info("✅ Kill switch deactivated")
    
    def get_status(self) -> str:
        """Get guardian status for display"""
        can_trade, _ = self.daily_loss_limiter.can_trade()
        
        status = (
            f"🇬🇧💎 PLUMS GUARDIAN 💎🇬🇧\n"
            f"  Circuit Breaker: {'🚨 ACTIVE' if self.drawdown_monitor.circuit_breaker_active else '✅ OK'}\n"
            f"  Daily Loss: ${self.daily_loss_limiter.daily_pnl:.2f} / ${self.limits.max_daily_loss_usd:.2f}\n"
            f"  Kill Switch: {'🚨 ACTIVE' if self.kill_switch_active else '✅ ARMED'}\n"
            f"  Active Positions: {len(self.hold_time_monitor.position_entries)}"
        )
        
        return status
