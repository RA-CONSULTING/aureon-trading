#!/usr/bin/env python3
"""
👑 QUEEN AUTO-TAGGER
Automatic bot classification and tagging based on behavior patterns
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable


@dataclass
class AutoTagRule:
    """Rule for automatically tagging bots"""
    name: str
    condition: Callable  # Function that takes bot data and returns bool
    tag: str
    reason: str
    priority: int = 1  # Higher = applied first
    alert_queen: bool = False  # Should Queen narrate this?


class QueenAutoTagger:
    """
    Automatically tags bots based on behavioral patterns.
    Queen's intelligent classification system.
    """
    
    def __init__(self, state=None):
        self.state = state
        self.rules = self._initialize_rules()
        self.tags_applied = 0
        self.alerts_generated = 0
        
    def _initialize_rules(self) -> List[AutoTagRule]:
        """Initialize all auto-tagging rules"""
        
        return [
            # --- CRITICAL THREATS ---
            AutoTagRule(
                name="mega_whale",
                condition=lambda b: self._get_volume(b) > 1_000_000,
                tag="MEGA_WHALE",
                reason="Volume exceeds $1M threshold - institutional threat",
                priority=10,
                alert_queen=True
            ),
            
            AutoTagRule(
                name="whale_sweep",
                condition=lambda b: self._get_volume(b) > 500_000 and self._get_size(b) == 'whale',
                tag="whale_sweep",
                reason="Large whale position building - likely liquidity sweep incoming",
                priority=9,
                alert_queen=True
            ),
            
            AutoTagRule(
                name="coordinated_attack",
                condition=lambda b: self._check_firm_surge(b),
                tag="coordinated",
                reason="Multiple bots from same firm detected - coordinated attack pattern",
                priority=8,
                alert_queen=True
            ),
            
            # --- HIGH PRIORITY ---
            AutoTagRule(
                name="spoofing_pattern",
                condition=lambda b: self._detect_spoofing(b),
                tag="spoofing",
                reason="Rapid order/cancel pattern detected - possible market manipulation",
                priority=7,
                alert_queen=True
            ),
            
            AutoTagRule(
                name="hft_shark",
                condition=lambda b: self._get_size(b) == 'shark' and self._get_volume(b) > 100_000,
                tag="hft_shark",
                reason="High-frequency shark pattern - predatory trading",
                priority=6,
                alert_queen=False
            ),
            
            AutoTagRule(
                name="front_runner",
                condition=lambda b: self._detect_front_running(b),
                tag="front_runner",
                reason="Leading large orders consistently - front-running suspected",
                priority=6,
                alert_queen=True
            ),
            
            # --- MONITORING ---
            AutoTagRule(
                name="accumulator",
                condition=lambda b: self._detect_accumulation(b),
                tag="accumulator",
                reason="Steady accumulation pattern - building large position",
                priority=5,
                alert_queen=False
            ),
            
            AutoTagRule(
                name="ghost_pattern",
                condition=lambda b: self._detect_ghost_pattern(b),
                tag="ghost_alameda",
                reason="Pattern matches defunct Alameda Research signature",
                priority=4,
                alert_queen=True
            ),
            
            AutoTagRule(
                name="wash_trader",
                condition=lambda b: self._detect_wash_trading(b),
                tag="wash_trader",
                reason="Self-trading pattern detected - artificial volume",
                priority=4,
                alert_queen=False
            ),
            
            # --- STANDARD CLASSIFICATIONS ---
            AutoTagRule(
                name="market_maker",
                condition=lambda b: self._detect_market_maker(b),
                tag="market_maker",
                reason="Providing liquidity on both sides - legitimate MM",
                priority=2,
                alert_queen=False
            ),
            
            AutoTagRule(
                name="retail_bot",
                condition=lambda b: self._get_volume(b) < 10_000,
                tag="retail",
                reason="Small volume - likely retail algorithm",
                priority=1,
                alert_queen=False
            ),
        ]
    
    # --- Detection Methods ---
    
    def _get_volume(self, bot_data: Dict) -> float:
        """Extract volume from bot data - check multiple sources"""
        # Check for raw volume attached directly
        if hasattr(bot_data, '_raw_volume'):
            return bot_data._raw_volume
        # Check metrics object
        if hasattr(bot_data, 'metrics'):
            return getattr(bot_data.metrics, 'total_volume_usd', 0)
        # Check dict keys
        if isinstance(bot_data, dict):
            return bot_data.get('total_volume_usd', 0) or bot_data.get('volume', 0) or bot_data.get('value_usd', 0)
        return bot_data.get('volume', 0) or bot_data.get('metrics', {}).get('total_volume_usd', 0)
    
    def _get_size(self, bot_data: Dict) -> str:
        """Extract size class"""
        if hasattr(bot_data, 'size_class'):
            return bot_data.size_class.lower()
        return (bot_data.get('size_class') or bot_data.get('size', 'minnow')).lower()
    
    def _check_firm_surge(self, bot_data: Dict) -> bool:
        """Check if firm has multiple bots active"""
        if not self.state:
            return False
        owner = getattr(bot_data, 'owner_name', None) or bot_data.get('owner_name')
        if not owner or owner == 'unknown':
            return False
        # Check if this firm has 3+ bots in last 60 seconds
        recent_count = self.state.firm_activity.get(owner, 0)
        return recent_count >= 3
    
    def _detect_spoofing(self, bot_data: Dict) -> bool:
        """Detect spoofing pattern"""
        # Check for rapid order placement/cancellation
        if hasattr(bot_data, 'metrics'):
            tps = getattr(bot_data.metrics, 'trades_per_second', 0)
            return tps > 5  # More than 5 trades/sec = possible spoofing
        return False
    
    def _detect_front_running(self, bot_data: Dict) -> bool:
        """Detect front-running behavior"""
        # Check if bot consistently trades right before large moves
        # For now, use latency as proxy
        if hasattr(bot_data, 'metrics'):
            latency = getattr(bot_data.metrics, 'avg_latency_ms', 999)
            return latency < 10  # Ultra-low latency = potential front-runner
        return False
    
    def _detect_accumulation(self, bot_data: Dict) -> bool:
        """Detect accumulation pattern"""
        # Steady small buys over time
        if hasattr(bot_data, 'strategies'):
            strategies = bot_data.strategies or []
            return 'accumulation' in strategies or 'accumulator' in strategies
        return False
    
    def _detect_ghost_pattern(self, bot_data: Dict) -> bool:
        """Detect patterns matching defunct firms (Alameda, 3AC)"""
        owner = getattr(bot_data, 'owner_name', None) or bot_data.get('owner_name', '')
        if 'alameda' in owner.lower() or 'three arrows' in owner.lower():
            return True
        # Check for ghost pattern characteristics
        return False
    
    def _detect_wash_trading(self, bot_data: Dict) -> bool:
        """Detect wash trading (self-trading)"""
        if hasattr(bot_data, 'metrics'):
            mm_ratio = getattr(bot_data.metrics, 'market_making_ratio', 0)
            # Perfect 50/50 buy/sell with high volume = suspicious
            return 0.48 < mm_ratio < 0.52 and self._get_volume(bot_data) > 50_000
        return False
    
    def _detect_market_maker(self, bot_data: Dict) -> bool:
        """Detect legitimate market maker"""
        if hasattr(bot_data, 'strategies'):
            strategies = bot_data.strategies or []
            return 'market_making' in strategies
        return False
    
    # --- Main Processing ---
    
    def process_bot(self, bot_id: str, bot_data: Dict) -> Optional[Dict]:
        """
        Process a bot and auto-tag if rules match.
        Returns tag info if applied, None otherwise.
        """
        # Sort rules by priority
        sorted_rules = sorted(self.rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            try:
                if rule.condition(bot_data):
                    # Apply tag
                    tag_info = {
                        'tag': rule.tag,
                        'reason': rule.reason,
                        'actor': 'auto_tagger',
                        'timestamp': time.time(),
                        'rule_name': rule.name
                    }
                    
                    self.tags_applied += 1
                    
                    # Alert Queen if configured
                    if rule.alert_queen and self.state:
                        alert_msg = f"AUTO-TAG: {bot_id} flagged as {rule.tag}. {rule.reason}"
                        self.state.add_queen_message(alert_msg, 'warning' if 'threat' in rule.tag.lower() else 'info')
                        self.alerts_generated += 1
                    
                    return tag_info
            except Exception as e:
                print(f"Auto-tag rule '{rule.name}' failed: {e}")
                continue
        
        return None
    
    def get_stats(self) -> Dict:
        """Return auto-tagger statistics"""
        return {
            'rules_active': len(self.rules),
            'tags_applied': self.tags_applied,
            'alerts_generated': self.alerts_generated
        }


# Singleton instance
_auto_tagger = None

def get_auto_tagger(state=None):
    """Get or create auto-tagger instance"""
    global _auto_tagger
    if _auto_tagger is None:
        _auto_tagger = QueenAutoTagger(state=state)
    return _auto_tagger
