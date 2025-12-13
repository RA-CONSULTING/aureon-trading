#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     📊 TRADE LOGGER & PROBABILITY MATRIX DATA VALIDATOR 📊                           ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                ║
║                                                                                      ║
║     Comprehensive logging for:                                                      ║
║       • Every trade executed (entry/exit timestamps)                                 ║
║       • Probability matrix predictions vs actual outcomes                            ║
║       • HNC frequency harmonics during each trade                                    ║
║       • Full market sweep verification                                               ║
║       • Cross-reference trader data with market conditions                           ║
║                                                                                      ║
║     Output: JSONL files for analysis & ML training                                   ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import threading
from collections import defaultdict

# Configure logging with safe UTF-8/ASCII handling
class SafeUTF8Formatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        try:
            # Try UTF-8 first
            _ = msg.encode('utf-8')
            return msg
        except Exception:
            # Fallback: replace non-encodable chars
            return msg.encode('utf-8', errors='replace').decode('ascii', errors='replace')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(SafeUTF8Formatter('%(asctime)s [%(levelname)s] %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        stream_handler,
        logging.FileHandler('trade_logger.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradeEntry:
    """Complete record of a single trade"""
    timestamp: str
    symbol: str
    side: str  # BUY/SELL
    exchange: str
    entry_price: float
    entry_time: float
    quantity: float
    entry_value: float
    coherence: float
    dominant_node: str
    hnc_frequency: float
    hnc_is_harmonic: bool
    probability_score: float
    imperial_probability: float
    cosmic_phase: str
    earth_coherence: float
    gates_passed: int
    
@dataclass
class TradeExit:
    """Exit record for a trade"""
    trade_id: str
    timestamp: str
    symbol: str
    exit_price: float
    exit_time: float
    exit_value: float
    gross_pnl: float
    net_pnl: float
    pnl_pct: float
    fees: float
    reason: str  # TP/SL/REBALANCE/etc
    hold_time_seconds: float
    hold_time_minutes: float
    
@dataclass
class ProbabilityValidation:
    """Cross-reference actual outcomes with predictions"""
    symbol: str
    entry_timestamp: str
    exit_timestamp: str
    predicted_probability: float
    predicted_action: str  # BUY/SELL/HOLD
    actual_outcome: str  # WIN/LOSS
    outcome_pct: float
    validation_1m: Optional[bool] = None  # Did 1m prediction match?
    validation_5m: Optional[bool] = None  # Did 5m prediction match?
    frequency_band: str = ""  # 174/256/396/432/440/etc
    coherence_level: str = ""  # LOW/MEDIUM/HIGH
    
@dataclass
class MarketSweepRecord:
    """Full market conditions during trading period"""
    timestamp: str
    total_opportunities_found: int
    opportunities_entered: int
    opportunities_rejected: int
    rejection_reasons: Dict[str, int] = field(default_factory=dict)  # {reason: count}
    hissing_frequencies: List[float] = field(default_factory=list)  # 440Hz distortion
    harmonic_frequencies: List[float] = field(default_factory=list)  # 256/528Hz
    average_coherence: float = 0.0
    system_flux: str = ""  # BULLISH/BEARISH/NEUTRAL
    dominant_node_distribution: Dict[str, int] = field(default_factory=dict)

class TradeLogger:
    """Comprehensive trade logging system"""
    
    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = os.path.join(tempfile.gettempdir(), 'aureon_trade_logs')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize output files
        self.trades_file = self.output_dir / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.exits_file = self.output_dir / f"exits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.validations_file = self.output_dir / f"validations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.market_sweep_file = self.output_dir / f"market_sweep_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        # In-memory tracking
        self.active_trades: Dict[str, Dict] = {}  # {trade_id: trade_data}
        self.trade_counter = 0
        self.lock = threading.Lock()
        
        logger.info(f"📊 Trade Logger initialized")
        logger.info(f"   Output directory: {self.output_dir}")
        logger.info(f"   Trades file: {self.trades_file.name}")
        
    def log_trade_entry(self, trade_data: Dict[str, Any]) -> str:
        """Log a trade entry and return trade_id"""
        with self.lock:
            self.trade_counter += 1
            trade_id = f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.trade_counter:06d}"
        
        entry = TradeEntry(
            timestamp=datetime.now().isoformat(),
            symbol=trade_data.get('symbol', 'UNKNOWN'),
            side=trade_data.get('side', 'BUY'),
            exchange=trade_data.get('exchange', 'kraken'),
            entry_price=trade_data.get('entry_price', 0.0),
            entry_time=trade_data.get('entry_time', time.time()),
            quantity=trade_data.get('quantity', 0.0),
            entry_value=trade_data.get('entry_value', 0.0),
            coherence=trade_data.get('coherence', 0.5),
            dominant_node=trade_data.get('dominant_node', 'Unknown'),
            hnc_frequency=trade_data.get('hnc_frequency', 256.0),
            hnc_is_harmonic=trade_data.get('hnc_is_harmonic', False),
            probability_score=trade_data.get('probability_score', 0.5),
            imperial_probability=trade_data.get('imperial_probability', 0.5),
            cosmic_phase=trade_data.get('cosmic_phase', 'UNKNOWN'),
            earth_coherence=trade_data.get('earth_coherence', 0.5),
            gates_passed=trade_data.get('gates_passed', 0),
        )
        
        # Store for later exit matching
        with self.lock:
            self.active_trades[trade_id] = asdict(entry)
        
        # Write to file
        with open(self.trades_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'trade_id': trade_id,
                **asdict(entry)
            }) + '\n')
        
        logger.info(f"📝 Trade Entry: {trade_id} | {entry.symbol} @ {entry.entry_price:.6f} | Γ={entry.coherence:.2f}")
        
        return trade_id
    
    def log_trade_exit(self, trade_id: str, exit_data: Dict[str, Any]) -> None:
        """Log trade exit and calculate P&L"""
        exit_record = TradeExit(
            trade_id=trade_id,
            timestamp=datetime.now().isoformat(),
            symbol=exit_data.get('symbol', 'UNKNOWN'),
            exit_price=exit_data.get('exit_price', 0.0),
            exit_time=exit_data.get('exit_time', time.time()),
            exit_value=exit_data.get('exit_value', 0.0),
            gross_pnl=exit_data.get('gross_pnl', 0.0),
            net_pnl=exit_data.get('net_pnl', 0.0),
            pnl_pct=exit_data.get('pnl_pct', 0.0),
            fees=exit_data.get('fees', 0.0),
            reason=exit_data.get('reason', 'UNKNOWN'),
            hold_time_seconds=exit_data.get('hold_time_seconds', 0.0),
            hold_time_minutes=exit_data.get('hold_time_seconds', 0.0) / 60.0,
        )
        
        # Write to file
        with open(self.exits_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(exit_record)) + '\n')
        
        # Remove from active trades
        with self.lock:
            if trade_id in self.active_trades:
                del self.active_trades[trade_id]
        
        result = "✅ WIN" if exit_record.net_pnl > 0 else "❌ LOSS"
        logger.info(f"📊 Trade Exit: {trade_id} | {result} | P&L: ${exit_record.net_pnl:+.2f} ({exit_record.pnl_pct:+.2f}%) | Reason: {exit_record.reason}")
    
    def log_probability_validation(self, validation_data: Dict[str, Any]) -> None:
        """Log prediction vs actual outcome for ML training"""
        validation = ProbabilityValidation(
            symbol=validation_data.get('symbol', 'UNKNOWN'),
            entry_timestamp=validation_data.get('entry_timestamp', datetime.now().isoformat()),
            exit_timestamp=validation_data.get('exit_timestamp', datetime.now().isoformat()),
            predicted_probability=validation_data.get('predicted_probability', 0.5),
            predicted_action=validation_data.get('predicted_action', 'HOLD'),
            actual_outcome=validation_data.get('actual_outcome', 'UNKNOWN'),
            outcome_pct=validation_data.get('outcome_pct', 0.0),
            validation_1m=validation_data.get('validation_1m'),
            validation_5m=validation_data.get('validation_5m'),
            frequency_band=validation_data.get('frequency_band', ''),
            coherence_level=validation_data.get('coherence_level', ''),
        )
        
        # Write to file
        with open(self.validations_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(validation)) + '\n')
        
        accuracy = "✅" if (validation.predicted_action == 'BUY' and validation.actual_outcome == 'WIN') else "❌"
        logger.info(f"📈 Validation: {accuracy} {validation.symbol} | Pred: {validation.predicted_action} | Actual: {validation.actual_outcome} ({validation.outcome_pct:+.2f}%)")
    
    def log_market_sweep(self, sweep_data: Dict[str, Any]) -> None:
        """Log full market analysis snapshot"""
        sweep = MarketSweepRecord(
            timestamp=datetime.now().isoformat(),
            total_opportunities_found=sweep_data.get('total_opportunities_found', 0),
            opportunities_entered=sweep_data.get('opportunities_entered', 0),
            opportunities_rejected=sweep_data.get('opportunities_rejected', 0),
            rejection_reasons=sweep_data.get('rejection_reasons', {}),
            hissing_frequencies=sweep_data.get('hissing_frequencies', []),
            harmonic_frequencies=sweep_data.get('harmonic_frequencies', []),
            average_coherence=sweep_data.get('average_coherence', 0.0),
            system_flux=sweep_data.get('system_flux', 'NEUTRAL'),
            dominant_node_distribution=sweep_data.get('dominant_node_distribution', {}),
        )
        
        # Write to file
        with open(self.market_sweep_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(sweep)) + '\n')
        
        logger.info(f"🌍 Market Sweep: Found {sweep.total_opportunities_found} opp | Entered {sweep.opportunities_entered} | Γ_avg={sweep.average_coherence:.2f} | Flux: {sweep.system_flux}")
    
    def get_trade_summary(self) -> Dict[str, Any]:
        """Get summary statistics of logged trades"""
        # Count files
        trade_count = sum(1 for line in open(self.trades_file, encoding='utf-8'))
        exit_count = sum(1 for line in open(self.exits_file, encoding='utf-8')) if self.exits_file.exists() else 0
        validation_count = sum(1 for line in open(self.validations_file, encoding='utf-8')) if self.validations_file.exists() else 0
        
        return {
            'total_trades_entered': trade_count,
            'total_trades_exited': exit_count,
            'active_trades': len(self.active_trades),
            'validations_recorded': validation_count,
            'trades_file': str(self.trades_file),
            'exits_file': str(self.exits_file),
            'validations_file': str(self.validations_file),
            'market_sweep_file': str(self.market_sweep_file),
        }
    
    def export_training_data(self, output_file: str = None) -> str:
        """Export all data in ML-friendly format"""
        if output_file is None:
            output_file = self.output_dir / f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        # Merge trades + exits + validations
        training_records = []
        
        try:
            with open(self.trades_file, encoding='utf-8') as f:
                trades = [json.loads(line) for line in f]
            
            with open(self.exits_file, encoding='utf-8') as f:
                exits = {line['trade_id']: json.loads(line) for line in f if 'trade_id' in line}
        except:
            trades = []
            exits = {}
        
        # Combine
        for trade in trades:
            trade_id = trade.get('trade_id')
            exit_data = exits.get(trade_id)
            
            if exit_data:
                record = {
                    **trade,
                    **exit_data,
                    'completed': True
                }
            else:
                record = {
                    **trade,
                    'completed': False
                }
            
            training_records.append(record)
        
        # Write export
        with open(output_file, 'w') as f:
            for record in training_records:
                f.write(json.dumps(record) + '\n')
        
        logger.info(f"💾 Exported {len(training_records)} training records to {output_file}")
        return str(output_file)

# Global logger instance
_trade_logger = None

def get_trade_logger() -> TradeLogger:
    """Get or create global trade logger"""
    global _trade_logger
    if _trade_logger is None:
        _trade_logger = TradeLogger()
    return _trade_logger

if __name__ == '__main__':
    logger = get_trade_logger()
    
    # Test logging
    logger.log_trade_entry({
        'symbol': 'BTCUSD',
        'side': 'BUY',
        'exchange': 'kraken',
        'entry_price': 95000.0,
        'quantity': 0.01,
        'entry_value': 950.0,
        'coherence': 0.65,
        'dominant_node': 'Tiger',
        'hnc_frequency': 256.0,
        'hnc_is_harmonic': True,
        'probability_score': 0.72,
        'imperial_probability': 0.68,
        'cosmic_phase': 'ALIGNMENT',
        'earth_coherence': 0.78,
        'gates_passed': 4,
    })
    
    logger.log_market_sweep({
        'total_opportunities_found': 45,
        'opportunities_entered': 3,
        'opportunities_rejected': 42,
        'average_coherence': 0.58,
        'system_flux': 'BULLISH',
        'harmonic_frequencies': [256.0, 528.0, 396.0],
    })
    
    print("\n✅ Trade Logger initialized and ready for integration")
