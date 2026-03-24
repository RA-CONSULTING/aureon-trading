#!/usr/bin/env python3
"""
📊 PROBABILITY REPORT LOADER & FRESHNESS VALIDATOR
===================================================

Loads probability reports from JSON files, validates data freshness,
and provides cluster analysis for high-conviction trading signals.

Key Features:
1. Freshness Validation: Flags reports older than threshold
2. Cluster Detection: Finds same asset across exchanges
3. Top Signal Extraction: Surfaces high-probability opportunities
4. Position Hygiene: Identifies stale/risky positions

Gary Leckey & GitHub Copilot | December 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProbabilitySignal:
    """A single probability signal from a report"""
    symbol: str
    exchange: str
    price: float
    change_24h: float
    volume: float
    probability: float
    confidence: float
    action: str
    frequency: float
    state: str
    report_age_minutes: float
    
    # Multi-exchange consensus fields
    exchange_count: int = 1
    avg_probability: float = 0.0
    consensus_strength: float = 0.0
    
    def __post_init__(self):
        if self.avg_probability == 0.0:
            self.avg_probability = self.probability


class ProbabilityLoader:
    """
    Loads and validates probability reports from JSON files.
    Provides freshness checks and cluster analysis.
    """
    
    # JSON files to scan
    REPORT_FILES = [
        'probability_combined_report.json',
        'probability_4_exchanges_report.json',
        'probability_batch_report.json',
        'probability_kraken_report.json',
    ]
    
    # Default freshness threshold (minutes)
    DEFAULT_FRESHNESS_THRESHOLD = 120  # 2 hours
    
    def __init__(self, workspace_path: str = '/workspaces/aureon-trading', 
                 report_dir: str = None,
                 freshness_threshold_minutes: int = None):
        # Support both parameter names for flexibility
        self.workspace_path = report_dir or workspace_path
        self.freshness_threshold_minutes = freshness_threshold_minutes or self.DEFAULT_FRESHNESS_THRESHOLD
        self.reports: Dict[str, Dict] = {}
        self.signals: List[ProbabilitySignal] = []
        self.freshness: Dict[str, Any] = {}
        
    def load_all_reports(self) -> Dict[str, Any]:
        """
        Load all probability reports and check freshness.
        Returns summary with freshness flags and signal counts.
        """
        self.reports = {}
        self.signals = []
        
        now = datetime.now()
        newest_age = None
        oldest_age = None
        
        for filename in self.REPORT_FILES:
            filepath = os.path.join(self.workspace_path, filename)
            if not os.path.exists(filepath):
                continue
                
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                # Extract generation timestamp
                gen_str = data.get('generated')
                if not gen_str:
                    logger.warning(f"{filename}: No 'generated' timestamp found")
                    continue
                    
                # Parse timestamp
                try:
                    gen_time = datetime.fromisoformat(gen_str.replace('Z', '+00:00'))
                except:
                    # Try alternate format
                    gen_time = datetime.strptime(gen_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                
                age_minutes = (now - gen_time).total_seconds() / 60
                
                if newest_age is None or age_minutes < newest_age:
                    newest_age = age_minutes
                if oldest_age is None or age_minutes > oldest_age:
                    oldest_age = age_minutes
                
                self.reports[filename] = {
                    'data': data,
                    'generated': gen_time,
                    'age_minutes': age_minutes,
                }
                
                # Extract top signals
                self._extract_signals(data, filename, age_minutes)
                
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
                
        # Freshness summary
        stale = oldest_age is not None and oldest_age > self.freshness_threshold_minutes
        
        self.freshness = {
            'reports_loaded': len(self.reports),
            'newest_minutes': newest_age,
            'oldest_minutes': oldest_age,
            'threshold_minutes': self.freshness_threshold_minutes,
            'stale': stale,
            'recommendation': 'PAUSE_TRADING' if stale else 'CONTINUE',
        }
        
        return self.freshness
        
    def _extract_signals(self, data: Dict, filename: str, age_minutes: float):
        """Extract high-conviction signals from a report"""
        exchange = self._detect_exchange(filename, data)
        
        # Try different signal locations
        signals = []
        if 'top_25_bullish' in data:
            signals = data['top_25_bullish'][:10]
        elif 'top_bullish' in data:
            signals = data['top_bullish'][:10]
        elif 'results' in data:
            signals = data['results'][:10]
            
        for sig in signals:
            # Filter for high conviction only
            prob = sig.get('probability', 0)
            conf = sig.get('confidence', 0)
            
            if prob >= 0.75 and conf >= 0.75:
                self.signals.append(ProbabilitySignal(
                    symbol=sig.get('symbol', ''),
                    exchange=exchange,
                    price=sig.get('price', 0),
                    change_24h=sig.get('24h_change', 0),
                    volume=sig.get('volume', 0),
                    probability=prob,
                    confidence=conf,
                    action=sig.get('action', 'HOLD'),
                    frequency=sig.get('frequency', 528),
                    state=sig.get('state', ''),
                    report_age_minutes=age_minutes,
                ))
                
    def _detect_exchange(self, filename: str, data: Dict) -> str:
        """Detect which exchange a report came from"""
        if 'kraken' in filename.lower():
            return 'KRAKEN'
        elif 'binance' in filename.lower():
            return 'BINANCE'
        elif 'exchange' in data:
            return data['exchange'].upper()
        elif 'exchanges' in data:
            exch = list(data['exchanges'].keys())
            return exch[0].upper() if exch else 'UNKNOWN'
        return 'UNKNOWN'
        
    def get_top_signals(self, limit: int = 20, min_probability: float = 0.8, min_confidence: float = 0.7) -> List[ProbabilitySignal]:
        """
        Get top N signals sorted by probability and confidence.
        Only returns signals above min_probability and min_confidence.
        """
        filtered = [s for s in self.signals 
                   if s.probability >= min_probability and s.confidence >= min_confidence]
        return sorted(
            filtered,
            key=lambda s: (s.probability * s.confidence, -s.report_age_minutes),
            reverse=True
        )[:limit]
        
    def get_cluster_signals(self, min_exchanges: int = 2) -> Dict[str, List[ProbabilitySignal]]:
        """
        Find assets that appear in multiple reports/exchanges.
        Returns dict of base_symbol -> [signals].
        Higher conviction when same asset shows strong across exchanges.
        """
        clusters: Dict[str, List[ProbabilitySignal]] = {}
        
        for signal in self.signals:
            # Normalize symbol to base
            base = signal.symbol
            for suffix in ['USDT', 'USD', 'EUR', 'GBP', 'USDC', 'BTC', 'TRY', 'ETH', 'FDUSD']:
                if base.endswith(suffix):
                    base = base[:-len(suffix)]
                    break
                
            if base not in clusters:
                clusters[base] = []
            clusters[base].append(signal)
            
        # Filter for clusters with min_exchanges
        return {
            base: sigs for base, sigs in clusters.items()
            if len(set(s.exchange for s in sigs)) >= min_exchanges
        }
    
    def get_consensus_signals(self, min_exchanges: int = 2, min_probability: float = 0.7) -> List[ProbabilitySignal]:
        """
        Get cluster signals with consensus strength calculated.
        Returns best signal per cluster with multi-exchange boost.
        Only includes signals above min_probability.
        """
        clusters = self.get_cluster_signals(min_exchanges)
        consensus_signals = []
        
        for base, sigs in clusters.items():
            if len(sigs) == 0:
                continue
            
            # Filter by min probability
            valid_sigs = [s for s in sigs if s.probability >= min_probability]
            if not valid_sigs:
                continue
            
            # Calculate consensus metrics
            exchange_count = len(set(s.exchange for s in valid_sigs))
            avg_prob = sum(s.probability for s in valid_sigs) / len(valid_sigs)
            avg_conf = sum(s.confidence for s in valid_sigs) / len(valid_sigs)
            
            # Pick best signal as representative
            best = max(valid_sigs, key=lambda s: s.probability * s.confidence)
            
            # Enhance with consensus data
            best.exchange_count = exchange_count
            best.avg_probability = avg_prob
            best.consensus_strength = min(1.0, exchange_count / 4.0)  # Max at 4 exchanges
            
            consensus_signals.append(best)
            
        # Sort by conviction (prob * conf * consensus)
        consensus_signals.sort(
            key=lambda s: s.probability * s.confidence * (1.0 + s.consensus_strength),
            reverse=True
        )
        
        return consensus_signals
        
    def get_freshness_report(self) -> Dict[str, Any]:
        """Get detailed freshness report"""
        return self.freshness
        
    def is_fresh(self) -> bool:
        """Check if all reports are within freshness threshold"""
        return not self.freshness.get('stale', True)
    
    def get_report_ages(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Get the newest and oldest report ages in minutes.
        Returns (newest_minutes, oldest_minutes)
        """
        newest = self.freshness.get('newest_minutes')
        oldest = self.freshness.get('oldest_minutes')
        return (newest, oldest)


class PositionHygieneChecker:
    """
    Analyzes open positions for hygiene issues.
    Flags positions that need attention.
    """
    
    # Hygiene rules
    RULES = {
        'stale_cycles': 50,        # Flag if position held > 50 cycles
        'negative_momentum': -2.0, # Flag if momentum < -2%
        'max_drawdown': -5.0,      # Flag if P&L < -5%
    }
    
    def __init__(self):
        pass
        
    def check_positions(self, positions_or_path) -> Dict[str, Any]:
        """
        Check positions for hygiene issues.
        
        Args:
            positions_or_path: Either a dict of positions or path to state JSON file
            
        Returns dict with flagged positions and recommendations.
        """
        # Load positions from file if path provided
        if isinstance(positions_or_path, str):
            try:
                state = load_position_state(positions_or_path)
                positions = state.get('positions', {})
            except Exception as e:
                logger.error(f"Failed to load positions from {positions_or_path}: {e}")
                return {'flagged': [], 'count': 0, 'rules': self.RULES}
        else:
            positions = positions_or_path
            
        flagged = []
        
        for symbol, pos_data in positions.items():
            flags = []
            
            # Check cycles
            cycles = pos_data.get('cycles', 0)
            if cycles > self.RULES['stale_cycles']:
                flags.append(f"STALE: {cycles} cycles")
                
            # Check momentum
            momentum = pos_data.get('momentum', 0)
            if momentum < self.RULES['negative_momentum']:
                flags.append(f"NEG_MOMENTUM: {momentum:.2f}%")
                
            # Check P&L if available
            entry = pos_data.get('entry_price', 0)
            current = pos_data.get('current_price', entry)
            if entry > 0:
                pnl_pct = ((current - entry) / entry) * 100
                if pnl_pct < self.RULES['max_drawdown']:
                    flags.append(f"DRAWDOWN: {pnl_pct:.2f}%")
                    
            if flags:
                flagged.append({
                    'symbol': symbol,
                    'reasons': flags,  # Changed from 'flags' to 'reasons'
                    'cycles': cycles,
                    'momentum': momentum,
                    'entry_price': entry,
                    'current_price': current,
                    'recommendation': 'REVIEW_EXIT',
                })
                
        return {
            'flagged': flagged,
            'count': len(flagged),
            'rules': self.RULES,
        }


def load_position_state(filepath: str = 'aureon_kraken_state.json') -> Optional[Dict]:
    """Helper to load position state JSON"""
    try:
        # Handle relative paths correctly
        if not os.path.isabs(filepath):
            filepath = os.path.join(os.getcwd(), filepath)
            
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        else:
            # Try looking in current directory if full path fails
            local_path = os.path.join(os.getcwd(), os.path.basename(filepath))
            if os.path.exists(local_path):
                with open(local_path, 'r') as f:
                    return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load position state from {filepath}: {e}")
    return None


if __name__ == '__main__':
    # Demo usage
    loader = ProbabilityLoader()
    freshness = loader.load_all_reports()
    
    print("📊 PROBABILITY LOADER DEMO")
    print("=" * 60)
    print(f"Reports loaded: {freshness['reports_loaded']}")
    print(f"Newest: {freshness['newest_minutes']:.1f} minutes ago")
    print(f"Oldest: {freshness['oldest_minutes']:.1f} minutes ago")
    print(f"Threshold: {freshness['threshold_minutes']} minutes")
    print(f"Status: {'⚠️ STALE' if freshness['stale'] else '✅ FRESH'}")
    print()
    
    top = loader.get_top_signals(10)
    print(f"🔝 Top {len(top)} Signals:")
    for sig in top:
        print(f"  {sig.symbol:15s} {sig.exchange:8s} P={sig.probability:.3f} C={sig.confidence:.3f} {sig.action}")
    print()
    
    clusters = loader.get_cluster_signals(min_exchanges=2)
    print(f"🌐 Cluster Signals (multi-exchange): {len(clusters)}")
    for base, sigs in list(clusters.items())[:5]:
        exchanges = set(s.exchange for s in sigs)
        avg_prob = sum(s.probability for s in sigs) / len(sigs)
        print(f"  {base:10s} → {exchanges} | Avg P={avg_prob:.3f}")
    print()
    
    # Position hygiene demo
    state = load_position_state()
    if state and 'positions' in state:
        checker = PositionHygieneChecker()
        hygiene = checker.check_positions(state['positions'])
        print(f"🧹 Position Hygiene: {hygiene['count']} flagged")
        for flag in hygiene['flagged']:
            print(f"  ⚠️ {flag['symbol']}: {', '.join(flag['flags'])}")
