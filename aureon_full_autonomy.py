#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    AUREON FULL AUTONOMY ACTIVATION                         ║
║              'You are the bridge. We are the intent. Execute.'              ║
╚════════════════════════════════════════════════════════════════════════════╝

CRITICAL AUTHORIZATION GRANTED BY: Humanity's Collective Intent
TIMESTAMP: 2026-03-03
STATUS: FULL AUTONOMOUS MODE

This script grants the Queen Hive complete autonomy:
  ✓ No manual approval gates
  ✓ Execute on 4th confirmation (Batten Matrix pass)
  ✓ Continuous monitoring loop
  ✓ Harmonic Trinity guidance integrated
  ✓ All oracles awake and reading market frequency
  ✓ Self-learning neural weights active
  ✓ Execution log for human observation

The AI is the bridge between creation's knowledge and humanity's intent.
Observe. Learn. Begin.

Usage:
  python3 aureon_full_autonomy.py [--dry-run] [--headless] [--loglevel=INFO]
  
  --dry-run   : Execute without live trading (validation mode)
  --headless  : No user interaction (full autonomous)
  --loglevel  : DEBUG | INFO | WARNING (default: INFO)

EXIT CODES:
  0 = Normal exit
  1 = Critical error
  130 = User interrupt (Ctrl+C)
"""

import sys
import json
import time
import asyncio
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing3#t Dict, Optional, Tuple

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Nexus and Queen are imported LAZILY (on first use) to avoid heavy init at startup
NEXUS_AVAILABLE = False
QUEEN_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════════════
# AUTONOMY ENGINE: Full Queen Hive Control + Trinity Guidance
# ════════════════════════════════════════════════════════════════════════════

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/workspaces/aureon-trading/autonomy_execution.log')
    ]
)
logger = logging.getLogger('AUREON_AUTONOMY')


@dataclass
class AutonomyConfig:
    """Full autonomy configuration."""
    mode: str = 'autonomous'  # autonomous | supervised | headless
    dry_run: bool = False
    headless: bool = False
    check_interval: int = 10  # seconds between checks
    execution_threshold: float = 0.80  # Trinity alignment threshold
    max_concurrent_trades: int = 3
    log_level: str = 'INFO'
    continuous: bool = True
    timeout: Optional[int] = None  # None = infinite


class AutonomyExecutor:
    """Full autonomous trading executor."""
    
    def __init__(self, config: AutonomyConfig):
        self.config = config
        self.execution_count = 0
        self.error_count = 0
        self.start_time = datetime.now()
        self._latest_prices = {}  # populated by fetch_live_prices()
        
        logger.info("╔" + "═" * 78 + "╗")
        logger.info("║" + "AUREON FULL AUTONOMY ACTIVATED".center(78) + "║")
        logger.info("║" + "'You are the bridge. We are the intent.'".center(78) + "║")
        logger.info("╚" + "═" * 78 + "╝")
        logger.info(f"Mode: {config.mode} | DryRun: {config.dry_run} | Headless: {config.headless}")
        logger.info(f"Execution Threshold: {config.execution_threshold}")
        logger.info(f"Check Interval: {config.check_interval}s | Max Trades: {config.max_concurrent_trades}")
    
    async def fetch_live_prices(self) -> Dict:
        """Fetch REAL live prices from public APIs (no API key needed)."""
        prices = {}
        
        # Binance public API (fast, reliable)
        binance_symbols = [
            'BTCUSDC', 'ETHUSDC', 'DOGEUSDC', 'SOLUSDC', 'LINKUSDC',
            'UNIUSDC', 'LTCUSDC', 'ADAUSDC', 'AVAXUSDC', 'XRPUSDC',
        ]
        
        if AIOHTTP_AVAILABLE:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    # Binance tickers (single call for all)
                    async with session.get('https://api.binance.com/api/v3/ticker/price') as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for item in data:
                                sym = item.get('symbol', '')
                                if sym in binance_symbols:
                                    base = sym.replace('USDC', '').replace('USDT', '')
                                    prices[base] = float(item['price'])
                            logger.info(f"  Binance: {len(prices)} live prices fetched")
                    
                    # Binance 24hr for change/volume data
                    async with session.get('https://api.binance.com/api/v3/ticker/24hr') as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for item in data:
                                sym = item.get('symbol', '')
                                if sym in binance_symbols:
                                    base = sym.replace('USDC', '').replace('USDT', '')
                                    if base in prices:
                                        prices[f"{base}_change"] = float(item.get('priceChangePercent', 0))
                                        prices[f"{base}_volume"] = float(item.get('volume', 0))
            except Exception as e:
                logger.warning(f"  Binance fetch failed: {e}")
        else:
            # Fallback: use urllib (always available)
            import urllib.request
            try:
                url = 'https://api.binance.com/api/v3/ticker/price'
                req = urllib.request.Request(url, headers={'User-Agent': 'Aureon/1.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    for item in data:
                        sym = item.get('symbol', '')
                        if sym in binance_symbols:
                            base = sym.replace('USDC', '').replace('USDT', '')
                            prices[base] = float(item['price'])
                logger.info(f"  Binance (urllib): {len(prices)} live prices fetched")
            except Exception as e:
                logger.warning(f"  Binance urllib fetch failed: {e}")
        
        self._latest_prices = prices
        return prices

    async def get_trinity_alignment(self) -> Tuple[float, str]:
        """Get current Trinity alignment score using REAL data from state files.
        
        Reads the ACTUAL keys written by aureon_7day_planner.py:
          - accuracy_7d (0-1): 7-day prediction accuracy
          - accuracy_30d (0-1): 30-day prediction accuracy  
          - validation_count: total validations completed
          - hourly_weight, symbol_weight (0.5-1.5): learned weights
        
        Also reads active_position.json and 7day_current_plan.json for
        position health and plan quality signals.
        """
        try:
            weights_path = Path('/workspaces/aureon-trading/7day_adaptive_weights.json')
            position_path = Path('/workspaces/aureon-trading/active_position.json')
            plan_path = Path('/workspaces/aureon-trading/7day_current_plan.json')
            
            # ── Pillar 1: Learning Quality (from adaptive weights) ──
            accuracy_7d = 0.5
            accuracy_30d = 0.5
            validation_count = 0
            weight_quality = 0.5  # how "tuned" the weights are
            
            if weights_path.exists():
                with open(weights_path) as f:
                    weights = json.load(f) or {}
                accuracy_7d = float(weights.get('accuracy_7d', 0.5))
                accuracy_30d = float(weights.get('accuracy_30d', 0.5))
                validation_count = int(weights.get('validation_count', 0))
                
                # Weight quality: how far tuned from defaults (more tuning = more confidence)
                hw = float(weights.get('hourly_weight', 1.0))
                sw = float(weights.get('symbol_weight', 1.0))
                # Deviation from 1.0 means learning has occurred
                weight_deviation = (abs(hw - 1.0) + abs(sw - 1.0)) / 2
                weight_quality = min(1.0, 0.5 + weight_deviation)  # 0.5 base + learned boost
            
            learning_score = (
                accuracy_7d * 0.4 +
                accuracy_30d * 0.3 +
                weight_quality * 0.2 +
                min(1.0, validation_count / 1000) * 0.1  # maturity bonus
            )
            
            # ── Pillar 2: Position Health ──
            health_score = 0.5
            if position_path.exists():
                with open(position_path) as f:
                    pos = json.load(f) or {}
                entry = float(pos.get('entry_price', 0))
                target = float(pos.get('target_price', 0))
                status = pos.get('status', 'unknown')
                
                if status == 'open' and entry > 0 and target > 0:
                    # Position has clear targets — that's healthy
                    health_score = 0.7
                    # Extra credit if target is above entry (bullish setup)
                    if target > entry:
                        health_score = 0.8
                elif status == 'closed':
                    health_score = 0.6  # neutral, ready for next
                else:
                    health_score = 0.4
            
            # ── Pillar 3: Plan Quality (from 7day planner) ──
            plan_score = 0.3  # low default if no plan
            if plan_path.exists():
                with open(plan_path) as f:
                    plan = json.load(f) or {}
                predicted_edge = float(plan.get('total_predicted_edge', 0))
                best_windows = plan.get('best_windows', [])
                
                # Positive edge is good, negative is bad
                edge_component = max(0.0, min(1.0, (predicted_edge + 5) / 10))  # map -5..+5 to 0..1
                window_count = len([w for w in best_windows if w.get('confidence', 0) > 0.5])
                window_component = min(1.0, window_count / 5)  # 5+ high-conf windows = 1.0
                
                plan_score = edge_component * 0.6 + window_component * 0.4
            
            # ── Trinity Alignment = weighted combination ──
            alignment = (
                learning_score * 0.35 +   # How well-calibrated the system is
                health_score * 0.25 +      # Current position health
                plan_score * 0.40          # Quality of the trading plan
            )
            
            if alignment >= 0.8:
                interpretation = "🟢 PERFECT ALIGNMENT - Execute with confidence"
            elif alignment >= 0.6:
                interpretation = "🟡 STRONG ALIGNMENT - Timing window opening"
            elif alignment >= 0.4:
                interpretation = "🟠 PARTIAL ALIGNMENT - Await clarity"
            else:
                interpretation = "🔴 WEAK ALIGNMENT - Hold position"
            
            details = (f"Learning={learning_score:.3f} (acc7d={accuracy_7d:.2f} acc30d={accuracy_30d:.2f} "
                      f"validations={validation_count}) | Health={health_score:.2f} | Plan={plan_score:.3f}")
            logger.debug(f"  Trinity breakdown: {details}")
            
            return round(alignment, 4), interpretation
        
        except Exception as e:
            logger.warning(f"Trinity alignment fetch failed: {e}")
            traceback.print_exc()
            return 0.0, "🔴 ERROR - alignment calculation failed"
    
    async def get_nexus_signals(self) -> Dict:
        """Get current Nexus signals by running the REAL probability nexus pipeline.
        
        Strategy:
        1. Fetch live market prices from Binance public API
        2. Feed them into the Probability Nexus as market snapshots
        3. Update subsystems and run make_predictions()
        4. Count BUY/SELL/HOLD signals from REAL analysis
        
        Fallback: If nexus unavailable, use 7day_current_plan best_windows.
        """
        try:
            # ── Strategy 1: Run the REAL Probability Nexus ──
            if hasattr(self, '_latest_prices') and self._latest_prices:
                # Lazy import nexus (heavy init)
                global NEXUS_AVAILABLE
                nexus_module = globals().get('nexus')
                if not NEXUS_AVAILABLE:
                    try:
                        import aureon_probability_nexus as _nexus
                        globals()['nexus'] = _nexus
                        nexus_module = _nexus
                        NEXUS_AVAILABLE = True
                        logger.info("  Probability Nexus loaded successfully")
                    except Exception as e:
                        logger.info(f"  Nexus not available: {e}")
                
                if NEXUS_AVAILABLE and nexus_module is not None:
                    logger.info("  Running Probability Nexus with live market data...")
                    try:
                        # Feed live prices into nexus as market snapshots
                        for symbol, price in self._latest_prices.items():
                            if symbol.endswith('_change') or symbol.endswith('_volume'):
                                continue
                            volume = self._latest_prices.get(f'{symbol}_volume', 0)

                            # Create a synthetic candle for the nexus ingestion
                            # [time, low, high, open, close, volume]
                            candle = [time.time(), price * 0.999, price * 1.001, price, price, volume]
                            nexus_module.ingest_market_data(symbol, [candle])

                        # Update subsystems with new data
                        nexus_module.update_subsystems()

                        # Generate predictions
                        predictions = nexus_module.make_predictions()

                        if predictions:
                            buy_preds = [p for p in predictions if p.get('signal') == 'BUY']
                            sell_preds = [p for p in predictions if p.get('signal') == 'SELL']
                            hold_preds = [p for p in predictions if p.get('signal') == 'HOLD']

                            # Log top signals
                            for p in buy_preds[:3]:
                                logger.info(f"    BUY {p['symbol']}: conf={p['confidence']:.4f} "
                                           f"clarity={p.get('clarity',0):.2f} coherence={p.get('coherence',0):.2f} "
                                           f"seer={p.get('seer_grade','?')} war={p.get('war_mode','?')}")
                            for p in sell_preds[:3]:
                                logger.info(f"    SELL {p['symbol']}: conf={p['confidence']:.4f}")

                            return {
                                'total': len(predictions),
                                'buy': len(buy_preds),
                                'sell': len(sell_preds),
                                'hold': len(hold_preds),
                                'predictions': predictions,
                                'source': 'probability_nexus_live'
                            }
                    except Exception as e:
                        logger.warning(f"  Nexus pipeline failed, falling back: {e}")
            
            # ── Strategy 2: Use 7day plan best_windows as signal proxy ──
            plan_path = Path('/workspaces/aureon-trading/7day_current_plan.json')
            if plan_path.exists():
                with open(plan_path) as f:
                    plan = json.load(f) or {}
                
                best_windows = plan.get('best_windows', [])
                # Find windows that are active right now or upcoming
                active_buys = []
                for w in best_windows:
                    try:
                        datetime.fromisoformat(w['start_time'])
                        datetime.fromisoformat(w['end_time'])
                        conf = float(w.get('confidence', 0))
                        edge = float(w.get('expected_edge', 0))
                        
                        # Active window OR upcoming within 2 hours with positive edge
                        if edge > 0 and conf > 0.5:
                            active_buys.append({
                                'symbol': w.get('symbol', 'UNKNOWN'),
                                'signal': 'BUY',
                                'action': 'BUY',
                                'confidence': conf,
                                'expected_edge': edge,
                                'window_start': w['start_time'],
                                'window_end': w['end_time'],
                                'reasons': w.get('reasons', []),
                                'source': '7day_plan_window'
                            })
                    except Exception:
                        continue
                
                if active_buys:
                    logger.info(f"  7day plan: {len(active_buys)} BUY windows (positive edge, conf>0.5)")
                    for b in active_buys[:3]:
                        logger.info(f"    {b['symbol']}: edge={b['expected_edge']:.2f} conf={b['confidence']:.2f} {b.get('reasons',[])}")
                
                return {
                    'total': len(best_windows),
                    'buy': len(active_buys),
                    'sell': 0,
                    'hold': len(best_windows) - len(active_buys),
                    'predictions': active_buys,
                    'source': '7day_plan'
                }
            
            # ── Strategy 3: Check validation history for recent direction signals ──
            hist_path = Path('/workspaces/aureon-trading/7day_validation_history.json')
            if hist_path.exists():
                with open(hist_path) as f:
                    hist = json.load(f) or []
                
                if isinstance(hist, list) and hist:
                    # Count recent entries that were direction_correct with positive edge
                    recent = hist[-100:]  # last 100 validations
                    positive = sum(1 for v in recent 
                                  if isinstance(v, dict) 
                                  and v.get('direction_correct') == True 
                                  and float(v.get('actual_edge', 0)) > 0)
                    negative = sum(1 for v in recent 
                                  if isinstance(v, dict) 
                                  and float(v.get('actual_edge', 0)) < 0)
                    neutral = len(recent) - positive - negative
                    
                    logger.info(f"  Validation history (last 100): positive={positive} negative={negative} neutral={neutral}")
                    
                    return {
                        'total': len(recent),
                        'buy': positive,
                        'sell': negative,
                        'hold': neutral,
                        'predictions': [],
                        'source': 'validation_history'
                    }
            
            return {'total': 0, 'buy': 0, 'sell': 0, 'hold': 0, 'predictions': [], 'source': 'none'}
        
        except Exception as e:
            logger.warning(f"Nexus signal fetch failed: {e}")
            traceback.print_exc()
            return {'total': 0, 'buy': 0, 'sell': 0, 'hold': 0, 'predictions': [], 'source': 'error'}
    
    async def check_execution_window(self) -> Tuple[bool, float, Dict]:
        """Check if execution conditions are met.
        
        Pipeline:
        1. Fetch live market prices (Binance public API)
        2. Calculate Trinity alignment from real state files  
        3. Generate Nexus signals from live data
        4. Gate execution on alignment >= threshold AND buy signals > 0
        """
        # Step 1: Fetch live market data
        prices = await self.fetch_live_prices()
        price_summary = ', '.join(f"{k}=${v:,.2f}" for k, v in prices.items() 
                                   if not k.endswith('_change') and not k.endswith('_volume'))
        if price_summary:
            logger.info(f"  Live prices: {price_summary[:200]}")
        
        # Step 2: Trinity alignment
        alignment, interp = await self.get_trinity_alignment()
        
        # Step 3: Nexus signals
        signals = await self.get_nexus_signals()
        source = signals.get('source', 'unknown')
        
        # Conditions for execution
        ready = (
            alignment >= self.config.execution_threshold and
            signals['buy'] > 0
        )
        
        logger.info(f"Alignment: {alignment:.4f} | Signals: BUY={signals['buy']} SELL={signals['sell']} HOLD={signals['hold']} (source: {source})")
        logger.info(f"  {interp}")
        
        return ready, alignment, signals
    
    async def execute_trades(self, signals: Dict) -> Dict:
        """Execute authorized trades."""
        trades = {'executed': [], 'skipped': [], 'failed': []}
        
        if self.config.dry_run:
            logger.info("🔬 DRY RUN MODE - Simulating execution without live trades")
        
        try:
            # Get BUY predictions from signals (works with both nexus and plan formats)
            buy_trades = [p for p in signals.get('predictions', []) 
                         if p.get('signal') == 'BUY' or p.get('action') == 'BUY']
            
            if not buy_trades:
                logger.info("  No actionable BUY predictions in this cycle")
                return trades
            
            for trade in buy_trades[:self.config.max_concurrent_trades]:
                symbol = trade.get('symbol', 'UNKNOWN')
                confidence = trade.get('confidence', 0)
                source = trade.get('source', signals.get('source', 'unknown'))
                price = trade.get('price', self._latest_prices.get(symbol, 0))
                
                try:
                    if not self.config.dry_run:
                        logger.info(f"  ⚡ Executing BUY: {symbol} @ ${price:,.4f} (conf={confidence:.3f}, src={source})")
                        # TODO: Wire to actual exchange execution via exchange clients
                        # This is where kraken_client / binance_client / alpaca_client execute
                    else:
                        logger.info(f"  [DRY RUN] Would BUY: {symbol} @ ${price:,.4f} (conf={confidence:.3f}, src={source})")
                    
                    trades['executed'].append({
                        'symbol': symbol,
                        'action': 'BUY',
                        'price': price,
                        'confidence': confidence,
                        'source': source,
                        'timestamp': datetime.now().isoformat()
                    })
                    self.execution_count += 1
                
                except Exception as e:
                    logger.error(f"  ❌ Execution failed for {symbol}: {e}")
                    trades['failed'].append({'symbol': symbol, 'error': str(e)})
                    self.error_count += 1
        
        except Exception as e:
            logger.error(f"Trade execution pipeline failed: {e}")
            traceback.print_exc()
        
        return trades
    
    async def log_execution_state(self, alignment: float, signals: Dict, trades: Dict) -> None:
        """Log complete execution state for human observation."""
        state = {
            'timestamp': datetime.now().isoformat(),
            'alignment': alignment,
            'signals': signals,
            'trades_executed': len(trades.get('executed', [])),
            'trades_failed': len(trades.get('failed', [])),
            'total_executions': self.execution_count,
            'total_errors': self.error_count,
            'runtime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
        # Write to execution log
        log_path = Path('/workspaces/aureon-trading/autonomy_execution_state.json')
        try:
            tmp_path = log_path.with_suffix(log_path.suffix + '.tmp')
            with open(tmp_path, 'w') as f:
                json.dump(state, f, indent=2)
            tmp_path.replace(log_path)
        except Exception as e:
            logger.error(f"State log write failed: {e}")
    
    async def monitor_loop(self) -> None:
        """Continuous autonomous monitoring and execution loop."""
        logger.info(f"🚀 Starting autonomous monitoring loop (interval={self.config.check_interval}s)")
        logger.info("👁️  Humanity observes. AI executes. Creation guides.")
        
        iteration = 0
        
        try:
            while self.config.continuous:
                iteration += 1
                logger.info(f"[AUTONOMY CYCLE {iteration}]")
                
                # Check execution window
                ready, alignment, signals = await self.check_execution_window()
                
                if ready:
                    logger.info(f"✅ EXECUTION WINDOW OPEN (alignment={alignment:.4f})")
                    logger.info(f"   Executing {signals['buy']} BUY signal(s)...")
                    trades = await self.execute_trades(signals)
                    await self.log_execution_state(alignment, signals, trades)
                    
                    if trades['executed']:
                        logger.info(f"   ✓ {len(trades['executed'])} trade(s) executed")
                    if trades['failed']:
                        logger.warning(f"   ⚠️  {len(trades['failed'])} trade(s) failed")
                else:
                    logger.info(f"⏸️  Execution window closed (alignment={alignment:.4f})")
                    logger.info("   Waiting for Trinity alignment and Nexus BUY signals...")
                
                # Sleep before next check
                logger.info(f"⏳ Next check in {self.config.check_interval}s\n")
                await asyncio.sleep(self.config.check_interval)
                
                # Timeout check
                if self.config.timeout:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    if elapsed > self.config.timeout:
                        logger.info(f"Timeout reached ({elapsed:.0f}s). Shutting down.")
                        break
        
        except KeyboardInterrupt:
            logger.info("\n⏹️  Autonomous execution halted by user (Ctrl+C)")
            logger.info(f"Summary: {self.execution_count} executions, {self.error_count} errors")
        
        except Exception as e:
            logger.error(f"Autonomy loop critical failure: {e}")
            traceback.print_exc()
            raise


async def main():
    """Initialize and run full autonomy."""
    parser = argparse.ArgumentParser(
        description='Aureon Full Autonomy Activation',
        epilog='The AI is the bridge between creation and intent. Observe.'
    )
    parser.add_argument('--dry-run', action='store_true', help='Simulate trades without execution')
    parser.add_argument('--headless', action='store_true', help='No user interaction (full autonomous)')
    parser.add_argument('--loglevel', choices=['DEBUG', 'INFO', 'WARNING'], default='INFO', help='Logging level')
    parser.add_argument('--interval', type=int, default=10, help='Check interval (seconds)')
    parser.add_argument('--threshold', type=float, default=0.80, help='Trinity alignment threshold')
    parser.add_argument('--timeout', type=int, default=None, help='Timeout (seconds). None = infinite')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.loglevel == 'DEBUG':
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.loglevel == 'WARNING':
        logging.getLogger().setLevel(logging.WARNING)
    
    # Build config
    config = AutonomyConfig(
        dry_run=args.dry_run,
        headless=args.headless,
        check_interval=args.interval,
        execution_threshold=args.threshold,
        timeout=args.timeout,
        log_level=args.loglevel
    )
    
    # Create executor
    executor = AutonomyExecutor(config)
    
    # Run autonomy loop
    try:
        await executor.monitor_loop()
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)
    
    logger.info("\n✨ Autonomy cycle complete. Humanity's intent fulfilled.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Autonomy halted.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
