#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║              🪞 AUREON UI BRIDGE - BIDIRECTIONAL MIRROR SYNC 🪞               ║
║═══════════════════════════════════════════════════════════════════════════════║
║                                                                               ║
║   TWO MIRRORS FACING EACH OTHER - DATA FLOWS BOTH WAYS:                       ║
║                                                                               ║
║   🖥️ TERMINAL (You)              🌐 UI (aureoninstitute.com)                  ║
║   ┌─────────────┐                ┌─────────────────────┐                     ║
║   │ Live trades │ ──PUSH──►     │ Aggregated stats    │                     ║
║   │ Positions   │                │ ALL users' data     │                     ║
║   │ Kill Scanner│ ◄──PULL──     │ Global coherence    │                     ║
║   │ Local state │                │ Cross-user patterns │                     ║
║   └─────────────┘                └─────────────────────┘                     ║
║                                                                               ║
║   TERMINAL HAS (unique to you):   UI HAS (aggregated from all):              ║
║   • Real-time execution state     • Sniper leaderboard (all users)          ║
║   • Pending signals               • Global harmonic coherence (Γ)           ║
║   • Local P&L velocity            • Fear & Greed (market-wide)              ║
║   • Kill Scanner ETA              • Cross-exchange arbitrage                 ║
║   • Mycelium local state          • Pattern correlations                     ║
║                                                                               ║
║   "Two mirrors reflecting infinity - each sees what the other cannot"        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
import time
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AureonUIBridge")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

AUREON_UI_CONFIG = {
    'BASE_URL': 'https://aureoninstitute.com',
    'SUPABASE_URL': os.getenv('SUPABASE_URL', ''),
    'SUPABASE_KEY': os.getenv('SUPABASE_ANON_KEY', ''),
    
    # ═══════════════════════════════════════════════════════════════════════
    # PULL ENDPOINTS - Get aggregated data FROM the UI (what other users generated)
    # ═══════════════════════════════════════════════════════════════════════
    'PULL_ENDPOINTS': {
        'market_data': '/functions/v1/fetch-all-tickers',
        'positions': '/functions/v1/fetch-open-positions',
        'positions_pnl': '/functions/v1/fetch-positions-pnl',
        'coherence_forecast': '/functions/v1/forecast-coherence',
        'unified_field': '/functions/v1/unified-field-analysis',
        'schumann': '/functions/v1/fetch-schumann-data',
        'harmonic_nexus': '/functions/v1/sync-harmonic-nexus',
        'trades': '/functions/v1/fetch-trades',
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # PUSH ENDPOINTS - Send terminal state TO the UI (your data enriches others)
    # ═══════════════════════════════════════════════════════════════════════
    'PUSH_ENDPOINTS': {
        'terminal_state': '/functions/v1/ingest-terminal-state',
        'ecosystem_snapshot': '/functions/v1/ingest-ecosystem-snapshot',
        'trades': '/functions/v1/ingest-trades',
        'brain_state': '/functions/v1/ingest-brain-state',
        'auris_state': '/functions/v1/ingest-auris-state',
        'probability_matrix': '/functions/v1/ingest-probability-matrix',
        'performance': '/functions/v1/ingest-performance-tracker',
        'kelly': '/functions/v1/ingest-kelly-computation',
        'hnc': '/functions/v1/ingest-hnc-detection',
        'telescope': '/functions/v1/ingest-telescope-state',
        'calibration': '/functions/v1/ingest-calibration-trade',
    },
    
    # Validation Thresholds
    'COHERENCE_MIN': 0.30,
    'COHERENCE_OPTIMAL': 0.70,
    'FEAR_GREED_EXTREME_FEAR': 25,
    'FEAR_GREED_EXTREME_GREED': 75,
    'DISTORTION_WARNING': 440,  # Hz
    'HARMONY_BAND': (426, 434),  # Hz range
    
    # Refresh Intervals (seconds)
    'MARKET_DATA_REFRESH': 10,
    'POSITIONS_REFRESH': 30,
    'HARMONIC_REFRESH': 60,
    'FIELD_REFRESH': 300,
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class FrequencyBand(Enum):
    """Harmonic frequency bands from UI"""
    LOVE = 'LOVE'           # 528 Hz - Healing
    HARMONY = 'HARMONY'     # 432 Hz - Natural
    LIBERATION = 'LIBERATION'  # 396 Hz - Release
    TRANSFORMATION = 'TRANSFORMATION'  # 417 Hz - Change
    DISTORTION = 'DISTORTION'  # 440 Hz - Artificial
    NEUTRAL = 'NEUTRAL'


class Element(Enum):
    """Platonic elements from UI"""
    FIRE = 'FIRE'       # 🔥 Tetrahedron
    WATER = 'WATER'     # 💧 Icosahedron  
    EARTH = 'EARTH'     # 🌍 Cube
    AIR = 'AIR'         # 💨 Octahedron
    ETHER = 'ETHER'     # ✨ Dodecahedron


class RiskLevel(Enum):
    """Risk levels from UI"""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'


@dataclass
class SniperKill:
    """Kill from Sniper Leaderboard"""
    symbol: str
    sniper_name: str
    province: str  # Ulster, Munster, etc.
    shots: int
    wins: int
    losses: int
    accuracy: float
    pnl: float
    rank: int = 0


@dataclass
class HarmonicReading:
    """Harmonic field reading from UI"""
    frequency: float  # Hz
    band: FrequencyBand
    element: Element
    coherence: float  # Γ (Gamma)
    schumann_sync: float  # % aligned with Earth
    phi_harmony: float  # Golden ratio alignment
    optimal_entry_score: int  # 0-100
    signal_confidence: float  # %
    recommended_action: str  # BUY/SELL/HOLD
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FearGreedIndex:
    """Fear & Greed sentiment from UI"""
    value: int  # 0-100
    label: str  # "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
    temperature: str  # HOT/COLD
    bull_bear_ratio: Tuple[float, float]  # (bull%, bear%)
    momentum: float  # % 
    momentum_direction: str  # ↗️ Bullish / ↘️ Bearish


@dataclass
class ArbitrageOpportunity:
    """Cross-exchange arbitrage from UI"""
    symbol: str
    exchange_buy: str
    exchange_sell: str
    spread_percent: float
    estimated_profit: float


@dataclass
class PositionStatus:
    """Position from UI with full details"""
    symbol: str
    exchange: str
    quantity: float
    cost_basis: float
    current_price: float
    entry_date: datetime
    cost_value: float
    current_value: float
    unrealized_pnl: float
    pnl_percent: float
    frequency_band: FrequencyBand = FrequencyBand.NEUTRAL
    element: Element = Element.ETHER
    risk_level: RiskLevel = RiskLevel.LOW
    frequency_hz: int = 432


@dataclass 
class UIValidatedSignal:
    """Validated trading signal from UI data"""
    symbol: str
    exchange: str
    action: str  # BUY/SELL/HOLD
    confidence: float
    reason: str
    
    # UI validation data
    frequency_aligned: bool
    coherence_pass: bool
    fear_greed_ok: bool
    risk_acceptable: bool
    
    # Harmonic data
    frequency_hz: float
    frequency_band: str
    element: str
    
    # Market metrics
    fear_greed_value: int
    arbitrage_opportunity: bool
    
    timestamp: datetime = field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════════
# UI DATA VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════════

class AureonUIValidator:
    """
    Validates trading decisions against live UI data from aureoninstitute.com
    
    The UI displays real-time harmonic analysis, Fear/Greed index, and position
    data that should be cross-referenced before executing trades.
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.config = AUREON_UI_CONFIG
        
        # Cached data
        self.harmonic_reading: Optional[HarmonicReading] = None
        self.fear_greed: Optional[FearGreedIndex] = None
        self.sniper_kills: List[SniperKill] = []
        self.positions: Dict[str, PositionStatus] = {}
        self.arbitrage_opps: List[ArbitrageOpportunity] = []
        
        # Last update timestamps
        self.last_harmonic_update: Optional[datetime] = None
        self.last_position_update: Optional[datetime] = None
        self.last_fear_greed_update: Optional[datetime] = None
        
        logger.info("🌐 Aureon UI Validator initialized")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    # ─────────────────────────────────────────────────────────────────────────
    # API CALLS
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _fetch_supabase(self, endpoint: str, payload: Dict = None) -> Optional[Dict]:
        """Fetch data from Supabase edge function"""
        if not self.config['SUPABASE_URL']:
            logger.warning("⚠️ SUPABASE_URL not configured")
            return None
        
        url = f"{self.config['SUPABASE_URL']}{endpoint}"
        headers = {
            'apikey': self.config['SUPABASE_KEY'],
            'Authorization': f"Bearer {self.config['SUPABASE_KEY']}",
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.post(url, json=payload or {}, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.warning(f"⚠️ API {endpoint} returned {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ API error {endpoint}: {e}")
            return None
    
    async def fetch_harmonic_field(self) -> Optional[HarmonicReading]:
        """Fetch current harmonic field analysis from UI/API"""
        data = await self._fetch_supabase(self.config['PULL_ENDPOINTS']['harmonic_nexus'])
        
        if not data:
            # Return cached if available
            return self.harmonic_reading
        
        try:
            # Parse harmonic data
            freq = data.get('dominant_frequency', 432)
            band = self._freq_to_band(freq)
            
            reading = HarmonicReading(
                frequency=freq,
                band=band,
                element=Element(data.get('dominant_element', 'ETHER').upper()),
                coherence=data.get('global_coherence', 0.5),
                schumann_sync=data.get('schumann_alignment', 0),
                phi_harmony=data.get('phi_harmony', 0),
                optimal_entry_score=data.get('entry_score', 50),
                signal_confidence=data.get('signal_confidence', 0.5),
                recommended_action=data.get('action', 'HOLD'),
                timestamp=datetime.now()
            )
            
            self.harmonic_reading = reading
            self.last_harmonic_update = datetime.now()
            
            logger.info(f"🎵 Harmonic Field: {freq}Hz ({band.value}) Γ={reading.coherence:.2f}")
            return reading
            
        except Exception as e:
            logger.error(f"❌ Error parsing harmonic data: {e}")
            return self.harmonic_reading
    
    async def fetch_positions_pnl(self) -> Dict[str, PositionStatus]:
        """Fetch current positions with P&L from UI/API"""
        data = await self._fetch_supabase(self.config['PULL_ENDPOINTS']['positions_pnl'])
        
        if not data or 'positions' not in data:
            return self.positions
        
        try:
            positions = {}
            for pos in data['positions']:
                symbol = pos.get('symbol', '')
                exchange = pos.get('exchange', '')
                key = f"{exchange}:{symbol}"
                
                positions[key] = PositionStatus(
                    symbol=symbol,
                    exchange=exchange,
                    quantity=pos.get('quantity', 0),
                    cost_basis=pos.get('cost_basis', 0),
                    current_price=pos.get('current_price', 0),
                    entry_date=datetime.fromisoformat(pos.get('entry_date', datetime.now().isoformat())),
                    cost_value=pos.get('cost_value', 0),
                    current_value=pos.get('current_value', 0),
                    unrealized_pnl=pos.get('unrealized_pnl', 0),
                    pnl_percent=pos.get('pnl_percent', 0),
                    frequency_band=self._freq_to_band(pos.get('frequency_hz', 432)),
                    element=Element(pos.get('element', 'ETHER').upper()),
                    risk_level=RiskLevel(pos.get('risk_level', 'LOW').upper()),
                    frequency_hz=pos.get('frequency_hz', 432)
                )
            
            self.positions = positions
            self.last_position_update = datetime.now()
            
            logger.info(f"📊 Updated {len(positions)} positions from UI")
            return positions
            
        except Exception as e:
            logger.error(f"❌ Error parsing positions: {e}")
            return self.positions
    
    async def fetch_coherence_forecast(self) -> Dict[str, Any]:
        """Fetch coherence forecast for optimal trading windows"""
        data = await self._fetch_supabase(self.config['PULL_ENDPOINTS']['coherence_forecast'])
        return data or {}
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🪞 PUSH METHODS - Send YOUR terminal state to UI (you enrich everyone)
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _push_supabase(self, endpoint: str, payload: Dict) -> bool:
        """Push data TO Supabase edge function"""
        if not self.config['SUPABASE_URL']:
            logger.debug("SUPABASE_URL not configured - skip push")
            return False
        
        url = f"{self.config['SUPABASE_URL']}{endpoint}"
        headers = {
            'apikey': self.config['SUPABASE_KEY'],
            'Authorization': f"Bearer {self.config['SUPABASE_KEY']}",
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    logger.debug(f"✅ Pushed to {endpoint}")
                    return True
                else:
                    logger.warning(f"⚠️ Push to {endpoint} returned {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Push error {endpoint}: {e}")
            return False
    
    async def push_terminal_state(self, state: Dict[str, Any]) -> bool:
        """
        🪞 PUSH your terminal state to the UI.
        
        This data enriches the collective intelligence:
        - Your positions help global pattern detection
        - Your P&L contributes to leaderboard
        - Your Kill Scanner state improves predictions
        """
        payload = {
            'temporal_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'terminal_id': state.get('terminal_id', 'default'),
            'positions': state.get('positions', []),
            'cash_balance': state.get('cash_balance', 0),
            'total_equity': state.get('total_equity', 0),
            'active_signals': state.get('active_signals', []),
            'kill_scanner_targets': state.get('kill_scanner_targets', []),
            'patriot_scouts': state.get('patriot_scouts', []),
            'mycelium_state': state.get('mycelium_state', {}),
            'coherence': state.get('coherence', 0.5),
            'metadata': state.get('metadata', {})
        }
        
        return await self._push_supabase(
            self.config['PUSH_ENDPOINTS']['terminal_state'],
            payload
        )
    
    async def push_trade(self, trade: Dict[str, Any]) -> bool:
        """
        🪞 PUSH a trade to the UI.
        
        Your trades update:
        - Sniper leaderboard (kills, accuracy)
        - Global P&L statistics
        - Pattern correlations
        """
        payload = {
            'temporal_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'symbol': trade.get('symbol'),
            'exchange': trade.get('exchange'),
            'side': trade.get('side'),
            'quantity': trade.get('quantity', 0),
            'price': trade.get('price', 0),
            'value_usd': trade.get('value_usd', 0),
            'pnl': trade.get('pnl', 0),
            'is_kill': trade.get('is_kill', False),
            'kill_eta_accuracy': trade.get('kill_eta_accuracy', None),
            'sniper_name': trade.get('sniper_name', 'Unknown'),
            'province': trade.get('province', 'Ulster'),
            'metadata': trade.get('metadata', {})
        }
        
        return await self._push_supabase(
            self.config['PUSH_ENDPOINTS']['trades'],
            payload
        )
    
    async def push_ecosystem_snapshot(self, ecosystem: Dict[str, Any]) -> bool:
        """
        🪞 PUSH ecosystem snapshot to UI.
        
        Includes state from all systems:
        - Auris nodes
        - Mycelium network
        - Brain/cognitive state
        - Kill Scanner targets
        - Performance metrics
        """
        payload = {
            'temporal_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'systems_online': ecosystem.get('systems_online', 0),
            'total_systems': ecosystem.get('total_systems', 25),
            'hive_mind_coherence': ecosystem.get('coherence', 0),
            'bus_consensus': ecosystem.get('consensus', 'HOLD'),
            'bus_confidence': ecosystem.get('confidence', 0),
            'system_states': ecosystem.get('system_states', {}),
            'kill_scanner': ecosystem.get('kill_scanner', {}),
            'patriots': ecosystem.get('patriots', {}),
            'mycelium': ecosystem.get('mycelium', {}),
            'metadata': ecosystem.get('metadata', {})
        }
        
        return await self._push_supabase(
            self.config['PUSH_ENDPOINTS']['ecosystem_snapshot'],
            payload
        )
    
    async def push_kill_event(self, kill: Dict[str, Any]) -> bool:
        """
        🪞 PUSH a kill event to update leaderboard.
        
        Your kills update the Sniper Leaderboard that everyone sees.
        """
        payload = {
            'temporal_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'symbol': kill.get('symbol'),
            'exchange': kill.get('exchange'),
            'pnl': kill.get('pnl', 0),
            'hold_time_seconds': kill.get('hold_time', 0),
            'eta_prediction': kill.get('eta_prediction', None),
            'eta_actual': kill.get('eta_actual', None),
            'probability_at_kill': kill.get('probability', 0),
            'sniper_name': kill.get('sniper_name', 'Unknown'),
            'province': kill.get('province', 'Ulster'),
            'velocity_at_kill': kill.get('velocity', 0),
        }
        
        # This updates sniper leaderboard
        return await self._push_supabase(
            self.config['PUSH_ENDPOINTS']['calibration'],
            payload
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # VALIDATION METHODS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _freq_to_band(self, freq: float) -> FrequencyBand:
        """Convert frequency Hz to band"""
        if freq >= 520 and freq <= 536:
            return FrequencyBand.LOVE
        elif freq >= 426 and freq <= 438:
            return FrequencyBand.HARMONY
        elif freq >= 390 and freq <= 402:
            return FrequencyBand.LIBERATION
        elif freq >= 411 and freq <= 423:
            return FrequencyBand.TRANSFORMATION
        elif freq >= 436 and freq <= 444:
            return FrequencyBand.DISTORTION
        return FrequencyBand.NEUTRAL
    
    def validate_frequency_alignment(self, symbol: str, target_band: FrequencyBand = FrequencyBand.HARMONY) -> bool:
        """
        Check if asset's frequency is aligned for trading.
        
        HARMONY (432 Hz) is optimal for trading.
        DISTORTION (440 Hz) suggests waiting.
        """
        pos_key = None
        for key, pos in self.positions.items():
            if symbol in key:
                pos_key = key
                break
        
        if not pos_key:
            # No position data, assume aligned
            return True
        
        pos = self.positions[pos_key]
        
        # Check if in distortion
        if pos.frequency_band == FrequencyBand.DISTORTION:
            logger.warning(f"⚠️ {symbol} in DISTORTION zone ({pos.frequency_hz}Hz) - wait for clarity")
            return False
        
        # Optimal bands for trading
        optimal_bands = [FrequencyBand.HARMONY, FrequencyBand.LOVE, FrequencyBand.LIBERATION]
        return pos.frequency_band in optimal_bands
    
    def validate_coherence(self, min_coherence: float = None) -> bool:
        """
        Validate global coherence meets threshold.
        
        Coherence (Γ) represents market harmony:
        - Γ > 0.70: Excellent trading conditions
        - Γ 0.40-0.70: Forming, proceed with caution
        - Γ < 0.40: Chaotic, avoid trading
        """
        if not self.harmonic_reading:
            return True  # No data, assume OK
        
        threshold = min_coherence or self.config['COHERENCE_MIN']
        
        if self.harmonic_reading.coherence < threshold:
            logger.warning(f"⚠️ Coherence Γ={self.harmonic_reading.coherence:.2f} below threshold {threshold}")
            return False
        
        return True
    
    def validate_fear_greed(self) -> Tuple[bool, str]:
        """
        Validate Fear & Greed is not at extremes.
        
        Extreme Fear (<25): Good buying opportunity
        Extreme Greed (>75): Caution on new buys
        """
        if not self.fear_greed:
            return True, "No F&G data"
        
        fg = self.fear_greed.value
        
        if fg <= self.config['FEAR_GREED_EXTREME_FEAR']:
            return True, f"😟 Extreme Fear ({fg}) - buying opportunity"
        elif fg >= self.config['FEAR_GREED_EXTREME_GREED']:
            return False, f"🤑 Extreme Greed ({fg}) - caution on buys"
        
        return True, f"Fear & Greed: {fg} ({self.fear_greed.label})"
    
    def validate_risk_level(self, symbol: str, max_risk: RiskLevel = RiskLevel.MEDIUM) -> bool:
        """Check if position's risk level is acceptable"""
        for key, pos in self.positions.items():
            if symbol in key:
                risk_order = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3}
                return risk_order[pos.risk_level] <= risk_order[max_risk]
        
        return True  # No position data, assume OK
    
    async def validate_trade(
        self,
        symbol: str,
        exchange: str,
        action: str,
        confidence: float = 0.5
    ) -> UIValidatedSignal:
        """
        Full validation of a trade against UI data.
        
        Cross-references:
        - Harmonic frequency alignment
        - Global coherence
        - Fear & Greed index
        - Position risk level
        - Arbitrage opportunities
        """
        # Refresh data if stale
        if not self.last_harmonic_update or \
           (datetime.now() - self.last_harmonic_update).seconds > self.config['HARMONIC_REFRESH']:
            await self.fetch_harmonic_field()
        
        if not self.last_position_update or \
           (datetime.now() - self.last_position_update).seconds > self.config['POSITIONS_REFRESH']:
            await self.fetch_positions_pnl()
        
        # Run validations
        freq_aligned = self.validate_frequency_alignment(symbol)
        coherence_pass = self.validate_coherence()
        fg_ok, fg_reason = self.validate_fear_greed()
        risk_ok = self.validate_risk_level(symbol)
        
        # Check for arbitrage opportunity
        arb_opp = any(a.symbol == symbol for a in self.arbitrage_opps)
        
        # Determine if trade is validated
        all_pass = freq_aligned and coherence_pass and risk_ok
        
        # Adjust for Fear/Greed (buying opportunity in extreme fear)
        if action == 'BUY' and not fg_ok:
            all_pass = False  # Block buys in extreme greed
        
        # Build reason string
        reasons = []
        if not freq_aligned:
            reasons.append("❌ Frequency misaligned")
        if not coherence_pass:
            reasons.append("❌ Low coherence")
        if not fg_ok:
            reasons.append(f"❌ {fg_reason}")
        if not risk_ok:
            reasons.append("❌ High risk level")
        
        if all_pass:
            reasons = ["✅ All validations passed"]
        
        # Get harmonic data
        freq_hz = 432
        freq_band = 'HARMONY'
        element = 'ETHER'
        
        if self.harmonic_reading:
            freq_hz = self.harmonic_reading.frequency
            freq_band = self.harmonic_reading.band.value
            element = self.harmonic_reading.element.value
        
        return UIValidatedSignal(
            symbol=symbol,
            exchange=exchange,
            action=action if all_pass else 'HOLD',
            confidence=confidence if all_pass else confidence * 0.5,
            reason=' | '.join(reasons),
            frequency_aligned=freq_aligned,
            coherence_pass=coherence_pass,
            fear_greed_ok=fg_ok,
            risk_acceptable=risk_ok,
            frequency_hz=freq_hz,
            frequency_band=freq_band,
            element=element,
            fear_greed_value=self.fear_greed.value if self.fear_greed else 50,
            arbitrage_opportunity=arb_opp,
            timestamp=datetime.now()
        )


# ═══════════════════════════════════════════════════════════════════════════════
# UI DATA BRIDGE (Connect to Trading System)
# ═══════════════════════════════════════════════════════════════════════════════

class AureonUIBridge:
    """
    Bridges UI data from aureoninstitute.com to the trading system.
    
    Provides:
    - Real-time harmonic field integration
    - Fear/Greed sentiment overlay
    - Position sync with UI display
    - Sniper leaderboard stats
    """
    
    def __init__(self, validator: AureonUIValidator = None):
        self.validator = validator or AureonUIValidator()
        self.connected = False
        
        # Injected signals queue
        self.signal_queue: List[UIValidatedSignal] = []
        
        # Statistics
        self.stats = {
            'trades_validated': 0,
            'trades_blocked': 0,
            'signals_injected': 0,
            'coherence_checks': 0,
            'frequency_alerts': 0,
        }
        
        logger.info("🌉 Aureon UI Bridge initialized")
    
    async def connect(self):
        """Establish connection to UI data sources"""
        await self.validator.__aenter__()
        self.connected = True
        
        # Initial data fetch
        await self.validator.fetch_harmonic_field()
        await self.validator.fetch_positions_pnl()
        
        logger.info("🌐 Connected to Aureon Institute UI")
    
    async def disconnect(self):
        """Clean up connections"""
        await self.validator.__aexit__(None, None, None)
        self.connected = False
        logger.info("🔌 Disconnected from UI")
    
    async def validate_and_enhance_signal(
        self,
        symbol: str,
        exchange: str,
        action: str,
        confidence: float,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        Validate a trading signal against UI data and enhance with harmonic info.
        
        Returns enhanced signal with UI validation data.
        """
        validated = await self.validator.validate_trade(symbol, exchange, action, confidence)
        
        self.stats['trades_validated'] += 1
        if validated.action == 'HOLD' and action != 'HOLD':
            self.stats['trades_blocked'] += 1
        
        # Build enhanced signal
        enhanced = {
            'symbol': symbol,
            'exchange': exchange,
            'original_action': action,
            'validated_action': validated.action,
            'original_confidence': confidence,
            'validated_confidence': validated.confidence,
            'ui_validation': {
                'frequency_aligned': validated.frequency_aligned,
                'coherence_pass': validated.coherence_pass,
                'fear_greed_ok': validated.fear_greed_ok,
                'risk_acceptable': validated.risk_acceptable,
                'reason': validated.reason,
            },
            'harmonic_data': {
                'frequency_hz': validated.frequency_hz,
                'frequency_band': validated.frequency_band,
                'element': validated.element,
            },
            'market_sentiment': {
                'fear_greed': validated.fear_greed_value,
                'arbitrage_available': validated.arbitrage_opportunity,
            },
            'timestamp': validated.timestamp.isoformat(),
        }
        
        return enhanced
    
    def get_harmonic_overlay(self) -> Dict[str, Any]:
        """Get current harmonic field data for display overlay"""
        if not self.validator.harmonic_reading:
            return {'status': 'no_data'}
        
        h = self.validator.harmonic_reading
        return {
            'status': 'active',
            'frequency_hz': h.frequency,
            'frequency_band': h.band.value,
            'element': h.element.value,
            'coherence_gamma': h.coherence,
            'schumann_sync': h.schumann_sync,
            'phi_harmony': h.phi_harmony,
            'entry_score': h.optimal_entry_score,
            'signal_confidence': h.signal_confidence,
            'action': h.recommended_action,
            'updated': h.timestamp.isoformat(),
        }
    
    def get_fear_greed_overlay(self) -> Dict[str, Any]:
        """Get current Fear & Greed data for display overlay"""
        if not self.validator.fear_greed:
            return {'status': 'no_data'}
        
        fg = self.validator.fear_greed
        return {
            'status': 'active',
            'value': fg.value,
            'label': fg.label,
            'temperature': fg.temperature,
            'bull_ratio': fg.bull_bear_ratio[0],
            'bear_ratio': fg.bull_bear_ratio[1],
            'momentum': fg.momentum,
            'momentum_direction': fg.momentum_direction,
        }
    
    def get_sniper_leaderboard(self) -> List[Dict[str, Any]]:
        """Get sniper leaderboard data"""
        return [asdict(kill) for kill in self.validator.sniper_kills]
    
    def inject_ui_signal(self, signal: UIValidatedSignal):
        """Inject a UI-derived signal into the trading system"""
        self.signal_queue.append(signal)
        self.stats['signals_injected'] += 1
        logger.info(f"💉 Injected UI signal: {signal.action} {signal.symbol} @ {signal.confidence:.2%}")
    
    def pop_signals(self) -> List[UIValidatedSignal]:
        """Pop all queued signals for processing"""
        signals = self.signal_queue.copy()
        self.signal_queue.clear()
        return signals
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics"""
        return {
            **self.stats,
            'connected': self.connected,
            'harmonic_fresh': self.validator.last_harmonic_update is not None and \
                             (datetime.now() - self.validator.last_harmonic_update).seconds < 120,
            'positions_fresh': self.validator.last_position_update is not None and \
                              (datetime.now() - self.validator.last_position_update).seconds < 60,
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🪞 BIDIRECTIONAL SYNC - The Two Mirrors
    # ─────────────────────────────────────────────────────────────────────────
    
    async def mirror_sync(self, local_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        🪞 BIDIRECTIONAL MIRROR SYNC 🪞
        
        This is the heart of the two-mirror system:
        1. PUSH your terminal state to enrich the UI
        2. PULL aggregated data back (including insights from other users)
        
        Args:
            local_state: Your terminal's current state
            
        Returns:
            Aggregated insights from the UI (what you couldn't see alone)
        """
        sync_result = {
            'pushed': False,
            'pulled': False,
            'push_success': [],
            'pull_data': {},
            'insights': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 1: PUSH your state (your data enriches everyone)
        # ═══════════════════════════════════════════════════════════════════
        try:
            # Push terminal state
            if await self.validator.push_terminal_state(local_state):
                sync_result['push_success'].append('terminal_state')
            
            # Push ecosystem snapshot if provided
            if 'ecosystem' in local_state:
                if await self.validator.push_ecosystem_snapshot(local_state['ecosystem']):
                    sync_result['push_success'].append('ecosystem')
            
            sync_result['pushed'] = len(sync_result['push_success']) > 0
            self.stats['pushes'] = self.stats.get('pushes', 0) + 1
            
        except Exception as e:
            logger.warning(f"⚠️ Push failed: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 2: PULL aggregated data (insights you couldn't see alone)
        # ═══════════════════════════════════════════════════════════════════
        try:
            # Pull harmonic field (global coherence from all users)
            harmonic = await self.validator.fetch_harmonic_field()
            if harmonic:
                sync_result['pull_data']['harmonic'] = {
                    'frequency_hz': harmonic.frequency,
                    'band': harmonic.band.value,
                    'coherence': harmonic.coherence,
                    'entry_score': harmonic.optimal_entry_score,
                }
            
            # Pull positions P&L (aggregated view)
            positions = await self.validator.fetch_positions_pnl()
            if positions:
                sync_result['pull_data']['positions_count'] = len(positions)
            
            # Pull coherence forecast (AI predictions)
            forecast = await self.validator.fetch_coherence_forecast()
            if forecast:
                sync_result['pull_data']['forecast'] = forecast
            
            sync_result['pulled'] = bool(sync_result['pull_data'])
            self.stats['pulls'] = self.stats.get('pulls', 0) + 1
            
        except Exception as e:
            logger.warning(f"⚠️ Pull failed: {e}")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 3: Generate INSIGHTS (what you learned from the collective)
        # ═══════════════════════════════════════════════════════════════════
        if sync_result['pulled']:
            harmonic_data = sync_result['pull_data'].get('harmonic', {})
            
            # Insight: Is global coherence better than your local view?
            local_coherence = local_state.get('coherence', 0.5)
            global_coherence = harmonic_data.get('coherence', 0.5)
            
            sync_result['insights']['coherence_delta'] = global_coherence - local_coherence
            sync_result['insights']['global_is_stronger'] = global_coherence > local_coherence
            
            # Insight: Entry conditions
            entry_score = harmonic_data.get('entry_score', 50)
            sync_result['insights']['entry_optimal'] = entry_score >= 70
            sync_result['insights']['entry_score'] = entry_score
            
            # Insight: Frequency alignment
            freq_band = harmonic_data.get('band', 'NEUTRAL')
            sync_result['insights']['market_in_harmony'] = freq_band in ['HARMONY', 'LOVE']
            sync_result['insights']['market_distorted'] = freq_band == 'DISTORTION'
        
        logger.info(f"🪞 Mirror sync: PUSH={sync_result['pushed']} PULL={sync_result['pulled']}")
        return sync_result
    
    async def push_trade_result(self, trade: Dict[str, Any]) -> bool:
        """Push a trade result to update the collective leaderboard"""
        return await self.validator.push_trade(trade)
    
    async def push_kill_to_leaderboard(self, kill: Dict[str, Any]) -> bool:
        """Push a successful kill to update the sniper leaderboard"""
        return await self.validator.push_kill_event(kill)


# ═══════════════════════════════════════════════════════════════════════════════
# MYCELIUM INTEGRATION - Connect to existing systems
# ═══════════════════════════════════════════════════════════════════════════════

class UIMyceliumConnector:
    """
    Connects UI Bridge to Mycelium State Aggregator.
    
    Allows UI-validated signals to flow through the mycelium network
    and coordinate with Kill Scanner and Irish Patriots.
    """
    
    def __init__(self, ui_bridge: AureonUIBridge = None):
        self.bridge = ui_bridge or AureonUIBridge()
        self.mycelium = None  # Will be set by ecosystem
        
    def set_mycelium(self, mycelium):
        """Connect to Mycelium State Aggregator"""
        self.mycelium = mycelium
        logger.info("🍄 UI Bridge connected to Mycelium Network")
    
    async def broadcast_harmonic_state(self):
        """Broadcast current harmonic state to mycelium"""
        if not self.mycelium:
            return
        
        harmonic = self.bridge.get_harmonic_overlay()
        
        if harmonic.get('status') == 'active':
            # Create harmonic intelligence for mycelium
            intelligence = {
                'source': 'ui_bridge',
                'type': 'harmonic_field',
                'data': harmonic,
                'timestamp': datetime.now().isoformat(),
            }
            
            # If mycelium has broadcast method, use it
            if hasattr(self.mycelium, 'inject_intelligence'):
                self.mycelium.inject_intelligence(intelligence)
    
    async def get_unified_validation(
        self,
        symbol: str,
        exchange: str,
        action: str,
        confidence: float
    ) -> Dict[str, Any]:
        """
        Get validation from both UI and Mycelium systems.
        
        Combines:
        - UI harmonic/coherence validation
        - Mycelium consensus
        - Kill Scanner status
        - Patriot scout intel
        """
        # Get UI validation
        ui_validated = await self.bridge.validate_and_enhance_signal(
            symbol, exchange, action, confidence
        )
        
        # Get mycelium consensus if available
        mycelium_consensus = None
        if self.mycelium and hasattr(self.mycelium, 'get_consensus'):
            mycelium_consensus = self.mycelium.get_consensus(f"{exchange}:{symbol}")
        
        return {
            'ui_validation': ui_validated,
            'mycelium_consensus': mycelium_consensus,
            'unified_action': ui_validated['validated_action'],
            'unified_confidence': ui_validated['validated_confidence'],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global bridge instance
_ui_bridge: Optional[AureonUIBridge] = None
_ui_connector: Optional[UIMyceliumConnector] = None


def get_ui_bridge() -> AureonUIBridge:
    """Get or create global UI Bridge instance"""
    global _ui_bridge
    if _ui_bridge is None:
        _ui_bridge = AureonUIBridge()
    return _ui_bridge


def get_ui_connector() -> UIMyceliumConnector:
    """Get or create global UI Mycelium Connector"""
    global _ui_connector
    if _ui_connector is None:
        _ui_connector = UIMyceliumConnector(get_ui_bridge())
    return _ui_connector


async def validate_trade_against_ui(
    symbol: str,
    exchange: str,
    action: str,
    confidence: float = 0.7
) -> Dict[str, Any]:
    """
    Quick validation of a trade against UI data.
    
    Usage:
        result = await validate_trade_against_ui('BTCUSD', 'kraken', 'BUY', 0.8)
        if result['validated_action'] == 'BUY':
            # Proceed with trade
    """
    bridge = get_ui_bridge()
    
    if not bridge.connected:
        async with bridge.validator:
            return await bridge.validate_and_enhance_signal(
                symbol, exchange, action, confidence
            )
    
    return await bridge.validate_and_enhance_signal(
        symbol, exchange, action, confidence
    )


async def get_harmonic_field_status() -> Dict[str, Any]:
    """Get current harmonic field status from UI"""
    bridge = get_ui_bridge()
    return bridge.get_harmonic_overlay()


async def get_fear_greed_status() -> Dict[str, Any]:
    """Get current Fear & Greed status from UI"""
    bridge = get_ui_bridge()
    return bridge.get_fear_greed_overlay()


async def mirror_sync_terminal(local_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    🪞 BIDIRECTIONAL MIRROR SYNC - Main Entry Point 🪞
    
    Call this periodically from your trading loop to:
    1. PUSH your terminal state (enriches collective intelligence)
    2. PULL aggregated insights (what others see that you don't)
    
    Args:
        local_state: Your current terminal state with:
            - positions: List of position dicts
            - cash_balance: Current cash
            - total_equity: Total portfolio value
            - coherence: Your local coherence calculation
            - kill_scanner_targets: Active targets
            - ecosystem: Full ecosystem snapshot (optional)
    
    Returns:
        Dict with:
            - pushed: Whether push succeeded
            - pulled: Whether pull succeeded
            - insights: What you learned from the collective
    
    Usage:
        # In your trading loop
        local_state = {
            'positions': [{'symbol': 'BTCUSD', 'pnl': 5.50}],
            'cash_balance': 100.0,
            'coherence': 0.65,
            'kill_scanner_targets': ['kraken:BTCUSD'],
        }
        insights = await mirror_sync_terminal(local_state)
        
        if insights['insights'].get('market_distorted'):
            print("⚠️ Global market in distortion - wait for clarity")
    """
    bridge = get_ui_bridge()
    
    if not bridge.connected:
        async with bridge.validator:
            return await bridge.mirror_sync(local_state)
    
    return await bridge.mirror_sync(local_state)


async def push_kill_to_leaderboard(
    symbol: str,
    exchange: str,
    pnl: float,
    hold_time: float,
    sniper_name: str = "The Silent",
    province: str = "Ulster"
) -> bool:
    """
    🎯 Push a successful kill to update the global sniper leaderboard.
    
    Your kills contribute to the collective stats that everyone sees.
    """
    bridge = get_ui_bridge()
    
    kill = {
        'symbol': symbol,
        'exchange': exchange,
        'pnl': pnl,
        'hold_time': hold_time,
        'sniper_name': sniper_name,
        'province': province,
        'probability': 1.0,  # It happened!
        'velocity': pnl / max(hold_time, 1),
    }
    
    return await bridge.push_kill_to_leaderboard(kill)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN / TEST
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Test UI Bridge functionality"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🌐 AUREON UI BRIDGE - Test Suite                           ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    bridge = AureonUIBridge()
    
    async with bridge.validator:
        # Test 1: Fetch harmonic field
        print("\n📡 Test 1: Fetching Harmonic Field...")
        harmonic = await bridge.validator.fetch_harmonic_field()
        if harmonic:
            print(f"   Frequency: {harmonic.frequency} Hz ({harmonic.band.value})")
            print(f"   Element: {harmonic.element.value}")
            print(f"   Coherence Γ: {harmonic.coherence:.2f}")
            print(f"   Entry Score: {harmonic.optimal_entry_score}")
        else:
            print("   ⚠️ No harmonic data (API not configured)")
        
        # Test 2: Fetch positions
        print("\n📊 Test 2: Fetching Positions...")
        positions = await bridge.validator.fetch_positions_pnl()
        print(f"   Loaded {len(positions)} positions")
        for key, pos in list(positions.items())[:3]:
            print(f"   • {pos.symbol} ({pos.exchange}): ${pos.current_value:.2f} [{pos.frequency_band.value}]")
        
        # Test 3: Validate a trade
        print("\n✅ Test 3: Trade Validation...")
        test_trades = [
            ('BTCUSD', 'kraken', 'BUY', 0.75),
            ('ETHUSD', 'binance', 'SELL', 0.60),
            ('XRPUSDC', 'kraken', 'BUY', 0.80),
        ]
        
        for symbol, exchange, action, conf in test_trades:
            result = await bridge.validate_and_enhance_signal(symbol, exchange, action, conf)
            status = "✅" if result['validated_action'] == action else "🚫"
            print(f"   {status} {action} {symbol} @ {conf:.0%} → {result['validated_action']} @ {result['validated_confidence']:.0%}")
            print(f"      Reason: {result['ui_validation']['reason']}")
        
        # Test 4: Get overlays
        print("\n🎨 Test 4: Overlays...")
        harmonic_overlay = bridge.get_harmonic_overlay()
        fg_overlay = bridge.get_fear_greed_overlay()
        print(f"   Harmonic: {harmonic_overlay.get('status', 'N/A')}")
        print(f"   Fear/Greed: {fg_overlay.get('status', 'N/A')}")
        
        # Stats
        print("\n📈 Bridge Stats:")
        stats = bridge.get_stats()
        for key, value in stats.items():
            print(f"   • {key}: {value}")
    
    print("\n✅ UI Bridge test complete!")


if __name__ == "__main__":
    asyncio.run(main())
