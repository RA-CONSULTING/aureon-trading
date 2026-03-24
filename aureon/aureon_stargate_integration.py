"""
Stargate / Quantum Mirror Integration

Maps planetary node resonance to market symbols using harmonic frequency alignment.

Architecture:
- Planetary nodes (Giza, Stonehenge, etc.) have resonance frequencies
- Market symbols have price-derived frequency signatures  
- High resonance coupling → bullish signal
- Low coupling / drift → bearish signal
- Publishes `whale.stargate.correlated` with coherence for predictor

Frequency Mapping:
- Giza (432 Hz) → Gold, BTC/USD (stability, foundation)
- Stonehenge (396 Hz) → GBP pairs (liberation, UK heritage)
- Machu Picchu (528 Hz) → Precious metals, healing sector (love frequency)
- Sedona (741 Hz) → Tech stocks, innovation (intuition)
- Mt Shasta (963 Hz) → Crypto, unity consciousness
"""
from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import sys
import os

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

import logging
import time
import math
from typing import Any, Dict, Optional, List, Tuple
from collections import defaultdict

from aureon_thought_bus import get_thought_bus, Thought

logger = logging.getLogger(__name__)

# Try to import stargate protocol
try:
    from aureon_stargate_protocol import PLANETARY_STARGATES, StargateNode, PHI
    STARGATE_AVAILABLE = True
except ImportError:
    STARGATE_AVAILABLE = False
    PHI = 1.618033988749895
    logger.warning("aureon_stargate_protocol not available; using fallback mode")


# ═══════════════════════════════════════════════════════════════
# 🗺️ PLANETARY NODE → SYMBOL MAPPINGS (HARMONIC CORRELATION)
# ═══════════════════════════════════════════════════════════════

# Map stargate nodes to asset classes based on resonance frequency
STARGATE_SYMBOL_MAP = {
    # Giza (432 Hz) - Foundation, stability, ancient wealth
    "giza": ["BTC/USD", "GC=F", "GOLD", "XAU/USD", "BTC", "PAXG"],
    
    # Stonehenge (396 Hz) - Liberation, UK heritage
    "stonehenge": ["GBP/USD", "GBPUSD", "GBP", "BP", "HSBC", "LLOY.L"],
    
    # Uluru (174 Hz) - Foundation, earth energy
    "uluru": ["AUD/USD", "AUDUSD", "AUD", "BHP", "RIO", "FMG.AX"],
    
    # Machu Picchu (528 Hz) - Love/Transformation, precious metals
    "machu_picchu": ["SILVER", "SI=F", "XAG/USD", "AG", "SLV", "PAAS", "PSLV"],
    
    # Angkor Wat (639 Hz) - Connection, Asian markets
    "angkor_wat": ["VND/USD", "VNINDEX", "VNM", "ASIA", "EWS", "ASHR"],
    
    # Glastonbury (852 Hz) - Spiritual Order, healing sector
    "glastonbury": ["JNJ", "PFE", "MRNA", "ABBV", "UNH", "GILD", "XLV"],
    
    # Sedona (741 Hz) - Intuition, tech/innovation
    "sedona": ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA", "META", "QQQ"],
    
    # Teotihuacan (417 Hz) - Undoing, emerging markets
    "teotihuacan": ["EEM", "VWO", "IEMG", "MXN/USD", "MXNUSD"],
    
    # Mt Shasta (963 Hz) - Unity, cosmic consciousness, crypto
    "mt_shasta": ["ETH/USD", "ETH", "SOL/USD", "AVAX/USD", "MATIC/USD", "ADA/USD"],
    
    # Newgrange (285 Hz) - Healing, regeneration
    "newgrange": ["REGN", "VRTX", "EDIT", "CRSP", "NTLA", "BEAM"],
    
    # Göbekli Tepe (126.7 Hz) - Ancient wisdom, precious resources
    "gobekli_tepe": ["TRY/USD", "COPPER", "HG=F", "FCX", "SCCO"],
    
    # Baalbek (432 Hz) - Ancient power, Middle East energy
    "baalbek": ["XLE", "USO", "CL=F", "OIL", "CRUDE", "BRN=F"],
}

# Reverse map: symbol → list of stargate nodes
SYMBOL_TO_STARGATES: Dict[str, List[str]] = defaultdict(list)
for node_id, symbols in STARGATE_SYMBOL_MAP.items():
    for symbol in symbols:
        SYMBOL_TO_STARGATES[symbol.upper()].append(node_id)


class StargateIntegration:
    def __init__(self):
        self.thought_bus = get_thought_bus()
        self._stargate_coherence: Dict[str, float] = {}  # node_id -> coherence
        self._quantum_mirrors: Dict[str, float] = {}     # mirror_id -> coherence
        
        # Subscribe to stargate and quantum events
        try:
            self.thought_bus.subscribe('stargate.*', self._on_stargate)
            logger.info("✅ Subscribed to stargate.*")
        except Exception as e:
            logger.debug(f'StargateIntegration: failed to subscribe to stargate.*: {e}')
        
        try:
            self.thought_bus.subscribe('quantum.mirror.*', self._on_quantum)
            logger.info("✅ Subscribed to quantum.mirror.*")
        except Exception as e:
            logger.debug(f'StargateIntegration: failed to subscribe to quantum.mirror.*: {e}')
        
        # Subscribe to market snapshots to emit correlations
        try:
            self.thought_bus.subscribe('market.snapshot', self._on_market_snapshot)
            logger.info("✅ Subscribed to market.snapshot for correlation emissions")
        except Exception as e:
            logger.debug(f'StargateIntegration: failed to subscribe to market.snapshot: {e}')

    def _normalize_symbol(self, raw: str) -> str:
        """Normalize symbol to match mapping keys"""
        s = raw.upper().replace('-', '/').replace('_', '/')
        # Handle common variations
        if s.endswith('USD') and '/' not in s:
            base = s[:-3]
            s = f"{base}/USD"
        return s

    def _get_stargate_nodes_for_symbol(self, symbol: str) -> List[Tuple[str, StargateNode]]:
        """Get all stargate nodes associated with a symbol"""
        if not STARGATE_AVAILABLE:
            return []
        
        norm_symbol = self._normalize_symbol(symbol)
        node_ids = SYMBOL_TO_STARGATES.get(norm_symbol, [])
        
        nodes = []
        for node_id in node_ids:
            if node_id in PLANETARY_STARGATES:
                nodes.append((node_id, PLANETARY_STARGATES[node_id]))
        
        return nodes

    def _compute_resonance_score(self, symbol: str, market_frequency: Optional[float] = None) -> Tuple[float, List[str]]:
        """
        Compute resonance score between symbol and its stargate nodes.
        
        Returns:
            (score, active_nodes) where score is 0-1 coherence
        """
        nodes = self._get_stargate_nodes_for_symbol(symbol)
        if not nodes:
            return (0.0, [])
        
        total_score = 0.0
        active_nodes = []
        
        for node_id, node in nodes:
            # Get node coherence from stargate events (if any)
            node_coherence = self._stargate_coherence.get(node_id, 0.5)
            
            # Frequency alignment (if market frequency known)
            freq_alignment = 1.0
            if market_frequency:
                # Frequency ratio (closer to 1.0 or PHI = better)
                freq_ratio = min(node.resonance_frequency, market_frequency) / max(node.resonance_frequency, market_frequency)
                phi_alignment = abs(freq_ratio - PHI) if freq_ratio > 1.0 else abs(1.0/freq_ratio - PHI)
                freq_alignment = max(freq_ratio, 1.0 / (1.0 + phi_alignment))
            
            # Casimir strength from node
            casimir = node.casimir_strength
            
            # Combined score
            node_score = node_coherence * freq_alignment * casimir
            total_score += node_score
            active_nodes.append(node_id)
        
        # Average and apply golden ratio
        avg_score = (total_score / len(nodes)) * PHI if nodes else 0.0
        return (min(avg_score, 1.0), active_nodes)

    def _on_stargate(self, thought: Thought) -> None:
        """Handle stargate activation events"""
        payload = thought.payload or {}
        
        # Extract node activation info
        node_id = payload.get('node_id') or payload.get('stargate_id')
        if node_id:
            coherence = float(payload.get('coherence', 0.5))
            self._stargate_coherence[node_id] = coherence
            logger.debug(f"🌌 Stargate {node_id} coherence: {coherence:.3f}")
            
            # Emit correlations for all symbols linked to this node
            if node_id in STARGATE_SYMBOL_MAP:
                for symbol in STARGATE_SYMBOL_MAP[node_id]:
                    self._emit_correlation(symbol, coherence, 'stargate', node_id)

    def _on_quantum(self, thought: Thought) -> None:
        """Handle quantum mirror events"""
        payload = thought.payload or {}
        
        # Extract mirror coherence
        mirror_id = payload.get('mirror_id') or payload.get('timeline_id')
        if mirror_id:
            coherence = float(payload.get('coherence_signature', 0.5) or payload.get('coherence', 0.5))
            self._quantum_mirrors[mirror_id] = coherence
            logger.debug(f"🪞 Quantum Mirror {mirror_id} coherence: {coherence:.3f}")
        
        # If quantum event mentions a symbol, correlate directly
        symbol = payload.get('symbol') or payload.get('asset')
        if symbol:
            coherence = float(payload.get('coherence', 0.5))
            self._emit_correlation(symbol, coherence, 'quantum_mirror', mirror_id or 'unknown')

    def _on_market_snapshot(self, thought: Thought) -> None:
        """
        When market data arrives, compute and emit stargate correlations.
        This happens passively - we don't block market data flow.
        """
        payload = thought.payload or {}
        symbol = payload.get('symbol')
        if not symbol:
            return
        
        # Extract market frequency if available (from harmonic analysis)
        market_freq = payload.get('dominant_frequency') or payload.get('frequency')
        
        # Compute resonance score
        score, active_nodes = self._compute_resonance_score(symbol, market_freq)
        
        if score > 0.3:  # Only emit if meaningful correlation
            self._emit_correlation(symbol, score, 'stargate_computed', ','.join(active_nodes))

    def _emit_correlation(self, symbol: str, coherence: float, source: str, node_info: str):
        """Emit correlation thought to whale.stargate.correlated"""
        payload = {
            'symbol': self._normalize_symbol(symbol),
            'source': source,
            'coherence': float(coherence),
            'node_info': node_info,
            'ts': time.time()
        }
        
        th = Thought(source='stargate_integration', topic='whale.stargate.correlated', payload=payload)
        try:
            self.thought_bus.publish(th)
            logger.debug(f"📡 Stargate correlation: {symbol} coherence={coherence:.3f} from {source}")
        except Exception as e:
            logger.debug(f'Failed to publish whale.stargate.correlated: {e}')


# Auto-start
_sg: Optional[StargateIntegration] = None
try:
    _sg = StargateIntegration()
    logger.info("✅ StargateIntegration initialized")
except Exception as e:
    logger.warning(f"⚠️  StargateIntegration failed to initialize: {e}")
    _sg = None


def get_stargate_integration() -> Optional[StargateIntegration]:
    """Get singleton instance"""
    return _sg

