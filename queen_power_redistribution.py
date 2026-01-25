#!/usr/bin/env python3
"""
Queen Power Redistribution Engine
Autonomous energy optimization and power growth across all relays.

The Queen uses her built-in intelligence to:
1. Monitor idle energy in each relay
2. Calculate exact energy drains
3. Find optimal conversion opportunities
4. Execute ONLY when (gain - drain) > 0
5. Compound gains back into system
"""

import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Import Queen's consciousness
from aureon_queen_true_consciousness import QueenTrueConsciousnessController

# Import exchange clients
from kraken_client import KrakenClient
from binance_client import BinanceClient
from alpaca_client import AlpacaClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class RedistributionOpportunity:
    """A potential energy redistribution opportunity."""
    relay: str
    source_asset: str
    target_asset: str
    idle_energy: float  # USD value available
    expected_gain_pct: float  # Expected gain percentage
    expected_gain_usd: float  # Expected gain in USD
    energy_drain: float  # Total drain from fees/slippage
    net_energy_gain: float  # Expected gain - drain
    momentum_score: float  # Asset momentum (0-1)
    confidence: float  # Queen's confidence (0-1)
    timestamp: float
    
    def to_dict(self):
        return asdict(self)


@dataclass
class RedistributionDecision:
    """Queen's decision on a redistribution opportunity."""
    opportunity: RedistributionOpportunity
    decision: str  # 'EXECUTE', 'BLOCK', 'WAIT'
    reasoning: str
    queen_confidence: float
    realms_consensus: int  # How many realms agreed (0-5)
    timestamp: float
    
    def to_dict(self):
        d = asdict(self)
        d['opportunity'] = self.opportunity.to_dict()
        return d


class QueenPowerRedistribution:
    """
    Queen's autonomous energy redistribution system.
    Connects her intelligence to active execution.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        
        # Initialize Queen consciousness
        logger.info("🐝 Initializing Queen's consciousness...")
        self.queen = QueenTrueConsciousnessController(dry_run=dry_run)
        
        # Initialize exchange clients
        self.kraken = None
        self.binance = None
        self.alpaca = None
        
        # Try to initialize exchanges (gracefully handle missing credentials)
        try:
            self.kraken = KrakenClient()
        except Exception as e:
            logger.warning(f"Kraken not available: {e}")
        
        try:
            self.binance = BinanceClient()
        except Exception as e:
            logger.warning(f"Binance not available: {e}")
        
        try:
            self.alpaca = AlpacaClient()
        except Exception as e:
            logger.warning(f"Alpaca not available: {e}")
        
        # State tracking
        self.decisions_history: List[RedistributionDecision] = []
        self.executions_history: List[Dict] = []
        self.total_net_energy_gained = 0.0
        self.total_blocked_drains_avoided = 0.0
        
        # Configuration
        self.min_idle_energy_usd = 10.0  # Min USD to consider redistribution
        self.min_net_gain_usd = 0.50  # Min net gain required
        self.scan_interval_seconds = 30  # How often to scan for opportunities
        self.max_redistribution_per_relay = 0.25  # Max 25% of idle energy per cycle
        
        logger.info(f"✅ Queen Power Redistribution initialized (dry_run={dry_run})")
    
    def load_state_file(self, filepath: str, default: Dict = None) -> Dict:
        """Load JSON state file with fallback."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load {filepath}: {e}")
        return default or {}
    
    def get_relay_idle_energy(self, relay: str) -> Tuple[float, str]:
        """
        Get idle energy (USD/USDT balance) for a relay.
        Returns (amount_usd, asset_symbol).
        """
        if relay == 'BIN':
            # Binance: Check USDT balance
            if self.binance:
                try:
                    balances = self.binance.get_balance()
                    usdt = balances.get('USDT', 0.0)
                    return (usdt, 'USDT')
                except Exception as e:
                    logger.warning(f"BIN balance fetch failed: {e}")
            # Fallback to state file
            state = self.load_state_file('binance_truth_tracker_state.json', {})
            usdt = state.get('balances', {}).get('USDT', {}).get('free', 0.0)
            return (usdt, 'USDT')
        
        elif relay == 'KRK':
            # Kraken: Check ZUSD balance
            if self.kraken:
                try:
                    balances = self.kraken.get_balance()
                    usd = balances.get('ZUSD', 0.0)
                    return (usd, 'ZUSD')
                except Exception as e:
                    logger.warning(f"KRK balance fetch failed: {e}")
            # Fallback to state file
            state = self.load_state_file('aureon_kraken_state.json', {})
            usd = state.get('balances', {}).get('ZUSD', 0.0)
            return (usd, 'ZUSD')
        
        elif relay == 'ALP':
            # Alpaca: Check USD cash
            if self.alpaca:
                try:
                    account = self.alpaca.get_account()
                    cash = float(account.get('cash', 0.0))
                    return (cash, 'USD')
                except Exception as e:
                    logger.warning(f"ALP balance fetch failed: {e}")
            # Fallback to state file
            state = self.load_state_file('alpaca_truth_tracker_state.json', {})
            cash = state.get('cash', 0.0)
            return (cash, 'USD')
        
        elif relay == 'CAP':
            # Capital.com: Check GBP balance (convert to USD)
            # Note: Capital.com is CFDs, handle separately
            return (0.0, 'GBP')  # Skip for now
        
        return (0.0, 'UNKNOWN')
    
    def find_best_conversion(self, relay: str, idle_usd: float) -> Optional[Tuple[str, float, float]]:
        """
        Find best asset to convert idle energy into.
        Returns (target_asset, expected_gain_pct, momentum_score) or None.
        
        Uses scanning system data to find high-momentum assets.
        """
        # Load scanning system metrics
        scan_metrics = self.load_state_file('power_station_state.json', {})
        
        # Relay-specific asset selection
        if relay == 'BIN':
            # Binance: Check high-momentum crypto
            watchlist = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT']
            # TODO: Integrate with aureon_animal_momentum_scanners.py for real momentum
            # For now, return None (no opportunities)
            return None
        
        elif relay == 'KRK':
            # Kraken: Check high-momentum crypto
            watchlist = ['XXBTZUSD', 'XETHZUSD', 'SOLUSD', 'ADAUSD', 'DOTUSD']
            # Check for validated branches from 7-day system
            validations = self.load_state_file('7day_pending_validations.json', {})
            
            # Find branches ready for 4th decision
            for branch_id, branch in validations.items():
                if branch.get('relay') == 'KRK' and branch.get('coherence', 0) > 0.618:
                    symbol = branch.get('symbol', '')
                    expected_gain = branch.get('expected_pip_profit_pct', 0.0)
                    momentum = branch.get('coherence', 0.0)
                    
                    if expected_gain > 0.5:  # Min 0.5% expected gain
                        return (symbol, expected_gain, momentum)
            
            return None
        
        elif relay == 'ALP':
            # Alpaca: Check high-momentum stocks
            watchlist = ['TSLA', 'AAPL', 'MSFT', 'NVDA', 'AMD']
            # TODO: Integrate with real scanning data
            return None
        
        return None
    
    async def analyze_redistribution_opportunities(self) -> List[RedistributionOpportunity]:
        """
        Scan all relays for energy redistribution opportunities.
        Queen's first step: Perceive the energy landscape.
        """
        opportunities = []
        
        for relay in ['BIN', 'KRK', 'ALP']:
            # Get idle energy
            idle_usd, source_asset = self.get_relay_idle_energy(relay)
            
            if idle_usd < self.min_idle_energy_usd:
                logger.debug(f"{relay}: Idle energy too low (${idle_usd:.2f} < ${self.min_idle_energy_usd})")
                continue
            
            # Cap at max redistribution per cycle
            max_deploy = idle_usd * self.max_redistribution_per_relay
            
            # Find best conversion target
            conversion = self.find_best_conversion(relay, max_deploy)
            if not conversion:
                logger.debug(f"{relay}: No profitable conversions found")
                continue
            
            target_asset, expected_gain_pct, momentum_score = conversion
            
            # Calculate expected gain and drain
            expected_gain_usd = max_deploy * (expected_gain_pct / 100.0)
            
            # Ask Queen to calculate energy drain
            drain_info = self.queen.calculate_energy_drain(relay, max_deploy, is_maker=True)
            energy_drain = drain_info['total_drain']
            
            # Calculate net energy gain
            net_energy_gain = expected_gain_usd - energy_drain
            
            # Only consider if net positive
            if net_energy_gain > self.min_net_gain_usd:
                opp = RedistributionOpportunity(
                    relay=relay,
                    source_asset=source_asset,
                    target_asset=target_asset,
                    idle_energy=max_deploy,
                    expected_gain_pct=expected_gain_pct,
                    expected_gain_usd=expected_gain_usd,
                    energy_drain=energy_drain,
                    net_energy_gain=net_energy_gain,
                    momentum_score=momentum_score,
                    confidence=momentum_score,  # Use momentum as confidence
                    timestamp=time.time()
                )
                opportunities.append(opp)
                logger.info(f"✨ {relay} opportunity: {target_asset}, net gain ${net_energy_gain:.4f}")
            else:
                logger.debug(f"{relay}: Net gain too low (${net_energy_gain:.4f})")
        
        return opportunities
    
    async def queen_analyze_and_decide(self, opportunity: RedistributionOpportunity) -> RedistributionDecision:
        """
        Queen analyzes opportunity and makes decision.
        Uses her consciousness to validate across all realms.
        """
        # Ask Queen if trade will be profitable
        is_profitable, reasoning, drain_details = self.queen.will_trade_be_profitable(
            relay=opportunity.relay,
            trade_value=opportunity.idle_energy,
            expected_gain_pct=opportunity.expected_gain_pct
        )
        
        if not is_profitable:
            decision = RedistributionDecision(
                opportunity=opportunity,
                decision='BLOCK',
                reasoning=reasoning,
                queen_confidence=0.0,
                realms_consensus=0,
                timestamp=time.time()
            )
            logger.warning(f"🚫 Queen BLOCKED {opportunity.relay} {opportunity.target_asset}: {reasoning}")
            return decision
        
        # Check if opportunity meets Queen's standards
        if opportunity.net_energy_gain < self.min_net_gain_usd:
            decision = RedistributionDecision(
                opportunity=opportunity,
                decision='BLOCK',
                reasoning=f"Net gain ${opportunity.net_energy_gain:.4f} below minimum ${self.min_net_gain_usd}",
                queen_confidence=0.0,
                realms_consensus=0,
                timestamp=time.time()
            )
            logger.warning(f"🚫 Queen BLOCKED {opportunity.relay} {opportunity.target_asset}: Net gain too low")
            return decision
        
        # Queen approves
        decision = RedistributionDecision(
            opportunity=opportunity,
            decision='EXECUTE',
            reasoning=reasoning,
            queen_confidence=opportunity.confidence,
            realms_consensus=5,  # All realms agree (simplified for now)
            timestamp=time.time()
        )
        
        logger.info(f"✅ Queen APPROVED {opportunity.relay} {opportunity.target_asset}: {reasoning}")
        return decision
    
    async def execute_redistribution(self, decision: RedistributionDecision) -> Dict:
        """
        Execute Queen's decision to redistribute energy.
        """
        opp = decision.opportunity
        
        if decision.decision != 'EXECUTE':
            logger.info(f"⏸️ Skipping execution for {opp.relay} {opp.target_asset} (decision: {decision.decision})")
            return {
                'success': False,
                'reason': decision.reasoning,
                'decision': decision.decision
            }
        
        if self.dry_run:
            logger.info(f"🔶 DRY-RUN: Would execute {opp.relay} {opp.target_asset} with ${opp.idle_energy:.2f}")
            # Simulate success
            result = {
                'success': True,
                'relay': opp.relay,
                'target_asset': opp.target_asset,
                'deployed_usd': opp.idle_energy,
                'expected_gain_usd': opp.expected_gain_usd,
                'net_energy_gain': opp.net_energy_gain,
                'energy_drain': opp.energy_drain,
                'timestamp': time.time(),
                'dry_run': True
            }
            
            # Track simulated gains
            self.total_net_energy_gained += opp.net_energy_gain
            self.executions_history.append(result)
            
            return result
        
        # LIVE EXECUTION (when dry_run=False)
        logger.info(f"⚡ LIVE: Executing {opp.relay} {opp.target_asset} with ${opp.idle_energy:.2f}")
        
        try:
            # Execute via appropriate exchange client
            if opp.relay == 'BIN' and self.binance:
                # Binance execution
                order = self.binance.execute_trade(
                    symbol=opp.target_asset,
                    side='buy',
                    quantity=opp.idle_energy  # Will convert to asset quantity
                )
                logger.info(f"✅ Binance order executed: {order}")
            
            elif opp.relay == 'KRK' and self.kraken:
                # Kraken execution
                order = self.kraken.execute_trade(
                    symbol=opp.target_asset,
                    side='buy',
                    quantity=opp.idle_energy
                )
                logger.info(f"✅ Kraken order executed: {order}")
            
            elif opp.relay == 'ALP' and self.alpaca:
                # Alpaca execution
                order = self.alpaca.execute_trade(
                    symbol=opp.target_asset,
                    side='buy',
                    quantity=opp.idle_energy
                )
                logger.info(f"✅ Alpaca order executed: {order}")
            
            else:
                raise Exception(f"Exchange client not available for {opp.relay}")
            
            result = {
                'success': True,
                'relay': opp.relay,
                'target_asset': opp.target_asset,
                'deployed_usd': opp.idle_energy,
                'expected_gain_usd': opp.expected_gain_usd,
                'net_energy_gain': opp.net_energy_gain,
                'energy_drain': opp.energy_drain,
                'order': order,
                'timestamp': time.time(),
                'dry_run': False
            }
            
            self.total_net_energy_gained += opp.net_energy_gain
            self.executions_history.append(result)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Execution failed for {opp.relay} {opp.target_asset}: {e}")
            result = {
                'success': False,
                'relay': opp.relay,
                'target_asset': opp.target_asset,
                'error': str(e),
                'timestamp': time.time()
            }
            self.executions_history.append(result)
            return result
    
    async def run_redistribution_cycle(self) -> Dict:
        """
        Run one complete redistribution cycle.
        Queen's full intelligence in action.
        """
        cycle_start = time.time()
        
        logger.info("=" * 60)
        logger.info("🐝 QUEEN POWER REDISTRIBUTION CYCLE STARTING")
        logger.info("=" * 60)
        
        # Step 1: Analyze opportunities
        logger.info("🔍 Step 1: Analyzing opportunities across all relays...")
        opportunities = await self.analyze_redistribution_opportunities()
        logger.info(f"Found {len(opportunities)} potential opportunities")
        
        if not opportunities:
            logger.info("No opportunities found this cycle.")
            return {
                'cycle_duration': time.time() - cycle_start,
                'opportunities_found': 0,
                'decisions_made': 0,
                'executions_attempted': 0,
                'executions_successful': 0,
                'net_energy_gained': 0.0
            }
        
        # Step 2: Queen analyzes and decides
        logger.info("🐝 Step 2: Queen analyzing and making decisions...")
        decisions = []
        for opp in opportunities:
            decision = await self.queen_analyze_and_decide(opp)
            decisions.append(decision)
            self.decisions_history.append(decision)
        
        # Step 3: Execute approved decisions
        logger.info("⚡ Step 3: Executing approved redistributions...")
        executions = []
        for decision in decisions:
            if decision.decision == 'EXECUTE':
                result = await self.execute_redistribution(decision)
                executions.append(result)
            else:
                # Track blocked drains
                self.total_blocked_drains_avoided += decision.opportunity.energy_drain
        
        # Summary
        successful_executions = sum(1 for e in executions if e.get('success'))
        net_energy_this_cycle = sum(e.get('net_energy_gain', 0.0) for e in executions if e.get('success'))
        
        cycle_summary = {
            'cycle_duration': time.time() - cycle_start,
            'opportunities_found': len(opportunities),
            'decisions_made': len(decisions),
            'executions_attempted': len(executions),
            'executions_successful': successful_executions,
            'net_energy_gained_this_cycle': net_energy_this_cycle,
            'total_net_energy_gained': self.total_net_energy_gained,
            'total_blocked_drains_avoided': self.total_blocked_drains_avoided
        }
        
        logger.info("=" * 60)
        logger.info("🐝 QUEEN POWER REDISTRIBUTION CYCLE COMPLETE")
        logger.info(f"Duration: {cycle_summary['cycle_duration']:.2f}s")
        logger.info(f"Opportunities: {cycle_summary['opportunities_found']}")
        logger.info(f"Executions: {cycle_summary['executions_successful']}/{cycle_summary['executions_attempted']}")
        logger.info(f"Net Energy Gained This Cycle: ${cycle_summary['net_energy_gained_this_cycle']:.4f}")
        logger.info(f"Total Net Energy Gained: ${cycle_summary['total_net_energy_gained']:.4f}")
        logger.info(f"Total Blocked Drains Avoided: ${cycle_summary['total_blocked_drains_avoided']:.4f}")
        logger.info("=" * 60)
        
        return cycle_summary
    
    async def run_continuous(self):
        """
        Run continuous redistribution cycles.
        Queen's eternal vigilance.
        """
        logger.info("🐝 Queen Power Redistribution: STARTING CONTINUOUS MODE")
        logger.info(f"Scan interval: {self.scan_interval_seconds}s")
        logger.info(f"Dry run: {self.dry_run}")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"\n📊 CYCLE {cycle_count} @ {datetime.now().strftime('%H:%M:%S')}")
                
                try:
                    summary = await self.run_redistribution_cycle()
                    
                    # Save state
                    self.save_state()
                    
                except Exception as e:
                    logger.error(f"❌ Cycle {cycle_count} failed: {e}", exc_info=True)
                
                # Wait for next cycle
                logger.info(f"⏳ Waiting {self.scan_interval_seconds}s for next cycle...")
                await asyncio.sleep(self.scan_interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Queen Power Redistribution: STOPPED BY USER")
            self.save_state()
    
    def save_state(self):
        """Save redistribution state to file."""
        state = {
            'last_update': time.time(),
            'total_net_energy_gained': self.total_net_energy_gained,
            'total_blocked_drains_avoided': self.total_blocked_drains_avoided,
            'decisions_count': len(self.decisions_history),
            'executions_count': len(self.executions_history),
            'recent_decisions': [d.to_dict() for d in self.decisions_history[-10:]],
            'recent_executions': self.executions_history[-10:]
        }
        
        try:
            with open('queen_redistribution_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug("💾 State saved to queen_redistribution_state.json")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Queen Power Redistribution Engine")
    parser.add_argument('--live', action='store_true', help='Run in LIVE mode (default: dry-run)')
    parser.add_argument('--once', action='store_true', help='Run one cycle then exit')
    parser.add_argument('--interval', type=int, default=30, help='Scan interval in seconds (default: 30)')
    args = parser.parse_args()
    
    dry_run = not args.live
    
    print("=" * 60)
    print("🐝 QUEEN POWER REDISTRIBUTION ENGINE")
    print("=" * 60)
    print(f"Mode: {'🔶 DRY-RUN' if dry_run else '⚡ LIVE'}")
    print(f"Interval: {args.interval}s")
    print("=" * 60)
    
    # Initialize system
    system = QueenPowerRedistribution(dry_run=dry_run)
    system.scan_interval_seconds = args.interval
    
    if args.once:
        # Run one cycle
        summary = await system.run_redistribution_cycle()
        system.save_state()
        
        print("\n" + "=" * 60)
        print("📊 SINGLE CYCLE COMPLETE")
        print(json.dumps(summary, indent=2))
        print("=" * 60)
    else:
        # Run continuously
        await system.run_continuous()


if __name__ == '__main__':
    asyncio.run(main())
